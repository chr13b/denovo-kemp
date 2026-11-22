# Our approach: from a catalytic motif to replicated Kemp-eliminase designs

Team 01, Perlin x D-BSSE Protein Design Hackathon. This page is the technical description of what we did, step by
step, with the filters and selection criteria that produced our top designs. It is written to be lifted into the
presentation. Every number comes from a run file or a table in `results/`; where something is an inference, it says so.
The longer reasoning is in `wiki/primer.md` (section numbers in brackets); the scoring rules are in `wiki/challenge.md`.

## 1. In one paragraph

We design 260-residue proteins around the two catalytic contacts of a Kemp eliminase (an Asp base and a Gln donor,
both held in place around the transition-state analogue 6NT). Backbones come from RFdiffusion3 (RFD3), sequences from
LigandMPNN, and each sequence is judged by the same cofold the organizers use (Boltz-2). The central difficulty is
that the designed geometry is almost never reproduced by the cofold, and a single cofold is so noisy (0.4 to 1+ A on a
contact) that ranking designs by one fold ranks noise. So the method is: **generate many sequences on one good
backbone, screen cheaply on one fold, replicate the best over five seeds, and select on the replicated numbers and a
novelty gate**. Sequence-sampling "arms" (a bias on LigandMPNN) were used to raise the share of good sequences.

## 2. What is scored, and what we measure instead

The organizers cofold each submitted sequence with 6NT in Boltz-2, five replicates, and score (their order and wording):
(1) catalytic contact distances, which carries the most weight; (2) approach geometry, angle and in-plane, where the
worse of the two decides; (3) interface confidence iPDE; (4) active-site packing, CA atoms around the base up to 12 A;
(5) pose consistency across seeds. Geometry (1 and 2 together) outweighs everything else combined and the terms
multiply. Novelty (backbone TM-score <= 0.7, sequence identity <= 70 %) is a gate, not a score.

We do not know the scorer's functional forms, so we measure the quantities and build proxies.

| Quantity | Definition | Source of the target |
|---|---|---|
| base distance | declared Asp (index `base=`) carboxylate O to N3 of 6NT | 25 crystal copies: 2.41-2.69 A |
| donor distance | declared Gln (index `oxy=`) NE2 to N1 of 6NT | 25 crystal copies: 2.92-3.24 A |
| approach angle | angle at the ring nitrogen between the contact atom and the ring centroid | base 167.1-175.8 deg, donor 162.1-173.0 deg |
| out-of-plane | angle between the contact vector and the plane of the benzotriazole | base 1.0-11.7 deg, donor 0.6-16.1 deg |
| iPDE | Boltz-2 `complex_ipde`, as reported | lower is better |
| burial | CA atoms within 12 A of the base OD2 (`cluster/rescore_replicated.py`) | 44.6-49.4 across our top designs |

The 25 crystal copies are the engaged ligand copies of the Kemp-eliminase entries in the PDB (43 ligand copies from 23
structures, 25 of them with both contacts engaged); table `results/kemp_family_geometry.tsv`.

**Two ways to measure the base contact, and why both matter.** The organizers' verify script measures OD2 of the
declared Asp. Our `geometry_full.tsv` uses the nearest oxygen of the declared residue. We call a fold "OD2 nearest" when
the two agree within 0.02 A, and require it in at least 4 of 5 seeds (a hedge against an OD2-only scorer).

**D, our geometry score (lower is better).** For each of the six terms, how far the value lies outside its crystal
window, in tolerance units (0.25 A for distances, 15 deg for angles), distances below the window counted double (too
short is punished harder). D is the sum. "Good" is D <= 8.7, the 95th percentile of the unbiased design population.

**D2, "the worse of the two decides".** The organizers say the angle and in-plane terms do not average. D adds them. D2
uses max() of the two per contact. Computed per design in `cluster/rescore_replicated.py`.

## 3. The pipeline, stage by stage

```
motif (HG3.17 Asp + Gln + 6NT) -> RFD3 backbone -> LigandMPNN sequences -> Boltz-2 cofold -> measure
                                  (12 min)          (6 s per batch)        (19 s per fold)
```

1. **RFD3 (backbone).** Input: `HG3_17_kemp_motif.pdb` with Asp A127 held rigid by OD1/CG/OD2, Gln A50 by OE1/CD/NE2, and
   the whole ligand; output a 260-residue backbone (`contig 260-260`) with no side chains. Different seeds build
   different proteins (8.5 % identity between seeds 1 and 2). RFD3 reproduces the crystal contact window on every run
   (about 0.013 A deviation) [primer d2]; all geometric loss happens later, in the refold.
