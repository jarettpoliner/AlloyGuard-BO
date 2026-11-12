"""Post hoc interpretation only. Read frozen decisions; fit no models or policies."""
from pathlib import Path
import hashlib,json,math,itertools
import numpy as np
import pandas as pd
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'results/decision_review';O.mkdir(exist_ok=True)
# Snapshot all existing scientific inputs/artifacts, not caches or this separate workstream.
protected=[]
for folder in ['results/citrine','results/v2','src','configs','tests','data/citrine','docs']:
 protected += [p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
protected += [R/'requirements.lock',R/'pyproject.toml',R/'V2.md',R/'README.md']
snapshot={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(protected)}
M=pd.read_csv(R/'results/v2/evaluation/primary/metrics.csv');C=pd.read_csv(R/'results/v2/evaluation/primary/curves.csv');T=pd.read_json(R/'results/v2/evaluation/primary/traces.jsonl',lines=True)
co=pd.read_csv(R/'results/citrine/cohort.csv');policies=list(M.policy.unique());seeds=sorted(M.seed.unique())
assert len(seeds)==30 and len(M)==240
for metric in ['auc_mpa_evaluations','failure_count']:
 v1=pd.read_csv(R/'results/citrine/primary/metrics.csv').pivot(index='seed',columns='policy',values=metric)
 v2=M.pivot(index='seed',columns='policy',values=metric)
 assert np.allclose(v1,v2[v1.columns],atol=1e-10,rtol=0)
def ci(x):
 x=np.asarray(x,float);mean=float(x.mean());half=float(t.ppf(.975,len(x)-1)*x.std(ddof=1)/np.sqrt(len(x)))
 return {'mean':mean,'lower95':mean-half,'upper95':mean+half,'n':len(x)}
def fieller(loss,saved):
 # Confidence set for ratio mean(loss)/mean(saved), from paired t test inversion.
 x=np.asarray(loss);y=np.asarray(saved);n=len(x);q=t.ppf(.975,n-1)**2;v=np.cov(x,y,ddof=1)/n
 a=y.mean()**2-q*v[1,1];b=-2*(x.mean()*y.mean()-q*v[0,1]);c=x.mean()**2-q*v[0,0];disc=b*b-4*a*c
 if disc<0:return {'type':'all_real' if a<0 else 'empty','intervals':[]}
 roots=sorted([float((-b-np.sqrt(disc))/(2*a)),float((-b+np.sqrt(disc))/(2*a))]) if abs(a)>1e-12 else []
 if not roots:return {'type':'degenerate_linear','coefficients':[float(a),float(b),float(c)]}
 return {'type':'bounded' if a>0 else 'disjoint_unbounded','roots':roots,'scope':'Unrestricted Fieller ratio set; negative penalties are not operational.'}
rows=[]
for budget in [5,10,15]:
 for (seed,pol),g in C[C.step<=budget].groupby(['seed','policy']):
  g=g.sort_values('step');assert len(g)==budget+1
  rows.append(dict(budget=budget,seed=seed,policy=pol,auc=float(np.trapezoid(g.best_feasible_strength_mpa)),failures=int(g.iloc[-1].cumulative_failures),initial=float(g.iloc[0].best_feasible_strength_mpa),final=float(g.iloc[-1].best_feasible_strength_mpa)))
P=pd.DataFrame(rows);P.to_csv(O/'campaign_prefix_metrics.csv',index=False)
for metric,old in [('auc','auc_mpa_evaluations'),('failures','failure_count')]:
 a=P[P.budget==15].pivot(index='seed',columns='policy',values=metric);b=M.pivot(index='seed',columns='policy',values=old)
 assert np.allclose(a,b[a.columns])
summary=[];paired=[];utilities=[];breaks=[];dominance={};envelopes={}
lambdas=sorted(set(range(0,5001,50))|{250,500,1000,1500,2000,3000,5000})
for budget,g in P.groupby('budget'):
 A=g.pivot(index='seed',columns='policy',values='auc');F=g.pivot(index='seed',columns='policy',values='failures')
 means=g.groupby('policy')[['auc','failures']].mean();dom={}
 for p in policies:
  sr={'budget':int(budget),'policy':p}
  for metric in ['auc','failures','final']:
   for k,v in ci(g[g.policy==p][metric]).items():sr[metric+'_'+k]=v
  summary.append(sr)
  dom[p]=[q for q in policies if q!=p and means.loc[q,'auc']>=means.loc[p,'auc'] and means.loc[q,'failures']<=means.loc[p,'failures'] and (means.loc[q,'auc']>means.loc[p,'auc'] or means.loc[q,'failures']<means.loc[p,'failures'])]
  for lam in lambdas:
   u=A[p]-lam*F[p];delta=u-(A.cbo-lam*F.cbo)
   utilities.append(dict(budget=int(budget),policy=p,lambda_penalty=lam,utility_mean=float(u.mean()),**{'difference_'+k:v for k,v in ci(delta).items()}))
  if p!='cbo':
   loss=A.cbo-A[p];saved=F.cbo-F[p]
   breaks.append(dict(budget=int(budget),policy=p,mean_auc_loss=float(loss.mean()),mean_failures_saved=float(saved.mean()),break_even=float(loss.mean()/saved.mean()) if saved.mean()!=0 else None,loss_ci=ci(loss),saved_ci=ci(saved),fieller95=fieller(loss,saved),direction='new_policy_favored_above' if saved.mean()>0 else 'new_policy_favored_below' if saved.mean()<0 else 'parallel_utility_lines'))
 for p,q in itertools.combinations(policies,2):
  for metric,array in [('auc',A),('failures',F)]:paired.append(dict(budget=int(budget),policy=p,reference=q,metric=metric,**ci(array[p]-array[q])))
 # Exact upper envelope of empirical mean lines on lambda >=0 (descriptive only).
 crossings={0.}
 for p,q in itertools.combinations(policies,2):
  df=means.loc[p,'failures']-means.loc[q,'failures']
  if df:
   cross=(means.loc[p,'auc']-means.loc[q,'auc'])/df
   if cross>0:crossings.add(float(cross))
 points=sorted(crossings);env=[]
 for i,left in enumerate(points):
  right=points[i+1] if i+1<len(points) else None;mid=(left+right)/2 if right is not None else left+max(1,left)
  winner=(means.auc-mid*means.failures).idxmax()
  if env and env[-1]['policy']==winner:env[-1]['upper_lambda']=right
  else:env.append(dict(lower_lambda=left,upper_lambda=right,policy=winner))
 dominance[str(budget)]=dom;envelopes[str(budget)]=env
S=pd.DataFrame(summary);Q=pd.DataFrame(paired);U=pd.DataFrame(utilities)
S.to_csv(O/'summary.csv',index=False);Q.to_csv(O/'all_paired_differences.csv',index=False);U.to_csv(O/'utility_curves.csv',index=False)
(O/'break_even.json').write_text(json.dumps(breaks,indent=2)+'\n');(O/'pareto_and_utility_envelope.json').write_text(json.dumps({'mean_dominated_by':dominance,'empirical_mean_utility_envelope':envelopes},indent=2)+'\n')
a=T[T.policy_name=='risk_budget'].sort_values(['seed','selection_step']);b=T[T.policy_name=='risk_threshold'].sort_values(['seed','selection_step'])
match=(a.case_id.to_numpy()==b.case_id.to_numpy());different=sorted(a.loc[~match,'seed'].unique().tolist())
A=P[P.budget==15].pivot(index='seed',columns='policy',values='auc');F=P[P.budget==15].pivot(index='seed',columns='policy',values='failures')
initial=C[(C.policy=='cbo')&(C.step==0)].best_feasible_strength_mpa
maxfeas=float(co.loc[co.elongation_percent>=10,'yield_strength_mpa'].max())
n=co.leakage_group.value_counts();study=co.study_doi.value_counts()
cohort=dict(cases=len(co),feasible=int((co.elongation_percent>=10).sum()),feasible_fraction=float((co.elongation_percent>=10).mean()),chemistries=co.composition_key.nunique(),studies=co.study_doi.nunique(),components=len(n),largest_component=int(n.max()),component_size_counts={str(k):int(v) for k,v in n.value_counts().items()},component_equal_correlation_effective_count=float(n.sum()**2/(n*n).sum()),study_equal_correlation_effective_count=float(study.sum()**2/(study*study).sum()),effective_count_caveat='Concentration-based count assuming perfect within-group correlation, not an estimated statistical ESS.',probability_no_initial_feasible=math.comb(22,12)/math.comb(80,12),random_expected_failures_15=15*22/80,mean_initial_incumbent=float(initial.mean()),maximum_feasible_strength=maxfeas,initial_incumbent_auc_fraction=float(15*initial.mean()/A.cbo.mean()),cbo_auc_fraction_of_unattainable_instant_oracle=float(A.cbo.mean()/(15*maxfeas)),matched_risk_selections=int(match.sum()),risk_decision_count=len(match),risk_different_seeds=different,risk_budget_minus_threshold_auc=ci(A.risk_budget-A.risk_threshold),risk_budget_minus_threshold_failures=ci(F.risk_budget-F.risk_threshold),cbo_vs_random_auc=ci(A.cbo-A.random),cbo_vs_random_failures=ci(F.cbo-F.random))
(O/'cohort_and_distinguishability.json').write_text(json.dumps(cohort,indent=2)+'\n')
fig,axes=plt.subplots(1,3,figsize=(15,4.6))
for ax,budget in zip(axes,[5,10,15]):
 for p in policies:
  g=U[(U.budget==budget)&(U.policy==p)];ax.plot(g.lambda_penalty,g.utility_mean,label=p)
 ax.set(title=f'{budget}-query prefix',xlabel='Failure penalty λ (MPa × steps / failure)',ylabel='Mean utility (MPa × steps)')
axes[0].legend(fontsize=7);fig.suptitle('Externally specified penalty scenarios, not tuned policy parameters');fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(O/f'utility_curves.{ext}',dpi=170)
plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(15,4.6))
for ax,budget in zip(axes,[5,10,15]):
 for p in ['random','risk_threshold','risk_budget','cd_risk_threshold']:
  g=U[(U.budget==budget)&(U.policy==p)];ax.plot(g.lambda_penalty,g.difference_mean,label=p);ax.fill_between(g.lambda_penalty,g.difference_lower95,g.difference_upper95,alpha=.10)
 ax.axhline(0,color='black',linestyle=':');ax.set(title=f'{budget}-query prefix',xlabel='Failure penalty λ',ylabel='Utility difference vs CBO')
