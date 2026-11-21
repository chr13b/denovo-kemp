"""Build and check `designs.fasta` offline, with the rules from wiki/submission.md.

    from kemp.submission import Design, build_fasta, check
    problems = check([Design("chris_01", "MKD...", base=3, oxy=7)])

This is our safety net, not the authority: always also run the organizers' `validate-submission.py`
before uploading. Rules enforced here (all from raw/20261121_organizers_submission.md):
  <= 20 designs, 50-260 residues, 20 standard AAs uppercase, unique names of allowed characters,
  1-based base=/oxy= indices that exist and point at an allowed residue type, base != oxy,
  no duplicate sequences.
"""

from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

MAX_DESIGNS = 20
MIN_LEN, MAX_LEN = 50, 260
AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
BASE_OK = set("DE")  # catalytic base: ASP / GLU
OXY_OK = set("QNSTYKR")  # oxyanion-hole donor; HIS is impossible in this format
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
HEADER_RE = re.compile(
    r"^(?P<name>\S+)\s+(?=.*\bbase\s*=)(?=.*\b(?:oxy|oxyanion)\s*=)"
    r"(?:\s*(?:base\s*=\s*(?P<base>\d+)|(?:oxy|oxyanion)\s*=\s*(?P<oxy>\d+)))+\s*$"
)


@dataclasses.dataclass
class Design:
    name: str
    sequence: str
    base: int  # 1-based index of the catalytic base (D/E)
    oxy: int  # 1-based index of the oxyanion-hole donor (Q/N/S/T/Y/K/R)

    def header(self) -> str:
        return f">{self.name} base={self.base} oxy={self.oxy}"

    def residue(self, index: int) -> str:
        """The residue at a 1-based index, or '' if out of range."""
        return self.sequence[index - 1] if 1 <= index <= len(self.sequence) else ""


def check(designs: list[Design]) -> list[str]:
    """Every reason the organizers' validator would reject this set. Empty list means it should pass."""
    problems: list[str] = []
    if not designs:
        problems.append("no designs: the file would be empty")
    if len(designs) > MAX_DESIGNS:
        problems.append(f"{len(designs)} designs, but at most {MAX_DESIGNS} are allowed")

    for what, values in (("name", [d.name for d in designs]), ("sequence", [d.sequence for d in designs])):
        for value in {v for v in values if values.count(v) > 1}:
            label = value if what == "name" else f"{value[:20]}... ({len(value)} aa)"
            problems.append(f"duplicate {what}: {label} appears {values.count(value)}x")

    for d in designs:
        where = f"{d.name}:"
        if not NAME_RE.match(d.name):
            problems.append(f"{where} bad name (letters, digits, _ and - only, max 64 chars)")
        if not MIN_LEN <= len(d.sequence) <= MAX_LEN:
            problems.append(f"{where} length {len(d.sequence)}, must be {MIN_LEN}-{MAX_LEN}")
        if bad := sorted(set(d.sequence) - AMINO_ACIDS):
            problems.append(f"{where} not a standard uppercase amino acid: {' '.join(bad)}")
        for field, index, allowed in (("base", d.base, BASE_OK), ("oxy", d.oxy, OXY_OK)):
            residue = d.residue(index)
            if not residue:
                problems.append(f"{where} {field}={index} is outside the sequence (1-{len(d.sequence)})")
            elif residue not in allowed:
                problems.append(
                    f"{where} {field}={index} points at {residue}, must be one of "
                    f"{' '.join(sorted(allowed))} (off-by-one? indices are 1-based)"
                )
        if d.base == d.oxy:
            problems.append(f"{where} base and oxy are the same residue ({d.base})")
    return problems


def build_fasta(designs: list[Design], width: int = 60) -> str:
    """The submission file as text. Call check() first; this does not validate."""
    lines = []
    for d in designs:
        lines.append(d.header())
        lines += [d.sequence[i : i + width] for i in range(0, len(d.sequence), width)]
    return "\n".join(lines) + "\n"


def parse_fasta(text: str) -> tuple[list[Design], list[str]]:
    """Read a submission file back. Returns (designs, header problems)."""
    designs: list[Design] = []
    problems: list[str] = []
    name = base = oxy = None
    chunks: list[str] = []

    def flush() -> None:
        if name is not None:
            designs.append(Design(name, "".join(chunks), int(base), int(oxy)))

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            flush()
            name = base = oxy = None
            chunks = []
            match = HEADER_RE.match(line[1:].strip())
            if not match:
                problems.append(f"bad header: {line!r} (need '>name base=N oxy=M' and nothing else)")
                continue
            name, base, oxy = match["name"], match["base"], match["oxy"]
        elif name is not None:
            chunks.append(line)
        else:
            problems.append(f"sequence line before any header: {line[:30]!r}")
    flush()
    return designs, problems


def load_designs(path: str | Path) -> list[Design]:
    """Read designs from JSON Lines: one {"name","sequence","base","oxy", ...} object per line.

    Unknown keys (notes, run ids, scores) are ignored, so the file can hold our own bookkeeping.
    """
    designs = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            record = json.loads(line)
            designs.append(
                Design(
                    name=str(record["name"]),
                    sequence=str(record["sequence"]).strip().upper(),
                    base=int(record["base"]),
                    oxy=int(record["oxy"]),
                )
            )
        except (ValueError, KeyError, TypeError) as e:
            raise SystemExit(f"{path}:{n}: cannot read this line ({e})") from e
    return designs
