#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.matplotlib-cache" XDG_CACHE_HOME="$PWD/.cache"
run_root="${1:-.local-reproduction/run1}"
if [[ -e "$run_root" ]]; then
  echo "Choose a fresh output directory: $run_root already exists" >&2
  exit 1
fi
.venv/bin/python scripts/prepare_publication_inputs.py
.venv/bin/python scripts/run_citrine.py --output "$run_root/v1"
.venv/bin/python scripts/run_v2.py --output "$run_root/v2"
.venv/bin/python scripts/verify_publication.py --reproduced "$run_root" --output "$run_root/verification.json"
