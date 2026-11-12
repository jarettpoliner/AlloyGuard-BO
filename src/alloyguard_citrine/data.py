from __future__ import annotations
import hashlib,json,re
from decimal import Decimal
from pathlib import Path
import numpy as np
import pandas as pd
from alloyguard_strength.schema import Candidate,Outcome

UPSTREAM="d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e"
BLOBS={"MPEA_dataset.csv":"a4542498c5d5af66372d4c99abaeeaa5254a12fe","2018_data.csv":"1724b87f4e82c6ee9abed9a97ab945e92f199f92",
       "2019_data.csv":"aee7d343837b5e6b75081443236784745ff93358","wos_query_refs.bib":"670023f068c89096d19e7a08f8dd4baffa78a643"}
ELEMENTS=set("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split())
YS="PROPERTY: YS (MPa)";EL="PROPERTY: Elongation (%)";MODE="PROPERTY: Type of test";DOI="REFERENCE: doi";RECIPE="PROPERTY: synthesis method"


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def formula(text:str)->dict[str,float]:
    text=re.sub(r"\s+","",str(text))
    tokens=re.findall(r"[A-Z][a-z]?|\d+(?:\.\d+)?|[()]",text)
    if ''.join(tokens)!=text or not tokens:raise ValueError("Unsupported or invalid composition syntax")
    position=0
    def sequence(nested=False):
        nonlocal position
        result={}
        while position<len(tokens) and tokens[position]!=')':
            token=tokens[position];position+=1
            if token=='(':
                part=sequence(True)
                if position>=len(tokens) or tokens[position]!=')':raise ValueError("Unbalanced composition")
                position+=1
            elif token in ELEMENTS:part={token:Decimal(1)}
            else:raise ValueError("Invalid element or coefficient position")
            amount=Decimal(1)
            if position<len(tokens) and re.fullmatch(r"\d+(?:\.\d+)?",tokens[position]):
                amount=Decimal(tokens[position]);position+=1
            if amount<=0:raise ValueError("Nonpositive stoichiometry")
            for element,value in part.items():result[element]=result.get(element,Decimal(0))+amount*value
        if not result:raise ValueError("Empty composition group")
        return result
    counts=sequence()
    if position!=len(tokens):raise ValueError("Unbalanced composition")
    total=sum(counts.values())
    return {e:float(v/total) for e,v in sorted(counts.items())}


def chemistry_key(parsed):return json.dumps({e:round(v,12) for e,v in parsed.items()},sort_keys=True)

def normalized_recipe(value):
    return re.sub(r"\s+","",str(value)).upper() if pd.notna(value) else ''

def doi(value):
    match=re.search(r"10\.\d{4,9}/[^\s]+",str(value),re.I)
    return match.group(0).rstrip('.,;').lower() if match else ''


def connected_groups(rows):
    parent=list(range(len(rows)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    seen={}
    for i,row in enumerate(rows):
        for key in (("study",row["study_doi"]),("chemistry",row["composition_key"])):
            if key in seen:
                a,b=find(i),find(seen[key]);parent[a]=b
            else:seen[key]=i
    components={}
    for i in range(len(rows)):components.setdefault(find(i),[]).append(i)
    ordered=sorted(components.values(),key=lambda a:min(rows[i]["case_id"] for i in a))
    return {i:f"citrine-component-{g:03d}" for g,indices in enumerate(ordered) for i in indices}


def qualify(root:Path):
    raw=root/"data/citrine/raw";out=root/"results/citrine";out.mkdir(parents=True,exist_ok=True)
    sources=[]
    for name,expected in BLOBS.items():
        path=raw/name
        if not path.exists():raise FileNotFoundError(f"Required published source absent: {name}; raw files cannot substitute for MPEA_dataset.csv")
        data=path.read_bytes();blob=hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
        if blob!=expected:raise ValueError(f"Official source blob mismatch: {name}")
        sources.append({"filename":name,"size_bytes":len(data),"sha256":sha(path),"git_blob_sha1":blob,"upstream_blob_match":True})
    master=pd.read_csv(raw/"MPEA_dataset.csv")
    inputs=pd.concat([pd.read_csv(raw/"2018_data.csv"),pd.read_csv(raw/"2019_data.csv")],ignore_index=True)
    temp=next(c for c in master if "temperature" in c)
    # Raw files cross-check the publication's rows; they never replace the master targets.
    if len(master)!=1545 or len(inputs)!=len(master):raise ValueError("Unexpected source row counts")
    if not master[MODE].fillna('').equals(inputs[MODE].fillna('')):raise ValueError("Source loading alignment differs")
    if not master[temp].fillna(-999).equals(pd.to_numeric(inputs[temp],errors='coerce').fillna(-999)):
        raise ValueError("Source temperature alignment differs; no default temperatures allowed")
    if not master[DOI].map(doi).equals(inputs[DOI].map(doi)):raise ValueError("Source study alignment differs")
    y=pd.to_numeric(master[YS],errors='coerce');e=pd.to_numeric(master[EL],errors='coerce')
    t=pd.to_numeric(master[temp],errors='coerce')
    eligible=(master[MODE]=='T')&(t==25)&np.isfinite(y)&np.isfinite(e)&(y>0)&(e>=0)
    preliminary=[];flags=[]
    for i,row in master.iterrows():
        reasons=[]
        if row[MODE]!='T':reasons.append("NOT_EXPLICIT_TENSILE")
        if not np.isfinite(t.iloc[i]) or t.iloc[i]!=25:reasons.append("NOT_EXPLICIT_25_C")
        if not np.isfinite(y.iloc[i]) or not np.isfinite(e.iloc[i]):reasons.append("MISSING_NUMERIC_TARGET_PAIR")
        elif y.iloc[i]<=0 or e.iloc[i]<0:reasons.append("INVALID_TARGET_SIGN")
        parsed=None
        try:parsed=formula(row.FORMULA)
        except ValueError:reasons.append("INVALID_COMPOSITION")
        recipe=normalized_recipe(inputs.loc[i,RECIPE]);study=doi(row[DOI])
        if not recipe:reasons.append("MISSING_PROCESSING_RECIPE")
        if not study:reasons.append("MISSING_STUDY_DOI")
        # Master processing removes censor markers; never reinterpret a bound as exact.
        for target in (YS,EL):
            if re.search(r"[<>]",str(inputs.loc[i,target])):reasons.append("CENSORED_SOURCE_TARGET")
        if eligible.iloc[i] and parsed is not None:
            key=chemistry_key(parsed)
            case_id="citrine-"+hashlib.sha256((key+'|'+recipe+'|'+study).encode()).hexdigest()[:16]
            preliminary.append({"master_row":i,"case_id":case_id,"composition_key":key,"study_doi":study,
                "processing_recipe":recipe,"master_processing_class":row['PROPERTY: Processing method'],
                "yield_strength_mpa":float(y.iloc[i]),"elongation_percent":float(e.iloc[i]),
                "raw_source_file":"2018_data.csv" if i<614 else "2019_data.csv",
                "raw_source_row":i if i<614 else i-614,
                "raw_yield_value":str(inputs.loc[i,YS]),"raw_elongation_value":str(inputs.loc[i,EL]),
                "source_comment":str(inputs.loc[i,'REFERENCE: comment']) if pd.notna(inputs.loc[i,'REFERENCE: comment']) else '',
                "composition":parsed,"base_reasons":reasons})
        flags.append({"master_row":i,"source_study":study,"formula":row.FORMULA,"processing_recipe":recipe,
                      "loading_mode":row[MODE],"test_temperature_c":t.iloc[i],"first_exclusion":reasons[0] if reasons else '',
                      "exclusion_reasons":json.dumps(reasons),"preliminary_t25_numeric_pair":bool(eligible.iloc[i])})
    # Exclude all ambiguous repeats by composition+recorded recipe even across studies.
    # The raw notes explicitly warn identical recipes can hide different anneals.
    keys=[(r["composition_key"],r["processing_recipe"]) for r in preliminary]
    counts={key:keys.count(key) for key in set(keys)}
    rows=[];ambiguous=[]
    for row,key in zip(preliminary,keys):
        reason=list(row["base_reasons"])
        if counts[key]>1:reason.append("AMBIGUOUS_REPEATED_COMPOSITION_RECIPE")
        flags[row["master_row"]]["exclusion_reasons"]=json.dumps(reason)
        flags[row["master_row"]]["first_exclusion"]=reason[0] if reason else ''
        if reason:
            if counts[key]>1:ambiguous.append({k:v for k,v in row.items() if k!='composition'})
            continue
        row["qualification_status"]="VERIFIED"
        row["qualification_scope"]="Published master explicitly T and25C, cross-checked against original raw entry; unique reported composition/recipe case, not a fresh individual-paper remeasurement"
        row["feature_status"]="PUBLISHED_ATOMIC_FRACTIONS_COMPOSITION_ONLY"
        rows.append(row)
    rows=sorted(rows,key=lambda r:r["case_id"])
    groups=connected_groups(rows)
    elements=sorted({element for row in rows for element in row["composition"]})
    output=[]
    for i,row in enumerate(rows):
        output.append({**{k:v for k,v in row.items() if k not in ('composition','base_reasons')},
                       "leakage_group":groups[i],**{c:row["composition"].get(c,0.) for c in elements}})
    cohort=pd.DataFrame(output)
    if not cohort.case_id.is_unique:raise ValueError("Independent case ID collision")
    raw_composition_checks=[]
    for row in rows:
        source_composition=formula(inputs.loc[row["master_row"],"FORMULA"])
        maximum=max(source_composition.values())
        rounded={e:round(v/maximum,3) for e,v in source_composition.items()}
        total=sum(rounded.values());recovered={e:v/total for e,v in rounded.items()}
        if set(recovered)!=set(row["composition"]) or any(not np.isclose(recovered[e],row["composition"][e],atol=1e-10,rtol=0) for e in recovered):
            raise ValueError("Raw/master atomic composition differs from documented published normalization")
        raw_composition_checks.append(row["master_row"])
    cohort.to_csv(out/"cohort.csv",index=False)
    pd.DataFrame(flags).to_csv(out/"record_audit.csv",index=False)
    pd.DataFrame(ambiguous).to_csv(out/"ambiguous_cases_preserved.csv",index=False)
    positives=int((cohort.elongation_percent>=10).sum());negatives=len(cohort)-positives
    groups_positive=int(cohort.loc[cohort.elongation_percent>=10,'leakage_group'].nunique())
    groups_negative=int(cohort.loc[cohort.elongation_percent<10,'leakage_group'].nunique())
    exclusions=pd.Series([r['first_exclusion'] for r in flags if r['first_exclusion']]).value_counts().to_dict()
    bibliography=(raw/'wos_query_refs.bib').read_text()
    bib_dois={s.lower().rstrip('.,;') for s in re.findall(r'10\.\d{4,9}/[^\s{}\"]+',bibliography,re.I)}
    comparison={"raw_rows_2018":614,"raw_rows_2019":931,"master_rows":len(master),
        "loading_temperature_study_alignment":"All1545 rows match corresponding raw files in assembly order; no inferred/default temperatures",
        "qualified_raw_composition_crosschecks_passed":len(raw_composition_checks),
        "raw_not_master":"Concatenated raw files used solely for provenance/recipe/censor checks, never substituted for the published master",
        "master_to_raw_direct_numeric_yield_mismatches":int((pd.to_numeric(inputs[YS],errors='coerce').notna()&~np.isclose(pd.to_numeric(inputs[YS],errors='coerce'),y,equal_nan=True)).sum()),
        "bibliography_doi_count":len(bib_dois),"qualified_study_dois_in_2019_bibliography":sum(d in bib_dois for d in cohort.study_doi.unique()),
        "bibliography_scope":"2019 literature search, not guaranteed to enumerate all2018 review sources"}
    report={"G1a":"COMPLETE_OFFICIAL_GIT_BLOB_MATCH","G1b":"COMPLETE_PUBLISHED_REPORTED_CASE_COHORT",
        "study_scope":"EXPLORATORY_RETROSPECTIVE_NOT_PROSPECTIVE_VALIDATION", "raw_master_rows":len(master),
        "explicit_tensile_25c_numeric_pairs":int(eligible.sum()),"qualified_reported_cases":len(cohort),
        "feasible_count":positives,"infeasible_count":negatives,"study_count":int(cohort.study_doi.nunique()),
        "chemical_composition_count":int(cohort.composition_key.nunique()),"leakage_components":int(cohort.leakage_group.nunique()),
        "positive_groups":groups_positive,"negative_groups":groups_negative,
        "calibration_supported":min(positives,negatives)>=15 and min(groups_positive,groups_negative)>=3,
        "element_columns":elements,"exclusion_first_reason_counts":exclusions,"source_cross_checks":comparison,
        "missing_values_by_master_column":master.isna().sum().to_dict(),"cohort_sha256":sha(out/'cohort.csv'),
        "master_sha256":sha(raw/'MPEA_dataset.csv'),"yield_range_mpa":[float(cohort.yield_strength_mpa.min()),float(cohort.yield_strength_mpa.max())],
        "elongation_range_percent":[float(cohort.elongation_percent.min()),float(cohort.elongation_percent.max())],
        "large_elongation_note":"Elongation above100% is physically possible and is not excluded on that basis. Such rows in the initial T25 subset were excluded only for ambiguous repeated processing identity.",
        "processing_qualification":"Recorded recipe sequence is known pre-experiment. No claim all quantitative annealing/strain-rate/grain-size variables are controlled. Repeated ambiguous recipe keys are wholly quarantined, not averaged.",
        "primary_feature_plan":"Atomic composition only, consistent with existing pipeline. Recipe is known grouping metadata; processing-feature addition reserved as exploratory ablation if declared before final run.",
        "source_processing_caution":"Upstream removes ±uncertainty and inequality markers and averages some ranges. Censored source targets excluded. One retained ±reported mean uses the published numeric mean, with source uncertainty preserved in cohort metadata.",
        "independence_caution":"Reported cases are unique in this cohort, not proven independent physical replications. Study/chemistry overlaps grouped for calibration and held-out analyses; seed replays share one finite pool."}
    (out/'data_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'feature_schema.json').write_text(json.dumps({"element_columns":elements,"basis":"Atomic fractions from official normalized atomic-ratio master formulas","post_experiment_features_used":False},indent=2)+'\n')
    manifest={"official_repository":"https://github.com/CitrineInformatics/MPEA_dataset","upstream_commit":UPSTREAM,
        "user_upload_commit":"b3d0390f6de21a1989d8f1b934ec608486e878c9","publication":"Borg et al. (2020), Scientific Data, DOI10.1038/s41597-020-00768-9",
        "title":"Expanded dataset of mechanical properties and observed phases of multi-principal element alloys",
        "source_license":"Official Git repository Apache License2.0; full text retained as UPSTREAM_LICENSE. No inference that this changes AlloyGuard's MIT license or the separate Mendeley dataset license.",
        "license_sha256":sha(raw/'UPSTREAM_LICENSE'),"source_records":sources,
        "source_inspection":"README, utils.py and process.ipynb read as text/JSON only; no upstream code/notebook executed",
        "retrieval_date_utc":"2026-11-12","original_files_unchanged":True}
    (out/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print({k:report[k] for k in ('explicit_tensile_25c_numeric_pairs','qualified_reported_cases','feasible_count','infeasible_count','study_count','leakage_components','calibration_supported')})
    return cohort,report


def load(root,feature_plan="composition_only"):
    folder=Path(root)/'results/citrine'
    schema=json.loads((folder/'feature_schema.json').read_text())
    frame=pd.read_csv(folder/'cohort.csv')
    if feature_plan not in ("composition_only","composition_plus_recipe"):raise ValueError("Unknown feature plan")
    recipes=sorted(frame.processing_recipe.unique())
    candidates=tuple(Candidate(r.case_id,tuple(float(getattr(r,c)) for c in schema['element_columns'])+
        (tuple(float(r.processing_recipe==recipe) for recipe in recipes) if feature_plan=="composition_plus_recipe" else ()),
        r.leakage_group,r.feature_status if feature_plan=="composition_only" else "ATOMIC_FRACTIONS_PLUS_PLANNED_RECIPE_ONEHOT") for r in frame.itertuples())
    outcomes={r.case_id:Outcome(float(r.yield_strength_mpa),float(r.elongation_percent)) for r in frame.itertuples()}
    return candidates,outcomes
