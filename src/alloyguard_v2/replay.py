"""v2 orchestration: reuse the private outcome oracle; never pass it to selection."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from alloyguard_strength.schema import Observation
from alloyguard_strength.replay import OutcomeOracle,summarize
from .policies import select,RiskLedger,POLICIES

def replay(candidates,outcomes,config,seed,policy,initial_ids=None,target_ids=None):
    candidates=tuple(sorted(candidates,key=lambda c:c.case_id));byid={c.case_id:c for c in candidates}
    if len(byid)!=len(candidates):raise ValueError('Duplicate cases')
    if initial_ids is None:
        idx=np.random.default_rng(seed).choice(len(candidates),config['initial_size'],replace=False)
        initial_ids=tuple(candidates[int(i)].case_id for i in idx)
    if len(set(initial_ids))!=len(initial_ids):raise ValueError('Duplicate initial IDs')
    available=set(byid) if target_ids is None else set(target_ids)
    if target_ids is not None and (set(initial_ids)&available or {byid[k].leakage_group for k in initial_ids}&{byid[k].leakage_group for k in available}):
        raise ValueError('Heldout group overlap')
    if len(available-set(initial_ids))<config['budget']:raise ValueError('Insufficient candidates')
    oracle=OutcomeOracle(outcomes);obs=tuple(Observation(byid[k],oracle.reveal(k)) for k in initial_ids)
    ledger=RiskLedger(config['risk']['total_budget'],config['budget']);traces=[];curves=[];failures=0
    def curve(step):
        good=[o.outcome.yield_strength_mpa for o in obs if o.outcome.elongation_percent>=config['elongation_threshold_percent']]
        return dict(seed=seed,policy=policy,step=step,best_feasible_strength_mpa=max(good,default=0.),has_feasible=bool(good),cumulative_failures=failures,initial_ids=json.dumps(initial_ids))
    curves.append(curve(0))
    for step in range(1,config['budget']+1):
        seen={o.candidate.case_id for o in obs}
        pool=tuple(c for c in candidates if c.case_id in available and c.case_id not in seen)
        row=select(obs,pool,config,policy,seed,step,ledger)
        # Charge immutable, pre-reveal prediction; never charge the realized label.
        ledger=ledger.charge(row['feasibility_probability_calibrated'])
        row.update(predicted_risk_spent_after=ledger.spent,predicted_risk_budget_overrun=max(0.,-ledger.remaining))
        result=oracle.reveal(row['case_id'])
        row.update(seed=seed,measured_strength_mpa=result.yield_strength_mpa,measured_elongation_percent=result.elongation_percent,feasible=result.elongation_percent>=config['elongation_threshold_percent'])
        traces.append(row);failures+=int(not row['feasible']);obs=(*obs,Observation(byid[row['case_id']],result));curves.append(curve(step))
    return traces,curves

def run(candidates,outcomes,config,output,split=None):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    metrics=[];curves=[]
    with (output/'traces.jsonl').open('w') as log:
        for seed in config['seeds']:
            initial=None;target=None
            if split is not None:
                train,target=split
                initial=tuple(np.random.default_rng(seed).choice(sorted(train),config['initial_size'],replace=False))
            for policy in config['policies']:
                tr,cv=replay(candidates,outcomes,config,seed,policy,initial,target)
                for row in tr:log.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
                metrics.append(summarize(tr,cv));curves.extend(cv)
            log.flush()
            print(f'{output.name}: seed {seed} complete',flush=True)
    pd.DataFrame(metrics).to_csv(output/'metrics.csv',index=False);pd.DataFrame(curves).to_csv(output/'curves.csv',index=False)
    (output/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    if split is not None:(output/'split.json').write_text(json.dumps({'train_ids':sorted(split[0]),'target_ids':sorted(split[1])},indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()},indent=2)+'\n')
