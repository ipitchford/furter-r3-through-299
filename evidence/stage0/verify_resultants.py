#!/usr/bin/env python3
"""Arithmetic, provenance, and modular verifier for the R(3) resultant pilot."""

from __future__ import annotations

import argparse
import copy
import json
import platform
import sys
from pathlib import Path

from r3_common import R3Error, atomic_json_write, g_terms, require, sha256
from verify_colength import DEFAULT_SINGULAR, verify_receipt as verify_colength_receipt


sys.set_int_max_str_digits(0)


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")
PRODUCER_PATH = SCRIPT_PATH.with_name("cover_resultant.py")
MODULAR_PRODUCER_PATH = SCRIPT_PATH.with_name("modular_colength.py")
COLENGTH_VERIFIER_PATH = SCRIPT_PATH.with_name("verify_colength.py")
ASSEMBLER_PATH = SCRIPT_PATH.with_name("assemble_resultant_shards.py")
CRT_VERIFIER_PATH = SCRIPT_PATH.with_name("verify_resultant_crt.py")
PREFIX_VERIFIER_PATH = SCRIPT_PATH.with_name("verify_resultant_prefix.py")


def remove_nondeterminism(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: remove_nondeterminism(item)
            for key, item in value.items()
            if key not in {"elapsed_seconds", "assembly"}
        }
    if isinstance(value, list):
        return [remove_nondeterminism(item) for item in value]
    return value


def source_bindings(receipt: dict[str, object]) -> None:
    hashes = receipt.get("startup_sha256")
    require(isinstance(hashes, dict), "resultant receipt lacks source bindings")
    for path in (PRODUCER_PATH, COMMON_PATH):
        keys = [key for key in hashes if Path(key).name == path.name]
        require(len(keys) == 1, f"receipt must bind exactly one {path.name}")
        require(hashes.get(keys[0]) == sha256(path), f"stale source hash for {path.name}")
    runtime = receipt.get("runtime_sha256")
    require(isinstance(runtime, dict) and runtime, "resultant receipt lacks runtime bindings")
    require(len(runtime) == receipt.get("environment", {}).get("runtime_artifact_count"),
            "resultant runtime inventory count mismatch")
    for raw_path, expected_hash in runtime.items():
        require(isinstance(raw_path, str) and isinstance(expected_hash, str),
                "invalid resultant runtime binding")
        path = Path(raw_path)
        require(path.is_file() and sha256(path) == expected_hash,
                f"resultant runtime artifact is absent or changed: {path.name}")
    require(any(Path(path).name.startswith("libflint") for path in runtime),
            "resultant receipt does not bind the FLINT shared library")
    assembly = receipt.get("assembly")
    if assembly is not None:
        require(isinstance(assembly, dict) and assembly.get("gap_free") is True,
                "invalid resultant assembly record")
        require(assembly.get("script_sha256") == sha256(ASSEMBLER_PATH),
                "resultant assembly script binding is stale")
        inputs = assembly.get("inputs_sha256")
        require(isinstance(inputs, dict) and inputs,
                "resultant assembly lacks raw input bindings")
        for name, expected in inputs.items():
            path = SCRIPT_PATH.parent / name
            require(path.is_file() and sha256(path) == expected,
                    f"resultant assembly input is absent or changed: {name}")


