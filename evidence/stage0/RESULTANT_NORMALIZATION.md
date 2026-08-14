# Weighted resultant normalization used in Stage 0

This note fixes the normalization implemented by `cover_resultant.py`.  It is
an internal finite-computation method, not an all-degree nonvanishing proof.

Let $f_0,f_1,f_2$ be weighted-homogeneous forms in variables of weights
$(1,2,3)$, with weighted degrees $d,d+1,d+2$.  Pull them back by

\[
\pi:\mathbf P^2\longrightarrow\mathbf P(1,2,3),\qquad
[y_1:y_2:y_3]\longmapsto[y_1:y_2^2:y_3^3].
\]

The pullbacks have ordinary degrees $d,d+1,d+2$.  Their ordinary
Macaulay resultant is computed from the exact Koszul strand in degree

\[
d+(d+1)+(d+2)-2=3d+1.
\]

The determinant-of-Koszul-complex construction is standard sparse-resultant
machinery; a modern reference is C. D'Andrea and G. Jeronimo, *Sparse
Nullstellensatz, Resultants and Determinants of Complexes*,
<https://arxiv.org/abs/2407.13450>.  The axis calculation below is specific to
the $(1,2,3)$ cover used here.

The generic degree of the cover is $6$, but the coordinate axes have
stabilizers.  If $d$ is odd, exactly one form is nonzero on the $x_2$-axis;
write its pure-axis coefficient as $a_2$.  In every three-degree window,
exactly one form is nonzero on the $x_3$-axis; write its coefficient as
$a_3$.  Under the standard primitive sparse/weighted-resultant convention,
$R_d$ is normalized by

\[
|R_d|^6=
|\operatorname{Res}(f_0\circ\pi,f_1\circ\pi,f_2\circ\pi)|
\,|a_2|^{3\,[d\text{ odd}]}|a_3|^4.
\]

Here is the universal divisor calculation behind that identity.  Work first
over the universal coefficient ring.  On the dense torus, the finite cover is
degree six, so the pullback common-zero divisor has order six along the
irreducible weighted-resultant divisor.  Any discrepancy is supported on a
coordinate stratum.  On the $x_2$-axis an odd-$d$ three-degree window has only
one nonzero restriction, so its coefficient $a_2$ cuts out a divisor; the
local cover has multiplicity three, leaving the missing exponent $6-3=3$.
For even $d$, two forms have nonzero $x_2$ restrictions, so simultaneous
vanishing is codimension two and contributes no divisor.  On the $x_3$-axis
exactly one degree is divisible by three; the local cover multiplicity is two,
leaving exponent $6-2=4$.  There are no other codimension-one coordinate
strata.  Unique factorization in the universal coefficient ring therefore
gives the displayed equality up to a rational unit; primitive integral
normalization and absolute value fix that unit.  This is the ramification
factorization used by the producer, not an inference from the finite prime
tests below.

The implementation accepts a case only when the corrected integer is an exact
sixth power.  The verification chain then uses a coefficient construction
different from the producer's closed multinomial formula: it recovers the
inverse series sparsely from

\[
G=w-x_1G^2-x_2G^3-x_3G^4.
\]

For $2\le d\le17$, `verify_resultant_prefix.py` independently rebuilds both
Koszul maps, recomputes the two integer determinants, reconstructs the axis
factor, and checks the exact sixth root.  For $18\le d\le25$, the producer and
`verify_resultant_crt.py` independently rebuild the maps and recompute every
modular determinant residue.  A Hadamard bound on the selected numerator minor
and the nonzero integral denominator bound $|\det D|\ge1$ give an explicit
upper bound for $R_d^2$; certified pairwise-coprime 61-bit primes are accumulated
until their product exceeds twice that bound.  Symmetric CRT reconstruction is
then unique, and the verifier requires the reconstructed integer to be an exact
positive square.  Thus every stored value through $d=25$ has a second
determinant construction; the split is computational, not mathematical.

For every computed $2\le d\le25$, the strongest calibration is external to
the determinant construction: for every tested prime $p\le997$,

\[
p\mid R_d
\quad\Longleftrightarrow\quad
\mathbf F_p[x_1,x_2,x_3]/(g_{d,3},g_{d+1,3},g_{d+2,3})
\text{ is infinite-dimensional}.
\]

The normalized prime support is also checked against the independently verified
modular geometry.  This is a cross-method calibration in addition to the two
determinant reconstructions.  It does not prove that $R_d\ne0$ for all $d$, nor
a recurrence for $R_d$.

Under the primitive integral normalization fixed above, this resultant is the
intrinsic bad-prime object: reduction modulo $p$ vanishes exactly when the
three reduced forms acquire a common nonzero weighted-projective point, or
equivalently when the complete-intersection Hilbert function jumps.  Raw
cofactor denominators do not have this invariance.  The finite computation can
therefore inform a valuation or closed-form attack, but the present package
does not infer an all-$d$ formula from the values through $d=25$.
