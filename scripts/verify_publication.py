"""Non-mutating publication audit and optional fresh-replay comparison.

Original scientific outputs are never rewritten. Independent arithmetic checks
read measurements and logs rather than calling acquisition or replay metrics.
"""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np
import pandas as pd
import yaml
from alloyguard_citrine.experiment import load_frozen
from alloyguard_strength.replay import config_hash

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):return [json.loads(x) for x in path.read_text().splitlines()]
def clean(row):
    row=json.loads(json.dumps(row))
    row.get('diagnostics',{}).pop('fit_seconds',None)
    return row

def verify(reproduced=None):
    original=json.loads((ROOT/'results/publication/original_work_manifest.json').read_text())
    absent=[]
    for name,expected in original.items():
        p=ROOT/name
        if not p.exists():
            assert name.startswith(('data/processed/','data/raw/','data/additional/raw/')),name
            absent.append(name);continue
        assert digest(p)==expected,('Original scientific artifact changed',name)
    historic=json.loads((ROOT/'results/v2/v1_preservation.json').read_text())
    for name,expected in historic.items():
        path=ROOT/('docs/archive/prepublication_README.md' if name=='README.md' else name)
        assert digest(path)==expected,('v1 snapshot mismatch',name)
    load_frozen(ROOT,ROOT/'configs/citrine/frozen.yaml')
    v2=json.loads((ROOT/'configs/v2/frozen.json').read_text())
    assert config_hash(v2)==v2['config_hash']
    for name,expected in v2['frozen_files'].items():assert digest(ROOT/name)==expected,name
    source=json.loads((ROOT/'results/citrine/source_manifest.json').read_text())
    for record in source['source_records']:
        p=ROOT/'data/citrine/raw'/record['filename'];b=p.read_bytes()
        assert len(b)==record['size_bytes'] and digest(p)==record['sha256']
        assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==record['git_blob_sha1']
    assert digest(ROOT/'data/citrine/raw/UPSTREAM_LICENSE')==source['license_sha256']
    cohort=pd.read_csv(ROOT/'results/citrine/cohort.csv').set_index('case_id')
    raw=pd.read_csv(ROOT/'data/citrine/raw/MPEA_dataset.csv');temp=next(c for c in raw if 'temperature' in c)
    assert len(raw)==1545 and len(cohort)==80 and cohort.index.is_unique
    assert (cohort.elongation_percent>=10).sum()==58
    assert cohort.study_doi.nunique()==36 and cohort.composition_key.nunique()==68 and cohort.leakage_group.nunique()==31
    assert not cohort.duplicated(['composition_key','processing_recipe']).any()
    for case in cohort.itertuples():
        r=raw.loc[case.master_row]
        assert r['PROPERTY: Type of test']=='T' and r[temp]==25
        assert case.yield_strength_mpa==r['PROPERTY: YS (MPa)'] and case.elongation_percent==r['PROPERTY: Elongation (%)']
    audit=json.loads((ROOT/'results/citrine/data_audit.json').read_text())
    assert 80+sum(audit['exclusion_first_reason_counts'].values())==1545
    directories=[('v1',ROOT/'results/citrine/primary')]+[(f'v2/{p.name}',p) for p in sorted((ROOT/'results/v2/evaluation').iterdir()) if p.is_dir()]
    selections=0;runs=0;reproduced_count=0;checked=[]
    for label,folder in directories:
        cfg=json.loads((folder/'config.json').read_text());assert cfg['config_hash']==config_hash(cfg)
        tr=rows(folder/'traces.jsonl');curves=pd.read_csv(folder/'curves.csv');metrics=pd.read_csv(folder/'metrics.csv')
        manifest=json.loads((folder/'manifest.json').read_text());hashes=manifest.get('artifact_sha256',manifest)
        for name,expected in hashes.items():assert digest(folder/name)==expected,(folder,name)
        groups={}
        for row in tr:groups.setdefault((row['seed'],row['policy_name']),[]).append(row)
        assert len(groups)==len(metrics)
        for seed,frame in curves[curves.step==0].groupby('seed'):assert frame.initial_ids.nunique()==1
        split_path=folder/'split.json';split=json.loads(split_path.read_text()) if split_path.exists() else None
        for (seed,policy),events in groups.items():
            cv=curves[(curves.seed==seed)&(curves.policy==policy)].sort_values('step');m=metrics[(metrics.seed==seed)&(metrics.policy==policy)].iloc[0]
            seen=json.loads(cv.iloc[0].initial_ids);assert len(seen)==cfg['initial_size'] and len(set(seen))==len(seen)
            if split:
                assert set(seen)<=set(split['train_ids'])
                assert not set(cohort.loc[seen].leakage_group)&set(cohort.loc[split['target_ids']].leakage_group)
            threshold=cfg['elongation_threshold_percent'];initial_good=[cohort.loc[k].yield_strength_mpa for k in seen if cohort.loc[k].elongation_percent>=threshold]
            best=max(initial_good,default=0.);curve=[best];failures=0;spent=0.;probs=[];labels=[]
            assert len(events)==cfg['budget'] and len(cv)==cfg['budget']+1
            for step,row in enumerate(events,1):
                assert row['case_id'] not in seen and row['diagnostics']['observed_ids']==seen
                assert row['observed_count']==len(seen) and row['selection_step']==step
                case=cohort.loc[row['case_id']]
                assert row['measured_strength_mpa']==case.yield_strength_mpa and row['measured_elongation_percent']==case.elongation_percent
                feasible=case.elongation_percent>=threshold;assert row['feasible']==feasible
                if split:assert row['case_id'] in split['target_ids']
                for fold in row['diagnostics']['calibration_folds']:
                    a=set(fold['train_ids']);b=set(fold['validation_ids'])
                    assert not a&b and a|b==set(seen)
                    assert not set(cohort.loc[list(a)].leakage_group)&set(cohort.loc[list(b)].leakage_group)
                p=row['feasibility_probability_calibrated'];assert 0<p<1
                if policy in ('risk_threshold','risk_budget','cd_cbo','cd_risk_threshold'):
                    allowance=max(0,cfg['risk']['total_budget']-spent)/(cfg['budget']-step+1)
                    minimum=0 if policy=='cd_cbo' else max(0,1-allowance) if policy=='risk_budget' else cfg['risk']['minimum_probability']
                    assert math.isclose(row['predicted_risk_spent_before'],spent,abs_tol=1e-9)
                    assert math.isclose(row['minimum_probability'],minimum,abs_tol=1e-9)
                    assert row['risk_fallback']==(row['eligible_count']==0)
                    if not row['risk_fallback']:assert p>=minimum
                spent+=1-p
                if 'predicted_risk_spent_after' in row:assert math.isclose(row['predicted_risk_spent_after'],spent,abs_tol=1e-9)
                if feasible:best=max(best,case.yield_strength_mpa)
                else:failures+=1
                curve.append(best);probs.append(p);labels.append(float(feasible));seen.append(row['case_id'])
                assert cv.iloc[step].cumulative_failures==failures
            assert np.array_equal(np.array(curve),cv.best_feasible_strength_mpa.to_numpy())
            assert math.isclose(float(np.trapezoid(curve)),m.auc_mpa_evaluations,abs_tol=1e-8)
            assert m.failure_count==failures
            y=np.array(labels);p=np.array(probs)
            assert math.isclose(float(np.mean((p-y)**2)),m.brier,abs_tol=1e-12)
            assert math.isclose(float(-np.mean(y*np.log(p)+(1-y)*np.log1p(-p))),m.log_loss,abs_tol=1e-12)
            runs+=1
        selections+=len(tr)
        if reproduced is not None:
            fresh=reproduced/label;again=rows(fresh/'traces.jsonl');assert len(again)==len(tr)
            for a,b in zip(tr,again):assert clean(a)==clean(b),(label,a['seed'],a['policy_name'],a['selection_step'])
            for name in ['curves.csv','metrics.csv']:
                a=pd.read_csv(folder/name);b=pd.read_csv(fresh/name)
                if 'fit_seconds' in a:a=a.drop(columns='fit_seconds');b=b.drop(columns='fit_seconds')
                pd.testing.assert_frame_equal(a,b,check_exact=True)
            reproduced_count+=len(again)
        checked.append(label)
    # Independently confirm that all original baselines have identical v1/v2 behavior.
    prior=rows(ROOT/'results/citrine/primary/traces.jsonl');new=rows(ROOT/'results/v2/evaluation/primary/traces.jsonl')
    index={(x['seed'],x['policy_name'],x['selection_step']):x for x in new}
    for row in prior:
        other=index[(row['seed'],row['policy_name'],row['selection_step'])]
        for key,value in clean(row).items():
            if key!='config_hash':assert clean(other)[key]==value
    means=pd.read_csv(ROOT/'results/v2/evaluation/primary/metrics.csv').groupby('policy').mean(numeric_only=True)
    saved=pd.read_csv(ROOT/'results/v2/summary.csv').set_index('policy')
    readme=(ROOT/'README.md').read_text()
    for policy in means.index:
        for field in ['auc_mpa_evaluations','failure_count','best_feasible_at_15_mpa']:
            assert math.isclose(means.loc[policy,field],saved.loc[policy,field],abs_tol=1e-8)
            assert f'{means.loc[policy,field]:,.2f}' in readme,(policy,field)
    assert means.auc_mpa_evaluations.idxmax()=='cbo'
    verdicts=json.loads((ROOT/'results/v2/verdicts.json').read_text())
    assert all(not v['both_goals_met'] for v in verdicts.values())
    breaks=json.loads((ROOT/'results/decision_review/break_even.json').read_text())
    for p in ['risk_threshold','risk_budget']:
        observed=(means.loc['cbo','auc_mpa_evaluations']-means.loc[p,'auc_mpa_evaluations'])/(means.loc['cbo','failure_count']-means.loc[p,'failure_count'])
        record=next(b for b in breaks if b['budget']==15 and b['policy']==p)
        assert math.isclose(observed,record['break_even'],abs_tol=1e-8)
        assert f'{observed:.2f}' in readme
    return dict(status='PASSED',mode='FRESH_REPRODUCTION' if reproduced else 'SAVED_EVIDENCE_AUDIT',
        audited_selections=selections,audited_runs=runs,fresh_reproduced_selections=reproduced_count,
        scenarios=checked,original_manifest_files=len(original),missing_ignored_local_inputs=absent,
        original_scientific_files_unchanged=True,historical_readme_archived_byte_identically=True,
        exact_v1_v2_baseline_selections=len(prior),cohort_cases=80,feasible_cases=58,studies=36,components=31,
        readme_numbers_match_saved_metrics=True,lock_sha256=digest(ROOT/'requirements.lock'),
        v2_config_hash=v2['config_hash'],scope='Independent computational checks, not external human peer review',
        limitations=['Seed intervals condition on reused data','Steel upload redistribution license unresolved','GE/Mendeley licensing is user-verified official-record evidence, not newly fetched metadata'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--reproduced',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=verify(args.reproduced)
    if args.output.exists():raise FileExistsError('Choose a fresh verification output path')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