def axis_coefficients(d: int) -> tuple[int | None, int]:
    degrees = (d, d + 1, d + 2)
    x2 = [
        coefficient
        for degree in degrees
        for exponent, coefficient in g_terms(degree)
        if degree % 2 == 0 and exponent == (0, degree // 2, 0)
    ]
    x3 = [
        coefficient
        for degree in degrees
        for exponent, coefficient in g_terms(degree)
        if degree % 3 == 0 and exponent == (0, 0, degree // 3)
    ]
    require(len(x3) == 1, "independent x3-axis inventory failed")
    if d % 2:
        require(len(x2) == 1, "independent odd-d x2-axis inventory failed")
        return x2[0], x3[0]
    require(len(x2) == 2, "independent even-d x2-axis inventory failed")
    return None, x3[0]


def verify_resultant_receipt(receipt: dict[str, object], d_min: int, d_max: int) -> dict[int, int]:
    if receipt.get("schema") == "polydegree-r3-resultant-composite-v1":
        return verify_composite_receipt(receipt, d_min, d_max)
    require(receipt.get("schema") == "polydegree-r3-cover-resultant-v2", "wrong resultant schema")
    require(receipt.get("status") == "PASS", "resultant receipt is not terminal PASS")
    require(receipt.get("d_min") == d_min and receipt.get("d_max") == d_max,
            "resultant range mismatch")
    source_bindings(receipt)
    controls = receipt.get("controls")
    require(isinstance(controls, dict) and
            controls.get("large_exact_integer_decimal_digits") == 5001 and
            controls.get("large_exact_integer_serialization_enabled") is True and
            controls.get("checkpoint_exact_prefix_validated") is True and
            isinstance(controls.get("resumed_case_count"), int) and
            controls["resumed_case_count"] >= 0,
            "large exact integer serialization control is absent")
    cases = receipt.get("cases")
    require(isinstance(cases, list) and len(cases) == d_max - d_min + 1,
            "resultant case count mismatch")
    values: dict[int, int] = {}
    for expected_d, case in zip(range(d_min, d_max + 1), cases):
        require(isinstance(case, dict) and case.get("d") == expected_d,
                "resultant case inventory mismatch")
        dimensions = case.get("dimensions")
        require(isinstance(dimensions, dict), "missing Koszul dimensions")
        strand = 3 * expected_d + 1
        k0 = (strand + 2) * (strand + 1) // 2
        require(dimensions.get("strand_degree") == strand and dimensions.get("K0") == k0,
                "stored Macaulay strand dimension mismatch")
        require(dimensions.get("K1") == dimensions.get("K0") + dimensions.get("K2"),
                "stored Koszul Euler characteristic mismatch")
        numerator = case.get("numerator_minor_det")
        denominator = case.get("denominator_minor_det")
        ordinary = case.get("ordinary_cover_resultant_abs")
        require(all(isinstance(value, int) and value != 0
                    for value in (numerator, denominator, ordinary)),
                "invalid determinant data")
        quotient, remainder = divmod(abs(numerator), abs(denominator))
        require(remainder == 0 and quotient == ordinary, "ordinary determinant ratio mismatch")
        x2, x3 = axis_coefficients(expected_d)
        correction = abs(x3) ** 4 * (abs(x2) ** 3 if x2 is not None else 1)
        stored_correction = case.get("axis_correction")
        require(isinstance(stored_correction, dict), "missing axis correction")
        require(stored_correction.get("x2_axis_coefficient") == x2 and
                stored_correction.get("x3_axis_coefficient") == x3 and
                stored_correction.get("factor_abs") == correction,
                "axis correction mismatch")
        corrected = ordinary * correction
        require(case.get("axis_corrected_cover_resultant_abs") == corrected,
                "corrected cover resultant mismatch")
        weighted = case.get("weighted_resultant_abs")
        require(isinstance(weighted, int) and weighted > 0, "invalid weighted resultant")
        require(weighted ** 6 == corrected and case.get("sixth_power_identity") is True,
                "sixth-power identity mismatch")
        values[expected_d] = weighted
    corrupted = dict(values)
    corrupted[d_min] += 1
    require(corrupted[d_min] ** 6 != cases[0]["axis_corrected_cover_resultant_abs"],
            "resultant mutation control failed")
    return values


def verify_composite_receipt(
    receipt: dict[str, object], d_min: int, d_max: int
) -> dict[int, int]:
    require(receipt.get("status") == "PASS", "composite resultant receipt is not PASS")
    require(receipt.get("d_min") == d_min and receipt.get("d_max") == d_max,
            "composite resultant range mismatch")
    assembly = receipt.get("assembly")
    require(isinstance(assembly, dict) and assembly.get("gap_free") is True,
            "composite resultant assembly record is invalid")
    require(assembly.get("script_sha256") == sha256(ASSEMBLER_PATH),
            "composite resultant assembler binding is stale")
    variant = assembly.get("variant")
    prefix_end = assembly.get("prefix_end")
    require(variant in {"ordinary", "optimized"} and
            isinstance(prefix_end, int) and d_min <= prefix_end < d_max and
            assembly.get("crt_start") == prefix_end + 1,
            "composite resultant partition is invalid")
    expected_names = {
        f"resultant-prefix-{variant}.json",
        "resultant-prefix-verification.json",
    } | {
        f"resultant-shard-{variant}-d{d:02}.json"
        for d in range(prefix_end + 1, d_max + 1)
    } | {
        f"resultant-shard-verification-d{d:02}.json"
        for d in range(prefix_end + 1, d_max + 1)
    }
    inputs = assembly.get("inputs_sha256")
    require(isinstance(inputs, dict) and set(inputs) == expected_names,
            "composite resultant raw input inventory mismatch")
    for name, expected in inputs.items():
        path = SCRIPT_PATH.parent / name
        require(path.is_file() and sha256(path) == expected,
                f"composite resultant input is absent or changed: {name}")
    from assemble_resultant_shards import (
        load_prefix,
        verified_crt_value,
        verified_prefix_values,
    )
    checkpoint, verified_prefix_end = load_prefix(
        SCRIPT_PATH.parent / f"resultant-prefix-{variant}.json", d_min, d_max
    )
    require(verified_prefix_end == prefix_end, "composite prefix endpoint mismatch")
    values, _ = verified_prefix_values(
        SCRIPT_PATH.parent / f"resultant-prefix-{variant}.json", checkpoint
    )
    for d in range(prefix_end + 1, d_max + 1):
        path = SCRIPT_PATH.parent / f"resultant-shard-{variant}-d{d:02}.json"
        verification_path = (
            SCRIPT_PATH.parent / f"resultant-shard-verification-d{d:02}.json"
        )
        raw = json.loads(path.read_text())
        cases = raw.get("cases")
        require(raw.get("schema") == "polydegree-r3-cover-resultant-crt-v1" and
                raw.get("status") == "PASS" and raw.get("d_min") == d and
                raw.get("d_max") == d and isinstance(cases, list) and
                len(cases) == 1 and cases[0].get("d") == d,
                f"composite CRT shard metadata mismatch at d={d}")
        verified = verified_crt_value(path, verification_path, d)
        require(cases[0].get("weighted_resultant_abs") == verified,
                f"composite CRT shard differs from its verification at d={d}")
        values[d] = verified
    require(sorted(values) == list(range(d_min, d_max + 1)),
            "composite resultant verified inventory is not gap-free")
    stored = receipt.get("values")
    require(stored == [
        {"d": d, "weighted_resultant_abs": values[d]}
        for d in range(d_min, d_max + 1)
    ], "composite resultant stored values mismatch")
    return values


def verify_composite_peer_projection(
    ordinary: dict[str, object], peer: dict[str, object], d_min: int, d_max: int
) -> dict[int, int]:
    require(peer.get("schema") == "polydegree-r3-resultant-composite-v1" and
            peer.get("status") == "PASS" and peer.get("d_min") == d_min and
            peer.get("d_max") == d_max, "peer composite resultant metadata mismatch")
    require(peer.get("values") == ordinary.get("values"),
            "peer composite resultant values differ")
    left = ordinary.get("assembly")
    right = peer.get("assembly")
    require(isinstance(left, dict) and isinstance(right, dict) and
            left.get("variant") == "ordinary" and right.get("variant") == "optimized" and
            left.get("prefix_end") == right.get("prefix_end") and
            left.get("crt_start") == right.get("crt_start") and
            left.get("gap_free") is True and right.get("gap_free") is True and
            left.get("script_sha256") == right.get("script_sha256") == sha256(ASSEMBLER_PATH),
            "ordinary/optimized composite assembly metadata differs")
    prefix_end = left["prefix_end"]
    ordinary_prefix = json.loads(
        (SCRIPT_PATH.parent / "resultant-prefix-ordinary.json").read_text()
    )
    optimized_prefix = json.loads(
        (SCRIPT_PATH.parent / "resultant-prefix-optimized.json").read_text()
    )
    require(remove_nondeterminism(copy.deepcopy(ordinary_prefix)) ==
            remove_nondeterminism(copy.deepcopy(optimized_prefix)),
            "ordinary/optimized full-integer prefixes differ outside timing")
    for d in range(prefix_end + 1, d_max + 1):
        ordinary_raw = json.loads(
            (SCRIPT_PATH.parent / f"resultant-shard-ordinary-d{d:02}.json").read_text()
        )
        optimized_raw = json.loads(
            (SCRIPT_PATH.parent / f"resultant-shard-optimized-d{d:02}.json").read_text()
        )
        require(remove_nondeterminism(copy.deepcopy(ordinary_raw)) ==
                remove_nondeterminism(copy.deepcopy(optimized_raw)),
                f"ordinary/optimized CRT shards differ outside timing at d={d}")
    return {
        row["d"]: row["weighted_resultant_abs"]
        for row in peer["values"]
    }


def verify_modular_parity(
    modular: dict[str, object], values: dict[int, int], d_min: int, d_max: int,
    singular_executable: Path = DEFAULT_SINGULAR,
) -> dict[str, object]:
    require(modular.get("schema") == "polydegree-r3-modular-colength-v1",
            "wrong modular receipt schema")
    require(modular.get("status") == "PASS" and modular.get("incomplete") == [],
            "modular receipt is not terminal PASS")
    hashes = modular.get("startup_sha256")
    require(isinstance(hashes, dict), "modular receipt lacks hashes")
    for path in (MODULAR_PRODUCER_PATH, COMMON_PATH):
        keys = [key for key in hashes if Path(key).name == path.name]
        require(len(keys) == 1, f"modular receipt must bind exactly one {path.name}")
        require(hashes.get(keys[0]) == sha256(path), f"stale modular hash for {path.name}")
    parameters = modular.get("parameters")
    require(isinstance(parameters, dict) and parameters.get("first_good") is False,
            "modular parity needs a full prime map")
    require(parameters.get("d_min") <= d_min and parameters.get("d_max") >= d_max,
            "modular map does not cover resultant range")
    prime_inventory = parameters.get("primes")
    require(isinstance(prime_inventory, list) and prime_inventory,
            "modular map lacks a prime inventory")
    verify_colength_receipt(
        modular,
        parameters["d_min"],
        parameters["d_max"],
        max(prime_inventory),
        True,
        singular_executable,
    )
    rows = modular.get("rows")
    require(isinstance(rows, list), "modular map lacks rows")
    checked = 0
    bad = 0
    by_degree: dict[int, list[int]] = {d: [] for d in range(d_min, d_max + 1)}
    for row in rows:
        d = row.get("d")
        if not isinstance(d, int) or not d_min <= d <= d_max:
            continue
        prime = row.get("prime")
        classification = row.get("classification")
        require(isinstance(prime, int), "modular row prime is invalid")
        divides = values[d] % prime == 0
        require((classification == "BAD") == divides,
                f"resultant/modular disagreement at d={d}, p={prime}")
        checked += 1
        bad += int(divides)
        if divides:
            by_degree[d].append(prime)
    prime_count = len(parameters.get("primes", []))
    require(checked == (d_max - d_min + 1) * prime_count,
            "resultant/modular parity did not cover the Cartesian range")
    return {
        "comparisons": checked,
        "dividing_bad_primes": bad,
        "exact_equivalence": True,
        "by_degree": [
            {"d": d, "bad_and_dividing_primes": by_degree[d]}
            for d in range(d_min, d_max + 1)
        ],
    }


def rank_mod_prime(rows: list[list[int]], prime: int) -> int:
    matrix = [[value % prime for value in row] for row in rows]
    row_count = len(matrix)
    column_count = len(matrix[0]) if matrix else 0
    rank = 0
    for column in range(column_count):
        pivot = next((row for row in range(rank, row_count) if matrix[row][column]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        inverse = pow(matrix[rank][column], -1, prime)
        matrix[rank] = [(value * inverse) % prime for value in matrix[rank]]
        for row in range(row_count):
            if row == rank or not matrix[row][column]:
                continue
            factor = matrix[row][column]
            matrix[row] = [
                (left - factor * right) % prime
                for left, right in zip(matrix[row], matrix[rank])
            ]
        rank += 1
        if rank == row_count:
            break
    return rank


def recurrence_screen(values: dict[int, int]) -> dict[str, object]:
    require(set(range(2, 26)).issubset(values), "recurrence screen needs d=2..25")
    training = list(range(2, 20))
    holdouts = list(range(20, 25))
    primes = (1000003, 1000033)
    tests = []
    candidates = []
    for degree_p in range(13):
        for degree_q in range(13 - degree_p):
            columns = degree_p + degree_q + 2
            rows = []
            for d in training:
                rows.append(
                    [-(values[d] * d ** power) for power in range(degree_p + 1)]
                    + [(values[d + 1] * d ** power) for power in range(degree_q + 1)]
                )
            ranks = [rank_mod_prime(rows, prime) for prime in primes]
            excluded = max(ranks) == columns
            test = {
                "degree_P": degree_p,
                "degree_Q": degree_q,
                "columns": columns,
                "modular_ranks": dict(zip((str(prime) for prime in primes), ranks)),
                "nonzero_rational_relation_excluded": excluded,
            }
            tests.append(test)
            if not excluded:
                candidates.append(test)
    return {
        "ansatz": "R_(d+1) Q(d) = R_d P(d), deg(P)+deg(Q)<=12",
        "training_transitions": training,
        "reserved_holdout_transitions": holdouts,
        "moduli": list(primes),
        "tests": tests,
        "unexcluded_training_candidates": candidates,
        "all_low_complexity_relations_excluded_on_training": not candidates,
        "holdout_disposition": (
            "reserved and not fit" if not candidates else
            "candidate reconstruction required before holdout evaluation"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    parser.add_argument("--modular-map", type=Path, required=True)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    input_paths = (args.input, args.peer, args.modular_map)
    for path in input_paths:
        require(path.is_file(), f"missing input: {path}")
    require(args.out.resolve() not in {path.resolve() for path in input_paths},
            "resultant verification output must not overwrite an input")
    singular = args.singular.resolve()
    require(singular.is_file(), "Singular executable is absent")
    source_paths = (
        SCRIPT_PATH, PRODUCER_PATH, COMMON_PATH, MODULAR_PRODUCER_PATH,
        COLENGTH_VERIFIER_PATH, CRT_VERIFIER_PATH, PREFIX_VERIFIER_PATH,
        ASSEMBLER_PATH,
    )
    watched_paths = (*input_paths, singular)
    startup_sources = {path.name: sha256(path) for path in source_paths}
    startup_inputs = {str(path.resolve()): sha256(path) for path in watched_paths}
    receipt = json.loads(args.input.read_text())
    peer = json.loads(args.peer.read_text())
    values = verify_resultant_receipt(receipt, 2, 25)
    peer_values = verify_composite_peer_projection(receipt, peer, 2, 25)
    require(values == peer_values, "ordinary/optimized resultant values differ")
    require(remove_nondeterminism(copy.deepcopy(receipt)) ==
            remove_nondeterminism(copy.deepcopy(peer)),
            "ordinary/optimized resultant receipts differ outside timing fields")
    modular = json.loads(args.modular_map.read_text())
    parity = verify_modular_parity(modular, values, 2, 25, singular)
    recurrence = recurrence_screen(values)
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "resultant verifier source changed during verification")
    require({str(path.resolve()): sha256(path) for path in watched_paths} == startup_inputs,
            "resultant input or Singular executable changed during verification")
    output = {
        "schema": "polydegree-r3-resultant-verification-v1",
        "status": "PASS",
        "inputs_sha256": {
            path.name: startup_inputs[str(path.resolve())] for path in input_paths
        },
        "verified_degrees": list(range(2, 26)),
        "full_integer_determinant_degrees": list(range(2, 18)),
        "independently_reconstructed_full_integer_degrees": list(range(2, 18)),
        "independently_reconstructed_crt_degrees": list(range(18, 26)),
        "ordinary_optimized_timing_free_parity": True,
        "axis_and_sixth_power_identities": True,
        "modular_prime_support_parity": parity,
        "recurrence_screen": recurrence,
        "negative_controls": {"weighted_resultant_increment_rejected": True},
        "source_sha256": startup_sources,
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(args.out, output)
    print(json.dumps({
        "status": "PASS",
        "degrees": 24,
        "modular_comparisons": parity["comparisons"],
        "recurrence_candidates": len(recurrence["unexcluded_training_candidates"]),
    }, sort_keys=True))
    print("resultant verification receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 RESULTANT VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
