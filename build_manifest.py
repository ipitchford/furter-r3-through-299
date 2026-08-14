#!/usr/bin/env python3
"""Create a deterministic SHA-256 manifest for the reviewed public tree."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "MANIFEST.json"
EXCLUDED_PARTS = {".git", "build", "__pycache__"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == OUTPUT:
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        files.append({
            "path": relative.as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    payload = {
        "schema": "furter-r3-public-manifest-v1",
        "version": "0.1.0-candidate",
        "creator": "Anonymous",
        "files": files,
    }
    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n",
                         encoding="utf-8")
    temporary.replace(OUTPUT)
    print(f"wrote {OUTPUT} with {len(files)} entries")


if __name__ == "__main__":
    main()

