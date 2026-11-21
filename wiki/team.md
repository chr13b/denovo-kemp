# Team

**`bash onboard.sh` adds your row for you** — it asks for a handle and fills in the rest. Then edit your own
row to say what you're good at and what you're taking on. Don't edit other people's rows; this file is
union-merged, so two people adding rows at once will not conflict.

Your handle is a short lowercase nickname; it goes into your branch names, experiment IDs and log entries.
Full setup: [../SETUP.md](../SETUP.md). "Owns" = who reviews and decides, not the only person allowed to touch it.

| Handle | GitHub | Background / strengths | Owns | Current branch |
|--------|--------|------------------------|------|----------------|
| chris | chr13b | — | repo, cluster access, pipeline | `chris` |
| TODO | | | | |

## Working agreements

- Every ~2–3 h: `make sync`, write a log entry (`uv run python tools/new.py log …`), then a 10-minute
  stand-up around `make status`.
- Merge into `main` early and often: small pull requests, merge commits, CI green.
- Add an experiment page *before* running (`uv run python tools/new.py exp …`) so nobody duplicates work.
- Decisions with lasting impact go in [decisions.md](decisions.md).
- Cluster etiquette: 2 GPU workers for the whole team, so say in the chat when you start a long job.
  Name your project folders `<handle>_<topic>` and never touch `/mnt/work/kemp_example`.

## ⚠️ Every `kemp-e2e` job burns ~10 min of shared GPU on a stage that does nothing

As of 2026-11-21 there are five `kemp-e2e` jobs queued behind one usable GPU. Each spends roughly
**10 of its ~23 minutes** in the MMseqs2 stage, and chris-03 proved that stage is a **no-op** for de
novo designs: every one returns `depth 1, nonquery_rows 0`, and removing it gives **bit-identical**
Boltz-2 output (same MD5). Five jobs is therefore about **50 minutes of queue time spent on nothing**,
on a cluster where we are all waiting behind each other.

The MMseqs2 index is also the only reason the template asks for `--mem=30G --constraint=g6.2xlarge`.
Drop the stage and a job fits a smaller node and runs ~2× faster.

If you only need backbones, or only need to fold sequences, use the split pipeline in `cluster/`:

    bash cluster/launch_design.sh     <name> <motif-dir>   # RFD3 only, ~12 min per motif
    bash cluster/launch_oversample.sh <name> <run-dir>     # LigandMPNN + Boltz-2 only, ~25 s/sequence

`launch_oversample.sh` reads any finished run's `bridge/` **read-only**, so it works on your runs
without touching them.

**And a second reason not to run single end-to-end designs:** one Boltz-2 fold is noisier than the
geometry window we are aiming at. The same control sequence at the same `--seed 1` gave base contacts
of 2.49 Å and 2.07 Å in two different batches, against a window 0.28 Å wide. A single design's
geometry number is not a result — see `wiki/primer.md` §5(g5).

## ⚠️ Cluster: the two l4small nodes are dead, and jobs asking for them hang forever

`gpu-dy-l4small-1` and `-2` sit in `idle~`/`idle%` with reason "Scheduler health check" and Slurm
will not resume them. We are not admins, so `scontrol update NodeName=... State=POWER_UP` returns
`Invalid user id`. **Effectively the cluster is one GPU: `gpu-dy-l4-1` (g6.2xlarge, 8 CPU, 31 GB).**

**If your job requests `--constraint=g6.xlarge` it will never start.** It shows as
`Reason=ReqNodeNotAvail,_UnavailableNodes:gpu-dy-l4small-[1-2]`. zonghu's jobs 32 and 33 are in
exactly this state as of 2026-11-21 — I have not touched them, since they are yours to requeue.

**Use `--constraint=g6.2xlarge`** (the one working node). I previously advised
`--constraint="l4small|l4"` here and **that was wrong while the small nodes are dead**: Slurm allocates
the job to a dead node, the power-up fails, and the job is requeued to the back of the line. My own job
47 was requeued **6 times and never ran** before I found this (`scontrol show job <id> | grep Restarts`
— anything above 0 means you are in this loop). Switch back only when `sinfo` shows an l4small node
healthy. Never request `l4big` — it is reserved.

Check your own jobs with:

    squeue -o "%.6i %.14j %.9T %.6M %.18R"
    scontrol show job <id> | grep -E "Reason|Features"

## For zonghu — please read before launching more backbones (chris, 2026-11-21)

**UPDATE, after actually testing it (job 31):** I owe you a second correction, in the other
direction. I said your Trp44 motif "was never refuted, only tested with one sequence" — true — and
predicted it would win once tested properly. **It lost.** 72 sequences on your backbone:

