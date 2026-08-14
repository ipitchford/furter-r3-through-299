# Reproduction environment

The terminal producer and verifier receipts record their own environments.
The frozen local run used:

| Role | Runtime |
|---|---|
| modular producer and cofactor extraction | CPython 3.14.6, Singular 4.4.1 |
| coefficient and sparse-identity verification | CPython 3.14.6, SymPy 1.14.0 |
| cover/Koszul resultant production and independent determinant reconstruction | CPython 3.14.6, python-flint 0.8.0 |
| assembly, modular/resultant cross-checks, and root verification | CPython 3.14.6, standard library plus SymPy 1.14.0 |

The local executables were:

```text
/opt/homebrew/bin/Singular
/Users/admin/Documents/Codex/2026-08-12/he/work/polydegree-flint-venv/bin/python
```

Receipts bind the exact producer/shared-source bytes and, for Singular jobs,
the resolved executable bytes.  The verifiers accept a current executable via
`--singular`, compare its SHA-256 with the single executable digest stored in
the producer receipt, and do not require the historical path to exist.  Source
files are likewise matched once by basename and then by SHA-256.  Relocation
therefore preserves content identity without trusting a name alone.

The resultant producers additionally capture and recheck the resolved Python
executable and framework library, every non-cache file in the installed
`flint` package and its distribution metadata, and the bundled FLINT, GMP, and
MPFR dynamic libraries.  The independent determinant verifiers bind their own
source, the independently implemented formal-reversion core, every raw input,
and the producer/runtime inventory validated from that input.  The internal
replay requires those recorded artifacts
to remain available at their bound paths.  Reproducing the producers in a new
environment creates a new runtime-bound receipt pair; equality of mathematical
projections, not path identity with the original machine, is then the relevant
comparison.

No network access is needed for `REPLAY.sh`.  Set `PYTHON_BIN` to a Python
environment containing SymPy and `FLINT_PYTHON_BIN` to one containing
python-flint.  They may be different interpreters.  The replay regenerates
every independent exact-prefix and CRT determinant-verification receipt,
rather than trusting the stored verifier outputs.  Installing dependencies or
reproducing producer receipts in a new environment is a separate action.
