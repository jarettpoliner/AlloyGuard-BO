# Execution log

## 11 November 2026, America/New_York — setup and data-access gate

- Inspected the existing checkout and read `AlloyGuard_BO_Research_Execution_Plan (1).md` and the user's authoritative execution prompt. Initial Git status was clean; the original plan and LICENSE were preserved. No AGENTS.md or prior implementation was present.
- The user explicitly authorized project implementation, extending the onboarding scope. Project files were added for that request. No unrelated checkout was changed; no push or commit was made.
- Managed environment became ready. Status reported current observations, running phase, enforced restricted networking, no declared secrets/runtime variables. GitHub authentication verified with read-only `git ls-remote origin HEAD` (aad46b4525d5903eadb5953cefefcaba3d8771d1).
- `curl -i --max-time 20` against `https://api.figshare.com/v2/articles/17032760`, `https://doi.org/10.6084/m9.figshare.17032760.v1`, and `https://pmc.ncbi.nlm.nih.gov/articles/PMC9679436/` returned proxy CONNECT 403. No source content was downloaded or executed. This is an explicit policy denial; no bypass was attempted.
- Installed CPU scientific dependencies into `.venv` with verified package transport, froze exact versions in `requirements.lock`, and ran `pip check` successfully. Python 3.12.14 is compatible with the requested Python >=3.11.
- Implemented only the provenance acquisition helper. `.venv/bin/python -m pytest -q`: 5 passed. These are mocked integrity tests, not scientific-model tests.
- Actual `.venv/bin/python scripts/download_data.py` exited 2 with `BLOCKED_DATA_SOURCE: URLError: ... Tunnel connection failed: 403 Forbidden`.
- Saved environment draft fields `install_script`, `start_skill`, and required domain additions. Tool confirmed saved and `requires_publish=true`. Existing presets were preserved. Draft save does not apply or publish settings.
- Re-ran the saved setup commands to check repeatability. No application service is required. No modeling or outcome-dependent design decisions were made. Required audits, experiments and scientific metrics remain unrun.

## Gates

| Gate | Status | Evidence |
|---|---|---|
| G1 Data verified | BLOCKED_DATA_SOURCE | Official sources denied by proxy; no measurements available |
| G2 Models verified | NOT_STARTED | Authentic data prerequisite unmet |
| G3 Policies verified | NOT_STARTED | No policies implemented |
| G4 Replay verified | NOT_STARTED | No replay implemented |
| G5 Protocol frozen | NOT_STARTED | Data audit required first |
| G6 Benchmark complete | NOT_STARTED | No results |
| G7 Scientific validation complete | NOT_STARTED | No findings |
| G8 Repository complete | NOT_STARTED | Only environment and acquisition preparation complete |

## Critical review of current deliverables

No claimed scientific results, inferred license, substituted measurements, or passing scientific gates. The acquisition helper checks integrity but deliberately does not claim a full schema audit. Source content, actual download redirects and version-specific API behavior remain unverified until access works. The lockfile pins versions, not a cross-platform wheel/hash resolution; installation retained normal TLS/package verification. Final scientific independent audit remains pending, since no models or conclusions exist.

## Final current-instance checks

- Repeated install from `requirements.lock`: passed, all pinned packages already satisfied. Repeated test run: 5 passed.
- Imported NumPy, SciPy, pandas, scikit-learn, matplotlib and PyYAML; fitted minimal GP regression/classification fixtures and verified finite predictions. This verifies installed APIs only, not the scientific model.
- `git diff --stat` empty: original tracked plan and LICENSE unchanged. New setup/helper/documentation files are untracked and reviewable; ignored virtual environment is retained locally.
- Lockfile SHA-256: `f5ea917bffc828771f41f5c87a526aaefd95cba1d5cb62646ac172ca9a271a0a`.
- Downloader SHA-256: `6cdb4619fc3cd023ab2c351b8eb4e26f3bf340d76b4380a98a9c2f34760f19a8`.
- Refreshed runtime status after draft save: observations current, network enforced, custom domain list still empty. Saved network additions have not been applied; no unchanged failing request was repeated.

## Resume — identified official file 31504751

- First checked `data/raw/`: directory and original CSV absent. Created the empty directory for the user's original file; no replacement measurements generated.
- Preserved existing helpers, tests, source manifest, lockfile, and reports; appended continuation findings rather than replacing earlier findings. New user-provided source expectations are in `data/identified_source_requirements.json`.
- Direct HTTPS probe `curl -i -L --max-time 30 https://ndownloader.figshare.com/files/31504751` failed with proxy CONNECT HTTP 403, exit 56. No redirect or file bytes received.
- Refreshed managed runtime: current observations, running phase, enforced policy, custom domain list empty. Read saved draft revision 2: eight requested custom hosts, including the direct-download host, are saved but unapplied. No duplicate domain update or secret request is needed.
- Added `scripts/acquire_identified_data.py` to validate local bytes before attempting direct acquisition, requiring the exact supplied 4,706-byte size and MD5. Only verified bytes can produce a SHA-256/structural-inspection receipt. Source metadata/license remain explicitly unverified until checked independently.
- Four additional tests exercise wrong size, wrong checksum at correct size, local-file precedence/preservation, and prevention of invalid-download writes. Full suite: **9 passed in 0.03s**. These do not validate real experimental data.
- End-to-end new acquisition command exited 2: `BLOCKED_DATA_SOURCE: URLError: ... Tunnel connection failed: 403 Forbidden`. No acquisition receipt exists and actual dataset SHA-256 remains unknown.
- G1 remains blocked. G2–G8 not started. No policies, calibration, benchmarks, figures, or scientific conclusions claimed. Existing frozen dependency lock is unchanged; there is no frozen experimental protocol yet.
- Minimum external action: apply saved Figshare/source domain changes, or supply the unchanged original CSV in `data/raw/` to enable local integrity/schema auditing. Independent official provenance/license verification remains required for G1.

