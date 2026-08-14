#!/bin/zsh
set -euo pipefail
unsetopt BG_NICE

PACKAGE_DIR="${0:A:h}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
FLINT_PYTHON_BIN="${FLINT_PYTHON_BIN:-$PYTHON_BIN}"
SINGULAR_BIN="${SINGULAR_BIN:-$(command -v Singular || true)}"
[[ -n "$SINGULAR_BIN" && -x "$SINGULAR_BIN" ]] || {
  echo "Singular executable not found; set SINGULAR_BIN" >&2
  exit 1
}
REPLAY_DIR="$(mktemp -d /tmp/r3-stage0-replay.XXXXXX)"
trap 'rm -rf "$REPLAY_DIR"' EXIT

cd "$PACKAGE_DIR"

"$PYTHON_BIN" -c 'import sympy'
"$FLINT_PYTHON_BIN" -c 'import flint'

"$PYTHON_BIN" -m py_compile \
  r3_common.py modular_colength.py run_modular_screen_shards.py \
  assemble_modular_screen_shards.py verify_colength.py \
  run_good_prime_grid_shards.py assemble_good_prime_grid_shards.py \
  verify_good_prime_grid.py analyze_good_prime_frontier.py \
  projective_patch_screen.py verify_projective_patch_screen.py \
  run_projective_patch_shards.py assemble_projective_patch_shards.py \
  analyze_combined_good_prime_frontier.py \
  probe_groebner_signatures.py \
  extract_modular_radical_certificates.py verify_modular_radical_certificates.py \
  extract_rational_radical_certificates.py verify_rational_radical_certificates.py \
  extract_cofactors.py verify_cofactors.py \
  cover_resultant.py cover_resultant_crt.py verify_resultant_crt.py \
  verify_resultant_prefix.py \
  assemble_resultant_shards.py verify_resultants.py \
  analyze_cofactor_recurrence.py build_falsification_queue.py verify_root.py \
  analyze_euler_socle_recurrence.py \
  verify_counterexample_candidate.py verify_package.py build_internal_package.py

"$PYTHON_BIN" -O verify_counterexample_candidate.py --self-test

"$PYTHON_BIN" verify_colength.py \
  --input known-map-d2-49-p997.json \
  --peer known-map-d2-49-p997-opt.json \
  --expected-d-min 2 --expected-d-max 49 --expected-prime-max 997 \
  --require-good-coverage --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/known-verification.json"

"$PYTHON_BIN" assemble_projective_patch_shards.py \
  --shard-directory . \
  --out "$REPLAY_DIR/screen-patches-d50-300.json" \
  --singular "$SINGULAR_BIN"

cmp "$REPLAY_DIR/screen-patches-d50-300.json" screen-patches-d50-300.json

"$PYTHON_BIN" verify_projective_patch_screen.py \
  --input screen-patches-d50-300.json \
  --expected-d-min 50 --expected-d-max 300 --expected-prime-max 997 \
  --timeout 300 --workers 4 --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/screen-patch-verification.json"
"$PYTHON_BIN" -O verify_projective_patch_screen.py \
  --input screen-patches-d50-300.json \
  --expected-d-min 50 --expected-d-max 300 --expected-prime-max 997 \
  --timeout 300 --workers 4 --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/screen-patch-verification-opt.json"
cmp "$REPLAY_DIR/screen-patch-verification.json" \
  "$REPLAY_DIR/screen-patch-verification-opt.json"
cmp "$REPLAY_DIR/screen-patch-verification.json" \
  screen-patches-d50-300-verification.json
cmp "$REPLAY_DIR/screen-patch-verification-opt.json" \
  screen-patches-d50-300-verification-opt.json

"$PYTHON_BIN" analyze_combined_good_prime_frontier.py \
  --known-map known-map-d2-49-p997.json \
  --known-verification known-map-d2-49-p997-verification.json \
  --patch-screen screen-patches-d50-300.json \
  --patch-verification screen-patches-d50-300-verification.json \
  --patch-verification-peer screen-patches-d50-300-verification-opt.json \
  --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/good-prime-frontier.json"

"$PYTHON_BIN" probe_groebner_signatures.py \
  --map known-map-d2-49-p997.json \
  --verification known-map-d2-49-p997-verification.json \
  --expected-d-min 2 --expected-d-max 49 --expected-prime-max 997 \
  --singular "$SINGULAR_BIN" --out "$REPLAY_DIR/groebner-signatures.json"
"$PYTHON_BIN" -O probe_groebner_signatures.py \
  --map known-map-d2-49-p997.json \
  --verification known-map-d2-49-p997-verification.json \
  --expected-d-min 2 --expected-d-max 49 --expected-prime-max 997 \
  --singular "$SINGULAR_BIN" --out "$REPLAY_DIR/groebner-signatures-opt.json"