2. **Backbone choice.** Backbones were compared on *designability*: the median CA RMSD between the designed backbone and
   its Boltz-2 refold over a sweep of sequences. It separates backbones (seed 4 passes; seeds 2, 3, 5 and the
   family-motif backbones do not, or give no in-window hits) but says nothing about an individual sequence
   (rank correlation 0.857 across 8 backbones, 0.12 within one) [primer g6b]. **All our designs sit on the backbone of
   seed 4, with the base at position 86 (Asp) and the donor at position 52 (Gln).**
3. **LigandMPNN (sequences).** `ligand_mpnn`, checkpoint `ligandmpnn_v_32_010_25`, ligand and side-chain context on,
   `--fixed_residues "A52 A86"` so the two catalytic residues are never redesigned, temperature 0.1/0.2/0.3, batches of
   8, seeds `1000 x T + offset`. Many sequences per backbone: 72 per sweep.
4. **Boltz-2 (the check).** `boltz predict`, model boltz2, 200 sampling steps, 3 recycling steps, 1 diffusion sample,
   query-only alignment. The MSA stage is a no-op for de novo sequences (no homologue exists; MSA depth 1), measured as
   bit-identical output with and without it [chris-03], so we skip MMseqs2 for a 3-4x gain. The seed is per invocation,
   so a replicate seed is set per call (`--seed`), and the noise depends on the batch composition.
5. **Measurement.** `cluster/measure_boltz_outputs.py` (declared residues, nearest-atom scan as a cross-check) and
   `cluster/geometry_vs_crystal.py` (all quantities of section 2) per structure, written to `geometry.tsv` and
   `geometry_full.tsv`.

## 4. Filters and selection, in the order they are applied

| Step | What it does | What it removes | Evidence |
|---|---|---|---|
| F0 | RFD3 backbone is a defect filter only | broken backbones | no RFD3-stage feature predicts success (Zonghu: |rho| < 0.6, n = 11) |
| F1 | Single fold per sequence, ranked by D | the great majority | across 352 swept designs, **84 % have the ligand outside the pocket** |
| F1b | free filter iPDE < 1.6 and ipTM > 0.85 | 83 % of designs | keeps 17 % and 5 of the 6 best by D |
| F2 | **5-seed replication** of the best by single-fold D (top 20, then top 25) | designs that were one lucky fold | 48 designs replicated in total; most single-fold winners do not survive |
| F3 | selection rule (pre-registered) | everything that is not reproducible | see below |
| F4 | novelty gate | designs too close to published structures | foldseek TM-align, query-normalised, both databases |
| F5 | index check | off-by-one in `base=` / `oxy=` | residue at `base=` must be D/E, at `oxy=` in QNSTYKR (never H) |
| F6 | the organizers' validator | invalid files | must print ACCEPTED |
| F7 | upload, byte-verified read-back | | `submit-designs.sh` |

**F3, the pre-registered rule** (written before the replication data): both distances inside the crystal window in at
least 3 of 5 seeds (declared residues, OD2 for the base), mean D over the five seeds <= 15, and OD2 the nearest oxygen in
at least 4 of 5 seeds. Free slots stay empty: the organizers do not say how a team is scored from its designs (best,
mean or sum), and a weak extra design could dilute a mean.

**F4, novelty.** qTM (TM-score normalised by the designed protein, the question "is my fold already known?") must be
<= 0.70 against (a) the Kemp-eliminase family structures and (b) 40,066 PDB 30 %-identity representatives. Our top
designs: family qTM 0.29-0.30, PDB qTM 0.55-0.57. Sequence identity: MMseqs2 found no homologue at all (MSA depth 1), and
Zonghu measured 32-37 % to the HG series. Which TM normalisation the organizers use is not confirmed.

**What the rule did.** Only **s024** satisfies it. Several close variants have a better replicated mean geometry but
narrowly miss "both in window in 3 of 5 seeds" (s010 misses the donor window by 0.06-0.18 A in three seeds). Adding them
is an amendment made after seeing the data, and is recorded as such in `wiki/submission.md`.

## 5. The sequence-sampling arms, technically

### 5.1 The mechanism

LigandMPNN decodes the sequence one position at a time, in a random order, conditioning each residue on the structure,
the ligand and the residues already chosen. At each position it computes logits over the 20 amino acids and samples from

    p(aa) = softmax( (logit(aa) + bias(position, aa)) / T )

(LigandMPNN `model_utils.py`, `sample()`; the bias is added to the raw logit and then divided by the temperature). A
**bias file** is a JSON `{"A49": {"S": -1.5, "T": -1.5}, ...}` passed with `--bias_AA_per_residue`; keys are chain plus
PDB residue number. Because the bias is added before the division, **at T = 0.3 a bias of 1.5 is a log-odds shift of
1.5 / 0.3 = 5, i.e. a factor of about 148 in odds**, and 3.0 is a shift of 10. This is why the biases are small numbers
and still decisive.

