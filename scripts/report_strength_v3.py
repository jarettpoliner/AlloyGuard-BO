import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(root/".matplotlib-cache"))
os.environ.setdefault("XDG_CACHE_HOME",str(root/".cache"))
import argparse
from alloyguard_strength.reporting import render
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run",required=True);args=p.parse_args()
    print(render(root/args.run))
