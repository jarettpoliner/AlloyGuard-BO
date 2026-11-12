# AlloyGuard-BO: scientific decision and campaign value

**Recommendation A: finalize AlloyGuard-BO for publication as a reproducible benchmark with negative and trade-off results. Do not start another algorithm campaign on this cohort.** Risk-aware selection has conditional practical value when avoiding failed experiments is sufficiently important, but neither risk method is established as broadly superior. This report is a post hoc interpretation of frozen results; it changes no method, protocol, or original verdict and does not publish anything externally.

## What v1/v2 established

All methods use 30 matched initializations, 12 initial cases and 15 additional experiments. Intervals below are paired, unadjusted 95% t intervals over replay seeds. They quantify initialization variability on this fixed cohort—not independent materials, studies, or population generalization. AUC rewards earlier discovery of confirmed feasible strength.

| Policy | Mean discovery AUC | Mean failures | ΔAUC vs CBO [95% interval] | Δfailures vs CBO [95% interval] |
|---|---:|---:|---|---|
| random | 13,023.16 | 4.300 | -962.41 [-2,026.12, 101.30] | -0.97 [-2.15, 0.21] |
| strength_bo | 13,332.68 | 7.167 | -652.89 [-1,231.94, -73.84] | 1.90 [0.73, 3.07] |
| cbo | 13,985.57 | 5.267 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| rc_cbo | 13,978.82 | 5.233 | -6.75 [-52.61, 39.11] | -0.03 [-0.24, 0.17] |
| risk_threshold | 12,043.20 | 3.267 | -1,942.37 [-2,799.81, -1,084.94] | -2.00 [-2.92, -1.08] |
| risk_budget | 12,055.10 | 3.267 | -1,930.47 [-2,777.88, -1,083.07] | -2.00 [-2.92, -1.08] |
| cd_cbo | 13,013.30 | 6.500 | -972.27 [-1,643.08, -301.47] | 1.23 [0.33, 2.14] |
| cd_risk_threshold | 12,544.49 | 3.733 | -1,441.08 [-2,202.77, -679.39] | -1.53 [-2.40, -0.67] |

Ordinary CBO has the highest mean discovery AUC. Its advantage over random is uncertain (AUC interval includes zero), so “best mean” is not proof of universal superiority. It improves both AUC and failures over strength-only BO within conditional paired intervals. Reliability calibration remains indistinguishable from CBO. The risk policies save 2.00 failures per campaign (38.0%) while losing approximately 1,930–1,942 AUC units (13.8–13.9%); both effects have paired intervals excluding zero. This is a measurable trade-off, not the originally sought nearly free safety improvement. The original negative joint-goal verdicts remain valid.

**Mean Pareto frontier:** risk-budget BO, CD-risk-threshold, random, reliability-calibrated CBO, ordinary CBO. Strength-only BO is dominated by ordinary/calibrated CBO; CD-CBO is dominated by random and ordinary/calibrated CBO. Risk-threshold is technically dominated by risk-budget at the observed means, but this last dominance is too small to interpret as a reliable algorithm difference. Mean dominance is descriptive, not simultaneous statistical dominance.

**The two binary risk policies are not meaningfully distinguished here.** They choose the same case at 435/450 matched steps and differ only in seeds 6 and 15. Risk-budget minus risk-threshold AUC is +11.90 [−12.44, 36.24]; failure counts and final feasible strength are identical in every seed. Zero observed failure-difference variance is not proof of population equivalence. Fallback occurs at 442/450 and 441/450 selections: the .75 predicted-feasibility requirement is usually unattainable, so both mostly select minimum predicted risk. This benchmark barely exercises a genuinely distinct budget-allocation mechanism. All risk-budget runs exceed their predicted 3.75 allocation, despite fewer actual failures; it is not a hard safety guarantee.

## Does retaining continuous ductility help?

Not with the tested specification. On identical CBO histories and queried cases, continuous-model Brier is 0.2693 versus binary 0.2220; paired difference +0.0473 [0.0216, 0.0730]. Log loss increases by 0.2572 [0.1490, 0.3655], and pooled ROC AUC falls from 0.6786 to 0.5613. In the measured 5–15% elongation band, Brier worsens from 0.2926 to 0.4897. On random histories continuous Brier is modestly lower but its paired interval crosses zero, while log loss is worse. Thus the negative prediction result is not solely caused by CD-CBO selecting different cases.

CD-CBO’s nominal 95% ductility intervals cover only 78.4%; standardized log residual SD is 1.83 rather than 1. These observations support misspecified uncertainty, with consequential confident errors. Plausible contributors are fixed log-response noise, heteroscedastic literature measurements, sparse composition coverage, missing processing inputs, and a Gaussian log-response approximation that does not remove skewness. Kernel-bound warnings persist. These are supported limitations, not a causal identification of which change would fix them. Modeling magnitude is not inherently worse: this particular continuous model failed. Strength–ductility independence in product CEI is another untested approximation.

