# Citrine 25°C tensile study: reproducibility

This is the completed **exploratory retrospective published-data benchmark**, independent in its artifacts from the frozen GE and provisional Mendeley studies. It is not prospective validation, and possible overlap with the earlier Mendeley software-development inputs is explicitly audited.

## Data and provenance

Primary: `MPEA_dataset.csv`,1545 rows, the complete master identified by the official [Citrine repository](https://github.com/CitrineInformatics/MPEA_dataset). Publication: Borg et al. (2020), Scientific Data, DOI10.1038/s41597-020-00768-9. Pin:`d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e`. All supplied master, 2018,2019,bibliography files match official Git blob identities exactly. The upstream README, Apache 2.0 license, processing notebook and utility source are retained under `data/citrine/raw/`. No upstream code/notebook is executed. The Apache license is a separate upstream repository license; original AlloyGuard MIT and Mendeley CC BY 4.0 attributions remain separate.

`source_manifest.json`, `data_audit.json`, `record_audit.csv`, `ambiguous_cases_preserved.csv` and `cohort.csv` under `results/citrine/` document every input/output hash, exclusion and retained case. The raw files are source cross-checks, never presented as an equivalent published master. If `MPEA_dataset.csv` is absent, acquisition reports that specific file requirement or retrieves its exact pinned official bytes; it never substitutes raw concatenation.

Qualification: explicitT and 25°C in master and raw records; numerical positive yield strength and nonnegative elongation; validated atom-ratio parsing; known recorded recipe; source DOI. Keep exactly one unambiguous composition+recorded-recipe case across studies. All repeated ambiguous recipe keys are quarantined intact, not averaged/deleted from evidence. This yields 80 reported cases, 58 feasible/22 infeasible, 36 cited studies and 31 conservative study-or-chemistry overlap groups. The cohort does not assert that all omitted quantitative process/strain-rate variables are controlled. Elongation>100% is not intrinsically invalid; those preliminary cases are excluded for repeated ambiguous recipe identity, not that value.

## Environment and inputs

Tested on Python 3.12.14/Linux, CPU numerical threads fixed to one, exact existing `requirements.lock`. No GPU, external inference service or extra library is needed. Use the existing checkout; cloud tasks are already isolated, so do not create a worktree.

The current prepared machine retains all original raw inputs. For a fresh checkout of the user's uploaded repository, restore the legacy regression-test inputs before running the whole test suite: copy `GE_RefractoryAlloyScreeningDataset_FINAL.csv` from root to `data/raw/`, and the two original workbooks from their `A database ...` folders into `data/additional/raw/` unchanged. Their expected hashes are in preserved source manifests. These legacy datasets are needed for the preserved 72 regression tests and the overlap diagnostic, not as training data for Citrine replay. The current result artifacts include historical cohorts/audits used by those tests. Do not replace a missing legacy original with synthetic measurements.

```bash
python -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements.lock
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.matplotlib-cache" XDG_CACHE_HOME="$PWD/.cache"
.venv/bin/python scripts/acquire_citrine.py
.venv/bin/python scripts/qualify_citrine.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_strength_v3.py
```

`acquire_citrine.py` prefers existing verified originals, then matching user-uploaded root files, and only downloads missing artifacts via pinned official HTTPS paths. Every file must match an expected Git blob hash before writing; different existing files are never overwritten. It executes no source code. Local inputs were verified without redownloading during reproduction.

## Frozen experiment

`configs/citrine/frozen.yaml` was written after 91 passing pre-freeze tests, synthetic checks, one-seed and five-seed smoke, and before primary results existed. Config hash:`0d7938858f175c854f1555f88ba0dc983cdff22c505f00bba742d7db50de5011`. Existing strength-model source is reused unchanged. Adapter source/data/qualification/lock hashes are checked before execution. Final suite:95 passing tests, including four post-evaluation audit checks without methodology changes.

12 outcome-blind initial cases and 15 extra queries, matched per seed across random, standard BO, CBO and RC-CBO;30 primary seeds 0–29. Objective: measured yield strength MPa; feasibility: tensile elongation≥10%. Primary score: trapezoid AUC best confirmed feasible strength at steps 0–15,0 before feasible observation. No measured phases, grain size, other properties or bibliography columns as predictors. Calibration uses only observed, study/chemistry-group OOF labels. No final-result-based tuning.

Complete primary reproduction and independent outcome/forecast audit (choose an unused directory):

```bash
bash scripts/reproduce_citrine.sh results/citrine/reproduced_fresh
```

The original primary remains at `results/citrine/primary/`; it is never overwritten. `freeze_citrine.py` refuses to refreeze the same protocol. Timing and rendering metadata may vary; all deterministic decisions, forecasts and non-timing metrics must match exactly/tolerantly as specified in the audit. The full second 30-seed run has already matched, and all 1800 primary decisions were audited against master measurements.

## Predeclared extra analyses and report generation

```bash
# New output root for all initialization, recipe-feature and grouped-shift diagnostics
.venv/bin/python scripts/run_citrine.py --diagnostics --output results/citrine/diagnostics_fresh
# Regenerate overlap diagnostic and all main figures/report from preserved original experiments
.venv/bin/python scripts/audit_citrine_overlap.py
.venv/bin/python scripts/report_citrine.py
```

Primary sensitivity outputs are retained under `results/citrine/diagnostics/`: initial sizes 8/16, five seeds 100–104,15 queries; known-recipe one-hot feature ablation on all policies equally; three source/chemistry-component heldout folds with seeds 200–204. Recipes are pre-experiment metadata. No study or chemistry component crosses heldout pools. Fold 1 has 15 target cases and 15 queries, so final target discovery is exhausted; comparisons concern order and prequential forecasts. Extra analyses are exploratory, correlated and not used to choose the primary model or cohort.

Report regeneration uses the original primary/diagnostics as the reference and saved audit evidence. To inspect separately regenerated diagnostics, compare their metrics/curves against the reference without editing either result tree. The primary reproduction entry point checks all deterministic primary outputs, not wall times or PDF timestamps. A user wishing to test a new methodology must create a separately labeled protocol/result revision rather than modify frozen code/data/config.

## Main artifacts and interpretation

- [Scientific report](../results/citrine/REPORT.md), five PNG/vector-PDF figures, actual numerical comparisons and all limitations.
- [Frozen configuration](../configs/citrine/frozen.yaml), [freeze evidence](../results/citrine/freeze_evidence.json).
- [Primary manifest](../results/citrine/primary/manifest.json), JSONL decisions, metrics and curves.
- [Paired comparisons](../results/citrine/paired_comparisons.json), [calibration/fit diagnostics](../results/citrine/model_diagnostics.json), [failure cases](../results/citrine/failure_analysis.json).
- [Independent audit](../results/citrine/independent_audit.json), [prior-data overlap](../results/citrine/prior_dataset_overlap.json), [final tests](../results/citrine/final_test_evidence.json).

Verdict: **NO_CONFIRMED_IMPROVEMENT from calibration**. Ordinary CBO has the highest mean discovery AUC, while RC-minus-CBO is−6.75 with conditional 95% interval[−52.61,39.11]. Calibration activated 194/450 steps and changed 25 acquisition winners, so this is a real active-calibration comparison, not the disabled-calibration GE case. Small imbalanced data, repeated finite-pool seeds, partial process descriptions, study dependencies and possible prior-development data overlap prevent universal or prospective superiority claims.
