#!/usr/bin/env python3
"""Independently verify rational R(3) radical certificates and invariants."""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import platform
from fractions import Fraction
from pathlib import Path

import sympy as sp

from r3_common import R3Error, atomic_json_write, bezout_colength, require, sha256
from verify_colength import verify_receipt


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
PRODUCER_PATH = BASE / "extract_rational_radical_certificates.py"
COMMON_PATH = BASE / "r3_common.py"
MAP_PRODUCER_PATH = BASE / "modular_colength.py"
MAP_VERIFIER_PATH = BASE / "verify_colength.py"
SOURCE_PATHS = (
    SCRIPT_PATH,
    PRODUCER_PATH,
    COMMON_PATH,
    MAP_PRODUCER_PATH,
    MAP_VERIFIER_PATH,
)
Monomial = tuple[int, int, int]
Sparse = dict[Monomial, Fraction]
WEIGHTS = (1, 2, 3)


def remove_timing(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: remove_timing(item)
            for key, item in value.items()
            if key != "elapsed_seconds"
        }
    if isinstance(value, list):
        return [remove_timing(item) for item in value]
    return value


def weighted_monomials(total: int) -> list[Monomial]:
    require(total >= 0, "weighted degree must be nonnegative")
    answer = []
    for a3 in range(total // 3 + 1):
        remainder = total - 3 * a3
        for a2 in range(remainder // 2 + 1):
            answer.append((remainder - 2 * a2, a2, a3))
    return answer


def monomial_weight(monomial: Monomial) -> int:
    return sum(weight * exponent for weight, exponent in zip(WEIGHTS, monomial))


def add(left: Sparse, right: Sparse) -> Sparse:
    answer = dict(left)
    for monomial, coefficient in right.items():
        value = answer.get(monomial, Fraction(0)) + coefficient
        if value:
            answer[monomial] = value
        else:
            answer.pop(monomial, None)
    return answer


def scale(polynomial: Sparse, scalar: Fraction) -> Sparse:
    return {monomial: coefficient * scalar for monomial, coefficient in polynomial.items()
            if coefficient * scalar}


def multiply(left: Sparse, right: Sparse) -> Sparse:
    answer: Sparse = {}
    for a, ca in left.items():
        for b, cb in right.items():
            monomial = tuple(x + y for x, y in zip(a, b))
            answer = add(answer, {monomial: ca * cb})
    return answer


def derivative(polynomial: Sparse, variable: int) -> Sparse:
    answer: Sparse = {}
    for monomial, coefficient in polynomial.items():
        exponent = monomial[variable]
        if exponent:
            target = list(monomial)
            target[variable] -= 1
            answer[tuple(target)] = coefficient * exponent
    return answer


def decode(rows: object) -> Sparse:
    require(isinstance(rows, list), "sparse polynomial is not a list")
    answer: Sparse = {}
    previous: Monomial | None = None
    for row in rows:
        require(isinstance(row, dict) and set(row) == {
            "exponents", "numerator", "denominator"
        }, "malformed rational sparse row")
        exponents = row["exponents"]
        numerator = row["numerator"]
        denominator = row["denominator"]
        require(
            isinstance(exponents, list)
            and len(exponents) == 3
            and all(isinstance(value, int) and value >= 0 for value in exponents),
            "invalid sparse exponents",
        )
        require(isinstance(numerator, int) and isinstance(denominator, int)
                and denominator > 0, "invalid rational coefficient")
        monomial = tuple(exponents)
        require(monomial not in answer, "duplicate sparse monomial")
        if previous is not None:
            require(previous > monomial, "sparse rows are not in descending monomial order")
        previous = monomial
        coefficient = Fraction(numerator, denominator)
        require(coefficient != 0, "zero sparse coefficient")
        answer[monomial] = coefficient
    return answer


def encode(polynomial: Sparse) -> list[dict[str, object]]:
    return [
        {
            "exponents": list(monomial),
            "numerator": coefficient.numerator,
            "denominator": coefficient.denominator,
        }
        for monomial, coefficient in sorted(polynomial.items(), reverse=True)
    ]


def independent_generators(max_n: int) -> dict[int, Sparse]:
    """Revert H(t) sparsely, without the multinomial coefficient formula."""
    require(max_n >= 0, "max_n must be nonnegative")
    unit: Sparse = {(0, 0, 0): Fraction(1)}
    variables: list[Sparse] = [
        {(1, 0, 0): Fraction(1)},
        {(0, 1, 0): Fraction(1)},
        {(0, 0, 1): Fraction(1)},
    ]
    series: dict[int, Sparse] = {1: unit}

    def power_coefficient(power: int, total: int) -> Sparse:
        partial: dict[int, Sparse] = {0: unit}
        for _ in range(power):
            next_partial: dict[int, Sparse] = {}
            for subtotal, left in partial.items():
                for degree, right in series.items():
                    combined_degree = subtotal + degree
                    if combined_degree <= total:
                        product = multiply(left, right)
                        next_partial[combined_degree] = add(
                            next_partial.get(combined_degree, {}), product
                        )
            partial = next_partial
        return partial.get(total, {})

    for coefficient_index in range(2, max_n + 2):
        nonlinear = sum_polynomials(
            [
                multiply(variables[power - 2], power_coefficient(power, coefficient_index))
                for power in range(2, 5)
            ]
        )
        series[coefficient_index] = scale(nonlinear, Fraction(-1))
    answer = {n: series[n + 1] for n in range(max_n + 1)}
    for n, polynomial in answer.items():
        require(polynomial, f"independently reconstructed g_{n} is empty")
        require(all(monomial_weight(monomial) == n for monomial in polynomial),
                f"independently reconstructed g_{n} is not weighted homogeneous")
    return answer


def row_vector(polynomial: Sparse, columns: list[Monomial]) -> list[sp.Rational]:
    column_set = set(columns)
    require(set(polynomial) <= column_set, "polynomial contains a wrong-weight monomial")
    return [sp.Rational(polynomial.get(monomial, 0).numerator,
                        polynomial.get(monomial, 0).denominator)
            for monomial in columns]


def ideal_rows(generators: list[Sparse], degrees: list[int], weight: int,
               columns: list[Monomial]) -> list[list[sp.Rational]]:
    rows = []
    for generator, degree in zip(generators, degrees, strict=True):
        if weight < degree:
            continue
        for multiplier in weighted_monomials(weight - degree):
            product = multiply({multiplier: Fraction(1)}, generator)
            rows.append(row_vector(product, columns))
    return rows


def quotient_reduction(
    polynomial: Sparse, columns: list[Monomial], rref: sp.Matrix, pivots: tuple[int, ...]
) -> tuple[sp.Rational, ...]:
    vector = sp.Matrix([row_vector(polynomial, columns)])
    for row_index, pivot in enumerate(pivots):
        coefficient = vector[0, pivot]
        if coefficient:
            vector -= coefficient * rref[row_index, :]
    return tuple(vector[0, index] for index in range(len(columns)))


def quotient_data(generators: list[Sparse], degrees: list[int], weight: int) -> dict[str, object]:
    columns = weighted_monomials(weight)
    rows = ideal_rows(generators, degrees, weight, columns)
    matrix = sp.Matrix(rows) if rows else sp.zeros(0, len(columns))
    rref, pivots = matrix.rref()
    return {
        "columns": columns,
        "rref": rref,
        "pivots": pivots,
        "dimension": len(columns) - len(pivots),
    }


def hilbert_complete_intersection(d: int, limit: int) -> list[int]:
    base = [len(weighted_monomials(weight)) for weight in range(limit + 1)]
    result = base
    for degree in (d, d + 1, d + 2):
        result = [
            result[weight] - (result[weight - degree] if weight >= degree else 0)
            for weight in range(limit + 1)
        ]
    return result


def determinant_3(matrix: list[list[Sparse]]) -> Sparse:
    answer: Sparse = {}
    for permutation in itertools.permutations(range(3)):
        inversions = sum(
            permutation[i] > permutation[j] for i in range(3) for j in range(i + 1, 3)
        )
        term: Sparse = {(0, 0, 0): Fraction(-1 if inversions % 2 else 1)}
        for row, column in enumerate(permutation):
            term = multiply(term, matrix[row][column])
        answer = add(answer, term)
    return answer


def minor_2(matrix: list[list[Sparse]], removed_row: int, removed_column: int) -> Sparse:
    rows = [row for row in range(3) if row != removed_row]
    columns = [column for column in range(3) if column != removed_column]
    return add(
        multiply(matrix[rows[0]][columns[0]], matrix[rows[1]][columns[1]]),
        scale(multiply(matrix[rows[0]][columns[1]], matrix[rows[1]][columns[0]]), Fraction(-1)),
    )


def adjugate_3(matrix: list[list[Sparse]]) -> list[list[Sparse]]:
    answer = [[{} for _ in range(3)] for _ in range(3)]
    for row in range(3):
        for column in range(3):
            cofactor = minor_2(matrix, row, column)
            if (row + column) % 2:
                cofactor = scale(cofactor, Fraction(-1))
            answer[column][row] = cofactor
    return answer


def matrix_vector(matrix: list[list[Sparse]], vector: list[Sparse]) -> list[Sparse]:
    return [
        sum_polynomials([multiply(matrix[row][column], vector[column]) for column in range(3)])
        for row in range(3)
    ]


def sum_polynomials(polynomials: list[Sparse]) -> Sparse:
    answer: Sparse = {}
    for polynomial in polynomials:
        answer = add(answer, polynomial)
    return answer


def rational_value(value: sp.Rational) -> dict[str, int]:
    return {"numerator": int(value.p), "denominator": int(value.q)}


def verify_map_binding(
    modular_map: dict[str, object], verification: dict[str, object], map_path: Path,
    singular: Path, expected_prime_max: int
) -> dict[str, object]:
    parameters = modular_map.get("parameters")
    require(isinstance(parameters, dict), "modular map lacks parameters")
    d_min = parameters.get("d_min")
    d_max = parameters.get("d_max")
    require(isinstance(d_min, int) and isinstance(d_max, int), "map range is malformed")
    summary = verify_receipt(modular_map, d_min, d_max, expected_prime_max, True, singular)
    require(
        verification.get("schema") == "polydegree-r3-modular-colength-verification-v1"
        and verification.get("status") == "PASS",
        "modular map verification is not terminal PASS",
    )
    require(verification.get("input_sha256") == sha256(map_path),
            "modular map verification binds another input")
    require(verification.get("summary") == summary, "modular map verification summary mismatch")
    return summary


def verify_case(case: object, expected_d: int, generators_by_n: dict[int, Sparse],
                map_rows: dict[tuple[int, int], str], primes: list[int]) -> dict[str, object]:
    require(isinstance(case, dict), "certificate case is not an object")
    require(case.get("d") == expected_d, "certificate degree mismatch")
    d = expected_d
    socle = 3 * d - 3
    require(case.get("socle_weight") == socle, "socle weight mismatch")
    require(case.get("expected_colength") == bezout_colength(d), "colength field mismatch")
    require(case.get("singular_remainders_zero") is True,
            "producer did not record zero lift remainders")
    require(case.get("producer_lower_remainders_nonzero") is True,
            "producer lower-remainder diagnostic is absent")
    generators = [generators_by_n[d + offset] for offset in range(3)]
    degrees = [d, d + 1, d + 2]
    expected_exponents = [socle + 1, socle // 2 + 1, socle // 3 + 1]
    targets = case.get("targets")
    require(isinstance(targets, list) and len(targets) == 3,
            "certificate must have exactly three targets")
    denominator_values: list[int] = []
    mutation_rejected = False
    exact_targets = []
    quotient_cache: dict[int, dict[str, object]] = {}

    def qdata(weight: int) -> dict[str, object]:
        if weight not in quotient_cache:
            quotient_cache[weight] = quotient_data(generators, degrees, weight)
        return quotient_cache[weight]

    for axis, target in enumerate(targets):
        require(isinstance(target, dict) and set(target) == {
            "variable", "exponent", "cofactors", "producer_lower_remainder"
        }, "malformed target object")
        exponent = expected_exponents[axis]
        require(target["variable"] == f"x{axis + 1}" and target["exponent"] == exponent,
                "target variable or exponent mismatch")
        raw_cofactors = target["cofactors"]
        require(isinstance(raw_cofactors, list) and len(raw_cofactors) == 3,
                "target cofactor inventory mismatch")
        cofactors = [decode(rows) for rows in raw_cofactors]
        for rows in raw_cofactors:
            denominator_values.extend(row["denominator"] for row in rows)
        reconstructed = sum_polynomials(
            [multiply(cofactor, generator) for cofactor, generator in zip(cofactors, generators, strict=True)]
        )
        target_monomial = [0, 0, 0]
        target_monomial[axis] = exponent
        expected = {tuple(target_monomial): Fraction(1)}
        require(reconstructed == expected, f"exact rational identity failed at d={d}, axis={axis + 1}")
        upper_weight = WEIGHTS[axis] * exponent
        upper_data = qdata(upper_weight)
        upper_reduction = quotient_reduction(
            expected, upper_data["columns"], upper_data["rref"], upper_data["pivots"]
        )
        require(not any(upper_reduction), "upper target is not in the exact Macaulay span")
        lower_monomial = list(target_monomial)
        lower_monomial[axis] -= 1
        lower = {tuple(lower_monomial): Fraction(1)}
        lower_weight = upper_weight - WEIGHTS[axis]
        lower_data = qdata(lower_weight)
        lower_reduction = quotient_reduction(
            lower, lower_data["columns"], lower_data["rref"], lower_data["pivots"]
        )
        require(any(lower_reduction), "one-lower target unexpectedly lies in the ideal")
        producer_lower = decode(target["producer_lower_remainder"])
        require(producer_lower, "producer stored a zero lower remainder")
        if not mutation_rejected:
            mutated = [dict(cofactor) for cofactor in cofactors]
            selected = next(iter(mutated[0]))
            mutated[0][selected] += 1
            mutation_rejected = sum_polynomials(
                [multiply(cofactor, generator)
                 for cofactor, generator in zip(mutated, generators, strict=True)]
            ) != expected
        exact_targets.append(
            {
                "variable": f"x{axis + 1}",
                "exponent": exponent,
                "cofactor_term_counts": [len(cofactor) for cofactor in cofactors],
                "upper_membership": True,
                "one_lower_nonmembership": True,
                "lower_weight": lower_weight,
            }
        )
    require(mutation_rejected, "cofactor mutation was not rejected")

    hilbert_limit = socle + 3
    expected_hilbert = hilbert_complete_intersection(d, hilbert_limit)
    observed_hilbert = [qdata(weight)["dimension"] for weight in range(hilbert_limit + 1)]
    require(observed_hilbert == expected_hilbert, "exact weighted Hilbert function mismatch")
    require(sum(observed_hilbert) == bezout_colength(d), "exact colength mismatch")
    require(observed_hilbert[socle] == 1 and observed_hilbert[socle + 1:] == [0, 0, 0],
            "socle endpoint or vanishing tail mismatch")

    euler_matrix: list[list[Sparse]] = []
    variables = [{(1, 0, 0): Fraction(1)}, {(0, 1, 0): Fraction(1)},
                 {(0, 0, 1): Fraction(1)}]
    for degree, generator in zip(degrees, generators, strict=True):
        row = [
            scale(derivative(generator, axis), Fraction(WEIGHTS[axis], degree))
            for axis in range(3)
        ]
        require(sum_polynomials([multiply(entry, variables[axis]) for axis, entry in enumerate(row)])
                == generator, "weighted Euler decomposition failed")
        euler_matrix.append(row)
    determinant = determinant_3(euler_matrix)
    require(determinant and all(monomial_weight(monomial) == socle for monomial in determinant),
            "Euler-Jacobian determinant has wrong weight")
    socle_data = qdata(socle)
    determinant_reduction = quotient_reduction(
        determinant, socle_data["columns"], socle_data["rref"], socle_data["pivots"]
    )
    require(any(determinant_reduction), "Euler-Jacobian determinant vanishes in the quotient")
    adjugate = adjugate_3(euler_matrix)
    adjugate_times_g = matrix_vector(adjugate, generators)
    determinant_times_x = [multiply(determinant, variable) for variable in variables]
    require(adjugate_times_g == determinant_times_x, "adjugate identity failed")

    socle_scalars = []
    for axis, exponent in enumerate(expected_exponents):
        lower_exponent = exponent - 1
        if WEIGHTS[axis] * lower_exponent != socle:
            continue
        target_monomial = [0, 0, 0]
        target_monomial[axis] = lower_exponent
        target_reduction = quotient_reduction(
            {tuple(target_monomial): Fraction(1)}, socle_data["columns"],
            socle_data["rref"], socle_data["pivots"]
        )
        nonzero_positions = [index for index, value in enumerate(determinant_reduction) if value]
        require(nonzero_positions, "determinant has no quotient coordinate")
        pivot = nonzero_positions[0]
        scalar = target_reduction[pivot] / determinant_reduction[pivot]
        require(tuple(scalar * value for value in determinant_reduction) == target_reduction,
                "top monomial is not a scalar multiple of the determinant class")
        require(scalar != 0, "socle scalar unexpectedly vanished")
        socle_scalars.append({
            "variable": f"x{axis + 1}",
            "exponent": lower_exponent,
            "scalar_times_euler_determinant": rational_value(scalar),
        })

    dividing_primes = [prime for prime in primes
                       if any(denominator % prime == 0 for denominator in denominator_values)]
    denominator_classification = [
        {"prime": prime, "classification": map_rows[(d, prime)]}
        for prime in dividing_primes if (d, prime) in map_rows
    ]
    good_conflicts = [row["prime"] for row in denominator_classification
                      if row["classification"] == "GOOD"]
    return {
        "d": d,
        "expected_colength": bezout_colength(d),
        "hilbert_function": observed_hilbert,
        "targets": exact_targets,
        "cofactor_mutation_rejected": mutation_rejected,
        "euler_jacobian": {
            "determinant": encode(determinant),
            "weighted_degree": socle,
            "nonzero_socle_class": True,
            "adjugate_identity": True,
            "socle_scalars": socle_scalars,
        },
        "denominator_support_within_map": {
            "dividing_primes": denominator_classification,
            "good_prime_conflicts": good_conflicts,
            "claim_boundary": "diagnostic only; arbitrary lift denominators need not be intrinsic",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--map-verification", type=Path, required=True)
    parser.add_argument("--expected-d-min", type=int, default=2)
    parser.add_argument("--expected-d-max", type=int, default=8)
    parser.add_argument("--expected-prime-max", type=int, default=997)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    input_path = args.input.resolve()
    peer_path = args.peer.resolve()
    map_path = args.map.resolve()
    map_verification_path = args.map_verification.resolve()
    singular = args.singular.resolve()
    output = args.out.resolve()
    watched_paths = (input_path, peer_path, map_path, map_verification_path, singular)
    require(all(path.is_file() for path in watched_paths), "one or more verifier inputs are absent")
    require(output not in {*watched_paths, *SOURCE_PATHS}, "output overwrites an input or source")
    require(not output.exists(), "refusing to overwrite an existing output")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {str(path): sha256(path) for path in watched_paths}
    receipt = json.loads(input_path.read_text())
    peer = json.loads(peer_path.read_text())
    modular_map = json.loads(map_path.read_text())
    map_verification = json.loads(map_verification_path.read_text())
    require(remove_timing(copy.deepcopy(receipt)) == remove_timing(copy.deepcopy(peer)),
            "ordinary and optimized rational certificate receipts differ outside timing")
    require(
        receipt.get("schema") == "polydegree-r3-rational-radical-certificates-v1"
        and receipt.get("status") == "PASS",
        "rational certificate receipt is not terminal PASS",
    )
    require(receipt.get("d_min") == args.expected_d_min
            and receipt.get("d_max") == args.expected_d_max, "certificate range mismatch")
    producer_sources = receipt.get("source_sha256")
    require(isinstance(producer_sources, dict), "producer source bindings are absent")
    require(producer_sources.get(PRODUCER_PATH.name) == sha256(PRODUCER_PATH)
            and producer_sources.get(COMMON_PATH.name) == sha256(COMMON_PATH),
            "producer source bindings are stale")
    producer_runtime = receipt.get("runtime_sha256")
    require(isinstance(producer_runtime, dict)
            and producer_runtime.get(str(singular)) == sha256(singular),
            "producer Singular binding is stale")
    map_summary = verify_map_binding(
        modular_map, map_verification, map_path, singular, args.expected_prime_max
    )
    parameters = modular_map["parameters"]
    primes = parameters["primes"]
    map_rows = {(row["d"], row["prime"]): row["classification"] for row in modular_map["rows"]}
    generators = independent_generators(args.expected_d_max + 2)
    cases = receipt.get("cases")
    require(isinstance(cases, list)
            and [case.get("d") for case in cases]
            == list(range(args.expected_d_min, args.expected_d_max + 1)),
            "certificate case inventory mismatch")
    verified = [
        verify_case(case, d, generators, map_rows, primes)
        for d, case in zip(range(args.expected_d_min, args.expected_d_max + 1), cases, strict=True)
    ]
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "verifier source changed during execution")
    require({str(path): sha256(path) for path in watched_paths} == startup_inputs,
            "verifier input or runtime changed during execution")
    output_receipt = {
        "schema": "polydegree-r3-rational-radical-verification-v1",
        "status": "PASS",
        "claim_boundary": (
            "Independent formal reversion, exact sparse expansion, weighted Macaulay "
            "linear algebra, and Euler-Jacobian socle checks for the displayed finite "
            "degrees only; no all-degree R(3) claim is made."
        ),
        "d_min": args.expected_d_min,
        "d_max": args.expected_d_max,
        "formula_independence": {
            "method": "direct sparse compositional reversion over ZZ",
            "checked_n": list(range(args.expected_d_max + 3)),
            "weighted_homogeneity": True,
        },
        "ordinary_optimized_timing_free_parity": True,
        "map_summary": map_summary,
        "verified": verified,
        "inputs_sha256": {path.name: startup_inputs[str(path)] for path in watched_paths[:-1]},
        "runtime_sha256": {singular.name: startup_inputs[str(singular)]},
        "source_sha256": startup_sources,
        "environment": {"python": platform.python_version(), "sympy": sp.__version__},
    }
    atomic_json_write(output, output_receipt)
    print(json.dumps({"status": "PASS", "verified": len(verified)}, sort_keys=True))
    print("rational radical verification:", output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError, ValueError) as exc:
        print(f"R3 RATIONAL RADICAL VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
