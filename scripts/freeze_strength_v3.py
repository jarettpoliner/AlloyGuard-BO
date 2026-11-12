"""Only a source-qualified primary cohort and successful tests permit freezing."""
from pathlib import Path
import json,hashlib
import pandas as pd
import yaml
from alloyguard_strength.replay import config_hash,method_hash

if __name__=="__main__":
    root=Path(__file__).resolve().parents[1];out=root/"configs/strength_v3/benchmark_frozen.yaml"
    if out.exists():raise FileExistsError("Use a separately labeled protocol revision")
    q=json.loads((root/"results/strength_v3/qualification.json").read_text())
    if q["G1b"]!="COMPLETE":raise ValueError("CANNOT_FREEZE_G1B_UNRESOLVED: primary-source-qualified cohort required")
    cohort=pd.read_csv(root/"results/strength_v3/primary_cohort.csv")
    cfg=yaml.safe_load((root/"configs/strength_v3/development.yaml").read_text())
    cfg.update(status="FROZEN_PRIMARY_SCIENTIFIC_PROTOCOL",initial_size=12,budget=15,seeds=list(range(30)))
    cfg["calibration"]["enabled"]=bool(q["primary_calibration_supported"])
    if len(cohort)<cfg["initial_size"]+cfg["budget"] or not (cohort.qualification_status=="VERIFIED").all():
        raise ValueError("Insufficient qualified independent cases")
    if cohort.case_id.duplicated().any():raise ValueError("Repeated experimental case")
    tests=json.loads((root/"results/strength_v3/test_evidence.json").read_text())
    if tests["failures"] or tests["errors"] or not tests["tests"]:raise ValueError("Passing tests required")
    cfg.update(final_protocol_frozen=True,source_hash=method_hash(),
        cohort_ids_hash=hashlib.sha256(json.dumps(sorted(cohort.case_id)).encode()).hexdigest(),
        dataset_hash=hashlib.sha256((root/"results/strength_v3/primary_cohort.csv").read_bytes()).hexdigest(),
        annotation_sha256=q["annotation_sha256"],qualification_sha256=hashlib.sha256((root/"results/strength_v3/qualification.json").read_bytes()).hexdigest(),
        lock_hash=hashlib.sha256((root/"requirements.lock").read_bytes()).hexdigest())
    cfg["config_hash"]=config_hash(cfg)
    out.write_text(yaml.safe_dump(cfg,sort_keys=True))
    print(cfg["config_hash"])
