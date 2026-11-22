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

### (d2b) CORRECTION to (d2): the ligand moves, not the fold

(d2) called the loss "refold fidelity", and across backbones that reading was right — the failing
seeds genuinely collapsed at CA RMSD 13–15 Å. **Within a single backbone it is wrong**, and chris-04
(72 sequences on seed 4's backbone) shows it clearly:

| | min | median | max |
|---|---|---|---|
| CA RMSD | 0.49 | **0.77 Å** | 17.37 |
| base contact | 2.38 | **5.12 Å** | 23.15 |

The protein refolds reliably — at T = 0.1, **all 24** sequences came back under 2 Å CA RMSD — while the
base contact ranges over 21 Å. And CA RMSD hardly predicts it: **r = +0.12**. (iptm is the best of what
we log, at r = −0.40; LigandMPNN's `ligand_confidence` is r = −0.00.)

So the sequence is not failing to encode the fold. It is failing to **hold the ligand**. Nothing we can
compute before folding is a good enough filter — which is fine, since folding is 19 s. **Fold
everything and filter on the measured contact.**

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

### (g2) The instrument check: the base contact is trustworthy, the donor contact is not

We judge designs against crystal distances but measure them with Boltz-2. chris-04 folded three real
enzymes' own sequences in the same batch to compare the two instruments directly:

| structure | base→N3 | donor→N1 | crystal base | crystal donor |
|---|---|---|---|---|
| **4BS0** (HG3.17) | **2.49** | **6.08** ✗ | 2.53 | 3.10 |
| 3NYD (HG3) | 3.49 (but base→N1 = 2.21, a flipped pose) | 2.80 | — | — |
| 7K4U | 2.11 | **5.34** ✗ | 2.54 | 3.20 |

- ✅ **Base: validated.** 2.49 Å predicted against 2.53 Å crystallographic, on the very structure our
  motif came from. The 2.41–2.69 Å window is reachable through Boltz-2 and base numbers mean what we
  have been treating them as meaning.
- ❌ **Donor: not validated.** Boltz-2 loses the donor on two of three real enzymes.
- **Caveat:** these controls are 307–318-residue natural constructs folded single-sequence with **no
  pocket conditioning**, while zonghu's `aff_*` runs use `pocket_force: true` at 5 Å. The control is
  harsher than it needs to be, so the donor failure may be an artefact rather than a limit of the
  model. Redoing it with pocket conditioning is the proper follow-up.

Practical consequence: **optimise and report the base contact; treat the donor as secondary** until
that control is redone. Convenient, because the base contact is where our designs were failing and
geometry is dominated by it.

### (g3) Sequence oversampling buys catalytic geometry but ZERO fold diversity

`tools/self_diversity.sh` on chris-04's 75 structures, all-vs-all, single linkage at qTM 0.7:

| cluster | members | what it is |
|---|---|---|
| fold 1 | **71 of 72 designs** | all one fold — qTM 0.98–0.99 to each other |
| fold 2 | 3 | the natural controls 4BS0 / 3NYD / 7K4U, qTM 0.82–0.90, 72–90 % identity |
| fold 3 | 1 | `s070`, the one design that refolded into something else |

The controls clustering together is the check that the tool works: they genuinely *are* homologues,
and our designs sit in a separate cluster from them.

The designs' sequences differ a lot — 58–74 % pairwise identity — but the fold is identical, which is
exactly what "same backbone, different sequence" has to mean. **So Idea A alone cannot fill 20
submission slots.** Twenty sequences off one backbone are twenty copies of one fold, and if that fold
is inactive in the lab, every slot fails together. Fold diversity has to come from different
**backbones** — which is what Ideas B and C supply. A and B/C are complements, not competitors.

One trap worth recording, because it produced a confidently wrong answer first time: foldseek names a
hit `<stem>_<chain>`, e.g. `s059_A`. Matching those against filenames needs both sides normalised, and
stripping a 1–3 character suffix turns `..._model_0` into `..._model` and `c_3NYD` into `c`. The
mismatch silently matched nothing and reported "75 structures -> 75 distinct folds" for 75 copies of
one fold. The script now strips exactly one character and aborts if no edge matches a node.

### (g4) Designability varies between backbones; one three-anchor backbone looked worse (weak evidence)

> **Evidence grade, corrected:** one backbone per condition, compared against seed 4 (selected as the
> best). The two-anchor motif's own seeds span 0.77–10.67 Å median CA RMSD, so Trp44's 2.02 Å is inside
> that range. Only its donor median (18.92 Å vs 4.7–11.9) stands out, and it is n = 1. Read the table
> below as "no benefit, possibly a cost", **not** as "anchors destroy designability".

chris-05 ran the identical 72-sequence protocol on zonghu's three-anchor Trp44 backbone:

| | seed 4 (2 anchors) | Trp44 (3 anchors) |
|---|---|---|
| best base contact | **2.38 Å** | 3.26 Å |
| median donor contact | 4.68 Å | **18.92 Å** |
| median CA RMSD | **0.77 Å** | 2.02 Å |
| refolded < 2 Å | 70/72 (97 %) | 35/72 (49 %) |
| inside both windows | **2/72** | **0/72** |

Both backbones satisfy their motifs essentially perfectly in design space — RFD3 deviation 0.0129 Å
and 0.0167 Å. The difference appears only once you try to write sequences for them. So:

- **`fixed_pair_distance_max_deviation` measures whether the design met the constraint, and says
  nothing about whether the backbone is encodable.** A motif can look perfectly satisfied and still
  produce a backbone no sequence stabilises.
- **Designability is measurable per backbone**: the median CA RMSD over a sequence sweep. 0.77 Å vs
  2.02 Å here, and it tracks the in-window hit rate. But it needs a sweep to measure, which is why
  single-sequence verdicts (chris-02) were unreliable in *both* directions.
- **Prefer the minimal motif.** Two anchors already place the ligand correctly. Extra pinned geometry
  costs the sequences that would have worked.

Backbone diversity therefore has to come from different **arrangements** of the same two anchors —
which is exactly chris-06 — not from adding anchors.

### (g5) A single Boltz-2 prediction is MUCH noisier than the target window

*(first measured on 4BS0; the 3NYD numbers below are worse and were added later)*

The natural-enzyme controls go into every sweep with the same sequences and the same `--seed 1`. They
matched to 4 decimal places between two 75-structure batches, then changed in a 51-structure batch:

| batch | rows | 4BS0 base | 4BS0 donor |
|---|---|---|---|
| job 27 | 75 | 2.4925 | 6.0775 |
| job 31 | 75 | 2.4925 | 6.0775 |
| job 40 | 51 | **2.0722** | **4.8453** |

Boltz's `--seed` applies per invocation, so the RNG stream depends on batch composition rather than on
the structure. The identical sequence gives **2.49 Å and 2.07 Å** — a 0.42 Å swing against a window
**0.28 Å wide**.

So **no single fold can place a design inside the window.** Measurement noise exceeds the thing being
measured. Three consequences:

1. **Every submission candidate needs 5-seed replication** before we believe its geometry. This is
   also precisely the organizers' consistency term, which we had never measured
   (`cluster/replicate_seeds.sbatch`, job 47).
2. **Treat the hit rate, not the single best number, as the signal.** 2/72 in-window for seed 4's
   backbone against 0/72 and 0/48 for two others is a comparison between distributions, and that part
   survives the noise.
3. A sweep's winner is a *shortlist entry*, not a result. Rank by replicated mean, not by one fold.

### (g5b) How bad the noise actually is: the same enzyme reads 2.45 to 3.78 Å

The controls go into every sweep unchanged. Five batches of 3NYD, the same sequence and the same
`--seed 1` each time:

| batch | rows | base | donor | nearest donor |
|---|---|---|---|---|
| job 27 | 75 | 3.49 | 2.80 | GLN37:NE2 |
| job 40 | 51 | 2.45 | 4.25 | GLN207:NE2 |
| job 39 | 51 | 2.45 | 4.25 | GLN207:NE2 |
| job 35 | 35 | 3.78 | 5.32 | GLN207:NE2 |
| **job 59** | **19** | **2.53** | **3.10** | GLN207:NE2 |
| crystal | — | ~2.5 | ~3.0 | — |

**Base spans 1.33 Å, donor spans 2.52 Å, for a real and highly evolved enzyme.** The two 51-row
batches agree exactly, confirming that the RNG stream is fixed by batch composition rather than by
the structure. In job 59 the geometry comes out essentially perfect (2.53 / 3.10, both in window);
in job 35 the same sequence looks like a failed design.

Three consequences, and the third is uncomfortable:

1. **Absolute single-fold geometry is close to meaningless.** A real enzyme reads anywhere from 2.45
   to 3.78 Å on the contact we are optimising.
2. **Averages over many sequences survive; single values do not.** I first wrote that comparisons
   within a batch are "fair because the batch shares one RNG" — that was wrong. Each structure in a
   batch consumes its own part of the random stream, so each design carries its *own* independent
   noise. Medians and hit rates over dozens of sequences average it out; any one design's contact
   does not.
3. **Our 2/72 "hits" are one draw each, and may be partly noise.** A design whose true mean is 4 Å can
   read 2.5 Å once; designs we discarded may be better than they looked. Job 47's 5-seed replication
   is not a nicety — without it we cannot say s024 is a good design, only that it drew a good number.

### (g5c) Replication changed the answer: 1 of 2 single-fold hits survived

Five seeds at the scorer's declared positions (`results/replication_job47_pinned.tsv`): **s024** holds
base and donor in-window in 3/5 seeds (base 2.77 ± 0.51 Å); **s059** in 0/5 (base 3.22 ± 0.80, donor
never below 3.82 Å) though it looked identical to s024 in one fold. A single-fold "in window" call was
right half the time. Measure at the *declared* positions, not by scan: a nearest-atom scan can only read
equal or shorter, and for the donor it latched onto other Gln/Asn residues and made s059 look fine.

### (g8) We had only been checking distances; the scorer also judges approach angle and in-plane geometry

The organizers state that "distance alone is not enough: each contact is also judged on the angle it
approaches the ring at and on whether it lies in the ring plane", that the two do not average ("the worse
decides"), and that geometry outweighs everything else combined. We measured neither until now
(`cluster/geometry_vs_crystal.py`, `results/geometry_full_crystal_vs_designs.tsv`; atom definitions are our
stand-ins, the scorer's are unpublished). Crystal ranges over 25 engaged copies: base approach angle
167–176°, base out-of-plane 1–12°, donor approach 162–173°, donor out-of-plane 1–16°.

| over 352 swept designs | count |
|---|---|
| both distances in window | 3 (by nearest-oxygen; 2 by OD2) |
| base approach **and** in-plane in range | 7 |
| donor approach **and** in-plane in range | 3 |
| all four approach/in-plane quantities | **0** |
| all six (distances + approach + in-plane) | **0** |

**s024, 5 seeds** (base d / donor d, base approach / out-of-plane, donor approach / out-of-plane):
2.51/3.52, 129°/25°, 177°/2° · 2.48/3.57, 144°/22°, 165°/15° · 3.78/5.53, 74°/47°, 66°/32° ·
2.56/3.84, 133°/22°, 164°/16° · 2.50/3.59, 138°/15°, 164°/15°. So **the donor geometry is crystal-like in
four seeds, the base is not**: approach about 30° short of the crystal and 10–15° beyond its in-plane range.
**s059 is the mirror image**: base approach/in-plane crystal-like (161–175°, 1–9°), donor end-on (71–93°,
51–72° out of plane), which the organizers say "scores poorly even at a perfect distance".

On a continuous proxy D (overshoot beyond the crystal range in tolerance units, too-short distances double;
our invention, not the scorer's), s024's five seeds give D = 4.8, 3.5, 29.6, 5.3, 3.5 against a median of
**53.7** over all 352 single-fold designs: in four of five seeds it sits in the extreme tail of everything
we have made. The pipeline's own sequence averages D = 24.3, s059 17.6.

The other two terms do not separate anything: burial (CA atoms within 12 Å) is 48 for s024 and 45–48 for the
natural enzymes and the other designs, and s024 has the lowest iPDE of everything measured (1.20, against
1.62 for the pipeline's sequence, 1.80 for s059 and 1.53–3.00 for the natural enzymes).

**Why this matters for the plan.** 15 of the 20 best single-fold designs by D sit on seed 4's backbone
(which is 72 of 352), so the backbone effect is real, and the existing 352 contain candidates that the
distance-only filter never flagged and never replicated (s042, s004, s006, s019).

### (g9) What decides geometry on a good backbone: not the pocket residues, and not similarity to winners

Two read-only checks on seed 4's 72 designs (`cluster/pocket_and_smoothness.py`), with geometry as the
continuous proxy D from (g8).

- **The pocket is nearly the same in the best and the worst designs.** On the *designed* backbone 13 residues sit
  within 5 Å of the ligand, 11 of them free. Seven of those 11 are the same residue in the 12 best designs and
  in the 12 worst (V56, A82, Q116, A213, S214, N217, L243). Class counts at those positions barely relate to D
  (hydrophobic −0.29, Gly/Pro +0.07, polar +0.13, charged +0.14), and LigandMPNN's own scores say nothing
  (overall confidence −0.04, ligand confidence +0.01, sequence recovery −0.13).
- **D is not smooth in sequence space at this range.** Sequence identity to the three best designs, over a
  56–74 % identity range, correlates with D at −0.07, −0.05 and +0.09. Resampling around a winner at that
  similarity is no better than blind sampling. Whether it helps at 90–99 % identity (a few point mutations)
  is untested.
- **No design has an aromatic residue at any free pocket position** (mean count 0.0 in 72 designs), although the
  crystal ring is stacked by Trp44 at 3.86 Å. That region of sequence space was never sampled, so the data
  cannot say whether an aromatic helps; it is the one cheap, mechanistically motivated thing left to test.

A trap, recorded so it is not repeated: defined on the *refolded* structure, Gly/Pro near the ligand correlated
with worse geometry at +0.68 within seed 4. Defined on the designed backbone it is +0.07. A ligand that lands in
the wrong place touches different residues, so the refold-defined number was circular.

**Consequence.** My planned "pocket-fixed resampling around s024" would mostly reproduce blind sampling, because
the pocket is already near-identical in every design. Replaced by three small comparison arms (see the plan).

### (g10) Why most designs are 'bad', which are good, and what a free metric can do

Over all 352 swept designs, geometry D (0 = inside every crystal range; our proxy): 5th percentile 17.3, median
53.5, 95th percentile 129. Only 6 designs (1.7 %) have D <= 10 and 29 (8 %) have D <= 20.

**The dominant failure is not a subtle pose error: in 297 of 352 designs (84 %) the ligand is not in the pocket at
all** (base > 5 Å or donor > 6 Å). Only 19 designs (5 %) put it roughly in place, and 6 of those reach D <= 10.
Share inside the crystal range per quantity: base distance 2.0 %, donor distance 1.7 %, base approach 2.3 %, donor
approach 1.1 %, but in-plane 24.7 % (base) and 27.8 % (donor), so lying in the ring plane is the easy part and
arriving along the ring's outward axis is the hard part.

**What the good ones share.** 12 of the 15 best by D sit on seed 4's backbone (72 of 352 designs); by temperature
they are 3 at T 0.1, 6 at 0.2, 6 at 0.3, a rate of 3.8 %, 3.4 % and 6.3 % (not significant). They refold more
faithfully and more confidently: median iptm 0.885 against 0.793, iPDE 1.23 against 2.17, CA RMSD 0.80 against 1.83.
Not their pocket residues and not their sequence similarity (see g9).

**A free filter.** Across all designs geometry D correlates with iPDE (+0.43), iptm (-0.42) and complex pLDDT (-0.47);
within seed 4 alone only weakly (+0.22, -0.23, -0.27). As a pre-filter, `iPDE < 1.6 and iptm > 0.85` keeps 17 % of
designs and 5 of the 6 with D <= 10 (precision 8.2 %, 4.8x the 1.7 % base rate). It is a triage step to shrink what
gets replicated, not a replacement for measuring the geometry.

**How the pose is tested, and its limits.** The same Boltz-2 cofold the scorer runs (single sequence, 6NT), the
contacts measured at the declared residues, compared with the span of 25 engaged crystal copies, repeated over 5 seeds
for consistency, plus iPDE and burial. It is one model judged against crystals. There is no independent second
predictor on the cluster and no wet lab, and Boltz-2 itself does not reproduce the natural enzymes' donor contact.

### (g11) What the crystals teach beyond the two contacts: the pocket map, and a pocket that is too polar

`cluster/pocket_vs_crystal.py` describes the ligand's environment (protein atoms within 4.5 Å) in the 25 engaged
crystal copies and in our 352 designs.

**The pocket map is highly conserved.** Nine residues touch the ligand in all 25 copies: Trp44, Pro45, Glu46, Gln50
(donor), Gly83, Asp127 (base), Leu236, Met237, Thr265. Ala21 (23/25), Val266 (22/25), Met172 (20/25) and Cys84
(19/25) follow.

| per structure | residues | aromatic | aliphatic | polar | charged | stacked aromatic |
|---|---|---|---|---|---|---|
| 25 crystal copies | 14.4 | 1.9 | 6.3 | **2.1** | 2.0 | 40 % |
| designs with the ligand roughly in place (34) | 14.1 | 1.2 | 5.8 | **4.5** | 1.9 | 9 % |
| 15 best designs by D | 13.9 | 1.2 | 6.7 | 3.7 | 1.7 | 7 % |
| all 352 designs | 13.0 | 1.6 | 4.6 | 3.7 | 1.8 | 18 % |

The size of the pocket and its aromatic content are similar; **the designs' pockets are about twice as polar**
(4.5 against 2.1, and about 3.5 against 1.1 once the pinned donor and base are removed). That agrees with the
earlier within-seed-4 signal that more hydrophobic pocket residues go with better geometry (-0.29), and it is
the one lever here read off the crystals rather than guessed. It became the fifth experiment arm
(`bias_polar_down.json`, calibrated: baseline 4.1 polar residues at the 11 free pocket positions, push 1.5 gives
about 1.5).

**On stacking, the data is weak.** Our strict test (ring centroids within 5.0 Å, planes within 35 degrees) passes
in only 10 of 25 crystal copies although Trp44 touches the ligand in all 25, so 'stacked' is a lower bound. Among
designs with the ligand roughly in place, 3 have a stacked aromatic and 31 do not (median D 19.4 against 17.7); over
all designs those with one have a median D of 57.7, no better than the rest. Nothing here supports or refutes the
aromatic arm; it stays an untested hypothesis.

**What cannot be learned from the crystals.** They are 23 near-identical structures of one protein family, so what
they define is the HG3.17 pose, not necessarily the best pose for a de novo scaffold. They cannot tell us whether a
design will be active, and a model trained on 23 such structures would learn the family, not the chemistry.

### (g6) Motif variety: one alternative arrangement looked worse than 4BS0 (weak evidence)

> **Evidence grade, corrected:** one backbone per motif. Within the 4BS0 motif alone, RFD3 seeds give
> 0.77 / 1.33 / 1.53 / 1.91 / 1.92 Å, so the 1.99 vs 1.33 Å gap to 8USL_B is inside seed-to-seed noise.
> "4BS0 is already the best arrangement" is a plausible prior (it is HG3.17's own structure), not a
> measured result.

chris-06 took the most geometrically distinct family member (8USL_B, 2.20 Å away from 4BS0 in the
pinned-atom distance matrix) and ran the identical sweep on a backbone built from each:

| | 4BS0_A (what the pipeline ships) | 8USL_B (most distinct) |
|---|---|---|
| median CA RMSD | **1.33 Å** | 1.99 Å |
| refolded < 2 Å | **84 %** | 53 % |
| best base contact | **2.90 Å** | 3.52 Å |
| median base contact | **6.66 Å** | 9.73 Å |

Worse on every axis. And in hindsight predictable: **4BS0 is the 1.09 Å structure of HG3.17, the most
optimised variant in the family.** Its active site is the product of directed evolution; an arbitrary
other member is a less refined version of the same idea. My farthest-point selection picked the most
*different* motif, which is not the same as the most *useful* one — a selection criterion worth
remembering as a mistake.

So backbone diversity has to come from **more RFD3 seeds on the 4BS0 motif**, which is the cheap axis
anyway at 12 min each. The motif-extraction tooling still works and stays available.

### (g6b) Designability rank-orders backbones (ρ = 0.86, n = 8) but says nothing about a sequence (r = 0.12)

> **Update, n = 8.** The table below is the original six. With the two new screens (seeds 12 and 13)
> the rank correlation is **ρ = +0.857** (I first reported +0.943 at n = 6), and **+0.829** among the six
> plain 4BS0-motif backbones (n = 6, not significant at the 5 % level). Still positive, weaker than I said.
> **Caveats:** both axes are computed from the
> *same* refolded structures, so part of the link is mechanical — a protein that collapses cannot hold
> a ligand. It is a good reason to screen cheaply, not proof that designability *causes* good contacts.

Six backbones swept under one protocol, ranked by designability:

| backbone | n | median CA RMSD | **median base** | best base | in window |
|---|---|---|---|---|---|
| **seed 4** | 72 | **0.77 Å** | **5.12 Å** | 2.38 | **2/72** |
| 4BS0_A fresh | 32 | 1.33 | 6.66 | 2.90 | 0/32 |
| seed 3 | 48 | 1.53 | 7.45 | 3.86 | 0/48 |
| 8USL_B | 32 | 1.99 | 9.73 | 3.52 | 0/32 |
| Trp44 (3 anchors) | 72 | 2.02 | 7.64 | 3.26 | 0/72 |
| seed 5 | 48 | 10.67 | 11.32 | 3.33 | 0/48 |

| relationship | statistic |
|---|---|
| **across backbones**: median CA RMSD vs **median** base contact | Spearman ρ = +0.943 at n = 6 → **+0.857 at n = 8** |
| **within** seed 4 (n=72): a sequence's CA RMSD vs its base contact | **r = +0.122** |

These are not in conflict — the distinction is the point. **A backbone's designability almost
perfectly predicts how close its ligand ends up. An individual sequence's refold quality predicts
nothing about its own contact.** Hence the funnel: screen backbones on designability, then sample
sequences blind, because no per-sequence filter exists and folding costs 19 s anyway.

**A statistic to avoid:** ranking backbones by their *best* contact gives ρ = +0.486 instead of
+0.943 (at n = 6), because best-of-72 beats best-of-32 by construction. When sample sizes differ, compare
medians, not minima. I nearly reported the weak number as the result.

### (g7) The funnel all four experiments point at

Everything measured so far collapses into one procedure:

```
RFD3 on the 4BS0 motif, many seeds          12 min each   — backbones are cheap
        ↓
short sweep (~32 seq) → median CA RMSD      ~16 min       — SCREEN ON DESIGNABILITY
        ↓    keep < ~1.5 Å                                   (2 of 5 seeds pass)
deep sweep (72+ seq) at T = 0.2–0.3         ~25 min       — ~3 % land in window
        ↓
5-seed replication of the hits              ~10 min       — the noise is 0.43 Å, the window 0.28 Å
        ↓
novelty gate, then submit across folds
```

The point of the screen is that **designability is the property that actually varies between
backbones** — 0.77, 1.33, 1.99, 10.67 Å median CA RMSD across the four we have swept — it is cheap to
measure, and it is invisible in everything the pipeline reports about a design.

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

## 7. The three ideas we commit to (supersedes §6) — **all three are now running**

Status as of 2026-11-21, built and launched. Tooling lives in `cluster/`; experiment pages
`chris-04` (A), `chris-05` (B) and `chris-06` (C) carry the pre-registered decision rules,
written before any result existed.

| | what it does | job | outcome |
|---|---|---|---|
| **A** | 72 sequences on seed 4's existing backbone | **27** | ✅ **supported, smaller than first reported** — 2 single-fold hits; **1 survived 5-seed replication** (s024, 3/5 seeds both in window; s059 0/5) |
| **B** | 72 sequences on zonghu's Trp44 backbone | **31** | ⚠️ **inconclusive, leans negative** — 0/72, but n = 1 backbone and the comparison is against our best seed |
| **C** | RFD3 on 4BS0_A vs 8USL_B, each chaining a sweep | **34** → 35, 36 | ⚠️ **inconclusive** — one backbone per motif; seed-to-seed spread within a motif is as large as the gap |
| controls | 4BS0 / 3NYD / 7K4U folded in every batch | (bundled) | ✅ base validated, donor not — see (g2) |

**Idea A's headline:** on seed 4's own backbone, where the organizers' single sequence gave base
3.32 Å and donor 3.75 Å (both outside the window), two of 72 sampled sequences land inside both —
**s024 at base 2.49 Å** against a family median of 2.51, and s059 at 2.59 Å. Both pass the novelty
gate against all 40,066 PDB representatives (qTM 0.561 and 0.546, ≤3 % identity) and are banked in
`results/designs.jsonl`. The hit rate is ~3 % per sequence, which is precisely why sampling once
found nothing. Full numbers in `wiki/experiments/chris-04_…`.

**Also measured: T = 0.1 — the organizers' default — is the worst of the three temperatures**, giving
0 winners from 24 sequences against 2 at T = 0.2 and 1 at T = 0.3, with no meaningful loss in folding
success (24/23/23 refolded under 2 Å). Use T = 0.2–0.3.

Two things had to be fixed to make this possible, and both are worth knowing:

- **`boltz predict <directory>` parses every file it finds** and dies on the first one it does
  not recognise (`RuntimeError: Unable to parse filetype .a3m`). The alignments now live in a
  sibling directory and are referenced by absolute path.
- **The organizers' template pins `--constraint=g6.2xlarge --mem=30G`.** Only one node on the
  cluster satisfies that, so every job of ours serialised behind it while two `l4small` nodes
  sat idle. The 30 GB exists for the MMseqs2 index — which these jobs never load. Relaxing it
  to `--constraint="l4small|l4" --mem=14G` is what actually delivers the parallelism chris-03
  predicted. (`l4big` stays excluded; it is reserved.)

One batched `boltz predict` call also matters more than it sounds: folding 75 structures in
one call loads the model once. Seventy-five separate calls would pay the model-load cost 75
times and turn a 25-minute job into hours.



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

### How they turned out — this is the decision

I expected the three to stack, with A multiplying B and C. **They did not. Two of the three are dead,
and the survivor is better than the stack would have been**, because it is specific about where the
compute goes.

| | prediction | outcome |
|---|---|---|
| **A** sequence oversampling | "should find in-window designs" | ✅ **2/72 single-fold, 1/72 after replication** — still the lever, and a 50 % false-positive rate for one-fold calls |
| **B** third anchor | "better posed, should win" | ❌ 0/72, worse on every axis — anchors cost designability (g4) |
| **C** motif variety | "4BS0's placement may be unusually hard" | ❌ 4BS0 is the *best* arrangement, being HG3.17's own (g6) |

Both failures were informative in the same way: they showed that the thing that varies between
backbones is not geometry — every backbone has perfect geometry — but **designability**, how readily
a sequence can be written for it. That is measurable, cheap, and invisible in everything the pipeline
reports about a single design. See §5(g4), (g6) and the funnel in §5(g7).

**What we commit to:**

```
RFD3 on the 4BS0 motif, many seeds       12 min each  — backbones are cheap and are the bottleneck
        ↓
short sweep (~16-32 seq) → median CA RMSD  ~7-16 min  — SCREEN ON DESIGNABILITY, keep < ~1.5 A
        ↓                                                (2 of 5 seeds passed)
deep sweep (72+ seq) at T = 0.2-0.3        ~25 min    — ~3 % land in the window
        ↓                                                (32 seq is under-powered: P(0 hits) = 0.38)
5-seed replication of the hits             ~10 min    — noise is 0.43 A, the window is 0.28 A
        ↓
novelty gate  →  bank  →  submit across folds
```

What we explicitly do **not** do, each with a measured reason: add motif anchors (g4), use other
family motifs (g6), chase MSA depth (§6b), relax with force fields (§6b), build a pre-fold learned
filter (d2b — nothing we can compute beats r = +0.12), or trust any single fold's geometry (g5).

### Two controls to run alongside (19 s and 2 min, both overdue)

1. **Instrument check.** Fold HG3.17's *real* sequence with 6NT and measure the two contacts with our
   own code. We judge designs against *crystal* distances but measure with *Boltz-2* — different
   instruments. If Boltz-2 reports 2.5 Å for the real enzyme, the window is real and seed 4 genuinely
   misses. If it reports 3.3 Å, then seed 4 is already at parity with HG3.17 and our target is
   miscalibrated. **We cannot interpret any number in finding (d2) until this is run.** Cost: 19 s.
2. **Self-diversity.** foldseek all-vs-all on our own designs before submitting. 20 slots filled with
   20 copies of one fold is a bad hedge when the organizers pick ≥5 for the lab. The 40 k-representative
   database is already built; this reuses it.
