"""Turn many LigandMPNN sequences into one directory of Boltz-2 queries.

Runs ON THE CLUSTER inside env-boltz2 (needs pyyaml only).

    python build_boltz_queries.py <ligandmpnn_root> <queries_dir> <sequence.json|-> [extra_fasta ...]

<ligandmpnn_root> is scanned for */seqs/*.fa, so several temperature sweeps can be
collected in one pass. Every unique sequence becomes

    <queries_dir>/<name>.yaml      - the Boltz-2 specification
    <queries_dir>.msa/<name>.a3m  - a query-only alignment

The alignments live in a SIBLING directory, not in <queries_dir>. `boltz predict <dir>` tries
to parse every file it finds and dies on the first one it does not recognise:
"RuntimeError: Unable to parse filetype .a3m, please provide a .fasta or .yaml file."
The yaml references the alignment by absolute path, so the split costs nothing.

The query-only a3m is not a shortcut: chris-03 showed the 183 GB MMseqs2 search returns
depth 1 / nonquery_rows 0 for every de novo design, and that replacing it with the query
alone gives bit-identical Boltz-2 output (same MD5). This reproduces that file exactly and
saves ~10 min per sequence.

Writes <queries_dir>/../queries.json: the metadata for each query, so the measurement step
can report temperature and LigandMPNN scores next to the geometry.
"""

import json
import re
import sys
from pathlib import Path

import yaml

HEADER = re.compile(r"(\w+)=([^,\s]+)")


def parse_fasta(path):
    """Yield (header, sequence) pairs, skipping LigandMPNN's input-sequence record.

    The first record in a LigandMPNN .fa is the *input* backbone sequence, which carries
    `batch_size=` in its header and is not a design. Designs carry `id=`.
    """
    name, parts = None, []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if name is not None:
                yield name, "".join(parts)
            name, parts = line[1:], []
        elif line.strip():
            parts.append(line.strip())
    if name is not None:
        yield name, "".join(parts)


root = Path(sys.argv[1])
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
msa_dir = out.parent / f"{out.name}.msa"
msa_dir.mkdir(parents=True, exist_ok=True)

# The parent run's bridge/sequence.json tells us where the pinned base and donor landed in
# the designed sequence. LigandMPNN holds those positions fixed, so every sampled sequence
# shares them - which is what makes the organizers' pinned measurement reproducible here.
positions = {}
if len(sys.argv) > 3 and sys.argv[3] != "-":
    for item in json.loads(Path(sys.argv[3]).read_text())["fixed"]:
        if item["original"] == "A127":
            positions["base_position"] = item["position"]
        elif item["original"] == "A50":
            positions["donor_position"] = item["position"]
    print(f"pinned positions from {sys.argv[3]}: {positions}")

records, seen = [], {}
for fasta in sorted(root.glob("*/seqs/*.fa")):
    temperature = fasta.parent.parent.name
    for header, sequence in parse_fasta(fasta):
        fields = dict(HEADER.findall(header))
        if "id" not in fields:
            continue  # the input-sequence record, not a design
        if sequence in seen:
            seen[sequence]["duplicates"] += 1
            continue
        record = {
            "name": f"s{len(records):03d}",
            "sequence": sequence,
            "length": len(sequence),
            "source": temperature,
            "temperature": float(fields.get("T", "nan")),
            "ligandmpnn_id": fields.get("id"),
            "seed": fields.get("seed"),
            "overall_confidence": float(fields.get("overall_confidence", "nan")),
            "ligand_confidence": float(fields.get("ligand_confidence", "nan")),
            "seq_rec": float(fields.get("seq_rec", "nan")),
            "duplicates": 0,
            "kind": "design",
            **positions,
        }
        records.append(record)
        seen[sequence] = record

# Controls supplied as plain FASTA: natural enzymes folded under the SAME conditions as the
# designs. Without these the designs' numbers cannot be read, because we compare them to
# crystal distances while measuring with Boltz-2 - two different instruments.
for extra in sys.argv[4:]:
    for header, sequence in parse_fasta(Path(extra)):
        if sequence in seen:
            continue
        # A header in the SUBMISSION format - ">name base=86 oxy=52" - declares where the scorer
        # measures. Honour it: such a record is a design, and gets the scorer's pinned measurement
        # instead of the numbering-agnostic scan. The scan takes the nearest candidate atom over the
        # whole protein, so it can only read equal or SHORTER than the declared residue, and for the
        # donor it often latched onto a different Gln/Asn (job 47: s059's donor read 2.7-2.95 A by
        # scan and 3.82-4.85 A at the declared Gln52). Headers without base=/oxy= stay controls.
        declared = dict(HEADER.findall(header))
        is_design = declared.get("base", "").isdigit() and declared.get("oxy", "").isdigit()
        record = {
            "name": f"{'d' if is_design else 'c'}_{header.split()[0]}",
            "sequence": sequence,
            "length": len(sequence),
            "source": "submission" if is_design else "control",
            "temperature": float("nan"),
            "ligandmpnn_id": None,
            "seed": None,
            "overall_confidence": float("nan"),
            "ligand_confidence": float("nan"),
            "seq_rec": float("nan"),
            "duplicates": 0,
            "kind": "design" if is_design else "control",
        }
        if is_design:
            record["base_position"] = int(declared["base"])
            record["donor_position"] = int(declared["oxy"])
        records.append(record)
        seen[sequence] = record

for record in records:
    name = record["name"]
    a3m = msa_dir / f"{name}.a3m"
    a3m.write_text(f">{name}\n{record['sequence']}\n")
    specification = {
        "version": 1,
        "sequences": [
            {"protein": {"id": "A", "sequence": record["sequence"], "msa": str(a3m.resolve())}},
            {"ligand": {"id": "B", "ccd": "6NT"}},
        ],
    }
    (out / f"{name}.yaml").write_text(yaml.safe_dump(specification, sort_keys=False))

(out.parent / "queries.json").write_text(json.dumps(records, indent=2) + "\n")
designs = sum(1 for r in records if r["kind"] == "design")
controls = sum(1 for r in records if r["kind"] == "control")
collapsed = sum(r["duplicates"] for r in records)
print(f"queries: {len(records)} ({designs} designs, {controls} controls); {collapsed} duplicates collapsed")
print(f"wrote {out} (yaml), {msa_dir} (a3m) and {out.parent / 'queries.json'}")
