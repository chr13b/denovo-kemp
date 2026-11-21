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

**2. We now have a scoring proxy we can compute ourselves.** Target ≈ **2.5–2.7 Å** for the base and
**3.0–3.1 Å** for the donor. Against that:

| Design | base (target ~2.6) | donor (target ~3.05) |
|---|---|---|
| seed 1 baseline | 5.91 Å ✗ far too long | 2.94 Å ✓ |
| seed 3 | 8.33 Å ✗ | 3.08 Å ✓ |
| **seed 4** | 3.32 Å — ~0.7 Å long | 3.75 Å — ~0.7 Å long |

Remember the penalty is asymmetric: too long is punished **less** than too short. Seed 4 is loose on both
but errs in the forgiving direction.

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

### (b) Designs either fold or they explode — nothing in between

CA RMSD between the RFD3 backbone and the Boltz-2 prediction came out as **{0.70, 1.36, 1.43}** or
**{13.67, 14.63}**. Nothing between 1.4 and 13.7. When it fails, the ligand leaves the site entirely
(contacts of 15–22 Å) and iPDE collapses to 5.5–6.7.

So the first question is never "how good is this design" but **"did it fold at all"** — one number.

### (c) Roughly half of everything fails

3 of 5 designs survived refolding at 260 AA with default settings. **Budget for a ~50 % loss rate.**

### (d) The base is fragile, the donor is not

Among designs that *did* fold, the donor contact moved −0.15, −0.02, +0.66 Å while the base contact moved
+3.38, +5.80, +0.79 Å. Since geometry dominates scoring, **base placement is where designs lose points.**

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

## 7. How these fit together

A sensible order given ~a day of compute:

1. **Idea 1 step 2 first** (one job): does single-sequence Boltz-2 reproduce seed 4's numbers? One answer
   unlocks roughly double throughput, or rules the idea out.
2. **Idea 3 step 1** in parallel with that, since it only needs the design stage.
3. **Idea 2** once we have 3–5 folding designs worth ranking.
4. Keep every design that folds. With ≥5 lab-validation slots available independent of score, a design
   that is chemically interesting but mid-ranked still has somewhere to go.
