# AlloyGuard-BO execution status

**Research verdict: BLOCKED (`BLOCKED_DATA_SOURCE`).**

The central hypothesis has not been tested. No real dataset, scientific model, sequential replay, benchmark comparison, or figures have been produced. Quantitative performance differences and uncertainty intervals are unavailable.

## Provenance gate

The requested source is Detor et al. (2022), *Refractory high entropy alloy dataset with room temperature ductility screening*, https://doi.org/10.1016/j.dib.2022.108582, with dataset https://doi.org/10.6084/m9.figshare.17032760.v1. The source identity, version, license, file identifier, size and checksums have not yet been independently verified. The manifest explicitly records unknown fields as null.

On 11 November 2026 (America/New_York; 12 November UTC), fresh HTTPS probes to the official Figshare API, dataset DOI and open-access publication returned proxy CONNECT HTTP 403 denials. The environment reported an enforced restricted policy without those domains. This establishes an environment access blocker, not an absent dataset or a scientific failure of RC-CBO. Existing GitHub read authentication worked.

## Completed engineering validation

A project-local Python 3.12.14 virtual environment contains the requested CPU scientific stack, pinned in `requirements.lock`. `pip check` passed. Five acquisition tests passed: checksum rejection, source-version enforcement, repeatable acquisition, preservation of existing files, and HTTPS enforcement. Test data are mock acquisition fixtures only, stored by pytest outside the experimental data directories. These tests provide no scientific validation.

The downloader inspects current Figshare metadata, explicitly requests version 1, requires the original filename, checks source size/MD5, computes SHA-256, records license metadata, and refuses to replace different existing raw data. Actual schema auditing remains mandatory after successful acquisition.

## Saved reusable environment configuration

`install_script`, `start_skill`, and additive custom-domain requirements were saved successfully as an environment draft. Saving does not apply or publish it. Existing package-manager network presets were preserved. No secrets are required for the public data acquisition. Review/save the network changes in environment settings, then retry the downloader. Any metadata-discovered download redirect host must also be allowed if blocked. Publish the environment after review; fresh-task restoration has not been tested.

## Remaining work and scientific limits

G1 remains blocked; G2–G8 are not started. No scientific conclusion, calibration guarantee, physical discovery, or superiority over any baseline or proprietary system is supported. The user's acquisition-before-modeling gate prevents proceeding to scientific modeling without authentic data.

Once access works, verify the CSV and publication; document duplicate aggregation and class support; implement and test matched policies and oracle isolation; freeze the configuration before comparison; then execute the one-seed, five-seed and full paired benchmark. The next evidence-driven step is the actual data audit, which determines whether calibration has sufficient class support. The supplied dataset cannot establish simulation-to-laboratory discrepancy without paired simulation and laboratory hardness measurements.

## Resumed acquisition attempt — file 31504751

The existing repository, dependency lock, code, tests, and earlier report were preserved. The user identified the original file, expected size 4,706 bytes, source MD5 `2a829ae75f620735b874b73fe69bf4d5`, and CC BY 4.0 license. These claims are now recorded separately from the unverified source manifest.

The first resumed check found no `data/raw/` directory or CSV. The official direct URL `https://ndownloader.figshare.com/files/31504751` returned proxy CONNECT HTTP 403. Current runtime observations remain enforced restricted networking with no custom domains; the saved draft already contains `ndownloader.figshare.com`, `api.figshare.com`, and the source publication/DOI hosts. The draft has not been applied to the running instance.

An additional helper now checks an existing local original first, otherwise downloads the direct file, enforces the supplied size/MD5 and computes SHA-256, preserving different existing files. Original acquisition code and tests are unchanged. Current suite: **9 passed**, including four new failure-path tests. Successful real-file validation is unrun; no synthetic data were substituted.

**Verdict remains BLOCKED_DATA_SOURCE. G1 is blocked; G2–G8 remain not started.** Dataset schema, class counts, suitability for rank >=3, source license, actual SHA-256, and comparative performance cannot be determined without the original bytes. No final experimental decisions have been made or changed.

Minimum action: place the original CSV at `/workspace/AlloyGuard-BO/data/raw/GE_RefractoryAlloyScreeningDataset_FINAL.csv`, or review/save the existing network draft to allow the Figshare download and metadata/publication access. Local file placement unblocks byte/schema auditing; independent source/license verification still needs official metadata/publication access or authentic accompanying metadata. No token is required for this public dataset. Publication of the reusable environment remains a separate user action after review.
