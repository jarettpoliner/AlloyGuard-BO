# AlloyGuard-BO strength/elongation continuation

## Established result and gate split

**G1a is complete. G1b remains unresolved; no final scientific comparison has run.** The executable software pipeline, model/policy correctness and provisional replay have advanced while cohort qualification remains separate. No claim is made that the literature cannot support a cohort—only that one is not established from the evidence accessible in this environment.

## G1a — source provenance and local integrity complete

Dataset: *A database of mechanical properties for multi principal element alloys*, Zhipeng Li, Zhuoran Zeng, Ruijia Tan, Mitra Taheri, Nick Birbilis. Mendeley Data, **v1, 29 July 2025**, DOI https://doi.org/10.17632/4d4kpfwpf6.1, CC BY 4.0. Associated peer-reviewed publication: same title, *Chemical Data Collections* **47**, 101068 (2023), https://doi.org/10.1016/j.cdc.2023.101068. The dataset release date and publication year are distinct, not silently conflated.

The user independently verified these official sources. This attestation resolves the earlier unknown publication/version/license fields for the MPEA continuation. The agent accepted and recorded it, while fresh remote corroboration of the Mendeley page and publication DOI returned proxy CONNECT HTTP 403. The local original `MPEA_parsed_mechanical_database.xlsx` is 282828 bytes and matches the previously recovered Git blob `8dfa71562a028c9a8dfab9ca47e4079dcef65adf`. SHA-256 `ba34522f472520f3dd6114f5e3fbddb139b7dba5414b153e6476fe3153f5f25f`, MD5 `c85db7af18b64a20e0d6cffc8eb09f49`. No source-provided official file checksum was freshly retrieved, and that distinction remains recorded in `data/additional/mpea_official_provenance_v3.json`. No additional request for dataset-level provenance is needed.

## G1b — prioritized scientific qualification

The eight highest-coverage citation groups account for **123 /457 (26.9%)** numeric paired rows. Selection is by record contribution, not optimization performance; this is an efficient initial review panel, not a statistical claim of representativeness. It includes the conflicting-case source. Review/data-compilation citations must lead to the underlying original tests rather than being treated as independent experimental studies.

| Priority | Source DOI | Paired records | Cumulative coverage |
|---|---|---:|---:|
| 1 | 10.1016/j.jallcom.2022.163774 | 36 | 7.9% |
| 2 | 10.1016/j.pmatsci.2021.100777 | 20 | 12.3% |
| 3 | 10.1016/j.dib.2018.11.111 | 19 | 16.4% |
| 4 | 10.1016/j.jallcom.2021.162907 | 12 | 19.0% |
| 5 | 10.1016/j.intermet.2015.01.004 | 11 | 21.4% |
| 6 | 10.1016/j.msea.2023.144677 | 9 | 23.4% |
| 7 | 10.1007/s11837-012-0366-5 | 8 | 25.2% |
| 8 | 10.1016/j.intermet.2016.09.003 | 8 | 26.9% |

No primary full text was available locally. Official publication access remains proxy-blocked; these papers are marked **not retrieved**, not falsely recorded as reviewed. The largest source alone contributes 36 rows (21 provisionally >=10%, 15 below); source review may establish a useful limited cohort without reviewing all 135 citations. Whether those rows are compatible independent tensile cases remains to be established. A one-study cohort would not support study-disjoint calibration and would require that limitation/gate, rather than forcing calibration.

### Record-level classification

| Classification | Records | Interpretation |
|---|---:|---|
| VERIFIED | 0 | No case-level source evidence yet supplied/retrieved |
| CONDITION_UNCERTAIN | 453 | Numeric paired values, unresolved test temperature/material-state identity |
| CONFLICTING | 4 | Two unresolved case-identity groups, preserved for source resolution |
| EXCLUDED | 1256 | No valid numeric yield/elongation pair for this objective; not a claim all other properties are invalid |

