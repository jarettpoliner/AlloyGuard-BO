# Scientific dataset qualification — new strength/elongation study

**Status: G1 blocked; no new primary dataset frozen and no new models implemented.**

The strongest *provisional* candidate is the newer MPEA workbook, based on class support and available study citations, not BO performance. Neither new workbook clears the prespecified provenance and measurement-compatibility hard gates. Existing GE methods/results are preserved unchanged. This report does not claim that all unverified records are invalid; it records what is and is not established.

## Comparison before optimization

| Source | Raw records | Numeric paired targets | Provisional >=10% / <10% | Exact deduplicated paired | Study mapping | Qualification |
|---|---:|---:|---:|---:|---|---|
| MPEA | 1713 | 457 | 341 / 116 | 457 | 135 parsed citation IDs | Preferred candidate; G1 unresolved |
| Steel | 3234 | 3234 | 3181 / 53 | 1943 (only 32 <10%) | Absent | Weaker candidate; G1 unresolved |
| GE | 86 | Different target/constraint | 7 feasible /75 infeasible groups | 82 groups | Original single-source benchmark | Retain independently; no MPa conversion |
| Citrine | — | — | — | — | — | Not present; no automatic selection |

The user's preliminary MPEA 1,713/457/341/116 and steel 3,234/53 counts are confirmed for raw numeric records. These are **not independent eligible-case counts**. Steel has 1291 exact duplicates after record-ID removal; only 32 distinct full records fall below 10% after that deduplication. MPEA has no exact duplicate full paired record, but one duplicated composition–processing-note–study proxy with conflicting measured outcomes, and chemical/processing aliases remain unresolved.

## Integrity and provenance

Files recovered unchanged from user repository commit `be942502d094d5a360595166e25a53cc24d5cf88` into `data/additional/raw/`; original names retained. Each archive parsed successfully without executing formulas/macros/scripts. Local SHA-256 and MD5 are recorded, but no source-provided checksum is available for independent official-record verification.

- MPEA SHA-256: `ba34522f472520f3dd6114f5e3fbddb139b7dba5414b153e6476fe3153f5f25f` (282828 bytes).
- Steel SHA-256: `eaa89971150cff2bd97d8a1fe20b21e908731fcf755b37155608b1200235b484` (444713 bytes).

Neither workbook embeds a dataset-level license, official dataset record, publication citation or source version. Row-level study DOIs are not a dataset license. The existing repository MIT software license is not assumed to license third-party experimental data. No raw workbook is committed/pushed or merged with GE. Crossref metadata lookup received proxy CONNECT HTTP 403; current runtime policy has no applied custom domains. No token is needed for public source metadata. Repository byte identity is verified; official publication/version/license remain unresolved.

## MPEA scientific audit

All 457 numeric paired rows have positive finite yield strength and elongation within [0,100]%; ranges [62.0, 2663.0] MPa and [0.0, 98.0]%. Zero elongation is retained, not silently discarded. There are 330 distinct composition strings and 310 distinct rounded numeric chemical vectors; these are not interchangeable independent-case counts.

Numeric compositions are fraction-like and rounded to approximately three decimals. Paired sums span [0.997, 1.0020000000000002]; none have missing or negative element values. The full workbook contains sums down to 0.775, so it must not be silently normalized globally. Atomic versus mass basis and source rounding remain unverified. No composition repairs, outcome imputation or threshold changes were applied.

Paired sources yield 135 normalized DOI citation groups. One source can itself be an earlier aggregation, so these are citation groups rather than proven independent original studies. A study review queue retains each citation and Excel row IDs. Study/chemical-overlap connected-component counts are provided as conservative leakage diagnostics; no random row split is proposed as independent validation.

82 paired records have blank processing notes; many others have generic CAST/WROUGHT/OTHER labels. Processing notes, annealing/sintering temperatures and rates are not automatically test conditions. There is no test-temperature column and no explicit verified tensile/room-temperature case map. 316 paired rows also report UTS and 4 also report compressive strength. This is supporting context, not proof that paired yield and elongation came from the same tensile test.

The entire workbook has 7 simulation-marked records; **none of the 457 paired numeric rows is explicitly simulation-marked in its notes**. Absence of a note is not affirmative experimental provenance. All paired cases remain unverified pending source review. Do not infer that all paired records are simulations or exclude all rows based on unrelated workbook entries.

The duplicated case proxy `AlCoCrFeNi2.1`, note `50μm/s`, DOI `10.1016/j.jallcom.2021.162907`, reports (423 MPa, 23.7%) and (431 MPa, 13%). These may be replicates or distinct unrecorded test conditions; they must not be treated as independently identified experiments or blindly averaged. Both are retained for source review.

## Feature and leakage controls required before modeling

Exclude measured phases and FCC/BCC/HCP/IM indicators, measured hardness/UTS/compressive strength/plasticity, target properties and source identifiers from predictors. Retain source identifiers only for provenance/grouping. Planned processing variables can be features only after their pre-experiment availability and semantics are verified. Unverified steel cluster labels/numbers may encode properties; they are excluded. No outcome-derived descriptors are proposed.

The desired independent case is canonical composition + planned processing + verified loading/temperature/test conditions. Group repeated cases together. Require study-disjoint evaluation, and prevent same composition–processing duplicates crossing train/test boundaries. Effective independent class counts cannot yet be established. The 10% elongation requirement remains provisional and unchanged; class balance alone does not validate this physical endpoint.

## Decision and next action

**No scientifically qualified primary selected yet.** Prefer MPEA conditionally, reject automatic Citrine selection, and keep steel optional pending its own provenance/condition audit. The provisional study maximizes experimentally measured **tensile yield strength (MPa)** with **tensile elongation >=10%**, restricted initially to documented room-temperature (20–30 °C) measurements. Unknown test temperatures are unresolved, not assumed room temperature. If source documentation supports another well-defined stratum, it must be separately declared before modeling.

To complete new G1, supply official dataset/publication URL or DOI and license/version, plus data dictionary or primary-source annotations establishing composition units, tensile pairing, temperature and processing/case identity. `mpea_study_review_queue.csv` lists the source-review work needed. After qualification, create a separately labeled strength study with group-aware calibration/shift tests; preserve all original GE modules/config/source hashes/results. New G2–G8 have not started, and no new benchmark results or superiority claims are fabricated.

The existing GE 43-test benchmark remains a completed independent study, with its previously reported calibration-support and source-metadata qualifications. Its results are not evidence for the proposed yield-strength/elongation study.
