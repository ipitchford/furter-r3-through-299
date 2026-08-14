#!/usr/bin/env python3
"""Exact R(3) resultant pilot via the standard-graded 2-by-3 cover."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import flint
from flint import fmpz_mat

from r3_common import R3Error, atomic_json_write, g_terms, require, sha256


# Determinants in the requested finite range legitimately exceed Python's
# defensive 4,300-decimal-digit conversion limit.  They are internally
# generated exact integers, not untrusted decimal input.
sys.set_int_max_str_digits(0)


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")
PYTHON_EXECUTABLE = Path(sys.executable).resolve()
PYTHON_LIBRARY = (Path(sys.base_prefix).resolve() / "Python").resolve()
FLINT_PACKAGE_ROOT = Path(flint.__file__).resolve().parent

SparseTerms = tuple[tuple[tuple[int, int, int], int], ...]


def runtime_artifact_paths() -> list[Path]:
    dist_info = sorted(
        path for path in FLINT_PACKAGE_ROOT.parent.glob("python_flint-*.dist-info")
        if path.is_dir()
    )
    require(len(dist_info) == 1, "expected exactly one python-flint dist-info directory")
    paths = [PYTHON_EXECUTABLE, PYTHON_LIBRARY]
    for root in (FLINT_PACKAGE_ROOT, dist_info[0]):
        paths.extend(
            path.resolve()
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        )
    unique = sorted(set(paths), key=str)
    require(all(path.is_file() for path in unique), "a producer runtime artifact is absent")
    require(any(path.name.startswith("libflint") for path in unique),
            "FLINT shared library is not in the runtime inventory")
    return unique


def runtime_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path): sha256(path) for path in paths}


def source_hashes() -> dict[str, str]:
    return {
        str(SCRIPT_PATH): sha256(SCRIPT_PATH),
        str(COMMON_PATH): sha256(COMMON_PATH),
    }


def require_frozen_inputs(
    startup_sources: dict[str, str],
    runtime_paths: list[Path],
    startup_runtime: dict[str, str],
) -> None:
    require(source_hashes() == startup_sources, "source changed during resultant computation")
    require(runtime_artifact_paths() == runtime_paths,
            "producer runtime artifact inventory changed during computation")
    require(runtime_hashes(runtime_paths) == startup_runtime,
            "producer runtime artifact changed during computation")


def load_checkpoint(
    path: Path,
    d_min: int,
    d_max: int,
    startup_sources: dict[str, str],
    startup_runtime: dict[str, str],
) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    checkpoint = json.loads(path.read_text())
    require(checkpoint.get("schema") == "polydegree-r3-cover-resultant-checkpoint-v1",
            "wrong resultant checkpoint schema")
    require(checkpoint.get("status") == "CHECKPOINT_ONLY_NOT_A_CERTIFICATE",
            "resultant checkpoint has an invalid status")
    require(checkpoint.get("d_min") == d_min and checkpoint.get("d_max") == d_max,
            "resultant checkpoint range mismatch")
    require(checkpoint.get("startup_sha256") == startup_sources,
            "resultant checkpoint source binding mismatch")
    require(checkpoint.get("runtime_sha256") == startup_runtime,
            "resultant checkpoint runtime binding mismatch")
    cases = checkpoint.get("cases")
    require(isinstance(cases, list), "resultant checkpoint cases are not a list")
    require([case.get("d") for case in cases] == list(range(d_min, d_min + len(cases))),
            "resultant checkpoint is not an exact contiguous prefix")
    require(len(cases) <= d_max - d_min + 1, "resultant checkpoint exceeds the range")
    return cases


def write_checkpoint(
    path: Path,
    d_min: int,
    d_max: int,
    cases: list[dict[str, object]],
    startup_sources: dict[str, str],
    startup_runtime: dict[str, str],
) -> None:
    atomic_json_write(path, {
        "schema": "polydegree-r3-cover-resultant-checkpoint-v1",
        "status": "CHECKPOINT_ONLY_NOT_A_CERTIFICATE",
        "claim_boundary": (
            "This is a resumable exact prefix only. It cannot support a mathematical "
            "claim until the terminal PASS receipt covers the full requested range."
        ),
        "d_min": d_min,
        "d_max": d_max,
        "completed_d": [case["d"] for case in cases],
        "cases": cases,
        "startup_sha256": startup_sources,
        "runtime_sha256": startup_runtime,
    })


def standard_monomials(degree: int) -> list[tuple[int, int, int]]:
    if degree < 0:
        return []
    return [
        (degree - second - third, second, third)
        for third in range(degree + 1)
        for second in range(degree - third + 1)
    ]


def covered_forms(d: int) -> tuple[SparseTerms, SparseTerms, SparseTerms]:
    forms = []
    for degree in (d, d + 1, d + 2):
        forms.append(tuple(
            ((exponent[0], 2 * exponent[1], 3 * exponent[2]), coefficient)
            for exponent, coefficient in g_terms(degree)
        ))
    return tuple(forms)


def add_exponents(left: tuple[int, int, int], right: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(left[index] + right[index] for index in range(3))


def build_maps(d: int, forms: tuple[SparseTerms, SparseTerms, SparseTerms]) -> tuple[fmpz_mat, fmpz_mat, dict[str, int], list[tuple[int, tuple[int, int, int]]]]:
    degrees = (d, d + 1, d + 2)
    strand = sum(degrees) - 2
    k0_basis = standard_monomials(strand)
    k0_index = {monomial: index for index, monomial in enumerate(k0_basis)}
    k1_basis: list[tuple[int, tuple[int, int, int]]] = []
    for component, degree in enumerate(degrees):
        k1_basis.extend(
            (component, monomial) for monomial in standard_monomials(strand - degree)
        )
    k1_index = {basis: index for index, basis in enumerate(k1_basis)}
    d1_rows = [[0] * len(k1_basis) for _ in k0_basis]
    for column, (component, multiplier) in enumerate(k1_basis):
        for exponent, coefficient in forms[component]:
            d1_rows[k0_index[add_exponents(multiplier, exponent)]][column] += coefficient

    pairs = ((0, 1), (0, 2), (1, 2))
    k2_basis: list[tuple[tuple[int, int], tuple[int, int, int]]] = []
    for left, right in pairs:
        k2_basis.extend(
            ((left, right), monomial)
            for monomial in standard_monomials(strand - degrees[left] - degrees[right])
        )
    d2_rows = [[0] * len(k2_basis) for _ in k1_basis]
    for column, ((left, right), multiplier) in enumerate(k2_basis):
        for exponent, coefficient in forms[left]:
            d2_rows[k1_index[(right, add_exponents(multiplier, exponent))]][column] += coefficient
        for exponent, coefficient in forms[right]:
            d2_rows[k1_index[(left, add_exponents(multiplier, exponent))]][column] -= coefficient
    d1 = fmpz_mat(d1_rows)
    d2 = fmpz_mat(d2_rows) if k2_basis else fmpz_mat(len(k1_basis), 0)
    dimensions = {
        "strand_degree": strand,
        "K0": len(k0_basis),
        "K1": len(k1_basis),
        "K2": len(k2_basis),
    }
    require(dimensions["K1"] == dimensions["K0"] + dimensions["K2"],
            "standard Koszul strand Euler characteristic is not zero")
    return d1, d2, dimensions, k1_basis


def rref_pivots(matrix: fmpz_mat) -> tuple[list[int], int]:
    numerator, denominator, rank = matrix.rref()
    require(int(rank) == matrix.nrows(), "covered K1->K0 map is not surjective")
    pivots: list[int] = []
    for row in range(matrix.nrows()):
        candidates = [
            column for column in range(matrix.ncols())
            if int(numerator[row, column]) != 0
        ]
        require(candidates, "RREF row has no pivot")
        pivot = candidates[0]
        require(int(numerator[row, pivot]) == int(denominator),
                "RREF pivot does not equal its denominator")
        require(all(int(numerator[other, pivot]) == 0 for other in range(matrix.nrows())
                    if other != row), "RREF pivot column is not reduced")
        pivots.append(pivot)
    require(pivots == sorted(set(pivots)), "RREF pivots are not strictly increasing")
    return pivots, int(denominator)


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


def exact_nth_root(value: int, exponent: int) -> int | None:
    require(value >= 0 and exponent >= 2, "invalid exact-root request")
    if value in (0, 1):
        return value
    approximation = 1 << ((value.bit_length() + exponent - 1) // exponent)
    while True:
        candidate = ((exponent - 1) * approximation + value // approximation ** (exponent - 1)) // exponent
        if candidate >= approximation:
            break
        approximation = candidate
    while (approximation + 1) ** exponent <= value:
        approximation += 1
    while approximation ** exponent > value:
        approximation -= 1
    return approximation if approximation ** exponent == value else None


def axis_coefficients(d: int) -> tuple[int | None, int]:
    degrees = (d, d + 1, d + 2)
    x2_coefficients = [
        coefficient
        for degree in degrees
        for exponent, coefficient in g_terms(degree)
        if degree % 2 == 0 and exponent == (0, degree // 2, 0)
    ]
    x3_coefficients = [
        coefficient
        for degree in degrees
        for exponent, coefficient in g_terms(degree)
        if degree % 3 == 0 and exponent == (0, 0, degree // 3)
    ]
    require(len(x3_coefficients) == 1, "three-degree window lacks one x3-axis coefficient")
    if d % 2:
        require(len(x2_coefficients) == 1, "odd-d window lacks one x2-axis coefficient")
        x2_axis = x2_coefficients[0]
    else:
        require(len(x2_coefficients) == 2, "even-d window lacks two x2-axis coefficients")
        x2_axis = None
    require(x2_axis != 0 if x2_axis is not None else True, "x2-axis coefficient vanished")
    require(x3_coefficients[0] != 0, "x3-axis coefficient vanished")
    return x2_axis, x3_coefficients[0]


def compute_case(d: int) -> dict[str, object]:
    started = time.monotonic()
    d1, d2, dimensions, k1_basis = build_maps(d, covered_forms(d))
    require((d1 * d2).is_zero(), "covered Koszul composition is nonzero")
    pivots, rref_denominator = rref_pivots(d1)
    complement = sorted(set(range(d1.ncols())) - set(pivots))
    require(len(complement) == d2.ncols(), "pivot complement has wrong size")
    denominator = int(select_rows(d2, complement).det()) if complement else 1
    require(denominator != 0, "complementary Koszul minor vanished")
    numerator = int(select_columns(d1, pivots).det())
    require(numerator != 0, "RREF-selected numerator minor vanished")
    quotient, remainder = divmod(abs(numerator), abs(denominator))
    require(remainder == 0 and quotient > 0, "cover determinant ratio was not a positive integer")
    x2_axis, x3_axis = axis_coefficients(d)
    correction = abs(x3_axis) ** 4
    if x2_axis is not None:
        correction *= abs(x2_axis) ** 3
    corrected_cover = quotient * correction
    weighted = exact_nth_root(corrected_cover, 6)
    require(weighted is not None, "axis-corrected cover resultant was not an exact sixth power")
    require(weighted ** 6 == corrected_cover, "sixth-power reconstruction failed")
    return {
        "d": d,
        "dimensions": dimensions,
        "rref_denominator": rref_denominator,
        "pivot_columns": pivots,
        "numerator_minor_det": numerator,
        "denominator_minor_det": denominator,
        "ordinary_cover_resultant_abs": quotient,
        "axis_correction": {
            "x2_axis_coefficient": x2_axis,
            "x2_missing_power": 3 if x2_axis is not None else 0,
            "x3_axis_coefficient": x3_axis,
            "x3_missing_power": 4,
            "factor_abs": correction,
        },
        "axis_corrected_cover_resultant_abs": corrected_cover,
        "weighted_resultant_abs": weighted,
        "sixth_power_identity": True,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d-min", type=int, required=True)
    parser.add_argument("--d-max", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()
    require(2 <= args.d_min <= args.d_max, "invalid d range")
    require(not args.out.exists(), "refusing to overwrite an existing terminal output")
    large_integer_digits = len(str(10**5000))
    require(large_integer_digits == 5001, "large exact integer serialization control failed")
    startup_hashes = source_hashes()
    runtime_paths = runtime_artifact_paths()
    startup_runtime_hashes = runtime_hashes(runtime_paths)
    checkpoint_path = args.checkpoint or args.out.with_name(f".{args.out.name}.checkpoint")
    cases = load_checkpoint(
        checkpoint_path, args.d_min, args.d_max, startup_hashes, startup_runtime_hashes
    )
    resumed_case_count = len(cases)
    for d in range(args.d_min + resumed_case_count, args.d_max + 1):
        cases.append(compute_case(d))
        require_frozen_inputs(startup_hashes, runtime_paths, startup_runtime_hashes)
        write_checkpoint(
            checkpoint_path,
            args.d_min,
            args.d_max,
            cases,
            startup_hashes,
            startup_runtime_hashes,
        )
    require_frozen_inputs(startup_hashes, runtime_paths, startup_runtime_hashes)
    receipt = {
        "schema": "polydegree-r3-cover-resultant-v2",
        "status": "PASS",
        "claim_boundary": (
            "Exact finite resultant values only; no all-d recurrence, "
            "nonvanishing theorem, or proof of R(3) is claimed."
        ),
        "construction": {
            "cover": ["x1=y1", "x2=y2^2", "x3=y3^3"],
            "generic_cover_degree": 6,
            "ramification_correction": (
                "multiply by abs(x2-axis coefficient)^3 for odd d and "
                "abs(x3-axis coefficient)^4 for every d"
            ),
            "ordinary_strand_degree": "(d)+(d+1)+(d+2)-2 = 3d+1",
            "ordinary_resultant": "absolute exact Koszul determinant ratio",
            "weighted_resultant": "exact positive sixth root of axis-corrected cover resultant",
        },
        "d_min": args.d_min,
        "d_max": args.d_max,
        "controls": {
            "large_exact_integer_decimal_digits": large_integer_digits,
            "large_exact_integer_serialization_enabled": True,
            "checkpoint_exact_prefix_validated": True,
            "resumed_case_count": resumed_case_count,
        },
        "cases": cases,
        "startup_sha256": startup_hashes,
        "runtime_sha256": startup_runtime_hashes,
        "environment": {
            "python": platform.python_version(),
            "python_executable": str(PYTHON_EXECUTABLE),
            "python_library": str(PYTHON_LIBRARY),
            "python_flint": flint.__version__,
            "flint_package_root": str(FLINT_PACKAGE_ROOT),
            "runtime_artifact_count": len(runtime_paths),
            "platform": platform.platform(),
        },
    }
    atomic_json_write(args.out, receipt)
    print(json.dumps({"status": "PASS", "cases": len(cases)}, sort_keys=True))
    print("cover-resultant receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except R3Error as exc:
        print(f"R3 COVER RESULTANT FAILED: {exc}")
        raise SystemExit(1)
