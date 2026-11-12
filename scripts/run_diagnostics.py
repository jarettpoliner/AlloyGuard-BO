"""Post-primary, separately labeled initialization sensitivity and OOD support audit."""
import os
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[name]="1"
from pathlib import Path
import json,argparse
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from alloyguard.data import problem_from_frame
from alloyguard.schema import ELEMENTS
from alloyguard.replay import load_config,hash_config,run_experiment
if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-prefix",default="results")
    args=parser.parse_args()
    destination=root/args.output_prefix
    destination.mkdir(parents=True,exist_ok=True)
    assert (root/"results/primary/benchmark_manifest.json").exists()
    frame=pd.read_csv(root/"data/processed/compositions.csv")
    cs,ys=problem_from_frame(frame)
    config=load_config(root/"configs/benchmark_frozen.yaml")
    for n in config["sensitivity_initial_sizes"]:
        cfg={**config,"initial_size":n,"seeds":config["sensitivity_seeds"],"experiment_label":f"EXPLORATORY_initial_{n}"}
        cfg["config_hash"]=hash_config(cfg)
        run_experiment(root,cs,ys,cfg,destination/f"sensitivity_initial_{n}")
    labels=KMeans(n_clusters=3,random_state=0,n_init=10).fit_predict(frame[list(ELEMENTS)])
    records=[]
    for group in range(3):
        mask=labels==group
        records.append({"composition_cluster":group,"target_groups":int(mask.sum()),
                        "target_feasible":int((frame.loc[mask,"ductility_rank"]>=3).sum()),
                        "training_feasible":int((frame.loc[~mask,"ductility_rank"]>=3).sum())})
    eligible=[r for r in records if r["target_groups"]>=15 and r["target_feasible"]>=4 and r["training_feasible"]>=4]
    assert not eligible, "Support unexpectedly changed: implement a separately labeled OOD replay before claiming completion"
    report={"status":"OOD_TEST_INSUFFICIENT_SUPPORT","method":"KMeans(k=3, seed=0, n_init=10) on compositions only",
            "requirements":config["ood"],"groups":records,
            "reason":"Seven feasible groups cannot provide at least four positives on both sides of a held-out split. No OOD outcome comparison claimed."}
    target=destination/"chemistry_shift.json"
    if target.exists():
        raise FileExistsError("Chemistry-shift results already exist; use an unused output prefix")
    target.write_text(json.dumps(report,indent=2)+"\n")
