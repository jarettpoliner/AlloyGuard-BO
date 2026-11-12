#!/usr/bin/env python3
"""Execute frozen v2 experiments to a fresh output root; never writes v1."""
import argparse,copy,hashlib,json
from pathlib import Path
import yaml
from alloyguard_citrine.data import load
from alloyguard_strength.cohort import group_holdouts
from alloyguard_strength.replay import config_hash
from alloyguard_v2.replay import run
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',default='results/v2/evaluation');p.add_argument('--primary-only',action='store_true');args=p.parse_args()
cfg=json.loads((ROOT/'configs/v2/frozen.json').read_text())
for path,digest in cfg['frozen_files'].items():
 if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen file changed: '+path)
if cfg['config_hash']!=config_hash(cfg):raise ValueError('Config changed')
cs,ys=load(ROOT)
out=ROOT/args.output
run(cs,ys,cfg,out/'primary')
if not args.primary_only:
 for name,key,value in [('initial_8','initial_size',8),('initial_16','initial_size',16),('threshold_8','elongation_threshold_percent',8.),('threshold_12','elongation_threshold_percent',12.)]:
  sub=copy.deepcopy(cfg);sub[key]=value;sub['seeds']=list(range(100,105));sub['config_hash']=config_hash(sub)
  run(cs,ys,sub,out/name)
 for fold,split in enumerate(group_holdouts(cs,0)):
  if len(split[0])<12 or len(split[1])<15:raise ValueError('Insufficient frozen group split support')
  sub=copy.deepcopy(cfg);sub['seeds']=list(range(200,205));sub['config_hash']=config_hash(sub)
  run(cs,ys,sub,out/f'group_{fold}',split)
