"""Read explicitly qualified/provisional cohort artifacts without property leakage."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .schema import Candidate,Outcome


def load_cohort(path:Path,element_columns:list[str],allow_provisional:bool=False):
    frame=pd.read_csv(path)
    if frame.empty:raise ValueError("No qualified cases available")
    if not allow_provisional and not (frame.qualification_status=="VERIFIED").all():
        raise ValueError("Unqualified cases cannot enter the final primary cohort")
    if frame.case_id.duplicated().any():raise ValueError("Duplicate case IDs")
    # Deliberate construction: no experimental outcomes/dataframe reach a Candidate.
    cs=tuple(Candidate(str(row.case_id),tuple(float(getattr(row,c)) for c in element_columns),
            str(row.leakage_group),str(row.feature_status)) for row in frame.itertuples())
    outcomes={str(row.case_id):Outcome(float(row.yield_strength_mpa),float(row.elongation_percent)) for row in frame.itertuples()}
    return cs,outcomes


def group_holdouts(candidates,seed:int=0):
    """Composition/study-component heldouts defined without target values."""
    groups=sorted({c.leakage_group for c in candidates})
    order=np.random.default_rng(seed).permutation(groups)
    if len(groups)<3:raise ValueError("Insufficient independent groups for shift evaluation")
    for fold in range(3):
        targets=set(order[fold::3])
        train_ids=tuple(c.case_id for c in candidates if c.leakage_group not in targets)
        target_ids={c.case_id for c in candidates if c.leakage_group in targets}
        yield train_ids,target_ids
