# Exact Finite Rigidity for Furter's R(3): All Windows Through n=299

**Anonymous — 14 August 2026 — Version 0.1.0-candidate**

## Abstract

Let $`g_{k,3}\in\mathbb Z[x_1,x_2,x_3]`$ be the coefficient of
$`X^{k+1}`$ in the compositional inverse of
$`X(1+x_1X+x_2X^2+x_3X^3)`$. We prove, by exact computer-assisted
certificates, that

``` math
\sqrt{(g_{d,3},g_{d+1,3},g_{d+2,3})\mathbb Q[x_1,x_2,x_3]}
=(x_1,x_2,x_3) \qquad (2\le d\le300).
```

Equivalently, Furter's $`R(3,n)`$ holds for every $`1\le n\le299`$. The
release also proves a periodic Kummer-theoretic obstruction to a universal
one-fixed-prime GOOD-fibre certificate and publishes a machine-readable
Universal $`R(3)`$ Challenge. Universal $`R(3)`$ remains open.

**Status.** This is an unrefereed computer-assisted theorem candidate.
The exact finite claim is stronger than a probabilistic calculation, but
the release has not received specialist peer review or an independent
external reconstruction.

# Introduction

Furter’s rigidity conjectures ask whether an unexpectedly long initial
cancellation in a polynomial composition forces both polynomials to be
the identity. They are important because Furter connected them to
closure relations between strata of plane polynomial automorphisms . Edo
and van den Essen found a further bridge to a restricted family in the
Strong Factorial Conjecture . The universal statement $`R(3)`$ is still
open.

Lewis, Perry and Straub (LPS) recast related closure questions as
explicit ideal computations in inverse-series coefficients and verified
their stronger condition in the three-variable column for $`d<50`$ . The
present work takes the radical-maximality half of that architecture and
extends its exact finite rigidity consequence to $`d\le300`$.

Our principal result is deliberately finite.

<div id="thm:main" class="theorem">

**Theorem 1** (Exact finite $`R(3)`$). *Furter’s $`R(3,n)`$ holds for
every integer $`n`$ with $`1\le n\le299`$.*

</div>

The proof does not infer a characteristic-zero theorem from the apparent
frequency of good modular reductions. For every degree it records an
exact empty special fibre over a single finite field. A properness
argument then gives the corresponding characteristic-zero conclusion. A
bad prime has no negative implication for characteristic zero; it merely
cannot certify that degree by this route.

The computation reveals a structural limitation. For every prime
$`p\ge7`$, infinitely many inverse coefficients vanish identically
modulo $`p`$, so infinitely many three-term windows are necessarily bad
at that prime. The exact map supplies a bad window for each of
$`p=2,3,5`$ as well. Thus no fixed prime certifies every degree, and any
universal proof based on good special fibres must coordinate multiple
primes.

# Inverse coefficients and the rigidity dictionary

Give $`x_i`$ weight $`i`$. Define $`g_{n,3}`$ by
``` math
\begin{equation}
\label{eq:g-explicit}
g_{n,3}=\sum_{a_1+2a_2+3a_3=n}
(-1)^{a_1+a_2+a_3}
\frac{(n+a_1+a_2+a_3)!}
{(n+1)n!a_1!a_2!a_3!}
x_1^{a_1}x_2^{a_2}x_3^{a_3}.
\end{equation}
```
These are integral weighted-homogeneous polynomials of weight $`n`$.
Equivalently, if $`G`$ is the unique formal solution with initial term
$`w`$ of
``` math
\begin{equation}
\label{eq:inverse-series}
G=w-x_1G^2-x_2G^3-x_3G^4,
\end{equation}
```
then $`g_{n,3}`$ is the coefficient of $`w^{n+1}`$ in $`G`$.

For $`d\ge2`$ put
``` math
I_d=(g_{d,3},g_{d+1,3},g_{d+2,3})\subset\mathbb{Z}[x_1,x_2,x_3].
```

<div id="lem:dictionary" class="lemma">

**Lemma 2** (Source dictionary). *The equality
``` math
\sqrt{I_d\mathbb{Q}[x_1,x_2,x_3]}=(x_1,x_2,x_3)
```
is Furter’s one-map assertion $`\widetilde R(3,d-1)`$ and is equivalent
to his two-map assertion $`R(3,d-1)`$.*

</div>

<div class="proof">

