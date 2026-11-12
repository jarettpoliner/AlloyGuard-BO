# AlloyGuard-BO v2: exploratory risk and continuous-ductility experiments

Ordinary CBO has the highest mean discovery AUC (13,985.57 MPa × experiments). All four new branches receive NO CONFIRMED IMPROVEMENT under the frozen joint goals. Binary risk policies cut failures by 37.97% but retain only 86.11–86.20% of AUC; CD-CBO increases failures by 23.42% while retaining 93.05%; CD-threshold reduces failures by 29.11% but retains 89.70%. These are outcomes for fixed untuned settings on a reused cohort, not a rejection of every possible risk or continuous model.

## Scope and frozen decisions

All v1 scientific artifacts remain unchanged. This is a new exploratory analysis of the same 80 published tensile cases, 36 studies and 31 study-or-composition components. There is no independent alloy dataset. Thirty replay seeds are conditional random-initialization replicates, not 30 independent datasets. No parameter search or final-result tuning was used. The exact protocol is `configs/v2/protocol.md`; its hash and all scientific implementation hashes are frozen in `configs/v2/frozen.json` before the first v2 comparative run. Fixed .75 probability threshold, 3.75 predicted-failure budget, log-response noise .15 and scale floor .5 are engineering assumptions, not optimized settings.

## Phase 1: what actually went wrong in v1

CBO selected 158 failures in 450 queries, versus random’s 129. The paired mean difference is +0.9667 failures per replay (95% interval −0.2120 to 2.1454); its AUC advantage is +962.41 (−101.30 to 2026.12). Neither comparison establishes a difference beyond initialization variability on this fixed cohort. CBO outperforms unconstrained strength BO in both paired AUC and failure count in v1; temperature calibration did not confirm improvement.

79.75% of failed CBO selections had predicted feasibility in [.4,.6], and none had probability >=.75. Failed CBO selections had mean predicted strength 867.63 MPa versus 693.75 for successful choices, and mean EI 195.21 versus 98.78 MPa. Multiplying EI by a moderately uncertain feasibility probability does not remove high-strength/high-risk candidates. The measured strength–elongation Spearman correlation is -0.787. These associations support a strength–ductility trade-off explanation; they do not prove causation.

The overconfidence hypothesis is not supported globally: CBO predicted 6.6874 failures per run but observed 5.2667; actual minus predicted failures is −1.4207 (−2.2404 to −0.6010). High probability among failures alone would not establish miscalibration. Probabilities tend toward the boundary and underpredict aggregate feasibility on selected cases. A stricter probability threshold can therefore discard useful candidates even when the classifier is cautious.

| policy | failed_boundary_fraction | failed_mean_probability | mean_predicted_failure | actual_failure |
| --- | --- | --- | --- | --- |
| cbo | 0.7975 | 0.5215 | 0.4458 | 0.3511 |
| random | 0.6899 | 0.5573 | 0.4168 | 0.2867 |
| rc_cbo | 0.7516 | 0.5346 | 0.4258 | 0.3489 |
| strength_bo | 0.9814 | 0.4951 | 0.4963 | 0.4778 |

## Primary numerical comparison

| policy | auc_mpa_evaluations | failure_count | best_feasible_at_15_mpa | brier | log_loss | strength_interval_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| random | 13023.1600 | 4.3000 | 934.8000 | 0.2134 | 0.6185 | 0.8156 |
| strength_bo | 13332.6833 | 7.1667 | 967.3667 | 0.2446 | 0.6823 | 0.8333 |
| cbo | 13985.5733 | 5.2667 | 1017.9333 | 0.2220 | 0.6360 | 0.7644 |
| rc_cbo | 13978.8233 | 5.2333 | 1005.8333 | 0.2192 | 0.6295 | 0.7733 |
| risk_threshold | 12043.2000 | 3.2667 | 815.4267 | 0.1971 | 0.5859 | 0.7756 |
| risk_budget | 12055.1000 | 3.2667 | 815.4267 | 0.1971 | 0.5858 | 0.7756 |
| cd_cbo | 13013.3000 | 6.5000 | 937.4667 | 0.2836 | 0.8258 | 0.8022 |
| cd_risk_threshold | 12544.4933 | 3.7333 | 858.9333 | 0.1913 | 0.6371 | 0.8578 |

