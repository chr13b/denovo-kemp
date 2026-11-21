# [2026-11-21 22:09] fix | Corrections: job 47 requeue loop, B and C overclaimed, rho weaker, validator accepts (chris)

- TODO

- **Job 47 (the decisive 5-seed replication) was requeued 6 times and never ran; jobs 58 and 61 twice
  each.** Cause: my own `--constraint="l4small|l4"` let Slurm allocate to the dead l4small nodes, the
  power-up failed, and the job went to the back of the line. Pinned the three pending jobs to
  `g6.2xlarge` with `scontrol update`, fixed `cluster/oversample.sbatch` and `replicate_seeds.sbatch`,
  and corrected my advice in `wiki/team.md` (which would have sent zonghu into the same loop).
  Check with `scontrol show job <id> | grep Restarts`.
- **Ideas B and C were not refuted; they are inconclusive.** One backbone per condition, and the plain
  two-anchor motif's own RFD3 seeds span median CA RMSD 0.77 / 1.33 / 1.53 / 1.91 / 1.92 / 10.67 Å, so
  Trp44 (2.02) and 8USL_B (1.99) sit inside the range the minimal motif produces by itself. I had
  compared against seed 4, which was chosen because it was the best. Statuses, primer headings, the
  chris-05/06 pages and the note to zonghu are corrected. Only Trp44's donor median (18.92 Å vs
  4.7-11.9 for all others) stands out, and that is n = 1.
- **The designability correlation is weaker than reported.** rho = +0.943 at n = 6 became **+0.857 at
  n = 8** and +0.829 among the six plain 4BS0-motif backbones. Both axes come from the same refolds,
  so part of it is mechanical.
- **"Within-batch comparisons are fair because the RNG is shared" was wrong.** Each structure draws its
  own noise; only averages over many sequences are reliable.
- **How strong is Idea A?** 3 base-window hits and 2 both-window hits among 336 designs on 8
  backbones, all on seed 4's (pre-chosen) backbone: p = 0.0095 and p = 0.045 by exact hypergeometric.
  Suggestive, not conclusive, and each hit is one noisy draw.
- **The organizers' own `validate-submission.py` ACCEPTS `results/designs.fasta`** (2 designs, 260
  residues, base/oxy checked). Downloaded only the validator, not the uploader.
- Seeds 12 and 13 screens (jobs 59, 60): 0/16 each, median CA RMSD 1.91 and 1.92. The "1 inside BOTH"
  printed for job 59 was a natural-enzyme control, not a design (reporting bug, already fixed).
- Pre-registered the decision rule for job 47 in `chris-04` before it runs.
