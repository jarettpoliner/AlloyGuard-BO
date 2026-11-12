# AlloyGuard-BO: A Reliability Layer for Experimental Alloy Selection

**Status:** Pre-implementation research specification, 11 November 2026  
**Scope:** One-week, CPU-runnable, reproducible retrospective experiment using public refractory-alloy data  
**Proposed repository:** `alloyguard-bo`  
**Central claim to test:** Laboratory-calibrated feasibility probabilities can reduce wasted experimental selections and improve the rate of discovering hard, sufficiently ductile refractory alloys compared with hardness-only Bayesian optimization.

## 0. Epistemic limits and research fit

Radical AI reports (i) a computation-to-laboratory throughput imbalance, (ii) physics/model corrections informed by more than 500 hardness measurements, and (iii) a separate electronic-materials campaign in which two samples were too brittle to prepare for characterization. Radical also reports simulating ductility using its internal EGIP/physics workflow, so **the new idea is not simply to add ductility as another predicted property**. The defensible demonstrator is a *decision-level reliability layer* connecting uncertain, empirically evaluated feasibility to candidate selection.

The GE public dataset does **not** include paired Radical simulation-versus-laboratory hardness values; it therefore cannot validate a true simulation-discrepancy model, EGIP, Maresca–Curtin, manufacturing success probability, or actual Radical system performance. It **does** include measured hardness, observed 0–5 ductility screening ranks, alloy composition, and a precomputed Thermo-Calc solidus estimate. It supports a finite-pool laboratory-outcome replay with a learned mechanical-feasibility constraint.

The project is a rigorous application/benchmark of existing methods, not a claim to invent constrained BO. Its publishable-grade value is careful evaluation of uncertainty calibration, sparse feedback, and decision quality, including negative results.

## 1. Frozen scientific problem

### Design space

Each tested composition is represented by atomic fractions

`x = (c_Hf, c_Mo, c_Nb, c_Re, c_Ru, c_Ta, c_Ti, c_W, c_Zr)`, where all fractions are nonnegative and sum approximately to 1.

The public dataset contains 86 records describing 82 unique experimentally synthesized refractory alloys. All samples were investigated in an as-arc-melted condition, with no later heat treatments. Preserve as-reported hardness units (GPa), ductility ranks, and predicted solidus temperatures (°C).

### Property objective and constraint

- **Objective:** maximize experimentally observed room-temperature microhardness `H(x)` in GPa.
- **Feasibility:** the predeclared screening threshold `F(x) = 1[D(x) >= 3]`, where `D` is the experimental *ordinal* ductility rank 0–5. Rank >=3 is an operational threshold for the demonstrator, not a validated universal brittleness limit. Audit class counts before freezing the threshold.
- **Optional known screening constraint:** predicted Thermo-Calc solidus temperature meets a specified temperature requirement, provided the dataset has sufficient candidate coverage. Do not silently mix Kelvin and Celsius. Do not use the solidus threshold simply to engineer an algorithmic win. An experimentally determined melting temperature is *not* available here.

**Single decision at each round:** choose the composition to synthesize/test next among an unlabeled, fixed pool of actually tested alloys. When its hidden outcome is revealed, the learner receives its measured hardness and ductility rank. There are no process-choice or measurement-choice actions in the principal benchmark, because the dataset cannot support a trustworthy benchmark of those choices.

### Null and alternative hypotheses

- **H0:** Explicit feasibility modeling/calibration does not improve laboratory-confirmed hardness discovery under equal experimental budgets versus hardness-only BO or ordinary constrained BO.
- **H1:** A reliability-aware constrained BO policy improves at least one prespecified decision-quality outcome (feasible hardness discovery, failure avoidance, or time to first feasible candidate) without unacceptable deterioration in the others.

We will report all outcomes; no win is assumed.

## 2. One integrated model, not a family of speculative architectures

**Name:** Reliability-Calibrated Constrained Bayesian Optimization (RC-CBO).

The implementation has two observation heads because hardness and feasibility are different empirical measurements, but it is **one** joint experimental decision system.

### 2.1 Shared input representation

Main model: nine fractional composition coordinates. Fit preprocessing only on observed training compositions. A small, frozen, physics-derived feature option can be tested as an ablation, but not used to tune against future hidden outcomes. Candidate features include weighted mean atomic radius, atomic-radius mismatch, valence electron concentration, and configurational mixing entropy; all elemental metadata must be sourced and versioned. Keep dimensionality small to avoid overfit with ~82 alloys.

