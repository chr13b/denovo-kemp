#!/usr/bin/env bash
# Set up this repo on a new laptop, from nothing to a working checkout.
#
#   bash onboard.sh                          # asks for what it needs
#   bash onboard.sh --handle ana
#
# Safe to run twice: every step checks before it changes anything.
set -u -o pipefail

REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
cd "$REPO"

HANDLE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --handle) HANDLE="${2:-}"; shift 2 ;;
        -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
        *) echo "unknown option: $1 (try --help)"; exit 2 ;;
    esac
done

ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }

FAILED=0
note_fail() { FAILED=1; bad "$*"; }

# ---------------------------------------------------------------- 1. prerequisites
step "1/4  Prerequisites"

command -v git >/dev/null || { bad "git is not installed. Install it first, then re-run."; exit 1; }
ok "git $(git --version | awk '{print $3}')"

if ! command -v uv >/dev/null 2>&1; then
    [ -x "$HOME/.local/bin/uv" ] && export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v uv >/dev/null 2>&1; then
    warn "uv not found - installing it (this is the only thing we install globally)"
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        export PATH="$HOME/.local/bin:$PATH"
    else
        bad "Could not install uv. Install it manually: https://docs.astral.sh/uv/"
        exit 1
    fi
fi
ok "uv $(uv --version 2>/dev/null | awk '{print $2}')"
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) warn "add this to your ~/.bashrc or ~/.zshrc:  export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

# ---------------------------------------------------------------- 2. python env + hooks
step "2/4  Python environment and git hooks"

uv sync --locked      || { note_fail "uv sync failed"; }
uv run --frozen pre-commit install >/dev/null 2>&1 \
    && ok "commit hooks installed (they block commits straight to main, and private keys)" \
    || note_fail "could not install the commit hooks"

# Local merge QoL: remember conflict resolutions, show the common ancestor in conflicts.
git config rerere.enabled true
git config merge.conflictstyle diff3
ok "merge settings configured (rerere + diff3)"

# ---------------------------------------------------------------- 3. handle
step "3/4  Your handle"

if [ -z "$HANDLE" ] && [ -f .env ]; then
    HANDLE=$(grep -E '^KEMP_HANDLE=' .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
    [ -n "$HANDLE" ] && ok "found KEMP_HANDLE=$HANDLE in .env"
fi
if [ -z "$HANDLE" ]; then
    DEFAULT=$(git config user.name 2>/dev/null | awk '{print tolower($1)}' | tr -cd 'a-z0-9')
    printf '  Short lowercase nickname for branches/experiments (e.g. ana, raj, chris)\n'
    printf '  Handle [%s]: ' "${DEFAULT:-yourname}"
    read -r HANDLE </dev/tty || true
    HANDLE=${HANDLE:-$DEFAULT}
fi
HANDLE=$(printf '%s' "$HANDLE" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9')
if [ -z "$HANDLE" ]; then
    note_fail "no handle set; re-run with --handle <name>"
else
    [ -f .env ] || cp .env.example .env
    if grep -qE '^KEMP_HANDLE=' .env; then
        # portable in-place edit (BSD and GNU sed differ on -i)
        TMP=$(mktemp); sed "s|^KEMP_HANDLE=.*|KEMP_HANDLE=$HANDLE|" .env > "$TMP" && mv "$TMP" .env
    else
        printf 'KEMP_HANDLE=%s\n' "$HANDLE" >> .env
    fi
    ok "handle '$HANDLE' saved to .env (gitignored; your tools read it from there)"

    # Add your row to wiki/team.md, before the TODO placeholder. Never touches other rows.
    if grep -qE "^\| *$HANDLE *\|" wiki/team.md; then
        ok "wiki/team.md already has a row for '$HANDLE'"
    else
        GH=$(git config user.email 2>/dev/null | cut -d@ -f1)
        ROW="| $HANDLE | ${GH:-} | TODO: your background | TODO | \`$HANDLE\` |"
        TMP=$(mktemp)
        awk -v row="$ROW" '!done && /^\| *TODO *\|/ { print row; done=1 } { print }' wiki/team.md > "$TMP"
        if grep -qF "$ROW" "$TMP"; then mv "$TMP" wiki/team.md; ok "added your row to wiki/team.md"
        else rm -f "$TMP"; warn "could not place your row automatically - add it by hand"; fi
    fi
fi

# ---------------------------------------------------------------- 4. prove it all works
step "4/4  Checks"

if uv run --frozen pytest -q 2>&1 | tail -1; then ok "test suite passed"; else note_fail "tests failed"; fi
uv run --frozen python tools/check_index.py >/dev/null 2>&1 \
    && ok "INDEX.md is consistent" || warn "INDEX lint reported something - run: uv run python tools/check_index.py"

# ---------------------------------------------------------------- done
printf '\n\033[1m%s\033[0m\n' "----------------------------------------------------------------"
if [ "$FAILED" = "0" ]; then
    printf '\033[32mReady.\033[0m  Handle: %s\n' "${HANDLE:-?}"
else
    printf '\033[33mFinished with problems (see ✗ above).\033[0m  Ask in the team chat.\n'
fi
cat <<EOF

What to do next
  1. uv run python tools/status.py        what the team has done so far
  2. Read wiki/challenge.md               the rules and how designs are scored
  3. Start your own branch (one branch per person is simplest):
         git checkout -b ${HANDLE:-<handle>}
     Prefer a branch per topic instead? Use ${HANDLE:-<handle>}/<topic> - but git cannot have
     both styles for one name, so pick one. See CONTRIBUTING.md section 1.
  4. Before you run anything:
         uv run python tools/new.py exp <slug>
  5. Working with an AI assistant? Point it at AGENTS.md first - see SETUP.md part 4.

Everyday commands (make is optional; each target is just uv run ... in the Makefile)
  make status | make check | make sync | make submission
EOF
