---
name: submit
description: Build, check and upload designs.fasta for the hackathon submission. Use when the user wants to submit designs, add a design to the submission, check the FASTA file, or asks "are we ready to submit".
---

# Build and upload the submission

Rules and format: `wiki/submission.md`. The organizers' validator is the authority; ours is the early warning.

1. **Collect candidates** in `results/designs.jsonl`, one JSON object per line:
   `{"name": "<handle>_01", "sequence": "MKAY...", "base": 19, "oxy": 24, "note": "run kemp-1234"}`
   Extra keys are fine and stay out of the FASTA. Max 20 designs; duplicates waste a slot.
2. **Check the catalytic indices by hand for every new design.** They are **1-based indices into the
   submitted sequence**, not HG3.17 numbering. `base=` must land on D or E, `oxy=` on Q/N/S/T/Y/K/R
   (never H). An off-by-one is not caught by the scorer: it measures an unrelated residue and returns a
   plausible but wrong number. Print the residue at each index and confirm it.
3. **Build and validate offline:** `make submission` → `results/designs.fasta`.
   It refuses to write the file if any rule is broken; fix the reported problems rather than working around them.
4. **Run the organizers' validator**, which decides: `python3 validate-submission.py results/designs.fasta`.
   Fetch it once with the `aws s3 cp` commands in `wiki/submission.md`.
5. **Check novelty** per design before counting it as a submission: TM-score ≤ 0.7 to published structures
   **and** ≤ 70 % sequence identity to published enzymes. Mutating a known Kemp eliminase does not qualify.
   Record the check on the experiment page. If it has not been verified, say so plainly.
6. **Upload** (needs the team AWS sign-in): `./submit-designs.sh results/designs.fasta`.
   Re-uploading replaces the previous file; **the file present at the deadline is the one scored**,
   and there is no grace period. Upload something valid early.
7. **Record it:** update the Status table in `wiki/submission.md` (count, time of upload), then
   `python tools/new.py log submit "<n> designs uploaded"`, and tag the commit:
   `git tag -a submission-vN -m "..." && git push origin submission-vN`.
