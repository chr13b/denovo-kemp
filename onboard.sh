#!/usr/bin/env bash
# Set up this repo on a new laptop, from nothing to a verified cluster connection.
#
#   bash onboard.sh                          # asks for what it needs
#   bash onboard.sh --handle ana --key ~/Downloads/pdh-team-01.pem
#   bash onboard.sh --skip-cluster           # repo only, set the key up later
#
# Safe to run twice: every step checks before it changes anything.
# It never writes the cluster key into the repo, and never prints the key.
set -u -o pipefail

REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
cd "$REPO"

HANDLE=""; KEYSRC=""; SKIP_CLUSTER=0
while [ $# -gt 0 ]; do
    case "$1" in
        --handle) HANDLE="${2:-}"; shift 2 ;;
        --key)    KEYSRC="${2:-}"; shift 2 ;;
        --skip-cluster) SKIP_CLUSTER=1; shift ;;
        -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
        *) echo "unknown option: $1 (try --help)"; exit 2 ;;
    esac
done

# The cluster address is not published in this repository: export KEMP_CLUSTER_IP from your connect file.
HOST_IP="${KEMP_CLUSTER_IP:-}"
HOST_USER="ec2-user"
HOST_ALIAS="pdh-team"
# From the team connection file the organizers sent (not published). Verified against the live host 2026-11-21.
EXPECTED_FP="SHA256:3HYAek1L/uZ+NT9YtwYhFBd9FUuz0vW06FWAurPTQWk"

ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }

FAILED=0
note_fail() { FAILED=1; bad "$*"; }

# ---------------------------------------------------------------- 1. prerequisites
step "1/6  Prerequisites"

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
step "2/6  Python environment and git hooks"

uv sync --locked      || { note_fail "uv sync failed"; }
uv run --frozen pre-commit install >/dev/null 2>&1 \
    && ok "commit hooks installed (they block commits straight to main, and private keys)" \
    || note_fail "could not install the commit hooks"

# Local merge QoL: remember conflict resolutions, show the common ancestor in conflicts.
git config rerere.enabled true
git config merge.conflictstyle diff3
ok "merge settings configured (rerere + diff3)"

# ---------------------------------------------------------------- 3. handle
step "3/6  Your handle"

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

# ---------------------------------------------------------------- 4. cluster key
step "4/6  Cluster key"

KEYDEST="$HOME/.ssh/pdh-team-01.pem"
if [ -z "$HOST_IP" ] && [ "$SKIP_CLUSTER" != "1" ]; then
    warn "KEMP_CLUSTER_IP is not set, so the cluster step is skipped"
    SKIP_CLUSTER=1
fi
if [ "$SKIP_CLUSTER" = "1" ]; then
    warn "skipped (--skip-cluster). Re-run without it once you have the key."
elif [ -f "$KEYDEST" ]; then
    chmod 600 "$KEYDEST" 2>/dev/null
    ok "key already installed at ~/.ssh/pdh-team-01.pem"
else
    if [ -z "$KEYSRC" ]; then
        printf '  Get pdh-team-01.pem from Chris directly (DM/USB). NEVER from a public link,\n'
        printf '  and never copy it into this repo.\n'
        printf '  Path to the key file (blank to skip): '
        read -r KEYSRC </dev/tty || true
    fi
    KEYSRC=$(printf '%s' "$KEYSRC" | sed "s|^~|$HOME|; s|^'||; s|'$||")
    if [ -z "$KEYSRC" ]; then
        warn "no key given - skipping cluster setup. Re-run onboard.sh later."
        SKIP_CLUSTER=1
    elif [ ! -f "$KEYSRC" ]; then
        note_fail "no file at: $KEYSRC"
        SKIP_CLUSTER=1
    else
        case "$(cd "$(dirname "$KEYSRC")" && pwd -P)" in
            "$REPO"|"$REPO"/*) bad "That path is inside the repo. Move the key out of the repo first."; exit 1 ;;
        esac
        mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
        cp "$KEYSRC" "$KEYDEST" && chmod 600 "$KEYDEST" \
            && ok "key installed at ~/.ssh/pdh-team-01.pem (mode 600)" \
            || note_fail "could not copy the key"
    fi
fi

# ssh config entry
if [ "$SKIP_CLUSTER" != "1" ]; then
    touch "$HOME/.ssh/config" && chmod 600 "$HOME/.ssh/config"
    if grep -qE "^[[:space:]]*Host[[:space:]]+$HOST_ALIAS([[:space:]]|$)" "$HOME/.ssh/config"; then
        ok "~/.ssh/config already has a '$HOST_ALIAS' entry"
    else
        cat >> "$HOME/.ssh/config" <<EOF

# denovo-kemp cluster, team 01
Host $HOST_ALIAS
    HostName $HOST_IP
    User $HOST_USER
    IdentityFile $KEYDEST
    IdentitiesOnly yes
    ServerAliveInterval 60
EOF
        ok "added '$HOST_ALIAS' to ~/.ssh/config"
    fi
fi

# ---------------------------------------------------------------- 5. verify the host, then connect
step "5/6  Cluster connection"

if [ "$SKIP_CLUSTER" = "1" ]; then
    warn "skipped"
elif ssh-keygen -F "$HOST_IP" >/dev/null 2>&1; then
    ok "host key already trusted"
else
    # Check the fingerprint ourselves instead of teaching people to type "yes" at a prompt.
    SCAN=$(mktemp)
    if ssh-keyscan -t ed25519 "$HOST_IP" 2>/dev/null > "$SCAN" && [ -s "$SCAN" ]; then
        GOT=$(ssh-keygen -lf "$SCAN" 2>/dev/null | awk '{print $2}' | head -1)
        if [ "$GOT" = "$EXPECTED_FP" ]; then
            cat "$SCAN" >> "$HOME/.ssh/known_hosts"
            ok "host fingerprint matches the one the organizers published"
        else
            bad "FINGERPRINT MISMATCH - do not connect, tell an organiser."
            bad "  expected $EXPECTED_FP"
            bad "  got      ${GOT:-<none>}"
            FAILED=1; SKIP_CLUSTER=1
        fi
    else
        warn "could not reach the host to check its fingerprint (VPN/firewall?)"
        SKIP_CLUSTER=1
    fi
    rm -f "$SCAN"
fi

if [ "$SKIP_CLUSTER" != "1" ]; then
    if OUT=$(ssh -o ConnectTimeout=20 -o BatchMode=yes "$HOST_ALIAS" 'echo OK; squeue -h | wc -l' 2>&1); then
        ok "connected: ssh $HOST_ALIAS works ($(printf '%s' "$OUT" | tail -1) job(s) in the queue)"
    else
        note_fail "ssh $HOST_ALIAS failed: $(printf '%s' "$OUT" | tail -1)"
    fi
fi

# ---------------------------------------------------------------- 6. prove it all works
step "6/6  Checks"

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
