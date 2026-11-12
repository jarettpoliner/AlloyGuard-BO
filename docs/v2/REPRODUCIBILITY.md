# Reproduce AlloyGuard-BO v2

Run from the existing repository with the unchanged `requirements.lock` environment. All v1 source, tests, data, frozen configurations and reports remain byte-identical. v2 lives in `src/alloyguard_v2`, `configs/v2`, `results/v2`, this directory, and new `*_v2.py` scripts/test. No fresh download is needed.

```bash
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.matplotlib-cache"
.venv/bin/pytest -q
.venv/bin/python scripts/run_v2.py --output results/v2/my_reproduction
```

The output must not already exist. This executes 30 seeds ×8 policies ×15 queries, plus four sensitivity scenarios and three grouped scenarios, each5 seeds ×8 policies ×15 queries:7,800 new queries in total. Each scenario has immutable traces, curves, metrics, configuration and checksums. For only the main comparison, add `--primary-only`. The frozen file hashes are checked before evaluation. Changing any frozen scientific file blocks a run; create a new explicitly labeled protocol revision rather than updating the existing freeze. Do not run `freeze_v2.py` again: it is a one-way original preparation step, retained for provenance.

Original workflow (already executed): full124-test pre-freeze suite; read-only v1 diagnosis; freeze; full evaluations;900 common-history shadow predictions; reporting; full3,600-query primary rerun; independent audit; final tests. `results/v2/freeze_evidence.json` records the pre-result freeze. Parameters were engineering assumptions, never selected by evaluation performance; per-step GP kernel fitting uses only revealed training observations.

Reporting and diagnosis are reproducible without rerunning v1 experiments:

```bash
.venv/bin/python scripts/diagnose_v2.py
.venv/bin/python scripts/shadow_v2.py
.venv/bin/python scripts/report_v2.py
.venv/bin/python scripts/audit_v2.py
```

These write only v2 presentation/analysis artifacts; they never alter v1. The audit expects the checked full rerun under `results/v2/reproduction/primary`, already supplied. To recreate it from scratch elsewhere, pass a new output root and compare all traces except `diagnostics.fit_seconds` and all metrics except `fit_seconds`; CSV curves must match exactly. The existing audit uses the documented canonical paths.

Read `configs/v2/protocol.md`, `results/v2/REPORT.md`, `results/v2/verdicts.json`, and `results/v2/audit.json` together. All conclusions are exploratory. `summary.csv` includes conditional seed intervals; `comparisons.json` includes paired contrasts. `common_history_quality.csv` and `common_history_paired.json` compare binary and continuous forecasts on identical queried cases. The post hoc 5–15% band is descriptive and never a model input. `factorial_ablations.json` separates continuous response modeling from threshold acquisition. `sensitivity.csv` and `group_support.json` retain all supplementary results.

The budget policy explicitly permits a minimum-risk fallback when no candidate meets the remaining per-step allocation; it is not a hard safety guarantee. There is no risk-parameter search or policy promotion. The Pareto curve joins nondominated fixed-policy means, not an optimized continuum. v1's negative calibration finding remains intact.
