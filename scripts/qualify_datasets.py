"""Scientific qualification of supplied workbooks; no model or optimization is run."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from workbook_reader import read_workbook

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/additional/raw"
OUT=ROOT/"results/dataset_qualification"
NOTE="Note on any unqiue processing or data features"
COMMIT="be942502d094d5a360595166e25a53cc24d5cf88"


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_pairs(frame,yield_column,elongation_column):
    y=pd.to_numeric(frame[yield_column],errors="coerce")
    e=pd.to_numeric(frame[elongation_column],errors="coerce")
    paired=np.isfinite(y)&np.isfinite(e)
    physically_valid=paired&(y>0)&(e>=0)&(e<=100)
    return y,e,paired,physically_valid


def normalize_study(value):
    # Exact DOI extraction from raw citation text; no title/name-based identity inference.
    match=re.search(r"10\.\d{4,9}/[^\s<>\"]+",str(value),flags=re.I)
    return match.group(0).rstrip(".,;").lower() if match else None


def normalize_text(value):
    return re.sub(r"\s+"," ",str(value).strip()) if pd.notna(value) else ""


def connected_components(studies,chemistries):
    # Strong conservative grouping, using no property labels. Same study OR rounded
    # chemical vector is connected; this is an audit proxy, not proof of independence.
    parent=list(range(len(studies)))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    seen={}
    for i,(study,chemistry) in enumerate(zip(studies,chemistries)):
        for key in (("study",study),("chemistry",chemistry)):
            if key in seen: union(i,seen[key])
            else: seen[key]=i
    groups={}
    for i in range(len(studies)): groups.setdefault(find(i),[]).append(i)
    return sorted(groups.values(),key=len,reverse=True)


def manifest(path,inspection,remote_path):
    data=path.read_bytes()
    blob=hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
    expected={"MPEA_parsed_mechanical_database.xlsx":"8dfa71562a028c9a8dfab9ca47e4079dcef65adf", "Steel database with labelled clusters.xlsx":"9d9b021a934620fbfc6132964c39a58b1c1b91c6"}[path.name]
    if blob!=expected: raise ValueError("Workbook differs from identified user-uploaded Git blob")
    return {"filename":path.name,"repository_blob_sha1":blob,"size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
            "local_md5":hashlib.md5(data).hexdigest(),"acquisition":"User-uploaded repository blob recovered without resetting existing checkout",
            "repository_commit":COMMIT,"repository_path":remote_path,
            "source_publication":None,"official_dataset_record":None,"source_version":None,
            "source_license":None,"source_provided_checksum":None,
            "verification_status":"LOCAL_GIT_BLOB_INTEGRITY_ONLY_NOT_OFFICIAL_SOURCE_AUTHENTICATION",
            "metadata_note":"Workbook cell-level study citations do not establish dataset-level provenance, source version, or redistribution license. Repository MIT code license is not assumed to cover uploaded datasets.",
            "workbook_inspection":inspection}


def mpea_audit(path):
    frames,inspection=read_workbook(path);f=next(iter(frames.values()))
    y,e,paired,valid=numeric_pairs(f,"Yield Strength (MPa)","Elongation (%)")
    p=f.loc[valid].copy().reset_index(drop=True)
    p[["__excel_row","Composition","Yield Strength (MPa)","Elongation (%)",NOTE,"Source"]].to_csv(OUT/"mpea_paired_raw_inspection.csv",index=False)
    elements=list(f.columns)[list(f.columns).index("Ag"):]
    comp=f[elements].apply(pd.to_numeric,errors="coerce")
    pc=p[elements].apply(pd.to_numeric,errors="coerce")
    sums=comp.sum(axis=1,min_count=len(elements));ps=pc.sum(axis=1,min_count=len(elements))
    notes=p[NOTE].map(normalize_text)
    sources=p.Source.map(normalize_study)
    chem=[tuple(float(v) for v in row) for row in pc.to_numpy()]
    all_notes=f[NOTE].fillna("").astype(str)
    all_simulated=all_notes.str.contains(r"\bFEM\b|simulat",case=False,regex=True)
    full_duplicate_fields=[c for c in f.columns if c not in ("__excel_row","__blank_1")]
    clean_fields=[c for c in p.columns if c not in ("__excel_row","__blank_1")]
    ambiguous=p.copy()
    ambiguous["__study_id"]=sources
    ambiguous["__processing_proxy"]=notes
    key=["Composition","__processing_proxy","__study_id"]
    ambiguous_rows=ambiguous[ambiguous.duplicated(key,keep=False)]
    components=connected_components(sources.tolist(),chem)
    outcomes=(pd.to_numeric(p["Elongation (%)"])>=10).to_numpy()
    component_summary=[{"component":i,"rows":len(indices),"feasible":int(outcomes[indices].sum()),
                        "infeasible":int((~outcomes[indices]).sum()),
                        "studies":len(set(sources.iloc[indices]))} for i,indices in enumerate(components)]
    source_summary=[]
    for study,indices in sources.groupby(sources).groups.items():
        subset=p.loc[indices]
        source_summary.append({"normalized_study_doi":study,"raw_citation_examples":json.dumps(subset.Source.unique().tolist()),
                               "paired_numeric_records":len(subset),"feasible_count":int((pd.to_numeric(subset["Elongation (%)"])>=10).sum()),
                               "infeasible_count":int((pd.to_numeric(subset["Elongation (%)"])<10).sum()),
                               "excel_rows":json.dumps(subset.__excel_row.astype(int).tolist()),
                               "test_mode_verified":False,"test_temperature_c":None,"same_test_case_pairing_verified":False,
                               "source_review_status":"PENDING_PRIMARY_PUBLICATION_REVIEW"})
    pd.DataFrame(source_summary).to_csv(OUT/"mpea_study_review_queue.csv",index=False)
    ambiguous_rows.to_csv(OUT/"mpea_ambiguous_repeat_candidates.csv",index=False)
    flags=[]
    for i,row in p.iterrows():
        note=notes.iloc[i]
        flags.append({"excel_row":int(row["__excel_row"]),"study_doi":sources.iloc[i],
                      "composition_raw":row.Composition,"processing_notes_raw":note,
                      "yield_strength_mpa":float(row["Yield Strength (MPa)"]),"elongation_percent":float(row["Elongation (%)"]),
                      "feasible_provisional":bool(outcomes[i]),"composition_sum":float(ps.iloc[i]),
                      "test_mode_status":"UNVERIFIED", "test_temperature_status":"UNRECORDED",
                      "experimental_pairing_status":"UNVERIFIED",
                      "same_row_compressive_strength_also_reported":pd.notna(pd.to_numeric(row["Compressive strength (MPa)"],errors="coerce")),
                      "note_mentions_simulation":bool(re.search(r"\bFEM\b|simulat",note,flags=re.I)),
                      "eligible_for_frozen_primary":False})
    pd.DataFrame(flags).to_csv(OUT/"mpea_record_qualification.csv",index=False)
    entry=manifest(path,inspection,"A database of mechanical properties for multi prin/"+path.name)
    report={"status":"PROVISIONAL_CANDIDATE_NOT_QUALIFIED","raw_records":len(f),
            "numeric_paired_records":int(paired.sum()),"numeric_physically_valid_paired_records":int(valid.sum()),
            "provisional_feasible_records":int(outcomes.sum()),"provisional_infeasible_records":int((~outcomes).sum()),
            "missing_values_by_column":f.isna().sum().to_dict(),"columns":list(f.columns),"element_columns":elements,
            "yield_strength_paired_range_mpa":[float(y[valid].min()),float(y[valid].max())],
            "elongation_paired_range_percent":[float(e[valid].min()),float(e[valid].max())],
            "exact_duplicate_rows_excluding_record_id_all":int(f.duplicated(full_duplicate_fields).sum()),
            "exact_duplicate_rows_excluding_record_id_paired":int(p.duplicated(clean_fields).sum()),
            "unique_composition_strings_paired":int(p.Composition.nunique()),
            "unique_rounded_numeric_compositions_paired":len(set(chem)),
            "unique_composition_processing_study_proxies":int(ambiguous.groupby(key,dropna=False).ngroups),
            "ambiguous_same_case_proxy_records":len(ambiguous_rows),
            "independent_case_count":None,"independent_feasible_class_counts":None,
            "composition_fraction_status":"Numerical columns are fraction-like and rounded to ~3 decimals; atomic versus mass basis not independently documented. No normalization or unit reinterpretation performed.",
            "composition_sum_all_range":[float(sums.min()),float(sums.max())],
            "composition_sum_paired_range":[float(ps.min()),float(ps.max())],
            "paired_missing_composition_records":int(pc.isna().any(axis=1).sum()),
            "paired_negative_composition_records":int((pc<0).any(axis=1).sum()),
            "all_records_composition_sum_deviation_gt_0_02":int((abs(sums-1)>.02).sum()),
            "paired_records_composition_sum_deviation_gt_0_005":int((abs(ps-1)>.005).sum()),
            "simulation_marked_records_whole_workbook":int(all_simulated.sum()),
            "simulation_marked_records_numeric_pair_subset":sum(r["note_mentions_simulation"] for r in flags),
            "paired_records_also_reporting_compressive_strength":sum(r["same_row_compressive_strength_also_reported"] for r in flags),
            "paired_records_also_reporting_ultimate_tensile_strength":int(pd.to_numeric(p["Ultimate Tensile Strength (MPa)"],errors="coerce").notna().sum()),
            "blank_processing_notes_paired":int((notes=="").sum()),
            "raw_citation_count_paired":int(p.Source.nunique()),"normalized_study_doi_count_paired":int(sources.nunique()),
            "unparseable_study_citations_paired":int(sources.isna().sum()),
            "explicitly_verified_tensile_room_temperature_pairs":0,
            "verified_test_temperature_column_present":False,
            "study_and_rounded_composition_components":component_summary,
            "component_caution":"Transitive study OR rounded chemistry overlap is conservative; rounded fractions can alias real compositions and generic processing notes do not prove independent experiments. Not a final split or independence count.",
            "feature_exclusions":["Phases present","FCC","BCC","HCP","IM","Hardness (HVN)","Ultimate Tensile Strength (MPa)","Compressive strength (MPa)","Plasticity (%) - Compressive","Source"],
            "blockers":["Dataset publication/official record/version/license not supplied or embedded", "No explicit test temperature field; processing temperatures cannot be treated as test temperatures", "Paired tensile loading and yield/elongation test-case correspondence need primary-source confirmation", "At least one composition-processing-study proxy has conflicting measurements and unknown replicate/condition identity", "Composition fraction basis and source rounding require documentation"],
            "no_new_models_or_benchmarks_run":True}
    return entry,report


def steel_audit(path):
    frames,inspection=read_workbook(path);f=next(iter(frames.values()))
    y,e,paired,valid=numeric_pairs(f,"Yield strength (MPa)","Ductility (%)")
    meaningful=[c for c in f if c not in ("__excel_row","Entry") and not c.startswith("__blank")]
    d=f.loc[valid].drop_duplicates(meaningful)
    # Also inspect duplicates without potentially outcome-derived cluster labels.
    without_clusters=[c for c in meaningful if c not in ("Cluster Number (0 to 11)","Cluster Number","Cluster label")]
    dedup=f.loc[valid].drop_duplicates(without_clusters)
    elements=list(f.columns)[list(f.columns).index("Al"):list(f.columns).index("__blank_25")]
    chemistry=f[elements].apply(pd.to_numeric,errors="coerce")
    condition_key=["Name","Processing condition"]
    conflicts=f.loc[valid].groupby(condition_key,dropna=False).agg(yield_values=("Yield strength (MPa)","nunique"),elongation_values=("Ductility (%)","nunique"))
    pd.DataFrame({"name":f.Name,"processing":f["Processing condition"],"excel_row":f.__excel_row}).to_csv(OUT/"steel_case_identifiers.csv",index=False)
    report={"status":"NOT_QUALIFIED_SECONDARY_CANDIDATE", "raw_records":len(f),"columns":list(f.columns),
            "numeric_paired_records":int(paired.sum()),"numeric_physically_valid_paired_records":int(valid.sum()),
            "provisional_feasible_records":int((e[valid]>=10).sum()),"provisional_infeasible_records":int((e[valid]<10).sum()),
            "exact_duplicate_records_excluding_record_id":int(f.duplicated(meaningful).sum()),
            "exact_deduplicated_records":len(d),"exact_deduplicated_infeasible_records":int((pd.to_numeric(d["Ductility (%)"])<10).sum()),
            "deduplicated_records_ignoring_cluster_labels":len(dedup),
            "deduplicated_infeasible_ignoring_cluster_labels":int((pd.to_numeric(dedup["Ductility (%)"])<10).sum()),
            "unique_numeric_compositions":len(chemistry.drop_duplicates()),
            "name_processing_proxy_cases":int(f.groupby(condition_key,dropna=False).ngroups),
            "name_processing_proxy_cases_with_conflicting_properties":int(((conflicts.yield_values>1)|(conflicts.elongation_values>1)).sum()),
            "missing_values_by_column":f.isna().sum().to_dict(),"element_columns":elements,
            "composition_sum_range":[float(chemistry.sum(axis=1).min()),float(chemistry.sum(axis=1).max())],
            "composition_basis":"Values are percentage-like; mass-vs-atomic basis unverified, do not convert as atomic fractions", 
            "yield_strength_range_mpa":[float(y[valid].min()),float(y[valid].max())],
            "ductility_range_percent":[float(e[valid].min()),float(e[valid].max())],
            "study_identifier_available":False,"test_temperature_column_available":False,
            "independent_case_count":None,"independent_feasible_class_counts":None,
            "cluster_feature_status":"Exclude all provided cluster labels/numbers unless their inputs and outcome-blind construction are documented",
            "blockers":["No official dataset publication/version/license or study mapping in workbook", "Ductility is not explicitly established as comparable tensile elongation at common temperature", "Large exact duplication and possible additional condition-level repetitions", "Very small minority class after exact deduplication; larger total size is not adequate justification", "Cluster labels may encode outcome information and are not qualified predictors"]}
    return manifest(path,inspection,"A database of mechanical properties of steels/"+path.name),report


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    config=ROOT/"configs/dataset_qualification_v2.yaml"
    ma,m=mpea_audit(RAW/"MPEA_parsed_mechanical_database.xlsx")
    sa,s=steel_audit(RAW/"Steel database with labelled clusters.xlsx")
    for name,value in (("mpea_manifest",ma),("mpea_audit",m),("steel_manifest",sa),("steel_audit",s)):
        (OUT/f"{name}.json").write_text(json.dumps(value,indent=2)+"\n")
    ge_manifest=json.loads((ROOT/"data/source_manifest.json").read_text())
    ge_audit=json.loads((ROOT/"results/data_audit.json").read_text())
    decision={"revision":"qualification_v2", "status":"BLOCKED_G1_SOURCE_AND_MEASUREMENT_COMPARABILITY",
              "assessment_config_sha256":hash_file(config),"selected_primary":None,
              "preferred_candidate_pending_qualification":"MPEA_parsed_mechanical_database.xlsx",
              "decision_basis":"Prespecified provenance/measurement hard gates before class-support/size criteria. No optimization results used.",
              "rationale":"MPEA has the strongest provisional paired class support and study citations. It cannot yet be declared a tensile room-temperature strength/elongation benchmark. Steel has substantial exact duplication, extreme imbalance and no study IDs; GE uses a different objective/ordinal constraint and remains a separately documented completed benchmark. Citrine input is absent.",
              "ge_preserved":{"sha256":ge_manifest["sha256"],"groups":ge_audit["unique_compositions"],"feasible":ge_audit["feasible_count"],"target":"hardness GPa, ordinal screening rank >=3; not merged with MPa/elongation data"},
              "citrine_status":"NOT_PRESENT_IN_WORKSPACE_OR_SELECTED_REMOTE_TREE",
              "new_gate_status":{"G1":"BLOCKED","G2":"NOT_STARTED","G3":"NOT_STARTED","G4":"NOT_STARTED","G5":"NOT_STARTED","G6":"NOT_STARTED","G7":"NOT_STARTED","G8":"NOT_STARTED"},
              "minimum_next_action":"Supply official source DOI/URL + license/version for MPEA, and data dictionary or primary-publication annotations verifying composition basis, experimental tensile yield/elongation pairing, test temperature and independent processing/test cases. Allow official metadata/publication access if primary sources need retrieval.",
              "primary_scientific_question":"Can calibrated constrained BO improve discovery of high measured tensile yield strength with measured tensile elongation >=10%? Remains provisional until G1.",
              "optimization_performance_used_for_dataset_selection":False,
              "existing_ge_frozen_protocol_modified":False}
    (OUT/"primary_dataset_decision.json").write_text(json.dumps(decision,indent=2)+"\n")
    source_rows=pd.read_csv(OUT/"mpea_study_review_queue.csv")
    report=f'''# Scientific dataset qualification — new strength/elongation study

**Status: G1 blocked; no new primary dataset frozen and no new models implemented.**

The strongest *provisional* candidate is the newer MPEA workbook, based on class support and available study citations, not BO performance. Neither new workbook clears the prespecified provenance and measurement-compatibility hard gates. Existing GE methods/results are preserved unchanged. This report does not claim that all unverified records are invalid; it records what is and is not established.

## Comparison before optimization

| Source | Raw records | Numeric paired targets | Provisional >=10% / <10% | Exact deduplicated paired | Study mapping | Qualification |
|---|---:|---:|---:|---:|---|---|
| MPEA | {m['raw_records']} | {m['numeric_paired_records']} | {m['provisional_feasible_records']} / {m['provisional_infeasible_records']} | {m['numeric_paired_records']-m['exact_duplicate_rows_excluding_record_id_paired']} | {m['normalized_study_doi_count_paired']} parsed citation IDs | Preferred candidate; G1 unresolved |
| Steel | {s['raw_records']} | {s['numeric_paired_records']} | {s['provisional_feasible_records']} / {s['provisional_infeasible_records']} | {s['exact_deduplicated_records']} (only {s['exact_deduplicated_infeasible_records']} <10%) | Absent | Weaker candidate; G1 unresolved |
| GE | 86 | Different target/constraint | 7 feasible /75 infeasible groups | 82 groups | Original single-source benchmark | Retain independently; no MPa conversion |
| Citrine | — | — | — | — | — | Not present; no automatic selection |

The user's preliminary MPEA 1,713/457/341/116 and steel 3,234/53 counts are confirmed for raw numeric records. These are **not independent eligible-case counts**. Steel has {s['exact_duplicate_records_excluding_record_id']} exact duplicates after record-ID removal; only {s['exact_deduplicated_infeasible_records']} distinct full records fall below 10% after that deduplication. MPEA has no exact duplicate full paired record, but one duplicated composition–processing-note–study proxy with conflicting measured outcomes, and chemical/processing aliases remain unresolved.

## Integrity and provenance

Files recovered unchanged from user repository commit `{COMMIT}` into `data/additional/raw/`; original names retained. Each archive parsed successfully without executing formulas/macros/scripts. Local SHA-256 and MD5 are recorded, but no source-provided checksum is available for independent official-record verification.

- MPEA SHA-256: `{ma['sha256']}` ({ma['size_bytes']} bytes).
- Steel SHA-256: `{sa['sha256']}` ({sa['size_bytes']} bytes).

Neither workbook embeds a dataset-level license, official dataset record, publication citation or source version. Row-level study DOIs are not a dataset license. The existing repository MIT software license is not assumed to license third-party experimental data. No raw workbook is committed/pushed or merged with GE. Crossref metadata lookup received proxy CONNECT HTTP 403; current runtime policy has no applied custom domains. No token is needed for public source metadata. Repository byte identity is verified; official publication/version/license remain unresolved.

## MPEA scientific audit

All 457 numeric paired rows have positive finite yield strength and elongation within [0,100]%; ranges {m['yield_strength_paired_range_mpa']} MPa and {m['elongation_paired_range_percent']}%. Zero elongation is retained, not silently discarded. There are {m['unique_composition_strings_paired']} distinct composition strings and {m['unique_rounded_numeric_compositions_paired']} distinct rounded numeric chemical vectors; these are not interchangeable independent-case counts.

Numeric compositions are fraction-like and rounded to approximately three decimals. Paired sums span {m['composition_sum_paired_range']}; none have missing or negative element values. The full workbook contains sums down to {m['composition_sum_all_range'][0]}, so it must not be silently normalized globally. Atomic versus mass basis and source rounding remain unverified. No composition repairs, outcome imputation or threshold changes were applied.

Paired sources yield {m['normalized_study_doi_count_paired']} normalized DOI citation groups. One source can itself be an earlier aggregation, so these are citation groups rather than proven independent original studies. A study review queue retains each citation and Excel row IDs. Study/chemical-overlap connected-component counts are provided as conservative leakage diagnostics; no random row split is proposed as independent validation.

{m['blank_processing_notes_paired']} paired records have blank processing notes; many others have generic CAST/WROUGHT/OTHER labels. Processing notes, annealing/sintering temperatures and rates are not automatically test conditions. There is no test-temperature column and no explicit verified tensile/room-temperature case map. {m['paired_records_also_reporting_ultimate_tensile_strength']} paired rows also report UTS and {m['paired_records_also_reporting_compressive_strength']} also report compressive strength. This is supporting context, not proof that paired yield and elongation came from the same tensile test.

The entire workbook has {m['simulation_marked_records_whole_workbook']} simulation-marked records; **none of the 457 paired numeric rows is explicitly simulation-marked in its notes**. Absence of a note is not affirmative experimental provenance. All paired cases remain unverified pending source review. Do not infer that all paired records are simulations or exclude all rows based on unrelated workbook entries.

The duplicated case proxy `AlCoCrFeNi2.1`, note `50μm/s`, DOI `10.1016/j.jallcom.2021.162907`, reports (423 MPa, 23.7%) and (431 MPa, 13%). These may be replicates or distinct unrecorded test conditions; they must not be treated as independently identified experiments or blindly averaged. Both are retained for source review.

## Feature and leakage controls required before modeling

Exclude measured phases and FCC/BCC/HCP/IM indicators, measured hardness/UTS/compressive strength/plasticity, target properties and source identifiers from predictors. Retain source identifiers only for provenance/grouping. Planned processing variables can be features only after their pre-experiment availability and semantics are verified. Unverified steel cluster labels/numbers may encode properties; they are excluded. No outcome-derived descriptors are proposed.

The desired independent case is canonical composition + planned processing + verified loading/temperature/test conditions. Group repeated cases together. Require study-disjoint evaluation, and prevent same composition–processing duplicates crossing train/test boundaries. Effective independent class counts cannot yet be established. The 10% elongation requirement remains provisional and unchanged; class balance alone does not validate this physical endpoint.

## Decision and next action

**No scientifically qualified primary selected yet.** Prefer MPEA conditionally, reject automatic Citrine selection, and keep steel optional pending its own provenance/condition audit. The provisional study maximizes experimentally measured **tensile yield strength (MPa)** with **tensile elongation >=10%**, restricted initially to documented room-temperature (20–30 °C) measurements. Unknown test temperatures are unresolved, not assumed room temperature. If source documentation supports another well-defined stratum, it must be separately declared before modeling.

To complete new G1, supply official dataset/publication URL or DOI and license/version, plus data dictionary or primary-source annotations establishing composition units, tensile pairing, temperature and processing/case identity. `mpea_study_review_queue.csv` lists the source-review work needed. After qualification, create a separately labeled strength study with group-aware calibration/shift tests; preserve all original GE modules/config/source hashes/results. New G2–G8 have not started, and no new benchmark results or superiority claims are fabricated.

The existing GE 43-test benchmark remains a completed independent study, with its previously reported calibration-support and source-metadata qualifications. Its results are not evidence for the proposed yield-strength/elongation study.
'''
    (OUT/"REPORT.md").write_text(report)
    (OUT/"artifact_manifest.json").write_text(json.dumps({"assessment_config_sha256":hash_file(config),
       "artifacts":{p.name:hash_file(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!="artifact_manifest.json"}},indent=2)+"\n")
    print({"status":decision["status"],"mpea_pairs":m["numeric_paired_records"],"steel_exact_unique":s["exact_deduplicated_records"],"preferred_candidate":decision["preferred_candidate_pending_qualification"],"new_primary_selected":False})

if __name__=="__main__": main()