The source-verified primary cohort file exists with its schema but **zero cases**, so primary independent-class counts are **0 verified feasible /0 verified infeasible**, not a claim that all experimental records fail screening. Effective independence among the uncertain rows remains unknown. The secondary software input has **453 provisional rows (339 >=10%, 114 below)**. It is not described as a controlled room-temperature benchmark. No temperatures, replicate identities or processing states were invented.

The previously identified `AlCoCrFeNi2.1` / `50μm/s` / `10.1016/j.jallcom.2021.162907` rows at Excel 511 and 516 report (423 MPa,23.7%) and (431 MPa,13%). Source evidence is needed to decide distinct conditions versus replicates; both are preserved. DOI normalization also connects `CoCrFeMn`, source `10.1016/j.intermet.2016.09.003`, Excel 670 and 1531: both report (338 MPa,4.3%) but represent an unresolved duplicate/identity question. These are not falsely described as discordant measurements. All four remain in the record audit and raw data, rather than arbitrary averaging or deletion.

`record_qualification.csv` preserves reasons, references, original Excel rows, processing notes, target values and uncertainty flags. `primary_cohort.csv` and `secondary_provisional_cohort.csv` are independent, traceable derivatives. The original GE and prior qualification artifacts are unchanged.

### Evidence annotations and independent cases

`data/additional/annotations/record_evidence_v3.csv` is the explicit review interface. An accepted VERIFIED record requires matching study DOI, evidence URL/locator/excerpt/reviewer, tensile loading, measured 20–30 °C test temperature, documented atomic composition basis, identified processing state, experimental rather than simulated values, and same-material-state target pairing. Unknown temperature is not assumed room temperature, and processing temperatures are not relabeled test temperatures. Accepted annotations are traceable reviewer statements, not automated proof that a URL's content has been read.

Repeated annotated composition–processing–study–temperature identities are quarantined until a source-justified replicate protocol exists; all raw measurements are kept. Rounded chemical vectors and DOI links define conservative study/chemistry overlap components for cross-fitting and shift splits. This prevents the same known study or reported chemistry from crossing heldout groups, but does not by itself prove physical independence. Measured phases, FCC/BCC/HCP/IM, hardness, UTS, compressive properties and source ID are excluded from predictors. Planned processing descriptors can be added only after pre-experiment availability is verified; current models use reported element coordinates only.

## G2–G4 — executable MPa pipeline and software evidence

Separate package `src/alloyguard_strength/` leaves frozen GE runtime source intact. `Candidate` holds only ID, reported composition features, leakage group and feature-status metadata; revealed `Observation` holds outcomes. The replay-owned private oracle is never passed to policies. Outcome units are explicit MPa and elongation percent, not renamed hardness or ordinal screening ranks. This is an architectural accident-prevention boundary, not an adversarial Python sandbox.

Strength: observed-only StandardScaler and target mean/scale (floor 50 MPa), constant-amplitude Matérn-5/2 GPR, bounded signal optimization (amplitude [0.1,10], length [0.3,6]), max 60 L-BFGS-B iterations, assumed 25 MPa observational noise. Latent variance feeds EI; noisy-observation variance adds 25² for intervals/NLL. These are development defaults, not a validated noise law or frozen final methodology. Feasibility: observed-only Matérn-5/2 Laplace GPC, length 2, with explicit Beta(1,1) empirical-prior fallback for one class. Imbalance is retained, not artificially reweighted.

Temperature: observed-only three-fold StratifiedGroupKFold by conservative study/chemistry component. At least 20 observations, five of each class and three observed groups per class are required; every train and validation fold must contain both classes. Each fold refits preprocessing/classification. T in [1/3,3], mean OOF log loss +0.05·log(T)² regularization. Identity plus explicit reason on insufficient support. Fold IDs/groups, fit status and warnings are logged. Final dataset calibration support also requires 15 qualified cases per class and at least three groups per class; otherwise the final freeze would explicitly disable calibration.

Four policies: uniform seeded random; strength-only latent EI; ordinary CBO (EI·p_raw); RC-CBO (EI·p_cal), with matched models/preprocessing and exhaustive finite-pool scoring. Constrained policies use best observed feasible strength, or probability plus 0.05·normalized nearest-observed distance before any feasible incumbent. Multiplying EI by a separately modeled feasibility probability is a factorization approximation, not exact correlated-outcome constrained EI.

