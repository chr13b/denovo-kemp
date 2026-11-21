# kemp-challenge

Team 01 at the **Perlin x D-BSSE Protein Design Hackathon**. We design Kemp eliminase enzymes and submit
up to 20 protein sequences; GPU work runs on the provided AWS cluster.

### 👉 New here? Read [SETUP.md](SETUP.md) — it takes you from zero to running in about 20 minutes.

| | |
|---|---|
| What we must deliver, and how it is scored | [wiki/challenge.md](wiki/challenge.md) |
| How to use the GPU cluster | [wiki/cluster.md](wiki/cluster.md) |
| How to submit designs | [wiki/submission.md](wiki/submission.md) |
| Where every file is | [INDEX.md](INDEX.md) |
| Where the team is right now | `make status` |
| How we branch and merge | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Instructions for AI assistants | [AGENTS.md](AGENTS.md) (any tool), [CLAUDE.md](CLAUDE.md) (Claude Code) |

## Quickstart

Needs [git](https://git-scm.com/downloads) and [uv](https://docs.astral.sh/uv/getting-started/installation/);
uv brings its own Python.

```bash
git clone https://github.com/chr13b/kemp-challenge.git
cd kemp-challenge
make setup   # environment from uv.lock + git hooks
make check   # all checks; must pass before you push
make status  # experiments and recent log entries
```

No `make` (plain Windows)? Every target is one or two `uv run …` lines in the [Makefile](Makefile).

## How the repo is organized

Three layers, after Andrej Karpathy's "LLM Wiki" pattern:

| Layer | Where | What |
|-------|-------|------|
| Sources | `raw/` | The organizers' documents. **Never edited.** |
| Knowledge | `wiki/` + `INDEX.md` + `log/` | Our distilled understanding, decisions and one page per experiment. |
| Code + artifacts | `src/`, `scripts/`, `configs/`, `envs/` → `runs/` → `results/` | Reproducible code. Every run records its config, commit and environment. |

The code is **nano-style** (think nanoGPT): flat, readable scripts, no premature abstraction, few
dependencies. Scripts are numbered by pipeline stage; copy `scripts/00_smoke.py` to start a new one.

## Day-to-day

```bash
git switch -c <handle>/<topic>                 # your own branch; never work on main
make sync                                      # merge main into your branch, often
uv run python tools/new.py exp <slug>          # an experiment page, before you run anything
uv run python tools/new.py log <type> "<t>"    # a log entry, after you did something
make check                                     # before every push
make submission                                # build and check results/designs.fasta
```
