#!/usr/bin/env python3
"""Independent structural verifier for R(3) modular-colength receipts."""

from __future__ import annotations

import argparse
import copy
import json
import platform
import shutil
from pathlib import Path

import sympy as sp

from r3_common import (
    R3Error,
    atomic_json_write,
    bezout_colength,
    g_terms,
    primes_through,
    require,
    sha256,
)


SCRIPT_PATH = Path(__file__).resolve()
COMMON_PATH = SCRIPT_PATH.with_name("r3_common.py")
PRODUCER_PATH = SCRIPT_PATH.with_name("modular_colength.py")
ASSEMBLER_PATH = SCRIPT_PATH.with_name("assemble_modular_screen_shards.py")
DEFAULT_SINGULAR = Path(shutil.which("Singular") or "/opt/homebrew/bin/Singular").resolve()


def inverse_series_coefficients(max_n: int) -> dict[int, dict[tuple[int, int, int], int]]:
    """Invert H(t)=t+x1*t^2+x2*t^3+x3*t^4 without the multinomial formula."""
    require(max_n >= 0, "max_n must be nonnegative")
    x1, x2, x3, t, w = sp.symbols("x1 x2 x3 t w")
    variables = (x1, x2, x3)
    H = t + x1 * t**2 + x2 * t**3 + x3 * t**4
    G = w
    for power in range(2, max_n + 2):
        unknown = sp.Symbol(f"c{power}")
        candidate = G + unknown * w**power
        truncated = sp.expand(H.subs(t, candidate)).series(w, 0, power + 1).removeO()
        equation = sp.expand(truncated - w).coeff(w, power)
        solutions = sp.solve(equation, unknown)
        require(len(solutions) == 1, f"series reversion did not have one solution at {power}")
        G = sp.expand(candidate.subs(unknown, solutions[0]))
    answer: dict[int, dict[tuple[int, int, int], int]] = {}
    for n in range(max_n + 1):
        polynomial = sp.Poly(sp.expand(G.coeff(w, n + 1)), *variables, domain=sp.ZZ)
        answer[n] = {tuple(int(v) for v in monomial): int(coefficient)
                     for monomial, coefficient in polynomial.terms()}
    return answer


def verify_formula_independence(max_n: int = 8) -> dict[str, object]:
    reverted = inverse_series_coefficients(max_n)
    for n in range(max_n + 1):
        multinomial = {exponents: coefficient for exponents, coefficient in g_terms(n)}
        require(reverted[n] == multinomial, f"series-reversion mismatch at n={n}")
    corrupted = dict(reverted[max_n])
    first = next(iter(corrupted))
    corrupted[first] += 1
    require(corrupted != {exponents: coefficient for exponents, coefficient in g_terms(max_n)},
            "formula mutation negative control failed")
    return {
        "method": "formal compositional reversion in SymPy over ZZ",
        "checked_n": list(range(max_n + 1)),
        "coefficient_mutation_rejected": True,
    }


def remove_timing(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: remove_timing(item)
            for key, item in value.items()
            if key not in {"elapsed_seconds", "assembly", "grid_assembly"}
        }
    if isinstance(value, list):
        return [remove_timing(item) for item in value]
    return value


def verify_source_bindings(
    receipt: dict[str, object], singular_executable: Path = DEFAULT_SINGULAR
) -> None:
    bindings = receipt.get("startup_sha256")
    require(isinstance(bindings, dict), "missing startup_sha256 bindings")
    required = [PRODUCER_PATH, COMMON_PATH]
    for path in required:
        keys = [key for key in bindings if Path(key).name == path.name]
        require(len(keys) == 1, f"receipt must bind exactly one {path.name}")
        require(bindings.get(keys[0]) == sha256(path),
                f"stale or missing source hash for {path.name}")
    singular_keys = [key for key in bindings if Path(key).name == "Singular"]
    require(len(singular_keys) == 1, "receipt must bind exactly one Singular executable")
    require(singular_executable.is_file(), "current Singular executable is absent")
    require(bindings[singular_keys[0]] == sha256(singular_executable),
            "current Singular bytes do not match the receipt binding")
    assembly = receipt.get("assembly")
    if assembly is not None:
        require(isinstance(assembly, dict) and assembly.get("gap_free") is True,
                "invalid modular assembly record")
        require(assembly.get("script_sha256") == sha256(ASSEMBLER_PATH),
                "modular assembly script binding is stale")
        inputs = assembly.get("inputs_sha256")
        require(isinstance(inputs, dict) and inputs, "modular assembly lacks shard bindings")
        for name, expected in inputs.items():
            path = SCRIPT_PATH.parent / name
            require(path.is_file() and sha256(path) == expected,
                    f"modular assembly shard is absent or changed: {name}")


