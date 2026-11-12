"""Citrine orchestration uses existing strength policy/replay implementation unchanged."""
from __future__ import annotations
import hashlib,json,platform,time
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from alloyguard_strength.replay import config_hash,method_hash,run_suite,replay,summarize
from alloyguard_strength.cohort import group_holdouts
from alloyguard_strength.policies import POLICIES
from .data import load,sha


def adapter_hash():
    return hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sorted(Path(__file__).parent.glob('*.py')))).hexdigest()

def configure(root,source):
    root=Path(root);cfg=yaml.safe_load(Path(source).read_text())
    audit=json.loads((root/'results/citrine/data_audit.json').read_text())
    cs,_=load(root,cfg['feature_plan'])
    cfg.update(dataset_hash=audit['cohort_sha256'],source_hash=method_hash(),adapter_hash=adapter_hash(),
        cohort_ids_hash=hashlib.sha256(json.dumps(sorted(c.case_id for c in cs)).encode()).hexdigest(),
        lock_hash=sha(root/'requirements.lock'),qualification_hash=sha(root/'results/citrine/data_audit.json'))
    cfg['calibration']['enabled']=bool(audit['calibration_supported'])
    cfg['config_hash']=config_hash(cfg)
    return cfg

def load_frozen(root,path):
    cfg=yaml.safe_load(Path(path).read_text())
    if cfg['config_hash']!=config_hash(cfg):raise ValueError('Frozen configuration changed')
    if cfg['adapter_hash']!=adapter_hash() or cfg['source_hash']!=method_hash():raise ValueError('Frozen scientific code changed')
    if cfg['dataset_hash']!=sha(Path(root)/'results/citrine/cohort.csv'):raise ValueError('Frozen cohort changed')
    if cfg['qualification_hash']!=sha(Path(root)/'results/citrine/data_audit.json'):raise ValueError('Frozen qualification changed')
    if cfg['lock_hash']!=sha(Path(root)/'requirements.lock'):raise ValueError('Dependency lock changed')
    return cfg

def run(root,cfg,output,final=True):
    root=Path(root);cs,outcomes=load(root,cfg['feature_plan'])
    if cfg['adapter_hash']!=adapter_hash():raise ValueError('Adapter changed')
    qualification=json.loads((root/'results/citrine/data_audit.json').read_text())
    if qualification['G1b']!='COMPLETE_PUBLISHED_REPORTED_CASE_COHORT':raise ValueError('Citrine qualification incomplete')
    if cfg['qualification_hash']!=sha(root/'results/citrine/data_audit.json'):raise ValueError('Qualification changed')
    if cfg['dataset_hash']!=sha(root/'results/citrine/cohort.csv'):raise ValueError('Cohort changed')
    manifest=run_suite(cs,outcomes,cfg,output,'FINAL_SCIENTIFIC' if final else 'PROVISIONAL_SOFTWARE_VALIDATION',{'G1b':'COMPLETE'})
    manifest.update(interpretation_scope=cfg['interpretation_scope'],adapter_hash=adapter_hash(),
        qualification_hash=cfg['qualification_hash'],upstream_commit=json.loads((root/'results/citrine/source_manifest.json').read_text())['upstream_commit'],
        python=platform.python_version(),lock_hash=cfg['lock_hash'])
    (Path(output)/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

def diagnostics(root,cfg,output):
    root=Path(root);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for n in cfg['sensitivity']['initial_sizes']:
        modified=json.loads(json.dumps(cfg));modified.update(initial_size=n,seeds=cfg['sensitivity']['seeds'],experiment=f'EXPLORATORY_initial_{n}')
        modified['config_hash']=config_hash(modified)
        run(root,modified,output/f'initial_{n}')
        print(f'Completed initialization sensitivity n={n}',flush=True)
    modified=json.loads(json.dumps(cfg));modified.update(feature_plan=cfg['sensitivity']['feature_ablation'],seeds=cfg['sensitivity']['seeds'],experiment='EXPLORATORY_recipe_feature_ablation')
    modified['config_hash']=config_hash(modified)
    run(root,modified,output/'recipe_features')
    print('Completed recipe feature ablation',flush=True)
    cs,outcomes=load(root,cfg['feature_plan']);byid={c.case_id:c for c in cs}
    frame=pd.read_csv(root/'results/citrine/cohort.csv').set_index('case_id')
    shift_log=[]
    for fold,(train_ids,target_ids) in enumerate(group_holdouts(cs,cfg['shift']['group_permutation_seed'])):
        eligible=len(train_ids)>=cfg['shift']['minimum_training_cases'] and len(target_ids)>=cfg['shift']['minimum_target_cases']
        support={}
        for name,ids in (('train',train_ids),('target',sorted(target_ids))):
            labels=frame.loc[list(ids),'elongation_percent']>=10
            support[name]={'cases':len(ids),'feasible':int(labels.sum()),'infeasible':int((~labels).sum())}
            eligible &= min(int(labels.sum()),int((~labels).sum()))>=cfg['shift']['minimum_cases_each_class_each_pool']
        if not eligible:
            shift_log.append({'fold':fold,'status':'INSUFFICIENT_PREDECLARED_SUPPORT',**support});continue
        dest=output/f'study_chemistry_shift_{fold}'
        if dest.exists():raise FileExistsError('Preserve prior shift results')
        dest.mkdir();rows=[];curves=[];metrics=[]
        for seed in cfg['shift']['seeds']:
            rng=np.random.default_rng(seed);ordered=sorted(train_ids)
            initial=tuple(ordered[int(i)] for i in rng.choice(len(ordered),cfg['shift']['initial_size'],replace=False))
            for policy in POLICIES:
                trace,curve=replay(cs,outcomes,cfg,seed,policy,initial_ids=initial,target_ids=target_ids)
                rows.extend(trace);curves.extend(curve);metrics.append(summarize(trace,curve))
        (dest/'traces.jsonl').write_text(''.join(json.dumps(r,sort_keys=True,allow_nan=False)+'\n' for r in rows))
        pd.DataFrame(curves).to_csv(dest/'curves.csv',index=False);pd.DataFrame(metrics).to_csv(dest/'metrics.csv',index=False)
        (dest/'split.json').write_text(json.dumps({'train_pool_ids':sorted(train_ids),'target_pool_ids':sorted(target_ids),'config_hash':cfg['config_hash'],'fold':fold},indent=2)+'\n')
        shift_log.append({'fold':fold,'status':'COMPLETED',**support,'selections':len(rows)})
        print(f'Completed study/chemistry shift fold{fold}',flush=True)
    (output/'shift_support.json').write_text(json.dumps(shift_log,indent=2)+'\n')
