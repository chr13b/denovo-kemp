# Setup — start here

Welcome! This is the one page you need on day one. No prior experience with this repo,
with Claude, or with clusters is assumed.

---

## ⚡ The fast path (about 3 minutes)

**One thing first, or nothing below works:** ask Chris to **invite your GitHub account** to
`chr13b/kemp-challenge` (it's private).

Then paste this into a terminal (macOS/Linux/WSL, or **Git Bash** on Windows — not PowerShell):

```bash
git clone https://github.com/chr13b/kemp-challenge.git
cd kemp-challenge
bash onboard.sh
```

`onboard.sh` asks for your handle, then does the rest: installs `uv` if you don't have it, builds the exact
Python environment from the lockfile, installs the commit hooks, writes your handle to `.env`, adds your row to
`wiki/team.md`, and runs the test suite. It prints a ✓ or ✗ for every step and is safe to run again.

Non-interactive, if you prefer:

```bash
bash onboard.sh --handle ana
```

When it says **Ready**, you're done — skip to [Part 3](#part-3--the-daily-rhythm). If any step shows ✗,
the rest of this page explains that step by hand, and the team chat is faster than guessing.

> Windows note: use **Git Bash** (ships with Git for Windows).

---

The rest of this page is the same thing done by hand, with explanations. Copy each block in order.

If anything does not work, **ask in the team chat instead of guessing** — and tell us which step broke,
so we can fix this page for the next person.

Words used below: **terminal** = the black window where you type commands (PowerShell on Windows,
Terminal on macOS/Linux). **repo** = this project folder. **Euler** = ETH's shared HPC cluster, where the GPU jobs run.

---

## Part 1 — The repo on your laptop (10 min)

### 1.1 Install the three tools

| Tool | What it does | Install |
|---|---|---|
| **git** | shares code with the team | [git-scm.com/downloads](https://git-scm.com/downloads) |
| **uv** | installs Python and our libraries, identically for everyone | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| **GitHub access** | you need to be a collaborator on `chr13b/kemp-challenge` | ask Chris to invite your GitHub account |

Check that they work (each should print a version):

```bash
git --version
uv --version
```

### 1.2 Get the repo

```bash
git clone https://github.com/chr13b/kemp-challenge.git
cd kemp-challenge
```

If git asks for a password: GitHub does **not** accept your account password here. Use a **personal access
token** as the password — create one at *Settings → Developer settings → Personal access tokens → Tokens
(classic)* with the `repo` scope. Step-by-step in [CONTRIBUTING.md](CONTRIBUTING.md) §6.
(`gh auth login` also works, but its browser flow can time out and needs a 2FA app.)

### 1.3 Set it up and check it works

```bash
make setup    # installs Python + libraries (~20 s) and turns on the safety checks
make check    # runs all checks; must end without errors
make status   # shows what the team has done so far
```

No `make` on Windows? Open the file `Makefile` — each entry is just one or two `uv run …` lines you can
paste directly. Or use **Git Bash** / **WSL**, where `make` usually exists.

**What `make setup` did:** it created a private Python environment inside the repo and installed git
hooks. The hooks run automatically when you commit and catch the usual accidents (leftover merge
markers, huge files, a private key, unformatted code, **and committing to `main` by mistake**).
If a commit is refused, read the message — it tells you what to fix. Never bypass it with `--no-verify`.

### 1.4 Claim your handle

Your **handle** is a short lowercase nickname (`chris`, `alex`, `sam`). It goes into your branch names
and file names so that two people can never create the same file. Add yourself to the table in
[wiki/team.md](wiki/team.md), then:

```bash
echo "KEMP_HANDLE=yourhandle" >> .env    # .env is private to you and never committed
```

### 1.5 Your first branch

**Never work directly on `main`.** Always work on your own branch (the hooks will stop you anyway):

```bash
git switch -c yourhandle/first-look     # create and switch to your branch
```

Pattern: `<handle>/<topic>`, e.g. `alex/scoring`. Your branch is yours, so you cannot break anyone else's work.

---

## Part 2 — Euler

Our GPU work runs on **Euler** (ETH Zurich's HPC cluster) through Slurm, with RFD4-Proteina. Your laptop is for
editing and checking; nothing heavy runs on it. The loop:

1. Edit here, run `make check`, commit and push your branch.
2. On Euler, pull that branch.
3. Submit the script through Slurm (`sbatch`) and follow it there.
4. Bring small results back into `results/` through git. `runs/` stays on Euler.

The details nobody has filled in yet (Euler access from the repo, the RFD4-Proteina environment, a job template)
are listed in [wiki/euler-rfd4.md](wiki/euler-rfd4.md). Don't run heavy computations on a login node; submit them
through Slurm.

---

## Part 3 — The daily rhythm

```bash
# starting work
git switch yourhandle/topic
git fetch origin && git merge origin/main      # or: make sync

# ... do your work ...

make check                                     # must pass
git add -A && git commit -m "feat: what I did"
git push -u origin HEAD                        # then open a Pull Request on GitHub
```

Two habits that keep the team fast:

- **Write it down.** After a few hours of work: `uv run python tools/new.py log experiment "what I tried"`,
  then fill in a few bullets. Anyone — human or AI — can then pick up where you left off.
- **`make sync` often.** Merging small changes often is painless; merging a day's work at once is not.

Before an experiment, create its page so nobody duplicates your work:

```bash
uv run python tools/new.py exp my-idea     # creates wiki/experiments/yourhandle-01_my-idea.md
```

---

## Part 4 — Using an AI assistant (optional, any tool)

The repo is written so that **any** AI coding assistant can work in it: Claude Code, Codex, Cursor,
Copilot, Gemini, Aider, or a chat window where you paste files.

- Using **Claude Code**? Just run `claude` in the repo. It reads `CLAUDE.md` automatically and knows
  the layout and rules. Useful commands: `/experiment`, `/submit`, `/sync`, `/lint`, `/ingest`.
- Using **anything else**? Point it at [AGENTS.md](AGENTS.md) first. That file is tool-neutral and tells
  any assistant how this repo works and what the rules are.
- Using a **plain chat window**? Paste `AGENTS.md` and `INDEX.md` into the conversation at the start.

You do not have to use AI at all. Everything here works by hand.

### Copy-paste starter prompt (works with any assistant)

Paste this as your **first** message in a new session, from inside the repo folder:

```text
You are helping me in the `kemp-challenge` repo for a 1-day protein-design hackathon
(Perlin x D-BSSE, team 01). Before anything else, read AGENTS.md and INDEX.md in the repo
root, then run `uv run python tools/status.py` to see where the team is.

Working rules you must follow (they are in AGENTS.md too):
- I work on my own branch `<handle>/<topic>`. Never commit to main.
- Write an experiment page with `uv run python tools/new.py exp <slug>` BEFORE running anything.
- Never report a number you did not read from a run's own output files. Say "not measured"
  instead of estimating.
- Update INDEX.md in the same commit as any file you add, and add a log entry with
  `uv run python tools/new.py log <type> "<title>"`.
- `make check` must pass before you push.
- Never print, copy or commit an SSH key or any token. Refer to them by path.

My handle is: <your handle>. Today I'm working on: <what you want to do>.
Start by telling me what the team has already done and what you suggest I pick up.
```

### Secrets

Refer to keys and tokens by path or environment variable, never by content, and never commit them. `.gitignore`
and the `detect-private-key` commit hook block the common cases.

---

## Cheat sheet

| I want to… | Command |
|---|---|
| see what the team did | `make status` |
| check my work before pushing | `make check` |
| update my branch from main | `make sync` |
| start an experiment | `uv run python tools/new.py exp <slug>` |
| write a log entry | `uv run python tools/new.py log <type> "<title>"` |
| run on Euler | push, pull on Euler, `sbatch` ([wiki/euler-rfd4.md](wiki/euler-rfd4.md)) |
| build the submission file | `make submission` |
| find anything in the repo | open [INDEX.md](INDEX.md) |
| know what we must deliver | read [wiki/challenge.md](wiki/challenge.md) |
| understand branching/merging | read [CONTRIBUTING.md](CONTRIBUTING.md) |
