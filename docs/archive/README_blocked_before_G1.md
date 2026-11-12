# AlloyGuard-BO

**Status: data-source blocked; research implementation not yet complete.**

This project will test whether training-only calibration of feasibility probabilities improves finite-pool selection of hard refractory alloys with ductility screening rank >=3. The intended comparison is random selection, hardness-only BO, constrained BO, and reliability-calibrated constrained BO. No performance results exist yet.

The current repository provides a tested, provenance-controlled downloader and a reproducible Python environment. See [execution status](results/REPORT.md), [execution log](docs/EXECUTION_LOG.md) and the original research plan. The existing LICENSE is preserved.

From `/workspace/AlloyGuard-BO`:

```bash
bash scripts/setup_environment.sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/download_data.py
```

The downloader requires allowed HTTPS access to `api.figshare.com` and its metadata-provided download host. DOI/publication access is also required for scientific interpretation. Current requests receive proxy HTTP 403. Review and save the prepared network settings, then retry. It records real checksums/license only after successful acquisition. Raw downloads are ignored by Git pending license review.

The lockfile pins the installed scientific stack on Python 3.12.14/Linux. No GPU, external inference API, service, credentials, or network endpoint exposure is needed. Setup can be rerun without changing the lockfile.

Dataset audit, synthetic model checks, smoke/full benchmarks and report-generation commands will be added only as their implementations are completed and verified. The current report is a blocker report, not a research result. The intended study is retrospective, small-sample, and limited to previously measured compositions; ordinal ductility screening does not establish universal mechanical reliability or synthesis success.

Sources requested: [Detor et al.](https://doi.org/10.1016/j.dib.2022.108582), [official dataset v1](https://doi.org/10.6084/m9.figshare.17032760.v1). Other required sources remain to be consulted after network access is applied. No literature-content verification is claimed.

## Resume with the identified original file

The user supplied official file ID `31504751`, expected size 4,706 bytes, MD5 `2a829ae75f620735b874b73fe69bf4d5`, and license CC BY 4.0. These source claims are recorded separately in `data/identified_source_requirements.json`; independent verification remains pending.

Place the unmodified original CSV at `data/raw/GE_RefractoryAlloyScreeningDataset_FINAL.csv`, or enable the saved Figshare domains, then run:

```bash
.venv/bin/python scripts/acquire_identified_data.py
```

This checks a local file first; only if absent does it request the identified direct URL. It refuses size/MD5 mismatches, preserves existing local files, computes SHA-256, and records actual columns/row count after byte verification. Its receipt does not mark G1 passed: publication interpretation, source/license verification, numerical schema and scientific data audits remain mandatory. The existing API-based downloader is preserved.