**72 tests passed**, zero failures/errors/skips. Coverage includes MPa noise decomposition, posterior update, training-only scaling, single-class priors, grouped OOF isolation, calibration activation/identity, EI/risk discount, cold start, deterministic equal-budget replay, hidden-target invariance, duplicate/reveal rejection, valid and invalid group shifts, qualified-cohort guards and source-evidence requirements. Separate synthetic correctness status: **PASSED**; deterministic known strength/elongation functions exercise active grouped calibration without representing synthetic measurements as experiments.

Five-seed provisional software replay: 24 initial rows, three queries per policy, seeds 700–704, four matched policies, **60 selections**. A complete second run matched all deterministic decision/forecast/outcome fields and non-timing metrics. Every recorded observed-ID set and fold group separation was audited. Active calibration software steps: 13; strength optimizer non-successes: 0. These counts test exercised execution paths, not calibration efficacy. Fit warnings/fallbacks are retained. All 20 retained fit warnings report the conservative 0.3 lower length-scale bound. All predictions/acquisitions remain finite and optimizer statuses successful; the bound was not changed based on provisional policy outcomes. This is a small-sample/model-fit limitation to examine on qualified data, not proof of scientific accuracy. An earlier development smoke is separately preserved; current reproducibility refers to `provisional_validation` and `provisional_reproduction` under the same current source hash.

Five plot types (PNG/PDF) were rendered from the provisional trace, each prominently labeled **PROVISIONAL SOFTWARE CHECK — unverified test conditions**. They verify the report pipeline. Their curves are not final scientific figures and are not interpreted as method rankings or physical reliability evidence. Raw provisional metric files exist for reproducibility only; no paired significance or superiority claim is made.

## G5–G8 — scientific freeze and final evaluation pending

`configs/strength_v3/development.yaml` is explicitly **not frozen**. `scripts/freeze_strength_v3.py` refuses to create a final protocol until a sufficient qualified cohort (at least the planned initialization+query budget, both classes), passing tests and G1b exist. Its observed rejection was `CANNOT_FREEZE_G1B_UNRESOLVED`. Final execution independently checks cohort/config/source hashes and requires a frozen scientific mode. No false `benchmark_frozen.yaml` or empty "successful" primary run was created.

The execution/evaluation infrastructure supports matched budgets, best feasible-strength curves/AUC, screening failures, prequential Brier/log loss, strength MAE/NLL/interval coverage, censoring, timings and explicit group-disjoint holdouts. Scientific sensitivity/shift comparisons and uncertainty intervals must wait for a frozen qualified cohort. No final effect size, improvement verdict or physical discovery is reported now.

## Reproducibility and exact remaining action

Use the existing `.venv`, exact unchanged `requirements.lock`, `PYTHONPATH=src`, and one BLAS/OpenMP thread. `scripts/reproduce_strength_v3.sh` rebuilds the case/provenance artifacts, tests, synthetic verification, paired provisional executions, software audit and labeled plots under new output directories. It does not run/freeze primary science. See README for commands.

The saved network draft now includes `data.mendeley.com`, `www.sciencedirect.com`, and `linkinghub.elsevier.com`, preserving the earlier DOI/Crossref/publication domains. Saving did not apply or publish settings; a fresh runtime status still showed no applied custom domains. **Apply the saved source-access settings, or provide methods/table evidence for prioritized studies—starting with the 36-record source `10.1016/j.jallcom.2022.163774` and the conflicting-key source.** No further dataset provenance/license request is needed, no credential is needed for public access, and no indiscriminate 135-study review is required before development continues.

After source evidence establishes a defensible cohort, rerun qualification, freeze primary input/config/preprocessing/model rules, and run final matched real-data experiments. If support is too small for study-aware calibration, document/disable it and retain defensible lower-claim comparisons. Until then, the remaining blocker is access to scientific test-condition evidence; software development and correctness are no longer blocked by that gate.
