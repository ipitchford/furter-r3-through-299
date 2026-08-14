#!/usr/bin/env python3
"""Root verifier for the frozen Furter R(3) Stage 0 internal package."""

from __future__ import annotations

import argparse
import copy
import json
import math
import platform
from collections import Counter
from pathlib import Path

from analyze_cofactor_recurrence import recurrence_screen as cofactor_recurrence_screen
from analyze_euler_socle_recurrence import (
    extract_sequences as extract_euler_socle_sequences,
    order_two_screen as euler_order_two_screen,
    ratio_screen as euler_ratio_screen,
)
from analyze_combined_good_prime_frontier import (
    derive_frontier as derive_combined_frontier,
    require_patch_verification_binding,
)
from build_falsification_queue import verified_degrees, verified_patch_degrees
from r3_common import (
    R3Error,
    atomic_json_write,
    g_terms,
    primes_through,
    require,
    sha256,
)
from verify_cofactors import decode, identity_residual
from verify_colength import (
    DEFAULT_SINGULAR,
    verify_formula_independence,
    verify_receipt as verify_colength_receipt,
)
from verify_modular_radical_certificates import verify_payload as verify_modular_certificates
from verify_projective_patch_screen import validate_receipt as validate_patch_receipt
from verify_resultants import (
    remove_nondeterminism,
    recurrence_screen as resultant_recurrence_screen,
    verify_modular_parity,
)


SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent


def require_source_binding(receipt: dict[str, object], path: Path) -> None:
    bindings = receipt.get("source_sha256")
    require(isinstance(bindings, dict), f"receipt lacks source hashes for {path.name}")
    keys = [key for key in bindings if Path(key).name == path.name]
    require(len(keys) == 1, f"receipt must bind exactly one {path.name}")
    require(bindings[keys[0]] == sha256(path), f"receipt binds stale {path.name}")


def load(name: str) -> tuple[dict[str, object], Path]:
    path = BASE / name
    require(path.is_file(), f"missing root input {name}")
    return json.loads(path.read_text()), path


def verify_cofactor_cases(receipt: dict[str, object]) -> dict[int, list[dict]]:
    require(receipt.get("schema") == "polydegree-r3-x3-cofactors-v1" and
            receipt.get("status") == "PASS", "cofactor receipt is not terminal PASS")
    require(receipt.get("d_min") == 2 and receipt.get("d_max") == 8,
            "root expects cofactor degrees 2..8")
    cases: dict[int, list[dict]] = {}
    for case in receipt.get("cases", []):
        d = case.get("d")
        require(isinstance(d, int) and 2 <= d <= 8, "invalid cofactor case degree")
        raw = case.get("cofactors")
        require(isinstance(raw, dict) and set(raw) == {"A", "B", "C"},
                "invalid cofactor inventory")
        decoded = {name: decode(raw[name]) for name in ("A", "B", "C")}
        require(not identity_residual(d, decoded), f"cofactor identity failed at d={d}")
        cases[d] = [decoded[name] for name in ("A", "B", "C")]
    require(sorted(cases) == list(range(2, 9)), "cofactor degree inventory is incomplete")
    return cases


def verify_fixed_prime_zero_band(known: dict[str, object]) -> dict[str, object]:
    """Regress the analytic zero-band lemma against the complete d<=49 map."""
    parameters = known.get("parameters")
    require(isinstance(parameters, dict), "known map lacks parameters")
    require(parameters.get("d_min") == 2 and parameters.get("d_max") == 49
            and parameters.get("first_good") is False,
            "zero-band regression requires the complete d=2..49 map")
    primes = parameters.get("primes")
    require(primes == primes_through(997),
            "zero-band regression requires the exact prime inventory through 997")
    rows = known.get("rows")
    require(isinstance(rows, list), "known map lacks rows")
    classifications = {
        (row.get("d"), row.get("prime")): row.get("classification")
        for row in rows if isinstance(row, dict)
    }
    zero_polynomials = 0
    forced_bad_windows = 0
    checked_primes = [prime for prime in primes_through(53) if prime >= 7]
    for prime in checked_primes:
        band_width = (prime + 2) // 4
        for n in range(52):
            k = (-n) % prime
            if 2 <= k <= band_width:
                require(
                    all(
                        coefficient % prime == 0
                        for _, coefficient in g_terms(n)
                    ),
                    f"periodic zero-band check failed at n={n}, p={prime}",
                )
                zero_polynomials += 1
        for d in range(2, 50):
            residue = d % prime
            if prime - band_width - 2 <= residue <= prime - 2:
                require(classifications.get((d, prime)) == "BAD",
                        f"periodic BAD-window check failed at d={d}, p={prime}")
                forced_bad_windows += 1
    small_prime_witnesses = [[2, 2], [3, 3], [5, 6]]
    for prime, d in small_prime_witnesses:
        require(classifications.get((d, prime)) == "BAD",
                f"small-prime BAD witness failed at d={d}, p={prime}")
    return {
        "analytic_statement": (
            "g_(n,3)=0 mod p when n=-k mod p, "
            "2<=k<=floor((p+2)/4), p>=7"
        ),
        "finite_regression_coefficient_range": [0, 51],
        "finite_regression_degree_range": [2, 49],
        "finite_regression_prime_range": [7, 53],
        "checked_primes": checked_primes,
        "zero_polynomials_checked": zero_polynomials,
        "forced_bad_windows_checked": forced_bad_windows,
        "small_prime_bad_witnesses": small_prime_witnesses,
        "claim_boundary": "finite executable regression; the all-prime proof is analytic",
    }


