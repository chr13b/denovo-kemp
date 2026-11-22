# [2026-11-22 01:43] experiment | Scorer v2 on the organizers-style metrics pack (57 structures) (zonghu)

- **What:** scored every structure of `share_metrics_pack` (56 Boltz-2 designs/natural enzymes + the 4BS0 crystal)
  with `scripts/40_score_metrics_pack.py`, using `kemp.scoring.weighted_total` (weighted K1-K5, no K5-less column).
  Tables: `results/criteria/metrics_pack_weighted_v2.tsv` (7K4U targets) and `..._family.tsv` (23-crystal medians).
- **The pack's headline test holds.** Mean weighted score over 5 seeds: **s024 0.528 > s059 0.088 > seed4_original 0.051**
  (family targets: 0.505 / 0.083 / 0.049). Seed-matched s024 > original in 5/5, s024 > s059 in 4/5, but
  **s059 > original in only 3/5**: that gap is within noise. s024's seed 3 collapses to 0.04.
- **K5 exists only for the 3 replicated sequences** (0.270 / 0.245 / 0.016); every other total drops K5 and
  renormalises, so it is not strictly comparable to the replicated ones.
- **Within `spread_seed4`:** rank agreement with the manifest's D is rho 0.88 (v2) / 0.86 (family), but the scores
  are all <= 0.042: the scorer ranks them and judges all as failed (donor 3.7-6.0 A, ring plane off by 87-161 deg).
- **The 23-crystal target changes little:** crystal 4BS0 scores 0.951 (v2) / 0.966 (family); rankings are stable.
- **Limit:** the manifest has `base_position`/`donor_position` only for the replicated rows. Seed4-backbone structures
  (44) are scored at D86/Q52 (asserted); the other 13 (other backbones, natural enzymes) use the nearest allowed atom
  and are marked `inferred`. Some are visibly wrong (natural 4BS0 "Gln209"). Rescore once real positions arrive.
