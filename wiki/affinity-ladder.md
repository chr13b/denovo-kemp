# Affinity ladder: scoring transition-state discrimination

Cofold one sequence with the **substrate**, the **TS analogue** and the **product**, predict a
binding affinity for each with Boltz-2, and report how much worse the substrate and product bind
than the TS analogue.

Built in [experiments/zonghu-02…](experiments/zonghu-02_affinity-ladder-controls.md).
Code: [`scripts/20_build_affinity_ladder.py`](../scripts/20_build_affinity_ladder.py),
[`scripts/21_report_affinity_ladder.py`](../scripts/21_report_affinity_ladder.py),
[`src/kemp/ligands.py`](../src/kemp/ligands.py).

## Why this is worth measuring

An enzyme accelerates a reaction by binding the **transition state** more tightly than the ground
state: `k_cat/k_uncat ≈ K_S / K_TS`. So the physically meaningful design target is not "does the
ligand bind" but **"is the TS bound more tightly than the substrate"**. That is a different and more
causal question than the geometry term in [challenge.md](challenge.md), which asks whether the
*arrangement* looks productive. A design can have textbook geometry and still not discriminate.

Product release matters too: if the product binds as tightly as the TS, the enzyme inhibits itself.

## The ladder

All three verified with RDKit on 2026-11-21 — see [data.md](data.md):

| key | molecule | SMILES | formula | MW | heavy atoms |
|---|---|---|---|---|---|
| `substrate` | 5-nitrobenzisoxazole | `O=[N+]([O-])c1ccc2oncc2c1` | C7H4N2O3 | 164.12 | 12 |
| `ts_analog` | 6-nitrobenzotriazole | `O=[N+]([O-])c1ccc2nn[nH]c2c1` | C6H4N4O2 | 164.12 | 12 |
| `product` | 2-cyano-4-nitrophenol | `N#Cc1cc([N+](=O)[O-])ccc1O` | C7H4N2O3 | 164.12 | 12 |

Two properties make this an unusually clean comparison:

- **Mass and size are matched exactly** — same MW to 2 dp, same heavy-atom count. Boltz-2 has an
  `--affinity_mw_correction` option and a size-dependent accuracy warning, so a ladder where the
  molecules differ in size would confound affinity with molecular weight. This one cannot.
- **`ts_analog` has the same InChIKey as CCD `6NT`** (`AOCDQWRMYHJTMY-UHFFFAOYSA-N`), the component
  the organizers' pipeline cofolds. The ladder is therefore comparable to our RFD3/Boltz runs.

substrate → product is a true isomerisation (both C7H4N2O3), as Kemp elimination requires.

## Reading the output

Boltz-2 reports `affinity_pred_value` = **log10(IC50), IC50 in µM**, so lower means tighter.
One decade = `R·T·ln(10)` = **1.364 kcal/mol** at 298 K. The report converts differences to kcal/mol:

```
ddG(X − TS) = 1.364 × [ log10IC50(X) − log10IC50(TS) ]
```

**Positive ddG = that ligand binds more weakly than the TS analogue = the direction catalysis needs**,
for both the substrate and the product. The µM offset cancels in the difference, so only differences
are meaningful; `pseudo_dg_kcal` exists for readability and is *not* an absolute binding energy.

Boltz-2 also reports `affinity_probability_binary` (0–1, binder vs decoy). Per the Boltz-2 README
these two heads are trained on different data for different purposes: the probability is for
**hit discovery**, and `affinity_pred_value` is for **"how affinity changes with small modifications
of the molecule"** — which is exactly this use case.

## How to run it

```bash
# 1. build the bundle (laptop, no GPU)
uv run python scripts/20_build_affinity_ladder.py --label=mydesign --sequence=MVDAD... --seeds=3
# 2. ship + launch (the command lines are printed by step 1)
# 3. bring out/ back, then
uv run python scripts/21_report_affinity_ladder.py --out=<local out dir> --label=mydesign
```

