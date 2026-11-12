import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(root/'.matplotlib-cache'));os.environ.setdefault('XDG_CACHE_HOME',str(root/'.cache'))
from alloyguard_citrine.reporting import report
if __name__=='__main__':
    print(report(root))
    from complete_citrine_report import complete
    complete(root)
