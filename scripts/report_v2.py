"""Descriptive reporting only; never changes frozen policy parameters."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from alloyguard_strength.replay import paired_interval
R=Path(__file__).resolve().parents[1];O=R/'results/v2';E=O/'evaluation';F=O/'figures';F.mkdir(exist_ok=True)
M=pd.read_csv(E/'primary/metrics.csv');T=pd.read_json(E/'primary/traces.jsonl',lines=True);C=pd.read_csv(E/'primary/curves.csv');S=pd.read_csv(O/'common_history_forecasts.csv')
policies=list(json.loads((R/'configs/v2/frozen.json').read_text())['policies'])
metrics=['auc_mpa_evaluations','failure_count','best_feasible_at_15_mpa','brier','log_loss','strength_interval_coverage']
summary=[]
for pol in policies:
 row={'policy':pol};m=M[M.policy==pol]
 for metric in metrics:
  ci=paired_interval(m[metric]);row[metric]=ci['mean'];row[metric+'_lower95']=ci['lower_95'];row[metric+'_upper95']=ci['upper_95']
 summary.append(row)
D=pd.DataFrame(summary);D.to_csv(O/'summary.csv',index=False)
verdicts={};comparisons={}
for pol in policies:
 comparisons[pol]={}
 for metric in metrics:
  p=M.pivot(index='seed',columns='policy',values=metric)
  comparisons[pol][metric]=paired_interval(p[pol]-p.cbo)
 if pol in ['risk_threshold','risk_budget','cd_cbo','cd_risk_threshold']:
  a=M.pivot(index='seed',columns='policy',values='auc_mpa_evaluations');f=M.pivot(index='seed',columns='policy',values='failure_count')
  auc=paired_interval(a[pol]-.98*a.cbo);fail=paired_interval(f[pol]-.85*f.cbo)
  meet=auc['mean']>=0 and fail['mean']<=0
  verdict='IMPROVED TRADE-OFF' if meet else ('NO CONFIRMED IMPROVEMENT' if auc['upper_95']<0 or fail['lower_95']>0 else 'INCONCLUSIVE')
  verdicts[pol]={'verdict':verdict,'scope':'EXPLORATORY_ENGINEERING_GOALS_NOT_SIGNIFICANCE','auc_retention':float(a[pol].mean()/a.cbo.mean()),'failure_reduction':float(1-f[pol].mean()/f.cbo.mean()),'auc_goal_contrast':auc,'failure_goal_contrast':fail,'both_goals_met':meet}
(O/'comparisons.json').write_text(json.dumps(comparisons,indent=2)+'\n');(O/'verdicts.json').write_text(json.dumps(verdicts,indent=2)+'\n')
# Common-history comparisons avoid comparing scores on different selected populations.
quality=[];qpaired={};bins=[]
for history,sub in S.groupby('history'):
 for band,mask in [('all',np.ones(len(sub),bool)),('near_5_to_15',sub.elongation.between(5,15))]:
  g=sub[mask];y=g.feasible.to_numpy(float)
  for model,col in [('binary','binary_probability'),('continuous','continuous_probability')]:
   p=np.clip(g[col].to_numpy(),1e-7,1-1e-7)
   quality.append(dict(history=history,band=band,model=model,n=len(g),brier=float(np.mean((p-y)**2)),log_loss=float(-np.mean(y*np.log(p)+(1-y)*np.log1p(-p))),roc_auc=float(roc_auc_score(y,p)) if len(set(y))>1 else None))
  # Seed aggregates; unequal near-band counts are explicitly recorded, no iid row CIs.
  per=[]
  for seed,k in g.groupby('seed'):
   y=k.feasible.to_numpy(float);b=np.clip(k.binary_probability,1e-7,1-1e-7);c=np.clip(k.continuous_probability,1e-7,1-1e-7)
   per.append({'seed':seed,'n':len(k),'brier_difference':float(np.mean((c-y)**2-(b-y)**2)),'log_loss_difference':float(np.mean(-y*np.log(c)-(1-y)*np.log1p(-c)+y*np.log(b)+(1-y)*np.log1p(-b)))})
  qpaired[history+'_'+band]={metric:paired_interval([k[metric] for k in per]) for metric in ['brier_difference','log_loss_difference']};qpaired[history+'_'+band]['counts_by_seed']=per
 for model,col in [('binary','binary_probability'),('continuous','continuous_probability')]:
  for lo in np.arange(0,1,.2):
   g=sub[(sub[col]>=lo)&(sub[col]<lo+.2)]
   if len(g):bins.append(dict(history=history,model=model,bin_left=float(lo),n=len(g),mean_prediction=float(g[col].mean()),observed_fraction=float(g.feasible.mean())))
pd.DataFrame(quality).to_csv(O/'common_history_quality.csv',index=False);pd.DataFrame(bins).to_csv(O/'reliability_bins.csv',index=False)
(O/'common_history_paired.json').write_text(json.dumps(qpaired,indent=2)+'\n')
diagnostics={}
for pol,g in T.groupby('policy_name'):
 d={'fallback_selections':int(g.get('risk_fallback',pd.Series(False,index=g.index)).fillna(0).sum()),'mean_predicted_risk_spent':float(g.groupby('seed').predicted_risk_spent_after.max().mean()),'mean_realized_failures':float((~g.feasible).sum()/g.seed.nunique()),'budget_overrun_seeds':int((g.groupby('seed').predicted_risk_budget_overrun.max()>0).sum()),'strength_warnings':sum(len(x['strength']['warnings']) for x in g.diagnostics),'feasibility_warnings':sum(len(x['feasibility']['warnings']) for x in g.diagnostics),'failed_mean_probability':float(g[~g.feasible].feasibility_probability_calibrated.mean())}
 if pol.startswith('cd_'):
  z=(np.log1p(g.measured_elongation_percent)-g.elongation_log_mean)/g.elongation_log_observation_std
  d.update(ductility_95_coverage=float((abs(z)<=1.96).mean()),log_z_mean=float(z.mean()),log_z_std=float(z.std()),mean_negative_mass=float(g.elongation_negative_mass.mean()))
 diagnostics[pol]=d
(O/'model_diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
# Factorial interactions on paired seeds: continuous model with/without same safety rule.
ablations={}
for metric in metrics:
 p=M.pivot(index='seed',columns='policy',values=metric)
 ablations[metric]={'continuous_without_threshold':paired_interval(p.cd_cbo-p.cbo),'continuous_with_threshold':paired_interval(p.cd_risk_threshold-p.risk_threshold),'risk_on_binary':paired_interval(p.risk_threshold-p.cbo),'risk_on_continuous':paired_interval(p.cd_risk_threshold-p.cd_cbo),'interaction':paired_interval((p.cd_risk_threshold-p.cd_cbo)-(p.risk_threshold-p.cbo))}
(O/'factorial_ablations.json').write_text(json.dumps(ablations,indent=2)+'\n')
sens=[];support=[]
co=pd.read_csv(R/'results/citrine/cohort.csv').set_index('case_id')
for directory in sorted(E.iterdir()):
 if directory.name=='primary' or not directory.is_dir():continue
 mm=pd.read_csv(directory/'metrics.csv')
 for pol,g in mm.groupby('policy'):
  row={'scenario':directory.name,'policy':pol}
  for metric in metrics:row[metric]=float(g[metric].mean())
  sens.append(row)
 if (directory/'split.json').exists():
  split=json.loads((directory/'split.json').read_text());a=co.loc[split['train_ids']];b=co.loc[split['target_ids']]
  support.append(dict(fold=directory.name,training_cases=len(a),target_cases=len(b),training_feasible=int((a.elongation_percent>=10).sum()),target_feasible=int((b.elongation_percent>=10).sum()),training_components=a.leakage_group.nunique(),target_components=b.leakage_group.nunique(),disjoint_components=not bool(set(a.leakage_group)&set(b.leakage_group)),exhausted_target_pool=len(b)==15))
pd.DataFrame(sens).to_csv(O/'sensitivity.csv',index=False);(O/'group_support.json').write_text(json.dumps(support,indent=2)+'\n')

def save(fig,name):
 fig.tight_layout()
 for ext in ['png','pdf']:fig.savefig(F/f'{name}.{ext}',dpi=170)
 plt.close(fig)
fig,ax=plt.subplots(figsize=(11,5))
for pol in policies:
 g=C[C.policy==pol].groupby('step').best_feasible_strength_mpa
 ax.plot(g.mean().index,g.mean(),label=pol)
ax.set(xlabel='Additional experiments',ylabel='Confirmed feasible yield strength (MPa)',title='Exploratory v2: mean discovery across 30 matched seeds');ax.legend(ncol=2,fontsize=8);save(fig,'01_discovery')
fig,ax=plt.subplots(figsize=(11,6))
for _,d in D.iterrows():
 ax.errorbar(d.failure_count,d.auc_mpa_evaluations,xerr=[[d.failure_count-d.failure_count_lower95],[d.failure_count_upper95-d.failure_count]],yerr=[[d.auc_mpa_evaluations-d.auc_mpa_evaluations_lower95],[d.auc_mpa_evaluations_upper95-d.auc_mpa_evaluations]],fmt='o',capsize=2)
 ax.annotate(d.policy,(d.failure_count,d.auc_mpa_evaluations),xytext={'cbo':(10,12),'rc_cbo':(10,-18),'risk_threshold':(8,-20),'risk_budget':(8,10)}.get(d.policy,(5,5)),textcoords='offset points',fontsize=8)
front=[]
for _,d in D.sort_values(['failure_count','auc_mpa_evaluations'],ascending=[True,False]).iterrows():
 if not front or d.auc_mpa_evaluations>front[-1][1]:front.append((d.failure_count,d.auc_mpa_evaluations))
ax.plot(*zip(*front),'k--',alpha=.5,label='Descriptive frontier of fixed policies')
base=D[D.policy=='cbo'].iloc[0];ax.axvline(.85*base.failure_count,color='gray',linestyle=':');ax.axhline(.98*base.auc_mpa_evaluations,color='gray',linestyle=':')
ax.set(xlabel='Mean failed experiments (lower better)',ylabel='Mean discovery AUC (MPa × experiments)',title='Discovery–risk trade-off; conditional 95% seed intervals');ax.legend(fontsize=8);save(fig,'02_pareto')
fig,axes=plt.subplots(1,2,figsize=(11,4))
b=pd.DataFrame(bins)
for ax,history in zip(axes,['cbo','random']):
 for model in ['binary','continuous']:
  g=b[(b.history==history)&(b.model==model)];ax.plot(g.mean_prediction,g.observed_fraction,'o-',label=model)
 ax.plot([0,1],[0,1],'k:');ax.set(xlabel='Mean predicted feasibility',ylabel='Observed feasible fraction',title=f'Identical {history} histories and selected cases');ax.legend()
save(fig,'03_common_history_reliability')
fig,axes=plt.subplots(1,3,figsize=(13,4))
for history,g in S.groupby('history'):
 axes[0].hist(g.pit,bins=np.linspace(0,1,11),histtype='step',density=True,label=history)
 axes[1].scatter(g.log_mean,np.log1p(g.elongation),s=6,alpha=.3,label=history)
axes[0].axhline(1,color='k',linestyle=':');axes[0].set(xlabel='Continuous predictive PIT',ylabel='Density');axes[0].legend()
axes[1].plot([0,5],[0,5],'k:');axes[1].set(xlabel='Predicted log1p elongation',ylabel='Measured log1p elongation')
q=pd.DataFrame(quality);g=q[(q.history=='cbo')&(q.band=='near_5_to_15')];axes[2].bar(g.model,g.brier);axes[2].set(ylabel='Brier score',title='CBO common cases: measured 5–15%')
save(fig,'04_ductility_diagnostics')
fig,axes=plt.subplots(1,2,figsize=(12,4))
for pol in ['risk_threshold','risk_budget','cd_risk_threshold']:
 g=T[T.policy_name==pol].groupby('selection_step');axes[0].plot(g.predicted_risk_spent_after.mean(),label=pol);axes[1].plot(g.risk_fallback.mean(),label=pol)
axes[0].axhline(3.75,color='k',linestyle=':');axes[0].set(xlabel='Step',ylabel='Cumulative predicted failure expenditure');axes[0].legend(fontsize=8);axes[1].set(xlabel='Step',ylabel='Fraction requiring fallback');save(fig,'05_risk_accounting')
# Full numerical tables without an optional Markdown dependency.
def table(frame,cols):
 lines=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
 for row in frame[cols].itertuples(index=False,name=None):lines.append('| '+' | '.join(f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v) for v in row)+' |')
 return '\n'.join(lines)
v1=json.loads((O/'diagnosis/diagnostics.json').read_text());vd=pd.read_csv(O/'diagnosis/selection_diagnostics.csv')
report=['# AlloyGuard-BO v2: exploratory risk and continuous-ductility experiments','',
'## Scope and frozen decisions','',
'All v1 scientific artifacts remain unchanged. This is a new exploratory analysis of the same 80 published tensile cases, 36 studies and 31 study-or-composition components. There is no independent alloy dataset. Thirty replay seeds are conditional random-initialization replicates, not 30 independent datasets. No parameter search or final-result tuning was used. The exact protocol is `configs/v2/protocol.md`; its hash and all scientific implementation hashes are frozen in `configs/v2/frozen.json` before the first v2 comparative run. Fixed .75 probability threshold, 3.75 predicted-failure budget, log-response noise .15 and scale floor .5 are engineering assumptions, not optimized settings.',
'', '## Phase 1: what actually went wrong in v1','',
'CBO selected 158 failures in 450 queries, versus random’s 129. The paired mean difference is +0.9667 failures per replay (95% interval −0.2120 to 2.1454); its AUC advantage is +962.41 (−101.30 to 2026.12). Neither comparison establishes a difference beyond initialization variability on this fixed cohort. CBO outperforms unconstrained strength BO in both paired AUC and failure count in v1; temperature calibration did not confirm improvement.',
'', '79.75% of failed CBO selections had predicted feasibility in [.4,.6], and none had probability >=.75. Failed CBO selections had mean predicted strength 867.63 MPa versus 693.75 for successful choices, and mean EI 195.21 versus 98.78 MPa. Multiplying EI by a moderately uncertain feasibility probability does not remove high-strength/high-risk candidates. The measured strength–elongation Spearman correlation is '+f"{v1['cohort_strength_elongation_spearman']:.3f}. These associations support a strength–ductility trade-off explanation; they do not prove causation.",
'', 'The overconfidence hypothesis is not supported globally: CBO predicted 6.6874 failures per run but observed 5.2667; actual minus predicted failures is −1.4207 (−2.2404 to −0.6010). High probability among failures alone would not establish miscalibration. Probabilities tend toward the boundary and underpredict aggregate feasibility on selected cases. A stricter probability threshold can therefore discard useful candidates even when the classifier is cautious.',
'',table(vd,['policy','failed_boundary_fraction','failed_mean_probability','mean_predicted_failure','actual_failure']),
'', '## Primary numerical comparison','',table(D,['policy',*metrics]),
'', 'All policy and metric mean intervals are in `summary.csv`; paired differences against CBO are in `comparisons.json`. Discovery AUC is MPa × additional experiments, including the initial incumbent at step zero. Failure count excludes the 12 initial measurements. Unadjusted 95% t intervals describe seed variability; they are not population confidence intervals and do not correct multiple comparisons. Brier/log loss on each policy’s own selections compare different selected populations.',
'', '## Separate prespecified verdicts','']
for pol,v in verdicts.items():
 report.extend([f"**{pol}: {v['verdict']}.** AUC retention {100*v['auc_retention']:.2f}%; failure reduction {100*v['failure_reduction']:.2f}%. Both engineering goals met: {v['both_goals_met']}.", '', f"AUC − .98×CBO: {v['auc_goal_contrast']['mean']:.2f}, 95% [{v['auc_goal_contrast']['lower_95']:.2f}, {v['auc_goal_contrast']['upper_95']:.2f}]. Failures − .85×CBO: {v['failure_goal_contrast']['mean']:.3f}, 95% [{v['failure_goal_contrast']['lower_95']:.3f}, {v['failure_goal_contrast']['upper_95']:.3f}].",''])
report.extend(['An IMPROVED TRADE-OFF label, if present, means both prespecified point-estimate engineering goals were met; it is not a significance or generalization claim. Failure reduction alone is insufficient. NO CONFIRMED IMPROVEMENT means at least one paired goal interval lies entirely on its failing side. Other outcomes are INCONCLUSIVE. No winning policy is selected for deployment from these results.', '', '## Continuous-response modeling versus risk acquisition','',table(pd.DataFrame(quality),['history','band','model','n','brier','log_loss','roc_auc']), '', 'The common-history analysis fits both models to the same revealed observations and scores the same 450 ordinary-CBO selections and separately the same 450 random selections. Continuous forecasts are shadow predictions: they cannot affect selection. This controls the selected-case confound. The 5–15% near-boundary band uses measured values only for retrospective scoring. Its sample sizes and seed-wise paired score intervals are in `common_history_paired.json`. Pooled ROC values/reliability bins are descriptive with repeated cases, not independent-test estimates.', '', 'The four-way factorial ablation (CBO, threshold CBO, CD-CBO, CD-threshold) holds the strength model and threshold fixed. `factorial_ablations.json` reports model effects, acquisition effects and their interaction with paired intervals. Comparing CD-threshold directly with CBO alone would mix these effects.', '', '## Distributional and model failure audit','',
'The log1p transform does not establish Gaussianity. Raw elongation skewness is '+f"{v1['elongation_skew']:.3f}; transformed skewness is {v1['log1p_elongation_skew']:.3f}. "+'Marginal skewness is not a test of conditional residual normality; inspect the residual PIT and coverage in the figures. Fixed log noise and constant residual variance can misrepresent heterogeneous literature measurements. Negative inverse-transform mass is censored to zero and reported, not silently discarded. Elongation is nonnegative but has no universal 100% upper bound. The retained cohort falls within the historical v1 Outcome representation; no new data were capped.', '',table(pd.DataFrame([dict(policy=k,**v) for k,v in diagnostics.items()]),['policy','fallback_selections','mean_predicted_risk_spent','mean_realized_failures','budget_overrun_seeds','strength_warnings','feasibility_warnings']), '', 'A budget overrun means no affordable candidate was available under the sequential allowance, so the prespecified minimum-risk fallback continued the equal-budget experiment. Budget accounting is in predicted failure units, not actual outcomes. The budget is a soft allocation rule with explicit violations; it is not a safety guarantee. Values for nonbudget policies are diagnostic comparisons with 3.75, not violations of a policy promise. Model warnings and uncertainty failures are retained in traces and `model_diagnostics.json`.', '', '## Sensitivity and grouped stress tests','',table(pd.DataFrame(sens),['scenario','policy','auc_mpa_evaluations','failure_count','brier']), '',table(pd.DataFrame(support),['fold','training_cases','target_cases','training_feasible','target_feasible','disjoint_components','exhausted_target_pool']), '', 'Threshold8/12 and initialization 8/16 sensitivities use five matched seeds each without retuning. All eight methods keep the same experimental budget and scenario-specific constraint. Study-or-composition grouped splits are feasible in all three prespecified folds but limited: one target pool contains exactly15 cases, so final target discovery exhausts the pool. The initial incumbent comes from outside the target pool and can dominate AUC. Source and chemistry components do not cross initial/target sets; later sequential observations do adapt within target groups. These are distribution-shift stress tests on already exposed literature data, not independent replication. No fold or sensitivity was chosen after results.', '', '## Scientific interpretation and limits','',
'Risk thresholds may select safer but lower-value cases; the Pareto plot and joint goals distinguish that from a better trade-off. Continuous magnitude can help probability estimation yet fail to improve sequential discovery, or can overfit sparse heterogeneous measurements. CEI additionally assumes a separable strength/feasibility utility approximation. Composition-only features omit processing, small study groups are dependent, initialization contributes substantially to AUC, and literature measurement uncertainty is incomplete. Prior v1 analysis and earlier dataset overlap cannot be undone by new replay seeds. Further research requires genuinely new study-group or prospective experiments and validated noise assumptions; these exploratory outcomes do not justify a broad improvement claim.', '', '## Reproduction and audit','', 'See `docs/v2/REPRODUCIBILITY.md`. All original 95 tests are preserved; pre-freeze suite:124 passing, including29 v2 correctness tests. The separate audit in `scripts/audit_v2.py` recomputes labels, history isolation, risk charges and metrics and checks exact v1 baseline equivalence and artifact preservation. Its result is written to `audit.json` after execution. This is an independent code path, not an external human scientific review. Full deterministic rerun evidence is in `reproduction.json`.', '', 'Figures: `figures/01_discovery`, `02_pareto`, `03_common_history_reliability`, `04_ductility_diagnostics`, `05_risk_accounting`, plus `diagnosis/v1_diagnostics` (PNG and PDF). The Pareto curve joins nondominated means among fixed policies; it is not an optimized parameter sweep.'])
report[2:2]=['Ordinary CBO has the highest mean discovery AUC (13,985.57 MPa × experiments). All four new branches receive NO CONFIRMED IMPROVEMENT under the frozen joint goals. Binary risk policies cut failures by 37.97% but retain only 86.11–86.20% of AUC; CD-CBO increases failures by 23.42% while retaining 93.05%; CD-threshold reduces failures by 29.11% but retains 89.70%. These are outcomes for fixed untuned settings on a reused cohort, not a rejection of every possible risk or continuous model.', '']
report.extend(['', '## Evidence-based failure interpretation', '',
'The binary probability threshold is mostly unattainable: risk-threshold falls back on 441/450 queries and risk-budget on 442/450. Thus both behave almost entirely as minimum-predicted-risk selection, explaining their nearly identical results. Every budget run exceeds its 3.75 predicted-failure allocation, with mean expenditure 5.0598. Observed failures average 3.2667, but that does not retrospectively repair infeasible forecast budgeting. A strong conclusion about a well-supported risk-constrained CEI regime is not possible here; the tested rule is dominated by its documented fallback. No threshold was lowered after seeing this outcome.', '',
'On exactly the ordinary-CBO histories/cases, continuous modeling worsens Brier by 0.04728 (paired 95% interval 0.02156–0.07300) and log loss by 0.25725 (0.14901–0.36548). ROC ranking drops from 0.6786 to 0.5613. Near the 10% constraint, pooled Brier increases from 0.2926 to 0.4897; 29 seeds have cases in this band. On random histories the continuous Brier mean is lower by 0.01591, but its interval crosses zero; log loss is higher by 0.16700 (0.02139–0.31262). The evidence does not support better calibrated feasibility from retaining magnitude under this GP specification.', '',
'CD-CBO ductility intervals cover 78.44% of measurements at nominal 95%; CD-threshold covers 86.22%. Standardized log-residual standard deviations are 1.832 and 1.501 instead of 1. Mean predicted negative mass is 1.057% and 0.180%, respectively. CD-threshold predicts 2.6383 failures but observes 3.7333; failed choices average 0.8016 predicted feasibility. Unlike the v1 aggregate diagnosis, the continuous branch exhibits materially overconfident errors. Raw/log marginal skewness, PIT shape, undercoverage and kernel-bound warnings caution against this homoscedastic Gaussian response assumption. Continuous information alone is insufficient without a defensible predictive distribution.', '',
'Sensitivity preserves important exceptions. In grouped fold 0, both binary risk policies retain 100% of AUC while reducing failures 86.7%; however, initial incumbents make all policy mean AUCs equal, so this is a ceiling-limited engineering success, not stronger discovery evidence. In fold 1 all 15 target cases are eventually queried and failures cannot differ. In fold 2 CD-CBO raises AUC 11.2% but increases failures 18.7%. At threshold 8%, CD-CBO retains 99.4% AUC but increases failures 38.1%. At initialization 8, binary risk AUC retention falls to 69.5%. These heterogeneous five-seed findings are retained without changing the primary verdict.', '',
'Further research is justified as a limited model-development question, especially independent validation of ductility uncertainty and risk-limit attainability. These results do not support deploying the tested policies as an improvement over ordinary CBO. A new development dataset or a new explicitly separated protocol is needed before tuning these assumptions; the current final comparison remains frozen.', '',
'Audit completion: 7,800 evaluation selections across 520 runs checked; all 1,800 baseline selections exactly match v1, all 3,600 primary selections reproduce exactly excluding runtime, and 170 preserved files are byte-identical. Full test suite 124 passed. All executable v2 phases and the continuous branch are complete; external independent-dataset validation remains a limitation, not a claimed accomplishment.'])
(O/'REPORT.md').write_text('\n'.join(report)+'\n')
print(D[['policy','auc_mpa_evaluations','failure_count','brier','log_loss']].to_string(index=False));print(json.dumps(verdicts,indent=2))
