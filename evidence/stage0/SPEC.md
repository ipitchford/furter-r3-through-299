# Furter R(3) Stage 0 evidence contract

**Status:** internal research infrastructure; the terminal modular map proves
the displayed bounded single-map assertions $\widetilde R(3,d-1)$ and hence
Furter's equivalent composition statements $R(3,d-1)$, but no proof of the
universal statement `R(3)` or the Strong Factorial Conjecture is claimed by
this specification.

For `d>=2`, put

\[
I_d=(g_{d,3},g_{d+1,3},g_{d+2,3})\subset\mathbb Z[x_1,x_2,x_3],
\qquad \deg(x_i)=i.
\]

The coefficient convention is

\[
g_{n,3}=\sum_{a_1+2a_2+3a_3=n}
(-1)^{a_1+a_2+a_3}
\frac{(n+a_1+a_2+a_3)!}
{(n+1)n!a_1!a_2!a_3!}
x_1^{a_1}x_2^{a_2}x_3^{a_3}.
\]

Equivalently, $g_{n,3}$ is the coefficient of $X^{n+1}$ in the compositional
inverse of $H(X)=X+x_1X^2+x_2X^3+x_3X^4$.  Consequently $I_d$ is the
$\widetilde R(3,d-1)$ window.  The range $2\le d\le300$ is exactly the
single-map index range $1\le d-1\le299$.

For a prime `p`, the modular colength test computes an exact Gröbner basis of
`I_d` over `F_p` and asks for the vector-space dimension of the quotient.
There are only two admissible mathematical outcomes:

- `GOOD`: the quotient is finite dimensional and has dimension
  `d(d+1)(d+2)/6`;
- `BAD`: the quotient is infinite dimensional, equivalently the three forms
  have a nontrivial common point over the algebraic closure of `F_p`.

Any other finite dimension is a fail-closed specification error.  A `GOOD`
prime proves that the characteristic-zero weighted-projective intersection is
empty: otherwise its projective closure over `Spec Z` would have nonempty
special fibre at every prime by properness.  A `BAD` prime is not a
counterexample to `R(3)`; it only says that this prime cannot certify the
characteristic-zero instance.

For the bounded extension $50\le d\le300$, the proof-bearing producer uses an
equivalent stratified projective certificate instead of materializing the
entire quotient.  It checks that the ideals obtained on

\[
x_1=1,\qquad x_1=0,\ x_2=1,\qquad
x_1=x_2=0,\ x_3=1
\]

are all unit ideals over one shared $\mathbf F_p$.  The generators have exact
integer coefficients, and each receipt nests all three strata under the same
prime-labelled attempt; the validators reject an incomplete cover or a
different degree/prime attempt.  These three strata cover every nonzero
weighted-projective point over the algebraic closure.  This remains true in
characteristics 2 and 3: the required power maps are surjective on an
algebraically closed field.  Thus three unit ideals—not merely absence of
$\mathbf F_p$-rational points—
are exactly a `GOOD` empty-special-fibre certificate; a proper ideal on any
stratum is exactly `BAD`.  A timeout is neither and is skipped.  The selected
GOOD certificate for every degree is independently replayed under ordinary
and optimized Python.  Unlike the complete $d\le49$ map, the selected prime is
not called minimal if an earlier attempt timed out.

The implication uses two standard lemmas, recorded here to make the certificate
boundary explicit.  First, the weighted polynomial ring over a field is
Cohen--Macaulay.  Three weighted-homogeneous forms of degrees $d,d+1,d+2$
with no common weighted-projective zero generate a height-three ideal, hence a
regular sequence, and their quotient has weighted Bezout length
$d(d+1)(d+2)/(1\cdot2\cdot3)$.  Conversely, that finite length forces height
three and therefore excludes a projective common zero.  Second, the common-zero
subscheme in weighted projective space is proper over `Spec Z`.  If its generic
fibre were nonempty, the closed image of each irreducible component dominating
the generic point would contain every point of `Spec Z`; every special fibre
would then be nonempty.  Thus one `GOOD` special fibre proves the generic fibre
empty.  No semicontinuity heuristic is used.