cmp "$REPLAY_DIR/groebner-signatures.json" "$REPLAY_DIR/groebner-signatures-opt.json"

"$PYTHON_BIN" extract_modular_radical_certificates.py \
  --map known-map-d2-49-p997.json \
  --verification known-map-d2-49-p997-verification.json \
  --d-min 2 --d-max 8 --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/modular-radical-certificates.json"
"$PYTHON_BIN" -O extract_modular_radical_certificates.py \
  --map known-map-d2-49-p997.json \
  --verification known-map-d2-49-p997-verification.json \
  --d-min 2 --d-max 8 --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/modular-radical-certificates-opt.json"
cmp "$REPLAY_DIR/modular-radical-certificates.json" \
  "$REPLAY_DIR/modular-radical-certificates-opt.json"

"$PYTHON_BIN" -O verify_modular_radical_certificates.py \
  --input modular-radical-certificates-d2-8.json \
  --peer modular-radical-certificates-d2-8-opt.json \
  --map known-map-d2-49-p997.json \
  --map-verification known-map-d2-49-p997-verification.json \
  --d-min 2 --d-max 8 --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/modular-radical-certificate-verification.json"

"$PYTHON_BIN" extract_rational_radical_certificates.py \
  --d-min 2 --d-max 12 --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/rational-radical-certificates-d2-12.json"
"$PYTHON_BIN" -O extract_rational_radical_certificates.py \
  --d-min 2 --d-max 12 --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/rational-radical-certificates-d2-12-opt.json"
cmp "$REPLAY_DIR/rational-radical-certificates-d2-12.json" \
  "$REPLAY_DIR/rational-radical-certificates-d2-12-opt.json"

"$PYTHON_BIN" verify_rational_radical_certificates.py \
  --input "$REPLAY_DIR/rational-radical-certificates-d2-12.json" \
  --peer "$REPLAY_DIR/rational-radical-certificates-d2-12-opt.json" \
  --map known-map-d2-49-p997.json \
  --map-verification known-map-d2-49-p997-verification.json \
  --expected-d-min 2 --expected-d-max 12 --expected-prime-max 997 \
  --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/rational-radical-certificates-d2-12-verification.json"
"$PYTHON_BIN" -O verify_rational_radical_certificates.py \
  --input "$REPLAY_DIR/rational-radical-certificates-d2-12.json" \
  --peer "$REPLAY_DIR/rational-radical-certificates-d2-12-opt.json" \
  --map known-map-d2-49-p997.json \
  --map-verification known-map-d2-49-p997-verification.json \
  --expected-d-min 2 --expected-d-max 12 --expected-prime-max 997 \
  --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/rational-radical-certificates-d2-12-verification-opt.json"
cmp "$REPLAY_DIR/rational-radical-certificates-d2-12-verification.json" \
  "$REPLAY_DIR/rational-radical-certificates-d2-12-verification-opt.json"

"$PYTHON_BIN" analyze_euler_socle_recurrence.py \
  --input "$REPLAY_DIR/rational-radical-certificates-d2-12-verification.json" \
  --peer "$REPLAY_DIR/rational-radical-certificates-d2-12-verification-opt.json" \
  --out "$REPLAY_DIR/euler-socle-recurrence-screen.json"
"$PYTHON_BIN" -O analyze_euler_socle_recurrence.py \
  --input "$REPLAY_DIR/rational-radical-certificates-d2-12-verification.json" \
  --peer "$REPLAY_DIR/rational-radical-certificates-d2-12-verification-opt.json" \
  --out "$REPLAY_DIR/euler-socle-recurrence-screen-opt.json"
cmp "$REPLAY_DIR/euler-socle-recurrence-screen.json" \
  "$REPLAY_DIR/euler-socle-recurrence-screen-opt.json"

"$PYTHON_BIN" verify_cofactors.py \
  --input cofactors-d2-8.json --peer cofactors-d2-8-opt.json \
  --expected-d-min 2 --expected-d-max 8 --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/cofactor-verification.json"

"$FLINT_PYTHON_BIN" -O verify_resultant_prefix.py \
  --input resultant-prefix-ordinary.json \
  --peer resultant-prefix-optimized.json \
  --out "$REPLAY_DIR/resultant-prefix-verification.json"
cmp "$REPLAY_DIR/resultant-prefix-verification.json" \
  resultant-prefix-verification.json

for batch_start in 18 22; do
  typeset -a crt_pids
  crt_pids=()
  for d in $(seq "$batch_start" $((batch_start + 3))); do
    "$FLINT_PYTHON_BIN" -O verify_resultant_crt.py \
      --input "resultant-shard-ordinary-d${d}.json" \
      --out "$REPLAY_DIR/resultant-shard-verification-d${d}.json" &
    crt_pids+=("$!")
  done
  for crt_pid in "${crt_pids[@]}"; do
    wait "$crt_pid"
  done
  for d in $(seq "$batch_start" $((batch_start + 3))); do
    cmp "$REPLAY_DIR/resultant-shard-verification-d${d}.json" \
      "resultant-shard-verification-d${d}.json"
  done