**What is enforced, and by what.** The bias changes probabilities; it does not forbid anything. The two catalytic
residues are held by a separate mechanism, `--fixed_residues`, which masks them out of sampling so the input residue is
copied through (`S_t = S_t * chain_mask + S_true * (1 - chain_mask)`). We verify afterwards that Asp86 and Gln52 are
intact in all 216 arm sequences (72 of 72 in every arm).

### 5.2 How each arm's bias file is built (`cluster/make_arm_inputs.py`)

* **Pocket positions.** The 13 residues with any atom within 5 A of the ligand on the *designed* backbone (positions 49,
  52, 56, 82, 86, 116, 119, 143, 213, 214, 217, 243, 247). 52 and 86 are pinned, leaving **11 free pocket positions**.
  They are defined on the designed backbone on purpose: defined on the refold they would depend on where the ligand
  landed, which is circular.
* **Polar-down:** S, T, N, Q, H shifted by -1.5 at the 11 sites. The crystals have about 2.1 polar residues within 4.5 A
  of the ligand (about 1 once the pinned Gln50 is removed); our designs with the ligand in place have 4.5.
* **Aromatic** (not run to completion): W +3.0, F and Y +2.25 at the 11 sites. No design had any aromatic residue there
  although the crystal ring is stacked by Trp44.
* **Close variants of a parent:** +1.5 toward the parent's own residue at a random 88 % of the non-pinned positions
  (seed 7); the other 12 % (31 positions) are left free. Calibrated on the head node: push 1.0 gave 83-89 % identity to
  the parent, 1.5 gave 89-93 %, 2.5 gave 93-97 %.

All arms: 72 sequences, T = 0.3 only, one Boltz-2 fold each (seed 1), the same backbone, scored by D, compared with a
72-sequence unbiased baseline run the same way. The job is `cluster/oversample.sbatch` with the bias passed through
`OS_EXTRA_ARGS`; a different seed offset per arm keeps the random streams apart.

### 5.3 Did the bias do what it was meant to? (measured on the sequences that came out)

| arm | identity to s024 | polar (S/T/N/Q/H) at the 11 pocket sites | aromatic (W/F/Y) there | D86 and Q52 kept |
|---|---|---|---|---|
| baseline, no bias | 63 % | 4.0 of 11 | 0.0 | 72 / 72 |
| polar-down, -1.5 | 62 % | **1.7 of 11** | 0.1 | 72 / 72 |
| close to s024, +1.5 | **91 %** | 3.1 of 11 | 0.0 | 72 / 72 |

Both levers were applied as intended: polar-down cut the polar count by 58 %, close variants raised identity from 63 to
91 %. So the polar-down null result below is a real null, not a failed bias.

### 5.4 What the arms found

| arm | median D | D <= 8.7 | D <= 20 | ligand in place | vs baseline |
|---|---|---|---|---|---|
| baseline | 30.5 | 1 | 12 | 22 | |
| polar-down | 32.1 | 1 | 9 | 15 | Mann-Whitney p = 0.21 |
| **close variants of s024** | **25.2** | **11** | **28** | **34** | **p = 0.013** |

* **Close variants enrich the good tail about 11-fold** (11 against 1 design with D <= 8.7), and the effect is dose-
  dependent *within* the arm: by identity to s024, the lowest third (86-91 %) has 2 of 24 good designs (median D 30.6),
  the middle third 3 of 24 (24.1), the highest third (92-95 %) 6 of 24 (21.9).
* **No single mutation is established.** 133 of the 260 positions vary across the 72 sequences. The strongest candidate
  is I59M (4 of the 11 good designs against 3 of the other 61; one-sided Fisher p = 0.009 before correcting for about
  400 candidate residues, so not significant), and it is absent from the two best replicated designs (s010, s057). The
  effect looks diffuse, which fits the earlier finding that the pocket residues are the same in the best and the worst
  designs [primer g9]. Our reading, not tested: geometry depends on the scaffold context around the pocket, which a
  close variant inherits from its parent.
* **Polar-down does not help**, though it was read off the crystals. The pre-registered winner rule (median <= 0.8 x
  baseline and a large gain in good designs) is formally **not met** for close variants (median 25.2 against a 24.4 cut),
  although the count of good designs passes widely. Reported as it is.
* **At the replicated level the enrichment is weaker than at the single-fold level.** Of the 25 arm designs replicated
  over five seeds, 3 of 17 close variants, 1 of 4 polar-down and 0 of 4 baseline designs reach a replicated mean D
  <= 8.7. The numbers are small and the replicated designs were chosen by single-fold D, so this is consistent with the
  lever but does not demonstrate it at the level that is scored.
* **Not run:** the aromatic arm (cancelled after one minute), the checkpoint-005 arm and the 216-sequence main sweep, all
  for time. Those hypotheses remain untested. All arms share one backbone, so none adds fold diversity.

