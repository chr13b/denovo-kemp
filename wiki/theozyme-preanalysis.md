# Theozyme pre-analysis

What the published Kemp eliminase structures say about the catalytic site, and a ranked set of theozyme candidates
built from them. Lives in [../pre_analysis/](../pre_analysis/README.md). It was done before the design runs and
outside this repo's run tooling, so nothing here is backed by a `runs/` directory yet (see Status).

## Why it matters for the score
[challenge.md](challenge.md) says the scorer measures **base → `6NT_N3`** and **donor → `6NT_N1`**. The analysis
centres on the same two contacts: a carboxylate (Asp/Glu) or His–Asp base at the TSA N3 (the C3–H site), and an
optional donor at N1 (the leaving-group side), plus an aromatic stacker and an optional nitro-side donor.

## Where to look
- Recommended variants, methods and caveats: [../pre_analysis/kemp_theozymes_v2/report/index.html](../pre_analysis/kemp_theozymes_v2/report/index.html)
- Observed base, stacker and donor geometries in 36 TSA complexes: [../pre_analysis/kemp_eliminase/theozyme/extracted/theozyme_summary.csv](../pre_analysis/kemp_eliminase/theozyme/extracted/theozyme_summary.csv)
- Origin of the published theozymes and best kcat/KM per family: [../pre_analysis/kemp_eliminase/theozyme/THEOZYME_ORIGIN.md](../pre_analysis/kemp_eliminase/theozyme/THEOZYME_ORIGIN.md)
- Nitro-group donor and stacker geometries from other enzymes: [../pre_analysis/nitro_enzymes/README.md](../pre_analysis/nitro_enzymes/README.md)
- Turning the recommended candidates into RFD4-Proteina design inputs: [theozyme-inputs.md](theozyme-inputs.md)
- Candidate theozyme PDBs (TSA in chain A, the real substrate in `__michaelis` files): [../pre_analysis/kemp_theozymes_v2/candidates/](../pre_analysis/kemp_theozymes_v2/candidates/)

## What to keep in mind
- The ranking weights are the author's choices; geometry scores did not predict the activity of the published
  lineages (Spearman ρ = −0.10, n = 5, see the v1 report). Treat the ranking as "close to observed contacts", not as predicted activity.
- The HG3.17 activity (≈2.3×10⁵ M⁻¹s⁻¹) comes from a web summary and is not verified in the paper text.
- None of the three crystal structures that contain the real substrate shows a productive arrangement, so the
  real-substrate check is a model check.
- Theozymes are static idealisations of a transition-state analog; the scorer cofolds sequences in Boltz-2, so a theozyme
  is an input to motif design, not a prediction of what Boltz-2 will place.

## Status
- Moved into the repo on 2026-11-21 without conversion: the scripts do not use `kemp.config` / `start_run`, and there is no experiment page.
- Open: a handle, branch and log entry for this work; deciding which candidates feed motif-based design and
  turning that step into a numbered `scripts/` stage with a run directory.