axes[0].legend(fontsize=7);fig.suptitle('Pointwise paired 95% seed intervals; not simultaneous or population intervals');fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(O/f'paired_utility.{ext}',dpi=170)
plt.close(fig)
# Additional pointwise comparisons at externally interpretable round penalties.
anchors=[]
for lam in [0,500,1000,1500,2000,3000,5000]:
 for p,q in itertools.combinations(policies,2):anchors.append(dict(lambda_penalty=lam,policy=p,reference=q,**ci((A[p]-A[q])-lam*(F[p]-F[q]))))
pd.DataFrame(anchors).to_csv(O/'all_paired_utility_anchors.csv',index=False)
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in snapshot.items())
(O/'preservation.json').write_text(json.dumps({'status':'PASSED','protected_file_count':len(snapshot),'sha256':snapshot},indent=2)+'\n')
print(json.dumps(cohort,indent=2));print('Envelope',envelopes)
print('15-step break-even',[(x['policy'],x['break_even'],x['fieller95']) for x in breaks if x['budget']==15])
print('Risk break-even by budget',[(x['budget'],x['policy'],x['break_even']) for x in breaks if x['policy'].startswith('risk_')])
# Concise decision report; all references resolve within this new analysis directory.
def fmt(v):return f"{v['mean']:,.2f} [{v['lower95']:,.2f}, {v['upper95']:,.2f}]"
lines=['# AlloyGuard-BO: scientific decision and campaign value', '',
'**Recommendation A: finalize AlloyGuard-BO for publication as a reproducible benchmark with negative and trade-off results. Do not start another algorithm campaign on this cohort.** Risk-aware selection has conditional practical value when avoiding failed experiments is sufficiently important, but neither risk method is established as broadly superior. This report is a post hoc interpretation of frozen results; it changes no method, protocol, or original verdict and does not publish anything externally.', '',
'## What v1/v2 established', '',
'All methods use 30 matched initializations, 12 initial cases and 15 additional experiments. Intervals below are paired, unadjusted 95% t intervals over replay seeds. They quantify initialization variability on this fixed cohort—not independent materials, studies, or population generalization. AUC rewards earlier discovery of confirmed feasible strength.', '',
'| Policy | Mean discovery AUC | Mean failures | ΔAUC vs CBO [95% interval] | Δfailures vs CBO [95% interval] |', '|---|---:|---:|---|---|']
for p in policies:
 lines.append(f"| {p} | {A[p].mean():,.2f} | {F[p].mean():.3f} | {fmt(ci(A[p]-A.cbo))} | {fmt(ci(F[p]-F.cbo))} |")