| | seed 4 backbone | your Trp44 backbone |
|---|---|---|
| best base contact | **2.38 Å** | 3.26 Å |
| median donor contact | 4.68 Å | **18.92 Å** |
| median CA RMSD | **0.77 Å** | 2.02 Å |
| refolded < 2 Å | 70/72 | 35/72 |
| inside both windows | **2/72** | **0/72** |

Your single-sequence result (CA RMSD 4.26 Å) was not unlucky — it was the tail of a distribution whose
median is 2.02 Å. The motif is fine chemically and RFD3 satisfies it to 0.0167 Å; the problem is that
the backbone RFD3 has to build to satisfy four constraints at once (base, donor, indole plane, whole
ligand) is one LigandMPNN cannot write a stabilising sequence for. **Pinning more geometry costs
designability, and RFD3's deviation number cannot see that cost.**

So: the two-anchor motif wins, and the way to get backbone diversity is different *arrangements* of
the same two anchors (crystal structures from the family — `/mnt/work/tools/family_motifs/`) rather
than more anchors. Full write-up in `wiki/experiments/chris-05_…`; your job 7 is cited throughout.


Your Trp44 theozyme was **not** refuted by job 7, and I was wrong to read it that way.

`summary.json` reports the catalytic contacts twice. On your run the RFD3 column reads **base 2.53 Å,
donor 3.20 Å** — inside the window measured across 23 crystal structures (2.41–2.69 / 2.92–3.60). The
geometry was lost in the **Boltz-2 refold** (CA RMSD 4.26 Å), not in the motif. The same is true of all
five of my seeds: RFD3 nails it every time, the refold loses it, and the refold is decided by the
**sequence** — which the launcher samples exactly once (`id: 1, T: 0.1`).

Your hand-off is also correct, which I had doubted: `bridge/sequence.json` maps A50→237 (Q), A127→54 (D),
A44→98 (W), so all three anchors survive into the sequence. The `prepare_rfd3_input.py` warnings are just
the launcher noting the motif is not its 2-residue default. And your LigandMPNN scores beat mine
(`ligand_confidence` 0.534 vs 0.445, `seq_rec` 0.483 vs 0.302).

**What this means for your queue:** a new RFD3 backbone costs 12 min; a new sequence on an existing
backbone costs 6 s (LigandMPNN) + 19 s (Boltz-2). Sampling 32–72 sequences on a backbone you already
have is cheaper than two new backbones and varies the thing that actually fails.

`cluster/launch_oversample.sh <project-name> <your-run-dir>` does it from any finished run's `bridge/`,
read-only — I ran it on your `kemp-7` as chris-05 and touched nothing in your directories. Two things to
know: `boltz predict <dir>` chokes on `.a3m` files in the same directory, and the template's
`--constraint=g6.2xlarge --mem=30G` exists only for the MMseqs2 index, so dropping MMseqs2 lets a job fit
the l4small nodes.

Also worth your time: your `aff_*` affinity runs show the TS analogue separating cleanly from substrate
and product in all three enzymes, but HG3 and HG3.17 score **2.06 vs 2.06** despite ~1000× activity
difference. Good negative filter, not a ranker. Details in `wiki/primer.md` §5(h).

**CORRECTION to the update above (same day, after checking my own statistics):** "it lost" overstated
what one backbone can show. Each condition I compared is a **single** RFD3 backbone, and the plain
two-anchor motif's own seeds range widely: median CA RMSD 0.77, 1.33, 1.53, 1.91, 1.92 and 10.67 Å.
Your backbone's 2.02 Å sits inside that range — I had compared it against seed 4, which I chose
*because* it was the best. What does look unusual is the **donor** contact (median 18.92 Å, against
4.7–11.9 Å for every other backbone, i.e. the ligand leaves the pocket); that may be real, but it is
still n = 1. So: **no evidence the third anchor helps, and no proof it hurts.** Please don't drop the
Trp44 line on my say-so — two or three more RFD3 seeds with your motif would show whether the donor
result repeats, and that is ~12 min each.

## Division of labour (suggestion for the first hours)

Discuss and overwrite. The point is that nobody waits on anybody.

| Track | What | Why it is independent |
|---|---|---|
| Pipeline | get the example verified, then run the first own design end to end | needs the cluster, not our analysis code |
| Scoring | reimplement the scoring terms as a local filter: contact distance/angle/dihedral, and **base burial = count CA atoms within 12 Å of the catalytic base** (the one term with an exact published definition — start there) | pure geometry on predicted structures |
| Novelty | TM-score and sequence-identity checks against published structures | gate every candidate before it takes a submission slot |
| Strategy | read the scoring section closely, decide what to optimize, keep `wiki/pitch.md` current | reading and writing, no compute |
