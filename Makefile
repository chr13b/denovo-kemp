# Each target is a thin wrapper around one uv command. No make? Run the indented line by hand.
.PHONY: setup smoke test lint fmt index check

setup:  # create .venv with pinned deps (uv.lock) and the right Python (.python-version)
	uv sync

smoke:  # end-to-end check of env + run bookkeeping -> runs/<timestamp>_smoke/
	uv run python scripts/00_smoke.py

test:
	uv run pytest

lint:
	uv run ruff check .

fmt:  # auto-format and auto-fix
	uv run ruff format . && uv run ruff check --fix .

index:  # INDEX.md covers every file; no dead markdown links
	uv run python tools/check_index.py

check: index lint test  # run before every push; CI runs the same
