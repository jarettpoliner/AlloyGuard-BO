"""Strength/elongation correctness, group leakage and scientific-cohort gate tests."""
from __future__ import annotations
import copy,dataclasses,json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import yaml
from alloyguard_strength.schema import Candidate,Outcome,Observation
from alloyguard_strength.models import StrengthGP,FeasibilityGP
from alloyguard_strength.calibration import GroupedTemperature
from alloyguard_strength.policies import select_next,expected_improvement,POLICIES
from alloyguard_strength.replay import replay,config_hash,require_scientific_cohort,OutcomeOracle,summarize
from alloyguard_strength.cohort import load_cohort,group_holdouts

ROOT=Path(__file__).resolve().parents[1]

def config():
    cfg=yaml.safe_load((ROOT/"configs/strength_v3/development.yaml").read_text())
    cfg.update(initial_size=12,budget=3,dataset_hash="SYNTHETIC_CORRECTNESS_ONLY")
    cfg["config_hash"]=config_hash(cfg)
    return cfg

def toy(n=72):
    rng=np.random.default_rng(91)
    cs=tuple(Candidate(f"synthetic-{i:03d}",(float(x),float(1-x)),f"group-{i%12}","SYNTHETIC") for i,x in enumerate(np.linspace(0,1,n)))
    outcomes={c.case_id:Outcome(300+1800*c.composition_features[0]+float(rng.normal(0,2)),20*(1-c.composition_features[0])) for c in cs}
    return cs,outcomes

def observed(cs,ys):return tuple(Observation(c,ys[c.case_id]) for c in cs)


def test_strength_units_training_only_scale_and_noise_decomposition():
    x=np.array([[0.,1.],[.4,.6],[1.,0.]])
    model=StrengthGP(config()["strength"]).fit(x,np.array([300.,1000.,1500.]))
    mu,latent,noisy=model.predict([[.5,.5]])
    assert np.isfinite(mu).all() and mu[0]>100
    np.testing.assert_allclose(noisy**2-latent**2,25**2)
    np.testing.assert_allclose(model.scaler.mean_,x.mean(axis=0))
    after=StrengthGP(config()["strength"]).fit(np.vstack([x,[.5,.5]]),np.array([300.,1000.,1500.,2000.])).predict([[.5,.5]])[0]
    assert abs(after[0]-mu[0])>100

@pytest.mark.parametrize("label",[0,1])
def test_single_class_prior_uses_only_observed_labels(label):
    model=FeasibilityGP(config()["feasibility"]).fit(np.arange(4).reshape(-1,1),[label]*4)
    np.testing.assert_allclose(model.predict([[2.],[8.]]),(4*label+1)/6)
    assert model.diagnostics["status"]=="SINGLE_CLASS_SMOOTHED_PRIOR"


def test_group_calibration_keeps_studies_and_chemistry_components_disjoint():
    cs,ys=toy();obs=observed(cs[:60],ys)
    model=GroupedTemperature(config()["calibration"],config()["feasibility"],10).fit(obs)
    assert model.status=="CALIBRATION_ACTIVE" and 1/3<=model.temperature<=3
    allowed={o.candidate.case_id for o in obs};validation=[]
    for fold in model.folds:
        assert not set(fold["train_groups"])&set(fold["validation_groups"])
        assert not set(fold["train_ids"])&set(fold["validation_ids"])
        assert set(fold["train_ids"])|set(fold["validation_ids"])==allowed
        validation.extend(fold["validation_ids"])
    assert set(validation)==allowed and len(validation)==len(set(validation))


def test_calibration_disabled_or_insufficient_support_is_exact_identity():
    cs,ys=toy();cfg=config()
    m=GroupedTemperature(cfg["calibration"],cfg["feasibility"],10).fit(observed(cs[:8],ys))
    assert m.status=="CALIBRATION_INSUFFICIENT_DATA"
    np.testing.assert_array_equal(m.transform([.1,.9]),[.1,.9])
    cfg["calibration"]["enabled"]=False
    m=GroupedTemperature(cfg["calibration"],cfg["feasibility"],10).fit(observed(cs[:60],ys))
    assert m.status=="CALIBRATION_DISABLED_ABLATION"


def test_calibration_cannot_cross_one_study_even_if_many_rows():
    cs,ys=toy();single=tuple(dataclasses.replace(c,leakage_group="same-study") for c in cs[:60])
    m=GroupedTemperature(config()["calibration"],config()["feasibility"],10).fit(observed(single,ys))
    assert m.status=="CALIBRATION_INSUFFICIENT_DATA"
    assert m.diagnostics["reason"]=="INSUFFICIENT_DISTINCT_GROUPS_PER_CLASS"


def test_ei_stable_nonnegative_and_infeasible_high_strength_discount():
    ei=expected_improvement([2000.,1200.,300.],[100.,100.,0.],500.)
    assert np.isfinite(ei).all() and (ei>=0).all()
    assert np.argmax(ei[:2])==0 and np.argmax(ei[:2]*[.01,.9])==1
    assert ei[2]==0
    with pytest.raises(ValueError):expected_improvement([1],[1],None)


def test_cold_start_and_constrained_matching_with_calibration_off():
    cs,ys=toy();obs=observed(cs[48:60],ys);remain=cs[:48]+cs[60:]
    cfg=config();cfg["calibration"]["enabled"]=False
    a=select_next(obs,remain,cfg,"cbo",1,1);b=select_next(obs,remain,cfg,"rc_cbo",1,1)
    assert a.mode=="FEASIBILITY_DISCOVERY" and a.expected_improvement_mpa==0
    assert a.case_id==b.case_id and a.acquisition_score==b.acquisition_score