Avoid an unqualified centered log-ratio transformation because many compositions have exactly zero elemental fractions. Do not treat one-hot alloy names as physics features. Dataset-wide *unlabeled* composition geometry may be used for space-filling initialization, but experimental target columns may not influence this initialization.

### 2.2 Hardness head: Gaussian-process regression

`H(x) | D_t ~ Normal(mu_H,t(x), sigma_H,t^2(x))`.

Fit a regularized Matérn-5/2 GP to measured hardness, with observation noise inferred from the training set and a conservative noise floor. Fit/scaling are performed afresh using observed data at each step. Exact duplicated composition entries are never split across training and candidate sides; treat duplicate rows as repeat measurements with documented aggregation or a consistent replicate-noise treatment.

Do not claim that a physical prior exists unless an actual independent low-fidelity hardness predictor is implemented and validated. The Thermo-Calc solidus is a *different physical quantity*, not a low-fidelity hardness label.

### 2.3 Feasibility head: Gaussian-process classification

`p_t(x) = P(D(x) >= 3 | observed data)`.

Use a GP classifier (Laplace approximation with Matérn kernel) for the binary *decision event*. Retain original 0–5 ranks in the stored data and analysis, even though the prespecified decision is binary; rank information is not silently treated as continuous ground truth.

Record class imbalance, discrimination (ROC-AUC only when both classes are present), proper scoring (Brier/log loss), and calibration diagnostics. If labels are nearly all feasible or infeasible, flag that the benchmark lacks statistical support for the chosen constraint and apply the predefined feasibility gate below; do not change thresholds to make RC-CBO win.

### 2.4 Calibration: one small-data correction, not a deep model

Post-hoc one-parameter temperature scaling of GP class probabilities, fitted **only** on grouped, out-of-fold predictions from the *currently observed* training set. Compare against the uncalibrated GP probabilities as an ablation. Regularize temperature towards 1; avoid fitting an unstable calibrator early in the campaign. Activate calibration only when predeclared minimum data/class-support conditions hold; otherwise use the GP classifier unchanged and log a `CALIBRATION_INSUFFICIENT_DATA` status.

Calibration trained on random row splits with duplicate compositions leaked across folds is invalid. Calibration on the entire 82-alloy table before replay is invalid. A low Brier score does not by itself imply robust out-of-distribution probabilities.

### 2.5 Decision policy

Define observed feasible incumbent:

`h_best,t = max{observed H(x_i) : D(x_i) >= 3}`.

For a candidate `x`, compute expected improvement in *latent true hardness* rather than taking posterior measurement noise as exploitable improvement:

`EI_t(x) = (mu_H(x)-h_best,t) Phi(z) + sigma_H(x) phi(z)`, `z=(mu_H(x)-h_best,t)/sigma_H(x)`.

The RC-CBO acquisition is:

`alpha_RC(x) = EI_t(x) * p_cal,t(x)`.

This factorization assumes conditional independence of hardness and feasibility given x and the fitted heads; it is an approximation, not a universal equality. The limitation should be explicit. Evaluate in log-space or with stable numerical primitives. For the finite candidate pool, score every unobserved candidate and choose `argmax` rather than performing an unnecessary continuous optimizer.

**No feasible incumbent yet:** do not pass an undefined `h_best` into EI. Use a documented feasibility-search mode combining `p_t(x)` and a small exploration incentive; define its coefficient before outcome comparisons and keep it identical across algorithms where applicable. Log the switch from feasibility search to feasible-improvement search.

**Optional scientific safety policy:** a documented minimum calibrated `P(feasible)` for proposing deployment, separate from the offline optimizer score. A candidate outside model support may be marked `NEEDS_HUMAN_REVIEW`, not declared objectively infeasible.

### 2.6 Output contract

For a selected candidate, store: composition and units; predicted hardness mean/interval; GP probability of feasible ductility; calibrated probability; EI; constrained EI; distance to observed chemistry; active constraints; uncertainty/calibration status; why selected; prior dataset IDs; model/config versions; and action `SELECT_NEXT_ALLOY` or `REVIEW_REQUIRED`. Outcomes may be `PASS`, `FAIL`, or `INCONCLUSIVE` with reason codes; do not overwrite failures with successes or drop observations.

## 3. Data preparation and validity gates (Day 1)