## Cost-sensitive campaign value

Use **U = AUC − λ × failures**, with λ set externally by the experimental decision-maker. AUC has units MPa × experiment steps; λ therefore has units MPa × steps per failed experiment. It is a preference conversion, not money, profit, or physical yield. A failure already consumes a query and can reduce AUC; the additional penalty represents extra aversion/cost beyond that opportunity loss. Equal successful-experiment costs and shared initialization costs cancel at a fixed budget. Different durations, unequal assay costs, catastrophic failures, and terminal-value preferences are not represented.

The transparent illustrative grid is λ = 0, 50, …, 5,000, with no penalty chosen or optimized from outcomes. Negative utilities at large penalties are permissible under this arbitrary zero. At 15 steps, λ≈965 means accepting approximately 64.35 MPa less *average incumbent strength over those steps* per avoided failure; this is not the loss of final strength or a currency conversion.

For a policy with positive mean failures saved, break-even against CBO is (mean AUC lost)/(mean failures saved). The 15-step estimates and paired Fieller 95% ratio sets are:

| Policy | Break-even λ vs CBO | Fieller 95% set |
|---|---:|---|
| risk_threshold | 971.19 | [522.99, 1,841.66] |
| risk_budget | 965.24 | [522.86, 1,824.52] |
| cd_risk_threshold | 939.83 | [381.04, 2,449.14] |

These wide intervals reflect uncertain benefit-to-cost ratios. Random’s point crossover is 995.60 but its failures-saved interval includes zero and its Fieller set contains every nonnegative λ; there is no localized break-even estimate supported by these data. The calibrated-CBO crossover at 202.50 is driven by a negligible 0.0333 failures/run difference and has an all-real Fieller set. Neither should be treated as a reliable operational threshold.

| External λ | Risk-budget utility difference vs CBO [95% interval] |
|---:|---|
| 0 | -1,930.47 [-2,777.88, -1,083.07] |
| 500 | -930.47 [-1,808.13, -52.82] |
| 1,000 | 69.53 [-1,046.52, 1,185.57] |
| 1,500 | 1,069.53 [-394.70, 2,533.75] |
| 2,000 | 2,069.53 [207.96, 3,931.10] |
| 3,000 | 4,069.53 [1,353.33, 6,785.73] |
| 5,000 | 8,069.53 [3,566.24, 12,572.81] |

At λ=1,000 the mean preference just flips but uncertainty is large. At externally chosen λ=2,000 the risk-budget benefit is +2,069.53 [207.96, 3,931.10], and risk-threshold is +2,057.63 [187.80, 3,927.46]. This supports conditional practical value against ordinary CBO on this cohort. It does not establish superiority to every policy or justify choosing λ=2,000 because its interval excludes zero. Intervals are pointwise, not simultaneous across penalties/comparisons; the analysis is post hoc.

The empirical all-policy utility envelope at 15 steps is CBO for λ<202.50, calibrated CBO from 202.50–956.22, CD-risk-threshold from 956.22–1,048.70, and risk-budget above 1,048.70 (ties at boundaries). This is a descriptive geometry of mean lines, not a recommendation to switch algorithms at precisely these values. Random is Pareto-nondominated yet never maximizes this linear mean utility at 15 steps: nondominated points need not be supported by a linear objective. The narrow CD/calibration regions are not evidence of algorithmic improvement. All pairwise utility intervals at round penalties are supplied separately.

## Campaign-budget sensitivity

| Additional-query prefix | Risk-threshold break-even vs CBO | Risk-budget break-even vs CBO | Empirical mean-utility envelope |
|---:|---:|---:|---|
| 5 | 340.68 | 329.32 | cbo 0.0–329.3; risk_budget 329.3–∞ |
| 10 | 675.28 | 652.84 | cbo 0.0–434.4; random 434.4–1347.8; risk_budget 1347.8–∞ |
| 15 | 971.19 | 965.24 | cbo 0.0–202.5; rc_cbo 202.5–956.2; cd_risk_threshold 956.2–1048.7; risk_budget 1048.7–∞ |

These are the first 5/10/15 decisions from the frozen 15-query campaigns, not fresh horizon-aware evaluations. In particular, risk-budget still planned for 15 steps; a newly budgeted 5-step policy might behave differently and has not been tested. Absolute AUC scales with horizon, so λ thresholds cannot be transferred unchanged to a different definition such as mean AUC or terminal strength. Paired uncertainty at every prefix/penalty is in the CSVs and plots. No extrapolation beyond 15 queries is supported.

