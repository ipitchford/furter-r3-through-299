#!/usr/bin/env python3
"""Extract exact rational three-axis R(3) membership certificates."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
from fractions import Fraction
from pathlib import Path

import sympy as sp

from r3_common import (
    R3Error,
    atomic_json_write,
    bezout_colength,
    require,
    sha256,
    singular_polynomial_integer,
)


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
COMMON_PATH = BASE / "r3_common.py"
SOURCE_PATHS = (SCRIPT_PATH, COMMON_PATH)


def parse_marked(output: str, name: str) -> str:
    pattern = rf"^R3_{name}_BEGIN\s*$\n(.*?)^R3_{name}_END\s*$"
    matches = re.findall(pattern, output, flags=re.MULTILINE | re.DOTALL)
    require(len(matches) == 1, f"could not parse one {name} block")
    return matches[0].strip()


def sparse_rational(expression: str) -> list[dict[str, object]]:
    x1, x2, x3 = sp.symbols("x1 x2 x3")
    parsed = sp.sympify(
        expression.replace("^", "**"), locals={"x1": x1, "x2": x2, "x3": x3}
    )
    polynomial = sp.Poly(parsed, x1, x2, x3, domain=sp.QQ)
    rows = []
    for exponents, coefficient in polynomial.terms():
        value = Fraction(int(coefficient.p), int(coefficient.q))
        rows.append(
            {
                "exponents": list(exponents),
                "numerator": value.numerator,
                "denominator": value.denominator,
            }
        )
    return rows


def extract_case(singular: Path, d: int, timeout: float) -> dict[str, object]:
    polynomials = [singular_polynomial_integer(d + offset) for offset in range(3)]
    socle_weight = 3 * d - 3
    target_exponents = [
        socle_weight + 1,
        socle_weight // 2 + 1,
        socle_weight // 3 + 1,
    ]
    coefficient_markers = []
    for target in range(1, 4):
        for generator in range(1, 4):
            name = f"C_{target}_{generator}"
            coefficient_markers.append(
                f'print("R3_{name}_BEGIN"); print(string(T[{generator},{target}])); '
                f'print("R3_{name}_END");'
            )
    lower_markers = []
    for target in range(1, 4):
        name = f"LOWER_{target}"
        lower_markers.append(
            f'print("R3_{name}_BEGIN"); print(string(lower{target})); '
            f'print("R3_{name}_END");'
        )
    program = f"""option(redSB);
ring r=0,(x1,x2,x3),dp;
poly f0={polynomials[0]};
poly f1={polynomials[1]};
poly f2={polynomials[2]};
ideal I=f0,f1,f2;
int N1={target_exponents[0]}; int N2={target_exponents[1]}; int N3={target_exponents[2]};
poly t1=x1^N1; poly t2=x2^N2; poly t3=x3^N3;
ideal J=t1,t2,t3;
matrix T=lift(I,J);
poly r1=t1-(T[1,1]*f0+T[2,1]*f1+T[3,1]*f2);
poly r2=t2-(T[1,2]*f0+T[2,2]*f1+T[3,2]*f2);
poly r3=t3-(T[1,3]*f0+T[2,3]*f1+T[3,3]*f2);
ideal G=std(I);
poly lower1=reduce(x1^(N1-1),G);
poly lower2=reduce(x2^(N2-1),G);
poly lower3=reduce(x3^(N3-1),G);
print("R3_N="+string(N1)+","+string(N2)+","+string(N3));
print("R3_REMAINDER="+string(r1)+","+string(r2)+","+string(r3));
{chr(10).join(coefficient_markers)}
{chr(10).join(lower_markers)}
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
        f"Singular rational lift failed at d={d}: {completed.stderr[-1000:]}",
    )
    combined = completed.stdout + "\n" + completed.stderr
    exponent_matches = re.findall(r"^R3_N=(\d+),(\d+),(\d+)\s*$", combined, re.MULTILINE)
    remainder_matches = re.findall(r"^R3_REMAINDER=(.*)\s*$", combined, re.MULTILINE)
    require(len(exponent_matches) == 1, "pure-power exponent marker is ambiguous")
    require(remainder_matches == ["0,0,0"], "Singular returned a nonzero lift remainder")
    observed_exponents = [int(value) for value in exponent_matches[0]]
    require(observed_exponents == target_exponents, "Singular target exponents changed")

    targets = []
    for target_index, exponent in enumerate(target_exponents, start=1):
        cofactors = []
        for generator_index in range(1, 4):
            expression = parse_marked(combined, f"C_{target_index}_{generator_index}")
            cofactors.append(sparse_rational(expression))
        lower_expression = parse_marked(combined, f"LOWER_{target_index}")
        require(lower_expression != "0", f"one-lower target unexpectedly reduced to zero at d={d}")
        targets.append(
            {
                "variable": f"x{target_index}",
                "exponent": exponent,
                "cofactors": cofactors,
                "producer_lower_remainder": sparse_rational(lower_expression),
            }
        )
    return {
        "d": d,
        "socle_weight": socle_weight,
        "expected_colength": bezout_colength(d),
        "targets": targets,
        "singular_remainders_zero": True,
        "producer_lower_remainders_nonzero": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d-min", type=int, default=2)
    parser.add_argument("--d-max", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=1200.0)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(2 <= args.d_min <= args.d_max, "invalid degree range")
    require(args.timeout > 0, "timeout must be positive")
    singular = args.singular.resolve()
    output = args.out.resolve()
    require(singular.is_file(), "Singular executable is absent")
    require(output not in {*SOURCE_PATHS, singular}, "output overwrites a source or runtime")
    require(not output.exists(), "refusing to overwrite an existing output")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_runtime = {str(singular): sha256(singular)}
    cases = [extract_case(singular, d, args.timeout) for d in range(args.d_min, args.d_max + 1)]
    require(
        {path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
        "producer source changed during extraction",
    )
    require({str(singular): sha256(singular)} == startup_runtime,
            "Singular executable changed during extraction")
    receipt = {
        "schema": "polydegree-r3-rational-radical-certificates-v1",
        "status": "PASS",
        "claim_boundary": (
            "Exact rational pure-power membership identities for the displayed finite "
            "degrees only; no recurrence or all-degree claim is made."
        ),
        "d_min": args.d_min,
        "d_max": args.d_max,
        "cases": cases,
        "source_sha256": startup_sources,
        "runtime_sha256": startup_runtime,
        "environment": {"python": platform.python_version(), "sympy": sp.__version__},
    }
    atomic_json_write(output, receipt)
    print(json.dumps({"status": "PASS", "cases": len(cases)}, sort_keys=True))
    print("rational radical certificates:", output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, OSError, subprocess.SubprocessError, ValueError) as exc:
        print(f"R3 RATIONAL RADICAL EXTRACTION FAILED: {exc}")
        raise SystemExit(1)