Download the primary CSV from the Figshare record associated with Detor et al. (2022): https://doi.org/10.6084/m9.figshare.17032760.v1. Record the exact file, source URL, SHA-256, citation, and any licensing notes.

Audit and write machine-readable results for:

1. Header spelling, missingness, types, units, extreme values.
2. Row count (published 86), composition key uniqueness (published 82), and duplicate-replicate variance.
3. Composition sum tolerance, allowed nine elements, nonnegativity, fractional scaling, and at% to fraction conversion.
4. Histograms/counts of ranks 0–5; `D >= 3` feasible fraction; hardness range by feasibility and chemistry; predicted solidus distribution.
5. Whether there are enough positive/negative examples to fit and evaluate feasibility reliably. **Feasibility gate:** preferably >=15 of each class; if not, record an explicit limitation and use only an upfront, science-justified alternative threshold as a secondary analysis. Never select a threshold according to which BO method wins.
6. The data-generating process: only successfully synthesized/tested alloys are represented; the publication notes unsuccessful melting attempts are excluded. Hence the classifier does not model failed synthesis of arbitrary candidates.

All outcome-based inspection to set rules is documented before benchmark runs, with a frozen config artifact. The CSV's actual contents were not inspected at planning time; the published article established the schema, not the exact class counts.

## 4. Benchmark protocol

### 4.1 In-distribution finite-pool replay (primary)

- Pool = all **unique composition groups** with available hardness/ductility; each group is either entirely observed or entirely hidden from the policy.
- Initialize from 12 composition groups chosen by an **outcome-blind** space-filling or fixed seeded random design. For 30–50 independent seeds, all strategies use the *identical* starting compositions and candidate pool.
- Each method receives only experimental outcomes already revealed in its own replay.
- At each iteration, fit its models to its own revealed data; select exactly one unseen composition; reveal actual published outcome; update; continue for a predeclared 15–20-query budget.
- A shared pool is not an unlimited generative candidate engine. This tests *which known, previously measured composition would be selected next if its label were hidden*, not actual untested chemical discovery.
- Report paired seed-level uncertainty intervals; avoid interpreting overlapping repeated-replay observations as statistically independent experiments.

### 4.2 Strategies to compare (same budget)

A. Random unobserved candidate.  
B. Hardness-only Matérn GP + EI.  
C. Ordinary constrained BO = same hardness GP, same feasibility GPC, raw `p_t`, product acquisition.  
D. **RC-CBO (proposed)** = model C plus calibrated feasibility probabilities.

An additional simple physically motivated ranking (e.g. known-solidus filter then highest predicted hardness) is optional, not required for core completion.

Keep the base GP models, optimizer, initialization and noise assumptions matched between C and D. This isolates the contribution of calibration. Do not compare against a deliberately poor baseline.

### 4.3 Family-shift stress test (secondary, clearly labeled)

Define held-out chemistry families from composition **only** (e.g. presence of a sufficiently common element or predeclared unsupervised clusters). Verify each held-out group is large enough before using it as a target pool. Train initially outside the group, then sequentially select from that group and disclose its outcomes. No outcome-dependent cluster selection. The experiment tests sensitivity to covariate shift, but with only ~82 compositions cannot establish general robustness to new alloy systems.

### 4.4 Proper evaluation metrics

**Primary**: area under the *best laboratory-confirmed feasible hardness versus number of extra lab evaluations* curve. Use a predeclared convention for no feasible observed candidate, such as 0 GPa until a feasible measurement appears, and report it transparently.

**Secondary**:
- Best observed feasible hardness at query counts 5, 10, 15, and 20 (when budget permits).
- Time to first experimentally feasible candidate and fraction of runs achieving one.
- Number/fraction of queried materials with observed `D < 3`.
- Predicted-feasibility Brier score and log loss on *prequential predictions before labels are revealed*; calibration diagrams with very coarse bins and small-sample uncertainty.
- Hardness MAE/NLL and predictive interval coverage on sequentially observed points, noting adaptively selected samples are not i.i.d.
- Training/retraining time, total runtime, failure/fallback rates.

Do not use final pool labels in any feature fitting, hyperparameter selection, calibration, policy decision, or acquisition optimization. After a run completes, only the evaluator can access those labels to score the predictions.

### 4.5 Scientific acceptance criteria

**Software validity gate** (mandatory): 100% unit/integration tests pass; no duplicate leakage, no hidden-label access, finite valid scores, deterministic seeded replays, tracked configuration, and reproducible reported curves.

