from __future__ import annotations
import warnings
import numpy as np
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern
from sklearn.preprocessing import StandardScaler

class HardnessModel:
    """Matérn-5/2 GPR; fixed GPa observation noise, optimized signal kernel.

    alpha is training noise; the returned GP variance excludes future observation
    noise. It is added explicitly only for observation intervals and scoring.
    """
    def __init__(self, config):
        self.config = config

    def fit(self, x, y):
        self.scaler=StandardScaler().fit(x)
        self.offset=float(np.mean(y))
        self.scale=max(float(np.std(y)),0.5)
        self.noise=float(self.config["observation_noise_gpa"])
        self.optimizer_events=[]
        def optimizer(obj, theta, bounds):
            result=minimize(obj,theta,method="L-BFGS-B",jac=True,bounds=bounds,
                            options={"maxiter":self.config["maxiter"],"ftol":1e-8})
            self.optimizer_events.append({"success":bool(result.success),"message":str(result.message),"iterations":int(result.nit)})
            return result.x,result.fun
        kernel=ConstantKernel(1.,(0.1,10.))*Matern(2.,(0.3,6.),nu=2.5)
        self.gp=GaussianProcessRegressor(kernel=kernel,alpha=(self.noise/self.scale)**2,
                    optimizer=optimizer,n_restarts_optimizer=0,normalize_y=False,random_state=0)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            self.gp.fit(self.scaler.transform(x),(np.asarray(y)-self.offset)/self.scale)
        self.diagnostics={"status":"FIT", "warnings":[str(w.message) for w in captured],
                          "optimizer":self.optimizer_events,"kernel":str(self.gp.kernel_),
                          "noise_gpa":self.noise}
        return self

    def predict(self,x):
        mu,sd=self.gp.predict(self.scaler.transform(x),return_std=True)
        mu=mu*self.scale+self.offset
        latent=np.maximum(sd*self.scale,1e-9)
        noisy=np.sqrt(latent**2+self.noise**2)
        if not all(np.isfinite(a).all() for a in (mu,latent,noisy)):
            raise FloatingPointError("Non-finite hardness prediction")
        return mu,latent,noisy