## G1 — Local experimental data verified and audited

- The user's upload was in the latest remote Git commit at repository root rather than the requested local raw path. Read-only remote inspection found `843c94d3264ab73904512ff3e54b1634084428d1`; fetched that commit and copied only its CSV into the existing `data/raw/` directory. No checkout reset, repository restart, merge, push, or overwriting of local implementation files.
- Exact local size 4,706 bytes; MD5 `2a829ae75f620735b874b73fe69bf4d5`; SHA-256 `a9f2b7aaf4b7305535c321bf1354115ac0c157ef1159b23829dff850212ceacd`. No further dataset download after integrity matched.
- `PYTHONPATH=src .venv/bin/python scripts/audit_data.py` passed: actual expected 12-column schema, 86 complete finite raw records, 82 exact unique composition groups, atomic-percent sums within 1e-6 at%, nonnegative fractions. No renormalization or imputation.
- Two triplicate groups: mean hardness and minimum ordinal rank, with replicate ranges/SD/row IDs preserved. No composition can be split between observed/hidden sides. Rank 4/4/5 replicates all satisfy the operational threshold.
- Frozen scientific decision before comparisons: retain rank >=3. Seven feasible versus 75 infeasible composition groups fail the original plan's preferred 15-per-class support gate. Disable real-data calibration; do not invent or relax support to activate it. RC-CBO must coincide with CBO. The calibration implementation is still tested independently on synthetic observations.
- G1 passes for the supplied original measurements and scientific schema with a provenance qualification: exact bytes match official identifiers supplied by user; official publisher metadata/license were not independently re-downloaded. CC BY 4.0 is attributed to the user's source record, not falsely claimed as independently fetched. Source-manifest qualification remains explicit.

## G2–G4 — Models, policies and leakage-safe replay verified

- Implemented typed immutable composition-only candidates and revealed observations, private replay-owned oracle, no target table/oracle passed to policies, complete structured decisions, no repeated composition selection, deterministic finite-pool acquisition.
- Hardness: observed-only StandardScaler, target centering/scaling, Matérn-5/2 GPR, bounded signal optimization with 60-iteration cap, fixed 0.15 GPa observation-noise assumption. EI uses latent variance; future observation intervals add noise explicitly.
- Feasibility: Matérn Laplace GPC, fixed regularized kernel, class imbalance retained, logged Beta(1,1) prior fallback for single-class observations. No class-oversampling probability distortion.
- Temperature scaling: grouped observed-only three-fold cross-fitting, minimum support, bounded positive temperature, regularized log(T), identity fallback. Real-data gate disabled from G1; no hidden outcome is used to fit it.
- Random, hardness-only EI, raw CBO and calibrated CBO implemented. Identical constrained cold-start uses feasibility plus 0.05 times normalized nearest-observed composition distance. Product acquisition explicitly approximates conditional factorization.
- `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest -q --junitxml=results/test_results.xml`: **38 passed, 0 failed, 0 errors, 0 skipped**. Tests cover real data integrity/invalid schemas, duplicate grouping, posterior updates, noise decomposition, probability bounds, class fallback, EI, no feasible incumbent, cross-fit isolation, target-invariant policy inputs, deterministic equal-budget replay, unique selection and config hashing.
- `PYTHONPATH=src .venv/bin/python scripts/verify_synthetic.py`: passed; deterministic noisy toy has high-hardness infeasible region and known feasible optimum, all four policies equal budgets, repeated decisions identical. Evidence explicitly labeled software correctness only.
- One-seed real replay: seed 314, four policies x 15 selections = 60 selections completed. Five-seed smoke: seeds 0–4, four policies x 15 = 300 selections completed. Full manifests/traces saved under `results/one_seed/` and `results/smoke/`; rankings not used for protocol adjustment.
- All numerical warnings are retained per fit. Bound optima reflect regularized small-sample GP fits; optimizer status, finite predictions and positive variances checked before primary freeze. No policy changes made after smoke.

## G5 — Protocol frozen before final comparison

