#!/usr/bin/env python3
"""Bounded structural recurrence search for exact R(3) cofactor vectors."""

from __future__ import annotations

import argparse
import json
import platform
from fractions import Fraction
from pathlib import Path

import sympy as sp

from r3_common import R3Error, atomic_json_write, require, sha256, weighted_compositions_3


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")
PRODUCER_PATH = SCRIPT_PATH.with_name("extract_cofactors.py")
VERIFIER_PATH = SCRIPT_PATH.with_name("verify_cofactors.py")
Monomial = tuple[int, int, int]
Sparse = dict[Monomial, Fraction]


def decode(rows: object) -> Sparse:
    require(isinstance(rows, list), "cofactor is not a sparse list")
    answer: Sparse = {}
    for row in rows:
        require(isinstance(row, dict), "cofactor row is not an object")
        exponent = tuple(row["exponents"])
        coefficient = Fraction(row["numerator"], row["denominator"])
        require(exponent not in answer and coefficient, "invalid sparse cofactor row")
        answer[exponent] = coefficient
    return answer


def add(left: Monomial, right: Monomial) -> Monomial:
    return tuple(left[index] + right[index] for index in range(3))


def monomials_of_weight(weight: int) -> list[Monomial]:
    require(weight >= 0, "negative multiplier weight")
    return list(weighted_compositions_3(weight))


def monomial_weight(monomial: Monomial) -> int:
    return monomial[0] + 2 * monomial[1] + 3 * monomial[2]


def verify_component_homogeneity(d: int, components: list[Sparse]) -> None:
    expected = (2 * d, 2 * d - 1, 2 * d - 2)
    for name, polynomial, weight in zip(("A", "B", "C"), components, expected):
        require(polynomial, f"empty {name} cofactor at d={d}")
        require(all(monomial_weight(monomial) == weight for monomial in polynomial),
                f"non-homogeneous {name} cofactor at d={d}")


def row_ansatz(
    source: list[Sparse], target: Sparse, multiplier_weights: list[int]
) -> tuple[list[list[Fraction]], list[Fraction], list[tuple[int, Monomial]]]:
    unknowns = [
        (column, multiplier)
        for column, weight in enumerate(multiplier_weights)
        for multiplier in monomials_of_weight(weight)
    ]
    output_monomials = set(target)
    for column, multiplier in unknowns:
        output_monomials.update(add(multiplier, monomial) for monomial in source[column])
    equations: list[list[Fraction]] = []
    right_hand: list[Fraction] = []
    for output in sorted(output_monomials):
        equations.append([
            source[column].get(
                tuple(output[index] - multiplier[index] for index in range(3)),
                Fraction(0),
            ) if all(output[index] >= multiplier[index] for index in range(3)) else Fraction(0)
            for column, multiplier in unknowns
        ])
        right_hand.append(target.get(output, Fraction(0)))
    return equations, right_hand, unknowns


def rank_fraction(rows: list[list[Fraction]]) -> int:
    matrix = sp.Matrix([
        [sp.Rational(value.numerator, value.denominator) for value in row]
        for row in rows
    ])
    return int(matrix.rank())