**It does not need the big GPU node.** There is no MMseqs2 step, so the job asks for
`g6.xlarge` / 4 CPU / 14 GB, which means **two can run at once** on the `l4small` nodes and the
team's RFD3 pipeline keeps `g6.2xlarge`. (`l4big` is never used.) Compute nodes have no internet, so
`run.sh` symlinks the staged weights into the Boltz cache — Boltz resolves the affinity checkpoint
as `<cache>/boltz2_aff.ckpt` and therefore never downloads.

MSA defaults to `empty` (Boltz-2 single-sequence mode). That lowers absolute structure confidence,
but it is **identical across the three ligands**, so it cannot bias the difference between them.
Pass `--msa=<path to an .a3m on the cluster>` to reuse an alignment from an earlier run.

## There is no experimental substrate-binding constant to validate against

This is the single most important thing to know before reading a ladder result.

Table 1 of [Broom et al.](https://www.biorxiv.org/content/10.1101/2020.03.19.999235v1.full)
reports the HG series as **k_cat/K_M only**, with this footnote, verbatim:

> "Individual parameters *K*<sub>M</sub> and *k*<sub>cat</sub> could not be determined accurately
> because saturation was not possible at the maximum substrate concentration tested (2 mM)."

So for the best-characterised Kemp eliminases in existence, **K_M was never measured** — these
enzymes bind 5-nitrobenzisoxazole too weakly to saturate at 2 mM. Two consequences:

1. **"Substrate binding affinity" has no published ground truth here.** Any claim this pipeline
   makes about substrate binding cannot be checked against experiment for this series.
2. **k_cat/K_M is the right target anyway.** Transition-state theory makes k_cat/K_M the free-energy
   difference between the transition state and *free* enzyme + *free* substrate — i.e. it is a
   measure of **transition-state affinity**, which is exactly what the ladder's reference leg
   estimates. So validate against k_cat/K_M, and do not claim to validate K_M.

It also means the real affinities are **≥ mM**, i.e. log10(IC50/µM) ≳ 3.3 — the weak-binding
extreme, far from the nM–µM regime where Boltz-2's affinity head was trained.

## Limits — read before trusting a number

1. **These ligands are far smaller than Boltz-2's affinity training data.** The model warns above 56
   heavy atoms; ours have 12. The small-fragment end is not a regime the affinity head was built for,
   and we have no evidence about its accuracy there.
2. **IC50 is not Kd**, and `affinity_pred_value` regresses heterogeneous assay data. Treat it as a
   ranking signal inside one ladder, never as a binding energy.
3. **6NT is a TS *analogue*, not the transition state.** The organizers say so themselves
   ("the TS analogue is just an approximation used for scoring"). Binding it well is evidence about
   shape and electrostatic complementarity to a TS-*like* species, not about the real TS energy. The
   true TS is anionic and partially bonded; no stable molecule reproduces that.
4. **The three ligands are very similar, so the differences may be smaller than model noise.**
   This is the main practical risk. [chris-02](experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md)
   measured large Boltz-2 seed variance. Always run ≥ 3 seeds; the report prints the propagated SEM
   and whether `|ddG|` exceeds it, and says **"within noise"** when it does not.
5. **Unvalidated until the controls pass.** A ladder on a design means nothing until we know the
   method separates a real Kemp eliminase from a protein that is not one:
   - **positive control:** [`results/affinity/hg3_k50q_7k4u_chainA.fasta`](../results/affinity/hg3_k50q_7k4u_chainA.fasta)
     — HG3 K50Q from 7K4U, 305 aa, with W44/Q50/D127 verified in place. An evolved, experimentally
     active Kemp eliminase, so it *should* prefer the TS analogue.
   - **negative control:** chicken lysozyme `P00698`, already present on the cluster in
     `inputs/mmseqs_control.fasta`. Not a Kemp eliminase, so it should show no preference.
   If the positive control shows no TS preference, **the method is uninformative and the ladder
   should not be used to rank designs** — that outcome is itself a useful, cheap result.
6. `affinity_probability_binary < 0.5` for every ligand means Boltz-2 does not consider the protein a
   binder at all, and the `affinity_pred_value` differences are comparisons between non-binders. The
   report flags this.
