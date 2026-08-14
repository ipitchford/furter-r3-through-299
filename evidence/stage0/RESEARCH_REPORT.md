# Furter R(3) Stage 0 research report

**Status:** terminal pre-freeze, 14 August 2026.  Terminal receipts prove the
finite instances $R(3,d-1)$ for every $2\le d\le300$, exact rational
three-axis certificates through $d=12$, and the $x_3^d$ cofactor identities
through $d=8$.  The independently reconstructed resultant pilot and
ordinary/optimized root are terminal PASS, and the complete current-tree
replay ended with `R3_STAGE0_REPLAY_PASS`.  Frozen-package construction and
fresh extracted verification remain.  This is not a proof or refutation of universal
Furter `R(3)`, the Strong Factorial Conjecture, or a new all-degree Polydegree
theorem.

## 1. Exact target and implication boundary

With

\[
I_d=(g_{d,3},g_{d+1,3},g_{d+2,3})
\subset\mathbb Z[x_1,x_2,x_3],\qquad \deg x_i=i,
\]

the computed one-map rigidity window is Furter's
$\widetilde R(3,d-1)$ assertion

\[
\sqrt{I_d\mathbb Q[x_1,x_2,x_3]}=(x_1,x_2,x_3).
\]

Here $g_{k,3}$ is the coefficient of $X^{k+1}$ in the compositional inverse.
Thus $2\le d\le300$ means the one-map indices $1\le n=d-1\le299$.  Furter's
Lemma 2 proves $\widetilde R(3,n)$ equivalent to his two-map composition
conjecture $R(3,n)$, which is the unadorned notation used elsewhere in this
report.

All windows would prove `R(3)`.  Since `R(1)` and `R(2)` are known, Edo and
van den Essen's Theorem 2.25 identifies `R(3)` with the Strong Factorial
statement only for the special three-variable family

\[
X_1X_2X_3(\mu_1X_1+\mu_2X_2+\mu_3X_3).
\]

It does not identify `R(3)` with the unrestricted Strong Factorial
Conjecture.  Furter's Theorem B sends each `R(3,n)` to the corresponding
length-two Polydegree closure description for multidegree $(4,n+1)$ and,
by symmetry, $(n+1,4)$; even all of `R(3)` would not prove the general
Polydegree Conjecture.  None of these all-index conclusions follows from a
finite table.

The determinant-augmented LPS condition is separate.  This Stage 0 programme
studies only the first radical-membership half.  Existing LPS work proves the
stronger `PIC(d,3)` for $2\le d<50$; the current terminal map rechecks its
radical half there and extends the first radical half alone through $d=300$.

Primary-source anchors for that dictionary are:

- J.-P. Furter, *Polynomial Composition Rigidity and Plane Polynomial
  Automorphisms*, Section 1.2, Lemma 2 and Theorem B:
  <https://doi.org/10.1112/jlms/jdu064>;
- E. Edo and A. van den Essen, *The Strong Factorial Conjecture*,
  Proposition 2.23 and Theorem 2.25:
  <https://arxiv.org/abs/1304.3956>;
- D. Lewis, K. Perry and A. Straub, *An Algorithmic Approach to the
  Polydegree Conjecture for Plane Polynomial Automorphisms*, definitions of
  $g_{d,e}$, `PIC(d,e)`, Theorems 3--4 and Lemma 12:
  <https://arxiv.org/abs/1809.09681>.

The package makes no priority claim for the new finite range; it records exact
replayable computations and their mathematical consequence.

## 2. Finite exact conclusions

### Modular colength

For each tested prime, an exact Singular Gröbner basis computes the quotient
dimension.  A finite quotient must have the weighted Bézout length

\[
\frac{d(d+1)(d+2)}6.
\]

One prime with that length proves the characteristic-zero projective common
zero locus empty by properness.  A positive-dimensional reduction is only a
bad certifying prime, not a characteristic-zero counterexample.

The current terminal receipts contain:

- the complete map for every $2\le d\le49$ and every prime $p\le997$;
- ordinary and optimized Python producer parity;
- independent coefficient reconstruction by formal series reversion; and
- baseline, zero-third-generator, and impossible-finite-colength controls.

