# Setup — start here (about 20 minutes)

Welcome! This is the one page you need on day one. No prior experience with this repo,
with Claude, or with clusters is assumed. Copy each block into your terminal, in order.

If anything does not work, **ask in the team chat instead of guessing** — and tell us which step broke,
so we can fix this page for the next person.

Words used below: **terminal** = the black window where you type commands (PowerShell on Windows,
Terminal on macOS/Linux). **repo** = this project folder. **cluster** = the shared GPU computer.

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

If git asks for a password: GitHub needs a **personal access token**, not your account password.
Easiest fix is [GitHub CLI](https://cli.github.com/): install it, run `gh auth login`, then clone again.

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

## Part 2 — The cluster (10 min)

Our GPUs live on an AWS cluster. Your laptop only sends commands there; all computation runs on the cluster.
Reference: [wiki/cluster.md](wiki/cluster.md).

### 2.1 Get the team key

Chris has the file `pdh-team-01.pem`. Get it **directly from a teammate** (chat DM, USB stick, AirDrop).

> ⚠️ **Never put this key in the repo, in a public chat, or in a cloud folder.** It is the password to our
> cluster and is shared by the whole team. The repo actively blocks `*.pem` files, but do not rely on that.

### 2.2 Install the key and the shortcut

**macOS / Linux / WSL / Git Bash:**

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cp /path/to/pdh-team-01.pem ~/.ssh/ && chmod 600 ~/.ssh/pdh-team-01.pem
cat >> ~/.ssh/config <<'EOF'

Host pdh-team
    HostName 35.181.61.66
    User ec2-user
    IdentityFile ~/.ssh/pdh-team-01.pem
    IdentitiesOnly yes
    ServerAliveInterval 60
EOF
```

**Windows PowerShell:**

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
Copy-Item .\pdh-team-01.pem "$env:USERPROFILE\.ssh\"
icacls "$env:USERPROFILE\.ssh\pdh-team-01.pem" /inheritance:r /grant:r "$env:USERNAME:R"
Add-Content "$env:USERPROFILE\.ssh\config" @"

Host pdh-team
    HostName 35.181.61.66
    User ec2-user
    IdentityFile $env:USERPROFILE\.ssh\pdh-team-01.pem
    IdentitiesOnly yes
"@
```

(`chmod 600` / `icacls` make the key readable only by you. SSH refuses to use a key that others can read.)

### 2.3 Connect

```bash
ssh pdh-team
```

The first time, SSH shows a fingerprint. It **must** be:

```
SHA256:3HYAek1L/uZ+NT9YtwYhFBd9FUuz0vW06FWAurPTQWk
```

Type `yes` only if it matches exactly. If it differs, stop and tell an organiser.
When you see a prompt like `[ec2-user@ip-172-31-26-233 ~]$`, you are on the cluster.
`exit` brings you back to your laptop.

- *Permission denied* → the key is in the wrong place or its permissions are too open (redo 2.2).
- *Connection timed out* → ask an organiser; the address may have changed.

### 2.4 Rules on the cluster (important)

1. **Never run heavy computations directly after connecting.** The machine you land on (the "head node")
   has no GPU. Always submit jobs with the provided `run.sh`, which queues them onto a GPU.
2. **Never use the `l4big` queue** — jobs sent there wait forever.
3. **Leave `/mnt/work/kemp_example` alone.** It is our reference. Make your own project folder with your handle in the name.
4. `/mnt/work` is **not backed up**. Copy anything that matters to your laptop and into this repo.

The exact commands are in [wiki/cluster.md](wiki/cluster.md) — the Claude command `/cluster` walks you through them too.

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
  the layout and rules. Useful commands: `/cluster`, `/experiment`, `/submit`, `/sync`, `/lint`, `/ingest`.
- Using **anything else**? Point it at [AGENTS.md](AGENTS.md) first. That file is tool-neutral and tells
  any assistant how this repo works and what the rules are.
- Using a **plain chat window**? Paste `AGENTS.md` and `INDEX.md` into the conversation at the start.

You do not have to use AI at all. Everything here works by hand.

---

## Cheat sheet

| I want to… | Command |
|---|---|
| see what the team did | `make status` |
| check my work before pushing | `make check` |
| update my branch from main | `make sync` |
| start an experiment | `uv run python tools/new.py exp <slug>` |
| write a log entry | `uv run python tools/new.py log <type> "<title>"` |
| connect to the cluster | `ssh pdh-team` |
| build the submission file | `make submission` |
| find anything in the repo | open [INDEX.md](INDEX.md) |
| know what we must deliver | read [wiki/challenge.md](wiki/challenge.md) |
| understand branching/merging | read [CONTRIBUTING.md](CONTRIBUTING.md) |
