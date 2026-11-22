"""INFORMATIVE Metriken. Gehen NICHT in den Score ein und werden NICHT gewichtet.

Bewusst ohne Urteil: dieses Modul gibt Zahlen aus, keine Bestanden/Durchgefallen.
Die Organisatoren werten diese Groessen nicht, sie sind aber chemisch relevant
und kosten Millisekunden. Wer sie zum Ranken benutzt, erfindet ein Kriterium.

Drei Blocks:

1. LADUNGSUMGEBUNG auf beiden Seiten - Base (Asp127) UND H-Brueckendonor (Gln50).
   Gezaehlt wird pro RESIDUUM, nicht pro Atom: ein Aspartat ist eine Ladung, nicht
   zwei. Arg/Lys = +1, Asp/Glu = -1, His separat, weil bei pH 7 grenzwertig.

2. PI-SYSTEM am Liganden, allgemein. Nicht auf Trp eingeschraenkt - manche Designs
   enthalten an der Stelle gar kein Tryptophan, und LigandMPNN setzt dort oft von
   sich aus Phe, Tyr oder His hin. Gesucht wird der naechste aromatische Ring
   ueberhaupt.

3. H-BRUECKEN AN DIE NITROGRUPPE. Im 6NT sind das O11 und O21 am NO1. Die
   Nitrogruppe zieht Elektronendichte ab und hilft, die entstehende negative
   Ladung zu delokalisieren; eine H-Bruecke dorthin ist eine echte zusaetzliche
   Stabilisierung, die kein gewertetes Kriterium erfasst.
"""

import glob
import json
import math
from pathlib import Path

import numpy as np
from biotite.structure.io import pdbx

BENZO = ("C4", "C5", "C6", "C7", "C3A", "C7A")
NITRO_O = ("O11", "O21")

# aromatische Ringe, allgemein - nicht nur Trp
AROMATIC = {
    "TRP": ("CG", "CD1", "CD2", "NE1", "CE2", "CE3", "CZ2", "CZ3", "CH2"),
    "PHE": ("CG", "CD1", "CD2", "CE1", "CE2", "CZ"),
    "TYR": ("CG", "CD1", "CD2", "CE1", "CE2", "CZ"),
    "HIS": ("CG", "ND1", "CD2", "CE1", "NE2"),
}
# formale Ladung bei pH 7, pro Residuum
CHARGED = {
    "ARG": (+1, ("NE", "NH1", "NH2")),
    "LYS": (+1, ("NZ",)),
    "ASP": (-1, ("OD1", "OD2")),
    "GLU": (-1, ("OE1", "OE2")),
    "HIS": (0, ("ND1", "NE2")),
}
# Schweratome, die ein H tragen und eine Bruecke donieren koennen
DONOR_ATOMS = {"N", "NE", "NH1", "NH2", "NZ", "NE1", "ND1", "NE2", "ND2", "OG", "OG1", "OH", "SG"}
R_ELEC, R_HBOND = 6.0, 3.5


def plane(coords):
    c = np.asarray(coords)
    return np.linalg.svd(c - c.mean(axis=0))[2][2], c.mean(axis=0)


def charge_env(prot, centre_coords, exclude_resid):
    """Ladungen und H-Brueckendonoren im Umkreis, pro Residuum gezaehlt."""
    pos = neg = his = don = 0
    details = []
    for rid in sorted(set(prot.res_id)):
        if rid == exclude_resid:
            continue
        res = prot[prot.res_id == rid]
        rn = str(res.res_name[0])
        if rn in CHARGED:
            q, names = CHARGED[rn]
            pts = [a.coord for a in res if a.atom_name in names]
            if pts:
                dmin = min(min(float(np.linalg.norm(p - c)) for c in centre_coords) for p in pts)
                if dmin <= R_ELEC:
                    if q > 0:
                        pos += 1
                    elif q < 0:
                        neg += 1
                    else:
                        his += 1
                    details.append("%s%d %.1f" % (rn, rid, dmin))
        for a in res:
            if a.atom_name in DONOR_ATOMS:
                if min(float(np.linalg.norm(a.coord - c)) for c in centre_coords) <= R_HBOND:
                    don += 1
    return {"pos": pos, "neg": neg, "his": his, "net": pos - neg, "hbond_donors": don, "nearby": details[:4]}


