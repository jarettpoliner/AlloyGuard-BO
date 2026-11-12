from pathlib import Path
import numpy as np
import yaml
from alloyguard.schema import Candidate,ExperimentalOutcome,Observation

ROOT=Path(__file__).resolve().parents[1]

def config():
    cfg=yaml.safe_load((ROOT/"configs/base.yaml").read_text())
    cfg.update(dataset_hash="SYNTHETIC_CORRECTNESS_ONLY",config_hash="TEST",initial_size=4,budget=3)
    return cfg

def toy(n=30):
    # No experimental data: known noiseless hardness 3+8*x, feasible x<=0.45.
    rng=np.random.default_rng(333)
    cs=tuple(Candidate(f"toy-{i:03d}",(float(x),float(1-x),0.,0.,0.,0.,0.,0.,0.))
             for i,x in enumerate(np.linspace(0,1,n)))
    outcomes={c.alloy_id:ExperimentalOutcome(3+8*c.composition[0]+float(rng.normal(0,.02)),
                    4 if c.composition[0]<=.45 else 1) for c in cs}
    return cs,outcomes

def observations(candidates,outcomes):
    return tuple(Observation(c,outcomes[c.alloy_id]) for c in candidates)
