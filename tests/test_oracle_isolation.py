import ast
import dataclasses
import inspect
import pytest
from alloyguard import policies
from alloyguard.oracle import OutcomeOracle
from alloyguard.policies import select_next_alloy
from alloyguard.schema import ExperimentalOutcome,Candidate
from helpers import config,toy,observations

def test_policy_cannot_receive_hidden_outcomes_and_is_target_invariant():
    cs,ys=toy(); obs=observations(cs[:6],ys); candidates=cs[6:]
    a=select_next_alloy(obs,candidates,config(),"cbo",0,1)
    # Change every hidden label in the oracle: the same policy input/decision must result.
    altered={c.alloy_id:ExperimentalOutcome(100.,0) for c in candidates}
    hidden_oracle=OutcomeOracle(altered)
    b=select_next_alloy(obs,candidates,config(),"cbo",0,1)
    assert a.alloy_id==b.alloy_id and a.acquisition_score==b.acquisition_score
    assert {f.name for f in dataclasses.fields(Candidate)}=={"alloy_id","composition"}
    assert "oracle" not in inspect.signature(select_next_alloy).parameters
    tree=ast.parse(inspect.getsource(policies))
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):
            assert node.module not in ("oracle","data","replay")
    assert not hasattr(hidden_oracle,"outcomes")

def test_oracle_reveal_once():
    _,ys=toy(); o=OutcomeOracle(ys); key=next(iter(ys))
    assert o.reveal(key)==ys[key]
    with pytest.raises(ValueError): o.reveal(key)
