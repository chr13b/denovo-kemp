# [2026-11-22 11:05] experiment | New seed-4 sequences, chris replicates scored, ipTM term K6 (zonghu) (zonghu)

- TODO
- **What:** 128 new LigandMPNN sequences on the seed-4 backbone (job 101, T 0.15-0.45), top 15 refolded at Boltz seeds 1-5 (job 102); chris' 45 replicated designs scored too. Added an ipTM term K6 (baseline 0.8372, `scripts/40_score_metrics_pack.py`; shared `kemp.scoring` untouched).
- **Result:** best 5-seed mean K1-K6: `new:s018` 0.775 (K1-K5 0.746), then chris `arms_98_s010` 0.759, s068 0.718. All checked tops pass the novelty gate (TM family ~0.30, PDB 0.54-0.57, HG identity 33-37 %).
- **Caveat:** best of many candidates, same seeds 1-5 used for selection; needs an independent replication. Single-fold scores overstated several designs (s048, s058, s100 fall below 0.04).
- **Files:** `results/candidates/` (csv, zips, confidence jsons, `ranking_k1_k6.md`), `results/criteria/newseq_s4_k5_k6.tsv`, `chris_replicates_k5_k6.tsv`.
