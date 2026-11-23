# Ranking der besten Designs: gewichteter Score K1–K6

Mittel über je 5 Boltz-2-Seeds, 193 Designs insgesamt (Pack, family_motifs, chris' Replikation, eigene neue Sequenzen).
Berechnet mit `scripts/40_score_metrics_pack.py --target=v2` (Zielgeometrie 7K4U), Stand 2026-11-22.

| # | Design | K1 | K2 | K3 | K4 | K5 | ipTM | K6 | K1–K5 | **K1–K6** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | new:s018 | 0.78 | 0.50 | 0.98 | 0.93 | 0.80 | 0.885 | 1.00 | 0.746 | **0.775** |
| 2 | chris:arms_98_s010 | 0.75 | 0.52 | 0.99 | 0.96 | 0.69 | 0.891 | 1.00 | 0.729 | 0.759 |
| 3 | s068 (eigene Seeds) | 0.78 | 0.27 | 1.00 | 0.93 | 0.99 | 0.942 | 1.00 | 0.683 | 0.718 |
| 4 | chris:seed4_s068 | 0.76 | 0.28 | 1.00 | 0.93 | 0.98 | 0.939 | 1.00 | 0.673 | 0.708 |
| 5 | chris:arms_98_s057 | 0.63 | 0.49 | 1.00 | 0.88 | 0.60 | 0.907 | 1.00 | 0.659 | 0.696 |
| 6 | chris:arms_98_s060 | 0.47 | 0.39 | 1.00 | 0.87 | 0.54 | 0.913 | 1.00 | 0.551 | 0.594 |
| 7 | new:s122 | 0.45 | 0.38 | 1.00 | 0.93 | 0.84 | 0.920 | 1.00 | 0.551 | 0.591 |
| 8 | chris:arms_97_s008 | 0.56 | 0.40 | 1.00 | 0.85 | 0.34 | 0.922 | 1.00 | 0.522 | 0.566 |
| 9 | s024 (Pack) | 0.70 | 0.36 | 0.99 | 0.95 | 0.27 | 0.881 | 1.00 | 0.528 | 0.562 |
| 10 | new:s007 | 0.71 | 0.23 | 0.77 | 0.88 | 0.47 | 0.801 | 0.81 | 0.529 | 0.557 |
| 11 | s042 (eigene Seeds) | 0.65 | 0.17 | 0.96 | 0.94 | 0.52 | 0.883 | 1.00 | 0.499 | 0.545 |
| 12 | new:s087 | 0.52 | 0.58 | 0.97 | 0.96 | 0.22 | 0.873 | 1.00 | 0.507 | 0.539 |
| 13 | new:s108 | 0.79 | 0.12 | 1.00 | 0.93 | 0.52 | 0.907 | 1.00 | 0.453 | 0.491 |
| 14 | chris:arms_96_s069 | 0.45 | 0.41 | 0.94 | 0.89 | 0.26 | 0.859 | 0.99 | 0.447 | 0.487 |
| 15 | chris:arms_96_s004 | 0.69 | 0.34 | 0.99 | 0.83 | 0.12 | 0.901 | 1.00 | 0.422 | 0.459 |

## Bedeutung der Spalten

Alle Teil-Scores liegen zwischen 0 (schlecht) und 1 (ideal). K1–K4 und ipTM werden pro Seed gemessen und dann über die
5 Seeds gemittelt. K5 gibt es nur einmal pro Design.

| Spalte | Name | Was sie misst | Wann gut |
|---|---|---|---|
| **Design** | | Herkunft: `new:` = meine neuen Sequenzen auf dem Seed4-Backbone (Job 101/102), `chris:` = chris' Replikation (`chris_autopilot`), `fm:` = family_motifs, ohne Präfix = Pack-Designs | |
| **K1** | Distanz | Abstand der zwei katalytischen Kontakte: Base (Asp86 zu N3 des Liganden, Ziel 2.535 Å) und Donor (Gln52 zu N1, Ziel 3.197 Å). Gaußkurve um das Ziel, zu kurz wird härter bestraft als zu lang. Es zählt der schlechtere der beiden Kontakte. | nahe 1 |
| **K2** | Winkel | Anflugwinkel: Abweichung des Kontakts vom idealen Winkel und von der Ringebene des Liganden, jeweils für Base und Donor. Es zählt die größte Abweichung, Score = exp(−(Abweichung/35°)²). 24° ergibt etwa 0.6, 50° etwa 0.13. | über 0.5 |
| **K3** | iPDE | Vorhergesagter Fehler der Protein-Ligand-Schnittstelle (`complex_ipde`) von Boltz-2. 1 bei iPDE = 1 Å, fällt darüber ab. Das Modell sagt damit, wie sicher es sich bei der Position des Liganden ist, nicht ob die Chemie stimmt. | nahe 1 |
| **K4** | Burial | Wie tief die Base vergraben ist: Anzahl der Cα-Atome innerhalb von 12 Å, (n − 20)/30 auf 0 bis 1 begrenzt. | nahe 1 (50 oder mehr Nachbarn) |
| **K5** | Konsistenz | Wie stabil die Pose über die 5 Seeds ist: größte Standardabweichung der beiden Kontaktdistanzen über die Seeds, Score = exp(−(Std/0.75 Å)²). Ein Design, das in einem Seed einbricht, wird hier bestraft. | über 0.5 |
| **ipTM** | | Rohwert (0 bis 1) der Boltz-2-Schnittstellensicherheit zwischen Protein und Ligand, Mittel über die Seeds. Baseline der Referenz-Pipeline: 0.8372. | über 0.8372 |
| **K6** | ipTM-Score | 1.0, wenn der ipTM die Baseline erreicht oder schlägt. Darunter exp(−((0.8372 − ipTM)/0.1)²). Gewicht 0.15. Die Form der Kurve und das Gewicht sind meine Wahl. | 1.0 |
| **K1–K5** | | Gewichtetes geometrisches Mittel aus K1 bis K5 mit den Gewichten K1 0.33, K2 0.22, K3, K4, K5 je 0.15. Mittel der 5 Seed-Scores des Designs. | über 0.5 ist stark |
| **K1–K6** | | Dasselbe mit ipTM als sechstem Term (Gewicht 0.15), normiert auf die Summe der Gewichte. **Das ist der Sortierschlüssel.** Nicht direkt mit K1–K5 vergleichbar, weil ein Term von 1.0 das Mittel anhebt. | über 0.5 ist stark |

## Hinweise

- Novelty (Backbone-TM ≤ 0.7, Sequenzidentität ≤ 70 %) ist ein Tor und kein Teil des Scores. Geprüft sind die Top-Designs
  `new:s018`, `new:s122`, `new:s007`, `new:s087` und `chris:arms_*` (alle bestanden, TM zur PDB 0.54–0.57, Identität zu HG 33–37 %).
- Kontakte sind bei allen gezeigten Designs auf Asp86 und Gln52 festgelegt (deklarierte Positionen).
- Die Werte sind Mittel einer einzelnen Rechnung mit den Seeds 1 bis 5 und aus vielen Kandidaten ausgewählt. Das beste von vielen
  ist teils Glück, eine unabhängige Wiederholung mit anderen Seeds ist nötig.
- Quellen: `scripts/40_score_metrics_pack.py` und `kemp.scoring` (`src/kemp/scoring.py`).
