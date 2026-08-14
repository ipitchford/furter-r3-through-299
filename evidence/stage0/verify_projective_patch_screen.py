#!/usr/bin/env python3
"""Independently verify exact projective-patch GOOD certificates."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from projective_patch_screen import (
    COMMON_PATH,
    SCRIPT_PATH as PRODUCER_PATH,
    STRATA,
    validate_attempt,
)
from r3_common import (
    R3Error,
    atomic_json_write,
    g_terms,
    primes_through,
    require,
    sha256,
)
from verify_colength import verify_formula_independence


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
FORMULA_VERIFIER_PATH = BASE / "verify_colength.py"
SOURCE_PATHS = (
    SCRIPT_PATH,
    PRODUCER_PATH,
    COMMON_PATH,
    FORMULA_VERIFIER_PATH,
)


def specialized_polynomial(n: int, prime: int, stratum: int) -> str:
    terms = []
    for (a1, a2, a3), coefficient in g_terms(n):
        if stratum >= 1 and a1:
            continue
        if stratum >= 2 and a2:
            continue
        coefficient %= prime
        if not coefficient:
            continue
        factors = [str(coefficient)]
        if stratum == 0:
            if a2:
                factors.append("x2" if a2 == 1 else f"x2^{a2}")
            if a3:
                factors.append("x3" if a3 == 1 else f"x3^{a3}")
        elif stratum == 1 and a3:
            factors.append("x3" if a3 == 1 else f"x3^{a3}")
        terms.append("*".join(factors))
    return "+".join(terms) if terms else "0"


def independent_stratum(
    singular: Path, d: int, prime: int, stratum: int,
    timeout: float, zero_third: bool = False,
) -> dict[str, object]:
    variables = ("(x2,x3)", "(x3)", "(z)")[stratum]
    polynomials = [specialized_polynomial(d + offset, prime, stratum)
                   for offset in range(3)]
    if zero_third:
        polynomials[2] = "0"
    program = f"""option(redSB);
