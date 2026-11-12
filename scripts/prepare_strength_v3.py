"""G1a provenance, prioritized G1b review, and explicitly provisional software inputs.

No source-verification assertion is inferred from a filename or missing metadata.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
import numpy as np
import pandas as pd
from workbook_reader import read_workbook
from qualify_datasets import numeric_pairs,normalize_study,normalize_text,connected_components,NOTE

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"results/strength_v3"
ELEMENTS=None
ANNOTATION_COLUMNS=["excel_row","study_doi","evidence_url","evidence_locator","evidence_excerpt","reviewer",
                    "loading_mode","test_temperature_c","composition_basis","processing_state_id",
                    "same_material_state","experimental","resolution_note"]


def verified_annotation(row,source):
    required=["evidence_url","evidence_locator","evidence_excerpt","reviewer","processing_state_id"]
    if any(pd.isna(row.get(k)) or not str(row.get(k)).strip() for k in required):return False,"INCOMPLETE_SOURCE_EVIDENCE"
    if normalize_study(row.get("study_doi"))!=source:return False,"CITATION_MISMATCH"
    if str(row.get("loading_mode")).lower()!="tensile":return False,"NOT_VERIFIED_TENSILE"
    temp=pd.to_numeric(row.get("test_temperature_c"),errors="coerce")
    if not np.isfinite(temp) or not 20<=temp<=30:return False,"NOT_VERIFIED_20_TO_30_C"
    if row.get("composition_basis") not in ("atomic_fraction","atomic_ratio"):return False,"UNVERIFIED_COMPOSITION_BASIS"
    if any(str(row.get(k)).strip().lower() not in ("true","1","yes") for k in ("same_material_state","experimental")):
        return False,"UNVERIFIED_EXPERIMENTAL_SAME_STATE_PAIR"
    return True,"PRIMARY_SOURCE_ANNOTATION_ACCEPTED"


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    path=ROOT/"data/additional/raw/MPEA_parsed_mechanical_database.xlsx"
    raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    old=json.loads((ROOT/"results/dataset_qualification/mpea_manifest.json").read_text())
    if digest!=old["sha256"]:raise ValueError("MPEA upload changed from audited original")
    provenance={"G1a":"COMPLETE_USER_VERIFIED_PROVENANCE_AND_LOCAL_INTEGRITY",
        "title":"A database of mechanical properties for multi principal element alloys",
        "authors":["Zhipeng Li","Zhuoran Zeng","Ruijia Tan","Mitra Taheri","Nick Birbilis"],
        "repository":"Mendeley Data","dataset_doi":"10.17632/4d4kpfwpf6.1",
        "official_record":"https://data.mendeley.com/datasets/4d4kpfwpf6/1",
        "publication_date":"2025-07-29","version":1,"license":"CC BY 4.0",
        "license_url":"https://creativecommons.org/licenses/by/4.0/",
        "associated_publication":{"title":"A database of mechanical properties for multi principal element alloys",
            "journal":"Chemical Data Collections","volume":47,"article":"101068","year":2023,"doi":"10.1016/j.cdc.2023.101068"},
        "official_filename":path.name,"local_size_bytes":len(raw),"local_sha256":digest,
        "local_md5":hashlib.md5(raw).hexdigest(),"git_blob":old["repository_blob_sha1"],
        "metadata_evidence":"User independently verified the official Mendeley record and associated publication; accepted as supplied authoritative provenance, not freshly retrieved by the agent",
        "agent_remote_corroboration":"Official Mendeley URL and publication DOI each returned proxy CONNECT HTTP 403 during this continuation",
        "source_file_checksum_independently_retrieved":False,
        "documentation_scope":"User-verified documentation identifies tensile yield strength, tensile elongation, UTS, compressive properties, compositions and processing/heat treatment. Does not supply per-case temperatures or material-state identity.",
        "acquisition":"Existing original user-uploaded workbook; no substitute dataset or re-download"}
    (ROOT/"data/additional/mpea_official_provenance_v3.json").write_text(json.dumps(provenance,indent=2)+"\n")
    f=next(iter(read_workbook(path)[0].values()))
    elements=list(f.columns)[list(f.columns).index("Ag"):]
    y,e,paired,valid=numeric_pairs(f,"Yield Strength (MPa)","Elongation (%)")
    p=f.loc[valid].copy().reset_index(drop=True)
    sources=p.Source.map(normalize_study)
    notes=p[NOTE].map(normalize_text)
    chemistry=[tuple(float(v) for v in row) for row in p[elements].to_numpy()]
    components=connected_components(sources.tolist(),chemistry)
    group_for={i:f"study-chemistry-component-{g:03d}" for g,indices in enumerate(components) for i in indices}
    keys=pd.DataFrame({"formula":p.Composition.map(normalize_text),"notes":notes,"source":sources})
    conflicting=keys.duplicated(list(keys.columns),keep=False)
    annotations_path=ROOT/"data/additional/annotations/record_evidence_v3.csv"
    if not annotations_path.exists():pd.DataFrame(columns=ANNOTATION_COLUMNS).to_csv(annotations_path,index=False)
    annotations=pd.read_csv(annotations_path)
    if annotations.excel_row.duplicated().any():raise ValueError("Duplicate/conflicting evidence annotations")
    unknown_rows=set(annotations.excel_row)-set(f.__excel_row)
    if unknown_rows:raise ValueError("Annotation refers to missing Excel rows")
    lookup={int(r["excel_row"]):r for r in annotations.to_dict("records")}
    records=[];cohort=[]
    for i,row in p.iterrows():
        excel=int(row["__excel_row"]);study=sources.iloc[i]
        case_id=f"mpea-row-{excel:04d}"
        status="CONFLICTING" if conflicting.iloc[i] else "CONDITION_UNCERTAIN"
        reason="UNRESOLVED_REPEAT_OR_MATERIAL_STATE" if conflicting.iloc[i] else "TEST_TEMPERATURE_AND_CASE_STATE_NOT_SOURCE_VERIFIED"
        annotation=lookup.get(excel)
        feature_status="REPORTED_COMPOSITION_BASIS_UNVERIFIED"
        if annotation:
            accepted,why=verified_annotation(annotation,study)
            if accepted:
                status="VERIFIED";reason=why;feature_status="SOURCE_VERIFIED_ATOMIC_COMPOSITION"
            else:reason=why
        state=str(annotation["processing_state_id"]) if annotation and status=="VERIFIED" else "UNVERIFIED"
        record={"excel_row":excel,"case_id":case_id,"study_doi":study,"composition_raw":row.Composition,
            "composition_key":json.dumps(chemistry[i]),
            "processing_notes_raw":notes.iloc[i],"qualification_status":status,"qualification_reason":reason,
            "test_temperature_c":annotation.get("test_temperature_c") if annotation else None,
            "evidence_url":annotation.get("evidence_url") if annotation else None,
            "evidence_locator":annotation.get("evidence_locator") if annotation else None,
            "processing_state_id":state,"yield_strength_mpa":float(row["Yield Strength (MPa)"]),
            "elongation_percent":float(row["Elongation (%)"]),"feasible_provisional":float(row["Elongation (%)"])>=10,
            "feature_status":feature_status,"leakage_group":group_for[i]}
        records.append(record)
        cohort.append({**record,**{c:float(row[c]) for c in elements}})
    table=pd.DataFrame(records)
    # Repeated fully annotated same-case identities are never arbitrarily averaged.
    verified=table.qualification_status=="VERIFIED"
    identity=["study_doi","composition_key","processing_state_id","test_temperature_c"]
    dup=table.loc[verified].duplicated(identity,keep=False)
    for index in table.loc[verified].index[dup]:
        table.loc[index,["qualification_status","qualification_reason"]]=["CONFLICTING","REPLICATE_PROTOCOL_REQUIRED_PRESERVE_ALL_RAW_MEASUREMENTS"]
        cohort[index]["qualification_status"]="CONFLICTING"
        cohort[index]["qualification_reason"]="REPLICATE_PROTOCOL_REQUIRED_PRESERVE_ALL_RAW_MEASUREMENTS"
    absent=f.loc[~valid]
    for _,row in absent.iterrows():
        records.append({"excel_row":int(row["__excel_row"]),"case_id":f"mpea-row-{int(row['__excel_row']):04d}",
            "study_doi":normalize_study(row.Source),"composition_raw":row.Composition,
            "processing_notes_raw":normalize_text(row[NOTE]),"qualification_status":"EXCLUDED",
            "qualification_reason":"NO_VALID_NUMERIC_PAIRED_YIELD_AND_ELONGATION_FOR_THIS_OBJECTIVE"})
    all_records=pd.concat([table,pd.DataFrame(records[len(table):])],ignore_index=True).sort_values("excel_row")
    all_records.to_csv(OUTPUT/"record_qualification.csv",index=False)
    cases=pd.DataFrame(cohort)
    primary=cases[cases.qualification_status=="VERIFIED"].copy()
    secondary=cases[cases.qualification_status!="CONFLICTING"].copy()
    primary.to_csv(OUTPUT/"primary_cohort.csv",index=False)
    secondary.to_csv(OUTPUT/"secondary_provisional_cohort.csv",index=False)
    ranked=pd.read_csv(ROOT/"results/dataset_qualification/mpea_study_review_queue.csv").sort_values(
        ["paired_numeric_records","normalized_study_doi"],ascending=[False,True]).reset_index(drop=True)
    ranked.insert(0,"coverage_rank",np.arange(1,len(ranked)+1))
    ranked["cumulative_records"]=ranked.paired_numeric_records.cumsum()
    ranked["cumulative_fraction"]=ranked.cumulative_records/len(p)
    priority=ranked.head(8).copy()
    priority["publication_access_status"]="NOT_RETRIEVED_DOI_NETWORK_POLICY_DENIAL"
    priority["review_complete"]=False
    priority["review_note"]=["Check underlying original studies; citation is a review/data compilation" if any(t in doi for t in ("/j.pmatsci.","/j.dib.")) else "Verify tensile temperature, processing/material state and same-case target pairing" for doi in priority.normalized_study_doi]
    priority.to_csv(OUTPUT/"priority_studies.csv",index=False)
    (OUTPUT/"feature_schema.json").write_text(json.dumps({"element_columns":elements,"primary_features":"composition only",
        "excluded_features":["measured phases","FCC","BCC","HCP","IM","hardness","UTS","compressive strength","plasticity","source as predictor"],
        "provisional_representation":"As-reported rounded element coordinates, no mass/atomic claim or renormalization until source verified",
        "processing_features":"Not enabled until independently verified as planned pre-experiment descriptors"},indent=2)+"\n")
    counts=all_records.qualification_status.value_counts().to_dict()
    primary_positive=int((primary.elongation_percent>=10).sum())
    primary_negative=int((primary.elongation_percent<10).sum())
    positive_groups=primary.loc[primary.elongation_percent>=10,"leakage_group"].nunique()
    negative_groups=primary.loc[primary.elongation_percent<10,"leakage_group"].nunique()
    g1b="COMPLETE" if len(primary)>=27 and min(primary_positive,primary_negative)>0 else "BLOCKED_NO_SUFFICIENT_SOURCE_QUALIFIED_COHORT"
    support={"G1a":provenance["G1a"],"G1b":g1b,"provenance_parts_complete":True,
        "raw_records":len(f),"paired_numeric_records":len(p),"record_status_counts":counts,
        "qualified_independent_cases":len(primary),"qualified_feasible":int((primary.elongation_percent>=10).sum()),
        "qualified_infeasible":int((primary.elongation_percent<10).sum()),
        "qualified_positive_groups":int(positive_groups),"qualified_negative_groups":int(negative_groups),
        "primary_calibration_supported":min(primary_positive,primary_negative)>=15 and min(positive_groups,negative_groups)>=3,
        "secondary_provisional_records":len(secondary),"secondary_provisional_feasible":int((secondary.elongation_percent>=10).sum()),
        "secondary_provisional_infeasible":int((secondary.elongation_percent<10).sum()),
        "secondary_independent_case_count":None,"secondary_final_scientific_benchmark_allowed":False,
        "priority_studies":len(priority),"priority_paired_records":int(priority.paired_numeric_records.sum()),
        "priority_coverage_fraction":float(priority.paired_numeric_records.sum()/len(p)),
        "workbook_sha256":digest,"primary_cohort_sha256":hashlib.sha256((OUTPUT/"primary_cohort.csv").read_bytes()).hexdigest(),
        "secondary_cohort_sha256":hashlib.sha256((OUTPUT/"secondary_provisional_cohort.csv").read_bytes()).hexdigest(),
        "annotation_sha256":hashlib.sha256(annotations_path.read_bytes()).hexdigest(),
        "source_review_scope":"Eight highest-coverage citations initially, including the conflicting-key source; no requirement to review all 135 before development",
        "conflict_resolution":"Four records in two unresolved case-identity groups preserved as CONFLICTING: two discordant measurements and two same-value potential duplicates after DOI normalization; no raw deletion, averaging or invented replicate state",
        "minimum_action":"Apply saved source-access settings (doi.org, data.mendeley.com, www.sciencedirect.com) or provide methods/table evidence for the prioritized sources; no further dataset-level provenance request is needed.",
        "scientific_interpretation":"Zero verified cases means none established with available evidence, not proof no defensible cohort exists in the literature."}
    (OUTPUT/"qualification.json").write_text(json.dumps(support,indent=2)+"\n")
    print({k:support[k] for k in ("G1a","G1b","record_status_counts","qualified_independent_cases","secondary_provisional_records","priority_paired_records")})

if __name__=="__main__":main()