def verify_receipt(
    receipt: dict[str, object],
    expected_d_min: int,
    expected_d_max: int,
    expected_prime_max: int | None,
    require_good_coverage: bool,
    singular_executable: Path = DEFAULT_SINGULAR,
) -> dict[str, object]:
    require(receipt.get("schema") == "polydegree-r3-modular-colength-v1", "wrong schema")
    require(receipt.get("status") == "PASS", "only terminal PASS receipts are normative")
    require(receipt.get("incomplete") == [], "PASS receipt contains incomplete cases")
    verify_source_bindings(receipt, singular_executable)
    parameters = receipt.get("parameters")
    require(isinstance(parameters, dict), "missing parameters")
    require(parameters.get("d_min") == expected_d_min, "d_min mismatch")
    require(parameters.get("d_max") == expected_d_max, "d_max mismatch")
    primes = parameters.get("primes")
    require(isinstance(primes, list) and primes, "missing prime inventory")
    if expected_prime_max is not None:
        require(primes == primes_through(expected_prime_max), "prime inventory mismatch")
    require(primes == sorted(set(primes)), "prime inventory is not strictly increasing")
    rows = receipt.get("rows")
    require(isinstance(rows, list) and rows, "missing rows")
    first_good = parameters.get("first_good")
    require(isinstance(first_good, bool), "first_good flag is not Boolean")

    seen: set[tuple[int, int]] = set()
    good_degrees: set[int] = set()
    good_count = 0
    bad_count = 0
    rows_by_d: dict[int, list[int]] = {d: [] for d in range(expected_d_min, expected_d_max + 1)}
    for row in rows:
        require(isinstance(row, dict), "non-object row")
        d = row.get("d")
        prime = row.get("prime")
        require(isinstance(d, int) and expected_d_min <= d <= expected_d_max, "row d out of range")
        require(isinstance(prime, int) and prime in primes, "row prime not in inventory")
        require((d, prime) not in seen, "duplicate (d,p) row")
        seen.add((d, prime))
        rows_by_d[d].append(prime)
        expected = bezout_colength(d)
        require(row.get("expected_colength") == expected, "stored expected colength mismatch")
        vdim = row.get("vdim")
        classification = row.get("classification")
        if classification == "GOOD":
            require(vdim == expected, "GOOD row has wrong vdim")
            good_count += 1
            good_degrees.add(d)
        elif classification == "BAD":
            require(vdim == -1, "BAD row is not positive-dimensional")
            bad_count += 1
        else:
            raise R3Error("unknown row classification")
        require(isinstance(row.get("groebner_basis_size"), int)
                and row["groebner_basis_size"] >= 0, "invalid Gröbner-basis size")
        if classification == "GOOD":
            require(row["groebner_basis_size"] >= 1,
                    "GOOD row cannot have an empty Gröbner basis")

    for d, attempted in rows_by_d.items():
        if first_good:
            require(d in good_degrees, f"screening degree d={d} has no GOOD prime")
            good_prime = next(row["prime"] for row in rows
                              if row["d"] == d and row["classification"] == "GOOD")
            expected_prefix = [prime for prime in primes if prime <= good_prime]
            require(attempted == expected_prefix, f"d={d} is not the exact first-good prefix")
        else:
            require(attempted == primes, f"d={d} does not contain the full prime map")

    counts = receipt.get("counts")
    require(isinstance(counts, dict), "missing counts")
    require(counts == {"rows": len(rows), "good": good_count, "bad": bad_count, "incomplete": 0},
            "receipt counts mismatch")
    coverage = receipt.get("good_degree_coverage")
    require(coverage == sorted(good_degrees), "good-degree coverage mismatch")
    if first_good or require_good_coverage:
        require(coverage == list(range(expected_d_min, expected_d_max + 1)),
                "not every requested degree has a GOOD certificate")

    controls = receipt.get("controls")
    require(isinstance(controls, dict), "missing controls")
    baseline = controls.get("baseline")
    mutation = controls.get("zero_third_mutation")
    require(isinstance(baseline, dict) and baseline.get("vdim") == bezout_colength(2),
            "baseline control mismatch")
    require(isinstance(mutation, dict) and mutation.get("vdim") == -1,
            "zero-third mutation control mismatch")
    require(controls.get("impossible_finite_colength_rejected") is True,
            "impossible finite-colength control missing")
    return {
        "row_count": len(rows),
        "good_count": good_count,
        "bad_count": bad_count,
        "degree_count": expected_d_max - expected_d_min + 1,
        "prime_count": len(primes),
        "first_good": first_good,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--peer", type=Path)
    parser.add_argument("--expected-d-min", type=int, required=True)
    parser.add_argument("--expected-d-max", type=int, required=True)
    parser.add_argument("--expected-prime-max", type=int)
    parser.add_argument("--require-good-coverage", action="store_true")
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.input.is_file(), "input receipt does not exist")
    require(args.out.resolve() not in {
        args.input.resolve(),
        args.peer.resolve() if args.peer is not None else Path("/")
    }, "verification output must not overwrite an input")
    singular = args.singular.resolve()
    require(singular.is_file(), "Singular executable is absent")
    source_paths = (SCRIPT_PATH, COMMON_PATH, PRODUCER_PATH)
    watched_paths = [args.input, singular]
    if args.peer is not None:
        require(args.peer.is_file(), "peer receipt does not exist")
        watched_paths.append(args.peer)
    startup_sources = {path.name: sha256(path) for path in source_paths}
    startup_inputs = {str(path.resolve()): sha256(path) for path in watched_paths}
    input_hash = startup_inputs[str(args.input.resolve())]
    receipt = json.loads(args.input.read_text())
    summary = verify_receipt(
        receipt, args.expected_d_min, args.expected_d_max, args.expected_prime_max,
        args.require_good_coverage, singular,
    )
    peer_parity = None
    if args.peer is not None:
        peer = json.loads(args.peer.read_text())
        verify_receipt(
            peer, args.expected_d_min, args.expected_d_max, args.expected_prime_max,
            args.require_good_coverage, singular,
        )
        require(remove_timing(copy.deepcopy(receipt)) == remove_timing(copy.deepcopy(peer)),
                "ordinary/optimized receipts differ outside timing fields")
        peer_parity = {
            "peer_sha256": startup_inputs[str(args.peer.resolve())],
            "timing_free_projection_equal": True,
        }
    formula = verify_formula_independence()
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "colength verifier source changed during verification")
    require({str(path.resolve()): sha256(path) for path in watched_paths} == startup_inputs,
            "colength verifier input or Singular executable changed during verification")
    output = {
        "schema": "polydegree-r3-modular-colength-verification-v1",
        "status": "PASS",
        "input_sha256": input_hash,
        "summary": summary,
        "formula_independence": formula,
        "peer_parity": peer_parity,
        "source_sha256": startup_sources,
        "environment": {"python": platform.python_version(), "sympy": sp.__version__},
    }
    atomic_json_write(args.out, output)
    print(json.dumps({"status": "PASS", **summary}, sort_keys=True))
    print("verification receipt:", args.out.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 COLENGTH VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
