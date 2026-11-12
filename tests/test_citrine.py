"""Published-master qualification and frozen-model reuse, not result-based tuning."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import pytest
from alloyguard_citrine.data import formula,normalized_recipe,load,BLOBS
from alloyguard_citrine.experiment import configure
from alloyguard_strength.replay import method_hash,require_scientific_cohort
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('text,expected',[('AlCoCrFeNi',{'Al':.2,'Co':.2,'Cr':.2,'Fe':.2,'Ni':.2}),('Al2Co1',{'Al':2/3,'Co':1/3}),('(CoCr)2Ni',{'Co':.4,'Cr':.4,'Ni':.2}),('Co25Cr25(FeNi)50',{'Co':1/6,'Cr':1/6,'Fe':1/3,'Ni':1/3})])
def test_atomic_parser_known_stoichiometry(text,expected):
    parsed=formula(text)
    assert set(parsed)==set(expected)
    for e in expected:assert parsed[e]==pytest.approx(expected[e])

@pytest.mark.parametrize('text',['','Unknown2','Fe-1Ni','(CoCr','Co0Ni','()2Fe'])
def test_invalid_compositions_rejected(text):
    with pytest.raises(ValueError):formula(text)

def test_recipe_sequence_not_sorted_or_inferred():
    assert normalized_recipe(' CR + A ')=='CR+A'
    assert normalized_recipe('A + CR')!='CR+A'
    assert normalized_recipe(float('nan'))==''

def test_uploaded_all_four_source_blobs_match_official_not_raw_substitution():
    for name,expected in BLOBS.items():
        data=(ROOT/'data/citrine/raw'/name).read_bytes()
        assert hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()==expected
    manifest=json.loads((ROOT/'results/citrine/source_manifest.json').read_text())
    assert manifest['upstream_commit']=='d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e'
    assert len(manifest['source_records'])==4

def test_real_qualified_case_counts_class_support_and_exclusions():
    q=json.loads((ROOT/'results/citrine/data_audit.json').read_text())
    assert q['explicit_tensile_25c_numeric_pairs']==246
    assert q['qualified_reported_cases']==80 and q['feasible_count']==58 and q['infeasible_count']==22
    assert 80+sum(q['exclusion_first_reason_counts'].values())==1545
    assert q['source_cross_checks']['qualified_raw_composition_crosschecks_passed']==80
    assert q['source_cross_checks']['master_to_raw_direct_numeric_yield_mismatches']==0
    assert q['calibration_supported']

def test_every_included_case_has_explicit_test_temperature_and_no_ambiguous_recipe_key():
    frame=pd.read_csv(ROOT/'results/citrine/cohort.csv');raw=pd.read_csv(ROOT/'data/citrine/raw/MPEA_dataset.csv')
    temp=next(c for c in raw if 'temperature' in c)
    assert (raw.loc[frame.master_row,'PROPERTY: Type of test']=='T').all()
    assert (raw.loc[frame.master_row,temp]==25).all()
    assert not frame.duplicated(['composition_key','processing_recipe']).any()
    excluded=pd.read_csv(ROOT/'results/citrine/ambiguous_cases_preserved.csv')
    assert not set(frame.master_row)&set(excluded.master_row)
    assert frame.study_doi.notna().all() and frame.processing_recipe.notna().all()

def test_elongation_over100_not_falsely_flagged_physically_invalid():
    raw=pd.read_csv(ROOT/'data/citrine/raw/MPEA_dataset.csv');audit=pd.read_csv(ROOT/'results/citrine/record_audit.csv')
    for index in raw[raw['PROPERTY: Elongation (%)']>100].index:
        assert 'INVALID_TARGET_SIGN' not in audit.loc[index,'exclusion_reasons']

def test_cohort_inputs_contain_no_measurement_or_phase_predictors():
    candidates,outcomes=load(ROOT);schema=json.loads((ROOT/'results/citrine/feature_schema.json').read_text())
    assert len(candidates)==len(outcomes)==80
    for c in candidates:
        assert len(c.composition_features)==len(schema['element_columns'])
        assert np.isclose(sum(c.composition_features),1) and min(c.composition_features)>=0
        assert not hasattr(c,'yield_strength_mpa') and not hasattr(c,'elongation_percent')
    augmented,_=load(ROOT,'composition_plus_recipe')
    assert len(augmented[0].composition_features)>len(candidates[0].composition_features)
    assert set(c.case_id for c in augmented)==set(c.case_id for c in candidates)

def test_group_components_prevent_study_and_chemistry_fold_leakage():
    f=pd.read_csv(ROOT/'results/citrine/cohort.csv')
    assert f.groupby('study_doi').leakage_group.nunique().max()==1
    assert f.groupby('composition_key').leakage_group.nunique().max()==1
    assert f.leakage_group.nunique()==31

def test_existing_strength_model_code_unchanged_and_final_mode_guarded():
    previous=json.loads((ROOT/'results/strength_v3/provisional_validation/manifest.json').read_text())
    assert previous['source_hash']==method_hash()
    cfg=configure(ROOT,ROOT/'configs/citrine/proposed.yaml')
    with pytest.raises(ValueError,match='NOT_FROZEN'):
        require_scientific_cohort(cfg,{'G1b':'COMPLETE'},['case'])

def test_frozen_qualification_hash_change_rejected(tmp_path):
    import shutil,yaml
    from alloyguard_citrine.experiment import load_frozen
    cfg=configure(ROOT,ROOT/'configs/citrine/proposed.yaml')
    cfg['final_protocol_frozen']=True
    from alloyguard_strength.replay import config_hash
    cfg['config_hash']=config_hash(cfg)
    (tmp_path/'results/citrine').mkdir(parents=True)
    for name in ('cohort.csv','data_audit.json'):
        shutil.copyfile(ROOT/'results/citrine'/name,tmp_path/'results/citrine'/name)
    shutil.copyfile(ROOT/'requirements.lock',tmp_path/'requirements.lock')
    path=tmp_path/'frozen.yaml';path.write_text(yaml.safe_dump(cfg))
    assert load_frozen(tmp_path,path)['dataset_hash']==cfg['dataset_hash']
    audit=tmp_path/'results/citrine/data_audit.json';audit.write_text(audit.read_text()+' ')
    with pytest.raises(ValueError,match='qualification changed'):load_frozen(tmp_path,path)
