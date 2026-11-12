"""Integrity failure tests; no fixtures represent experimental measurements."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "identified", Path(__file__).resolve().parents[1] / "scripts/acquire_identified_data.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_wrong_size_rejected():
    with pytest.raises(ValueError, match="Size mismatch"):
        module.validate_bytes(b"not experimental data")


def test_correct_size_wrong_checksum_rejected():
    with pytest.raises(ValueError, match="MD5 mismatch"):
        module.validate_bytes(b"x" * module.SIZE)


def test_existing_local_file_checked_without_network_and_preserved(tmp_path):
    raw = tmp_path / "data/raw" / module.FILENAME
    raw.parent.mkdir(parents=True)
    original = b"preserve user file"
    raw.write_bytes(original)
    def no_network():
        pytest.fail("Local file must be checked before making a network request")
    with pytest.raises(ValueError, match="Size mismatch"):
        module.acquire(tmp_path, no_network)
    assert raw.read_bytes() == original
    assert not (tmp_path / "data/identified_file_receipt.json").exists()


def test_invalid_download_never_written(tmp_path):
    with pytest.raises(ValueError, match="MD5 mismatch"):
        module.acquire(tmp_path, lambda: (b"x" * module.SIZE, module.URL))
    assert not (tmp_path / "data/raw" / module.FILENAME).exists()