ring r={prime},{variables},dp;
poly f0={polynomials[0]};
poly f1={polynomials[1]};
poly f2={polynomials[2]};
ideal I=f0,f1,f2;
ideal G=std(I);
poly rem=reduce(1,G);
print("R3_INDEPENDENT_REM="+string(rem));
quit;
"""
    completed = subprocess.run(
        [str(singular), "-q"], input=program, text=True, capture_output=True,
        timeout=timeout, check=False, env={**os.environ, "LC_ALL": "C"},
    )
    require(completed.returncode == 0,
            f"independent stratum failed: {(completed.stdout + completed.stderr)[-1000:]}")
    markers = re.findall(
        r"^R3_INDEPENDENT_REM=(.*)\s*$",
        completed.stdout + "\n" + completed.stderr,
        re.MULTILINE,
    )
    require(len(markers) == 1 and markers[0] in {"0", "1"},
            "independent stratum marker is malformed")
    return {
        "stratum": STRATA[stratum][0],
        "unit_ideal": markers[0] == "0",
        "remainder_of_one": int(markers[0]),
    }


def independent_certify_prime(
    singular: Path, d: int, prime: int, timeout: float,
    zero_third: bool = False,
) -> dict[str, object]:
    strata = []
    for stratum in range(len(STRATA)):
        result = independent_stratum(
            singular, d, prime, stratum, timeout, zero_third
        )
        strata.append(result)
        if result["unit_ideal"] is False:
            return {"d": d, "prime": prime, "classification": "BAD", "strata": strata}
    return {"d": d, "prime": prime, "classification": "GOOD", "strata": strata}


def independent_controls(singular: Path, timeout: float) -> dict[str, object]:
    baseline = independent_certify_prime(singular, 2, 5, timeout)
    mutation = independent_certify_prime(singular, 2, 5, timeout, zero_third=True)
    require(baseline["classification"] == "GOOD", "independent baseline failed")
    require(mutation["classification"] == "BAD", "independent mutation was not BAD")
    return {
        "baseline_good": True,
        "zero_third_mutation_bad": True,
        "specialized_strata": [name for name, _ in STRATA],
    }


def validate_receipt(
    receipt: dict[str, object], expected_d_min: int, expected_d_max: int,
    expected_prime_max: int, singular: Path,
) -> dict[str, object]:
    require(
        receipt.get("schema") == "polydegree-r3-projective-patch-screen-v1"
        and receipt.get("status") == "PASS",
        "projective-patch receipt is not terminal PASS",
    )
    parameters = receipt.get("parameters")
    require(isinstance(parameters, dict), "patch receipt lacks parameters")
    require(parameters.get("d_min") == expected_d_min
            and parameters.get("d_max") == expected_d_max,
            "patch receipt range mismatch")
    primes = parameters.get("primes")
    require(primes == primes_through(expected_prime_max), "patch prime inventory mismatch")
    require(receipt.get("cover") == [name for name, _ in STRATA],
            "patch cover inventory mismatch")
    source_hashes = receipt.get("source_sha256")
    require(isinstance(source_hashes, dict)
            and source_hashes.get(PRODUCER_PATH.name) == sha256(PRODUCER_PATH)
            and source_hashes.get(COMMON_PATH.name) == sha256(COMMON_PATH),
            "patch producer source binding mismatch")
    require(receipt.get("runtime_sha256") == {str(singular): sha256(singular)},
            "patch producer runtime binding mismatch")
    cases = receipt.get("cases")
    require(isinstance(cases, list)
            and [case.get("d") for case in cases if isinstance(case, dict)]
            == list(range(expected_d_min, expected_d_max + 1)),
            "patch case inventory mismatch")
    observed_counts = {"degrees": len(cases), "attempts": 0, "good": 0,
                       "bad": 0, "timeout": 0}
    chosen = []
    for case in cases:
        d = case["d"]
        attempts = case.get("attempts")
        require(isinstance(attempts, list) and attempts, f"d={d} has no attempts")
        attempt_primes = []
        for attempt in attempts:
            validate_attempt(attempt, d)
            prime = attempt.get("prime")
            require(isinstance(prime, int) and prime in primes, "invalid attempt prime")
            attempt_primes.append(prime)
            classification = attempt["classification"]
            observed_counts["attempts"] += 1
            observed_counts[classification.lower()] += 1
        require(attempt_primes == primes[:len(attempt_primes)],
                f"d={d} attempts are not the exact initial prime prefix")
        require(attempts[-1]["classification"] == "GOOD"
                and all(attempt["classification"] != "GOOD" for attempt in attempts[:-1]),
                f"d={d} does not stop at its unique first completed GOOD attempt")
        chosen.append((d, attempts[-1]["prime"]))
    require(receipt.get("good_degree_coverage")
            == list(range(expected_d_min, expected_d_max + 1)),
            "patch GOOD coverage is incomplete")
    require(receipt.get("counts") == observed_counts, "patch counts mismatch")
    controls = receipt.get("controls")
    require(isinstance(controls, dict)
            and controls.get("stratified_cover_complete") is True
            and controls.get("baseline_d2_p5", {}).get("classification") == "GOOD"
            and controls.get("zero_third_mutation_d2_p5", {}).get("classification") == "BAD",
            "patch controls are incomplete")
    return {
        "degree_range": [expected_d_min, expected_d_max],
        "degree_count": len(cases),
        "chosen_good_primes": [[d, prime] for d, prime in chosen],
        "producer_counts": observed_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-d-min", type=int, required=True)
    parser.add_argument("--expected-d-max", type=int, required=True)
    parser.add_argument("--expected-prime-max", type=int, default=997)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--singular", type=Path, default=Path("/opt/homebrew/bin/Singular"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    input_path = args.input.resolve()
    singular = args.singular.resolve()
    output = args.out.resolve()
    require(input_path.is_file() and singular.is_file(), "verifier input or runtime is absent")
    require(args.workers >= 1, "verifier worker count must be positive")
    require(output not in {input_path, singular, *SOURCE_PATHS},
            "verifier output overwrites input, source, or runtime")
    require(not output.exists(), "refusing to overwrite patch verification receipt")
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    startup_inputs = {input_path.name: sha256(input_path), str(singular): sha256(singular)}
    receipt = json.loads(input_path.read_text())
    summary = validate_receipt(
        receipt, args.expected_d_min, args.expected_d_max,
        args.expected_prime_max, singular,
    )
    recomputed = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                independent_certify_prime, singular, d, prime, args.timeout
            ): (d, prime)
            for d, prime in summary["chosen_good_primes"]
        }
        for future in as_completed(futures):
            d, prime = futures[future]
            result = future.result()
            require(result["classification"] == "GOOD",
                    f"independent patch replay failed at d={d}, p={prime}")
            recomputed.append([d, prime])
    recomputed.sort()
    require(recomputed == summary["chosen_good_primes"],
            "independent patch replay inventory mismatch")
    formula = verify_formula_independence(10)
    replayed_controls = independent_controls(singular, min(args.timeout, 30.0))
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "patch verifier source changed during execution")
    require({input_path.name: sha256(input_path), str(singular): sha256(singular)}
            == startup_inputs, "patch verifier input or runtime changed")
    output_receipt = {
        "schema": "polydegree-r3-projective-patch-verification-v1",
        "status": "PASS",
        "claim_boundary": (
            "Independent exact replay of the selected GOOD three-stratum certificates "
            "for the displayed finite degree range only; no all-degree claim is made."
        ),
        "summary": summary,
        "independently_replayed_good_primes": recomputed,
        "formula_independence": formula,
        "negative_controls": {
            "zero_third_mutation_rejected": True,
            "stratified_cover_inventory_exact": True,
            "attempt_prime_prefix_exact": True,
        },
        "independent_method": {
            "description": "specialize first, then verify unit ideals in dimensions 2,1,0",
            "controls": replayed_controls,
        },
        "worker_count": args.workers,
        "inputs_sha256": {input_path.name: startup_inputs[input_path.name]},
        "source_sha256": startup_sources,
        "runtime_sha256": {singular.name: startup_inputs[str(singular)]},
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(output, output_receipt)
    print(json.dumps({"status": "PASS", "degrees": len(recomputed)}, sort_keys=True))
    print("projective patch verification:", output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 PROJECTIVE PATCH VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