def recurrence_screen(cases: dict[int, list[Sparse]]) -> dict[str, object]:
    require(sorted(cases) == list(range(2, 9)),
            "cofactor recurrence screen requires the exact d=2..8 inventory")
    for d, components in cases.items():
        require(len(components) == 3, f"cofactor component inventory changed at d={d}")
        verify_component_homogeneity(d, components)
    component_base = (0, -1, -2)  # component weights are 2d + this offset.
    training = list(range(2, 7))
    holdout = 7
    row_results = []
    all_consistent = True
    for target_row in range(3):
        coefficient_rows: list[list[Fraction]] = []
        right_hand: list[Fraction] = []
        expected_unknowns: list[tuple[int, Monomial]] | None = None
        multiplier_weights = [
            (2 * (2 + 1) + component_base[target_row])
            - (2 * 2 + component_base[source_column])
            for source_column in range(3)
        ]
        for d in training:
            equations, rhs, unknowns = row_ansatz(
                cases[d], cases[d + 1][target_row], multiplier_weights
            )
            if expected_unknowns is None:
                expected_unknowns = unknowns
            require(unknowns == expected_unknowns, "ansatz inventory changed with d")
            coefficient_rows.extend(equations)
            right_hand.extend(rhs)
        coefficient_rank = rank_fraction(coefficient_rows)
        augmented_rank = rank_fraction([
            row + [value] for row, value in zip(coefficient_rows, right_hand)
        ])
        consistent = coefficient_rank == augmented_rank
        all_consistent = all_consistent and consistent
        row_results.append({
            "target_component": ("A", "B", "C")[target_row],
            "multiplier_weights_from_A_B_C": multiplier_weights,
            "unknown_count": len(expected_unknowns or []),
            "equation_count": len(coefficient_rows),
            "coefficient_rank": coefficient_rank,
            "augmented_rank": augmented_rank,
            "consistent_on_training": consistent,
        })
    return {
        "ansatz": (
            "H_(d+1)=M(x)H_d with d-independent entries and each entry assigned "
            "the unique weighted degree forced by component homogeneity"
        ),
        "training_transitions": [[d, d + 1] for d in training],
        "reserved_holdout_transition": [holdout, holdout + 1],
        "row_results": row_results,
        "full_matrix_recurrence_consistent_on_training": all_consistent,
        "holdout_disposition": (
            "candidate must be reconstructed and tested" if all_consistent
            else "reserved and not fit because the ansatz already fails exactly on training"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cofactors", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    input_paths = (args.cofactors, args.verification)
    require(all(path.is_file() for path in input_paths),
            "cofactor recurrence input is absent")
    require(args.out.resolve() not in {path.resolve() for path in input_paths},
            "cofactor recurrence output must not overwrite an input")
    source_paths = (SCRIPT_PATH, COMMON_PATH, PRODUCER_PATH, VERIFIER_PATH)
    startup_sources = {path.name: sha256(path) for path in source_paths}
    startup_inputs = {path.name: sha256(path) for path in input_paths}
    receipt = json.loads(args.cofactors.read_text())
    verification = json.loads(args.verification.read_text())
    require(receipt.get("schema") == "polydegree-r3-x3-cofactors-v1" and
            receipt.get("status") == "PASS", "cofactor receipt is not terminal PASS")
    require(receipt.get("d_min") == 2 and receipt.get("d_max") == 8,
            "cofactor recurrence screen requires d=2..8")
    require(verification.get("status") == "PASS" and
            verification.get("input_sha256") == sha256(args.cofactors),
            "cofactor verification does not bind the input receipt")
    cases: dict[int, list[Sparse]] = {}
    growth = []
    for case in receipt["cases"]:
        d = case["d"]
        decoded = [decode(case["cofactors"][name]) for name in ("A", "B", "C")]
        verify_component_homogeneity(d, decoded)
        cases[d] = decoded
        coefficients = [coefficient for polynomial in decoded for coefficient in polynomial.values()]
        growth.append({
            "d": d,
            "term_counts": case["term_counts"],
            "maximum_numerator_bits": max(abs(value.numerator).bit_length() for value in coefficients),
            "maximum_denominator_bits": max(value.denominator.bit_length() for value in coefficients),
        })
    recurrence = recurrence_screen(cases)
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "cofactor recurrence source changed during the screen")
    require({path.name: sha256(path) for path in input_paths} == startup_inputs,
            "cofactor recurrence input changed during the screen")
    output = {
        "schema": "polydegree-r3-cofactor-recurrence-screen-v1",
        "status": "PASS",
        "claim_boundary": (
            "This exact bounded screen excludes only the displayed d-independent "
            "first-order matrix ansatz; it does not exclude higher-order, periodic, "
            "d-dependent, or differently normalized cofactor recurrences."
        ),
        "inputs_sha256": startup_inputs,
        "cofactor_expression_growth": growth,
        "component_homogeneity_verified": True,
        "recurrence_screen": recurrence,
        "source_sha256": startup_sources,
        "environment": {"python": platform.python_version(), "sympy": sp.__version__},
    }
    atomic_json_write(args.out, output)
    print(json.dumps({
        "status": "PASS",
        "training_consistent": recurrence["full_matrix_recurrence_consistent_on_training"],
    }, sort_keys=True))
    print("cofactor recurrence screen:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 COFACTOR RECURRENCE SCREEN FAILED: {exc}")
        raise SystemExit(1)