- `PYTHONPATH=src .venv/bin/python scripts/freeze_protocol.py` checked zero-failure pre-freeze test evidence, synthetic verification, one-seed and five-seed manifests; froze 30 predetermined seeds (0–29), n_initial=12, budget=15, threshold=3, all hyperparameters/cold-start rules, primary/secondary conventions, data processing, sensitivity seeds/initial sizes and OOD support requirements.
- Canonical config SHA-256: `fe5fe4829880e29676d481143fbb12b106b2326839a3fa7802f776f7ae36a94d`. Scientific Python source SHA-256: `c55d6ea7627663d2663772b6cca5f5d5bbe4f0dd5024ca395e2272fb79d9d9d3`. Processed data SHA-256: `9f92eae22b0f957625b58d78372db7acbc9579f33132376c899f261135690ce0`.
- No final comparative outcome had been inspected at freeze; no policy/source-method change was made afterward. A type-only `.pyi` public interface and report/audit wrappers were subsequently added without changing frozen runtime source, predictions, or methods. Tests later added are post-comparison audit assertions, not outcome-based methodology revisions.

## G6 — Real-data benchmark complete

- `PYTHONPATH=src .venv/bin/python scripts/run_benchmark.py`: 30 seeds x 4 policies x 15 additional selections = **1,800 real-data selections**, 120 runs, completed in 12.42 seconds with one numerical thread.
- `results/primary/` contains immutable full decisions/forecasts/outcomes/fit diagnostics in JSONL/CSV, step-zero-through-15 curves, run metrics, config and hashed completion manifest. Output directories refuse silent replacement.
- Mean AUC (GPa·evaluations): random 49.983751; hardness-only 64.405707; CBO/RC-CBO 61.703192. Mean failed rank-screen selections /15: 14.10, 13.10, 12.433333, 12.433333 respectively.
- CBO minus hardness-only AUC: −2.702515, conditional paired 95% t interval [−4.858650, −0.546380]. Failure-count difference −0.666667 [−0.981890, −0.351444]. RC-CBO minus CBO exactly zero for every seed, with identical selected IDs/forecasts/acquisition scores because calibration is disabled.
- No claimed calibration benefit. Primary metric favors hardness-only over the constrained policy in this fixed pool, despite fewer constrained screening failures. Correlated finite-pool repeated replay is not independent physical experimentation.

## G7 — Scientific validation, figures and failure analysis

- `PYTHONPATH=src .venv/bin/python scripts/run_diagnostics.py`: exploratory initial sizes 8 and 16, seeds 100–104, equal 15-query budgets within each experiment; 600 additional selections. All separately labeled and saved, with no primary-method tuning. Different initial sizes incur different total measurement costs.
- Composition-only KMeans clusters contain (22 groups, 4 feasible), (29,3), (31,0). Predeclared >=4 positives on each train/target side is impossible with seven total: `OOD_TEST_INSUFFICIENT_SUPPORT`. No OOD performance result manufactured.
- `scripts/generate_report.py`: five required figures in PNG and vector PDF; prequential reliability bins, ROC-AUC/Brier/log loss, regression MAE/NLL/coverage, timings and proper warning/fallback counts saved. Primary has 35 retained kernel-bound warnings, 0 optimizer non-successes, 162 feasibility-prior fallback fits, 0 calibration activations/failures/ranking changes.
- `scripts/posthoc_analysis.py`: most observed AUC loss associated descriptively with eight seeds starting without feasible alloys (mean CBO-minus-hardness AUC −10.557154); 22 seeds with initial feasibility have +0.153717. This is posthoc diagnosis, not a causal improvement proposal or tuned replacement policy.
- Actual Figure 5 case: seed 26, step 1, predicted hardness 12.093616 GPa, p=0.071429 from single-class fallback; observed 10.599406 GPa, rank 0. Matched-observation CBO chose a different but still rank-1 candidate. Neither low probability nor different selection proves risk avoidance. The complete case is retained, not replaced with a favorable example.
- Independent audit recomputed all outcomes/AUC/failure counts for 1,800 decisions from raw grouped data, verified pre-reveal observed sets, no repeats/replicate leaks, matched initialization, frozen source/config/output hashes, and constrained-policy equality. It is a separate recomputation within this session, not external peer review.
- `bash scripts/reproduce.sh results/reproduced_primary`: complete second 30-seed real-data run (1,800 selections) matched **all deterministic decision/forecast/outcome fields exactly** and all non-timing metrics; timing naturally differed. No new measurements/data or dataset downloads. Original artifacts were not overwritten.

## G8 — Repository, reproducibility and final review

- Complete source modules, typed immutable schemas/public policy type stub, exact dependency lock, test suites, scripts, frozen configs, manifests, all raw-derived results, figures, scientific report, method/model/data cards, references and CITATION.cff are present. Original LICENSE, plan, acquisition code/tests and lock preserved; historical blocked README/report notes archived. No remote push, deployment, service exposure or privileged modifications.
- Final unit/integration/numerical/artifact-audit suite: **43 passed, 0 failures, 0 errors, 0 skipped** (`results/final_test_results.xml` and `final_test_evidence.json`). The original pre-freeze 38-test evidence is kept separately.
- Visually inspected discovery and failure figures: legible axes/units, policy labels, exact CBO/RC overlap and genuine measured failure annotation. All five PNG/PDF pairs generated from run outputs.
- Initial plotting reported unwritable default matplotlib/fontconfig caches; reporting/audit wrappers now set project-local MPLCONFIGDIR and XDG_CACHE_HOME. Regeneration succeeded. This runtime-output correction does not change frozen scientific source or benchmark outputs.
- Full `results/REPORT.md` includes actual results, paired uncertainty qualifications, all secondary metrics/censoring, exploratory sensitivities, insufficient OOD support, actual failure/counterfactual, warning diagnosis, provenance caveat and next research step.
- **Research verdict: INCONCLUSIVE for calibration efficacy.** Seven feasible groups cannot support the prescribed calibration experiment; RC-CBO reduces to ordinary CBO. This does not establish active-calibration equivalence or superiority, physical discovery, or performance against Radical AI's system.

