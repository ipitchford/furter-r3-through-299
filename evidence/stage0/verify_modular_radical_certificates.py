#!/usr/bin/env python3
"""Independently expand finite-field pure-power membership certificates."""

from __future__ import annotations

import argparse
import copy
import json
import platform
from pathlib import Path

from analyze_good_prime_frontier import require_verification_binding
from r3_common import R3Error, atomic_json_write, g_terms, require, sha256
from verify_colength import DEFAULT_SINGULAR, verify_formula_independence, verify_receipt


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
PRODUCER_PATH = BASE / "extract_modular_radical_certificates.py"
SOURCE_PATHS = (
    SCRIPT_PATH,
    PRODUCER_PATH,
    BASE / "r3_common.py",
    BASE / "modular_colength.py",
    BASE / "verify_colength.py",
    BASE / "analyze_good_prime_frontier.py",
)
Exponent = tuple[int, int, int]
Sparse = dict[Exponent, int]


def add(left: Sparse, right: Sparse, prime: int) -> Sparse:
    result = dict(left)
    for exponents, coefficient in right.items():
        value = (result.get(exponents, 0) + coefficient) % prime
        if value:
            result[exponents] = value
        else:
            result.pop(exponents, None)
    return result


def multiply(left: Sparse, right: Sparse, prime: int) -> Sparse:
    result: Sparse = {}
    for left_exponents, left_coefficient in left.items():
        for right_exponents, right_coefficient in right.items():
            exponents = tuple(
                left_exponents[index] + right_exponents[index] for index in range(3)
            )
            value = (
                result.get(exponents, 0) + left_coefficient * right_coefficient
            ) % prime
            if value:
                result[exponents] = value
            else:
                result.pop(exponents, None)
    return result


def decode(rows: object, prime: int) -> Sparse:
    require(isinstance(rows, list), "cofactor encoding is not a list")
    result: Sparse = {}
    order: list[Exponent] = []
    for row in rows:
        require(isinstance(row, dict) and set(row) == {"exponents", "coefficient"},
                "malformed cofactor term")
        raw_exponents = row["exponents"]
        coefficient = row["coefficient"]
        require(
            isinstance(raw_exponents, list)
            and len(raw_exponents) == 3
            and all(isinstance(value, int) and value >= 0 for value in raw_exponents),
            "invalid cofactor exponents",
        )
        require(isinstance(coefficient, int) and 1 <= coefficient < prime,
                "cofactor coefficient is not canonical modulo p")
        exponents = tuple(raw_exponents)
        require(exponents not in result, "duplicate cofactor monomial")
        result[exponents] = coefficient
        order.append(exponents)
    require(order == sorted(order, reverse=True), "cofactor terms are not canonically ordered")
    return result


def generator(n: int, prime: int) -> Sparse:
    result: Sparse = {}
    for exponents, coefficient in g_terms(n):
        value = coefficient % prime
        if value:
            result[tuple(exponents)] = value
    require(result, f"generator g_{n} vanished modulo {prime}")
    return result


def independently_select_smallest_good(
    modular_map: dict[str, object], d_min: int, d_max: int
) -> dict[int, int]:
    selected: dict[int, int] = {}
    rows = modular_map.get("rows")
    require(isinstance(rows, list), "modular map lacks rows")
    for row in rows:
        require(isinstance(row, dict), "modular map contains a malformed row")
        d = row.get("d")
        prime = row.get("prime")
        if (
            row.get("classification") == "GOOD"
            and isinstance(d, int)
            and d_min <= d <= d_max
            and isinstance(prime, int)
        ):
            selected[d] = min(selected.get(d, prime), prime)
    require(sorted(selected) == list(range(d_min, d_max + 1)),
            "verified map lacks GOOD coverage for the certificate range")
    return selected


