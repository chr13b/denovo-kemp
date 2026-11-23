# Setup — start here

Welcome! This is the one page you need on day one. No prior experience with this repo,
with Claude, or with clusters is assumed.

> **Note (2026-11-23).** Written for the team during the first two days of the project (2026-11-21 and 2026-11-22). The invitation, key
> and cluster steps below applied while the organizers' cluster was provided. The laptop side (`make setup`, `make check`)
> works from a plain clone.

---

## ⚡ The fast path (about 3 minutes)

**Two things first, or nothing below works:**
1. Ask the repository owner to **invite your GitHub account** to `chr13b/denovo-kemp` (it was private during the project; once it is public you can simply fork it).
2. Ask Chris for **`pdh-team-01.pem`** — directly, person to person. Save it to your Downloads folder.
   Never from a public link, never into this repo.

Then paste this into a terminal (macOS/Linux/WSL, or **Git Bash** on Windows — not PowerShell):

```bash
git clone https://github.com/chr13b/denovo-kemp.git
cd denovo-kemp
bash onboard.sh
```

`onboard.sh` asks for your handle and the path to the key, then does the rest: installs `uv` if you don't
have it, builds the exact Python environment from the lockfile, installs the commit hooks, writes your
handle to `.env`, adds your row to `wiki/team.md`, installs the key with the right permissions, writes your
SSH config, **checks the cluster's fingerprint against the one the organizers published**, connects, and
runs the test suite. It prints a ✓ or ✗ for every step and is safe to run again.

Non-interactive, if you prefer:

```bash
bash onboard.sh --handle ana --key ~/Downloads/pdh-team-01.pem
bash onboard.sh --skip-cluster      # repo only; do the key later
```

When it says **Ready**, you're done — skip to [Part 3](#part-3--the-daily-rhythm). If any step shows ✗,
the rest of this page explains that step by hand, and the team chat is faster than guessing.

> Windows note: use **Git Bash** (ships with Git for Windows). The manual PowerShell commands are in
> Part 2 if you'd rather do it step by step.

---

The rest of this page is the same thing done by hand, with explanations. Copy each block in order.

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
| **GitHub access** | you need to be a collaborator on `chr13b/denovo-kemp` | ask the repository owner to invite your GitHub account |

Check that they work (each should print a version):

```bash
git --version
uv --version
```

### 1.2 Get the repo

```bash
git clone https://github.com/chr13b/denovo-kemp.git
cd denovo-kemp
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
    HostName <CLUSTER_IP>
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
    HostName <CLUSTER_IP>
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

### Copy-paste starter prompt (works with any assistant)

Paste this as your **first** message in a new session, from inside the repo folder:

```text
You are helping me in the `denovo-kemp` repo for a 1-day protein-design project
(team 01). Before anything else, read AGENTS.md and INDEX.md in the repo
root, then run `uv run python tools/status.py` to see where the team is.

Working rules you must follow (they are in AGENTS.md too):
- I work on my own branch `<handle>/<topic>`. Never commit to main.
- Write an experiment page with `uv run python tools/new.py exp <slug>` BEFORE running anything.
- Never report a number you did not read from a run's own output files. Say "not measured"
  instead of estimating.
- Update INDEX.md in the same commit as any file you add, and add a log entry with
  `uv run python tools/new.py log <type> "<title>"`.
- `make check` must pass before you push.
- Never print, copy or commit the cluster key (`*.pem`) or any token. Refer to them by path.

My handle is: <your handle>. Today I'm working on: <what you want to do>.
Start by telling me what the team has already done and what you suggest I pick up.
```

### Keeping an AI session from stalling on the cluster key

Assistants get cautious — sometimes to the point of stopping mid-task — when a conversation starts
handling private keys, because out of context that looks like credential theft. Nothing about our setup is
off-limits; it's an organizer-issued key for our own team's cluster. The friction comes from *how* the key
enters the conversation, and it's avoidable:

- **Refer to the key by path, never by content.** `~/.ssh/pdh-team-01.pem` is fine. Pasting the key text
  into chat is not — it also permanently writes your team's private key into a session transcript.
- **Let scripts touch the file; don't ask the assistant to.** `bash onboard.sh --key <path>` reads the file
  itself. `ssh pdh-team` uses it without anyone reading it.
- **Say what the task is.** "Install the organizers' cluster key for our team so `ssh pdh-team` works" reads
  very differently from "put this key somewhere".
- **Don't ask for the key to be committed, emailed or uploaded.** That is the one thing we genuinely never
  do — it would put the whole team's access in git history forever. `.gitignore` plus the
  `detect-private-key` commit hook already block it.

Same rules for GitHub tokens and AWS credentials: by path or by environment variable, never pasted.

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
