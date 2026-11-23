# Submission

One file, `designs.fasta`, uploaded to S3. Source of truth:
[raw/20261121_organizers_submission.md](../raw/20261121_organizers_submission.md).
The scoring criteria are summarised in [challenge.md](challenge.md).

> **Status: closed.** The project phase ended on 2026-11-22. This page stays as reference for the file format, the
> validator and the upload route; what was actually uploaded, and what was not, is in the Status table below.

## File format

```
>my_design_01 base=19 oxy=24
MKAYLVTGGAGFIGSHLVDRLLEQGHEVIVLDNLSTGKRENVPAGATLVEGDLGDAALLD
>my_design_02 base=19 oxy=41
MTAYLITGGAGFIGSHLCERLLADGHDVVVLDNLSTGSRANLDPSASLVVGDIRDGALVR
```

- **Sequence only.** Never include the ligand: every design is cofolded against **6NT**.
- `base=` / `oxy=` are **1-based** indices into *our* submitted sequence — not HG3.17 numbering, not 0-based.
  The first residue is 1. An off-by-one is not an error the scorer catches; it silently measures the
  distance to an unrelated residue and returns a plausible, wrong number.
- `base=` must point at **D** or **E**; `oxy=` at **Q, N, S, T, Y, K** or **R**. They must be different residues.
- `oxyanion=` is a synonym for `oxy=`; spaces around `=` are fine.
- **Nothing else in the header.** Free text after the name is rejected. Keep notes in the repo, not the FASTA.
- **HIS can never be the donor** — the format cannot express the tautomer. Design around it.

## Where the indices come from (worked example)

A pipeline run's `summary.json` hands you both. `rfd3.fixed[].position` values are **1-based indices into
`ligandmpnn.sequence`**, so no renumbering is needed. From the verified reference run:

```
rfd3.fixed: A127 -> position 177, amino_acid D     sequence[177] = D   -> base=177
            A50  -> position  99, amino_acid Q     sequence[ 99] = Q   -> oxy=99
```

Always print the residue at each index before trusting it — `make submission` does this for you and
refuses the file if a residue is of the wrong type.

## Our workflow

1. Collect candidates in `results/designs.jsonl`, one JSON object per line
   (`name`, `sequence`, `base`, `oxy`, plus any notes you like — notes stay out of the FASTA):
   ```json
   {"name": "chris_01", "sequence": "MKAY...", "base": 19, "oxy": 24, "note": "run kemp-1234"}
   ```
2. Build and check locally — this applies every rule above, offline:
   ```bash
   make submission        # -> results/designs.fasta
   ```
3. Run the **organizers'** validator too (it is the authority):
   ```bash
   python3 validate-submission.py results/designs.fasta
   ```
   Get it once per machine:
   ```bash
   aws s3 cp s3://perlin-pdh-2026-paris/release/submission/validate-submission.py . --region eu-west-3
   aws s3 cp s3://perlin-pdh-2026-paris/release/submission/submit-designs.sh      . --region eu-west-3
   chmod +x submit-designs.sh
   ```
4. Upload (needs the team AWS sign-in):
   ```bash
   ./submit-designs.sh results/designs.fasta
   ```
   The browser route and our team's direct bucket link are in
   [raw/20261121_organizers_connect-team01.txt](../raw/20261121_organizers_connect-team01.txt).
   Opening the bucket from the S3 home page shows "Access denied" — that is expected.

## How to fill the 20 slots — the arithmetic, from measured rates

Measured by 2026-11-21, all from `wiki/experiments/chris-04..07` (the final numbers are in
[approach.md](approach.md) and [ranking-combined.md](ranking-combined.md)):

| quantity | measured value |
|---|---|
| RFD3 backbones that are **designable** (median CA RMSD < 2 Å over a sweep) | **2 of 5** seeds (3 and 4); seeds 2 and 5 are not |
| in-window hit rate on a designable backbone | **2 of 72** in a single fold (~3 %), **1 of 72 (~1.4 %) after 5-seed replication**; the Trp44 backbone gave 0 of 72 |
| cost per backbone | 12 min RFD3 + ~25 min for a 72-sequence sweep ≈ **37 min** |
| distinct folds per backbone | **1** — 71 of 72 designs cluster at qTM 0.98–0.99 |

Twenty slots filled with twenty *distinct folds* would need ~20 designable backbones that each yield
a hit. At ~40 % designable and a 3 % hit rate, that is far more than a day of one GPU. **It is not
reachable, and planning for it would waste the time we do have.**

So the realistic shape of a submission is:

- **Aim for 4–6 distinct folds**, not 20. Each needs its own backbone, from a different crystal
  *arrangement* of the same two anchors (`cluster/build_family_motifs.py`) — not from more anchors,
  which costs designability (chris-05).
