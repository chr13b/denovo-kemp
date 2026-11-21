---
name: experiment
description: Plan, run and record a computational experiment reproducibly. Use when the user wants to try an idea, run a pipeline step, compare settings, or asks "let's test whether…".
---

# Run an experiment

1. **Question first.** Run `make status` to check that no one has done this already.
   Then run `python tools/new.py exp <slug>`, which creates `wiki/experiments/<handle>-NN_<slug>.md` and prints the ID.
   Fill in the Question and Why-it-matters lines, and leave the status as `planned`.
2. **Code.** Prefer adding a `Config` field to an existing script over writing a near-duplicate script.
   For a new pipeline step, copy `scripts/00_smoke.py` to `scripts/NN_specific_verb_noun.py` and keep its shape.
   Put reusable settings in `configs/<id>.json`. Add a new script to `INDEX.md` (configs are covered by `configs/`).
   For new data, use `kemp.data.fetch(..., checksum=...)` and add a row to `wiki/data.md`.
3. **Commit, then run.** Use the experiment ID as the run name, so the page, config and run dir share it.
   `meta.json` then records a meaningful commit:
   `uv run python scripts/NN_x.py configs/<id>.json --name=<id> --seed=0`
   While it runs, set the status to `running`.
4. **Record.** Read the numbers from the run's `summary.json` and `metrics.jsonl`. Never quote a number you didn't read there.
   On the experiment page, fill in Runs (run dir + commit), Result, and Verdict and next step.
   Set the status to `done: supported`, `done: refuted` or `done: inconclusive`.
   If a figure or table is worth keeping, copy it to `results/` and index it with its run ID.
5. **Log.** Run `python tools/new.py log experiment "<id> <title>"` and write the result in one line.
6. If the result changes the plan, also update `wiki/challenge.md`, `wiki/decisions.md` or `wiki/pitch.md`.
   If the step belongs in the final pipeline, add it to `make reproduce`.
7. Run `make check`.
