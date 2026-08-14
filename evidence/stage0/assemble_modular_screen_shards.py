#!/usr/bin/env python3
"""Assemble fully verified modular-screen range shards into canonical peers."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
from pathlib import Path

from r3_common import R3Error, atomic_json_write, require, sha256
from verify_colength import DEFAULT_SINGULAR, remove_timing, verify_receipt


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
SOURCE_PATHS = (
    SCRIPT_PATH,
    BASE / "r3_common.py",
    BASE / "modular_colength.py",
    BASE / "verify_colength.py",
)


def read_frozen_json(path: Path) -> tuple[dict[str, object], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    value = json.loads(raw)
    require(isinstance(value, dict), f"JSON root is not an object: {path.name}")
    require(sha256(path) == digest, f"input changed while reading: {path.name}")
    return value, digest


def ranges() -> list[tuple[int, int]]:
    return [(start, min(start + 9, 300)) for start in range(50, 301, 10)]


def shard_name(variant: str, start: int, end: int) -> str:
    return f"screen-shard-{variant}-d{start:03}-{end:03}.json"


def assemble_variant(
    variant: str, directory: Path, output: Path, singular: Path,
    startup_sources: dict[str, str],
) -> dict[str, object]:
    shards = []
    input_hashes = {}
    startup = None
    environment = None
    controls = None
    rows = []
    coverage = []
    shard_timeouts = {}
    counts = {"rows": 0, "good": 0, "bad": 0, "incomplete": 0}
    for start, end in ranges():
        path = directory / shard_name(variant, start, end)
        require(path.is_file(), f"missing modular shard: {path.name}")
        receipt, input_digest = read_frozen_json(path)
        verify_receipt(receipt, start, end, 997, True, singular)
        shard_timeout = receipt.get("parameters", {}).get("timeout_seconds")
        require(isinstance(shard_timeout, (int, float)) and shard_timeout >= 1800.0,
                f"modular shard timeout is below the 1800-second floor: {path.name}")
        shard_timeouts[path.name] = float(shard_timeout)
        if startup is None:
            startup = receipt["startup_sha256"]
            environment = receipt["environment"]
            controls = receipt["controls"]
        else:
            require(receipt["startup_sha256"] == startup,
                    f"modular shard source/runtime mismatch: {path.name}")
            require(remove_timing(copy.deepcopy(receipt["environment"])) ==
                    remove_timing(copy.deepcopy(environment)),
                    f"modular shard environment mismatch: {path.name}")
        rows.extend(receipt["rows"])
        coverage.extend(receipt["good_degree_coverage"])
        for key in counts:
            counts[key] += receipt["counts"][key]
        input_hashes[path.name] = input_digest
        shards.append([start, end])
    require(shards == ranges(), "modular shard range inventory is not exact")
    require(coverage == list(range(50, 301)), "modular shard coverage is not gap-free")
    require(counts["incomplete"] == 0, "modular shards contain incomplete cases")
    output_receipt = {
        "schema": "polydegree-r3-modular-colength-v1",
        "status": "PASS",
        "claim_boundary": (
            "GOOD rows are exact finite-instance R(3) certificates via empty special fibre; "
            "BAD rows are discovery/divisibility evidence only."
        ),
        "parameters": {
            "d_min": 50,
            "d_max": 300,
            "primes": list(range(0)),
            "first_good": True,
            "timeout_seconds": min(shard_timeouts.values()),
        },
        "controls": controls,
        "rows": rows,
        "incomplete": [],
        "good_degree_coverage": coverage,
        "counts": counts,
        "environment": {
            **environment,
            "assembly_python": platform.python_version(),
        },
        "startup_sha256": startup,
        "assembly": {
            "variant": variant,
            "ranges": shards,
            "gap_free": True,
            "inputs_sha256": input_hashes,
            "per_shard_timeout_seconds": shard_timeouts,
            "script_sha256": sha256(SCRIPT_PATH),
        },
    }
    output_receipt["parameters"]["primes"] = receipt["parameters"]["primes"]
    verify_receipt(output_receipt, 50, 300, 997, True, singular)
    require(all(sha256(directory / name) == expected
                for name, expected in input_hashes.items()),
            "a modular shard changed before assembled publication")
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "a modular assembler source changed before publication")
    atomic_json_write(output, output_receipt)
    return output_receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-directory", type=Path, default=BASE)
    parser.add_argument("--ordinary-out", type=Path, required=True)
    parser.add_argument("--optimized-out", type=Path, required=True)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    args = parser.parse_args()
    singular = args.singular.resolve()
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    ordinary = assemble_variant(
        "ordinary", args.shard_directory, args.ordinary_out, singular,
        startup_sources,
    )
    optimized = assemble_variant(
        "optimized", args.shard_directory, args.optimized_out, singular,
        startup_sources,
    )
    require(remove_timing(copy.deepcopy(ordinary)) == remove_timing(copy.deepcopy(optimized)),
            "ordinary/optimized assembled modular screens differ outside timing")
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "a modular assembler source changed during assembly")
    print(json.dumps({
        "status": "PASS",
        "rows": ordinary["counts"]["rows"],
        "good": ordinary["counts"]["good"],
        "bad": ordinary["counts"]["bad"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 MODULAR ASSEMBLY FAILED: {exc}")
        raise SystemExit(1)
