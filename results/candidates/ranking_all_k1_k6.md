# Gesamtranking aller Designs: gewichteter Score K1–K5 (K1–K6 nur als Kontrolle)

Mittel über je 5 Boltz-2-Seeds (echte Seeds 1–5), 198 Designs aus fünf Quellen. Sortiert nach **K1–K5** (die Kriterien der Organisatoren). K1–K6 enthält zusätzlich den ipTM-Term und dient nur der Qualitätskontrolle, ipTM ist kein Kriterium der Organisatoren. Spaltenbedeutung: `ranking_k1_k6.md`.
Berechnet mit `scripts/40_score_metrics_pack.py --target=v2`, Stand 2026-11-22. Bei den Pack-Designs s068/s042 gibt es zwei Läufe
(eigene Seeds und chris' Seeds, gleiche Sequenz), die Werte weichen durch Seed-Rauschen ab.

| # | Design | Quelle | K1 | K2 | K3 | K4 | K5 | ipTM | **K1–K5** | K1–K6 (QC) | Novelty |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 | JJ (RFD4-Proteina) | 0.94 | 0.34 | 1.00 | 0.92 | 0.98 | 0.920 | **0.757** | 0.785 | PASS |
| 2 | s018 | neue Sequenzen (zonghu) | 0.78 | 0.50 | 0.98 | 0.93 | 0.80 | 0.885 | **0.746** | 0.775 | PASS |
| 3 | arms_98_s010 | chris Replikation | 0.75 | 0.52 | 0.99 | 0.96 | 0.69 | 0.891 | **0.729** | 0.759 | PASS |
| 4 | P7 | JJ (RFD4-Proteina) | 0.54 | 0.96 | 1.00 | 0.42 | 0.99 | 0.903 | **0.706** | 0.739 | PASS |
| 5 | s068 | Pack/eigene Seeds | 0.78 | 0.27 | 1.00 | 0.93 | 0.99 | 0.942 | **0.683** | 0.718 | PASS |
| 6 | seed4_s068 | chris Replikation | 0.76 | 0.28 | 1.00 | 0.93 | 0.98 | 0.939 | **0.673** | 0.708 | PASS (gleiche Sequenz wie s068) |
| 7 | arms_98_s057 | chris Replikation | 0.63 | 0.49 | 1.00 | 0.88 | 0.60 | 0.907 | **0.659** | 0.696 | PASS |
| 8 | P9 | JJ (RFD4-Proteina) | 0.64 | 0.35 | 1.00 | 0.58 | 0.93 | 0.955 | **0.616** | 0.656 | PASS |
| 9 | P10 | JJ (RFD4-Proteina) | 0.30 | 0.89 | 1.00 | 0.78 | 0.98 | 0.938 | **0.616** | 0.655 | PASS |
| 10 | s122 | neue Sequenzen (zonghu) | 0.45 | 0.38 | 1.00 | 0.93 | 0.84 | 0.920 | **0.551** | 0.591 | PASS |
| 11 | arms_98_s060 | chris Replikation | 0.47 | 0.39 | 1.00 | 0.87 | 0.54 | 0.913 | **0.551** | 0.594 | PASS |
| 12 | s007 | neue Sequenzen (zonghu) | 0.71 | 0.23 | 0.77 | 0.88 | 0.47 | 0.801 | **0.529** | 0.557 | PASS |
| 13 | s024 | Pack (Organisatoren-Seeds) | 0.70 | 0.36 | 0.99 | 0.95 | 0.27 | 0.881 | **0.528** | 0.562 | PASS |
| 14 | arms_97_s008 | chris Replikation | 0.56 | 0.40 | 1.00 | 0.85 | 0.34 | 0.922 | **0.522** | 0.566 | PASS |
| 15 | s087 | neue Sequenzen (zonghu) | 0.52 | 0.58 | 0.97 | 0.96 | 0.22 | 0.873 | **0.507** | 0.539 | PASS |
| 16 | s042 | Pack/eigene Seeds | 0.65 | 0.17 | 0.96 | 0.94 | 0.52 | 0.883 | **0.499** | 0.545 | PASS |
| 17 | s108 | neue Sequenzen (zonghu) | 0.79 | 0.12 | 1.00 | 0.93 | 0.52 | 0.907 | **0.453** | 0.491 | nicht geprüft |
| 18 | arms_96_s069 | chris Replikation | 0.45 | 0.41 | 0.94 | 0.89 | 0.26 | 0.859 | **0.447** | 0.487 | PASS |
| 19 | arms_96_s004 | chris Replikation | 0.69 | 0.34 | 0.99 | 0.83 | 0.12 | 0.901 | **0.422** | 0.459 | PASS |
| 20 | s034 | neue Sequenzen (zonghu) | 0.50 | 0.32 | 0.92 | 0.91 | 0.14 | 0.863 | **0.400** | 0.438 | nicht geprüft |
| 21 | seed4_s069 | chris Replikation | 0.20 | 0.23 | 0.94 | 0.89 | 0.87 | 0.863 | **0.398** | 0.447 | nicht geprüft |
| 22 | os59__4BS0_A_s12__s007 | family_motifs | 0.55 | 0.08 | 0.88 | 0.88 | 0.50 | 0.838 | **0.383** | 0.431 | PASS (PDB 0.699, knapp) |
| 23 | s081 | neue Sequenzen (zonghu) | 0.33 | 0.49 | 0.99 | 0.93 | 0.16 | 0.891 | **0.356** | 0.384 | nicht geprüft |
| 24 | seed4_s042 | chris Replikation | 0.48 | 0.12 | 0.97 | 0.95 | 0.41 | 0.880 | **0.342** | 0.383 | nicht geprüft |
| 25 | s091 | neue Sequenzen (zonghu) | 0.43 | 0.10 | 0.95 | 0.92 | 0.70 | 0.862 | **0.313** | 0.361 | nicht geprüft |

## Vergleich nach Quelle (bestes Design je Quelle)

| Quelle | Bestes Design | K1–K6 | Auffälligkeit |
|---|---|---|---|
| JJ (RFD4-Proteina, eigene Pipeline) | P1 | 0.785 | beste Distanz (K1 0.94) und Konsistenz (K5 0.98); Winkel schwach (K2 0.34). P7 hat den besten Winkel (0.96), aber nur K4 0.42 |
| neue Sequenzen (zonghu, Seed4-Backbone) | s018 | 0.775 | ausgewogen: K1 0.78, K2 0.50, K5 0.80 |
| chris Replikation (Seed4-Backbone) | arms_98_s010 | 0.759 | bester Winkel unter den Seed4-Designs (K2 0.52), K5 0.69 |
| Pack / bekannte Designs (Seed4-Backbone) | s068 | 0.718 | beste Konsistenz (K5 0.99), aber Winkel schwach (K2 0.27) |
| family_motifs (chris, andere Backbones) | os59 s007 | 0.431 | Winkel praktisch nicht getroffen (K2 0.08) |

## Einordnung

- Die Top 3 (P1 0.785, s018 0.775, arms_98_s010 0.759) liegen innerhalb von 0.03. Das ist kein belastbarer Unterschied, zumal alle aus
  vielen Kandidaten ausgewählt sind und mit denselben Seeds 1–5 bewertet wurden.
- **Zwei Familien:** Die Seed4-Designs (s068, s018, arms, s024, s042) sind sich als Backbone ähnlich. JJs Designs stammen von einer
  anderen Pipeline und einem anderen Fold, das gibt Diversität für die 20 Einreichungsplätze.
- **JJ P3** ist nicht in der Liste: Mit echten Seeds bricht es ein (K5 0.05, K1–K6 0.296). JJ P2, P4, P5, P6, P8 wurden nicht mit echten Seeds neu gefaltet, weil
  sie in der ersten Runde schwach waren (K1–K6 0.01 bis 0.44 mit Diffusions-Samples).
- Die Faltung der JJ-Designs lief ohne MSA wie bei JJ. Die Seed4-Designs wurden mit einem Query-only-MSA gefaltet.
- Novelty: alle als „PASS" markierten Designs bestehen das Tor (TM ≤ 0.70, Identität zu HG ≤ 70 %). „nicht geprüft" heißt nur, dass ich es noch nicht gemessen habe.
