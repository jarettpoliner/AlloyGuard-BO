from pathlib import Path
from alloyguard.data import audit
if __name__ == "__main__":
    _, report = audit(Path(__file__).resolve().parents[1])
    print({k:report[k] for k in ("raw_rows","unique_compositions","feasible_count","infeasible_count","calibration_supported","sha256")})
