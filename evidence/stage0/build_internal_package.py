#!/usr/bin/env python3
"""Build the curated, deterministic R(3) Stage 0 internal package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from r3_common import R3Error, require
from verify_package import verify_directory


BASE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = BASE.parents[1] / "outputs" / "r3-stage0-internal-2026-08-13"

RESULTANT_RAW = [
    "resultant-prefix-ordinary.json", "resultant-prefix-optimized.json",
    "resultant-prefix-verification.json",
] + [
    f"resultant-shard-{variant}-d{d:02}.json"
    for variant in ("ordinary", "optimized")
    for d in range(18, 26)
] + [
    f"resultant-shard-verification-d{d:02}.json"
    for d in range(18, 26)
]
SCREEN_RANGES = [(start, min(start + 9, 300)) for start in range(50, 301, 10)]
SCREEN_RAW = [
    f"projective-patch-shard-d{start:03}-{end:03}.json"
    for start, end in SCREEN_RANGES
]

FILES = [
    "README.md", "SPEC.md", "RESEARCH_REPORT.md", "RESULTANT_NORMALIZATION.md",
    "ENVIRONMENT.md", "SOURCE_CHECK.md", "GOOD_PRIME_FRONTIER.md",
    "EULER_SOCLE_ROUTE.md",
    "METHODOLOGY_AUDIT.md", "COMPLETION_AUDIT.md",
    "REPRODUCE.md", "REPLAY.sh",
    "r3_common.py", "modular_colength.py", "run_modular_screen_shards.py",
    "assemble_modular_screen_shards.py", "verify_colength.py",
    "run_good_prime_grid_shards.py", "assemble_good_prime_grid_shards.py",
    "verify_good_prime_grid.py", "analyze_good_prime_frontier.py",
    "projective_patch_screen.py", "verify_projective_patch_screen.py",
    "run_projective_patch_shards.py", "assemble_projective_patch_shards.py",
    "analyze_combined_good_prime_frontier.py",
    "probe_groebner_signatures.py",
    "extract_modular_radical_certificates.py",
    "verify_modular_radical_certificates.py",
    "extract_rational_radical_certificates.py",
    "verify_rational_radical_certificates.py",
    "extract_cofactors.py", "verify_cofactors.py", "cover_resultant.py",
    "cover_resultant_crt.py", "verify_resultant_crt.py",
    "verify_resultant_prefix.py",
    "assemble_resultant_shards.py", "verify_resultants.py",
    "analyze_cofactor_recurrence.py",
    "analyze_euler_socle_recurrence.py",
    "build_falsification_queue.py", "verify_counterexample_candidate.py",
    "verify_root.py", "verify_package.py",
    "build_internal_package.py",
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
    "cofactors-d2-8-verification.json", "cofactor-recurrence-screen.json",
    "falsification-queue.json", "root-receipt.json",
] + RESULTANT_RAW + SCREEN_RAW


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists(), f"refusing to overwrite existing package: {output}")
    root_source_inventory = {path.name for path in BASE.glob("*.py")}
    packaged_source_inventory = {name for name in FILES if name.endswith(".py")}
    require(
        root_source_inventory == packaged_source_inventory,
        "root-hashed and packaged Python source inventories differ: "
        f"root_only={sorted(root_source_inventory - packaged_source_inventory)}, "
        f"package_only={sorted(packaged_source_inventory - root_source_inventory)}",
    )
    require(all((BASE / name).is_file() for name in FILES), "one or more curated inputs are absent")
    require("WORK IN PROGRESS" not in (BASE / "README.md").read_text(),
            "README still marks the workflow as incomplete")
    require("WORK IN PROGRESS" not in (BASE / "RESEARCH_REPORT.md").read_text(),
            "research report still marks the workflow as incomplete")
    require("**State:** open" not in (BASE / "METHODOLOGY_AUDIT.md").read_text(),
            "methodology audit is still open")
    completion_audit = (BASE / "COMPLETION_AUDIT.md").read_text()
    require("**State:** terminal pre-freeze" in completion_audit,
            "completion audit is not terminal pre-freeze")
    require("`PENDING`" not in completion_audit,
            "completion audit still contains pending requirements")
    root = json.loads((BASE / "root-receipt.json").read_text())
    require(root.get("status") == "PASS", "root receipt is not terminal PASS")
    zip_path = output.with_suffix(".zip")
    companion = zip_path.with_suffix(".zip.sha256")
    require(not zip_path.exists(), f"refusing to overwrite existing archive: {zip_path}")
    require(not companion.exists(), f"refusing to overwrite existing hash: {companion}")
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    for name in FILES:
        shutil.copy2(BASE / name, staging / name)
    for executable_name in ("REPLAY.sh",):
        (staging / executable_name).chmod(0o755)
    manifest = {
        "schema": "polydegree-r3-stage0-manifest-v1",
        "status": "FROZEN_INTERNAL",
        "claim_boundary": (
            "Manifest and archive hashes establish byte integrity only; mathematical "
            "claims are bounded by root-receipt.json and RESEARCH_REPORT.md."
        ),
        "files": [
            {
                "path": name,
                "bytes": (staging / name).stat().st_size,
                "sha256": digest(staging / name),
            }
            for name in sorted(FILES)
        ],
    }
    manifest_path = staging / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    require(verify_directory(staging).get("root_status") == "PASS",
            "staged package failed its pre-freeze integrity/root verification")

    temporary_zip_fd, temporary_zip_name = tempfile.mkstemp(
        prefix=f".{zip_path.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(temporary_zip_fd)
    temporary_zip = Path(temporary_zip_name)
    with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(staging.iterdir(), key=lambda item: item.name):
            info = zipfile.ZipInfo(f"{output.name}/{path.name}", date_time=(2026, 8, 13, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (
                0o755 if path.name == "REPLAY.sh"
                else 0o644
            ) << 16
            archive.writestr(info, path.read_bytes())
    temporary_companion_fd, temporary_companion_name = tempfile.mkstemp(
        prefix=f".{companion.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(temporary_companion_fd)
    temporary_companion = Path(temporary_companion_name)
    temporary_companion.write_text(f"{digest(temporary_zip)}  {zip_path.name}\n")
    staging.replace(output)
    temporary_zip.replace(zip_path)
    temporary_companion.replace(companion)
    print(json.dumps({
        "status": "FROZEN_INTERNAL",
        "files": len(FILES),
        "zip_sha256": digest(zip_path),
    }, sort_keys=True))
    print("package:", output)
    print("archive:", zip_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (R3Error, OSError, zipfile.BadZipFile) as exc:
        print(f"R3 PACKAGE BUILD FAILED: {exc}")
        raise SystemExit(1)
