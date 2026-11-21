"""For each entry in curated.csv: download the mmCIF, find nitro groups (N bonded to 2 O + 1 heavy atom)
in non-water hetero residues, and list every residue/ligand/water with an atom within CUTOFF of a nitro atom.
Crystal-symmetry contacts are excluded (image_idx != 0).
Outputs: nitro_contacts.csv (one row per nitro group x contacting residue), nitro_summary.csv (one row per entry)."""
import csv, os, sys, urllib.request
import gemmi

CUTOFF, HB = 4.0, 3.5          # vdW contact cutoff / polar (H-bond-range) cutoff, Angstrom
os.makedirs("structures", exist_ok=True)

def fetch(pid):
    p = f"structures/{pid}.cif"
    if not os.path.exists(p):
        urllib.request.urlretrieve(f"https://files.rcsb.org/download/{pid}.cif", p)
    return p

def find_nitro(model):
    """Return list of (chain, residue, N atom, [O atoms]) for nitro/nitronate groups in hetero residues."""
    out = []
    for ch in model:
        for res in ch:
            if res.het_flag != 'H' or res.is_water():
                continue
            for a in res:
                if a.element.name != 'N' or (a.altloc not in ('\0', 'A')):
                    continue
                O, other = [], []
                for b in res:
                    if b is a or b.altloc not in ('\0', 'A'):
                        continue
                    d = a.pos.dist(b.pos)
                    if b.element.name == 'O' and d < 1.50: O.append(b)
                    elif b.element.name != 'H' and d < 1.70: other.append(b)
                if len(O) == 2 and len(other) == 1:
                    out.append((ch, res, a, O))
    return out

def label(cra):
    r = cra.residue
    return f"{cra.chain.name}:{r.name}{r.seqid.num}{r.seqid.icode.strip()}"

rows, summ = [], []
for e in csv.DictReader(open("curated.csv")):
    pid = e["pdb_id"]
    try:
        st = gemmi.read_structure(fetch(pid)); st.setup_entities()
    except Exception as ex:
        summ.append([pid, e["category"], 0, f"ERROR {ex}", "", ""]); continue
    model = st[0]
    nitros = find_nitro(model)
    if not nitros:
        summ.append([pid, e["category"], 0, "no nitro group in structure", "", ""]); continue
    ns = gemmi.NeighborSearch(model, st.cell, 5).populate()
    cs = gemmi.ContactSearch(CUTOFF); cs.ignore = gemmi.ContactSearch.Ignore.SameResidue
    cs.twice = False
    contacts = cs.find_contacts(ns)
    # index nitro atoms
    nitro_of = {}   # (chain, resseq-key, atom serial) -> nitro idx
    for i, (ch, res, N, Os) in enumerate(nitros):
        for a in [N] + Os:
            nitro_of[(ch.name, str(res.seqid), a.serial)] = (i, a.name)
    per_group = {}  # (nitro idx, contact label) -> dict
    for c in contacts:
        if c.image_idx != 0: continue
        for mine, other in ((c.partner1, c.partner2), (c.partner2, c.partner1)):
            key = (mine.chain.name, str(mine.residue.seqid), mine.atom.serial)
            if key in nitro_of:
                i, nname = nitro_of[key]
                lab = label(other)
                kind = ('water' if other.residue.is_water() else
                        'protein' if gemmi.find_tabulated_residue(other.residue.name) and
                                     gemmi.find_tabulated_residue(other.residue.name).is_amino_acid() else 'ligand/other')
                g = per_group.setdefault((i, lab), dict(kind=kind, resname=other.residue.name,
                                                        resnum=other.residue.seqid.num, min=99, pair="", polar=99, ppair=""))
                d = c.dist
                if d < g['min']: g['min'], g['pair'] = d, f"{nname}...{other.atom.name}"
                if other.atom.element.name in ('N', 'O') and nname != 'N' and d < g['polar']:
                    g['polar'], g['ppair'] = d, f"{nname}...{other.atom.name}"
    for (i, lab), g in sorted(per_group.items(), key=lambda kv: (kv[0][0], kv[1]['min'])):
        ch, res, N, Os = nitros[i]
        rows.append([pid, e["category"], f"{ch.name}:{res.name}{res.seqid.num}", i + 1, g['kind'], lab, g['resname'], g['resnum'],
                     round(g['min'], 2), g['pair'], round(g['polar'], 2) if g['polar'] < HB else "", g['ppair'] if g['polar'] < HB else ""])
    # summary: protein residues H-bonding (<=HB) to nitro O across all copies
    hb = {}
    for r in rows:
        if r[0] == pid and r[4] == 'protein' and r[10] != "": hb.setdefault(f"{r[6]}{r[7]}", set()).add(r[3])
    near = {}
    for r in rows:
        if r[0] == pid and r[4] == 'protein': near.setdefault(f"{r[6]}{r[7]}", set()).add(r[3])
    summ.append([pid, e["category"], len(nitros), ";".join(sorted({f"{res.name}" for _, res, _, _ in nitros})),
                 " ".join(f"{k}(x{len(v)})" for k, v in sorted(hb.items(), key=lambda kv: int(''.join(c for c in kv[0][3:] if c.isdigit()) or 0))),
                 " ".join(f"{k}(x{len(v)})" for k, v in sorted(near.items(), key=lambda kv: int(''.join(c for c in kv[0][3:] if c.isdigit()) or 0)))])
    print(pid, len(nitros), "nitro group(s)", file=sys.stderr)

with open("nitro_contacts.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pdb_id", "category", "nitro_ligand", "nitro_group_no", "contact_kind", "contact", "contact_resname", "contact_resnum",
                f"min_dist_A(<={CUTOFF})", "closest_atom_pair", f"polar_dist_A(<={HB})", "polar_atom_pair"])
    w.writerows(rows)
with open("nitro_summary.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pdb_id", "category", "n_nitro_groups", "nitro_ligand(s)_or_note", f"protein_residues_polar<={HB}A (x=#nitro groups)", f"protein_residues_<={CUTOFF}A"])
    w.writerows(summ)
print(len(rows), "contact rows;", len(summ), "entries")
