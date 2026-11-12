# Clean-clone reproduction and preservation

Use Python 3.12.14 on Linux CPU. The original `requirements.lock`, scientific modules, frozen protocols and tests are unchanged. Install the lock into a new virtual environment using the README commands; the project is also packaged with `pyproject.toml`, but `PYTHONPATH=$PWD/src` avoids build-tool dependencies in the documented workflow. Other Python/library versions have not been validated as equivalent.

1. Run `python scripts/prepare_publication_inputs.py` using the installed environment. It copies the three pre-existing uploaded historical inputs to ignored local paths only if absent, checking SHA-256 before and after. No network or credentials are needed after dependencies are installed. Primary Citrine sources are already committed with their license.
2. Run `.venv/bin/python -m pytest -q`: the unchanged 124-test suite includes synthetic correctness, numerical tests, isolation, calibration grouping, model tests and frozen-artifact assertions.
3. Run `bash scripts/reproduce_publication.sh .local-reproduction/run1`. It regenerates v1 primary (1,800 selections), v2 primary (3,600), four v2 sensitivity scenarios (2,400), and three grouped scenarios (1,800): **9,600 fresh selections**. Each policy has equal matched budgets in its scenario. Existing output roots are rejected.
4. The wrapper independently checks preserved source/config/data bytes and compares fresh traces, curves and non-timing metrics with the originals. Full primary/scenario output remains in the chosen local root. Its `verification.json` records actual checks. The checked publication run's compact evidence is `results/publication/verification.json`.

For a quick existing-evidence audit, without rerunning models:

```bash
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
.venv/bin/python scripts/verify_publication.py --output .local-reproduction/evidence-check.json
```

This audits the saved original outputs but does **not** claim a fresh reproduction unless `--reproduced` is provided. Check the resulting mode.

## Exactness and limits

The documented environment reproduces all decision/forecast trace fields except measured `fit_seconds`; tables exclude this runtime column. Floating-point comparisons across unvalidated hardware/BLAS versions may need investigation rather than silently weakening tolerances. PDF timestamps can differ; figures are presentation artifacts. Public results retain original warnings and failures. No new optimization policy or final-result tuning is performed.

The new verification path reads saved original data and outputs. It checks the 80 published cases against master outcomes/mode/temperature, recorded pre-reveal IDs, matched initializations, repeated selections, calibration folds, cumulative failures, AUC, probabilities and forecast-budget accounting. It verifies source hashes and README summary numbers. Source modules remain frozen; no scripts that regenerate original qualification/report paths are run by the wrapper.

## Historical documentation and hashes

`README.md`, `CITATION.cff` and `.gitignore` are intentionally updated for publication. Their exact former bytes are retained under `docs/archive/prepublication_*`. Original preservation manifests still describe their original snapshots and are not rewritten. The publication verifier resolves the historical README path to that archive when validating those snapshots. The old `audit_v2.py` compares root README bytes directly and consequently is a historical-stage audit; use `verify_publication.py` for the publication tree. Old report-generation wrappers can rewrite original output paths; avoid those for non-mutating verification.

`results/publication/original_work_manifest.json` records original scientific work before publication. Missing ignored local files (e.g. processed GE cache) are reported separately; published source, protocols, tests and results must match. Historical raw test inputs are materialized from unchanged uploads. Code/data/report files in the original work snapshot remain unchanged; the three presentation/configuration originals are archived rather than lost.

All original audit-bearing research traces and reports are retained. Newly generated verification trajectories, virtual environments, caches and build products are excluded from Git. The retained historical duplicate reproduction traces are deliberate evidence for the original audits; they are not new candidate experiments. No individual research artifact approaches GitHub's 100 MB file limit. See `DATA_LICENSES.md` before reusing historical non-Citrine uploads.