All policy and metric mean intervals are in `summary.csv`; paired differences against CBO are in `comparisons.json`. Discovery AUC is MPa × additional experiments, including the initial incumbent at step zero. Failure count excludes the 12 initial measurements. Unadjusted 95% t intervals describe seed variability; they are not population confidence intervals and do not correct multiple comparisons. Brier/log loss on each policy’s own selections compare different selected populations.

## Separate prespecified verdicts

**risk_threshold: NO CONFIRMED IMPROVEMENT.** AUC retention 86.11%; failure reduction 37.97%. Both engineering goals met: False.

AUC − .98×CBO: -1662.66, 95% [-2511.17, -814.15]. Failures − .85×CBO: -1.210, 95% [-1.986, -0.434].

**risk_budget: NO CONFIRMED IMPROVEMENT.** AUC retention 86.20%; failure reduction 37.97%. Both engineering goals met: False.

AUC − .98×CBO: -1650.76, 95% [-2489.24, -812.29]. Failures − .85×CBO: -1.210, 95% [-1.986, -0.434].

**cd_cbo: NO CONFIRMED IMPROVEMENT.** AUC retention 93.05%; failure reduction -23.42%. Both engineering goals met: False.

AUC − .98×CBO: -692.56, 95% [-1351.70, -33.42]. Failures − .85×CBO: 2.023, 95% [1.218, 2.829].

**cd_risk_threshold: NO CONFIRMED IMPROVEMENT.** AUC retention 89.70%; failure reduction 29.11%. Both engineering goals met: False.

AUC − .98×CBO: -1161.37, 95% [-1912.25, -410.49]. Failures − .85×CBO: -0.743, 95% [-1.508, 0.022].

An IMPROVED TRADE-OFF label, if present, means both prespecified point-estimate engineering goals were met; it is not a significance or generalization claim. Failure reduction alone is insufficient. NO CONFIRMED IMPROVEMENT means at least one paired goal interval lies entirely on its failing side. Other outcomes are INCONCLUSIVE. No winning policy is selected for deployment from these results.

## Continuous-response modeling versus risk acquisition

| history | band | model | n | brier | log_loss | roc_auc |
| --- | --- | --- | --- | --- | --- | --- |
| cbo | all | binary | 450 | 0.2220 | 0.6360 | 0.6786 |
| cbo | all | continuous | 450 | 0.2693 | 0.8933 | 0.5613 |
| cbo | near_5_to_15 | binary | 111 | 0.2926 | 0.7810 | 0.3330 |
| cbo | near_5_to_15 | continuous | 111 | 0.4897 | 1.6719 | 0.2507 |
| random | all | binary | 450 | 0.2134 | 0.6185 | 0.6317 |
| random | all | continuous | 450 | 0.1975 | 0.7855 | 0.6404 |
| random | near_5_to_15 | binary | 92 | 0.2813 | 0.7582 | 0.4559 |
| random | near_5_to_15 | continuous | 92 | 0.3687 | 1.3791 | 0.6130 |

The common-history analysis fits both models to the same revealed observations and scores the same 450 ordinary-CBO selections and separately the same 450 random selections. Continuous forecasts are shadow predictions: they cannot affect selection. This controls the selected-case confound. The 5–15% near-boundary band uses measured values only for retrospective scoring. Its sample sizes and seed-wise paired score intervals are in `common_history_paired.json`. Pooled ROC values/reliability bins are descriptive with repeated cases, not independent-test estimates.

The four-way factorial ablation (CBO, threshold CBO, CD-CBO, CD-threshold) holds the strength model and threshold fixed. `factorial_ablations.json` reports model effects, acquisition effects and their interaction with paired intervals. Comparing CD-threshold directly with CBO alone would mix these effects.

## Distributional and model failure audit

