"""Die fuenf Kriterien + Novelty-Gate, ueber ALLE Designs im Team.

Zweck: den Scorer an einer groesseren Stichprobe pruefen. Mit 11 eigenen Designs
war nicht zu sehen, ob die Kriterien ueberhaupt unterscheiden oder sich nur
gegenseitig wiederholen. Mit den Team-Designs dazu geht das.

Die Kriterien stammen wortwoertlich aus challenge.md; K1 und K2 wiegen laut
Organisatoren zusammen schwerer als alles andere, und die Terme MULTIPLIZIEREN -
eine Null an einer Stelle ist nicht durch Staerke an anderer aufzuwiegen.
"""

import glob
import json
import math
from pathlib import Path

import numpy as np
from biotite.structure.io import pdbx

CRYSTAL = {"base": (133.1, -6.7), "donor": (140.8, -10.4)}  # Winkel, Ringebene
TRIAZOLE = ("N1", "N2", "N3", "C3A", "C7A")


def ang(a, b, c):
    v1, v2 = a - b, c - b
    cos = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def oop(p, ring):
    ring = np.asarray(ring)
    ctr = ring.mean(axis=0)
    nrm = np.linalg.svd(ring - ctr)[2][2]
    v = p - ctr
    return math.degrees(math.asin(max(-1.0, min(1.0, float(np.dot(v / np.linalg.norm(v), nrm))))))


rows = []
for sm in sorted(glob.glob("/mnt/work/projects/*/results/kemp-*/summary.json")):
    d = json.loads(Path(sm).read_text())
    name = Path(sm).parts[4]
    b = d.get("boltz") or {}
    conf, ct = b.get("confidence") or {}, b.get("contacts_angstrom") or {}
    cif = next(iter(sorted(Path(sm).parent.glob("boltz/**/predictions/*/*_model_0.cif"))), None)
    if cif is None:
        continue
    at = pdbx.get_structure(pdbx.CIFFile.read(str(cif)), model=1, use_author_fields=True)
    lig = at[at.hetero & (at.element != "H")]
    prot = at[(~at.hetero) & (at.element != "H")]
    ca = prot[prot.atom_name == "CA"]
    ring = [lig[lig.atom_name == n].coord[0] for n in TRIAZOLE if len(lig[lig.atom_name == n]) == 1]

    pos = {f["original"]: f["position"] for f in (d.get("ligandmpnn") or {}).get("fixed", [])}
    r = dict(
        name=name,
        k1_base=ct.get("A127_OD2_to_6NT_N3"),
        k1_donor=ct.get("A50_NE2_to_6NT_N1"),
        k3_ipde=conf.get("complex_ipde"),
        k2=None,
        k4=None,
        ca_rmsd=b.get("backbone_ca_rmsd_from_rfd3_angstrom"),
    )

    # K2: Winkel UND Ringebene, der SCHLECHTERE entscheidet (kein Mittelwert)
    if len(ring) >= 3:
        worst = 0.0
        for lab, (res, root, cont, tgt) in (
            ("base", ("A127", "CG", "OD2", "N3")),
            ("donor", ("A50", "CD", "NE2", "N1")),
        ):
            if res not in pos:
                worst = None
                break
            sel = prot[prot.res_id == pos[res]]
            ar, ac = sel[sel.atom_name == root], sel[sel.atom_name == cont]
            al = lig[lig.atom_name == tgt]
            if len(ar) != 1 or len(ac) != 1 or len(al) != 1:
                worst = None
                break
            ra, ro = CRYSTAL[lab]
            worst = max(
                worst, abs(ang(ar.coord[0], ac.coord[0], al.coord[0]) - ra), abs(oop(ac.coord[0], ring) - ro)
            )
        r["k2"] = worst
    # K4: CA im 12-A-Umkreis der Base
    if "A127" in pos:
        s = prot[(prot.res_id == pos["A127"]) & (prot.atom_name == "OD2")]
        if len(s) == 1:
            r["k4"] = int((np.linalg.norm(ca.coord - s.coord[0], axis=1) <= 12.0).sum())
    rows.append(r)

ok = [r for r in rows if r["k1_base"] and r["k1_donor"] and r["k2"] and r["k3_ipde"] and r["k4"]]
print("=== Die fuenf Kriterien, alle Designs im Team (n=%d vollstaendig) ===\n" % len(ok))
hd = "%-24s %8s %8s %9s %8s %6s" % ("design", "K1 Basis", "K1 Donor", "K2 worst", "K3 iPDE", "K4 CA")
print(hd)
print("-" * len(hd))
for r in sorted(ok, key=lambda x: x["k1_base"] + x["k1_donor"]):
    print(
        "%-24s %8.2f %8.2f %8.0fÂ° %8.2f %6d"
        % (r["name"], r["k1_base"], r["k1_donor"], r["k2"], r["k3_ipde"], r["k4"])
    )

print("\n=== Unterscheiden die Kriterien ueberhaupt, oder wiederholen sie sich? ===")
print("    Rangkorrelation zwischen den Kriterien. Nahe +-1 = redundant, nahe 0 = unabhaengig.")


def sp(x, y):
    rx = np.argsort(np.argsort(np.asarray(x, float))).astype(float)
    ry = np.argsort(np.argsort(np.asarray(y, float))).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    den = math.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / den) if den else float("nan")


keys = [
    ("K1 Basis", "k1_base"),
    ("K1 Donor", "k1_donor"),
    ("K2 worst", "k2"),
    ("K3 iPDE", "k3_ipde"),
    ("K4 CA", "k4"),
]
print("\n  %-10s %s" % ("", "".join("%10s" % k for k, _ in keys)))
for i, (ln, lk) in enumerate(keys):
    cells = []
    for j, (_, rk) in enumerate(keys):
        cells.append("        - " if i == j else "%10.2f" % sp([r[lk] for r in ok], [r[rk] for r in ok]))
    print("  %-10s %s" % (ln, "".join(cells)))

print("\n=== Spannweite je Kriterium: diskriminiert es, oder ist es konstant? ===")
for ln, lk in keys:
    v = np.array([r[lk] for r in ok], float)
    print(
        "  %-10s min %7.2f  max %7.2f  Median %7.2f  Spanne %7.2f %s"
        % (
            ln,
            v.min(),
            v.max(),
            np.median(v),
            v.max() - v.min(),
            "" if (v.max() - v.min()) > 0.3 * abs(np.median(v)) else "<- schmal, trennt kaum",
        )
    )
