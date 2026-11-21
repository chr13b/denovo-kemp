# Structures and metrics to test your metric against

{count} Boltz-2 predictions of designed Kemp eliminases cofolded with the transition-state analogue 6NT,
plus our measurements of each. Everything is a PREDICTION; nothing here is wet-lab data.

## Why a spread and not just winners
A metric is only useful if it separates good from bad. So the pack holds the best designs by our geometry
score, an evenly spaced sample down one backbone's ranking, its worst designs, a few mid-range designs from
other backbones, and three designs replicated over 5 Boltz-2 seeds (our closest thing to ground truth).

## Files
- `manifest.tsv`: one row per structure. `group` says why it is here; `D` is our geometry score; `cluster_dir`
  is where the structure, confidence json, **PAE and PDE matrices** (not bundled, 250 KB each) live on the cluster.
- `structures/*.cif` (+ `.confidence.json`): the predicted complexes. Protein is chain A, ligand 6NT is chain B.
- `designs.fasta`: the sequences, headers in the submission format (`base=` / `oxy=` are 1-based indices).
- `structures/crystal__4BS0.cif` and `crystal_contacts_43_ligand_copies.tsv`: the reference crystal (HG3.17 + 6NT).

## Groups
`best` (12 best by D), `spread_seed4` (12 evenly spaced down seed 4's ranking), `worst_seed4` (8 worst),
`midrange_*` (other backbones), `replicated_5seeds` (3 sequences x 5 seeds), `natural_control` (3 natural enzymes).

## What D is (OUR proxy, not the scorer's function)
For the base contact (Asp carboxylate O to 6NT N3) and the donor contact (Gln NE2 to 6NT N1) we measure the
distance, the **approach angle** at the ring nitrogen (angle between the contact atom and the ring centroid)
and the **out-of-plane** angle (contact vector against the benzotriazole plane). Each is compared with the
min-max over 25 engaged crystal copies; D is the total overshoot beyond that range in tolerance units (0.25 A for
distances, 15 degrees for angles), with a too-short distance counted double (the organizers say too short is
penalised harder). D = 0 means inside every crystal range. Crystal ranges:

| quantity | crystal range |
|---|---|
| base distance | 2.41-2.69 A |
| donor distance | 2.92-3.24 A (3.60 counting one ASP+TYR copy) |
| base approach angle | 167-176 deg |
| base out-of-plane | 1-12 deg |
| donor approach angle | 162-173 deg |
| donor out-of-plane | 1-16 deg |

## Things to know before trusting a number
1. **One Boltz-2 prediction is noisy.** The same sequence folded at different seeds moves its base contact by
   0.5-1+ A. The `replicated_5seeds` rows (s024, s059, seed4_original) are the reliable part; judge a metric
   against those first.
2. s024 is our best design (D = 4.8, 3.5, 29.6, 5.3, 3.5 over five seeds); s059 is its mirror image (base right,
   donor end-on); seed4_original is the pipeline's own single sequence, worse than both.
3. Contacts are measured at the DECLARED residues (`base_position`, `donor_position`), as the scorer does, not at
   the nearest atom anywhere. A nearest-atom scan reads equal or shorter and can latch onto the wrong residue.
4. The natural enzymes are folded WITHOUT an MSA and are not a fair reference; their distances use a scan and
   they have no angles.
5. 84 % of all our designs do not put the ligand in the pocket at all (base > 5 A or donor > 6 A); the pack
   deliberately includes such cases.

## Quick start
```python
import pandas as pd
m = pd.read_csv("manifest.tsv", sep="\t")
print(m.groupby("group")["D"].describe())
print(m[["D", "iptm", "complex_ipde", "complex_plddt", "ca_rmsd"]].corr(method="spearman")["D"])
```
Your metric is interesting if it ranks `best` and `replicated_5seeds` (s024) above `worst_seed4`, AND if it still
separates designs WITHIN `spread_seed4`, where every design shares one backbone.
