import numpy as np
import pytest
from alloyguard.feasibility import FeasibilityModel
from helpers import config

@pytest.mark.parametrize("labels",[[0]*6,[1]*6,[0,0,0,0,0,1]])
def test_probability_support_and_single_class_behavior(labels):
    m=FeasibilityModel(config()["feasibility"]).fit(np.arange(6).reshape(-1,1),labels)
    p=m.predict([[.1],[9.]])
    assert ((p>0)&(p<1)).all()
    assert m.diagnostics["class_counts"]==[labels.count(0),labels.count(1)]
    if len(set(labels))==1:
        assert m.diagnostics["status"]=="SINGLE_CLASS_SMOOTHED_PRIOR"
        np.testing.assert_allclose(p,(sum(labels)+1)/8)
