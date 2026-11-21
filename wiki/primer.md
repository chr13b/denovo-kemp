# Primer: what we are actually doing, and why it is hard

A from-scratch explanation of the challenge for someone who has not designed a protein before.
Rules and scoring live in [challenge.md](challenge.md); this page explains the *reasoning* behind them.
Everything stated as a measurement here comes from our own runs
([chris-01](experiments/chris-01_reference-pipeline-baseline.md),
[chris-02](experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md)).

---

## 1. The chemistry

### The reaction

The **Kemp elimination** turns 5-nitrobenzisoxazole into a substituted salicylonitrile. One step:

```
        base (B:)
           ↓  takes H+ from C3
   [5-nitrobenzisoxazole]  →  [transition state]  →  2-hydroxy-5-nitrobenzonitrile
                                    ↑
                           the N–O bond breaks, negative
                           charge builds on the leaving oxygen
```

A base removes a proton from carbon 3. As that happens the weak N–O bond of the isoxazole ring breaks,
and the ring opens into a nitrile plus a phenolate. Everything happens in one concerted step, so the
transition state has a proton half-transferred to the base *and* negative charge half-developed on the
oxygen, simultaneously.

### Why chemists love this reaction

It needs **no cofactor, no metal, no ATP** — just a well-placed base. It is spectrophotometrically easy
to follow. That makes it the standard benchmark for computational enzyme design: if your method cannot
make a Kemp eliminase, it cannot make anything. Famous attempts: the Baker lab's KE07/KE70/HG3 designs,
and Hilvert's directed evolution of HG3 into **HG3.17**, which reached catalytic efficiency comparable to
natural enzymes. HG3.17 is the scaffold our motif is taken from — and it is explicitly *not* allowed as
an answer.

### What an enzyme has to do

An enzyme does not "push" a reaction. It **binds the transition state more tightly than it binds the
substrate or the product**. Everything an enzyme does is that one trick. So designing one means building
a pocket shaped to be maximally comfortable for a structure that exists for ~10⁻¹³ s.

Two groups do the work here, and both are things we must declare in our submission:

| Element | What it does | Allowed residues | Why those |
|---|---|---|---|
| **Catalytic base** | takes the proton off C3 | **D** or **E** (Asp/Glu) | a carboxylate is the right basicity; buried, its pKa rises so it stays deprotonated and nucleophilic |
| **Oxyanion-hole donor** | donates an H-bond to the developing negative charge | **Q N S T Y K R** | stabilising the forming oxyanion lowers the barrier |

**Why His is banned here** (it would chemically be a fine base): His donates from NE2 *or* ND1 depending
on its tautomer, and a FASTA header cannot say which. The format cannot express it, so it is excluded.

### The ligand we are actually scored against

The real transition state cannot be put in a structure file — it is a fleeting arrangement, not a
molecule. So the organizers use a **transition-state analogue (TSA)**: a stable molecule shaped like the
transition state.

**6NT = 6-nitrobenzotriazole.** Note what changed: the substrate is a benz**isoxazole** (ring contains
N and **O**); the analogue is a benzo**triazole** (ring contains three **N**, no oxygen at all). So:

- The atom our base aims at is **N3** of 6NT (standing in for C3–H).
- The atom our donor aims at is **N1** of 6NT (standing in for the leaving oxygen).
- The organizers say plainly: *"The TS analogue is just an approximation used for scoring."*

This matters practically: optimise geometry **to those nitrogens**, and do not reason about an oxygen
that is not in the scored structure.

### The target geometry — measured, not guessed

The organizers say the scored distance targets come "from crystal structures of working Kemp eliminases".
**That structure is PDB `4BS0`** — HG3.17 at 1.09 Å, and it has **6NT itself** bound, the same ligand we are
scored against. So we can read the targets straight off it
(`uv run python scripts/31_measure_reference_geometry.py`):

| Contact | chain A | chain B | What it is |
|---|---|---|---|
| **Asp127 OD2 → 6NT N3** | **2.53 Å** | 2.69 Å | the catalytic base, poised on the atom it deprotonates |
| **Gln50 NE2 → 6NT N1** | **3.10 Å** | 3.00 Å | the oxyanion-hole donor |
| Trp44 NE1 → 6NT N3 | 3.86 Å | 3.98 Å | the third motif residue — aromatic, packs the site |

Two things follow.

**1. This is where RFD3's "constant" numbers come from.** RFD3 is handed 2.527 Å and 3.09 Å — these
crystal values. The motif in `inputs/Kemp.json` is lifted directly out of 4BS0. What looked like an
arbitrary constant is actually the geometry of the best Kemp eliminase ever made.

**2. We now have a scoring proxy we can compute ourselves — from the whole family, not one structure.**
A full-text PDB search for "kemp eliminase" returns **97 entries**; 23 of them have 6NT bound, giving
**43 ligand copies**. `scripts/32_kemp_family_geometry.py` measures all of them
(table: `results/kemp_family_geometry.tsv`).

17 of the 43 copies are variants where the canonical contact is simply not made (Lys50 or Gln207 at
6–8 Å, or non-HG3 scaffolds). Among the **26 copies where both contacts are engaged**:

| Contact | min | **median** | max | window width |
|---|---|---|---|---|
| **base** — carboxylate O → 6NT N3 | 2.41 Å | **2.51 Å** | 2.69 Å | **0.28 Å** |
| **donor** — donor atom → 6NT N1 | 2.92 Å | **3.03 Å** | 3.60 Å | 0.68 Å |

The base window is **remarkably tight** — across 23 independent crystal structures of working enzymes,
every engaged catalytic base sits between 2.41 and 2.69 Å. That is the precision the Blomberg paper's
title refers to, and it is a hard target to hit.

**This forces an honest recalibration of seed 4:**

| Design | base (window 2.41–2.69) | donor (window 2.92–3.60) |
|---|---|---|
| seed 1 baseline | 5.91 Å ✗ | 2.94 Å ✓ |
| seed 3 | 8.33 Å ✗ | 3.08 Å ✓ |
| **seed 4** | **3.32 Å ✗ — 0.63 Å beyond the maximum** | **3.75 Å ✗ — just outside** |

Seed 4 is our best design and it is **outside the productive window on both contacts**. Earlier I called
it "loose but erring in the forgiving direction"; against the real distribution that was too generous.
It is a valid, novel, well-folded submission — but on geometry, the term that dominates scoring, no
design we have made is yet in the range where real Kemp eliminases operate.

Interestingly, the *donor* contact is where our folded designs do well (2.94, 3.08 Å — both inside the
window), and the *base* is where every one of them fails. That is finding (d) again, now with a
quantitative target attached.

---

## 2. The computational problem

We submit **sequences only** — at most 20, each 50–260 residues, each with `base=` and `oxy=` 1-based
indices. The organizers do everything else. So our entire job is: *produce amino-acid strings whose
predicted complex with 6NT has excellent catalytic geometry.*

### The provided pipeline, stage by stage

```
  inputs/Kemp.json  (motif: which residues + which atoms are held fixed)
          │
          ▼
  1. RFD3 (RFdiffusion3)      a diffusion model. Input: the catalytic motif geometry +
          │                   a length. Output: a BACKBONE (CA/N/C positions only,
          │                   no side chains, no sequence) that holds the motif in place.
          ▼
  2. LigandMPNN               inverse folding. Input: backbone + ligand. Output: an amino-acid
          │                   SEQUENCE predicted to fold into that backbone, aware of the ligand.
          ▼
  3. MMseqs2                  searches a 183 GB sequence database for homologues → an MSA.
          │                   (For our de novo designs this finds NOTHING — see §5.)
          ▼
  4. Boltz-2                  cofolding. Input: sequence + 6NT. Output: a predicted 3D complex
          │                   plus confidence numbers. THIS is what gets scored.
          ▼
  summary.json                all the numbers we read
```

The slides frame it as **Shape → Sequence → Score**.

**The crucial asymmetry:** stages 1–2 *design*, stage 4 *checks*. Stage 4 does not know what stage 1
intended. It just predicts what the sequence will do. When those disagree, the design has failed — and
that disagreement is the central problem of the whole field (see §5).

### LigandMPNN does not fold anything — it does the opposite

This trips everyone up, so it is worth being precise. There are two opposite problems:

| | Question | Input → Output | Tool here |
|---|---|---|---|
| **Folding** | "what shape does this sequence take?" | sequence → structure | Boltz-2 |
| **Inverse folding** | "what sequence would produce this shape?" | structure → sequence | LigandMPNN |

LigandMPNN is **inverse folding**. It never folds anything and never produces a 3D structure. It is handed
a finished backbone (from RFD3) plus the ligand, and for each position it answers *"given the local
geometry here, and the ligand sitting there, which amino acid belongs at this position?"* Its output is a
string of letters.

So nothing is "folded separately from the whole protein". The sequence of the **entire 260-residue
protein** is designed at once, with the ligand present throughout — that is exactly what the "Ligand" in
LigandMPNN means, and it is why the residues lining the pocket come out hydrophobic and correctly shaped
rather than random.

**The real folding happens once, in Boltz-2, and it folds everything together** — full sequence plus
ligand, simultaneously, as one complex. That is also the honest test: Boltz-2 is given *only* the
sequence and the ligand. It is never told what RFD3 designed. If the sequence genuinely encodes the
intended structure, Boltz-2 rediscovers it; if not, we find out. That independence is the whole point —
if we fed RFD3's backbone to the folder, the check would be circular and meaningless.

### What exactly we ran in the seed sweep — only the seed

Four copies of the verified example (`new-project.sh`), then **one integer changed** in each, at three
places: RFD3's diffusion seed, LigandMPNN's sampling seed, Boltz-2's sampling seed. Verified before
submitting that exactly those three lines differed and `inputs/Kemp.json` was byte-identical. Nothing
else was touched.

**RFD3's input is the motif, not a protein.** `HG3_17_kemp_motif.pdb` plus instructions in `Kemp.json`:
hold Asp `A127` rigid by its OD1/CG/OD2 atoms, hold Gln `A50` by OE1/CD/NE2, hold all of ligand 6NT, and
build **exactly 260 residues** around them (`contig: 260-260`).

**RFD3's output is a bare backbone** — N, CA, C, O coordinates only, no side chains, no sequence — that
holds those three fragments in the given arrangement. LigandMPNN then reads backbone + ligand and writes
a sequence for it.

Changing the seed changes the diffusion trajectory, so each run builds a **completely different protein**:
seed 2 shares only 8.5 % sequence identity with seed 1, and the catalytic residues land at different
positions (seed 1 `base=177 oxy=99`, seed 4 `base=86 oxy=52`).

