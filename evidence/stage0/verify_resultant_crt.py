#!/usr/bin/env python3
"""Independent verifier for modular-determinant/CRT R(3) resultants."""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from pathlib import Path

import flint
from flint import fmpz_mat, nmod_mat

from r3_common import R3Error, atomic_json_write, require, sha256, sha256_bytes


sys.set_int_max_str_digits(0)

SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
PRODUCER_PATH = BASE / "cover_resultant_crt.py"
EXACT_PRODUCER_PATH = BASE / "cover_resultant.py"
COMMON_PATH = BASE / "r3_common.py"
MILLER_RABIN_BASES_64 = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
ZERO_EXPONENT = (0, 0, 0)
INVERSE_SERIES: dict[int, dict[tuple[int, int, int], int]] = {
    1: {ZERO_EXPONENT: 1}
}


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


def projection_sha256(receipt: dict[str, object]) -> str:
    encoded = json.dumps(
        remove_timing(receipt), sort_keys=True, separators=(",", ":")
    ).encode()
    return sha256_bytes(encoded)


def multiply_polynomials(
    left: dict[tuple[int, int, int], int],
    right: dict[tuple[int, int, int], int],
) -> dict[tuple[int, int, int], int]:
    output: dict[tuple[int, int, int], int] = {}
    for left_exp, left_coefficient in left.items():
        for right_exp, right_coefficient in right.items():
            exponent = tuple(left_exp[index] + right_exp[index] for index in range(3))
            output[exponent] = output.get(exponent, 0) + left_coefficient * right_coefficient
    return {exponent: coefficient for exponent, coefficient in output.items() if coefficient}


def power_series_coefficient(
    series: dict[int, dict[tuple[int, int, int], int]],
    power: int,
    target: int,
) -> dict[tuple[int, int, int], int]:
    coefficients: dict[int, dict[tuple[int, int, int], int]] = {
        0: {ZERO_EXPONENT: 1}
    }
    for _ in range(power):
        next_coefficients: dict[int, dict[tuple[int, int, int], int]] = {}
        for left_degree, left_polynomial in coefficients.items():
            for right_degree, right_polynomial in series.items():
                degree = left_degree + right_degree
                if degree > target:
                    continue
                product = multiply_polynomials(left_polynomial, right_polynomial)
                accumulator = next_coefficients.setdefault(degree, {})
                for exponent, coefficient in product.items():
                    accumulator[exponent] = accumulator.get(exponent, 0) + coefficient
        coefficients = next_coefficients
    return {
        exponent: coefficient
        for exponent, coefficient in coefficients.get(target, {}).items()
        if coefficient
    }


def independent_g_terms(n: int) -> tuple[tuple[tuple[int, int, int], int], ...]:
    """Recover g_n by sparse formal reversion, not the producer's closed formula."""
    require(n >= 0, "independent coefficient index must be nonnegative")
    target = n + 1
    while max(INVERSE_SERIES) < target:
        degree = max(INVERSE_SERIES) + 1
        coefficient: dict[tuple[int, int, int], int] = {}
        for variable, power in enumerate((2, 3, 4)):
            for exponent, value in power_series_coefficient(
                INVERSE_SERIES, power, degree
            ).items():
                shifted = list(exponent)
                shifted[variable] += 1
                key = tuple(shifted)
                coefficient[key] = coefficient.get(key, 0) - value
        INVERSE_SERIES[degree] = {
            exponent: value for exponent, value in coefficient.items() if value
        }
        require(INVERSE_SERIES[degree],
                f"independent formal reversion produced no coefficient at {degree}")
    return tuple(sorted(INVERSE_SERIES[target].items()))


def is_prime_64(value: int) -> bool:
    require(isinstance(value, int) and 0 <= value < 2**64,
            "CRT prime is outside the 64-bit contract")
    if value < 2:
        return False
    for prime in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if value % prime == 0:
            return value == prime
    odd = value - 1
    power = 0
    while odd % 2 == 0:
        odd //= 2
        power += 1
    for base in MILLER_RABIN_BASES_64:
        if base % value == 0:
            continue
        witness = pow(base, odd, value)
        if witness in (1, value - 1):
            continue
        for _ in range(power - 1):
            witness = witness * witness % value
            if witness == value - 1:
                break
        else:
            return False
    return True


