#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.matplotlib-cache" XDG_CACHE_HOME="$PWD/.cache"
run_prefix="${1:-results/citrine/reproduced_new}"
.venv/bin/python scripts/acquire_citrine.py
.venv/bin/python scripts/qualify_citrine.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_strength_v3.py
.venv/bin/python scripts/run_citrine.py --output "$run_prefix"
.venv/bin/python scripts/audit_citrine.py --reproduced "$run_prefix"
.venv/bin/python scripts/audit_citrine_overlap.py
.venv/bin/python scripts/report_citrine.py
