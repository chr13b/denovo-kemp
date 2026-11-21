"""Shared helpers for the Kemp theozyme generator (pure python + numpy; no gemmi/pandas needed)."""
import math, os, re, csv, shlex
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
KEMP = os.path.join(ROOT, "kemp_eliminase")
NITRO = os.path.join(ROOT, "nitro_enzymes")
ALIGNED = os.path.join(KEMP, "structures", "aligned_on_substrate")

AA = {"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL",
      "HID","HIE","HIP","HSD","HSE","HSP","CYX","CYM","ASH","GLH","LYN","MSE"}
HISN = {"HID": "HIS", "HIE": "HIS", "HIP": "HIS", "HSD": "HIS", "HSE": "HIS", "HSP": "HIS"}
BB = ("N", "CA", "C", "O")
# canonical TSA labels; per-ligand atom names (same maps as kemp_eliminase/theozyme/align_full_structures.py)
CORE = ["N1", "N2", "N3", "C3A", "C7A", "C4", "C5", "C6", "C7"]
TSA_MAP = {
    "6NT": {k: k for k in CORE + ["NO1"]}, "3NY": {k: k for k in CORE + ["NO1"]},
    "0CU": dict(zip(CORE, ["NAG", "NAE", "NAF", "CAJ", "CAK", "CAD", "CAH", "CAC", "CAI"])),
    "0CT": dict(zip(CORE, ["NAG", "NAE", "NAF", "CAH", "CAI", "CAC", "CAA", "CAB", "CAD"])),
    "VWF": dict(zip(CORE + ["NO1"], ["NAG", "NAH", "NAI", "CAJ", "CAF", "CAK", "CAC", "CAD", "CAE", "CAB"])),
}
AR_RINGS = {"PHE": [["CG", "CD1", "CE1", "CZ", "CE2", "CD2"]], "TYR": [["CG", "CD1", "CE1", "CZ", "CE2", "CD2"]],
            "TRP": [["CD2", "CE2", "CZ2", "CH2", "CZ3", "CE3"], ["CG", "CD1", "NE1", "CE2", "CD2"]],
            "HIS": [["CG", "ND1", "CE1", "NE2", "CD2"]]}

def unit(v):
    n = np.linalg.norm(v); return v / n if n else v
def angle(a, b, c):   # angle at b, degrees
    u, v = unit(a - b), unit(c - b); return math.degrees(math.acos(max(-1, min(1, float(u @ v)))))
def dihedral(a, b, c, d):
    b0, b1, b2 = a - b, c - b, d - c
    b1 = unit(b1); v = b0 - (b0 @ b1) * b1; w = b2 - (b2 @ b1) * b1
    x = float(v @ w); y = float(np.cross(b1, v) @ w); return math.degrees(math.atan2(y, x))
def ring_frame(pts):
    c = pts.mean(0); n = np.linalg.svd(pts - c)[2][2]; return c, unit(n)
def kabsch(P, Q):
    """rotation R and translation t minimising |R P + t - Q|; returns R, t, rmsd"""
    Pc, Qc = P.mean(0), Q.mean(0); H = (P - Pc).T @ (Q - Qc)
    U, S, Vt = np.linalg.svd(H); d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T; t = Qc - R @ Pc
    return R, t, float(np.sqrt(((P @ R.T + t - Q) ** 2).sum() / len(P)))

def parse_pdb(path):
    atoms = []
    for l in open(path):
        if l.startswith(("ATOM", "HETATM")):
            res = l[17:20].strip()
            atoms.append(dict(name=l[12:16].strip(), res=HISN.get(res, res), raw=res, chain=l[21], num=int(l[22:26]),
                              el=(l[76:78].strip() or l[12:16].strip()[0]).upper(), xyz=np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])])))
    return atoms

def read_cif_atoms(path):
    """minimal mmCIF atom_site reader -> list of dicts (first model, altloc ' '/A, no H)"""
    cols, rows, inloop, hdr = [], [], False, []
    txt = open(path).read().split("\n")
    i = 0
    while i < len(txt):
        if txt[i].startswith("loop_"):
            j = i + 1; hdr = []
            while j < len(txt) and txt[j].startswith("_"): hdr.append(txt[j].strip()); j += 1
            if hdr and hdr[0].startswith("_atom_site."):
                idx = {h.split(".", 1)[1]: k for k, h in enumerate(hdr)}
                while j < len(txt) and txt[j] and not txt[j].startswith(("loop_", "#", "_")):
                    f = shlex.split(txt[j]) if ("'" in txt[j] or '"' in txt[j]) else txt[j].split()
                    if len(f) >= len(hdr):
                        if f[idx["pdbx_PDB_model_num"]] == "1" and f[idx["type_symbol"]] not in ("H", "D") and f[idx["label_alt_id"]] in (".", "?", "A"):
                            rows.append(dict(name=f[idx["label_atom_id"]], res=HISN.get(f[idx["label_comp_id"]], f[idx["label_comp_id"]]), raw=f[idx["label_comp_id"]],
                                             chain=f[idx["auth_asym_id"]], num=int(f[idx["auth_seq_id"]]), el=f[idx["type_symbol"]].upper(), het=f[idx["group_PDB"]] == "HETATM",
                                             xyz=np.array([float(f[idx["Cartn_x"]]), float(f[idx["Cartn_y"]]), float(f[idx["Cartn_z"]])])))
                    j += 1
                return rows
            i = j
        else: i += 1
    return rows

def residues(atoms):
    out = {}
    for a in atoms: out.setdefault((a["chain"], a["num"], a["res"]), []).append(a)
    return out

def write_pdb(path, blocks, remarks=()):
    """blocks: list of (chain, resnum, resname, hetero, [(name, element, xyz), ...])"""
    ser = 1; L = [f"REMARK {r}" for r in remarks]
    for ch, num, rn, het, ats in blocks:
        for nm, el, x in ats:
            nm_f = (" " + nm).ljust(4) if len(nm) < 4 else nm
            L.append(f'{"HETATM" if het else "ATOM  "}{ser:5d} {nm_f} {rn:>3} {ch}{num:4d}    {x[0]:8.3f}{x[1]:8.3f}{x[2]:8.3f}  1.00  0.00          {el:>2}')
            ser += 1
    L.append("END"); open(path, "w").write("\n".join(L) + "\n")
