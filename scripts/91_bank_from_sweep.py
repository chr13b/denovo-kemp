"""Promote the best designs from a sequence sweep into submission candidates.

Usage:
    uv run python scripts/91_bank_from_sweep.py <geometry.tsv> <queries.json> \
        [--name-prefix=chris_a] [--max=5] [--require-window=both|base|none] [--dry-run]

A sweep produces dozens of folded sequences. This selects the ones worth a submission slot and
appends them to `results/designs.jsonl` in the format `make submission` consumes.

Selection, in order:
  1. keep only rows the measurement step actually measured, with no 2.2 Å clashes
  2. apply --require-window (default: both base and donor inside the family-measured windows)
  3. rank by |base − 2.51 Å|, the family median, because the geometry term has an OPTIMUM and
     too short is punished harder than too long
  4. take --max of them

The off-by-one guard matters more here than anywhere else in the repo: `base=` and `oxy=` are
1-based indices into the SUBMITTED sequence, and the scorer does not reject a wrong index - it
silently measures an unrelated residue and returns a plausible number. So every candidate's
residue identity is verified against the index before it is written, and a mismatch is fatal.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kemp import submission  # noqa: E402
from kemp.paths import RESULTS  # noqa: E402

BASE_WINDOW = (2.41, 2.69)
DONOR_WINDOW = (2.92, 3.60)
FAMILY_MEDIAN_BASE = 2.51
BASE_OK = set("DE")
DONOR_OK = set("QNSTYKR")


def parse_args(argv):
    options = {"name-prefix": "chris_sweep", "max": "5", "require-window": "both"}
    positional = []
    for item in argv:
        if item == "--dry-run":
            options["dry-run"] = "1"
        elif item.startswith("--"):
            key, _, value = item[2:].partition("=")
            options[key] = value
        else:
            positional.append(item)
    return positional, options


def read_tsv(path):
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        row = dict(zip(header, line.split("\t"), strict=False))
        for key, value in list(row.items()):
            if value == "":
                row[key] = None
            else:
                try:
                    row[key] = float(value)
                except ValueError:
                    pass
        rows.append(row)
    return rows


def contact(row, which):
    for key in (f"pinned_{which}", f"scan_{which}"):
        value = row.get(key)
        if isinstance(value, float) and value == value:
            return value
    return None


positional, options = parse_args(sys.argv[1:])
if len(positional) < 2:
    sys.exit(__doc__)
tsv_path, queries_path = Path(positional[0]), Path(positional[1])
limit = int(options["max"])
requirement = options["require-window"]
prefix = options["name-prefix"]

rows = read_tsv(tsv_path)
sequences = {r["name"]: r["sequence"] for r in json.loads(queries_path.read_text())}
positions = {
    r["name"]: (r.get("base_position"), r.get("donor_position")) for r in json.loads(queries_path.read_text())
}

candidates = []
for row in rows:
    if row.get("status") != "measured" or row.get("kind") != "design":
        continue
    if (row.get("clashes_below_2_2") or 0) > 0:
        continue
    base, donor = contact(row, "base"), contact(row, "donor")
    if base is None or donor is None:
        continue
    in_base = BASE_WINDOW[0] <= base <= BASE_WINDOW[1]
    in_donor = DONOR_WINDOW[0] <= donor <= DONOR_WINDOW[1]
    if requirement == "both" and not (in_base and in_donor):
        continue
    if requirement == "base" and not in_base:
        continue
    candidates.append((abs(base - FAMILY_MEDIAN_BASE), row, base, donor, in_base, in_donor))

candidates.sort(key=lambda item: item[0])
print(f"{len(rows)} rows -> {len(candidates)} pass the '{requirement}' window requirement")
if not candidates:
    print("Nothing to bank. Loosen --require-window to inspect near-misses, e.g. --require-window=none")
    sys.exit(0)

entries, problems = [], []
for rank, (_, row, base, donor, in_base, in_donor) in enumerate(candidates[:limit], 1):
    name = str(row["name"])
    sequence = sequences.get(name)
    base_position, donor_position = positions.get(name, (None, None))
    if not sequence or not isinstance(base_position, int) or not isinstance(donor_position, int):
        problems.append(f"{name}: missing sequence or pinned positions")
        continue
    # THE guard. A wrong index is not rejected downstream; it is silently mis-measured.
    base_residue = sequence[base_position - 1] if 1 <= base_position <= len(sequence) else "?"
    donor_residue = sequence[donor_position - 1] if 1 <= donor_position <= len(sequence) else "?"
    if base_residue not in BASE_OK:
        problems.append(f"{name}: base index {base_position} holds '{base_residue}', not D/E")
        continue
    if donor_residue not in DONOR_OK:
        problems.append(f"{name}: donor index {donor_position} holds '{donor_residue}', not Q/N/S/T/Y/K/R")
        continue
    entries.append(
        {
            "name": f"{prefix}_{rank:02d}",
            "sequence": sequence,
            "base": base_position,
            "oxy": donor_position,
            "note": (
                f"{tsv_path.parent.name}/{name}; base {base:.2f} A ({base_residue}{base_position}), "
                f"donor {donor:.2f} A ({donor_residue}{donor_position}); "
                f"window base={'in' if in_base else 'out'} donor={'in' if in_donor else 'out'}; "
                f"CA RMSD {row.get('ca_rmsd')}; iptm {row.get('iptm')}; T={row.get('temperature')}"
            ),
        }
    )
    print(
        f"  {entries[-1]['name']}: base {base:.2f} ({base_residue}{base_position})  "
        f"donor {donor:.2f} ({donor_residue}{donor_position})  "
        f"CA RMSD {row.get('ca_rmsd')}"
    )

for problem in problems:
    print(f"  REJECTED {problem}")

if not entries:
    sys.exit("No candidate survived the index check; nothing written.")

designs = [
    submission.Design(name=e["name"], sequence=e["sequence"], base=e["base"], oxy=e["oxy"]) for e in entries
]
reasons = submission.check(designs)
if reasons:
    print("\nThe offline validator rejects this set:")
    for reason in reasons:
        print(f"  - {reason}")
    sys.exit("Nothing written.")
print("\nOffline validator: all rules pass for these candidates.")

if options.get("dry-run"):
    print("--dry-run: not writing. Remove the flag to append to results/designs.jsonl")
    sys.exit(0)

target = Path(RESULTS) / "designs.jsonl"
existing = target.read_text() if target.is_file() else ""
with target.open("a") as stream:
    if existing and not existing.endswith("\n"):
        stream.write("\n")
    for entry in entries:
        stream.write(json.dumps(entry) + "\n")
print(f"appended {len(entries)} candidates to {target}")
print("Next: uv run python tools/novelty_check.sh on each, then `make submission`")