The log1p transform does not establish Gaussianity. Raw elongation skewness is 0.637; transformed skewness is -0.838. Marginal skewness is not a test of conditional residual normality; inspect the residual PIT and coverage in the figures. Fixed log noise and constant residual variance can misrepresent heterogeneous literature measurements. Negative inverse-transform mass is censored to zero and reported, not silently discarded. Elongation is nonnegative but has no universal 100% upper bound. The retained cohort falls within the historical v1 Outcome representation; no new data were capped.

| policy | fallback_selections | mean_predicted_risk_spent | mean_realized_failures | budget_overrun_seeds | strength_warnings | feasibility_warnings |
| --- | --- | --- | --- | --- | --- | --- |
| cbo | 0 | 6.6874 | 5.2667 | 30 | 198 | 0 |
| cd_cbo | 0 | 5.5695 | 6.5000 | 27 | 164 | 177 |
| cd_risk_threshold | 56 | 2.6383 | 3.7333 | 0 | 132 | 131 |
| random | 0 | 6.2516 | 4.3000 | 30 | 281 | 0 |
| rc_cbo | 0 | 6.3868 | 5.2333 | 30 | 198 | 0 |
| risk_budget | 442 | 5.0598 | 3.2667 | 30 | 269 | 0 |
| risk_threshold | 441 | 5.0705 | 3.2667 | 30 | 267 | 0 |
| strength_bo | 0 | 7.4441 | 7.1667 | 30 | 190 | 0 |

A budget overrun means no affordable candidate was available under the sequential allowance, so the prespecified minimum-risk fallback continued the equal-budget experiment. Budget accounting is in predicted failure units, not actual outcomes. The budget is a soft allocation rule with explicit violations; it is not a safety guarantee. Values for nonbudget policies are diagnostic comparisons with 3.75, not violations of a policy promise. Model warnings and uncertainty failures are retained in traces and `model_diagnostics.json`.

## Sensitivity and grouped stress tests

