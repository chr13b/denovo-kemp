# chris-06: a motif library from the Kemp family's own crystal structures (Idea C)

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** running
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

## Result

TODO — read from each `design-29/*/bridge/motif.json`, then the oversampling runs built on them.

## Verdict and next step

TODO
