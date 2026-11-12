"""Convenience wrapper for the five-seed smoke (not final inference)."""
import runpy,sys
from pathlib import Path
if __name__=="__main__":
    sys.argv=[sys.argv[0],"--config","configs/smoke.yaml","--output","results/smoke"]
    runpy.run_path(str(Path(__file__).with_name("run_benchmark.py")),run_name="__main__")