*Proof.* The coefficient convention follows from Lagrange inversion and
agrees with the LPS definition. Furter’s Lemma 2 identifies the
vanishing of the three consecutive inverse coefficients with
$`\widetilde R(3,d-1)`$ and proves the equivalence with $`R(3,d-1)`$ .
The only common affine zero being the origin is precisely the displayed
radical equality. ◻

</div>

The shift $`n=d-1`$ is essential: $`2\le d\le300`$ corresponds exactly
to $`1\le n\le299`$.

# From one good special fibre to characteristic zero

Let $`p`$ be prime and write $`I_{d,p}`$ for the reduction of $`I_d`$ in
$`\mathbb{F}_p[x_1,x_2,x_3]`$.

<div class="definition">

**Definition 3**. The pair $`(d,p)`$ is *GOOD* if $`I_{d,p}`$ has height
three, equivalently if the quotient is finite-dimensional. It is *BAD*
if the three forms have a nonzero common point over
$`\overline{\mathbb{F}}_p`$.

</div>

Because the forms have weighted degrees $`d,d+1,d+2`$, a GOOD quotient
is a weighted complete intersection. Its length is
``` math
\begin{equation}
\label{eq:length}
 \frac{d(d+1)(d+2)}{1\cdot2\cdot3}=\binom{d+2}{3}
\end{equation}
```
and its socle weight is
``` math
\begin{equation}
\label{eq:socle}
 d+(d+1)+(d+2)-(1+2+3)=3d-3.
\end{equation}
```

<div id="lem:properness" class="lemma">

**Lemma 4** (Good-special-fibre bridge). *If $`(d,p)`$ is GOOD, then
$`\sqrt{I_d\mathbb{Q}[x_1,x_2,x_3]}=(x_1,x_2,x_3)`$.*

</div>

<div class="proof">

*Proof.* Regard the common-zero scheme as a closed subscheme of the
weighted projective plane over $`\operatorname{Spec}\mathbb{Z}_{(p)}`$.
This morphism is proper. If its generic fibre were nonempty, the closure
of a generic point would have closed image containing the generic point
of $`\operatorname{Spec}\mathbb{Z}_{(p)}`$, hence the closed point as
well. The special fibre would then be nonempty, contrary to GOOD. Thus
the generic weighted-projective fibre is empty, so the only affine
common zero in characteristic zero is the origin. ◻

</div>

This argument uses one prime for the whole projective fibre.
Certificates from different primes on different affine charts cannot be
combined.

For completeness, the same bridge has a graded-module formulation. With
$`A=\mathbb{Z}[x_1,x_2,x_3]/I_d`$, every weighted piece $`A_k`$ is a
finite $`\mathbb{Z}`$-module. A GOOD special fibre is a complete
intersection with Hilbert series
``` math
\frac{(1-t^d)(1-t^{d+1})(1-t^{d+2})}
 {(1-t)(1-t^2)(1-t^3)}.
```
The special fibre vanishes above weight $`3d-3`$. Nakayama’s lemma then
kills the corresponding localized integral pieces and makes the generic
fibre Artinian. Equal complete-intersection Hilbert functions also show
that the localized graded pieces are free, a fact used by the structural
pilot to lift modular nonvanishing.

# The exact finite computation

Two proof-bearing lanes cover the degree interval.

## Complete modular map for $`2\le d\le49`$

For every one of the 48 degrees and every one of the 168 primes
$`p\le997`$, an exact Singular Gröbner-basis computation classified the
quotient as GOOD or BAD. The map contains 8,064 rows: 6,931 GOOD and
1,133 BAD. An independent formal-reversion implementation checks the
generator formula on a fixed grid. The verifier rejects an impossible
finite length and includes a mutation in which the third generator is
replaced by zero.

This lane reproduces the radical half of the published LPS range. Its
role in the present release is regression and continuity; the new finite
range begins at $`d=50`$.

## Weighted-projective cover for $`50\le d\le300`$

Materializing complete quotient bases becomes increasingly expensive.
The second lane instead certifies the absence of a nonzero projective
common zero on the three strata
``` math
\begin{equation}
\label{eq:charts}
 x_1=1,\qquad x_1=0,\ x_2=1,\qquad
 x_1=x_2=0,\ x_3=1.
\end{equation}
```
These strata cover the weighted projective plane over an algebraically
closed field, including in characteristics $`2`$ and $`3`$. For a fixed
attempt $`(d,p)`$, the producer reduces the integral generators at $`p`$
and proves that the ideal on each stratum is the unit ideal. All three
results are nested under the same prime-labelled attempt. A second
specialize-first implementation rebuilds every selected GOOD certificate
under ordinary and optimized Python.

