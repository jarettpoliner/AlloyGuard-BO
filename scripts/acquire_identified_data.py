"""Use the identified official file, checking local bytes before network access.

This validates byte integrity against user-supplied source identifiers. It does
not independently establish source metadata, licensing, or scientific validity.
The original metadata-based downloader remains available and unchanged.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

FILENAME = "GE_RefractoryAlloyScreeningDataset_FINAL.csv"
URL = "https://ndownloader.figshare.com/files/31504751"
SIZE = 4706
MD5 = "2a829ae75f620735b874b73fe69bf4d5"


def validate_bytes(content: bytes) -> dict:
    if len(content) != SIZE:
        raise ValueError(f"Size mismatch: expected {SIZE}, received {len(content)}")
    digest = hashlib.md5(content).hexdigest()
    if digest != MD5:
        raise ValueError(f"MD5 mismatch: expected {MD5}, received {digest}")
    rows = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))
    if len(rows) < 2 or not rows[0] or len(set(rows[0])) != len(rows[0]):
        raise ValueError("CSV is empty or has duplicate column names")
    if any(len(row) != len(rows[0]) for row in rows[1:]):
        raise ValueError("CSV contains inconsistent field counts")
    return {"size_bytes": len(content), "md5": digest,
            "sha256": hashlib.sha256(content).hexdigest(),
            "actual_columns": rows[0], "parsed_data_rows": len(rows) - 1}


def download() -> tuple[bytes, str]:
    with urlopen(URL, timeout=30) as response:
        if urlparse(response.url).scheme != "https":
            raise ValueError("Non-HTTPS redirect rejected")
        return response.read(SIZE + 1), response.url


def acquire(root: Path, get=None) -> dict:
    raw = root / "data/raw" / FILENAME
    if raw.exists():
        content = raw.read_bytes()
        method, resolved = "local_file", None
    else:
        content, resolved = (get or download)()
        method = "official_direct_download"
    integrity = validate_bytes(content)
    receipt = {
        "status": "BYTE_INTEGRITY_VERIFIED_SCIENTIFIC_AUDIT_PENDING",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": method, "resolved_download_url": resolved,
        "expected_metadata_source": "user-provided official-file identifiers",
        "article_id": 17032760, "file_id": 31504751,
        "requested_version": 1,
        "source_doi": "https://doi.org/10.6084/m9.figshare.17032760.v1",
        "download_url": URL, "original_filename": FILENAME,
        "reported_license": "CC BY 4.0",
        "source_metadata_independently_verified": False,
        "license_independently_verified": False,
        "scientific_schema_audit_complete": False,
        **integrity,
    }
    # An existing local file is validated, never repaired or replaced.
    if not raw.exists():
        raw.parent.mkdir(parents=True, exist_ok=True)
        with raw.open("xb") as handle:
            handle.write(content)
    destination = root / "data/identified_file_receipt.json"
    if destination.exists():
        old = json.loads(destination.read_text())
        if old.get("sha256") != receipt["sha256"]:
            raise FileExistsError("Different existing receipt; preserve and investigate")
        return old
    destination.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(acquire(args.root), indent=2))
    except Exception as exc:
        parser.exit(2, f"BLOCKED_DATA_SOURCE: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
