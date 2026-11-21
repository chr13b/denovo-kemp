"""Geometry of contacts to nitro groups.

For every nitro group found in the curated entries (see nitro_contacts.py) this writes:
  nitro_polar_geometry.csv  one row per N/O atom X within POLAR A of a nitro O (closest nitro O only)
  nitro_local_frame.csv     every heavy atom within LOCAL A of the nitro N, in the nitro's local frame

Definitions
  d_O_X        distance nitro O ... X
  ang_N_O_X    angle N-O...X at the nitro oxygen (sp2 O lone pairs lie ~120-130 deg from the N-O bond, in the nitro plane)
  ang_X        max over X's covalent heavy-atom neighbours Y of angle Y-X...O (X-side directionality proxy; NaN for water,
               ~180 = O lies along the Y-X bond extension, i.e. X lone pair/H pointing away from Y is NOT implied - see README)
  elev_deg     elevation of the O->X vector above the nitro plane (0 = in-plane, 90 = along the plane normal)
  local frame  origin = nitro N; x = along the (C/N substituent) -> N bond (away from the substituent);
               z = nitro plane normal; y = z cross x (in plane, perpendicular to the C-N axis)
Only atoms of the deposited model at their deposited coordinates are used (no crystal-symmetry mates or lattice translations)."""
import csv, os
import gemmi, numpy as np, pandas as pd

POLAR, LOCAL = 3.5, 5.0
meta = {r["pdb_id"]: r for r in csv.DictReader(open("curated.csv"))}

def v(p): return np.array([p.x, p.y, p.z])
def angle(a, b, c):  # angle at b
    u, w = a - b, c - b
    return np.degrees(np.arccos(np.clip(u @ w / (np.linalg.norm(u) * np.linalg.norm(w)), -1, 1)))

def category(res, atom, het):
    if res.is_water(): return "Water"
    if het: return "Cofactor / other ligand"
    n, a = res.name, atom.name
    if a == "N": return "Backbone N-H"
    if a in ("O", "OXT"): return "Acceptor O"
    if n in ("SER", "THR", "TYR") and a in ("OG", "OG1", "OH"): return "Ser/Thr/Tyr OH"
    if n in ("ASN", "GLN") and a in ("ND2", "NE2"): return "Asn/Gln NH2"
    if n in ("ASN", "GLN") and a in ("OD1", "OE1"): return "Acceptor O"
    if n in ("ASP", "GLU") and atom.element.name == "O": return "Acceptor O"
    if n == "HIS" and a in ("ND1", "NE2"): return "His N"
    if (n == "ARG" and a in ("NE", "NH1", "NH2")) or (n == "LYS" and a == "NZ"): return "Arg/Lys N+"
    return "Other"

def is_protein(res):
    ri = gemmi.find_tabulated_residue(res.name)
    return bool(ri and ri.is_amino_acid())

def ok(a): return a.altloc in ("\0", "A") and a.element.name not in ("H", "D")

def nitro_groups(model):
    for ch in model:
        for res in ch:
            if res.het_flag != "H" or res.is_water(): continue
            for a in res:
                if a.element.name != "N" or not ok(a): continue
                O, oth = [], []
                for b in res:
                    if b is a or not ok(b): continue
                    d = a.pos.dist(b.pos)
                    if b.element.name == "O" and d < 1.50: O.append(b)
                    elif d < 1.70: oth.append(b)
                if len(O) == 2 and len(oth) == 1: yield ch, res, a, O, oth[0]

def same_asu_atoms(ns, model, pos, radius):
    """(cra, position) for atoms of the deposited model (no symmetry mates / lattice translations) within radius of pos."""
    for m in ns.find_atoms(pos, "\0", radius=radius):
        cra = m.to_cra(model)
        if ok(cra.atom) and pos.dist(cra.atom.pos) <= radius:
            yield cra, cra.atom.pos

pol, loc = [], []
for pid, e in meta.items():
    st = gemmi.read_structure(f"structures/{pid}.cif"); st.setup_entities()
    model = st[0]
    ns = gemmi.NeighborSearch(model, st.cell, 6).populate()
    for gi, (ch, res, N, Os, C) in enumerate(nitro_groups(model), 1):
        n, o1, o2, c = v(N.pos), v(Os[0].pos), v(Os[1].pos), v(C.pos)
        ax = (n - c) / np.linalg.norm(n - c)
        nz = np.cross(o1 - n, o2 - n); nz /= np.linalg.norm(nz)
        ny = np.cross(nz, ax)
        base = dict(pdb_id=pid, family=e["category"], nitro_ligand=f"{ch.name}:{res.name}{res.seqid.num}", nitro_group=gi)
        seen = set()
        for cra, xpos in same_asu_atoms(ns, model, N.pos, LOCAL):
            r = cra.residue
            if r.seqid == res.seqid and cra.chain.name == ch.name and r.name == res.name: continue
            key = (cra.chain.name, str(r.seqid), cra.atom.serial)
            if key in seen: continue
            seen.add(key)
            x = v(xpos)
            rel = x - n
            cat = category(r, cra.atom, not is_protein(r) and not r.is_water())
            loc.append(dict(base, contact=f"{cra.chain.name}:{r.name}{r.seqid.num}", atom=cra.atom.name, element=cra.atom.element.name,
                            category=cat, d_N=np.linalg.norm(rel), lx=rel @ ax, ly=rel @ ny, lz=rel @ nz,
                            d_Omin=min(np.linalg.norm(x - o1), np.linalg.norm(x - o2))))
            if cra.atom.element.name not in ("N", "O"): continue
            dO = [np.linalg.norm(x - o1), np.linalg.norm(x - o2)]
            k = int(np.argmin(dO))
            if dO[k] > POLAR: continue
            Opos = (o1, o2)[k]
            # X-side angle from covalent heavy neighbours (excluding the nitro ligand itself)
            nbr = [v(p) for c2, p in same_asu_atoms(ns, model, xpos, 1.75)
                   if c2.atom is not cra.atom and c2.residue.name != res.name and xpos.dist(p) < 1.75]
            angX = max((angle(y, x, Opos) for y in nbr), default=np.nan) if cat != "Water" else np.nan
            w = Opos - x
            pol.append(dict(base, contact=f"{cra.chain.name}:{r.name}{r.seqid.num}", resname=r.name, resnum=r.seqid.num, atom=cra.atom.name,
                            category=cat, nitro_O=Os[k].name, d_O_X=dO[k], ang_N_O_X=angle(n, Opos, x), ang_X=angX,
                            elev_deg=np.degrees(np.arcsin(abs((-w) @ nz) / np.linalg.norm(w)))))
pd.DataFrame(pol).round(3).to_csv("nitro_polar_geometry.csv", index=False)
pd.DataFrame(loc).round(3).to_csv("nitro_local_frame.csv", index=False)
print(len(pol), "polar contacts;", len(loc), "local-frame atoms")
