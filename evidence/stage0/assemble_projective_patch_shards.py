#!/usr/bin/env python3
"""Assemble exact projective-patch shards into one canonical screen."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

from projective_patch_screen import COMMON_PATH, SCRIPT_PATH as PRODUCER_PATH
from r3_common import R3Error, atomic_json_write, require, sha256
from run_projective_patch_shards import ranges, shard_name
from verify_projective_patch_screen import validate_receipt


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
VERIFIER_PATH = BASE / "verify_projective_patch_screen.py"
LAUNCHER_PATH = BASE / "run_projective_patch_shards.py"
SOURCE_PATHS = (
    SCRIPT_PATH,
    PRODUCER_PATH,
    COMMON_PATH,
    VERIFIER_PATH,
    LAUNCHER_PATH,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-directory", type=Path, default=BASE)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    directory = args.shard_directory.resolve()
    singular = args.singular.resolve()
    output = args.out.resolve()
    require(directory.is_dir() and singular.is_file(), "assembler input or runtime is absent")
    require(output not in {singular, *SOURCE_PATHS}, "assembler output overwrites source or runtime")
    require(not output.exists(), "refusing to overwrite assembled patch screen")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    shard_hashes = {}
    cases = []
    coverage = []
    counts = {"degrees": 0, "attempts": 0, "good": 0, "bad": 0, "timeout": 0}
    controls = None
    source_hashes = None
    runtime_hashes = None
    environment = None
    prime_inventory = None
    cover_inventory = None
    timeout_values = []
    for start, end in ranges():
        path = directory / shard_name(start, end)
        require(path.is_file(), f"missing patch shard: {path.name}")
        receipt = json.loads(path.read_text())
        validate_receipt(receipt, start, end, 997, singular)
        shard_hashes[path.name] = sha256(path)
        if controls is None:
            controls = receipt["controls"]
            source_hashes = receipt["source_sha256"]
            runtime_hashes = receipt["runtime_sha256"]
            environment = receipt["environment"]
            prime_inventory = receipt["parameters"]["primes"]
            cover_inventory = receipt["cover"]
        else:
            require(receipt["controls"] == controls, "patch shard controls differ")
            require(receipt["source_sha256"] == source_hashes,
                    "patch shard producer sources differ")
            require(receipt["runtime_sha256"] == runtime_hashes,
                    "patch shard runtimes differ")
            require(receipt["environment"] == environment,
                    "patch shard environments differ")
            require(receipt["parameters"]["primes"] == prime_inventory,
                    "patch shard prime inventories differ")
            require(receipt["cover"] == cover_inventory,
                    "patch shard cover inventories differ")
        cases.extend(receipt["cases"])
        coverage.extend(receipt["good_degree_coverage"])
        timeout_values.append(receipt["parameters"]["timeout_seconds_per_stratum"])
        for key in counts:
            counts[key] += receipt["counts"][key]
    require([case["d"] for case in cases] == list(range(50, 301)),
            "assembled patch case range is not gap-free")
    require(coverage == list(range(50, 301)), "assembled patch GOOD coverage is incomplete")
    receipt = {
        "schema": "polydegree-r3-projective-patch-screen-v1",
        "status": "PASS",
        "claim_boundary": (
            "A GOOD row is an exact empty weighted-projective special-fibre certificate "
            "from the complete three-stratum cover. BAD rows certify a nonempty special "
            "fibre only; TIMEOUT rows carry no mathematical conclusion."
        ),
        "parameters": {
            "d_min": 50,
            "d_max": 300,
            "primes": prime_inventory,
            "timeout_seconds_per_stratum": min(timeout_values),
            "selection": "first completed GOOD after exact BAD rows and skipped timeouts",
        },
        "cover": cover_inventory,
        "controls": controls,
        "cases": cases,
        "good_degree_coverage": coverage,
        "counts": counts,
        "source_sha256": source_hashes,
        "runtime_sha256": runtime_hashes,
        "environment": {**environment, "assembly_python": platform.python_version()},
        "assembly": {
            "ranges": [list(pair) for pair in ranges()],
            "gap_free": True,
            "inputs_sha256": shard_hashes,
            "script_sha256": sha256(SCRIPT_PATH),
        },
    }
    validate_receipt(receipt, 50, 300, 997, singular)
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "assembler source changed during execution")
    require(all(sha256(directory / name) == digest for name, digest in shard_hashes.items()),
            "patch shard changed during assembly")
    atomic_json_write(output, receipt)
    print(json.dumps({"status": "PASS", **counts}, sort_keys=True))
    print("assembled projective patch screen:", output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 PROJECTIVE PATCH ASSEMBLY FAILED: {exc}")
        raise SystemExit(1)
