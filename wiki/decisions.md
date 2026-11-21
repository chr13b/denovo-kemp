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
