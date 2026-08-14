#!/usr/bin/env python3
"""Launch resumable full-prime-map shards for the R(3) good-prime frontier."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from r3_common import R3Error, require
from verify_colength import DEFAULT_SINGULAR, verify_receipt


BASE = Path(__file__).resolve().parent
PRODUCER = BASE / "modular_colength.py"


def degree_ranges(d_min: int, d_max: int, chunk_size: int) -> list[tuple[int, int]]:
    require(2 <= d_min <= d_max, "invalid degree range")
    require(chunk_size >= 1, "chunk size must be positive")
    return [
        (start, min(start + chunk_size - 1, d_max))
        for start in range(d_min, d_max + 1, chunk_size)
    ]


def shard_name(variant: str, start: int, end: int, prime_max: int) -> str:
    return f"good-prime-grid-{variant}-d{start:03d}-{end:03d}-p{prime_max:03d}.json"


def run_one(
    variant: str,
    start: int,
    end: int,
    prime_max: int,
    singular: Path,
    timeout: float,
    output_directory: Path,
    resume: bool,
) -> dict[str, object]:
    output = output_directory / shard_name(variant, start, end, prime_max)
    if output.exists():
        require(resume, f"refusing existing shard without --resume: {output.name}")
        receipt = json.loads(output.read_text())
        summary = verify_receipt(receipt, start, end, prime_max, False, singular)
        require(summary["first_good"] is False, "reused grid shard is first-GOOD truncated")
        return {"range": [start, end], "state": "REUSED_VERIFIED", "output": output.name}

    command = [sys.executable]
    if variant == "optimized":
        command.append("-O")
    command.extend(
        [
            str(PRODUCER),
            "--d-min",
            str(start),
            "--d-max",
            str(end),
            "--prime-max",
            str(prime_max),
            "--timeout",
            str(timeout),
            "--singular",
            str(singular),
            "--out",
            str(output),
        ]
    )
    completed = subprocess.run(
        command,
        cwd=BASE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    require(
        completed.returncode == 0,
        f"{variant} grid shard {start}..{end} failed:\n{completed.stdout[-2000:]}",
    )
    receipt = json.loads(output.read_text())
    summary = verify_receipt(receipt, start, end, prime_max, False, singular)
    require(summary["first_good"] is False, "computed grid shard is first-GOOD truncated")
    return {"range": [start, end], "state": "COMPUTED_VERIFIED", "output": output.name}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("ordinary", "optimized"), required=True)
    parser.add_argument("--d-min", type=int, default=2)
    parser.add_argument("--d-max", type=int, default=300)
    parser.add_argument("--prime-max", type=int, default=53)
    parser.add_argument("--chunk-size", type=int, default=5)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--output-directory", type=Path, default=BASE)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    require(args.workers >= 1, "workers must be positive")
    require(args.timeout > 0, "timeout must be positive")
    require(args.prime_max >= 2, "prime maximum must be at least two")
    singular = args.singular.resolve()
    output_directory = args.output_directory.resolve()
    require(singular.is_file(), "Singular executable is absent")
    output_directory.mkdir(parents=True, exist_ok=True)
    ranges = degree_ranges(args.d_min, args.d_max, args.chunk_size)

    completed_rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                run_one,
                args.variant,
                start,
                end,
                args.prime_max,
                singular,
                args.timeout,
                output_directory,
                args.resume,
            ): (start, end)
            for start, end in ranges
        }
        for future in as_completed(futures):
            row = future.result()
            completed_rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    require(len(completed_rows) == len(ranges), "launcher did not finish every range")
    print(
        json.dumps(
            {
                "status": "PASS",
                "variant": args.variant,
                "ranges": len(completed_rows),
                "d_min": args.d_min,
                "d_max": args.d_max,
                "prime_max": args.prime_max,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError, subprocess.SubprocessError) as exc:
        print(f"R3 GOOD-PRIME GRID LAUNCH FAILED: {exc}")
        raise SystemExit(1)
