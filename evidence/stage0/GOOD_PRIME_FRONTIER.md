# Good-prime frontier for Furter `R(3)`

**Status:** internal structural research note, 14 August 2026  
**Claim boundary:** the observations below are exact on the stated finite
range.  The proposed all-degree mechanism is a research target, not a theorem.

## 1. Exact observation motivating the pivot

The terminal receipts cover every degree $2\le d\le300$.  For $d\le49$, let
$q(d)$ be the smallest tested prime in the complete map through $p=997$ for
which

\[
\dim_{\mathbf F_{q(d)}}
\mathbf F_{q(d)}[x_1,x_2,x_3]/
(g_{d,3},g_{d+1,3},g_{d+2,3})
=\frac{d(d+1)(d+2)}6.
\]

For $50\le d\le300$, let $q(d)$ instead denote the first completed GOOD prime
after exact BAD attempts and skipped timeouts.  These later values are selected
certifying primes, not necessarily the smallest GOOD primes.  Across the
combined range, the selected-prime histogram is:

| prime | number of degrees |
|---:|---:|
| 3 | 1 |
| 5 | 16 |
| 7 | 9 |
| 11 | 28 |
| 13 | 23 |
| 17 | 21 |
| 19 | 13 |
| 23 | 20 |
| 29 | 24 |
| 31 | 35 |
| 37 | 16 |
| 41 | 23 |
| 43 | 13 |
| 47 | 18 |
| 53 | 7 |
| 59 | 2 |
| 61 | 2 |
| 67 | 7 |
| 71 | 5 |
| 73 | 4 |
| 83 | 4 |
| 89 | 5 |
| 97 | 2 |
| 127 | 1 |

The largest selected prime is $127$, attained only at $d=280$.  The patch
screen records 2,539 exact BAD attempts and 64 timeouts before the 251 selected
GOOD fibres.  Thus $127$ is a selected-prime maximum, not a minimum-prime
bound for the underlying mathematics.

The low-prime behavior is already nontrivial: $p=2$ is BAD throughout the
range, and $p=3$ is GOOD only at $d=2$.  Thus no single-small-prime argument is
available.  Conversely, the GOOD sets for larger primes appear in structured
blocks.  Examples from the observed rows include

\[
\begin{aligned}
p=13:&\quad 168,170,171,181,182,183,194,195,196,197,\\
p=29:&\quad 146,147,148,173,174,175,177,178,179,180,\\
p=31:&\quad 156,157,158,159,160,161,162,185,\ldots,193.
\end{aligned}
\]

The producer screen and both independent ordinary/optimized replays are
terminal.  The root receipt remains the final package-level binding.

## 2. General theorem that would settle the first radical half

A sufficient structural statement is:

> There is a finite set of primes $P$ such that, for every $d\ge2$, at least
> one $p\in P$ makes $(g_{d,3},g_{d+1,3},g_{d+2,3})$ a height-three ideal over
> $\mathbf F_p$.

The properness argument in `SPEC.md` would then prove every
`R(3,d-1)`, hence `R(3)`.  The finite data suggests testing
the 24 selected primes observed through $d=300$, whose largest member is
$127$, but does not justify that particular set or any universal bound on
$p(d)$.  A weaker residue-dependent construction of a good prime $p(d)$ would
be equally sufficient.

## 3. Candidate proof architecture

The inverse coefficients are governed integrally by

\[
G=w-x_1G^2-x_2G^3-x_3G^4.
\]

For a fixed prime $p$, the multinomial coefficients in $g_{n,3}$ and the
Frobenius identity for $G^p$ suggest recursions controlled by the base-$p$
digits of $n$.  The concrete programme is:

1. derive Cartier/Frobenius transition formulas for the three-polynomial
   window $(g_n,g_{n+1},g_{n+2})$ over $\mathbf F_p$;
2. attach to each reachable digit state a fail-closed height-three
   certificate, preferably three leading monomials or a bounded Gröbner
   signature;
3. form the product transition system for several primes and prove that no
   reachable state is BAD for every prime simultaneously; and
4. export the finite transition table and its exact checker as a certificate,
   rather than trusting a pattern inferred from the degree table.

This is deliberately different from the failed rational-ratio search for
$R_d$.  A $p$-automatic or digit-recursive law may be simple even when no
low-order recurrence over $\mathbb Q(d)$ exists.

### 3.1 What finite-state theory already gives

This part of the architecture is supported by an existing theorem, not only
by the observed blocks.  Over $\mathbf F_p$, the complete inverse series is
the unique solution at the origin of

