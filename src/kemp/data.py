"""Reproducible data: download by URL with a pinned checksum, and hash files obtained any other way.

    from kemp.data import fetch, sha256
    path = fetch("https://example.org/set.csv", "external/set.csv", checksum="ab12...")
    # -> data/external/set.csv, downloaded once, checksum verified on every call
    sha256(path)  # for files from a USB stick or shared drive: record the hash in wiki/data.md

Every dataset gets a row in wiki/data.md (source, version/date, sha256, how to get it).
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path

from kemp.paths import DATA


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: str, checksum: str | None = None, data_dir: Path = DATA) -> Path:
    """Download `url` to data_dir/dest once, then verify its sha256 on every call."""
    path = Path(data_dir) / dest
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_name(path.name + ".part")
        with urllib.request.urlopen(url) as response, open(part, "wb") as f:
            shutil.copyfileobj(response, f)
        part.replace(path)
    actual = sha256(path)
    if checksum is None:
        print(f"[data] {path}  sha256={actual}  <- pin this in your script and wiki/data.md")
    elif actual != checksum:
        raise SystemExit(f"[data] checksum mismatch for {path}: expected {checksum}, got {actual}")
    return path
