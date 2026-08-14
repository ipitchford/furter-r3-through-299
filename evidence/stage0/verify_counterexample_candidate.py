#!/usr/bin/env python3
"""Exact acceptance gate for reconstructed algebraic R(3) counterexamples."""

from __future__ import annotations

import argparse
import json
import platform
from fractions import Fraction
from pathlib import Path

import sympy as sp

from r3_common import R3Error, atomic_json_write, g_terms, require, sha256


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")
Polynomial = tuple[Fraction, ...]


def trim(values: list[Fraction] | tuple[Fraction, ...]) -> Polynomial:
    result = list(values)
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return tuple(result or [Fraction(0)])


def parse_scalar(value: object) -> Fraction:
    require(isinstance(value, (int, str)) and not isinstance(value, bool),
            "field coefficients must be integers or rational strings")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise R3Error(f"invalid rational coefficient: {value}") from exc


def parse_polynomial(value: object) -> Polynomial:
    require(isinstance(value, list) and value, "polynomial encoding must be a nonempty list")
    return trim([parse_scalar(coefficient) for coefficient in value])


def reduce_mod(value: Polynomial, modulus: Polynomial) -> Polynomial:
    require(len(modulus) >= 2 and modulus[-1] == 1, "modulus must be monic of positive degree")
    result = list(trim(value))
    degree = len(modulus) - 1
    while len(result) - 1 >= degree:
        factor = result[-1]
        shift = len(result) - len(modulus)
        if factor:
            for index, coefficient in enumerate(modulus):
                result[shift + index] -= factor * coefficient
        result = list(trim(result))
    return trim(result)


def add(left: Polynomial, right: Polynomial, modulus: Polynomial) -> Polynomial:
    size = max(len(left), len(right))
    values = [Fraction(0) for _ in range(size)]
    for index, coefficient in enumerate(left):
        values[index] += coefficient
    for index, coefficient in enumerate(right):
        values[index] += coefficient
    return reduce_mod(trim(values), modulus)


def multiply(left: Polynomial, right: Polynomial, modulus: Polynomial) -> Polynomial:
    values = [Fraction(0) for _ in range(len(left) + len(right) - 1)]
    for left_index, left_coefficient in enumerate(left):
        for right_index, right_coefficient in enumerate(right):
            values[left_index + right_index] += left_coefficient * right_coefficient
    return reduce_mod(trim(values), modulus)


def power(value: Polynomial, exponent: int, modulus: Polynomial) -> Polynomial:
    require(exponent >= 0, "negative exponents are not supported")
    result: Polynomial = (Fraction(1),)
    base = reduce_mod(value, modulus)
    remaining = exponent
    while remaining:
        if remaining & 1:
            result = multiply(result, base, modulus)
        remaining //= 2
        if remaining:
            base = multiply(base, base, modulus)
    return result


def require_irreducible_modulus(modulus: Polynomial) -> None:
    require(len(modulus) >= 2 and modulus[-1] == 1, "minimal polynomial must be monic")
    alpha = sp.Symbol("alpha")
    expression = sum(
        sp.Rational(coefficient.numerator, coefficient.denominator) * alpha**index
        for index, coefficient in enumerate(modulus)
    )
    polynomial = sp.Poly(expression, alpha, domain=sp.QQ)
    require(polynomial.degree() >= 1 and polynomial.is_irreducible,
            "minimal polynomial is not irreducible over Q")


def evaluate_g(
    n: int, coordinates: tuple[Polynomial, Polynomial, Polynomial], modulus: Polynomial
) -> Polynomial:
    total: Polynomial = (Fraction(0),)
    for exponents, coefficient in g_terms(n):
        term: Polynomial = (Fraction(coefficient),)
        for coordinate, exponent in zip(coordinates, exponents, strict=True):
            term = multiply(term, power(coordinate, exponent, modulus), modulus)
        total = add(total, term, modulus)
    return reduce_mod(total, modulus)


def validate_candidate(
    candidate: dict[str, object], allowed_degrees: set[int]
) -> dict[str, object]:
    require(
        candidate.get("schema") == "polydegree-r3-algebraic-counterexample-candidate-v1",
        "wrong counterexample-candidate schema",
    )
    d = candidate.get("d")
    require(isinstance(d, int) and d in allowed_degrees,
            "candidate degree is not in the exact escalation queue")
    field = candidate.get("number_field")
    require(isinstance(field, dict), "candidate lacks a number-field encoding")
    modulus = parse_polynomial(field.get("minimal_polynomial"))
    require_irreducible_modulus(modulus)
    coordinate_encoding = candidate.get("coordinates")
    require(isinstance(coordinate_encoding, dict) and set(coordinate_encoding) == {"x1", "x2", "x3"},
            "candidate coordinate inventory must be exactly x1,x2,x3")
    coordinates = tuple(
        reduce_mod(parse_polynomial(coordinate_encoding[name]), modulus)
        for name in ("x1", "x2", "x3")
    )
    require(any(coordinate != (Fraction(0),) for coordinate in coordinates),
            "all-zero coordinates do not define a projective point")
    residuals = [evaluate_g(d + offset, coordinates, modulus) for offset in range(3)]
    require(all(residual == (Fraction(0),) for residual in residuals),
            "candidate fails exact polynomial evaluation")
    mutated = add(residuals[0], (Fraction(1),), modulus)
    require(mutated != (Fraction(0),), "residual mutation negative control failed")
    return {
        "d": d,
        "number_field_degree": len(modulus) - 1,
        "projective_nonzero": True,
        "exact_zero_residuals": [True, True, True],
        "residual_mutation_rejected": True,
    }