## Current gate ledger (supersedes historical blocked ledger)

| Gate | Final status | Evidence |
|---|---|---|
| G1 | PASSED_WITH_PROVENANCE_QUALIFICATION | Exact original size/MD5/SHA-256 and actual scientific schema audited; official license/source metadata user-supplied, not independently fetched |
| G2 | PASSED | GP posterior/noise/probability/numerical and calibration correctness tests |
| G3 | PASSED | Four matched policies, finite EI, no-feasible and single-class tests |
| G4 | PASSED | Typed policy/oracle boundary, observed-group cross-fitting, duplicate exclusion, deterministic toy and real replay |
| G5 | PASSED | Hashed frozen methods/data/source/config before primary comparison |
| G6 | PASSED | Completed 30-seed, 1,800-selection primary with immutable artifacts |
| G7 | PASSED | Paired statistics, 5 figures, exploratory diagnostics, critical raw-outcome audit; unsupported calibration/OOD efficacy explicitly not claimed |
| G8 | PASSED | 43 tests, full deterministic 30-seed reproduction, report/docs/scripts/artifact review |

## Reproduction entry-point completion

The final reproduction script also regenerates both initialization sensitivity experiments and the composition-only chemistry-shift support audit under an unused nested diagnostics directory. The new diagnostics-output option and audit comparison were exercised against the preserved originals without rerunning or changing any policy methodology. Both sensitivity metrics/curves and chemistry-shift counts matched. The documented entry point therefore covers secondary analyses as well as primary replay, posthoc failure diagnostics, figures and report regeneration. No original experiment directories are silently overwritten.

## New strength/elongation extension — dataset qualification before models

This is a separate study under the user's latest instructions, not a revision of the GE frozen methodology. The original GE source files, lock, raw/processed data, configs, primary/reproduced results and research plan are unchanged. No newly nominated primary benchmark is claimed.

### Discovery and integrity

- Inspected the workspace and full selected remote Git tree. Only GE was locally present. Remote commit `be942502d094d5a360595166e25a53cc24d5cf88` contains the two additional workbooks. Copied their exact Git blobs into `data/additional/raw/`; no reset, merge, new repository, push or overwrite of existing work. Citrine CSV absent from inspected workspace and selected remote tree.
- MPEA Git blob: `8dfa71562a028c9a8dfab9ca47e4079dcef65adf`, size 282,828 bytes. Steel Git blob: `9d9b021a934620fbfc6132964c39a58b1c1b91c6`, size 444,713 bytes. Whole-file SHA-256/MD5 and source paths are saved in separate manifests. Local/upload byte identity is established; no official version/checksum/license is invented.
- Used Python stdlib ZIP/XML and existing pandas to read cached XLSX cells; no downloaded code execution, workbook formula execution or dependency installation. Exact original dependency lock is preserved. No source MIT software license is assumed to cover the uploaded third-party data.

### Prespecified suitability assessment and audit

- Saved `configs/dataset_qualification_v2.yaml` before any new optimization/model comparison. Hard gates: source record/publication/license/version; actual experimental same-case tensile yield/elongation; documented test temperature; known composition units; identifiable independent cases. Class support/size are considered only after these gates. Initial proposed stratum: verified 20–30 °C tensile tests, elongation >=10%, maximum measured tensile yield strength (MPa). Unknown conditions are unresolved, not silently assumed.
- `.venv/bin/python scripts/qualify_datasets.py`: verified 1,713 MPEA records and 457 finite physically screened numeric pairs (341 >=10%, 116 <10%). Raw paired strength 62–2663 MPa, elongation 0–98%; zero elongation retained. Numeric compositions are fraction-like/rounded; no unit reinterpretation or renormalization. Paired composition sums 0.997–1.002; full workbook has larger composition anomalies outside the paired subset.
- MPEA paired rows have 138 raw citations, 135 normalized DOI citation IDs, 330 composition strings and 310 rounded chemistry vectors. No exact duplicate full paired record. 456 composition–processing-note–study proxy keys represent 457 rows: the repeated `AlCoCrFeNi2.1`/`50μm/s`/`10.1016/j.jallcom.2021.162907` case reports different measurements. Replicate versus unrecorded-condition status is unknown; no automatic aggregation is justified. Full cases/source metadata preserved for review.
- MPEA has 82 paired records with blank processing notes, no test-temperature column, 316 pairs also reporting UTS, and four pairs also reporting compressive strength. Neither property-column names nor processing temperatures establish loading/test temperature or same-test pairing. Seven whole-workbook records mention FEM/simulation, but **none of the 457 paired rows is explicitly simulation-marked**. Lack of a note is not affirmative experimental provenance.
- Steel: all 3,234 records have numeric paired properties, with 53 <10% before deduplication. Removing record ID and exact repeated content yields 1,943 distinct full records, only 32 <10%. Study IDs and explicit test-temperature information are missing; percentage-like composition basis remains unverified. Undocumented clusters are excluded from predictors. Larger raw N does not make steel the stronger feasibility benchmark.
- Source/chemistry-overlap components and a 135-citation primary-publication review queue are saved to prevent random-row leakage. Independent-case counts and class support remain unresolved. Measured phase labels/indicators, hardness, other properties and potentially outcome-derived clusters are excluded from proposed predictors.

