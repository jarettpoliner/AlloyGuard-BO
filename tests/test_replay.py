import pytest
from alloyguard.policies import POLICIES,select_next_alloy
from alloyguard.replay import replay,hash_config
from helpers import config,toy,observations

@pytest.mark.parametrize("policy",POLICIES)
def test_equal_budgets_no_repeat_and_determinism(policy):
    cs,ys=toy(); cfg=config()
    a,curves,summary=replay(cs,ys,cfg,42,policy)
    b,other,_=replay(cs,ys,cfg,42,policy)
    assert [r["alloy_id"] for r in a]==[r["alloy_id"] for r in b]
    assert len(a)==3 and len(curves)==4
    assert len(set(r["alloy_id"] for r in a))==3
    assert curves[0]["initial_ids"]==other[0]["initial_ids"]
    assert all(r["training_observation_count"]==4+i for i,r in enumerate(a))
    assert all(curves[i+1]["best_feasible_hardness_gpa"]>=curves[i]["best_feasible_hardness_gpa"] for i in range(3))
    assert 0<=summary["failure_rate"]<=1

def test_initialization_is_matched_across_policies():
    cs,ys=toy(); cfg=config()
    designs=[replay(cs,ys,cfg,1,p)[1][0]["initial_ids"] for p in POLICIES]
    assert len(set(designs))==1

def test_observed_candidates_cannot_be_selected():
    cs,ys=toy()
    with pytest.raises(ValueError,match="observed"):
        select_next_alloy(observations(cs[:5],ys),cs,config(),"cbo",0,1)

def test_hash_covers_decisions():
    cfg=config(); before=hash_config(cfg); cfg["threshold"]=4
    assert hash_config(cfg)!=before
