"""Experiment engine owns the oracle; policy receives only typed revealed inputs."""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import json
import platform
import time
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from .schema import Observation
from .oracle import OutcomeOracle
from .policies import POLICIES, select_next_alloy
from .metrics import summarize_run
from .data import sha256_file


def hash_config(config):
    clean={k:v for k,v in config.items() if k!="config_hash"}
    return hashlib.sha256(json.dumps(clean,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def load_config(path):
    cfg=yaml.safe_load(Path(path).read_text())
    if cfg.get("config_hash") and cfg["config_hash"]!=hash_config(cfg):
        raise ValueError("Frozen configuration hash mismatch")
    cfg["config_hash"]=hash_config(cfg)
    return cfg


def replay(candidates,outcomes,config,seed,policy_name):
    candidates=tuple(sorted(candidates,key=lambda c:c.alloy_id))
    if len({c.alloy_id for c in candidates})!=len(candidates):
        raise ValueError("Candidate IDs must be unique")
    size=config["initial_size"]; budget=config["budget"]
    if size<2 or size+budget>len(candidates):
        raise ValueError("Invalid initialization/evaluation budget")
    indices=np.random.default_rng(seed).choice(len(candidates),size=size,replace=False)
    initial=tuple(candidates[int(i)] for i in indices)
    oracle=OutcomeOracle(outcomes)
    observations=tuple(Observation(c,oracle.reveal(c.alloy_id)) for c in initial)
    traces=[]; curves=[]
    initial_ids={c.alloy_id for c in initial}
    def curve(step,failures):
        feasible=[o.outcome.hardness_gpa for o in observations if o.outcome.ductility_rank>=config["threshold"]]
        return {"seed":seed,"policy":policy_name,"selection_step":step,
                "best_feasible_hardness_gpa":max(feasible,default=0.),"has_feasible":bool(feasible),
                "cumulative_failures":failures,"initial_ids":json.dumps([c.alloy_id for c in initial])}
    curves.append(curve(0,0)); failures=0
    for step in range(1,budget+1):
        seen={o.candidate.alloy_id for o in observations}
        remaining=tuple(c for c in candidates if c.alloy_id not in seen)
        # No oracle reference or hidden targets cross this interface.
        decision=select_next_alloy(observations,remaining,config,policy_name,seed,step)
        chosen=next(c for c in remaining if c.alloy_id==decision.alloy_id)
        outcome=oracle.reveal(chosen.alloy_id)
        record=asdict(decision)
        feasible=outcome.ductility_rank>=config["threshold"]
        record.update(seed=seed,measured_hardness_gpa=outcome.hardness_gpa,
                      measured_ductility_rank=outcome.ductility_rank,measured_feasible=feasible)
        traces.append(record)
        observations=(*observations,Observation(chosen,outcome))
        failures+=int(not feasible)
        curves.append(curve(step,failures))
    assert len({r["alloy_id"] for r in traces})==budget
    assert not initial_ids.intersection(r["alloy_id"] for r in traces)
    return traces,curves,summarize_run(traces,curves,seed,policy_name)


def source_hash(root):
    paths=sorted((root/"src/alloyguard").glob("*.py"))
    return hashlib.sha256(b"".join(p.name.encode()+p.read_bytes() for p in paths)).hexdigest()


def run_experiment(root,candidates,outcomes,config,outdir):
    outdir=Path(outdir)
    if (outdir/"benchmark_manifest.json").exists():
        raise FileExistsError("Results already exist: choose a new directory, never silently replace frozen runs")
    if config["config_hash"]!=hash_config(config):
        raise ValueError("Configuration changed after hashing")
    if config.get("source_hash") and config["source_hash"]!=source_hash(root):
        raise ValueError("Scientific source changed after freezing")
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"config.yaml").write_text(yaml.safe_dump(config,sort_keys=True))
    started=time.time(); all_traces=[]; all_curves=[]; summaries=[]
    with (outdir/"traces.jsonl").open("w") as log:
        for seed in config["seeds"]:
            for policy in POLICIES:
                traces,curves,summary=replay(candidates,outcomes,config,seed,policy)
                for row in traces:
                    log.write(json.dumps(row,sort_keys=True,allow_nan=False)+"\n")
                log.flush()
                all_traces.extend(traces); all_curves.extend(curves); summaries.append(summary)
            print(f"seed {seed}: four policies completed",flush=True)
    pd.DataFrame(summaries).to_csv(outdir/"metrics.csv",index=False)
    pd.DataFrame(all_curves).to_csv(outdir/"curves.csv",index=False)
    flat=[{k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()} for r in all_traces]
    pd.DataFrame(flat).to_csv(outdir/"traces.csv",index=False)
    manifest={"status":"COMPLETED","config_hash":config["config_hash"],
              "dataset_hash":config["dataset_hash"],"source_hash":source_hash(root),
              "processed_dataset_hash":config["processed_dataset_hash"],
              "seed_count":len(config["seeds"]),"policies":list(POLICIES),"selections":len(all_traces),
              "initial_size":config["initial_size"],"additional_budget":config["budget"],
              "elapsed_seconds":time.time()-started,"python":platform.python_version(),
              "platform":platform.platform(),"lock_sha256":sha256_file(root/"requirements.lock"),
              "artifacts":{name:sha256_file(outdir/name) for name in ("metrics.csv","curves.csv","traces.csv","traces.jsonl","config.yaml")}}
    (outdir/"benchmark_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest
