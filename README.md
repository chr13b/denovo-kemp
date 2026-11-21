# kemp-challenge

Our hackathon repo.

- **What we're solving:** [wiki/challenge.md](wiki/challenge.md)
- **Where everything is:** [INDEX.md](INDEX.md), the map of every file
- **What happened so far:** [LOG.md](LOG.md)

## Quickstart

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/). uv installs the right Python itself.

```bash
git clone git@github.com:chr13b/kemp-challenge.git
cd kemp-challenge
make setup   # = uv sync         → .venv with pinned deps
make smoke   # creates runs/<timestamp>_smoke/, which proves the setup works
make check   # index lint + ruff + pytest; must pass before you push
```

No `make` (plain Windows)? Every Makefile target is a single `uv run …` line, so copy it from the [Makefile](Makefile).

## How the repo is organized

There are three layers, after Andrej Karpathy's "LLM Wiki" pattern:

| Layer | Where | What |
|-------|-------|------|
| Sources | `raw/` | Challenge brief, papers, organizer notes. **Never edited.** |
| Knowledge | `wiki/` + `INDEX.md` + `LOG.md` | Distilled understanding, decisions and the experiment registry, kept current (mostly by Claude). |
| Code + artifacts | `src/`, `scripts/`, `configs/` → `runs/` → `results/` | Reproducible code. Every run records its config and git commit. |

The code is **nano-style** (think nanoGPT): flat, readable scripts, no premature abstraction, few dependencies.
Scripts are numbered by pipeline stage (`scripts/NN_verb_noun.py`). Copy `scripts/00_smoke.py` to start a new one.
The full rules are in [CLAUDE.md](CLAUDE.md).

## Team workflow

1. `git pull`, then `git switch -c <name>/<topic>`
2. Do the work. Experiments go in `wiki/experiments.md` *before* you run them.
3. Add new files to `INDEX.md` and a line about what you did to `LOG.md`, or ask Claude to run `/lint`.
4. Run `make check`, push, and open a PR. Merge when CI is green.

## Working with Claude Code

`CLAUDE.md` loads automatically and imports `INDEX.md`, so Claude starts every session with the full map.
Project skills:

- `/ingest`: turn a source into wiki knowledge
- `/experiment`: run an experiment reproducibly and record the verdict
- `/lint`: fix drift between the repo, the index and the wiki
