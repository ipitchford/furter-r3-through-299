#!/usr/bin/env python3
"""Fail-closed exact modular-colength producer for Furter R(3) windows."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import time
from pathlib import Path

from r3_common import (
    R3Error,
    atomic_json_write,
    bezout_colength,
    is_prime,
    primes_through,
    require,
    sha256,
    singular_polynomial,
)


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")


def classify_vdim(vdim: int, expected: int) -> str:
    if vdim == expected:
        return "GOOD"
    if vdim == -1:
        return "BAD"
    raise R3Error(
        f"inadmissible finite colength {vdim}; expected {expected} or -1 for positive dimension"
    )


def singular_version(executable: Path) -> str:
    completed = subprocess.run(
        [str(executable), "--version"],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    require(completed.returncode in (0, 1), "Singular --version failed")
    first_line = (completed.stdout + completed.stderr).splitlines()
    require(first_line, "Singular --version returned no output")
    return first_line[0]


def run_vdim(
    executable: Path,
    d: int,
    prime: int,
    timeout: float,
    zero_third: bool = False,
) -> dict[str, object]:
    require(d >= 2, "d must be at least two")
    require(is_prime(prime), f"modulus {prime} is not prime")
    polynomials = [singular_polynomial(d + offset, prime) for offset in range(3)]
    if zero_third:
        polynomials[2] = "0"
    program = f"""option(redSB);