**Predictive validity gate**: report both calibration and discriminative performance; do not assert calibrated or OOD-safe based solely on training fit.

**Decision validity gate**: RC-CBO improves the primary metric over C with a paired uncertainty interval that excludes zero, *or* explicitly report failure/inconclusiveness. Do not tune hyperparameters after seeing primary comparison results without marking a new exploratory experiment.

**Scientific interpretation gate**: no claim that the new method outperforms Radical AI's unpublished pipeline; no claim that it solves simulation-to-lab discrepancy with this dataset; no claim of synthesis-failure prediction from data conditional on successful synthesis.

## 5. Synthetic software-verification test (not a scientific result)

Define a fully synthetic, known smooth hardness function over low-dimensional simplex coordinates, a feasibility boundary, and a deliberately biased cheap predictor. Include deterministic fixed-seed noise. Use only for tests:
- posterior update changes after revealing a measurement;
- score is finite, nonnegative, reproducible;
- a known infeasible high-hardness region is appropriately discounted;
- policy handles zero feasible incumbents;
- label masking prevents outcome leakage;
- duplicate composition groups never straddle training and pool.

Synthetic success is a *correctness check*, not evidence of performance on Radical or real laboratory campaigns.

## 6. Code architecture and interfaces

```
alloyguard-bo/
  README.md
  CITATION.cff
  LICENSE
  pyproject.toml
  configs/
    base.yaml
    benchmark_frozen.yaml
  data/
    README.md
    raw/                 # optional, follow source license
    processed/           # generated, hashes
  src/alloyguard/
    data.py              # provenance, schema, grouping
    features.py          # leakage-safe composition/physics features
    surrogates.py        # hardness GP, GP feasibility classifier
    calibration.py       # cross-fit temperature scaling
    acquisition.py       # stable EI, constrained EI, cold-start
    replay.py            # strict observed/hidden oracle boundary
    policies.py          # matched A/B/C/D policies
    metrics.py           # primary + secondary metrics
    report.py            # artifacts/plots
    schema.py            # model prediction + decision contract
  scripts/
    download_data.py
    audit_data.py
    run_replay.py
    make_report.py
  tests/
    test_dataset_integrity.py
    test_masking_and_splits.py
    test_acquisition.py
    test_cold_start.py
    test_calibration_no_leak.py
    test_replay_deterministic.py
    test_synthetic_oracle.py
  results/
    audit.json
    frozen_config.yaml
    traces.parquet
    metrics.csv
    figures/
    report.md
```

**Core typed interfaces:**

```
Observation = {
  alloy_id: str,
  composition_at_frac: float[9],
  hardness_gpa: float | None,
  ductility_rank: int | None,
  predicted_solidus_c: float | None,
  observed_at_step: int | None
}

Prediction = {
  hardness_mean_gpa: float,
  hardness_sd_gpa: float,
  feasible_probability_raw: float,
  feasible_probability_calibrated: float,
  calibration_status: str,
  feature_shift_score: float
}

Decision = {
  composition_id: str,
  acquisition_score: float,
  estimated_improvement_gpa: float,
  predicted_feasibility: float,
  policy_id: str,
  dataset_hash: str,
  model_config_hash: str,
  step: int,
  rationale: str
}
```

Fit transformation statistics only on revealed training records; preserve optional input units. Serialize policy settings and outputs deterministically. In the replay, the policy never gets a reference to `oracle_outcomes`.

### Engineering stack

Python 3.11+, NumPy, pandas, scipy, scikit-learn (`GaussianProcessRegressor`, `GaussianProcessClassifier`), matplotlib, pytest, PyYAML, and optionally BoTorch for numerical cross-checks. CPU is sufficient. Pin exact package versions in lockfile; set numpy/sklearn seeds and BLAS concurrency in benchmark runner. Because the finite pool is tiny, evaluate acquisition scores exhaustively rather than introducing continuous surrogate search or a neural encoder.

## 7. Seven-day critical path

**Day 1 — Acquire and audit.** Source dataset, hash, duplicate grouping, scientific data cards, class/label distribution, freeze target and primary metric. **STOP** if source is unavailable or class support is too weak; document and switch to a defined lower-claim benchmark rather than fake data.

**Day 2 — Hardness and feasibility models.** Reproducible preprocessing, GP fits, input diagnostics, unit tests, reference property plots.