lines.extend(['',
'Ordinary CBO has the highest mean discovery AUC. Its advantage over random is uncertain (AUC interval includes zero), so “best mean” is not proof of universal superiority. It improves both AUC and failures over strength-only BO within conditional paired intervals. Reliability calibration remains indistinguishable from CBO. The risk policies save 2.00 failures per campaign (38.0%) while losing approximately 1,930–1,942 AUC units (13.8–13.9%); both effects have paired intervals excluding zero. This is a measurable trade-off, not the originally sought nearly free safety improvement. The original negative joint-goal verdicts remain valid.', '',
'**Mean Pareto frontier:** risk-budget BO, CD-risk-threshold, random, reliability-calibrated CBO, ordinary CBO. Strength-only BO is dominated by ordinary/calibrated CBO; CD-CBO is dominated by random and ordinary/calibrated CBO. Risk-threshold is technically dominated by risk-budget at the observed means, but this last dominance is too small to interpret as a reliable algorithm difference. Mean dominance is descriptive, not simultaneous statistical dominance.', '',
'**The two binary risk policies are not meaningfully distinguished here.** They choose the same case at 435/450 matched steps and differ only in seeds 6 and 15. Risk-budget minus risk-threshold AUC is +11.90 [−12.44, 36.24]; failure counts and final feasible strength are identical in every seed. Zero observed failure-difference variance is not proof of population equivalence. Fallback occurs at 442/450 and 441/450 selections: the .75 predicted-feasibility requirement is usually unattainable, so both mostly select minimum predicted risk. This benchmark barely exercises a genuinely distinct budget-allocation mechanism. All risk-budget runs exceed their predicted 3.75 allocation, despite fewer actual failures; it is not a hard safety guarantee.', '',
'## Does retaining continuous ductility help?', '',
'Not with the tested specification. On identical CBO histories and queried cases, continuous-model Brier is 0.2693 versus binary 0.2220; paired difference +0.0473 [0.0216, 0.0730]. Log loss increases by 0.2572 [0.1490, 0.3655], and pooled ROC AUC falls from 0.6786 to 0.5613. In the measured 5–15% elongation band, Brier worsens from 0.2926 to 0.4897. On random histories continuous Brier is modestly lower but its paired interval crosses zero, while log loss is worse. Thus the negative prediction result is not solely caused by CD-CBO selecting different cases.', '',
'CD-CBO’s nominal 95% ductility intervals cover only 78.4%; standardized log residual SD is 1.83 rather than 1. These observations support misspecified uncertainty, with consequential confident errors. Plausible contributors are fixed log-response noise, heteroscedastic literature measurements, sparse composition coverage, missing processing inputs, and a Gaussian log-response approximation that does not remove skewness. Kernel-bound warnings persist. These are supported limitations, not a causal identification of which change would fix them. Modeling magnitude is not inherently worse: this particular continuous model failed. Strength–ductility independence in product CEI is another untested approximation.', '',
'## Cost-sensitive campaign value', '',
'Use **U = AUC − λ × failures**, with λ set externally by the experimental decision-maker. AUC has units MPa × experiment steps; λ therefore has units MPa × steps per failed experiment. It is a preference conversion, not money, profit, or physical yield. A failure already consumes a query and can reduce AUC; the additional penalty represents extra aversion/cost beyond that opportunity loss. Equal successful-experiment costs and shared initialization costs cancel at a fixed budget. Different durations, unequal assay costs, catastrophic failures, and terminal-value preferences are not represented.', '',
'The transparent illustrative grid is λ = 0, 50, …, 5,000, with no penalty chosen or optimized from outcomes. Negative utilities at large penalties are permissible under this arbitrary zero. At 15 steps, λ≈965 means accepting approximately 64.35 MPa less *average incumbent strength over those steps* per avoided failure; this is not the loss of final strength or a currency conversion.', '',
'For a policy with positive mean failures saved, break-even against CBO is (mean AUC lost)/(mean failures saved). The 15-step estimates and paired Fieller 95% ratio sets are:', '',
'| Policy | Break-even λ vs CBO | Fieller 95% set |', '|---|---:|---|'])
for p in ['risk_threshold','risk_budget','cd_risk_threshold']:
 b=next(x for x in breaks if x['budget']==15 and x['policy']==p);lo,hi=b['fieller95']['roots'];lines.append(f"| {p} | {b['break_even']:,.2f} | [{lo:,.2f}, {hi:,.2f}] |")
