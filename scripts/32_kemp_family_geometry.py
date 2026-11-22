"""Download every 'kemp eliminase' PDB entry and measure the catalytic geometry across all of them.

Gives the TARGET DISTRIBUTION the organizers refer to ("crystal structures of working Kemp
eliminases"), instead of the single 4BS0 data point.
"""

import json
import math
import os
import subprocess

DEST = "/mnt/work/tools/kemp_pdb"
os.makedirs(DEST, exist_ok=True)

# 1. search
q = {
    "query": {
        "type": "group",
        "logical_operator": "and",
        "nodes": [
            {
                "type": "group",
                "label": "text",
                "logical_operator": "and",
                "nodes": [
                    {"type": "terminal", "service": "full_text", "parameters": {"value": "kemp eliminase"}}
                ],
            }
        ],
    },
    "return_type": "entry",
    "request_options": {
        "paginate": {"start": 0, "rows": 200},
        "results_content_type": ["experimental"],
        "sort": [{"sort_by": "score", "direction": "desc"}],
        "scoring_strategy": "combined",
    },
}
with open("/tmp/q2.json", "w") as fh:
    json.dump(q, fh)
raw = subprocess.run(
    [
        "curl",
        "-s",
        "--max-time",
        "90",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "--data-binary",
        "@/tmp/q2.json",
        "https://search.rcsb.org/rcsbsearch/v2/query",
    ],
    capture_output=True,
    text=True,
).stdout
ids = [r["identifier"] for r in json.loads(raw).get("result_set", [])]
print(f"kemp eliminase entries: {len(ids)}")

# 2. download
for i in ids:
    f = f"{DEST}/{i}.cif"
    if not os.path.exists(f) or os.path.getsize(f) == 0:
        subprocess.run(
            ["curl", "-sSL", "--max-time", "60", "-o", f, f"https://files.rcsb.org/download/{i}.cif"],
            capture_output=True,
        )
have = [i for i in ids if os.path.exists(f"{DEST}/{i}.cif") and os.path.getsize(f"{DEST}/{i}.cif") > 1000]
print(f"downloaded: {len(have)}")


def atoms_of(path):
    cols, out, in_loop = [], [], False
    for line in open(path, errors="ignore"):
        s = line.strip()
        if s.startswith("_atom_site."):
            cols.append(s.split(".", 1)[1])
            in_loop = True
            continue
        if in_loop and (s.startswith("ATOM") or s.startswith("HETATM")):
            f = s.split()
            if len(f) < len(cols):
                continue
            a = dict(zip(cols, f, strict=False))
            if a.get("label_alt_id", ".") not in (".", "?", "A"):
                continue
            out.append(a)
        elif in_loop and s.startswith("#"):
            in_loop = False
    return out


def d(a, b):
    return math.sqrt(sum((float(a[f"Cartn_{c}"]) - float(b[f"Cartn_{c}"])) ** 2 for c in "xyz"))


BASE_ATOMS = {"OD1", "OD2", "OE1", "OE2"}
DONOR_ATOMS = {"NE2", "ND2", "OG", "OG1", "OH", "NZ", "NH1", "NH2", "OD1"}
BASE_RES = {"ASP", "GLU"}
DONOR_RES = {"GLN", "ASN", "SER", "THR", "TYR", "LYS", "ARG"}

ligand_counts, rows = {}, []
for pid in have:
    ats = atoms_of(f"{DEST}/{pid}.cif")
    ligs = [
        a
        for a in ats
        if a.get("group_PDB") == "HETATM"
        and a.get("label_comp_id") not in ("HOH", "SO4", "GOL", "EDO", "PO4", "CL", "NA", "MG")
    ]
    for a in ligs:
        ligand_counts[a["label_comp_id"]] = ligand_counts.get(a["label_comp_id"], 0) + 1
    tsa = [a for a in ligs if a["label_comp_id"] == "6NT"]
    if not tsa:
        continue
    prot = [a for a in ats if a.get("group_PDB") == "ATOM"]
    copies = {}
    for a in tsa:
        copies.setdefault((a["auth_asym_id"], a["auth_seq_id"]), []).append(a)
    for key, lg in copies.items():
        n3 = [x for x in lg if x["label_atom_id"] == "N3"]
        n1 = [x for x in lg if x["label_atom_id"] == "N1"]
        if not n3 or not n1:
            continue
        bd = [
            (d(p, n3[0]), p)
            for p in prot
            if p["label_comp_id"] in BASE_RES and p["label_atom_id"] in BASE_ATOMS
        ]
        dd = [
            (d(p, n1[0]), p)
            for p in prot
            if p["label_comp_id"] in DONOR_RES and p["label_atom_id"] in DONOR_ATOMS
        ]
        if not bd or not dd:
            continue
        b, bp = min(bd, key=lambda t: t[0])
        o, op = min(dd, key=lambda t: t[0])
        rows.append(
            (
                pid,
                key[0],
                b,
                f"{bp['label_comp_id']}{bp['auth_seq_id']}:{bp['label_atom_id']}",
                o,
                f"{op['label_comp_id']}{op['auth_seq_id']}:{op['label_atom_id']}",
            )
        )

print("\nligands seen (top 10):", sorted(ligand_counts.items(), key=lambda x: -x[1])[:10])
print(f"\nstructures with 6NT bound: {len({r[0] for r in rows})}, ligand copies: {len(rows)}")
print(f"\n{'pdb':<6}{'ch':<4}{'base d':>8}  {'base residue':<18}{'donor d':>8}  donor residue")
print("-" * 78)
for r in sorted(rows):
    print(f"{r[0]:<6}{r[1]:<4}{r[2]:>8.2f}  {r[3]:<18}{r[4]:>8.2f}  {r[5]}")

if rows:
    bs = sorted(r[2] for r in rows)
    ds = sorted(r[4] for r in rows)

    def stats(v):
        n = len(v)
        return f"n={n}  min={v[0]:.2f}  median={v[n // 2]:.2f}  mean={sum(v) / n:.2f}  max={v[-1]:.2f}"

    print(f"\nBASE  (carboxylate O -> 6NT N3): {stats(bs)}")
    print(f"DONOR (donor atom   -> 6NT N1): {stats(ds)}")

with open("/mnt/work/tools/kemp_family_geometry.tsv", "w") as fh:
    fh.write("pdb\tchain\tbase_dist\tbase_residue\tdonor_dist\tdonor_residue\n")
    for r in sorted(rows):
        fh.write(f"{r[0]}\t{r[1]}\t{r[2]:.3f}\t{r[3]}\t{r[4]:.3f}\t{r[5]}\n")
print("\nwrote /mnt/work/tools/kemp_family_geometry.tsv")
