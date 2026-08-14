#!/usr/bin/env python3
"""Independent exact-determinant verifier for the R(3) resultant prefix."""

from __future__ import annotations

import argparse
import copy
import json
import platform
import sys
from pathlib import Path

import flint

from r3_common import R3Error, atomic_json_write, require, sha256
from verify_resultant_crt import (
    COMMON_PATH,
    EXACT_PRODUCER_PATH,
    independent_axis,
    independent_maps,
    select_columns,
    select_rows,
)


sys.set_int_max_str_digits(0)

SCRIPT_PATH = Path(__file__).resolve()
INDEPENDENT_CORE_PATH = SCRIPT_PATH.with_name("verify_resultant_crt.py")


def remove_timing(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: remove_timing(item)
            for key, item in value.items()
            if key != "elapsed_seconds"
        }
    if isinstance(value, list):
        return [remove_timing(item) for item in value]
    return value


def exact_sixth_root(value: int) -> int:
    require(isinstance(value, int) and value > 0,
            "corrected resultant must be a positive integer")
    low = 0
    high = 1 << ((value.bit_length() + 5) // 6 + 1)
    while low + 1 < high:
        middle = (low + high) // 2
        if middle**6 <= value:
            low = middle
        else:
            high = middle
    require(low > 0 and low**6 == value,
            "independently reconstructed corrected resultant is not a sixth power")
    return low


def verify_source_runtime(receipt: dict[str, object]) -> None:
    bindings = receipt.get("startup_sha256")
    require(isinstance(bindings, dict), "prefix lacks producer source bindings")
    for path in (EXACT_PRODUCER_PATH, COMMON_PATH):
        keys = [key for key in bindings if Path(key).name == path.name]
        require(len(keys) == 1 and bindings[keys[0]] == sha256(path),
                f"prefix binds stale {path.name}")
    runtime = receipt.get("runtime_sha256")
    require(isinstance(runtime, dict) and runtime, "prefix lacks runtime bindings")
    for raw_path, expected in runtime.items():
        path = Path(raw_path)
        require(path.is_file() and sha256(path) == expected,
                f"prefix runtime artifact is absent or changed: {path.name}")
    resolved_runtime = {Path(raw_path).resolve(): expected for raw_path, expected in runtime.items()}
    for current_path, label in (
        (Path(sys.executable).resolve(), "Python executable"),
        (Path(flint.__file__).resolve(), "loaded flint module"),
    ):
        require(current_path in resolved_runtime and
                sha256(current_path) == resolved_runtime[current_path],
                f"current {label} is not bound by the prefix receipt")


def verify_case(case: dict[str, object], d: int) -> int:
    require(case.get("d") == d, "prefix degree inventory mismatch")
    d1, d2, dimensions = independent_maps(d)
    require(case.get("dimensions") == dimensions,
            f"prefix Koszul dimensions mismatch at d={d}")
    require((d1 * d2).is_zero(), f"independent Koszul composition is nonzero at d={d}")
    pivots = case.get("pivot_columns")
    require(isinstance(pivots, list) and pivots == sorted(set(pivots)) and
            len(pivots) == d1.nrows() and
            all(isinstance(column, int) and 0 <= column < d1.ncols()
                for column in pivots),
            f"invalid prefix pivot inventory at d={d}")
    complement = sorted(set(range(d1.ncols())) - set(pivots))
    require(len(complement) == d2.ncols(),
            f"prefix pivot complement has wrong size at d={d}")
    numerator = int(select_columns(d1, pivots).det())
    denominator = int(select_rows(d2, complement).det())
    require(denominator != 0, f"prefix denominator determinant vanishes at d={d}")
    require(case.get("numerator_minor_det") == numerator and
            case.get("denominator_minor_det") == denominator,
            f"stored prefix determinant differs from independent reconstruction at d={d}")
    quotient, remainder = divmod(abs(numerator), abs(denominator))
    require(remainder == 0 and case.get("ordinary_cover_resultant_abs") == quotient,
            f"prefix determinant quotient mismatch at d={d}")
    x2, x3 = independent_axis(d)
    axis = abs(x3) ** 4 * (abs(x2) ** 3 if x2 is not None else 1)
    require(case.get("axis_correction") == {
        "x2_axis_coefficient": x2,
        "x2_missing_power": 3 if x2 is not None else 0,
        "x3_axis_coefficient": x3,
        "x3_missing_power": 4,
        "factor_abs": axis,
    }, f"prefix axis correction mismatch at d={d}")
    corrected = quotient * axis
    require(case.get("axis_corrected_cover_resultant_abs") == corrected,
            f"prefix corrected resultant mismatch at d={d}")
    weighted = exact_sixth_root(corrected)
    require(case.get("weighted_resultant_abs") == weighted and
            case.get("sixth_power_identity") is True,
            f"prefix weighted resultant mismatch at d={d}")
    return weighted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.input.is_file() and args.peer.is_file(),
            "prefix input or peer is absent")
    source_paths = (SCRIPT_PATH, INDEPENDENT_CORE_PATH, EXACT_PRODUCER_PATH, COMMON_PATH)
    startup_sources = {path.name: sha256(path) for path in source_paths}
    startup_inputs = {
        args.input.name: sha256(args.input),
        args.peer.name: sha256(args.peer),
    }
    receipt = json.loads(args.input.read_text())
    peer = json.loads(args.peer.read_text())
    for candidate in (receipt, peer):
        require(candidate.get("schema") == "polydegree-r3-cover-resultant-v2" and
                candidate.get("status") == "PASS" and
                candidate.get("d_min") == 2 and candidate.get("d_max") == 17,
                "invalid terminal exact-prefix metadata")
        verify_source_runtime(candidate)
    require(remove_timing(copy.deepcopy(receipt)) == remove_timing(copy.deepcopy(peer)),
            "ordinary/optimized exact prefixes differ outside timing")
    cases = receipt.get("cases")
    require(isinstance(cases, list) and
            [case.get("d") for case in cases] == list(range(2, 18)),
            "terminal exact prefix must be the contiguous range d=2..17")
    values = {d: verify_case(case, d) for d, case in zip(range(2, 18), cases)}
    mutation_rejected = (values[2] + 1) ** 6 != cases[0].get(
        "axis_corrected_cover_resultant_abs"
    )
    require(mutation_rejected, "prefix weighted-resultant mutation was not rejected")
    require({args.input.name: sha256(args.input), args.peer.name: sha256(args.peer)} ==
            startup_inputs, "exact-prefix input changed during verification")
    require({path.name: sha256(path) for path in source_paths} == startup_sources,
            "prefix verifier or a proof-relevant source changed during verification")
    output = {
        "schema": "polydegree-r3-resultant-prefix-verification-v1",
        "status": "PASS",
        "inputs_sha256": startup_inputs,
        "verified_values": [
            {"d": d, "weighted_resultant_abs": values[d]} for d in sorted(values)
        ],
        "ordinary_optimized_timing_free_parity": True,
        "independent_reconstruction": {
            "coefficients": "sparse formal compositional reversion",
            "koszul_maps": "independently assembled integer matrices",
            "determinants": "exact FLINT integer determinants",
        },
        "negative_controls": {
            "weighted_resultant_increment_rejected": mutation_rejected,
        },
        "source_sha256": startup_sources,
        "environment": {
            "python": platform.python_version(),
            "python_optimize": sys.flags.optimize,
        },
    }
    atomic_json_write(args.out, output)
    print(json.dumps({
        "status": "PASS",
        "degrees": sorted(values),
        "receipt": str(args.out.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, OSError, json.JSONDecodeError, IndexError, ValueError) as exc:
        print(f"R3 PREFIX VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
