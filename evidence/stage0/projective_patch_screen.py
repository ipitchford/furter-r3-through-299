#!/usr/bin/env python3
"""Exact stratified projective-patch screen for Furter R(3) windows."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
from pathlib import Path

from r3_common import (
    R3Error,
    atomic_json_write,
    primes_through,
    require,
    sha256,
    singular_polynomial,
)


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
COMMON_PATH = BASE / "r3_common.py"
SOURCE_PATHS = (SCRIPT_PATH, COMMON_PATH)
STRATA = (
    ("x1_nonzero", "x1-1"),
    ("x1_zero_x2_nonzero", "x1,x2-1"),
    ("x1_x2_zero_x3_nonzero", "x1,x2,x3-1"),
)


def singular_version(executable: Path) -> str:
    completed = subprocess.run(
        [str(executable), "--version"], text=True, capture_output=True,
        timeout=30, check=False,
    )
    require(completed.returncode in (0, 1), "Singular --version failed")
    lines = (completed.stdout + completed.stderr).splitlines()
    require(lines, "Singular --version returned no output")
    return lines[0]


def run_stratum(
    executable: Path,
    polynomials: list[str],
    prime: int,
    name: str,
    constraints: str,
    timeout: float,
) -> dict[str, object]:
    program = f"""option(redSB);
