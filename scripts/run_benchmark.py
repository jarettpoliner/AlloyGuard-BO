"""Run a specified configuration; refuses to replace existing result directories."""
import os
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[name]="1"
from pathlib import Path
import argparse
import pandas as pd
from alloyguard.data import problem_from_frame,sha256_file
from alloyguard.replay import load_config,hash_config,run_experiment

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config",default="configs/benchmark_frozen.yaml")
    p.add_argument("--output",default="results/primary")
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    config=load_config(root/args.config)
    if "dataset_hash" not in config:
        import json
        audit=json.loads((root/"results/data_audit.json").read_text())
        config.update(dataset_hash=audit["sha256"],processed_dataset_hash=audit["processed_sha256"])
        config["config_hash"]=hash_config(config)
    path=root/"data/processed/compositions.csv"
    if sha256_file(path)!=config["processed_dataset_hash"]:
        raise ValueError("Processed dataset changed")
    candidates,outcomes=problem_from_frame(pd.read_csv(path))
    print(run_experiment(root,candidates,outcomes,config,root/args.output))