def verify_generator_axis_specializations(max_n: int = 302) -> dict[str, object]:
    """Check closed one-axis specializations for every finite-window coefficient."""
    require(max_n >= 4, "generator-axis regression must include the hand-check grid")
    for n in range(max_n + 1):
        terms = g_terms(n)
        x1_value = sum(
            coefficient
            for (a1, a2, a3), coefficient in terms
            if a2 == 0 and a3 == 0
        )
        catalan, remainder = divmod(math.comb(2 * n, n), n + 1)
        require(remainder == 0, f"Catalan quotient failed at n={n}")
        expected_x1 = -catalan if n % 2 else catalan
        require(x1_value == expected_x1, f"x1-axis specialization failed at n={n}")

        x2_value = sum(
            coefficient
            for (a1, a2, a3), coefficient in terms
            if a1 == 0 and a3 == 0
        )
        expected_x2 = 0
        if n % 2 == 0:
            m = n // 2
            fuss, remainder = divmod(math.comb(3 * m, m), 2 * m + 1)
            require(remainder == 0, f"ternary Fuss-Catalan quotient failed at n={n}")
            expected_x2 = -fuss if m % 2 else fuss
        require(x2_value == expected_x2, f"x2-axis specialization failed at n={n}")

        x3_value = sum(
            coefficient
            for (a1, a2, a3), coefficient in terms
            if a1 == 0 and a2 == 0
        )
        expected_x3 = 0
        if n % 3 == 0:
            m = n // 3
            fuss, remainder = divmod(math.comb(4 * m, m), 3 * m + 1)
            require(remainder == 0, f"quaternary Fuss-Catalan quotient failed at n={n}")
            expected_x3 = -fuss if m % 2 else fuss
        require(x3_value == expected_x3, f"x3-axis specialization failed at n={n}")

    return {
        "coefficient_range": [0, max_n],
        "inverse_convention": (
            "g_n is the coefficient of X^(n+1) in the compositional inverse of "
            "H(X)=X+x1*X^2+x2*X^3+x3*X^4"
        ),
        "formulas": {
            "x1": "(-1)^n*binomial(2n,n)/(n+1)",
            "x2": "0 unless n=2m; then (-1)^m*binomial(3m,m)/(2m+1)",
            "x3": "0 unless n=3m; then (-1)^m*binomial(4m,m)/(3m+1)",
        },
        "low_degree_axis_values_n1_to_n4": {
            "x1": [-1, 2, -5, 14],
            "x2": [0, -1, 0, 3],
            "x3": [0, 0, -1, 0],
        },
        "axis_values_checked": 3 * (max_n + 1),
        "claim_boundary": (
            "closed-form pure-axis regression; full coefficients are independently "
            "reverted through n=10"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=BASE / "root-receipt.json")
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    args = parser.parse_args()

    input_names = (
        "known-map-d2-49-p997.json", "known-map-d2-49-p997-opt.json",
        "known-map-d2-49-p997-verification.json",
        "screen-patches-d50-300.json",
        "screen-patches-d50-300-verification.json",
        "screen-patches-d50-300-verification-opt.json",
        "good-prime-frontier-d2-300.json",
        "groebner-signatures-d2-49.json", "groebner-signatures-d2-49-opt.json",
        "modular-radical-certificates-d2-8.json",
        "modular-radical-certificates-d2-8-opt.json",
        "modular-radical-certificates-d2-8-verification.json",
        "rational-radical-certificates-d2-12.json",
        "rational-radical-certificates-d2-12-opt.json",
        "rational-radical-certificates-d2-12-verification.json",
        "rational-radical-certificates-d2-12-verification-opt.json",
        "euler-socle-recurrence-screen.json",
        "cover-resultants-d2-25.json", "cover-resultants-d2-25-opt.json",
        "cover-resultants-d2-25-verification.json",
        "cofactors-d2-8.json", "cofactors-d2-8-opt.json",
        "cofactors-d2-8-verification.json", "falsification-queue.json",
        "cofactor-recurrence-screen.json",
    )
    root_input_paths = tuple(BASE / name for name in input_names)
    require(all(path.is_file() for path in root_input_paths),
            "one or more root inputs are absent")
    require(args.out.resolve() not in {path.resolve() for path in root_input_paths},
            "root output must not overwrite an input")
    singular = args.singular.resolve()
    require(singular.is_file(), "Singular executable is absent")
    source_paths = tuple(sorted(BASE.glob("*.py")))
    watched_paths = (*root_input_paths, singular)
    startup_sources = {path.name: sha256(path) for path in source_paths}
    startup_inputs = {path.name: sha256(path) for path in watched_paths}

    known, known_path = load("known-map-d2-49-p997.json")
    known_peer, known_peer_path = load("known-map-d2-49-p997-opt.json")
    known_verification, known_verification_path = load("known-map-d2-49-p997-verification.json")
    screen, screen_path = load("screen-patches-d50-300.json")
    screen_verification, screen_verification_path = load(
        "screen-patches-d50-300-verification.json"
    )
    screen_verification_peer, screen_verification_peer_path = load(
        "screen-patches-d50-300-verification-opt.json"
    )
    good_prime_frontier, good_prime_frontier_path = load("good-prime-frontier-d2-300.json")
    groebner_signatures, groebner_signatures_path = load("groebner-signatures-d2-49.json")
    groebner_signatures_peer, groebner_signatures_peer_path = load(
        "groebner-signatures-d2-49-opt.json"
    )
    modular_certificates, modular_certificates_path = load(
        "modular-radical-certificates-d2-8.json"
    )
    modular_certificates_peer, modular_certificates_peer_path = load(
        "modular-radical-certificates-d2-8-opt.json"
    )
    modular_certificate_verification, modular_certificate_verification_path = load(
        "modular-radical-certificates-d2-8-verification.json"
    )
    rational_certificates, rational_certificates_path = load(
        "rational-radical-certificates-d2-12.json"
    )
    rational_certificates_peer, rational_certificates_peer_path = load(
        "rational-radical-certificates-d2-12-opt.json"
    )
    rational_certificate_verification, rational_certificate_verification_path = load(
        "rational-radical-certificates-d2-12-verification.json"
    )
    rational_certificate_verification_peer, rational_certificate_verification_peer_path = load(
        "rational-radical-certificates-d2-12-verification-opt.json"
    )
    euler_recurrence, euler_recurrence_path = load(
        "euler-socle-recurrence-screen.json"
    )
    resultants, resultants_path = load("cover-resultants-d2-25.json")
    resultants_peer, resultants_peer_path = load("cover-resultants-d2-25-opt.json")
    resultant_verification, resultant_verification_path = load("cover-resultants-d2-25-verification.json")
    cofactors, cofactors_path = load("cofactors-d2-8.json")
    cofactors_peer, cofactors_peer_path = load("cofactors-d2-8-opt.json")
    cofactor_verification, cofactor_verification_path = load("cofactors-d2-8-verification.json")
    queue, queue_path = load("falsification-queue.json")
    cofactor_screen, cofactor_screen_path = load("cofactor-recurrence-screen.json")

    known_summary = verify_colength_receipt(known, 2, 49, 997, True, singular)
    known_peer_summary = verify_colength_receipt(known_peer, 2, 49, 997, True, singular)
    require(known_summary == known_peer_summary, "known-map ordinary/optimized summaries differ")
    require(remove_nondeterminism(copy.deepcopy(known)) ==
            remove_nondeterminism(copy.deepcopy(known_peer)),
            "known-map ordinary/optimized projections differ")
    require(known_verification.get("status") == "PASS" and
            known_verification.get("input_sha256") == sha256(known_path) and
            known_verification.get("peer_parity", {}).get("peer_sha256") == sha256(known_peer_path),
            "known-map verification receipt does not bind both producers")
    require_source_binding(known_verification, BASE / "verify_colength.py")
    screen_summary = validate_patch_receipt(screen, 50, 300, 997, singular)
    require(screen_verification == screen_verification_peer,
            "patch-screen ordinary/optimized verifications differ")
    require_patch_verification_binding(
        screen_verification, screen_path, screen_summary, singular
    )
    require_source_binding(
        screen_verification, BASE / "verify_projective_patch_screen.py"
    )
    formula = verify_formula_independence(10)
    generator_axes = verify_generator_axis_specializations(302)
    zero_band = verify_fixed_prime_zero_band(known)
    certified = verified_degrees(known, 2, 49) | verified_patch_degrees(screen, 50, 300)
    require(certified == set(range(2, 301)), "root finite coverage is not d=2..300")
    recomputed_frontier = derive_combined_frontier(known, screen)
    frontier_keys = (
        "degree_range",
        "selected_good_prime_by_degree",
        "selected_good_prime_histogram",
        "largest_selected_good_prime",
        "degrees_attaining_largest_selected_prime",
        "observed_selected_good_primes",
        "selection_calibration",
        "patch_bad_attempt_count",
        "patch_timeout_attempt_count",
    )
    require(
        good_prime_frontier.get("schema")
        == "polydegree-r3-combined-good-prime-frontier-v1"
        and good_prime_frontier.get("status") == "PASS",
        "good-prime frontier is not terminal PASS",
    )
    require(
        all(good_prime_frontier.get(key) == recomputed_frontier[key] for key in frontier_keys),
        "good-prime frontier differs from root recomputation",
    )
    require(
        good_prime_frontier.get("negative_controls", {}).get(
            "missing_terminal_degree_rejected"
        )
        is True,
        "good-prime frontier lacks its range negative control",
    )
    require(
        good_prime_frontier.get("inputs_sha256")
        == {
            known_path.name: sha256(known_path),
            known_verification_path.name: sha256(known_verification_path),
            screen_path.name: sha256(screen_path),
            screen_verification_path.name: sha256(screen_verification_path),
            screen_verification_peer_path.name: sha256(screen_verification_peer_path),
        },
        "good-prime frontier does not bind both verified maps",
    )
    require_source_binding(
        good_prime_frontier, BASE / "analyze_combined_good_prime_frontier.py"
    )
    require(
        groebner_signatures.get("schema") == "polydegree-r3-groebner-signature-probe-v1"
        and groebner_signatures.get("status") == "PASS"
        and groebner_signatures == groebner_signatures_peer,
        "Gröbner-signature peers are not identical terminal receipts",
    )
    signature_rows = groebner_signatures.get("rows")
    require(isinstance(signature_rows, list) and len(signature_rows) == 48,
            "Gröbner-signature row inventory mismatch")
    known_smallest_good: dict[int, int] = {}
    for row in known["rows"]:
        if row["classification"] == "GOOD":
            d = row["d"]
            known_smallest_good[d] = min(
                known_smallest_good.get(d, row["prime"]), row["prime"]
            )
    require(sorted(known_smallest_good) == list(range(2, 50)),
            "known map lacks a complete smallest-GOOD inventory")
    exact_diagonal_degrees = []
    offset_histogram: Counter[tuple[int, int, int]] = Counter()
    basis_sizes = []
    for expected_d, row in zip(range(2, 50), signature_rows, strict=True):
        require(isinstance(row, dict) and row.get("d") == expected_d,
                "Gröbner-signature degree order mismatch")
        require(row.get("prime") == known_smallest_good[expected_d],
                "Gröbner signature does not use the smallest certified GOOD prime")
        exponents = row.get("pure_initial_exponents")
        require(
            isinstance(exponents, dict)
            and set(exponents) == {"x1", "x2", "x3"}
            and all(isinstance(exponents[key], int) and exponents[key] > 0 for key in exponents),
            "invalid pure initial-exponent signature",
        )
        basis_size = row.get("basis_size")
        require(isinstance(basis_size, int) and basis_size >= 3,
                "invalid Gröbner basis size")
        basis_sizes.append(basis_size)
        exponent_tuple = tuple(exponents[f"x{axis}"] for axis in range(1, 4))
        offset_histogram[tuple(value - expected_d for value in exponent_tuple)] += 1
        if exponent_tuple == (expected_d, expected_d, expected_d):
            exact_diagonal_degrees.append(expected_d)
    recomputed_signature_summary = {
        "exact_diagonal_count": len(exact_diagonal_degrees),
        "exact_diagonal_degrees": exact_diagonal_degrees,
        "deviation_count": 48 - len(exact_diagonal_degrees),
        "deviation_degrees": [
            d for d in range(2, 50) if d not in set(exact_diagonal_degrees)
        ],
        "maximum_basis_size": max(basis_sizes),
        "minimum_basis_size": min(basis_sizes),
        "pure_exponent_offset_states": [
            {"offset": list(offset), "count": offset_histogram[offset]}
            for offset in sorted(offset_histogram)
        ],
    }
    require(groebner_signatures.get("summary") == recomputed_signature_summary,
            "stored Gröbner-signature summary differs from root recomputation")
    require(
        groebner_signatures.get("inputs_sha256")
        == {
            known_path.name: sha256(known_path),
            known_verification_path.name: sha256(known_verification_path),
        },
        "Gröbner-signature receipt does not bind the verified known map",
    )
    require_source_binding(groebner_signatures, BASE / "probe_groebner_signatures.py")
    require(
        groebner_signatures.get("runtime_sha256") == {singular.name: sha256(singular)},
        "Gröbner-signature Singular binding mismatch",
    )

    require(modular_certificates == modular_certificates_peer,
            "modular radical certificate peers differ")
    modular_certificate_summary = verify_modular_certificates(
        modular_certificates,
        known,
        known_path,
        known_verification_path,
        2,
        8,
        singular,
    )
    require(
        verify_modular_certificates(
            modular_certificates_peer,
            known,
            known_path,
            known_verification_path,
            2,
            8,
            singular,
        )
        == modular_certificate_summary,
        "modular radical certificate peer summaries differ",
    )
    require(
        modular_certificate_verification.get("schema")
        == "polydegree-r3-modular-radical-certificate-verification-v1"
        and modular_certificate_verification.get("status") == "PASS"
        and modular_certificate_verification.get("summary") == modular_certificate_summary
        and modular_certificate_verification.get("formula_independence", {}).get(
            "checked_n"
        )
        == list(range(11))
        and modular_certificate_verification.get("formula_independence", {}).get(
            "coefficient_mutation_rejected"
        )
        is True
        and modular_certificate_verification.get("cofactor_mutation_rejected") is True
        and modular_certificate_verification.get("inputs_sha256") == {
            modular_certificates_path.name: sha256(modular_certificates_path),
            modular_certificates_peer_path.name: sha256(modular_certificates_peer_path),
            known_path.name: sha256(known_path),
            known_verification_path.name: sha256(known_verification_path),
        }
        and modular_certificate_verification.get("runtime_sha256")
        == {singular.name: sha256(singular)},
        "modular radical certificate verification binding mismatch",
    )
    require_source_binding(
        modular_certificate_verification,
        BASE / "verify_modular_radical_certificates.py",
    )
    require_source_binding(
        modular_certificate_verification,
        BASE / "extract_modular_radical_certificates.py",
    )

    require(
        rational_certificates == rational_certificates_peer,
        "rational radical certificate peers differ",
    )
    require(
        rational_certificate_verification == rational_certificate_verification_peer,
        "rational radical verification peers differ",
    )
    rational_verified = rational_certificate_verification.get("verified")
    require(
        rational_certificate_verification.get("schema")
        == "polydegree-r3-rational-radical-verification-v1"
        and rational_certificate_verification.get("status") == "PASS"
        and rational_certificate_verification.get("d_min") == 2
        and rational_certificate_verification.get("d_max") == 12
        and rational_certificate_verification.get("map_summary") == known_summary
        and rational_certificate_verification.get(
            "ordinary_optimized_timing_free_parity"
        )
        is True
        and rational_certificate_verification.get("formula_independence", {}).get(
            "checked_n"
        )
        == list(range(15))
        and rational_certificate_verification.get("inputs_sha256")
        == {
            rational_certificates_path.name: sha256(rational_certificates_path),
            rational_certificates_peer_path.name: sha256(rational_certificates_peer_path),
            known_path.name: sha256(known_path),
            known_verification_path.name: sha256(known_verification_path),
        }
        and rational_certificate_verification.get("runtime_sha256")
        == {singular.name: sha256(singular)},
        "rational radical verification metadata or bindings mismatch",
    )
    require(
        isinstance(rational_verified, list)
        and [case.get("d") for case in rational_verified if isinstance(case, dict)]
        == list(range(2, 13)),
        "rational radical verified degree inventory mismatch",
    )
    for case in rational_verified:
        d = case["d"]
        targets = case.get("targets")
        euler = case.get("euler_jacobian")
        require(
            case.get("expected_colength") == d * (d + 1) * (d + 2) // 6
            and isinstance(case.get("hilbert_function"), list)
            and sum(case["hilbert_function"]) == case["expected_colength"]
            and isinstance(targets, list)
            and len(targets) == 3
            and all(
                isinstance(target, dict)
                and target.get("upper_membership") is True
                and target.get("one_lower_nonmembership") is True
                for target in targets
            )
            and isinstance(euler, dict)
            and euler.get("weighted_degree") == 3 * d - 3
            and euler.get("nonzero_socle_class") is True
            and euler.get("adjugate_identity") is True,
            f"rational radical invariant summary failed at d={d}",
        )
    require_source_binding(
        rational_certificate_verification,
        BASE / "verify_rational_radical_certificates.py",
    )
    require_source_binding(
        rational_certificate_verification,
        BASE / "extract_rational_radical_certificates.py",
    )
    euler_sequences = extract_euler_socle_sequences(rational_certificate_verification)
    recomputed_euler_screens = {
        name: {
            "rational_ratio": euler_ratio_screen(sequence),
            "order_two": euler_order_two_screen(sequence),
        }
        for name, sequence in euler_sequences.items()
    }
    require(
        euler_recurrence.get("schema")
        == "polydegree-r3-euler-socle-recurrence-screen-v1"
        and euler_recurrence.get("status") == "PASS"
        and euler_recurrence.get("degree_range") == [2, 12]
        and euler_recurrence.get("screens") == recomputed_euler_screens
        and euler_recurrence.get("gate") == "STOP_LOW_COMPLEXITY"
        and euler_recurrence.get("survivors")
        == {
            "lambda_x1": {"rational_ratio": [], "order_two": []},
            "nu_x3": {"rational_ratio": [], "order_two": []},
        }
        and euler_recurrence.get("negative_controls")
        == {
            "geometric_ratio_detected": True,
            "terminal_mutation_falsified_on_holdout": True,
        }
        and euler_recurrence.get("inputs_sha256")
        == {
            rational_certificate_verification_path.name: sha256(
                rational_certificate_verification_path
            ),
            rational_certificate_verification_peer_path.name: sha256(
                rational_certificate_verification_peer_path
            ),
        },
        "Euler-socle recurrence screen mismatch",
    )
    require_source_binding(
        euler_recurrence,
        BASE / "analyze_euler_socle_recurrence.py",
    )
    require_source_binding(
        euler_recurrence,
        BASE / "verify_rational_radical_certificates.py",
    )

    require(resultants.get("schema") == "polydegree-r3-resultant-composite-v1" and
            resultants.get("status") == "PASS" and resultants.get("d_min") == 2 and
            resultants.get("d_max") == 25, "ordinary resultant composite metadata mismatch")
    require(resultants_peer.get("schema") == "polydegree-r3-resultant-composite-v1" and
            resultants_peer.get("status") == "PASS" and resultants_peer.get("d_min") == 2 and
            resultants_peer.get("d_max") == 25, "optimized resultant composite metadata mismatch")
    resultant_values = {
        row["d"]: row["weighted_resultant_abs"] for row in resultants.get("values", [])
    }
    resultant_peer_values = {
        row["d"]: row["weighted_resultant_abs"] for row in resultants_peer.get("values", [])
    }
    require(sorted(resultant_values) == list(range(2, 26)) and
            all(isinstance(value, int) and value > 0 for value in resultant_values.values()),
            "ordinary resultant value inventory is invalid")
    require(resultant_values == resultant_peer_values,
            "resultant ordinary/optimized values differ")
    require(remove_nondeterminism(copy.deepcopy(resultants)) ==
            remove_nondeterminism(copy.deepcopy(resultants_peer)),
            "resultant ordinary/optimized projections differ")
    resultant_bound_hashes = set(resultant_verification.get("inputs_sha256", {}).values())
    require(resultant_verification.get("status") == "PASS" and
            {sha256(resultants_path), sha256(resultants_peer_path), sha256(known_path)} <=
            resultant_bound_hashes and
            resultant_verification.get("negative_controls", {}).get(
                "weighted_resultant_increment_rejected") is True and
            resultant_verification.get("full_integer_determinant_degrees") == list(range(2, 18)) and
            resultant_verification.get(
                "independently_reconstructed_full_integer_degrees"
            ) == list(range(2, 18)) and
            resultant_verification.get("independently_reconstructed_crt_degrees") ==
                list(range(18, 26)),
            "resultant verification receipt lacks producer/map bindings or negative control")
    require_source_binding(resultant_verification, BASE / "verify_resultants.py")
    require_source_binding(resultant_verification, BASE / "verify_resultant_crt.py")
    require_source_binding(resultant_verification, BASE / "verify_resultant_prefix.py")
    modular_parity = verify_modular_parity(known, resultant_values, 2, 25, singular)
    resultant_recurrence = resultant_recurrence_screen(resultant_values)
    require(resultant_recurrence["all_low_complexity_relations_excluded_on_training"] is True,
            "unexpected resultant recurrence candidate reached the root")
    require(resultant_recurrence["reserved_holdout_transitions"] == list(range(20, 25)),
            "resultant holdout inventory changed")

    cofactor_cases = verify_cofactor_cases(cofactors)
    cofactor_peer_cases = verify_cofactor_cases(cofactors_peer)
    require(cofactor_cases == cofactor_peer_cases, "cofactor ordinary/optimized values differ")
    require(remove_nondeterminism(copy.deepcopy(cofactors)) ==
            remove_nondeterminism(copy.deepcopy(cofactors_peer)),
            "cofactor ordinary/optimized projections differ")
    require(cofactor_verification.get("status") == "PASS" and
            cofactor_verification.get("input_sha256") == sha256(cofactors_path) and
            cofactor_verification.get("peer_sha256") == sha256(cofactors_peer_path) and
            cofactor_verification.get("coefficient_mutation_rejected") is True,
            "cofactor verification receipt lacks producer bindings or negative control")
    require_source_binding(cofactor_verification, BASE / "verify_cofactors.py")
    require_source_binding(cofactor_verification, BASE / "verify_colength.py")
    require(cofactor_verification.get("formula_independence", {}).get("checked_n") ==
            list(range(11)), "cofactor receipt lacks formula reconstruction through g_10")
    recomputed_cofactor_screen = cofactor_recurrence_screen(cofactor_cases)
    require(recomputed_cofactor_screen == cofactor_screen.get("recurrence_screen"),
            "stored cofactor recurrence screen differs from root recomputation")
    require(cofactor_screen.get("component_homogeneity_verified") is True,
            "stored cofactor screen lacks the homogeneity guard")
    require(recomputed_cofactor_screen["full_matrix_recurrence_consistent_on_training"] is False,
            "unexpected cofactor recurrence candidate reached the root")

    require(queue.get("schema") == "polydegree-r3-falsification-queue-v1" and
            queue.get("status") == "PASS", "falsification queue is not terminal empty PASS")
    require(queue.get("unresolved_degrees") == [] and queue.get("escalation_queue") == [],
            "falsification queue contains unresolved degrees")
    require(queue.get("exactly_certified_degrees") == list(range(2, 301)),
            "falsification queue coverage mismatch")
    require_source_binding(queue, BASE / "build_falsification_queue.py")
    require_source_binding(queue, BASE / "verify_colength.py")
    require_source_binding(queue, BASE / "analyze_combined_good_prime_frontier.py")
    require_source_binding(queue, BASE / "verify_projective_patch_screen.py")
    require(
        queue.get("inputs_sha256")
        == {
            known_path.name: sha256(known_path),
            known_verification_path.name: sha256(known_verification_path),
            screen_path.name: sha256(screen_path),
            screen_verification_path.name: sha256(screen_verification_path),
        },
        "falsification queue does not bind the exact verified maps",
    )
    require(
        queue.get("runtime_sha256") == {singular.name: sha256(singular)},
        "falsification queue Singular binding mismatch",
    )

    inputs = [
        known_path, known_peer_path, known_verification_path,
        screen_path, screen_verification_path, screen_verification_peer_path,
        good_prime_frontier_path,
        groebner_signatures_path, groebner_signatures_peer_path,
        modular_certificates_path, modular_certificates_peer_path,
        modular_certificate_verification_path,
        rational_certificates_path, rational_certificates_peer_path,
        rational_certificate_verification_path,
        rational_certificate_verification_peer_path,
        euler_recurrence_path,
        resultants_path, resultants_peer_path, resultant_verification_path,
        cofactors_path, cofactors_peer_path, cofactor_verification_path,
        queue_path, cofactor_screen_path,
    ]
    require(tuple(inputs) == root_input_paths,
            "root implementation input order differs from its frozen inventory")
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "root source changed during verification")
    require({path.name: sha256(path) for path in watched_paths} == startup_inputs,
            "root input or Singular executable changed during verification")
    output = {
        "schema": "polydegree-r3-stage0-root-v1",
        "status": "PASS",
        "claim_boundary": (
            "The root proves the exact single-map assertions R_tilde(3,d-1), hence "
            "Furter's equivalent R(3,d-1), for d=2..300 and the stored finite "
            "identities/data only. Universal R(3), Strong Factorial, and all-d "
            "Polydegree claims remain open."
        ),
        "finite_rigidity_windows": {"d_min": 2, "d_max": 300, "count": 299},
        "known_map": known_summary,
        "screen": screen_summary,
        "formula_independence": formula,
        "generator_axis_specializations": generator_axes,
        "good_prime_frontier": {
            "largest_selected_good_prime": recomputed_frontier[
                "largest_selected_good_prime"
            ],
            "degrees_attaining_largest_selected_prime": recomputed_frontier[
                "degrees_attaining_largest_selected_prime"
            ],
            "observed_selected_good_primes": recomputed_frontier[
                "observed_selected_good_primes"
            ],
            "selection_calibration": recomputed_frontier["selection_calibration"],
            "patch_timeout_attempt_count": recomputed_frontier[
                "patch_timeout_attempt_count"
            ],
            "claim_boundary": "finite degrees 2..300 only",
        },
        "fixed_prime_zero_band": zero_band,
        "exploratory_groebner_signatures": {
            "degree_range": [2, 49],
            "pure_exponent_offset_states": recomputed_signature_summary[
                "pure_exponent_offset_states"
            ],
            "claim_boundary": "producer-side finite structural probe only",
        },
        "modular_radical_certificate_pilot": {
            "verified_degrees": list(range(2, 9)),
            "identity_shape": "x_i^N=sum_j A_ij*g_(d+j) over one certified F_p",
            "independent_sparse_expansion": True,
            "cofactor_mutation_rejected": True,
            "claim_boundary": "finite proof-object architecture pilot only",
        },
        "rational_radical_certificate_pilot": {
            "verified_degrees": list(range(2, 13)),
            "memberships": 33,
            "one_lower_nonmemberships": 33,
            "complete_intersection_hilbert_functions": True,
            "euler_jacobian_nonzero_socle_classes": True,
            "adjugate_identities": True,
            "recurrence_gate": "STOP_LOW_COMPLEXITY",
            "excluded_recurrence_classes": {
                "rational_ratio_max_total_degree": 5,
                "order_two_max_polynomial_degree": 1,
            },
            "claim_boundary": "exact rational finite structural pilot only",
        },
        "resultants": {
            "independently_reconstructed_full_integer_degrees": list(range(2, 18)),
            "independently_reconstructed_crt_degrees": list(range(18, 26)),
            "modular_prime_support_parity": modular_parity,
            "gate": "STOP",
            "gate_reason": "all tested first-order rational-ratio recurrences are excluded on training",
            "reserved_holdouts": [20, 21, 22, 23, 24, 25],
        },
        "cofactors": {
            "verified_degrees": list(range(2, 9)),
            "identity": "A_d*g_d+B_d*g_(d+1)+C_d*g_(d+2)=x3^d",
            "gate": "STOP",
            "gate_reason": "the minimal d-independent homogeneity-compatible matrix recurrence is inconsistent",
            "reserved_holdout": [7, 8],
        },
        "falsification_lane": {
            "tested_degrees": list(range(2, 301)),
            "unresolved": [],
            "numerical_homotopy_triggered": False,
        },
        "next_route": "CANONICAL_EULER_SOCLE_IDENTITIES_OR_GOOD_PRIME_AUTOMATON",
        "inputs_sha256": {path.name: startup_inputs[path.name] for path in inputs},
        "sources_sha256": startup_sources,
        "runtime_sha256": {singular.name: startup_inputs[singular.name]},
        "environment": {
            "python": platform.python_version(),
        },
    }
    atomic_json_write(args.out, output)
    print(json.dumps({
        "status": "PASS",
        "finite_windows": 299,
        "resultant_degrees": 24,
        "cofactor_degrees": 7,
        "rational_certificate_degrees": 11,
    }, sort_keys=True))
    print("root receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 ROOT VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
