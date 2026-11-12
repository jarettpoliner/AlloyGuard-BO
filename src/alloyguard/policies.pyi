from typing import Any, Literal, Sequence
from .schema import Candidate, Observation, Decision
POLICIES: tuple[str, ...]
def select_next_alloy(
    observations: Sequence[Observation],
    candidates: Sequence[Candidate],
    config: dict[str, Any],
    policy_name: Literal["random", "hardness_bo", "cbo", "rc_cbo"],
    seed: int,
    step: int,
) -> Decision: ...