The screen covers 251 degrees and records 2,854 attempts: 2,539 exact
BAD fibres, 251 selected GOOD fibres, and 64 timeouts. A timeout has no
mathematical meaning and is never used as evidence. The largest selected
prime is $`127`$, at $`d=280`$; because some earlier attempts timed out,
the selected prime is not always claimed to be the smallest possible
GOOD prime.

<div id="prop:finite" class="proposition">

**Proposition 5** (Certified finite range). *For every $`d`$ with
$`2\le d\le300`$, there exists a recorded prime $`p`$ for which
$`(d,p)`$ is GOOD.*

</div>

<div class="proof">

*Computer-assisted proof.* For $`d\le49`$, the exact modular-map receipt
contains at least one row labelled GOOD for every degree and the
verifier recomputes the expected length
<a href="#eq:length" data-reference-type="eqref"
data-reference="eq:length">[eq:length]</a>. For $`50\le d\le300`$, the
assembled projective-screen receipt contains exactly one selected
same-prime three-stratum unit-ideal certificate for every degree.
Independent ordinary and optimized verifier receipts agree
byte-for-byte. A root verifier binds the degree inventory, source and
runtime hashes, controls, and subordinate receipts. A package verifier
then extracts the frozen archive into a fresh directory, runs the
replay, checks the manifest, and reproduces a PASS root. All
computations are exact; no floating-point tolerance enters an acceptance
path. ◻

</div>

<div class="proof">

*Proof of Theorem <a href="#thm:main" data-reference-type="ref"
data-reference="thm:main">1</a>.* Apply
Proposition <a href="#prop:finite" data-reference-type="ref"
data-reference="prop:finite">5</a> and
Lemma <a href="#lem:properness" data-reference-type="ref"
data-reference="lem:properness">4</a> for every $`2\le d\le300`$, then
use Lemma <a href="#lem:dictionary" data-reference-type="ref"
data-reference="lem:dictionary">2</a> with $`n=d-1`$. ◻

</div>

<div id="cor:polydegree" class="corollary">

**Corollary 6** (Length-two Polydegree consequence). *For every
$`2\le k\le300`$, Furter’s closure equality of Theorem B holds for the
length-two multidegrees $`(4,k)`$ and $`(k,4)`$.*

</div>

<div class="proof">

*Proof.* Use $`R(3,k-1)`$ in Furter’s Theorem B and his symmetry lemma
. ◻

</div>

This corollary is not presented as the first proof of the full $`e=3`$
Polydegree column. A separate Evidence Press candidate has already
proved that column for all degrees by a
smooth-point/Fourier/interval-arithmetic route .

# A fixed-prime obstruction

The modular data suggests blocks, but the key negative fact is analytic.

<div id="thm:zeroband" class="theorem">

**Theorem 7** (Periodic zero band). *Let $`p\ge7`$ be prime and put
$`K_p=\lfloor(p+2)/4\rfloor`$. If
``` math
n\equiv-k\pmod p,\qquad 2\le k\le K_p,
```
then $`g_{n,3}`$ is the zero polynomial in
$`\mathbb{F}_p[x_1,x_2,x_3]`$.*

</div>

<div class="proof">

*Proof.* Consider a monomial indexed by $`(a_1,a_2,a_3)`$ in
<a href="#eq:g-explicit" data-reference-type="eqref"
data-reference="eq:g-explicit">[eq:g-explicit]</a>, write
$`s=a_1+a_2+a_3`$, and let $`b_i`$ be the units digit of $`a_i`$ in base
$`p`$. The weighted-degree condition gives
``` math
b_1+2b_2+3b_3\equiv-k\pmod p.
```
If $`b_1+b_2+b_3<k`$, then the left side is at most $`3(k-1)<p-k`$, a
contradiction. Thus $`b_1+b_2+b_3\ge k`$. Adding the base-$`p`$ units
digits of $`n,a_1,a_2,a_3`$ therefore produces a carry, because the
units digit of $`n`$ is $`p-k`$. By Kummer’s theorem the multinomial
coefficient
``` math
\frac{(n+s)!}{n!a_1!a_2!a_3!}
```
is divisible by $`p`$. Since $`n+1\equiv1-k\not\equiv0\pmod p`$,
division by $`n+1`$ preserves divisibility. Every coefficient of
$`g_{n,3}`$ vanishes. ◻

</div>

<div id="cor:nofixedprime" class="corollary">