### What if we did *not* pin the motif atoms?

`select_fixed_atoms` is a choice, not a law. Loosening it is a real design axis:

| Setting | Effect | Trade-off |
|---|---|---|
| **Fix all motif atoms** (current) | every design starts from exact HG3.17 catalytic geometry | RFD3 must build a foldable 260-mer around a rigid constraint — and ~50 % of the time it cannot |
| **Fix fewer atoms** (e.g. base carboxylate only, drop the donor) | RFD3 has far more freedom to find a foldable backbone | the donor is no longer guaranteed to be positioned; we would have to recover it afterwards |
| **Fix nothing** | pure de novo binder design | almost certainly loses catalytic geometry — the thing we are actually scored on |

The case for loosening: our failures are **folding** failures, not geometry failures, and the rigid motif
is the main thing making the backbone hard to build. Giving RFD3 slack where it matters least (the donor
contact already survives refolding reliably — see §5d) could raise the success rate without costing the
contact that actually drives the score.

The case against: catalytic geometry **is** the score, geometry is the dominant term, and the constraint
costs us nothing at generation time — it is "free" precision. Unpinning risks trading a scored quantity
for an unscored one.

**This is testable and cheap**: generate backbones with the donor unpinned, and compare refolding success
rate and final Boltz-2 geometry against the pinned runs. It only needs the design stage, not Boltz.

---

## 3. What we are scored on

Four terms, which **multiply** — so one failure cannot be bought back by strength elsewhere. Measured on
**5 Boltz-2 replicates per sequence**.

