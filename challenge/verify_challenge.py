#!/usr/bin/env python3
"""Fail-closed structural verifier for the Universal R(3) Challenge record."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHALLENGE = Path(__file__).with_name("challenge.json")


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
    payload = json.loads(CHALLENGE.read_text(encoding="utf-8"))
    require(payload["schema"] == "universal-r3-challenge-v1", "wrong schema")
    require(payload["creator"] == "Anonymous", "creator drift")
    require(payload["claim_boundary"]["proved"] ==
            "R(3,n) for every integer 1 <= n <= 299", "proved range drift")
    require(payload["claim_boundary"]["open"] ==
            "R(3,n) for all n >= 1", "open target drift")
    require(payload["normalization"]["furter_index"] == "n=d-1",
            "index convention drift")
    require(payload["completed_benchmark"]["d_range"] == [2, 300],
            "benchmark degree range drift")
    require(payload["completed_benchmark"]["furter_n_range"] == [1, 299],
            "benchmark Furter range drift")

    route_ids = [route["id"] for route in payload["routes"]]
    require(route_ids == ["canonical-euler-socle", "finite-prime-good-automaton",
                          "exceptional-initial-state"], "route inventory drift")
    require(all(route["obligations"] and route["falsifiers"]
                for route in payload["routes"]), "empty obligations or falsifiers")

    root_receipt = ROOT / payload["completed_benchmark"]["root_receipt"]
    external_receipt = ROOT / payload["completed_benchmark"]["archive_verification"]
    require(root_receipt.is_file(), "missing root receipt")
    require(external_receipt.is_file(), "missing external verification receipt")

    root = json.loads(root_receipt.read_text(encoding="utf-8"))
    require(root["status"] == "PASS", "root receipt is not PASS")
    require(root["finite_rigidity_windows"] == {"count": 299, "d_max": 300,
                                                 "d_min": 2},
            "root finite inventory drift")
    require("Universal R(3)" in root["claim_boundary"],
            "root claim boundary missing universal exclusion")

    external = json.loads(external_receipt.read_text(encoding="utf-8"))
    require(external["status"] == "PASS", "external package receipt is not PASS")
    require(external["inputs_sha256"]["r3-stage0-internal-2026-08-13.zip"] ==
            payload["completed_benchmark"]["evidence_archive_sha256"],
            "archive SHA-256 drift")

    print(json.dumps({
        "status": "PASS",
        "schema": payload["schema"],
        "challenge_sha256": sha256(CHALLENGE),
        "root_receipt_sha256": sha256(root_receipt),
        "external_receipt_sha256": sha256(external_receipt),
        "route_ids": route_ids,
        "claim_boundary": payload["claim_boundary"],
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