**Corollary 8** (No universal fixed GOOD prime). *For every prime
$`p\ge7`$, infinitely many windows $`I_{d,p}`$ are BAD. No prime,
including $`2,3,5`$, supplies a GOOD witness for every degree through
the good-special-fibre architecture.*

</div>

<div class="proof">

*Proof.* For $`p\ge7`$, any three-term window intersecting the periodic
zero band has at most two nonzero generators and thus height at most
two. Explicitly,
``` math
p-K_p-2\le d\bmod p\le p-2
```
forces BAD, and each congruence class recurs infinitely often. For
$`p=2,3,5`$, the exact map supplies a BAD witness at $`d=2,3,6`$
respectively. Those three witnesses are sufficient for the stated
no-universal-fixed-prime conclusion; no infinitude assertion for the
small primes is needed here. ◻

</div>

The same carry proof works for weights $`1,\ldots,e`$. If
$`K_{p,e}=\lfloor(p+e-1)/(e+1)\rfloor`$, then $`g_{n,e}=0\pmod p`$
whenever $`n\equiv-k\pmod p`$ and $`2\le k\le K_{p,e}`$. We make no
priority claim for this elementary generalization.

# Structural evidence beyond the finite theorem

## The canonical Euler–socle route

Define the weighted Euler matrix
``` math
(M_d)_{ij}=\frac{j}{d+i-1}\partial_{x_j}g_{d+i-1,3}.
```
Weighted Euler identities give
``` math
M_d(x_1,x_2,x_3)^T=(g_{d,3},g_{d+1,3},g_{d+2,3})^T.
```
Consequently the adjugate identity places $`x_i\det(M_d)`$ in $`I_d`$
for each $`i`$, while $`\det(M_d)`$ has the socle weight $`3d-3`$. In an
Artinian complete intersection the Jacobian represents a nonzero socle
class .

This contracts one possible all-degree proof to two canonical
identities. It would suffice to prove, for every $`d\ge2`$, nonzero
scalars $`\lambda_d,\nu_d`$ such that
``` math
\begin{equation}
\label{eq:euler-targets}
 x_1^{3d-3}-\lambda_d\det(M_d)\in I_d,
 \qquad
 x_3^{d-1}-\nu_d\det(M_d)\in I_d.
\end{equation}
```
Indeed the adjugate identities would force $`x_1=x_3=0`$ on the
common-zero locus, and the nonzero pure-$`x_2`$ Fuss–Catalan coefficient
in the even member of each three-term window would then force $`x_2=0`$.

Exact rational certificates verify the three pure-power memberships, the
one-lower nonmemberships, the Hilbert functions, the Euler identities,
and <a href="#eq:euler-targets" data-reference-type="eqref"
data-reference="eq:euler-targets">[eq:euler-targets]</a> for
$`2\le d\le12`$. This is a finite structural pilot, not an interpolation
argument.

## The finite-prime automaton route

Equation <a href="#eq:inverse-series" data-reference-type="eqref"
data-reference="eq:inverse-series">[eq:inverse-series]</a> defines an
algebraic multivariate series over every finite field. Multivariate
Christol theory therefore gives a finite $`p`$-kernel for its
coefficient array . What is missing is not coefficient automaticity, but
a finite-state lift from coefficient sections to an ideal certificate,
such as a bounded family of leading-monomial or Gröbner signatures. In
view of Corollary <a href="#cor:nofixedprime" data-reference-type="ref"
data-reference="cor:nofixedprime">8</a>, a successful construction must
use a product automaton for several primes and show that no reachable
state is BAD in every component.

## Calibrated negative results

Normalized weighted resultants were independently reconstructed through
$`d=25`$: full integer determinants through $`d=17`$ and modular
determinants with rigorous CRT reconstruction for $`18\le d\le25`$.
Across 4,032 prime-degree comparisons, a prime divides the normalized
resultant exactly when the corresponding fibre is BAD. A withheld-data
screen excludes every first-order rational-ratio recurrence
$`R_{d+1}Q(d)=R_dP(d)`$ with $`\deg P+\deg Q\le12`$. Separate screens
reject a small $`d`$-independent raw-cofactor transport and
low-complexity recurrences for the Euler–socle scalars. These results
close only the specified ansatz classes; they do not rule out
higher-order creative telescoping or a finite automaton.

# Evidence object and assurance boundary

The release archive is an executable evidence object rather than a table
of claimed CAS outputs. Its root receipt binds:

- the 299-degree inventory and the two exact certificate lanes;

- producer, verifier, input, runtime, and receipt SHA-256 identities;

