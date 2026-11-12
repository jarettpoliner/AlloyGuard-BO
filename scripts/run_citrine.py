import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import argparse
from alloyguard_citrine.experiment import configure,load_frozen,run,diagnostics
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default='configs/citrine/frozen.yaml');p.add_argument('--output',default='results/citrine/primary');p.add_argument('--smoke',action='store_true');p.add_argument('--diagnostics',action='store_true');args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    cfg=configure(root,root/args.config) if args.smoke else load_frozen(root,root/args.config)
    if args.diagnostics:diagnostics(root,cfg,root/args.output)
    else:
        m=run(root,cfg,root/args.output,final=not args.smoke)
        print({k:m[k] for k in ('status','mode','seed_count','selections','interpretation_scope')})
