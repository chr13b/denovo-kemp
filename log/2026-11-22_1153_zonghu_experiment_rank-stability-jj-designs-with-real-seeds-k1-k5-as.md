# [2026-11-22 11:53] experiment | Rank stability, JJ designs with real seeds, K1-K5 as primary (zonghu) (zonghu)

- TODO
- **What:** scored JJ's 10 RFD4-Proteina designs (`Kemp_JJ_Final`), refolded the top 5 at real Boltz seeds 1-5 (job 103); `scripts/40_score_metrics_pack.py` gained `--base_atom=od2` and the heteroatom angles A1/A4; new `scripts/42_rank_stability.py` re-ranks 198 designs under 6 variants.
- **Result:** top 8 under all variants: P1, s018, arms_98_s010, P7. JJ P3 collapses with real seeds (K5 0.05). Ranking is now sorted by K1-K5; K1-K6 (ipTM) is QC only.
- **Files:** `results/criteria/rank_stability.tsv`, `jj_final_*_k5_k6.tsv`, `results/candidates/ranking_all_k1_k6.md`.
