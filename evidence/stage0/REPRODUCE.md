# Full producer reproduction

`REPLAY.sh` verifies all stored mathematical evidence, regenerates the
independent exact-prefix and CRT determinant-verification receipts, and
byte-compares the root under ordinary and optimized Python.  Set `PYTHON_BIN`
to the SymPy-capable system interpreter and `FLINT_PYTHON_BIN` to the
python-flint environment shown below.  The commands below regenerate the
producer receipts.  They are intentionally separate because the complete
prime map, independently replayed degree-300 patch screen, and large exact
determinants are expensive.

Use a clean copy and do not edit any producer or `r3_common.py` while a job is
running.  Every producer checks its startup hashes again before atomically
publishing its receipt.  The resultant producer also binds its Python/FLINT
runtime artifacts and explicitly enables serialization of internally generated
exact integers beyond Python's default decimal-digit ceiling.

```zsh
python3 modular_colength.py \
  --d-min 2 --d-max 49 --prime-max 997 --timeout 300 \
  --out known-map-d2-49-p997.json
python3 -O modular_colength.py \
  --d-min 2 --d-max 49 --prime-max 997 --timeout 300 \
  --out known-map-d2-49-p997-opt.json

python3 run_projective_patch_shards.py \
  --workers 8 --timeout 120 --singular /opt/homebrew/bin/Singular --resume
python3 assemble_projective_patch_shards.py \
  --shard-directory . \
  --singular /opt/homebrew/bin/Singular \
  --out screen-patches-d50-300.json
python3 verify_projective_patch_screen.py \
  --input screen-patches-d50-300.json \
  --expected-d-min 50 --expected-d-max 300 --expected-prime-max 997 \
  --timeout 300 --workers 4 --singular /opt/homebrew/bin/Singular \
  --out screen-patches-d50-300-verification.json
python3 -O verify_projective_patch_screen.py \
  --input screen-patches-d50-300.json \
  --expected-d-min 50 --expected-d-max 300 --expected-prime-max 997 \
  --timeout 300 --workers 4 --singular /opt/homebrew/bin/Singular \
  --out screen-patches-d50-300-verification-opt.json

# Post-screen structural experiment: complete GOOD/BAD rectangle p <= 53.
python3 run_good_prime_grid_shards.py \
  --variant ordinary --d-min 2 --d-max 300 --prime-max 53 \
  --chunk-size 5 --workers 4 --timeout 3600
python3 run_good_prime_grid_shards.py \
  --variant optimized --d-min 2 --d-max 300 --prime-max 53 \
  --chunk-size 5 --workers 4 --timeout 3600
python3 assemble_good_prime_grid_shards.py \
  --variant ordinary --d-min 2 --d-max 300 --prime-max 53 \
  --chunk-size 5 --out good-prime-grid-ordinary-d2-300-p53.json
python3 assemble_good_prime_grid_shards.py \
  --variant optimized --d-min 2 --d-max 300 --prime-max 53 \
  --chunk-size 5 --out good-prime-grid-optimized-d2-300-p53.json
python3 -O verify_good_prime_grid.py \
  --input good-prime-grid-ordinary-d2-300-p53.json \
  --peer good-prime-grid-optimized-d2-300-p53.json \
  --d-min 2 --d-max 300 --prime-max 53 --chunk-size 5 \
  --shard-directory . --singular /opt/homebrew/bin/Singular \
  --out good-prime-grid-d2-300-p53-verification.json

python3 extract_cofactors.py --d-min 2 --d-max 8 --timeout 600 \
  --out cofactors-d2-8.json
python3 -O extract_cofactors.py --d-min 2 --d-max 8 --timeout 600 \
  --out cofactors-d2-8-opt.json

python3 extract_modular_radical_certificates.py \
  --map known-map-d2-49-p997.json \
  --verification known-map-d2-49-p997-verification.json \
  --d-min 2 --d-max 8 --singular /opt/homebrew/bin/Singular \
  --out modular-radical-certificates-d2-8.json
python3 -O extract_modular_radical_certificates.py \
  --map known-map-d2-49-p997.json \
  --verification known-map-d2-49-p997-verification.json \
  --d-min 2 --d-max 8 --singular /opt/homebrew/bin/Singular \
  --out modular-radical-certificates-d2-8-opt.json
python3 -O verify_modular_radical_certificates.py \
  --input modular-radical-certificates-d2-8.json \
  --peer modular-radical-certificates-d2-8-opt.json \
  --map known-map-d2-49-p997.json \
  --map-verification known-map-d2-49-p997-verification.json \
  --d-min 2 --d-max 8 --singular /opt/homebrew/bin/Singular \
  --out modular-radical-certificates-d2-8-verification.json

python3 extract_rational_radical_certificates.py \
  --d-min 2 --d-max 12 --singular /opt/homebrew/bin/Singular \
  --out rational-radical-certificates-d2-12.json
python3 -O extract_rational_radical_certificates.py \
  --d-min 2 --d-max 12 --singular /opt/homebrew/bin/Singular \
  --out rational-radical-certificates-d2-12-opt.json
python3 verify_rational_radical_certificates.py \
  --input rational-radical-certificates-d2-12.json \
  --peer rational-radical-certificates-d2-12-opt.json \
  --map known-map-d2-49-p997.json \
  --map-verification known-map-d2-49-p997-verification.json \
  --expected-d-min 2 --expected-d-max 12 --expected-prime-max 997 \
  --singular /opt/homebrew/bin/Singular \
  --out rational-radical-certificates-d2-12-verification.json
python3 -O verify_rational_radical_certificates.py \
  --input rational-radical-certificates-d2-12.json \
  --peer rational-radical-certificates-d2-12-opt.json \
  --map known-map-d2-49-p997.json \
  --map-verification known-map-d2-49-p997-verification.json \
  --expected-d-min 2 --expected-d-max 12 --expected-prime-max 997 \
  --singular /opt/homebrew/bin/Singular \
  --out rational-radical-certificates-d2-12-verification-opt.json

FLINT_PY=/Users/admin/Documents/Codex/2026-08-12/he/work/polydegree-flint-venv/bin/python

$FLINT_PY cover_resultant.py --d-min 2 --d-max 17 \
  --out resultant-prefix-ordinary.json
$FLINT_PY -O cover_resultant.py --d-min 2 --d-max 17 \
  --out resultant-prefix-optimized.json
$FLINT_PY -O verify_resultant_prefix.py \
  --input resultant-prefix-ordinary.json \
  --peer resultant-prefix-optimized.json \
  --out resultant-prefix-verification.json

for d in {18..25}; do
  $FLINT_PY cover_resultant_crt.py --d-min $d --d-max $d \
    --out resultant-shard-ordinary-d${d}.json
  $FLINT_PY -O cover_resultant_crt.py --d-min $d --d-max $d \
    --out resultant-shard-optimized-d${d}.json
  $FLINT_PY -O verify_resultant_crt.py \
    --input resultant-shard-ordinary-d${d}.json \
    --out resultant-shard-verification-d${d}.json
done

python3 assemble_resultant_shards.py \
  --ordinary-prefix resultant-prefix-ordinary.json \
  --optimized-prefix resultant-prefix-optimized.json \
  --shard-directory . \
  --ordinary-out cover-resultants-d2-25.json \
  --optimized-out cover-resultants-d2-25-opt.json \
  --d-min 2 --d-max 25
```

Then run:

```zsh
PYTHON_BIN=python3 \
FLINT_PYTHON_BIN="$FLINT_PY" \
SINGULAR_BIN=/opt/homebrew/bin/Singular \
./REPLAY.sh
```

After the terminal research record and methodology audit are closed, freeze
and verify the internal package with:

```zsh
python3 build_internal_package.py \
  --output ../../outputs/r3-stage0-internal-2026-08-13
python3 verify_package.py \
  --directory ../../outputs/r3-stage0-internal-2026-08-13 \
  --zip ../../outputs/r3-stage0-internal-2026-08-13.zip \
  --sha256 ../../outputs/r3-stage0-internal-2026-08-13.zip.sha256 \
  --singular /opt/homebrew/bin/Singular \
  --flint-python "$FLINT_PY" \
  --out ../../outputs/r3-stage0-internal-2026-08-13.verification.json
```

A regenerated producer receipt may differ in elapsed time and absolute startup
path.  The verifiers compare the mathematical projection and the bound bytes,
not those irrelevant runtime fields.
