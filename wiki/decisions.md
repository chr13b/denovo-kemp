# Decisions

Record a decision here if it would be expensive to reverse, or if someone might later ask "why?".
**Append only** (this file is union-merged). Use a dated heading, never a number:
`## YYYY-MM-DD · Title (handle)`, followed by Decision / Why / Alternatives. To revise a decision, add a new
entry that names the old one.

## 2026-11-21 · Repo layout: LLM wiki + nano-style code (chris)
- **Decision:** Three layers:
  - `raw/`: immutable sources
  - `wiki/` + `INDEX.md` + `log/`: maintained knowledge
  - code (`src/`, `scripts/`, `configs/`): outputs go to `runs/` (disposable, gitignored) and `results/` (curated, tracked)
- **Why:** The team is new, and the AI pair programmer starts every session cold.
  - A single map (`INDEX.md`, auto-loaded through `CLAUDE.md`) lets anyone find their way around in a minute.
  - The log gives the timeline.
  - Run directories that record the config and git commit make every number traceable.
- **Inspiration:**
  - Karpathy's "LLM Wiki" gist: raw sources / wiki / schema file, an index and a log, and the ingest / query / lint operations
  - nanoGPT and nanochat: flat, readable code with minimal abstraction
  - cookiecutter-data-science: data kept separate from results
- **Alternatives:**
  - The full cookiecutter-data-science layout (too many empty directories for a hackathon)
  - Hydra + W&B (setup costs more than it saves at hackathon scale; revisit if we run large sweeps)

## 2026-11-21 · Python ≥ 3.10, managed by uv (chris)
- **Decision:** Use uv for the environment, and commit `uv.lock` and `.python-version`. CI installs with `uv sync --locked`.
- **Why:** It gives a reproducible environment with one command on every teammate's machine and in CI.
- **Alternatives:** conda (slower and harder to lock). Tools that need conda or a container get a pinned spec
  in `envs/` and a wrapper script.

## 2026-11-21 · Merge-safe conventions for parallel personal branches (chris)
- **Decision:**
  - One file per log entry (`log/`) and per experiment (`wiki/experiments/`)
  - IDs per person (`<handle>-NN`), never global counters
  - `merge=union` for shared append-only lists; `uv.lock` is regenerated, never merged
  - pre-commit hooks + CI on every push
  - Merge `origin/main` locally before each PR, and merge PRs with merge commits
- **Why:** Everyone starts on their own branch. A single shared log, a shared table or a "next free number"
  would conflict on every merge.
- **Alternatives:**
  - One `LOG.md` with `merge=union` (GitHub's web merge ignores merge drivers, so conflicts would still appear there)
  - Trunk-only development (too risky while people don't know each other's code yet)

## 2026-11-21 · Keep AI-assistant instructions tool-neutral (chris)
- **Decision:** `AGENTS.md` is the canonical brief for AI assistants, and `CLAUDE.md`, `GEMINI.md`,
  `.github/copilot-instructions.md` and `.cursor/rules/kemp-challenge.mdc` point at it. Procedures live
  as plain-Markdown playbooks in `.claude/skills/<name>/SKILL.md`, readable by any tool.
- **Why:** Everyone on the team uses a different assistant and brings their own prompts and skills. One
  shared brief keeps the project rules identical across tools, while personal tooling stays personal.
- **Alternatives:** Claude-only instructions (excludes teammates); duplicating the rules per tool
  (they would drift apart within a day).

## 2026-11-21 · Our own offline submission validator (chris)
- **Decision:** `kemp.submission` + `make submission` rebuild `designs.fasta` from `results/designs.jsonl`
  and enforce every documented rule locally; the organizers' `validate-submission.py` stays the authority.
- **Why:** Scoring cannot detect a wrong `base=`/`oxy=` index — it measures an unrelated residue and
  returns a plausible but wrong number. A local check with tests makes that mistake visible immediately,
  and the file is rebuilt reproducibly instead of hand-edited.
- **Alternatives:** Writing the FASTA by hand (one typo costs a slot or the score); relying only on the
  organizers' validator (needs AWS, and tends to be run too late).

## 2026-11-21 · Split the pipeline: design once, sample sequences many times (chris)
- **Decision:** Stop running the organizers' end-to-end pipeline for each design. Run RFD3 once per
  *design problem* (`cluster/design_backbones.sbatch`) and then sample 30–70 sequences per backbone,
  folding each (`cluster/oversample.sbatch`). Neither stage runs MMseqs2. Keep every design whose refold
  lands in the family-measured window, base 2.41–2.69 Å and donor 2.92–3.60 Å.
- **Why:** `summary.json` reports the catalytic contacts twice, on the RFD3 backbone and on the Boltz-2
  refold. Across all six full-pipeline runs — ours and zonghu's — RFD3 gives base 2.53 Å / donor 3.09 Å
  every time, dead centre in the crystal window, reproducing the pinned motif to 0.013 Å. **All of the
  geometric loss is in the refold**, which is determined by the sequence — and the pipeline samples the
  sequence exactly once per backbone (`id: 1, T: 0.1`). At 6 s for LigandMPNN and 19 s for Boltz-2 against
  12 min for RFD3, we were spending the expensive step to re-roll the cheap one.
- **Alternatives:** More RFD3 seeds (what we did before — varies the one thing that was already correct);
  force-field relaxation (never scored, since the organizers fold the submitted sequence themselves);
  tighter `select_fixed_atoms` or shorter contigs (both act on a step already exact to 0.013 Å).

## 2026-11-21 · Judge designs against the instrument, not only the crystals (chris)
- **Decision:** Fold the real enzymes' own sequences (4BS0, 3NYD, 7K4U) with 6NT in **every** sweep, and
  calibrate the target window against what Boltz-2 reports for them rather than against the crystal
  distances alone. `cluster/build_control_fasta.py` takes the sequences from the deposited structures.
- **Why:** The target window comes from crystallography; our designs are measured by Boltz-2. Those are
  different instruments and we had never cross-checked them. If Boltz-2 reports ~3.3 Å for HG3.17 itself,
  then seed 4's 3.32 Å is at parity with a working enzyme and the "miss" was an artefact of comparing
  across instruments. It costs 19 s and it changes the meaning of every geometry number we report.
- **Alternatives:** Trusting the crystal numbers directly (risks optimising toward an unreachable target);
  asking the organisers for the scorer's reference values (worth doing anyway, but slower than measuring).
