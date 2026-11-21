# Challenge

**Perlin x D-BSSE Protein Design Hackathon — we are team 01.**
Sources: [raw/20261121_organizers_start-here.md](../raw/20261121_organizers_start-here.md),
[raw/20261121_organizers_submission.md](../raw/20261121_organizers_submission.md),
[raw/20261121_organizers_cluster-guide.md](../raw/20261121_organizers_cluster-guide.md).
Details on running jobs are in [cluster.md](cluster.md); the file format is in [submission.md](submission.md).

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

Each design is cofolded with ligand 6NT in **Boltz-2** and ranked against other teams' designs.
The terms **multiply**, so one failed term cannot be bought back by another.

1. **Catalytic contact distances** — highest weight. Declared base near the atom it deprotonates,
   declared donor near the atom that develops negative charge.
   **There is an optimum, not a direction:** too short is a clash and is punished *harder* than the same error too long.
   The targets come from crystal structures of working Kemp eliminases and from textbook H-bond geometry.
2. **Approach geometry** — the angle to the ring and whether the contact lies in the ring plane.
   The **worse** of the two decides (they do not average). An end-on donor scores badly even at a perfect distance.
3. **Interface confidence (iPDE)** — mean predicted distance error over the protein-ligand interface. Lower is better.
4. **Active-site packing** — the catalytic base enclosed in a pocket, not solvent-exposed.
5. **Pose consistency** — the ligand lands in the same place across repeated predictions. Variance counts against us.

Geometry (1 + 2) **outweighs everything else combined**. Designs are folded **with MSAs**, so a natural-scaffold
design is not handicapped versus a de novo one.

> **Scoring happens on the Boltz-2 cofold, not on RFD3's output.** In our verified reference run the base
> contact was 2.53 Å in the RFD3 design but 5.91 Å after refolding, while the donor contact held. One run
> is not proof, but filter candidates on Boltz-2 geometry rather than RFD3 geometry until we know better:
> [experiments/chris-01_reference-pipeline-baseline.md](experiments/chris-01_reference-pipeline-baseline.md).

## Resources

- **Cluster:** AWS GPU cluster, Slurm, 2 GPUs in parallel (2× g6.xlarge) **or** 1 bigger node (g6.2xlarge), not both.
  Details and commands: [cluster.md](cluster.md).
- **Provided pipeline:** RFD3 (backbone) → LigandMPNN (sequence) → MMseqs2 (MSA) → Boltz-2 (complex prediction).
- **Provided example:** a single 260-residue Kemp design with the catalytic base, donor and ligand fixed.
- Other tools and pipelines are allowed, but **only the provided compute**.

## Timeline

- 2026-11-21: kickoff, repo set up, cluster access verified.
- TODO: submission deadline (ask an organiser and put it here — after the deadline S3 refuses uploads, no grace period).
- TODO: presentation slot.

## Submission checklist

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

- [ ] What is the exact submission deadline (date, time, timezone)?
- [ ] Is there a presentation, and how long?
- [ ] License/IP rules for our code and designs? (decides whether we add a LICENSE file)
- [ ] Which atom exactly is the `oxy` target (leaving oxygen O1 of 6NT)? Useful for our own geometry checks.
- [ ] Are repeated Boltz-2 predictions with different seeds the way the pose-consistency term is computed?
