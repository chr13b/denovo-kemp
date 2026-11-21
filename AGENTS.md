# AGENTS.md — brief for any AI assistant

Tool-neutral instructions for this repo. Works for Claude Code, Codex, Cursor, Copilot, Gemini, Aider,
or a plain chat window. **Read this file and `INDEX.md` before doing anything.**

Claude Code users: `CLAUDE.md` is the same content plus Claude-specific bits, and loads automatically.

## What this project is

The **Perlin x D-BSSE Protein Design Hackathon**, team 01. We design Kemp eliminase enzymes and submit
up to 20 protein sequences as one `designs.fasta`. GPU work runs on ETH's Euler cluster through Slurm: we edit here,
push, pull on Euler and submit with `sbatch` (`wiki/euler-rfd4.md`).
The task, scoring and hard rules are in `wiki/challenge.md` — **read it before any scientific decision**.

## How to orient yourself (in this order)

1. `INDEX.md` — one line per file. The map.
2. `make status` — the experiment table and recent log entries.
3. `wiki/challenge.md` — what we must deliver and how it is scored.
4. `git status -sb` — which branch you are on.

## The three layers

| Layer | Where | Rule |
|---|---|---|
| Sources | `raw/` | **Immutable.** Organizer documents. Read them; never edit or delete them. |
| Knowledge | `wiki/`, `INDEX.md`, `log/` | Distilled and current. Every claim cites a `raw/` file or a run. |
| Code + artifacts | `src/ scripts/ configs/ tests/ tools/` → `runs/` → `results/` | Reproducible from git + config. |

## Non-negotiable rules

1. **Never invent numbers.** Only report values you read from a run's `summary.json` / `metrics.jsonl`,
   or from a `raw/` source. If you have not measured it, say so.
2. **Never edit `raw/`**, and never rewrite another person's log entry or experiment page. Add your own instead.
3. **Update `INDEX.md`** in the same commit whenever you add, move or delete a file.
4. **Write a log entry** for any real piece of work: `python tools/new.py log <type> "<title>"`.
5. **Run `make check`** before claiming you are done. It must pass.
6. **Per-person names, never global counters.** Experiments are `<handle>-NN` (`tools/new.py exp <slug>`),
   branches are `<handle>/<topic>`. Everyone works in parallel; colliding names break merges.
7. **Never hand-merge `uv.lock`.** Resolve `pyproject.toml`, then run `uv lock`.
8. **Secrets: refer to them by path, never by content.** SSH keys, `.env`, GitHub tokens and any cluster
   credentials never enter git and never get printed into the conversation. Name a key by its path and let
   scripts read the file rather than reading it yourself. This is both a security rule and a practical one: a
   transcript full of key material is a liability, and it is the fastest way to make an assistant stall
   mid-task on what looks out of context like credential theft. State the task plainly and keep the secret
   out of the text.
9. **Euler:** no heavy compute on login nodes; submit through Slurm. See `wiki/euler-rfd4.md`.
10. **Ask rather than guess** when the challenge rules are ambiguous. Add the question to
    `wiki/challenge.md` under "Open questions".

## Playbooks

Step-by-step procedures live in `.claude/skills/<name>/SKILL.md`. They are plain Markdown — **any**
assistant can read and follow them. Ignore the YAML header if your tool does not use it.

| Task | File |
|---|---|
| Plan, run and record an experiment | `.claude/skills/experiment/SKILL.md` |
| Build, check and upload the submission | `.claude/skills/submit/SKILL.md` |
| Turn a new document into wiki knowledge | `.claude/skills/ingest/SKILL.md` |
| Update a branch from main, resolve conflicts | `.claude/skills/sync/SKILL.md` |
| Tidy up index, log and wiki | `.claude/skills/lint/SKILL.md` |

## Code style

Flat and readable, in the spirit of nanoGPT. One file, one idea; a script reads top to bottom.
No framework, base class or registry until the third time it is needed. Few dependencies (`uv add`).
Scripts are `scripts/NN_verb_noun.py` by stage (`0x` setup/data, `1x` generate, `2x` score, `3x` analyze,
`9x` submit), each with a usage docstring, a `Config` dataclass via `kemp.config.parse`, and
`kemp.run.start_run`. Copy `scripts/00_smoke.py`. Paths come from `kemp.paths` only.
Shared helpers move into `src/kemp/` only once **two** scripts need them.

## Commands

```
make setup       install the environment and git hooks
make status      experiment table + recent log entries
make check       all checks (formatting, lint, tests, index) — must pass before pushing
make sync        merge origin/main into this branch
make submission  build results/designs.fasta from results/designs.jsonl and validate it offline
make smoke       prove the setup works end to end
make reproduce   the full pipeline, fresh clone -> results
```

Each `make` target is one or two `uv run …` lines in the `Makefile`; run them directly if `make` is missing.

## Using a different assistant

Nothing here is Claude-specific except `CLAUDE.md` and the `.claude/` folder. If your tool has its own
rules file, point it at this file rather than duplicating content — `GEMINI.md`,
`.github/copilot-instructions.md` and `.cursor/rules/kemp-challenge.mdc` already do exactly that.
Bring your own skills, prompts and agents; keep them in your own tool's config, and if a prompt proves
genuinely useful to everyone, propose adding it as a playbook so the whole team benefits.
