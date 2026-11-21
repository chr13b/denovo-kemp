# zonghu-01: trp stack theozyme vs crystal

- **Owner:** zonghu
- **Date:** 2026-11-21
- **Status:** running
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

TODO: only numbers read from the run's `summary.json` / `metrics.jsonl`.

## Verdict and next step

TODO
