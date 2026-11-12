#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.matplotlib-cache"
export XDG_CACHE_HOME="$PWD/.cache"
.venv/bin/python scripts/acquire_identified_data.py
.venv/bin/python scripts/audit_data.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_synthetic.py
.venv/bin/python scripts/run_benchmark.py --config configs/benchmark_frozen.yaml --output "${1:-results/reproduced_primary}"
.venv/bin/python scripts/run_diagnostics.py --output-prefix "${1:-results/reproduced_primary}/diagnostics"
.venv/bin/python scripts/audit_results.py --reproduced "${1:-results/reproduced_primary}" --diagnostics "${1:-results/reproduced_primary}/diagnostics"
.venv/bin/python scripts/posthoc_analysis.py
.venv/bin/python scripts/generate_report.py
