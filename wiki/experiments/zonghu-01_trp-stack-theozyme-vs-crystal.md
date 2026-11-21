# zonghu-01: trp stack theozyme vs crystal

- **Owner:** zonghu
- **Date:** 2026-11-21
- **Status:** done: inconclusive (the feasibility gate passed; the comparison was not run)
- **Question:** Does handing RFD3 a theozyme with **idealised Trp44 π-stacking** (instead of the
  crystallographic edge-on contact) still scaffold, and does the stacking survive into the Boltz-2 cofold?
- **Why it matters:** Trp44 is the only part of the HG3 motif we can change without touching the scored
  base/donor chemistry. If an idealised stack scaffolds as readily as the crystal pose, it becomes a free
  diversification axis for our 20 slots. If it refuses to scaffold, we stop and keep the crystal geometry.
- **Script + config:** theozyme built by `C:\Users\xiang\kemp_rfd3_workflow\scripts\optimize.py`
  (outside this repo; see [../data.md](../data.md)). Cluster config = the stock
  `Kemp_HG3_17_base_donor` entry with the motif and `unindex` changed, see below.
- **Runs:** `/mnt/work/projects/zonghu_{core,trpopt}_s{1,2}` on `pdh-team`

Status values: `planned`, `running`, `done: supported`, `done: refuted`, `done: inconclusive`, `abandoned`.

## Design

Two theozymes, both derived from **7K4U** (HG3 K50Q + 6NT TS analogue, Otten et al. *Science* 2020).
**6NT, ASP127 and GLN50 are byte-for-byte identical between the two files** — verified by diff — so the
only variable is the Trp44 position.

| | `theozyme_7k4u_core.pdb` (crystal) | `theozyme_7k4u_core_trpopt.pdb` (idealised) |
|---|---|---|
| interplanar angle | 17.5° | 0.0° |
| perpendicular separation | 3.29 Å | 3.45 Å |
| lateral offset (vs benzo ring) | 4.00 Å | 0.00 Å |
| centroid distance | 5.18 Å | 3.45 Å |
| TRP44 CZ3 → ASP127 OD2 | 3.33 Å (crowds the base) | gone |
| ASP127 OD2 → 6NT N3 | 2.53 Å | 2.53 Å (unchanged) |
| GLN50 NE2 → 6NT N1 | 3.20 Å | 3.20 Å (unchanged) |

The crystal pose is an **edge-on contact**, not a stack: at a 4.00 Å lateral offset only TRP44 CE3 is
close (3.51 Å to C4). In the idealised pose all nine 6NT ring atoms sit 3.45–4.01 Å from the indole.
Offset 0.00 Å on the benzo ring is deliberate: 6NT is electron-poor (nitro + triazole, mimicking a
delocalised anion) and indole is electron-rich, so near-cofacial donor–acceptor stacking is favoured
here, unlike the benzene dimer. Between the two *bicyclic* systems the offset is 1.84 Å.

4 jobs, 2 seeds per theozyme (seeds 1 and 2, changed in all three places as in chris-02):

| project | theozyme | seed |
|---|---|---|
| `zonghu_core_s1` | crystal | 1 |
| `zonghu_core_s2` | crystal | 2 |
| `zonghu_trpopt_s1` | idealised | 1 |
| `zonghu_trpopt_s2` | idealised | 2 |

### Changes to the stock pipeline (project copies only — the example is untouched)

1. `inputs/HG3_17_kemp_motif.pdb` **overwritten** with the theozyme. Necessary, not cosmetic:
   `prepare_rfd3_input.py` overwrites `specification["input"]` with that exact path, so editing the
   `input` field in `Kemp.json` has no effect. `prepare_ligandmpnn.py` also reads this file as the
   geometry *reference*, so overwriting it keeps the reference self-consistent.
2. `inputs/Kemp.json`, key `Kemp_HG3_17_base_donor` (the key name is hardcoded in both helpers and in
   `json_keys_subset`, so it is kept): `unindex` `A50,A127` → **`A44,A50,A127`**, and `select_fixed_atoms`
   gains `"A44": "CD2,CE2,CE3,CZ2,CZ3,CH2"` — the six-membered indole ring, i.e. the stacking plane
   itself. `contig` stays `260-260` to match the chris-01 baseline.
