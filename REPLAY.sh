#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h}"
cd "$ROOT"

python3 challenge/verify_challenge.py >/dev/null
python3 verify_release.py

if [[ "${FULL_EVIDENCE_REPLAY:-0}" == "1" ]]; then
  echo "Running full exact evidence replay."
  evidence/stage0/REPLAY.sh
else
  echo "PUBLIC_RELEASE_FAST_REPLAY_PASS"
  echo "Set FULL_EVIDENCE_REPLAY=1 to recompute the full Stage 0 evidence chain."
fi

