#!/usr/bin/env python3
"""Parallel launcher for resumable exact modular-screen range shards."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from r3_common import R3Error, require


BASE = Path(__file__).resolve().parent
PRODUCER = BASE / "modular_colength.py"


def ranges() -> list[tuple[int, int]]:
    return [(start, min(start + 9, 300)) for start in range(50, 301, 10)]


def shard_name(variant: str, start: int, end: int) -> str:
    return f"screen-shard-{variant}-d{start:03}-{end:03}.json"


def run_one(
    variant: str, start: int, end: int, singular: Path, timeout: float, resume: bool
) -> dict[str, object]:
    output = BASE / shard_name(variant, start, end)
    if output.exists():
        require(resume, f"refusing existing shard without --resume: {output.name}")
        return {"range": [start, end], "state": "REUSED", "output": output.name}
    command = [sys.executable]
    if variant == "optimized":
        command.append("-O")
    command.extend([
        str(PRODUCER),
        "--d-min", str(start),
        "--d-max", str(end),
        "--prime-max", "997",
        "--first-good",
        "--timeout", str(timeout),
        "--singular", str(singular),
        "--out", str(output),
    ])
    completed = subprocess.run(
        command,
        cwd=BASE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    require(completed.returncode == 0,
            f"{variant} shard {start}..{end} failed:\n{completed.stdout[-2000:]}")
    return {"range": [start, end], "state": "COMPUTED", "output": output.name}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("ordinary", "optimized"), required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    require(args.workers >= 1, "workers must be positive")
    singular = args.singular.resolve()
    require(singular.is_file(), "Singular executable is absent")
    completed_rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                run_one, args.variant, start, end, singular, args.timeout, args.resume
            ): (start, end)
            for start, end in ranges()
        }
        for future in as_completed(futures):
            row = future.result()
            completed_rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    require(len(completed_rows) == len(ranges()), "launcher did not finish every range")
    print(json.dumps({
        "status": "PASS",
        "variant": args.variant,
        "shards": len(completed_rows),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, OSError, subprocess.SubprocessError) as exc:
        print(f"R3 MODULAR SHARD LAUNCH FAILED: {exc}")
        raise SystemExit(1)
