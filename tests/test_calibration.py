import numpy as np
from alloyguard.calibration import TemperatureCalibrator
from helpers import config,toy,observations

def test_insufficient_data_and_dataset_gate_are_identity():
    cs,ys=toy(); obs=observations(cs[:5],ys)
    cfg=config()
    m=TemperatureCalibrator(cfg["calibration"],cfg["feasibility"]).fit(obs)
    np.testing.assert_array_equal(m.transform([.1,.9]),[.1,.9])
    assert m.status=="CALIBRATION_INSUFFICIENT_DATA" and m.temperature==1
    cfg["calibration"]["enabled"]=True
    m=TemperatureCalibrator(cfg["calibration"],cfg["feasibility"]).fit(obs)
    assert m.status=="CALIBRATION_INSUFFICIENT_DATA"

def test_crossfitting_uses_only_disjoint_observed_groups():
    cs,ys=toy(48); observed=observations(cs[:40],ys)
    cfg=config(); cfg["calibration"]["enabled"]=True
    m=TemperatureCalibrator(cfg["calibration"],cfg["feasibility"]).fit(observed)
    assert m.status=="CALIBRATION_ACTIVE"
    assert 1/3<=m.temperature<=3
    allowed={o.candidate.alloy_id for o in observed}
    heldout={c.alloy_id for c in cs[40:]}
    val=[]
    for fold in m.folds:
        a=set(fold["train_ids"]); b=set(fold["validation_ids"])
        assert not a&b and a|b==allowed and not (a|b)&heldout
        val.extend(b)
    assert len(val)==len(set(val))==40
    p=m.transform([.01,.5,.99])
    assert ((p>0)&(p<1)).all() and p[0]<p[1]<p[2]