lines.extend(['',
'These wide intervals reflect uncertain benefit-to-cost ratios. Random’s point crossover is 995.60 but its failures-saved interval includes zero and its Fieller set contains every nonnegative λ; there is no localized break-even estimate supported by these data. The calibrated-CBO crossover at 202.50 is driven by a negligible 0.0333 failures/run difference and has an all-real Fieller set. Neither should be treated as a reliable operational threshold.', '',
'| External λ | Risk-budget utility difference vs CBO [95% interval] |', '|---:|---|'])
for lam in [0,500,1000,1500,2000,3000,5000]:lines.append(f"| {lam:,} | {fmt(ci((A.risk_budget-A.cbo)-lam*(F.risk_budget-F.cbo)))} |")
lines.extend(['',
'At λ=1,000 the mean preference just flips but uncertainty is large. At externally chosen λ=2,000 the risk-budget benefit is +2,069.53 [207.96, 3,931.10], and risk-threshold is +2,057.63 [187.80, 3,927.46]. This supports conditional practical value against ordinary CBO on this cohort. It does not establish superiority to every policy or justify choosing λ=2,000 because its interval excludes zero. Intervals are pointwise, not simultaneous across penalties/comparisons; the analysis is post hoc.', '',
'The empirical all-policy utility envelope at 15 steps is CBO for λ<202.50, calibrated CBO from 202.50–956.22, CD-risk-threshold from 956.22–1,048.70, and risk-budget above 1,048.70 (ties at boundaries). This is a descriptive geometry of mean lines, not a recommendation to switch algorithms at precisely these values. Random is Pareto-nondominated yet never maximizes this linear mean utility at 15 steps: nondominated points need not be supported by a linear objective. The narrow CD/calibration regions are not evidence of algorithmic improvement. All pairwise utility intervals at round penalties are supplied separately.', '',
'## Campaign-budget sensitivity', '',
'| Additional-query prefix | Risk-threshold break-even vs CBO | Risk-budget break-even vs CBO | Empirical mean-utility envelope |', '|---:|---:|---:|---|'])
for budget in [5,10,15]:
 bs={x['policy']:x for x in breaks if x['budget']==budget}
 env='; '.join(f"{e['policy']} {e['lower_lambda']:.1f}–"+(f"{e['upper_lambda']:.1f}" if e['upper_lambda'] is not None else '∞') for e in envelopes[str(budget)])
 lines.append(f"| {budget} | {bs['risk_threshold']['break_even']:.2f} | {bs['risk_budget']['break_even']:.2f} | {env} |")
