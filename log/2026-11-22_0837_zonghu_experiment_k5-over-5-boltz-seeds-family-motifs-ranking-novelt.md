# [2026-11-22 08:37] experiment | K5 over 5 Boltz seeds, family-motifs ranking, novelty of pack designs (zonghu) (zonghu)

- TODO
- **What:** refolded the 128 family-motifs designs at Boltz seeds 1-5 (`scripts/41_k5_seeds.sbatch`) and scored K1-K5 with `scripts/40_score_metrics_pack.py`: `results/criteria/family_motifs_k5_seeds_v2.tsv`, `family_motifs_k5_ranking.txt`.
- **Result:** best mean 0.383 (`os59__4BS0_A_s12__s007`); pack designs s068/s024/s042 score 0.68/0.53/0.50 over 5 seeds.
- **Also:** PDBs with marked Base/Donor for s068, s024, s042, s006, s004 in `results/structures/`; novelty table of the pack designs added.
- **Correction:** pack seed12 s001 is 0.225 (declared donor), not 0.494.
- **Open:** novelty of the new top 20 not yet run.
