import numpy as np
from scipy.special import xlogy
from scipy.stats import t

def probability_scores(y,p):
    y=np.asarray(y,float); p=np.clip(np.asarray(p,float),1e-7,1-1e-7)
    return float(np.mean((p-y)**2)),float(-np.mean(xlogy(y,p)+xlogy(1-y,1-p)))

def paired_interval(values):
    values=np.asarray(values,float)
    mean=float(values.mean())
    half=float(t.ppf(.975,len(values)-1)*values.std(ddof=1)/np.sqrt(len(values))) if len(values)>1 else float("nan")
    return {"mean":mean,"lower_95":mean-half,"upper_95":mean+half,"n_seeds":len(values)}

def summarize_run(traces,curves,seed,policy):
    y=np.array([r["measured_feasible"] for r in traces],int)
    raw=np.array([r["feasibility_probability_raw"] for r in traces])
    cal=np.array([r["feasibility_probability_calibrated"] for r in traces])
    brier,loss=probability_scores(y,cal); brier_raw,loss_raw=probability_scores(y,raw)
    residual=np.array([r["hardness_mean_gpa"]-r["measured_hardness_gpa"] for r in traces])
    noisy=np.array([r["hardness_observation_std_gpa"] for r in traces])
    first=next((r["selection_step"] for r in curves if r["has_feasible"]),None)
    values=np.array([r["best_feasible_hardness_gpa"] for r in curves])
    result={"seed":seed,"policy":policy,"auc_gpa_evaluations":float(np.trapezoid(values)),
            "failure_count":int((1-y).sum()),"failure_rate":float((1-y).mean()),
            "time_to_first_feasible":first,"first_feasible_censored":first is None,
            "brier":brier,"log_loss":loss,"brier_raw":brier_raw,"log_loss_raw":loss_raw,
            "hardness_mae_gpa":float(abs(residual).mean()),
            "hardness_nll":float(np.mean(.5*np.log(2*np.pi*noisy**2)+.5*(residual/noisy)**2)),
            "hardness_interval_coverage":float(np.mean(abs(residual)<=1.96*noisy)),
            "calibration_active_fraction":float(np.mean([r["calibration_status"]=="CALIBRATION_ACTIVE" for r in traces])),
            "ranking_change_count":sum(r["raw_acquisition_winner"]!=r["calibrated_acquisition_winner"] for r in traces),
            "fit_seconds":sum(r["fit_diagnostics"]["fit_seconds"] for r in traces),
            "single_class_fallback_count":sum(r["fit_diagnostics"]["feasibility"]["status"]!="FIT" for r in traces),
            "fit_warning_count":sum(len(r["fit_diagnostics"]["hardness"]["warnings"])+len(r["fit_diagnostics"]["feasibility"]["warnings"]) for r in traces),
            "hardness_optimizer_failure_count":sum(not e["success"] for r in traces for e in r["fit_diagnostics"]["hardness"]["optimizer"]),
            "calibration_failure_count":sum(r["calibration_status"]=="CALIBRATION_FIT_FAILED" for r in traces)}
    for budget in (5,10,15):
        if budget<len(curves):
            result[f"best_feasible_at_{budget}_gpa"]=curves[budget]["best_feasible_hardness_gpa"]
            result[f"found_feasible_by_{budget}"]=curves[budget]["has_feasible"]
    return result