For every $50\le d\le300$, the complementary producer certifies the same
empty special fibre on the complete three-stratum weighted-projective cover.
All 251 selected GOOD fibres were independently rebuilt by a second
specialize-first implementation under ordinary and optimized Python, producing
byte-identical verification receipts.  The assembled screen contains 2,854
prime attempts: 2,539 exact BAD fibres, 251 selected GOOD fibres, and 64
timeouts carrying no conclusion.  Every attempt reduces the exact integral
generators once at its recorded prime and checks all three strata at that same
prime; certificates assembled from different primes would not prove one empty
projective fibre.

Consequently, the current evidence proves all 299 finite instances
$R(3,d-1)$ for $2\le d\le300$, equivalently

\[
\sqrt{I_d\mathbb Q[x_1,x_2,x_3]}=(x_1,x_2,x_3)
\qquad(2\le d\le300).
\]

This implication can be read degree by degree, without treating modular
evidence as a merely probabilistic proxy.  Properness of the closed common-zero
subscheme over $\operatorname{Spec}\mathbb Z_{(p)}$ sends an empty special
fibre directly to an empty generic fibre; no flatness hypothesis is needed.
If $A=\mathbb Z[x_1,x_2,x_3]/I_d$, the special and generic fibres are then
height-three complete intersections of the same weighted degrees.  Their
Koszul resolutions give the same Hilbert function, degree by degree.  The
localized graded pieces are therefore free over $\mathbb Z_{(p)}$, so a class
certified nonzero in the `GOOD` fibre remains nonzero over $\mathbb Q$.
The modular lane is consequently theorem-valid for the stated finite windows;
the rational lane below exposes additional structure.

The 64 timed-out attempts prevent a smallest-GOOD-prime claim in the extended
range, but do not weaken the selected exact GOOD certificates.  The bounded
extension does not prove the universal all-$d$ statement `R(3)`.

### Exact cofactors

Singular lifting produced explicit rational polynomials $A_d,B_d,C_d$ with

\[
A_dg_{d,3}+B_dg_{d+1,3}+C_dg_{d+2,3}=x_3^d
\qquad(2\le d\le8).
\]

An independent formal-reversion and sparse rational convolution verifier
expands every identity and rejects a mutated cofactor coefficient.  Singular's
stored lower-power nonmembership flags are producer diagnostics only; they are
not part of the independently certified conclusion.

The structural route also has a finite-field proof-object pilot.  At the
smallest certified `GOOD` prime for each $2\le d\le8$, Singular discovered
cofactors for exact identities

\[
x_i^{N_i}=A_{i0}g_{d,3}+A_{i1}g_{d+1,3}+A_{i2}g_{d+2,3}
\qquad(i=1,2,3).
\]

The targets are theorem-driven rather than fitted: the complete-intersection
socle bound $3d-3$ gives
$N_1=3d-2$, $N_2=\lfloor(3d-3)/2\rfloor+1$, and $N_3=d$.

Ordinary and optimized producer receipts are byte-identical.  A separate
sparse implementation reconstructs the generators over $\mathbf F_p$, expands
all 21 identities, and rejects a cofactor mutation.  This validates the
proposed certificate format on seven finite degrees; it does not supply the
missing base-$p$ digit-transition theorem.

A second lane now certifies the same three pure-power memberships exactly over
$\mathbb Q$ for every $2\le d\le12$.  Its verifier reconstructs the generators
by compositional reversion, expands all 33 identities by independent sparse
rational arithmetic, and checks all 33 one-lower nonmemberships by exact
weighted Macaulay row reduction.  It also recovers the complete-intersection
Hilbert lengths

\[
4,10,20,35,56,84,120,165,220,286,364
\]

and the expected socle degree $3d-3$ in every case.

For the weighted Euler matrix

\[
(M_d)_{ij}=\frac{j}{d+i-1}\,\partial_{x_j}g_{d+i-1,3},
\]

