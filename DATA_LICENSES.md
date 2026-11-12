# Dataset rights, provenance and redistribution scope

The MIT license covers original AlloyGuard-BO code. It does not automatically cover uploaded datasets, upstream source/notebooks, articles, or their figures. This publication preserves the upstream license and attribution; it makes no assertion of exclusive ownership of literature facts.

## Primary v1/v2: Citrine MPEA dataset

Source: [CitrineInformatics/MPEA_dataset](https://github.com/CitrineInformatics/MPEA_dataset), pinned commit `d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e`. Publication: Borg et al. (2020), *Expanded dataset of mechanical properties and observed phases of multi-principal element alloys*, Scientific Data, [10.1038/s41597-020-00768-9](https://doi.org/10.1038/s41597-020-00768-9). The upstream README also identifies the [Figshare record](https://doi.org/10.6084/m9.figshare.12642953).

The official Git repository distributes these materials under **Apache License 2.0**. The exact complete license is retained at `data/citrine/raw/UPSTREAM_LICENSE`; SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`. The pinned upstream tree contains LICENSE and no root NOTICE file. Upstream README, bibliography, processing notebook and utility source are retained with attribution. All four input CSV/bibliography Git blobs match the pinned official source; exact byte counts/SHA-256 values are recorded in `results/citrine/source_manifest.json`. This is repository-license evidence, not an inference from AlloyGuard's MIT license or the article's publication license.

**Unmodified source:** `MPEA_dataset.csv`, `2018_data.csv`, `2019_data.csv`, `wos_query_refs.bib` at repository root (pre-existing uploads) and byte-identical copies in `data/citrine/raw/`. `process.ipynb` and `upstream_utils.py.txt` are retained for provenance, not executed by the benchmark. No publisher article/PDF is redistributed.

**Modified/derived data notice:** `results/citrine/cohort.csv`, record audits, excluded-case tables, group IDs and features are AlloyGuard-derived selections/transforms, not official upstream master files. Qualification filters to explicit tensile/25°C paired records, parses atomic compositions, excludes ambiguous recipe repeats and derives study/chemistry groups. These changes are described in `results/citrine/data_audit.json` and implemented in `src/alloyguard_citrine/data.py`. Preserve this attribution and the upstream license when redistributing source or derived data. Model outputs are not new experimental measurements.

## Earlier GE screening study (separate objective)

Detor et al. (2022), *Refractory high entropy alloy dataset with room temperature ductility screening*, Data in Brief 45, 108582; [10.1016/j.dib.2022.108582](https://doi.org/10.1016/j.dib.2022.108582). Figshare article 17032760, file 31504751. The user supplied the official-record **CC BY 4.0** license. Exact local bytes are independently verified (4,706 bytes, MD5 `2a829ae75f620735b874b73fe69bf4d5`); publisher metadata could not be freshly fetched because the environment rejects the Figshare API connection. See `data/source_manifest.json`. Original root upload is unchanged; local test copies are ignored. Attribution applies to historical derived tables as well. This is hardness and ordinal screening, not tensile elongation.

## Historical Mendeley provisional dataset

Li, Zeng, Tan, Taheri and Birbilis, *A database of mechanical properties for multi principal element alloys*, Mendeley Data v1, [10.17632/4d4kpfwpf6.1](https://doi.org/10.17632/4d4kpfwpf6.1); associated publication [10.1016/j.cdc.2023.101068](https://doi.org/10.1016/j.cdc.2023.101068). **CC BY 4.0**, based on user-verified official provenance recorded in `data/additional/mpea_official_provenance_v3.json`; fresh remote corroboration was blocked. Original workbook already exists on main; no additional raw copy is staged. Historical filtered tables and software-validation outputs remain clearly provisional and derived, not part of the qualified Citrine efficacy benchmark.

## Pre-existing steel upload: unresolved

`A database of mechanical properties of steels/Steel database with labelled clusters.xlsx` was uploaded to public main before this publication. Its official source/version/redistribution license remains unknown; `results/dataset_qualification/steel_manifest.json` records the limitation. The repository's MIT license does not resolve it. No new copy of that workbook is added; the existing file and historical audit metadata are preserved as requested. It is excluded from v1/v2 scientific comparisons. Historical qualification tests read a local checksum-matched copy of the existing upload only.

**Remaining owner action:** establish the steel dataset's official source and permission before further third-party redistribution or use. This publication cannot certify rights for that pre-existing upload, and does not silently remove it or rewrite Git history. This issue does not affect the verified Apache-licensed Citrine benchmark. GE/Mendeley licenses remain explicitly attributed to supplied official-record evidence, rather than falsely described as newly fetched verification.
