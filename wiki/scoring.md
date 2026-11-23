# Scoring: the organizers' five criteria, and a metric for each

What the organizers actually score, as opposed to what is convenient to measure.
Source: the organizers' submission document (not included), via `wiki/challenge.md`.

The terms **multiply**. One weak factor is not repairable by strength elsewhere,
which is why the combined score below is a product and not a sum.

| # | Criterion | Our metric | Where |
|---|---|---|---|
| K1 | Contact distances base→N3, donor→N1 | `check_ligand_contacts` | `src/kemp/structure.py` |
| K2 | Approach geometry: angle **and** ring plane | `check_approach_geometry` | `src/kemp/structure.py` |
| K3 | Interface confidence **iPDE** | `check_interface_error` | `src/kemp/filters.py` |
| K4 | Active-site packing (CA within 12 Å of the base) | `check_base_burial` | `src/kemp/structure.py` |
| K5 | Pose consistency: spread of the metrics across Boltz-2 seeds | `scripts/36_score_v2_weighted.py` | measured, jobs 81/82 |

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

Superseded by scorer v2 below; the v1 script has been deleted. Each criterion mapped
to a sub-score in [0, 1] and the five were multiplied.

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

## Scorer v2: what the precised criteria changed

The organizers' restatement (2026-11-22) named three things v1 got wrong and made
the fifth criterion measurable. All four are fixed in
`scripts/36_score_v2_weighted.py`.

### 1. The two contacts have different target distances

> scored against a target taken from crystal structures of working Kemp eliminases
> and from textbook hydrogen-bond geometry, which agree

So the target is measurable, not a matter of taste. Measured in 7K4U by
`scripts/37_measure_crystal_reference.py`:

| contact | crystal | textbook N-H···O | agree? |
|---|---|---|---|
| base Asp127 OD2···N3 | **2.535 Å** | 2.8–3.0 Å | **no, 0.27 Å shorter** |
| donor Gln50 NE2···N1 | **3.197 Å** | 2.8–3.0 Å | yes, within 0.2 Å |

v1 used a single 2.9 Å optimum for both contacts. That was wrong twice over: the
two targets differ by 0.66 Å from each other, and neither equals 2.9.

**This is an open question for the organizers.** The brief says crystal and
textbook agree; for the base they do not. 2.535 Å is a short, strong hydrogen
bond — chemically plausible for a catalytic base against a TS analogue — but it
is outside the textbook range. The choice matters: scoring `vA_s2`'s base contact
of 3.65 Å against 2.535 Å gives 0.42, against 2.9 Å it gives 0.68.

### 2. A real dihedral, and a bug it exposed

> distance, angle and dihedral measurements

v1 had only an SVD plane deviation. v2 measures the proper torsion
contact–ring_atom–nb1–nb2, and the two agree on the crystal (nearly in-plane),
which cross-validates both.

**The first implementation was wrong.** It compared *signed* dihedrals against the
crystal's +166.8° (base) and −164.0° (donor). The sign only says which side of the
plane the contact leans to, and both sides are chemically equivalent, so a
mirror-image approach was punished by ~330°. That drove `s_approach` to 0.000 for
14 of 16 designs. The correct planarity measure is **180 − |dihedral|**, which
makes the crystal reference 13.2° (base) and 16.0° (donor). After the fix, `vA_s2`
moved from 70° to 58° worst deviation and `chris_seedsweep_s4` from 124° to 92°.

### 3. Weights, not a bare product

> Geometry — items 1 and 2 together — outweighs everything else combined

A bare product cannot express that. v2 uses a **weighted geometric mean**, so
weights become exponents:

| term | weight |
|---|---|
| contact distances | 0.33 |
| approach geometry | 0.22 |
| iPDE | 0.15 |
| base burial | 0.15 |
| pose consistency | 0.15 |

Geometry sums to 0.55 against 0.45 for everything else, and distances carry more
than approach, as the brief states. Multiplicative behaviour is kept — a zero in
any term still collapses the score.

### 4. Pose consistency, measured at last

> how well metrics are reproduced across multiple Boltz-2 seeds, serves as a proxy
> for preorganization

So K5 is the **spread of the metrics**, not a ligand RMSD. Jobs 81/82 refolded one
fixed sequence with five Boltz-2 seeds each (`results/criteria/consistency.json`):

| design | base contact across 5 seeds | std | donor contact | std | K5 |
|---|---|---|---|---|---|
| `zonghu_vA_s2` | 2.48, 3.65, 3.65, 2.73, 2.82 | 0.55 Å | 4.61, 3.00, 3.37, 3.56, 4.94 | 0.83 Å | 0.290 |
| `zonghu_vA_s3` | 5.59, 10.84, 5.83, 4.87, 7.98 | 2.43 Å | 10.52, 14.01, 7.26, 6.98, 9.27 | 2.86 Å | 0.000 |

**This is the most consequential result of the session, and it is bad news for our
own headline number.** The single prediction we had been quoting for `vA_s2` was
base 3.65 / donor 3.00. Across five seeds the donor ranges 3.00–4.94 Å with a mean
of 3.90: **the 3.00 Å we celebrated was the best of five draws, not a property of
the design.** The base 3.65 Å was, conversely, the worst of its five. Neither
number was representative, and reporting a single seed overstated the design.

`vA_s3` is simply not reproducible — the ligand lands anywhere from 4.9 to 14.0 Å
from the base. It led on K2 and K3 in v1, which now looks like an artefact of one
lucky draw. Any design ranked on a single Boltz-2 prediction is ranked on noise.

### v2 ranking

| Rank | Design | Total | weakest term | K2 worst |
|---|---|---|---|---|
| 1 | **`zonghu_vA_s2`** | **0.3090** | approach 0.064 | donor angle 58° |
| 2 | `chris_seedsweep_s4` | 0.1363 | approach 0.001 | donor ring plane 92° |
| 3 | `zonghu_ms_s1` | 0.0053 | approach 0.000 | donor ring plane 129° |
| 4 | `zonghu_vA_s3` | 0.0002 | **consistency 0.000** | donor angle 115° |

Everything below is numerically zero. **Only two designs are non-negligible**, and
both are limited by approach geometry on the **donor** — the same contact the
rigid-indole experiment in zonghu-03 showed to be the fragile one.

### Two corrections to earlier conclusions

- **Dropping the MSA to gain throughput is off the table.** The brief states
  designs are folded *with* MSAs, so screening without one would measure a
  different quantity than the organizers score. `wiki/scoring.md` previously
  listed this as one of two remaining throughput levers; it is not one.
- **The brief says "Four criteria" and then lists five.** The grouping in the same
  paragraph ("Geometry — items 1 and 2 together") resolves it: geometry is one
  criterion with two parts. v2's weights follow that reading.

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
- **K5 is now measured for two designs only** (`vA_s2`, `vA_s3`), because each
  one costs five Boltz-2 runs. For every other design the term is left out of the
  weighted mean rather than set to 1.0, so an unmeasured design is neither
  rewarded nor punished for it — but it also means the other 14 totals are not
  directly comparable to the two that carry a K5 term.
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
23 min on broken backbones and does nothing else.

The one throughput lever left is folding more sequences per backbone. Dropping the
MSA, considered earlier, is **not** available: the brief states designs are folded
with MSAs, so a screen without one would not measure what is scored.

## Related

- `wiki/novelty.md` — the hard gate, which is not a ranking term
- `wiki/design-filters.md` — threshold provenance for the funnel's other filters
- `wiki/experiments/zonghu-03_trp-flexibility-and-dyad-geometry.md` — where these designs come from
- `tests/test_criteria.py` — K2 validated against the crystal
