#!/usr/bin/env python3
"""Probe compact pure-power initial-ideal signatures at certified GOOD primes."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
from collections import Counter
from pathlib import Path

from analyze_good_prime_frontier import require_verification_binding
from r3_common import (
    R3Error,
    atomic_json_write,
    bezout_colength,
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
    BASE / "verify_colength.py",
    BASE / "analyze_good_prime_frontier.py",
)


def pure_initial_signature(
    singular: Path, d: int, prime: int, timeout: float
) -> dict[str, object]:
    polynomials = [singular_polynomial(d + offset, prime) for offset in range(3)]
    program = f"""option(redSB);
ring r={prime},(x1,x2,x3),dp;
ideal I={','.join(polynomials)};
ideal G=std(I);
intvec e;
print("R3_SIZE="+string(size(G)));
print("R3_VDIM="+string(vdim(G)));
for (int i=1; i<=size(G); i++) {{
  e=leadexp(G[i]);
  print("R3_LE="+string(e));
}}
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
    require(completed.returncode == 0, f"Singular signature probe failed at d={d}, p={prime}")
    combined = completed.stdout + "\n" + completed.stderr
    size_matches = re.findall(r"^R3_SIZE=(\d+)\s*$", combined, flags=re.MULTILINE)
    vdim_matches = re.findall(r"^R3_VDIM=(-?\d+)\s*$", combined, flags=re.MULTILINE)
    exponent_matches = re.findall(r"^R3_LE=([0-9]+,[0-9]+,[0-9]+)\s*$", combined, flags=re.MULTILINE)
    require(len(size_matches) == 1 and len(vdim_matches) == 1, "signature markers are ambiguous")
    basis_size = int(size_matches[0])
    exponents = [tuple(int(piece) for piece in raw.split(",")) for raw in exponent_matches]
    require(len(exponents) == basis_size, "leading-exponent inventory does not match basis size")
    require(int(vdim_matches[0]) == bezout_colength(d), "signature probe colength mismatch")
    pure = {}
    for axis in range(3):
        candidates = [
            exponent[axis]
            for exponent in exponents
            if exponent[axis] > 0
            and all(exponent[other] == 0 for other in range(3) if other != axis)
        ]
        require(candidates, f"initial ideal lacks a pure power on axis {axis + 1}")
        pure[f"x{axis + 1}"] = min(candidates)
    return {"basis_size": basis_size, "pure_initial_exponents": pure}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--expected-d-min", type=int, required=True)
    parser.add_argument("--expected-d-max", type=int, required=True)
    parser.add_argument("--expected-prime-max", type=int, default=997)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.timeout > 0, "timeout must be positive")
    map_path = args.map.resolve()
    verification_path = args.verification.resolve()
    singular = args.singular.resolve()
    watched_paths = [map_path, verification_path, singular]
    require(all(path.is_file() for path in watched_paths), "one or more probe inputs are absent")
    require(args.out.resolve() not in set(watched_paths), "probe output overwrites an input")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {str(path): sha256(path) for path in watched_paths}

    modular_map = json.loads(map_path.read_text())
    verification = json.loads(verification_path.read_text())
    summary = verify_receipt(
        modular_map,
        args.expected_d_min,
        args.expected_d_max,
        args.expected_prime_max,
        True,
        singular,
    )
    require_verification_binding(verification, map_path, summary)
    smallest_good: dict[int, int] = {}
    for row in modular_map["rows"]:
        if row["classification"] == "GOOD":
            d = row["d"]
            smallest_good[d] = min(smallest_good.get(d, row["prime"]), row["prime"])
    require(
        sorted(smallest_good) == list(range(args.expected_d_min, args.expected_d_max + 1)),
        "smallest-GOOD degree inventory is incomplete",
    )

    rows = []
    for d in range(args.expected_d_min, args.expected_d_max + 1):
        prime = smallest_good[d]
        rows.append(
            {
                "d": d,
                "prime": prime,
                **pure_initial_signature(singular, d, prime, args.timeout),
            }
        )
    require(
        {path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
        "signature-probe source changed during execution",
    )
    require(
        {str(path): sha256(path) for path in watched_paths} == startup_inputs,
        "signature-probe input or Singular executable changed during execution",
    )
    exact_diagonal = [
        row["d"]
        for row in rows
        if list(row["pure_initial_exponents"].values()) == [row["d"]] * 3
    ]
    deviations = [row for row in rows if row["d"] not in exact_diagonal]
    offset_histogram = Counter(
        tuple(row["pure_initial_exponents"][f"x{axis}"] - row["d"] for axis in range(1, 4))
        for row in rows
    )
    output = {
        "schema": "polydegree-r3-groebner-signature-probe-v1",
        "status": "PASS",
        "claim_boundary": (
            "Producer-side finite Gröbner-signature evidence only; no all-degree "
            "transition law or independent Gröbner reconstruction is claimed."
        ),
        "degree_range": {
            "d_min": args.expected_d_min,
            "d_max": args.expected_d_max,
            "count": len(rows),
        },
        "monomial_order": "Singular dp on (x1,x2,x3)",
        "rows": rows,
        "summary": {
            "exact_diagonal_count": len(exact_diagonal),
            "exact_diagonal_degrees": exact_diagonal,
            "deviation_count": len(deviations),
            "deviation_degrees": [row["d"] for row in deviations],
            "maximum_basis_size": max(row["basis_size"] for row in rows),
            "minimum_basis_size": min(row["basis_size"] for row in rows),
            "pure_exponent_offset_states": [
                {"offset": list(offset), "count": offset_histogram[offset]}
                for offset in sorted(offset_histogram)
            ],
        },
        "inputs_sha256": {
            map_path.name: startup_inputs[str(map_path)],
            verification_path.name: startup_inputs[str(verification_path)],
        },
        "source_sha256": startup_sources,
        "runtime_sha256": {singular.name: startup_inputs[str(singular)]},
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(args.out, output)
    print(json.dumps({"status": "PASS", **output["summary"]}, sort_keys=True))
    print("signature receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError, subprocess.SubprocessError) as exc:
        print(f"R3 GROEBNER SIGNATURE PROBE FAILED: {exc}")
        raise SystemExit(1)
