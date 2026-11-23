"""Die Kristall-Referenzgeometrie exakt ausmessen - Abstand, Winkel UND Dihedral.

Die Organisatoren sagen: "scored against a target taken from crystal structures of
working Kemp eliminases and from textbook hydrogen-bond geometry, which agree".
Also ist der Zielwert messbar und nicht zu raten. Hier wird er gemessen und gegen
die Lehrbuchgeometrie geprueft - stimmen beide, ist der Zielwert belegt.

Neu gegenueber vorher: ein echtes DIHEDRAL. Bisher hatte ich nur eine
Ebenenabweichung per SVD. Die Organisatoren nennen ausdruecklich
"distance, angle and dihedral measurements".
"""

import math
import sys

import numpy as np
from biotite.structure.io.pdb import PDBFile

# Lehrbuch: N-H...O Wasserstoffbruecke, Schweratomabstand
TEXTBOOK_HBOND = (2.8, 3.0)


def dist(a, b):
    return float(np.linalg.norm(a - b))


def angle(a, b, c):
    v1, v2 = a - b, c - b
    cos = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def dihedral(p0, p1, p2, p3):
    """Torsion p0-p1-p2-p3 in Grad, Vorzeichen nach IUPAC."""
    b0, b1, b2 = p0 - p1, p2 - p1, p3 - p2
    b1n = b1 / np.linalg.norm(b1)
    v = b0 - np.dot(b0, b1n) * b1n
    w = b2 - np.dot(b2, b1n) * b1n
    x = float(np.dot(v, w))
    y = float(np.dot(np.cross(b1n, v), w))
    return math.degrees(math.atan2(y, x))


def plane_dev(p, ring):
    ring = np.asarray(ring)
    ctr = ring.mean(axis=0)
    nrm = np.linalg.svd(ring - ctr)[2][2]
    v = p - ctr
    return math.degrees(math.asin(max(-1.0, min(1.0, float(np.dot(v / np.linalg.norm(v), nrm))))))


at = PDBFile.read(sys.argv[1]).get_structure(model=1)
at = at[at.element != "H"]


def get(resname_or_id, name):
    if isinstance(resname_or_id, int):
        s = at[(at.res_id == resname_or_id) & (at.atom_name == name)]
    else:
        s = at[(at.res_name == resname_or_id) & (at.atom_name == name)]
    if len(s) != 1:
        raise SystemExit(f"nicht eindeutig: {resname_or_id}:{name} -> {len(s)}")
    return s.coord[0]


L = "6NT"
ring = [get(L, n) for n in ("N1", "N2", "N3", "C3A", "C7A")]
ctr = np.mean(ring, axis=0)

print("=== Kristall-Referenz aus %s ===\n" % sys.argv[1])
for lab, (rid, root, contact, tgt, nb1, nb2) in {
    "Base  Asp127 OD2...N3": (127, "CG", "OD2", "N3", "N2", "C3A"),
    "Donor Gln50  NE2...N1": (50, "CD", "NE2", "N1", "N2", "C7A"),
}.items():
    r, c = get(rid, root), get(rid, contact)
    t, a1, a2 = get(L, tgt), get(L, nb1), get(L, nb2)
    d = dist(c, t)
    print(lab)
    print(
        "  Abstand   %.3f A        %s"
        % (
            d,
            "stimmt mit Lehrbuch %.1f-%.1f ueberein" % TEXTBOOK_HBOND
            if TEXTBOOK_HBOND[0] - 0.25 <= d <= TEXTBOOK_HBOND[1] + 0.25
            else "AUSSERHALB Lehrbuch %.1f-%.1f" % TEXTBOOK_HBOND,
        )
    )
    print("  Winkel am Ringatom  %s-%s...%s   %7.1f deg" % (root, contact, tgt, angle(r, c, t)))
    print("  Anflugwinkel  %s...%s-Zentrum      %7.1f deg" % (contact, tgt, angle(c, t, ctr)))
    print(
        "  Dihedral  %s-%s-%s-%s %7.1f deg  (0/180 = in der Ringebene)"
        % (contact, tgt, nb1, nb2, dihedral(c, t, a1, a2))
    )
    print("  Ebenenabweichung per SVD           %7.1f deg  (Quervergleich)" % plane_dev(c, ring))
    print()
print(
    "Ringplanaritaet (max Abweichung der 5 Ringatome): %.3f A"
    % max(abs(np.dot(p - ctr, np.linalg.svd(np.asarray(ring) - ctr)[2][2])) for p in ring)
)
