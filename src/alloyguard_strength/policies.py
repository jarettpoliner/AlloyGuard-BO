from __future__ import annotations
from collections.abc import Sequence
import time
import numpy as np
from scipy.spatial.distance import cdist
from scipy.special import ndtr
from .schema import Candidate,Observation,Decision
from .models import StrengthGP,FeasibilityGP
from .calibration import GroupedTemperature

POLICIES=("random","strength_bo","cbo","rc_cbo")

def expected_improvement(mu,sd,best):
    if best is None or not np.isfinite(best):raise ValueError("Finite observed incumbent required")
    mu,sd=np.broadcast_arrays(np.asarray(mu,float),np.asarray(sd,float))
    if not np.isfinite(mu).all() or not np.isfinite(sd).all() or (sd<0).any():raise ValueError("Invalid moments")
    d=mu-best;z=d/np.maximum(sd,1e-15)
    return np.where(sd<=1e-12,np.maximum(d,0),np.maximum(d*ndtr(z)+sd*np.exp(-.5*z*z)/np.sqrt(2*np.pi),0))

def select_next(observations:Sequence[Observation],candidates:Sequence[Candidate],config:dict,
                policy_name:str,seed:int,step:int)->Decision:
    if policy_name not in POLICIES or not observations or not candidates:raise ValueError("Invalid policy inputs")
    ids=[c.case_id for c in candidates];seen={o.candidate.case_id for o in observations}
    if len(set(ids))!=len(ids) or seen&set(ids):raise ValueError("Duplicate/observed candidates")
    start=time.perf_counter()
    x=np.array([o.candidate.composition_features for o in observations]);q=np.array([c.composition_features for c in candidates])
    target=np.array([o.outcome.yield_strength_mpa for o in observations])
    labels=np.array([o.outcome.elongation_percent>=config["elongation_threshold_percent"] for o in observations])
    regression=StrengthGP(config["strength"]).fit(x,target);mu,sd,noisy=regression.predict(q)
    classifier=FeasibilityGP(config["feasibility"]).fit(x,labels);raw=classifier.predict(q)
    calibration=GroupedTemperature(config["calibration"],config["feasibility"],config["elongation_threshold_percent"])
    if policy_name=="rc_cbo":calibration.fit(observations)
    cal=calibration.transform(raw)
    dist=cdist(q,x).min(axis=1)
    constrained=policy_name in ("cbo","rc_cbo")
    if constrained and not labels.any():
        mode="FEASIBILITY_DISCOVERY";ei=np.zeros(len(q))
        exploration=config["exploration_coefficient"]*np.minimum(dist/np.sqrt(2),1)
        score_raw=raw+exploration;score_cal=cal+exploration
    else:
        mode="FEASIBLE_STRENGTH_IMPROVEMENT" if constrained else "STRENGTH_IMPROVEMENT"
        incumbent=float(target[labels].max()) if constrained else float(target.max())
        ei=expected_improvement(mu,sd,incumbent);score_raw=ei*raw;score_cal=ei*cal
    if policy_name=="random":
        score=np.random.default_rng(np.random.SeedSequence([seed,step,733])).random(len(q));mode="UNIFORM_RANDOM"
    elif policy_name=="strength_bo":score=ei
    elif policy_name=="cbo":score=score_raw
    else:score=score_cal
    if not np.isfinite(score).all() or (score<0).any():raise FloatingPointError("Invalid acquisition")
    i=int(np.argmax(score));c=candidates[i]
    return Decision(case_id=c.case_id,policy_name=policy_name,selection_step=step,
        composition_features=c.composition_features,feature_status=c.feature_status,
        strength_mean_mpa=float(mu[i]),strength_latent_std_mpa=float(sd[i]),strength_observation_std_mpa=float(noisy[i]),
        strength_observation_interval_mpa=(float(mu[i]-1.96*noisy[i]),float(mu[i]+1.96*noisy[i])),
        feasibility_probability_raw=float(raw[i]),feasibility_probability_calibrated=float(cal[i]),
        calibration_status=calibration.status if policy_name=="rc_cbo" else "NOT_APPLIED",temperature=calibration.temperature,
        expected_improvement_mpa=float(ei[i]),constrained_expected_improvement_mpa=float(ei[i]*(cal[i] if policy_name=="rc_cbo" else raw[i])),
        acquisition_score=float(score[i]),mode=mode,observed_count=len(observations),
        nearest_observed_composition_distance=float(dist[i]),raw_winner=ids[int(np.argmax(score_raw))],
        calibrated_winner=ids[int(np.argmax(score_cal))],config_hash=config["config_hash"],dataset_hash=config["dataset_hash"],
        diagnostics={"strength":regression.diagnostics,"feasibility":classifier.diagnostics,"calibration":calibration.diagnostics,
            "calibration_folds":calibration.folds,"observed_ids":[o.candidate.case_id for o in observations],
            "observed_groups":[o.candidate.leakage_group for o in observations],"fit_seconds":time.perf_counter()-start})
