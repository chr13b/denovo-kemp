# [2026-11-21 23:27] experiment | Pocket and smoothness checks: geometry is a lottery at 56-74 percent identity; no aromatics sampled (chris)

- TODO

- On seed 4's 72 designs, the pocket (13 residues within 5 A of the ligand on the DESIGNED backbone, 11
  free) is near-identical in the best and worst designs: 7 of 11 positions carry the same residue in both
  groups. Class counts relate weakly to D (hydrophobic -0.29, Gly/Pro +0.07); LigandMPNN's own scores
  say nothing (-0.04 / +0.01 / -0.13).
- **Sequence similarity to the three best designs does not predict D** (Spearman -0.07, -0.05, +0.09) over
  56-74 % identity. Resampling around a winner at that range is no better than blind sampling. Untested at
  90-99 % identity.
- **No design has an aromatic residue at any free pocket position**, though the crystal ring is stacked by
  Trp44. An unsampled region, hence a cheap test.
- **Trap, corrected:** Gly/Pro near the ligand correlated +0.68 with worse geometry when the pocket was read
  off the refolded structure and +0.07 when read off the designed backbone. The refold-defined number was
  circular, since a misplaced ligand touches different residues. Not a lever.
- Consequence: the planned "pocket-fixed resampling around s024" is dropped; it would mostly reproduce blind
  sampling. Replaced by small comparison arms judged on the whole D distribution.
- AWS from the cluster: identity resolves, shared release prefix readable, own folder listing AccessDenied
  (expected per the docs). Write permission is only confirmable by uploading. Nothing uploaded.