def verify_case(case: object, expected_d: int, expected_prime: int) -> dict[str, object]:
    require(isinstance(case, dict), "certificate case is not an object")
    require(case.get("d") == expected_d and case.get("prime") == expected_prime,
            "certificate degree or prime mismatch")
    socle_weight_bound = 3 * expected_d - 3
    require(case.get("socle_weight_bound") == socle_weight_bound,
            "certificate socle-weight bound mismatch")
    require(case.get("singular_remainders_zero") is True,
            "producer did not record zero lift remainders")
    targets = case.get("targets")
    require(isinstance(targets, list) and len(targets) == 3,
            "certificate must contain exactly three targets")
    generators = [generator(expected_d + offset, expected_prime) for offset in range(3)]
    target_exponents = []
    total_terms = 0
    expected_target_exponents = [
        socle_weight_bound + 1,
        socle_weight_bound // 2 + 1,
        socle_weight_bound // 3 + 1,
    ]
    for axis, target in enumerate(targets):
        require(isinstance(target, dict) and set(target) == {
            "variable", "exponent", "cofactors"
        }, "malformed target object")
        require(target["variable"] == f"x{axis + 1}", "target variable order mismatch")
        exponent = target["exponent"]
        require(exponent == expected_target_exponents[axis],
                "target exponent differs from the universal socle-bound exponent")
        cofactors = target["cofactors"]
        require(isinstance(cofactors, list) and len(cofactors) == 3,
                "target has the wrong cofactor inventory")
        reconstructed: Sparse = {}
        for cofactor_rows, polynomial in zip(cofactors, generators, strict=True):
            cofactor = decode(cofactor_rows, expected_prime)
            total_terms += len(cofactor)
            reconstructed = add(
                reconstructed, multiply(cofactor, polynomial, expected_prime), expected_prime
            )
        target_exponents_vector = [0, 0, 0]
        target_exponents_vector[axis] = exponent
        expected = {tuple(target_exponents_vector): 1}
        require(reconstructed == expected,
                f"pure-power identity failed at d={expected_d}, axis={axis + 1}")
        target_exponents.append(exponent)
    return {"d": expected_d, "prime": expected_prime,
            "target_exponents": target_exponents, "cofactor_terms": total_terms}


def require_source_binding(receipt: dict[str, object], path: Path) -> None:
    bindings = receipt.get("source_sha256")
    require(isinstance(bindings, dict), "certificate receipt lacks source bindings")
    require(bindings.get(path.name) == sha256(path),
            f"certificate receipt binds stale {path.name}")


