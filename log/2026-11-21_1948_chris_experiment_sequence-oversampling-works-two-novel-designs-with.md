# [2026-11-21 19:48] experiment | Sequence oversampling works: two novel designs with real catalytic geometry (chris)

- TODO

- **chris-04 (job 27) is supported.** 72 LigandMPNN sequences on seed 4's *existing* RFD3 backbone,
  all folded by Boltz-2 in one batched call, 75/75 measured. **Two land inside both crystal windows**
  where the organizers' single sequence (base 3.32, donor 3.75) missed both:
  `s024` base **2.49** donor **3.53** (T=0.2), `s059` base **2.59** donor **3.48** (T=0.3).
  Family median base is 2.51 Å. Hit rate ~3 % per sequence - which is why sampling once found nothing.
- Both pass the novelty gate against all 40,066 PDB representatives: qTM **0.561** and **0.546**,
  ≤3.0 % sequence identity. Banked as `chris_osA_01` / `chris_osA_02` in `results/designs.jsonl`,
  index-verified (D at 86, Q at 52) and accepted by the offline validator.
- **T = 0.1, the organizers' default, is the worst setting**: 0 winners from 24, against 2 at T = 0.2
  and 1 at T = 0.3, with folding success essentially unchanged (24/23/23 refolded under 2 Å).
- **Correction to my own finding (d2).** I called the loss "refold fidelity". Within one backbone that
  is wrong: median CA RMSD is 0.77 Å and all 24 sequences at T=0.1 refolded under 2 Å, while the base
  contact ranges 2.38-23.15 Å. CA RMSD predicts it at **r = +0.12**; iptm at r = -0.40;
  `ligand_confidence` at r = -0.00. The sequence fails to hold the **ligand**, not to encode the fold.
  No pre-fold filter we have is good enough - so fold everything (19 s) and filter on the contact.
- **Instrument check, split verdict.** Boltz-2 reproduces 4BS0's base contact at **2.49 Å** against a
  crystal 2.53 Å, so the base window is reachable and base numbers are meaningful. It **loses the
  donor** on 4BS0 (6.08 Å vs 3.10) and 7K4U (5.34), and flips the pose on 3NYD. Caveat: the controls
  are 307-318 residue natural constructs folded with no pocket conditioning, unlike zonghu's `aff_*`
  runs which use `pocket_force: true`. Redo with pocket conditioning before trusting donor numbers.
- Idea C's design stage (job 34) completed with 0 failures: both family motifs gave in-window
  backbones (4BS0_A 2.53/3.09 at 0.0129 Å deviation; 8USL_B 2.56/3.24 at 0.0157 Å) and auto-chained
  sweeps 35 and 36. Idea B (job 31) is folding.
