import copy
from pathlib import Path
import numpy as np
import pytest
import yaml
from alloyguard_v2.policies import RiskLedger,constrained_choice,DuctilityGP,select,POLICIES
from alloyguard_v2.replay import replay
from alloyguard_strength.replay import replay as original
from alloyguard_strength.schema import Candidate,Outcome,Observation

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def cfg():
 c=yaml.safe_load((ROOT/'configs/citrine/frozen.yaml').read_text());c.update(budget=3,initial_size=4,risk={'minimum_probability':.75,'total_budget':.75},ductility={'log_noise':.15,'log_scale_floor':.5})
 return c
@pytest.fixture
def pool():
 cs=tuple(Candidate(str(i),(i/10+.01,1-i/10),str(i)) for i in range(10))
 ys={str(i):Outcome(300+80*i,float(2+3*i)) for i in range(10)}
 return cs,ys

def test_ledger_prediction_only_carry_and_overrun():
 s=RiskLedger(1,3).charge(.9)
 assert s.spent==pytest.approx(.1)
 assert s.allowance==pytest.approx(.45)
 s=s.charge(.1).charge(.1)
 assert s.remaining==pytest.approx(-.9)
 with pytest.raises(ValueError):_ = s.allowance
 with pytest.raises(ValueError):s.charge(.5)
@pytest.mark.parametrize('p',[np.nan,-.1,1.1])
def test_invalid_risk(p):
 with pytest.raises(ValueError):RiskLedger(1,3).charge(p)

def test_threshold_fallback_and_ties():
 assert constrained_choice([.8,.9],[20,5],.75)==(0,False,2)
 assert constrained_choice([.2,.4,.4],[100,2,3],.9)==(2,True,0)
 assert constrained_choice([.4,.4],[0,0],.9)==(0,True,0)
@pytest.mark.parametrize('p,score', [([np.nan],[1]),([.2],[-1]),([],[]),([2],[1]),([.2],[np.inf])])
def test_invalid_acquisition(p,score):
 with pytest.raises(ValueError):constrained_choice(p,score,.75)

@pytest.mark.parametrize('policy',POLICIES)
def test_hidden_outcome_isolation(cfg,pool,policy):
 cs,ys=pool;initial=('0','2','5','8')
 first,_=replay(cs,ys,cfg,7,policy,initial)
 altered=dict(ys)
 for c in cs:
  if c.case_id not in initial:altered[c.case_id]=Outcome(9999,0)
 second,_=replay(cs,altered,cfg,7,policy,initial)
 for key in ['case_id','feasibility_probability_raw','strength_mean_mpa','acquisition_score','predicted_risk_spent_after']:
  assert first[0][key]==second[0][key]
 assert first[0]['diagnostics']['observed_ids']==list(initial)

@pytest.mark.parametrize('policy',['random','strength_bo','cbo','rc_cbo'])
def test_unchanged_baselines(cfg,pool,policy):
 a,b=replay(*pool,cfg,2,policy);x,y=original(*pool,cfg,2,policy)
 assert b==y
 for r,s in zip(a,x):
  for k in s:
   if k!='diagnostics':assert r[k]==s[k]

@pytest.mark.parametrize('policy',['risk_threshold','risk_budget','cd_cbo','cd_risk_threshold'])
def test_all_failed_initialization_and_duplicate_guard(cfg,pool,policy):
 cs,ys=pool;obs=tuple(Observation(c,Outcome(200,0)) for c in cs[:4])
 r=select(obs,cs[4:],cfg,policy,0,1,RiskLedger(.75,3))
 assert r['mode']=='FEASIBILITY_DISCOVERY'
 assert np.isfinite(r['acquisition_score'])
 with pytest.raises(ValueError):select(obs,cs,cfg,policy,0,1,RiskLedger(.75,3))

def test_continuous_tail_monotonic_and_finite(cfg):
 x=np.array([[0.,1],[.5,.5],[1.,0]])
 m=DuctilityGP(cfg['ductility']).fit(x,[0.,10.,90.])
 p,mu,sd,mass=m.predict(x,10)
 p2,*_=m.predict(x,12)
 assert np.all(p2<=p) and np.all(sd>0) and np.isfinite(p).all()
 assert np.all((mass>=0)&(mass<=1))
 # Same binary labels, different measured magnitudes must change continuous forecasts.
 m2=DuctilityGP(cfg['ductility']).fit(x,[0.,10.,11.])
 assert not np.allclose(m.predict(x,20)[0],m2.predict(x,20)[0])
 with pytest.raises(ValueError):m.predict(x,0)

def test_group_leakage_rejected(cfg,pool):
 cs,ys=pool
 with pytest.raises(ValueError):replay(cs,ys,cfg,0,'cbo',('0','1','2','3'),{'0','4','5','6'})

def test_predictive_ledger_matches_logged_probabilities(cfg,pool):
 tr,_=replay(*pool,cfg,5,'risk_budget')
 spent=0
 for row in tr:
  assert row['predicted_risk_spent_before']==pytest.approx(spent)
  assert row['minimum_probability']==pytest.approx(max(0,1-max(0,.75-spent)/(4-row['selection_step'])))
  spent+=1-row['feasibility_probability_raw']
  assert row['predicted_risk_spent_after']==pytest.approx(spent)