### Genuine remaining blocker and scope decision

- Neither workbook provides an overall official dataset/publication/version/license record. No source documentation establishes comparable tensile room-temperature yield/elongation pairs and processing/test-case identity. A public Crossref title-metadata lookup returned proxy CONNECT HTTP 403. Runtime status is current/enforced with no applied custom domains; earlier saved domains remain unapplied.
- Asked asynchronously for official source/publication DOI/URL/license and test-condition/data-dictionary documentation while continuing the complete local audit. No response supplied those sources during this work.
- Decision: **MPEA is preferred provisionally**, based on class support and available citation mapping, with no optimization outcomes used. **No qualified new primary selected. New G1 blocked; new G2–G8 not started.** Do not adapt the GE nine-element/hardness model by relabeling MPa or ordinal screening as elongation, and do not silently mix incompatible cases.
- Minimum action: official MPEA dataset/publication identifier with license/version and source/data-dictionary annotations for composition basis, loading mode, actual test temperature, same-case property pairing and processing/replicate identity. Official metadata/publication access can be enabled for source review; no credential needed. Once qualified, proceed with a separately frozen strength study and preserve GE independently.

### Validation and reproducibility

- `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest -q --junitxml=results/dataset_qualification/test_results.xml`: **51 passed**, no failures/errors/skips (43 original tests plus eight new workbook/parser/qualification checks).
- New tests verify actual workbook row/class counts, exact steel deduplication, finite numeric screening with zero elongation retained, citation normalization/transitive leakage groups, OOXML column parsing, cached-formula reading without execution, uncached-formula rejection, and unchanged GE source/lock hashes.
- Qualification script is repeatable without new dependencies; output JSON/CSV/Markdown and hashed artifact manifest under `results/dataset_qualification/`. New original workbooks are locally retained but ignored pending license qualification. No new strength BO metrics or improvement claims produced.

## MPEA v3 continuation — G1a resolved; software proceeds while G1b is reviewed

### Resolved provenance and separate gates

- Accepted the user's independently verified Mendeley Data source: *A database of mechanical properties for multi principal element alloys*, Li/Zeng/Tan/Taheri/Birbilis, v1, 29 July 2025, DOI `10.17632/4d4kpfwpf6.1`, CC BY 4.0. Associated Chemical Data Collections 47,101068 (2023), DOI `10.1016/j.cdc.2023.101068`. No repeated request for dataset provenance or license.
- G1a **COMPLETE_USER_VERIFIED_PROVENANCE_AND_LOCAL_INTEGRITY**. Exact original workbook: 282,828 bytes; SHA-256 `ba34522f472520f3dd6114f5e3fbddb139b7dba5414b153e6476fe3153f5f25f`; MD5 `c85db7af18b64a20e0d6cffc8eb09f49`; Git blob `8dfa71562a028c9a8dfab9ca47e4079dcef65adf`. New explicit source manifest records verification evidence and does not pretend an official checksum was fetched.
- Fresh HTTPS requests to `https://data.mendeley.com/datasets/4d4kpfwpf6/1` and `https://doi.org/10.1016/j.cdc.2023.101068` returned proxy CONNECT HTTP 403. Current enforced runtime policy still had no custom domains. Added Mendeley/ScienceDirect/linkinghub source domains to the draft, preserving all prior domains/presets; save confirmed, unapplied/unpublished. No bypass, credential request, dataset re-download or source-content execution.

### Efficient G1b qualification

- Ranked the 135 normalized citation IDs by paired row contribution, not policy performance; prioritized the top eight (123/457=26.9% coverage), including conflicting source `10.1016/j.jallcom.2021.162907`. Top source `10.1016/j.jallcom.2022.163774` contributes 36 rows (21 provisionally feasible,15 infeasible). Review/database citations are flagged for underlying-original-study checks, not treated as proven independent studies.
- No primary full-text evidence was available locally or accessible under current source-domain policy. The eight are explicitly marked not retrieved/review incomplete; no indiscriminate requirement to read all 135 was imposed.
- New `results/strength_v3/record_qualification.csv`: 1,256 EXCLUDED (no valid paired targets for this objective), 453 CONDITION_UNCERTAIN, four CONFLICTING (unresolved identity), zero VERIFIED. Source-verified primary cohort is schema-bearing but empty. This means no cohort has been *established with accessible evidence*, not that no defensible cohort exists in the literature.
- Two previously known discordant `AlCoCrFeNi2.1`/50μm/s records remain intact. DOI normalization also connects two same-value `CoCrFeMn` records at Excel 670/1531, `10.1016/j.intermet.2016.09.003` (338 MPa,4.3%); these are potential duplicates/identity ambiguity, not falsely claimed discordant values. All four are preserved in raw/audit files and quarantined from the provisional execution input; no arbitrary averaging/deletion or invented replicate status.
- Explicit evidence-annotation interface requires citation match, actual methods/table evidence URL/locator/excerpt/reviewer, tensile mode, source-established test temperature/material-state pairing, composition basis and processing identity. Missing test temperature is not room temperature. Repeated source-verified same-case keys require a replicate protocol. No measured phase/property or source-ID predictors. Qualified independent cases/classes: 0 established/0+0; provisional independent-case count remains unknown.

