"""Post-comparison audit assertions; these do not tune or modify methodology."""
import json
import numpy as np
from alloyguard.replay import load_config,source_hash
from alloyguard.policies import select_next_alloy
from alloyguard.schema import ExperimentalOutcome
from alloyguard.metrics import probability_scores
from helpers import ROOT,config,toy,observations


def test_frozen_source_and_observed_dataset_support():
    cfg=load_config(ROOT/"configs/benchmark_frozen.yaml")
    assert cfg["source_hash"]==source_hash(ROOT)
    assert cfg["calibration_gate_evidence"]["feasible"]==7
    assert not cfg["calibration"]["enabled"]
    assert len(cfg["seeds"])==30


def test_active_calibration_is_connected_to_rc_policy_on_supported_fixture():
    cs,ys=toy(48); cfg=config();cfg["calibration"]["enabled"]=True
    decision=select_next_alloy(observations(cs[:40],ys),cs[40:],cfg,"rc_cbo",2,1)
    assert decision.calibration_status=="CALIBRATION_ACTIVE"
    assert 1/3<=decision.temperature<=3
    assert decision.constrained_expected_improvement==decision.expected_improvement*decision.feasibility_probability_calibrated
    assert len(decision.fit_diagnostics["calibration_folds"])==3


def test_no_feasible_run_is_censored_and_auc_zero():
    from alloyguard.replay import replay
    cs,ys=toy(); impossible={k:ExperimentalOutcome(v.hardness_gpa,0) for k,v in ys.items()}
    rows,curve,metrics=replay(cs,impossible,config(),2,"rc_cbo")
    assert all(r["selection_rationale"]=="FEASIBILITY_DISCOVERY" for r in rows)
    assert metrics["auc_gpa_evaluations"]==0
    assert metrics["time_to_first_feasible"] is None and metrics["first_feasible_censored"]
    assert metrics["failure_count"]==3


def test_probability_scores_use_predictions_before_reveal_and_known_reference():
    brier,loss=probability_scores([0,1],[.5,.5])
    assert brier==.25 and np.isclose(loss,np.log(2))


def test_full_real_data_run_records_expected_contract_without_calibration_claim():
    rows=[json.loads(line) for line in (ROOT/"results/primary/traces.jsonl").read_text().splitlines()]
    assert len(rows)==1800
    rc=[r for r in rows if r["policy_name"]=="rc_cbo"]
    assert len(rc)==450
    assert all(r["calibration_status"]=="CALIBRATION_INSUFFICIENT_DATA" for r in rc)
    assert all(r["fit_diagnostics"]["calibration"]["reason"]=="DATASET_CLASS_SUPPORT_GATE" for r in rc)
