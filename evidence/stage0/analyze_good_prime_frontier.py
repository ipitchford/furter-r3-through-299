#!/usr/bin/env python3
"""Derive an auditable smallest-GOOD-prime frontier from verified R(3) maps."""

from __future__ import annotations

import argparse
import json
import platform
from collections import Counter
from pathlib import Path

from r3_common import R3Error, atomic_json_write, require, sha256
from verify_colength import DEFAULT_SINGULAR, verify_receipt


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
SOURCE_PATHS = (
    SCRIPT_PATH,
    BASE / "r3_common.py",
    BASE / "verify_colength.py",
    BASE / "modular_colength.py",
)


def require_verification_binding(
    verification: dict[str, object], input_path: Path, summary: dict[str, object]
) -> None:
    require(
        verification.get("schema") == "polydegree-r3-modular-colength-verification-v1",
        f"wrong verification schema for {input_path.name}",
    )
    require(verification.get("status") == "PASS", f"verification is not PASS: {input_path.name}")
    require(
        verification.get("input_sha256") == sha256(input_path),
        f"verification does not bind {input_path.name}",
    )
    require(
        verification.get("summary") == summary,
        f"verification summary mismatch for {input_path.name}",
    )
    source_hashes = verification.get("source_sha256")
    require(isinstance(source_hashes, dict), "verification lacks source bindings")
    require(
        source_hashes.get("verify_colength.py") == sha256(BASE / "verify_colength.py"),
        f"verification binds a stale verifier for {input_path.name}",
    )
    parity = verification.get("peer_parity")
    require(
        isinstance(parity, dict)
        and parity.get("timing_free_projection_equal") is True
        and isinstance(parity.get("peer_sha256"), str),
        f"verification lacks ordinary/optimized parity for {input_path.name}",
    )


def require_gap_free_ranges(
    ranges: list[tuple[int, int]], expected_min: int, expected_max: int
) -> None:
    require(expected_min <= expected_max, "invalid expected degree range")
    ordered = sorted(ranges)
    cursor = expected_min
    for start, end in ordered:
        require(start == cursor, f"degree ranges overlap or leave a gap at d={cursor}")
        require(start <= end, "degree range has reversed endpoints")
        cursor = end + 1
    require(cursor == expected_max + 1, f"degree ranges end before d={expected_max}")


