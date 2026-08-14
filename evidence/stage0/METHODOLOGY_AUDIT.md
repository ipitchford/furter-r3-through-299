# Stage 0 methodology audit and response

**Date:** 13 August 2026  
**State:** terminal pre-freeze; package verification remains external to this record

## Scope and assurance class

A separate methodology-focused review inspected the mathematical implication,
CAS boundary, producer/verifier split, provenance bindings, controls, recurrence
gates, and package plan.  This was an internal cross-agent review within the
authoring workflow.  It is not independent specialist peer review or an
external reconstruction.

## Initial disposition

The reviewer accepted the exact modular map for $2\le d\le49$ and the logical
implication from one `GOOD` special fibre to the corresponding
characteristic-zero rigidity window.  The exact cofactor identities for
$2\le d\le8$ were accepted subject to regeneration of the canonical verifier
receipt.  The $50\le d\le300$ screen and the $2\le d\le25$ resultant pilot
were held because their terminal artifacts did not yet exist.

The review also rejected the phrase "independently verified weighted
resultants": the arithmetic verifier did not independently reconstruct the
Koszul matrices or determinants.  It requested a universal ramification
factorization for the normalization, portable executable binding, an
independent check of the generator formula through $g_{10,3}$, an explicit
homogeneity precondition for the cofactor recurrence, and calibration of the
lower-power diagnostic.

## Repairs completed before the final run

- `SPEC.md` now records the Cohen--Macaulay/regular-sequence weighted Bezout
  argument and the properness argument used by every `GOOD` certificate.
- The graded-module/Nakayama proof now makes explicit that one exact GOOD
  special fibre proves the corresponding characteristic-zero instance.  Equal
  complete-intersection Hilbert functions also justify lifting independently
  verified modular nonmembership to characteristic zero.
- The projective proof now states the two operational preconditions explicitly:
  the generators are integral at the selected prime and all three atlas strata
  belong to one prime-labelled attempt.  Properness proves generic emptiness
  without flatness; the Koszul Hilbert comparison is reserved for lifting
  nonzero graded classes.
- The proposed one-prime modular falsification of the Euler identities was
  rejected.  Modular nonvanishing at a GOOD prime gives a one-way positive
  certificate, but modular vanishing can reflect positive $p$-adic valuation
  and is inconclusive over $\mathbb Q$.
- A later cross-model note sharpened four freeze conditions now made explicit:
  patch certificates are unit-ideal certificates over the algebraic closure,
  all three strata use one shared prime, the generators are integral, and the
  three weighted-projective strata remain a set-theoretic cover in
  characteristics 2 and 3.  It also triggered a root-bound signed
  Catalan/Fuss--Catalan regression for all $g_0,\ldots,g_{302}$.
- A subsequent Sol review correctly narrowed the conjectural consequences.
  Universal `R(3)` is equivalent, given known `R(1)` and `R(2)`, to the Strong
  Factorial assertion only for
  $X_1X_2X_3(\mu_1X_1+\mu_2X_2+\mu_3X_3)$, and gives the length-two
  $(4,n+1)$ and $(n+1,4)$ Polydegree row and column.  It does not prove either
  overarching conjecture.
- That review also correctly centred Furter's existing third-order recurrence,
  but its proposed second-recurrence/desingularisation programme was already
  superseded by a separate July exact record.  There, an Ore-module theorem,
  an explicit exceptional branch solution, and differentiated-row identities
  show that every universal pole-branch recurrence retains Furter's
  exceptional factor.  This closes that recurrence module, not the global
  initial-state compatibility problem for the distinguished inverse-series
  sequence.  The July artifacts are not inputs to the present Stage 0 root,
  so they narrow the next research target without enlarging this package's
  certified finite theorem.
- The Sol review's proof-object recommendation is accepted as an assurance
  boundary rather than silently claimed as completed.  The $d=2,\ldots,8$
  modular pilot stores sparse cofactors and verifies them by independent
  arithmetic; the $d=50,\ldots,300$ theorem lane stores chart outcomes and is
  independently replayed through a second Singular wrapper, but it does not
  yet export portable sparse Nullstellensatz identities for all 251 degrees.
- A local Fable record audit then corrected three summary-level ambiguities
  without changing the theorem: the $d\le49$ lane uses exact weighted-Bezout
  colength while the $d\ge50$ lane uses three same-prime chart unit ideals;
  periodic infinitude of BAD windows is proved only for $p\ge7$ (single BAD
  instances suffice at $p=2,3,5$); and the second structural route is the
  exact two-identity Euler--socle reduction, with a resultant comparison only
  a proposed strategy for proving its scalar nonvanishing.
- The same note's single-prime experiment is superseded by the proved
  zero-band obstruction: every fixed prime has BAD windows.  Fibrewise
  Christol/Bridy automaticity remains useful, but no theorem currently makes
  the intrinsic-resultant sequence automatic.  Only a finite-cover product
  automaton could settle the GOOD-prime route.
- The source dictionary now distinguishes Furter's single-map
  $\widetilde R(3,n)$ from his equivalent two-map $R(3,n)$ and fixes the
  certified index range at $1\le n\le299$.  The canonical Euler socle class is
  not identified with the global resultant without an additional proof.