def standard_monomials(degree: int) -> list[tuple[int, int, int]]:
    if degree < 0:
        return []
    return [
        (degree - second - third, second, third)
        for third in range(degree + 1)
        for second in range(degree - third + 1)
    ]


def add(left: tuple[int, int, int], right: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(left[index] + right[index] for index in range(3))


def independent_maps(d: int) -> tuple[fmpz_mat, fmpz_mat, dict[str, int]]:
    degrees = (d, d + 1, d + 2)
    strand = sum(degrees) - 2
    forms = [
        [((a1, 2 * a2, 3 * a3), coefficient)
         for (a1, a2, a3), coefficient in independent_g_terms(degree)]
        for degree in degrees
    ]
    k0 = standard_monomials(strand)
    k0_index = {monomial: index for index, monomial in enumerate(k0)}
    k1 = [
        (component, monomial)
        for component, degree in enumerate(degrees)
        for monomial in standard_monomials(strand - degree)
    ]
    k1_index = {basis: index for index, basis in enumerate(k1)}
    first = [[0] * len(k1) for _ in k0]
    for column, (component, multiplier) in enumerate(k1):
        for exponent, coefficient in forms[component]:
            first[k0_index[add(multiplier, exponent)]][column] += coefficient
    pairs = ((0, 1), (0, 2), (1, 2))
    k2 = [
        ((left, right), monomial)
        for left, right in pairs
        for monomial in standard_monomials(strand - degrees[left] - degrees[right])
    ]
    second = [[0] * len(k2) for _ in k1]
    for column, ((left, right), multiplier) in enumerate(k2):
        for exponent, coefficient in forms[left]:
            second[k1_index[(right, add(multiplier, exponent))]][column] += coefficient
        for exponent, coefficient in forms[right]:
            second[k1_index[(left, add(multiplier, exponent))]][column] -= coefficient
    dimensions = {"strand_degree": strand, "K0": len(k0), "K1": len(k1), "K2": len(k2)}
    require(dimensions["K1"] == dimensions["K0"] + dimensions["K2"],
            "independent Koszul Euler characteristic failed")
    return fmpz_mat(first), fmpz_mat(second), dimensions


def select_columns(matrix: fmpz_mat, columns: list[int]) -> fmpz_mat:
    return fmpz_mat([
        [int(matrix[row, column]) for column in columns]
        for row in range(matrix.nrows())
    ])


def select_rows(matrix: fmpz_mat, rows: list[int]) -> fmpz_mat:
    return fmpz_mat([
        [int(matrix[row, column]) for column in range(matrix.ncols())]
        for row in rows
    ])


def independent_axis(d: int) -> tuple[int | None, int]:
    x2 = [
        coefficient
        for degree in (d, d + 1, d + 2)
        for exponent, coefficient in independent_g_terms(degree)
        if degree % 2 == 0 and exponent == (0, degree // 2, 0)
    ]
    x3 = [
        coefficient
        for degree in (d, d + 1, d + 2)
        for exponent, coefficient in independent_g_terms(degree)
        if degree % 3 == 0 and exponent == (0, 0, degree // 3)
    ]
    require(len(x3) == 1, "independent x3-axis inventory failed")
    if d % 2:
        require(len(x2) == 1, "independent odd x2-axis inventory failed")
        return x2[0], x3[0]
    require(len(x2) == 2, "independent even x2-axis inventory failed")
    return None, x3[0]


def exact_ceil_root(value: int, exponent: int) -> int:
    low = 0
    high = 1 << ((value.bit_length() + exponent - 1) // exponent + 1)
    while low + 1 < high:
        middle = (low + high) // 2
        if middle**exponent >= value:
            high = middle
        else:
            low = middle
    require(high**exponent >= value and (high - 1) ** exponent < value,
            "independent exact bound root failed")
    return high


def verify_source_runtime(receipt: dict[str, object]) -> None:
    bindings = receipt.get("startup_sha256")
    require(isinstance(bindings, dict), "CRT receipt lacks source bindings")
    for path in (PRODUCER_PATH, EXACT_PRODUCER_PATH, COMMON_PATH):
        keys = [key for key in bindings if Path(key).name == path.name]
        require(len(keys) == 1 and bindings[keys[0]] == sha256(path),
                f"CRT receipt binds stale {path.name}")
    runtime = receipt.get("runtime_sha256")
    require(isinstance(runtime, dict) and runtime, "CRT receipt lacks runtime bindings")
    require(len(runtime) == receipt.get("environment", {}).get("runtime_artifact_count"),
            "CRT runtime count mismatch")
    for raw_path, expected in runtime.items():
        path = Path(raw_path)
        require(path.is_file() and sha256(path) == expected,
                f"CRT runtime artifact is absent or changed: {path.name}")
    resolved_runtime = {Path(raw_path).resolve(): expected for raw_path, expected in runtime.items()}
    current_executable = Path(sys.executable).resolve()
    current_flint = Path(flint.__file__).resolve()
    for current_path, label in (
        (current_executable, "Python executable"),
        (current_flint, "loaded flint module"),
    ):
        require(current_path in resolved_runtime and
                sha256(current_path) == resolved_runtime[current_path],
                f"current {label} is not bound by the CRT receipt")


def verify_crt_receipt(receipt: dict[str, object], d_min: int, d_max: int) -> dict[int, int]:
    require(receipt.get("schema") == "polydegree-r3-cover-resultant-crt-v1",
            "wrong CRT resultant schema")
    require(receipt.get("status") == "PASS", "CRT resultant receipt is not PASS")
    require(receipt.get("d_min") == d_min and receipt.get("d_max") == d_max,
            "CRT resultant range mismatch")
    verify_source_runtime(receipt)
    cases = receipt.get("cases")
    require(isinstance(cases, list) and len(cases) == d_max - d_min + 1,
            "CRT resultant case count mismatch")
    values = {}
    for d, case in zip(range(d_min, d_max + 1), cases):
        require(case.get("d") == d, "CRT resultant case inventory mismatch")
        d1, d2, dimensions = independent_maps(d)
        require(case.get("dimensions") == dimensions, "CRT Koszul dimensions mismatch")
        require((d1 * d2).is_zero(), "independent Koszul composition is nonzero")
        pivots = case.get("pivot_columns")
        require(isinstance(pivots, list) and pivots == sorted(set(pivots)) and
                len(pivots) == d1.nrows() and
                all(isinstance(value, int) and 0 <= value < d1.ncols() for value in pivots),
                "CRT pivot inventory is invalid")
        complement = sorted(set(range(d1.ncols())) - set(pivots))
        require(len(complement) == d2.ncols(), "CRT pivot complement has wrong size")
        numerator = select_columns(d1, pivots)
        denominator = select_rows(d2, complement)
        x2, x3 = independent_axis(d)
        axis = abs(x3) ** 4 * (abs(x2) ** 3 if x2 is not None else 1)
        require(case.get("axis_correction") == {
            "x2_axis_coefficient": x2,
            "x2_missing_power": 3 if x2 is not None else 0,
            "x3_axis_coefficient": x3,
            "x3_missing_power": 4,
            "factor_abs": axis,
        }, "CRT axis correction mismatch")
        norms = [
            sum(int(numerator[row, column]) ** 2 for column in range(numerator.ncols()))
            for row in range(numerator.nrows())
        ]
        require(case.get("hadamard_row_squared_norms") == norms,
                "CRT Hadamard row norms mismatch")
        bound = exact_ceil_root(math.prod(norms) * axis**2, 6)
        require(case.get("r2_upper_bound") == bound, "CRT R^2 bound mismatch")

        rows = case.get("crt_rows")
        require(isinstance(rows, list) and rows, "CRT residue rows are absent")
        primes = [row.get("prime") for row in rows]
        require(len(primes) == len(set(primes)), "CRT prime inventory has duplicates")
        residue = 0
        modulus = 1
        for row in rows:
            prime = row["prime"]
            require(is_prime_64(prime) and prime % 3 == 2,
                    "CRT modulus is not a certified prime congruent to 2 mod 3")
            numerator_mod = int(nmod_mat(numerator, prime).det())
            denominator_mod = int(nmod_mat(denominator, prime).det())
            require(denominator_mod != 0, "CRT denominator minor vanished")
            signed_sixth = numerator_mod * (axis % prime) * pow(
                denominator_mod, -1, prime
            ) % prime
            oriented = pow(signed_sixth, pow(3, -1, prime - 1), prime)
            require(row == {
                "prime": prime,
                "numerator_minor_mod_prime": numerator_mod,
                "denominator_minor_mod_prime": denominator_mod,
                "signed_corrected_sixth_power_mod_prime": signed_sixth,
                "oriented_r2_mod_prime": oriented,
            }, "CRT modular determinant row mismatch")
            multiplier = ((oriented - residue) % prime) * pow(modulus % prime, -1, prime) % prime
            residue += modulus * multiplier
            modulus *= prime
        require(modulus > 2 * bound and case.get("crt_modulus") == modulus,
                "CRT modulus does not exceed twice the bound")
        require(case.get("oriented_crt_residue") == residue, "CRT residue mismatch")
        symmetric = residue if residue <= modulus // 2 else residue - modulus
        require(case.get("symmetric_crt_reconstruction") == symmetric,
                "symmetric CRT reconstruction mismatch")
        r2 = abs(symmetric)
        require(r2 <= bound and case.get("weighted_resultant_squared") == r2,
                "CRT reconstruction exceeds its bound")
        weighted = math.isqrt(r2)
        require(weighted > 0 and weighted**2 == r2 and
                case.get("weighted_resultant_abs") == weighted,
                "CRT reconstruction is not the stored exact square")
        require(case.get("controls") == {
            "modulus_exceeds_twice_bound": True,
            "symmetric_reconstruction_within_bound": True,
            "exact_square_reconstruction": True,
        }, "CRT controls mismatch")
        values[d] = weighted
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.input.is_file(), "CRT input receipt is absent")
    source_paths = (SCRIPT_PATH, PRODUCER_PATH, EXACT_PRODUCER_PATH, COMMON_PATH)
    startup_sources = {path.name: sha256(path) for path in source_paths}
    startup_input = sha256(args.input)
    receipt = json.loads(args.input.read_text())
    d_min = receipt.get("d_min")
    d_max = receipt.get("d_max")
    require(isinstance(d_min, int) and isinstance(d_max, int),
            "CRT input has no integer range")
    values = verify_crt_receipt(receipt, d_min, d_max)
    require(sha256(args.input) == startup_input,
            "CRT input changed during independent verification")
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "CRT verifier or a proof-relevant source changed during verification")
    cases = receipt.get("cases")
    require(isinstance(cases, list) and len(cases) == len(values),
            "CRT mutation-control case inventory mismatch")
    mutation_rejected = all(
        (values[d] + 1) ** 2 != case.get("weighted_resultant_squared")
        for d, case in zip(sorted(values), cases)
    )
    require(mutation_rejected, "CRT weighted-resultant mutation was not rejected")
    output = {
        "schema": "polydegree-r3-cover-resultant-crt-verification-v1",
        "status": "PASS",
        "input": args.input.name,
        "input_sha256": startup_input,
        "input_timing_free_projection_sha256": projection_sha256(receipt),
        "verified_values": [
            {"d": d, "weighted_resultant_abs": values[d]}
            for d in sorted(values)
        ],
        "negative_controls": {
            "weighted_resultant_increment_rejected": mutation_rejected,
        },
        "source_sha256": startup_sources,
        "environment": {
            "python": platform.python_version(),
            "python_optimize": sys.flags.optimize,
        },
    }
    atomic_json_write(args.out, output)
    print(json.dumps({
        "status": "PASS",
        "degrees": sorted(values),
        "receipt": str(args.out.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, OSError, json.JSONDecodeError, IndexError) as exc:
        print(f"R3 CRT VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
