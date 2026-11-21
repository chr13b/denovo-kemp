"""Motif table for nitro-binding sites (input for building annotated CIFs).

One *site* per entry = the nitro-bearing ligand copy with the most motif residues. Motif residues are protein residues that
  hbond  - have an N/O atom within 3.5 A of a nitro O (2.4 <= d <= 3.5; from nitro_polar_geometry.csv), or
  pi     - have an aromatic ring (F/Y/W/H) stacked on the nitro group: ring centroid 3.0-4.6 A above/below the nitro plane,
           <= 2.5 A lateral offset from the nitro N, ring normal within 40 deg of the nitro-plane normal.
Writes motif_table.csv (one row per motif residue) and motif_sites.csv (one row per site, with compact selections).
Residue numbers are author numbering of each entry; insertion codes are kept in `icode` but the polar-contact input has none."""
import csv, collections
import gemmi, numpy as np, pandas as pd

meta = {r["pdb_id"]: r for r in csv.DictReader(open("curated.csv"))}
pol = pd.read_csv("nitro_polar_geometry.csv")
pol = pol[(pol.d_O_X >= 2.4) & ~pol.category.isin(["Water", "Cofactor / other ligand"])]
RINGS = {"PHE": [["CG", "CD1", "CD2", "CE1", "CE2", "CZ"]], "TYR": [["CG", "CD1", "CD2", "CE1", "CE2", "CZ"]],
         "TRP": [["CG", "CD1", "NE1", "CE2", "CD2"], ["CD2", "CE2", "CE3", "CZ2", "CZ3", "CH2"]], "HIS": [["CG", "ND1", "CD2", "CE1", "NE2"]]}
BB = ("N", "CA", "C", "O")

def v(p): return np.array([p.x, p.y, p.z])
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

def stacked(model, nitro):
    ch, res, N, Os, C = nitro
    n, o1, o2, c = v(N.pos), v(Os[0].pos), v(Os[1].pos), v(C.pos)
    nz = np.cross(o1 - n, o2 - n); nz /= np.linalg.norm(nz)
    ax = (n - c) / np.linalg.norm(n - c)
    out = {}
    for ch2 in model:
        for r in ch2:
            if r.name not in RINGS: continue
            for ring in RINGS[r.name]:
                at = [r[nm][0] if r.find_atom(nm, "*") else None for nm in ring]
                if any(a is None for a in at): continue
                pts = np.array([v(a.pos) for a in at]); cen = pts.mean(0)
                rel = cen - n
                if np.linalg.norm(rel) > 5.5: continue
                z = abs(rel @ nz); lat = np.linalg.norm(rel - (rel @ nz) * nz)
                nrm = np.linalg.svd(pts - cen)[2][2]
                ang = np.degrees(np.arccos(min(1, abs(nrm @ nz))))
                if 3.0 <= z <= 4.6 and lat <= 2.5 and ang <= 40:
                    key = (ch2.name, r.seqid.num, r.seqid.icode.strip(), r.name)
                    if key not in out or z < out[key][0]: out[key] = (z, lat, ang)
    return out

def fix_atoms(res, kind):
    names = [a.name for a in res if ok(a)]
    if kind in ("bb_NH", "bb_O"): return [x for x in names if x in BB]
    if kind == "bb+sidechain": return names
    return [x for x in names if x not in ("N", "C", "O", "OXT")]   # side chain + CA (anchor)

