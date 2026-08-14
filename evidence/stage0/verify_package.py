#!/usr/bin/env python3
"""Fail-closed manifest and ZIP verifier for the R(3) Stage 0 package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


DEFAULT_SINGULAR = Path(shutil.which("Singular") or "/opt/homebrew/bin/Singular").resolve()
SCRIPT_PATH = Path(__file__).resolve()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json_write(path: Path, payload: dict[str, object]) -> None:
    path = path.resolve()
    require(path.parent.is_dir(), "verification-receipt parent is absent")
    require(not path.exists(), f"refusing to overwrite verification receipt: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_directory(directory: Path) -> dict[str, object]:
    manifest_path = directory / "MANIFEST.json"
    require(manifest_path.is_file(), "MANIFEST.json is absent")
    manifest = json.loads(manifest_path.read_text())
    require(manifest.get("schema") == "polydegree-r3-stage0-manifest-v1",
            "wrong manifest schema")
    require(manifest.get("status") == "FROZEN_INTERNAL", "manifest is not frozen")
    rows = manifest.get("files")
    require(isinstance(rows, list) and rows, "manifest has no file rows")
    require(all(isinstance(row, dict) and isinstance(row.get("path"), str) and
                isinstance(row.get("bytes"), int) and row["bytes"] >= 0 and
                isinstance(row.get("sha256"), str) for row in rows),
            "manifest contains a malformed file row")
    expected = {row["path"] for row in rows}
    require(len(expected) == len(rows), "manifest contains duplicate file rows")
    actual = {path.name for path in directory.iterdir() if path.name != "MANIFEST.json"}
    require(actual == expected,
            f"payload inventory mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    for row in rows:
        path = directory / row["path"]
        require(path.is_file(), f"manifested path absent: {row['path']}")
        require(path.stat().st_size == row["bytes"], f"size mismatch: {row['path']}")
        require(digest(path) == row["sha256"], f"hash mismatch: {row['path']}")
    root = json.loads((directory / "root-receipt.json").read_text())
    completion_audit = (directory / "COMPLETION_AUDIT.md").read_text()
    require("**State:** terminal pre-freeze" in completion_audit and
            "`PENDING`" not in completion_audit,
            "completion audit is not terminal pre-freeze")
    require(root.get("status") == "PASS", "root receipt is not PASS")
    require(root.get("finite_rigidity_windows") == {"d_min": 2, "d_max": 300, "count": 299},
            "root finite-window claim mismatch")
    require(root.get("resultants", {}).get("gate") == "STOP", "resultant gate is not STOP")
    require(root.get("resultants", {}).get(
        "independently_reconstructed_full_integer_degrees"
    ) == list(range(2, 18)), "root full-integer reconstruction inventory mismatch")
    require(root.get("resultants", {}).get(
        "independently_reconstructed_crt_degrees"
    ) == list(range(18, 26)), "root CRT reconstruction inventory mismatch")
    require(root.get("cofactors", {}).get("gate") == "STOP", "cofactor gate is not STOP")
    require(
        root.get("modular_radical_certificate_pilot", {}).get("verified_degrees")
        == list(range(2, 9))
        and root.get("modular_radical_certificate_pilot", {}).get(
            "independent_sparse_expansion"
        )
        is True,
        "root modular radical certificate pilot mismatch",
    )
    require(
        root.get("rational_radical_certificate_pilot")
        == {
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
        "root rational radical certificate pilot mismatch",
    )
    expected_zero_band = {
        "analytic_statement": (
            "g_(n,3)=0 mod p when n=-k mod p, "
            "2<=k<=floor((p+2)/4), p>=7"
        ),
        "finite_regression_coefficient_range": [0, 51],
        "finite_regression_degree_range": [2, 49],
        "finite_regression_prime_range": [7, 53],
        "checked_primes": [7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53],
        "zero_polynomials_checked": 114,
        "forced_bad_windows_checked": 169,
        "small_prime_bad_witnesses": [[2, 2], [3, 3], [5, 6]],
        "claim_boundary": (
            "finite executable regression; the all-prime proof is analytic"
        ),
    }
    require(root.get("fixed_prime_zero_band") == expected_zero_band,
            "root fixed-prime zero-band regression mismatch")
    expected_generator_axes = {
        "coefficient_range": [0, 302],
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
        "axis_values_checked": 909,
        "claim_boundary": (
            "closed-form pure-axis regression; full coefficients are independently "
            "reverted through n=10"
        ),
    }
    require(
        root.get("generator_axis_specializations") == expected_generator_axes,
        "root generator-axis specialization regression mismatch",
    )
    source_bindings = root.get("sources_sha256")
    require(isinstance(source_bindings, dict) and source_bindings,
            "root lacks source bindings")
    packaged_python = {path.name for path in directory.glob("*.py")}
    require(
        set(source_bindings) == packaged_python,
        "packaged and root-bound Python source inventories differ: "
        f"root_only={sorted(set(source_bindings) - packaged_python)}, "
        f"package_only={sorted(packaged_python - set(source_bindings))}",
    )
    for binding_name in ("inputs_sha256", "sources_sha256"):
        bindings = root.get(binding_name)
        require(isinstance(bindings, dict) and bindings,
                f"root lacks {binding_name}")
        for name, expected_hash in bindings.items():
            path = directory / name
            require(path.is_file() and digest(path) == expected_hash,
                    f"root {binding_name} mismatch: {name}")
    return {"files": len(rows), "root_status": "PASS"}


def replay_extracted(directory: Path, singular: Path, flint_python: Path) -> None:
    require(singular.is_file(), "current Singular executable is absent")
    require(flint_python.is_file(), "current python-flint interpreter is absent")
    environment = os.environ.copy()
    environment["PYTHON_BIN"] = sys.executable
    environment["FLINT_PYTHON_BIN"] = str(flint_python)
    environment["SINGULAR_BIN"] = str(singular)
    completed = subprocess.run(
        ["zsh", str(directory / "REPLAY.sh")],
        cwd=directory,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        # The extracted replay includes the exact prefix reconstruction and
        # eight high-degree CRT reconstructions.  Keep a finite fail-closed
        # bound with cross-machine headroom for the complete sequential chain.
        timeout=57600,
        check=False,
    )
    require(completed.returncode == 0,
            f"fresh extracted replay failed:\n{completed.stdout[-4000:]}")
    require("R3_STAGE0_REPLAY_PASS" in completed.stdout,
            "fresh extracted replay lacked its terminal marker")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--sha256", type=Path)
    parser.add_argument("--singular", type=Path, default=DEFAULT_SINGULAR)
    parser.add_argument(
        "--flint-python",
        type=Path,
        default=Path(os.environ.get("FLINT_PYTHON_BIN", sys.executable)),
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    # Preserve the caller's virtual-environment launcher path.  Resolving a
    # venv's ``bin/python`` symlink before execution selects the base
    # interpreter and can discard the venv's site-packages (including flint).
    # ``digest`` still follows the symlink when binding executable bytes.
    flint_python = args.flint_python.expanduser().absolute()
    require(directory.is_dir(), "package directory is absent")
    if args.out is not None:
        output = args.out.resolve()
        require(directory not in output.parents,
                "external verification receipt must not be written inside the package")
        require(args.zip is not None and args.sha256 is not None,
                "a durable verification receipt requires ZIP and companion inputs")
        require(not output.exists(), "refusing to overwrite verification receipt")
    summary = verify_directory(directory)
    packaged_verifier = directory / SCRIPT_PATH.name
    require(packaged_verifier.is_file() and
            digest(packaged_verifier) == digest(SCRIPT_PATH),
            "running verifier bytes differ from the packaged verifier")
    if args.zip is not None:
        require(args.zip.is_file(), "ZIP is absent")
        if args.sha256 is not None:
            require(args.sha256.is_file(), "ZIP companion hash is absent")
            fields = args.sha256.read_text().strip().split()
            require(len(fields) == 2 and fields[0] == digest(args.zip) and
                    fields[1] == args.zip.name, "ZIP companion hash mismatch")
        with zipfile.ZipFile(args.zip) as archive:
            require(archive.testzip() is None, "ZIP CRC failure")
            expected_members = {
                f"{directory.name}/{name}"
                for name in {"MANIFEST.json"} |
                {row["path"] for row in json.loads(
                    (directory / "MANIFEST.json").read_text()
                )["files"]}
            }
            require(set(archive.namelist()) == expected_members and
                    len(archive.namelist()) == len(expected_members),
                    "ZIP member inventory differs from the manifest")
            with tempfile.TemporaryDirectory(prefix="r3-package-verify-") as temporary:
                archive.extractall(temporary)
                extracted = Path(temporary) / directory.name
                require(verify_directory(extracted) == summary, "extracted package summary differs")
                replay_extracted(
                    extracted, args.singular.resolve(), flint_python
                )
    result = {
        "status": "PASS",
        **summary,
        "fresh_extracted_replay": args.zip is not None,
    }
    if args.out is not None:
        singular = args.singular.resolve()
        verifier_python = Path(sys.executable).resolve()
        receipt = {
            "schema": "polydegree-r3-stage0-package-verification-v1",
            "status": "PASS",
            "claim_boundary": (
                "This receipt proves package byte integrity and successful replay from a "
                "fresh extraction in the recorded local runtime. Mathematical claims remain "
                "bounded by the packaged root receipt and research report."
            ),
            "package_directory_name": directory.name,
            "summary": result,
            "inputs_sha256": {
                "MANIFEST.json": digest(directory / "MANIFEST.json"),
                "root-receipt.json": digest(directory / "root-receipt.json"),
                args.zip.name: digest(args.zip),
                args.sha256.name: digest(args.sha256),
            },
            "runtime_sha256": {
                str(singular): digest(singular),
                str(flint_python): digest(flint_python),
                str(verifier_python): digest(verifier_python),
            },
            "verifier_sha256": digest(SCRIPT_PATH),
        }
        atomic_json_write(args.out, receipt)
        result["verification_receipt"] = str(args.out.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, json.JSONDecodeError, zipfile.BadZipFile,
            subprocess.SubprocessError) as exc:
        print(f"R3 PACKAGE VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
