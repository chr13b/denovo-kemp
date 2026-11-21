# zonghu-03: Trp-Flexibilität und die Dyad-Geometrie

- **Owner:** zonghu
- **Date:** 2026-11-21
- **Status:** done: supported — das starre Indol zerstört den Donor; freies Trp bringt ihn zurück
- **Question:** Warum bekommen unsere Designs im Boltz-2-Cofold immer nur **Basis ODER Donor**,
  nie beides? Und hilft es, Trp44 flexibel zu lassen statt es starr zu fixieren?
- **Why it matters:** Geometrie dominiert die Wertung und die Terme multiplizieren sich
  ([challenge.md](../challenge.md)). Ein Design, das nur einen der beiden Kontakte trifft, ist
  wertlos. Wenn die Ursache eine Überbestimmung unseres eigenen Motivs ist, kostet die Korrektur
  nichts — sie ist eine Zeile in `Kemp.json`.
- **Script + config:** `/mnt/work/projects/zonghu_stage/setup_vA.sh`, Diagnose mit
  `diagnose.py` (ebenda). Filter: [../design-filters.md](../design-filters.md).
- **Runs:** Cluster-Jobs `62–66` (starres Indol), `72–74` (Variante A, freies Trp)

## Befund 1: das Dyad ist in **jedem** Design zu weit

Im Kristall 7K4U sind OD2 (Base) und NE2 (Donor) **5.47 Å** auseinander. Gemessen über alle
fertigen Cofolds, inklusive chris' Läufen:

| Design | OD2–NE2 | Basis | Donor |
|---|---|---|---|
| chris_s4 | **7.16** | 3.32 | 3.75 |
| zonghu_g10_s3 | 7.25 | 2.27 | 8.78 |
| zonghu_g10_s5 | 7.38 | 4.03 | 9.21 |
| chris_s3 | 7.41 | 8.33 | 3.08 |
| zonghu_g10_s2 | 10.13 | 4.06 | 11.76 |
| chris_s5 | 14.13 | 14.88 | 15.83 |
| zonghu_vA_s1 | 17.10 | 13.21 | 5.48 |
| chris_s2 | 18.72 | 21.92 | 18.86 |
| zonghu_trpopt_s1 | 31.10 | 11.99 | 26.49 |

**Kein einziges Design kommt unter 7.1 Å.** Das erklärt das Entweder-oder direkt: 6NT ist starr,
seine beiden Akzeptoratome N1 und N3 liegen nur ~2.2 Å auseinander. Sitzen die Proteinreste
7.4 statt 5.5 Å auseinander, lässt sich nur noch einer davon auf H-Brücken-Abstand bringen.

**Wo es bricht:** RFD3 hält das Dyad exakt — OD2 und NE2 gehören zu `select_fixed_atoms` und
`fixed_pair_distance_max_deviation` ist 0.016 Å. Im RFD3-Backbone sind es also 5.47 Å **per
Konstruktion**. Das Dyad geht erst beim **Rückfalten in Boltz-2** verloren. Mehr RFD3-Sampling
kann das nicht beheben.

## Befund 2: das starre Indol zerstört den Donor

| Motiv-Definition | Donor-Werte (Å) |
|---|---|
| Trp44 mit ganzem Indol fixiert (9 Atome) | 8.78 · 9.21 · 11.76 |
| Trp44 mit 6-Ring fixiert (job 7) | 26.49 |
| **Trp44 in `unindex`, Koordinaten frei** | **5.48 · 3.00 · 7.26** |
| Trp44 gar nicht im Motiv (chris) | 2.94 · 3.08 · 3.75 |

Sauber getrennt über unabhängige Scaffolds hinweg. Mehr Constraint hat die Geometrie **nicht**
stabilisiert, sondern das Gegenteil bewirkt: das überbestimmte aktive Zentrum zwingt RFD3 in
Backbones, die Boltz-2 beim Rückfalten in Richtung natürlicher Geometrie relaxiert — und der
Donor ist der Teil, der dabei nachgibt.

n = 3 gegen n = 3, also eine starke Vermutung, kein Beweis.

## Befund 3: das beste Design des Projekts

**`zonghu_vA_s2` (Job 73)** — freies Trp, `select_buried` auf A127:

```
Basis 3.65 Å   Donor 3.00 Å   CA-RMSD 1.56 Å   pLDDT 86.1   ipTM 0.769   0 Clashes
```

**Vier von fünf Gates bestanden**, scheitert einzig an der Basis — um **0.05 Å**. Zum ersten Mal
sind Basis und Donor **gleichzeitig** auf H-Brücken-Abstand. Besserer Donor als der bisherige
Teambestwert chris_s4 (3.00 gegen 3.75), sauber gefaltet.

Annotierte Struktur: `/mnt/work/projects/zonghu_stage/export/design_vA_s2.pdb` (+ `.pml`).
Katalytische Reste dort: **ASP41** (Base), **GLN139** (Donor), **TRP147** (π-Stacking).
Das freie Trp hat mit **pLDDT 68.3** die mit Abstand niedrigste Konfidenz der drei — erwartbar,
da es nicht mehr fixiert wird, aber ein Hinweis, dass seine Platzierung unsicher bleibt.

**Die Basis-Schwelle wurde nicht verschoben**, um dieses Design bestehen zu lassen. 2.4–3.6 Å
stammt aus den gemessenen 2.5–2.6 Å echter Kemp-Eliminasen (Broom et al., alle sechs HG-Varianten).

## Befund 4: `min_lig_dist` in Gate 1 ist wertlos

Alle drei Variante-A-Läufe gaben exakt **2.55 Å** — es ist der fixierte Asp-Kontakt aus dem
Theozym, nicht ein Ergebnis. Dieselbe Lehre wie [chris-02](chris-02_seed-sweep-boltz-vs-rfd3-geometry.md):
**RFD3-Abstände sind ein Input.** In Gate 1 trägt nur die Clash-Zahl Information.

## Verdict und nächste Schritte

1. **Trp44 nicht mehr starr fixieren.** `unindex` ja, `select_fixed_atoms` nein. Kostenlos.
2. **Dyad-Abstand OD2–NE2 als Metrik aufnehmen** — trennt empirisch besser als die Einzelkontakte
   (≤ 7.4 Å bei allen brauchbaren, > 10 Å bei allen kaputten).
3. **Mehrere Sequenzen pro Backbone.** Bis hierher erzeugte die Pipeline genau **eine**
   (`--number_of_batches 1`), obwohl der Standard 8–16 ist. Umgesetzt in `setup_ms.sh` mit einer
   Auswahlstufe, die `kemp.fa` wieder auf die von `prepare_queries.py` erwartete Form bringt.
   Läuft als `zonghu_ms_s1–3`.
4. **`vA_s2` novelty-prüfen** (TM ≤ 0.7, Identität ≤ 70 %) — ohne GPU möglich, und es ist der
   erste echte Kandidat des Projekts.