- **Fill the remaining slots with different sequences on the folds that work.** The slots are per
  sequence, not per fold, and sequences on one backbone differ by 26–42 % identity, so they are not
  duplicates — they are independent bets on the same scaffold.
- **Spread the ≥5 lab-validation nominations across folds**, not across sequences of one fold. If a
  fold is inactive, every sequence on it fails together.
- **Never submit a geometry number from a single fold.** One Boltz-2 prediction carries ~±0.4 Å of
  noise against a 0.28 Å window (primer §5(g5)). Replicate the shortlist over 5 seeds
  (`cluster/replicate_seeds.sbatch`) and rank on the replicated mean.

Order of operations for each candidate: sweep → in-window filter → **5-seed replication** → novelty
gate (`tools/novelty_check.sh`) → `scripts/91_bank_from_sweep.py` → `make submission`. Check fold
diversity across the whole set at the end with `tools/self_diversity.sh`.

## Rules of the road

- Re-upload as often as you like. **The file at the deadline is the one scored**; each upload replaces the last.
- After the deadline S3 refuses uploads. **No grace period** — upload a valid file early, improve it later.
- We cannot see other teams' submissions, and they cannot see ours.
- Every design must pass novelty (TM-score ≤ 0.7, identity ≤ 70 %). Record the check on the experiment page.

## Status (final)

| | |
|---|---|
| Final upload | **2026-11-22 12:16 UTC, by a teammate: 20 designs, 5162 bytes.** We read it back from the bucket, read-only, and compared it with our ranking: [ranking-combined.md](ranking-combined.md) section 4.4. We did not upload anything ourselves after the first file below. |
| Prepared, not uploaded | Two validated alternatives, built from the fresh-seed ranking: [`results/designs_combined_recommended.fasta`](../results/designs_combined_recommended.fasta) (8 designs) and [`results/designs_swapped_18.fasta`](../results/designs_swapped_18.fasta) (the uploaded file with four designs swapped out, 18 designs). The organizers' validator accepts both. |
| Earlier upload | 2026-11-21 23:15:30 UTC (S3's own timestamp), from the cluster with `submit-designs.sh`: 1 design (`chris_osA_01` = s024), sha256 prefix `1cf53b55`, S3 version `b43yX__RrxQPzbJd19vsm3Ek2aDIcCkJ`. Read back and verified: `head-object` showed 294 bytes and an ETag equal to the local file's MD5. This confirmed write access, and was replaced by the later upload. |
| Deadline | **Estimated at about 13:30 UTC on 2026-11-22; never confirmed by the organizers.** The earlier belief (2026-11-22 10:00 Paris/Basel = 09:00 UTC) evidently did not hold, since an upload at 12:16 UTC is in the bucket. |
| Scores | The organizers did not release per-design scores to the team. Everything measured in this repository comes from our own instrument (Boltz-2, five seeds, our scoring code). |

## Uploading from the cluster (done once on 2026-11-21; this is how)

The head node's AWS identity resolves and the shared release prefix is readable (that is how the validator was
fetched). Listing our own submissions folder returns **AccessDenied**, which the organizers' docs describe as
expected; write permission was then confirmed by the first real upload. The documented route is the
organizers' own `submit-designs.sh` (validate, resolve the account id, refuse to upload a rejected file), run on
the cluster beside `validate-submission.py`. Fallback: upload `results/designs.fasta` through the browser using
the folder link in the team packet. Each upload replaces the previous one and the file present at the deadline is
the one scored, so uploading a validated file early and again after every improvement is safe.

## Validator status on 2026-11-21 (historical)

The organizers' own `validate-submission.py` (downloaded from the shared bucket, run on the cluster
with no network) **ACCEPTS** `results/designs.fasta`: 2 designs, 260 residues each, `base=` and `oxy=`
declared and checked. The uploader `submit-designs.sh` has deliberately **not** been downloaded or run.
Re-run the validator after every change to the file.

## Candidate sets prepared at the end of the run (2026-11-22 07:36 UTC; superseded, see Status)

Files on the cluster in `/mnt/work/projects/chris_autopilot/`, all validated and novelty-checked, none uploaded beyond
the first. A teammate later uploaded a different 20-design file (see Status), and the later alternatives are the two
files in `results/` named there.

| file | designs | note |
|---|---|---|
| (already uploaded) | s024 | the strict pre-registered rule |
| `designs_option_B.fasta` | s024 + s010 | recommended; s010 is outside the rule, see primer (g13) |
| `designs_option_C.fasta` | s024 + s010 + s057 + s008 + s060 | wider; the last three are less defensible |

Upload the chosen one with
`cd /mnt/work/projects/chris_oversample_a/validator && ./submit-designs.sh /mnt/work/projects/chris_autopilot/designs_option_B.fasta`.
Each upload replaces the last, and the file present at the deadline is scored.
