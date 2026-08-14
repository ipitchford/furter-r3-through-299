#!/usr/bin/env python3
"""Formula-independent exact verifier for sparse R(3) cofactor certificates."""

from __future__ import annotations

import argparse
import copy
import json
import platform
import shutil
from fractions import Fraction
from pathlib import Path

from r3_common import R3Error, atomic_json_write, g_terms, require, sha256
from verify_colength import verify_formula_independence


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")
PRODUCER_PATH = SCRIPT_PATH.with_name("extract_cofactors.py")
FORMULA_VERIFIER_PATH = SCRIPT_PATH.with_name("verify_colength.py")
DEFAULT_SINGULAR = Path(shutil.which("Singular") or "/opt/homebrew/bin/Singular").resolve()
Monomial = tuple[int, int, int]
Sparse = dict[Monomial, Fraction]


def remove_nondeterminism(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: remove_nondeterminism(item)
            for key, item in value.items()
            if key != "elapsed_seconds"
        }
    if isinstance(value, list):
        return [remove_nondeterminism(item) for item in value]
    return value


def add_term(polynomial: Sparse, monomial: Monomial, coefficient: Fraction) -> None:
    value = polynomial.get(monomial, Fraction(0)) + coefficient
    if value:
        polynomial[monomial] = value
    elif monomial in polynomial:
        del polynomial[monomial]


def multiply(left: Sparse, right: Sparse) -> Sparse:
    answer: Sparse = {}
    for a, ca in left.items():
        for b, cb in right.items():
            monomial = tuple(x + y for x, y in zip(a, b))
            add_term(answer, monomial, ca * cb)
    return answer


def decode(rows: object) -> Sparse:
    require(isinstance(rows, list), "cofactor is not a sparse row list")
    answer: Sparse = {}
    for row in rows:
        require(isinstance(row, dict), "cofactor row is not an object")
        exponents = row.get("exponents")
        numerator = row.get("numerator")
        denominator = row.get("denominator")
        require(isinstance(exponents, list) and len(exponents) == 3
                and all(isinstance(value, int) and value >= 0 for value in exponents),
                "invalid cofactor exponents")
        require(isinstance(numerator, int) and isinstance(denominator, int) and denominator > 0,
                "invalid rational coefficient")
        monomial = tuple(exponents)
        require(monomial not in answer, "duplicate cofactor monomial")
        coefficient = Fraction(numerator, denominator)
        require(coefficient != 0, "zero sparse cofactor term")
        answer[monomial] = coefficient
    return answer


def g_sparse(n: int) -> Sparse:
    return {exponents: Fraction(coefficient) for exponents, coefficient in g_terms(n)}


