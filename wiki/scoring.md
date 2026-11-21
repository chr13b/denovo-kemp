# Scoring: the organizers' five criteria, and a metric for each

What the organizers actually score, as opposed to what is convenient to measure.
Source: `raw/20261121_organizers_submission.md`, via `wiki/challenge.md`.

The terms **multiply**. One weak factor is not repairable by strength elsewhere,
which is why the combined score below is a product and not a sum.

| # | Criterion | Our metric | Where |
|---|---|---|---|
| K1 | Contact distances base→N3, donor→N1 | `check_ligand_contacts` | `src/kemp/structure.py` |
| K2 | Approach geometry: angle **and** ring plane | `check_approach_geometry` | `src/kemp/structure.py` |
| K3 | Interface confidence **iPDE** | `check_interface_error` | `src/kemp/filters.py` |
| K4 | Active-site packing (CA within 12 Å of the base) | `check_base_burial` | `src/kemp/structure.py` |
| K5 | Pose consistency across replicate predictions | **missing** — see below | — |

K1 and K2 together outweigh everything else combined.

## The correction that prompted this page

Until 2026-11-22 the funnel gated on **mean pLDDT ≥ 80** and **ipTM ≥ 0.6**.
Neither is on the organizers' list. The scored confidence term is **iPDE**, it was
present in every `summary.json` as `complex_ipde`, and it was never used.

They disagree, and not marginally: `zonghu_vA_s2` has pLDDT **86.1**, which reads
as comfortably good, and iPDE **2.42**, which ranks **10th of 14**. Gating on
pLDDT selected on a quantity nobody scores.

`check_boltz_confidence` still exists, because fold quality is worth knowing, but
its docstring now says plainly that it is not a scored criterion.

## K2 in detail: the worse of the two decides

The organizers are explicit that the angle term and the in-plane term **do not
average** — the worse of the two sets the score. `check_approach_geometry`
therefore returns `max(|Δangle|, |Δout-of-plane|)`. A good angle cannot buy off a
bad ring plane.

Reference geometry, measured from 7K4U twice independently:

| | angle | out of plane |
|---|---|---|
| base (Asp127 CG–OD2···N3) | 133.1° | −6.7° |
| donor (Gln50 CD–NE2···N1) | 140.8° | −10.4° |

Validated against ground truth: the crystal reproduces its own reference values
with **0 deviation** (`tests/test_criteria.py`).

Why the plane term matters chemically: the N3–H of the TS analogue lies **in** the
triazole plane. A base approaching from the ring *face* is not on the proton
transfer axis, however good its distance looks. K1 alone cannot see this.

## Combined score

`scripts/33_combine_criteria.py`. Each criterion maps to a sub-score in [0, 1],
and the five are multiplied.

Results over all 16 designs the team had on 2026-11-22
(`results/criteria/five_criteria_n16.json`):

| Rank | Design | Product | Limited by |
|---|---|---|---|
| 1 | **`zonghu_vA_s2`** | **0.2965** | K2 (0.430) |
| 2 | `chris_seedsweep_s4` | 0.1188 | K2 (0.138) |
| 3 | `zonghu_ms_s1` | 0.0382 | K2 (0.107) |
| 4 | `zonghu_vA_s3` | 0.0318 | K1 donor |
| 5 | `zonghu_ms_s2` | 0.0106 | K1 donor |
| 6 | `zonghu_g10_s3` | 0.0025 | K1 donor |

`zonghu_vA_s2` leads by a factor of **2.5** — a wider margin than any single
criterion suggests, because it is the only design with no weak factor. That is
what a product is for.

**K2 is the bottleneck for all three leaders, without exception.** Below them the
binding constraint switches to the donor distance. Approach geometry is therefore
where the remaining headroom is, and the `select_hbond_*` variant (jobs 78–80) was
the first attempt at it.

## The criteria are not redundant

Checked because five correlated metrics would be one metric with extra steps.
Spearman between criteria over n = 15:

| | K1 base | K1 donor | K2 | K3 | K4 |
|---|---|---|---|---|---|
| **K1 base** | – | 0.50 | 0.58 | 0.38 | −0.34 |
| **K1 donor** | 0.50 | – | 0.40 | 0.33 | −0.27 |
| **K2** | 0.58 | 0.40 | – | 0.27 | −0.40 |
| **K3** | 0.38 | 0.33 | 0.27 | – | −0.21 |
| **K4** | −0.34 | −0.27 | −0.40 | −0.21 | – |

Nothing is near ±1, so every criterion carries its own information and none can
be dropped. All five also have wide spreads (K2 from 23° to 120°, K4 from 20 to
55 CA), so none is a constant that merely looks like a filter.

K4 correlates **negatively** with the distance terms, i.e. a more buried base goes
with better contacts. Physically sensible, and in the right direction.

## What is not sound here

- **The sub-score shapes are ours, not the organizers'.** H-bond optimum 2.9 Å,
  asymmetric so that too short is punished harder than too long (as the brief
  states), K2 on a 42° scale, K3 linear from 1.4 to 5.0, K4 saturating at 50 CA.
  The organizers' functional forms are unknown. **The ranking is robust** —
  `vA_s2` leads under any sensible parametrisation — but the absolute products are
  not the organizers' points and should not be quoted as a score.
- **K5 has never been measured.** Pose consistency needs several Boltz-2
  predictions of the *same* sequence; the pipeline makes exactly one
  (`diffusion_samples 1`, one seed) while the organizers use 5 replicates. It is
  deliberately **not** set to 1.0 in the product, so the score is not flattered by
  a missing term. Replicate runs for `vA_s2` and `vA_s3` are jobs 81/82.
- **Thresholds are empirical.** iPDE 2.0 and burial 45 CA come from the observed
  split across 16 designs, not from physics or from the organizers.

## There is no cheap pre-filter

Tested, because 23 min per design is the binding cost and a pre-filter would
multiply throughput. Over 11 designs with a known Boltz-2 outcome, no RFD3-stage
feature predicts success: radius of gyration, helix/sheet/coil fractions, clash
count and **base burial measured on the RFD3 backbone** all give |ρ| < 0.6, which
at n = 11 is indistinguishable from noise.

The reason is visible in the raw numbers: the RFD3 backbones are nearly identical
to each other (RoG 16.1–17.0 Å, helix 0.42–0.54) while the outcomes range from
2.27 Å to 13.21 Å on the base contact. **What decides the outcome happens entirely
inside LigandMPNN and Boltz-2**, downstream of everything we can measure cheaply.

Consequence: stage-1 gating is a **defect filter**, not a quality filter. It saves
23 min on broken backbones and does nothing else. The only throughput levers left
are dropping the MSA (untested) and folding more sequences per backbone.

## Related

- `wiki/novelty.md` — the hard gate, which is not a ranking term
- `wiki/design-filters.md` — threshold provenance for the funnel's other filters
- `wiki/experiments/zonghu-03_trp-flexibility-and-dyad-geometry.md` — where these designs come from
- `tests/test_criteria.py` — K2 validated against the crystal