the receipt verifies $M_dx=(g_d,g_{d+1},g_{d+2})^T$, the adjugate
memberships $x_i\det M_d\in I_d$, and that $\det M_d$ is a nonzero top-socle
class.  The canonical quotient scalars for $x_1^{3d-3}$ and $x_3^{d-1}$
reproduce the independently supplied values through $d=5$ and extend them
through $d=12$.  This is a structural finite pilot, not an interpolation claim.
It also shows why raw Singular-lift cofactor denominators are not invariant:
from $d=4$ onward they can contain primes at which the fibre is `GOOD`.
Recurrence searches must therefore use canonical quotient classes or
canonical normal-form cofactors, never arbitrary raw lifts.

## 3. Resultant pilot and recurrence tests

The terminal composite contains every normalized value for $2\le d\le25$,
split between full integer determinants through $d=17$ and modular
determinant/CRT certificates thereafter.  Ordinary/optimized prefix and shard
receipts have timing-free parity.  A separate sparse formal-reversion
coefficient construction independently rebuilds the Koszul maps, recomputes
the full integer determinants for $2\le d\le17$, and recomputes every modular
determinant, Hadamard bound, and CRT reconstruction for $18\le d\le25$.

The recurrence screen reserves transitions
$20\to21,\ldots,24\to25$ as untouched holdouts.  On training transitions
$2\to3,\ldots,19\to20$, it tests every
first-order rational-ratio ansatz

\[
R_{d+1}Q(d)=R_dP(d),\qquad \deg P+\deg Q\le12.
\]

Every tested ansatz has full column rank modulo at least one of the two test
primes, so no nonzero rational relation in the displayed class survives even
the training data.  The five terminal transitions remain unused.  The gate is
therefore terminal `STOP`: this excludes only that bounded first-order class,
not a higher-order holonomic recurrence.  Independently, all 4,032 comparisons
against the verified $p\le997$ modular map satisfy
$p\mid R_d$ exactly when the reduced fibre is `BAD`.

The inverse series itself is algebraic and hence its coefficient sequence is
D-finite over characteristic zero.  That theorem does not transfer
automatically to the derived scalar sequences tested here—especially the
resultant of a window whose determinantal size grows with $d$.  The negative
gate therefore does not close a general holonomic or creative-telescoping
route; it excludes only the displayed ansatz.  With only 24 exact resultant
values, substantially higher-order fitting would be underdetermined rather
than informative.

For the cofactor vector $H_d=(A_d,B_d,C_d)^T$, a separate exact screen tests
the smallest homogeneity-compatible transport

\[
H_{d+1}=M(x_1,x_2,x_3)H_d
\]

with a $d$-independent $3\times3$ polynomial matrix.  Each output component
is inconsistent already on the $d=2\to3,\ldots,6\to7$ training transitions;
the $7\to8$ holdout remains unused.  Numerator and denominator sizes also
grow sharply.  The raw-lift uniform-identity route therefore fails its
`ADVANCE` gate.

That negative gate does not apply to the canonical weighted-Euler route now
recorded in `EULER_SOCLE_ROUTE.md`.  Two exact quotient identities—one for
$x_1^{3d-3}$ and one for $x_3^{d-1}$—would combine with the adjugate identity
and the nonzero pure-$x_2$ Fuss--Catalan coefficient to prove `R(3)` at that
degree.  The finite pilot verifies this architecture through $d=12$; the
all-degree identity families remain open.

A future modular socle sweep has a strictly one-way interpretation.  At a
`GOOD` prime, nonvanishing of either top-degree monomial lifts through the free
graded lattice and proves that it is a nonzero rational multiple of the Euler
determinant.  Vanishing at one prime is inconclusive: the integral class may be
nonzero but divisible by that prime.  Such a sweep may extend positive finite
structure evidence, but it cannot be used as the proposed one-prime
falsification gate for the rational identity family.

An exact recurrence screen uses $d=2,\ldots,9$ only for fitting and reserves
the last three transitions.  For both canonical scalar sequences it finds no
training relation of the form

\[
a_{d+1}Q(d)=a_dP(d),\qquad \deg P+\deg Q\le5,
\]

