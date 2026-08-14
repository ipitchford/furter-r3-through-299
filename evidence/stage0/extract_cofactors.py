#!/usr/bin/env python3
"""Extract exact x3^d cofactor certificates with Singular's lift."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import time
from fractions import Fraction
from pathlib import Path

import sympy as sp

from r3_common import (
    R3Error,
    atomic_json_write,
    require,
    sha256,
    singular_polynomial_integer,
)


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")


def parse_marked(output: str, name: str) -> str:
    pattern = rf"^R3_{name}_BEGIN\s*$\n(.*?)^R3_{name}_END\s*$"
    matches = re.findall(pattern, output, flags=re.MULTILINE | re.DOTALL)
    require(len(matches) == 1, f"could not parse one {name} block")
    return matches[0].strip()


def sparse_rational(expression: str) -> list[dict[str, object]]:
    x1, x2, x3 = sp.symbols("x1 x2 x3")
    parsed = sp.sympify(expression.replace("^", "**"), locals={"x1": x1, "x2": x2, "x3": x3})
    polynomial = sp.Poly(parsed, x1, x2, x3, domain=sp.QQ)
    rows = []
    for exponents, coefficient in polynomial.terms():
        rational = Fraction(int(coefficient.p), int(coefficient.q))
        rows.append({
            "exponents": list(exponents),
            "numerator": rational.numerator,
            "denominator": rational.denominator,
        })
    return rows


def extract_case(executable: Path, d: int, timeout: float) -> dict[str, object]:
    polynomials = [singular_polynomial_integer(d + offset) for offset in range(3)]
    program = f"""option(redSB);
ring r=0,(x1,x2,x3),dp;
poly f0={polynomials[0]};
poly f1={polynomials[1]};
poly f2={polynomials[2]};
ideal I=f0,f1,f2;
ideal J=x3^{d};
matrix T=lift(I,J);
poly A=T[1,1];
poly B=T[2,1];
poly C=T[3,1];
poly remainder=x3^{d}-(A*f0+B*f1+C*f2);
ideal G=std(I);
poly lower=reduce(x3^{d-1},G);
print(\"R3_A_BEGIN\"); print(string(A)); print(\"R3_A_END\");
print(\"R3_B_BEGIN\"); print(string(B)); print(\"R3_B_END\");
print(\"R3_C_BEGIN\"); print(string(C)); print(\"R3_C_END\");
print(\"R3_REMAINDER_BEGIN\"); print(string(remainder)); print(\"R3_REMAINDER_END\");
print(\"R3_LOWER_BEGIN\"); print(string(lower)); print(\"R3_LOWER_END\");
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
    require(completed.returncode == 0, f"Singular lift failed at d={d}: {completed.stderr[-1000:]}")
    output = completed.stdout + "\n" + completed.stderr
    remainder = parse_marked(output, "REMAINDER")
    require(remainder == "0", f"Singular returned a nonzero lift remainder at d={d}")
    lower = parse_marked(output, "LOWER")
    require(lower != "0", f"unexpected smaller power x3^{d-1} in the ideal at d={d}")
    cofactors = {
        name: sparse_rational(parse_marked(output, name)) for name in ("A", "B", "C")
    }
    return {
        "d": d,
        "target": {"variable": "x3", "exponent": d},
        "cofactors": cofactors,
        "term_counts": {name: len(rows) for name, rows in cofactors.items()},
        "lower_power_remainder_nonzero": True,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d-min", type=int, default=2)
    parser.add_argument("--d-max", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(2 <= args.d_min <= args.d_max, "invalid d range")
    require(args.timeout > 0, "timeout must be positive")
    executable = args.singular.resolve()
    require(executable.is_file(), "Singular executable missing")
    hashes = {
        str(SCRIPT_PATH): sha256(SCRIPT_PATH),
        str(COMMON_PATH): sha256(COMMON_PATH),
        str(executable): sha256(executable),
    }
    cases = [extract_case(executable, d, args.timeout) for d in range(args.d_min, args.d_max + 1)]
    require(hashes == {
        str(SCRIPT_PATH): sha256(SCRIPT_PATH),
        str(COMMON_PATH): sha256(COMMON_PATH),
        str(executable): sha256(executable),
    }, "source or Singular executable changed during cofactor extraction")
    receipt = {
        "schema": "polydegree-r3-x3-cofactors-v1",
        "status": "PASS",
        "claim_boundary": (
            "Each row is an exact rational polynomial identity for one finite d; "
            "no recurrence or parameter-uniform identity is claimed."
        ),
        "d_min": args.d_min,
        "d_max": args.d_max,
        "cases": cases,
        "startup_sha256": hashes,
        "environment": {"python": platform.python_version(), "sympy": sp.__version__},
    }
    atomic_json_write(args.out, receipt)
    print(json.dumps({"status": "PASS", "cases": len(cases)}, sort_keys=True))
    print("cofactor receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, subprocess.TimeoutExpired) as exc:
        print(f"R3 COFACTOR EXTRACTION FAILED: {exc}")
        raise SystemExit(1)
