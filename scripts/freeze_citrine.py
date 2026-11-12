from pathlib import Path
import json
import yaml
from alloyguard_citrine.experiment import configure,adapter_hash
from alloyguard_strength.replay import config_hash,method_hash
if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];target=root/'configs/citrine/frozen.yaml'
    if target.exists():raise FileExistsError('Never refreeze an existing final protocol; create a labeled revision')
    tests=json.loads((root/'results/citrine/pre_freeze_test_evidence.json').read_text())
    assert tests['tests']>0 and tests['failures']==tests['errors']==tests['skipped']==0
    for directory,seeds in (('one_seed_checked',1),('smoke_checked',5)):
        manifest=json.loads((root/'results/citrine'/directory/'manifest.json').read_text())
        assert manifest['seed_count']==seeds and manifest['adapter_hash']==adapter_hash() and manifest['source_hash']==method_hash()
    assert json.loads((root/'results/strength_v3/synthetic_verification.json').read_text())['status']=='PASSED'
    cfg=configure(root,root/'configs/citrine/proposed.yaml')
    cfg['final_protocol_frozen']=True
    cfg['config_hash']=config_hash(cfg)
    target.write_text(yaml.safe_dump(cfg,sort_keys=True))
    (root/'results/citrine/freeze_evidence.json').write_text(json.dumps({'status':'FROZEN_BEFORE_PRIMARY','config_hash':cfg['config_hash'],
        'cohort_hash':cfg['dataset_hash'],'model_source_hash':cfg['source_hash'],'adapter_hash':cfg['adapter_hash'],'pre_freeze_test_count':tests['tests'],
        'primary_run_existed_at_freeze':(root/'results/citrine/primary').exists(),'interpretation_scope':cfg['interpretation_scope']},indent=2)+'\n')
    print(cfg['config_hash'])
