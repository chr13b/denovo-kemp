# chris-06: a motif library from the Kemp family's own crystal structures (Idea C)

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** done: inconclusive (one backbone per motif; the tooling works)
- **Question:** Every design we and zonghu have made uses **one** arrangement of base + donor + ligand,
  lifted from 4BS0. The family offers 26 engaged ligand copies across 23 crystal structures. **Does the
  choice of arrangement change how well a de novo backbone holds the base contact through refolding?**
- **Why it matters:** It is the one variable in the whole pipeline we have never varied. If 4BS0's
  particular base placement is simply hard to realise in a de novo scaffold, another family member's
  may be easier — and we would never find out by sampling seeds.
- **Script + config:** `cluster/build_family_motifs.py` → `cluster/design_backbones.sbatch`,
  launched by `cluster/launch_design.sh`
- **Runs:** cluster job **29**, `/mnt/work/projects/chris_family_motifs/results/design-29/`;
  motifs in `/mnt/work/tools/family_motifs/`

## Why this drops in with no changes to the launcher

Of the 26 engaged copies in `results/kemp_family_geometry.tsv`, **25 use ASP127 + GLN50** — the same
residue types at the same residue numbers as HG3.17. So their coordinates satisfy the launcher's
assertions verbatim: `unindex: "A50,A127"` and
`select_fixed_atoms: {A127: OD1,CG,OD2, A50: OE1,CD,NE2, 6NT: ALL}` need no edit. Only the 3D
arrangement differs, which is exactly the variable under test. (The 1 exception is an ASP+TYR
arrangement on a different scaffold; it is excluded.)

## How the four motifs were chosen

Not by contact distance — all 25 agree there to within 0.3 Å. The quantity RFD3 actually has to
satisfy is the **set of mutual distances between the pinned atoms**: `prepare_ligandmpnn.py` scores a
design by `max |reference_distance − design_distance|` over those 18 atoms, and warns above 0.05 Å.
So the selection clusters the copies under that same metric and takes farthest-point representatives,
seeded with 4BS0 chain A because that is the arrangement every design so far has used.

| motif | base | donor | geometry spread from the chosen set |
|---|---|---|---|
| **4BS0_A** | 2.53 Å | 3.10 Å | — (the incumbent, seeds the selection) |
| **8USL_B** | 2.56 Å | 3.23 Å | **2.20 Å** |
| **8RD5_A** | 2.57 Å | 3.03 Å | 0.76 Å |
| **7K4U_A** | 2.54 Å | 3.20 Å | 0.60 Å |

8USL_B is a genuinely different design problem: 2.20 Å of difference in the pinned-atom distance
matrix, against a 0.05 Å tolerance. Same two contact distances, completely different arrangement.
This is the content of the idea — the two scored distances do not determine the geometry.

All four motif files round-tripped through biotite with 12 ligand heavy atoms and 29 atoms total.

## What this run does

Stage 1 only: RFD3 at seed 1 on each of the four motifs (~12 min each), producing four backbones plus
their LigandMPNN hand-offs. **No MMseqs2 and no Boltz-2** — splitting the pipeline here is the point,
since RFD3 is the 12-minute step and its geometry is already exact.

Stage 2 is chris-04's oversampling job, pointed at each `bridge/` this produces.

## Pre-registered decision rule

| Observation | Reading | Next step |
|---|---|---|
| ≥1 motif's backbones refold with base in 2.41–2.69 Å more often than 4BS0's | arrangement **matters** | adopt that motif; expand to 8–10 representatives |
| all four behave alike | arrangement is not the lever; sequence sampling is all that matters | drop Idea C, concentrate on chris-04 |
| RFD3 fails on a motif | that crystal copy has strain or a missing atom | record which, exclude, continue with the rest |

A per-motif sanity check applies first: RFD3 must reproduce each motif to ≤0.05 Å
(`fixed_pair_distance_max_deviation_angstrom`). A motif it cannot satisfy tells us nothing about refolding.

## Result — inconclusive: one backbone per motif cannot separate motif from RFD3 seed

> **Correction (added later the same day).** I originally headed this "arrangement matters". The data
> cannot say that. 8USL_B and 4BS0_A are each **one** backbone, and the 4BS0 motif's *own* RFD3 seeds
> give median CA RMSD of 0.77, 1.33, 1.53, 1.91 and 1.92 Å (plus a collapsed 10.67) — a spread as big
> as the 8USL_B-vs-4BS0_A gap (1.99 vs 1.33). Seed-to-seed variation within one motif is at least as
> large as motif-to-motif variation here. To test motifs properly, each needs several RFD3 seeds.

### Design stage: clean, both motifs

Job 34, 0 failures. Both crystal arrangements gave in-window backbones, and RFD3 satisfied each to
well under the 0.05 Å tolerance:

| motif | RFD3 base | RFD3 donor | deviation |
|---|---|---|---|
| 4BS0_A | 2.53 Å | 3.09 Å | 0.0129 Å |
| 8USL_B | 2.56 Å | 3.24 Å | 0.0157 Å |