**Day 3 — Selection policies.** EI and constrained EI, cold start, masked replay engine, deterministic toy oracle, tests for leaking future observations.

**Day 4 — Full primary benchmark.** A/B/C/D across fixed seeds; representative selection traces; primary decision curves. Do not change methodology after looking at the ranking.

**Day 5 — Calibration and ablations.** Implement grouped out-of-fold temperature scaling, verify no hidden-label leakage, repeat matched benchmark, plot prequential calibration and latency.

**Day 6 — Scientific challenge.** Family-shift stress test if supported, replicates/noise sensitivity, failure-case analysis, paired uncertainty summaries, audit all key conclusions.

**Day 7 — Publication-quality repo.** README with one-command reproduction, results tables and figures, `REPORT.md`, caveats, tests/CI, model card, exact provenance. No promotion of surrogate discoveries as new synthesized alloys.

**Do not expand scope:** no LLM embeddings, no generative microstructure model, no neural foundation model, no claimed high-fidelity MD, no dynamic reagent/process optimization, no experiment repeats without suitable provenance, no multi-fidelity lab-vs-simulation model using fabricated paired observations.

## 8. Expected deliverables

1. Dataset audit + source manifest and scientific assumptions.
2. A functional `select_next_alloy()` implementation returning traceable recommendation and uncertainty rationale.
3. Four matched policies with leak-proof sequential replay.
4. Figures: primary best-feasible-hardness discovery curves; failed selections vs budget; prequential calibration plot; characteristic failure case showing why a hardness-only suggestion was unsafe (if actual observations support one).
5. Ablation: same constrained policy before/after calibration; composition-only versus compact physical descriptor features only if source verified.
6. Paired confidence intervals, predeclared acceptance criteria, and explicit negative/inconclusive results.
7. README, unit/integration tests, version-pinned environment, model/deployment contract, and limitations.

## 9. Day-90 upgrade path (not required in week one)

With access to **matched** low-fidelity calculations and lab measurements for the same compositions, add a proper discrepancy model:

`H_lab(x) = rho * H_sim(x) + delta(x) + eps`, where `delta(x)` is a GP over chemistry and process state.

Compare predictive calibration and regret with a simple lab-only GP; consider correlated multi-fidelity BO and diagnostic repeat/characterization actions once true action-specific data and costs become available. Use process and microstructure fields when actually observed. This is the stronger direct test of Radical's disclosed simulation-to-lab mismatch, but cannot honestly be validated by the GE table alone.

## 10. Primary literature and documentation

- Radical AI, *Beyond Composition: Computing What Materials Will Actually Do* (9 March 2026): https://www.radical-ai.com/news/beyond-composition-computing-what-materials-will-actually-do
- Radical AI, *6 Predictions, 6 Validated Materials: Enabling Frontier Electronic Property Materials* (23 September 2026): https://www.radical-ai.com/news/6-predictions-6-validated-materials-enabling-frontier-electronic-property-materials
- Detor, Oppenheimer, Casey & Crawford, *Refractory high entropy alloy dataset with room temperature ductility screening*, Data in Brief 45, 108582 (2022): https://doi.org/10.1016/j.dib.2022.108582 ; dataset: https://doi.org/10.6084/m9.figshare.17032760.v1
- Gardner et al., *Bayesian Optimization with Inequality Constraints*, ICML (2014): https://proceedings.mlr.press/v32/gardner14.html
- Gelbart, Snoek & Adams, *Bayesian Optimization with Unknown Constraints* (2014): https://arxiv.org/abs/1403.5607
- Vela et al., *Data-augmented modeling for yield strength of refractory high entropy alloys: A Bayesian approach*, Acta Materialia (2023): https://doi.org/10.1016/j.actamat.2023.119351
- *Online Calibrated and Conformal Prediction Improves Bayesian Optimization*, AISTATS (2024): https://pmc.ncbi.nlm.nih.gov/articles/PMC11482741/
- BoTorch constrained / log-EI reference: https://botorch.org/docs/v0.17.2/tutorials/closed_loop_botorch_only ; https://botorch.readthedocs.io/en/stable/acquisition.html

## 11. Final scientific rule

This project is successful only if it produces a reproducible, truthful decision-level comparison. If the ordinary constrained BO baseline is just as good, the negative result is the result. If the dataset cannot support stable probability calibration, the scientifically correct outcome is to demonstrate that limitation. Never retrofit the experimental setup to make the proposal win.