### G2–G4 software developed autonomously

- Implemented separate typed `src/alloyguard_strength/` modules for MPa GPR, tensile-elongation binary GPC, conservative study/chemistry-group OOF regularized temperature scaling, four policies, immutable policy inputs, replay-owned oracle, prequential metrics and group-aware holdouts. Original `src/alloyguard/` frozen GE source is unchanged.
- Strength GP: observed-only scaling, Matérn-5/2, bounded signal optimization/max60 iterations, assumed 25 MPa noise, explicit latent versus future-observation variance. Feasibility: observed-only Matérn GPC, Beta(1,1) single-class fallback. Calibration: n>=20, both classes>=5 and >=3 observed groups/class; all 3 grouped folds require both classes; T bounded [1/3,3] and regularized log(T); identity fallback with reasons. Every fold refits preprocessing/model and logs disjoint groups/IDs/fit diagnostics. Approximate factorized EI·p is explicitly qualified.
- Random, strength-only EI, ordinary CBO and RC-CBO share matched architecture/preprocessing/budgets, differ only in acquisition/calibration as intended. Cold start is identical probability+0.05 geometry exploration, no undefined feasible incumbent. All candidates scored exhaustively; no repeated independent-case ID/reveal. Source/chemistry component holdouts have explicit disjointness checks and tests; no physical shift robustness claim without qualified data.
- Full tests: **72 passed, zero failures/errors/skips** (`results/strength_v3/test_results.xml`). Preserves previous 51 tests plus21 new strength/group-calibration/leakage/numerical/annotation/replay tests.
- Dedicated synthetic verifier passed deterministic known MPa strength/elongation functions, fixed observation noise, active grouped calibration and constrained risk discount. Synthetic artifacts are labeled software correctness, not experimental validation.
- Five-seed provisional integration (seeds700–704,n_initial24,budget3,four policies=60 selections) completed using the 453 broader flagged rows. A second complete replay exactly reproduced deterministic decisions/forecasts/outcomes/non-timing metrics. Independent software audit verified every observed-ID set, grouped calibration isolation and raw reported targets. 13 calibration-active software steps, zero strength optimizer non-successes. These are exercised code paths, not calibration quality or optimization efficacy findings.
- Five PNG/PDF plot types generated with conspicuous PROVISIONAL SOFTWARE CHECK labels. No final comparative ranking, effect size, significance interval, physical reliability claim or room-temperature benchmark interpretation was made from this run.

### Scientific freeze/final evaluation remains guarded

- `configs/strength_v3/development.yaml` explicitly nonfrozen. `freeze_strength_v3.py` was exercised and correctly refused G1b-unresolved input (`CANNOT_FREEZE_G1B_UNRESOLVED`). Final execution separately requires frozen config/source/cohort hashes and qualified records. No empty successful scientific run or fake final frozen protocol created.
- G2–G4 pass *software verification only*. New G5 not frozen; G6 final comparison unrun; G7 efficacy unevaluated; G8 final research incomplete. These are not inherited from the completed GE study.
- Existing GE frozen source, dependency lock and primary artifact hashes were independently rechecked unchanged. No dependency installation, worktree/repository restart, push, privileged changes or deployment.
- Current reproducibility entry point: `bash scripts/reproduce_strength_v3.sh <unused-output-prefix>` rebuilds provenance/cohort tables, tests, synthetic checks, two provisional runs, audit and labeled figures/report. Full report and gate ledger are in `results/strength_v3/REPORT.md` / `verdict.json`; prior source audits/reports preserved.
- **Only remaining external prerequisite:** apply saved source-access settings or provide methods/table excerpts for prioritized publications (begin with the 36-row source and conflicting key). This is access to case-level evidence, not another dataset metadata/license request. Once a defensible cohort is established, freeze and run the final benchmark; insufficient calibration support will be disabled/documented rather than forced.

### Final continuation checks

- End-to-end `bash scripts/reproduce_strength_v3.sh results/strength_v3/reproduction_checked` passed: 72 tests, synthetic checks, two deterministic 60-selection provisional runs, group/observed-ID audit, five labeled PNG/PDF plot types and full continuation report. It did not run or freeze primary science.
- Software fit warnings investigated: all20 are the conservative 0.3 lower GP length-scale bound; zero optimizer non-successes and no invalid predictions/acquisitions. The bound was not changed based on provisional outcomes. Exact warnings remain logged; they indicate a modeling limitation, not reliable physical extrapolation.
- Visually inspected the strength discovery pipeline figure: explicit PROVISIONAL SOFTWARE CHECK/unverified-condition title, MPa axes and policy labels. No scientific interpretation of its relative curves is made.
- Rechecked all original GE scientific source, lock and primary output hashes; unchanged. Confirmed no final strength frozen configuration was created. Source-access evidence, current report/verdict and 72-test evidence are saved under `results/strength_v3/`; the environment startup instructions were updated and saved as a draft, not applied/published.

