"""Explicit modes separate provisional execution checks from frozen science."""
import os
for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):os.environ[key]="1"
from pathlib import Path
import argparse,json,hashlib
import yaml
from alloyguard_strength.cohort import load_cohort
from alloyguard_strength.replay import config_hash,run_suite,require_scientific_cohort

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=["PROVISIONAL_SOFTWARE_VALIDATION","FINAL_SCIENTIFIC"],required=True)
    parser.add_argument("--config",default="configs/strength_v3/development.yaml")
    parser.add_argument("--output",default="results/strength_v3/provisional_smoke")
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    directory=root/"results/strength_v3"
    qualification=json.loads((directory/"qualification.json").read_text())
    primary=args.mode=="FINAL_SCIENTIFIC"
    path=directory/("primary_cohort.csv" if primary else "secondary_provisional_cohort.csv")
    schema=json.loads((directory/"feature_schema.json").read_text())
    config=yaml.safe_load((root/args.config).read_text())
    if primary and not config.get("final_protocol_frozen"):
        raise ValueError("FINAL_BENCHMARK_BLOCKED_PROTOCOL_NOT_FROZEN_AND_G1B_UNRESOLVED")
    candidates,outcomes=load_cohort(path,schema["element_columns"],allow_provisional=not primary)
    config["dataset_hash"]=hashlib.sha256(path.read_bytes()).hexdigest()
    if primary:
        if config.get("config_hash")!=config_hash(config):raise ValueError("Frozen configuration changed")
    else:config["config_hash"]=config_hash(config)
    result=run_suite(candidates,outcomes,config,root/args.output,args.mode,qualification)
    print({k:result[k] for k in ("status","mode","scientific_conclusions_allowed","seed_count","selections")})
