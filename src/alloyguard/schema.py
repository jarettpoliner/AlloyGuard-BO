"""Typed policy inputs deliberately contain no hidden target table."""
from dataclasses import dataclass, field
import math

ELEMENTS = ("Hf", "Mo", "Nb", "Re", "Ru", "Ta", "Ti", "W", "Zr")

@dataclass(frozen=True, slots=True)
class Candidate:
    alloy_id: str
    composition: tuple[float, ...]
    def __post_init__(self):
        if (len(self.composition) != 9 or not all(math.isfinite(x) and x >= 0 for x in self.composition)
                or abs(sum(self.composition) - 1) > 1e-8):
            raise ValueError("Expected nine finite nonnegative atomic fractions summing to one")

@dataclass(frozen=True, slots=True)
class ExperimentalOutcome:
    hardness_gpa: float
    ductility_rank: int
    def __post_init__(self):
        if not math.isfinite(self.hardness_gpa) or self.hardness_gpa <= 0:
            raise ValueError("Hardness must be finite and positive")
        if self.ductility_rank not in range(6):
            raise ValueError("Ductility must be an ordinal rank 0..5")

@dataclass(frozen=True, slots=True)
class Observation:
    candidate: Candidate
    outcome: ExperimentalOutcome

@dataclass(frozen=True, slots=True)
class Decision:
    alloy_id: str
    composition_atomic_fractions: tuple[float, ...]
    hardness_mean_gpa: float
    hardness_std_gpa: float
    hardness_observation_std_gpa: float
    hardness_prediction_interval: tuple[float, float]
    feasibility_probability_raw: float
    feasibility_probability_calibrated: float
    calibration_status: str
    temperature: float
    expected_improvement: float
    constrained_expected_improvement: float
    acquisition_score: float
    candidate_support_diagnostic: str
    nearest_observed_distance: float
    active_constraints: str
    selection_rationale: str
    training_observation_count: int
    policy_name: str
    model_config_hash: str
    dataset_hash: str
    selection_step: int
    raw_acquisition_winner: str
    calibrated_acquisition_winner: str
    fit_diagnostics: dict = field(default_factory=dict)