def identity_residual(d: int, cofactors: dict[str, Sparse]) -> Sparse:
    residual: Sparse = {(0, 0, d): Fraction(-1)}
    for offset, name in enumerate(("A", "B", "C")):
        product = multiply(cofactors[name], g_sparse(d + offset))
        for monomial, coefficient in product.items():
            add_term(residual, monomial, coefficient)
    return residual


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    parser.add_argument("--expected-d-min", type=int, default=2)
    parser.add_argument("--expected-d-max", type=int, default=8)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.input.is_file() and args.peer.is_file(),
            "cofactor input or peer is absent")
    require(args.out.resolve() not in {args.input.resolve(), args.peer.resolve()},
            "cofactor verification output must not overwrite an input")
    singular = args.singular.resolve()
    require(singular.is_file(), "Singular executable is absent")
    source_paths = (SCRIPT_PATH, COMMON_PATH, PRODUCER_PATH, FORMULA_VERIFIER_PATH)
    watched_paths = (args.input, args.peer, singular)
    startup_sources = {path.name: sha256(path) for path in source_paths}
    startup_inputs = {str(path.resolve()): sha256(path) for path in watched_paths}
    receipt = json.loads(args.input.read_text())
    peer = json.loads(args.peer.read_text())
    require(remove_nondeterminism(copy.deepcopy(receipt)) ==
            remove_nondeterminism(copy.deepcopy(peer)),
            "ordinary/optimized cofactor receipts differ outside timing fields")
    require(receipt.get("schema") == "polydegree-r3-x3-cofactors-v1", "wrong schema")
    require(receipt.get("status") == "PASS", "cofactor producer was not terminal PASS")
    require(receipt.get("d_min") == args.expected_d_min, "d_min mismatch")
    require(receipt.get("d_max") == args.expected_d_max, "d_max mismatch")
    bindings = receipt.get("startup_sha256")
    require(isinstance(bindings, dict), "missing source bindings")
    for path in (PRODUCER_PATH, COMMON_PATH):
        keys = [key for key in bindings if Path(key).name == path.name]
        require(len(keys) == 1, f"receipt must bind exactly one {path.name}")
        require(bindings.get(keys[0]) == sha256(path), f"stale source binding for {path.name}")
    singular_keys = [key for key in bindings if Path(key).name == "Singular"]
    require(len(singular_keys) == 1, "receipt must bind exactly one Singular executable")
    require(singular.is_file() and bindings[singular_keys[0]] == sha256(singular),
            "current Singular bytes do not match the receipt binding")
    formula = verify_formula_independence(max_n=args.expected_d_max + 2)
    cases = receipt.get("cases")
    require(isinstance(cases, list), "missing cases")
    require([case.get("d") for case in cases] == list(range(args.expected_d_min, args.expected_d_max + 1)),
            "cofactor d inventory mismatch")
    verified = []
    mutation_rejected = False
    for case in cases:
        d = case["d"]
        raw = case.get("cofactors")
        require(isinstance(raw, dict) and set(raw) == {"A", "B", "C"}, "cofactor inventory mismatch")
        cofactors = {name: decode(raw[name]) for name in ("A", "B", "C")}
        residual = identity_residual(d, cofactors)
        require(not residual, f"exact sparse identity failed at d={d}")
        require(case.get("term_counts") == {name: len(cofactors[name]) for name in cofactors},
                "cofactor term counts mismatch")
        require(case.get("lower_power_remainder_nonzero") is True,
                "producer lower-power diagnostic missing")
        verified.append({"d": d, "term_counts": case["term_counts"]})
        if not mutation_rejected:
            mutated = {name: dict(value) for name, value in cofactors.items()}
            selected = next(iter(mutated["A"]))
            mutated["A"][selected] += 1
            mutation_rejected = bool(identity_residual(d, mutated))
    require(mutation_rejected, "cofactor coefficient mutation was not rejected")
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "cofactor verifier source changed during verification")
    require({str(path.resolve()): sha256(path) for path in watched_paths} == startup_inputs,
            "cofactor input, peer, or Singular executable changed during verification")
    output = {
        "schema": "polydegree-r3-x3-cofactor-verification-v1",
        "status": "PASS",
        "input_sha256": startup_inputs[str(args.input.resolve())],
        "peer_sha256": startup_inputs[str(args.peer.resolve())],
        "ordinary_optimized_timing_free_parity": True,
        "formula_independence": formula,
        "verified": verified,
        "coefficient_mutation_rejected": mutation_rejected,
        "producer_lower_power_diagnostics_present": True,
        "claim_boundary": (
            "Sparse convolution independently verifies the displayed x3^d identities. "
            "The lower-power nonmembership flags are producer diagnostics and are not "
            "independently certified by this receipt."
        ),
        "method": "formal reversion through g_10 plus independent sparse rational convolution",
        "source_sha256": startup_sources,
        "environment": {"python": platform.python_version()},
    }
    atomic_json_write(args.out, output)
    print(json.dumps({"status": "PASS", "verified": len(verified)}, sort_keys=True))
    print("verification receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 COFACTOR VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
