"""Regularized temperature scaling with observed-group-only cross fitting."""
from __future__ import annotations
import numpy as np
from scipy.special import expit, logit
from scipy.optimize import minimize_scalar
from sklearn.model_selection import StratifiedGroupKFold
from .feasibility import FeasibilityModel
from .features import compositions

class TemperatureCalibrator:
    def __init__(self,config,feasibility_config):
        self.config=config
        self.feasibility_config=feasibility_config
        self.temperature=1.
        self.status="CALIBRATION_INSUFFICIENT_DATA"
        self.folds=[]
        self.diagnostics={}

    def fit(self,observations):
        self.temperature=1.
        self.status="CALIBRATION_INSUFFICIENT_DATA"
        self.folds=[]
        y=np.array([o.outcome.ductility_rank>=3 for o in observations],int)
        counts=np.bincount(y,minlength=2)
        self.diagnostics={"n":len(y),"class_counts":counts.tolist(),"reason":"observed_support"}
        if not self.config["enabled"]:
            self.diagnostics["reason"]="DATASET_CLASS_SUPPORT_GATE"
            return self
        if len(y)<self.config["min_observations"] or min(counts)<self.config["min_per_class"]:
            return self
        x=compositions([o.candidate for o in observations])
        groups=np.array([o.candidate.alloy_id for o in observations])
        if len(set(groups)) != len(groups):
            raise ValueError("Observations must already be unique composition groups")
        try:
            oof=np.full(len(y),np.nan)
            splitter=StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=0)
            for train,valid in splitter.split(x,y,groups):
                model=FeasibilityModel(self.feasibility_config).fit(x[train],y[train])
                oof[valid]=model.predict(x[valid])
                self.folds.append({"train_ids":groups[train].tolist(),"validation_ids":groups[valid].tolist(),
                                   "fit_status":model.diagnostics["status"]})
            if not np.isfinite(oof).all():
                raise ValueError("Incomplete out-of-fold predictions")
            logits=logit(np.clip(oof,1e-7,1-1e-7))
            def objective(log_temperature):
                z=logits/np.exp(log_temperature)
                return float(np.mean(np.logaddexp(0,z)-y*z)+self.config["regularization"]*log_temperature**2)
            result=minimize_scalar(objective,bounds=(-np.log(3),np.log(3)),method="bounded",
                                   options={"maxiter":60,"xatol":1e-6})
            if not result.success or not np.isfinite(result.fun):
                raise ValueError("Temperature optimization failed")
            self.temperature=float(np.exp(result.x))
            self.status="CALIBRATION_ACTIVE"
            self.diagnostics.update(oof_probabilities=oof.tolist(),oof_labels=y.tolist(),objective=float(result.fun))
        except (ValueError,FloatingPointError,np.linalg.LinAlgError) as exc:
            self.status="CALIBRATION_FIT_FAILED"
            self.diagnostics["error"]=repr(exc)
        return self

    def transform(self,p):
        p=np.clip(np.asarray(p,float),1e-7,1-1e-7)
        return expit(logit(p)/self.temperature) if self.status=="CALIBRATION_ACTIVE" else p.copy()