lines.extend(['',
'These are the first 5/10/15 decisions from the frozen 15-query campaigns, not fresh horizon-aware evaluations. In particular, risk-budget still planned for 15 steps; a newly budgeted 5-step policy might behave differently and has not been tested. Absolute AUC scales with horizon, so λ thresholds cannot be transferred unchanged to a different definition such as mean AUC or terminal strength. Paired uncertainty at every prefix/penalty is in the CSVs and plots. No extrapolation beyond 15 queries is supported.', '',
'## Can this benchmark distinguish better methods?', '',
'Feasibility is common: 58/80 cases (72.5%) pass. Uniform sampling expects 4.125 failures in 15 queries; the observed 30-seed mean is 4.30. With 12 uniform initial cases, the exact chance of no feasible incumbent is only 1.07×10⁻⁸. The benchmark consequently offers almost no test of cold-start feasibility discovery. Risk-budget saves only 1.03 failures relative to random, versus 2.00 relative to CBO; its practical increment should not be framed only against the riskier acquisition baseline.', '',
'The mean initial incumbent is 792.76 MPa. Holding it unchanged throughout would already account for 85.0% of CBO’s mean AUC. Therefore AUC retention can obscure weak *incremental* discovery, and a 98% retention target is not equivalent to retaining 98% of newly acquired value. Yet CBO achieves only 80.7% of the unattainable “best 1,155 MPa alloy known from step zero” ceiling: high feasibility does not establish that CBO is optimal or that improvement is impossible.', '',
'The 80 cases represent 68 chemistries, 36 studies and 31 connected study-or-chemistry components, not 80 proven independent experiments. Sixteen components are singletons; the largest contains 9 cases. The concentration count (Σn)²/Σn² is 18.6 components (22.7 by study), under a perfect-within-group-correlation analogy—not an estimated effective statistical sample size. Residual dependence across components is unknown. Ambiguous repeated composition/recipe records were excluded in v1 (159 records); this avoids treating ambiguous duplicates as independent but narrows representativeness. Remaining recipes do not fully control treatment details, strain rate, or measurement uncertainty. Sixty-three cases have possible overlap with earlier software-development data, so this is not pristine external validation.', '',
'Grouped stress tests retain only 15–34 target cases, one fold exhausts all 15, and another has 30/34 feasible cases with incumbent-dominated AUC. They demonstrate execution under group shift, not robust cross-dataset generalization. The paired design can expose large conditional losses (as it did for risk and CD-CBO), but cannot resolve small calibration/risk-policy differences or establish stable rankings across new alloys. More replay seeds could reduce conditional Monte Carlo uncertainty; they do not add independent measurements. Formal population power or a true effective sample size cannot be recovered from these replays alone.', '',
'## Decision and conditions for a materially stronger v3', '',
'**Choose A now.** Publish the reproducible benchmark, source qualification, leakage controls, negative calibration/continuous-model results, and explicit safety–discovery frontier. Useful claims are that constrained acquisition improves over unconstrained strength search in this replay, stricter risk preferences buy fewer failures at appreciable discovery cost, and predictive magnitude or calibration alone does not guarantee better decisions. Unsupported claims include universal CBO superiority, hard safety control, superiority of risk budgeting over thresholding, independent-dataset generalization, or economic savings.', '',
'Risk-aware policies have preference-dependent value, especially when externally justified failure penalties are high. The present evidence favors describing a minimum-predicted-risk versus discovery trade-off, not crediting a sophisticated risk-budget mechanism. Retain both published implementations/results, but do not promote one based on their tiny difference.', '',
'A future B would be justified only as a separately preregistered project with a materially stronger basis: a source-disjoint independent dataset or prospective campaign; development-only model/noise/threshold selection; study/process-aware validation; sufficient infeasible and near-threshold measurements; and external elicitation of failure costs and campaign horizon before testing. A specific hypothesis worth investigating on development data is that validated heteroscedastic ductility uncertainty plus recorded processing conditions reduces confidently wrong feasibility predictions. The current logs motivate that hypothesis but do not validate a replacement model. An alternative genuinely different objective—e.g. measured assay cost and terminal feasible strength—requires real cost information and an independent evaluation, not a retrospective metric chosen to rescue these results.', '',
'Further algorithm selection on this same exposed cohort would introduce researcher selection bias even with new seeds. This utility analysis does not retroactively validate either v2 policy or revise its frozen goals. No v3 method was implemented and no original artifact was overwritten.', '',
'## Evidence and reproduction', '',
'Run from the repository: `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLCONFIGDIR="$PWD/.matplotlib-cache" .venv/bin/python scripts/review_campaign_value.py`.', '',
'Inputs: `results/v2/evaluation/primary/{metrics.csv,curves.csv,traces.jsonl}`, frozen v1 results, qualified cohort, v2 model/common-history diagnostics. Outputs here: `summary.csv` (means and intervals), `all_paired_differences.csv` (all policy pairs), `break_even.json` (ratio sets), `utility_curves.csv`, `all_paired_utility_anchors.csv`, `pareto_and_utility_envelope.json`, `cohort_and_distinguishability.json`, and `preservation.json`. Utility plots are PNG/PDF. Budget metrics are recomputed from decision curves and checked against frozen 15-step summaries. The original v1/v2 baseline equality is verified. No model fitting or experimental rerun is needed.'])
(O/'DECISION_REPORT.md').write_text('\n'.join(lines)+'\n')
# Keep the full statistical discussion as an appendix and the requested decision brief concise.
(O/'TECHNICAL_APPENDIX.md').write_text((O/'DECISION_REPORT.md').read_text())
brief=['# AlloyGuard-BO scientific decision report', '',
'**Recommendation A: finalize and publish the reproducible benchmark with its negative and trade-off results. Do not start v3 on the same cohort.** No experiments or frozen artifacts were changed; no new algorithm was developed. Publication is a recommendation, not an action taken.', '',
'## What the evidence establishes', '',
'Thirty matched replays show a real conditional safety–discovery trade-off. Ordinary CBO has the best mean discovery AUC; both binary risk policies avoid two failures per 15-query campaign at a loss of roughly 14% of AUC. Differences below are paired 95% t intervals across replay seeds, conditional on this same 80-case cohort—not population or independent-dataset confidence intervals.', '',
'| Policy | Mean AUC | Mean failures | ΔAUC vs CBO [95% interval] | Δfailures vs CBO [95% interval] |', '|---|---:|---:|---|---|']
for p in policies:brief.append(f"| {p} | {A[p].mean():,.1f} | {F[p].mean():.2f} | {fmt(ci(A[p]-A.cbo))} | {fmt(ci(F[p]-F.cbo))} |")
brief.extend(['',
'CBO improves on strength-only BO here, but its AUC advantage over random remains uncertain. Reliability calibration did not confirm improvement. The original v2 joint goals remain unmet: reduced failures did not preserve 98% of discovery AUC.', '',
'**Mean Pareto frontier:** risk-budget, CD-risk-threshold, random, calibrated CBO, ordinary CBO. Strength BO and CD-CBO are dominated by CBO/calibrated CBO; CD-CBO is also dominated by random. Risk-threshold is technically dominated by risk-budget at the means, but the difference is not meaningful evidence: risk-budget gains only 11.90 AUC [−12.44, 36.24], with identical failure counts and final strength in every seed. They match on 435/450 selections and differ in only two seeds. Fallbacks occur on 442/450 and 441/450 decisions, so both mostly act as minimum-predicted-risk selection. This does not establish a benefit from explicit risk budgeting or a hard safety guarantee.', '',
'**Continuous ductility failed under the tested assumptions.** On exactly CBO’s histories/cases, continuous Brier worsens from 0.2220 to 0.2693; paired increase 0.0473 [0.0216, 0.0730]. Log loss increases by 0.2572 [0.1490, 0.3655]; ranking and near-threshold scores worsen. CD-CBO’s nominal 95% ductility intervals cover only 78.4%. Fixed noise, heterogeneous literature measurements, missing processing inputs and an inadequate log-Gaussian uncertainty model are plausible contributors, not proven isolated causes. The finding rejects this specification’s claimed benefit, not continuous information in principle.', '',
'## When fewer failures have practical value', '',
'For **U = AUC − λ × failures**, λ is an externally elicited preference in **MPa × experiment steps per failure**, not money. Failure already consumes an experiment; this penalty represents additional aversion beyond the discovery opportunity cost. The illustrative range 0–5,000 (increments of 50) is not optimized. Initial costs cancel between matched policies; unequal assay costs and durations are not modeled.', '',
'| Binary risk policy | 15-query break-even λ vs CBO | Paired Fieller 95% set |', '|---|---:|---|',
'| Risk-threshold | 971.19 | [522.99, 1,841.66] |',
'| Risk-budget | 965.24 | [522.86, 1,824.52] |', '',
'At λ=1,000, risk-budget’s utility advantage is +69.53 [−1,046.52, 1,185.57]: inconclusive. At externally justified λ=2,000 it is +2,069.53 [207.96, 3,931.10]; threshold gives +2,057.63 [187.80, 3,927.46]. Thus risk-aware selection can be practically valuable to a sufficiently failure-averse campaign, without meeting the original nearly-free-safety goal. This does not prove superiority to every alternative or justify choosing a penalty because its interval excludes zero. All intervals are pointwise and unadjusted.', '',
'Across all methods, the empirical 15-step utility envelope switches CBO → calibrated CBO → CD-risk-threshold → risk-budget at λ≈202.50, 956.22 and 1,048.70. These precise crossings are descriptive, not robust recommendations; the calibration crossover has an unbounded confidence set. Random is Pareto-nondominated but never maximizes this linear mean utility at 15 steps. Full pairwise uncertainty is supplied.', '',
'| Additional-query prefix | Threshold break-even λ | Budget break-even λ |', '|---:|---:|---:|', '| 5 | 340.68 | 329.32 |', '| 10 | 675.28 | 652.84 |', '| 15 | 971.19 | 965.24 |', '',
'These are early-stopped prefixes of the frozen 15-query trajectories, not newly horizon-optimized policies. Risk-budget still planned for 15. AUC scales with horizon; penalties must be interpreted consistently. No conclusions beyond 15 queries are supported.', '',
'## Why the benchmark is useful but limited', '',
'Feasibility is already 72.5% (58/80): random expects 4.125 failures in 15 queries, and a 12-case initialization lacks any feasible case with probability only 1.07×10⁻⁸. Cold-start feasibility discovery is effectively untested. The initial incumbent accounts for 85.0% of CBO AUC if held constant, so retention percentages can hide poor incremental discovery. Nevertheless, CBO reaches only 80.7% of the idealized best-alloy-from-step-zero ceiling; improvement is not mathematically exhausted.', '',
'There are 68 chemistries, 36 studies and 31 connected study/chemistry groups. A group-size concentration proxy is 18.6—not an estimated statistical effective sample size. Ambiguous duplicate recipes were excluded, but processing and study dependence remain. Grouped test pools contain only 15–34 cases; one is exhausted by the budget and another is heavily feasible/incumbent-limited. Thirty seeds do not create thirty independent datasets. The benchmark detects large conditional trade-offs but does not reliably distinguish small algorithmic gains. More seeds reduce Monte Carlo uncertainty, not data dependence or generalization uncertainty.', '',
'## Decision before v3', '',
'Publish the useful findings: constrained search versus unconstrained search, the quantified failure–discovery frontier, and the failure of calibration/continuous magnitude alone to improve decisions. Do not claim universal CBO superiority, economic savings, hard risk control, or risk-budget superiority over thresholding.', '',
'A materially stronger v3 needs source-disjoint independent or prospective data; development-only tuning; study/process-aware validation; sufficient infeasible and near-boundary cases; and externally specified campaign costs/horizons. The logs motivate testing whether independently validated heteroscedastic ductility uncertainty and processing information reduce confidently wrong predictions. They do not yet validate a replacement algorithm. A different objective such as measured assay cost and terminal strength requires actual cost evidence and a fresh protocol, not retrospective rescue of v2. Further method selection on this exposed cohort would create selection bias even with new seeds.', '',
'## Supporting artifacts', '',
'[Full statistical interpretation and reproduction command](TECHNICAL_APPENDIX.md) · [Utility curves](utility_curves.png) · [Paired utility intervals](paired_utility.png) · [All paired policy differences](all_paired_differences.csv) · [Budget/utility data](utility_curves.csv) · [Preservation check](preservation.json).'])
(O/'DECISION_REPORT.md').write_text('\n'.join(brief)+'\n')
# Independent arithmetic checks against decision labels, not just frozen metrics.
for row in P.itertuples():
 selected=T[(T.seed==row.seed)&(T.policy_name==row.policy)&(T.selection_step<=row.budget)]
 assert len(selected)==row.budget and int((~selected.feasible).sum())==row.failures
for item in breaks:
 if item['break_even'] is not None:
  assert abs(item['mean_auc_loss']-item['break_even']*item['mean_failures_saved'])<1e-7
 # Inverted ratio endpoints must have utility CI touching zero.
 if item['fieller95']['type']=='bounded':
  sub=P[P.budget==item['budget']];aa=sub.pivot(index='seed',columns='policy',values='auc');ff=sub.pivot(index='seed',columns='policy',values='failures')
  for endpoint in item['fieller95']['roots']:
   interval=ci((aa[item['policy']]-aa.cbo)-endpoint*(ff[item['policy']]-ff.cbo))
   assert min(abs(interval['lower95']),abs(interval['upper95']))<1e-6
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in snapshot.items())
(O/'verification.json').write_text(json.dumps({'status':'PASSED','policy_budget_seed_rows_checked':len(P),'full_budget_matches_frozen_metrics':True,'baseline_matches_v1':True,'prefix_failures_match_decision_labels':True,'fieller_endpoints_match_paired_utility_intervals':True,'protected_files_unchanged':len(snapshot),'no_new_models_or_policy_runs':True},indent=2)+'\n')
