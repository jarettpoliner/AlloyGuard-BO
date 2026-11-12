# Publication preparation and verification

The public repository initially contained the MIT license, original execution plan and seven uploaded data/source files. Local branch `work` was at `aad46b4`; the source code, tests, protocols, results and reports existed only as untracked workspace files. The remote main tip was `b3d0390f6de21a1989d8f1b934ec608486e878c9`.

A separate `publication/completed-v1-v2` branch was created and fast-forwarded to that remote tip, preserving every existing upload and all local work. No reset, force push, result deletion or history rewrite is part of publication. The prepared commit adds the completed research and final documentation. Remote publication is established only after the pushed commit is verified with `git ls-remote` and its public README is checked.

## Changes

- Final research README with numerical results, architecture diagram, uncertainty and closure decision.
- Original scientific modules, 124 tests, pinned dependencies, data qualification, frozen protocols and full original result/audit artifacts.
- v1/v2 scientific figures, decision report, cost-sensitive analysis, negative conclusions and limitations.
- Dataset rights/attribution and updated citation; unchanged upstream Apache license and original MIT license.
- Offline preparation of pre-existing historical test inputs; non-mutating clean-clone reproduction and independent publication verifier.
- GitHub Actions definition for the tests and saved-evidence audit, with optional manual full reproduction. Local clean-tree verification does not claim a GitHub-hosted workflow has already run.

The former README, citation and ignore file are archived byte-identically. All original scientific modules, tests, frozen configurations and result files remain unchanged. `original_work_manifest.json` records their bytes. The publication verifier understands the archival README mapping; historical stage-specific audit scripts are preserved rather than edited to make old snapshots appear current.

## Exclusions and scan

Virtual environments, caches, private-key/environment filenames, build outputs and newly generated verification trajectories are excluded from Git. Existing audit-bearing repeated traces remain because original reproducibility evidence refers to them. Their aggregate size is approximately 103 MiB before Git compression; the largest individual trace is approximately 12 MiB. No >100 MB file is present. `results/publication/staging_scan.json` records a high-confidence token/private-key/credential-URL scan and excluded-directory checks. That scan is useful evidence, not a guarantee against all possible sensitive content. No credential values or private platform files are intentionally included.

## Verification evidence

`results/publication/tests.xml` records the original-workspace test pass; `clean_tests.xml` records a fresh exported-tree run. `environment.json` verifies Python 3.12.14 and all 23 pinned distributions after an independent virtual-environment installation. `verification.json` records the 9,600-selection clean-tree reproduction and independent checks of measurements, labels, observed IDs, grouping, AUC, failures, probabilities, risk accounting, frozen hashes, baseline equality and README numerical summaries.

Fresh reproduction lives in ignored local storage, not in a second research repository or a new scientific workstream. Only compact verification evidence is added to the publication. Original historical reports and plots are not regenerated.

## Remaining limitations

The pre-existing steel workbook's official source/license is unresolved; it is preserved, not newly licensed or duplicated, and is not part of the Citrine scientific benchmark. GE/Mendeley licensing relies on recorded user-verified official metadata; fresh metadata access was blocked. Citrine source blobs and Apache license are independently matched to the official pinned Git source. See `DATA_LICENSES.md` for the owner's remaining rights-verification action.

The GitHub API returned Forbidden in this environment, while ordinary Git transport and public repository HTML access worked. A non-force Git publication can therefore succeed even if a pull request cannot be created here. Do not interpret local tests or a prepared commit as proof of remote publication; check the actual remote commit.