| scenario | policy | auc_mpa_evaluations | failure_count | brier |
| --- | --- | --- | --- | --- |
| group_0 | cbo | 14415.0000 | 3.0000 | 0.2072 |
| group_0 | cd_cbo | 14415.0000 | 3.4000 | 0.1920 |
| group_0 | cd_risk_threshold | 14415.0000 | 1.6000 | 0.1004 |
| group_0 | random | 14415.0000 | 1.4000 | 0.1793 |
| group_0 | rc_cbo | 14415.0000 | 3.0000 | 0.1965 |
| group_0 | risk_budget | 14415.0000 | 0.4000 | 0.1305 |
| group_0 | risk_threshold | 14415.0000 | 0.4000 | 0.1305 |
| group_0 | strength_bo | 14415.0000 | 3.2000 | 0.2130 |
| group_1 | cbo | 11430.6600 | 5.0000 | 0.2187 |
| group_1 | cd_cbo | 11752.5400 | 5.0000 | 0.1986 |
| group_1 | cd_risk_threshold | 11506.1400 | 5.0000 | 0.2005 |
| group_1 | random | 11739.5400 | 5.0000 | 0.2211 |
| group_1 | rc_cbo | 11430.6600 | 5.0000 | 0.2107 |
| group_1 | risk_budget | 11383.0600 | 5.0000 | 0.2149 |
| group_1 | risk_threshold | 11383.0600 | 5.0000 | 0.2147 |
| group_1 | strength_bo | 11920.1400 | 5.0000 | 0.2210 |
| group_2 | cbo | 11509.5200 | 6.4000 | 0.2453 |
| group_2 | cd_cbo | 12795.8600 | 7.6000 | 0.3556 |
| group_2 | cd_risk_threshold | 11454.7600 | 6.0000 | 0.2865 |
| group_2 | random | 13418.8800 | 6.0000 | 0.2377 |
| group_2 | rc_cbo | 11509.5200 | 6.6000 | 0.2560 |
| group_2 | risk_budget | 10220.4000 | 4.8000 | 0.2299 |
| group_2 | risk_threshold | 10220.4000 | 4.8000 | 0.2299 |
| group_2 | strength_bo | 12125.4000 | 8.0000 | 0.2477 |
| initial_16 | cbo | 14151.2000 | 6.0000 | 0.2281 |
| initial_16 | cd_cbo | 13561.2000 | 7.0000 | 0.2779 |
| initial_16 | cd_risk_threshold | 12969.0000 | 2.6000 | 0.1506 |
| initial_16 | random | 13404.7000 | 4.4000 | 0.2074 |
| initial_16 | rc_cbo | 14033.6000 | 5.6000 | 0.2162 |
| initial_16 | risk_budget | 12762.0000 | 3.6000 | 0.2015 |
| initial_16 | risk_threshold | 12762.0000 | 3.6000 | 0.2015 |
| initial_16 | strength_bo | 13629.0000 | 6.8000 | 0.2299 |
| initial_8 | cbo | 15645.9000 | 7.0000 | 0.2530 |
| initial_8 | cd_cbo | 13638.7000 | 7.6000 | 0.2875 |
| initial_8 | cd_risk_threshold | 12301.4000 | 3.6000 | 0.1961 |
| initial_8 | random | 11437.2000 | 3.0000 | 0.2008 |
| initial_8 | rc_cbo | 15645.9000 | 7.0000 | 0.2535 |
| initial_8 | risk_budget | 10869.5000 | 3.4000 | 0.2013 |
| initial_8 | risk_threshold | 10869.5000 | 3.4000 | 0.2013 |
| initial_8 | strength_bo | 13480.2000 | 7.0000 | 0.2416 |
| threshold_12 | cbo | 13554.9000 | 5.6000 | 0.2354 |
| threshold_12 | cd_cbo | 13056.1000 | 7.0000 | 0.2578 |
| threshold_12 | cd_risk_threshold | 12140.7000 | 4.4000 | 0.2086 |
| threshold_12 | random | 12952.7000 | 4.0000 | 0.2048 |
| threshold_12 | rc_cbo | 13554.9000 | 5.8000 | 0.2402 |
| threshold_12 | risk_budget | 11794.8000 | 3.0000 | 0.1912 |
| threshold_12 | risk_threshold | 11794.8000 | 3.2000 | 0.1998 |
| threshold_12 | strength_bo | 13085.1000 | 7.2000 | 0.2432 |
| threshold_8 | cbo | 13554.9000 | 4.2000 | 0.2126 |
| threshold_8 | cd_cbo | 13478.8000 | 5.8000 | 0.3108 |
| threshold_8 | cd_risk_threshold | 12932.9000 | 4.6000 | 0.2282 |
| threshold_8 | random | 12952.7000 | 3.0000 | 0.1866 |
| threshold_8 | rc_cbo | 13554.9000 | 4.4000 | 0.2076 |
| threshold_8 | risk_budget | 11760.0000 | 1.8000 | 0.1629 |
| threshold_8 | risk_threshold | 11760.0000 | 2.2000 | 0.1759 |
| threshold_8 | strength_bo | 13085.1000 | 6.6000 | 0.2410 |

| fold | training_cases | target_cases | training_feasible | target_feasible | disjoint_components | exhausted_target_pool |
| --- | --- | --- | --- | --- | --- | --- |
| group_0 | 46 | 34 | 28 | 30 | True | False |
| group_1 | 65 | 15 | 48 | 10 | True | True |
| group_2 | 49 | 31 | 40 | 18 | True | False |

Threshold8/12 and initialization 8/16 sensitivities use five matched seeds each without retuning. All eight methods keep the same experimental budget and scenario-specific constraint. Study-or-composition grouped splits are feasible in all three prespecified folds but limited: one target pool contains exactly15 cases, so final target discovery exhausts the pool. The initial incumbent comes from outside the target pool and can dominate AUC. Source and chemistry components do not cross initial/target sets; later sequential observations do adapt within target groups. These are distribution-shift stress tests on already exposed literature data, not independent replication. No fold or sensitivity was chosen after results.

## Scientific interpretation and limits

Risk thresholds may select safer but lower-value cases; the Pareto plot and joint goals distinguish that from a better trade-off. Continuous magnitude can help probability estimation yet fail to improve sequential discovery, or can overfit sparse heterogeneous measurements. CEI additionally assumes a separable strength/feasibility utility approximation. Composition-only features omit processing, small study groups are dependent, initialization contributes substantially to AUC, and literature measurement uncertainty is incomplete. Prior v1 analysis and earlier dataset overlap cannot be undone by new replay seeds. Further research requires genuinely new study-group or prospective experiments and validated noise assumptions; these exploratory outcomes do not justify a broad improvement claim.

