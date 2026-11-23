"""Novelty, Teil 1: Sequenzidentitaet unserer Designs gegen HG3 und HG3.17.

challenge.md: "Novelty | backbone TM-score <= 0.7 ... AND sequence <= 70 % identity".
Das ist ein GATE, kein Score - ein Design darueber qualifiziert nicht.

Groesstes Risiko: unsere Theozyme stammen aus 7K4U, also HG3. Baut RFD3 etwas
HG3-aehnliches, faellt es durch. Hier die direkte paarweise Pruefung, ohne Cluster.

Globales Alignment (Needleman-Wunsch, BLOSUM-frei, einfache Match/Mismatch-Kosten)
reicht: wir suchen keine feine Homologie, sondern "ist das praktisch dasselbe Protein".
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] if "__file__" in dir() else Path(".")


def read_fasta(p: Path) -> str:
    return "".join(
        ln.strip()
        for ln in p.read_text(encoding="utf-8-sig").splitlines()
        if ln.strip() and not ln.startswith(">")
    )


def identity(a: str, b: str) -> tuple[float, int, int]:
    """Globales Alignment, Identitaet bezogen auf die kuerzere Sequenz.

    Linearer Speicher ueber zwei Zeilen; 300x300 ist winzig.
    """
    n, m = len(a), len(b)
    GAP = -1
    # nur Score noetig, Rueckverfolgung ueber zweite Matrix waere teuer -> wir
    # zaehlen Treffer ueber eine volle DP mit Backtrace, da n,m <= 400 ist das ok
    score = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = GAP * i
    for j in range(1, m + 1):
        score[0][j] = GAP * j
    for i in range(1, n + 1):
        ai = a[i - 1]
        row, prow = score[i], score[i - 1]
        for j in range(1, m + 1):
            row[j] = max(prow[j - 1] + (1 if ai == b[j - 1] else -1), prow[j] + GAP, row[j - 1] + GAP)
    # Backtrace
    i, j, matches, alen = n, m, 0, 0
    while i > 0 and j > 0:
        if score[i][j] == score[i - 1][j - 1] + (1 if a[i - 1] == b[j - 1] else -1):
            matches += a[i - 1] == b[j - 1]
            alen += 1
            i, j = i - 1, j - 1
        elif score[i][j] == score[i - 1][j] + GAP:
            i -= 1
            alen += 1
        else:
            j -= 1
            alen += 1
    alen += i + j
    return 100.0 * matches / min(n, m), matches, alen


refs = {}
base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/affinity")
for name, f in (
    ("HG3", "hg3.fasta"),
    ("HG3.17", "hg3_17.fasta"),
    ("HG3.7", "hg3_7.fasta"),
    ("Lysozym P00698", "lysozyme_P00698.fasta"),
):
    p = base / f
    if p.exists():
        refs[name] = read_fasta(p)

designs = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else {}
print("NOVELTY-GATE: Sequenzidentitaet <= 70 % erforderlich\n")
print("%-24s %-16s %8s %s" % ("design", "gegen", "Identitaet", "Gate"))
print("-" * 70)
worst = {}
for dname, seq in designs.items():
    for rname, rseq in refs.items():
        pid, m, al = identity(seq, rseq)
        flag = "OK" if pid <= 70 else "FAELLT DURCH"
        if pid > worst.get(dname, (0, ""))[0]:
            worst[dname] = (pid, rname)
        print("%-24s %-16s %7.1f %%  %s" % (dname, rname, pid, flag))
print("\n--- schlechtester Fall je Design ---")
for d, (pid, r) in sorted(worst.items(), key=lambda x: -x[1][0]):
    print("  %-24s %5.1f %% gegen %-16s %s" % (d, pid, r, "OK" if pid <= 70 else "FAELLT DURCH"))
