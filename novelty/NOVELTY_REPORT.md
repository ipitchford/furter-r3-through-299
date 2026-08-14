# Novelty-gate report: Furter R(3) through index 299

**Search date:** 14 August 2026  
**Researcher/agent:** Codex, for Anonymous  
**Corpus boundary:** public literature discoverable through publisher DOI
pages, arXiv, author-hosted manuscripts, and exact-formula/title web searches  
**Intended contribution unit:** exact finite computer-assisted theorem

## 1. Frozen claim

### Exact statement

For every integer $d$ with $2\le d\le300$, put

$$
I_d=(g_{d,3},g_{d+1,3},g_{d+2,3})
\subset \mathbb Q[x_1,x_2,x_3],
$$

where $g_{k,3}$ is the coefficient of $X^{k+1}$ in the compositional inverse
of $X(1+x_1X+x_2X^2+x_3X^3)$. The release proves

$$
\sqrt{I_d}=(x_1,x_2,x_3).
$$

By Furter's equivalence, this is $R(3,n)$ for every $1\le n\le299$.

### Exclusions

- No claim for $n\ge300$, and no proof of universal $R(3)$.
- No proof of the unrestricted Strong Factorial Conjecture.
- No proof of the general Polydegree Conjecture.
- No claim that the length-two $(4,k)$ and $(k,4)$ closure consequences are
  the first proof of the full $e=3$ column: Evidence Press has already
  released a separate all-$d$ candidate by a smooth-point/Fourier/Arb route.
- No specialist peer review or external reconstruction is claimed.

### Permitted claim language before the gate

"We prove, by exact computer-assisted certificates, Furter's $R(3,n)$ for
$1\le n\le299$. Universal $R(3)$ remains open."

## 2. Normalisation and translation table

| Original notation | Canonical notation | Transformation checked |
|---|---|---|
| Furter $\widetilde R(3,n)$ | $\sqrt{I_{n+1}}=(x_1,x_2,x_3)$ | Furter, Lemma 2 |
| Furter $R(3,n)$ | one-map radical assertion | Furter, Lemma 2 |
| LPS $g_{d,e}$ | inverse coefficient in $e$ variables | LPS definition and independent formal reversion |
| release range $2\le d\le300$ | $1\le n\le299$ | $n=d-1$ |
| GOOD special fibre | height-three ideal over one $\mathbf F_p$ | weighted Bezout plus properness |

## 3. Fingerprints

### Sequences

- Consecutive inverse-coefficient windows
  $(g_{d,3},g_{d+1,3},g_{d+2,3})$.
- Complete-intersection lengths $d(d+1)(d+2)/6$.
- Normalized weighted resultants $R_d$ for $2\le d\le25$.
- Canonical Euler--socle scalars for $2\le d\le12$.

### Generating functions

The inverse series is the unique formal solution

$$G=w-x_1G^2-x_2G^3-x_3G^4.$$

### Small matrices/kernels

The weighted Euler matrix is

$$
(M_d)_{ij}=\frac{j}{d+i-1}\,\partial_{x_j}g_{d+i-1,3},
\qquad 1\le i,j\le3.
$$

### Invariants and recurrences

- Weighted degrees $d,d+1,d+2$ and socle degree $3d-3$.
- Furter's published order-three recurrence and its exceptional factor.
- The periodic zero-band condition
  $g_{n,3}=0\pmod p$ for
  $n\equiv-k\pmod p$, $2\le k\le\lfloor(p+2)/4\rfloor$, $p\ge7$.

## 4. Alias map

| Analysis | Probability | Combinatorics | Mathematical physics | Other |
|---|---|---|---|---|
| compositional inversion, algebraic formal series | none found | Lagrange inversion, multinomial valuations, Kummer carries | none found | polynomial composition rigidity, Polydegree Conjecture, Strong Factorial Conjecture |

## 5. Search log