def verify_payload(
    receipt: dict[str, object],
    modular_map: dict[str, object],
    map_path: Path,
    verification_path: Path,
    d_min: int,
    d_max: int,
    singular: Path,
) -> list[dict[str, object]]:
    require(
        receipt.get("schema") == "polydegree-r3-modular-radical-certificates-v1"
        and receipt.get("status") == "PASS",
        "modular radical certificate receipt is not terminal PASS",
    )
    require(receipt.get("d_min") == d_min and receipt.get("d_max") == d_max,
            "certificate receipt range mismatch")
    for source_path in (
        PRODUCER_PATH,
        BASE / "r3_common.py",
        BASE / "modular_colength.py",
        BASE / "verify_colength.py",
        BASE / "analyze_good_prime_frontier.py",
    ):
        require_source_binding(receipt, source_path)
    require(
        receipt.get("inputs_sha256") == {
            map_path.name: sha256(map_path),
            verification_path.name: sha256(verification_path),
        },
        "certificate receipt does not bind the verified modular map",
    )
    require(receipt.get("runtime_sha256") == {singular.name: sha256(singular)},
            "certificate receipt Singular binding mismatch")
    cases = receipt.get("cases")
    require(isinstance(cases, list) and len(cases) == d_max - d_min + 1,
            "certificate case inventory mismatch")
    smallest = independently_select_smallest_good(modular_map, d_min, d_max)
    return [
        verify_case(case, d, smallest[d])
        for d, case in zip(range(d_min, d_max + 1), cases, strict=True)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--map-verification", type=Path, required=True)
    parser.add_argument("--d-min", type=int, default=2)
    parser.add_argument("--d-max", type=int, default=8)
    parser.add_argument("--expected-prime-max", type=int, default=997)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    paths = tuple(
        path.resolve() for path in (
            args.input, args.peer, args.map, args.map_verification, args.singular
        )
    )
    output_path = args.out.resolve()
    require(all(path.is_file() for path in paths), "one or more verification inputs are absent")
    require(output_path not in {*paths, *SOURCE_PATHS},
            "verification output overwrites an input or source")
    require(not output_path.exists(), "refusing to overwrite an existing output")
    input_path, peer_path, map_path, map_verification_path, singular = paths
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {str(path): sha256(path) for path in paths}
    modular_map = json.loads(map_path.read_text())
    map_verification = json.loads(map_verification_path.read_text())
    parameters = modular_map.get("parameters")
    require(isinstance(parameters, dict), "modular map lacks parameters")
    map_d_min = parameters.get("d_min")
    map_d_max = parameters.get("d_max")
    require(
        isinstance(map_d_min, int)
        and isinstance(map_d_max, int)
        and map_d_min <= args.d_min <= args.d_max <= map_d_max,
        "verified modular map does not cover the requested certificate range",
    )
    map_summary = verify_receipt(
        modular_map,
        map_d_min,
        map_d_max,
        args.expected_prime_max,
        True,
        singular,
    )
    require_verification_binding(map_verification, map_path, map_summary)
    formula_independence = verify_formula_independence(args.d_max + 2)
    receipt = json.loads(input_path.read_text())
    peer = json.loads(peer_path.read_text())
    require(receipt == peer, "ordinary/optimized modular certificates differ")
    summary = verify_payload(
        receipt, modular_map, map_path, map_verification_path,
        args.d_min, args.d_max, singular,
    )
    verify_payload(
        peer, modular_map, map_path, map_verification_path,
        args.d_min, args.d_max, singular,
    )
    mutated = copy.deepcopy(receipt)
    mutation_applied = False
    for case in mutated["cases"]:
        prime = case["prime"]
        if prime <= 2:
            continue
        for target in case["targets"]:
            for cofactor in target["cofactors"]:
                if cofactor:
                    coefficient = cofactor[0]["coefficient"]
                    cofactor[0]["coefficient"] = coefficient % (prime - 1) + 1
                    mutation_applied = True
                    break
            if mutation_applied:
                break
        if mutation_applied:
            break
    require(mutation_applied, "no cofactor term was available for the mutation control")
    mutation_rejected = False
    try:
        verify_payload(
            mutated, modular_map, map_path, map_verification_path,
            args.d_min, args.d_max, singular,
        )
    except R3Error:
        mutation_rejected = True
    require(mutation_rejected, "cofactor mutation was not rejected")
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "certificate verifier source changed during execution")
    require({str(path): sha256(path) for path in paths} == startup_inputs,
            "certificate verifier input changed during execution")
    output = {
        "schema": "polydegree-r3-modular-radical-certificate-verification-v1",
        "status": "PASS",
        "claim_boundary": (
            "Independent sparse expansion of the displayed finite-field membership "
            "identities only; no all-degree transition theorem is claimed."
        ),
        "d_min": args.d_min,
        "d_max": args.d_max,
        "summary": summary,
        "formula_independence": formula_independence,
        "cofactor_mutation_rejected": mutation_rejected,
        "inputs_sha256": {
            path.name: startup_inputs[str(path)]
            for path in (input_path, peer_path, map_path, map_verification_path)
        },
        "source_sha256": startup_sources,
        "runtime_sha256": {singular.name: startup_inputs[str(singular)]},
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(output_path, output)
    print(json.dumps({"status": "PASS", "cases": len(summary)}, sort_keys=True))
    print("modular radical certificate verification:", output_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 MODULAR RADICAL CERTIFICATE VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
