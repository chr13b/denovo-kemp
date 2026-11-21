---
name: experiment
description: Plan, run and record a computational experiment reproducibly. Use when the user wants to try an idea, run a pipeline step, compare settings, or asks "let's test whether…".
---

# Run an experiment

1. **Question first.** Add a row to `wiki/experiments.md` with:
   - the next `E-NNN` ID
   - the question or hypothesis
   - which result would change our plan

   Set its status to `planned`. Check the table first so you don't duplicate earlier work.
2. **Code.** Prefer adding a `Config` field to an existing script over writing a near-duplicate script.
   For a new pipeline step, copy `scripts/00_smoke.py` to `scripts/NN_verb_noun.py` and keep its shape.
   Put reusable settings in `configs/E-NNN.json`, and add both files to `INDEX.md`.
3. **Commit, then run.** That way `meta.json` records a meaningful git commit:
   `uv run python scripts/NN_verb_noun.py configs/E-NNN.json --seed=0`
   While it runs, set the status to `running`.
4. **Record.** Read the numbers from the run's `summary.json` and `metrics.jsonl`. Never quote a number you didn't read there.
   In the experiments row, fill in the run directory, key results and a verdict
   (`supported`, `refuted` or `inconclusive`), plus the next step.
   If a figure or table is worth keeping, copy it to `results/` and index it with its run ID.
5. **Log.** Append `## [YYYY-MM-DD] experiment | E-NNN <title>` to `LOG.md`, with the result in one line.
6. If the result changes the plan, also update `wiki/challenge.md` or `wiki/decisions.md`.
7. Run `make check`.
