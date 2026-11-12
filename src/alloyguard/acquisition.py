import numpy as np
from scipy.special import ndtr

def expected_improvement(mu,sd,incumbent):
    if incumbent is None or not np.isfinite(incumbent):
        raise ValueError("EI requires a finite incumbent")
    mu,sd=np.broadcast_arrays(np.asarray(mu,float),np.asarray(sd,float))
    if not np.isfinite(mu).all() or not np.isfinite(sd).all() or (sd<0).any():
        raise ValueError("Invalid predictive moments")
    improvement=mu-incumbent
    z=improvement/np.maximum(sd,1e-15)
    result=improvement*ndtr(z)+sd*np.exp(-0.5*z*z)/np.sqrt(2*np.pi)
    return np.where(sd<=1e-12,np.maximum(improvement,0),np.maximum(result,0))

def discovery_score(probability,distance,coefficient):
    return np.asarray(probability)+coefficient*np.minimum(np.asarray(distance)/np.sqrt(2),1)