def derive_frontier(
    receipts: list[dict[str, object]], expected_min: int, expected_max: int
) -> dict[str, object]:
    good_by_degree: dict[int, list[int]] = {}
    attempted_by_degree: dict[int, list[int]] = {}
    modes: list[dict[str, object]] = []
    for receipt in receipts:
        parameters = receipt["parameters"]
        start = parameters["d_min"]
        end = parameters["d_max"]
        first_good = parameters["first_good"]
        modes.append({"d_min": start, "d_max": end, "first_good": first_good})
        for row in receipt["rows"]:
            d = row["d"]
            prime = row["prime"]
            attempted_by_degree.setdefault(d, []).append(prime)
            if row["classification"] == "GOOD":
                good_by_degree.setdefault(d, []).append(prime)

    expected_degrees = list(range(expected_min, expected_max + 1))
    require(sorted(attempted_by_degree) == expected_degrees, "attempted degree inventory is not exact")
    require(sorted(good_by_degree) == expected_degrees, "one or more degrees have no GOOD prime")
    smallest = {d: min(good_by_degree[d]) for d in expected_degrees}
    histogram = Counter(smallest.values())
    largest_smallest = max(smallest.values())
    maximizers = [d for d in expected_degrees if smallest[d] == largest_smallest]
    require(sum(histogram.values()) == len(expected_degrees), "frontier histogram count mismatch")

    return {
        "degree_range": {"d_min": expected_min, "d_max": expected_max, "count": len(expected_degrees)},
        "smallest_good_prime_by_degree": [
            {"d": d, "prime": smallest[d]} for d in expected_degrees
        ],
        "smallest_good_prime_histogram": {
            str(prime): histogram[prime] for prime in sorted(histogram)
        },
        "largest_smallest_good_prime": largest_smallest,
        "degrees_attaining_largest_smallest_prime": maximizers,
        "observed_smallest_good_primes": sorted(histogram),
        "input_modes": modes,
        "all_input_ranges_are_full_prime_maps": all(
            mode["first_good"] is False for mode in modes
        ),
        "contains_first_good_truncation": any(mode["first_good"] is True for mode in modes),
        "attempted_row_count": sum(len(values) for values in attempted_by_degree.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--verification", type=Path, action="append", required=True)
    parser.add_argument("--expected-d-min", type=int, required=True)
    parser.add_argument("--expected-d-max", type=int, required=True)
    parser.add_argument("--expected-prime-max", type=int, default=997)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    require(len(args.input) == len(args.verification), "input/verification counts differ")
    require(args.input, "at least one verified map is required")
    input_paths = [path.resolve() for path in args.input]
    verification_paths = [path.resolve() for path in args.verification]
    singular = args.singular.resolve()
    watched_paths = [*input_paths, *verification_paths, singular]
    require(all(path.is_file() for path in watched_paths), "one or more inputs are absent")
    require(args.out.resolve() not in set(watched_paths), "output must not overwrite an input")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {str(path): sha256(path) for path in watched_paths}

    receipts: list[dict[str, object]] = []
    ranges: list[tuple[int, int]] = []
    input_bindings: list[dict[str, object]] = []
    for input_path, verification_path in zip(input_paths, verification_paths, strict=True):
        receipt = json.loads(input_path.read_text())
        verification = json.loads(verification_path.read_text())
        parameters = receipt.get("parameters")
        require(isinstance(parameters, dict), f"missing parameters in {input_path.name}")
        start = parameters.get("d_min")
        end = parameters.get("d_max")
        require(isinstance(start, int) and isinstance(end, int), "invalid degree endpoints")
        summary = verify_receipt(
            receipt, start, end, args.expected_prime_max, True, singular
        )
        require_verification_binding(verification, input_path, summary)
        ranges.append((start, end))
        receipts.append(receipt)
        input_bindings.append(
            {
                "map": input_path.name,
                "map_sha256": startup_inputs[str(input_path)],
                "verification": verification_path.name,
                "verification_sha256": startup_inputs[str(verification_path)],
            }
        )

    require_gap_free_ranges(ranges, args.expected_d_min, args.expected_d_max)
    frontier = derive_frontier(receipts, args.expected_d_min, args.expected_d_max)

    mutated_ranges = ranges[:-1]
    mutation_rejected = False
    try:
        require_gap_free_ranges(mutated_ranges, args.expected_d_min, args.expected_d_max)
    except R3Error:
        mutation_rejected = True
    require(mutation_rejected, "missing-range negative control was not rejected")
    require(
        {path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
        "frontier analyzer source changed during execution",
    )
    require(
        {str(path): sha256(path) for path in watched_paths} == startup_inputs,
        "frontier input or Singular executable changed during execution",
    )
    output = {
        "schema": "polydegree-r3-good-prime-frontier-v1",
        "status": "PASS",
        "claim_boundary": (
            "This receipt proves only the displayed finite smallest-GOOD-prime frontier. "
            "It does not prove that a bounded prime set works for every degree."
        ),
        **frontier,
        "negative_controls": {"missing_terminal_range_rejected": mutation_rejected},
        "inputs": input_bindings,
        "source_sha256": startup_sources,
        "runtime_sha256": {singular.name: startup_inputs[str(singular)]},
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(args.out, output)
    print(
        json.dumps(
            {
                "status": "PASS",
                "d_min": args.expected_d_min,
                "d_max": args.expected_d_max,
                "largest_smallest_good_prime": frontier["largest_smallest_good_prime"],
            },
            sort_keys=True,
        )
    )
    print("frontier receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 GOOD-PRIME FRONTIER FAILED: {exc}")
        raise SystemExit(1)
