"""Synthetic correctness evidence only: never included in real-data results."""
import os
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[name]="1"
import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/"tests"))
from helpers import toy,config
from alloyguard.policies import POLICIES
from alloyguard.replay import replay
from alloyguard.acquisition import expected_improvement
import numpy as np
if __name__=="__main__":
    cs,ys=toy(40); cfg=config(); cfg.update(initial_size=12,budget=8)
    results={}
    for policy in POLICIES:
        a,c,m=replay(cs,ys,cfg,31,policy)
        b,_,_=replay(cs,ys,cfg,31,policy)
        assert [r["alloy_id"] for r in a]==[r["alloy_id"] for r in b]
        assert len(a)==8 and len({r["alloy_id"] for r in a})==8
        assert all(0<r["feasibility_probability_raw"]<1 and r["acquisition_score"]>=0 for r in a)
        results[policy]={"selections":len(a),"deterministic":True}
    x=np.linspace(0,1,40)
    report={"status":"PASSED","purpose":"software verification only, not experimental evidence",
            "known_noiseless_feasible_optimum_gpa":float((3+8*x[x<=.45]).max()),
            "known_unconstrained_optimum_gpa":11.,"noise_seed":333,"policies":results}
    (root/"results/synthetic_verification.json").write_text(json.dumps(report,indent=2)+"\n")
    print(report)
