#!/usr/bin/env python3
"""Combine the full known map with the exact projective-patch frontier."""

from __future__ import annotations

import argparse
import json
import platform
from collections import Counter
from pathlib import Path

from analyze_good_prime_frontier import require_verification_binding
from r3_common import R3Error, atomic_json_write, require, sha256
from verify_colength import (
    verify_formula_independence,
    verify_receipt as verify_colength_receipt,
)
from verify_projective_patch_screen import (
    SOURCE_PATHS as PATCH_VERIFIER_SOURCE_PATHS,
    validate_receipt as validate_patch_receipt,
)


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
SOURCE_PATHS = (
    SCRIPT_PATH,
    BASE / "r3_common.py",
    BASE / "analyze_good_prime_frontier.py",
    BASE / "verify_colength.py",
    BASE / "verify_projective_patch_screen.py",
    BASE / "projective_patch_screen.py",
)


def require_patch_verification_binding(
    verification: dict[str, object], patch_path: Path,
    expected_summary: dict[str, object], singular: Path,
) -> None:
    require(
        verification.get("schema") == "polydegree-r3-projective-patch-verification-v1"
        and verification.get("status") == "PASS",
        "patch verification is not terminal PASS",
    )
    require(verification.get("summary") == expected_summary,
            "patch verification summary mismatch")
    require(verification.get("inputs_sha256") == {patch_path.name: sha256(patch_path)},
            "patch verification binds another screen")
    require(verification.get("independently_replayed_good_primes")
            == expected_summary["chosen_good_primes"],
            "patch verification replay inventory mismatch")
    sources = verification.get("source_sha256")
    verifier = BASE / "verify_projective_patch_screen.py"
    expected_sources = {
        path.name: sha256(path) for path in PATCH_VERIFIER_SOURCE_PATHS
    }
    require(sources == expected_sources and sources.get(verifier.name) == sha256(verifier),
            "patch verification source inventory or binding mismatch")
    require(verification.get("runtime_sha256") == {singular.name: sha256(singular)},
            "patch verification runtime binding mismatch")
    require(
        verification.get("formula_independence") == verify_formula_independence(10),
        "patch verification formula reconstruction mismatch",
    )
    require(
        verification.get("negative_controls")
        == {
            "zero_third_mutation_rejected": True,
            "stratified_cover_inventory_exact": True,
            "attempt_prime_prefix_exact": True,
        },
        "patch verification negative-control inventory mismatch",
    )
    require(
        verification.get("independent_method")
        == {
            "description": (
                "specialize first, then verify unit ideals in dimensions 2,1,0"
            ),
            "controls": {
                "baseline_good": True,
                "zero_third_mutation_bad": True,
                "specialized_strata": [
                    "x1_nonzero",
                    "x1_zero_x2_nonzero",
                    "x1_x2_zero_x3_nonzero",
                ],
            },
        },
        "patch verification independent-method inventory mismatch",
    )
    require(
        isinstance(verification.get("worker_count"), int)
        and verification["worker_count"] >= 1,
        "patch verification worker count is invalid",
    )


