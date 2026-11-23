# Challenge

**A computational Kemp-eliminase design project (team 01).**
Sources: [raw/20261121_organizers_start-here.md](../raw/20261121_organizers_start-here.md),
[raw/20261121_organizers_submission.md](../raw/20261121_organizers_submission.md),
[raw/20261121_organizers_cluster-guide.md](../raw/20261121_organizers_cluster-guide.md),
and the organizers' kickoff deck (8 image-only slides, removed from the tree before publication; everything
decision-relevant in it is distilled onto this page).
Details on running jobs are in [cluster.md](cluster.md); the file format is in [submission.md](submission.md).

> **Outcome (project closed, 2026-11-22).** The final 20-design file was uploaded by a teammate at 12:16 UTC
> ([submission.md](submission.md), Status). The organizers did not release per-design scores to the team, so every
> number in this wiki comes from our own instrument. The brief offered every team the chance to submit at least five
> designs for lab validation, independent of score (section "Lab validation" below); how those five were nominated was
> never stated to us. This page is kept as written during the event: the rules and the scoring description are
> reference material, the checklist and the open questions are the record of what we knew at the time.

## Goal

Design **Kemp eliminase** enzymes: protein sequences that catalyse the Kemp elimination (deprotonation
of C3 of a benzisoxazole, here ligand **6NT**). We submit **sequences only**, up to 20 of them.
Everything else (structure prediction, ligand placement, scoring) is done by the organizers.

## Hard rules

| Rule | Value |
|---|---|
| Designs per team | at most **20** (duplicates are scored once and waste a slot) |
| Sequence length | **50–260** residues (the cluster example starts at 260) |
| Alphabet | the 20 standard amino acids, uppercase |
| Required per design | `base=` and `oxy=` in the FASTA header, 1-based indices |
| `base=` residue | must be **D** or **E** (the catalytic base that deprotonates C3) |
| `oxy=` residue | must be one of **Q N S T Y K R** (oxyanion-hole donor). **H is not allowed** |
| Novelty | backbone **TM-score ≤ 0.7** to published structures **and** sequence **≤ 70 % identity** to published enzymes |
| Compute | only the provided cluster (fairness rule) |

**Novelty is a gate, not a score.** HG3.17 itself does not qualify, and mutating a known Kemp eliminase
will not qualify either. The design must be far away on *both* sequence and fold.

## Scoring (what we optimize)

Each design is cofolded with ligand 6NT in **Boltz-2** and ranked against other teams' designs,
on **5 replicates per sequence** (slide 7). The terms **multiply**, so one failed term cannot be bought
back by another.

The organizers' written doc says "four criteria" and then lists five; the slides (6/08) resolve it —
their items 1 and 2 are the two halves of one **Geometry** term. The four as the slides name them:

| # | Term | The organizers' definition | What it asks |
|---|---|---|---|
| 1 | **Geometry** | "distance, angle and **dihedral** measurements, comparing against the ideal approach geometry for the base and H-bond donor" | Is the ligand/active-site orientation *productive*? |
| 2 | **iPDE** | "estimated error between protein and Ligand Token distances" | Is the ligand **confidently placed**? Lower is better. |
| 3 | **Catalytic base burial** | "**number of CA atoms close to the catalytic base (up to 12 Å)**" | Is the base buried, not solvent-exposed, so its pKa is preserved? |
| 4 | **Consistency** | "how well metrics are reproduced across multiple Boltz-2 seeds" | Does cofolding give a good structure *reproducibly*? Proxy for preorganization. |

**Geometry outweighs everything else combined.** Within it:

- **There is an optimum, not a direction.** Too short is a clash and is punished *harder* than the same
  error too long. Targets come from crystal structures of working Kemp eliminases and textbook H-bond geometry.
- The angle and in-plane/dihedral terms **do not average — the worse of the two decides.** An end-on donor
  scores badly even at a perfect distance.

> **Burial is the one term we can compute exactly and cheaply right now**: count CA atoms within 12 Å of the
> declared base. No model needed, just the predicted structure. Highest value-per-GPU-minute of anything here.

> **Consistency is measured the way we are measuring it in
> [experiments/chris-02…](experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md)** — repeated Boltz-2
> predictions under different seeds. Our sweep and the scorer's replicate count (5) are the same procedure.

### The ligand is a transition-state *analogue*, not the substrate

