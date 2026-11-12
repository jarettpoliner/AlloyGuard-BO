"""Mock source bytes test acquisition integrity, not experimental findings."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("download_data", Path(__file__).resolve().parents[1] / "scripts/download_data.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def source(tmp_path, *, version=1, checksum=None):
    payload = b"Hf(at%),Hardness (GPa)\n100,1\n"
    metadata = {"version": version, "license": {"name": "TEST_FIXTURE_ONLY"},
                "files": [{"name": module.FILENAME, "id": 1,
                           "download_url": "https://api.figshare.com/test-fixture",
                           "size": len(payload),
                           "computed_md5": checksum or hashlib.md5(payload).hexdigest()}]}
    def get(url):
        if url.endswith("test-fixture"):
            return payload, url
        return json.dumps(metadata).encode(), url
    return get, payload


def test_verified_acquisition_is_repeatable(tmp_path):
    get, payload = source(tmp_path)
    a = module.acquire(tmp_path, get)
    b = module.acquire(tmp_path, get)
    assert a["sha256"] == b["sha256"] == hashlib.sha256(payload).hexdigest()
    assert (tmp_path / "data/raw" / module.FILENAME).read_bytes() == payload
    assert a["status"] == "ACQUIRED_SCHEMA_AUDIT_PENDING"


def test_rejects_checksum_mismatch_without_writing_data(tmp_path):
    get, _ = source(tmp_path, checksum="0" * 32)
    with pytest.raises(ValueError, match="checksum mismatch"):
        module.acquire(tmp_path, get)
    assert not (tmp_path / "data/raw").exists()


def test_rejects_wrong_version(tmp_path):
    get, _ = source(tmp_path, version=2)
    with pytest.raises(ValueError, match="version 1"):
        module.acquire(tmp_path, get)


def test_preserves_existing_different_raw_file(tmp_path):
    raw = tmp_path / "data/raw" / module.FILENAME
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"existing user data")
    get, _ = source(tmp_path)
    with pytest.raises(FileExistsError):
        module.acquire(tmp_path, get)
    assert raw.read_bytes() == b"existing user data"


def test_disallows_http():
    with pytest.raises(ValueError, match="HTTPS required"):
        module.fetch("http://api.figshare.com/test")
