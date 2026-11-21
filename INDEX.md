# INDEX

The map of this repo, one line per file or directory: `path — what it is`.
**If you add, move or delete a file, update this file in the same commit.** `make index` enforces it:
it catches dead links and files that aren't listed.
Files in `wiki/ raw/ src/ scripts/ tools/ configs/ results/ .claude/skills/` each need their own line.
Elsewhere, a line for the directory is enough.

## Meta
- [CLAUDE.md](CLAUDE.md) — schema: rules, conventions and workflows for Claude and humans
- [AGENTS.md](AGENTS.md) — pointer to CLAUDE.md for other coding agents (Codex, Cursor, …)
- [README.md](README.md) — human quickstart and team workflow
- [LOG.md](LOG.md) — append-only chronological log; recent entries: `grep "^## \[" LOG.md | tail`
- [pyproject.toml](pyproject.toml) — package `kemp`, dependencies (uv), ruff and pytest config
- [.python-version](.python-version) — Python version uv installs and uses
- `uv.lock` — exact pinned dependency versions; created by the first `uv sync`, then committed
- [Makefile](Makefile) — `setup smoke test lint fmt index check`
- [.env.example](.env.example) — template for local paths and secrets; copy to `.env` (gitignored)
- [.gitignore](.gitignore) · [.gitattributes](.gitattributes) — ignore rules; LF line endings everywhere
- [.github/](.github/) — CI: runs the index lint, ruff and pytest on every push to main and every PR

## Claude skills (`/name` in Claude Code)
- [.claude/skills/ingest/SKILL.md](.claude/skills/ingest/SKILL.md) — `/ingest`: turn a raw source into wiki knowledge
- [.claude/skills/experiment/SKILL.md](.claude/skills/experiment/SKILL.md) — `/experiment`: question → run → verdict, reproducibly
- [.claude/skills/lint/SKILL.md](.claude/skills/lint/SKILL.md) — `/lint`: health-check INDEX, LOG and wiki, then fix drift

## Knowledge: wiki/ (maintained mostly by Claude)
- [wiki/challenge.md](wiki/challenge.md) — the task, rules, scoring, timeline and open questions. **Start here.**
- [wiki/experiments.md](wiki/experiments.md) — experiment registry: question → script/config → run → verdict
- [wiki/decisions.md](wiki/decisions.md) — decision records: what we chose, why, and the alternatives
- [wiki/team.md](wiki/team.md) — who owns what, plus working agreements
- [wiki/glossary.md](wiki/glossary.md) — domain and project terms

## Sources: raw/ (immutable, added by humans)
- _(empty: add the organizers' brief first, then run `/ingest`)_

## Code
- [src/kemp/paths.py](src/kemp/paths.py) — every project path, defined once (data/runs can be overridden by env var)
- [src/kemp/config.py](src/kemp/config.py) — `parse(Config)`: dataclass config with JSON/TOML file and `--key=value` overrides
- [src/kemp/run.py](src/kemp/run.py) — `start_run()`: run directory plus provenance (config, git commit, seed, metrics)
- [scripts/00_smoke.py](scripts/00_smoke.py) — smoke test for env and run bookkeeping; **template for new scripts**
- [tools/check_index.py](tools/check_index.py) — lint: dead markdown links and files missing from INDEX.md
- [configs/](configs/) — reusable run configs, named `<experiment-id>.json` (none yet)
- [tests/](tests/) — pytest suite (config parsing, run bookkeeping, index lint)

## Artifacts
- [data/](data/) — bulk inputs, gitignored; how to obtain them is documented in `wiki/challenge.md`
- [runs/](runs/) — one directory per execution, gitignored; registry in `wiki/experiments.md`
- [results/](results/) — curated tracked outputs (figures, tables, submission); each entry names its run (none yet)
- [notebooks/](notebooks/) — exploration only; nothing imports from here