## Citrine25°C tensile study — completed G1–G8 exploratory workflow

### G1: official files, published master and conservative cohort

- Current user direction explicitly selects published Citrine MPEA data as primary, before any new policy result inspection. This is a separately labeled study, not a silent merge/overwrite of GE or Mendeley. Existing72 tests, model sources, provisional results and reports preserved.
- User uploads found in remote commit `b3d0390f6de21a1989d8f1b934ec608486e878c9`; existing checkout wasn't reset. Recovered2018_data.csv,2019_data.csv,wos_query_refs.bib and **MPEA_dataset.csv**, then read the official public repository via the existing HTTPS Git proxy. Official pinned commit `d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e`; **all four blob hashes exactly match**. No missing-master substitution, no new project/worktree, push or credential access.
- Read official README, full Apache2.0 LICENSE, process.ipynb(JSON) and utility source **as data only**. Upstream notebooks/code not executed or dependencies installed. The README identifies MPEA_dataset.csv as complete master and combined/raw files as processing inputs. Atomic-ratio normalization explicitly uses atomic fractions, ratios normalized by maximum and three-decimal rounding. Upstream removes uncertainty/censor markers and averages some ranges; raw values are cross-checked rather than silently recast.
- Master1,545 records;2018 raw614 and2019 raw931. Test mode, explicit temperature and normalized DOI align row-wise for all1,545; direct numerical source yield values match.246 explicitT/25°C paired numeric records. All final80 canonical compositions match raw stoichiometry plus documented rounding; standalone safe parser includes parentheses, no pymatgen install.
- Primary criterion before optimization: positive finite yield, nonnegative finite elongation, explicit tensile modeT and25°C in both sources, valid composition, known recorded recipe and DOI, uncensored source target. All repeated composition+normalized-recipe keys (even across studies) quarantined intact rather than averaged across unknown anneals. Raw curator note warns repeated annealing recipes can represent different temperatures/durations. Detailed recipe sequence is preserved, not conflated with broad CAST/WROUGHT class.
- Qualified **80 unique reported case groups:58 feasible,22 infeasible**,36 cited studies,31 transitive study-OR-chemistry leakage groups. Full per-record/all/first exclusion reasons retained; exact counts in data_audit.json sum with80 to1,545. Elongation>100% is physically possible and not itself excluded; those preliminary rows are excluded by ambiguous recipe repetition. One retained ±reported mean uses the unchanged published numeric target, with uncertainty string retained. No unknown conditions invented, no target-driven policy tuning or measured-phase inputs.
- Case independence is a reported-data qualification, not proof of independently replicated laboratory trials or completely controlled heat treatment/strain rate. Cohort/source/input/output SHA-256 and Git hashes recorded. Official repository Apache license kept separately from AlloyGuard MIT and Mendeley CC BY4.0.

### G2–G4: reuse, tests and software checks

- Reused the existing `alloyguard_strength` models/policies/replay **unchanged** through `alloyguard_citrine` adapter. No MPa-to-hardness relabeling, no phases/grain size/UTS/other measured predictors. Primary composition-only representation; planned recipe one-hot ablation specified before final comparison. Existing raw/posterior noise separation, group-only OOF temperature scaling, typed candidate/oracle boundary and deterministic exhaustive acquisition retained.
- Pre-freeze full suite: **91 passed,0 failed/errors/skips**, including prior72 unchanged tests plus parser, source-pinning, explicit25°C, case grouping, source-composition checks and qualification-hash guards. Synthetic correctness passed using existing verifier. One-seed(seed314) and five-seed(seeds0–4) full15-query smoke completed for all four methods. An additional input-qualification guard was tested before freeze; initial/checkpoint smoke directories preserved separately rather than overwritten.
- All numerical warnings kept. No baseline weakened or hyperparameters changed based on final outcomes.

### G5: frozen before primary results

- `scripts/freeze_citrine.py` required passing tests/synthetic checks and current-source one/five-seed smoke. Frozen config hash `0d7938858f175c854f1555f88ba0dc983cdff22c505f00bba742d7db50de5011`; `freeze_evidence.json` records primary output did not yet exist. Adapter hash `00d34388d62cfe8408d90d843db74b90309557561ac10f5370b33f0b662f9c38` and original strength source/cohort/qualification/lock hashes recorded. No scientific source or method changed afterward.
- Primary seeds0–29,12 outcome-blind shared initialization cases,15 extra selections per policy, rank-independent elongation threshold10%, primary trapezoid best-feasible MPa AUC steps0–15,0 before first feasible. Global class/group support admits calibration; activation still requires current-observed minimums and valid grouped folds. One numerical thread; exact original lock unchanged.
- Initialization8/16, recipe one-hot ablation and three study/chemistry-disjoint shift folds/seeds/support rules were predeclared before comparison. No later favorable split/model selection.

