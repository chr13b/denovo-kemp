"""Ein kombinierter Score aus den fuenf Kriterien - MULTIPLIKATIV, wie vorgegeben.

challenge.md: "Geometry dominates scoring and the terms multiply; distances have an
optimum, and too short is punished harder than too long."

Daraus folgt die Bauform:
  * jedes Kriterium -> Teilscore in [0,1]
  * Produkt, nicht Summe: eine Null ist durch nichts aufzuwiegen
  * K1 asymmetrisch um das H-Brueckenoptimum, zu kurz haerter bestraft
  * K5 FEHLT noch -> wird NICHT stillschweigend als 1.0 gesetzt, sondern
    separat ausgewiesen, damit der Score nicht besser aussieht als die Datenlage

Novelty ist ein GATE, kein Term: ueber der Grenze wird gar nicht erst gewertet.
"""

import json
import math
import sys
from pathlib import Path

D_OPT, D_SOFT, D_HARD = 2.9, 3.5, 6.0  # H-Bruecke: Optimum, weich, aus
TM_GATE, ID_GATE = 0.70, 70.0


def k1_score(d):
    """Asymmetrisch: zu kurz ist schlimmer als zu lang (sterischer Konflikt)."""
    if d is None:
        return None
    if d < D_OPT:  # zu kurz: steiler Abfall
        return max(0.0, 1.0 - 2.5 * (D_OPT - d) / D_OPT)
    if d <= D_SOFT:
        return 1.0
    return max(0.0, math.exp(-(((d - D_SOFT) / (D_HARD - D_SOFT)) ** 2)))


def k2_score(dev):
    """Winkelabweichung in Grad; 30 Grad gilt als halb so gut."""
    return None if dev is None else max(0.0, math.exp(-((dev / 42.0) ** 2)))


def k3_score(ipde):
    """iPDE, kleiner ist besser. 1.4 ist das beobachtete Beste, 5+ ist Schrott."""
    return None if ipde is None else max(0.0, min(1.0, (5.0 - ipde) / (5.0 - 1.4)))


def k4_score(n):
    """CA im 12-A-Umkreis; saettigt, mehr als ~50 bringt nichts."""
    return None if n is None else max(0.0, min(1.0, (n - 20.0) / 30.0))


rows = json.loads(Path(sys.argv[1]).read_text())
tm = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else {}

print("=== Kombinierter Score, multiplikativ. K5 fehlt noch und ist ausgewiesen. ===\n")
hd = "%-22s %6s %6s %6s %6s %6s %8s  %s" % (
    "design",
    "K1b",
    "K1d",
    "K2",
    "K3",
    "K4",
    "PRODUKT",
    "Novelty-Gate",
)
print(hd)
print("-" * len(hd))

out = []
for r in rows:
    parts = {
        "K1b": k1_score(r.get("k1_base")),
        "K1d": k1_score(r.get("k1_donor")),
        "K2": k2_score(r.get("k2")),
        "K3": k3_score(r.get("k3_ipde")),
        "K4": k4_score(r.get("k4")),
    }
    if any(v is None for v in parts.values()):
        continue
    prod = 1.0
    for v in parts.values():
        prod *= v
    t = tm.get(r["name"])
    gate = (
        "nicht geprueft" if t is None else ("FAELLT DURCH TM=%.3f" % t if t > TM_GATE else "OK (TM %.3f)" % t)
    )
    out.append((prod, r["name"], parts, gate, t))

for prod, name, p, gate, _t in sorted(out, key=lambda x: -x[0]):
    print(
        "%-22s %6.3f %6.3f %6.3f %6.3f %6.3f %8.4f  %s"
        % (name, p["K1b"], p["K1d"], p["K2"], p["K3"], p["K4"], prod, gate)
    )

print("\n=== Was den Score begrenzt: der kleinste Faktor je Design ===")
for prod, name, p, _gate, _t in sorted(out, key=lambda x: -x[0])[:6]:
    worst = min(p, key=p.get)
    print("  %-22s Produkt %.4f, gebremst von %s (%.3f)" % (name, prod, worst, p[worst]))

elig = [o for o in out if o[4] is not None and o[4] <= TM_GATE]
print("\n=== Bestes Design, das das Novelty-Gate besteht ===")
if elig:
    prod, name, p, gate, t = max(elig, key=lambda x: x[0])
    print("  %s  Produkt %.4f  TM %.3f" % (name, prod, t))
print(
    "\nDurch das Gate gefallen: %s" % ", ".join(o[1] for o in out if o[4] is not None and o[4] > TM_GATE)
    or "  keines"
)