## Reproduction and audit

See `docs/v2/REPRODUCIBILITY.md`. All original 95 tests are preserved; pre-freeze suite:124 passing, including29 v2 correctness tests. The separate audit in `scripts/audit_v2.py` recomputes labels, history isolation, risk charges and metrics and checks exact v1 baseline equivalence and artifact preservation. Its result is written to `audit.json` after execution. This is an independent code path, not an external human scientific review. Full deterministic rerun evidence is in `reproduction.json`.

Figures: `figures/01_discovery`, `02_pareto`, `03_common_history_reliability`, `04_ductility_diagnostics`, `05_risk_accounting`, plus `diagnosis/v1_diagnostics` (PNG and PDF). The Pareto curve joins nondominated means among fixed policies; it is not an optimized parameter sweep.

## Evidence-based failure interpretation

The binary probability threshold is mostly unattainable: risk-threshold falls back on 441/450 queries and risk-budget on 442/450. Thus both behave almost entirely as minimum-predicted-risk selection, explaining their nearly identical results. Every budget run exceeds its 3.75 predicted-failure allocation, with mean expenditure 5.0598. Observed failures average 3.2667, but that does not retrospectively repair infeasible forecast budgeting. A strong conclusion about a well-supported risk-constrained CEI regime is not possible here; the tested rule is dominated by its documented fallback. No threshold was lowered after seeing this outcome.

On exactly the ordinary-CBO histories/cases, continuous modeling worsens Brier by 0.04728 (paired 95% interval 0.02156–0.07300) and log loss by 0.25725 (0.14901–0.36548). ROC ranking drops from 0.6786 to 0.5613. Near the 10% constraint, pooled Brier increases from 0.2926 to 0.4897; 29 seeds have cases in this band. On random histories the continuous Brier mean is lower by 0.01591, but its interval crosses zero; log loss is higher by 0.16700 (0.02139–0.31262). The evidence does not support better calibrated feasibility from retaining magnitude under this GP specification.

CD-CBO ductility intervals cover 78.44% of measurements at nominal 95%; CD-threshold covers 86.22%. Standardized log-residual standard deviations are 1.832 and 1.501 instead of 1. Mean predicted negative mass is 1.057% and 0.180%, respectively. CD-threshold predicts 2.6383 failures but observes 3.7333; failed choices average 0.8016 predicted feasibility. Unlike the v1 aggregate diagnosis, the continuous branch exhibits materially overconfident errors. Raw/log marginal skewness, PIT shape, undercoverage and kernel-bound warnings caution against this homoscedastic Gaussian response assumption. Continuous information alone is insufficient without a defensible predictive distribution.

Sensitivity preserves important exceptions. In grouped fold 0, both binary risk policies retain 100% of AUC while reducing failures 86.7%; however, initial incumbents make all policy mean AUCs equal, so this is a ceiling-limited engineering success, not stronger discovery evidence. In fold 1 all 15 target cases are eventually queried and failures cannot differ. In fold 2 CD-CBO raises AUC 11.2% but increases failures 18.7%. At threshold 8%, CD-CBO retains 99.4% AUC but increases failures 38.1%. At initialization 8, binary risk AUC retention falls to 69.5%. These heterogeneous five-seed findings are retained without changing the primary verdict.

Further research is justified as a limited model-development question, especially independent validation of ductility uncertainty and risk-limit attainability. These results do not support deploying the tested policies as an improvement over ordinary CBO. A new development dataset or a new explicitly separated protocol is needed before tuning these assumptions; the current final comparison remains frozen.

Audit completion: 7,800 evaluation selections across 520 runs checked; all 1,800 baseline selections exactly match v1, all 3,600 primary selections reproduce exactly excluding runtime, and 170 preserved files are byte-identical. Full test suite 124 passed. All executable v2 phases and the continuous branch are complete; external independent-dataset validation remains a limitation, not a claimed accomplishment.
