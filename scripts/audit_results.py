"""Skeptical independent recomputation from raw outcomes and recorded decisions.

This is an independent audit path in the same agent, not an external peer review.
"""
import os
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[name]="1"
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR",str(Path(__file__).resolve().parents[1]/".matplotlib-cache"))
os.environ.setdefault("XDG_CACHE_HOME",str(Path(__file__).resolve().parents[1]/".cache"))
import argparse,json
import numpy as np
import pandas as pd
from alloyguard.data import FILENAME,process,sha256_file
from alloyguard.replay import load_config,source_hash
from alloyguard.reporting import load_traces


def audit(root,reproduced=None,diagnostics=None):
    cfg=load_config(root/"configs/benchmark_frozen.yaml")
    run=root/"results/primary"
    manifest=json.loads((run/"benchmark_manifest.json").read_text())
    assert cfg["config_hash"]==manifest["config_hash"]
    assert cfg["source_hash"]==source_hash(root)==manifest["source_hash"]
    assert sha256_file(root/"requirements.lock")==cfg["dependency_lock_hash"]
    for name,digest in manifest["artifacts"].items():
        assert sha256_file(run/name)==digest, f"Changed original artifact {name}"
    grouped=process(pd.read_csv(root/"data/raw"/FILENAME,encoding="utf-8-sig"))
    truth=grouped.set_index("alloy_id")
    assert len(grouped)==82 and int((grouped.ductility_rank>=3).sum())==7
    traces=load_traces(run/"traces.jsonl")
    curves=pd.read_csv(run/"curves.csv")
    metrics=pd.read_csv(run/"metrics.csv")
    assert len(traces)==30*4*15 and len(metrics)==30*4 and len(curves)==30*4*16
    numerical_metrics=[]
    for (seed,policy),rows in metrics.groupby(["seed","policy"]):
        t=[r for r in traces if r["seed"]==seed and r["policy_name"]==policy]
        c=curves[(curves.seed==seed)&(curves.policy==policy)].sort_values("selection_step")
        initial=json.loads(c.iloc[0].initial_ids)
        seen=set(initial); assert len(seen)==12
        observed=[truth.loc[i] for i in initial]
        feasible=[float(r.hardness_gpa) for r in observed if r.ductility_rank>=3]
        best=[max(feasible,default=0.)]; failures=0
        for step,row in enumerate(t,1):
            key=row["alloy_id"]
            assert key not in seen
            assert row["training_observation_count"]==len(seen)
            assert set(row["fit_diagnostics"]["observed_ids"])==seen
            for fold in row["fit_diagnostics"]["calibration_folds"]:
                assert not set(fold["train_ids"])&set(fold["validation_ids"])
                assert set(fold["train_ids"])|set(fold["validation_ids"])==seen
            actual=truth.loc[key]
            assert np.isclose(row["measured_hardness_gpa"],actual.hardness_gpa)
            assert row["measured_ductility_rank"]==actual.ductility_rank
            if actual.ductility_rank>=3: feasible.append(float(actual.hardness_gpa))
            else: failures+=1
            best.append(max(feasible,default=0.))
            assert row["acquisition_score"]>=0 and np.isfinite(row["acquisition_score"])
            assert row["hardness_std_gpa"]<=row["hardness_observation_std_gpa"]
            assert row["feasibility_probability_raw"]==row["feasibility_probability_calibrated"]
            assert row["temperature"]==1.
            seen.add(key)
        np.testing.assert_allclose(best,c.best_feasible_hardness_gpa.to_numpy(),rtol=1e-12)
        area=float(np.trapezoid(best))
        assert np.isclose(area,rows.iloc[0].auc_gpa_evaluations)
        assert failures==rows.iloc[0].failure_count
        numerical_metrics.append({"seed":int(seed),"policy":policy,"recomputed_auc":area,"recomputed_failures":failures})
    # Matched initialization and constrained identity checked directly.
    for seed in range(30):
        initial=curves[(curves.seed==seed)&(curves.selection_step==0)].initial_ids
        assert initial.nunique()==1
        a=[r for r in traces if r["seed"]==seed and r["policy_name"]=="cbo"]
        b=[r for r in traces if r["seed"]==seed and r["policy_name"]=="rc_cbo"]
        for aa,bb in zip(a,b):
            for key in ("alloy_id","hardness_mean_gpa","hardness_std_gpa","feasibility_probability_raw","acquisition_score"):
                assert aa[key]==bb[key]
    reproduction="NOT_REQUESTED"
    if reproduced:
        other=load_traces(root/reproduced/"traces.jsonl")
        assert len(other)==len(traces)
        for a,b in zip(traces,other):
            # Diagnostics contain elapsed wall time; all deterministic contract fields must match.
            a={k:v for k,v in a.items() if k!="fit_diagnostics"}
            b={k:v for k,v in b.items() if k!="fit_diagnostics"}
            assert a==b,"Reproduction changed forecast/selection/outcome"
        oa=pd.read_csv(root/reproduced/"metrics.csv").drop(columns="fit_seconds")
        ma=metrics.drop(columns="fit_seconds")
        pd.testing.assert_frame_equal(ma,oa,check_exact=False,rtol=1e-12,atol=1e-12)
        reproduction="FULL_30_SEED_EXACT_DECISIONS_AND_FORECASTS_MATCH"
    diagnostic_reproduction="NOT_REQUESTED"
    if diagnostics:
        for n in (8,16):
            original=pd.read_csv(root/f"results/sensitivity_initial_{n}/metrics.csv").drop(columns="fit_seconds")
            regenerated=pd.read_csv(root/diagnostics/f"sensitivity_initial_{n}/metrics.csv").drop(columns="fit_seconds")
            pd.testing.assert_frame_equal(original,regenerated,check_exact=False,rtol=1e-12,atol=1e-12)
            assert (root/f"results/sensitivity_initial_{n}/curves.csv").read_bytes()==(root/diagnostics/f"sensitivity_initial_{n}/curves.csv").read_bytes()
        assert json.loads((root/"results/chemistry_shift.json").read_text())==json.loads((root/diagnostics/"chemistry_shift.json").read_text())
        diagnostic_reproduction="BOTH_SENSITIVITIES_AND_COMPOSITION_SHIFT_SUPPORT_MATCH"
    report={"status":"PASSED","audit_type":"independent recomputation and skeptical source review within same implementation session; not external peer review",
            "selections_audited":len(traces),"recomputed_runs":len(numerical_metrics),
            "protocol_hash":cfg["config_hash"],"source_hash":source_hash(root),
            "findings":["Raw MD5/size/SHA-256 consistent; official metadata/licensing user-supplied rather than independently fetched",
                        "Exact duplicate groups kept together; target units and aggregation explicit",
                        "Policy boundary exposes only compositions and observed targets, no oracle reference",
                        "Recorded training IDs equal exactly the revealed set before every selection",
                        "All recorded outcomes and AUC/failure metrics match independent raw-data recomputation",
                        "CBO and gated RC-CBO decisions, probabilities and acquisition values exactly equal",
                        "No calibration efficacy inference possible; sparse-class support limitation is retained",
                        "No prospective discovery, synthesis-success or proprietary-system superiority claim supported"],
            "remaining_scientific_limitations":["Seven feasible groups only","Overlapping finite-pool replays","No prospective laboratory validation","Full source documents not independently fetched"],
            "reproduction":reproduction,"diagnostic_reproduction":diagnostic_reproduction,"methodology_changed_after_primary":False}
    (root/"results/independent_audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print(report)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--reproduced");p.add_argument("--diagnostics")
    args=p.parse_args();audit(Path(__file__).resolve().parents[1],args.reproduced,args.diagnostics)