3. `src/prepare_ligandmpnn.py`: added `("A44", "TRP", "W", ("CD2", "CE2", "CZ2"))` to the mapping loop.
   Without this, Trp44 is not in `fixed_residues.txt` and LigandMPNN is free to mutate the tryptophan
   away, which would erase the variable under test. This also extends the
   `fixed_pair_distance_max_deviation` check to the Trp, so we find out whether RFD3 really held it.

Changes 1–3 deviate from what the launcher helpers assert, so **validation warnings are expected** in
`summary.json`. In project mode these warn and pass the real structure through; they are not failures.
Every warning is reported in the Result section below verbatim.

### Pre-registered decision rule

Judged on **Boltz-2** output only — per [../challenge.md](../challenge.md), RFD3 contact distances are an
input, not a result (they come back at the fixed 2.53 Å regardless).

- **Scaffolds at all:** `pipeline_completed: true` and `fixed_pair_distance_max_deviation ≤ 0.05 Å`
  for all three motif residues. If the idealised theozyme fails this where the crystal one passes, the
  idealised geometry is unscaffoldable → stop, keep the crystal pose.
- **Trp survived:** the residue at the mapped A44 position is `W` in the LigandMPNN sequence.
- **Stacking survived the cofold:** re-measure interplanar angle and offset in the Boltz-2 structure
  with `kemp_rfd3_workflow/scripts/analyze.py`.
- **n = 2 per arm cannot rank the two theozymes** and this experiment does not claim to.
  chris-02 measured the Boltz base contact ranging 3.32–21.92 Å across seeds, with ~half of designs
  failing to refold at all. This is a **feasibility test**: does a custom theozyme survive the pipeline,
  and does the Trp constraint cost us scaffolding success? A ranking would need ≫ 2 seeds per arm.

## Result

**Only 1 of the 4 planned jobs ran.** Job `7` (idealised theozyme, seed 1) completed; jobs `8`, `9`, `10`
were cancelled with `scancel` before starting, to hand the shared GPU node back. **Both crystal-theozyme
control arms are therefore missing**, which is what makes this inconclusive — see the Verdict.

Every number below is read from
[../../results/zonghu-01_trpopt_kemp-7_summary.json](../../results/zonghu-01_trpopt_kemp-7_summary.json).

### The feasibility gate: passed

| Check | Result |
|---|---|
| `pipeline_completed` | `true`, status `completed_with_warnings` |
| `validation_warnings` | exactly the 2 predicted (`prepare_rfd3_input.py`, motif/fixed-atom asserts) |
| RFD3 held the motif | `fixed_pair_distance_max_deviation` = **0.0167 Å** (tolerance 0.05) |
| all 3 residues mapped | `A50→A237 Q`, `A127→A54 D`, **`A44→A98 W`** |
| **Trp survived into the sequence** | `seq[98] = W` ✅ (also `seq[54] = D`, `seq[237] = Q`) |
| protein length | 260 |

So a custom theozyme does go through the stock pipeline, and the `prepare_ligandmpnn.py` patch works:
without it position 98 would not have been fixed.

### The design itself: fails the dominant scoring term

| Metric | RFD3 | Boltz-2 | chris-02 range (stock motif, folded runs) |
|---|---|---|---|
| base `A127_OD2 → 6NT_N3` | 2.532 Å | **11.99 Å** | 3.32 / 5.91 / 8.33 Å |
| donor `A50_NE2 → 6NT_N1` | 3.196 Å | **26.49 Å** | 2.94 / 3.08 / 3.75 Å |
| CA RMSD from RFD3 | — | **4.26 Å** | 0.70 / 1.36 / 1.43 (collapsed: 13.67 / 14.63) |
| `complex_ipde` | — | 1.665 | 1.52 – 1.87 (collapsed: 5.50 – 6.74) |
| min ligand–protein dist | **1.655 Å** | 2.473 Å | — |
| pairs < 2.2 Å | **6** | 0 | 0 |

