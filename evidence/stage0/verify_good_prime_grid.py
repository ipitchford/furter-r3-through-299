#!/usr/bin/env python3
"""Verify full-prime-map grid peers and their complete shard provenance."""

from __future__ import annotations

import argparse
import copy
import json
import platform
from pathlib import Path

from r3_common import R3Error, atomic_json_write, require, sha256
from run_good_prime_grid_shards import degree_ranges, shard_name
from verify_colength import (
    DEFAULT_SINGULAR,
    remove_timing,
    verify_formula_independence,
    verify_receipt,
)


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
ASSEMBLER_PATH = BASE / "assemble_good_prime_grid_shards.py"
LAUNCHER_PATH = BASE / "run_good_prime_grid_shards.py"
SOURCE_PATHS = (
    SCRIPT_PATH,
    ASSEMBLER_PATH,
    LAUNCHER_PATH,
    BASE / "verify_colength.py",
    BASE / "modular_colength.py",
    BASE / "r3_common.py",
)


def verify_grid_assembly(
    receipt: dict[str, object],
    variant: str,
    d_min: int,
    d_max: int,
    prime_max: int,
    chunk_size: int,
    shard_directory: Path,
) -> dict[str, str]:
    expected_ranges = degree_ranges(d_min, d_max, chunk_size)
    expected_names = [
        shard_name(variant, start, end, prime_max) for start, end in expected_ranges
    ]
    assembly = receipt.get("grid_assembly")
    require(isinstance(assembly, dict), f"{variant} receipt lacks grid assembly provenance")
    require(assembly.get("variant") == variant, f"{variant} assembly variant mismatch")
    require(assembly.get("gap_free") is True, f"{variant} assembly is not gap-free")
    require(
        assembly.get("ranges") == [list(pair) for pair in expected_ranges],
        f"{variant} assembly range inventory mismatch",
    )
    require(
        assembly.get("script_sha256") == sha256(ASSEMBLER_PATH),
        f"{variant} assembly binds stale assembler bytes",
    )
    require(
        assembly.get("launcher_sha256") == sha256(LAUNCHER_PATH),
        f"{variant} assembly binds stale launcher bytes",
    )
    inputs = assembly.get("inputs_sha256")
    timeouts = assembly.get("per_shard_timeout_seconds")
    require(isinstance(inputs, dict) and set(inputs) == set(expected_names),
            f"{variant} assembly shard inventory mismatch")
    require(isinstance(timeouts, dict) and set(timeouts) == set(expected_names),
            f"{variant} assembly timeout inventory mismatch")
    require(
        all(isinstance(timeouts[name], (int, float)) and timeouts[name] > 0 for name in expected_names),
        f"{variant} assembly contains an invalid timeout",
    )
    observed = {}
    for name in expected_names:
        path = shard_directory / name
        require(path.is_file(), f"{variant} grid shard is absent: {name}")
        observed[name] = sha256(path)
        require(observed[name] == inputs[name], f"{variant} grid shard hash mismatch: {name}")
    return observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    parser.add_argument("--d-min", type=int, default=2)
    parser.add_argument("--d-max", type=int, default=300)
    parser.add_argument("--prime-max", type=int, default=53)
    parser.add_argument("--chunk-size", type=int, default=5)
    parser.add_argument("--shard-directory", type=Path, default=BASE)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    input_path = args.input.resolve()
    peer_path = args.peer.resolve()
    shard_directory = args.shard_directory.resolve()
    singular = args.singular.resolve()
    require(input_path.is_file() and peer_path.is_file(), "grid peer input is absent")
    require(shard_directory.is_dir(), "grid shard directory is absent")
    require(singular.is_file(), "Singular executable is absent")
    require(args.out.resolve() not in {input_path, peer_path}, "output overwrites a grid peer")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    expected_ranges = degree_ranges(args.d_min, args.d_max, args.chunk_size)
    shard_paths = [
        shard_directory / shard_name(variant, start, end, args.prime_max)
        for variant in ("ordinary", "optimized")
        for start, end in expected_ranges
    ]
    watched_paths = [input_path, peer_path, singular, *shard_paths]
    require(all(path.is_file() for path in watched_paths), "one or more grid-verifier inputs are absent")
    startup_inputs = {str(path): sha256(path) for path in watched_paths}

    receipt = json.loads(input_path.read_text())
    peer = json.loads(peer_path.read_text())
    summary = verify_receipt(
        receipt, args.d_min, args.d_max, args.prime_max, False, singular
    )
    peer_summary = verify_receipt(
        peer, args.d_min, args.d_max, args.prime_max, False, singular
    )
    require(summary == peer_summary, "grid peer summaries differ")
    require(summary["first_good"] is False, "grid receipt is first-GOOD truncated")
    require(
        remove_timing(copy.deepcopy(receipt)) == remove_timing(copy.deepcopy(peer)),
        "ordinary/optimized grid mathematical projections differ",
    )
    ordinary_shards = verify_grid_assembly(
        receipt,
        "ordinary",
        args.d_min,
        args.d_max,
        args.prime_max,
        args.chunk_size,
        shard_directory,
    )
    optimized_shards = verify_grid_assembly(
        peer,
        "optimized",
        args.d_min,
        args.d_max,
        args.prime_max,
        args.chunk_size,
        shard_directory,
    )
    formula = verify_formula_independence()

    mutation = copy.deepcopy(receipt)
    mutation["grid_assembly"]["inputs_sha256"].pop(next(iter(ordinary_shards)))
    missing_shard_rejected = False
    try:
        verify_grid_assembly(
            mutation,
            "ordinary",
            args.d_min,
            args.d_max,
            args.prime_max,
            args.chunk_size,
            shard_directory,
        )
    except R3Error:
        missing_shard_rejected = True
    require(missing_shard_rejected, "missing-shard mutation was not rejected")
    require(
        {path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
        "grid-verifier source changed during execution",
    )
    require(
        {str(path): sha256(path) for path in watched_paths} == startup_inputs,
        "grid-verifier input changed during execution",
    )
    output = {
        "schema": "polydegree-r3-modular-colength-verification-v1",
        "status": "PASS",
        "input_sha256": startup_inputs[str(input_path)],
        "summary": summary,
        "formula_independence": formula,
        "peer_parity": {
            "peer_sha256": startup_inputs[str(peer_path)],
            "timing_free_projection_equal": True,
        },
        "grid_provenance": {
            "ordinary_shards_sha256": ordinary_shards,
            "optimized_shards_sha256": optimized_shards,
            "missing_shard_mutation_rejected": missing_shard_rejected,
        },
        "source_sha256": startup_sources,
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(args.out, output)
    print(json.dumps({"status": "PASS", **summary}, sort_keys=True))
    print("grid verification receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 GOOD-PRIME GRID VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
