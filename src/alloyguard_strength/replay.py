"""Typed hidden-outcome replay with a hard scientific-cohort freeze guard."""
from __future__ import annotations
from dataclasses import asdict
import hashlib,json,time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t
from .schema import Candidate,Outcome,Observation
from .policies import select_next,POLICIES

class OutcomeOracle:
    __slots__=("__outcomes","__seen")
    def __init__(self,outcomes:dict[str,Outcome]):self.__outcomes=dict(outcomes);self.__seen=set()
    def reveal(self,case_id:str)->Outcome:
        if case_id in self.__seen:raise ValueError("Case already revealed")
        outcome=self.__outcomes[case_id];self.__seen.add(case_id);return outcome

def config_hash(config:dict)->str:
    value={k:v for k,v in config.items() if k!="config_hash"}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def method_hash()->str:
    paths=sorted(Path(__file__).parent.glob("*.py"))
    return hashlib.sha256(b"".join(p.name.encode()+p.read_bytes() for p in paths)).hexdigest()

def require_scientific_cohort(config:dict,qualification:dict,cohort_ids:list[str])->None:
    if qualification.get("G1b")!="COMPLETE" or not cohort_ids:
        raise ValueError("FINAL_BENCHMARK_BLOCKED_G1B: no source-qualified cohort")
    if not config.get("final_protocol_frozen"):
        raise ValueError("FINAL_BENCHMARK_BLOCKED_PROTOCOL_NOT_FROZEN")
    if config.get("config_hash")!=config_hash(config):raise ValueError("Frozen config changed")
    if config.get("source_hash")!=method_hash():raise ValueError("Frozen scientific source changed")
    digest=hashlib.sha256(json.dumps(sorted(cohort_ids)).encode()).hexdigest()
    if digest!=config.get("cohort_ids_hash"):raise ValueError("Cohort changed after freezing")

def replay(candidates:tuple[Candidate,...],outcomes:dict[str,Outcome],config:dict,seed:int,
           policy_name:str,initial_ids:tuple[str,...]|None=None,target_ids:set[str]|None=None):
    candidates=tuple(sorted(candidates,key=lambda c:c.case_id));byid={c.case_id:c for c in candidates}
    if len(byid)!=len(candidates):raise ValueError("Duplicate independent cases")
    if initial_ids is None:
        idx=np.random.default_rng(seed).choice(len(candidates),config["initial_size"],replace=False)
        initial_ids=tuple(candidates[int(i)].case_id for i in idx)
    if len(set(initial_ids))!=len(initial_ids):raise ValueError("Repeated initialization case")
    if target_ids is not None:
        if set(initial_ids)&target_ids:raise ValueError("Observed/target overlap")
        initial_groups={byid[k].leakage_group for k in initial_ids}
        target_groups={byid[k].leakage_group for k in target_ids}
        if initial_groups&target_groups:raise ValueError("Study/composition group crossed held-out split")
    available=set(byid) if target_ids is None else set(target_ids)
    if len(available-set(initial_ids))<config["budget"]:raise ValueError("Insufficient candidate budget")
    oracle=OutcomeOracle(outcomes)
    observed=tuple(Observation(byid[k],oracle.reveal(k)) for k in initial_ids)
    traces=[];curves=[];failures=0
    def curve(step):
        feasible=[o.outcome.yield_strength_mpa for o in observed if o.outcome.elongation_percent>=config["elongation_threshold_percent"]]
        return {"seed":seed,"policy":policy_name,"step":step,"best_feasible_strength_mpa":max(feasible,default=0.),
                "has_feasible":bool(feasible),"cumulative_failures":failures,"initial_ids":json.dumps(initial_ids)}
    curves.append(curve(0))
    for step in range(1,config["budget"]+1):
        seen={o.candidate.case_id for o in observed}
        remaining=tuple(c for c in candidates if c.case_id in available and c.case_id not in seen)
        decision=select_next(observed,remaining,config,policy_name,seed,step)
        result=oracle.reveal(decision.case_id)
        row=asdict(decision);row.update(seed=seed,measured_strength_mpa=result.yield_strength_mpa,
            measured_elongation_percent=result.elongation_percent,feasible=result.elongation_percent>=config["elongation_threshold_percent"])
        traces.append(row);failures+=int(not row["feasible"])
        observed=(*observed,Observation(byid[decision.case_id],result));curves.append(curve(step))
    return traces,curves