The reaction (slide 4) is the Kemp elimination of **5-nitrobenzisoxazole**: a base deprotonates C3, the
isoxazole ring opens, and an H-bond donor stabilises the **developing oxyanion on the ring oxygen**.

What is actually cofolded and scored is **6NT = 6-nitrobenzotriazole**, the stable TS *analogue* — a
benzotriazole, so it has **no ring oxygen at all**. The organizers state plainly: *"The TS analogue is just
an approximation used for scoring"* (slide 7). In the reference run their own pipeline measured
**base → `6NT_N3`** and **donor → `6NT_N1`**, so those nitrogens stand in for the C3-H and the oxyanion.
Optimise against those atoms, and remember the analogue is a proxy for the chemistry, not the chemistry.

### MSA depth: a tension in the sources, and it matters

The submission doc says designs are folded with MSAs, "so a design on a natural scaffold is not handicapped
relative to a de novo one." Slide 7 says **"MSA depth for de novo design can impact folding confidence."**

Both can be true: the *procedure* treats everyone alike, but a genuinely de novo sequence has no homologues
to find, so its MSA is shallow and its folding confidence can suffer. Our reference run is evidence —
the design got **MSA depth 1** while the natural control got **301**
([chris-01](experiments/chris-01_reference-pipeline-baseline.md)).

Since iPDE and consistency both depend on folding confidence, **a maximally novel design may pay for its
novelty in two of the four scoring terms**, while the novelty gate forbids staying close to known enzymes.
Finding the sweet spot between those is a genuine strategic question, not a settled one.

> **Scoring happens on the Boltz-2 cofold, not on RFD3's output — and RFD3's contact distances tell you
> nothing.** Measured over 5 runs: the RFD3 base contact is `2.527 Å` in *every* one, because
> `select_fixed_atoms` holds the motif and ligand rigid. It is an input, not a result. The Boltz-2 base
> contact over the same runs ranged 3.32–21.92 Å. **Judge candidates only on Boltz-2 geometry**, and expect
> roughly **half of all designs to fail refolding entirely** (CA RMSD is bimodal: ~0.7–1.4 Å or ~13–15 Å,
> nothing between). Evidence:
> [experiments/chris-02…](experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md).

## Limitations the organizers named (slide 7)

**Compute**
- "Some design campaigns rely on tens to hundreds of thousands of generated variants. **You will have to do
  with significantly less.**" Our own measurement: the provided pipeline takes the whole allocation per job
  (~23 min, serial), so our realistic budget is **tens of designs, not thousands**. Screening cheaply before
  spending a GPU is therefore the whole game.
- "AWS node availability can fluctuate, this applies also for our scoring pipeline." Do not leave the
  submission to the last minute.
- Maximum design length **260 AA**.

**Scoring**
- "Scoring is reduced to a relatively simple set of metrics, measured on **only 5 replicates per sequence**."
- The novelty gate (> 70 % identity, TM > 0.7 → do not qualify).
- "The TS analogue is just an approximation used for scoring."
- "MSA depth for de novo design can impact folding confidence."

### Lab validation: 5 designs per team, independent of score

> "Every team will have the chance to submit **at least 5 designs for lab validation, independent of score**."

This is a second, parallel goal and it changes portfolio strategy: a handful of our 20 slots can be
scientifically interesting rather than score-maximising, because they get made in a lab regardless of where
we rank. How those 5 are nominated was never stated to us — see the open questions.

## Resources

- **Cluster:** AWS GPU cluster, Slurm, 2 GPUs in parallel (2× g6.xlarge) **or** 1 bigger node (g6.2xlarge), not both.
  Details and commands: [cluster.md](cluster.md).
- **Provided pipeline:** RFD3 (backbone) → LigandMPNN (sequence) → MMseqs2 (MSA) → Boltz-2 (complex prediction).
- **Provided example:** a single 260-residue Kemp design with the catalytic base, donor and ligand fixed.
- Other tools and pipelines are allowed, but **only the provided compute**.

## Timeline

- 2026-11-21: kickoff, repo set up, cluster access verified.
- 2026-11-22: submission deadline, **estimated at about 13:30 UTC and never confirmed by the organizers** (after the
  deadline S3 refuses uploads, no grace period). The final upload is the 12:16 UTC file in the bucket.
- Presentation: pitch decks were prepared (`slides/`); the slot is not recorded in the repository.

## Submission checklist

