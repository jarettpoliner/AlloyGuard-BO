from __future__ import annotations
from dataclasses import dataclass,field
import math

@dataclass(frozen=True,slots=True)
class Candidate:
    case_id: str
    composition_features: tuple[float,...]
    leakage_group: str
    feature_status: str = "REPORTED_COMPOSITION_BASIS_UNVERIFIED"
    def __post_init__(self):
        if not self.case_id or not self.leakage_group or not self.composition_features:
            raise ValueError("Case/group/features required")
        if not all(math.isfinite(x) and x>=0 for x in self.composition_features):
            raise ValueError("Composition features must be finite and nonnegative")
        if sum(self.composition_features)<=0:
            raise ValueError("Empty composition")

@dataclass(frozen=True,slots=True)
class Outcome:
    yield_strength_mpa: float
    elongation_percent: float
    def __post_init__(self):
        if not math.isfinite(self.yield_strength_mpa) or self.yield_strength_mpa<=0:
            raise ValueError("Positive finite yield strength required")
        if not math.isfinite(self.elongation_percent) or not 0<=self.elongation_percent<=100:
            raise ValueError("Elongation must be finite and in [0,100] percent")

@dataclass(frozen=True,slots=True)
class Observation:
    candidate: Candidate
    outcome: Outcome

@dataclass(frozen=True,slots=True)
class Decision:
    case_id: str
    policy_name: str
    selection_step: int
    composition_features: tuple[float,...]
    feature_status: str
    strength_mean_mpa: float
    strength_latent_std_mpa: float
    strength_observation_std_mpa: float
    strength_observation_interval_mpa: tuple[float,float]
    feasibility_probability_raw: float
    feasibility_probability_calibrated: float
    calibration_status: str
    temperature: float
    expected_improvement_mpa: float
    constrained_expected_improvement_mpa: float
    acquisition_score: float
    mode: str
    observed_count: int
    nearest_observed_composition_distance: float
    raw_winner: str
    calibrated_winner: str
    config_hash: str
    dataset_hash: str
    diagnostics: dict=field(default_factory=dict)
