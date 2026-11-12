# Yield-strength/elongation continuation

This is a separate study from the frozen GE hardness/ordinal-screening benchmark. All GE methods, lock, data and primary results remain unchanged.

**G1a complete:** accepted independently verified official Mendeley source v1, DOI `10.17632/4d4kpfwpf6.1`, published 29 July 2025, CC BY 4.0, associated Chemical Data Collections 47 (2023), 101068, DOI `10.1016/j.cdc.2023.101068`. [Recorded provenance](../data/additional/mpea_official_provenance_v3.json) distinguishes user verification from agent retrieval attempts (HTTP 403), and records actual original workbook size/SHA-256/MD5/Git blob identity. Dataset-level provenance is resolved.

**G1b unresolved:** no primary-source case methods/table evidence is yet accessible. [Eight prioritized studies](../results/strength_v3/priority_studies.csv) cover 123/457 paired rows and include the original conflicting-key source. No blanket 135-study review is required. An empty schema-bearing [primary cohort](../results/strength_v3/primary_cohort.csv) records zero *established* qualified cases, not an assertion the literature cannot support a cohort. The broader 453-row provisional subset retains condition uncertainty and excludes four unresolved identity records from software input while preserving them in the [record-level table](../results/strength_v3/record_qualification.csv) and original workbook.

**Software G2–G4 complete:** `src/alloyguard_strength/` implements MPa GP regression, binary tensile-elongation feasibility GPC, observed-study/chemistry-group OOF regularized temperature scaling, random/strength BO/CBO/RC-CBO, typed hidden-outcome replay, group-aware holdouts, metrics and labeled figures. Numerical/leakage/integration tests and deterministic provisional replay pass. These are engineering checks, not scientific efficacy findings. Current development settings use composition-only reported element vectors; no atomic/mass basis is invented for uncertain data. No measured phases, other mechanical properties, study ID or undocumented cluster label is a predictor.

The primary proposed objective remains maximum measured tensile yield strength (MPa), constrained by measured tensile elongation >=10%, initially for source-documented 20–30 °C tests. A documented alternative stratum can be separately declared before freezing if the accessible evidence supports it. Unknown temperature is not room temperature by assumption. Source annotations must identify loading, temperature, same material state and planned processing/test identity; legitimate replicates require a documented source-justified handling protocol rather than arbitrary deletion or averaging.

No frozen scientific protocol or final primary comparison exists. `freeze_strength_v3.py` refuses G1b-unresolved cases; final execution separately verifies the cohort/config/source hashes and explicit final mode. Insufficient class/group support disables calibration instead of forcing it. Group holdouts operate on source/chemistry overlap components without hidden targets. Recorded forecasts retain latent versus observation SD and use an explicitly assumed 25 MPa observational noise; no physical guarantee or validated coverage claim is attached.

From the repository root with existing `.venv` and locked dependencies:

```bash
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.matplotlib-cache" XDG_CACHE_HOME="$PWD/.cache"
.venv/bin/python scripts/prepare_strength_v3.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_strength_v3.py
# Complete software-only reproduction; choose an unused output prefix
bash scripts/reproduce_strength_v3.sh results/strength_v3/software_new
```

The reproduction entry point rebuilds qualified/provisional artifacts, tests, synthetic checks, two five-seed provisional executions, independent observed-ID/group/target audit, and five labeled diagnostic figure types. Provisional comparisons are not interpreted as method superiority, calibrated physical risk, or a room-temperature study. Run directories refuse overwriting.

After source evidence resolves G1b, not before:

```bash
.venv/bin/python scripts/prepare_strength_v3.py
.venv/bin/python scripts/freeze_strength_v3.py
.venv/bin/python scripts/run_strength_v3.py --mode FINAL_SCIENTIFIC \
  --config configs/strength_v3/benchmark_frozen.yaml --output results/strength_v3/primary
```

The annotation template is `data/additional/annotations/record_evidence_v3.csv`. Reviewer/evidence locator/excerpt/conditions are required; citation metadata alone does not verify measurements. If evidence identifies repeated experiments, preserve raw replicates and resolve case identity first. Existing v2 audits are historical artifacts and are not overwritten by v3 qualification.

The precise remaining action is to apply the saved source-access domain settings, or supply methods/table evidence from prioritized publications (start with `10.1016/j.jallcom.2022.163774`, 36 pairs, and `10.1016/j.jallcom.2021.162907`, conflicting key). No additional dataset DOI/license research or credentials are required. See [current report](../results/strength_v3/REPORT.md) and [gate verdict](../results/strength_v3/verdict.json).
