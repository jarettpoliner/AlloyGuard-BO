# Experimental data

No experimental data have been acquired. `source_manifest.json` records the failed source-access attempt without inventing hashes or licensing information. `raw/` and `processed/` are ignored. Run `../scripts/download_data.py` with the project's Python after access is restored. Successful acquisition does not complete the scientific schema audit or authorize committing raw data; review the recorded source license first.

## Identified-file continuation

The original file is still absent after the resume attempt. The directory `data/raw/` now exists for placement of the original CSV. Run `.venv/bin/python scripts/acquire_identified_data.py` from the repository root to prefer local validation or use the official file URL. Source identifiers supplied by the user are retained in `identified_source_requirements.json`; they are not represented as independently retrieved source metadata. No receipt or dataset SHA-256 exists yet.
