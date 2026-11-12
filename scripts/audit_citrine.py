"""Independent raw-outcome and observed-set audit, including full reproduction."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
from alloyguard_citrine.data import formula,sha
from alloyguard_citrine.experiment import load_frozen,adapter_hash
from alloyguard_strength.replay import method_hash
from alloyguard.replay import source_hash as ge_source_hash

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reproduced',default='results/citrine/reproduced_primary');args=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=root/'results/citrine';run=out/'primary';reproduced=root/args.reproduced
    cfg=load_frozen(root,root/'configs/citrine/frozen.yaml')
    manifest=json.loads((run/'manifest.json').read_text())
    for name,digest in manifest['artifact_sha256'].items():assert sha(run/name)==digest
    assert manifest['source_hash']==method_hash() and manifest['adapter_hash']==adapter_hash()
    master=pd.read_csv(root/'data/citrine/raw/MPEA_dataset.csv')
    cohort=pd.read_csv(out/'cohort.csv').set_index('case_id')
    assert len(cohort)==80 and cohort.index.is_unique and not cohort.duplicated(['composition_key','processing_recipe']).any()
    for row in cohort.itertuples():
        raw=master.loc[row.master_row]
        assert raw['PROPERTY: YS (MPa)']==row.yield_strength_mpa and raw['PROPERTY: Elongation (%)']==row.elongation_percent
        assert raw['PROPERTY: Type of test']=='T' and raw[next(c for c in master if 'temperature' in c)]==25
    rows=[json.loads(line) for line in (run/'traces.jsonl').read_text().splitlines()]
    curves=pd.read_csv(run/'curves.csv');metrics=pd.read_csv(run/'metrics.csv')
    assert len(rows)==1800 and len(metrics)==120 and len(curves)==1920
    for seed in range(30):
        initial=curves[(curves.seed==seed)&(curves.step==0)]
        assert initial.initial_ids.nunique()==1
        for policy in ('random','strength_bo','cbo','rc_cbo'):
            selected=[r for r in rows if r['seed']==seed and r['policy_name']==policy]
            ids=json.loads(initial.iloc[0].initial_ids);seen=set(ids);assert len(seen)==12
            feasible=[cohort.loc[k,'yield_strength_mpa'] for k in ids if cohort.loc[k,'elongation_percent']>=10]
            best=[max(feasible,default=0.)];failed=0
            for step,r in enumerate(selected,1):
                key=r['case_id'];assert key not in seen
                assert r['selection_step']==step and r['observed_count']==len(seen)
                assert set(r['diagnostics']['observed_ids'])==seen
                actual=cohort.loc[key]
                assert np.isclose(actual.yield_strength_mpa,r['measured_strength_mpa'])
                assert np.isclose(actual.elongation_percent,r['measured_elongation_percent'])
                target_positive=actual.elongation_percent>=10
                assert r['feasible']==target_positive
                if target_positive:feasible.append(float(actual.yield_strength_mpa))
                else:failed+=1
                best.append(max(feasible,default=0.))
                for fold in r['diagnostics']['calibration_folds']:
                    a=set(fold['train_ids']);b=set(fold['validation_ids'])
                    assert a|b==seen and not a&b
                    assert not set(cohort.loc[list(a),'leakage_group'])&set(cohort.loc[list(b),'leakage_group'])
                if r['calibration_status']=='CALIBRATION_ACTIVE':
                    folds=r['diagnostics']['calibration_folds']
                    assert len(folds)==3
                    val=[k for fold in folds for k in fold['validation_ids']]
                    assert len(val)==len(set(val))==len(seen) and set(val)==seen
                assert r['acquisition_score']>=0 and np.isfinite(r['acquisition_score'])
                assert np.isclose(r['strength_observation_std_mpa']**2-r['strength_latent_std_mpa']**2,625,atol=1e-7)
                seen.add(key)
            actual_curve=curves[(curves.seed==seed)&(curves.policy==policy)].sort_values('step')
            np.testing.assert_allclose(best,actual_curve.best_feasible_strength_mpa,rtol=1e-12)
            result=metrics[(metrics.seed==seed)&(metrics.policy==policy)].iloc[0]
            assert np.isclose(np.trapezoid(best),result.auc_mpa_evaluations)
            assert result.failure_count==failed
    again=[json.loads(line) for line in (reproduced/'traces.jsonl').read_text().splitlines()]
    assert len(again)==len(rows)
    for a,b in zip(rows,again):assert {k:v for k,v in a.items() if k!='diagnostics'}=={k:v for k,v in b.items() if k!='diagnostics'}
    pd.testing.assert_frame_equal(metrics.drop(columns='fit_seconds'),pd.read_csv(reproduced/'metrics.csv').drop(columns='fit_seconds'),check_exact=False,rtol=1e-12,atol=1e-12)
    # Each shift split is study/chemistry component disjoint; all target queries stay in target.
    shifts=[]
    for directory in sorted((out/'diagnostics').glob('study_chemistry_shift_*')):
        split=json.loads((directory/'split.json').read_text());train=set(split['train_pool_ids']);target=set(split['target_pool_ids'])
        assert not train&target
        assert not set(cohort.loc[list(train),'leakage_group'])&set(cohort.loc[list(target),'leakage_group'])
        shift_rows=[json.loads(line) for line in (directory/'traces.jsonl').read_text().splitlines()]
        assert all(r['case_id'] in target for r in shift_rows)
        shifts.append({'fold':split['fold'],'selections_audited':len(shift_rows)})
    ge=json.loads((root/'results/primary/benchmark_manifest.json').read_text())
    assert ge_source_hash(root)==ge['source_hash'] and sha(root/'requirements.lock')==ge['lock_sha256']
    for name,digest in ge['artifacts'].items():assert sha(root/'results/primary'/name)==digest
    old=json.loads((root/'results/strength_v3/provisional_validation/manifest.json').read_text())
    assert old['source_hash']==method_hash()
    report={'status':'PASSED','audit_scope':'Independent recomputation within this session, not external peer review',
        'primary_selections_audited':1800,'runs_recomputed':120,'full30_seed_reproduction':'ALL_DETERMINISTIC_CONTRACT_FIELDS_AND_NON_TIMING_METRICS_MATCH',
        'original_master_outcomes_temperature_and_loading_verified':True,'observed_only_grouped_calibration_verified':True,
        'shift_audits':shifts,'ge_and_existing_strength_source_and_lock_unchanged':True,
        'frozen_methods_changed_after_primary':False,'primary_config_hash':cfg['config_hash'],'adapter_hash':cfg['adapter_hash'],
        'scientific_limits':['80 conservative published reported cases, not independently remeasured trials','36 literature sources and chemistry dependencies','replay seeds condition on one finite dataset','quantitative processing and strain rates incompletely recorded','no prospective laboratory validation']}
    (out/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
