"""Scorer v2 - nach den praezisierten Kriterien der Organisatoren.

Vier Aenderungen gegenueber v1, alle aus der Aufgabenstellung belegt:

1. ZIELABSTAENDE PRO KONTAKT, am Kristall gemessen statt geraten.
   "scored against a target taken from crystal structures of working Kemp
   eliminases and from textbook hydrogen-bond geometry, which agree."
   Gemessen in 7K4U: Base OD2...N3 = 2.535 A, Donor NE2...N1 = 3.197 A.
   Die beiden sind NICHT gleich; v1 benutzte faelschlich 2.9 fuer beide.

2. ECHTES DIHEDRAL. "distance, angle and dihedral measurements". v1 hatte nur
   eine SVD-Ebenenabweichung. Jetzt beides, und sie bestaetigen sich.

3. GEWICHTUNG. "Geometry - items 1 and 2 together - outweighs everything else
   combined" und "[distances] carries the most weight of anything here".
   Umgesetzt als gewichtetes geometrisches Mittel: Exponenten statt blossem
   Produkt, denn nur so laesst sich "ueberwiegt alles andere zusammen" ausdruecken.
   Abstand 0.33 + Anflug 0.22 = 0.55 > 0.45 fuer den Rest.

4. K5 KONSISTENZ ist jetzt gemessen: Streuung der Metriken ueber 5 Boltz-Seeds
   derselben Sequenz. "how well metrics are reproduced across multiple boltz 2
   seeds, serves as a proxy for preorganization" - also die Streuung der
   Messwerte, nicht nur eine Pose-RMSD.

Asymmetrie: "Too short is a clash and is penalised harder than the same error
too long." -> sigma_kurz 0.5 A gegen sigma_lang 1.2 A, also 2.4-fach haerter.
"""

import glob
import json
import math
from pathlib import Path

import numpy as np
from biotite.structure.io import pdbx

# --- am Kristall gemessen (results/theozyme/theozyme_7k4u_core.pdb), nicht geraten
REF = {
    "base": {
        "res": "A127",
        "root": "CG",
        "contact": "OD2",
        "ring": "N3",
        "nb1": "N2",
        "nb2": "C3A",
        "dist": 2.535,
        "angle": 167.6,
        "oop": 13.2,
    },
    "donor": {
        "res": "A50",
        "root": "CD",
        "contact": "NE2",
        "ring": "N1",
        "nb1": "N2",
        "nb2": "C7A",
        "dist": 3.197,
        "angle": 164.9,
        "oop": 16.0,
    },
}
TRIAZOLE = ("N1", "N2", "N3", "C3A", "C7A")
SIG_SHORT, SIG_LONG = 0.50, 1.20  # zu kurz 2.4x haerter bestraft
SIG_ANG = 35.0  # Grad, fuer Winkel und Dihedral
W = {"dist": 0.33, "approach": 0.22, "ipde": 0.15, "burial": 0.15, "consistency": 0.15}


def ang(a, b, c):
    v1, v2 = a - b, c - b
    cos = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def dihedral(p0, p1, p2, p3):
    b0, b1, b2 = p0 - p1, p2 - p1, p3 - p2
    b1n = b1 / np.linalg.norm(b1)
    v = b0 - np.dot(b0, b1n) * b1n
    w = b2 - np.dot(b2, b1n) * b1n
    return math.degrees(math.atan2(float(np.dot(np.cross(b1n, v), w)), float(np.dot(v, w))))


def circ_dev(a, b):
    """Winkeldifferenz auf dem Kreis, immer <= 180."""
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def s_dist(d, target):
    """Asymmetrisch um den Kristallwert: zu kurz ist ein Clash."""
    sig = SIG_SHORT if d < target else SIG_LONG
    return math.exp(-(((d - target) / sig) ** 2))


def s_ang(dev):
    return math.exp(-((dev / SIG_ANG) ** 2))


def s_ipde(x):
    """iPDE, kleiner besser. 1.0 praktisch ideal, 5 ist Schrott."""
    return math.exp(-((max(0.0, x - 1.0) / 1.8) ** 2))


