#!/usr/bin/env python3
"""Screen canonical Euler-socle scalars for low-complexity exact recurrences."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

import sympy as sp

from r3_common import R3Error, atomic_json_write, require, sha256


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
VERIFIER_PATH = BASE / "verify_rational_radical_certificates.py"
SOURCE_PATHS = (SCRIPT_PATH, VERIFIER_PATH)


def decode(value: object) -> Fraction:
    require(
        isinstance(value, dict)
        and set(value) == {"numerator", "denominator"}
        and isinstance(value["numerator"], int)
        and isinstance(value["denominator"], int)
        and value["denominator"] > 0,
        "malformed rational scalar",
    )
    answer = Fraction(value["numerator"], value["denominator"])
    require(answer != 0, "canonical socle scalar unexpectedly vanished")
    return answer


def extract_sequences(receipt: dict[str, object]) -> dict[str, dict[int, Fraction]]:
    require(
        receipt.get("schema") == "polydegree-r3-rational-radical-verification-v1"
        and receipt.get("status") == "PASS"
        and receipt.get("d_min") == 2
        and receipt.get("d_max") == 12,
        "Euler-socle input is not the terminal d=2..12 verification receipt",
    )
    verified = receipt.get("verified")
    require(
        isinstance(verified, list)
        and [case.get("d") for case in verified if isinstance(case, dict)]
        == list(range(2, 13)),
        "Euler-socle input degree inventory mismatch",
    )
    sequences = {"lambda_x1": {}, "nu_x3": {}}
    for case in verified:
        d = case["d"]
        euler = case.get("euler_jacobian")
        require(isinstance(euler, dict), f"missing Euler data at d={d}")
        scalars = euler.get("socle_scalars")
        require(isinstance(scalars, list), f"missing socle scalars at d={d}")
        by_variable = {
            row.get("variable"): decode(row.get("scalar_times_euler_determinant"))
            for row in scalars
            if isinstance(row, dict)
        }
        require(set(by_variable) >= {"x1", "x3"}, f"missing x1/x3 scalar at d={d}")
        sequences["lambda_x1"][d] = by_variable["x1"]
        sequences["nu_x3"][d] = by_variable["x3"]
    return sequences


def rational_ratio_rows(
    sequence: dict[int, Fraction], degrees: list[int], p_degree: int, q_degree: int
) -> sp.Matrix:
    rows = []
    for d in degrees:
        current = sp.Rational(sequence[d].numerator, sequence[d].denominator)
        following = sp.Rational(sequence[d + 1].numerator, sequence[d + 1].denominator)
        rows.append(
            [-(current * d**power) for power in range(p_degree + 1)]
            + [(following * d**power) for power in range(q_degree + 1)]
        )
    return sp.Matrix(rows)


def ratio_screen(sequence: dict[int, Fraction], max_total_degree: int = 5) -> dict[str, object]:
    training = list(range(2, 9))
    holdouts = [9, 10, 11]
    models = []
    survivors = []
    falsified = []
    for total in range(max_total_degree + 1):
        for p_degree in range(total + 1):
            q_degree = total - p_degree
            training_matrix = rational_ratio_rows(
                sequence, training, p_degree, q_degree
            )
            full_matrix = rational_ratio_rows(
                sequence, training + holdouts, p_degree, q_degree
            )
            unknowns = p_degree + q_degree + 2
            training_rank = training_matrix.rank()
            full_rank = full_matrix.rank()
            training_nullity = unknowns - training_rank
            full_nullity = unknowns - full_rank
            disposition = "EXCLUDED_ON_TRAINING"
            if training_nullity > 0 and full_nullity == 0:
                disposition = "FALSIFIED_ON_HOLDOUT"
                falsified.append([p_degree, q_degree])
            elif full_nullity > 0:
                disposition = "SURVIVES_HOLDOUT"
                survivors.append([p_degree, q_degree])
            models.append(
                {
                    "degree_P": p_degree,
                    "degree_Q": q_degree,
                    "unknown_coefficients": unknowns,
                    "training_rank": training_rank,
                    "training_nullity": training_nullity,
                    "full_rank": full_rank,
                    "full_nullity": full_nullity,
                    "disposition": disposition,
                }
            )
    return {
        "equation": "a_(d+1) Q(d) = a_d P(d)",
        "max_total_degree": max_total_degree,
        "training_transitions": training,
        "holdout_transitions": holdouts,
        "models": models,
        "falsified_on_holdout": falsified,
        "survives_holdout": survivors,
    }


def order_two_rows(
    sequence: dict[int, Fraction], starts: list[int], polynomial_degree: int
) -> sp.Matrix:
    rows = []
    for d in starts:
        row = []
        for shift in range(3):
            value = sp.Rational(
                sequence[d + shift].numerator, sequence[d + shift].denominator
            )
            row.extend(value * d**power for power in range(polynomial_degree + 1))
        rows.append(row)
    return sp.Matrix(rows)


def order_two_screen(sequence: dict[int, Fraction], max_polynomial_degree: int = 1) -> dict[str, object]:
    training = list(range(2, 8))
    holdouts = [8, 9, 10]
    models = []
    survivors = []
    for degree in range(max_polynomial_degree + 1):
        training_matrix = order_two_rows(sequence, training, degree)
        full_matrix = order_two_rows(sequence, training + holdouts, degree)
        unknowns = 3 * (degree + 1)
        training_rank = training_matrix.rank()
        full_rank = full_matrix.rank()
        training_nullity = unknowns - training_rank
        full_nullity = unknowns - full_rank
        disposition = "EXCLUDED_ON_TRAINING"
        if training_nullity > 0 and full_nullity == 0:
            disposition = "FALSIFIED_ON_HOLDOUT"
        elif full_nullity > 0:
            disposition = "SURVIVES_HOLDOUT"
            survivors.append(degree)
        models.append(
            {
                "polynomial_degree": degree,
                "unknown_coefficients": unknowns,
                "training_rank": training_rank,
                "training_nullity": training_nullity,
                "full_rank": full_rank,
                "full_nullity": full_nullity,
                "disposition": disposition,
            }
        )
    return {
        "equation": "P0(d)a_d + P1(d)a_(d+1) + P2(d)a_(d+2) = 0",
        "max_polynomial_degree": max_polynomial_degree,
        "training_starts": training,
        "holdout_starts": holdouts,
        "models": models,
        "survives_holdout": survivors,
    }


def negative_control() -> dict[str, object]:
    geometric = {d: Fraction(3**d) for d in range(2, 13)}
    passing = ratio_screen(geometric, 0)
    require(passing["survives_holdout"] == [[0, 0]],
            "geometric-sequence positive control was not detected")
    mutated = dict(geometric)
    mutated[12] += 1
    rejected = ratio_screen(mutated, 0)
    require(rejected["survives_holdout"] == []
            and rejected["falsified_on_holdout"] == [[0, 0]],
            "terminal mutation was not rejected on holdout")
    return {
        "geometric_ratio_detected": True,
        "terminal_mutation_falsified_on_holdout": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    input_path = args.input.resolve()
    peer_path = args.peer.resolve()
    output = args.out.resolve()
    require(input_path.is_file() and peer_path.is_file(), "recurrence input is absent")
    require(output not in {input_path, peer_path, *SOURCE_PATHS},
            "recurrence output overwrites an input or source")
    require(not output.exists(), "refusing to overwrite recurrence receipt")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {path.name: sha256(path) for path in (input_path, peer_path)}
    receipt = json.loads(input_path.read_text())
    peer = json.loads(peer_path.read_text())
    require(receipt == peer, "Euler-socle verification peers differ")
    sequences = extract_sequences(receipt)
    screens = {
        name: {
            "rational_ratio": ratio_screen(sequence),
            "order_two": order_two_screen(sequence),
        }
        for name, sequence in sequences.items()
    }
    survivors = {
        name: {
            "rational_ratio": screen["rational_ratio"]["survives_holdout"],
            "order_two": screen["order_two"]["survives_holdout"],
        }
        for name, screen in screens.items()
    }
    gate = "ADVANCE" if any(
        values[family]
        for values in survivors.values()
        for family in ("rational_ratio", "order_two")
    ) else "STOP_LOW_COMPLEXITY"
    controls = negative_control()
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "recurrence source changed during execution")
    require({path.name: sha256(path) for path in (input_path, peer_path)} == startup_inputs,
            "recurrence input changed during execution")
    output_receipt = {
        "schema": "polydegree-r3-euler-socle-recurrence-screen-v1",
        "status": "PASS",
        "claim_boundary": (
            "Exact finite screen of the displayed bounded recurrence classes with three "
            "terminal holdout equations; no conclusion about higher-order holonomicity or "
            "the all-degree identities is made."
        ),
        "degree_range": [2, 12],
        "screens": screens,
        "survivors": survivors,
        "gate": gate,
        "negative_controls": controls,
        "inputs_sha256": startup_inputs,
        "source_sha256": startup_sources,
    }
    atomic_json_write(output, output_receipt)
    print(json.dumps({"status": "PASS", "gate": gate}, sort_keys=True))
    print("Euler-socle recurrence receipt:", output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError, ValueError) as exc:
        print(f"R3 EULER-SOCLE RECURRENCE SCREEN FAILED: {exc}")
        raise SystemExit(1)
