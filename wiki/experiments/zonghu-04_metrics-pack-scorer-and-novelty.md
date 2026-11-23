# zonghu-04: metrics pack scorer and novelty

- **Owner:** zonghu
- **Date:** 2026-11-22
- **Status:** done: inconclusive (novelty of the family-motifs top 20 is still open)
- **Question:** how do scorer v2 (weighted K1-K5) rankings look when K5 is measured over 5 Boltz-2 seeds, for the metrics pack and the 128 family-motifs designs?
- **Why it matters:** single-fold scores drop K5 and overstate designs; slots in the 20-sequence submission need a K5-based ranking plus the novelty gate.
- **Script + config:** `scripts/40_score_metrics_pack.py`, `scripts/41_k5_seeds.sbatch`
- **Runs:** `runs/20261122-080347_fm-k5-seeds/`, `runs/20261122-025059_k5-P/`, `runs/20261122-024359_k5-s042/` (cluster outputs in `/mnt/work/projects/zonghu_fm_k5/`)

## Result

5-seed mean weighted K1-K5: s068 0.683, s024 0.528, s042 0.499, s006 0.216, s004 0.215. Single-fold pack values were higher
(s042 0.921) because K5 is dropped there and the single folds look selected. Correction: pack `best__seed12__s001` is 0.225
with the declared donor Gln101, not 0.494 (inferred Ser103).

Family-motifs (128 designs, `results/criteria/family_motifs_k5_ranking.txt`): best mean `os59__4BS0_A_s12__s007` 0.383;
only 1 design above 0.3, 6 above 0.1. The angle term K2 is near 0 almost everywhere.

Novelty of s068/s024/s042/s006/s004 (`results/criteria/metrics_pack_novelty.tsv`): all PASS (family qTM ~0.30, PDB qTM 0.55-0.56,
identity to HG series 32-35 %). Structures with marked catalytic residues: `results/structures/`.

## Verdict and next step

Novelty of the new family-motifs top 20 is not yet checked; the pack seed4 designs are separate from family-motifs.
Remaining inferred pack structures: seed3 (x3) and Trp44 (x2).