Boltz-2 confidence was otherwise good: `complex_plddt` 0.773, `ptm` 0.886, `iptm` 0.869 — but
`pair_chains_iptm[protein][ligand]` is only **0.350**. MSA depth was **12**, unlike the depth-1 design in
chris-01; the sequence contains `…VLGGWSLGGAIA…`, a `GxSxG`-like motif, so MMseqs2 found homologues.
That is a novelty flag (TM ≤ 0.7 gate), not a win.

**Not a submission candidate.** Geometry dominates scoring and the terms multiply, so a 12 Å base contact
is disqualifying on its own. Not added to `results/designs.jsonl`.

### Two observations that generalise beyond this run

**1. A third failure mode: the fold is fine, the ligand binds elsewhere.** chris-02 found refolding to be
near-binary — CA RMSD either 0.70–1.43 Å or 13.67–14.63 Å, "nothing between 1.4 and 13.7". This run lands
at **4.26 Å, inside that gap**, with `complex_ipde` 1.665 (squarely in chris-02's *folded* range) and no
clashes, yet the ligand sits 12 Å from the base and 26 Å from the donor at a different surface site
(min ligand–protein distance 2.47 Å, so it is bound to *something*). One run does not refute "refolding is
binary", but it shows the dichotomy is not exhaustive.

**2. `complex_ipde` did not detect this failure.** iPDE 1.665 here is better than chris-01's 1.867, a run
whose ligand *was* in the site. If we build a cheap filter on iPDE (chris-02 next-step 2), this run is a
counter-example: **iPDE can look healthy while the ligand is in the wrong place.** Filter on the base and
donor contact distances themselves, not on iPDE alone.

### The RFD3 clash — and a correction

> **Correction (same day, before any follow-up GPU run).** The paragraph below originally argued that the
> cofacial pose "leaves the attachment end nowhere to go but into the nitro group". **That was wrong, and
> measuring it refuted it.** `scripts/attach.py` reports the clearance of exactly the atoms RFD3 is free
> to move:
>
> | pose | attachment end (CB/CG/CD1/NE1) min to ligand | backbone min to ligand | ring centroid radial offset |
> |---|---|---|---|
> | crystal | 3.86 Å | 5.11 Å | 4.02 Å |
> | idealised (`_trpopt`) | 3.48 Å | **5.81 Å** | 0.92 Å |
> | repaired (`_trpopt2`) | **3.97 Å** | **6.04 Å** | 0.92 Å |
>
> The idealised pose had *more* backbone room than the crystal, and a clash-free attachment plainly exists
> — `_trpopt2` reaches better clearance than the crystal on both measures **while keeping a cofacial stack**
> (perp 3.65 Å, offset 0.00 Å, interplanar 0.0°; it costs 0.20 Å of stacking distance). So the pose was not
> the cause. **The cause was under-constraint:** `select_fixed_atoms` pinned only the six-membered ring, and
> RFD3 moved CD1/NE1/CB by roughly 1 Å — which it should not be able to do at all, since the indole is a
> rigid fused ring system. The remaining, weaker version of the original idea is that a face-centred ring
> (radial offset 0.92 Å vs 4.02 Å) leaves a *smaller fraction* of RFD3's allowed placements clash-free; that
> is plausible and still untested.



RFD3 produced **6 protein–ligand pairs below 2.2 Å (min 1.655 Å)**; chris's runs had 0 and a 2.53 Å minimum.
Note the pipeline *records* this and never checks it, so it does not appear as a warning. Every clash is
against the **nitro group**:

| protein atom | ligand atom | distance |
|---|---|---|
| A99 SER N | O21 | 1.66 Å |
| A122 ILE O | O11 | 1.80 Å |
| A99 SER CB | O21 | 1.94 Å |
| A98 TRP C (motif) | O21 | 2.04 Å |
| A98 TRP CB (motif) | O11 | 2.05 Å |
| A99 SER CA | O21 | 2.16 Å |

The clashing atoms are the Trp's **attachment end** — CB, CG, CD1, backbone C — plus the next residue,
Ser99. Not the stacking ring, which stayed where it was put. Mechanism: `select_fixed_atoms` pinned only
the six-membered indole ring (`CD2,CE2,CE3,CZ2,CZ3,CH2`), leaving CB, CG, CD1, NE1 and the backbone free.
Laying that ring flat over the ligand at 3.45 Å forces the side chain to attach from one edge, and in the
cofacial pose the only free direction points at the nitro substituent. In the theozyme *file* those atoms
were clear (CB ≥ 3.25 Å from any ligand atom, backbone 5.81 Å); RFD3 moved them, never having been told not
to. It is a plausible — but untested — reason the Boltz-2 ligand left the site, since LigandMPNN designed a
sequence for a pocket with the ligand jammed into it.

**The fix, applied (laptop only, no GPU):** `theozyme_7k4u_core_trpopt2.pdb` and
`..._extended_trpopt2.pdb`, built with the attachment end and backbone constrained to at least the crystal's
clearance. Thresholds are calibrated to the crystal pose rather than chosen by me: CB/CG/CD1/NE1 ≥ 3.90 Å
and backbone ≥ 5.10 Å from any ligand atom. The same placement satisfies both the core and extended
constraint sets, so it does not clash with Thr265 or Phe267 either. ASP127, GLN50 and 6NT remain
byte-for-byte unchanged, and Trp44 keeps the canonical p-90 rotamer (chi1 68.8°, chi2 −78.3°).

**And the constraint that actually matters:** the new configs pin the **whole indole**
(`CG,CD1,CD2,NE1,CE2,CE3,CZ2,CZ3,CH2`), not just the six-ring. The indole cannot bend, so pinning 6 of its
9 atoms was never physically coherent; it is what let RFD3 move the attachment end. The cost is 3 more
fixed atoms, which lowers scaffolding success — that trade is the thing the next run should measure.

## Verdict and next step

**The pre-registered question "does a custom theozyme scaffold?" → yes.** Pipeline completes, RFD3 holds
all three residues to 0.0167 Å, and the Trp reaches the final sequence.

**The pre-registered comparison → not answered, and this run cannot answer it.** With the control arms
cancelled there is n = 1 and no crystal baseline at matched settings. Specifically, **11.99 Å sits inside
the 3.32–21.92 Å base-contact range chris-02 measured with the *stock* motif**, so this result is fully
consistent with ordinary pipeline variance and is *not* evidence against the idealised theozyme. The one
finding I would defend from n = 1 is the RFD3 clash, because it has a geometric mechanism rather than
depending on a seed.

Next steps, cheapest first:

1. ~~Fix the theozyme before spending more GPU.~~ **Done** — `_trpopt2`, see above. No lateral offset was
   needed: the cofacial stack survives, at 3.65 Å instead of 3.45 Å.
2. ~~Also pin `CG` (and ideally `CD1`).~~ **Done** — the whole indole is pinned in the new configs.
3. **Run the real comparison when the GPU is free**, 3 arms × 2 seeds = 6 jobs ≈ 2.3 h serial:
   crystal (`theozyme_7k4u_core.pdb`), `_trpopt` (six-ring pinned, the job-7 setup) and `_trpopt2`
   (whole indole pinned). Arm 2 vs 3 isolates **the pinning change**; arm 1 vs 3 isolates **the geometry**.
   Read `ligand_protein_pairs_below_2_2_angstrom` first — the prediction is that it drops to 0 for
   `_trpopt2`. The `zonghu_core_s1` / `_s2` folders survive, configured and ready:
   `bash /mnt/work/projects/zonghu_core_s1/run.sh`.
4. Tell the team that **iPDE alone is not a safe refold filter** (observation 2 above) before anyone builds
   a screening pipeline on it.
5. Worth considering: `ligand_protein_pairs_below_2_2_angstrom` is recorded by the pipeline and **never
   checked**. A one-line addition to our own tooling would turn it into a free pre-filter on RFD3 output —
   unlike the contact distances, it is not constant by construction, so it carries information.
