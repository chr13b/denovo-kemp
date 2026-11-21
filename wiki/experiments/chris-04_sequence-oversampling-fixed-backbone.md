# chris-04: sequence oversampling on a fixed backbone (Idea A)

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** running
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

## Result

TODO — read from `results/oversample-27/geometry.tsv`.

## Problems hit (recorded so they are not re-hit)

- **Job 25 died at the Boltz stage:** `RuntimeError: Unable to parse filetype .a3m`. `boltz predict <dir>`
  tries to parse **every** file in the directory, not just `.yaml`. Fixed by writing the query-only
  alignments to a sibling `queries.msa/` directory and referencing them by absolute path from the yaml.
- **The organizers' template pins `--constraint=g6.2xlarge --mem=30G`**, which only the single
  `gpu-dy-l4-1` node satisfies, so every job serialised behind it. That 30 GB exists for the MMseqs2
  index, which this job never loads (chris-03). Relaxed to `--constraint="l4small|l4" --mem=14G`,
  which admits the two idle `l4small` nodes and runs jobs in parallel. `l4big` stays excluded.

## Verdict and next step

TODO