## 6. Results: the replicated designs

Five-seed replicated numbers (declared residues; D, D2 and A_over are means over the five seeds). From
`results/rescored_replicated_48.tsv`.

| design | mean D | mean D2 | seeds D <= 8.7 | worst seed D | both in window | OD2 nearest | iPDE | burial |
|---|---|---|---|---|---|---|---|---|
| s010 (close variant) | 3.8 | 3.2 | 5 / 5 | 5.5 | 2 / 5 | 5 / 5 | 1.13 | 49.2 |
| s057 (close variant) | 5.0 | 4.8 | 5 / 5 | 7.9 | 1 / 5 | 5 / 5 | 0.98 | 46.4 |
| s008 (polar-down arm) | 6.2 | 5.1 | 4 / 5 | 9.0 | 1 / 5 | 5 / 5 | 0.91 | 45.6 |
| s060 (close variant) | 7.5 | 7.2 | 3 / 5 | 9.2 | 0 / 5 | 5 / 5 | 0.94 | 46.2 |
| s024 (the parent; the only rule pass) | 9.4 | 8.2 | 4 / 5 | 29.6 | 3 / 5 | 5 / 5 | 1.20 | 48.4 |
| s068 (seed-4 sweep) | 10.6 | 7.1 | 0 / 5 | 11.6 | 0 / 5 | **0 / 5** | 0.79 | 47.0 |

* **s010 is first under D and under D2.** Burial hardly separates designs (40.0-50.4 over all 48, 44.6-49.4 across the
  top 16), so adding it to our score changes no ranking.
* **s024 has one seed that loses the ligand** (D 29.6) and otherwise performs like the others.
* **s068** has the lowest iPDE (0.73-0.89) and a very stable pose, but its nearest oxygen is OD1, and OD2 is 3.2-3.4 A from
  N3. It passes if the scorer takes the nearest oxygen and fails if it takes OD2.

**Cross-check with an independent scorer.** Zonghu's weighted score of K1-K5 (his own implementation, 5 seeds per design,
target geometry from 7K4U) ranks the same designs: s010 0.759 (second of 193 designs), s068 0.718, s057 0.696, s060 0.594,
s008 0.566, s024 0.562; his own newer sequence `new:s018` leads at 0.775. On single folds his score and our D correlate at
Spearman -0.97 over 44 shared structures (fewer effective samples, since 15 are one design at several seeds). Both
analyses found independently that a single fold overstates a design.

**A shared weakness.** The angle *at the heteroatom* (C-O...N3 for the base, C-N...N1 for the donor, the definition his
K2 uses) lies outside the crystal range in **every one of the 48 replicated designs**: median 40 deg outside, range 10.6
to 93.2 deg, and only 12 designs under 30 deg. Our top candidates are 35 to 61 deg outside (s010 35, s008 35, s057 47,
s060 54, s024 61, s068 66). Under our own angle definition the same designs are close to the crystal window. The
organizers do not say which definition they use. If it is his, our designs lose on that term, and nothing we have
generated so far was selected for it.

## 7. Limits and open questions

* **One fold.** Every submitted candidate sits on seed 4's backbone; four of the five top designs share 88-94 % identity.
  A scorer whose definition differs from ours would hit them together.
* **Winner's curse.** The best of 48 (ours) or 193 (Zonghu's) replicated designs is partly luck, and the five seeds used
  to select are the five seeds that are reported. An independent re-fold with new seeds is the remedy and is planned.
* **Unconfirmed scorer details:** OD2 against the nearest oxygen; which angle definition; how a team is scored from its
  designs; which TM normalisation defines the novelty gate; how the five lab-validation designs are chosen; the exact
  deadline.
* **Proxy, not the score.** D, D2 and the replicate statistics are our stand-ins. They agree with an independent scorer on
  the ranking of single folds, which supports them, but the organizers' functional forms are unknown.

## 8. Reproducing it

| Step | Script |
|---|---|
| bias files for the arms | `cluster/make_arm_inputs.py <backbone.pdb> <queries.json> <reference> <out_dir> [seed]` |
| sequence sampling, folding, measuring | `cluster/oversample.sbatch` (`OS_EXTRA_ARGS`, `OS_SEED_OFFSET`, ...) |
| five-seed replication | `cluster/replicate_seeds.sbatch` (`RS_FASTA`, `RS_SEEDS`) |
| unattended driver (replicate, arms, rank) | `cluster/autopilot.py` |
| burial, D2 and the angle at the heteroatom | `cluster/rescore_replicated.py` |
| rule, novelty gate, index check, validator | `cluster/finalize.py` (never uploads) |
| share pack for a teammate | `tools/make_share_pack.py` |
