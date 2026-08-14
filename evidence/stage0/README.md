# Furter R(3) Stage 0 internal package

**Workflow state: terminal pre-freeze.**  The canonical frozen package is not
yet built.  Terminal evidence now proves every finite instance $R(3,d-1)$ for
$2\le d\le300$, and also covers exact rational three-axis radical certificates
through $d=12$ and independently expanded modular radical-certificate pilots
through $d=8$.  The independently reconstructed resultant pilot through
$d=25$, the ordinary/optimized root, and the complete current-tree replay are
terminal PASS.  Frozen-package construction and fresh extracted verification
remain to be completed.

This package contains exact finite research on the radical condition

\[
\sqrt{(g_{d,3},g_{d+1,3},g_{d+2,3})}=(x_1,x_2,x_3).
\]

The frozen package will preserve the proof of the stored finite instances
$R(3,d-1)$ through $d=300$, record an axis-corrected resultant pilot through
$d=25$, store exact $x_3^d$ cofactor identities through $d=8$, and retain a
finite-field proof-object pilot placing powers of every coordinate in the
corresponding ideals through $d=8$.  It will **not** prove
the universal statement `R(3)`, the Strong Factorial Conjecture, or any new
all-degree Polydegree theorem.

Start with:

- `SPEC.md` — fail-closed claim contract;
- `RESEARCH_REPORT.md` — calibrated mathematical conclusions;
- `RESULTANT_NORMALIZATION.md` — finite-cover and ramification convention;
- `ENVIRONMENT.md` — recorded producer/verifier and runtime split;
- `SOURCE_CHECK.md` — primary-source implication and index dictionary;
- `GOOD_PRIME_FRONTIER.md` — exact finite patterns and the structural
  good-prime proof target, including the proved periodic zero-band obstruction
  to a universally GOOD fixed-prime certificate;
- `EULER_SOCLE_ROUTE.md` — exact two-identity reduction and canonical
  Euler--Jacobian pivot pilot;
- `euler-socle-recurrence-screen.json` — exact low-complexity recurrence
  exclusion with terminal holdouts reserved;
- `analyze_good_prime_frontier.py` — verified finite frontier receipt;
- `modular-radical-certificates-d2-8-verification.json` — independently
  expanded finite-field pure-power membership pilot;
- `rational-radical-certificates-d2-12-verification.json` — independent exact
  rational expansion, Hilbert-function/sharpness checks, and Euler--Jacobian
  socle pivots for all three axes;
- `run_good_prime_grid_shards.py` and `assemble_good_prime_grid_shards.py` —
  resumable full-rectangle infrastructure for the post-screen Frobenius study;
- `METHODOLOGY_AUDIT.md` — internal adversarial findings and repair record;
- `COMPLETION_AUDIT.md` — requirement-by-requirement scope and evidence gate;
- `REPLAY.sh` — complete verification from stored evidence;
- `verify_root.py` — root receipt generator/checker.

The intended replay uses:

- system Python with SymPy;
- `/opt/homebrew/bin/Singular` 4.4.1 or byte-identical executable; and
- the pinned Python/FLINT interpreter recorded in `ENVIRONMENT.md` and
  `REPRODUCE.md` for expensive producer/independent-reconstruction runs.

No publication action is part of this package.
