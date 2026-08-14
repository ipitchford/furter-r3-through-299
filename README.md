# Exact finite rigidity for Furter's R(3)

This repository accompanies the unrefereed candidate:

> **Exact finite theorem.** Furter's `R(3,n)` holds for every
> `1 <= n <= 299`.

Universal `R(3)` remains open.

- DOI: <https://doi.org/10.5281/zenodo.21939362>
- Repository: <https://github.com/ipitchford/furter-r3-through-299>

The proof is exact and computer-assisted. The finite range is certified by
same-prime GOOD special fibres and transferred to characteristic zero by
properness. The repository also contains a machine-readable Universal `R(3)`
Challenge describing the two leading structural routes.

## Layout

- `manuscript/` — LaTeX source and built PDF.
- `evidence/stage0/` — frozen proof scripts, receipts, and controls.
- `challenge/` — machine-readable open-problem specification and verifier.
- `novelty/` — formula-first public-literature search record.
- `CITATION.cff`, `LICENSE`, `LICENSE-CODE`, and `PROVENANCE.md` — release
  metadata and rights/provenance boundary.

## Replay

The complete frozen evidence archive is a release asset named
`r3-stage0-internal-2026-08-13.zip`. Its SHA-256 is

```text
4538ce575a9dc2cbb6b6b4fcd097e1858a4c9a0578e1e101ead5f2f34c7110a9
```

The extracted evidence directory contains its own `REPLAY.sh`, manifest,
root receipt, and package verifier. The external fresh-extraction receipt is
stored at `evidence/r3-stage0-internal-2026-08-13.verification.json`.

## Status boundary

This is an unrefereed candidate, not a proof of universal `R(3)`, the
unrestricted Strong Factorial Conjecture, or the general Polydegree
Conjecture. Internal cross-model review and exact replay are not specialist
peer review or independent reproduction.
