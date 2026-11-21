# Pitch

The story for the final presentation, kept current as results come in, so the slides take 30 minutes
and not 3 hours. Every number here is read from a run's files and links to an experiment page.
**Status: draft on real results as of 2026-11-21; job 47 (5-seed replication) still outstanding.**

---

## 1. Problem — one sentence

Natural enzymes accelerate reactions by holding a substrate in a geometry so precise that a third of
an ångström in the wrong place costs most of the catalysis — and we want to design, from scratch, a
protein that has never existed and that holds this geometry anyway.

Concretely: the Kemp elimination, a proton abstraction with no natural enzyme, needs a carboxylate
base and a hydrogen-bond donor positioned around the substrate. We submit up to 20 sequences; the
organizers fold each with the transition-state analogue 6NT and score the geometry.

## 2. Our approach — what is different

**We measured the target instead of guessing it, then found that the pipeline was re-rolling the
wrong dice.**

Two moves, both of which came out of reading the data rather than adding a model:

**(a) The target geometry came from the family, not from one structure.** The brief says to compare
against "the ideal approach geometry" without giving numbers. We ran a full-text PDB search, found
97 Kemp eliminase entries, kept the **23 with 6NT bound** and measured all **43 ligand copies**,
excluding the 17 where the canonical contact is not actually made. Across the 26 engaged copies:

| contact | min | **median** | max | window |
|---|---|---|---|---|
| base — carboxylate O → 6NT N3 | 2.41 | **2.51 Å** | 2.69 | **0.28 Å wide** |
| donor — donor atom → 6NT N1 | 2.92 | **3.03 Å** | 3.60 | 0.68 Å |

Every engaged catalytic base in 23 independent crystal structures sits in a 0.28 Å window.
→ `results/kemp_family_geometry.tsv`, `scripts/32_kemp_family_geometry.py`

**(b) We found the pipeline's real bottleneck by reading its own output twice.** `summary.json`
reports the catalytic contacts on the *designed backbone* and on the *refolded* structure. Nobody had
compared the two columns. Across all six end-to-end runs — ours and a teammate's — RFdiffusion3 hits
**base 2.53 Å / donor 3.09 Å every single time**, reproducing the motif to 0.013 Å. **All of the
geometric loss happens in the refold**, which is decided by the sequence — and the pipeline samples
the sequence **exactly once per backbone**.

Costs: RFD3 **12 min**, LigandMPNN **6 s**, Boltz-2 **19 s**. We were spending the expensive step to
re-roll the cheap one. So we split the pipeline: design a backbone once, then sample sequences by the
dozen.
→ `wiki/primer.md` §5(d2), `wiki/experiments/chris-04_…`

## 3. Results — headline

**On a backbone whose single original sequence missed both targets, 2 of 72 sampled sequences land
inside both crystal windows — and both are novel folds.**

| | base (2.41–2.69) | donor (2.92–3.60) | novelty (qTM vs 40k PDB reps) |
|---|---|---|---|
| the pipeline's single sequence | 3.32 ✗ | 3.75 ✗ | 0.550 |
| **s024** | **2.49 ✓** | **3.53 ✓** | **0.561 PASS** |
| **s059** | **2.59 ✓** | **3.48 ✓** | **0.546 PASS** |
| family crystals | median **2.51** | median 3.03 | — |

s024's base contact is 2.49 Å against a family median of 2.51 Å, at **≤3 % sequence identity** to
anything in the PDB. Same backbone, same motif — only the sequence changed.

Supporting measurements, each cheap and each changing a decision:

| finding | number | what it changed |
|---|---|---|
| the MSA stage is a **no-op** for de novo designs | depth 1, `nonquery_rows` 0, **bit-identical** output without it | removed ~45 % of runtime and the 30 GB node requirement |
| **T = 0.1**, the default, is the **worst** temperature | 0/24 in-window vs 2/24 at T = 0.2 | one flag, free |
| more motif anchors **cost designability** | 3-anchor motif: median CA RMSD 2.02 Å vs 0.77 Å, **0/72** in window | kept the minimal motif |
| designability is a **per-backbone** property | seed 5: **0 of 48** sequences refolded under 2 Å | screen backbones by sweeping, not by one try |
| a single fold is **noisier than the window** | same sequence, same seed: 2.49 Å vs 2.07 Å (window is 0.28 Å) | replicate every candidate over 5 seeds |
| confidence metrics are **blind to chemistry** | a teammate's design: iptm **0.869** with the ligand **26 Å** away | always measure the two distances explicitly |
| Boltz-2's affinity head cannot rank enzymes | HG3 and HG3.17 both **2.06** despite ~1000× activity | use it as a filter, never a ranker |

## 4. What is next, and why it matters

**Next, concretely:**
1. **Replicate every candidate over 5 Boltz-2 seeds** before it takes a submission slot — this is also
   the organizers' own consistency term (job 47).
2. **Fill the 20 slots across different folds.** All 72 designs from one backbone are *one* fold at
   qTM 0.98–0.99, so sequence sampling buys geometry but no diversity. Backbones come from different
   crystal *arrangements* of the same two anchors (`cluster/build_family_motifs.py`).
3. **Re-run the natural-enzyme controls with pocket conditioning** before trusting any donor number.

**Why it matters beyond this hackathon.** The transferable result is not a sequence, it is a
reallocation. A de novo design pipeline looks like it is limited by the generative model, so that is
where the compute goes. Here it was not: the generator was already exact, and the loss sat in a
25-second step that was being sampled once. Reading an existing report's two columns against each
other was worth more than any model we could have added — and the same two-column check applies to any
design-then-validate pipeline.

## 5. Figures and artifacts

| what | where |
|---|---|
| the geometry target, 43 ligand copies / 23 structures | `results/kemp_family_geometry.tsv` |
| Idea A: 72 sequences, one backbone, fully measured | `results/oversample_a_seed4_job27.tsv` |
| Idea B: the three-anchor motif refuted | `results/oversample_b_trp44_job31.tsv` |
| seed 5: designability is per-backbone | `results/oversample_rescue_s5_job40.tsv` |
| submission candidates | `results/designs.jsonl` → `make submission` |
| the pipeline we actually run | `cluster/` |
| analysis in one command | `scripts/33_analyze_oversampling.py` |

**Figure worth drawing (not yet made):** one scatter, base contact against CA RMSD, for the 72
sequences of chris-04, with the 0.28 Å crystal window as a horizontal band and the two winners
marked. It shows the whole argument at once — the backbone refolds reliably (points clustered at low
RMSD) while the contact scatters over 20 Å, and the single original sequence sits outside the band.