\[
 P(w,x_1,x_2,x_3,Y)
 =Y-w+x_1Y^2+x_2Y^3+x_3Y^4=0,
 \qquad \frac{\partial P}{\partial Y}(0)=1.
\]

It is therefore an algebraic power series in the four variables
$(w,x_1,x_2,x_3)$.  The multivariate Christol theorem, equivalently the
finite-dimensional section-operator theorem, implies that the coefficient
array

\[
 (n,a_1,a_2,a_3)\longmapsto
 [w^{n+1}x_1^{a_1}x_2^{a_2}x_3^{a_3}]G
 \quad\text{in }\mathbf F_p
\]

has a finite $p$-kernel.  In particular, an exact finite transition system for
the coefficients exists and can in principle be constructed from $P$.

This does **not** by itself make the predicate

\[
 \operatorname{ht}(g_{d,3},g_{d+1,3},g_{d+2,3})=3
\]

automatic.  The required new lemma is a finite-state lift from coefficient
sections to an ideal certificate: for example, a bounded family of leading
monomial or Gröbner signatures that is preserved by every relevant base-$p$
digit transition.  The dense grid is intended to discover that certificate
vocabulary.  Treating coefficient automaticity alone as a proof of $R(3)$
would be a specification error.

There is a complementary univariate statement.  After fixing
$(x_1,x_2,x_3)$ in a finite field $\mathbf F_q$, the series $G(w)$ remains
algebraic of degree at most four, so Christol's theorem makes the specialized
coefficient sequence $q$-automatic; Bridy's curve bound gives a finite state
bound in terms of its degree, height and genus.  This fibrewise theorem does
not make the growing intrinsic-resultant sequence $(R_d\bmod p)_d$
automatic, and it does not control points over extensions of unbounded degree
in $\overline{\mathbf F}_p$.

Accordingly, a $p$-kernel experiment on $R_d\bmod p$ is exploratory rather
than proof-bearing.  The exact resultant prefix through $d=25$ is too short
to support a strong automaticity claim.  Moreover, the zero-band theorem
below rules out a universally GOOD single prime.  Any successful automaton
certificate must coordinate several primes and prove that their product state
never makes every prime BAD at once.

There is also an exact periodic obstruction to making this GOOD-special-fibre
certificate architecture use one fixed modulus.  Put
$K_p=\lfloor(p+2)/4\rfloor$.  For every prime $p\ge7$ and every $n\ge0$,

\[
 n\equiv-k\pmod p,\quad 2\le k\le K_p
 \quad\Longrightarrow\quad
 g_{n,3}=0
\]

in $\mathbf F_p[x_1,x_2,x_3]$.  To see this, write $b_i$ for the base-$p$
units digit of $a_i$.  The weighted-degree condition gives

\[
 b_1+2b_2+3b_3\equiv-k\pmod p.
\]

If $b_1+b_2+b_3<k$, then the left side is at most $3(k-1)<p-k$, contradicting
the congruence.  Thus adding $a_1,a_2,a_3$ to the base-$p$ units digit $p-k$
of $n$ produces a carry.  Kummer's theorem makes the multinomial coefficient

\[
 \frac{(n+s)!}{n!a_1!a_2!a_3!},\qquad s=a_1+a_2+a_3,
\]

divisible by $p$.  Since $p\nmid n+1$, the same is true of the coefficient of
the monomial in $g_{n,3}$.  Any three-polynomial window intersecting this
periodic zero band has at most two nonzero generators and is therefore
`BAD`.  Consequently

\[
 p-K_p-2\le d\bmod p\le p-2
 \quad\Longrightarrow\quad (d,p)\text{ is `BAD`}.
\]

The same argument has a general-$e$ form.  For the inverse coefficients
$g_{n,e}$ attached to weights $1,\ldots,e$, define

\[
 K_{p,e}=\left\lfloor\frac{p+e-1}{e+1}\right\rfloor.
\]

Then

\[
 n\equiv-k\pmod p,\quad 2\le k\le K_{p,e}
 \quad\Longrightarrow\quad g_{n,e}=0\pmod p.
\]

Indeed, if the sum of the $e$ units digits is less than $k$, their weighted
sum is at most $e(k-1)<p-k$, contradicting its congruence to $-k$ modulo
$p$.  The same base-$p$ carry and the fact that $p\nmid n+1$ finish the
proof.  The statement above is the specialization
$K_{p,3}=\lfloor(p+2)/4\rfloor$.  This generalization is recorded as an
internal structural lemma; no novelty claim is made for it here.

