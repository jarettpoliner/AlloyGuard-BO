import numpy as np
from alloyguard.hardness import HardnessModel
from helpers import config

def test_gp_updates_noise_and_training_only_scaling():
    x=np.array([[0.],[.3],[.7]])
    m=HardnessModel(config()["hardness"]).fit(x,[2.,3.,4.])
    mu,latent,noisy=m.predict([[.5],[10.]])
    assert np.isfinite(mu).all() and (latent>0).all()
    np.testing.assert_allclose(noisy**2-latent**2,.15**2,atol=1e-10)
    np.testing.assert_allclose(m.scaler.mean_,x.mean(axis=0))
    before=m.predict([[.5]])[0]
    after=HardnessModel(config()["hardness"]).fit(np.vstack([x,[[.5]]]),[2.,3.,4.,8.]).predict([[.5]])[0]
    assert abs(after[0]-before[0])>1

def test_constant_hardness_and_constant_features_stable():
    m=HardnessModel(config()["hardness"]).fit(np.ones((4,9)),[3.,3.,3.,3.])
    assert all(np.isfinite(a).all() for a in m.predict(np.ones((2,9))))
