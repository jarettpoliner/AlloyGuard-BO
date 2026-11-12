import numpy as np
import pytest
from alloyguard.acquisition import expected_improvement

@pytest.mark.parametrize("mu,sd,best",[([0,1,10],[0,1e-20,1],1),([-100,0,100],[1,1,1],0)])
def test_ei_finite_nonnegative_and_zero_variance(mu,sd,best):
    a=expected_improvement(mu,sd,best)
    assert np.isfinite(a).all() and (a>=0).all()
    if sd[0]==0: assert a[0]==max(mu[0]-best,0)

def test_ei_known_value_and_risk_discount():
    assert expected_improvement([1],[1],1)[0]==pytest.approx(1/np.sqrt(2*np.pi))
    ei=expected_improvement([10,6],[1,1],3)
    assert ei[0]>ei[1]
    assert np.argmax(ei*np.array([.01,.95]))==1

def test_no_incumbent_rejected():
    with pytest.raises(ValueError): expected_improvement([1],[1],None)