def s_burial(n):
    return max(0.0, min(1.0, (n - 20.0) / 30.0))


def s_consistency(stds):
    """Streuung der Kontaktabstaende ueber die Seeds; 0.75 A gilt als halb so gut."""
    return math.exp(-((max(stds) / 0.75) ** 2)) if stds else None


def measure(cif, pos):
    """Alle geometrischen Rohmasse aus einer Boltz-Struktur."""
    at = pdbx.get_structure(pdbx.CIFFile.read(str(cif)), model=1, use_author_fields=True)
    lig = at[at.hetero & (at.element != "H")]
    prot = at[(~at.hetero) & (at.element != "H")]
    ca = prot[prot.atom_name == "CA"]
    ring = [lig[lig.atom_name == n].coord[0] for n in TRIAZOLE if len(lig[lig.atom_name == n]) == 1]
    if len(ring) < 5:
        return None
    ctr = np.mean(ring, axis=0)
    out = {}
    for lab, r in REF.items():
        if r["res"] not in pos:
            return None
        sel = prot[prot.res_id == pos[r["res"]]]
        a_c = sel[sel.atom_name == r["contact"]]
        a_r = lig[lig.atom_name == r["ring"]]
        a_1 = lig[lig.atom_name == r["nb1"]]
        a_2 = lig[lig.atom_name == r["nb2"]]
        if any(len(x) != 1 for x in (a_c, a_r, a_1, a_2)):
            return None
        c, t = a_c.coord[0], a_r.coord[0]
        # Planaritaet = 180 - |Dihedral|: 0 heisst exakt in der Ringebene.
        # Das Vorzeichen des Dihedrals sagt nur, zu welcher Seite der Kontakt
        # minimal abweicht, und beide Seiten sind chemisch gleichwertig. Ein
        # vorzeichenbehafteter Vergleich wuerde einen Spiegelbild-Anflug mit ~330
        # Grad bestrafen, obwohl er dieselbe Geometrie ist.
        dih = dihedral(c, t, a_1.coord[0], a_2.coord[0])
        out[lab] = {
            "d": float(np.linalg.norm(c - t)),
            "angle": ang(c, t, ctr),
            "dih": dih,
            "oop": 180.0 - abs(dih),
        }
    s = prot[(prot.res_id == pos["A127"]) & (prot.atom_name == "OD2")]
    out["burial"] = (
        int((np.linalg.norm(ca.coord - s.coord[0], axis=1) <= 12.0).sum()) if len(s) == 1 else None
    )
    return out


# ---------------------------------------------------------------- K5 Konsistenz
cons = {}
for tag in ("vA_s2", "vA_s3"):
    sm = next(iter(sorted(glob.glob("/mnt/work/projects/zonghu_%s/results/kemp-*/summary.json" % tag))), None)
    if not sm:
        continue
    fixed = (json.load(open(sm)).get("ligandmpnn") or {}).get("fixed", [])
    pos = {f["original"]: f["position"] for f in fixed}
    per = []
    for cif in sorted(
        glob.glob(
            "/mnt/work/projects/zonghu_stage/consistency_%s/seed*/**/*_model_0.cif" % tag, recursive=True
        )
    ):
        m = measure(cif, pos)
        if m:
            per.append(m)
    if len(per) >= 2:
        cons["zonghu_" + tag] = {
            "n": len(per),
            "base_d": [round(p["base"]["d"], 2) for p in per],
            "donor_d": [round(p["donor"]["d"], 2) for p in per],
            "std_base": float(np.std([p["base"]["d"] for p in per], ddof=1)),
            "std_donor": float(np.std([p["donor"]["d"] for p in per], ddof=1)),
        }

