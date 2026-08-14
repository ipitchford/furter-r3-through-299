#!/usr/bin/env python3
"""Parallel resumable launcher for projective-patch degree shards."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from r3_common import R3Error, require


BASE = Path(__file__).resolve().parent
PRODUCER = BASE / "projective_patch_screen.py"


def ranges() -> list[tuple[int, int]]:
    return [(start, min(start + 9, 300)) for start in range(50, 301, 10)]


def shard_name(start: int, end: int) -> str:
    return f"projective-patch-shard-d{start:03}-{end:03}.json"


def run_one(
    start: int, end: int, singular: Path, timeout: float, resume: bool
) -> dict[str, object]:
    output = BASE / shard_name(start, end)
    if output.exists():
        require(resume, f"refusing existing shard without --resume: {output.name}")
        return {"range": [start, end], "state": "REUSED", "output": output.name}
    command = [
        sys.executable,
        str(PRODUCER),
        "--d-min", str(start),
        "--d-max", str(end),
        "--prime-max", "997",
        "--timeout", str(timeout),
        "--singular", str(singular),
        "--out", str(output),
    ]
    completed = subprocess.run(
        command, cwd=BASE, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
    )
    require(completed.returncode == 0,
            f"patch shard {start}..{end} failed:\n{completed.stdout[-2000:]}")
    return {"range": [start, end], "state": "COMPUTED", "output": output.name}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    require(args.workers >= 1 and args.timeout > 0, "invalid launcher workers or timeout")
    singular = args.singular.resolve()
    require(singular.is_file(), "Singular executable is absent")
    completed_rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(run_one, start, end, singular, args.timeout, args.resume):
                (start, end)
            for start, end in ranges()
        }
        for future in as_completed(futures):
            row = future.result()
            completed_rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    require(len(completed_rows) == len(ranges()), "launcher did not finish every patch shard")
    print(json.dumps({"status": "PASS", "shards": len(completed_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, OSError, subprocess.SubprocessError) as exc:
        print(f"R3 PROJECTIVE PATCH SHARD LAUNCH FAILED: {exc}")
        raise SystemExit(1)