So a motif lifted from an arbitrary family member is as satisfiable as the one the pipeline ships
with. The extraction and renumbering in `cluster/build_family_motifs.py` works.

### 4BS0_A, fresh backbone: designable, but 0 of 32 in window

`results/oversample_c_4bs0a_job35.tsv`. 32 sequences at T = 0.1 / 0.2.

| | seed 4 (same motif, different RFD3 seed) | **4BS0_A fresh** |
|---|---|---|
| median CA RMSD | 0.77 Å | **1.33 Å** — designable |
| refolded < 2 Å | 70/72 (97 %) | 27/32 (84 %) |
| best base contact | 2.38 Å | 2.90 Å |
| in window | 2/72 | **0/32** |

**This is weak evidence, and should be read as such.** At seed 4's measured hit rate of ~3 %, 32
sequences give an expected 1 hit, and seeing 0 has probability ≈0.38 under the *same* rate. So 0/32
does not show this backbone is worse — it shows 32 sequences is too few to tell. The informative
number is the designability, 1.33 Å, which puts it well inside the usable range.

Practical consequence for the sweeps: **32 sequences is under-powered.** Use 72+ per backbone, or
accept that a 0 result carries almost no information.

### The controls moved again, and now there are four measurements

Same 4BS0 sequence, same `--seed 1`, four different batches:

| batch | rows | base | donor |
|---|---|---|---|
| job 27 | 75 | 2.493 | 6.077 |
| job 31 | 75 | 2.493 | 6.077 |
| job 40 | 51 | 2.072 | 4.845 |
| job 35 | 35 | 2.065 | 5.468 |
| **crystal** | — | **2.53** | **3.10** |

Base readings cluster into two groups by batch size and span **0.43 Å**, against a window 0.28 Å
wide. The donor is wrong in every batch — 4.8 to 6.1 Å against a crystal 3.10 Å.

Note what this does to the target: Boltz-2's readings for a *real, working* enzyme average ≈2.28 Å,
**below** the crystal window of 2.41–2.69. If that holds up under proper replication, the window we
have been scoring against is not where Boltz-2 puts a good enzyme, and our candidates should be
ranked against the model's own reading of the natural enzymes instead. Job **47** settles it: all
three natural enzymes and all three of our candidates, 5 seeds each, one measurement protocol.

### 8USL_B, the most distinct arrangement: worse, and on the informative axis

`results/oversample_c_8usl_job36.tsv`. Same protocol, 32 sequences at T = 0.1 / 0.2.

| | **4BS0_A** (the incumbent arrangement) | **8USL_B** (2.20 Å away in pinned-atom geometry) |
|---|---|---|
| median CA RMSD | **1.33 Å** | 1.99 Å |
| refolded < 2 Å | **27/32 (84 %)** | 17/32 (53 %) |
| best base contact | **2.90 Å** | 3.52 Å |
| median base contact | **6.66 Å** | 9.73 Å |
| in window | 0/32 | 0/32 |

The hit counts are both 0 and both uninformative at this sample size. The *distributions* are not:
8USL_B is worse on designability (1.99 vs 1.33 Å median CA RMSD, 53 % vs 84 % refolding) and worse on
the contact distribution at every quantile. Those are 32-sample estimates of a distribution, far more
reliable than a 0-versus-0 hit comparison.

## Verdict and next step

**Not established either way.** (The 4BS0-is-already-optimised argument below is a plausible prior, not a result.)
Idea C's hypothesis was that 4BS0's base placement might be unusually hard to realise de novo and
another family member's might be easier. The opposite held for the one alternative tested: the most
geometrically distinct member gave less designable backbones.

In hindsight this is unsurprising, and we could have predicted it: **4BS0 is the 1.09 Å structure of
HG3.17, the most optimised variant in the family.** Its active-site arrangement is the product of
directed evolution; an arbitrary other member is a less refined version of the same idea. Geometric
*distance* from 4BS0 selects for difference, not for quality — the farthest-point selection I used
was choosing the most different motif, which is not the same as the most useful one.

So: **drop motif variety as a lever**, keep the tooling. What survives and is worth keeping:

1. `cluster/build_family_motifs.py` works — a motif lifted from any family member satisfies the
   launcher verbatim and RFD3 hits it to 0.013–0.016 Å. If we ever need a different arrangement, the
   path exists.
2. **Backbone diversity must come from more RFD3 seeds on the 4BS0 motif**, not from other motifs.
   That is the cheap axis: 12 min per backbone, and seeds 3 and 4 show different seeds give genuinely
   different folds and different designability.
3. **The funnel that falls out of all four experiments:** generate many backbones from the 4BS0 motif
   → screen each with a short sweep on **designability** (median CA RMSD, ~16 min) → deep-sweep only
   the designable ones (72+ sequences) → replicate the in-window hits over 5 seeds → novelty gate.
   Designability is measurable, cheap, and is the thing that actually varies between backbones.
