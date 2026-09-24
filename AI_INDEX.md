# AI index — furter-r3-through-299

## Identity and version

Documentation addendum: 2026-09-24. Indexes [source commit 1d5bde22ec49](https://github.com/ipitchford/furter-r3-through-299/tree/1d5bde22ec4904b9994523ff59c2297ebab9aede) and candidate tag `v0.1.0`. This index was added after that release: it is **not** part of the original tag, DOI archive or frozen manifest. Existing release files and checksums remain unchanged. For historical manifest/allow-list checks, use a clean checkout of that tag, not this documentation-enriched branch. The addendum is authenticated by Git history.

[Release identity and DOI](README.md) · [Evidence Press context](https://evidencepress.org/releases/furter-r3-through-299/)

## Exact scope

The exact finite candidate is R(3,n) for 1≤n≤299. Same-prime GOOD special fibres transfer to characteristic zero by properness. This package alone does not prove universal R(3), the unrestricted Strong Factorial Conjecture, or general Polydegree.

The linked manuscript and claim register control all hypotheses and quantifiers; this index is a navigation aid, not a substitute proof.

## Claim and evidence map

- [manuscript/](manuscript/) — Manuscript source and PDF.
- [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md) — Scope.
- [REPLAY.sh](REPLAY.sh) — Fast versus full replay entry point.
- [evidence/r3-stage0-internal-2026-08-13.verification.json](evidence/r3-stage0-internal-2026-08-13.verification.json) — Recorded extraction receipt.
- [novelty/](novelty/) — Historical literature search.
- [PROVENANCE.md](PROVENANCE.md) — Provenance.
- [LICENSE_MAP.md](LICENSE_MAP.md) — Rights.

## Reproduce

From the indexed release root, after inspecting the commands and installing the documented environment:

```sh
zsh REPLAY.sh
FULL_EVIDENCE_REPLAY=1 zsh REPLAY.sh
```

The first command performs release/challenge validation only (PUBLIC_RELEASE_FAST_REPLAY_PASS). The second invokes the full Stage 0 chain; inspect evidence/stage0/REPLAY.sh for its environment. The README binds the separate evidence ZIP by SHA-256.

## Trust boundary and safe reuse

The README and challenge describe the frontier at release time. Do not interpret their 'remains open' wording as current: consult the live Evidence Press page and subsequent literature before selecting research. Internal cross-model review and replay are not external peer review.

No new mathematical validation, formalisation, independent reproduction or novelty audit was performed for this documentation repair. Preserve the anonymous attribution and existing citation metadata. Distinguish producer checks, finite formal results, universal written arguments and external review. Before downstream reuse, match the exact statement and dependency scope and check subsequent corrections; a DOI or successful command alone is not proof of correctness.

## Licence and provenance

Use the rights/provenance sources linked above and [README](README.md); cited and third-party material retains its own terms. This new index is dedicated under CC0-1.0, without changing any existing licence or attribution.