ring r={prime},(x1,x2,x3),dp;
poly f0={polynomials[0]};
poly f1={polynomials[1]};
poly f2={polynomials[2]};
ideal I=f0,f1,f2;
ideal G=std(I);
int answer=vdim(G);
print(\"R3_VDIM=\"+string(answer));
print(\"R3_GSIZE=\"+string(size(G)));
quit;
"""
    started = time.monotonic()
    completed = subprocess.run(
        [str(executable), "-q"],
        input=program,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env={**os.environ, "LC_ALL": "C"},
    )
    elapsed = time.monotonic() - started
    require(completed.returncode == 0, f"Singular failed: {completed.stderr[-1000:]}")
    combined = completed.stdout + "\n" + completed.stderr
    vdim_matches = re.findall(r"^R3_VDIM=(-?\d+)\s*$", combined, flags=re.MULTILINE)
    size_matches = re.findall(r"^R3_GSIZE=(\d+)\s*$", combined, flags=re.MULTILINE)
    require(len(vdim_matches) == 1, f"could not parse one vdim marker: {combined[-1000:]}")
    require(len(size_matches) == 1, f"could not parse one basis-size marker: {combined[-1000:]}")
    return {
        "vdim": int(vdim_matches[0]),
        "groebner_basis_size": int(size_matches[0]),
        "elapsed_seconds": round(elapsed, 6),
        "zero_third_control": zero_third,
    }


def self_test(executable: Path, timeout: float) -> dict[str, object]:
    baseline = run_vdim(executable, d=2, prime=5, timeout=timeout)
    expected = bezout_colength(2)
    require(classify_vdim(int(baseline["vdim"]), expected) == "GOOD", "baseline control failed")
    mutation = run_vdim(executable, d=2, prime=5, timeout=timeout, zero_third=True)
    require(int(mutation["vdim"]) == -1, "zero-third-generator mutation was not rejected")
    rejected_impossible = False
    try:
        classify_vdim(expected + 1, expected)
    except R3Error:
        rejected_impossible = True
    require(rejected_impossible, "impossible finite-colength negative control was not rejected")
    return {
        "baseline": baseline,
        "zero_third_mutation": mutation,
        "impossible_finite_colength_rejected": rejected_impossible,
    }


def parse_primes(raw: str | None, maximum: int | None) -> list[int]:
    require((raw is None) != (maximum is None), "provide exactly one of --primes or --prime-max")
    if raw is not None:
        values = [int(piece) for piece in raw.split(",") if piece]
        require(values, "--primes was empty")
        require(all(is_prime(value) for value in values), "--primes contains a non-prime")
        require(len(set(values)) == len(values), "--primes contains duplicates")
        return sorted(values)
    require(maximum is not None, "internal prime parsing error")
    return primes_through(maximum)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d-min", type=int, required=True)
    parser.add_argument("--d-max", type=int, required=True)
    parser.add_argument("--primes")
    parser.add_argument("--prime-max", type=int)
    parser.add_argument("--first-good", action="store_true")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--continue-on-timeout", action="store_true")
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    require(2 <= args.d_min <= args.d_max, "invalid d range")
    require(args.timeout > 0, "timeout must be positive")
    executable = args.singular.resolve()
    require(executable.is_file(), f"Singular executable not found: {executable}")
    primes = parse_primes(args.primes, args.prime_max)
    startup_hashes = {
        str(SCRIPT_PATH): sha256(SCRIPT_PATH),
        str(COMMON_PATH): sha256(COMMON_PATH),
        str(executable): sha256(executable),
    }
    controls = self_test(executable, min(args.timeout, 60.0))
    rows: list[dict[str, object]] = []
    incomplete: list[dict[str, object]] = []
    started_at = time.time()
    for d in range(args.d_min, args.d_max + 1):
        expected = bezout_colength(d)
        found_good = False
        for prime in primes:
            try:
                result = run_vdim(executable, d, prime, args.timeout)
            except subprocess.TimeoutExpired:
                failure = {"d": d, "prime": prime, "failure": "TIMEOUT"}
                if not args.continue_on_timeout:
                    raise R3Error(f"Singular timed out at d={d}, p={prime}")
                incomplete.append(failure)
                continue
            classification = classify_vdim(int(result["vdim"]), expected)
            row = {
                "d": d,
                "prime": prime,
                "expected_colength": expected,
                "classification": classification,
                **result,
            }
            rows.append(row)
            if classification == "GOOD":
                found_good = True
                if args.first_good:
                    break
        if args.first_good and not found_good:
            incomplete.append({"d": d, "failure": "NO_GOOD_PRIME_IN_REQUESTED_SET"})

    end_hashes = {
        str(SCRIPT_PATH): sha256(SCRIPT_PATH),
        str(COMMON_PATH): sha256(COMMON_PATH),
        str(executable): sha256(executable),
    }
    require(end_hashes == startup_hashes, "source or Singular executable changed during run")
    covered_degrees = sorted({int(row["d"]) for row in rows if row["classification"] == "GOOD"})
    status = "PASS" if not incomplete else "PARTIAL"
    receipt = {
        "schema": "polydegree-r3-modular-colength-v1",
        "status": status,
        "claim_boundary": (
            "GOOD rows are exact finite-instance R(3) certificates via empty special fibre; "
            "BAD rows and PARTIAL runs are discovery evidence only."
        ),
        "parameters": {
            "d_min": args.d_min,
            "d_max": args.d_max,
            "primes": primes,
            "first_good": args.first_good,
            "timeout_seconds": args.timeout,
        },
        "controls": controls,
        "rows": rows,
        "incomplete": incomplete,
        "good_degree_coverage": covered_degrees,
        "counts": {
            "rows": len(rows),
            "good": sum(row["classification"] == "GOOD" for row in rows),
            "bad": sum(row["classification"] == "BAD" for row in rows),
            "incomplete": len(incomplete),
        },
        "environment": {
            "python": platform.python_version(),
            "singular": singular_version(executable),
            "platform": platform.platform(),
        },
        "startup_sha256": startup_hashes,
        "elapsed_seconds": round(time.time() - started_at, 6),
    }
    atomic_json_write(args.out, receipt)
    print(json.dumps({"status": status, **receipt["counts"]}, sort_keys=True))
    print("receipt:", args.out.resolve())
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except R3Error as exc:
        print(f"R3 MODULAR COLENGTH FAILED: {exc}")
        raise SystemExit(1)
