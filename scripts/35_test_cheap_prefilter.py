"""Gibt es einen billigen Vorfilter? Praediktoren am RFD3-Backbone gegen Boltz-Ausgang.

chris-02 forderte genau das und niemand hat es gebaut. Wir haben jetzt beschriftete
Beispiele: fuer jedes Design die RFD3-Stufe (75 s) UND den Boltz-Ausgang (23 min).

Getestet wird, ob irgendeine am RFD3-Backbone messbare Groesse den Erfolg vorhersagt.
Findet sich eine, vervielfacht sie den Durchsatz. Findet sich keine, ist auch das eine
Antwort - dann hilft nur mehr Rechenzeit.

n ist klein (ca. 11). Nur ein starker Effekt waere ueberhaupt sichtbar; alles unter
|rho| ~ 0.6 ist bei dieser Groesse nicht von Rauschen zu unterscheiden. Das steht
ausdruecklich dabei, statt Scheinpraezision zu erzeugen.
"""

import gzip
import json
from pathlib import Path

import numpy as np
from biotite.structure import annotate_sse
from biotite.structure.io import pdbx


def spearman(x, y):
    """Rangkorrelation, ohne scipy-Abhaengigkeit."""

    def rank(v):
        order = np.argsort(np.argsort(np.asarray(v, dtype=float)))
        return order.astype(float)

    rx, ry = rank(x), rank(y)
    rx -= rx.mean()
    ry -= ry.mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / d) if d else float("nan")


rows = []
for sm in sorted(Path("/mnt/work/projects").glob("zonghu_*/results/kemp-*/summary.json")):
    d = json.loads(sm.read_text())
    run = sm.parent
    rfd3 = next(iter(sorted(run.glob("rfd3/*.cif.gz"))), None)
    if rfd3 is None:
        continue
    with gzip.open(rfd3, "rt") as fh:
        at = pdbx.get_structure(pdbx.CIFFile.read(fh), model=1, use_author_fields=True)
    prot = at[(~at.hetero) & (at.element != "H")]
    ca = prot[prot.atom_name == "CA"]
    if len(ca) == 0:
        continue

    # --- Merkmale, alle am RFD3-BACKBONE messbar, also nach 75 s verfuegbar
    centre = ca.coord.mean(axis=0)
    rog = float(np.sqrt(((ca.coord - centre) ** 2).sum(axis=1).mean()))
    try:
        sse = annotate_sse(prot[prot.chain_id == prot.chain_id[0]])
        helix = float((sse == "a").mean())
        sheet = float((sse == "b").mean())
        coil = float((sse == "c").mean())
    except Exception:
        helix = sheet = coil = float("nan")

    r = d.get("rfd3") or {}
    clashes = r.get("ligand_protein_pairs_below_2_2_angstrom")
    pos = {f["original"]: f["position"] for f in (d.get("ligandmpnn") or {}).get("fixed", [])}
    burial_rfd3 = float("nan")
    if "A127" in pos:
        s = prot[(prot.res_id == pos["A127"]) & (prot.atom_name == "OD2")]
        if len(s) == 1:
            burial_rfd3 = float((np.linalg.norm(ca.coord - s.coord[0], axis=1) <= 12.0).sum())

    # --- Ausgang nach Boltz
    b = d.get("boltz") or {}
    c = b.get("confidence") or {}
    ct = b.get("contacts_angstrom") or {}
    base, don = ct.get("A127_OD2_to_6NT_N3"), ct.get("A50_NE2_to_6NT_N1")
    if base is None or don is None:
        continue
    rows.append(
        dict(
            name=sm.parts[-4],
            rog=rog,
            helix=helix,
            sheet=sheet,
            coil=coil,
            clashes=clashes if clashes is not None else -1,
            burial_rfd3=burial_rfd3,
            base=base,
            donor=don,
            ipde=c.get("complex_ipde", float("nan")),
            ca_rmsd=b.get("backbone_ca_rmsd_from_rfd3_angstrom", float("nan")),
            geo_sum=base + don,
        )
    )

print(f"n = {len(rows)} Designs mit RFD3-Backbone UND Boltz-Ausgang\n")
h = "%-22s %6s %6s %6s %6s %7s %8s | %7s %7s %7s" % (
    "design",
    "RoG",
    "helix",
    "sheet",
    "clash",
    "burial",
    "",
    "Basis",
    "Donor",
    "iPDE",
)
print(h)
print("-" * len(h))
for r in sorted(rows, key=lambda x: x["geo_sum"]):
    print(
        "%-22s %6.1f %6.2f %6.2f %6d %7.0f %8s | %7.2f %7.2f %7.2f"
        % (
            r["name"],
            r["rog"],
            r["helix"],
            r["sheet"],
            r["clashes"],
            r["burial_rfd3"],
            "",
            r["base"],
            r["donor"],
            r["ipde"],
        )
    )

print("\n=== Rangkorrelation RFD3-Merkmal  <->  Boltz-Ausgang ===")
print("    (negativ = hoeherer Wert geht mit BESSEREM, also kleinerem Abstand einher)")
feats = ["rog", "helix", "sheet", "coil", "clashes", "burial_rfd3"]
outs = ["base", "donor", "geo_sum", "ipde", "ca_rmsd"]
print("  %-14s %s" % ("merkmal", "  ".join("%8s" % o for o in outs)))
for f in feats:
    xs = [r[f] for r in rows]
    if np.all(np.isnan(xs)) or len(set(xs)) < 3:
        print("  %-14s  (konstant oder fehlend - traegt keine Information)" % f)
        continue
    cells = []
    for o in outs:
        rho = spearman(xs, [r[o] for r in rows])
        cells.append("%8.2f%s" % (rho, "*" if abs(rho) > 0.6 else " "))
    print("  %-14s %s" % (f, "  ".join(cells)))
print("\n  * = |rho| > 0.6, bei n=%d gerade noch bemerkenswert. Alles darunter ist Rauschen." % len(rows))
