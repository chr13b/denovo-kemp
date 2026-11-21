# chris-05: the Trp44 three-anchor motif, retested properly (Idea B)

- **Owner:** chris (motif by **zonghu**, job 7)
- **Date:** 2026-11-21
- **Status:** running
- **Question:** zonghu's 7K4U-derived theozyme adds a third anchor, **Trp44**, whose indole stacks on
  the ligand ring at 3.86 Å in 4BS0. Their run refolded badly (CA RMSD 4.26 Å, ligand 26 Å from the
  donor) and the motif looked refuted. **Was it the motif, or the one sequence it was tested with?**
- **Why it matters:** Two anchors let the benzotriazole pivot about the axis joining them — exactly the
  freedom the base contact loses. A third anchor over-determines the ligand. If the motif is sound, it
  is strictly better posed than ours and should become the default.
- **Script + config:** `cluster/oversample.sbatch`, launched by `cluster/launch_oversample.sh`
- **Runs:** cluster job **28**, `/mnt/work/projects/chris_oversample_b/results/oversample-28/`

## Why the motif was never actually tested

Reading zonghu's run rather than just its summary changes the picture completely:

| | RFD3 backbone | Boltz-2 refold |
|---|---|---|
| base (Asp→N3) | **2.53 Å** — in window | 11.99 Å |
| donor (Gln→N1) | **3.20 Å** — in window | 26.49 Å |
| CA RMSD | — | 4.26 Å |

**RFD3 satisfied the three-anchor motif exactly**, the same as it does ours. The geometry was lost in
the refold, which is primer finding (d2) — a sequence problem, not a motif problem. And it was sampled
once, at T = 0.1.

Their hand-off is also correct, which I had not verified before doubting it: `bridge/sequence.json`
maps **A50 → position 237 (Q), A127 → position 54 (D), A44 → position 98 (W)**, so all three anchors
are held fixed through LigandMPNN and survive into the sequence. The `prepare_rfd3_input.py` validation
warnings their run reported are the launcher complaining that the motif is not the 2-residue default —
they do not indicate a broken hand-off.

One more signal in their favour: their LigandMPNN scores are **better than ours** —
`ligand_confidence` 0.534 vs 0.445, `seq_rec` 0.483 vs 0.302. The designer was more comfortable with
the three-anchor pocket than with ours.

## What this run does

Identical to chris-04, on zonghu's backbone instead of ours: their `bridge/` is reused **read-only**,
no RFD3 is re-run, and 72 sequences (T = 0.1 / 0.2 / 0.3 × 24) are folded and measured. Nothing in
`zonghu_trpopt_s1/` is written to.

## Pre-registered decision rule

The comparison that matters is **chris-05 against chris-04 on the same axis**: best base contact, and
the fraction of sequences landing in the 2.41–2.69 Å window.

| Observation | Reading | Next step |
|---|---|---|
| chris-05 in-window fraction > chris-04 | the third anchor **does** constrain the base | make Trp44 the default motif; re-run chris-06 with a third anchor added |
| comparable fractions | the anchor is neutral here | prefer our 2-residue motif: fewer constraints, more scaffold freedom |
| chris-05 clearly worse | 3 anchors over-constrain a 260-residue scaffold | record and drop; tell zonghu before they spend more on it |

## Result

TODO — read from `results/oversample-28/geometry.tsv`.

## Verdict and next step

TODO
