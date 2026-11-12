import os
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[name]="1"
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(root/".matplotlib-cache"))
os.environ.setdefault("XDG_CACHE_HOME",str(root/".cache"))
from alloyguard.reporting import generate
if __name__=="__main__":
    generate(root)
    if (root/"results/independent_audit.json").exists():
        from complete_report import complete
        complete(root)
    print((root/"results/research_verdict.json").read_text())
