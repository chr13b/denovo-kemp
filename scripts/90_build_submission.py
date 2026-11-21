"""Turn our candidate list into designs.fasta and check it offline.

    uv run python scripts/90_build_submission.py       # results/designs.jsonl -> results/designs.fasta
    uv run python scripts/90_build_submission.py --designs=my.jsonl --out=/tmp/designs.fasta

Exits non-zero and writes nothing if any rule from wiki/submission.md is broken.
Afterwards run the organizers' validator, which is the authority:
    python3 validate-submission.py results/designs.fasta
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kemp.config import parse
from kemp.paths import RESULTS
from kemp.submission import build_fasta, check, load_designs, parse_fasta


@dataclass
class Config:
    designs: str = str(RESULTS / "designs.jsonl")  # input: one JSON object per line
    out: str = str(RESULTS / "designs.fasta")  # output: the file we upload


def main(cfg: Config) -> None:
    source = Path(cfg.designs)
    if not source.is_file():
        raise SystemExit(
            f"no candidate file at {source}\n"
            "Add one JSON object per line, e.g.:\n"
            '  {"name": "chris_01", "sequence": "MKAY...", "base": 19, "oxy": 24}\n'
            "Copy results/designs.jsonl.template to start. See wiki/submission.md."
        )

    designs = load_designs(source)
    problems = check(designs)
    if problems:
        print(f"{len(problems)} problem(s) — nothing written:")
        for p in problems:
            print(f"  - {p}")
        raise SystemExit(1)

    text = build_fasta(designs)
    roundtrip, header_problems = parse_fasta(text)  # the file must read back exactly as intended
    assert not header_problems, header_problems
    assert [(d.name, d.sequence, d.base, d.oxy) for d in roundtrip] == [
        (d.name, d.sequence, d.base, d.oxy) for d in designs
    ]

    out = Path(cfg.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"{len(designs)} design(s) of max 20 -> {out}")
    for d in designs:
        base, oxy = f"{d.base}({d.residue(d.base)})", f"{d.oxy}({d.residue(d.oxy)})"
        print(f"  {d.name}: {len(d.sequence)} aa, base={base}, oxy={oxy}")
    print("\nOur checks passed. Now run the organizers' validator, which decides:")
    print(f"  python3 validate-submission.py {out}")


if __name__ == "__main__":
    main(parse(Config))