| Term | Definition (organizers' words) | Can we compute it ourselves? |
|---|---|---|
| **Geometry** | "distance, angle and dihedral measurements, comparing against the ideal approach geometry for the base and H-bond donor" | Partly — we can measure distances/angles, but we do **not** know their target values |
| **iPDE** | "estimated error between protein and ligand token distances" | Yes, Boltz-2 reports it directly |
| **Catalytic base burial** | "**number of CA atoms close to the catalytic base (up to 12 Å)**" | **Yes, exactly** — pure geometry, no model needed |
| **Consistency** | "how well metrics are reproduced across multiple Boltz-2 seeds" | Yes, by running Boltz-2 repeatedly |

Geometry outweighs everything else combined. Distances have an **optimum, not a direction**: too short is
a clash and is punished harder than the same error too long.

**Novelty is a gate, not a score.** TM-score > 0.7 to a published structure, or > 70 % sequence identity
to a published enzyme, and the design simply does not qualify. You cannot mutate HG3.17 and win.

---

## 4. What we have to work with

### Compute
- AWS Slurm cluster, NVIDIA **L4 (24 GB)** GPUs. 8 logical CPUs of GPU worker at a time.
- **In practice one job at a time**: the provided `kemp-e2e.sbatch` requests `g6.2xlarge`, 8 CPUs, 30 GB
  — the whole allocation — because the MSA step needs ~28 GB. **~23 min per design, serial.**
- Never the `l4big` queue; never heavy compute on the head node.

### Models and data on the cluster (`/mnt/ref`, read-only, 295 GB)
| Thing | Where | Note |
|---|---|---|
| RFD3 weights | `data_weights/rfd3` | **RFdiffusion 3 only — there are no RFD4 weights** |
| LigandMPNN weights | `data_weights/ligandmpnn` | |
| Boltz-2 weights | `data_weights/boltz2` | |
| MMseqs2 + database | `data_weights/mmseqs2_db` | **183 GB** sequence DB for MSAs |
| Conda envs | `software/envs/{env-rfd3,env-ligandmpnn,env-boltz2}` | |
| The worked example | `/mnt/work/kemp_example` | verified; **never modify it** |

### Inputs that define the design problem
- `inputs/HG3_17_kemp_motif.pdb` — the catalytic motif taken from HG3.17.
- `inputs/Kemp.json` — which residues and **which atoms** are held rigid:
  `A127` (the Asp base: OD1, CG, OD2), `A50` (the Gln donor: OE1, CD, NE2), and `6NT: ALL`.
  Plus `contig`, the design length (`260-260` in the default).

### Tools we added
- **foldseek** at `/mnt/work/tools/foldseek` (installer: [`envs/foldseek.sh`](../envs/foldseek.sh)) for the
  TM-score half of the novelty gate.

### What we do NOT have
RFdiffusion 4 weights · a wet lab (the organizers do that for ≥5 designs per team) · unlimited compute ·
the organizers' exact geometric target values.

---

## 5. What we have measured, and why it is the whole story

These are our own numbers, not assumptions.

### (a) Only the Boltz-2 structure carries information

RFD3's reported contact distances are **2.527 Å and 3.09 Å in every single run**, because `Kemp.json`
pins those motif atoms and the ligand. They are an *input*, not a result. You cannot screen on them.

### (b) Designs mostly fold or explode — but the gap is not empty

Our first five runs gave CA RMSD of **{0.70, 1.36, 1.43}** or **{13.67, 14.63}** — nothing between 1.4 and
13.7, which looked cleanly bimodal. **zonghu's job 7 lands at 4.26 Å**, in the middle. So "binary" was an
artefact of n=5; treat it as *strongly* bimodal with a sparsely populated middle, not a law.

When a design does collapse, the ligand leaves the site entirely (contacts of 12–26 Å) and the catalytic
geometry is gone. The first question is still **"did it fold at all"**, and CA RMSD is still the cheapest
way to ask it — but use a threshold, not a presumed gap.

### (b2) High confidence does **not** mean good catalytic geometry

zonghu's job 7 is the clearest warning we have. Its global metrics look **better than our best design**:

| | zonghu-07 | our seed 4 |
|---|---|---|
| `iptm` | **0.869** | 0.846 |
| `complex_ipde` | 1.665 | 1.518 |
| CA RMSD | 4.26 Å | 0.70 Å |
| **base contact** | **11.99 Å** ✗ | 3.32 Å |
| **donor contact** | **26.49 Å** ✗ | 3.75 Å |

Boltz-2 is *confident* about where it put the ligand. It just put it 26 Å from the catalytic donor.
`iptm` and `iPDE` measure how sure the model is, **not whether the chemistry is right**. Any filter built
only on confidence metrics would have ranked this failed design above our best one. **Always measure the
two catalytic distances explicitly.**

### (c) Roughly half of everything fails

3 of 5 designs survived refolding at 260 AA with default settings. **Budget for a ~50 % loss rate.**

### (d) The base is fragile, the donor is not

Among designs that *did* fold, the donor contact moved −0.15, −0.02, +0.66 Å while the base contact moved
+3.38, +5.80, +0.79 Å. Since geometry dominates scoring, **base placement is where designs lose points.**

### (d2) THE central finding: RFD3 already hits the crystal window every single time

This is the most important table in this document. `summary.json` reports the catalytic contacts
**twice** — once on the RFD3 backbone, once on the Boltz-2 refold. Nobody had compared the two columns
across runs:

| run | RFD3 base | RFD3 donor | → | Boltz base | Boltz donor | base drift | CA RMSD |
|---|---|---|---|---|---|---|---|
| reference-1 | 2.53 | 3.09 | | 5.91 | 2.94 | +3.38 | 1.43 |
| seed 2 | 2.53 | 3.09 | | 21.92 | 18.86 | +19.39 | 14.63 |
| seed 3 | 2.53 | 3.09 | | 8.33 | 3.08 | +5.80 | 1.36 |
| **seed 4** | 2.53 | 3.09 | | **3.32** | **3.75** | **+0.79** | **0.70** |
| seed 5 | 2.53 | 3.09 | | 14.88 | 15.83 | +12.35 | 13.67 |
| zonghu-07 | 2.53 | 3.20 | | 11.99 | 26.49 | +9.46 | 4.26 |
| **crystal target** | **2.41–2.69** | **2.92–3.60** | | | | | |

**The RFD3 column is dead centre in the crystal window on every run** — base 2.53 Å against a family
median of 2.51 Å, donor 3.09 Å against a median of 3.03 Å. RFD3 reproduces the pinned motif to
`fixed_pair_distance_max_deviation = 0.013 Å`.

So the generation step is not the problem, and it never was. **100 % of the geometric loss happens in
the refold.** The question is not "can we design the right geometry" — we already do, every time. It is
**"can we find a sequence that encodes the backbone well enough that a folder rebuilds it."**

And `CA RMSD` tracks the loss almost monotonically: 0.70 Å → +0.79, 1.4 Å → +3.4/+5.8, 4.3 Å → +9.5,
14 Å → +12/+19. Refold fidelity *is* the scored quantity, one step removed.

### (d3) We have been taking the first sequence LigandMPNN offered, every time

`ligandmpnn_scores` reads `id: 1, T: 0.1` on every run. One sequence per backbone, at a temperature low
enough to be nearly deterministic. The sequence is the only thing that varies between a 0.70 Å refold
and a 14 Å one — and we sampled it **once**.

Costs, from chris-03: LigandMPNN **6 s**, Boltz-2 **19 s**, RFD3 **12 min**. Generating 50 sequences for
one backbone and folding all of them costs ~21 min — less than two new backbones. Our observed rate of
sub-1 Å refolds is 1 in 6; at 50 samples we should expect ~8 per backbone, and we get to keep the best
instead of the first.

**This is the single largest mispriced resource in the project.**

### (e) The MSA step costs ~45 % of our runtime and returns nothing

Every de novo design reports **MSA depth 1, nonquery_rows 0** — MMseqs2 searched 183 GB and found zero
homologues. (The one `depth: 301` in our data is the natural-protein control, lysozyme, which only the
verification mode runs.) From file timestamps, that search takes **~10 of the 23 minutes**.

This is the largest single inefficiency available to us, and §6 Idea 1 exploits it.

### (f) Seed 4 is novel — measured, not assumed

Checked with foldseek TM-align against two databases built from RCSB
(`envs/foldseek.sh --full`, then `tools/novelty_check.sh <structure>`):

| Database | Size | Seed 4's best TM | Closest hit |
|---|---|---|---|
| Kemp eliminase family | 7 structures incl. 4BS0, 3NYD, KE07, KE70 | **0.300** | 3NYD (HG3) |
| **PDB 30 %-identity representatives** | **40,066 structures / 368,093 chains** | **0.550** | 4A01 |

Sequence identity to every hit is **2–5 %**, and every design reports **MSA depth 1** — MMseqs2 searched
183 GB and found no homologues at all. **Seed 4 passes both halves of the novelty gate.**

> ⚠️ **TM-score normalisation decides this verdict, so get it right.** foldseek's default `alntmscore` is
> normalised by the *alignment* length. A 122-residue protein matching 72 residues of our 260-residue
> design scores **0.816** that way — which would look like a failure — while its TM normalised by our
> query is **0.243**. The question "is my fold already known?" is answered by **`qtmscore`**, normalised
> by the designed protein. `tools/novelty_check.sh` ranks on `qtmscore` and prints the others for context.
> **We have not confirmed which normalisation the organizers use** — it is in the open questions, and it
> is worth asking, because the three differ by more than the width of the gate.

So despite being built on HG3.17's catalytic geometry, the protein around it is genuinely new. That is
RFD3 doing its job: it was given three fixed fragments, not a scaffold.

### (g) The novelty/confidence tension

Slide 7 warns that "MSA depth for de novo design can impact folding confidence", and iPDE and consistency
both depend on folding confidence. Our designs have the shallowest possible MSA. So maximum novelty may
cost us in two of four scoring terms — while the novelty gate forbids staying near known enzymes. There is
a sweet spot and we do not know where it is.

---

### (h) Boltz-2's affinity head reads ligand chemistry, not catalytic proficiency

Boltz-2 ships a binding-affinity head, and zonghu has already run it on the three real enzymes against
three ligand states (`/mnt/work/projects/zonghu_aff_*`). Mean `affinity_pred_value`, 3 seeds each:

| enzyme | substrate | product | **TS analogue** | real activity |
|---|---|---|---|---|
| HG3 | 1.24 | 1.58 | **2.06** | baseline |
| HG3.7 | 1.26 | 1.49 | **2.00** | intermediate |
| HG3.17 | 1.55 | 1.37 | **2.06** | **~1000× HG3** |

Two things fall out, and they point in opposite directions:

- ✅ **The TS analogue separates cleanly from substrate and product in all three enzymes, with zero
  overlap across 9 runs** (TS 1.83–2.24; substrate 1.09–1.63; product 1.22–1.63). Preferential binding
  of the transition state over substrate and product is the textbook thermodynamic definition of
  catalysis, and the head detects it.
- ❌ **It cannot rank enzymes.** HG3 and HG3.17 differ ~1000-fold in rate and score **2.06 vs 2.06**.

So ΔG from this head is a usable **negative filter** — "does this pocket recognise the TS analogue
preferentially at all?" — and useless as a ranking signal, because on the one comparison where we know
the answer it returns the same number for a mediocre enzyme and a great one. Same lesson as (b2): the
learned scalars encode *recognition*, not *catalysis*. Only geometry encodes catalysis.

One loose end worth 3 seeds: HG3.17's `affinity_probability_binary1` for the TS analogue is 0.164 ±
0.003, against 0.36 ± 0.11 for both other enzymes — uniquely low and 30× less variable. That may be
noise in a 3-seed sample; it is the only number anywhere in our data that singles out the best enzyme.

## 6. Three candidate pipelines

Each states the hypothesis, the steps, the cost, and **what would prove it wrong**. They are not mutually
exclusive; 1 is close to free and should probably happen regardless.

---

### Idea 1 — "Strip the pipeline, screen wide" (throughput)

**Hypothesis.** We are paying ~10 min per design for an MSA that is provably empty, and ~23 min total for
designs that are ~50 % likely to be garbage. Removing the dead stage and screening cheaply before the
expensive stage should give us several times more scored designs per hour.

**Why it is credible.** Measurement (e): depth 1, nonquery_rows 0, in *every* de novo run. An MSA of the
query alone is informationally identical to single-sequence mode.

**Steps.**
1. Split `kemp-e2e.sbatch` into two jobs: **design** (RFD3 → LigandMPNN) and **evaluate** (Boltz-2).
2. In the evaluate job, run Boltz-2 in **single-sequence mode** (skip MMseqs2). Verify on seed 4 that the
   metrics match the MSA version within noise — *this verification is mandatory before trusting it.*
3. The design job needs far less RAM than 30 GB, so it can run on the small nodes — **two designs in
   parallel**, which the current script cannot do.
4. Filter between the stages on things computable from the RFD3/LigandMPNN output alone: **base burial**
   (CA atoms within 12 Å — a scored term, and free), radius of gyration, secondary-structure content,
   LigandMPNN score.
5. Only survivors get Boltz-2.

**Expected gain.** If the MSA really is free to drop and filtering removes half the failures, effective
throughput goes from ~2.5 designs/hour to plausibly ~10.

**What kills it.** If single-sequence Boltz-2 gives materially different iPDE/geometry than the MSA
version, the screen stops predicting the score and the saving is fake. **Test this first, on seed 4,
where we already know the MSA-version answer.**

---

### Idea 2 — "Consistency first" (match the scoring function)

**Hypothesis.** Scoring uses **5 replicates** and explicitly rewards reproducibility as a proxy for
preorganisation. A design with mediocre-but-stable geometry may outrank one with excellent-but-variable
geometry, because the terms multiply. Nobody else will be optimising this.

**Why it is credible.** It is a stated scoring term, we have the exact procedure, and our binary-failure
finding (b) suggests Boltz-2 output is strongly bimodal — so variance is probably large and informative.

**Steps.**
1. Take a design that folds (seed 4). Run Boltz-2 **5 times varying only the Boltz seed**, design fixed.
2. Report mean **and spread** of each contact distance, iPDE, and ligand pose.
3. Use that to define our internal objective: **worst-case over replicates**, not the mean, mirroring the
   "worse of the two decides" rule already used inside the geometry term.
4. Rank all candidates by worst-case geometry; prefer boring-and-stable over brilliant-and-erratic.

**Expected gain.** Directly optimises a term others may treat as noise; also tells us how many replicates
we need before a number is trustworthy, which makes every later comparison cheaper.

**What kills it.** If replicate variance turns out to be tiny for folded designs, the term is nearly
constant across candidates and cannot differentiate — then ignore it and spend the GPU on Idea 1.

---

### Idea 3 — "Shorter and more motif variety" (raise the base rate)

**Hypothesis.** We inherited `contig 260-260` — the *maximum* allowed length — and a 2-residue motif,
and we observe ~50 % refolding failure. Shorter de novo proteins are markedly easier to fold and to
predict. Lowering the length should raise the hit rate *and* cut GPU time per design.

**Why it is credible.** 260 is the competition ceiling, not a recommendation. All our failures occurred at
260. Kemp eliminases do not need 260 residues — HG3 is a TIM barrel, but a minimal active site does not
require one. Design time scales with length.

**Steps.**
1. Sweep `contig` at 150, 180, 210 (same seeds) and measure **refolding success rate** and iPDE, not just
   geometry. Our 260 runs are the control.
2. Vary the motif: the provided `Kemp_HG3_17_smoke` entry fixes a **third** residue, `A44` (a Trp, atoms
   CD1/NE1/CE2) — an aromatic that can stack against the ligand and pre-organise the pocket. Test whether
   including it improves base-contact retention, which (d) identifies as the weak point.
3. Try relaxing `select_fixed_atoms` for the base (fix fewer atoms) so RFD3 has more freedom to build a
   foldable backbone around it.

**Expected gain.** Attacks the 50 % failure rate at its source rather than filtering after the fact, and
shorter designs cost less GPU each. Also produces fold diversity, which matters for the ≥5 lab-validation
slots.

**What kills it.** If shorter designs cannot host the motif and burial drops (the base ends up
solvent-exposed), we trade one scoring term for another. **Measure burial, not just success rate.**

---

---

### Idea 4 — fine-tune a model on public structures (evaluated, and my recommendation is **no, not today**)

The idea: take public structural data — the PDB, the ~200 Kemp-eliminase-related entries, TIM barrels,
AlphaFold DB — and fine-tune one of the models so it produces designs more like the ones that work.

**Where it could plausibly help**

| Target | Rationale |
|---|---|
| **LigandMPNN** | Fine-tune on structures with carboxylate–heteroaromatic contacts so it picks pocket residues that preserve the base contact — our measured weak point (§5d). Smallest model, cheapest to train. |
| **RFD3** | Fine-tune on TIM barrels / known eliminase folds so generated backbones are more foldable. Attacks the 50 % failure rate directly. |
| **A cheap surrogate scorer** | *Not* fine-tuning a generator: train a small classifier on (design features → did it survive refolding). This is the one that actually fits our situation. |

**Pros**
- The failure mode is systematic (half of designs don't fold), and systematic failures are what learned
  filters fix well.
- Public data genuinely exists: PDB, AFDB, and the Kemp literature are all available.
- A surrogate scorer is cheap, needs no GPU training at scale, and compounds — every run we do adds a
  labelled example.

**Cons — and they are decisive for a one-day hackathon**
1. **We have 5 labelled examples.** Fine-tuning a generative model on 5 outcomes is not possible; even a
   surrogate classifier needs tens to hundreds. The data to train on is the thing we lack.
2. **The compute is the same compute.** Training competes directly with generating designs, on the same
   two GPUs, under the fairness rule. Every GPU-hour spent training is a GPU-hour not spent producing
   submittable designs.
3. **Fine-tuning on known enzymes pushes *toward* the novelty gate.** Train a generator to make things
   that look like published Kemp eliminases and you move it toward TM > 0.7 — disqualification. The
   objective is actively in tension with the rules.
4. **Setup cost is not small.** Training scripts, data curation, checkpoint handling, and a validation
   protocol — likely most of the remaining time, with the first usable checkpoint arriving near the
   deadline.
5. **The cheap wins are not yet taken.** We have a measured ~2× from dropping the MSA stage, an untested
   burial filter, and an untested length reduction. Fine-tuning is the expensive move to make *after*
   those are exhausted, not before.

**What I would do instead, which captures most of the benefit:** collect features for every design we
generate (burial count, radius of gyration, secondary-structure fraction, LigandMPNN score) alongside
the binary did-it-fold outcome. That costs nothing, it is the training set a surrogate would need, and
if we accumulate 30–50 designs a simple logistic regression on those features becomes genuinely useful
*within* the hackathon — and is the honest first step toward fine-tuning if the project continues.

**What would change my answer:** a multi-day timeline, or discovering that burial and the other free
features do *not* predict folding success — because then a learned filter would be the only route left.

---

---

## 6b. Plausible ideas that do **not** work here, and why

Each of these is a good instinct in a different setting. The reason they fail here is almost always the
same: **we submit a sequence, and the organizers fold it themselves.** Nothing we compute on a structure
is ever seen by the scorer.

### Force-field relaxation (FoldX, Rosetta, OpenMM)

> *"Geometry dominates and distances have an optimum — so relax the structure into ideal geometry."*

**It cannot help the score.** The scored structure is Boltz-2's prediction from *our sequence*, produced
on the organizers' machine. If we relax a structure locally and the contacts improve, we have improved a
file that nobody will ever look at. Worse, it is actively misleading: a relaxed model reports distances
that **differ from the ones actually scored**, so optimising against them optimises the wrong target.

Where a force field *could* earn its place is as a **selection** signal — "this sequence's predicted
structure is strained or clashing, so drop it". But we can already detect that directly from the Boltz-2
output: `ligand_protein_pairs_below_2_2_angstrom` counts clashes, and we have exact target distances from
4BS0. A force field would add licensing friction (FoldX and Rosetta both need registration) for
information we already have. **Recommendation: no.**

### Importing or transplanting an MSA

> *"Our designs have MSA depth 1 — why not give them an MSA from a similar PDB structure?"*

Two reasons, the second decisive.

1. **It would be wrong.** An MSA encodes the evolutionary covariation of *a particular protein family*.
   Pairing our sequence with HG3.17's alignment tells the folder "positions i and j co-vary" about a
   protein that is not ours. That is injecting false evidence, and the resulting structure prediction is
   not trustworthy.
2. **We do not control it.** We submit **sequence only**. The organizers run their own MSA search on it.
   Whatever they find — almost certainly depth 1 — is what they use. There is no field in a FASTA header
   for an alignment. The MSA is simply not ours to change.

The MSA finding ([§5e](#e-the-msa-step-costs-45-of-our-runtime-and-returns-nothing)) matters for **our own
screening speed**, not for the score.

### Chasing MSA depth by designing less novel proteins

The tension in §5g is real in principle, but **our own data argues against acting on it**: seed 4 has
MSA depth 1 and still reaches `complex_plddt` **0.947** and `iptm` **0.846**. Boltz-2 folded it
confidently with no evolutionary information at all. Deliberately trading novelty — the one hard gate —
for an MSA we have not shown we need would be a bad trade on current evidence. **Revisit only if we see
designs failing with low pLDDT specifically attributable to shallow MSAs.**

---

## 6c. What to actually do with a learned filter

The logistic regression idea is often misunderstood as "a model that designs proteins". It does not
design anything. It answers one question: **"given what I can measure cheaply, should I spend the
expensive step on this candidate?"**

With [chris-03](experiments/chris-03_msa-free-boltz-screen.md) the economics changed, and so did the
target. Evaluation (Boltz-2) is **19 seconds**; generation (RFD3) is **~12 minutes**. So the filter should
not predict "is this worth folding" — folding is free. It should predict, **from the RFD3 backbone alone,
whether this backbone is worth sequencing and keeping**, so we stop spending 12-minute generation slots on
shapes that cannot host a working site.

Features that are free at that point: base burial (CA atoms within 12 Å — a *scored* term), radius of
gyration, secondary-structure fractions, loop length around the motif, solvent exposure of the base,
LigandMPNN's own score, and — see below — ligand leverage. Label: did the design survive refolding with
both catalytic contacts intact.

**We have 6 runs.** That is nowhere near enough; a rule of thumb is ~10 examples per feature, so 4
features needs ~40 designs. The point of logging features now is that the dataset builds itself while we
do the work we were going to do anyway. **If we never reach 40 designs, we simply read the table by eye —
which is also fine, and already told us that CA RMSD separates winners from losers.**

### Can we put chemistry into it?

Yes, in three increasingly interesting ways:

1. **Already there.** LigandMPNN is run with `--ligand_mpnn_use_atom_context 1`: it sees 6NT's actual
   atoms and their element types when choosing residues. The chemistry is in the model.
2. **Through the motif.** zonghu's job 7 adds Trp44 — the aromatic that stacks on the ligand in 4BS0 at
   3.86 Å. That is chemical knowledge encoded as a geometric constraint, which is how this pipeline
   accepts it.
3. **Through pKa reasoning, via burial.** The catalytic Asp must stay protonation-competent, which is
   exactly why "catalytic base burial" is a scored term. Counting CA atoms within 12 Å is a crude proxy
   for a pKa argument — and it is the one the organizers chose, so it is the one to optimise.

### Ligand leverage: a free feature we are uniquely placed to compute

[Bertsch, *Confidence is not competence*](literature.md) argues that an inverse-folding model's
**confidence** is blind to binding by construction, and that the binding signal lives in the **mixed
derivative** — the model's response to *ablating the partner*.

In our pipeline that ablation is **one existing flag**: LigandMPNN runs with
`--ligand_mpnn_use_atom_context 1`; running it again with `0` is the partner-ablated pass. The per-position
logit difference is ligand leverage, and it is nearly free (LigandMPNN takes ~6 s).

**As a diagnostic feature this is well motivated:** leverage at the catalytic positions asks *"did the
sequence designer actually condition on the ligand here, or would it have chosen the same residue with an
empty pocket?"* A design whose pocket residues show near-zero leverage was never really designed around
6NT, and is a good candidate to discard early.

**As a steering knob, the paper's own result says be careful:** the actionable tilt "vanishes on fully
de-novo backbones", and on de novo binders plain confidence outperformed it. Our backbones are fully de
novo. The honest position is that the *diagnostic* use costs one extra 6-second run and does not depend on
the contested claim, while the *steering* use is a research question we should not bet the hackathon on.

---

## 7. The three ideas we commit to (supersedes §6)

§6 was written before finding (d2). Once you know RFD3 already hits the crystal window on every run and
the entire loss is in the refold, the ranking changes completely. These three are ordered by expected
points per GPU-hour, and the first one is not close.

### Idea A — **Sequence oversampling.** Stop making backbones, start making sequences.

*The one-line case:* we have been discarding the cheapest axis in the pipeline. RFD3 (12 min) gives
perfect geometry; LigandMPNN (6 s) and Boltz-2 (19 s) decide whether we keep it; we sampled that pair
**once per backbone**.

Take seed 4's backbone — the one with a 0.70 Å refold — and instead of one sequence, generate **64 at
T = 0.2–0.3**, fold every one, keep those whose base contact lands in 2.41–2.69 Å.

- Cost: 64 × (6 s + 19 s) ≈ **27 min on one GPU**, no RFD3, no MMseqs2.
- What it tests: is seed 4's +0.79 Å base drift a property of *that backbone* (floor) or of *that one
  sequence* (sampling artefact)? The answer decides the whole project.
- Why it should work: refold fidelity is sequence-determined, and we have never looked at its
  distribution. Our 1-in-6 rate of sub-1 Å refolds came from 6 *different* backbones; within a backbone
  already known to refold at 0.70 Å, the odds are far better than that.
- Failure mode that still teaches us something: if all 64 sequences cluster at +0.8 Å, the backbone has
  a geometric floor and we need Idea B. One 27-minute job either way.
- T = 0.1 is also just wrong for this purpose — it is the organizers' demo setting, near-deterministic.
  Diversity is the entire point.

**This is the recommendation.** It is one job, it needs no new tooling, and it converts a 12-minute
bottleneck into a 25-second one.

### Idea B — **Over-determine the ligand.** Three anchors, not two.

Our motif pins two residues (Asp127 base, Gln50 donor). With two anchors the benzotriazole can pivot
about the axis joining them — which is precisely the degree of freedom the base contact loses.

zonghu's `trpopt` motif already adds the third: **Trp44**, whose indole stacks on the ligand ring at
3.86 Å in 4BS0. Their spec pins all six aromatic carbons plus `6NT: ALL`
(`/mnt/work/projects/zonghu_trpopt_s1/inputs/Kemp.json`). That is a better-posed theozyme than ours.

And their run did **not** refute it: RFD3 gave 2.53 / 3.20 Å — in the window, same as ours. It lost the
geometry in the refold at CA RMSD 4.26 Å, which is **Idea A's problem, not the motif's**. The motif has
never actually been tested, because it was tested with one sequence.

So: Trp44 motif × Idea A's sequence oversampling. The combination is the best of both branches — their
geometry hypothesis, our diagnosis of where the loss happens.

### Idea C — **A motif library from 23 crystal structures**, not one.

We have been designing against a single arrangement of base + donor + ligand, lifted from 4BS0. The
family search gave **26 engaged ligand copies from 23 independent crystal structures** — 26
experimentally real, catalytically competent theozymes, each a slightly different solution to the same
chemical problem.

Each becomes an RFD3 motif. If our base contact keeps drifting because *4BS0's particular* base
placement is hard to realise in a de novo backbone, another family member's placement may simply be
easier — and we currently have no way to know, because n = 1 on the one variable we never varied.

Cheapest useful version: cluster the 26 copies by their base/donor/ligand internal geometry, take the
3–4 distinct arrangements, run one RFD3 job each, then Idea A on top of every backbone that comes out.
`results/kemp_family_geometry.tsv` already holds the measurements.

### How they compose

They are not alternatives — they stack, and A is the multiplier on both others:

```
       C (motif variety)        B (third anchor)
              │                        │
              └──────────┬─────────────┘
                         ▼
              RFD3  →  backbone with perfect geometry   (12 min, already solved)
                         ▼
              A: 64 × (LigandMPNN + Boltz-2)            (27 min, never attempted)
                         ▼
              keep base ∈ [2.41, 2.69] Å  →  novelty gate  →  submit
```

Order of execution: **A first, on seed 4's existing backbone** — 27 minutes, no new tooling, and it
tells us whether a backbone-level floor exists before we spend GPU-hours making more backbones. Then B
and C in parallel on the two idle `l4small` nodes, with A applied to everything they produce.

### Two controls to run alongside (19 s and 2 min, both overdue)

1. **Instrument check.** Fold HG3.17's *real* sequence with 6NT and measure the two contacts with our
   own code. We judge designs against *crystal* distances but measure with *Boltz-2* — different
   instruments. If Boltz-2 reports 2.5 Å for the real enzyme, the window is real and seed 4 genuinely
   misses. If it reports 3.3 Å, then seed 4 is already at parity with HG3.17 and our target is
   miscalibrated. **We cannot interpret any number in finding (d2) until this is run.** Cost: 19 s.
2. **Self-diversity.** foldseek all-vs-all on our own designs before submitting. 20 slots filled with
   20 copies of one fold is a bad hedge when the organizers pick ≥5 for the lab. The 40 k-representative
   database is already built; this reuses it.
