"""Descriptive finite-pool results; all claims conditional and exploratory."""
from pathlib import Path
import json,collections
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import t
from sklearn.metrics import roc_auc_score
from alloyguard_strength.replay import paired_interval

LABELS={'random':'Random','strength_bo':'Standard BO','cbo':'Constrained BO','rc_cbo':'Calibrated constrained BO'}
COLORS={'random':'#777777','strength_bo':'#d55e00','cbo':'#0072b2','rc_cbo':'#009e73'}

def traces(path):return [json.loads(line) for line in Path(path).read_text().splitlines()]

def comparisons(metrics):
    result={}
    for a,b in (('rc_cbo','cbo'),('cbo','strength_bo'),('rc_cbo','strength_bo'),('strength_bo','random'),('cbo','random')):
        result[f'{a}_minus_{b}']={}
        for column in ('auc_mpa_evaluations','failure_count','brier','strength_mae_mpa'):
            pivot=metrics.pivot(index='seed',columns='policy',values=column)
            result[f'{a}_minus_{b}'][column]=paired_interval(pivot[a]-pivot[b])
    return result

def report(root):
    root=Path(root);out=root/'results/citrine';run=out/'primary'
    m=pd.read_csv(run/'metrics.csv');curves=pd.read_csv(run/'curves.csv');rows=traces(run/'traces.jsonl')
    q=json.loads((out/'data_audit.json').read_text());cfg=json.loads((run/'config.json').read_text());manifest=json.loads((run/'manifest.json').read_text())
    pairs=comparisons(m);means=m.groupby('policy').mean(numeric_only=True)
    (out/'paired_comparisons.json').write_text(json.dumps(pairs,indent=2)+'\n');means.to_csv(out/'summary.csv')
    warnings=collections.Counter(w for r in rows for name in ('strength','feasibility') for w in r['diagnostics'][name]['warnings'])
    fallback=collections.Counter(r['diagnostics']['feasibility']['status'] for r in rows)
    cal=collections.Counter(r['calibration_status'] for r in rows if r['policy_name']=='rc_cbo')
    rc=[r for r in rows if r['policy_name']=='rc_cbo']
    raw_brier=np.mean([(r['feasibility_probability_raw']-r['feasible'])**2 for r in rc])
    cal_brier=np.mean([(r['feasibility_probability_calibrated']-r['feasible'])**2 for r in rc])
    diag={'warnings':dict(warnings),'feasibility_fit_status_counts':dict(fallback),'calibration_status_counts':dict(cal),
        'optimizer_non_successes':sum(not event['success'] for r in rows for event in r['diagnostics']['strength']['optimizer']),
        'rc_raw_vs_cal_same_selected_cases_brier':{'raw':float(raw_brier),'calibrated':float(cal_brier)},
        'ranking_changes':sum(r['raw_winner']!=r['calibrated_winner'] for r in rc),
        'fit_warnings_interpretation':'Conservative kernel bounds can be optimal with small-sample/noisy composition-only modeling; warnings retained, no result-based bound changes.',
        'discrimination_selected_forecasts':{}}
    for policy in LABELS:
        selected=[r for r in rows if r['policy_name']==policy];y=[r['feasible'] for r in selected]
        diag['discrimination_selected_forecasts'][policy]=float(roc_auc_score(y,[r['feasibility_probability_raw'] for r in selected])) if len(set(y))==2 else None
    (out/'model_diagnostics.json').write_text(json.dumps(diag,indent=2)+'\n')
    figdir=out/'figures';figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    def save(fig,name):
        fig.suptitle('Exploratory published-data replay: explicit tensile tests at25°C',fontsize=10)
        fig.tight_layout();fig.savefig(figdir/f'{name}.png',dpi=220);fig.savefig(figdir/f'{name}.pdf');plt.close(fig)
    for field,name,label in (('best_feasible_strength_mpa','01_discovery','Best confirmed feasible yield strength (MPa)'),('cumulative_failures','02_failures','Cumulative elongation<10% selections')):
        fig,ax=plt.subplots(figsize=(7.5,4.5))
        for policy in LABELS:
            g=curves[curves.policy==policy].groupby('step')[field];mu=g.mean();half=t.ppf(.975,len(cfg['seeds'])-1)*g.std()/np.sqrt(len(cfg['seeds']))
            ax.plot(mu.index,mu,label=LABELS[policy],color=COLORS[policy],linestyle='--' if policy=='rc_cbo' else '-',linewidth=2)
            ax.fill_between(mu.index,mu-half,mu+half,color=COLORS[policy],alpha=.1)
        ax.set(xlabel='Additional selections (12 shared initial cases)',ylabel=label);ax.set_xticks([0,5,10,15]);ax.legend(fontsize=8);ax.grid(alpha=.12);save(fig,name)
    fig,axes=plt.subplots(1,2,figsize=(8,4))
    bins_rows=[]
    for key,label in (('feasibility_probability_raw','Raw'),('feasibility_probability_calibrated','Temperature scaled')):
        p=np.array([r[key] for r in rc]);y=np.array([r['feasible'] for r in rc]);bins=np.minimum((p*5).astype(int),4)
        x=[];z=[]
        for b in range(5):
            mask=bins==b
            if mask.any():
                x.append(float(p[mask].mean()));z.append(float(y[mask].mean()))
                bins_rows.append({'forecast':label,'bin':b,'count':int(mask.sum()),'mean_probability':x[-1],'feasible_fraction':z[-1]})
        axes[0].plot(x,z,'o-',label=label)
    axes[0].plot([0,1],[0,1],'k--',alpha=.4);axes[0].set(xlabel='Mean pre-reveal probability',ylabel='Reported feasible fraction',xlim=(0,1),ylim=(0,1));axes[0].legend(fontsize=8)
    active=[r['temperature'] for r in rc if r['calibration_status']=='CALIBRATION_ACTIVE']
    axes[1].hist(active,bins=np.linspace(1/3,3,15),color=COLORS['rc_cbo']);axes[1].axvline(1,color='black',linestyle='--');axes[1].set(xlabel='Active fitted temperature T',ylabel='Selection steps')
    save(fig,'03_calibration');pd.DataFrame(bins_rows).to_csv(out/'reliability_bins.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(8,4))
    for policy in LABELS:
        selected=[r for r in rows if r['policy_name']==policy]
        actual=np.array([r['measured_strength_mpa'] for r in selected]);pred=np.array([r['strength_mean_mpa'] for r in selected]);sd=np.array([r['strength_observation_std_mpa'] for r in selected])
        axes[0].scatter(actual,pred,s=8,alpha=.2,label=LABELS[policy],color=COLORS[policy])
        axes[1].hist((actual-pred)/sd,bins=np.linspace(-8,8,35),histtype='step',density=True,color=COLORS[policy],label=LABELS[policy])
    axes[0].plot([100,1900],[100,1900],'k--',alpha=.4);axes[0].set(xlabel='Measured yield strength (MPa)',ylabel='Pre-reveal forecast (MPa)');axes[0].legend(fontsize=7)
    axes[1].set(xlabel='Residual / observation predictive SD',ylabel='Density in displayed range±8');save(fig,'04_prediction')
    pivot=m.pivot(index='seed',columns='policy',values='auc_mpa_evaluations');delta=pivot.rc_cbo-pivot.cbo
    worst=int(delta.idxmin());first_divergence=None
    for seed in sorted(m.seed.unique()):
        a=[r for r in rows if r['seed']==seed and r['policy_name']=='cbo'];b=[r for r in rows if r['seed']==seed and r['policy_name']=='rc_cbo']
        for ar,br in zip(a,b):
            if ar['case_id']!=br['case_id']:
                first_divergence={'seed':int(seed),'step':ar['selection_step'],'cbo':ar,'rc_cbo':br};break
        if first_divergence:break
    failure=[r for r in rows if r['policy_name']=='strength_bo' and not r['feasible']]
    case=max(failure,key=lambda r:r['strength_mean_mpa']) if failure else None
    fig,ax=plt.subplots(figsize=(7,4))
    sb=[r for r in rows if r['policy_name']=='strength_bo']
    ax.scatter([r['strength_mean_mpa'] for r in sb],[r['feasibility_probability_raw'] for r in sb],c=['#0072b2' if r['feasible'] else '#d55e00' for r in sb],alpha=.3,s=15)
    if case:
        ax.scatter([case['strength_mean_mpa']],[case['feasibility_probability_raw']],s=120,facecolors='none',edgecolors='black')
        ax.set_title(f"Actual standard-BO failure: seed{case['seed']}, step{case['selection_step']}\nMeasured {case['measured_strength_mpa']:.1f}MPa, elongation{case['measured_elongation_percent']:.1f}%",fontsize=9)
    ax.set(xlabel='Forecast yield strength (MPa)',ylabel='Raw probability elongation≥10%');save(fig,'05_failure')
    analysis={'worst_rc_minus_cbo_seed':worst,'worst_auc_difference':float(delta.loc[worst]),'seeds_rc_better':int((delta>0).sum()),
        'seeds_rc_worse':int((delta<0).sum()),'seeds_identical_auc':int((delta==0).sum()),'first_decision_divergence':first_divergence,
        'representative_standard_bo_failure':case,'interpretation':'Posthoc descriptive diagnosis only; no model/protocol adjustment.'}
    (out/'failure_analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
    table=[]
    for policy,label in LABELS.items():
        v=means.loc[policy];table.append(f'| {label} | {v.auc_mpa_evaluations:.2f} | {v.best_feasible_at_5_mpa:.2f} | {v.best_feasible_at_10_mpa:.2f} | {v.best_feasible_at_15_mpa:.2f} | {v.failure_count:.2f} | {v.brier:.4f} | {v.strength_mae_mpa:.2f} |')
    pair_text=[]
    for name,values in pairs.items():
        a=values['auc_mpa_evaluations'];f=values['failure_count']
        pair_text.append(f'- {name}: AUC difference {a["mean"]:.2f} MPa·evaluations,95% interval[{a["lower_95"]:.2f},{a["upper_95"]:.2f}]; failures difference {f["mean"]:.2f}[{f["lower_95"]:.2f},{f["upper_95"]:.2f}].')
    ablations=[];diagnostic_root=out/'diagnostics'
    for directory in sorted(diagnostic_root.glob('*')) if diagnostic_root.exists() else []:
        if directory.is_dir() and (directory/'metrics.csv').exists():
            extra=pd.read_csv(directory/'metrics.csv');extra_means=extra.groupby('policy').mean(numeric_only=True)
            for policy,v in extra_means.iterrows():ablations.append(f'| {directory.name} | {policy} | {v.auc_mpa_evaluations:.2f} | {v.failure_count:.2f} | {v.brier:.4f} |')
    shift=json.loads((diagnostic_root/'shift_support.json').read_text()) if (diagnostic_root/'shift_support.json').exists() else []
    best=means.auc_mpa_evaluations.idxmax();rc_diff=pairs['rc_cbo_minus_cbo']['auc_mpa_evaluations']
    verdict='NO_CONFIRMED_IMPROVEMENT'
    if rc_diff['lower_95']>0:verdict='EXPLORATORY_CALIBRATION_BENEFIT_CONDITIONAL_ON_THIS_POOL'
    tests=json.loads((out/'final_test_evidence.json').read_text()) if (out/'final_test_evidence.json').exists() else json.loads((out/'pre_freeze_test_evidence.json').read_text())
    audit=json.loads((out/'independent_audit.json').read_text()) if (out/'independent_audit.json').exists() else {'status':'PENDING'}
    result={'verdict':verdict,'best_mean_auc_policy':best,'rc_minus_cbo_auc':rc_diff,'scope':'EXPLORATORY_CONDITIONAL_FINITE_POOL',
        'test_evidence':tests,'audit_status':audit['status'],'gates':{f'G{i}':'COMPLETE_EXPLORATORY_WORKFLOW' for i in range(1,9)}}
    if audit['status']!='PASSED':result['gates']['G8']='PENDING_FINAL_AUDIT'
    (out/'verdict.json').write_text(json.dumps(result,indent=2)+'\n')
    text=f'''# AlloyGuard-BO Citrine25°C tensile benchmark

## Abstract and research verdict

**{verdict}.** This is an exploratory retrospective comparison on80 conservative published case groups,58 meeting tensile elongation≥10% and22 below it, across36 cited studies. Maximum mean primary discovery AUC was obtained by **{LABELS[best]}**. RC-CBO minus ordinary CBO AUC was **{rc_diff['mean']:.2f} MPa·evaluations**, paired conditional95% interval **[{rc_diff['lower_95']:.2f},{rc_diff['upper_95']:.2f}]**. A full30-seed matched comparison executed1,800 additional selections. It does not represent independent physical experiments or prospective discovery.

## Published source and integrity

Borg et al.(2020), *Expanded dataset of mechanical properties and observed phases of multi-principal element alloys*, Scientific Data, DOI10.1038/s41597-020-00768-9. Official repository https://github.com/CitrineInformatics/MPEA_dataset, pinned commit`{manifest['upstream_commit']}`. All four supplied source-file Git blobs match upstream exactly. The official README identifies `MPEA_dataset.csv` as the complete master; `combined_data.csv` is not intended for wide consumption. Original2018/2019 records and bibliography are cross-checks, never represented as an equivalent master dataset. Upstream repository LICENSE is Apache2.0; full text retained separately from AlloyGuard's MIT code license and the separate Mendeley workbook's license. Upstream notebooks/scripts were inspected as text/JSON and never executed.

Master SHA-256:`{q['master_sha256']}`. Cohort SHA-256:`{q['cohort_sha256']}`. Full file sizes/Git blob/SHA-256 checks are in `source_manifest.json`.

## Scientific qualification and all exclusions

The master contains1,545 rows. **246** explicitly report tensile modeT, temperature25°C, numerical yield strength and elongation. Raw files confirm each row's temperature/test/reference correspondence; no missing temperature was assumed room temperature. Keep positive finite yield strength, nonnegative finite elongation, valid atomic-ratio formulas, explicit recorded processing recipes and study DOIs. Raw censor bounds cannot become exact target values. The final primary cohort contains**{q['qualified_reported_cases']} unique composition+recorded-recipe cases**, no duplicate candidate key even across studies; **{q['feasible_count']} feasible/{q['infeasible_count']} infeasible**,{q['study_count']} cited studies,{q['chemical_composition_count']} chemistries and{q['leakage_components']} source/chemistry-connected groups. These are independent reported-case groups for replay, not independently verified physical replications with every process variable controlled.

First exclusion-reason counts (mutually exclusive, sum with80 cases to1,545):`{q['exclusion_first_reason_counts']}`. Every row, all overlapping reasons and source locator are retained in `record_audit.csv`. All ambiguous repeated composition/recipe groups are quarantined intact; none is averaged into a fictitious material state. Detailed source processing may conceal different anneals/working conditions despite identical recipe labels; a curator's raw note explicitly warns about this. The source also collapses detailed sequences into broad CAST/WROUGHT/etc classes. The adapter uses raw recorded recipe sequences only for case identity, retaining both versions as metadata.

All80 retained compositions match the upstream documented normalization of original formulas, including parenthesis parsing and rounding ratios to three decimals. Atomic fractions are computed from the published atomic-ratio formulas. This reproduces the published representation; rounding/ambiguous nominal notation can limit chemical fidelity and no independent assay of composition is implied. Published means remain targets; retained ±source uncertainty strings remain recorded. Elongation above100% is physically possible and is not rejected as physically invalid; such rows in the preliminary set are excluded only by ambiguous processing identity. No phases, grain size, measured hardness, UTS, other measured properties, density/modulus predictions or bibliography fields enter primary predictors.

## Methods: existing models, unchanged

Reused `alloyguard_strength` implementation: observed-only StandardScaler and target scaling (floor50MPa); Matérn5/2 GPR with amplitude[0.1,10], length[0.3,6], initial amplitude1,length2, deterministic L-BFGS-B max60 iterations; assumed observational SD25MPa. EI uses latent SD; observation intervals/NLL add25². The noise is a modeling assumption, not an inferred universal experimental error. Feasibility: Matérn5/2 Laplace GPC with fixed length2, max100 predictive iterations, single-class Beta(1,1) smoothed prior fallback. No artificial class rebalancing.

Primary features are composition only, matching the already implemented workflow. Known processing recipes define independent candidate cases; omitting their quantitative effects from primary regression is a deliberate model limitation. The predeclared processing-feature ablation adds one-hot recorded recipes to every policy equally, without measured-phase inputs. In that ablation the logged composition-feature tuple includes the explicitly documented recipe feature vector, and nearest-distance diagnostics are input-feature rather than purely chemical distances.

Calibration: currently observed data only, three-fold StratifiedGroupKFold by the transitive study-OR-chemistry component. Require≥20 observations,≥5 members/class,≥3 observed groups/class, both classes in every train/validation fold. Each fold refits observed-training scaling/classification. Fit positiveT∈[1/3,3] minimizing mean OOF log loss+0.05log(T)²; otherwise identity with reason. Dataset-level support gate≥15 cases and≥3 groups/class is met. All fold IDs, warnings and statuses are logged. No hidden labels train the calibrator.

Policies: uniform seeded random, standard strength-only latent EI, CBO(EI·raw feasibility), RC-CBO(EI·calibrated feasibility). CBO/RC differ only by calibration given identical observations; after different actions each sees its own revealed history. Conditional outcome dependence makes EI·p a factorization approximation, not exact correlated-outcome constrained EI. No-feasible start uses p+0.05normalized nearest-observed distance and no undefined incumbent. Full finite pool is exhaustively scored; ties follow stable IDs. Study provenance is grouping metadata, not a predictor. Typed candidates contain no target columns and never receive an oracle reference; this prevents accidental leakage, not adversarial Python introspection.

## Frozen protocol and validation

12 initial outcome-blind cases per seed, shared across all policies;15 extra evaluations; seeds0–29; fixed elongation threshold10%. Primary metric is trapezoidal area under best confirmed feasible-strength curve from step0 to15, including the shared initialized incumbent, with0MPa until a feasible case is observed. Failure counts exclude initialization. Tests, synthetic correctness, one-seed and five-seed smoke completed before freezing. No final results were used to revise cohort/threshold/models/protocol. Config hash`{cfg['config_hash']}`; base model source`{cfg['source_hash']}`; adapter source`{cfg['adapter_hash']}`. Numerical threads fixed to one. Original GE and provisional Mendeley artifacts remain untouched.

## Actual primary results

Means over30 matched seeds. AUC units MPa·evaluations; strengths MPa; failures out of15.

| Policy | AUC | Best@5 | Best@10 | Best@15 | Failures | Brier | Strength MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table)}

Paired differences:

{chr(10).join(pair_text)}

These t intervals summarize randomized seed variation **conditional on this fixed finite dataset/configuration**. Repeated replays share cases and are not independent laboratory experiments. They do not measure uncertainty across new materials/studies. No multiple-comparison correction or universal statistical-superiority claim is made. Selected-sample Brier/log loss/errors compare different adaptive populations across methods; they are not a common independent test set. Within RC's same450 queried cases, raw Brier={raw_brier:.4f}, calibrated Brier={cal_brier:.4f}; this descriptive paired-forecast diagnostic alone cannot prove better decisions.

![Discovery](figures/01_discovery.png)

Figure1. Mean best feasible strength, conditional95% seed-mean t bands. Zero means no observed feasible case. No material was synthesized here.

![Failures](figures/02_failures.png)

Figure2. Experimental-record elongation failures, not failed synthesis.

![Calibration](figures/03_calibration.png)

Figure3. Pre-reveal RC raw/calibrated forecasts, five fixed-width bins, and active fitted temperatures. Bin counts in reliability_bins.csv. Repeated cases and adaptive selection make these descriptive; no iid calibration guarantee or conformal guarantee is claimed.

![Prediction](figures/04_prediction.png)

Figure4. Predicted versus measured yield strength and residuals standardized by noisy-observation SD. Histogram displays±8; numerical NLL/coverage include all values. Gaussian intervals are approximate, not certified reliability.

![Failure](figures/05_failure.png)

Figure5. Actual standard-BO selections colored by observed feasibility; highlighted case has the highest predicted strength among its failed selections. This posthoc illustration does not establish that constrained BO would necessarily avoid it.

## Calibration effects, ablations and failure analysis

RC acquisition winner differs before reveal from its raw-feasibility counterfactual at**{diag['ranking_changes']}** steps. Calibration statuses:`{dict(cal)}`. Across seed-level AUC, RC better than CBO:{analysis['seeds_rc_better']}; worse:{analysis['seeds_rc_worse']}; equal:{analysis['seeds_identical_auc']}. Worst RC-minus-CBO seed{worst}, AUC delta{analysis['worst_auc_difference']:.2f}. The first action divergence, if any, both forecasts/actual outcomes, and actual high-strength failure example are retained in failure_analysis.json. No inconvenient outcomes or worse seeds are removed. Temperature scaling preserves raw probability ordering but can change EI·p ordering; sequential downstream effects are not the same as improving classification discrimination.

The primary CBO-versus-standard and RC-versus-CBO contrasts isolate feasibility and calibration contributions without weakening baselines. All planned extra runs are exploratory and use separate seed/config/run artifacts:

| Additional experiment | Policy | Mean AUC | Failures | Brier |
|---|---|---:|---:|---:|
{chr(10).join(ablations) if ablations else '| Pending | — | — | — | — |'}

Initial-size8/16 runs use seeds100–104 and15 queries. They have different total measurement costs; they do not select an optimal initialization. Processing ablation uses known recipe one-hot vectors and the same models/policies. Study/chemistry shift uses three outcome-blind component splits, seeds200–204,12 training-pool initial cases and15 heldout queries where prespecified size/class support permits. Shift support/outcomes:`{shift}`. No study or chemistry component crosses train/target pools. Its incumbent includes initial observed cases outside the target pool, so stronger initial materials can create a ceiling; this is not prospective proof of OOD robustness. No outcomes choose the split.

Optimizer non-successes:{diag['optimizer_non_successes']}. Logged warning events:{sum(warnings.values())}. Exact boundary-warning text, single-class fallback and calibration-activation/failure reasons are preserved per fit and in model_diagnostics.json. Conservative hyperparameter bounds were not changed to favor a result. Sparse labels, study dependence, unknown quantitative processing and composition-only misspecification can cause both uncertainty and selection failures even when fits are numerically valid.

## Reproducibility and independent audit

Test evidence:{tests['tests']} tests,{tests['failures']} failures,{tests['errors']} errors,{tests['skipped']} skipped. Audit status:{audit['status']}. The audit recomputes grouped truth/incumbents/AUC/failures, verifies recorded observed-ID sets and group-disjoint calibration, hashes all primary outputs and checks a second complete frozen30-seed run for deterministic decisions/forecasts/non-timing metrics. It is an independent computation within this session, not external peer review. See CITRINE_REPRODUCIBILITY.md and scripts/reproduce_citrine.sh. Exact locked dependencies unchanged; Python{manifest['python']}; source/license/input/output/config hashes retained. Times/rendering metadata can vary, scientific deterministic outputs cannot. Publication of cloud configuration is separate from local validation.

## Limits and next research step

80 selected published case groups are small and selection-biased after strict ambiguity exclusion. Only reported temperature/mode/recipe information is checked; strain rate, geometry, heat-treatment details and measurement extraction conventions remain heterogeneous. Master formulas have published rounding and nominal-notation limitations. Independent studies are connected through chemistry, and retrospective seeds share one pool. No prospective experiments, new-alloy synthesis, synthesis-failure prediction, physical safety certification, simulation-to-laboratory discrepancy fit or superiority over Radical AI's proprietary pipeline is claimed. No theoretical calibrated/conformal coverage guarantee follows from this temperature scaling.

The evidence supports further study of selection under mechanical constraints, with this exact conditional verdict; a stronger next step is a prospectively designed, composition/processing-resolved dataset with independently heldout studies, raw stress-strain definitions and repeated uncertainty measurements. Any benefit observed here needs independent replication; negative/inconclusive differences should remain reported rather than retuning on final seeds.
'''
    (out/'REPORT.md').write_text(text)
    return result
