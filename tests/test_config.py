from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from kemp.config import parse


@dataclass
class C:
    name: str = "x"
    n: int = 1
    lr: float = 0.1
    flag: bool = False


def test_defaults():
    assert parse(C, []) == C()


def test_cli_overrides_are_typed():
    cfg = parse(C, ["--n=3", "--lr=1", "--flag=true", "--name=42"])
    assert cfg == C(name="42", n=3, lr=1.0, flag=True)


def test_file_then_cli_later_wins(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"n": 5, "name": "from-file"}))
    assert parse(C, [str(path), "--n=7"]) == C(name="from-file", n=7)


@pytest.mark.parametrize("argv", [["--nn=3"], ["--n=abc"], ["--flag=maybe"], ["--n"]])
def test_bad_args_fail_loudly(argv):
    with pytest.raises(SystemExit):
        parse(C, argv)
