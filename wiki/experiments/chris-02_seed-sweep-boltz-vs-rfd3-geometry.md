# chris-02: seed sweep — is the RFD3 → Boltz-2 geometry drift systematic?

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** done: supported
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

All four finished, no validation warnings in any of them. Every number below is read from the tracked
`results/sweep_kemp-<job>_summary.json` files; regenerate the table with
`uv run python scripts/30_compare_rfd3_vs_boltz.py`.

| Seed / job | base RFD3 (Å) | base Boltz-2 (Å) | Δ base | donor RFD3 (Å) | donor Boltz-2 (Å) | Δ donor | `complex_ipde` | CA RMSD (Å) |
|---|---|---|---|---|---|---|---|---|
| 1 (reference, chris-01) | 2.53 | 5.91 | **+3.38** | 3.09 | 2.94 | −0.15 | 1.8669 | 1.433 |
| 2 | 2.53 | 21.92 | **+19.39** | 3.09 | 18.86 | +15.77 | 5.4966 | 14.625 |
| 3 | 2.53 | 8.33 | **+5.80** | 3.09 | 3.08 | −0.02 | 1.7469 | 1.358 |
| 4 | 2.53 | 3.32 | +0.79 | 3.09 | 3.75 | +0.66 | **1.5184** | **0.704** |
| 5 | 2.53 | 14.88 | **+12.35** | 3.09 | 15.83 | +12.74 | 6.7352 | 13.672 |

Each run really is a different design: seed 2 shares only 8.5 % sequence identity with seed 1, and the
catalytic residues land at different positions (seed 1 `base=177 oxy=99`, seed 2 `base=189 oxy=146`).

## Verdict

**3 of 4 new runs have base Δ > +1.5 Å → the pre-registered rule says the drift is systematic.**
Filter candidates on **Boltz-2** geometry. RFD3 contact distances are not a usable pre-filter.

Three findings, in descending order of how much they should change what we do:

**1. RFD3 contact distances are constant by construction — they carry zero information.**
The base contact is `2.527 Å` in *every* run, the donor `3.09 Å` in every run. `select_fixed_atoms` in
`inputs/Kemp.json` holds the motif atoms and the ligand rigid, so these distances are an *input* RFD3 is
handed, not a property of the design. Reported `fixed_pair_distance_max_deviation_angstrom` is 0.013 Å.
This is stronger than the decision rule: filtering on RFD3 contact geometry was never *possible*, not
merely unwise. Any cheap pre-filter has to use something else.

**2. Refolding is close to binary, not a gradient.** CA RMSD comes out as {0.70, 1.36} or {13.67, 14.63} —
nothing between 1.4 and 13.7. A design either refolds essentially as designed or collapses completely, and
when it collapses the ligand leaves the site entirely (contacts 15–22 Å, iPDE 5.5–6.7). So the first gate
is not "how good is the geometry" but **"did this design fold at all"**, and that is one cheap number.

**2 of 4 new designs (3 of 5 including the baseline) survived refolding.** At 260 AA with default settings,
expect to throw away roughly half of everything generated — that halves effective GPU throughput and is
the single most important number for planning how many designs we can afford.

**3. The base contact is the fragile one; the donor is not.** Among runs that *did* fold (1, 3, 4), the
donor contact barely moves (−0.15, −0.02, +0.66 Å) while the base contact moves +3.38, +5.80 and +0.79 Å.
Geometry carries the most scoring weight, so **the catalytic base placement is where designs lose points**,
even when everything else is fine.

### One candidate came out of this

**Seed 4 (`results/sweep_kemp-4_summary.json`) beats the reference on every metric we have:** iPDE
1.5184 vs 1.8669, CA RMSD 0.704 vs 1.433, base contact 3.32 Å vs 5.91 Å, donor 3.75 Å. It is not the shared
example, so unlike the baseline it could actually be submitted. **Not yet a candidate:** novelty is
unchecked (TM ≤ 0.7, identity ≤ 70 %), the donor contact at 3.75 Å is longer than ideal H-bond geometry,
and n = 1 for this design. Check novelty before it takes one of our 20 slots.

## Next steps

1. **Novelty-check seed 4.** If it passes it is our first real submission candidate.
2. **Build the cheap pre-filter on something that varies.** Base burial (CA atoms within 12 Å of the base —
   the one scoring term with an exact published definition) computed on the *RFD3* backbone is the obvious
   candidate, because it is free and it is a scored quantity. Test whether it predicts which designs survive
   refolding, using these 5 runs as the first labelled examples.
3. **Separate design variance from refold variance:** hold one design fixed and vary only the Boltz-2 seed,
   5 replicates — which is exactly how the organizers compute the consistency term
   ([../challenge.md](../challenge.md)). Run it on seed 4, since it is the design we might submit.
4. Do not spend GPU re-measuring RFD3 contact distances. They are a constant.
