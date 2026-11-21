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

### (f) The novelty/confidence tension

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

## 7. How these fit together

A sensible order given ~a day of compute:

1. **Idea 1 step 2 first** (one job): does single-sequence Boltz-2 reproduce seed 4's numbers? One answer
   unlocks roughly double throughput, or rules the idea out.
2. **Idea 3 step 1** in parallel with that, since it only needs the design stage.
3. **Idea 2** once we have 3–5 folding designs worth ranking.
4. Keep every design that folds. With ≥5 lab-validation slots available independent of score, a design
   that is chemically interesting but mid-ranked still has somewhere to go.