@pytest.mark.parametrize("policy",POLICIES)
def test_equal_budget_and_deterministic_replay(policy):
    cs,ys=toy(40);cfg=config()
    a,c=replay(cs,ys,cfg,7,policy);b,d=replay(cs,ys,cfg,7,policy)
    assert len(a)==cfg["budget"] and len({r["case_id"] for r in a})==len(a)
    assert [r["case_id"] for r in a]==[r["case_id"] for r in b]
    assert c==d and len(c)==cfg["budget"]+1
    assert all(r["observed_count"]==12+i for i,r in enumerate(a))
    assert all(0<r["feasibility_probability_raw"]<1 for r in a)


def test_initial_designs_match_between_policies():
    cs,ys=toy(40);designs=[replay(cs,ys,config(),3,p)[1][0]["initial_ids"] for p in POLICIES]
    assert len(set(designs))==1


def test_hidden_labels_do_not_cross_policy_interface():
    cs,ys=toy(40);obs=observed(cs[:12],ys)
    a=select_next(obs,cs[12:],config(),"cbo",2,1)
    hidden={c.case_id:Outcome(9999.,0.) for c in cs[12:]}
    oracle=OutcomeOracle(hidden)
    b=select_next(obs,cs[12:],config(),"cbo",2,1)
    assert a.case_id==b.case_id and a.strength_mean_mpa==b.strength_mean_mpa
    assert {f.name for f in dataclasses.fields(Candidate)}=={"case_id","composition_features","leakage_group","feature_status"}
    assert not hasattr(oracle,"outcomes")


def test_duplicate_selection_and_duplicate_reveal_rejected():
    cs,ys=toy();obs=observed(cs[:12],ys)
    with pytest.raises(ValueError):select_next(obs,cs,config(),"cbo",0,1)
    o=OutcomeOracle(ys);o.reveal(cs[0].case_id)
    with pytest.raises(ValueError):o.reveal(cs[0].case_id)


def test_group_holdout_geometry_has_no_study_or_component_overlap():
    cs,ys=toy()
    for initial,target in group_holdouts(cs,0):
        a={c.leakage_group for c in cs if c.case_id in initial}
        b={c.leakage_group for c in cs if c.case_id in target}
        assert not a&b and a|b=={c.leakage_group for c in cs}
    with pytest.raises(ValueError,match="group crossed"):
        replay(cs,ys,config(),0,"cbo",initial_ids=tuple(c.case_id for c in cs[:12]),target_ids={c.case_id for c in cs[12:]})


def test_final_freeze_guard_blocks_provisional_data():
    with pytest.raises(ValueError,match="G1B"):
        require_scientific_cohort(config(),{"G1b":"BLOCKED"},[])
    with pytest.raises(ValueError,match="NOT_FROZEN"):
        require_scientific_cohort(config(),{"G1b":"COMPLETE"},["case"])


def test_qualified_cohort_loader_cannot_silently_accept_uncertain_records():
    folder=ROOT/"results/strength_v3"
    schema=json.loads((folder/"feature_schema.json").read_text())
    with pytest.raises(ValueError,match="Unqualified"):
        load_cohort(folder/"secondary_provisional_cohort.csv",schema["element_columns"])
    cs,ys=load_cohort(folder/"secondary_provisional_cohort.csv",schema["element_columns"],True)
    assert len(cs)==453 and len(ys)==453
    assert not any(hasattr(c,"yield_strength_mpa") or hasattr(c,"elongation_percent") for c in cs)
    assert len(cs[0].composition_features)==len(schema["element_columns"])


def test_provenance_gate_and_record_statuses_preserve_missing_information():
    q=json.loads((ROOT/"results/strength_v3/qualification.json").read_text())
    assert q["G1a"].startswith("COMPLETE") and q["qualified_independent_cases"]==0
    assert q["record_status_counts"]=={"EXCLUDED":1256,"CONDITION_UNCERTAIN":453,"CONFLICTING":4}
    records=pd.read_csv(ROOT/"results/strength_v3/record_qualification.csv")
    assert records["test_temperature_c"].isna().all()
    assert records.excel_row.nunique()==1713


def test_valid_group_shift_replay_is_executable_without_target_access():
    cs,ys=toy();cfg=config()
    train,target=next(group_holdouts(cs,0))
    traces,curve=replay(cs,ys,cfg,3,"cbo",initial_ids=train[:12],target_ids=target)
    assert len(traces)==3 and all(r["case_id"] in target for r in traces)
    assert all(not set(r["diagnostics"]["observed_ids"])&target if r["selection_step"]==1 else True for r in traces)


def test_annotation_requires_real_condition_fields_not_just_known_publication():
    from prepare_strength_v3 import verified_annotation
    incomplete={"study_doi":"10.1016/j.jallcom.2021.162907","evidence_url":"https://doi.org/10.1016/j.jallcom.2021.162907"}
    assert not verified_annotation(incomplete,"10.1016/j.jallcom.2021.162907")[0]
    complete={**incomplete,"evidence_locator":"Methods p.2 (TEST FIXTURE)","evidence_excerpt":"FIXTURE ONLY",
        "reviewer":"TEST FIXTURE","processing_state_id":"fixture-state","loading_mode":"tensile", "test_temperature_c":25,
        "composition_basis":"atomic_fraction","same_material_state":True,"experimental":True}
    assert verified_annotation(complete,"10.1016/j.jallcom.2021.162907")[0]
    complete["test_temperature_c"]=float("nan")
    assert not verified_annotation(complete,"10.1016/j.jallcom.2021.162907")[0]
