# Universal R(3) Challenge

This directory turns the remaining universal problem into a stable,
machine-readable research interface. The completed theorem is
`R(3,n)` for `1 <= n <= 299`; the challenge is the all-`n` statement.

The three routes are deliberately distinct:

1. prove the two canonical Euler--socle identities in every degree;
2. build a finite-prime product automaton that always produces one same-prime
   GOOD fibre; or
3. control the distinguished global initial state at Furter's exceptional
   recurrence mode.

Run:

```sh
python3 challenge/verify_challenge.py
```

The verifier checks the statement boundary, route inventory, finite theorem
receipt, and external archive receipt. It does not verify a future submitted
solution; the acceptance conditions in `challenge.json` define what such a
submission must add.