def self_test() -> dict[str, bool]:
    allowed = {2}
    nonsolution = {
        "schema": "polydegree-r3-algebraic-counterexample-candidate-v1",
        "d": 2,
        "number_field": {"minimal_polynomial": ["0", "1"]},
        "coordinates": {"x1": ["1"], "x2": ["0"], "x3": ["0"]},
    }
    all_zero = json.loads(json.dumps(nonsolution))
    all_zero["coordinates"]["x1"] = ["0"]
    reducible = json.loads(json.dumps(nonsolution))
    reducible["number_field"]["minimal_polynomial"] = ["-1", "0", "1"]
    wrong_degree = json.loads(json.dumps(nonsolution))
    wrong_degree["d"] = 3
    outcomes = {}
    for name, candidate in (
        ("non_solution_rejected", nonsolution),
        ("all_zero_rejected", all_zero),
        ("reducible_field_rejected", reducible),
        ("non_escalated_degree_rejected", wrong_degree),
    ):
        rejected = False
        try:
            validate_candidate(candidate, allowed)
        except R3Error:
            rejected = True
        require(rejected, f"self-test failed: {name}")
        outcomes[name] = rejected

    # Positive arithmetic control in Q(i) = Q[alpha]/(alpha^2 + 1).  This is
    # deliberately not passed through validate_candidate: the origin is useful
    # for checking exact evaluation, but it is not a projective point.
    gaussian_modulus = (Fraction(1), Fraction(0), Fraction(1))
    alpha = (Fraction(0), Fraction(1))
    require_irreducible_modulus(gaussian_modulus)
    require(
        multiply(alpha, alpha, gaussian_modulus) == (Fraction(-1),),
        "Q(i) multiplication control failed",
    )
    require(
        power(alpha, 4, gaussian_modulus) == (Fraction(1),),
        "Q(i) exponentiation control failed",
    )
    origin = ((Fraction(0),),) * 3
    require(
        all(evaluate_g(n, origin, gaussian_modulus) == (Fraction(0),)
            for n in range(2, 5)),
        "Q(i) exact-evaluation control failed",
    )
    outcomes["gaussian_field_arithmetic_checked"] = True
    outcomes["exact_origin_evaluation_checked"] = True
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        require(args.candidate is None and args.queue is None and args.out is None,
                "--self-test cannot be combined with candidate inputs")
        print(json.dumps({"status": "PASS", **self_test()}, sort_keys=True))
        return 0
    require(args.candidate is not None and args.queue is not None and args.out is not None,
            "candidate mode requires --candidate, --queue, and --out")
    candidate_path = args.candidate.resolve()
    queue_path = args.queue.resolve()
    output_path = args.out.resolve()
    require(candidate_path.is_file() and queue_path.is_file(), "candidate or queue input is absent")
    require(output_path not in {candidate_path, queue_path}, "output overwrites an input")
    source_paths = (SCRIPT_PATH, COMMON_PATH)
    watched_paths = (candidate_path, queue_path)
    startup_sources = {path.name: sha256(path) for path in source_paths}
    startup_inputs = {path.name: sha256(path) for path in watched_paths}
    candidate = json.loads(candidate_path.read_text())
    queue = json.loads(queue_path.read_text())
    require(queue.get("schema") == "polydegree-r3-falsification-queue-v1",
            "wrong escalation-queue schema")
    require(queue.get("status") == "ESCALATION_REQUIRED",
            "candidate acceptance requires a terminal escalation queue")
    unresolved = queue.get("unresolved_degrees")
    require(isinstance(unresolved, list) and unresolved, "escalation queue has no unresolved degrees")
    require(all(isinstance(d, int) for d in unresolved), "invalid unresolved-degree inventory")
    verification = validate_candidate(candidate, set(unresolved))
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "counterexample verifier source changed during execution")
    require({path.name: sha256(path) for path in watched_paths} == startup_inputs,
            "counterexample verifier input changed during execution")
    output = {
        "schema": "polydegree-r3-algebraic-counterexample-verification-v1",
        "status": "COUNTEREXAMPLE_EXACTLY_VERIFIED",
        "claim_boundary": (
            "This receipt accepts only the encoded algebraic point and degree after exact "
            "number-field evaluation. Any broader conjectural consequence requires the "
            "separate implication dictionary."
        ),
        "verification": verification,
        "inputs_sha256": startup_inputs,
        "source_sha256": startup_sources,
        "environment": {"python": platform.python_version(), "sympy": sp.__version__},
    }
    atomic_json_write(output_path, output)
    print(json.dumps({"status": output["status"], **verification}, sort_keys=True))
    print("counterexample verification receipt:", output_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 COUNTEREXAMPLE VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
