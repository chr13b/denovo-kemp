from __future__ import annotations

import hashlib

import pytest

from kemp.data import fetch, sha256


def test_fetch_downloads_once_and_verifies(tmp_path):
    src = tmp_path / "source.txt"
    src.write_bytes(b"kemp")
    digest = hashlib.sha256(b"kemp").hexdigest()

    path = fetch(src.as_uri(), "external/source.txt", checksum=digest, data_dir=tmp_path / "data")
    assert path.read_bytes() == b"kemp" and sha256(path) == digest

    src.unlink()  # second call must not re-download
    assert fetch(src.as_uri(), "external/source.txt", checksum=digest, data_dir=tmp_path / "data") == path


def test_fetch_rejects_wrong_checksum(tmp_path):
    src = tmp_path / "source.txt"
    src.write_bytes(b"kemp")
    with pytest.raises(SystemExit):
        fetch(src.as_uri(), "x.txt", checksum="0" * 64, data_dir=tmp_path)
