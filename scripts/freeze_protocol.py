"""Freeze once, only after required tests/smoke evidence exists."""
from pathlib import Path
import json
import yaml
from alloyguard.replay import hash_config,source_hash
from alloyguard.data import sha256_file
if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    target=root/"configs/benchmark_frozen.yaml"
    if target.exists(): raise FileExistsError("Protocol already frozen; use a separately labeled revision")
    audit=json.loads((root/"results/data_audit.json").read_text())
    synthetic=json.loads((root/"results/synthetic_verification.json").read_text())
    smoke=json.loads((root/"results/smoke/benchmark_manifest.json").read_text())
    one=json.loads((root/"results/one_seed/benchmark_manifest.json").read_text())
    tests=json.loads((root/"results/test_evidence.json").read_text())
    assert synthetic["status"]=="PASSED" and smoke["seed_count"]==5 and one["seed_count"]==1
    assert tests["failures"]==0 and tests["errors"]==0 and tests["tests"]>0
    config=yaml.safe_load((root/"configs/base.yaml").read_text())
    config.update(seeds=list(range(30)),dataset_hash=audit["sha256"],processed_dataset_hash=audit["processed_sha256"],
                  source_hash=source_hash(root),dependency_lock_hash=sha256_file(root/"requirements.lock"),
                  calibration_gate_evidence={"feasible":audit["feasible_count"],"infeasible":audit["infeasible_count"],"support_min_per_class":15},
                  frozen_before_primary=True)
    assert config["calibration"]["enabled"]==audit["calibration_supported"]
    config["config_hash"]=hash_config(config)
    target.write_text(yaml.safe_dump(config,sort_keys=True))
    print(config["config_hash"])