and no order-two relation with polynomial coefficients of degree at most one.
The gate is therefore `STOP_LOW_COMPLEXITY`.  This excludes only those bounded
classes.  By itself the screen does not exclude higher-order creative
telescoping, but the all-order theorem below shows that a successful route
must use the distinguished global initial state or otherwise leave the
universal pole-branch recurrence module.

### Furter's recurrence and the exceptional mode

The principal all-degree recurrence is not a fitted recurrence from the
finite data.  Furter's Section 1.5, Lemma 8 gives, for $n\ge4$,

\[
A_nu_n+B_nu_{n-1}+C_nu_{n-2}+D_nu_{n-3}=0,
\qquad
A_n=n(n-1)(n-2)(M_1n-3M_2)\Delta.
\]

The possible vanishing of $M_1n-3M_2$ is exactly why the recurrence does not
automatically propagate a block of three zeroes.  It is therefore the central
structural obstruction, not merely one more low-complexity ansatz to fit.

A separate exact July 2026 internal recurrence record, not included in this
Stage 0 root, already pursued the most direct desingularisation proposals.  It
records and replays the following symbolic results:

- Furter's forward and reverse pivots vanish at the same exceptional factor;
- a separately derived five-term creative-telescoping recurrence is, after
  localization, a first-order left multiple of Furter's Ore operator;
- the universal annihilator of the three individual pole-branch residue
  sequences is the principal left ideal generated by Furter's operator;
- on the generic exceptional locus there is a nonzero branch combination
  with three consecutive zeroes, so every polynomial endpoint pivot built
  from universal branch recurrences retains the exceptional factor; and
- differentiating either Furter's row or the combined recurrence system
  preserves the same factor.

This is a `STOP` result for desingularisation *within the universal
pole-branch recurrence module*.  It is not a disproof of `R(3)`: the
distinguished sequence $u_n$ is fixed by global initial residue data, whereas
the exceptional local mode is a generic linear combination of branch
solutions.  The genuinely new recurrence input would be a global
compatibility theorem showing that the distinguished initial state cannot
enter that exceptional mode, or a relation annihilating only the
distinguished sum and not each branch separately.

## 4. Falsification lane

The exact modular and projective-patch receipts certify every one of the 299
tested degrees $2\le d\le300$.  The terminal falsification queue therefore has
no unresolved degree and numerical homotopy was not triggered.  This is a
bounded conclusion, not evidence that a counterexample cannot occur later.

If a future screen finds a degree with no good prime, numerical methods may
discover a candidate, but acceptance requires nonzero algebraic coordinates
and exact evaluation of all three $g$-polynomials.  The package contains an
executable number-field acceptance gate with all-zero, reducible-field, and
non-solution negative controls; it refuses an empty or non-escalating queue.

## 5. Stop/go decision and next mathematical target

| Route | Gate | Decision |
|---|---|---|
| low-complexity resultant recurrence | must survive training and five holdouts | `STOP` |
| raw Singular-lift cofactor recurrence | stable exact parameter law | `STOP` |
| universal pole-branch recurrence desingularisation | endpoint pivot not divisible by Furter's exceptional factor | `STOP WITH BOUNDARY`: July exact module theorem |
| finite counterexample escalation | unresolved exact degree | `NO ESCALATION`: queue empty through $d=300$ |
| good-prime/global exclusion | finite evidence plus structural mechanism | provisional `PIVOT` |

The next high-value work is not a longer unstructured table.  It is one of:

1. a global initial-state compatibility or exceptional-locus theorem that
   rules out Furter's surviving local mode for the distinguished sequence;
2. an all-degree proof of the two canonical Euler--socle identities `E1` and
   `E2` in `EULER_SOCLE_ROUTE.md`, including nonvanishing of their scalars; an
   exact comparison with the intrinsic normalized resultant is one possible
   strategy for that nonvanishing step, not an established identification; or
3. either a residue-dependent construction of a GOOD prime $p(d)$ or a
   finite-prime product automaton whose transition-stable certificates prove
   that every degree has a GOOD prime.

`GOOD_PRIME_FRONTIER.md` records the third route more precisely: the current
finite data suggests base-$p$ digit blocks and motivates a Cartier/Frobenius
transition certificate whose product over finitely many primes has no
simultaneously BAD reachable state.  This is a research programme, not an
inference from the finite table.

