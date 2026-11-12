"""Policies see only immutable candidate compositions and revealed observations."""
from __future__ import annotations
import time
import numpy as np
from .schema import Decision
from .features import compositions,support_distances
from .hardness import HardnessModel
from .feasibility import FeasibilityModel
from .calibration import TemperatureCalibrator
from .acquisition import expected_improvement,discovery_score

POLICIES=("random","hardness_bo","cbo","rc_cbo")


def select_next_alloy(observations,candidates,config,policy_name,seed,step):
    if policy_name not in POLICIES:
        raise ValueError("Unknown policy")
    if not observations or not candidates:
        raise ValueError("Observations and remaining candidates required")
    seen={o.candidate.alloy_id for o in observations}
    ids=[c.alloy_id for c in candidates]
    if len(set(ids))!=len(ids) or seen.intersection(ids):
        raise ValueError("Duplicate/observed candidate selection is forbidden")
    start=time.perf_counter()
    x=compositions([o.candidate for o in observations])
    q=compositions(candidates)
    h=np.array([o.outcome.hardness_gpa for o in observations])
    y=np.array([o.outcome.ductility_rank>=config["threshold"] for o in observations])
    hardness=HardnessModel(config["hardness"]).fit(x,h)
    mu,sd,noisy=hardness.predict(q)
    feasibility=FeasibilityModel(config["feasibility"]).fit(x,y)
    raw=feasibility.predict(q)
    calibrator=TemperatureCalibrator(config["calibration"],config["feasibility"])
    # CBO never fits/applies calibration; RC-CBO is otherwise identical.
    if policy_name=="rc_cbo":
        calibrator.fit(observations)
    cal=calibrator.transform(raw)
    distance=support_distances(x,q)
    if policy_name in ("cbo","rc_cbo") and not y.any():
        mode="FEASIBILITY_DISCOVERY"
        ei=np.zeros(len(q))
        raw_score=discovery_score(raw,distance,config["exploration_coefficient"])
        cal_score=discovery_score(cal,distance,config["exploration_coefficient"])
    else:
        mode="FEASIBLE_HARDNESS_IMPROVEMENT" if policy_name in ("cbo","rc_cbo") else "HARDNESS_IMPROVEMENT"
        incumbent=float(h[y].max()) if policy_name in ("cbo","rc_cbo") else float(h.max())
        ei=expected_improvement(mu,sd,incumbent)
        raw_score=ei*raw
        cal_score=ei*cal
    if policy_name=="random":
        score=np.random.default_rng(np.random.SeedSequence([seed,step,733])).random(len(q))
        mode="UNIFORM_RANDOM"
    elif policy_name=="hardness_bo":
        score=ei
    elif policy_name=="cbo":
        score=raw_score
    else:
        score=cal_score
    if not np.isfinite(score).all() or (score<0).any():
        raise FloatingPointError("Invalid acquisition score")
    # Candidate order is stable alloy ID order; argmax ties are deterministic.
    selected=int(np.argmax(score)); c=candidates[selected]
    diag={"hardness":hardness.diagnostics,"feasibility":feasibility.diagnostics,
          "calibration":calibrator.diagnostics,"calibration_folds":calibrator.folds,
          "fit_seconds":time.perf_counter()-start,
          "observed_ids":[o.candidate.alloy_id for o in observations],
          "minimum_candidate_score":float(score.min()),"maximum_candidate_score":float(score.max())}
    return Decision(
        alloy_id=c.alloy_id,composition_atomic_fractions=c.composition,
        hardness_mean_gpa=float(mu[selected]),hardness_std_gpa=float(sd[selected]),
        hardness_observation_std_gpa=float(noisy[selected]),
        hardness_prediction_interval=(float(mu[selected]-1.96*noisy[selected]),float(mu[selected]+1.96*noisy[selected])),
        feasibility_probability_raw=float(raw[selected]),feasibility_probability_calibrated=float(cal[selected]),
        calibration_status=calibrator.status if policy_name=="rc_cbo" else "NOT_APPLIED",
        temperature=calibrator.temperature,expected_improvement=float(ei[selected]),
        constrained_expected_improvement=float(ei[selected]*cal[selected] if policy_name=="rc_cbo" else ei[selected]*raw[selected]),
        acquisition_score=float(score[selected]),
        candidate_support_diagnostic="DISTANT_FROM_OBSERVATIONS" if distance[selected]>config["support_distance"] else "NEAR_OBSERVED_CHEMISTRY",
        nearest_observed_distance=float(distance[selected]),
        active_constraints="ductility_rank>=3 (probabilistic preference, no hard probability cutoff)" if policy_name in ("cbo","rc_cbo") else "none",
        selection_rationale=mode,training_observation_count=len(observations),policy_name=policy_name,
        model_config_hash=config["config_hash"],dataset_hash=config["dataset_hash"],selection_step=step,
        raw_acquisition_winner=ids[int(np.argmax(raw_score))],
        calibrated_acquisition_winner=ids[int(np.argmax(cal_score))],fit_diagnostics=diag)
