"""Observed-only OOF probabilities grouped by study/chemistry overlap component."""
from __future__ import annotations
from collections.abc import Sequence
import numpy as np
from scipy.special import expit,logit
from scipy.optimize import minimize_scalar
from sklearn.model_selection import StratifiedGroupKFold
from .schema import Observation
from .models import FeasibilityGP

class GroupedTemperature:
    def __init__(self,config:dict,model_config:dict,threshold:float):
        self.config=config;self.model_config=model_config;self.threshold=threshold
        self.temperature=1.;self.status="CALIBRATION_INSUFFICIENT_DATA";self.folds=[];self.diagnostics={}
    def fit(self,observations:Sequence[Observation])->GroupedTemperature:
        self.temperature=1.;self.status="CALIBRATION_INSUFFICIENT_DATA";self.folds=[]
        x=np.array([o.candidate.composition_features for o in observations])
        y=np.array([o.outcome.elongation_percent>=self.threshold for o in observations],int)
        groups=np.array([o.candidate.leakage_group for o in observations])
        ids=np.array([o.candidate.case_id for o in observations])
        if len(set(ids))!=len(ids):raise ValueError("Repeated case in observations")
        counts=np.bincount(y,minlength=2)
        self.diagnostics={"n":len(y),"class_counts":counts.tolist(),"groups":len(set(groups)),"reason":"OBSERVED_SUPPORT"}
        if not self.config["enabled"]:
            self.status="CALIBRATION_DISABLED_ABLATION";return self
        if len(y)<self.config["min_observations"] or min(counts)<self.config["min_per_class"]:
            return self
        if any(len(set(groups[y==label]))<3 for label in (0,1)):
            self.diagnostics["reason"]="INSUFFICIENT_DISTINCT_GROUPS_PER_CLASS";return self
        try:
            predictions=np.full(len(y),np.nan)
            split=StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=0)
            for train,valid in split.split(x,y,groups):
                if len(np.unique(y[train]))<2 or len(np.unique(y[valid]))<2:
                    self.diagnostics["reason"]="GROUP_FOLD_CLASS_SUPPORT";return self
                assert not set(groups[train])&set(groups[valid])
                model=FeasibilityGP(self.model_config).fit(x[train],y[train])
                if model.diagnostics["status"]!="FIT":
                    self.diagnostics["reason"]="GROUP_FOLD_MODEL_FALLBACK"
                    self.diagnostics["fold_model_diagnostics"]=model.diagnostics
                    return self
                predictions[valid]=model.predict(x[valid])
                self.folds.append({"train_ids":ids[train].tolist(),"validation_ids":ids[valid].tolist(),
                    "train_groups":sorted(set(groups[train])),"validation_groups":sorted(set(groups[valid])),
                    "model_diagnostics":model.diagnostics})
            if not np.isfinite(predictions).all():raise ValueError("Incomplete OOF forecasts")
            logits=logit(np.clip(predictions,1e-7,1-1e-7))
            def objective(logt):
                z=logits/np.exp(logt)
                return float(np.mean(np.logaddexp(0,z)-y*z)+self.config["regularization"]*logt**2)
            result=minimize_scalar(objective,bounds=(-np.log(3),np.log(3)),method="bounded",options={"maxiter":60})
            if not result.success:raise ValueError("Temperature fit failed")
            self.temperature=float(np.exp(result.x));self.status="CALIBRATION_ACTIVE"
            self.diagnostics.update(oof_predictions=predictions.tolist(),oof_labels=y.tolist(),objective=float(result.fun))
        except (ValueError,FloatingPointError,np.linalg.LinAlgError) as exc:
            self.status="CALIBRATION_FIT_FAILED";self.diagnostics["error"]=repr(exc)
        return self
    def transform(self,p):
        p=np.clip(np.asarray(p,float),1e-7,1-1e-7)
        return expit(logit(p)/self.temperature) if self.status=="CALIBRATION_ACTIVE" else p.copy()
