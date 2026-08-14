#!/usr/bin/env python3
"""Fast fail-closed checks for the public Furter R(3) release."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "r3-stage0-internal-2026-08-13.zip"
EXPECTED_ARCHIVE_SHA256 = "4538ce575a9dc2cbb6b6b4fcd097e1858a4c9a0578e1e101ead5f2f34c7110a9"
REQUIRED = [
    "README.md", "CLAIM_BOUNDARY.md", "PROVENANCE.md", "RELEASE_NOTES.md",
    "LICENSE", "LICENSE-CODE", "LICENSE_MAP.md", "CITATION.cff",
    "manuscript/paper.tex", "manuscript/paper.md", "manuscript/paper.pdf",
    "challenge/challenge.json", "challenge/verify_challenge.py",
    "novelty/target.yaml", "novelty/NOVELTY_REPORT.md",
    "evidence/stage0/root-receipt.json",
    "evidence/r3-stage0-internal-2026-08-13.verification.json",
    "r3-stage0-internal-2026-08-13.zip",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"REFUSING: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    for relative in REQUIRED:
        require((ROOT / relative).is_file(), f"missing required file {relative}")

    require(sha256(ARCHIVE) == EXPECTED_ARCHIVE_SHA256, "frozen archive hash drift")
    root = json.loads((ROOT / "evidence/stage0/root-receipt.json").read_text())
    require(root["status"] == "PASS", "root receipt is not PASS")
    require(root["finite_rigidity_windows"] == {"count": 299, "d_max": 300,
                                                 "d_min": 2},
            "finite theorem inventory drift")
    require("remain open" in root["claim_boundary"], "open-claim boundary missing")

    subprocess.run([sys.executable, str(ROOT / "challenge/verify_challenge.py")],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    public_text_files = [
        ROOT / "README.md", ROOT / "CLAIM_BOUNDARY.md", ROOT / "PROVENANCE.md",
        ROOT / "RELEASE_NOTES.md", ROOT / "CITATION.cff",
        ROOT / "manuscript/paper.tex", ROOT / "manuscript/paper.md",
        ROOT / "challenge/challenge.json", ROOT / "novelty/NOVELTY_REPORT.md",
    ]
    forbidden = re.compile(
        r"(ZENODO_ACCESS_TOKEN|OPENAI_API_KEY|ANTHROPIC_API_KEY|ghp_[A-Za-z0-9]+|"
        r"file://|/Users/admin/)"
    )
    for path in public_text_files:
        require(not forbidden.search(path.read_text(encoding="utf-8")),
                f"private path or secret-like text in {path.relative_to(ROOT)}")

    print(json.dumps({
        "status": "PASS",
        "archive_sha256": sha256(ARCHIVE),
        "paper_pdf_sha256": sha256(ROOT / "manuscript/paper.pdf"),
        "root_receipt_sha256": sha256(ROOT / "evidence/stage0/root-receipt.json"),
        "finite_rigidity_windows": root["finite_rigidity_windows"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

