# Weighted-Euler socle route to Furter's `R(3)`

**Status:** exact reduction lemma plus a verified finite pilot; the two required
all-degree identity families remain open.

Write

\[
I_d=(g_{d,3},g_{d+1,3},g_{d+2,3})
\subset \mathbb Q[x_1,x_2,x_3],
\qquad \deg(x_1,x_2,x_3)=(1,2,3).
\]

## 1. Canonical weighted-Euler matrix

Define the $3\times3$ matrix

\[
(M_d)_{ij}=\frac{j}{d+i-1}\,\partial_{x_j}g_{d+i-1,3}
\qquad(1\le i,j\le3).
\]

Weighted Euler's identity gives

\[
M_d(x_1,x_2,x_3)^T=(g_{d,3},g_{d+1,3},g_{d+2,3})^T.
\]

Consequently

\[
\operatorname{adj}(M_d)(g_d,g_{d+1},g_{d+2})^T
=\det(M_d)(x_1,x_2,x_3)^T,
\]

so $x_i\det(M_d)\in I_d$ for every $i$.  The determinant is weighted
homogeneous of degree

\[
d+(d+1)+(d+2)-(1+2+3)=3d-3.
\]

It is the weighted Jacobian scaled by

\[
\det M_d=\frac{6}{d(d+1)(d+2)}
\det\left(\frac{\partial(g_d,g_{d+1},g_{d+2})}
{\partial(x_1,x_2,x_3)}\right).
\]

For an Artinian complete intersection, the Jacobian determinant represents
the top socle class.  Scheja--Storch is the classical structural source for
this fact.  The finite receipts used here do not take that theorem on trust:
they reduce $\det M_d$ independently in each exact quotient and check that its
class is nonzero.  Under the standard complete-intersection residue
normalisation, the Jacobian has residue equal to the colength.  Hence the
chosen Euler scaling makes the determinant canonical:

\[
\operatorname{res}(\det M_d)
=\frac{6}{d(d+1)(d+2)}\binom{d+2}{3}=1.
\]

This normalisation explains the finite pivot scalars below.  It is not used
to infer the two identities in the next section: doing that from the socle
theorem would already assume the Artinian conclusion one is trying to prove.

## 2. The two-identity reduction

Suppose that for one $d\ge2$ there are nonzero rational numbers
$\lambda_d,\nu_d$ such that

\[
x_1^{3d-3}-\lambda_d\det M_d\in I_d,
\qquad
x_3^{d-1}-\nu_d\det M_d\in I_d.
\tag{E1--E2}
\]

Multiplying by $x_1$ and $x_3$, respectively, and using the adjugate
memberships gives

\[
x_1^{3d-2}\in I_d,\qquad x_3^d\in I_d.
\]

Thus every common zero has $x_1=x_3=0$.  Among three consecutive indices
$d,d+1,d+2$, one index is even, say $2m$.  Direct Lagrange reversion gives

\[
g_{2m,3}(0,x_2,0)
=(-1)^m\frac{1}{2m+1}\binom{3m}{m}x_2^m,
\]

whose rational coefficient is nonzero.  Hence $x_2=0$, the common zero locus
is the origin, and the coefficient window indexed by $d$ proves
`R(3,d-1)`.  This is the fixed index convention used throughout the package.

Therefore an all-$d$ proof of the two displayed polynomial-identity families
would prove Furter's `R(3)`.  This implication does not assume in advance that
the quotient is Artinian; the identities themselves force the radical
conclusion.

## 3. Exact finite pilot

`rational-radical-certificates-d2-12-verification.json` independently verifies
the Euler identity, all three adjugate memberships, nonvanishing of the
determinant class, and the following canonical quotient scalars:

| $d$ | $\lambda_d$ for $x_1^{3d-3}$ | $\nu_d$ for $x_3^{d-1}$ |
|---:|---:|---:|
| 2 | $1/14$ | $5/14$ |
| 3 | $-12/1001$ | $-25/286$ |
| 4 | $195/89012$ | $3151/178024$ |
| 5 | $-9868289/25234415052$ | $-349601/109239892$ |
| 6 | $548771964577/8234982165840628$ | $22080835885179/41174910829203140$ |
| 7 | $-97789141886434696/9036408223057507257867$ | $-20334137314103881853/239199041198581074472950$ |
| 8 | $2730189480904524292499712535057/1623132297973306239103750959748792380$ | $164410557175776930202391893094539/12735345722559787414506353684182832520$ |
| 9 | $-148391326877228880239519500852234095521491/589621764562239929200649050298326688052336998136$ | $-3239396550548549681503549534684730115097/1710238323941988424413067207037726789802578600$ |
| 10 | $6391916861067060108286640065936216051004907815609/175376898981539050137632620961811037100803735498632616944$ | $35377743742074702499496376570030080387695435269233/130971368371704127058687234715434985032605919113488085200$ |
| 11 | $-1903750407254465239024799925008859197010505572296569195752161112651/370872732986526704383682684418732777629591425180130373836566747076682865760$ | $-2140984701384618115806230839406977017161030054764021990320925599803/56923373006582571285780263723191560778046533622555848282873937205788447760$ |
| 12 | $1580146937828402516390094667771479150349152828352088987409894356135209740443289/2238395044768647843600090453749024866577194133583414868122757222091272113067320519388000$ | $24668961636705297854034561680118770057883778213462270053180043667580071265769/4807434769816926522467680249073195036199677175098612054195159288586433365375464664000$ |

The signs alternate as $(-1)^d$ on this finite range.  Eleven observations are
still too few to infer a recurrence without a bounded model class and held-out
terms.  `euler-socle-recurrence-screen.json` reserves the last three
transitions and finds no first-order rational ratio with
$\deg P+\deg Q\le5$, and no order-two recurrence with coefficient degree at
most one, even on the training data.  This is a calibrated
`STOP_LOW_COMPLEXITY`, not evidence against higher-order holonomicity.  Any
cofactor interpolation must use a fixed normal form: arbitrary Singular lifts
differ by syzygies and their denominators are not invariants.

## 4. Claim boundary

The implication lemma is exact: (E1--E2) for every $d$ would prove `R(3)`.
It is a sufficient route, not a proved equivalence.  Artinianity makes the top
socle one-dimensional, but does not by itself show that either displayed pure
monomial is nonzero in that socle.  The table verifies that stronger fact only
on the finite range $2\le d\le12$.

Neither the alternating sign pattern nor the existence of a useful recurrence
has been proved for all $d$, and the two all-degree identities (E1--E2) remain
the load-bearing open problem on this route.

## Source

G. Scheja and U. Storch, *Über Spurfunktionen bei vollständigen
Durchschnitten*, Journal für die reine und angewandte Mathematik 278/279
(1975), 174--190, <https://doi.org/10.1515/crll.1975.278-279.174>.
