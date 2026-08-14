# Substantive release review

**Date:** 14 August 2026  
**Reviewer class:** producer-side adversarial review  
**Scope:** mathematical claim fidelity, source dictionary, certificate bridge,
zero-band proof, challenge boundary, replay metadata, and public wording  
**Independence boundary:** not external specialist peer review or an
independent reconstruction

## Disposition

**PASS WITH ONE REPAIR, NOW COMPLETED.** No unresolved P0 or P1 issue remains.

## Load-bearing checks

- The root receipt states `d=2..300`, count 299, and maps this to Furter's
  `R(3,d-1)`. The manuscript consistently states `n=1..299`.
- Furter's Lemma 2 supports the one-map/two-map equivalence; Theorem B and the
  symmetry lemma support the `(4,k)` and `(k,4)` closure corollary.
- The LPS prior computation is described as the stronger `d<50` benchmark;
  the new contribution is not allowed to absorb that range as novel.
- The GOOD-special-fibre bridge is exact: the generators are integral, all
  three weighted-projective strata use one prime, unit ideals exclude
  geometric points over the algebraic closure, and properness transfers
  emptiness to the generic fibre.
- The large finite lane is correctly described as a second-wrapper Singular
  replay, not as portable sparse Nullstellensatz certificates or formal
  verification.
- The zero-band proof correctly uses a units-digit carry and Kummer's theorem;
  division by `n+1` is valid because `k>=2`.
- The Euler--socle and resultant material is labelled finite structural
  evidence with explicit ansatz boundaries.
- The public verifier binds the exact archive hash, 299-window root
  inventory, challenge boundary, and PDF; ordinary and `python -O` outputs
  agree.

## Finding and repair

### P1 — small-prime infinitude was asserted without the packaged proof

An introductory sentence initially said that every fixed prime has infinitely
many identically zero inverse coefficients. The analytic theorem in the
package proves that statement only for `p>=7`; for `p=2,3,5`, the root binds
one BAD witness each, which is sufficient to exclude a universal fixed GOOD
prime but not to prove infinitude.

The manuscript now says:

- infinitely many periodic BAD windows for every `p>=7`; and
- one exact BAD witness for each of `p=2,3,5`, sufficient for the architectural
  no-fixed-prime conclusion.

The abstract, theorem, corollary, claim boundary, challenge, and accessible
Markdown agree with this repaired statement.

## Deterministic regression

- LaTeX build: PASS, eight pages, no undefined citations/references or
  overfull boxes.
- `python3 verify_release.py`: PASS.
- `python3 -O verify_release.py`: byte-identical PASS.
- `python3 challenge/verify_challenge.py`: PASS.
- Frozen archive SHA-256:
  `4538ce575a9dc2cbb6b6b4fcd097e1858a4c9a0578e1e101ead5f2f34c7110a9`.
- Root receipt SHA-256:
  `889fcafed2a980b1d1ec5cbbf526f238321ddf27daef2a641dffcbb39cc26518`.
- External fresh-extraction receipt: PASS, 125 manifest entries, replay true.

## Remaining limitations

Universal `R(3)` remains open. The release has no Lean formalisation, external
specialist report, or outside rebuild. Those are assurance and future-work
limitations, not hidden conditions on the finite theorem.

