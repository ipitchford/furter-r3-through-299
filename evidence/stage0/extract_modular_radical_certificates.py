#!/usr/bin/env python3
"""Discover finite-field pure-power membership certificates with Singular."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
from pathlib import Path

import sympy as sp

from analyze_good_prime_frontier import require_verification_binding
from r3_common import (
    R3Error,
    atomic_json_write,
    require,
    sha256,
    singular_polynomial,
)
from verify_colength import DEFAULT_SINGULAR, verify_receipt


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
SOURCE_PATHS = (
    SCRIPT_PATH,
    BASE / "r3_common.py",
    BASE / "modular_colength.py",
    BASE / "verify_colength.py",
    BASE / "analyze_good_prime_frontier.py",
)


def parse_marked(output: str, name: str) -> str:
    pattern = rf"^R3_{name}_BEGIN\s*$\n(.*?)^R3_{name}_END\s*$"
    matches = re.findall(pattern, output, flags=re.MULTILINE | re.DOTALL)
    require(len(matches) == 1, f"could not parse one {name} block")
    return matches[0].strip()


def sparse_modular(expression: str, prime: int) -> list[dict[str, object]]:
    x1, x2, x3 = sp.symbols("x1 x2 x3")
    parsed = sp.sympify(
        expression.replace("^", "**"), locals={"x1": x1, "x2": x2, "x3": x3}
    )
    polynomial = sp.Poly(parsed, x1, x2, x3, modulus=prime)
    return [
        {"exponents": list(exponents), "coefficient": int(coefficient) % prime}
        for exponents, coefficient in polynomial.terms()
        if int(coefficient) % prime
    ]


def smallest_good_primes(
    receipt: dict[str, object], d_min: int, d_max: int
) -> dict[int, int]:
    result: dict[int, int] = {}
    for row in receipt["rows"]:
        if row["classification"] == "GOOD" and d_min <= row["d"] <= d_max:
            d = row["d"]
            result[d] = min(result.get(d, row["prime"]), row["prime"])
    require(sorted(result) == list(range(d_min, d_max + 1)),
            "map lacks a smallest GOOD prime for every requested degree")
    return result


def extract_case(
    singular: Path, d: int, prime: int, timeout: float
) -> dict[str, object]:
    polynomials = [singular_polynomial(d + offset, prime) for offset in range(3)]
    socle_weight_bound = 3 * d - 3
    exponents = [
        socle_weight_bound + 1,
        socle_weight_bound // 2 + 1,
        socle_weight_bound // 3 + 1,
    ]
    coefficient_markers = []
    for target in range(1, 4):
        for generator in range(1, 4):
            name = f"C_{target}_{generator}"
            coefficient_markers.append(
                f'print("R3_{name}_BEGIN"); print(string(T[{generator},{target}])); '
                f'print("R3_{name}_END");'
            )
    program = f"""option(redSB);
