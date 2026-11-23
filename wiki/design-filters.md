# Design filters: where every threshold comes from

Thresholds used by [`scripts/30_filter_designs.py`](../scripts/30_filter_designs.py), with the
evidence for each and an honest status. Replay them over every design we have ever run, free:

```bash
uv run python scripts/31_screen_summaries.py
```

## The headline: our gates reject everything, and the base contact is why

Replayed over all 6 tracked cofolds (chris-01, chris-02 seeds 2–5, zonghu-01 job 7):

| design | pLDDT | ipTM | base Å | donor Å | CA Å | failing gate(s) |
|---|---|---|---|---|---|---|
| reference_kemp-1 *(organizers' verified example)* | 83.6 | 0.837 | 5.91 | 2.94 | 1.43 | base |
| sweep_kemp-2 | 57.4 | 0.442 | 21.92 | 18.86 | 14.63 | plddt, iptm, folded, base, donor |
| sweep_kemp-3 | 88.2 | 0.838 | 8.33 | 3.08 | 1.36 | base |
| **sweep_kemp-4** | 94.5 | 0.843 | **3.32** | 3.75 | 0.70 | **donor only** |
| sweep_kemp-5 | 60.2 | 0.406 | 14.88 | 15.83 | 13.67 | plddt, iptm, folded, base, donor |
| zonghu-01_kemp-7 | 77.3 | 0.869 | 11.99 | 26.49 | 4.26 | plddt, folded, base, donor |

**0/6 pass. The binding gate is the base contact (5/6), not confidence.** Relaxing pLDDT from
85 to 80 changes the pass rate by exactly nothing. This matches
[chris-02](experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md)'s finding that the base
contact is the fragile term and the donor is not.

**The gate is not wrong — the designs are.** See the base-contact row below: real Kemp eliminases
sit at 2.5–2.6 Å, measured across six enzymes spanning a 1000-fold activity range. A gate that
accepts 5.91 Å would not be a better gate, it would be a gate that accepts non-enzymes.

## Threshold provenance

| gate | value | source | status |
|---|---|---|---|
| **base contact** `A127 OD2 → 6NT N3` | 2.4–3.6 Å | 7K4U crystal **2.53 Å** (measured twice here, independently); Broom et al. p6 verbatim: *"within hydrogen-bonding distance to the carboxylate oxygen of Asp127 (2.5–2.6 Å distance between heavy atoms)"* — true for **all six** HG variants, HG3 through HG3.17 | **Justified.** An O···N contact beyond ~3.5 Å is not an H-bond. Upper bound widened 3.4→3.6 Å to allow for re-docking slop, which changes nothing. |
| **donor contact** `A50 NE2 → 6NT N1` | 2.6–3.4 Å | 7K4U crystal **3.20 Å**; folded runs 2.94 / 3.08 Å. Standard N···N H-bond is 2.7–3.3 Å | **Justified — deliberately NOT widened.** Widening to 3.9 Å would make sweep_kemp-4 "pass", and that is fitting the threshold to the one design we want. chris-02 already noted its donor at 3.75 Å is "longer than ideal H-bond geometry". |
| **CA RMSD vs design** | ≤ 2.0 Å | chris-02 measured a bimodal split: 0.70 / 1.36 / 1.43 vs 13.67 / 14.63 Å, "nothing between 1.4 and 13.7" | **Justified.** Sits in the empty gap. Correctly rejects zonghu-01's 4.26 Å, the one run that landed inside it. |
| **ipTM** | ≥ 0.6 | observed bimodal: 0.406–0.442 collapsed vs 0.837–0.869 folded | **Justified.** Any value in 0.5–0.8 behaves identically; 0.6 sits in the gap. |
| **mean pLDDT** | ≥ **80** gate, 85 target | `kemp_rfd3_workflow/README.md`: *"Keep pLDDT > 80 (ideally > 85)"*. The organizers' own verified reference scores **83.6**, so a gate at 85 rejects their working example | **Lowered 85 → 80** on that independent document, not on our data. Note it changes no verdict. |
| motif RMSD (stage 1) | < 1.0 Å | RFD3 reports `fixed_pair_distance_max_deviation` 0.013–0.017 Å | Justified but **non-binding** — `select_fixed_atoms` holds the motif rigid, so this is an input, not a result. |
| steric clashes (stage 1) | 0 pairs < 2.2 Å | zonghu-01 job 7 had **6**; all of chris's had 0 | Justified, cheap, and the pipeline records it but never checks it. |
| GRAVY | −1.0 … 0.3 | HG3 −0.077, HG3.17 −0.017, lysozyme −0.150 (verified vs Biopython). zonghu-01's design: **0.401** | Plausible, **not yet validated against any outcome**. |
| pI | 4.0 … 9.5 | assay runs at pH 7.0 | **Soft warning band, not physics.** |
| packing, topology | see script | — | **Unvalidated proxies.** Report them; do not gate on them until they predict something. |

## The deeper problem: the challenge ranks, it does not gate

[challenge.md](challenge.md): scoring is a **ranking** on terms that **multiply**, and
*"There is an optimum, not a direction."* The only true gate is novelty. So binary pass/fail is the
wrong shape for *selection*, even though it is right for *triage*. Use three tiers:

1. **Triage (binary, physically real):** no clashes; did it fold at all (CA RMSD, ipTM); novelty.
   A design failing these is not a candidate at any ranking.
2. **Ranked (optimum, not direction):** base and donor contact, pLDDT, base burial. Score each by
   distance from its optimum and take the best N — do not threshold them.
3. **Report only (unvalidated):** packing proxy, topology fractions, GRAVY/pI windows.

Under that scheme **sweep_kemp-4 is already our best candidate** — best base contact (3.32 Å),
best CA RMSD (0.70 Å), highest pLDDT (94.5) — with a weak donor at 3.75 Å as a known defect.
That is the same conclusion chris-02 reached, reached without moving a single threshold.

## What this means for "run until one passes"

Expected cost at these thresholds is **> 138 min of serial big-node time per hit and plausibly
unbounded**, because 0/6 passed and the binding term is the one the pipeline reproduces worst.
More sampling at ~23 min/design is the expensive way to attack that. Cheaper levers first:

1. **Fix the input, not the sample size.** The base contact is handed to RFD3 as a constraint and
   comes back at 2.53 Å every time; it is Boltz-2 that loses it. A better theozyme
   ([zonghu-01](experiments/zonghu-01_trp-stack-theozyme-vs-crystal.md)'s `_trpopt2`) is a free change.
2. **Rank instead of gate**, per the three tiers above, and judge candidates relatively.
3. **Only then spend GPU**, and spend it on a batch big enough to estimate a rate rather than on a
   loop that terminates on the first lucky draw.
