"""Deterministic known strength/elongation functions: correctness only, no laboratory claim."""
import os
for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):os.environ[key]="1"
from pathlib import Path
import json
import numpy as np
import yaml
from alloyguard_strength.schema import Candidate,Outcome,Observation
from alloyguard_strength.policies import POLICIES,expected_improvement
from alloyguard_strength.calibration import GroupedTemperature
from alloyguard_strength.replay import replay,config_hash,summarize

if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    config=yaml.safe_load((root/"configs/strength_v3/development.yaml").read_text())
    config.update(initial_size=24,budget=5,dataset_hash="SYNTHETIC_NOT_EXPERIMENTAL")
    config["config_hash"]=config_hash(config)
    grid=np.linspace(0,1,72);rng=np.random.default_rng(91)
    candidates=tuple(Candidate(f"toy-{i:03d}",(float(x),float(1-x)),f"group-{i%12}","SYNTHETIC") for i,x in enumerate(grid))
    outcomes={c.case_id:Outcome(float(300+1800*x+rng.normal(0,2)),float(20*(1-x))) for c,x in zip(candidates,grid)}
    results={}
    for policy in POLICIES:
        a,curve=replay(candidates,outcomes,config,17,policy)
        b,_=replay(candidates,outcomes,config,17,policy)
        assert [r["case_id"] for r in a]==[r["case_id"] for r in b]
        assert len(a)==5 and len(set(r["case_id"] for r in a))==5
        assert all(r["acquisition_score"]>=0 and 0<r["feasibility_probability_raw"]<1 for r in a)
        results[policy]={"equal_budget":len(a),"deterministic":True}
    observed=tuple(Observation(c,outcomes[c.case_id]) for c in candidates[:60])
    calibration=GroupedTemperature(config["calibration"],config["feasibility"],10).fit(observed)
    assert calibration.status=="CALIBRATION_ACTIVE"
    for fold in calibration.folds:
        assert not set(fold["train_groups"])&set(fold["validation_groups"])
    ei=expected_improvement([2000,1200],[100,100],500)
    assert ei.argmax()==0 and (ei*[.01,.9]).argmax()==1
    evidence={"status":"PASSED","purpose":"software correctness only; not scientific evidence or measured materials",
        "noise_seed":91,"noise_sd_mpa":2,"known_continuous_feasible_optimum_mpa":1200.,
        "known_grid_feasible_optimum_noiseless_mpa":float((300+1800*grid[grid<=.5]).max()),
        "known_unconstrained_optimum_mpa":2100.,"constraint":"elongation=20*(1-x)>=10 percent",
        "active_group_calibration":True,"temperature":calibration.temperature,"policy_checks":results}
    (root/"results/strength_v3/synthetic_verification.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print({"synthetic_correctness":evidence["status"],"group_calibration_active":True})
