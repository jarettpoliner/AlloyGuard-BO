"""Read-only v1 diagnostics; all output is confined to v2."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr,skew
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from alloyguard_strength.replay import paired_interval
r=Path(__file__).resolve().parents[1];out=r/'results/v2/diagnosis';out.mkdir(exist_ok=True)
t=pd.read_json(r/'results/citrine/primary/traces.jsonl',lines=True);m=pd.read_csv(r/'results/citrine/primary/metrics.csv')
co=pd.read_csv(r/'results/citrine/cohort.csv')
rows=[]
for pol,f in t.groupby('policy_name'):
 failed=f[~f.feasible];prob=f.feasibility_probability_calibrated
 rows.append(dict(policy=pol,selections=len(f),failures=len(failed),mean_predicted_failure=(1-prob).mean(),actual_failure=(~f.feasible).mean(),failed_mean_probability=failed.feasibility_probability_calibrated.mean(),failed_boundary_fraction=failed.feasibility_probability_calibrated.between(.4,.6).mean(),failed_high_probability_fraction=(failed.feasibility_probability_calibrated>=.75).mean(),failed_predicted_strength=failed.strength_mean_mpa.mean(),success_predicted_strength=f[f.feasible].strength_mean_mpa.mean(),failed_EI=failed.expected_improvement_mpa.mean(),success_EI=f[f.feasible].expected_improvement_mpa.mean(),failed_CEI=failed.constrained_expected_improvement_mpa.mean(),success_CEI=f[f.feasible].constrained_expected_improvement_mpa.mean()))
d=pd.DataFrame(rows);d.to_csv(out/'selection_diagnostics.csv',index=False)
comparisons={}
for metric in ['auc_mpa_evaluations','failure_count','brier']:
 pivot=m.pivot(index='seed',columns='policy',values=metric)
 for pol in ['random','strength_bo','rc_cbo']:
  comparisons[f'cbo_minus_{pol}_{metric}']=paired_interval(pivot.cbo-pivot[pol])
residuals={}
for pol,f in t.groupby('policy_name'):
 vals=f.assign(residual=(~f.feasible).astype(float)-(1-f.feasibility_probability_calibrated)).groupby('seed').residual.sum()
 residuals[pol]=paired_interval(vals)
summary=dict(paired_comparisons=comparisons,actual_minus_predicted_failures_per_seed=residuals,cohort_strength_elongation_spearman=float(spearmanr(co.yield_strength_mpa,co.elongation_percent).statistic),elongation_skew=float(skew(co.elongation_percent)),log1p_elongation_skew=float(skew(np.log1p(co.elongation_percent))),interpretation='Conditional replay variability; repeated cases and adaptive selection. Outcome-conditioned failed probabilities alone are not calibration evidence.')
(out/'diagnostics.json').write_text(json.dumps(summary,indent=2)+'\n')
fig,ax=plt.subplots(1,3,figsize=(15,4))
for pol,f in t.groupby('policy_name'):
 ax[0].hist(f[~f.feasible].feasibility_probability_calibrated,bins=np.linspace(0,1,11),histtype='step',label=pol)
ax[0].axvspan(.4,.6,alpha=.1);ax[0].set(xlabel='Predicted feasibility of failed selections',ylabel='Count');ax[0].legend(fontsize=7)
f=t[t.policy_name=='cbo'];sc=ax[1].scatter(f.strength_mean_mpa,f.expected_improvement_mpa,c=f.feasibility_probability_raw,cmap='viridis',s=10)
ax[1].scatter(f[~f.feasible].strength_mean_mpa,f[~f.feasible].expected_improvement_mpa,facecolors='none',edgecolors='red',s=20,label='Failed');ax[1].legend();ax[1].set(xlabel='CBO predicted strength (MPa)',ylabel='Expected improvement (MPa)');fig.colorbar(sc,ax=ax[1],label='Predicted feasibility')
ax[2].bar(d.policy,d.actual_failure,label='Actual failure fraction',alpha=.6);ax[2].plot(d.policy,d.mean_predicted_failure,'ko',label='Mean predicted risk');ax[2].tick_params(axis='x',rotation=30);ax[2].legend(fontsize=8);ax[2].set(ylabel='Failure fraction')
fig.suptitle('All 30 v1 replay seeds — exploratory diagnostics');fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(out/f'v1_diagnostics.{ext}',dpi=160)
print(d.to_string(index=False));print(json.dumps(summary,indent=2))
