# Additional datasets — separate qualification study

## Current MPEA v3 status

MPEA **G1a is now complete** using the user independently verified official Mendeley v1 source (DOI `10.17632/4d4kpfwpf6.1`, CC BY 4.0) and Chemical Data Collections publication (DOI `10.1016/j.cdc.2023.101068`), with exact original local file integrity recorded in `mpea_official_provenance_v3.json`. G1b is separate. The strength pipeline is implemented and software-validated while prioritized source-condition review remains publisher-access blocked. See [current report](../../results/strength_v3/REPORT.md) and [workflow](../../docs/STRENGTH_V3.md). Do not repeat the resolved MPEA dataset-level provenance request. The earlier v2 qualification notes below are retained as historical context; steel source metadata remain unresolved independently.

The unchanged user-uploaded workbooks are retained locally under `raw/` and are not merged with the GE dataset. The current checkout did not initially contain them; they were recovered from Git commit `be942502d094d5a360595166e25a53cc24d5cf88` without resetting or overwriting existing work.

- `MPEA_parsed_mechanical_database.xlsx` from `A database of mechanical properties for multi prin/`.
- `Steel database with labelled clusters.xlsx` from `A database of mechanical properties of steels/`.

Exact Git blob identities, local byte sizes, SHA-256 and MD5 are in the [qualification manifests](../../results/dataset_qualification/). These establish local/upload identity, not an independently authenticated official dataset version or license. Raw workbook files are ignored here pending source/license qualification; no datasets were pushed or redistributed by the agent.

No original Citrine CSV was found in the workspace or the selected remote tree. GE remains at `data/raw/` with its existing separate manifests, processing, frozen methods and results.

Run from repository root:

```bash
.venv/bin/python scripts/qualify_datasets.py
```

This uses the existing locked dependencies and a stdlib OOXML reader; it does not require openpyxl, execute formulas, fit models, or run optimization. It rebuilds numerical/duplicate/condition/source audits, a 135-citation review queue, record-level qualification flags and the provisional primary-dataset decision. No temperature or loading mode is inferred as established fact from a target-column name or a processing temperature. Full report: [qualification report](../../results/dataset_qualification/REPORT.md).

The newer MPEA workbook is the preferred provisional candidate, with 457 numeric pairs (341 >=10%, 116 <10%). New G1 is blocked by official provenance/license/version and tensile/test-temperature/case-comparability verification. Effective independent case counts remain unknown. Supplying official dataset/publication identifiers and the applicable test-condition/source documentation is the next step; no new primary selection is frozen yet.
