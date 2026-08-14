#!/usr/bin/env python3
"""Assemble structurally verified R(3) full-prime-map grid shards."""

from __future__ import annotations

import argparse
import copy
import json
import platform
from pathlib import Path

from r3_common import R3Error, atomic_json_write, require, sha256
from run_good_prime_grid_shards import degree_ranges, shard_name
from verify_colength import DEFAULT_SINGULAR, remove_timing, verify_receipt


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
SOURCE_PATHS = (
    SCRIPT_PATH,
    BASE / "run_good_prime_grid_shards.py",
    BASE / "r3_common.py",
    BASE / "modular_colength.py",
    BASE / "verify_colength.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("ordinary", "optimized"), required=True)
    parser.add_argument("--d-min", type=int, default=2)
    parser.add_argument("--d-max", type=int, default=300)
    parser.add_argument("--prime-max", type=int, default=53)
    parser.add_argument("--chunk-size", type=int, default=5)
    parser.add_argument("--shard-directory", type=Path, default=BASE)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    singular = args.singular.resolve()
    shard_directory = args.shard_directory.resolve()
    require(singular.is_file(), "Singular executable is absent")
    require(shard_directory.is_dir(), "shard directory is absent")
    ranges = degree_ranges(args.d_min, args.d_max, args.chunk_size)
    shard_paths = [
        shard_directory / shard_name(args.variant, start, end, args.prime_max)
        for start, end in ranges
    ]
    require(all(path.is_file() for path in shard_paths), "one or more grid shards are absent")
    require(args.out.resolve() not in {path.resolve() for path in shard_paths}, "output overwrites a shard")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {path.name: sha256(path) for path in shard_paths}

    rows: list[dict[str, object]] = []
    coverage: set[int] = set()
    counts = {"rows": 0, "good": 0, "bad": 0, "incomplete": 0}
    startup = None
    environment = None
    controls = None
    timeouts: dict[str, float] = {}
    for (start, end), path in zip(ranges, shard_paths, strict=True):
        receipt = json.loads(path.read_text())
        summary = verify_receipt(receipt, start, end, args.prime_max, False, singular)
        require(summary["first_good"] is False, f"grid shard is truncated: {path.name}")
        parameters = receipt["parameters"]
        timeout = parameters["timeout_seconds"]
        require(isinstance(timeout, (int, float)) and timeout > 0, "invalid shard timeout")
        timeouts[path.name] = float(timeout)
        if startup is None:
            startup = receipt["startup_sha256"]
            environment = receipt["environment"]
            controls = receipt["controls"]
        else:
            require(receipt["startup_sha256"] == startup, "grid shard source/runtime mismatch")
            require(
                remove_timing(copy.deepcopy(receipt["environment"]))
                == remove_timing(copy.deepcopy(environment)),
                "grid shard environment mismatch",
            )
        rows.extend(receipt["rows"])
        coverage.update(receipt["good_degree_coverage"])
        for key in counts:
            counts[key] += receipt["counts"][key]

    require(counts["incomplete"] == 0, "grid contains incomplete cases")
    output = {
        "schema": "polydegree-r3-modular-colength-v1",
        "status": "PASS",
        "claim_boundary": (
            "This is a finite full-prime-map experiment. GOOD rows certify their finite "
            "R(3) instances; absence of a GOOD row in this bounded prime set does not refute R(3)."
        ),
        "parameters": {
            "d_min": args.d_min,
            "d_max": args.d_max,
            "primes": receipt["parameters"]["primes"],
            "first_good": False,
            "timeout_seconds": min(timeouts.values()),
        },
        "controls": controls,
        "rows": rows,
        "incomplete": [],
        "good_degree_coverage": sorted(coverage),
        "counts": counts,
        "environment": {**environment, "assembly_python": platform.python_version()},
        "startup_sha256": startup,
        "grid_assembly": {
            "variant": args.variant,
            "ranges": [list(pair) for pair in ranges],
            "gap_free": True,
            "inputs_sha256": startup_inputs,
            "per_shard_timeout_seconds": timeouts,
            "script_sha256": sha256(SCRIPT_PATH),
            "launcher_sha256": sha256(BASE / "run_good_prime_grid_shards.py"),
        },
    }
    summary = verify_receipt(
        output, args.d_min, args.d_max, args.prime_max, False, singular
    )
    require(summary["row_count"] == counts["rows"], "assembled row count mismatch")
    require(
        {path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
        "grid assembler source changed during execution",
    )
    require(
        {path.name: sha256(path) for path in shard_paths} == startup_inputs,
        "grid shard changed during assembly",
    )
    atomic_json_write(args.out, output)
    print(json.dumps({"status": "PASS", **summary}, sort_keys=True))
    print("assembled grid:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 GOOD-PRIME GRID ASSEMBLY FAILED: {exc}")
        raise SystemExit(1)