def summarize(traces:list[dict],curves:list[dict])->dict:
    y=np.array([r["feasible"] for r in traces],float)
    p=np.clip([r["feasibility_probability_calibrated"] for r in traces],1e-7,1-1e-7)
    raw=np.clip([r["feasibility_probability_raw"] for r in traces],1e-7,1-1e-7)
    residual=np.array([r["measured_strength_mpa"]-r["strength_mean_mpa"] for r in traces])
    sd=np.array([r["strength_observation_std_mpa"] for r in traces])
    first=next((r["step"] for r in curves if r["has_feasible"]),None)
    output={"seed":traces[0]["seed"],"policy":traces[0]["policy_name"],
        "auc_mpa_evaluations":float(np.trapezoid([r["best_feasible_strength_mpa"] for r in curves])),
        "failure_count":int((1-y).sum()),"failure_fraction":float((1-y).mean()),
        "brier":float(np.mean((p-y)**2)),"brier_raw":float(np.mean((raw-y)**2)),
        "log_loss":float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p))),
        "strength_mae_mpa":float(abs(residual).mean()),
        "strength_nll":float(np.mean(.5*np.log(2*np.pi*sd**2)+.5*(residual/sd)**2)),
        "strength_interval_coverage":float((abs(residual)<=1.96*sd).mean()),
        "time_to_first_feasible":first,"first_feasible_censored":first is None,
        "calibration_active_steps":sum(r["calibration_status"]=="CALIBRATION_ACTIVE" for r in traces),
        "ranking_changes":sum(r["raw_winner"]!=r["calibrated_winner"] for r in traces),
        "fit_seconds":sum(r["diagnostics"]["fit_seconds"] for r in traces)}
    for step in (5,10,15):
        if step<len(curves):output[f"best_feasible_at_{step}_mpa"]=curves[step]["best_feasible_strength_mpa"]
    return output

def run_suite(candidates:tuple[Candidate,...],outcomes:dict[str,Outcome],config:dict,output:Path,
              mode:str,qualification:dict|None=None):
    if mode=="FINAL_SCIENTIFIC":require_scientific_cohort(config,qualification or {},[c.case_id for c in candidates])
    elif mode not in ("PROVISIONAL_SOFTWARE_VALIDATION","SYNTHETIC_CORRECTNESS"):
        raise ValueError("Explicit run mode required")
    if config.get("config_hash")!=config_hash(config):raise ValueError("Configuration hash mismatch")
    output=Path(output)
    if output.exists():raise FileExistsError("Choose a new output directory; preserved runs are immutable")
    output.mkdir(parents=True);start=time.perf_counter();all_curves=[];metrics=[]
    with (output/"traces.jsonl").open("w") as log:
        for seed in config["seeds"]:
            for policy in POLICIES:
                traces,curves=replay(candidates,outcomes,config,seed,policy)
                for row in traces:log.write(json.dumps(row,sort_keys=True,allow_nan=False)+"\n")
                all_curves.extend(curves);metrics.append(summarize(traces,curves))
            log.flush()
    pd.DataFrame(metrics).to_csv(output/"metrics.csv",index=False)
    pd.DataFrame(all_curves).to_csv(output/"curves.csv",index=False)
    (output/"config.json").write_text(json.dumps(config,indent=2)+"\n")
    manifest={"status":"COMPLETED","mode":mode,"scientific_conclusions_allowed":mode=="FINAL_SCIENTIFIC",
        "config_hash":config["config_hash"],"source_hash":method_hash(),"dataset_hash":config["dataset_hash"],
        "seed_count":len(config["seeds"]),"policies":list(POLICIES),
        "selections":len(config["seeds"])*len(POLICIES)*config["budget"],"elapsed_seconds":time.perf_counter()-start,
        "artifact_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def paired_interval(differences):
    x=np.asarray(differences,float)
    if len(x)<2:raise ValueError("At least two paired seeds required")
    mean=float(x.mean());half=float(t.ppf(.975,len(x)-1)*x.std(ddof=1)/np.sqrt(len(x)))
    return {"mean":mean,"lower_95":mean-half,"upper_95":mean+half,"n":len(x)}
