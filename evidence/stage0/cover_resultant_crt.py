#!/usr/bin/env python3
"""Exact R(3) resultant certificates by modular determinants and CRT."""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
import time
from pathlib import Path

from flint import nmod_mat

from cover_resultant import (
    COMMON_PATH,
    SCRIPT_PATH as EXACT_PRODUCER_PATH,
    axis_coefficients,
    build_maps,
    covered_forms,
    runtime_artifact_paths,
    runtime_hashes,
    select_columns,
    select_rows,
)
from r3_common import R3Error, atomic_json_write, require, sha256


sys.set_int_max_str_digits(0)

SCRIPT_PATH = Path(__file__).resolve()
MILLER_RABIN_BASES_64 = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)


def is_prime_64(value: int) -> bool:
    """Deterministic Miller--Rabin for value < 2^64."""
    require(0 <= value < 2**64, "primality input is outside the 64-bit contract")
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


def certificate_primes():
    candidate = 2**61 - 1
    while True:
        candidate -= 1
        while candidate % 3 != 2:
            candidate -= 1
        if is_prime_64(candidate):
            yield candidate


def exact_ceil_root(value: int, exponent: int) -> int:
    require(value > 0 and exponent >= 2, "invalid exact root bound")
    low = 0
    high = 1 << ((value.bit_length() + exponent - 1) // exponent + 1)
    while low + 1 < high:
        middle = (low + high) // 2
        if middle**exponent >= value:
            high = middle
        else:
            low = middle
    require(high**exponent >= value and (high - 1) ** exponent < value,
            "exact ceiling root postcondition failed")
    return high


def select_modular_pivots(d1, d2, prime_iterator):
    skipped = []
    for prime in prime_iterator:
        reduced, rank = nmod_mat(d1, prime).rref()
        if int(rank) != d1.nrows():
            skipped.append({"prime": prime, "reason": "D1_NOT_FULL_ROW_RANK"})
            continue
        pivots = []
        for row in range(reduced.nrows()):
            candidates = [
                column for column in range(reduced.ncols())
                if int(reduced[row, column]) != 0
            ]
            require(candidates, "modular RREF row has no pivot")
            pivots.append(candidates[0])
        require(pivots == sorted(set(pivots)), "modular pivot inventory is invalid")
        complement = sorted(set(range(d1.ncols())) - set(pivots))
        require(len(complement) == d2.ncols(), "modular pivot complement has wrong size")
        numerator = select_columns(d1, pivots)
        denominator = select_rows(d2, complement)
        if int(nmod_mat(denominator, prime).det()) == 0:
            skipped.append({"prime": prime, "reason": "DENOMINATOR_MINOR_ZERO"})
            continue
        return prime, pivots, numerator, denominator, skipped
    raise R3Error("prime iterator terminated before a pivot certificate was found")


def hadamard_r2_bound(numerator, axis_factor: int) -> tuple[int, list[int]]:
    row_squared_norms = [
        sum(int(numerator[row, column]) ** 2 for column in range(numerator.ncols()))
        for row in range(numerator.nrows())
    ]
    require(all(value > 0 for value in row_squared_norms), "zero row in numerator minor")
    product = math.prod(row_squared_norms) * axis_factor**2
    bound = exact_ceil_root(product, 6)
    return bound, row_squared_norms


def crt_extend(residue: int, modulus: int, new_residue: int, prime: int) -> tuple[int, int]:
    require(math.gcd(modulus, prime) == 1, "CRT moduli are not coprime")
    multiplier = ((new_residue - residue) % prime) * pow(modulus % prime, -1, prime) % prime
    combined = residue + modulus * multiplier
    new_modulus = modulus * prime
    require(combined % modulus == residue and combined % prime == new_residue,
            "CRT extension postcondition failed")
    return combined, new_modulus


def compute_case(d: int) -> dict[str, object]:
    started = time.monotonic()
    d1, d2, dimensions, _ = build_maps(d, covered_forms(d))
    require((d1 * d2).is_zero(), "covered Koszul composition is nonzero")
    prime_iterator = certificate_primes()
    pivot_prime, pivots, numerator, denominator, skipped = select_modular_pivots(
        d1, d2, prime_iterator
    )
    x2_axis, x3_axis = axis_coefficients(d)
    axis_factor = abs(x3_axis) ** 4 * (abs(x2_axis) ** 3 if x2_axis is not None else 1)
    bound, row_squared_norms = hadamard_r2_bound(numerator, axis_factor)

    residue = 0
    modulus = 1
    rows = []
    pending = [pivot_prime]
    while modulus <= 2 * bound:
        prime = pending.pop() if pending else next(prime_iterator)
        numerator_mod = int(nmod_mat(numerator, prime).det())
        denominator_mod = int(nmod_mat(denominator, prime).det())
        if denominator_mod == 0:
            skipped.append({"prime": prime, "reason": "DENOMINATOR_MINOR_ZERO"})
            continue
        signed_sixth = numerator_mod * (axis_factor % prime) * pow(
            denominator_mod, -1, prime
        ) % prime
        cube_inverse = pow(3, -1, prime - 1)
        oriented_r2 = pow(signed_sixth, cube_inverse, prime)
        require(pow(oriented_r2, 3, prime) == signed_sixth,
                "modular cube-root postcondition failed")
        residue, modulus = crt_extend(residue, modulus, oriented_r2, prime)
        rows.append({
            "prime": prime,
            "numerator_minor_mod_prime": numerator_mod,
            "denominator_minor_mod_prime": denominator_mod,
            "signed_corrected_sixth_power_mod_prime": signed_sixth,
            "oriented_r2_mod_prime": oriented_r2,
        })

    symmetric = residue if residue <= modulus // 2 else residue - modulus
    r2 = abs(symmetric)
    require(r2 <= bound, "symmetric CRT reconstruction exceeds the Hadamard bound")
    weighted = math.isqrt(r2)
    require(weighted > 0 and weighted**2 == r2,
            "symmetric CRT reconstruction is not a positive exact square")
    require(all(
        (weighted**2 - row["oriented_r2_mod_prime"]) % row["prime"] == 0 or
        (weighted**2 + row["oriented_r2_mod_prime"]) % row["prime"] == 0
        for row in rows
    ), "reconstructed resultant fails a modular orientation check")
    return {
        "d": d,
        "dimensions": dimensions,
        "pivot_selection_prime": pivot_prime,
        "pivot_columns": pivots,
        "axis_correction": {
            "x2_axis_coefficient": x2_axis,
            "x2_missing_power": 3 if x2_axis is not None else 0,
            "x3_axis_coefficient": x3_axis,
            "x3_missing_power": 4,
            "factor_abs": axis_factor,
        },
        "hadamard_row_squared_norms": row_squared_norms,
        "r2_upper_bound": bound,
        "crt_rows": rows,
        "skipped_primes": skipped,
        "crt_modulus": modulus,
        "oriented_crt_residue": residue,
        "symmetric_crt_reconstruction": symmetric,
        "weighted_resultant_squared": r2,
        "weighted_resultant_abs": weighted,
        "controls": {
            "modulus_exceeds_twice_bound": modulus > 2 * bound,
            "symmetric_reconstruction_within_bound": True,
            "exact_square_reconstruction": True,
        },
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d-min", type=int, required=True)
    parser.add_argument("--d-max", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(2 <= args.d_min <= args.d_max, "invalid d range")
    require(not args.out.exists(), "refusing to overwrite an existing CRT receipt")
    runtime_paths = runtime_artifact_paths()
    startup_runtime = runtime_hashes(runtime_paths)
    startup_sources = {
        str(SCRIPT_PATH): sha256(SCRIPT_PATH),
        str(EXACT_PRODUCER_PATH): sha256(EXACT_PRODUCER_PATH),
        str(COMMON_PATH): sha256(COMMON_PATH),
    }
    cases = [compute_case(d) for d in range(args.d_min, args.d_max + 1)]
    require(startup_sources == {
        str(SCRIPT_PATH): sha256(SCRIPT_PATH),
        str(EXACT_PRODUCER_PATH): sha256(EXACT_PRODUCER_PATH),
        str(COMMON_PATH): sha256(COMMON_PATH),
    }, "CRT producer source changed during computation")
    require(runtime_artifact_paths() == runtime_paths and
            runtime_hashes(runtime_paths) == startup_runtime,
            "CRT producer runtime changed during computation")
    receipt = {
        "schema": "polydegree-r3-cover-resultant-crt-v1",
        "status": "PASS",
        "claim_boundary": (
            "Exact finite weighted-resultant values certified by modular Koszul "
            "determinants, a Hadamard bound, symmetric CRT, and exact square recovery."
        ),
        "d_min": args.d_min,
        "d_max": args.d_max,
        "cases": cases,
        "startup_sha256": startup_sources,
        "runtime_sha256": startup_runtime,
        "environment": {
            "python": platform.python_version(),
            "runtime_artifact_count": len(runtime_paths),
        },
    }
    atomic_json_write(args.out, receipt)
    print(json.dumps({"status": "PASS", "cases": len(cases)}, sort_keys=True))
    print("CRT resultant receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, OSError) as exc:
        print(f"R3 CRT RESULTANT FAILED: {exc}")
        raise SystemExit(1)
