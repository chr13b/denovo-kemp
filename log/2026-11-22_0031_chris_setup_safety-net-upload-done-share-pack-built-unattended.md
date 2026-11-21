# [2026-11-22 00:31] setup | Safety-net upload done, share pack built, unattended pipeline built and rehearsed (chris)

- TODO

- **Uploaded** the 1-design file (`chris_osA_01` = s024) from the cluster with the organizers' `submit-designs.sh`.
  It validated first, then `put-object` returned S3 version `b43yX__RrxQPzbJd19vsm3Ek2aDIcCkJ`, so write access
  is confirmed (listing our folder is AccessDenied, as the docs say to expect). Index check beforehand: D at 86,
  Q at 52, 260 residues; local and cluster copies matched by sha256.
- **Only one GPU works.** A `--constraint=l4small --no-requeue` probe started on `l4small-1` at 23:28:08 and
  died 12 s later as `NODE_FAIL / NodeDown`; the node failed its health check again. No second GPU.
- **Pose analysis (primer g10):** 84 % of 352 designs do not put the ligand in the pocket at all; only 5 % put it
  roughly in place. The good ones are on seed 4's backbone and refold more faithfully (iPDE 1.23 vs 2.17).
  `iPDE < 1.6 and iptm > 0.85` is a free triage filter: keeps 17 % of designs and 5 of the 6 best.
- **Share pack for a teammate:** `tools/make_share_pack.py` builds `data/share_metrics_pack.zip` (56 structures,
  3.3 MB): 12 best, 12 spread and 8 worst on seed 4, 6 mid-range from other backbones, s024/s059/pipeline sequence
  x 5 seeds (the closest thing to ground truth), 3 natural controls, the 4BS0 crystal, with a manifest, sequences
  and a README that defines every metric and its caveats.
- **Unattended pipeline** `cluster/autopilot.py` (Python 3.9-compatible, head node, resumable) with arm inputs
  calibrated on the head node: the aromatic bias needed scale 3 (1.5 gave 0.2 aromatics per sequence, 5 gave 7.8
  of 11); the close-variant push 1.5 gives 89-93 % identity to s024. Dry-run on real data reproduces job 47's
  verdicts through the new aggregator: s024 passes (3/5 both, mean D 9.4, OD2 nearest 5/5), s059 and the
  pipeline's sequence fail.
- Modified `oversample.sbatch` (checkpoint override, extra LigandMPNN args, seed offset, full-geometry step) and
  `replicate_seeds.sbatch` (full-geometry step); two 2-sequence smoke jobs queued to prove them on the GPU.
