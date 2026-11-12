# Experimental data and attribution

The original CSV is now present in `raw/` and verified: 4,706 bytes, MD5 `2a829ae75f620735b874b73fe69bf4d5`, SHA-256 `a9f2b7aaf4b7305535c321bf1354115ac0c157ef1159b23829dff850212ceacd`. The upload was recovered from the user's repository commit. No further dataset downloads were made after matching.

Source: Detor, Oppenheimer, Casey and Crawford (2022), Data in Brief 45, 108582, https://doi.org/10.1016/j.dib.2022.108582. Official dataset https://doi.org/10.6084/m9.figshare.17032760.v1; Figshare article 17032760, file 31504751. User reports CC BY 4.0 from the official record; metadata/license were not independently retrieved. Preserve original attribution and distinguish processed modifications. See `source_manifest.json`, `../docs/DATA_CARD.md` and `../results/data_audit.json`.

Raw bytes are unchanged. Processed CSV groups exact compositions into 82 candidates using mean hardness/minimum rank, preserving replicate evidence. Both raw and processed paths are ignored by Git; this running environment retains them, while a fresh clone needs the original CSV input or official acquisition. The user-uploaded repository version stores the CSV at its root; copy that unmodified file into `data/raw/` before reproduction if needed. Historical blocked notes are archived under `docs/archive/` and `results/archive/`.

From repository root:

```bash
.venv/bin/python scripts/acquire_identified_data.py
PYTHONPATH=src .venv/bin/python scripts/audit_data.py
```

The first command checks the local original before any network access. On absent data it uses only the official file URL, with exact size and checksum enforcement. The original API-based downloader remains available in `scripts/download_data.py`. No synthetic measurements belong in these directories.