ring r={prime},(x1,x2,x3),dp;
poly f0={polynomials[0]};
poly f1={polynomials[1]};
poly f2={polynomials[2]};
ideal I=f0,f1,f2,{constraints};
ideal G=std(I);
poly rem=reduce(1,G);
print("R3_PATCH_REM="+string(rem));
print("R3_PATCH_SIZE="+string(size(G)));
quit;
"""
    completed = subprocess.run(
        [str(executable), "-q"], input=program, text=True, capture_output=True,
        timeout=timeout, check=False, env={**os.environ, "LC_ALL": "C"},
    )
    require(completed.returncode == 0,
            f"Singular stratum failed: {(completed.stdout + completed.stderr)[-1000:]}")
    combined = completed.stdout + "\n" + completed.stderr
    remainder = re.findall(r"^R3_PATCH_REM=(.*)\s*$", combined, re.MULTILINE)
    basis_size = re.findall(r"^R3_PATCH_SIZE=(\d+)\s*$", combined, re.MULTILINE)
    require(len(remainder) == 1 and remainder[0] in {"0", "1"},
            "projective-patch remainder marker is malformed")
    require(len(basis_size) == 1, "projective-patch basis-size marker is malformed")
    return {
        "stratum": name,
        "unit_ideal": remainder[0] == "0",
        "remainder_of_one": int(remainder[0]),
        "groebner_basis_size": int(basis_size[0]),
    }


def certify_prime(
    executable: Path,
    d: int,
    prime: int,
    timeout: float,
    zero_third: bool = False,
) -> dict[str, object]:
    polynomials = [singular_polynomial(d + offset, prime) for offset in range(3)]
    if zero_third:
        polynomials[2] = "0"
    strata = []
    for name, constraints in STRATA:
        try:
            result = run_stratum(
                executable, polynomials, prime, name, constraints, timeout
            )
        except subprocess.TimeoutExpired:
            strata.append({"stratum": name, "timeout": True})
            return {
                "d": d,
                "prime": prime,
                "classification": "TIMEOUT",
                "strata": strata,
            }
        strata.append(result)
        if result["unit_ideal"] is False:
            return {
                "d": d,
                "prime": prime,
                "classification": "BAD",
                "strata": strata,
            }
    return {
        "d": d,
        "prime": prime,
        "classification": "GOOD",
        "strata": strata,
    }


def self_test(executable: Path, timeout: float) -> dict[str, object]:
    baseline = certify_prime(executable, 2, 5, timeout)
    require(baseline["classification"] == "GOOD", "projective baseline failed")
    mutation = certify_prime(executable, 2, 5, timeout, zero_third=True)
    require(mutation["classification"] == "BAD", "zero-third mutation was not BAD")
    require([row["stratum"] for row in baseline["strata"]]
            == [name for name, _ in STRATA], "projective cover inventory changed")
    return {
        "baseline_d2_p5": baseline,
        "zero_third_mutation_d2_p5": mutation,
        "stratified_cover_complete": True,
    }


def validate_attempt(attempt: object, expected_d: int) -> None:
    require(isinstance(attempt, dict), "patch attempt is not an object")
    require(attempt.get("d") == expected_d, "patch attempt degree mismatch")
    classification = attempt.get("classification")
    require(classification in {"GOOD", "BAD", "TIMEOUT"},
            "unknown patch classification")
    strata = attempt.get("strata")
    require(isinstance(strata, list) and strata, "patch attempt lacks strata")
    expected_names = [name for name, _ in STRATA]
    observed_names = [row.get("stratum") for row in strata if isinstance(row, dict)]
    require(observed_names == expected_names[:len(observed_names)],
            "patch strata are not an exact cover prefix")
    if classification == "GOOD":
        require(len(strata) == len(STRATA)
                and all(row.get("unit_ideal") is True
                        and row.get("remainder_of_one") == 0 for row in strata),
                "GOOD patch attempt lacks three unit ideals")
    elif classification == "BAD":
        require(strata[-1].get("unit_ideal") is False
                and strata[-1].get("remainder_of_one") == 1,
                "BAD patch attempt lacks a proper stratum ideal")
    else:
        require(strata[-1].get("timeout") is True,
                "TIMEOUT patch attempt lacks a timeout marker")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d-min", type=int, required=True)
    parser.add_argument("--d-max", type=int, required=True)
    parser.add_argument("--prime-max", type=int, default=997)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(2 <= args.d_min <= args.d_max, "invalid degree range")
    require(args.prime_max >= 2 and args.timeout > 0, "invalid prime or timeout bound")
    executable = args.singular.resolve()
    output = args.out.resolve()
    require(executable.is_file(), "Singular executable is absent")
    require(output not in {*SOURCE_PATHS, executable}, "output overwrites source or runtime")
    require(not output.exists(), "refusing to overwrite patch receipt")
    primes = primes_through(args.prime_max)
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_runtime = {str(executable): sha256(executable)}
    controls = self_test(executable, min(args.timeout, 30.0))
    cases = []
    coverage = []
    for d in range(args.d_min, args.d_max + 1):
        attempts = []
        for prime in primes:
            attempt = certify_prime(executable, d, prime, args.timeout)
            validate_attempt(attempt, d)
            attempts.append(attempt)
            if attempt["classification"] == "GOOD":
                coverage.append(d)
                break
        cases.append({"d": d, "attempts": attempts})
    complete = coverage == list(range(args.d_min, args.d_max + 1))
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "patch producer source changed during execution")
    require({str(executable): sha256(executable)} == startup_runtime,
            "Singular executable changed during patch screen")
    classifications = [
        attempt["classification"] for case in cases for attempt in case["attempts"]
    ]
    receipt = {
        "schema": "polydegree-r3-projective-patch-screen-v1",
        "status": "PASS" if complete else "PARTIAL",
        "claim_boundary": (
            "A GOOD row is an exact empty weighted-projective special-fibre certificate "
            "from the complete three-stratum cover. BAD rows certify a nonempty special "
            "fibre only; TIMEOUT rows carry no mathematical conclusion."
        ),
        "parameters": {
            "d_min": args.d_min,
            "d_max": args.d_max,
            "primes": primes,
            "timeout_seconds_per_stratum": args.timeout,
            "selection": "first completed GOOD after exact BAD rows and skipped timeouts",
        },
        "cover": [name for name, _ in STRATA],
        "controls": controls,
        "cases": cases,
        "good_degree_coverage": coverage,
        "counts": {
            "degrees": len(cases),
            "attempts": len(classifications),
            "good": classifications.count("GOOD"),
            "bad": classifications.count("BAD"),
            "timeout": classifications.count("TIMEOUT"),
        },
        "source_sha256": startup_sources,
        "runtime_sha256": startup_runtime,
        "environment": {
            "python": platform.python_version(),
            "singular": singular_version(executable),
            "platform": platform.platform(),
        },
    }
    atomic_json_write(output, receipt)
    print(json.dumps({"status": receipt["status"], **receipt["counts"]}, sort_keys=True))
    print("projective patch receipt:", output)
    return 0 if complete else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, OSError, subprocess.SubprocessError) as exc:
        print(f"R3 PROJECTIVE PATCH SCREEN FAILED: {exc}")
        raise SystemExit(1)