- ordinary/optimized Python parity where applicable;

- independent formal reversion and sparse arithmetic on bounded pilots;

- generator-axis Catalan and Fuss–Catalan regressions through
  $`g_{302,3}`$;

- fail-closed controls for impossible colengths, missing generators,
  altered cofactors, incomplete prime prefixes, and malformed
  inventories;

- an exact counterexample gate with no numerical-tolerance path; and

- a fresh-extraction replay and manifest verification.

The large $`d=50,\ldots,300`$ lane independently replays a second
Singular wrapper, but it does not yet export portable sparse
Nullstellensatz cofactors for all 251 degrees. Singular is therefore
inside that lane’s trusted computing boundary. Internal cross-model
adversarial review is not external specialist review, and executable
replay is not formal verification.

# Limitations and open problem

Theorem <a href="#thm:main" data-reference-type="ref"
data-reference="thm:main">1</a> is finite. It neither proves nor refutes
the next window, and it supplies no monotonicity principle in $`d`$.
Universal $`R(3)`$ would require an all-degree theorem, not a longer
table. The two best-defined targets are:

1.  prove both canonical identities
    <a href="#eq:euler-targets" data-reference-type="eqref"
    data-reference="eq:euler-targets">[eq:euler-targets]</a> for every
    $`d\ge2`$, including nonvanishing of their scalars; or

2.  construct a finite set of primes and a certified product automaton
    that gives a same-prime GOOD fibre in every degree despite each
    prime’s zero bands.

The companion Universal $`R(3)`$ Challenge records these obligations,
exact finite examples, falsifiers, and acceptance criteria in
machine-readable form.

# Data and code availability

All proof scripts, receipts, controls, manifests, the frozen replay
archive, and the machine-readable challenge are included with the public
release. The archive is identified by SHA-256 in its manifest and
external verification receipt. Public repository, release, and DOI links
are fixed in the versioned record: the source and replay package is at
<https://github.com/ipitchford/furter-r3-through-299>, and the permanent
release is <https://doi.org/10.5281/zenodo.21939362>.

# Ethics statement

This work uses no human participants, personal data, animals, clinical
data, or field interventions. No ethics approval was required.

# CRediT contribution statement

Anonymous: conceptualization, methodology, software, validation, formal
analysis, investigation, data curation, writing, visualization, and
project administration. The provenance record separately describes human
research direction and model-assisted implementation and review.

# Competing interests

The scholarly creator declares no competing interests. Evidence Press is
the publisher of this unrefereed candidate and of related
computer-assisted mathematics releases.

# Funding

No external funding is declared.

# AI assistance disclosure

AI systems contributed to literature triage, mathematical exploration,
software implementation, adversarial checking, exposition, and release
engineering under human direction. Exact computations were accepted only
through the recorded deterministic checks and replay gates. Model
agreement was not treated as mathematical evidence, independent
reproduction, or peer review.

<div class="thebibliography">

99

J.-P. Furter, *Polynomial composition rigidity and plane polynomial
automorphisms*, J. London Math. Soc. 91 (2015), 180–202.
<https://doi.org/10.1112/jlms/jdu064>

D. Lewis, K. Perry and A. Straub, *An algorithmic approach to the
Polydegree Conjecture for plane polynomial automorphisms*, J. Pure Appl.
Algebra 223 (2019), 5346–5359.
<https://doi.org/10.1016/j.jpaa.2019.04.002>

E. Edo and A. van den Essen, *The Strong Factorial Conjecture*, J.
Algebra 397 (2014), 443–456.
<https://doi.org/10.1016/j.jalgebra.2013.09.011>

G. Scheja and U. Storch, *Über Spurfunktionen bei vollständigen
Durchschnitten*, J. Reine Angew. Math. 278/279 (1975), 174–190.
<https://eudml.org/doc/151652>

B. Adamczewski, A. Bostan and X. Caruso, *A sharper multivariate
Christol’s theorem with applications to diagonals and Hadamard
products*. <https://arxiv.org/abs/2306.02640>

E. Rowland and R. Yassawi, *Automatic congruences for diagonals of
rational functions*, J. Théor. Nombres Bordeaux 27 (2015), 245–288.
<https://arxiv.org/abs/1310.8635>

Anonymous, *A Jacobian smooth-point criterion and the full $`(e=3)`$
column of the Polydegree Conjecture*, unrefereed candidate, Evidence
Press (2026). <https://doi.org/10.5281/zenodo.21909085>

</div>
