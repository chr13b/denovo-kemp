# chris-02: seed sweep — is the RFD3 → Boltz-2 geometry drift systematic?

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** running
- **Question:** In [chris-01](chris-01_reference-pipeline-baseline.md) the catalytic base contact went from
  2.53 Å in the RFD3 design to 5.91 Å after the Boltz-2 refold (+3.38 Å), while the donor contact held.
  That was **one** design. Does the drift happen for *every* design, or was that run an outlier?
- **Why it matters:** It decides where we spend the rest of our GPU time. Scoring is done on the Boltz-2
  cofold. If RFD3 geometry does not predict Boltz-2 geometry, then **no cheap pre-filter on RFD3 output is
  valid** — every candidate has to be refolded before we can judge it, which is ~23 min of GPU each and caps
  how many designs we can screen. If RFD3 geometry *does* predict it, we can generate many backbones, filter
  them in seconds, and refold only the survivors.
- **Script + config:** organizers' pipeline, unmodified except the seed. Projects
  `/mnt/work/projects/chris_seedsweep_s{2,3,4,5}` created with `new-project.sh` from the verified
  `/mnt/work/kemp_example`, then one edit per project:
  `sed -i "s/\bseed=1\b/seed=$S/; s/--seed 1\b/--seed $S/g" src/kemp-e2e.sbatch`
  (three call sites: RFD3 line 48, LigandMPNN line 62, Boltz-2 line 86).
  Verified before submitting: exactly those three lines differ from the reference, and `inputs/Kemp.json`
  is byte-identical (motif `Kemp_HG3_17_base_donor`, `contig 260-260`, fixed atoms on A127/A50/6NT).
- **Runs:** cluster jobs `2, 3, 4, 5` = seeds 2, 3, 4, 5 (job id happens to equal the seed).
  Results land in `/mnt/work/projects/chris_seedsweep_s<S>/results/kemp-<S>/summary.json`.
  Submitted 2026-11-21 ~12:5x. Serial, ~23 min each (~90 min total): the sbatch asks for
  `--constraint=g6.2xlarge --cpus-per-task=8 --mem=30G`, which is our whole allocation, so these do
  **not** run two at a time. Cancel a pending one with `scancel <jobid>` if someone needs the GPU.

## Method and what it does not isolate

All three seeds move together, so each run is an independent *design* **and** an independent *refold*.
That is deliberate: it reproduces the end-to-end process we would actually use, which is what the decision
above depends on. The cost is that design variance and Boltz-2 prediction variance are **confounded** — this
experiment cannot say *why* a contact drifts, only whether it does.

The follow-up that separates them: hold the design fixed and vary **only** the Boltz-2 seed. That isolates
refold noise, and it also measures the pose-consistency scoring term directly (scoring criterion 5 in
[../challenge.md](../challenge.md)). Worth doing once we know whether there is an effect to explain.

## Decision rule (written before the results)

Per run, read from `summary.json`: the RFD3 and Boltz-2 distances for the base contact
(`A127_OD2 → 6NT_N3`) and the donor contact (`A50_NE2 → 6NT_N1`), and compute Δ = Boltz − RFD3.

| Outcome across the 4 new runs | Reading | What we do |
|---|---|---|
| **≥ 3 of 4** have base Δ > +1.5 Å | drift is systematic | Filter candidates on **Boltz-2** geometry only. Treat RFD3 contact distances as not predictive. Budget ~23 min GPU per candidate judged and plan the design count around that. |
| **≤ 1 of 4** has base Δ > +1.5 Å | chris-01 was an outlier | RFD3 geometry is usable as a cheap pre-filter; refold only the designs that pass it. Re-examine what made chris-01 drift. |
| **2 of 4** | inconclusive | Do not build a filtering strategy on it. Run the fixed-design / Boltz-seed-only follow-up before committing GPU time. |

Secondary things to read off the same runs, no decision attached:
`complex_ipde`, `iptm`, `backbone_ca_rmsd_from_rfd3`, `ligand_protein_pairs_below_2_2_angstrom`,
`validation_warnings`, and whether the donor contact holds up as it did in chris-01.
With n = 5 including the baseline, these are a sense of spread, **not** statistics.

## Result

TODO: fill in from each run's `summary.json`. No number goes here that was not read from a run's files.

| Seed / job | base RFD3 (Å) | base Boltz-2 (Å) | Δ base | donor RFD3 (Å) | donor Boltz-2 (Å) | Δ donor | `complex_ipde` | CA RMSD (Å) |
|---|---|---|---|---|---|---|---|---|
| 1 (reference, chris-01) | 2.53 | 5.91 | **+3.38** | 3.09 | 2.94 | −0.15 | 1.8669 | 1.4326 |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |

## Verdict and next step

TODO: apply the decision rule above, then record which row of the table it landed in.
