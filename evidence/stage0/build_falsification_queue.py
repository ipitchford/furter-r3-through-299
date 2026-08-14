#!/usr/bin/env python3
"""Build the fail-closed R(3) counterexample-escalation queue."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

from analyze_good_prime_frontier import require_verification_binding
from analyze_combined_good_prime_frontier import require_patch_verification_binding
from r3_common import R3Error, atomic_json_write, require, sha256
from verify_colength import DEFAULT_SINGULAR, verify_receipt
from verify_projective_patch_screen import validate_receipt as validate_patch_receipt


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")
PRODUCER_PATH = SCRIPT_PATH.with_name("modular_colength.py")
VERIFIER_PATH = SCRIPT_PATH.with_name("verify_colength.py")
FRONTIER_ANALYZER_PATH = SCRIPT_PATH.with_name("analyze_good_prime_frontier.py")
COMBINED_FRONTIER_PATH = SCRIPT_PATH.with_name("analyze_combined_good_prime_frontier.py")
PATCH_PRODUCER_PATH = SCRIPT_PATH.with_name("projective_patch_screen.py")
PATCH_VERIFIER_PATH = SCRIPT_PATH.with_name("verify_projective_patch_screen.py")


def verified_degrees(receipt: dict[str, object], expected_min: int, expected_max: int) -> set[int]:
    require(receipt.get("schema") == "polydegree-r3-modular-colength-v1",
            "wrong modular receipt schema")
    require(receipt.get("status") == "PASS" and receipt.get("incomplete") == [],
            "falsification queue requires a terminal complete modular receipt")
    parameters = receipt.get("parameters")
    require(isinstance(parameters, dict), "modular receipt lacks parameters")
    require(parameters.get("d_min") == expected_min and parameters.get("d_max") == expected_max,
            "modular receipt range mismatch")
    coverage = receipt.get("good_degree_coverage")
    require(isinstance(coverage, list), "modular receipt lacks good coverage")
    return set(coverage)


def verified_patch_degrees(
    receipt: dict[str, object], expected_min: int, expected_max: int
) -> set[int]:
    require(receipt.get("schema") == "polydegree-r3-projective-patch-screen-v1"
            and receipt.get("status") == "PASS",
            "falsification queue requires a terminal patch screen")
    parameters = receipt.get("parameters")
    require(isinstance(parameters, dict)
            and parameters.get("d_min") == expected_min
            and parameters.get("d_max") == expected_max,
            "patch screen range mismatch")
    coverage = receipt.get("good_degree_coverage")
    require(coverage == list(range(expected_min, expected_max + 1)),
            "patch screen GOOD coverage is incomplete")
    return set(coverage)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--known-map", type=Path, required=True)
    parser.add_argument("--known-verification", type=Path, required=True)
    parser.add_argument("--screen", type=Path, required=True)
    parser.add_argument("--screen-verification", type=Path, required=True)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    paths = (args.known_map, args.known_verification, args.screen, args.screen_verification)
    require(all(path.is_file() for path in paths), "one or more falsification inputs are absent")
    require(args.out.resolve() not in {path.resolve() for path in paths},
            "falsification output must not overwrite an input")
    singular = args.singular.resolve()
    require(singular.is_file(), "Singular executable is absent")
    source_paths = (
        SCRIPT_PATH,
        COMMON_PATH,
        PRODUCER_PATH,
        VERIFIER_PATH,
        FRONTIER_ANALYZER_PATH,
        COMBINED_FRONTIER_PATH,
        PATCH_PRODUCER_PATH,
        PATCH_VERIFIER_PATH,
    )
    startup_sources = {path.name: sha256(path) for path in source_paths}
    watched_paths = (*paths, singular)
    startup_inputs = {str(path.resolve()): sha256(path.resolve()) for path in watched_paths}
    known = json.loads(args.known_map.read_text())
    screen = json.loads(args.screen.read_text())
    known_verification = json.loads(args.known_verification.read_text())
    screen_verification = json.loads(args.screen_verification.read_text())
    known_summary = verify_receipt(known, 2, 49, 997, True, singular)
    screen_summary = validate_patch_receipt(screen, 50, 300, 997, singular)
    require_verification_binding(known_verification, args.known_map.resolve(), known_summary)
    require_patch_verification_binding(
        screen_verification, args.screen.resolve(), screen_summary, singular
    )
    covered = verified_degrees(known, 2, 49) | verified_patch_degrees(screen, 50, 300)
    requested = set(range(2, 301))
    unresolved = sorted(requested - covered)
    queue = [
        {
            "d": d,
            "reason": "no GOOD prime in the completed exact screen",
            "next_actions": [
                "search for an exact nonzero projective common zero over a number field",
                "use numerical homotopy only to discover an algebraic candidate",
                "accept a counterexample only after exact polynomial evaluation",
            ],
        }
        for d in unresolved
    ]
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "falsification source changed while building the queue")
    require({str(path.resolve()): sha256(path.resolve()) for path in watched_paths} == startup_inputs,
            "falsification input changed while building the queue")
    output = {
        "schema": "polydegree-r3-falsification-queue-v1",
        "status": "PASS" if not unresolved else "ESCALATION_REQUIRED",
        "claim_boundary": (
            "An empty queue means only that every tested degree has an exact modular "
            "certificate. It is not an all-d theorem and says nothing about d>300."
        ),
        "tested_degrees": list(range(2, 301)),
        "exactly_certified_degrees": sorted(covered),
        "unresolved_degrees": unresolved,
        "escalation_queue": queue,
        "numerical_homotopy_disposition": (
            "not triggered: exact certificates exist for every tested degree"
            if not unresolved else "triggered only for the unresolved inventory"
        ),
        "bad_prime_interpretation": (
            "Individual BAD reductions are divisibility data for the resultant, "
            "not characteristic-zero counterexamples."
        ),
        "inputs_sha256": {
            path.name: startup_inputs[str(path.resolve())] for path in paths
        },
        "runtime_sha256": {singular.name: startup_inputs[str(singular)]},
        "source_sha256": startup_sources,
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(args.out, output)
    print(json.dumps({
        "status": output["status"],
        "tested": len(requested),
        "unresolved": len(unresolved),
    }, sort_keys=True))
    print("falsification queue:", args.out.resolve())
    return 0 if not unresolved else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 FALSIFICATION QUEUE FAILED: {exc}")
        raise SystemExit(1)
