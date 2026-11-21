"""Cross-check our offline rules against the organizers' validator, which is the authority.

Skipped unless their script is present. Get it (see wiki/submission.md), then these tests run:

    aws s3 cp s3://perlin-pdh-2026-paris/release/submission/validate-submission.py . --region eu-west-3

Set KEMP_ORGANIZER_VALIDATOR to point somewhere else. The dangerous direction is us being *more
permissive* than they are, so that is what this asserts; being stricter only costs us a warning.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from kemp.paths import ROOT
from kemp.submission import check, parse_fasta

SEQ = "MKD" + "A" * 46 + "QG"  # 51 aa: base D at 3, oxy Q at 50
BASE, OXY = 3, 50

CASES = {
    "valid": f">d1 base={BASE} oxy={OXY}\n{SEQ}\n",
    "oxyanion synonym": f">d1 base={BASE} oxyanion={OXY}\n{SEQ}\n",
    "spaces around =": f">d1 base = {BASE}  oxy = {OXY}\n{SEQ}\n",
    "lowercase sequence": f">d1 base={BASE} oxy={OXY}\n{SEQ.lower()}\n",
    "base on wrong residue": f">d1 base=2 oxy={OXY}\n{SEQ}\n",
    "oxy on wrong residue": f">d1 base={BASE} oxy=49\n{SEQ}\n",
    "oxy is HIS": f">d1 base={BASE} oxy=50\n{SEQ[:49]}H{SEQ[50:]}\n",
    "index out of range": f">d1 base={BASE} oxy=999\n{SEQ}\n",
    "base == oxy": f">d1 base=3 oxy=3\n{SEQ}\n",
    "missing oxy": f">d1 base={BASE}\n{SEQ}\n",
    "free text in header": f">d1 base={BASE} oxy={OXY} my best design\n{SEQ}\n",
    "unknown attribute": f">d1 base={BASE} oxy={OXY} foo=1\n{SEQ}\n",
    "ambiguous residue X": f">d1 base={BASE} oxy={OXY}\n{SEQ[:-1]}X\n",
    "too short": f">d1 base={BASE} oxy=20\nMKD{'A' * 16}Q\n",
    "too long": f">d1 base={BASE} oxy={OXY}\n{SEQ + 'A' * 300}\n",
    "bad name character": f">d 1 base={BASE} oxy={OXY}\n{SEQ}\n",
    "duplicate names": f">d1 base={BASE} oxy={OXY}\n{SEQ}\n>d1 base=1 oxy={OXY}\nE{SEQ[1:]}\n",
    "duplicate sequences": f">d1 base={BASE} oxy={OXY}\n{SEQ}\n>d2 base={BASE} oxy={OXY}\n{SEQ}\n",
    "empty file": "",
    "21 designs": "".join(f">d{i:02d} base={BASE} oxy={OXY}\n{SEQ + 'A' * i}\n" for i in range(21)),
}


def organizer_validator() -> Path | None:
    candidates = [Path(p) for p in [os.environ.get("KEMP_ORGANIZER_VALIDATOR", "")] if p]
    candidates += [ROOT / "validate-submission.py", ROOT / "results" / "validate-submission.py"]
    return next((p for p in candidates if p.is_file()), None)


@pytest.mark.parametrize("name", list(CASES))
def test_we_are_never_more_permissive(name, tmp_path):
    tool = organizer_validator()
    if tool is None:
        pytest.skip("organizers' validate-submission.py not present (see wiki/submission.md)")

    path = tmp_path / "designs.fasta"
    path.write_text(CASES[name], encoding="utf-8")
    # -I: isolated, so their script cannot pick up modules from the working directory
    theirs_accepts = (
        subprocess.run(
            [sys.executable, "-I", tool.name, str(path)],
            cwd=tool.parent,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )

    designs, header_problems = parse_fasta(CASES[name])
    we_accept = not header_problems and not check(designs)

    assert not (we_accept and not theirs_accepts), (
        f"{name!r}: we accept a file the organizers reject — fix kemp.submission"
    )
