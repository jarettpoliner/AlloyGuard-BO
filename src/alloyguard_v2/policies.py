"""Observed-only policies. Predicted risk is not a guarantee on realized failures."""
from dataclasses import dataclass, asdict
import time
import numpy as np
from scipy.special import ndtr
from scipy.spatial.distance import cdist
from alloyguard_strength.models import StrengthGP, FeasibilityGP
from alloyguard_strength.policies import select_next as baseline, expected_improvement, POLICIES as BASELINES
from alloyguard_strength.schema import Decision

POLICIES=(*BASELINES,'risk_threshold','risk_budget','cd_cbo','cd_risk_threshold')

@dataclass(frozen=True)
class RiskLedger:
    total: float
    horizon: int
    expenditures: tuple[float,...]=()
    def __post_init__(self):
        if not np.isfinite(self.total) or self.total<0 or self.horizon<1 or len(self.expenditures)>self.horizon:
            raise ValueError('Invalid risk budget')
        if any(not np.isfinite(x) or not 0<=x<=1 for x in self.expenditures):
            raise ValueError('Invalid expenditure')
    @property
    def spent(self): return float(sum(self.expenditures))
    @property
    def remaining(self): return self.total-self.spent
    @property
    def allowance(self):
        if len(self.expenditures)>=self.horizon: raise ValueError('Exhausted horizon')
        return max(0.,self.remaining)/(self.horizon-len(self.expenditures))
    def charge(self,p):
        if not np.isfinite(p) or not 0<=p<=1: raise ValueError('Invalid probability')
        return RiskLedger(self.total,self.horizon,(*self.expenditures,1-float(p)))

def constrained_choice(p,score,minimum):
    """Eligible CEI maximum; otherwise minimum risk, then CEI, then input order."""
    p=np.asarray(p,float);score=np.asarray(score,float)
    if p.ndim!=1 or len(p)==0 or p.shape!=score.shape or not np.isfinite(p).all() or not np.isfinite(score).all() or ((p<0)|(p>1)).any() or (score<0).any() or not 0<=minimum<=1:
        raise ValueError('Invalid acquisition inputs')
    eligible=np.flatnonzero(p>=minimum)
    fallback=not len(eligible)
    if fallback: eligible=np.flatnonzero(p==p.max())
    return int(eligible[np.argmax(score[eligible])]),fallback,int((p>=minimum).sum())

class DuctilityGP:
    """Gaussian log1p(elongation) observation forecast, censored at zero on inversion.

    Fixed noise/floor are engineering assumptions, not fitted on evaluation outcomes.
    Elongation has no physical 100% upper bound. The Gaussian assigns negative
    log-response mass; map that mass to zero and explicitly report it.
    """
    def __init__(self,config): self.config=config
    def fit(self,x,y):
        y=np.asarray(y,float)
        if not np.isfinite(y).all() or (y<0).any(): raise ValueError('Invalid elongation')
        self.model=StrengthGP({'noise_mpa':self.config['log_noise'],
                              'target_scale_floor_mpa':self.config['log_scale_floor']}).fit(x,np.log1p(y))
        return self
    def predict(self,x,threshold):
        if not np.isfinite(threshold) or threshold<=0: raise ValueError('Positive threshold required')
        mu,latent,sd=self.model.predict(x)
        p=np.clip(ndtr((mu-np.log1p(threshold))/sd),1e-7,1-1e-7)
        return p,mu,sd,ndtr(-mu/sd)

def select(observations,candidates,config,policy,seed,step,ledger):
    if policy in BASELINES:
        return asdict(baseline(observations,candidates,config,policy,seed,step))
    if policy not in POLICIES or not observations or not candidates: raise ValueError('Invalid policy inputs')
    ids=[c.case_id for c in candidates];seen={o.candidate.case_id for o in observations}
    if len(set(ids))!=len(ids) or seen.intersection(ids): raise ValueError('Duplicate/observed candidates')
    if len(ledger.expenditures)!=step-1: raise ValueError('Risk ledger step mismatch')
    start=time.perf_counter()
    x=np.array([o.candidate.composition_features for o in observations]);q=np.array([c.composition_features for c in candidates])
    ys=np.array([o.outcome.yield_strength_mpa for o in observations]);ye=np.array([o.outcome.elongation_percent for o in observations])
    labels=ye>=config['elongation_threshold_percent']
    strength=StrengthGP(config['strength']).fit(x,ys);mu,sd,noisy=strength.predict(q)
    extra={}
    if policy.startswith('cd_'):
        model=DuctilityGP(config['ductility']).fit(x,ye)
        p,em,es,negative=model.predict(q,config['elongation_threshold_percent'])
        feasibility=dict(model.model.diagnostics,kind='LOG1P_ELONGATION_REGRESSION')
    else:
        model=FeasibilityGP(config['feasibility']).fit(x,labels);p=model.predict(q);feasibility=model.diagnostics
    distance=cdist(q,x).min(axis=1)
    if labels.any():
        ei=expected_improvement(mu,sd,float(ys[labels].max()));score=ei*p;mode='FEASIBLE_STRENGTH_IMPROVEMENT'
    else:
        ei=np.zeros(len(q));score=p+config['exploration_coefficient']*np.minimum(distance/np.sqrt(2),1);mode='FEASIBILITY_DISCOVERY'
    minimum=0.
    if policy in ('risk_threshold','cd_risk_threshold'):minimum=config['risk']['minimum_probability']
    if policy=='risk_budget':minimum=max(0.,1-ledger.allowance)
    i,fallback,eligible=constrained_choice(p,score,minimum)
    if policy.startswith('cd_'):
        extra={'elongation_log_mean':float(em[i]),'elongation_log_observation_std':float(es[i]),
               'elongation_negative_mass':float(negative[i]),'elongation_median_percent':float(max(0,np.expm1(em[i]))),
               'elongation_interval_percent':[float(max(0,np.expm1(em[i]-1.96*es[i]))),float(max(0,np.expm1(em[i]+1.96*es[i])))]}
    c=candidates[i]
    decision=Decision(c.case_id,policy,step,c.composition_features,c.feature_status,float(mu[i]),float(sd[i]),float(noisy[i]),
       (float(mu[i]-1.96*noisy[i]),float(mu[i]+1.96*noisy[i])),float(p[i]),float(p[i]),'NOT_APPLIED',1.,
       float(ei[i]),float(ei[i]*p[i]),float(score[i]),mode,len(observations),float(distance[i]),
       ids[int(np.argmax(score))],ids[int(np.argmax(score))],config['config_hash'],config['dataset_hash'],
       {'strength':strength.diagnostics,'feasibility':feasibility,'calibration':{},'calibration_folds':[],
        'observed_ids':[o.candidate.case_id for o in observations],
        'observed_groups':[o.candidate.leakage_group for o in observations],'fit_seconds':time.perf_counter()-start})
    return dict(asdict(decision),**extra,minimum_probability=minimum,eligible_count=eligible,risk_fallback=fallback,
        predicted_risk_spent_before=ledger.spent,predicted_risk_remaining_before=ledger.remaining,
        predicted_risk_allowance=ledger.allowance,predicted_risk_selected=1-float(p[i]))
