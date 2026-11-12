#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.matplotlib-cache" XDG_CACHE_HOME="$PWD/.cache"
run_prefix="${1:-results/strength_v3/reproduced_software}"
.venv/bin/python scripts/prepare_strength_v3.py
.venv/bin/python -m pytest -q --junitxml=results/strength_v3/test_results.xml
.venv/bin/python scripts/verify_strength_v3.py
.venv/bin/python scripts/run_strength_v3.py --mode PROVISIONAL_SOFTWARE_VALIDATION --output "$run_prefix/first"
.venv/bin/python scripts/run_strength_v3.py --mode PROVISIONAL_SOFTWARE_VALIDATION --output "$run_prefix/second"
.venv/bin/python scripts/audit_strength_v3.py --first "$run_prefix/first" --second "$run_prefix/second"
.venv/bin/python scripts/report_strength_v3.py --run "$run_prefix/first"
.venv/bin/python scripts/summarize_strength_v3.py
