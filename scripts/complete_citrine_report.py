"""Additional result interpretation/secondary metrics; does not alter frozen methods."""
from pathlib import Path
import json
import pandas as pd

def complete(root):
    out=Path(root)/'results/citrine';path=out/'REPORT.md'
    text=path.read_text().split('\n## Direct interpretation and predictive uncertainty')[0]
    m=pd.read_csv(out/'primary/metrics.csv');pairs=json.loads((out/'paired_comparisons.json').read_text())
    diag=json.loads((out/'model_diagnostics.json').read_text());failure=json.loads((out/'failure_analysis.json').read_text())
    text+='''
## Direct interpretation and predictive uncertainty

**Which policy was best?** Ordinary constrained BO had the highest mean primary discovery AUC in this frozen cohort. Relative to standard BO, its conditional paired AUC difference was+652.89MPa·evaluations,95% interval[73.84,1231.94], and it made1.90 fewer elongation failures per15 queries, interval[0.73,3.07] for the reduction. This is evidence of a useful feasibility-model contribution in this pool/configuration, not a universal materials-discovery improvement. Its AUC difference versus random has an interval spanning zero, so the highest observed mean does not establish superiority to every baseline.

**Did calibration help decisions?** RC-CBO minus CBO AUC was−6.75[−52.61,39.11]. The interval includes both directions, the mean is near zero, and no improvement is confirmed. It changed acquisition rankings25 times and activated194/450 steps; it was not simply disabled as in the original GE experiment. On the same RC selected cases, Brier declined from0.222998(raw) to0.219216(calibrated), but this did not translate into demonstrated better selection. Calibration's failure-count difference versus CBO was−0.033[−0.241,0.174], also inconclusive. These are conditional unadjusted exploratory intervals, not independent prospective experiments.

**What failed?** Standard BO pursued high-yield-strength but low-elongation cases, averaging7.17 failures/15 versus5.27 for CBO,5.23 for RC-CBO and4.30 for random. Constraints are probabilistic preferences, not hard safety filters; constrained methods can still fail more often than random while pursuing a stronger objective. Composition-only strength modeling ignores quantitative processing and other study differences. Its high prequential errors, sub-nominal interval coverage and frequent lower kernel-length bounds expose misspecification/sparse-data limitations. Random forecasts are evaluated on a less selectively difficult population, so their lower errors do not alone prove a better surrogate.

| Policy | Log loss | Strength NLL | Nominal95% observation coverage | Feasible by15 | Median first feasible query* | Censored | Mean fitting time/run(s) |
|---|---:|---:|---:|---:|---:|---:|---:|
'''
    for policy,g in m.groupby('policy'):
        # All primary runs have a feasible initialization; metrics retain the definition for general use.
        found=1-g.first_feasible_censored.mean()
        text+=f'| {policy} | {g.log_loss.mean():.4f} | {g.strength_nll.mean():.3f} | {g.strength_interval_coverage.mean():.3f} | {found:.3f} | {g.time_to_first_feasible.median():.1f} | {int(g.first_feasible_censored.sum())} | {g.fit_seconds.mean():.3f} |\n'
    text+='\n*Query0 means initialization already contains a feasible case. Medians among uncensored runs are descriptive, not survival estimates. Coverage uses latent variance plus assumed25MPa observation noise and is not a calibrated guarantee.\n'
    text+=f"\nThere were{diag['optimizer_non_successes']} optimizer non-successes and{sum(diag['warnings'].values())} retained kernel-bound warning events. Of these,852 concern the conservative0.3 lower length bound and15 the6.0 upper bound. These indicate that marginal-likelihood optimization often preferred short-range or boundary covariance under composition-only small-data fits. Predictions/acquisitions remained finite. Bounds were not retuned after observing policy performance.\n"
    div=failure['first_decision_divergence']
    if div:
        a=div['cbo'];b=div['rc_cbo']
        text+=f"\nThe first CBO/RC decision divergence occurred at seed{div['seed']}, query{div['step']}, under the shared history up to that query. CBO chose`{a['case_id']}` with measured strength{a['measured_strength_mpa']:.2f}MPa, elongation{a['measured_elongation_percent']:.2f}%; RC chose`{b['case_id']}` with{b['measured_strength_mpa']:.2f}MPa,{b['measured_elongation_percent']:.2f}%, usingT={b['temperature']:.3f}. This is a traceable posthoc example, not a rule chosen to favor calibration.\n"
    case=failure['representative_standard_bo_failure']
    if case:
        text+=f"\nFigure5's measured failure is`{case['case_id']}` at seed{case['seed']}, query{case['selection_step']}: forecast{case['strength_mean_mpa']:.2f}MPa,p_raw={case['feasibility_probability_raw']:.3f}; actual{case['measured_strength_mpa']:.2f}MPa and{case['measured_elongation_percent']:.2f}% elongation. It demonstrates a real selected screening failure; it does not prove another policy would avoid the same event.\n"
    text+='\nThe shift panel is deliberately demanding but limited: fold1 has15 target cases and15 queries, so every policy exhausts that target pool by the end; differences there concern discovery order and prequential forecasts. Other folds have34 and31 target cases. All group splits are fixed without targets and no study/chemistry component crosses training/target pools. These three correlated splits support stress diagnosis, not a general OOD-robustness guarantee.\n'
    text+='\n**Further research is supported, but the calibrated-policy superiority hypothesis is not established.** The strongest next step is a larger prospective, processing-resolved experiment set with independently heldout studies and raw stress-strain/replicate uncertainty. Keep the present negative calibration comparison intact; any changed kernel/noise/calibration rules need a separate revision and evaluation cohort.\n'
    overlap_path=out/'prior_dataset_overlap.json'
    if overlap_path.exists():
        overlap=json.loads(overlap_path.read_text())
        text+=f"\n### Prior development-data exposure\n\nA posthoc provenance check found**{overlap['citrine_qualified_cases_with_possible_prior_software_dataset_overlap']} possible overlaps among80 Citrine cases** with the earlier Mendeley provisional software inputs, using exact target-pair matches and rounded composition agreement within0.003. This is evidence of possible common source observations, not proof of independent replication. Citrine therefore is **not a pristine external-validation dataset**. The existing model defaults were retained, no final Citrine outcomes tuned the methods, and all GP models were freshly fitted to each replay's currently revealed observations only. This guards within-replay target access but does not erase researcher/development-data exposure. Independent prospective or genuinely unseen-study evaluation remains necessary. Exact candidate matches and comparison rules are preserved in prior_dataset_overlap.json.\n"
    from readable_report import readable
    path.write_text(readable(text))

if __name__=='__main__':complete(Path(__file__).resolve().parents[1])