### G6: actual primary and additional experiments

- Full primary **30seeds×4policies×15=1,800 selections**,120 runs, completed. Mean AUC(MPa·evaluations): random13,023.16; standard BO13,332.683333; CBO13,985.573333; RC-CBO13,978.823333. Failures/15:4.30,7.166667,5.266667,5.233333 respectively.
- RC-minus-CBO primary difference **−6.75**, conditional paired95% t interval **[−52.609779,39.109779]**; no confirmed improvement. Calibration activated194/450 RC queries and changed25 acquisition winners. It genuinely affects this policy experiment, unlike GE's disabled calibration. Same RC queried-case Brier raw0.222998/calibrated0.219216 does not demonstrate improved experiment selection.
- CBO-minus-standard AUC+652.89[73.8445,1231.9355]; failure reduction1.90[0.7300,3.0700]. CBO's interval versus random includes zero. Highest mean does not imply superiority to all baselines or prospective new-study performance.
- Initialization8/16 and processing-feature ablations: three separately logged5-seed experiments,300 selections each=900. Three study/chemistry-heldout folds:300 selections each=900; all support checks passed. Fold1 has15 target cases/15 queries, so final pool is exhausted; timing/order/prediction are the informative outcomes there. No study or chemistry component crosses train/target.

### G7: scientific audit, predictions and failure analysis

- Source-derived five required PNG/PDF figures, conditional paired statistics, prequential calibration/discrimination, strength MAE/NLL/coverage, fit overhead, activation/ranking changes and failed-selection diagnostics generated from traces.
- **867 boundary warnings retained:**852 lower length bound0.3 and15 upper6.0;0 optimizer non-successes, finite valid predictions/acquisitions. Boundary preference indicates small-data/composition-only covariance limitations; no bounds were adjusted after seeing outcomes. Observation SD adds assumed25MPa noise; subnominal coverage is explicitly reported, not advertised as calibrated physical certainty.
- Failure report preserves first CBO/RC divergence, worst RC-minus-CBO seed, all positive/negative/equal seed outcomes and an actual high-predicted-strength low-elongation standard-BO selection. No inconvenient trace deleted or synthetic result substituted as laboratory evidence.
- Additional posthoc provenance audit found**63 possible overlaps among80 cases** with prior Mendeley software-test inputs (exact property pair and composition agreement within0.003). Not proof of independent duplicates, but sufficient to disclaim pristine external validation. All replay models still fit only revealed observations, not prior trained weights; defaults retained and no final policy outcomes tuned methods. Development-data exposure remains an explicit limitation, not erased by leakage-safe replay.
- Independent raw-outcome audit checked all**1,800 primary selections/120 runs**, original published T/25°C/targets, pre-reveal observed-ID sets, no case repeats, active-fold grouping, latent/noisy variance, every AUC/failure count, and900 heldout queries. Complete second frozen30-seed run reproduced all deterministic decision/forecast/outcome fields and non-timing metrics. This is an independent recomputation in the session, not external peer review.

### G8: deliverables and final validation

- Final full suite: **95 passed,0 failures/errors/skips**. Four post-evaluation tests verify freeze-before-primary evidence, calibration/probability contracts, equal matched budgets/no repeats, and independent audit/reproduction; they do not change methods.
- Complete executable source adapter, pinned official acquisition, qualification, frozen protocol, scientific replay, diagnostics, independent audit, report and reproduction scripts; all source/primary artifacts remain unmodified after freeze. Existing GE source/lock/primary hashes and original strength-model hash rechecked unchanged. Earlier studies preserved independently.
- Main report: `results/citrine/REPORT.md`; reproducibility: `docs/CITRINE_REPRODUCIBILITY.md`; actual primary outputs: `results/citrine/primary/`; frozen config: `configs/citrine/frozen.yaml`; source manifest/exclusions/case cohort/diagnostics/audit all under `results/citrine/`. Historical Mendeley qualification blockers are not incorrectly applied to the complete published Citrine benchmark.
- **Research verdict: NO_CONFIRMED_IMPROVEMENT from calibration, conditional exploratory evidence only.** Ordinary CBO has highest mean discovery AUC. Small80-case pool,22 negative cases, overlapping replays, study/chemistry dependencies, coarse process information and prior-development exposure limit claims. Results support an independently heldout prospective processing-resolved follow-up, not a new state-of-the-art or proprietary-system superiority claim.
- All executable G1–G8 stages for this exploratory published-data study complete. No deployment, remote push, new repository, dependency changes or physical experiment was performed. Cloud configuration publication remains separate from current-instance validation.

### Delivery verification

The documented Citrine reproduction entry point was exercised end-to-end under a new result directory: official artifacts verified locally with no source re-download, identical qualification/cohort, full95-test suite, synthetic checks, complete30-seed replay, deterministic primary-output audit, overlap diagnostic and figure/report regeneration. All passed. Scientific source/config/cohort hashes remain unchanged. Minor presentation-only report spacing is applied after numerical report generation without changing metrics, identifiers, URLs, frozen methods or primary artifacts. Updated startup guidance was saved as an environment draft; saving is not publication or proof of fresh-task restoration.