*The live checklist during the event; the final state of the upload is in [submission.md](submission.md), Status.*

- [ ] `designs.fasta` has ≤ 20 unique designs, each 50–260 residues
- [ ] every header carries `base=` and `oxy=` with correct residue types (`make submission` checks this locally)
- [ ] the organizers' `validate-submission.py` passes on the file
- [ ] novelty checked for every design (TM-score and sequence identity)
- [ ] uploaded with `./submit-designs.sh designs.fasta`, and re-uploaded after any change
  (**the file present at the deadline is the one scored**)
- [ ] `make reproduce` on a fresh clone regenerates the submission
- [ ] the submitted commit is tagged: `git tag -a submission-v1 -m "…" && git push origin submission-v1`
- [ ] [pitch.md](pitch.md) matches the slides

## Open questions (ask the organisers)

*As asked during the event. No answer to any of these is recorded in the repository, so they stand as the list of what
we did not know while designing.*

- [ ] **What is the exact submission deadline (date, time, timezone)?** *(first believed 2026-11-22 10:00 Paris/Basel = 09:00 UTC, which
      evidently did not hold because an upload at 12:16 UTC is in the bucket; then estimated at about 13:30 UTC; never confirmed)* ← the only
      one with a hard consequence: after it, S3 refuses uploads and there is no grace period.
- [ ] **Is the base contact measured to OD2 only, or to the nearer of the two carboxylate oxygens?** They are
      chemically equivalent and a prediction can place either one near the ligand. The reference pipeline's
      `verify_boltz.py` measures OD2 specifically. It changes our ranking: s042 (job 27) has its nearest oxygen
      at 2.45 Å but OD2 at 3.73 Å.
- [ ] **How is a team scored from its (up to 20) designs** — best design, mean, or sum? This decides whether a weak
      design in a free slot is harmless or costly. Until known, submit only designs we would defend.
- [ ] **How are the 5 lab-validation designs chosen** — do we nominate them, or do they take our top 5?
      This decides whether we reserve submission slots for interesting-but-risky designs.
- [ ] **Which TM-score normalisation defines the novelty gate** — by the designed protein, by the
      matched structure, or by the alignment? For our seed-4 design these give 0.55, 0.80 and 0.82
      against the same database, i.e. pass or fail depending only on the convention chosen.
- [ ] Is there a presentation, and how long?
- [ ] License/IP rules for our code and designs? (decides whether we add a LICENSE file)
- [ ] What are the *target* values for the geometry term (ideal distance, angle, dihedral)? The slides say
      "comparing against the ideal approach geometry" without giving numbers. We now measure them from the
      family ourselves (base 2.41–2.69 Å, donor 2.92–3.60 Å, over 26 engaged ligand copies from 23
      structures — `results/kemp_family_geometry.tsv`), but whether the scorer uses these values,
      an angle term as well, or a different reference set is still unknown.
- [ ] **Is the geometry term measured on the Boltz-2 refold only, or also on a submitted structure?**
      This matters more than it sounds: RFD3 hits the crystal window on every design we have made and the
      refold is where it is lost (primer d2). If only the refold is scored — which is what "cofold the
      submitted sequence" implies — then refold fidelity *is* the score, and we optimise for it directly.

### A question we could answer ourselves, and did

- [x] **Does Boltz-2 reproduce crystal geometry for a real Kemp eliminase?** We compare designs against
      distances measured from crystal structures but measure the designs with Boltz-2 — two different
      instruments. Folding 4BS0 / 3NYD / 7K4U's own sequences settles it, costs 19 s each, and is bundled into
      every sweep in `cluster/oversample.sbatch`. **Answered:** with query-only alignments the three natural
      enzymes land inside both windows in 0/5, 0/5 and 1/5 seeds ([pitch.md](pitch.md) section 3). That is a
      handicapped comparison, since their sequences carry no MSA here, so we did not rely on it.

**Answered** (from the slides, 2026-11-21 — keep for the record):
- ~~Which atom is the `oxy` target?~~ 6NT is a benzo**triazole** with no ring oxygen; the reference pipeline
  measures donor → `6NT_N1` and base → `6NT_N3`.
- ~~Is pose consistency computed from repeated seeds?~~ Yes — "across multiple Boltz-2 seeds", 5 replicates
  per sequence.
- ~~What exactly is "active-site packing"?~~ Number of CA atoms within 12 Å of the catalytic base.
