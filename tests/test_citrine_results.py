"""Post-evaluation audit assertions; no methods or outcome-dependent tuning."""
from pathlib import Path
import json
import numpy as np
from scipy.special import expit,logit
ROOT=Path(__file__).resolve().parents[1]

def test_protocol_was_frozen_before_primary_exists_and_all_prechecks_passed():
    freeze=json.loads((ROOT/'results/citrine/freeze_evidence.json').read_text())
    assert freeze['status']=='FROZEN_BEFORE_PRIMARY' and not freeze['primary_run_existed_at_freeze']
    assert freeze['pre_freeze_test_count']==91
    assert json.loads((ROOT/'results/citrine/primary/manifest.json').read_text())['config_hash']==freeze['config_hash']

def test_probability_calibration_contract_on_all_prereveal_records():
    rows=[json.loads(line) for line in (ROOT/'results/citrine/primary/traces.jsonl').read_text().splitlines()]
    assert len(rows)==1800
    for r in rows:
        raw=r['feasibility_probability_raw'];cal=r['feasibility_probability_calibrated']
        assert 0<raw<1 and 0<cal<1
        if r['calibration_status']=='CALIBRATION_ACTIVE':
            assert cal==float(expit(logit(raw)/r['temperature']))
        else:assert cal==raw
        expected=r['expected_improvement_mpa']*(cal if r['policy_name']=='rc_cbo' else raw)
        assert np.isclose(expected,r['constrained_expected_improvement_mpa'])

def test_equal_matched_budgets_and_no_record_repeat():
    rows=[json.loads(line) for line in (ROOT/'results/citrine/primary/traces.jsonl').read_text().splitlines()]
    for seed in range(30):
        designs=[]
        for policy in ('random','strength_bo','cbo','rc_cbo'):
            selected=[r for r in rows if r['seed']==seed and r['policy_name']==policy]
            assert len(selected)==15 and len({r['case_id'] for r in selected})==15
            initial=selected[0]['diagnostics']['observed_ids'];designs.append(initial)
            assert len(initial)==12 and not set(initial)&{r['case_id'] for r in selected}
        assert all(d==designs[0] for d in designs)

def test_independent_recomputation_and_complete_reproduction_evidence():
    audit=json.loads((ROOT/'results/citrine/independent_audit.json').read_text())
    assert audit['status']=='PASSED' and audit['primary_selections_audited']==1800
    assert audit['runs_recomputed']==120 and not audit['frozen_methods_changed_after_primary']
    assert len(audit['shift_audits'])==3