Effective multivariate Christol theory confirms that the complete coefficient
array of the algebraic inverse series has a finite $p$-kernel for every prime
$p$.  This validates the coefficient-transition layer of the proposed route.
It does not establish that height three, a Gröbner signature, or simultaneous
BADness is itself automatic; constructing a transition-stable ideal
certificate is the precise remaining mathematical step.

One limitation of this route is now proved uniformly rather than inferred
from the screen.  For every prime $p\ge7$, put
$K_p=\lfloor(p+2)/4\rfloor$.  Kummer's carry criterion gives the exact
periodic zero band

\[
 g_{n,3}=0\pmod p
 \quad\text{if}\quad
 n\equiv-k\pmod p,\quad 2\le k\le K_p,
\]

because the weighted congruence forces a carry when the base-$p$ units digits
of the indexing composition are added to the units digit $p-k$ of $n$.
Since $p\nmid n+1$, dividing the multinomial coefficient by $n+1$ preserves
the factor $p$.  It follows that every window with
$p-K_p-2\le d\bmod p\le p-2$ is BAD.  At $p=37$ this predicts the periodic
forced interval $26\le d\bmod37\le35$; its first occurrence is a subinterval
of the larger verified BAD run $18\le d\le35$.  Together with verified BAD
instances $(p,d)=(2,2),(3,3),(5,6)$, the lemma proves that no fixed prime
supplies a GOOD special-fibre witness for every degree.  This GOOD-fibre
certificate route must therefore vary the prime, possibly within a finite
cover.  The full proof is recorded in `GOOD_PRIME_FRONTIER.md`.

For clarity, the periodic argument proves infinitely many BAD windows for
each $p\ge7$.  At $p=2,3,5$, the current all-degree record uses only the one
displayed BAD instance for each prime; it does not claim an infinite small-
prime BAD family.

The carry proof extends verbatim to all truncation lengths $e$: with
$K_{p,e}=\lfloor(p+e-1)/(e+1)\rfloor$, one has
$g_{n,e}=0\pmod p$ whenever $n\equiv-k\pmod p$ and
$2\le k\le K_{p,e}$.  This is a general structural constraint on the
GOOD-special-fibre approach to eventual columns.  It is recorded as an
internal lemma without a novelty claim; it is not a proof of any Polydegree
column or of the Strong Factorial Conjecture.

The preferred certificate object is now explicit: over a selected
$\mathbf F_p$, exhibit exact cofactor identities placing one positive power of
each of $x_1,x_2,x_3$ in $I_d$.  Sparse arithmetic can verify those identities
without trusting a full Gröbner basis.  A viable all-degree proof would make
these certificates transition under base-$p$ digits and then show that the
product automaton over finitely many primes has no simultaneously uncertified
integer state.

The finite-frontier analyzer and resumable full-grid producer/assembler are
implemented and have passed a small ordinary/optimized end-to-end pilot.  The
full $d\le300$, $p\le53$ rectangle is queued after the core Stage 0 jobs so it
does not compete with the required degree-$300$ and resultant evidence.

The determinant-augmented LPS condition stays separate and deprioritized.  A
proof of the first radical half for all $d$ would settle `R(3)` directly;
it would not need the auxiliary LPS determinant condition.

## 6. Assurance boundary

The working tree provides terminal exact algebra for the ranges identified
above, independent coefficient and sparse-identity checks, ordinary/optimized
parity, source and executable hashes, and negative controls.  A complete
current-tree replay has re-established the finite claim range; archive-level
reproducibility still requires frozen-package verification and a fresh
extracted replay.  For $50\le d\le300$, the evidence records exact
prime-labelled chart outcomes and a second specialize-first Singular replay;
it does not export sparse Nullstellensatz cofactors for a lightweight
arithmetic-only checker.  That stronger proof-object architecture is present
only in the $d=2,\ldots,8$ modular pilot.  Thus the large-range assurance is
exact CAS recomputation, not CAS-free certificate checking.  None of this is
a proof of a universal conjecture, independent expert reconstruction, formal
proof-assistant verification, or peer review.