For example, $p=37$ forces the periodic BAD residue interval
$26\le d\bmod37\le35$.  Its first occurrence is a subinterval of the larger
verified BAD run $18\le d\le35$ at $p=37$.  The map also supplies BAD instances
$(p,d)=(2,2),(3,3),(5,6)$ for the remaining primes.  Thus no single prime can
supply a GOOD special-fibre witness for every degree; this GOOD-fibre
certificate route therefore requires varying primes, possibly drawn from a
finite cover.

Primary sources for this finite-state layer are:

- B. Adamczewski, A. Bostan and X. Caruso, *A sharper multivariate
  Christol's theorem with applications to diagonals and Hadamard products*,
  especially the section-operator characterization:
  <https://adamczewski.perso.math.cnrs.fr/Effective_Christol.pdf>;
- E. Rowland and R. Yassawi, *Automatic congruences for diagonals of rational
  functions*, for constructive Cartier/diagonal automata:
  <https://arxiv.org/abs/1310.8635>.

### 3.2 A certificate object that avoids trusting a full Gröbner basis

For one degree $d$ and prime $p$, it is enough to exhibit positive integers
$N_1,N_2,N_3$ and nine polynomials $A_{ij}$ in
$\mathbf F_p[x_1,x_2,x_3]$ satisfying

\[
 x_i^{N_i}=A_{i0}g_{d,3}+A_{i1}g_{d+1,3}+A_{i2}g_{d+2,3}
 \qquad(i=1,2,3).
\]

These three identities imply
$\sqrt{(g_{d,3},g_{d+1,3},g_{d+2,3})}=(x_1,x_2,x_3)$ directly.  They can be
verified by independent sparse arithmetic and require neither a trusted
Gröbner-basis implementation nor a quotient-dimension parser.  Singular may
still discover the cofactors, just as it does in the existing rational
$x_3^d$ pilot, but it does not remain in the identity-arithmetic core.  The
current command-line wrapper nevertheless requires the verified map and the
bound Singular executable so that prime selection and discovery provenance
remain auditable.

The target exponents need not be guessed.  For a `GOOD` fibre the weighted
complete intersection has Hilbert series

\[
 \frac{(1-t^d)(1-t^{d+1})(1-t^{d+2})}
 {(1-t)(1-t^2)(1-t^3)}
\]

and top weighted degree $3d-3$.  Hence the fixed choices

\[
 N_1=3d-2,\qquad
 N_2=\left\lfloor\frac{3d-3}{2}\right\rfloor+1,\qquad
 N_3=d
\]

always work.  Conversely, identities for these three targets force the
quotient to be finite dimensional.  In the forward direction, finiteness gives
height three; three homogeneous generators in the Cohen--Macaulay weighted
polynomial ring therefore form a regular sequence, which is the step that
justifies the displayed complete-intersection Hilbert series.  Thus this fixed
certificate format is equivalent to `GOOD`, while remaining directly
checkable.

### 3.3 The `GOOD`-special-fibre lemma

Let

\[
A=\mathbb Z[x_1,x_2,x_3]/(g_{d,3},g_{d+1,3},g_{d+2,3})
\]

with its positive weight grading.  The exact coefficient formula gives
$g_{n,3}\in\mathbb Z[x_1,x_2,x_3]$, so reduction is $p$-integral at every
prime.  A projective-patch attempt has one recorded prime $p$, and all three
strata are computed from that same reduction.  The producer, assembler, and
independent verifier enforce this shared-prime cover.  Unit-ideal certificates
from patches taken at different primes would not constitute a `GOOD` fibre.

Let $X\subset\mathbf P_{\mathbb Z_{(p)}}(1,2,3)$ be the closed common-zero
subscheme.  If the complete three-stratum certificate says $X_p=\varnothing$,
properness makes the image of $X$ closed in
$\operatorname{Spec}\mathbb Z_{(p)}$.  A nonempty generic fibre would put the
generic point in that image and hence the closed point as well, a
contradiction.  Therefore
$X_{\mathbb Q}=\varnothing$ and $A\otimes\mathbb Q$ is Artinian.  This
per-instance implication requires neither flatness nor a Hilbert-function
comparison.

The Hilbert comparison supplies the separate sharpness implication.  Both
the special and generic fibres are cut out by three homogeneous forms of
degrees $d,d+1,d+2$ in a three-variable Cohen--Macaulay weighted polynomial
ring.  Empty projective fibre gives height three, hence a regular sequence, in
both characteristics.  The Koszul resolution therefore fixes the same Hilbert
series

