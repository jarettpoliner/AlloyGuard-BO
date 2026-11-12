"""Append regenerated secondary statistics and final audit evidence to the report.

No model/configuration/primary result is altered; this is reporting only.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def complete(root):
    root=Path(root)
    path=root/"results/REPORT.md"
    text=path.read_text().split("\n## Additional quantitative interpretation")[0]
    m=pd.read_csv(root/"results/primary/metrics.csv")
    paired=json.loads((root/"results/paired_comparisons.json").read_text())
    a=paired["cbo_minus_hardness_bo"]["auc_gpa_evaluations"]
    f=paired["cbo_minus_hardness_bo"]["failure_count"]
    post=json.loads((root/"results/posthoc_analysis.json").read_text()) if (root/"results/posthoc_analysis.json").exists() else None
    audit=json.loads((root/"results/independent_audit.json").read_text())
    final=json.loads((root/"results/final_test_evidence.json").read_text()) if (root/"results/final_test_evidence.json").exists() else None
    text+=f'''
## Additional quantitative interpretation

The evidence does not support the general claim that the implemented constrained policy improves discovery efficiency over hardness-only BO. CBO AUC was lower by {a['mean']:.3f} GPa·evaluations, with conditional paired 95% interval [{a['lower_95']:.3f}, {a['upper_95']:.3f}]. It did reduce infeasible selections by {-f['mean']:.3f} per 15 selections; failure-count difference was {f['mean']:.3f} [{f['lower_95']:.3f}, {f['upper_95']:.3f}]. This is a tradeoff under the frozen metric, not an overall improvement. The primary metric favors hardness-only BO in this dataset/configuration. Both model-based policies substantially outperformed random on mean AUC, but the calibrated policy adds no effect because its calibration is disabled.

AUC includes the shared step-zero incumbent and rewards early feasible discoveries. Final feasible hardness alone can conceal delayed discovery. Paired seed intervals remain conditional finite-pool summaries, not universal physical performance claims or multiple-comparison-adjusted tests.

| Policy | P(feasible by 5) | By 10 | By 15 | Median first-feasible selection* | Censored at 15 | Log loss | Hardness NLL | Approx. 95% interval coverage | Fit time/run (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
'''
    for policy,g in m.groupby("policy"):
        text+=(f"| {policy} | {g.found_feasible_by_5.mean():.3f} | {g.found_feasible_by_10.mean():.3f} | {g.found_feasible_by_15.mean():.3f} | "
               f"{g.time_to_first_feasible.median():.1f} | {g.first_feasible_censored.sum()} | {g.log_loss.mean():.4f} | {g.hardness_nll.mean():.3f} | {g.hardness_interval_coverage.mean():.3f} | {g.fit_seconds.mean():.3f} |\n")
    text+="\n*First-feasible query is 0 if initial observations already contain a feasible group. Median is among uncensored runs, with censor counts shown; it is not a survival-model estimate. Full censored trajectories and per-budget probabilities are retained. Approximate Gaussian coverage below 0.95 indicates that these model intervals should not be advertised as calibrated uncertainty. NLL uses noisy-observation SD, not latent SD.\n"
    if post:
        c0=post["initialization_cohorts"]["initial_feasible_False"]
        c1=post["initialization_cohorts"]["initial_feasible_True"]
        e=post["representative_failure"]
        text+=f'''
### Cold-start and actual failure analysis (posthoc descriptive)

Among the {c0['count']} seeds with no initially feasible alloy, mean CBO-minus-hardness AUC was {c0['mean_cbo_minus_hardness_auc']:.3f}. Among the {c1['count']} seeds with an initially feasible alloy it was {c1['mean_cbo_minus_hardness_auc']:.3f}. This associates most observed AUC loss with feasibility-discovery starts; it does not causally identify a better cold-start algorithm. The worst CBO-minus-hardness seed was {post['worst_cbo_vs_hardness_seed']}, delta {post['worst_auc_difference']:.3f}; all its selection traces are preserved. The prescribed 0.05 exploration coefficient was not retuned.

The Figure 5 case is seed {e['seed']}, step {e['step']}, `{e['hardness_bo_alloy']}`. Hardness-only forecast {e['predicted_hardness_gpa']:.3f} GPa and feasibility {e['raw_probability']:.4f}; the observed alloy had hardness {e['actual_hardness_gpa']:.3f} GPa and rank {e['actual_rank']}. The training set was single-class, so the low probability was a smoothed empirical-prior fallback rather than validated chemistry-specific discrimination. A posthoc one-step CBO decision from exactly those same revealed observations chose `{e['matched_observation_cbo_counterfactual_alloy']}`, whose actual rank was {e['matched_observation_cbo_counterfactual_rank']}. It avoided that particular candidate but still selected an infeasible one. Thus the figure does not prove successful experimental risk avoidance. It illustrates both hardness-only disregard of feasibility and the limitations of sparse-feedback feasibility search. This counterfactual is a fixed-policy diagnostic, not the sequential CBO trajectory, and was never used for tuning.

Composition-support error summaries are in `posthoc_analysis.json`. They condition on adaptively selected forecasts and should not be read as a held-out generalization test.
'''
    text+=f'''
## Final independent audit and gate status

The independent recomputation within this implementation session audited **{audit['selections_audited']} selections and {audit['recomputed_runs']} runs** against the raw laboratory outcomes. It verified source/config/output checksums, grouped truth, exact recorded pre-selection observed sets, no duplicate query, every AUC/failure count, matched initialization and gated-policy equality. The complete regenerated 30-seed run status is **{audit['reproduction']}**. This is not external peer review.
'''
    passed=final and final["failures"]==0 and final["errors"]==0 and audit["reproduction"]=="FULL_30_SEED_EXACT_DECISIONS_AND_FORECASTS_MATCH"
    if passed:
        text+=f"\nFinal suite: **{final['tests']} passed, {final['failures']} failed, {final['errors']} errors, {final['skipped']} skipped**. The pre-freeze suite had 38 passing tests; additional post-comparison tests audit integration/artifacts without changing methodology. G1 is passed with the documented publisher-metadata/license verification qualification; G2–G8 are complete for this retrospective workflow. Calibration efficacy and OOD validation remain scientifically unsupported, explicitly disabled/unrun rather than passing scientific claims.\n"
        verdict=json.loads((root/"results/research_verdict.json").read_text())
        verdict["gates"]["G8"]="PASSED"
        verdict.update(final_test_count=final["tests"],full_reproduction_verified=True,
                       scientific_limitations=["Only seven feasible groups; calibration efficacy untested","OOD_TEST_INSUFFICIENT_SUPPORT","Publisher/license metadata user-supplied, not independently fetched","No prospective laboratory validation"])
        (root/"results/research_verdict.json").write_text(json.dumps(verdict,indent=2)+"\n")
    path.write_text(text)

if __name__=="__main__":
    complete(Path(__file__).resolve().parents[1])
