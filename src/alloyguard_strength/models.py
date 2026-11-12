"""MPa regression and binary elongation-feasibility models; training-only scaling."""
from __future__ import annotations
import warnings
import numpy as np
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor,GaussianProcessClassifier
from sklearn.gaussian_process.kernels import ConstantKernel,Matern
from sklearn.preprocessing import StandardScaler

class StrengthGP:
    def __init__(self,config:dict): self.config=config
    def fit(self,x:np.ndarray,y:np.ndarray)->StrengthGP:
        x=np.asarray(x,float);y=np.asarray(y,float)
        if len(x)!=len(y) or not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("Invalid regression training data")
        self.scaler=StandardScaler().fit(x)
        self.center=float(y.mean());self.scale=max(float(y.std()),self.config["target_scale_floor_mpa"])
        self.noise=self.config["noise_mpa"]
        events=[]
        def optimize(objective,theta,bounds):
            r=minimize(objective,theta,jac=True,bounds=bounds,method="L-BFGS-B",options={"maxiter":60,"ftol":1e-8})
            events.append({"success":bool(r.success),"message":str(r.message),"iterations":int(r.nit)})
            return r.x,r.fun
        kernel=ConstantKernel(1.,(.1,10.))*Matern(2.,(.3,6.),nu=2.5)
        self.gp=GaussianProcessRegressor(kernel=kernel,alpha=(self.noise/self.scale)**2,
            optimizer=optimize,normalize_y=False,random_state=0)
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            self.gp.fit(self.scaler.transform(x),(y-self.center)/self.scale)
        self.diagnostics={"status":"FIT","noise_mpa":self.noise,"kernel":str(self.gp.kernel_),
            "optimizer":events,"warnings":[str(w.message) for w in capture]}
        return self
    def predict(self,x:np.ndarray):
        mu,sd=self.gp.predict(self.scaler.transform(x),return_std=True)
        mu=mu*self.scale+self.center;latent=np.maximum(sd*self.scale,1e-9)
        observation=np.sqrt(latent**2+self.noise**2)
        if not all(np.isfinite(a).all() for a in (mu,latent,observation)):
            raise FloatingPointError("Invalid strength forecast")
        return mu,latent,observation

class FeasibilityGP:
    def __init__(self,config:dict):self.config=config
    def fit(self,x:np.ndarray,y:np.ndarray)->FeasibilityGP:
        y=np.asarray(y,int)
        if not np.isin(y,[0,1]).all():raise ValueError("Binary feasibility required")
        self.scaler=StandardScaler().fit(x);self.gp=None
        self.prior=(int(y.sum())+1)/(len(y)+2)
        counts=np.bincount(y,minlength=2)
        self.diagnostics={"class_counts":counts.tolist(),"status":"FIT","warnings":[]}
        if min(counts)==0:
            self.diagnostics["status"]="SINGLE_CLASS_SMOOTHED_PRIOR";return self
        try:
            self.gp=GaussianProcessClassifier(kernel=Matern(self.config["length_scale"],"fixed",nu=2.5),
                optimizer=None,max_iter_predict=100,random_state=0)
            with warnings.catch_warnings(record=True) as capture:
                warnings.simplefilter("always");self.gp.fit(self.scaler.transform(x),y)
            self.diagnostics["warnings"]=[str(w.message) for w in capture]
        except (ValueError,np.linalg.LinAlgError,FloatingPointError) as exc:
            self.gp=None;self.diagnostics.update(status="NUMERICAL_SMOOTHED_PRIOR",error=repr(exc))
        return self
    def predict(self,x:np.ndarray)->np.ndarray:
        p=self.gp.predict_proba(self.scaler.transform(x))[:,1] if self.gp is not None else np.full(len(x),self.prior)
        if not np.isfinite(p).all():raise FloatingPointError("Invalid feasibility forecast")
        return np.clip(p,1e-7,1-1e-7)