\[
\frac{(1-t^d)(1-t^{d+1})(1-t^{d+2})}
{(1-t)(1-t^2)(1-t^3)}
\]

degree by degree, with top degree $3d-3$.  Each localized graded piece
$(A_k)_{(p)}$ is a finite module over the DVR $\mathbb Z_{(p)}$; equality of
its special-fibre dimension and generic rank excludes $p$-power torsion and
makes it free.  Thus a homogeneous class nonzero modulo $p$ remains nonzero
over $\mathbb Q$.

This lifting is asymmetric.  An arbitrary ideal membership seen only modulo
$p$ does not lift to characteristic zero.  In the top socle degree, however,
a modular nonvanishing result at one `GOOD` prime does lift; the generic socle
is one-dimensional, so the lifted class is a nonzero rational multiple of the
Euler determinant.  The converse test is not valid: vanishing modulo one
`GOOD` prime can merely mean that the integral class is divisible by $p$, and
does not prove characteristic-zero vanishing.  Any modular sweep of the two
Euler monomials must therefore record successes as one-way certificates and
failures as inconclusive diagnostics, not as falsifications.

This lemma makes the exact modular map a complete proof of its bounded
characteristic-zero windows.  Rational certificates remain valuable because
they expose canonical socle representatives and possible all-degree
structure, not because the modular implication is incomplete.

This suggests a sharper finite-state theorem to seek: for each reachable
base-$p$ digit state, store bounded certificate data or a transition rule that
constructs the three identities for the successor state.  A finite set of
primes settles `R(3)` if the product automaton proves that every integer state
has such a certificate for at least one prime.

The observed pure leading exponents are useful for choosing candidate targets,
but they are not themselves membership identities.  A pure monomial in an
initial ideal certifies zero-dimensionality only together with a verified
Gröbner-basis argument.  The cofactor form above deliberately removes that
extra trust dependency, possibly at the cost of using slightly larger powers
$N_i$.

## 4. Falsification and next exact experiment

With the projective-patch screen terminal, a separate rectangular map for every
$2\le d\le300$ and every prime $p\le53$ remains a post-Stage-0 experiment.
Unlike the completed early-stopping screen, it would record the full GOOD/BAD
word for each small prime.  Then:

- test stability under shifts by $p$, $p^2$, and digit-prefix substitution;
- minimize the empirical state machines without treating minimization as a
  proof;
- derive transitions symbolically from the coefficient recursion; and
- reject a finite-prime-cover conjecture immediately if any degree is BAD for
  every prime in the proposed set.

Individual BAD reductions remain resultant-divisibility data, not
characteristic-zero counterexamples.  Any universal claim requires the exact
transition proof, not extrapolation from the finite screen.

The executable path is now explicit.  `analyze_good_prime_frontier.py`
derives a hash-bound finite frontier only from independently verified map
receipts.  `run_good_prime_grid_shards.py` and
`assemble_good_prime_grid_shards.py` produce the resumable full rectangle;
`verify_good_prime_grid.py` checks both mathematical parity and every shard,
range, assembler, and launcher binding.
Their $d=2,3,4$, $p\le7$ ordinary/optimized pilot passes, but the $d\le300$,
$p\le53$ rectangle is deliberately queued behind the current Stage 0 critical
path and is not part of the finite evidence stated in Section 1.

An additional producer-side probe, `probe_groebner_signatures.py`, computes
the reduced `dp` standard basis at the smallest certified GOOD prime for each
$2\le d\le49$.  In 39 of the 48 cases, the smallest pure powers in the initial
ideal are exactly $(x_1^d,x_2^d,x_3^d)$.  The deviation degrees are

\[
3,4,13,18,24,25,26,28,35.
\]

Except at $d=3$, every pure-power exponent in those deviations is one of
$d-1,d,d+1$; at $d=3$ the triple is $(4,3,1)$.  The complete bases range from
4 to 1138 elements, so the three pure-power elimination witnesses are a much
more plausible finite-state certificate than the full basis.  This probe has
ordinary/optimized byte parity but is producer-side exploratory evidence, not
an independent reconstruction or an all-degree statement.

After subtracting $(d,d,d)$, all 48 triples lie in the five-state alphabet

\[
(0,0,0),\quad(0,-1,0),\quad(0,0,-1),\quad(1,0,-2),\quad(1,1,0),
\]

with multiplicities $39,5,2,1,1$, respectively.  This is the first concrete
candidate state compression for the ideal-certificate layer; it must now be
tested beyond $d=49$ and derived from section transitions before it has any
all-degree force.