- `EULER_SOCLE_ROUTE.md` isolates the canonical residue-one Euler determinant
  and the two noncircular all-degree identity families that would imply
  universal `R(3)`; exact finite pivots are verified only through $d=12$.
- Singular verification binds current executable bytes rather than requiring
  the historical executable path.
- The cofactor verifier reconstructs $g_{0,3},\ldots,g_{10,3}$ by formal
  compositional reversion, expands every displayed identity by independent
  sparse rational convolution, and retains a coefficient-mutation control.
- Lower-power nonmembership flags are explicitly producer diagnostics and are
  excluded from the independently certified cofactor conclusion.
- The cofactor recurrence function itself rejects any non-homogeneous lift
  before fitting its bounded matrix ansatz.
- The modular-parity checker now invokes the full fail-closed colength receipt
  verifier rather than trusting stored row classifications.
- Verifier-generated receipts use basename-plus-SHA identities, allowing
  byte-identical replay after extraction, and replay regenerates every
  subordinate derived receipt before recomputing the root.
- `RESULTANT_NORMALIZATION.md` now supplies the universal cover-divisor and
  axis-ramification calculation.  A separate formal-reversion implementation
  rebuilds the Koszul maps and exact determinants for $d=2,\ldots,17$ and the
  modular determinants, bounds, and CRT reconstruction for $d=18,\ldots,25$.
- The structural pivot now has an explicit evidence boundary.  A verified-map
  analyzer derives the finite smallest-GOOD-prime frontier, and a separate
  producer-side probe records compact pure-power initial-ideal signatures with
  ordinary/optimized parity.  Multivariate Christol theory supports finite
  coefficient states but is not presented as proving that height three is
  automatic.
- A bounded proof-object pilot now uses Singular only to discover modular
  cofactors placing powers of all three coordinates in the ideal for
  $d=2,\ldots,8$.  A separate sparse-arithmetic implementation reconstructs
  the generators, expands all identities, and rejects a mutated coefficient;
  no digit-transition theorem is inferred from this finite pilot.
- The package builder requires exact equality between every Python source
  hashed by the root and every Python source included in the curated payload.
- The falsification lane has a separate exact-acceptance gate for reconstructed
  number-field points.  Numerical approximations cannot enter its acceptance
  path; projective nonzeroness, irreducibility, and all three residuals are
  checked exactly, with ordinary/optimized negative-control parity.

## Focused modular-certificate re-review

The new finite-field proof-object lane received a separate adversarial
re-review after integration.  It passed with no blocker or major soundness
issue.  The reviewer independently confirmed the weighted complete-intersection
socle degree $3d-3$, the equivalence between `GOOD` and the three fixed
pure-power identities, all seven independently expanded cases, ordinary/`-O`
parity, mutation rejection, and the root/replay/package bindings.  The minor
recommendations were actioned: the Cohen--Macaulay regular-sequence bridge and
the discovery/core trust boundary are explicit, output paths cannot overwrite
sources or existing receipts, and runtime wording does not claim unrecorded
SymPy byte pinning.

## Focused periodic-zero-band re-review

The exact modular zero-band lemma and its root/package integration received a
separate read-only re-review after repair.  It passed with no blocker, major,
or minor finding.  The reviewer independently checked the Kummer carry proof,
including its general-$e$ form, the precise GOOD-special-fibre claim boundary,
and the $p=37$ forced-subinterval wording.  The current executable regression
recomputes 114 zero-polynomial cases through $g_{51,3}$ and checks 169 forced
BAD windows in the complete $d=2,\ldots,49$ map.  It requires the exact prime
inventory through 997, and the package verifier compares the entire semantic
summary rather than accepting counts alone.  This is finite regression
evidence for an analytic all-prime proof, not an independent coefficient
derivation or an all-degree GOOD certificate.

## Final adversarial re-review and replay disposition

The focused final source-level re-review found no residual blocker, major, or
minor issue after three last fail-closed repairs: selected patch-prime attempts
must be the exact initial prime prefix, the deterministic root omits the
machine-specific absolute Singular path while retaining its byte hash, and the
combined-frontier verifier requires the strengthened prime-prefix negative
control.  Fresh ordinary and optimized patch receipts and root receipts were
then regenerated and agreed byte-for-byte.

The complete current-tree replay regenerated the mathematical evidence from
the stored inputs and terminated with `R3_STAGE0_REPLAY_PASS`.  It independently
replayed all 251 projective-patch degrees, reconstructed the normalized
resultants through $d=25$, ran the finite falsification and recurrence gates,
and reproduced byte-identical ordinary/optimized roots.  The first archive
verification attempt then exposed a launcher-only defect before any extracted
mathematics ran: resolving the supplied virtual-environment Python symlink
selected the base interpreter, where `flint` was unavailable.  The verifier
now preserves the caller's virtual-environment launcher path for execution
while continuing to hash the resolved executable bytes.  A negative control
confirms that the resolved base interpreter lacks `flint`, while the preserved
launcher imports the bound package.  The root and archive must therefore be
regenerated before the remaining external assurance step: verify the repaired
archive by a fresh extracted replay.
