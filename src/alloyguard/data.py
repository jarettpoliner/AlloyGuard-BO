"""Strict raw-data audit and deterministic whole-composition aggregation."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .schema import Candidate, ExperimentalOutcome, ELEMENTS

FILENAME = "GE_RefractoryAlloyScreeningDataset_FINAL.csv"
EXPECTED_MD5 = "2a829ae75f620735b874b73fe69bf4d5"
COMPOSITION = [f"{e}(at%)" for e in ELEMENTS]
RANK = "Ductility Ranking (0-5)"
HARDNESS = "Hardness (GPa)"
SOLIDUS = "Predicted Solidus (°C)"
COLUMNS = COMPOSITION + [RANK, SOLIDUS, HARDNESS]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_frame(frame: pd.DataFrame) -> None:
    if list(frame.columns) != COLUMNS:
        raise ValueError(f"Actual schema differs: {list(frame.columns)}")
    if frame.empty or frame.isna().any().any():
        raise ValueError("Empty dataset or missing measurements; no silent imputation")
    a = frame.to_numpy(dtype=float)
    if not np.isfinite(a).all():
        raise ValueError("Non-finite measurement")
    comp = frame[COMPOSITION].to_numpy(float)
    if np.any(comp < 0) or not np.allclose(comp.sum(axis=1), 100, atol=1e-6, rtol=0):
        raise ValueError("Invalid composition sums/nonnegativity; no silent normalization")
    ranks = frame[RANK].to_numpy(float)
    if not np.isin(ranks, np.arange(6)).all():
        raise ValueError("Ordinal screening ranks must be integers 0..5")
    if (frame[HARDNESS] <= 0).any() or (frame[SOLIDUS] <= 0).any():
        raise ValueError("Unexpected hardness/solidus range; investigate")


def process(frame: pd.DataFrame) -> pd.DataFrame:
    validate_frame(frame)
    records = []
    # Exact as-reported composition keys; no outcome-based grouping or tolerance merging.
    for key, group in frame.groupby(COMPOSITION, sort=True, dropna=False):
        digest = hashlib.sha256(json.dumps(list(key)).encode()).hexdigest()[:16]
        records.append({"alloy_id": f"alloy-{digest}",
                        **{e: float(v) / 100 for e, v in zip(ELEMENTS, key)},
                        "hardness_gpa": float(group[HARDNESS].mean()),
                        "ductility_rank": int(group[RANK].min()),
                        "solidus_c": float(group[SOLIDUS].mean()),
                        "replicate_count": len(group),
                        "raw_row_ids": json.dumps([int(i) for i in group.index]),
                        "hardness_replicate_sd": float(group[HARDNESS].std(ddof=1)) if len(group)>1 else 0.,
                        "rank_min": int(group[RANK].min()), "rank_max": int(group[RANK].max())})
    result = pd.DataFrame(records).sort_values("alloy_id").reset_index(drop=True)
    if result.alloy_id.duplicated().any():
        raise ValueError("Stable identifier collision")
    return result


def problem_from_frame(frame: pd.DataFrame):
    candidates = tuple(Candidate(row.alloy_id, tuple(float(getattr(row, e)) for e in ELEMENTS))
                       for row in frame.itertuples())
    outcomes = {row.alloy_id: ExperimentalOutcome(float(row.hardness_gpa), int(row.ductility_rank))
                for row in frame.itertuples()}
    return candidates, outcomes


def audit(root: Path) -> tuple[pd.DataFrame, dict]:
    path = root / "data/raw" / FILENAME
    content = path.read_bytes()
    if len(content) != 4706 or hashlib.md5(content).hexdigest() != EXPECTED_MD5:
        raise ValueError("Original file integrity mismatch")
    raw = pd.read_csv(path, encoding="utf-8-sig")
    grouped = process(raw)
    count = int((grouped.ductility_rank >= 3).sum())
    reps = grouped[grouped.replicate_count > 1].to_dict(orient="records")
    report = {
        "status": "VALIDATED_LOCAL_DATA", "raw_rows": len(raw), "unique_compositions": len(grouped),
        "actual_columns": list(raw.columns), "dtypes": {c:str(t) for c,t in raw.dtypes.items()},
        "missing_values": raw.isna().sum().to_dict(),
        "min_at_percent": float(raw[COMPOSITION].min().min()),
        "max_composition_sum_error_at_percent": float(abs(raw[COMPOSITION].sum(axis=1)-100).max()),
        "composition_tolerance_at_percent": 1e-6,
        "conversion": "Divide by 100; no renormalization or imputation",
        "hardness_range_gpa": [float(raw[HARDNESS].min()),float(raw[HARDNESS].max())],
        "solidus_range_c": [float(raw[SOLIDUS].min()),float(raw[SOLIDUS].max())],
        "raw_rank_counts": {str(k):int(v) for k,v in raw[RANK].value_counts().sort_index().items()},
        "grouped_rank_counts": {str(k):int(v) for k,v in grouped.ductility_rank.value_counts().sort_index().items()},
        "raw_feasible": int((raw[RANK]>=3).sum()), "feasible_count":count,
        "infeasible_count":len(grouped)-count, "feasibility_threshold":3,
        "duplicate_groups":reps,
        "duplicate_treatment":"Exact reported at% keys; mean hardness, minimum rank, preserve replicate metadata. Conservative any-replicate screening failure. Duplicate ranks 4/4/5 are all feasible.",
        "global_calibration_min_per_class":15,
        "calibration_supported":min(count,len(grouped)-count)>=15,
        "calibration_gate":"Disable all real-data calibration when either unique-composition class has fewer than 15 members; retain threshold.",
        "scientific_interpretation":"Rank is ordinal screening, not tensile strain; solidus is computational Thermo-Calc, not measured hardness. Successfully characterized compositions only.",
        "sha256": hashlib.sha256(content).hexdigest(), "md5":EXPECTED_MD5,
        "provenance_verification":"Local bytes match user-supplied official file MD5 and size. Source publisher metadata/license not independently retrieved due network policy; no new download attempted.",
    }
    (root/"data/processed").mkdir(exist_ok=True)
    out = root/"data/processed/compositions.csv"
    grouped.to_csv(out,index=False)
    report["processed_sha256"]=sha256_file(out)
    (root/"results/data_audit.json").write_text(json.dumps(report,indent=2)+"\n")
    text = (f"# Dataset audit\n\n86 raw records; {len(grouped)} unique compositions. "
            f"Rank >=3: **{count} feasible / {len(grouped)-count} infeasible** after grouping. "
            f"Raw feasible records: {report['raw_feasible']}.\n\n"
            +report["duplicate_treatment"]+"\n\n"+report["conversion"]+".\n\n"
            +f"Missing values: {int(raw.isna().sum().sum())}. Hardness range: {report['hardness_range_gpa']} GPa. "
            +f"Predicted solidus: {report['solidus_range_c']} °C. "
            +f"Maximum sum error: {report['max_composition_sum_error_at_percent']:.3g} at%; tolerance 1e-6 at%.\n\n"
            +f"Raw rank counts: {report['raw_rank_counts']}. Group counts: {report['grouped_rank_counts']}.\n\n"
            +"**Calibration support insufficient.** The original plan prefers at least 15 of each class. "
            +"The threshold stays fixed and calibration is disabled on real data; its code is verified separately. "
            +"RC-CBO must therefore reduce to ordinary CBO. Calibration efficacy cannot be established here.\n\n"
            +report["scientific_interpretation"]+"\n\n"+report["provenance_verification"]+"\n\n"
            +f"Raw SHA-256: `{report['sha256']}`. Processed SHA-256: `{report['processed_sha256']}`.\n")
    (root/"results/data_audit.md").write_text(text)
    manifest={"status":"LOCAL_BYTES_VERIFIED", "source_doi":"https://doi.org/10.6084/m9.figshare.17032760.v1",
              "article_id":17032760,"file_id":31504751,"dataset_version":1,"original_filename":FILENAME,
              "download_url":"https://ndownloader.figshare.com/files/31504751", "size_bytes":len(content),
              "source_md5":EXPECTED_MD5,"sha256":report["sha256"],
              "acquisition":"User uploaded original to repository; recovered from Git commit 843c94d3264ab73904512ff3e54b1634084428d1 without resetting local work",
              "license":{"name":"CC BY 4.0", "url":"https://creativecommons.org/licenses/by/4.0/", "evidence":"User-supplied official record; publisher metadata not independently accessible"},
              "attribution":"Detor, Oppenheimer, Casey and Crawford (2022), Data in Brief 45, 108582, https://doi.org/10.1016/j.dib.2022.108582",
              "verification_date_utc":"2026-11-12", "publisher":"Figshare (user-identified record)",
              "resolved_url":None,"publisher_metadata_independently_verified":False,
              "modifications":"Raw bytes unchanged. Processed group means/minimum rank documented separately."}
    (root/"data/source_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return grouped, report
