# Decisions

Record a decision here if it would be expensive to reverse, or if someone might later ask "why?".
Format: `## D-NNN Title (YYYY-MM-DD)` with Decision / Why / Alternatives. Newest entries go at the bottom.

## D-001 Repo layout: LLM wiki + nano-style code (2026-11-21)
- **Decision:** Three layers:
  - `raw/`: immutable sources
  - `wiki/` + `INDEX.md` + `LOG.md`: maintained knowledge
  - code (`src/`, `scripts/`, `configs/`): outputs go to `runs/` (disposable, gitignored) and `results/` (curated, tracked)
- **Why:** The team is new, and the AI pair programmer starts every session cold.
  - A single map (`INDEX.md`, auto-loaded through `CLAUDE.md`) lets anyone, human or Claude, find their way around in a minute.
  - An append-only log gives the timeline.
  - Run directories that record the config and git commit make every number traceable.
- **Inspiration:**
  - Karpathy's "LLM Wiki" gist: raw sources / wiki / schema file, `index.md` + `log.md`, and the ingest / query / lint operations
  - nanoGPT and nanochat: flat, readable code with minimal abstraction
  - cookiecutter-data-science: data kept separate from results
- **Alternatives:**
  - The full cookiecutter-data-science layout (too many empty directories for a hackathon)
  - Hydra + W&B (setup costs more than it saves at hackathon scale; revisit if we run large sweeps)

## D-002 Python ≥ 3.10, managed by uv (2026-11-21)
- **Decision:** Use uv for the environment, and commit `uv.lock` and `.python-version`.
- **Why:** It gives a reproducible environment with one command on every teammate's machine and in CI.
- **Alternatives:** conda (slower and harder to lock). Tools that need conda or a container get a wrapper script
  whose docstring records the exact environment.