rows = []
for sm in sorted(glob.glob("/mnt/work/projects/*/results/kemp-*/summary.json")):
    d = json.load(open(sm))
    name = Path(sm).parts[4]
    cif = next(iter(sorted(Path(sm).parent.glob("boltz/**/predictions/*/*_model_0.cif"))), None)
    if cif is None:
        continue
    at = pdbx.get_structure(pdbx.CIFFile.read(str(cif)), model=1, use_author_fields=True)
    lig = at[at.hetero & (at.element != "H")]
    prot = at[(~at.hetero) & (at.element != "H")]
    pos_map = {f["original"]: f["position"] for f in (d.get("ligandmpnn") or {}).get("fixed", [])}
    if "A127" not in pos_map or "A50" not in pos_map:
        continue
    benzo = [lig[lig.atom_name == n].coord[0] for n in BENZO if len(lig[lig.atom_name == n]) == 1]
    if len(benzo) < 6:
        continue
    lig_n, lig_c = plane(benzo)

    # --- 2. naechstes Pi-System, beliebiger Aromat
    stack = None
    for rid in sorted(set(prot.res_id)):
        res = prot[prot.res_id == rid]
        names = AROMATIC.get(str(res.res_name[0]))
        if not names:
            continue
        pts = [res[res.atom_name == n].coord[0] for n in names if len(res[res.atom_name == n]) == 1]
        if len(pts) < 5:
            continue
        n_r, c_r = plane(pts)
        dd = float(np.linalg.norm(c_r - lig_c))
        if stack is None or dd < stack["d"]:
            stack = {
                "res": "%s%d" % (res.res_name[0], rid),
                "d": dd,
                "inter": math.degrees(math.acos(max(0.0, min(1.0, abs(float(np.dot(n_r, lig_n))))))),
                "at_motif": rid == pos_map.get("A44"),
            }

    # --- 1. Ladungsumgebung, beide Seiten
    bres = prot[prot.res_id == pos_map["A127"]]
    dres = prot[prot.res_id == pos_map["A50"]]
    base_pts = [
        bres[bres.atom_name == n].coord[0]
        for n in ("OD1", "OD2", "OE1", "OE2")
        if len(bres[bres.atom_name == n]) == 1
    ]
    don_pts = [
        dres[dres.atom_name == n].coord[0]
        for n in ("NE2", "OE1", "ND2", "OD1", "OG", "OG1", "OH")
        if len(dres[dres.atom_name == n]) == 1
    ]
    if not base_pts or not don_pts:
        continue

    # --- 3. H-Bruecken an die Nitrogruppe
    nitro = [lig[lig.atom_name == n].coord[0] for n in NITRO_O if len(lig[lig.atom_name == n]) == 1]
    nh = []
    if nitro:
        for rid in sorted(set(prot.res_id)):
            res = prot[prot.res_id == rid]
            for a in res:
                if a.atom_name not in DONOR_ATOMS:
                    continue
                dmin = min(float(np.linalg.norm(a.coord - o)) for o in nitro)
                if dmin <= R_HBOND:
                    nh.append("%s%d:%s %.2f" % (res.res_name[0], rid, a.atom_name, dmin))

    rows.append(
        dict(
            name=name,
            stack=stack,
            base=charge_env(prot, base_pts, pos_map["A127"]),
            donor=charge_env(prot, don_pts, pos_map["A50"]),
            nitro_hbonds=nh,
            base_res=str(bres.res_name[0]),
            donor_res=str(dres.res_name[0]),
        )
    )

print("### INFORMATIVE METRIKEN - gehen NICHT in den Score ein, keine Gewichtung")
print()
print("=== 1. Ladungsumgebung, 6 A, pro Residuum (Arg/Lys +1, Asp/Glu -1, His separat) ===")
print()
print("  %-22s %-24s %-24s" % ("design", "--- Base-Seite ---", "--- Donor-Seite ---"))
print(
    "  %-22s %5s %5s %5s %6s %5s %5s %5s %6s"
    % ("", "pos", "neg", "His", "netto", "pos", "neg", "His", "netto")
)
print("  " + "-" * 70)
for r in sorted(rows, key=lambda x: x["base"]["net"]):
    b, dn = r["base"], r["donor"]
    print(
        "  %-22s %5d %5d %5d %+6d %5d %5d %5d %+6d"
        % (r["name"], b["pos"], b["neg"], b["his"], b["net"], dn["pos"], dn["neg"], dn["his"], dn["net"])
    )

print()
print("=== 2. Naechstes Pi-System am Benzolring des Liganden (beliebiger Aromat) ===")
print()
print("  %-22s %-10s %9s %9s  %s" % ("design", "Rest", "Abstand", "Winkel", "am Motiv-Platz"))
print("  " + "-" * 66)
for r in sorted(rows, key=lambda x: x["stack"]["d"] if x["stack"] else 99):
    s = r["stack"]
    if s:
        print(
            "  %-22s %-10s %7.2f A %8.0f°  %s"
            % (r["name"], s["res"], s["d"], s["inter"], "ja" if s["at_motif"] else "nein")
        )

print()
print("=== 3. H-Bruecken an die Nitrogruppe (O11/O21, Donor-Schweratom <= 3.5 A) ===")
print()
for r in sorted(rows, key=lambda x: -len(x["nitro_hbonds"])):
    print(
        "  %-22s %d   %s"
        % (r["name"], len(r["nitro_hbonds"]), ", ".join(r["nitro_hbonds"]) if r["nitro_hbonds"] else "-")
    )

json.dump(rows, open("/mnt/work/projects/zonghu_stage/diagnostics.json", "w"), indent=1, default=float)
print("\ngeschrieben: diagnostics.json")