| Date | Corpus/database | Query | Results inspected | Consequence |
|---|---|---|---|---|
| 2026-08-14 | publisher DOI / author manuscript | exact title *Polynomial composition rigidity and plane polynomial automorphisms* | Furter (2015) | original $R(m,n)$ statement, equivalence, and Polydegree dictionary located; universal $R(3)$ left conjectural |
| 2026-08-14 | arXiv / author manuscript | *algorithmic approach Polydegree Conjecture*; `d < 50` | Lewis--Perry--Straub (2019) | located the published computational benchmark $e=3$, $d<50$ |
| 2026-08-14 | arXiv / publisher DOI | *Strong Factorial Conjecture* and Furter rigidity | Edo--van den Essen (2014) | relationship is restricted; it is not an equivalence with the unrestricted conjecture at fixed $m=3$ |
| 2026-08-14 | exact formula web search | `g_{d,3}`, `g_{d+1,3}`, `g_{d+2,3}` with Polydegree terms | LPS and unrelated collisions | no public extension of the finite $R(3,n)$ range located |
| 2026-08-14 | exact conjecture search | `R(3,n)` with polynomial composition rigidity | Furter and unrelated Ramsey/rigidity uses | no published claim covering $1\le n\le299$ located |
| 2026-08-14 | arXiv / broad web | Polydegree Conjecture publications after 2019 | nearby polynomial-automorphism work and unrelated rigidity literature | no later public finite-window extension located |
| 2026-08-14 | exact topic search | Strong Factorial special cases, resultants, Newton polygons | Rocks; Filaseta--Rocks | related special-family work found, but no collision with the window theorem or zero-band statement |

## 6. Verified collisions or bridges

1. **Published finite-range collision.** Lewis, Perry and Straub prove the
   stronger determinant-augmented condition for the $e=3$ column when
   $d<50$. The new finite theorem therefore begins, as a range extension, at
   $d=50$ even though the release rechecks $d=2,ldots,49$ for regression.
2. **Conceptual bridge.** Furter proves the equivalence between the one-map
   radical condition and $R(3,n)$, then relates those instances to the
   length-two Polydegree closure problem.
3. **Restricted factorial bridge.** Edo and van den Essen connect rigidity
   with a special three-variable Strong Factorial family. This must not be
   restated as a proof of the unrestricted Strong Factorial Conjecture.
4. **Already-published Polydegree consequence.** The full $e=3$ Polydegree
   column is already an Evidence Press candidate by a different method. The
   new release's Polydegree consequences are corollaries and cross-validation,
   not its priority claim.
5. **Classical ingredients.** Properness, weighted complete-intersection
   Hilbert series, Kummer's theorem, and the Scheja--Storch socle theorem are
   not claimed as new.

## 7. Negative evidence and missingness audit

- No MathSciNet or zbMATH subscription-level full citation graph was queried.
- Searches were English-language and formula-based; non-indexed theses,
  workshop notes, and non-English documents may be missing.
- Some publisher citation pages did not expose complete citing-literature
  data.
- The zero-band lemma is elementary enough that an equivalent statement may
  exist in binomial-congruence literature under unrelated notation.
- Private manuscripts and unpublished work are outside the priority boundary.

These limitations constrain any "first" language. They do not affect the
mathematical validity of the frozen finite theorem.

## 8. Outcome by contribution unit

| Unit | Outcome | Confidence | Allowed wording | Forbidden wording |
|---|---|---:|---|---|
| Exact $R(3,n)$ theorem for $1\le n\le299$ | CLEAR relative to searched public record; extends known $n\le48$ benchmark | high | "we prove the finite range"; "no earlier published extension was found in the stated search" | "first ever" without the search boundary; "proves $R(3)$" |
| Same-prime GOOD-fibre certificate architecture | BRIDGE using standard properness and exact CAS | high | "we implement an exact same-prime special-fibre proof" | "new properness theorem" |
| Fixed-prime zero-band obstruction | BOUNDED UNCERTAINTY; no collision found | medium-high | "we establish" with proof; "no fixed prime works for this certificate route" | "no proof using one modulus can exist" |
| Euler--socle finite pilot | BRIDGE / structural evidence | high | "verified through $d=12$" | "uniform identity" or "solution of $R(3)$" |
| Frozen verification artefact | CLEAR TO RELEASE | high | "exact replayable evidence package" | "independent reproduction" or "formal verification" |

## 9. Decision

**CLEAR TO PROVE AND RELEASE, WITH BOUNDED NOVELTY LANGUAGE.**

The finite theorem is a public-record range extension of the LPS benchmark.
The release may state that no prior published extension to $n=299$ was found
in the documented search. It must not claim the universal conjecture or
present standard algebraic-geometric ingredients as original.

## 10. Rerun triggers

- discovery of a post-2019 paper or preprint computing $R(3,n)$ beyond the
  LPS range;
- discovery of the same Kummer zero-band statement in another notation;
- change of the headline from the finite theorem to an all-degree or
  Polydegree claim;
- addition of a new structural theorem beyond the currently verified finite
  Euler--socle pilot;
- any substantive change to the theorem range, generator normalization, or
  same-prime certificate definition.

