"""Align full structures on the substrate / transition-state-analog (TSA) frame with PyMOL.

Run from kemp_eliminase/:   pymol -cq theozyme/align_full_structures.py

Reference frame: 7K4Q chain A, 6NT (HG3 + 6-nitrobenzotriazole, 1.28 A).
Fit atoms (labels follow 6NT/3NY): N1 N2 N3 C3A C7A C4 C5 C6 C7 (+ nitro N "NO1" where present).
Chemical correspondence, substrate -> TSA: C3(H) -> N3, N2 -> N2, O1 -> N1, C3a -> C3A, C7a -> C7A, nitro on C5.
The reactive centre (substrate C3-H / TSA N3-H) is the site the catalytic base contacts.

direct/       core-tier structures with a bound TSA (or modelled substrate): fitted on the ligand atoms
extended/     extended-tier (mmCIF-only) structures with a bound TSA, same fit as direct/ (NMR entries: model 1)
transferred/  ligand-free structures: protein-superposed onto an already-fitted homolog, so the
              substrate frame is inherited and less exact (see alignment_summary.csv)
Only the ligand-binding chain + its ligand are written. Sites with <8 shell residues (likely
crystal-contact ligands) are skipped.
"""
import csv, math, os
from pymol import cmd

ROOT = os.getcwd()
OUT = os.path.join(ROOT, "structures", "aligned_on_substrate")
for d in ("direct", "extended", "transferred"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

CORE = ["N1", "N2", "N3", "C3A", "C7A", "C4", "C5", "C6", "C7"]
NITRO = "NO1"
MAP = {  # label -> atom name in the ligand
    "6NT": {k: k for k in CORE + [NITRO]},
    "3NY": {k: k for k in CORE + [NITRO]},
    # 0CU: 5,7-dichloro (N3 := NAF, the N the base contacts)
    "0CU": dict(zip(CORE, ["NAG", "NAE", "NAF", "CAJ", "CAK", "CAD", "CAH", "CAC", "CAI"])),
    # 0CT: unsubstituted, symmetric ring; N3 := NAF, the N the base contacts in 3UZJ
    "0CT": dict(zip(CORE, ["NAG", "NAE", "NAF", "CAH", "CAI", "CAC", "CAA", "CAB", "CAD"])),
    # VWF: 5-cyanobenzotriazole; ring labelled by the nitrile on C5 (CAB = nitrile C -> "NO1" slot)
    "VWF": dict(zip(CORE + [NITRO], ["NAG", "NAH", "NAI", "CAJ", "CAF", "CAK", "CAC", "CAD", "CAE", "CAB"])),
}
REF = ("7K4Q", "A", "6NT", "401")
ACID = {"ASP": ("OD1", "OD2"), "GLU": ("OE1", "OE2")}


def xyz_of(sel):
    m = cmd.get_model(sel)
    return [a.coord for a in m.atom]


def nearest_base(obj, n3_xyz):
    """closest Asp/Glu carboxylate O to a point; returns (label, dist)"""
    best = ("-", 99.0)
    for a in cmd.get_model(f"{obj} and polymer.protein and resn ASP+GLU and name OD1+OD2+OE1+OE2").atom:
        d = math.dist(a.coord, n3_xyz)
        if d < best[1]:
            best = (f"{a.resn}{a.resi}{a.chain}", d)
    return best


def substrate_map(obj, resn="MOL"):
    """label -> atom index for 5-nitro-1,2-benzisoxazole, from bond topology (heavy atoms)"""
    m = cmd.get_model(f"{obj} and resn {resn} and not hydro")
    adj = {i: set() for i in range(len(m.atom))}
    for b in m.bond:
        i, j = b.index
        adj[i].add(j); adj[j].add(i)
    el = [a.symbol for a in m.atom]
    O1 = [i for i in adj if el[i] == "O" and len(adj[i]) == 2][0]
    n2 = [j for j in adj[O1] if el[j] == "N"][0]
    c7a = [j for j in adj[O1] if el[j] == "C"][0]
    c3 = [j for j in adj[n2] if el[j] == "C"][0]
    c3a = [j for j in adj[c3] if el[j] == "C" and j in adj[c7a]][0]
    c4 = [j for j in adj[c3a] if el[j] == "C" and j not in (c3, c7a)][0]
    c7 = [j for j in adj[c7a] if el[j] == "C" and j not in (c3a, O1)][0]
    c5 = [j for j in adj[c4] if el[j] == "C" and j != c3a][0]
    c6 = [j for j in adj[c7] if el[j] == "C" and j != c7a][0]
    nit = [j for j in adj[c5] if el[j] == "N"]
    assert nit, "nitro group not on C5 - mapping would be inconsistent"
    idx = lambda i: m.atom[i].index
    return {"N1": idx(O1), "N2": idx(n2), "N3": idx(c3), "C3A": idx(c3a), "C7A": idx(c7a),
            "C4": idx(c4), "C5": idx(c5), "C6": idx(c6), "C7": idx(c7), NITRO: idx(nit[0])}


def sel_for(obj, labels, mapping, lig_sel):
    """list of (label, selection) for ligand atoms"""
    out = {}
    for k in labels:
        if k not in mapping:
            continue
        v = mapping[k]
        out[k] = f"{obj} and index {v}" if isinstance(v, int) else f"{lig_sel} and name {v}"
    return out


def fit(obj, mapping, lig_sel, ref_sel):
    mob = sel_for(obj, CORE + [NITRO], mapping, lig_sel)
    labs = [k for k in CORE + [NITRO] if k in mob and k in ref_sel]
    args = []
    for k in labs:
        args += [mob[k], ref_sel[k]]
    return cmd.pair_fit(*args), len(labs)


def load_clean(name, path, keep):
    cmd.load(path, "_tmp")
    cmd.remove("_tmp and polymer and not (alt ''+A)")   # ligands handled by fix_alt (some are only altloc B/C)
    cmd.remove("_tmp and hydro")
    cmd.create(name, f"_tmp and ({keep})", source_state=1, target_state=1)
    cmd.delete("_tmp")


def fix_alt(lig):
    """keep only the first alternate conformer of a ligand copy (A, else B, C ...)"""
    alts = sorted({a.alt for a in cmd.get_model(lig).atom if a.alt})
    if alts:
        cmd.remove(f"{lig} and not (alt ''+{alts[0]})")


# ---------------- sites to align (from extract_theozyme.py output)
sites, seen = [], set()
with open(os.path.join(ROOT, "theozyme", "extracted", "theozyme_summary.csv")) as f:
    for r in csv.DictReader(f):
        if int(r["n_shell_res"]) >= 8 and r["pdb"] not in seen:
            seen.add(r["pdb"]); sites.append(r)
rows = []

# ---------------- reference
rpdb, rch, rres, rnum = REF
rname = f"{rpdb}_{rch}"
load_clean(rname, os.path.join(ROOT, "structures", "core", f"{rpdb}.pdb"),
           f"chain {rch} and (polymer.protein or (resn {rres} and resi {rnum}))")
rlig = f"{rname} and resn {rres} and resi {rnum}"
fix_alt(rlig)
ref_sel = sel_for(rname, CORE + [NITRO], MAP[rres], rlig)
n3_ref = xyz_of(ref_sel["N3"])[0]
base = nearest_base(rname, n3_ref)
rows.append([rpdb, rch, rres, "direct", "reference", 0.0, len(CORE) + 1, base[0], round(base[1], 2), "-"])
cmd.save(os.path.join(OUT, "direct", f"{rname}.pdb"), rname)
fitted = {rpdb: rname}

# ---------------- direct fits
for r in sites:
    pdb, tsa, tid = r["pdb"], r["tsa"], r["tsa_id"]
    if pdb == rpdb:
        continue
    ch, num = tid[0], tid[1:]
    name = f"{pdb}_{ch}"
    load_clean(name, os.path.join(ROOT, "structures", "core", f"{pdb}.pdb"),
               f"chain {ch} and (polymer.protein or (resn {tsa} and resi {num}))")
    lig = f"{name} and resn {tsa} and resi {num}"
    fix_alt(lig)
    rms, n = fit(name, MAP[tsa], lig, ref_sel)
    n3 = xyz_of(sel_for(name, ["N3"], MAP[tsa], lig)["N3"])[0]
    b = nearest_base(name, n3)
    cmd.save(os.path.join(OUT, "direct", f"{name}.pdb"), name)
    fitted[pdb] = name
    rows.append([pdb, ch, tsa, "direct", f"ligand fit ({n} atoms)", round(rms, 3), n, b[0], round(b[1], 2), "-"])

# ---------------- Zenodo substrate-bound Des27 / Des27.7 (real substrate, modelled pose)
zdir = os.path.join(ROOT, "code", "zenodo_14563437", "Classical_MD_Simulations",
                    "Classical_MD_Simulations", "Starting_Structures")
for zname, zfile in (("Des27.7_sub", "Des27.7_liganded.pdb"), ("Des27_sub", "Des27_liganded.pdb")):
    load_clean(zname, os.path.join(zdir, zfile), "polymer.protein or resn MOL")
    sm = substrate_map(zname)
    rms, n = fit(zname, sm, f"{zname} and resn MOL", ref_sel)
    n3 = xyz_of(sel_for(zname, ["N3"], sm, "")["N3"])[0]
    b = nearest_base(zname, n3)
    cmd.save(os.path.join(OUT, "direct", f"{zname}.pdb"), zname)
    fitted[zname] = zname
    rows.append([zname, "-", "MOL (5-nitrobenzisoxazole)", "direct", f"substrate fit ({n} atoms)", round(rms, 3), n,
                 b[0], round(b[1], 2), "MD starting model (Listov 2025 Zenodo), modelled pose"])

# ---------------- extended tier: every mmCIF in structures/extended that contains a TSA
import glob
TSA_RES = "+".join(MAP)
for cif in sorted(glob.glob(os.path.join(ROOT, "structures", "extended", "*.cif"))):
    pdb = os.path.basename(cif)[:-4]
    cmd.load(cif, "_scan")
    copies, seen_c = [], set()
    for a in cmd.get_model(f"_scan and resn {TSA_RES} and not hydro").atom:
        k = (a.chain, a.resi, a.resn)
        if k in seen_c:
            continue
        seen_c.add(k)
        cmd.select("_sh", f"byres(_scan and polymer.protein within 4.5 of (_scan and chain {a.chain} and resi {a.resi} and resn {a.resn}))")
        copies.append((cmd.count_atoms("_sh and name CA"), k))
    cmd.delete("_scan"); cmd.delete("_sh")
    good = [c for c in copies if c[0] >= 8]
    if not good:
        continue
    _, (ch, num, tsa) = good[0]
    name = f"{pdb}_{ch}"
    load_clean(name, cif, f"chain {ch} and (polymer.protein or (resn {tsa} and resi {num}))")
    lig = f"{name} and resn {tsa} and resi {num}"
    fix_alt(lig)
    rms, n = fit(name, MAP[tsa], lig, ref_sel)
    n3 = xyz_of(sel_for(name, ["N3"], MAP[tsa], lig)["N3"])[0]
    b = nearest_base(name, n3)
    cmd.save(os.path.join(OUT, "extended", f"{name}.pdb"), name)
    fitted[pdb] = name
    rows.append([pdb, ch, tsa, "direct (extended)", f"ligand fit ({n} atoms)", round(rms, 3), n, b[0], round(b[1], 2),
                 f"{len(copies)} ligand copies in entry; used {tsa} {ch}{num}"])

# ---------------- transferred (ligand-free) structures
TRANSFER = [  # apo, holo object it is superposed onto, method
    ("3NPV", "3Q2D_A", "align"), ("3UXA", "3UXD_A", "align"), ("3NYZ", "3NZ1_A", "align"),
    ("3O2L", "3NYD_A", "align"), ("9U01", "9TZD_A", "align"),
    ("9HVB", "Des27.7_sub", "cealign"), ("9HVG", "Des27.7_sub", "cealign"), ("9HVH", "Des27.7_sub", "cealign"),
]
for apo, holo, how in TRANSFER:
    name = f"{apo}_A"
    load_clean(name, os.path.join(ROOT, "structures", "core", f"{apo}.pdb"), "chain A and polymer.protein")
    if how == "align":
        res = cmd.align(f"{name} and name CA", f"{holo} and polymer.protein and name CA")
        rms, n = res[0], res[1]
    else:
        res = cmd.cealign(f"{holo} and polymer.protein and name CA", f"{name} and name CA")
        rms, n = res["RMSD"], res["alignment_length"]
    # distance from this structure's own base to the holo's substrate/TSA N3
    holo_n3 = (xyz_of(f"{holo} and index {substrate_map(holo)['N3']}")[0] if holo.endswith("_sub")
               else None)
    if holo_n3 is None:
        hch = holo.split("_")[1]
        hr = next(x for x in rows if f"{x[0]}_{x[1]}" == holo)
        holo_n3 = xyz_of(sel_for(holo, ["N3"], MAP[hr[2]], f"{holo} and resn {hr[2]}")["N3"])[0]
    b = nearest_base(name, holo_n3)
    cmd.save(os.path.join(OUT, "transferred", f"{name}.pdb"), name)
    rows.append([apo, "A", "-", "transferred", f"{how} onto {holo}", round(rms, 3), n, b[0], round(b[1], 2),
                 "frame inherited from homolog; check base-to-N3 distance"])

with open(os.path.join(OUT, "alignment_summary.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pdb", "chain", "ligand", "kind", "method", "rmsd_A (ligand atoms or protein CA)",
                "n_atoms", "nearest_Asp/Glu", "its_O_to_N3_A", "note"])
    w.writerows(rows)

# ---------------- session
cmd.hide("everything")
cmd.show("cartoon", "polymer.protein")
cmd.show("sticks", "organic")
cmd.set("cartoon_transparency", 0.5)
cmd.util.cbc()
cmd.zoom(rlig)
cmd.save(os.path.join(OUT, "aligned_on_substrate.pse"))
print("wrote", len(rows), "aligned structures to", OUT)
