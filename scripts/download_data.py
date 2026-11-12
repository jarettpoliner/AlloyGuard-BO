"""Acquire only the official version-1 experimental CSV; never execute source content."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

ARTICLE = 17032760
API = f"https://api.figshare.com/v2/articles/{ARTICLE}"
FILENAME = "GE_RefractoryAlloyScreeningDataset_FINAL.csv"
DOI = "https://doi.org/10.6084/m9.figshare.17032760.v1"


def fetch(url: str) -> tuple[bytes, str]:
    if urlparse(url).scheme != "https":
        raise ValueError("HTTPS required")
    with urlopen(url, timeout=45) as response:
        if urlparse(response.url).scheme != "https":
            raise ValueError("Non-HTTPS redirect")
        body = response.read(10_000_001)
        if len(body) > 10_000_000:
            raise ValueError("Unexpectedly large dataset/metadata")
        return body, response.url


def acquire(root: Path, get=fetch) -> dict:
    # Inspect current metadata, then explicitly request the cited version.
    current_bytes, _ = get(API)
    current = json.loads(current_bytes)
    metadata_bytes, metadata_url = get(API + "/versions/1")
    metadata = json.loads(metadata_bytes)
    if metadata.get("version") != 1:
        raise ValueError("Source did not return dataset version 1")
    files = [f for f in metadata["files"] if f["name"] == FILENAME]
    if len(files) != 1:
        raise ValueError("Official record does not uniquely identify the expected CSV")
    source = files[0]
    content, resolved_url = get(source["download_url"])
    if len(content) != source["size"]:
        raise ValueError("Source file-size mismatch")
    expected_md5 = source.get("computed_md5") or source.get("supplied_md5")
    if not expected_md5:
        raise ValueError("Source checksum unavailable; investigate before accepting data")
    if hashlib.md5(content).hexdigest().lower() != expected_md5.lower():
        raise ValueError("Source checksum mismatch")
    first = content.decode("utf-8-sig").splitlines()[0]
    if "Hf" not in first or "Hardness" not in first or "<html" in first.lower():
        raise ValueError("Unexpected CSV content; inspect schema before proceeding")
    license_info = metadata.get("license")
    if not license_info:
        raise ValueError("License metadata missing")
    manifest = {
        "status": "ACQUIRED_SCHEMA_AUDIT_PENDING",
        "source_doi": DOI, "metadata_url": metadata_url,
        "article_id": ARTICLE, "file_id": source["id"],
        "version": 1, "latest_version_at_retrieval": current.get("version"),
        "original_filename": FILENAME, "download_url": source["download_url"],
        "resolved_download_url": resolved_url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
        "source_md5": expected_md5, "license": license_info,
        "publisher": "Figshare", "authors": metadata.get("authors", []),
        "source_title": metadata.get("title"),
        "associated_publication": "https://doi.org/10.1016/j.dib.2022.108582",
        "redistribution": "Review source license and attribution before committing raw data",
    }
    raw = root / "data/raw" / FILENAME
    # Never overwrite a different pre-existing download or manifest.
    if raw.exists() and raw.read_bytes() != content:
        raise FileExistsError("Existing raw file differs; preserve and investigate")
    manifest_path = root / "data/source_manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        if old.get("sha256") not in (None, manifest["sha256"]):
            raise FileExistsError("Existing provenance has a different hash")
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(content)
    (root / "data/figshare_version1_metadata.json").write_bytes(metadata_bytes)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        manifest = acquire(args.root)
    except Exception as exc:
        parser.exit(2, f"BLOCKED_DATA_SOURCE: {type(exc).__name__}: {exc}\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
