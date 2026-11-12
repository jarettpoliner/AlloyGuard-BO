from alloyguard.policies import select_next_alloy
from helpers import config,toy,observations

def test_zero_feasible_identical_cold_start():
    cs,ys=toy(); obs=observations(cs[20:24],ys)
    candidates=tuple(c for c in cs if c not in cs[20:24])
    a=select_next_alloy(obs,candidates,config(),"cbo",2,1)
    b=select_next_alloy(obs,candidates,config(),"rc_cbo",2,1)
    assert a.selection_rationale=="FEASIBILITY_DISCOVERY"
    assert a.expected_improvement==0 and a.alloy_id==b.alloy_id
    assert a.fit_diagnostics["feasibility"]["status"]=="SINGLE_CLASS_SMOOTHED_PRIOR"
    assert a.acquisition_score>0
