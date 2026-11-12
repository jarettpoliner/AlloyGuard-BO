"""Common-history prediction comparison; shadow forecasts never affect decisions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.special import ndtr
from alloyguard_citrine.data import load
from alloyguard_v2.policies import DuctilityGP
r=Path(__file__).resolve().parents[1];cfg=json.loads((r/'configs/v2/frozen.json').read_text());cs,ys=load(r);byid={c.case_id:c for c in cs}
source=pd.read_json(r/'results/citrine/primary/traces.jsonl',lines=True);rows=[]
for history in ['cbo','random']:
 for rec in source[source.policy_name==history].to_dict('records'):
  ids=rec['diagnostics']['observed_ids'];x=np.array([byid[k].composition_features for k in ids]);y=np.array([ys[k].elongation_percent for k in ids]);q=np.array([byid[rec['case_id']].composition_features])
  model=DuctilityGP(cfg['ductility']).fit(x,y);p,mu,sd,neg=model.predict(q,10.)
  actual=rec['measured_elongation_percent'];z=(np.log1p(actual)-mu[0])/sd[0]
  rows.append(dict(history=history,seed=rec['seed'],step=rec['selection_step'],case_id=rec['case_id'],binary_probability=rec['feasibility_probability_raw'],continuous_probability=float(p[0]),elongation=actual,feasible=rec['feasible'],log_mean=float(mu[0]),log_std=float(sd[0]),log_z=float(z),pit=float(ndtr(z)),covered=bool(abs(z)<=1.96),negative_mass=float(neg[0]),observed_ids=json.dumps(ids),warnings=json.dumps(model.model.diagnostics['warnings'])))
 pd.DataFrame(rows).to_csv(r/'results/v2/common_history_forecasts.csv',index=False)
 print(history+' shadow forecasts complete',flush=True)
