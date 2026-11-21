"""Tiny typed config system, in the spirit of nanoGPT's configurator.py.

Each script declares its settings as a dataclass with defaults, then:

    cfg = parse(Config)  # python scripts/10_x.py --n=5 --name=foo
    # python scripts/10_x.py configs/E-001.json --seed=1   (config file first, later args win)

Config files can be .json, or .toml on Python 3.11+. Unknown keys and wrong types fail loudly,
so a typo can't silently fall back to a default.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

_TRUE, _FALSE = {"1", "true", "yes", "y"}, {"0", "false", "no", "n"}


def parse(cls: type, argv: list[str] | None = None) -> Any:
    """Build `cls` (a dataclass) from defaults < config files < `--key=value` args, in argv order."""
    argv = sys.argv[1:] if argv is None else argv
    fields = {f.name: f for f in dataclasses.fields(cls)}
    values: dict[str, Any] = {}
    for arg in argv:
        if arg.startswith("--"):
            key, sep, raw = arg[2:].partition("=")
            key = key.replace("-", "_")
            if not sep:
                raise SystemExit(f"config: use --{key}=value (got {arg!r})")
            values[key] = _from_cli(_field(fields, key), raw)
        else:
            for key, val in _load_file(Path(arg)).items():
                values[key] = _check(_field(fields, key), val)
    return cls(**values)


def _field(fields: dict, key: str) -> dataclasses.Field:
    if key not in fields:
        raise SystemExit(f"config: unknown key {key!r}; valid keys: {', '.join(sorted(fields))}")
    return fields[key]


def _default(f: dataclasses.Field) -> Any:
    if f.default is not dataclasses.MISSING:
        return f.default
    if f.default_factory is not dataclasses.MISSING:
        return f.default_factory()
    return dataclasses.MISSING


def _from_cli(f: dataclasses.Field, raw: str) -> Any:
    d = _default(f)
    if isinstance(d, bool):
        if raw.lower() in _TRUE | _FALSE:
            return raw.lower() in _TRUE
        raise SystemExit(f"config: --{f.name} expects true/false, got {raw!r}")
    if isinstance(d, str):
        return raw
    try:
        val = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        val = raw
    return _check(f, val)


def _check(f: dataclasses.Field, val: Any) -> Any:
    d = _default(f)
    if d is dataclasses.MISSING or d is None:
        return val
    if isinstance(d, float) and isinstance(val, int) and not isinstance(val, bool):
        return float(val)
    if isinstance(val, bool) != isinstance(d, bool) or not isinstance(val, type(d)):
        raise SystemExit(f"config: {f.name} expects {type(d).__name__}, got {val!r}")
    return val


def _load_file(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"config: no such config file {path}")
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".toml":
        import tomllib  # Python 3.11+

        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise SystemExit(f"config: unsupported config file type {path.suffix} (use .json or .toml)")
