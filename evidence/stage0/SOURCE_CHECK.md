# Primary-source implication and index check

**Checked:** 13 August 2026  
**Role:** claim dictionary only; this is not novelty evidence.

## Furter rigidity

Furter's conjecture `R(m,n)` is the two-map composition statement for
polynomials of respective truncation lengths $m$ and $n$.  In the proof of
Lemma 2 he separately names the single-map inverse-coefficient assertion
$\widetilde R(m,n)$:

\[
 \widetilde a_{n+1}=\cdots=\widetilde a_{n+m}=0
 \quad\Longrightarrow\quad a(X)=X.
\]

That lemma proves $\widetilde R(m,n)$ equivalent to `R(m,n)`, and proves that
`R(m)` is equivalent to `R(m,n)` for every $n\ge0$.  Furter also proves the
symmetry between the two composition indices and uses partial rigidity to
obtain the corresponding length-two closure theorem for plane polynomial
automorphisms.  The tilde is retained below whenever the computed one-map
statement itself is meant; omitting it denotes Furter's equivalent two-map
statement.

Source: J.-P. Furter, *Polynomial Composition Rigidity and Plane Polynomial
Automorphisms*, especially Section 1.2, Lemma 2 and Theorem B,
<https://doi.org/10.1112/jlms/jdu064>.

## Strong Factorial bridge

Edo and van den Essen define the full and partial rigidity conjectures and
state explicitly that the full statement is the conjunction of all positive
partial windows.  Their Theorem 2.25 supplies the precise bridge through the
specified Strong Factorial family and lower-dimensional cases.  With

\[
E^{[3]}=\{X_1X_2X_3(\mu_1X_1+\mu_2X_2+\mu_3X_3):\mu_i\in\mathbb C\},
\]

Theorem 2.25(5) says that the Strong Factorial assertion for all members of
$E^{[3]}$ is equivalent to `R(1)`, `R(2)`, and `R(3)` together.  Since the
first two rigidity statements are known, universal `R(3)` is equivalent to
this *restricted family*, not to the unrestricted Strong Factorial
Conjecture.  The safe implication from the unrestricted conjecture is:

```text
unrestricted Strong Factorial Conjecture
  => required restricted family
  => R(3).
```

Thus a counterexample to `R(3)` would refute the unrestricted Strong Factorial
Conjecture.  A proof of `R(3)` would prove the displayed restricted family but
would not prove the unrestricted Strong Factorial Conjecture.  The finite
positive computations in this package prove neither universal statement.

Source: E. Edo and A. van den Essen, *The Strong Factorial Conjecture*,
Proposition 2.23 and Theorem 2.25, <https://arxiv.org/abs/1304.3956>.

## Length-two Polydegree consequence

Furter's Theorem B states that `R(m,n)` gives the corresponding length-two
closure description for multidegree $(m+1,n+1)$.  Therefore `R(3,n)` gives
the $(4,n+1)$ case, and Lemma 1 supplies the symmetric $(n+1,4)$ case.  All of
`R(3)` would settle this one infinite row and column of the length-two
problem; it would not settle the general Polydegree Conjecture.

Source: J.-P. Furter, *Polynomial Composition Rigidity and Plane Polynomial
Automorphisms*, Lemma 1 and Theorem B,
<https://doi.org/10.1112/jlms/jdu064>.

## LPS coefficient and predicate dictionary

For the coefficient convention used here, $g_{k,3}$ is the coefficient of
$X^{k+1}$ in the inverse series.  Therefore the block

\[
g_{d,3},g_{d+1,3},g_{d+2,3}
\]

is exactly the single-map window $\widetilde R(3,d-1)$ and hence, by Furter's
Lemma 2, proves the equivalent composition statement `R(3,d-1)`.  Thus the
certified range $2\le d\le300$ is $1\le n=d-1\le299$ in Furter's window
index.  The radical equality

\[
\sqrt{(g_{d,3},g_{d+1,3},g_{d+2,3})}=(x_1,x_2,x_3)
\]

is therefore exactly the first, radical-maximality half of the LPS
`PIC(d,3)` predicate.  `PIC(d,3)` also requires a separate determinant
non-membership condition.  The present Stage 0 work proves no new instance of
that determinant half and uses none of it to infer rigidity.

Source: D. Lewis, K. Perry and A. Straub, *An Algorithmic Approach to the
Polydegree Conjecture for Plane Polynomial Automorphisms*, definitions of
$g_{d,e}$ and `PIC(d,e)`, Theorems 3--4 and Lemma 12,
<https://arxiv.org/abs/1809.09681>.

## Calibrated boundary

No converse from the length-two closure conclusion back to partial rigidity is
asserted.  No finite computation is promoted to `R(3)`.  No priority or
novelty conclusion is drawn from this source check.