There is also a direct graded-module proof of the same bridge.  Put
$A=\mathbb Z[x_1,x_2,x_3]/I_d$ and let $A_k$ be its weight-$k$ part.  Every
$A_k$ is a finitely generated $\mathbb Z$-module.  If the fibre at $p$ is
`GOOD`, its regular-sequence Hilbert series vanishes above $3d-3$, so

\[
 (A_k)_{(p)}/p(A_k)_{(p)}=0\qquad(k>3d-3).
\]

Nakayama's lemma gives $(A_k)_{(p)}=0$, and hence
$A_k\otimes\mathbb Q=0$, in every such degree.  The generic fibre is therefore
Artinian and its three generators again form a regular sequence with the same
Hilbert series.  Degree by degree, $(A_k)_{(p)}$ has equal generic rank and
special-fibre dimension; the structure theorem over the DVR
$\mathbb Z_{(p)}$ then shows it is free.  Consequently, a homogeneous class
certified nonzero in the GOOD fibre is also nonzero over $\mathbb Q$.  This
last statement permits independently checked modular one-lower
nonmembership to certify characteristic-zero sharpness.

## Normative controls

1. Coefficients are formed as exact integers before reduction modulo `p`.
2. A second implementation based on formal series reversion must agree on a
   fixed small grid.
3. The root must check the signed Catalan/Fuss--Catalan specializations of
   every $g_{n,3}$ used by the finite theorem, namely $0\le n\le302$.
4. Replacing the third generator by zero must change a known-good test to an
   infinite-dimensional quotient.
5. An impossible finite colength is rejected explicitly, including under
   `python -O`.
6. Producer source and Singular executable hashes are captured before the run,
   rechecked before atomic publication, and bound into the receipt.
7. Timeouts or parse failures may appear only in a `PARTIAL` diagnostic
   receipt; they cannot support a mathematical claim.

## Stage 0 datasets and gates

- `known map`: all requested primes for `2<=d<=49`;
- `screen`: for every `50<=d<=300`, search increasing primes until the first
  `GOOD` certificate is found;
- `resultant gate`: normalize and compute only a pilot sequence, reserve at
  least five terminal values for withheld testing, and extend only if a
  low-complexity recurrence predicts all withheld values;
- `identity gate`: extract exact pure-power cofactors for the largest feasible
  prefix beginning at `d=2`, independently expand every identity, and test the
  two canonical weighted-Euler socle families only after enough exact terms
  exist for withheld validation.

Floating roots, raw CAS claims, and bad-prime patterns are discovery evidence
only.  A counterexample requires exact nonzero algebraic coordinates and exact
evaluation of all three defining polynomials.

`verify_counterexample_candidate.py` is the executable acceptance gate.  It
requires a degree already present in `falsification-queue.json`, an irreducible
monic minimal polynomial over $\mathbb Q$, nonzero projective coordinates in
the resulting number field, and exact zero residuals for all three generators.
It contains no floating-point or numerical-tolerance acceptance path.

`modular-radical-certificates-d2-8{,-opt,-verification}.json` is a bounded
proof-object pilot for the structural route.  Its independently checked
identities place a positive power of each coordinate in the modular ideal for
every $2\le d\le8$.  The fixed targets are $x_1^{3d-2}$,
$x_2^{\lfloor(3d-3)/2\rfloor+1}$, and $x_3^d$, obtained from the weighted
complete-intersection socle bound $3d-3$.  These identities certify only those displayed finite
fibres; no automaticity or all-degree transition is part of the contract.

`rational-radical-certificates-d2-12{,-opt,-verification{,-opt}}.json` is the
corresponding characteristic-zero proof-object lane.  It contains all three
pure-power identities for $2\le d\le12$.  Its verifier reconstructs the
generators by direct compositional reversion, expands every identity over
$\mathbb Q$, proves all three one-lower nonmemberships by exact weighted
Macaulay linear algebra, recomputes the complete Hilbert function, and checks
the canonical weighted-Euler determinant and its adjugate identities.  These
are eleven finite instances and do not constitute an all-degree theorem.
