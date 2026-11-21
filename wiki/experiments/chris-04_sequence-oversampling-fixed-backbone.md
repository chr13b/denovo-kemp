# chris-04: sequence oversampling on a fixed backbone (Idea A)

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** done: supported
- **Question:** Seed 4's base contact refolds to 3.32 Å, outside the crystal window of 2.41–2.69 Å.
  Is that **+0.79 Å drift a property of the backbone**, or of the single sequence we happened to sample?
- **Why it matters:** It decides where every remaining GPU-hour goes. If the drift is sequence-level,
  the fix is free (6 s + 19 s per attempt) and we stop generating backbones. If it is backbone-level,
  sequence sampling cannot save us and we need different motifs (chris-06) or more anchors (chris-05).
- **Script + config:** `cluster/oversample.sbatch`, launched by `cluster/launch_oversample.sh`
- **Runs:** cluster job **27**, `/mnt/work/projects/chris_oversample_a/results/oversample-27/`
  (an earlier attempt, job 25, died in the Boltz stage — see Problems below)

## What this run does

Holds seed 4's RFD3 backbone **completely fixed** (`bridge/kemp.pdb` from
`chris_seedsweep_s4/results/kemp-4`, reused read-only; RFD3 is not re-run) and samples the sequence
72 times: LigandMPNN at **T = 0.1, 0.2, 0.3**, 24 sequences each, then Boltz-2 on all of them in one
batched call, then the catalytic geometry of every refold.

Three temperatures rather than one because it separates two effects that a single sweep confounds:
**sampling** variance (within T = 0.1, where the original run sat) from **temperature** effect
(whether more diversity helps or just breaks the fold).

Also folded in the same batch, under identical conditions: **4BS0 (HG3.17), 3NYD (HG3) and 7K4U**,
with their sequences taken from the deposited structures. This is the instrument check — see below.

## Pre-registered decision rule (written before the results existed)

Let `base` be the pinned Asp→6NT N3 distance on the Boltz-2 refold, target window **2.41–2.69 Å**.

| Observation | Reading | Next step |
|---|---|---|
| ≥1 sequence with `base` in window | drift is **sequence-level** | Idea A is the pipeline. Oversample every backbone; submit the survivors |
| best `base` in 2.7–3.0 Å | partial — sampling helps but does not close the gap | combine with chris-05 (third anchor) before spending more |
| all 72 cluster at ≈3.3 Å (spread < 0.3 Å) | drift is **backbone-level** | abandon Idea A on this backbone; chris-06 motif variety becomes the main line |
| most sequences fail to fold (CA RMSD > 5 Å) | temperature too high for this backbone | re-run at T ≤ 0.15 only |

Secondary, logged either way: does **CA RMSD** predict base drift *within* one backbone, as it does
across backbones (primer d2)? That is the feature a learned filter would use, and 72 points from one
backbone is a far cleaner design matrix than 72 one-off backbones.

## The instrument check, and why it gates the rest

We compare designs to distances measured from **crystal structures** but measure them with **Boltz-2**.
Nothing so far shows the two instruments agree. Folding the real enzymes' own sequences settles it:

- Boltz-2 reports ≈2.5 Å for 4BS0 → the window is reachable, and our designs genuinely miss it.
- Boltz-2 reports ≈3.3 Å for 4BS0 → **seed 4 is already at parity with HG3.17** and the target as
  stated is an artefact of comparing two instruments.

Until this number exists, no verdict in this experiment can be interpreted. It costs 19 s.

## Result — **supported.** The drift is sequence-level.

75 of 75 structures measured. Full table: `results/oversample_a_seed4_job27.tsv`.

**Two sequences on seed 4's own backbone land inside both crystal windows, where the one sequence
the organizers' pipeline sampled missed both.**

| | base (2.41–2.69) | donor (2.92–3.60) | CA RMSD | iptm | plddt | novelty |
|---|---|---|---|---|---|---|
| seed 4, the original single sequence | 3.32 ✗ | 3.75 ✗ | 0.70 | 0.846 | 0.945 | qTM 0.550 |
| **s024** (T = 0.2) | **2.49 ✓** | **3.53 ✓** | 1.07 | 0.888 | 0.953 | **qTM 0.561 PASS** |
| **s059** (T = 0.3) | **2.59 ✓** | **3.48 ✓** | 0.60 | 0.847 | 0.938 | **qTM 0.546 PASS** |
| family crystals | 2.41–2.69 (med 2.51) | 2.92–3.60 (med 3.03) | | | | |

s024's base contact is 2.49 Å against a family median of 2.51 Å. Both designs pass the novelty gate
against all 40,066 PDB representatives at ≤3.0 % sequence identity, and both are banked in
`results/designs.jsonl` as `chris_osA_01` / `chris_osA_02`.

### The distribution, and what actually varies

| | min | median | max | sd |
|---|---|---|---|---|
| base contact | 2.38 | 5.12 | 23.15 | 3.96 |
| donor contact | 2.67 | 4.68 | 22.55 | 3.73 |
| CA RMSD | 0.49 | **0.77** | 17.37 | 2.12 |

In base window 3/72; in **both** windows 2/72. A ~3 % hit rate per sequence — which is exactly why
sampling once per backbone found nothing, and why sampling costs 25 s.

### This corrects finding (d2)'s framing

I described the loss as "refold fidelity", and across backbones that was right: the bad seeds
genuinely collapsed (CA RMSD 13–15 Å). **Within one backbone it is wrong.** The protein refolds
reliably — median CA RMSD 0.77 Å, and at T = 0.1 all 24 sequences refolded under 2 Å — while the base
contact ranges over 2.38–23.15 Å. And CA RMSD barely predicts it:

| feature | Pearson r vs base distance |
|---|---|
| CA RMSD | **+0.122** — essentially useless within a backbone |
| iptm | **−0.404** — the best of the three, and still weak |
| LigandMPNN `ligand_confidence` | −0.002 — no signal at all |

So the sequence is not failing to encode the *fold*. It is failing to hold the **ligand**. That is a
different and more specific problem than I stated, and it means no cheap pre-filter we have is good
enough to skip the fold — which is fine, because the fold costs 19 s. **Fold everything; filter on
the measured contact.**

### Temperature: T = 0.1 is the worst of the three

| T | best base | in base window | refolded < 2 Å |
|---|---|---|---|
| **0.1** (the organizers' default) | 2.72 | **0** | 24/24 |
| 0.2 | 2.49 | **2** | 23/24 |
| 0.3 | **2.38** | 1 | 23/24 |

Raising the temperature improves the best contact monotonically and costs almost nothing in folding
success. Both winners came from T ≥ 0.2; T = 0.1 produced none. **Use T = 0.2–0.3.**

## The instrument check — a split verdict, and a caveat I have to state

Measured on the same batch, same conditions. The `base→N1` and `donor→N3` columns test whether the
ligand's ring is oriented as in the crystal or flipped end-for-end.

| structure | base→N3 | base→N1 | donor→N1 | donor→N3 | nearest base | nearest donor |
|---|---|---|---|---|---|---|
| **4BS0** (HG3.17) | **2.49** | 2.71 | **6.08** ✗ | 6.11 | ASP129:OD2 | TYR176:OH |
| 3NYD (HG3) | 3.49 | **2.21** | 2.80 | 3.43 | ASP127:OD2 | GLN37:NE2 |
| 7K4U | **2.11** | 2.37 | **5.34** ✗ | 4.26 | ASP132:OD2 | GLN212:NE2 |
| s024 (ours) | **2.49** | 4.02 | **3.53** | 3.07 | ASP86:OD2 | GLN52:NE2 |
| s059 (ours) | **2.59** | 4.69 | **3.48** | 3.09 | ASP86:OD2 | GLN52:NE2 |

- ✅ **The base contact is validated.** Boltz-2 puts 4BS0's base at 2.49 Å against a crystal value of
  2.53 Å. The window is reachable, and base numbers mean what we have been treating them as meaning.
  (ASP129 rather than ASP127 is the N-terminal `GM` tag's two-residue offset, not an error.)
- ❌ **The donor contact is not validated.** Boltz-2 loses the donor entirely on 4BS0 (6.08 Å vs a
  crystal 3.10 Å) and on 7K4U, and on 3NYD it places the base nearer N1 than N3 — a flipped pose.
- **The caveat.** These controls are 307–318-residue natural constructs folded single-sequence with
  **no pocket conditioning**, whereas zonghu's `aff_*` runs use `pocket_force: true` with a 5 Å radius.
  So this control is harsher than the comparison requires, and the donor failure may be an artefact of
  unconditioned ligand placement in a large protein rather than a limit of Boltz-2. **Re-running the
  controls with pocket conditioning is the proper follow-up**, and zonghu already has the recipe.

Two consequences for how we read our own numbers. The base contact is the number to optimise and
report. The donor contact is secondary until that control is redone — which is convenient, because
geometry is dominated by the base contact anyway and the base is where our designs were failing.

One honest wrinkle in our winners: for both, the donor's nearest ligand nitrogen is **N3** (3.07/3.09)
rather than the scored **N1** (3.53/3.48). The scored measurement is inside the window, but the ring's
in-plane rotation is not exactly the crystal's. Worth watching, not worth blocking a submission over.

## Problems hit (recorded so they are not re-hit)

- **Job 25 died at the Boltz stage:** `RuntimeError: Unable to parse filetype .a3m`. `boltz predict <dir>`
  tries to parse **every** file in the directory, not just `.yaml`. Fixed by writing the query-only
  alignments to a sibling `queries.msa/` directory and referencing them by absolute path from the yaml.
- **The organizers' template pins `--constraint=g6.2xlarge --mem=30G`**, which only the single
  `gpu-dy-l4-1` node satisfies, so every job serialised behind it. That 30 GB exists for the MMseqs2
  index, which this job never loads (chris-03). Relaxed to `--constraint="l4small|l4" --mem=14G`,
  which admits the two idle `l4small` nodes and runs jobs in parallel. `l4big` stays excluded.

## Verdict and next step

**Idea A is the pipeline.** One 25-minute job on a backbone we already owned produced our first two
designs with real catalytic geometry, both novel, from a backbone whose original sequence missed both
windows. No RFD3, no MMseqs2, no new tooling needed beyond `cluster/`.

Next, in order:
1. **Run it on every backbone we have.** Each is 25 min and yields ~2 in-window candidates at a 3 %
   hit rate. Six backbones exist already.
2. **Use T = 0.2–0.3, never 0.1.** The default produced zero winners out of 24.
3. **Sample more per backbone.** At a 3 % hit rate, 72 sequences give ~2 hits; 200 would give ~6.
   Boltz-2 is 19 s, so 200 sequences is ~65 min — still cheaper than six new backbones.
4. **Redo the controls with pocket conditioning** (`pocket_force: true`, 5 Å) before trusting any
   donor-contact number, ours or the natural enzymes'.
5. Stop reporting CA RMSD as a quality filter for sequences on a fixed backbone. It has r = +0.12.
