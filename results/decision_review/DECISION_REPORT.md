# AlloyGuard-BO scientific decision report

**Recommendation A: finalize and publish the reproducible benchmark with its negative and trade-off results. Do not start v3 on the same cohort.** No experiments or frozen artifacts were changed; no new algorithm was developed. Publication is a recommendation, not an action taken.

## What the evidence establishes

Thirty matched replays show a real conditional safety–discovery trade-off. Ordinary CBO has the best mean discovery AUC; both binary risk policies avoid two failures per 15-query campaign at a loss of roughly 14% of AUC. Differences below are paired 95% t intervals across replay seeds, conditional on this same 80-case cohort—not population or independent-dataset confidence intervals.

| Policy | Mean AUC | Mean failures | ΔAUC vs CBO [95% interval] | Δfailures vs CBO [95% interval] |
|---|---:|---:|---|---|
| random | 13,023.2 | 4.30 | -962.41 [-2,026.12, 101.30] | -0.97 [-2.15, 0.21] |
| strength_bo | 13,332.7 | 7.17 | -652.89 [-1,231.94, -73.84] | 1.90 [0.73, 3.07] |
| cbo | 13,985.6 | 5.27 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| rc_cbo | 13,978.8 | 5.23 | -6.75 [-52.61, 39.11] | -0.03 [-0.24, 0.17] |
| risk_threshold | 12,043.2 | 3.27 | -1,942.37 [-2,799.81, -1,084.94] | -2.00 [-2.92, -1.08] |
| risk_budget | 12,055.1 | 3.27 | -1,930.47 [-2,777.88, -1,083.07] | -2.00 [-2.92, -1.08] |
| cd_cbo | 13,013.3 | 6.50 | -972.27 [-1,643.08, -301.47] | 1.23 [0.33, 2.14] |
| cd_risk_threshold | 12,544.5 | 3.73 | -1,441.08 [-2,202.77, -679.39] | -1.53 [-2.40, -0.67] |

CBO improves on strength-only BO here, but its AUC advantage over random remains uncertain. Reliability calibration did not confirm improvement. The original v2 joint goals remain unmet: reduced failures did not preserve 98% of discovery AUC.

**Mean Pareto frontier:** risk-budget, CD-risk-threshold, random, calibrated CBO, ordinary CBO. Strength BO and CD-CBO are dominated by CBO/calibrated CBO; CD-CBO is also dominated by random. Risk-threshold is technically dominated by risk-budget at the means, but the difference is not meaningful evidence: risk-budget gains only 11.90 AUC [−12.44, 36.24], with identical failure counts and final strength in every seed. They match on 435/450 selections and differ in only two seeds. Fallbacks occur on 442/450 and 441/450 decisions, so both mostly act as minimum-predicted-risk selection. This does not establish a benefit from explicit risk budgeting or a hard safety guarantee.

**Continuous ductility failed under the tested assumptions.** On exactly CBO’s histories/cases, continuous Brier worsens from 0.2220 to 0.2693; paired increase 0.0473 [0.0216, 0.0730]. Log loss increases by 0.2572 [0.1490, 0.3655]; ranking and near-threshold scores worsen. CD-CBO’s nominal 95% ductility intervals cover only 78.4%. Fixed noise, heterogeneous literature measurements, missing processing inputs and an inadequate log-Gaussian uncertainty model are plausible contributors, not proven isolated causes. The finding rejects this specification’s claimed benefit, not continuous information in principle.

## When fewer failures have practical value

For **U = AUC − λ × failures**, λ is an externally elicited preference in **MPa × experiment steps per failure**, not money. Failure already consumes an experiment; this penalty represents additional aversion beyond the discovery opportunity cost. The illustrative range 0–5,000 (increments of 50) is not optimized. Initial costs cancel between matched policies; unequal assay costs and durations are not modeled.

| Binary risk policy | 15-query break-even λ vs CBO | Paired Fieller 95% set |
|---|---:|---|
| Risk-threshold | 971.19 | [522.99, 1,841.66] |
| Risk-budget | 965.24 | [522.86, 1,824.52] |

At λ=1,000, risk-budget’s utility advantage is +69.53 [−1,046.52, 1,185.57]: inconclusive. At externally justified λ=2,000 it is +2,069.53 [207.96, 3,931.10]; threshold gives +2,057.63 [187.80, 3,927.46]. Thus risk-aware selection can be practically valuable to a sufficiently failure-averse campaign, without meeting the original nearly-free-safety goal. This does not prove superiority to every alternative or justify choosing a penalty because its interval excludes zero. All intervals are pointwise and unadjusted.

Across all methods, the empirical 15-step utility envelope switches CBO → calibrated CBO → CD-risk-threshold → risk-budget at λ≈202.50, 956.22 and 1,048.70. These precise crossings are descriptive, not robust recommendations; the calibration crossover has an unbounded confidence set. Random is Pareto-nondominated but never maximizes this linear mean utility at 15 steps. Full pairwise uncertainty is supplied.

| Additional-query prefix | Threshold break-even λ | Budget break-even λ |
|---:|---:|---:|
| 5 | 340.68 | 329.32 |
| 10 | 675.28 | 652.84 |
| 15 | 971.19 | 965.24 |

These are early-stopped prefixes of the frozen 15-query trajectories, not newly horizon-optimized policies. Risk-budget still planned for 15. AUC scales with horizon; penalties must be interpreted consistently. No conclusions beyond 15 queries are supported.

## Why the benchmark is useful but limited

Feasibility is already 72.5% (58/80): random expects 4.125 failures in 15 queries, and a 12-case initialization lacks any feasible case with probability only 1.07×10⁻⁸. Cold-start feasibility discovery is effectively untested. The initial incumbent accounts for 85.0% of CBO AUC if held constant, so retention percentages can hide poor incremental discovery. Nevertheless, CBO reaches only 80.7% of the idealized best-alloy-from-step-zero ceiling; improvement is not mathematically exhausted.

There are 68 chemistries, 36 studies and 31 connected study/chemistry groups. A group-size concentration proxy is 18.6—not an estimated statistical effective sample size. Ambiguous duplicate recipes were excluded, but processing and study dependence remain. Grouped test pools contain only 15–34 cases; one is exhausted by the budget and another is heavily feasible/incumbent-limited. Thirty seeds do not create thirty independent datasets. The benchmark detects large conditional trade-offs but does not reliably distinguish small algorithmic gains. More seeds reduce Monte Carlo uncertainty, not data dependence or generalization uncertainty.

## Decision before v3

Publish the useful findings: constrained search versus unconstrained search, the quantified failure–discovery frontier, and the failure of calibration/continuous magnitude alone to improve decisions. Do not claim universal CBO superiority, economic savings, hard risk control, or risk-budget superiority over thresholding.

A materially stronger v3 needs source-disjoint independent or prospective data; development-only tuning; study/process-aware validation; sufficient infeasible and near-boundary cases; and externally specified campaign costs/horizons. The logs motivate testing whether independently validated heteroscedastic ductility uncertainty and processing information reduce confidently wrong predictions. They do not yet validate a replacement algorithm. A different objective such as measured assay cost and terminal strength requires actual cost evidence and a fresh protocol, not retrospective rescue of v2. Further method selection on this exposed cohort would create selection bias even with new seeds.

## Supporting artifacts

[Full statistical interpretation and reproduction command](TECHNICAL_APPENDIX.md) · [Utility curves](utility_curves.png) · [Paired utility intervals](paired_utility.png) · [All paired policy differences](all_paired_differences.csv) · [Budget/utility data](utility_curves.csv) · [Preservation check](preservation.json).
