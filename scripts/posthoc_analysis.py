"""Descriptive analysis after freeze; never changes any selection method."""
import os
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[name]="1"
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(root/".matplotlib-cache"))
os.environ.setdefault("XDG_CACHE_HOME",str(root/".cache"))
import json
import pandas as pd
from alloyguard.data import problem_from_frame
from alloyguard.schema import Observation
from alloyguard.replay import load_config
from alloyguard.reporting import load_traces
from alloyguard.policies import select_next_alloy
if __name__=="__main__":
    m=pd.read_csv(root/"results/primary/metrics.csv")
    curves=pd.read_csv(root/"results/primary/curves.csv")
    traces=load_traces(root/"results/primary/traces.jsonl")
    p=m.pivot(index="seed",columns="policy",values="auc_gpa_evaluations")
    delta=p.cbo-p.hardness_bo
    cohorts={}
    for has in (False,True):
        seeds=curves[(curves.selection_step==0)&(curves.policy=="cbo")&(curves.has_feasible==has)].seed
        cohorts[f"initial_feasible_{has}"]={"seeds":seeds.tolist(),"count":len(seeds),
            "mean_cbo_minus_hardness_auc":float(delta.loc[seeds].mean()) if len(seeds) else None}
    worst=int(delta.idxmin())
    groups=pd.read_csv(root/"data/processed/compositions.csv")
    cs,ys=problem_from_frame(groups); byid={c.alloy_id:c for c in cs}
    case=json.loads((root/"results/representative_failure.json").read_text())
    ids=case["fit_diagnostics"]["observed_ids"]
    obs=tuple(Observation(byid[i],ys[i]) for i in ids)
    remain=tuple(c for c in cs if c.alloy_id not in set(ids))
    counter=select_next_alloy(obs,remain,load_config(root/"configs/benchmark_frozen.yaml"),"cbo",case["seed"],case["selection_step"])
    report={"label":"POSTHOC_DESCRIPTIVE_NO_METHOD_CHANGE", "initialization_cohorts":cohorts,
            "worst_cbo_vs_hardness_seed":worst,"worst_auc_difference":float(delta.loc[worst]),
            "worst_seed_traces":[{k:r[k] for k in ("policy_name","selection_step","alloy_id","selection_rationale","measured_hardness_gpa","measured_ductility_rank")} for r in traces if r["seed"]==worst and r["policy_name"] in ("cbo","hardness_bo")],
            "representative_failure":{"hardness_bo_alloy":case["alloy_id"],"seed":case["seed"],"step":case["selection_step"],
                "predicted_hardness_gpa":case["hardness_mean_gpa"],"raw_probability":case["feasibility_probability_raw"],
                "actual_hardness_gpa":case["measured_hardness_gpa"],"actual_rank":case["measured_ductility_rank"],
                "matched_observation_cbo_counterfactual_alloy":counter.alloy_id,
                "matched_observation_cbo_counterfactual_rank":ys[counter.alloy_id].ductility_rank,
                "matched_observation_cbo_counterfactual_hardness_gpa":ys[counter.alloy_id].hardness_gpa,
                "cbo_avoided_that_candidate":counter.alloy_id!=case["alloy_id"],
                "interpretation":"Posthoc one-step diagnostic from exactly the hardness-only observed set; not the sequential CBO run and not evidence of guaranteed risk avoidance."},
            "support_errors":{}}
    for name in ("NEAR_OBSERVED_CHEMISTRY","DISTANT_FROM_OBSERVATIONS"):
        rows=[r for r in traces if r["candidate_support_diagnostic"]==name]
        report["support_errors"][name]={"selected_forecasts":len(rows),"mean_abs_hardness_error_gpa":sum(abs(r["hardness_mean_gpa"]-r["measured_hardness_gpa"]) for r in rows)/len(rows) if rows else None,
                                       "note":"Adaptive selected forecasts, repeated pool observations; not a common held-out chemistry validation set"}
    (root/"results/posthoc_analysis.json").write_text(json.dumps(report,indent=2)+"\n")
    print({"worst_seed":worst,"cohorts":cohorts,"failure_case":report["representative_failure"]})
