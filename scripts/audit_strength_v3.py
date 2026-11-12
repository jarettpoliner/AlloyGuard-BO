"""Audit provisional execution separately from any scientific efficacy claim."""
from pathlib import Path
import json,hashlib,argparse
import pandas as pd
from alloyguard.replay import source_hash as ge_source_hash
from alloyguard_strength.replay import method_hash

if __name__=="__main__":
    root=Path(__file__).resolve().parents[1];folder=root/"results/strength_v3"
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first",default="results/strength_v3/provisional_validation")
    parser.add_argument("--second",default="results/strength_v3/provisional_reproduction")
    args=parser.parse_args()
    a=root/args.first;b=root/args.second
    ma=json.loads((a/"manifest.json").read_text());mb=json.loads((b/"manifest.json").read_text())
    assert ma["mode"]==mb["mode"]=="PROVISIONAL_SOFTWARE_VALIDATION"
    assert not ma["scientific_conclusions_allowed"] and not mb["scientific_conclusions_allowed"]
    assert ma["source_hash"]==mb["source_hash"]==method_hash()
    for directory,manifest in ((a,ma),(b,mb)):
        for name,digest in manifest["artifact_sha256"].items():
            assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest
    rows=[json.loads(line) for line in (a/"traces.jsonl").read_text().splitlines()]
    repeat=[json.loads(line) for line in (b/"traces.jsonl").read_text().splitlines()]
    assert len(rows)==len(repeat)==60
    cohort=pd.read_csv(folder/"secondary_provisional_cohort.csv").set_index("case_id")
    curves=pd.read_csv(a/"curves.csv")
    for seed in range(700,705):
        initial=curves[(curves.seed==seed)&(curves.step==0)]
        assert initial.initial_ids.nunique()==1
        for policy in ("random","strength_bo","cbo","rc_cbo"):
            subset=[r for r in rows if r["seed"]==seed and r["policy_name"]==policy]
            seen=set(json.loads(initial.iloc[0].initial_ids));assert len(seen)==24
            for r in subset:
                assert r["case_id"] not in seen
                assert set(r["diagnostics"]["observed_ids"])==seen
                assert r["observed_count"]==len(seen)
                actual=cohort.loc[r["case_id"]]
                assert r["measured_strength_mpa"]==actual.yield_strength_mpa
                assert r["measured_elongation_percent"]==actual.elongation_percent
                for fold in r["diagnostics"]["calibration_folds"]:
                    assert not set(fold["train_groups"])&set(fold["validation_groups"])
                    assert set(fold["train_ids"])|set(fold["validation_ids"])<=seen
                seen.add(r["case_id"])
    for x,y in zip(rows,repeat):
        assert {k:v for k,v in x.items() if k!="diagnostics"}=={k:v for k,v in y.items() if k!="diagnostics"}
    pd.testing.assert_frame_equal(pd.read_csv(a/"metrics.csv").drop(columns="fit_seconds"),
                                  pd.read_csv(b/"metrics.csv").drop(columns="fit_seconds"),check_exact=False,rtol=1e-12,atol=1e-12)
    original=json.loads((root/"results/primary/benchmark_manifest.json").read_text())
    assert ge_source_hash(root)==original["source_hash"]
    assert hashlib.sha256((root/"requirements.lock").read_bytes()).hexdigest()==original["lock_sha256"]
    for name,digest in original["artifacts"].items():
        assert hashlib.sha256((root/"results/primary"/name).read_bytes()).hexdigest()==digest
    active=sum(r["calibration_status"]=="CALIBRATION_ACTIVE" for r in rows)
    optimizer_failures=sum(not e["success"] for r in rows for e in r["diagnostics"]["strength"]["optimizer"])
    warnings=[w for r in rows for model in ("strength","feasibility") for w in r["diagnostics"][model]["warnings"]]
    report={"status":"PASSED_SOFTWARE_AUDIT_ONLY","provisional_selections_audited":60,
        "deterministic_decisions_forecasts_and_non_timing_metrics_reproduced":True,
        "recorded_observed_ids_verified":True,"group_calibration_no_overlap":True,
        "strength_optimizer_failures":optimizer_failures,"warnings":warnings,
        "calibration_active_software_steps":active,"ge_frozen_source_lock_and_primary_artifacts_unchanged":True,
        "final_scientific_protocol_frozen":False,"final_scientific_comparison_executed":False,
        "interpretation":"Provisional reported-measurement replay verifies engineering only. No conclusion about primary benchmark efficacy, calibrated probability quality or physical reliability is supported."}
    (folder/"software_audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print({k:report[k] for k in ("status","provisional_selections_audited","calibration_active_software_steps","strength_optimizer_failures")})
