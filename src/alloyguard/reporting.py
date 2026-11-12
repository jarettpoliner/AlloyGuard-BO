"""Regenerate descriptive analyses and figures solely from immutable run artifacts."""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import t
from sklearn.metrics import roc_auc_score
from .metrics import paired_interval

LABELS={"random":"Random", "hardness_bo":"Hardness-only BO", "cbo":"Ordinary CBO", "rc_cbo":"RC-CBO (calibration gated off)"}
COLORS={"random":"#777777","hardness_bo":"#d55e00","cbo":"#0072b2","rc_cbo":"#009e73"}


def load_traces(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def compare(metrics):
    pairs={}
    for left,right in (("cbo","hardness_bo"),("cbo","random"),("rc_cbo","cbo"),("rc_cbo","hardness_bo")):
        pairs[f"{left}_minus_{right}"]={}
        for metric in ("auc_gpa_evaluations","failure_count","best_feasible_at_15_gpa","brier","hardness_mae_gpa"):
            pivot=metrics.pivot(index="seed",columns="policy",values=metric)
            pairs[f"{left}_minus_{right}"][metric]=paired_interval(pivot[left]-pivot[right])
    return pairs


def make_figures(root,curves,traces):
    out=root/"results/figures"; out.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":220})
    def save(fig,name):
        fig.tight_layout();fig.savefig(out/f"{name}.png");fig.savefig(out/f"{name}.pdf");plt.close(fig)
    for column,name,ylabel in (("best_feasible_hardness_gpa","01_discovery","Best confirmed feasible hardness (GPa)"),
                               ("cumulative_failures","02_failures","Cumulative rank <3 selections")):
        fig,ax=plt.subplots(figsize=(7,4.4))
        for i,(policy,label) in enumerate(LABELS.items()):
            subset=curves[curves.policy==policy]
            g=subset.groupby("selection_step")[column]
            m=g.mean();sem=g.std()/np.sqrt(g.count())
            half=t.ppf(.975,len(subset.seed.unique())-1)*sem
            ax.plot(m.index,m.values,label=label,color=COLORS[policy],linestyle="--" if policy=="rc_cbo" else "-",linewidth=2)
            ax.fill_between(m.index,(m-half).values,(m+half).values,color=COLORS[policy],alpha=.09)
        ax.set(xlabel="Additional experimental selections (12 initial)",ylabel=ylabel)
        ax.legend(fontsize=8);ax.set_xticks([0,5,10,15]); ax.grid(alpha=.15)
        save(fig,name)
    # Prequential calibration uses only forecasts recorded before reveal.
    fig,axes=plt.subplots(1,2,figsize=(8,3.8))
    rc=[r for r in traces if r["policy_name"]=="rc_cbo"]
    reliability=[]
    for key,label in (("feasibility_probability_raw","Raw"),("feasibility_probability_calibrated","Calibrated (identity)")):
        p=np.array([r[key] for r in rc]); y=np.array([r["measured_feasible"] for r in rc],float)
        bins=np.minimum((p*5).astype(int),4)
        xs=[];ys=[]
        for b in range(5):
            mask=bins==b
            if mask.any():
                xs.append(float(p[mask].mean()));ys.append(float(y[mask].mean()))
                reliability.append({"forecast":label,"bin":b,"count":int(mask.sum()),"mean_probability":xs[-1],"empirical_feasible_fraction":ys[-1]})
        axes[0].plot(xs,ys,"o-",label=label,alpha=.8)
    axes[0].plot([0,1],[0,1],"k--",alpha=.4)
    axes[0].set(xlim=(0,1),ylim=(0,1),xlabel="Mean forecast probability",ylabel="Observed feasible fraction",title="Prequential; 5 fixed-width bins")
    axes[0].legend(fontsize=8)
    axes[1].hist([r["feasibility_probability_raw"] for r in rc],bins=np.linspace(0,1,11),color=COLORS["cbo"])
    axes[1].set(xlabel="Feasibility probability",ylabel="Selected forecasts",title="Repeated finite-pool observations")
    save(fig,"03_calibration")
    pd.DataFrame(reliability).to_csv(root/"results/reliability_bins.csv",index=False)
    fig,axes=plt.subplots(1,2,figsize=(8,3.8))
    for policy,label in LABELS.items():
        rows=[r for r in traces if r["policy_name"]==policy]
        actual=np.array([r["measured_hardness_gpa"] for r in rows]);pred=np.array([r["hardness_mean_gpa"] for r in rows])
        sd=np.array([r["hardness_observation_std_gpa"] for r in rows])
        axes[0].scatter(actual,pred,s=8,alpha=.25,label=label,color=COLORS[policy])
        axes[1].hist((actual-pred)/sd,bins=np.linspace(-8,8,33),histtype="step",density=True,label=label,color=COLORS[policy])
    axes[0].plot([2,13],[2,13],"k--",alpha=.4)
    axes[0].set(xlabel="Measured grouped hardness (GPa)",ylabel="Prequential predicted hardness (GPa)")
    axes[1].set(xlabel="Residual / observation predictive SD",ylabel="Density (display range ±8)")
    axes[0].legend(fontsize=6);save(fig,"04_predictive_validation")
    # Predefined descriptive failure criteria, not selection/threshold tuning.
    rows=[r for r in traces if r["policy_name"]=="hardness_bo"]
    cases=[r for r in rows if r["hardness_mean_gpa"]>=8 and r["feasibility_probability_raw"]<.35 and not r["measured_feasible"]]
    fig,ax=plt.subplots(figsize=(7,4))
    ax.scatter([r["hardness_mean_gpa"] for r in rows],[r["feasibility_probability_raw"] for r in rows],
               c=["#0072b2" if r["measured_feasible"] else "#d55e00" for r in rows],s=14,alpha=.3)
    case=None
    if cases:
        case=max(cases,key=lambda r:r["hardness_mean_gpa"])
        ax.scatter([case["hardness_mean_gpa"]],[case["feasibility_probability_raw"]],s=130,facecolors="none",edgecolors="black")
        ax.set_title(f"Actual hardness-only selection: seed {case['seed']}, step {case['selection_step']}\nMeasured {case['measured_hardness_gpa']:.2f} GPa, rank {case['measured_ductility_rank']} (infeasible)",fontsize=10)
        (root/"results/representative_failure.json").write_text(json.dumps(case,indent=2)+"\n")
    else:
        ax.set_title("No case satisfies the descriptive failure criteria")
    ax.set(xlabel="Predicted hardness (GPa)",ylabel="Raw feasibility probability")
    save(fig,"05_representative_failure")
    return case


def generate(root):
    root=Path(root); run=root/"results/primary"
    m=pd.read_csv(run/"metrics.csv"); c=pd.read_csv(run/"curves.csv")
    traces=load_traces(run/"traces.jsonl")
    paired=compare(m)
    (root/"results/paired_comparisons.json").write_text(json.dumps(paired,indent=2)+"\n")
    means=m.groupby("policy").mean(numeric_only=True)
    means.to_csv(root/"results/summary.csv")
    warning_counter=Counter(w for r in traces for name in ("hardness","feasibility") for w in r["fit_diagnostics"][name]["warnings"])
    diag={"warnings":dict(warning_counter),"optimizer_failures":int(m.hardness_optimizer_failure_count.sum()),
          "feasibility_fallbacks":int(m.single_class_fallback_count.sum()),
          "calibration_failures":int(m.calibration_failure_count.sum()),
          "calibration_active_steps":sum(r["calibration_status"]=="CALIBRATION_ACTIVE" for r in traces),
          "rc_cbo_ranking_changes":int(m[m.policy=="rc_cbo"].ranking_change_count.sum()),
          "source_of_boundary_warnings":"L-BFGS-B signal variance/length scale reach conservative bounds with small training sets. Fits remain finite; these are retained, not hidden.",
          "discrimination":{}}
    for policy in LABELS:
        rows=[r for r in traces if r["policy_name"]==policy]
        y=[r["measured_feasible"] for r in rows]
        diag["discrimination"][policy]={"prequential_selected_auc_raw":float(roc_auc_score(y,[r["feasibility_probability_raw"] for r in rows])) if len(set(y))==2 else None,
            "selected_forecasts":len(rows),"feasible_selected":sum(y)}
    (root/"results/model_diagnostics.json").write_text(json.dumps(diag,indent=2)+"\n")
    case=make_figures(root,c,traces)
    manifest=json.loads((run/"benchmark_manifest.json").read_text())
    audit=json.loads((root/"results/data_audit.json").read_text())
    rows=[]
    for policy,label in LABELS.items():
        a=means.loc[policy]
        rows.append(f"| {label} | {a.auc_gpa_evaluations:.3f} | {a.best_feasible_at_5_gpa:.3f} | {a.best_feasible_at_10_gpa:.3f} | {a.best_feasible_at_15_gpa:.3f} | {a.failure_count:.2f} | {a.brier:.4f} | {a.hardness_mae_gpa:.3f} |")
    pairs=[]
    for name,metrics in paired.items():
        d=metrics["auc_gpa_evaluations"]
        pairs.append(f"- {name}: {d['mean']:.3f} GPa·evaluations; paired 95% interval [{d['lower_95']:.3f}, {d['upper_95']:.3f}].")
    sensitivity=[]
    for n in (8,16):
        p=root/f"results/sensitivity_initial_{n}/metrics.csv"
        if p.exists():
            sm=pd.read_csv(p)
            for policy,v in sm.groupby("policy"):
                sensitivity.append(f"- Initial n={n}, {policy}: mean AUC {v.auc_gpa_evaluations.mean():.3f}, failures {v.failure_count.mean():.2f} (5 exploratory seeds).")
    ood_path=root/"results/chemistry_shift.json"
    ood=json.loads(ood_path.read_text()) if ood_path.exists() else {"status":"NOT_RUN"}
    # Equality is checked directly, not inferred merely from rounded summaries.
    identical=True
    for seed in sorted(m.seed.unique()):
        a=[r["alloy_id"] for r in traces if r["seed"]==seed and r["policy_name"]=="cbo"]
        b=[r["alloy_id"] for r in traces if r["seed"]==seed and r["policy_name"]=="rc_cbo"]
        identical &= a==b
    assert identical, "Unexpected CBO/RC difference under dataset calibration gate"
    status={"research_verdict":"INCONCLUSIVE","reason":"Calibration efficacy is not identifiable: 7 positive composition groups fail predeclared support gate; RC-CBO reduces exactly to CBO.",
            "cbo_rc_traces_identical":bool(identical),"gates":{"G1":"PASSED_WITH_PROVENANCE_QUALIFICATION","G2":"PASSED","G3":"PASSED","G4":"PASSED","G5":"PASSED","G6":"PASSED","G7":"PASSED","G8":"PENDING_FINAL_REPRODUCTION_AUDIT"}}
    (root/"results/research_verdict.json").write_text(json.dumps(status,indent=2)+"\n")
    # Table uses only standard Markdown (no optional tabulate dependency).
    table="\n".join(rows)
    report=f'''# AlloyGuard-BO: retrospective experimental selection study

## Abstract

**Research verdict: INCONCLUSIVE for the calibration hypothesis.** We evaluated random selection, hardness-only BO, ordinary constrained BO and RC-CBO using 86 experimental records grouped into 82 unique compositions. Only seven groups meet the frozen ordinal ductility-rank threshold >=3. This fails the predeclared 15-per-class support gate, so the real-data calibration procedure is disabled. RC-CBO and CBO consequently produce identical decisions for every seed; this is not evidence that temperature scaling cannot help a better-supported dataset. The full comparison ran {manifest['seed_count']} matched seeds, 12 initial compositions and 15 additional selections per policy ({manifest['selections']} selections).

## Scientific motivation

A hard alloy can fail a mechanical screening requirement. Constrained expected improvement follows Gardner et al. (2014) and Gelbart et al. (2014). Calibration is motivated by Deshpande et al. (2024), but our temperature scaling is not their exact procedure and carries no conformal or online coverage guarantee. This project tests a decision policy, not Radical AI's proprietary architecture. Its public narratives motivate the question; no independently verified claim about Radical's internal performance is made. Vela et al. (2023) addresses Bayesian modeling of refractory-alloy yield strength, a distinct target.

## Dataset and provenance

Detor, Oppenheimer, Casey and Crawford (2022), Data in Brief 45, 108582. Official dataset DOI: https://doi.org/10.6084/m9.figshare.17032760.v1, article 17032760, file 31504751, `GE_RefractoryAlloyScreeningDataset_FINAL.csv`. Local size 4,706 bytes and MD5 `2a829ae75f620735b874b73fe69bf4d5` match the user-supplied official identifiers. SHA-256: `{audit['sha256']}`. The user reports CC BY 4.0; official publisher metadata and license could not be independently fetched under the environment's network restriction. This provenance qualification is retained. After the bytes matched, no further dataset download was attempted. Source and processing manifests retain this distinction.

Nine atomic-percent columns are divided by 100 without renormalization; the maximum sum error is {audit['max_composition_sum_error_at_percent']:.3g} at%, below 1e-6 at%. All measurements are present, finite, and in expected ranges. Hardness is in GPa, solidus in °C, and ductility is an ordinal 0–5 screening rank, not tensile elongation. Two composition groups have three replicates each. We use arithmetic mean hardness and minimum rank, conservatively requiring all replicates to pass; original ranks and replicate spread remain recorded. The 4/4/5 replicate group is feasible under any minimum/median rule. No duplicate groups cross policy observations and hidden pools. Grouped class counts: 7 feasible and 75 infeasible. Maximum feasible measured group hardness is 4.5442369 GPa. Solidus is computational Thermo-Calc metadata and is excluded from the primary features and constraints.

## Methods

Composition-only features; StandardScaler fitted only to each current observed training set. Hardness uses a constant-amplitude Matérn-5/2 GP, initial length 2, length bounds [0.3,6], signal variance bounds [0.1,10], deterministic L-BFGS-B with max 60 iterations and no restarts. Targets are centered/scaled on observations only, scale floor 0.5 GPa. Fixed observational SD is 0.15 GPa, an explicit modeling assumption rather than a replicate-derived universal noise law. Training noise enters `alpha`; candidate EI uses latent posterior SD. Future observation intervals and NLL add 0.15² to latent variance. These are approximate 95% Gaussian intervals, not certified coverage.

Feasibility uses Laplace Gaussian-process classification with fixed unit-amplitude Matérn-5/2 length 2 and max 100 predictive iterations. Imbalance is preserved; no oversampling or class weighting distorts probabilities. With one observed class, the model returns a Beta(1,1)-smoothed empirical prior `(positive+1)/(n+2)` and logs the fallback. Numerical failures have a separate diagnostic fallback.

Temperature scaling fits log(T) on three-fold StratifiedGroupKFold predictions generated using current observations only, regularization 0.05·log(T)², bounds T in [1/3,3], at least 20 observations and at least five of each class. Every fold refits preprocessing and GP on its training groups. The dataset-level support gate requires 15 of each class; here it disables calibration globally and logs `CALIBRATION_INSUFFICIENT_DATA` with `DATASET_CLASS_SUPPORT_GATE`. This audit-derived gate is the only full-dataset label summary given to policy configuration; no individual hidden outcomes or labels enter policy fitting, selection or calibration. It prevents an unsupported calibration comparison rather than optimizing performance.

Ordinary CBO uses EI·p_raw; RC uses EI·p_cal. These products are a conditional-factorization approximation: hardness and feasibility may remain dependent. Hardness-only BO uses EI relative to the best observed hardness. Constrained EI uses the best observed feasible hardness. Without any feasible incumbent, both constrained policies score probability plus 0.05·minimum raw-composition distance/sqrt(2); EI is zero and no undefined incumbent is used. Candidates are exhaustively scored, with stable ID-order ties. Random selection is uniform seeded; fitted forecasts are logged for evaluation but do not affect random selection.

## Frozen experimental protocol and leakage controls

For each seed 0–29, uniform initialization without outcomes chooses 12 unique groups shared across all four policies. Each policy then reveals only its own 15 selected outcomes. Immutable typed candidates contain only ID and composition; observations contain only revealed outcomes. The replay engine owns the private oracle and never passes it or a hidden dataframe to policies. This is an architectural access boundary against accidental leakage, not a security sandbox for adversarial Python code. Tests check target invariance, duplicate exclusion, grouped cross-fitting and deterministic replay.

Software tests, synthetic checks, one-seed replay and five-seed smoke were completed before freezing `configs/benchmark_frozen.yaml`. Config hash: `{manifest['config_hash']}`; source hash: `{manifest['source_hash']}`. No final-comparison results were used to alter policies. The primary score is trapezoidal area over steps 0–15 of the best observed feasible-hardness curve, including the shared initialization at step zero, and zero GPa until a feasible alloy exists. Failed-selection counts exclude initialization. Time to first feasible is zero if initialization has a feasible alloy; runs without one by budget are explicitly censored.

## Results

Means over matched replay seeds; failure counts are out of 15 additional selections.

| Policy | AUC (GPa·eval) | Best @5 (GPa) | Best @10 | Best @15 | Failures | Brier | Hardness MAE (GPa) |
|---|---:|---:|---:|---:|---:|---:|---:|
{table}

Paired AUC differences (left minus right):

{chr(10).join(pairs)}

Intervals are t intervals over randomized seed-level paired differences, conditional on this fixed finite dataset and policy configuration. Replays overlap in compositions and are not independent laboratory experiments. These intervals do not capture uncertainty across new alloy domains or prospective campaigns. Brier/log loss and hardness errors are prequential on adaptively selected observations; their evaluation populations differ across policies. They are not common test-set scores.

![Discovery](figures/01_discovery.png)

Figure 1. Mean best confirmed feasible hardness versus additional selections; shading is a conditional seed-mean 95% t interval. RC and CBO overlap exactly. Zero indicates no observed feasible alloy.

![Failures](figures/02_failures.png)

Figure 2. Cumulative rank <3 selections, excluding initialization. These are screening failures, not synthesis failures.

![Calibration](figures/03_calibration.png)

Figure 3. Selected prequential RC forecasts in five fixed-width bins. Raw and calibrated probabilities coincide because calibration is gated off. Repeated alloys/seeds and sparse positives make this descriptive; a reliability curve does not establish out-of-distribution reliability.

![Predictive validation](figures/04_predictive_validation.png)

Figure 4. Pre-reveal hardness forecasts versus grouped measured hardness and residuals standardized by future-observation SD. The histogram displays residuals within ±8; NLL/coverage metrics include all records. Intervals are model assumptions, not calibrated mechanical guarantees.

![Failure example](figures/05_representative_failure.png)

Figure 5. Actual hardness-only selections; orange points fail rank >=3, blue pass. A highlighted case, if present, meets descriptive criteria predicted hardness >=8 GPa and feasibility <0.35 and was nevertheless selected by hardness-only EI. This example was selected after evaluation to illustrate a failure, never to tune the policy.

## Ablations, sensitivity and chemistry shift

Feasibility's contribution is the CBO-minus-hardness comparison above. The calibration ablation has exactly zero effect: all 450 CBO/RC query pairs match, there are zero calibration activations, and zero ranking changes. A monotone temperature transform could change the ranking of EI·p despite preserving discrimination; that mechanism is not exercised by these data.

{chr(10).join(sensitivity) if sensitivity else 'Sensitivity results are not yet generated.'}

Sensitivity runs are explicitly exploratory and use separately recorded configurations/seeds with equal budgets at each initial size; raw AUC across initial sizes is not a matched-budget causal comparison because initialization also consumes laboratory measurements. They do not select a winning initialization.

Chemistry-shift status: **{ood['status']}**. Three KMeans groups are defined using only unscaled composition fractions with seed 0, n_init=10. The predeclared meaningful-support requirement is at least four feasible groups in training and four in the held-out family, plus 15 target groups. Only seven feasible groups exist globally, so no split supports both requirements. Composition cluster counts are recorded, but no OOD calibration result is manufactured.

## Failure analysis and diagnostics

Real-data calibration cannot be estimated with the required support. The feasibility classifier starts with a single class in some replays; smoothed-prior fallback counts: {diag['feasibility_fallbacks']}. Hardness optimizer non-successes: {diag['optimizer_failures']}; logged warning messages: {sum(warning_counter.values())}. Bound warnings mean small-sample fits favor a bound; finite prediction and acquisition checks remain enforced. Exact warning text and frequencies are in `model_diagnostics.json`, with every per-step fit retained in JSONL. Fits/warnings were not discarded to improve metrics. No failed fit is silently described as an ordinary fit.

Distance diagnostics label raw-composition nearest-neighbor distance >0.35 as distant from observations. This is a heuristic support diagnostic, not a validated extrapolation test. Predictive miscalibration and adaptive selection can produce poor EI decisions even when numerics are correct. A policy can successfully identify the very few feasible alloys yet be unsuitable for predicting arbitrary ductile compositions.

## Reproducibility

Python {manifest['python']} on Linux; CPU numerical threads are fixed to one. Exact installed versions are in `requirements.lock` (hash `{manifest['lock_sha256']}`). From repository root, follow README's commands for local data validation, audit, tests, synthetic checks, smoke, freeze, primary replay and reporting. `scripts/reproduce.sh` writes regenerated runs under a new directory and verifies frozen methodology/data hashes rather than overwriting original results. Source, processed dataset, configuration and output hashes are in `results/primary/benchmark_manifest.json`. Timing fields vary across executions; deterministic selections/outcome metrics are verified separately. Full run wall time: {manifest['elapsed_seconds']:.1f} seconds; fitting overhead is recorded per policy/seed.

## Limitations

The dataset is small and has only seven positive composition groups at the fixed threshold. Selection is among previously measured alloys; no new compositions or physical experiments were generated. Repeated seed replays are correlated through a shared finite pool. There is no prospective laboratory validation or paired simulated/laboratory hardness dataset. Ordinal ductility screening imperfectly represents mechanical reliability, and successfully synthesized/characterized materials do not represent all failed synthesis attempts. Aggregate replicate handling and assumed noise simplify the measurement process. Official license/provenance metadata were user-supplied rather than independently retrieved, though file integrity matches exactly. External references are attributed, but full article contents were not freshly consulted because network restrictions persist. No superiority over Radical AI's internal system, novel theoretical guarantee, or state-of-the-art result is claimed.

## Conclusion and next research step

This implementation produces a real-data, matched finite-pool decision comparison. It cannot establish the proposed calibration benefit: the scientifically justified support gate forces RC-CBO to ordinary CBO, with zero paired difference. The next step is a larger, composition-diverse set of experimental screening outcomes with substantially more feasible cases, collected with an outcome-blind prospective protocol. A true simulation-to-laboratory discrepancy extension additionally needs paired computational and laboratory hardness with process/microstructure metadata; solidus is not a substitute for that pairing.
'''
    (root/"results/REPORT.md").write_text(report)
    return status
