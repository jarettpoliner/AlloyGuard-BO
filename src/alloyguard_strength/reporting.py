"""Trace-derived figures, with unavoidable labels for non-scientific run modes."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render(run_directory:Path):
    run_directory=Path(run_directory)
    manifest=json.loads((run_directory/"manifest.json").read_text())
    if manifest["mode"]=="FINAL_SCIENTIFIC" and not manifest["scientific_conclusions_allowed"]:
        raise ValueError("Unqualified final-run claim")
    label={"FINAL_SCIENTIFIC":"Source-qualified primary replay",
           "PROVISIONAL_SOFTWARE_VALIDATION":"PROVISIONAL SOFTWARE CHECK — unverified test conditions",
           "SYNTHETIC_CORRECTNESS":"SYNTHETIC CORRECTNESS — no experimental evidence"}[manifest["mode"]]
    curves=pd.read_csv(run_directory/"curves.csv")
    traces=pd.DataFrame([json.loads(line) for line in (run_directory/"traces.jsonl").read_text().splitlines()])
    out=run_directory/"figures";out.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False})
    def save(fig,name):
        fig.suptitle(label,fontsize=9);fig.tight_layout();fig.savefig(out/f"{name}.png",dpi=180);fig.savefig(out/f"{name}.pdf");plt.close(fig)
    for column,name,ylabel in (("best_feasible_strength_mpa","01_discovery","Best observed feasible yield strength (MPa)"),
                                ("cumulative_failures","02_constraint_failures","Reported elongation <10% selections")):
        fig,ax=plt.subplots(figsize=(7,4))
        for policy,part in curves.groupby("policy"):
            mean=part.groupby("step")[column].mean()
            ax.plot(mean.index,mean.values,label=policy,linestyle="--" if policy=="rc_cbo" else "-")
        ax.set(xlabel="Additional selections",ylabel=ylabel);ax.legend(fontsize=8);save(fig,name)
    fig,ax=plt.subplots(figsize=(6,4))
    rows=traces[traces.policy_name=="rc_cbo"]
    for column,title in (("feasibility_probability_raw","Raw"),("feasibility_probability_calibrated","Calibrated when supported")):
        p=rows[column].to_numpy();y=rows.feasible.to_numpy(float);bins=np.minimum((p*5).astype(int),4)
        x=[];z=[]
        for i in range(5):
            mask=bins==i
            if mask.any():x.append(p[mask].mean());z.append(y[mask].mean())
        ax.plot(x,z,"o-",label=title)
    ax.plot([0,1],[0,1],"k--",alpha=.4);ax.set(xlabel="Mean pre-reveal probability",ylabel="Reported feasible fraction",xlim=(0,1),ylim=(0,1));ax.legend(fontsize=8)
    save(fig,"03_probability_diagnostics")
    fig,ax=plt.subplots(figsize=(6,4))
    for policy,part in traces.groupby("policy_name"):
        ax.scatter(part.measured_strength_mpa,part.strength_mean_mpa,s=15,alpha=.4,label=policy)
    low=float(traces.measured_strength_mpa.min());high=float(traces.measured_strength_mpa.max())
    ax.plot([low,high],[low,high],"k--",alpha=.4);ax.set(xlabel="Reported strength (MPa)",ylabel="Pre-reveal predicted strength (MPa)");ax.legend(fontsize=8)
    save(fig,"04_strength_forecasts")
    fig,ax=plt.subplots(figsize=(6,4))
    ax.scatter(traces.strength_mean_mpa,traces.feasibility_probability_raw,
               c=["#0072b2" if y else "#d55e00" for y in traces.feasible],alpha=.5,s=18)
    ax.set(xlabel="Predicted strength (MPa)",ylabel="Raw feasibility probability")
    save(fig,"05_selection_risk")
    return {"mode":manifest["mode"],"scientific_conclusions_allowed":manifest["scientific_conclusions_allowed"],
            "figure_count":5,"label":label}