done

"$PYTHON_BIN" assemble_resultant_shards.py \
  --ordinary-prefix resultant-prefix-ordinary.json \
  --optimized-prefix resultant-prefix-optimized.json \
  --shard-directory . \
  --ordinary-out "$REPLAY_DIR/resultant-ordinary.json" \
  --optimized-out "$REPLAY_DIR/resultant-optimized.json" \
  --d-min 2 --d-max 25

cmp "$REPLAY_DIR/resultant-ordinary.json" cover-resultants-d2-25.json
cmp "$REPLAY_DIR/resultant-optimized.json" cover-resultants-d2-25-opt.json

"$PYTHON_BIN" verify_resultants.py \
  --input cover-resultants-d2-25.json \
  --peer cover-resultants-d2-25-opt.json \
  --modular-map known-map-d2-49-p997.json \
  --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/resultant-verification.json"

"$PYTHON_BIN" build_falsification_queue.py \
  --known-map known-map-d2-49-p997.json \
  --known-verification known-map-d2-49-p997-verification.json \
  --screen screen-patches-d50-300.json \
  --screen-verification screen-patches-d50-300-verification.json \
  --singular "$SINGULAR_BIN" \
  --out "$REPLAY_DIR/falsification-queue.json"

"$PYTHON_BIN" analyze_cofactor_recurrence.py \
  --cofactors cofactors-d2-8.json \
  --verification cofactors-d2-8-verification.json \
  --out "$REPLAY_DIR/cofactor-recurrence-screen.json"

cmp "$REPLAY_DIR/known-verification.json" known-map-d2-49-p997-verification.json
cmp "$REPLAY_DIR/screen-patch-verification.json" \
  screen-patches-d50-300-verification.json
cmp "$REPLAY_DIR/screen-patch-verification-opt.json" \
  screen-patches-d50-300-verification-opt.json
cmp "$REPLAY_DIR/good-prime-frontier.json" good-prime-frontier-d2-300.json
cmp "$REPLAY_DIR/groebner-signatures.json" groebner-signatures-d2-49.json
cmp "$REPLAY_DIR/groebner-signatures-opt.json" groebner-signatures-d2-49-opt.json
cmp "$REPLAY_DIR/modular-radical-certificates.json" \
  modular-radical-certificates-d2-8.json
cmp "$REPLAY_DIR/modular-radical-certificates-opt.json" \
  modular-radical-certificates-d2-8-opt.json
cmp "$REPLAY_DIR/modular-radical-certificate-verification.json" \
  modular-radical-certificates-d2-8-verification.json
cmp "$REPLAY_DIR/rational-radical-certificates-d2-12.json" \
  rational-radical-certificates-d2-12.json
cmp "$REPLAY_DIR/rational-radical-certificates-d2-12-opt.json" \
  rational-radical-certificates-d2-12-opt.json
cmp "$REPLAY_DIR/rational-radical-certificates-d2-12-verification.json" \
  rational-radical-certificates-d2-12-verification.json
cmp "$REPLAY_DIR/rational-radical-certificates-d2-12-verification-opt.json" \
  rational-radical-certificates-d2-12-verification-opt.json
cmp "$REPLAY_DIR/euler-socle-recurrence-screen.json" \
  euler-socle-recurrence-screen.json
cmp "$REPLAY_DIR/cofactor-verification.json" cofactors-d2-8-verification.json
cmp "$REPLAY_DIR/resultant-prefix-verification.json" resultant-prefix-verification.json
for d in {18..25}; do
  cmp "$REPLAY_DIR/resultant-shard-verification-d${d}.json" \
    "resultant-shard-verification-d${d}.json"
done
cmp "$REPLAY_DIR/resultant-verification.json" cover-resultants-d2-25-verification.json
cmp "$REPLAY_DIR/falsification-queue.json" falsification-queue.json
cmp "$REPLAY_DIR/cofactor-recurrence-screen.json" cofactor-recurrence-screen.json

"$PYTHON_BIN" verify_root.py --singular "$SINGULAR_BIN" --out "$REPLAY_DIR/root.json"
"$PYTHON_BIN" -O verify_root.py --singular "$SINGULAR_BIN" --out "$REPLAY_DIR/root-opt.json"
cmp "$REPLAY_DIR/root.json" "$REPLAY_DIR/root-opt.json"
cmp "$REPLAY_DIR/root.json" root-receipt.json

echo "R3_STAGE0_REPLAY_PASS"
