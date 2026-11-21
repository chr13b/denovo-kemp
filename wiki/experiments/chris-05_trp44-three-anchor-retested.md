# chris-05: the Trp44 three-anchor motif, retested properly (Idea B)

- **Owner:** chris (motif by **zonghu**, job 7)
- **Date:** 2026-11-21
- **Status:** done: inconclusive (leans negative; one backbone per condition)
- **Question:** zonghu's 7K4U-derived theozyme adds a third anchor, **Trp44**, whose indole stacks on
  the ligand ring at 3.86 Å in 4BS0. Their run refolded badly (CA RMSD 4.26 Å, ligand 26 Å from the
  donor) and the motif looked refuted. **Was it the motif, or the one sequence it was tested with?**
- **Why it matters:** Two anchors let the benzotriazole pivot about the axis joining them — exactly the
  freedom the base contact loses. A third anchor over-determines the ligand. If the motif is sound, it
  is strictly better posed than ours and should become the default.
- **Script + config:** `cluster/oversample.sbatch`, launched by `cluster/launch_oversample.sh`
- **Runs:** cluster job **31**, `/mnt/work/projects/chris_oversample_b/results/oversample-31/`
  (job 28 was cancelled before it hit the `.a3m` bug described in chris-04)

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

## Result — inconclusive, leaning negative

> **Correction (added later the same day).** I originally headed this "refuted". That overstated it.
> Each condition is **one** RFD3 backbone, and the plain two-anchor motif's own seeds span median CA
> RMSD 0.77 / 1.33 / 1.53 / 1.91 / 1.92 / 10.67 Å — so Trp44's 2.02 Å lies inside the range the
> *minimal* motif produces on its own. The comparison below is against seed 4, which was selected
> because it was the best backbone, so it is biased against Trp44. The one number that stands apart is
> the median donor contact (18.92 Å vs 4.7–11.9 Å for all seven other backbones). Reading: **no
> evidence the third anchor helps; weak, unreplicated evidence that it hurts the donor.** Using the
> minimal motif is still the sensible default, but as a cost decision, not a finding.

75 of 75 measured. Full table: `results/oversample_b_trp44_job31.tsv`. Tested properly this time —
72 sequences, not one — against chris-04 on the identical protocol.

| | seed 4 backbone (chris-04) | **Trp44 backbone (chris-05)** |
|---|---|---|
| best base contact | **2.38 Å** | 3.26 Å |
| median base contact | 5.12 Å | 7.64 Å |
| median **donor** contact | 4.68 Å | **18.92 Å** |
| median CA RMSD | **0.77 Å** | 2.02 Å |
| refolded < 2 Å | **70/72 (97 %)** | 35/72 (49 %) |
| in base window | 3/72 | **0/72** |
| in **both** windows | **2/72** | **0/72** |

Not a near miss. The best base contact over 72 sequences is 3.26 Å, outside the 2.41–2.69 Å window,
where seed 4's backbone reached 2.38 Å. No temperature helped: 0 in-window at T = 0.1, 0.2 and 0.3.

### Why it fails — and it is not Trp44's chemistry

The median donor contact of **18.92 Å** is the tell. In most designs the ligand has not drifted, it has
**left the pocket**. And the backbone is harder to encode: median CA RMSD 2.02 Å against seed 4's
0.77 Å, with 49 % of sequences refolding under 2 Å against 97 %.

The motif is satisfiable in *design* space — RFD3 hit it to 0.0167 Å, contacts 2.53 / 3.20 Å, as
always. But the backbone RFD3 must build to satisfy four simultaneous constraints (base, donor, the
whole indole plane, and the full ligand) is one **LigandMPNN cannot write a stabilising sequence for**.
The aromatic stack is real in 4BS0 at 3.86 Å; pinning it as a hard constraint on a 260-residue de novo
scaffold costs more in designability than it buys in ligand positioning.

This also explains zonghu's single-sequence result without the motif being wrong: their CA RMSD of
4.26 Å is in the tail of a distribution whose *median* is 2.02 Å. They drew a typical-to-poor sequence
from a backbone that is hard for every sequence.

### I predicted the opposite, and the prediction was wrong

I argued the third anchor should help because two anchors let the benzotriazole pivot about the axis
joining them. That reasoning was about the *design* step, which was never the problem — RFD3 already
placed the ligand correctly with two anchors. The extra constraint removed a degree of freedom that
was not being abused, and charged designability for it.

### A free reproducibility check

The three natural-enzyme controls returned **identical** numbers to job 27 (4BS0 2.49 / 6.08, 3NYD
3.49 / 2.80, 7K4U 2.11 / 5.34). Same inputs and seed give the same output across jobs, so the
instrument check is deterministic and the two sweeps are directly comparable.

## Verdict and next step

**Deprioritise the three-anchor motif (a cost decision, not a proof — see the correction above).** The pre-registered rule for "chris-05 clearly worse" was: record it,
stop, and tell zonghu before they spend more on it. Both are done — the note is in `wiki/team.md`.

What it teaches, which is worth more than the motif would have been:

1. **More motif constraints are not free.** The cost does not show up in RFD3's deviation (0.0167 Å,
   looks perfect) but in how hard the resulting backbone is to encode. `fixed_pair_distance_max_deviation`
   measures whether the *design* met the constraint, and tells you nothing about designability.
2. **Backbone designability is a real, measurable, per-backbone property** — median CA RMSD over a
   sequence sweep, 0.77 Å vs 2.02 Å here. That is the number to screen backbones on, and it needs a
   sweep to measure, which is why chris-02's single-sequence verdicts were unreliable in both
   directions.
3. **Prefer the minimal motif.** Two anchors already place the ligand correctly in design space. Adding
   geometry we do not need costs us the sequences that would have worked.

Next: the fold-diversity problem from chris-04 (g3) still has to be solved with *different* backbones —
but the evidence now says get them from **different motif arrangements at the same two anchors**
(chris-06) rather than from more anchors.