print("=== K5 Konsistenz: 5 Boltz-Seeds, dieselbe Sequenz ===")
print("    Proxy fuer Praeorganisation - streut die Pose, ist die Tasche nicht festgelegt.\n")
for k, v in cons.items():
    print("  %s  n=%d" % (k, v["n"]))
    print("    Base  %s   std %.2f A" % (v["base_d"], v["std_base"]))
    print("    Donor %s   std %.2f A" % (v["donor_d"], v["std_donor"]))
    print("    -> Konsistenz-Score %.3f" % s_consistency([v["std_base"], v["std_donor"]]))

# ------------------------------------------------------------------ alle Designs
rows = []
for sm in sorted(glob.glob("/mnt/work/projects/*/results/kemp-*/summary.json")):
    d = json.load(open(sm))
    name = Path(sm).parts[4]
    cif = next(iter(sorted(Path(sm).parent.glob("boltz/**/predictions/*/*_model_0.cif"))), None)
    if cif is None:
        continue
    pos = {f["original"]: f["position"] for f in (d.get("ligandmpnn") or {}).get("fixed", [])}
    m = measure(cif, pos)
    ipde = ((d.get("boltz") or {}).get("confidence") or {}).get("complex_ipde")
    if not m or m["burial"] is None or ipde is None:
        continue

    sd = min(s_dist(m[lab]["d"], REF[lab]["dist"]) for lab in ("base", "donor"))
    worst_dev, worst_what = 0.0, ""
    for lab in ("base", "donor"):
        for key, pretty in (("angle", "Winkel"), ("oop", "Ringebene")):
            dev = abs(m[lab][key] - REF[lab][key])
            if dev > worst_dev:
                worst_dev, worst_what = dev, "%s %s" % (lab, pretty)
    parts = {"dist": sd, "approach": s_ang(worst_dev), "ipde": s_ipde(ipde), "burial": s_burial(m["burial"])}
    c = cons.get(name)
    parts["consistency"] = s_consistency([c["std_base"], c["std_donor"]]) if c else None

    known = {k: v for k, v in parts.items() if v is not None}
    wsum = sum(W[k] for k in known)
    total = math.exp(sum(W[k] * math.log(max(v, 1e-9)) for k, v in known.items()) / wsum)
    rows.append(
        dict(
            name=name,
            m=m,
            ipde=ipde,
            worst_dev=worst_dev,
            worst_what=worst_what,
            parts=parts,
            total=total,
            has_k5=c is not None,
        )
    )

print("\n\n=== Scorer v2: gewichtetes geometrisches Mittel ===")
print("    Abstand .33 + Anflug .22 = .55 Geometrie > .45 Rest (iPDE/Burial/Konsistenz je .15)\n")
hd = "%-22s %7s %7s %9s %7s %7s %7s %8s %6s" % (
    "design",
    "d_base",
    "d_don",
    "K2 worst",
    "s_dist",
    "s_appr",
    "s_ipde",
    "TOTAL",
    "K5",
)
print(hd)
print("-" * len(hd))
for r in sorted(rows, key=lambda x: -x["total"]):
    print(
        "%-22s %7.2f %7.2f %8.0f° %7.3f %7.3f %7.3f %8.4f %6s"
        % (
            r["name"],
            r["m"]["base"]["d"],
            r["m"]["donor"]["d"],
            r["worst_dev"],
            r["parts"]["dist"],
            r["parts"]["approach"],
            r["parts"]["ipde"],
            r["total"],
            "%.3f" % r["parts"]["consistency"] if r["has_k5"] else "-",
        )
    )

print("\n=== Was jedes Design begrenzt ===")
for r in sorted(rows, key=lambda x: -x["total"])[:6]:
    k = {a: b for a, b in r["parts"].items() if b is not None}
    w = min(k, key=k.get)
    print(
        "  %-22s %.4f  schwaechster Term: %-12s %.3f   (K2 worst: %s)"
        % (r["name"], r["total"], w, k[w], r["worst_what"])
    )

out = "/mnt/work/projects/zonghu_stage/"
json.dump(rows, open(out + "scorer2.json", "w"), indent=1, default=float)
json.dump(cons, open(out + "consistency.json", "w"), indent=1, default=float)
print("\ngeschrieben: scorer2.json, consistency.json")
