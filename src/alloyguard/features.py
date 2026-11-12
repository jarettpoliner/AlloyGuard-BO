"""Observed-training-only scaling; geometry diagnostics use compositions alone."""
import numpy as np
from scipy.spatial.distance import cdist

def compositions(candidates):
    return np.asarray([c.composition for c in candidates],dtype=float)

def support_distances(train, candidates):
    return cdist(np.asarray(candidates),np.asarray(train)).min(axis=1)
