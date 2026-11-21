# flavia-01: theozyme target geometry

- **Owner:** flavia
- **Date:** 2026-11-21
- **Status:** done: supported
- **Question:** What catalytic geometry does a Kemp eliminase that actually works hold the ligand in,
  measured rather than assumed?
- **Why it matters:** Geometry dominates scoring and the terms multiply ([challenge.md](../challenge.md)),
  but until now we had no measured target. "Closer is better" is wrong — each distance is scored against
  an optimum, and too short is punished harder than too long. These numbers are what a design aims at,
  and what a local scoring filter would compare against.
- **Script + config:** `scripts/30_measure_theozyme_geometry.py` + `configs/flavia-01.json`
- **Runs:** `runs/20261121-140257_flavia-01/` at commit `710f1ff`, ~0.3 s on a laptop. No cluster time.

## Source

**PDB 7K4Z** — Kemp eliminase HG3.17 bound to 6-nitrobenzotriazole (ligand **6NT**) at 1.08 Å. Same
ligand the organizers cofold every design against, in an enzyme with measured activity. Registered in
[data.md](../data.md).

HG3.17 is a **geometry reference only**. It is ineligible as a design under the novelty rules
(TM ≤ 0.7, identity ≤ 70 %), so we copy the arrangement and never the fold or the sequence.

## Result

All numbers read from `runs/20261121-140257_flavia-01/summary.json`.

| | Base | Oxyanion donor |
|---|---|---|
| Residue / atom | ASP127 OD2 | GLN50 NE2 |
| Ligand atom | 6NT **N3** | 6NT **N1** |
| **Distance** | **2.51 Å** | **3.10 Å** |
| **In-plane deviation** | **5.3°** | **6.5°** |
| **Out-of-plane deviation** | **7.3°** | **2.8°** |
| Angle at the partner atom | 128.5° | 134.0° |

Also: N3–H···OD2 angle **165.4°**, H···O **1.67 Å** (the crystal models that hydrogen; Boltz-2 will
not give us one). Base burial: **47 Cα atoms within 12 Å** of ASP127 CG. Theozyme: 33 atoms, 3 residues.

Pocket within 5 Å of the ligand: TRP44, PRO45, GLU46, ALA82, GLY83, CYS84, TRP87, MET172, LEU236,
MET237, THR265, VAL266, MET267, ALA21.

### Which ligand atom plays which role

6NT is a triazole standing in for the substrate's isoxazole, so the ring atoms correspond:

| Benzisoxazole (substrate) | 6NT (analogue) | Role |
|---|---|---|
| C3–H | **N3–H** | the proton the base removes |
| N2 | N2 | — |
| O1 | **N1** | the leaving oxygen that takes the developing charge |

The script does not assume this. It takes the nearest allowed base to N3 and the nearest allowed donor
to N1 and recovers ASP127 and GLN50 on its own, which is the check that the mapping is right. It also
rejects any contact outside hydrogen-bonding range rather than emitting a target that would mislead a
design run. Independently, the crystal models hydrogen H3 on N3, which is where the acidic proton sits.

## Verdict and next step

**Both contacts are nearly coplanar with the aromatic ring — under 8° out of plane.** That is the bar a
real enzyme meets, and the scorer keeps the *worse* of the in-plane and out-of-plane terms rather than
averaging them, so a contact that looks right face-on can still score badly. The base sits noticeably
closer than the donor (2.51 Å vs 3.10 Å); that asymmetry is real, not noise — the base is doing
chemistry, the donor is stabilising charge.

**This sharpens the open question in [chris-01](chris-01_reference-pipeline-baseline.md).** There, the
reference design's base contact was 2.53 Å in RFD3's output and **5.91 Å** after the Boltz-2 refold.
RFD3 placed the base within 0.02 Å of what a working enzyme holds, and the refold — which is what gets
scored — threw it away. The donor survived (3.09 → 2.94 Å, against a 3.10 Å target). So the drift
chris-02 is measuring is not a small perturbation of a roughly-right pose; it is the one contact that
carries the most scoring weight moving several Å off a target we can now name.

Next:

1. A local scoring filter over these terms, so candidates are ranked before they take GPU time or one of
   our 20 submission slots. `kemp.geometry.contact_geometry` and `count_ca_within` already compute them
   for any structure with a ligand, not just this one. This is the **Scoring** track in
   [team.md](../team.md), which nobody had claimed.
2. Feed chris-02's seed sweep through that filter: if the base contact drifts on every seed, the fix is
   upstream of seed choice.
