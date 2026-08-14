#!/usr/bin/env python3
"""Assemble verified exact-prefix and per-degree R(3) resultant receipts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import sys
from pathlib import Path

from r3_common import R3Error, atomic_json_write, require, sha256
from verify_resultants import remove_nondeterminism, verify_resultant_receipt


sys.set_int_max_str_digits(0)

SCRIPT_PATH = Path(__file__).resolve()
BASE = SCRIPT_PATH.parent
PRODUCER_PATH = BASE / "cover_resultant.py"
COMMON_PATH = BASE / "r3_common.py"
CRT_VERIFIER_PATH = BASE / "verify_resultant_crt.py"
PREFIX_VERIFIER_PATH = BASE / "verify_resultant_prefix.py"
SOURCE_PATHS = (
    SCRIPT_PATH,
    COMMON_PATH,
    PRODUCER_PATH,
    BASE / "cover_resultant_crt.py",
    CRT_VERIFIER_PATH,
    PREFIX_VERIFIER_PATH,
    BASE / "verify_resultants.py",
)


def remove_elapsed(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: remove_elapsed(item)
            for key, item in value.items()
            if key != "elapsed_seconds"
        }
    if isinstance(value, list):
        return [remove_elapsed(item) for item in value]
    return value


def projection_sha256(receipt: dict[str, object]) -> str:
    encoded = json.dumps(
        remove_elapsed(receipt), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def read_frozen_json(path: Path) -> tuple[dict[str, object], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    value = json.loads(raw)
    require(isinstance(value, dict), f"JSON root is not an object: {path.name}")
    require(sha256(path) == digest, f"input changed while reading: {path.name}")
    return value, digest


def current_source_hashes() -> dict[str, str]:
    return {
        str(PRODUCER_PATH): sha256(PRODUCER_PATH),
        str(COMMON_PATH): sha256(COMMON_PATH),
    }


def verify_source_bindings(bindings: object) -> None:
    require(isinstance(bindings, dict), "missing resultant source bindings")
    for path in (PRODUCER_PATH, COMMON_PATH):
        keys = [key for key in bindings if Path(key).name == path.name]
        require(len(keys) == 1 and bindings[keys[0]] == sha256(path),
                f"resultant prefix binds stale {path.name}")


def verify_runtime(runtime: object) -> dict[str, str]:
    require(isinstance(runtime, dict) and runtime, "missing resultant runtime inventory")
    for raw_path, expected in runtime.items():
        require(isinstance(raw_path, str) and isinstance(expected, str),
                "invalid resultant runtime binding")
        path = Path(raw_path)
        require(path.is_file() and sha256(path) == expected,
                f"resultant runtime artifact is absent or changed: {path.name}")
    return runtime


def load_prefix(path: Path, expected_min: int, expected_target: int) -> tuple[dict[str, object], int]:
    require(path.is_file(), f"missing resultant prefix: {path}")
    receipt, _ = read_frozen_json(path)
    require(receipt.get("schema") == "polydegree-r3-cover-resultant-v2" and
            receipt.get("status") == "PASS",
            "invalid terminal resultant prefix receipt")
    require(receipt.get("d_min") == expected_min and
            isinstance(receipt.get("d_max"), int) and
            expected_min <= receipt["d_max"] < expected_target,
            "terminal resultant prefix range mismatch")
    cases = receipt.get("cases")
    require(isinstance(cases, list) and cases, "empty resultant prefix")
    prefix_end = receipt["d_max"]
    require([case.get("d") for case in cases] == list(range(expected_min, prefix_end + 1)),
            "resultant prefix is not gap-free")
    verify_source_bindings(receipt.get("startup_sha256"))
    verify_runtime(receipt.get("runtime_sha256"))
    verify_resultant_receipt(receipt, expected_min, prefix_end)
    return receipt, prefix_end


def shard_name(variant: str, d: int) -> str:
    return f"resultant-shard-{variant}-d{d:02}.json"


def verification_name(d: int) -> str:
    return f"resultant-shard-verification-d{d:02}.json"


def verified_prefix_values(
    prefix_path: Path, checkpoint: dict[str, object]
) -> tuple[dict[int, int], Path]:
    verification_path = prefix_path.parent / "resultant-prefix-verification.json"
    require(verification_path.is_file(), "missing independent exact-prefix verification")
    verification, _ = read_frozen_json(verification_path)
    require(
        verification.get("schema") == "polydegree-r3-resultant-prefix-verification-v1" and
        verification.get("status") == "PASS" and
        verification.get("inputs_sha256", {}).get(prefix_path.name) == sha256(prefix_path) and
        verification.get("ordinary_optimized_timing_free_parity") is True and
        verification.get("negative_controls", {}).get(
            "weighted_resultant_increment_rejected"
        ) is True,
        "invalid independent exact-prefix verification",
    )
    sources = verification.get("source_sha256")
    require(isinstance(sources, dict), "prefix verification lacks source bindings")
    for source_path in (PREFIX_VERIFIER_PATH, CRT_VERIFIER_PATH, PRODUCER_PATH, COMMON_PATH):
        require(sources.get(source_path.name) == sha256(source_path),
                f"prefix verification binds stale {source_path.name}")
    stored = verification.get("verified_values")
    expected = {
        case["d"]: case["weighted_resultant_abs"]
        for case in checkpoint["cases"]
    }
    require(stored == [
        {"d": d, "weighted_resultant_abs": expected[d]} for d in sorted(expected)
    ], "prefix verification value inventory is not exact")
    values = dict(expected)
    require(all(isinstance(value, int) and value > 0 for value in values.values()),
            "independent exact-prefix values differ from the checkpoint")
    return values, verification_path


def verified_crt_value(
    shard_path: Path, verification_path: Path, d: int
) -> int:
    require(verification_path.is_file(),
            f"missing independent CRT verification: {verification_path.name}")
    verification, _ = read_frozen_json(verification_path)
    require(
        verification.get("schema") ==
        "polydegree-r3-cover-resultant-crt-verification-v1" and
        verification.get("status") == "PASS" and
        (verification.get("input_sha256") == sha256(shard_path) or
         verification.get("input_timing_free_projection_sha256") ==
         projection_sha256(read_frozen_json(shard_path)[0])) and
        verification.get("negative_controls", {}).get(
            "weighted_resultant_increment_rejected"
        ) is True,
        f"invalid independent CRT verification at d={d}",
    )
    verified_values = verification.get("verified_values")
    require(isinstance(verified_values, list) and len(verified_values) == 1 and
            verified_values[0].get("d") == d,
            f"independent CRT verification inventory differs at d={d}")
    sources = verification.get("source_sha256")
    require(isinstance(sources, dict),
            f"CRT verification lacks source bindings at d={d}")
    for source_path in (CRT_VERIFIER_PATH, BASE / "cover_resultant_crt.py",
                        PRODUCER_PATH, COMMON_PATH):
        require(sources.get(source_path.name) == sha256(source_path),
                f"CRT verification binds stale {source_path.name} at d={d}")
    value = verified_values[0].get("weighted_resultant_abs")
    require(isinstance(value, int) and value > 0,
            f"CRT verification lacks a positive value at d={d}")
    return value


def assemble_variant(
    variant: str,
    prefix_path: Path,
    shard_directory: Path,
    output_path: Path,
    d_min: int,
    d_max: int,
    startup_sources: dict[str, str],
) -> dict[str, object]:
    checkpoint, prefix_end = load_prefix(prefix_path, d_min, d_max)
    values, prefix_verification_path = verified_prefix_values(prefix_path, checkpoint)
    inputs = {prefix_path.name: sha256(prefix_path)}
    input_paths = {prefix_path.name: prefix_path}
    inputs[prefix_verification_path.name] = sha256(prefix_verification_path)
    input_paths[prefix_verification_path.name] = prefix_verification_path
    for d in range(prefix_end + 1, d_max + 1):
        path = shard_directory / shard_name(variant, d)
        require(path.is_file(), f"missing resultant shard: {path.name}")
        receipt, shard_digest = read_frozen_json(path)
        require(receipt.get("schema") == "polydegree-r3-cover-resultant-crt-v1" and
                receipt.get("status") == "PASS" and receipt.get("d_min") == d and
                receipt.get("d_max") == d, f"resultant shard metadata mismatch at d={d}")
        shard_cases = receipt.get("cases")
        require(isinstance(shard_cases, list) and len(shard_cases) == 1 and
                shard_cases[0].get("d") == d,
                f"resultant shard case inventory mismatch at d={d}")
        weighted = shard_cases[0].get("weighted_resultant_abs")
        require(isinstance(weighted, int) and weighted > 0,
                f"resultant shard lacks a positive value at d={d}")
        verification_path = shard_directory / verification_name(d)
        require(verified_crt_value(path, verification_path, d) == weighted,
                f"independent CRT value differs at d={d}")
        values[d] = weighted
        inputs[path.name] = shard_digest
        input_paths[path.name] = path
        inputs[verification_path.name] = sha256(verification_path)
        input_paths[verification_path.name] = verification_path
    require(sorted(values) == list(range(d_min, d_max + 1)),
            "assembled resultant inventory is not gap-free")
    output = {
        "schema": "polydegree-r3-resultant-composite-v1",
        "status": "PASS",
        "claim_boundary": (
            "Exact finite weighted-resultant values: full-integer determinant-of-complex "
            "certificates on the prefix and independently verified modular determinant/CRT "
            "certificates on the remaining degrees."
        ),
        "d_min": d_min,
        "d_max": d_max,
        "values": [
            {"d": d, "weighted_resultant_abs": values[d]}
            for d in range(d_min, d_max + 1)
        ],
        "assembly": {
            "variant": variant,
            "prefix_end": prefix_end,
            "crt_start": prefix_end + 1,
            "gap_free": True,
            "inputs_sha256": inputs,
            "script_sha256": sha256(SCRIPT_PATH),
        },
        "environment": {
            "assembly_python": platform.python_version(),
        },
    }
    require(all(sha256(input_paths[name]) == expected
                for name, expected in inputs.items()),
            "a resultant input changed before assembled publication")
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "a resultant assembler source changed before publication")
    atomic_json_write(output_path, output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ordinary-prefix", type=Path, required=True)
    parser.add_argument("--optimized-prefix", type=Path, required=True)
    parser.add_argument("--shard-directory", type=Path, default=BASE)
    parser.add_argument("--ordinary-out", type=Path, required=True)
    parser.add_argument("--optimized-out", type=Path, required=True)
    parser.add_argument("--d-min", type=int, default=2)
    parser.add_argument("--d-max", type=int, default=25)
    args = parser.parse_args()
    startup_sources = {path.name: sha256(path) for path in SOURCE_PATHS}
    ordinary = assemble_variant(
        "ordinary", args.ordinary_prefix, args.shard_directory, args.ordinary_out,
        args.d_min, args.d_max, startup_sources,
    )
    optimized = assemble_variant(
        "optimized", args.optimized_prefix, args.shard_directory, args.optimized_out,
        args.d_min, args.d_max, startup_sources,
    )
    require(remove_nondeterminism(copy.deepcopy(ordinary["values"])) ==
            remove_nondeterminism(copy.deepcopy(optimized["values"])),
            "ordinary/optimized assembled mathematical cases differ outside timing")
    for d in range(ordinary["assembly"]["crt_start"], args.d_max + 1):
        ordinary_raw = json.loads(
            (args.shard_directory / shard_name("ordinary", d)).read_text()
        )
        optimized_raw = json.loads(
            (args.shard_directory / shard_name("optimized", d)).read_text()
        )
        require(remove_nondeterminism(copy.deepcopy(ordinary_raw)) ==
                remove_nondeterminism(copy.deepcopy(optimized_raw)),
                f"ordinary/optimized raw CRT shards differ outside timing at d={d}")
    require({path.name: sha256(path) for path in SOURCE_PATHS} == startup_sources,
            "a resultant assembler source changed during assembly")
    print(json.dumps({
        "status": "PASS",
        "cases": len(ordinary["values"]),
        "ordinary_prefix_end": ordinary["assembly"]["prefix_end"],
        "optimized_prefix_end": optimized["assembly"]["prefix_end"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, json.JSONDecodeError, OSError) as exc:
        print(f"R3 RESULTANT ASSEMBLY FAILED: {exc}")
        raise SystemExit(1)
