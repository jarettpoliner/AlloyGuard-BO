"""Independent result checks: no acquisition/replay helper used to recompute metrics."""
from pathlib import Path
import hashlib,json,math
import numpy as np
import pandas as pd
from alloyguard_strength.replay import config_hash
R=Path(__file__).resolve().parents[1];O=R/'results/v2';E=O/'evaluation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((O/'v1_preservation.json').read_text());assert all(sha(R/p)==h for p,h in old.items()),'v1 changed'
cfg=json.loads((R/'configs/v2/frozen.json').read_text());assert cfg['config_hash']==config_hash(cfg)
assert all(sha(R/p)==h for p,h in cfg['frozen_files'].items()),'Frozen science changed'
co=pd.read_csv(R/'results/citrine/cohort.csv').set_index('case_id')
checks=0;runs=0
for folder in sorted(E.iterdir()):
 if not folder.is_dir():continue
 c=json.loads((folder/'config.json').read_text());assert c['config_hash']==config_hash(c)
 manifest=json.loads((folder/'manifest.json').read_text());assert all(sha(folder/p)==h for p,h in manifest.items())
 tr=pd.read_json(folder/'traces.jsonl',lines=True);curves=pd.read_csv(folder/'curves.csv');metrics=pd.read_csv(folder/'metrics.csv')
 split=json.loads((folder/'split.json').read_text()) if (folder/'split.json').exists() else None
 for (seed,pol),g in tr.groupby(['seed','policy_name']):
  g=g.sort_values('selection_step');cv=curves[(curves.seed==seed)&(curves.policy==pol)].sort_values('step');m=metrics[(metrics.seed==seed)&(metrics.policy==pol)].iloc[0]
  initial=json.loads(cv.iloc[0].initial_ids);seen=list(initial);spent=0.;failures=0;best=max([co.loc[k].yield_strength_mpa for k in seen if co.loc[k].elongation_percent>=c['elongation_threshold_percent']],default=0.)
  bests=[best];y=[];p=[];noise=[]
  assert len(initial)==c['initial_size'] and len(g)==c['budget'] and len(cv)==c['budget']+1
  if split:
   assert set(initial)<=set(split['train_ids']);assert not set(co.loc[initial].leakage_group)&set(co.loc[split['target_ids']].leakage_group)
  for j,row in enumerate(g.to_dict('records'),1):
   case=co.loc[row['case_id']]
   assert row['case_id'] not in seen and row['diagnostics']['observed_ids']==seen
   assert row['observed_count']==len(seen) and row['selection_step']==j
   assert row['measured_strength_mpa']==case.yield_strength_mpa and row['measured_elongation_percent']==case.elongation_percent
   assert row['feasible']==(case.elongation_percent>=c['elongation_threshold_percent'])
   if split:assert row['case_id'] in split['target_ids']
   pp=row['feasibility_probability_calibrated'];assert 0<=pp<=1
   if pol in ['risk_threshold','risk_budget','cd_cbo','cd_risk_threshold']:
    assert math.isclose(row['predicted_risk_spent_before'],spent,abs_tol=1e-9)
    allowance=max(0,c['risk']['total_budget']-spent)/(c['budget']-j+1)
    minimum=0. if pol=='cd_cbo' else (max(0,1-allowance) if pol=='risk_budget' else c['risk']['minimum_probability'])
    assert math.isclose(row['minimum_probability'],minimum,abs_tol=1e-9)
    assert math.isclose(row['predicted_risk_allowance'],allowance,abs_tol=1e-9)
    assert bool(row['risk_fallback'])==(row['eligible_count']==0)
    if not row['risk_fallback']:assert pp+1e-12>=minimum
    else:assert pp<minimum
   spent+=1-pp;assert math.isclose(row['predicted_risk_spent_after'],spent,abs_tol=1e-8)
   assert math.isclose(row['predicted_risk_budget_overrun'],max(0,spent-c['risk']['total_budget']),abs_tol=1e-8)
   if pol.startswith('cd_'):
    from scipy.special import ndtr
    expected=np.clip(ndtr((row['elongation_log_mean']-np.log1p(c['elongation_threshold_percent']))/row['elongation_log_observation_std']),1e-7,1-1e-7)
    assert math.isclose(pp,expected,abs_tol=1e-8)
   assert math.isclose(row['strength_observation_std_mpa']**2-row['strength_latent_std_mpa']**2,625.,abs_tol=1e-5)
   y.append(float(row['feasible']));p.append(pp);failures+=not row['feasible']
   if row['feasible']:best=max(best,case.yield_strength_mpa)
   bests.append(best);assert cv.iloc[j].cumulative_failures==failures
   seen.append(row['case_id']);checks+=1
  assert np.allclose(cv.best_feasible_strength_mpa,bests)
  assert math.isclose(m.auc_mpa_evaluations,float(np.trapezoid(bests)),abs_tol=1e-7)
  assert m.failure_count==failures and math.isclose(m.best_feasible_at_15_mpa,best)
  y=np.array(y);p=np.clip(p,1e-7,1-1e-7)
  assert math.isclose(m.brier,float(np.mean((p-y)**2)),abs_tol=1e-8)
  assert math.isclose(m.log_loss,float(-np.mean(y*np.log(p)+(1-y)*np.log1p(-p))),abs_tol=1e-8)
  runs+=1
# Compare serialized JSON directly, avoiding pandas floating-point reader precision.
def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
new=rows(E/'primary/traces.jsonl');prior=rows(R/'results/citrine/primary/traces.jsonl')
lookup={(x['seed'],x['policy_name'],x['selection_step']):x for x in new}
for oldrow in prior:
 newrow=lookup[(oldrow['seed'],oldrow['policy_name'],oldrow['selection_step'])]
 for key,value in oldrow.items():
  if key in ['config_hash','diagnostics']:continue
  assert newrow[key]==value,(key,newrow[key],value)
 for key,value in oldrow['diagnostics'].items():
  if key!='fit_seconds':assert newrow['diagnostics'][key]==value,key
# Reproduction equality across all policies, ignoring only machine runtime.
repeat=rows(O/'reproduction/primary/traces.jsonl');assert len(new)==len(repeat)
for x,y in zip(new,repeat):
 x['diagnostics'].pop('fit_seconds');y['diagnostics'].pop('fit_seconds');assert x==y
for filename in ['metrics.csv','curves.csv']:
 a=pd.read_csv(E/'primary'/filename);b=pd.read_csv(O/'reproduction/primary'/filename)
 if 'fit_seconds' in a:a=a.drop(columns='fit_seconds');b=b.drop(columns='fit_seconds')
 pd.testing.assert_frame_equal(a,b,check_exact=True)
rep={'status':'PASSED','selections':len(repeat),'contract':'All trace fields and metrics exactly identical except measured fit time; curves exact.'}
(O/'reproduction.json').write_text(json.dumps(rep,indent=2)+'\n')
result={'status':'PASSED','v1_preserved_files':len(old),'audited_selections':checks,'audited_runs':runs,'exact_v1_baseline_selections':len(prior),'reproduced_primary_selections':len(repeat),'frozen_config_hash':cfg['config_hash'],'scope':'Independent verification code path, not external human review','limitations':['Seed intervals condition on reused cohort','Acquisition correctness checked by unit tests and full deterministic reproduction; trace audit does not independently refit every GP','No independent alloy dataset','Risk-budget feasibility can be impossible and overruns remain recorded']}
(O/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