## Can this benchmark distinguish better methods?

Feasibility is common: 58/80 cases (72.5%) pass. Uniform sampling expects 4.125 failures in 15 queries; the observed 30-seed mean is 4.30. With 12 uniform initial cases, the exact chance of no feasible incumbent is only 1.07×10⁻⁸. The benchmark consequently offers almost no test of cold-start feasibility discovery. Risk-budget saves only 1.03 failures relative to random, versus 2.00 relative to CBO; its practical increment should not be framed only against the riskier acquisition baseline.

The mean initial incumbent is 792.76 MPa. Holding it unchanged throughout would already account for 85.0% of CBO’s mean AUC. Therefore AUC retention can obscure weak *incremental* discovery, and a 98% retention target is not equivalent to retaining 98% of newly acquired value. Yet CBO achieves only 80.7% of the unattainable “best 1,155 MPa alloy known from step zero” ceiling: high feasibility does not establish that CBO is optimal or that improvement is impossible.

The 80 cases represent 68 chemistries, 36 studies and 31 connected study-or-chemistry components, not 80 proven independent experiments. Sixteen components are singletons; the largest contains 9 cases. The concentration count (Σn)²/Σn² is 18.6 components (22.7 by study), under a perfect-within-group-correlation analogy—not an estimated effective statistical sample size. Residual dependence across components is unknown. Ambiguous repeated composition/recipe records were excluded in v1 (159 records); this avoids treating ambiguous duplicates as independent but narrows representativeness. Remaining recipes do not fully control treatment details, strain rate, or measurement uncertainty. Sixty-three cases have possible overlap with earlier software-development data, so this is not pristine external validation.

Grouped stress tests retain only 15–34 target cases, one fold exhausts all 15, and another has 30/34 feasible cases with incumbent-dominated AUC. They demonstrate execution under group shift, not robust cross-dataset generalization. The paired design can expose large conditional losses (as it did for risk and CD-CBO), but cannot resolve small calibration/risk-policy differences or establish stable rankings across new alloys. More replay seeds could reduce conditional Monte Carlo uncertainty; they do not add independent measurements. Formal population power or a true effective sample size cannot be recovered from these replays alone.

## Decision and conditions for a materially stronger v3

**Choose A now.** Publish the reproducible benchmark, source qualification, leakage controls, negative calibration/continuous-model results, and explicit safety–discovery frontier. Useful claims are that constrained acquisition improves over unconstrained strength search in this replay, stricter risk preferences buy fewer failures at appreciable discovery cost, and predictive magnitude or calibration alone does not guarantee better decisions. Unsupported claims include universal CBO superiority, hard safety control, superiority of risk budgeting over thresholding, independent-dataset generalization, or economic savings.

Risk-aware policies have preference-dependent value, especially when externally justified failure penalties are high. The present evidence favors describing a minimum-predicted-risk versus discovery trade-off, not crediting a sophisticated risk-budget mechanism. Retain both published implementations/results, but do not promote one based on their tiny difference.

A future B would be justified only as a separately preregistered project with a materially stronger basis: a source-disjoint independent dataset or prospective campaign; development-only model/noise/threshold selection; study/process-aware validation; sufficient infeasible and near-threshold measurements; and external elicitation of failure costs and campaign horizon before testing. A specific hypothesis worth investigating on development data is that validated heteroscedastic ductility uncertainty plus recorded processing conditions reduces confidently wrong feasibility predictions. The current logs motivate that hypothesis but do not validate a replacement model. An alternative genuinely different objective—e.g. measured assay cost and terminal feasible strength—requires real cost information and an independent evaluation, not a retrospective metric chosen to rescue these results.

Further algorithm selection on this same exposed cohort would introduce researcher selection bias even with new seeds. This utility analysis does not retroactively validate either v2 policy or revise its frozen goals. No v3 method was implemented and no original artifact was overwritten.

## Evidence and reproduction

Run from the repository: `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLCONFIGDIR="$PWD/.matplotlib-cache" .venv/bin/python scripts/review_campaign_value.py`.

Inputs: `results/v2/evaluation/primary/{metrics.csv,curves.csv,traces.jsonl}`, frozen v1 results, qualified cohort, v2 model/common-history diagnostics. Outputs here: `summary.csv` (means and intervals), `all_paired_differences.csv` (all policy pairs), `break_even.json` (ratio sets), `utility_curves.csv`, `all_paired_utility_anchors.csv`, `pareto_and_utility_envelope.json`, `cohort_and_distinguishability.json`, and `preservation.json`. Utility plots are PNG/PDF. Budget metrics are recomputed from decision curves and checked against frozen 15-step summaries. The original v1/v2 baseline equality is verified. No model fitting or experimental rerun is needed.