rows, sites = [], []
for pid, e in meta.items():
    st = gemmi.read_structure(f"structures/{pid}.cif"); st.setup_entities(); model = st[0]
    res_ = (st.resolution or None)
    cand = collections.defaultdict(dict)       # ligand copy -> {(chain,num,icode,name): record}
    for gi, nitro in enumerate(nitro_groups(model), 1):
        ch, lig = nitro[0], nitro[1]
        lkey = f"{ch.name}:{lig.name}{lig.seqid.num}"
        d = cand[lkey]
        for _, r in pol[(pol.pdb_id == pid) & (pol.nitro_ligand == lkey) & (pol.nitro_group == gi)].iterrows():
            cch, rest = r.contact.split(":"); key = (cch, int(r.resnum), "", r.resname)
            rec = d.setdefault(key, dict(roles=set(), atoms=[], d=9, angO=np.nan, angX=np.nan, elev=np.nan, ng=gi, stack=None))
            rec["roles"].add("hbond"); rec["atoms"].append(f"{r.atom}-{r.nitro_O}")
            if r.d_O_X < rec["d"]: rec.update(d=r.d_O_X, angO=r.ang_N_O_X, angX=r.ang_X, elev=r.elev_deg, ng=gi, bb=(r.atom in ("N", "O")), bbatom=r.atom)
        for key, (z, lat, ang) in stacked(model, nitro).items():
            rec = d.setdefault(key, dict(roles=set(), atoms=[], d=9, angO=np.nan, angX=np.nan, elev=np.nan, ng=gi, stack=None))
            rec["roles"].add("pi"); rec["stack"] = (round(z, 2), round(lat, 2), round(ang, 0))
    if not cand or not any(cand.values()):
        continue
    best = max(cand, key=lambda k: (len(cand[k]), -ord(k[0])))
    chains = {c.name: c for c in model}
    srec = []
    for (cch, num, ic, rn), rec in sorted(cand[best].items(), key=lambda kv: (kv[0][0], kv[0][1])):
        r = next((x for x in chains[cch] if x.seqid.num == num and x.name == rn), None)
        if r is None: continue
        patoms = {x.split("-")[0] for x in rec["atoms"]}
        hasbb, hassc = bool(patoms & {"N", "O"}), bool(patoms - {"N", "O"}) or "pi" in rec["roles"]
        kind = "bb+sidechain" if hasbb and hassc else ("sidechain" if hassc else ("bb_NH" if "N" in patoms else "bb_O"))
        role = "+".join(sorted(rec["roles"]))
        rows.append(dict(pdb_id=pid, family=e["category"], resolution_A=res_, nitro_ligand_site=best, nitro_group=rec["ng"], chain=cch,
                         resnum=num, resname=rn, role=role, contact_type=kind, contact_atoms="; ".join(sorted(set(rec["atoms"]))),
                         d_O_X=None if rec["d"] == 9 else round(rec["d"], 2), ang_N_O_X=None if rec["d"] == 9 else round(rec["angO"], 0),
                         ang_X=None if rec["d"] == 9 or np.isnan(rec["angX"]) else round(rec["angX"], 0),
                         elev_deg=None if rec["d"] == 9 else round(rec["elev"], 0),
                         pi_z_lat_ang="" if rec["stack"] is None else "/".join(map(str, rec["stack"])),
                         suggested_fix_atoms=",".join(fix_atoms(r, kind))))
        srec.append((cch, num, rn, role, kind))
    sites.append(dict(pdb_id=pid, family=e["category"], resolution_A=res_, nitro_ligand_site=best, n_motif=len(srec),
                      n_hbond=sum("hbond" in s[3] for s in srec), n_pi=sum("pi" in s[3] for s in srec),
                      residues=" ".join(f"{s[0]}:{s[2]}{s[1]}" for s in srec),
                      selection=",".join(f"{s[0]}{s[1]}" for s in srec)))

T = pd.DataFrame(rows); S = pd.DataFrame(sites)
# representative per family: most motif residues among entries at <= 2.2 A, ties -> best resolution
S["resolution_A"] = pd.to_numeric(S.resolution_A)
ok_ = S[S.resolution_A <= 2.2].sort_values(["n_motif", "resolution_A"], ascending=[False, True])
rep = set(ok_.groupby("family").head(1).pdb_id)
S["representative"] = S.pdb_id.isin(rep); T["representative"] = T.pdb_id.isin(rep)
T.to_csv("motif_table.csv", index=False); S.to_csv("motif_sites.csv", index=False)
print(len(T), "motif residues;", len(S), "sites;", len(rep), "representatives")
print(S[S.representative][["pdb_id", "family", "resolution_A", "nitro_ligand_site", "n_hbond", "n_pi", "residues"]].to_string())