def derive_frontier(
    known: dict[str, object], patch: dict[str, object]
) -> dict[str, object]:
    smallest_known: dict[int, int] = {}
    for row in known["rows"]:
        if row["classification"] == "GOOD":
            d = row["d"]
            smallest_known[d] = min(smallest_known.get(d, row["prime"]), row["prime"])
    require(sorted(smallest_known) == list(range(2, 50)),
            "known map lacks a complete smallest-GOOD frontier")
    selected_patch = {}
    bad_before = {}
    timeouts_before = {}
    for case in patch["cases"]:
        d = case["d"]
        attempts = case["attempts"]
        require(attempts[-1]["classification"] == "GOOD",
                f"patch case d={d} does not terminate GOOD")
        selected_patch[d] = attempts[-1]["prime"]
        bad_before[d] = sum(row["classification"] == "BAD" for row in attempts[:-1])
        timeouts_before[d] = sum(
            row["classification"] == "TIMEOUT" for row in attempts[:-1]
        )
    require(sorted(selected_patch) == list(range(50, 301)),
            "patch screen lacks complete selected-GOOD coverage")
    selected = {**smallest_known, **selected_patch}
    histogram = Counter(selected.values())
    maximum = max(selected.values())
    return {
        "degree_range": {"d_min": 2, "d_max": 300, "count": 299},
        "selected_good_prime_by_degree": [
            {
                "d": d,
                "prime": selected[d],
                "selection_kind": (
                    "smallest_in_complete_map" if d <= 49
                    else "first_completed_after_bad_and_timeout_attempts"
                ),
                "certified_bad_primes_before_selection": bad_before.get(d, 0),
                "timeouts_before_selection": timeouts_before.get(d, 0),
            }
            for d in range(2, 301)
        ],
        "selected_good_prime_histogram": {
            str(prime): histogram[prime] for prime in sorted(histogram)
        },
        "largest_selected_good_prime": maximum,
        "degrees_attaining_largest_selected_prime": [
            d for d in range(2, 301) if selected[d] == maximum
        ],
        "observed_selected_good_primes": sorted(histogram),
        "selection_calibration": {
            "d2_49": "exact smallest GOOD prime in the full p<=997 map",
            "d50_300": (
                "first completed GOOD after exact BAD rows and skipped timeouts; "
                "not necessarily the smallest GOOD prime"
            ),
        },
        "patch_bad_attempt_count": sum(bad_before.values()),
        "patch_timeout_attempt_count": sum(timeouts_before.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--known-map", type=Path, required=True)
    parser.add_argument("--known-verification", type=Path, required=True)
    parser.add_argument("--patch-screen", type=Path, required=True)
    parser.add_argument("--patch-verification", type=Path, required=True)
    parser.add_argument("--patch-verification-peer", type=Path, required=True)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    paths = tuple(path.resolve() for path in (
        args.known_map, args.known_verification, args.patch_screen,
        args.patch_verification, args.patch_verification_peer,
    ))
    singular = args.singular.resolve()
    output = args.out.resolve()
    require(all(path.is_file() for path in (*paths, singular)), "frontier input is absent")
    require(output not in {*paths, singular, *SOURCE_PATHS},
            "frontier output overwrites input, source, or runtime")
    require(not output.exists(), "refusing to overwrite combined frontier")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {path.name: sha256(path) for path in paths}
    known_path, known_verification_path, patch_path, patch_verification_path, peer_path = paths
    known = json.loads(known_path.read_text())
    known_verification = json.loads(known_verification_path.read_text())
    patch = json.loads(patch_path.read_text())
    patch_verification = json.loads(patch_verification_path.read_text())
    patch_verification_peer = json.loads(peer_path.read_text())
    require(patch_verification == patch_verification_peer,
            "patch verification ordinary/optimized receipts differ")
    known_summary = verify_colength_receipt(known, 2, 49, 997, True, singular)
    require_verification_binding(known_verification, known_path, known_summary)
    patch_summary = validate_patch_receipt(patch, 50, 300, 997, singular)
    require_patch_verification_binding(
        patch_verification, patch_path, patch_summary, singular
    )
    frontier = derive_frontier(known, patch)
    mutated = json.loads(json.dumps(patch))
    mutated["cases"] = mutated["cases"][:-1]
    missing_terminal_rejected = False
    try:
        derive_frontier(known, mutated)
    except R3Error:
        missing_terminal_rejected = True
    require(missing_terminal_rejected, "missing terminal degree was not rejected")
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "combined frontier source changed during execution")
    require({path.name: sha256(path) for path in paths} == startup_inputs,
            "combined frontier input changed during execution")
    receipt = {
        "schema": "polydegree-r3-combined-good-prime-frontier-v1",
        "status": "PASS",
        "claim_boundary": (
            "Exact finite selected-GOOD-prime frontier through d=300. The d=50..300 "
            "selections are not claimed minimal when earlier attempts timed out."
        ),
        **frontier,
        "negative_controls": {"missing_terminal_degree_rejected": True},
        "inputs_sha256": startup_inputs,
        "source_sha256": startup_sources,
        "runtime_sha256": {singular.name: sha256(singular)},
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(output, receipt)
    print(json.dumps({
        "status": "PASS",
        "largest_selected_good_prime": frontier["largest_selected_good_prime"],
        "patch_timeouts": frontier["patch_timeout_attempt_count"],
    }, sort_keys=True))
    print("combined frontier:", output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 COMBINED FRONTIER FAILED: {exc}")
        raise SystemExit(1)
