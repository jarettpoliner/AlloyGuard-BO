# Published Citrine MPEA source

The primary dataset is the exact official `MPEA_dataset.csv`, not a replacement assembled from raw inputs. `2018_data.csv`, `2019_data.csv` and `wos_query_refs.bib` cross-check provenance, original temperature/test fields, synthesis recipes and target extraction. All four user uploads match the official source Git blobs at commit `d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e`.

Source: https://github.com/CitrineInformatics/MPEA_dataset. Borg et al. (2020), Scientific Data, DOI10.1038/s41597-020-00768-9, *Expanded dataset of mechanical properties and observed phases of multi-principal element alloys*. The official README and complete repository Apache 2.0 LICENSE are retained locally. No upstream code/notebook was executed; processing.ipynb and utilities were read as data to understand the published normalization and uncertainty removal.

`raw/` retains unmodified originals and provenance texts. `results/citrine/source_manifest.json` records exact sizes, SHA-256 and Git blob hashes; `cohort.csv`, `record_audit.csv` and `ambiguous_cases_preserved.csv` document all processing/exclusions. The raw and master files have different column meanings; the raw material is not claimed to be identical to the published master simply because row counts add up.

The strict exploratory cohort has 80 unique composition+recorded-recipe cases:58 with elongation>=10%,22 below, 36 cited studies. Every case is explicitly tensile and 25°C in both master and original row. Ambiguous repeats are wholly quarantined, never averaged across potentially different anneals. The source provides nominal recipes, not complete process/strain-rate control; this limitation is retained. Source and master row locators are zero-based data-row indices; spreadsheet line=master_row+2 including the header.

The known processing sequence is pre-experiment metadata. Primary predictors are atomic fractions from published normalized formulas. Recipe one-hot indicators enter only the predeclared feature ablation; no measured phases, grain size, hardness, UTS, source identifier, other mechanical measurements or calculated material-property descriptors are predictors.

Acquisition/reproduction uses `scripts/acquire_citrine.py`: it verifies existing files first, copies matching uploaded root files if available, and only retrieves missing artifacts from pinned official HTTPS URLs, verifying hashes before writing. Different existing content is not overwritten. See [full reproducibility](../../docs/CITRINE_REPRODUCIBILITY.md) and [scientific report](../../results/citrine/REPORT.md).