ring r={prime},(x1,x2,x3),dp;
poly f0={polynomials[0]};
poly f1={polynomials[1]};
poly f2={polynomials[2]};
ideal I=f0,f1,f2;
int N1={exponents[0]}; int N2={exponents[1]}; int N3={exponents[2]};
poly t1=x1^N1; poly t2=x2^N2; poly t3=x3^N3;
ideal J=t1,t2,t3;
matrix T=lift(I,J);
poly r1=t1-(T[1,1]*f0+T[2,1]*f1+T[3,1]*f2);
poly r2=t2-(T[1,2]*f0+T[2,2]*f1+T[3,2]*f2);
poly r3=t3-(T[1,3]*f0+T[2,3]*f1+T[3,3]*f2);
print("R3_N="+string(N1)+","+string(N2)+","+string(N3));
print("R3_REMAINDER="+string(r1)+","+string(r2)+","+string(r3));
{chr(10).join(coefficient_markers)}
quit;
"""
    completed = subprocess.run(
        [str(singular), "-q"],
        input=program,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env={**os.environ, "LC_ALL": "C"},
    )
    require(
        completed.returncode == 0,
        f"Singular modular lift failed at d={d}, p={prime}: {completed.stderr[-1000:]}",
    )
    combined = completed.stdout + "\n" + completed.stderr
    exponent_matches = re.findall(r"^R3_N=(\d+),(\d+),(\d+)\s*$", combined, re.MULTILINE)
    remainder_matches = re.findall(r"^R3_REMAINDER=(.*)\s*$", combined, re.MULTILINE)
    require(len(exponent_matches) == 1, "pure-power exponent marker is ambiguous")
    require(remainder_matches == ["0,0,0"], "Singular returned a nonzero lift remainder")
    exponents = [int(value) for value in exponent_matches[0]]
    require(
        exponents == [
            socle_weight_bound + 1,
            socle_weight_bound // 2 + 1,
            socle_weight_bound // 3 + 1,
        ],
        "Singular target exponents differ from the universal socle-bound targets",
    )
    targets = []
    for target_index, exponent in enumerate(exponents, start=1):
        cofactors = []
        for generator_index in range(1, 4):
            expression = parse_marked(combined, f"C_{target_index}_{generator_index}")
            cofactors.append(sparse_modular(expression, prime))
        targets.append(
            {
                "variable": f"x{target_index}",
                "exponent": exponent,
                "cofactors": cofactors,
            }
        )
    return {
        "d": d,
        "prime": prime,
        "socle_weight_bound": socle_weight_bound,
        "targets": targets,
        "singular_remainders_zero": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--d-min", type=int, default=2)
    parser.add_argument("--d-max", type=int, default=8)
    parser.add_argument("--expected-prime-max", type=int, default=997)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(2 <= args.d_min <= args.d_max, "invalid degree range")
    require(args.timeout > 0, "timeout must be positive")
    map_path = args.map.resolve()
    verification_path = args.verification.resolve()
    singular = args.singular.resolve()
    output_path = args.out.resolve()
    watched_paths = (map_path, verification_path, singular)
    require(all(path.is_file() for path in watched_paths), "one or more inputs are absent")
    require(output_path not in {*watched_paths, *SOURCE_PATHS},
            "output overwrites an input or source")
    require(not output_path.exists(), "refusing to overwrite an existing output")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {str(path): sha256(path) for path in watched_paths}
    modular_map = json.loads(map_path.read_text())
    verification = json.loads(verification_path.read_text())
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
    summary = verify_receipt(
        modular_map,
        map_d_min,
        map_d_max,
        args.expected_prime_max,
        True,
        singular,
    )
    require_verification_binding(verification, map_path, summary)
    smallest = smallest_good_primes(modular_map, args.d_min, args.d_max)
    cases = [
        extract_case(singular, d, smallest[d], args.timeout)
        for d in range(args.d_min, args.d_max + 1)
    ]
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "certificate producer source changed during execution")
    require({str(path): sha256(path) for path in watched_paths} == startup_inputs,
            "certificate input or Singular executable changed during execution")
    output = {
        "schema": "polydegree-r3-modular-radical-certificates-v1",
        "status": "PASS",
        "claim_boundary": (
            "Exact finite-field pure-power membership identities for the displayed "
            "degrees only; no digit transition or all-degree claim is made."
        ),
        "d_min": args.d_min,
        "d_max": args.d_max,
        "cases": cases,
        "inputs_sha256": {
            map_path.name: startup_inputs[str(map_path)],
            verification_path.name: startup_inputs[str(verification_path)],
        },
        "source_sha256": startup_sources,
        "runtime_sha256": {singular.name: startup_inputs[str(singular)]},
        "environment": {"python": platform.python_version(), "sympy": sp.__version__},
    }
    atomic_json_write(output_path, output)
    print(json.dumps({"status": "PASS", "cases": len(cases)}, sort_keys=True))
    print("modular radical certificates:", output_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError, subprocess.SubprocessError) as exc:
        print(f"R3 MODULAR RADICAL CERTIFICATE EXTRACTION FAILED: {exc}")
        raise SystemExit(1)
