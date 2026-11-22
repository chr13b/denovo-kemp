#!/usr/bin/env python3
"""Unattended GPU pipeline: replicate -> experiment arms -> main sweep -> replicate -> rank.

Runs ON THE CLUSTER'S HEAD NODE under nohup and does only light work: it polls Slurm, parses TSV files and
submits jobs. All GPU work goes through sbatch. Standard library only, Python 3.8 compatible.

    nohup python3 autopilot.py > autopilot.out 2>&1 &         # real run, resumable
    python3 autopilot.py --dry-run                              # logs what it would submit, submits nothing

Stages (state is saved after each, so a restart resumes where it stopped):
  repl1  replicate the best existing designs (ranked by geometry D) over 5 Boltz seeds
  arms   five 72-sequence arms on seed 4's backbone: baseline, aromatic pocket, polar-down pocket,
         close variants, checkpoint 005
  main   216 more sequences using the winning arm's settings (the baseline if none wins)
  repl2  replicate the best new designs
  final  aggregate every replicated design, apply the pre-registered selection rule, write a candidate file

It never uploads anything and never touches another user's jobs. Upload and the novelty gate stay with a human
or the supervising session. It stops and says so if a job fails twice, and it will not start a stage that
cannot finish before STOP_BY.

Geometry D is the continuous deviation from the crystal ranges (our proxy; the scorer's function is
unpublished).
"""

import argparse
import csv
import glob
import json
import math
import os
import subprocess
import time
import traceback
from datetime import datetime, timedelta, timezone

WORK = "/mnt/work/projects/chris_autopilot"
BRIDGE = "/mnt/work/projects/chris_seedsweep_s4/results/kemp-4/bridge"
REF_ENV = "/mnt/ref/hackathon/scripts/reference-paths.sh"
CRYSTALS = "/mnt/work/tools/kemp_pdb"
VALIDATOR = "/mnt/work/projects/chris_oversample_a/validator/validate-submission.py"
CKPT_005 = "/mnt/ref/data_weights/ligandmpnn/ligandmpnn_v_32_005_25.pt"
P = "/mnt/work/projects"
EXISTING = {  # label -> results dir holding queries.json and boltz output, for the designs already swept
    "seed4": f"{P}/chris_oversample_a/results/oversample-27",
    "Trp44": f"{P}/chris_oversample_b/results/oversample-31",
    "fresh4BS0A": f"{P}/chris_family_motifs/results/oversample-35",
    "8USL_B": f"{P}/chris_family_motifs/results/oversample-36",
    "seed12": f"{P}/chris_family_motifs/results/oversample-59",
    "seed13": f"{P}/chris_family_motifs/results/oversample-60",
    "seed11": f"{P}/chris_family_motifs/results/oversample-58",
    "seed3": f"{P}/chris_os_s3/results/oversample-39",
    "seed5": f"{P}/chris_os_s5/results/oversample-40",
}
JOB47 = f"{P}/chris_oversample_a/results/replicate-47"
STOP_BY = datetime(2026, 11, 22, 8, 0, tzinfo=timezone.utc)
ESTIMATE_MIN = {"repl1": 45, "arms": 125, "main": 75, "repl2": 55}
PENDING_WARN_MIN = 90
POLL_SECONDS = 45

# (low, high, tolerance, weight when below low) - the crystal range in tolerance units
RANGES = {
    "base_d": (2.41, 2.69, 0.25, 2.0),
    "donor_d": (2.92, 3.24, 0.25, 2.0),
    "base_approach": (167.1, 175.8, 15, 1.0),
    "base_oop": (1.0, 11.7, 15, 1.0),
    "donor_approach": (162.1, 173.0, 15, 1.0),
    "donor_oop": (0.6, 16.1, 15, 1.0),
}
BASE_WINDOW, DONOR_WINDOW = (2.41, 2.69), (2.92, 3.60)
GOOD_D = 8.7  # the 95th percentile of the baseline design population; "good" means D at or below this
RULE = {"min_seeds_both": 3, "max_mean_d": 15.0, "min_od2_nearest": 4, "max_designs": 20}

DRY = False


def now():
    return datetime.now(timezone.utc)


def log(message):
    line = "[%s] %s" % (now().strftime("%m-%d %H:%M:%S"), message)
    print(line, flush=True)
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, "autopilot.log"), "a") as handle:
        handle.write(line + "\n")


def sh(command, env=None):
    done = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
    return done.returncode, done.stdout.strip(), done.stderr.strip()


def in_env(command):
    """Run a command with the organizers' reference paths sourced (gives $ENV_ROOT and friends)."""
    return sh("bash -c 'source %s; %s'" % (REF_ENV, command))


def deviation(row):
    total = 0.0
    for key, (low, high, tol, weight) in RANGES.items():
        value = float(row[key])
        if value < low:
            total += weight * (low - value) / tol
        elif value > high:
            total += (value - high) / tol
    return total


def read_tsv(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def median(values):
    values = sorted(values)
    return values[len(values) // 2] if values else float("nan")


# ----------------------------------------------------------------------------- state
class State:
    def __init__(self):
        self.path = os.path.join(WORK, "state.json")
        self.data = json.load(open(self.path)) if os.path.exists(self.path) else {"stages": {}}

    def get(self, stage):
        return self.data["stages"].get(stage, {})

    def set(self, stage, **fields):
        self.data["stages"].setdefault(stage, {}).update(fields)
        if not DRY:
            with open(self.path, "w") as handle:
                json.dump(self.data, handle, indent=1)


# ----------------------------------------------------------------------------- slurm
def submit(name, script, variables):
    env = os.environ.copy()
    env.update({"PDH_WORKSPACE": WORK})
    env.update({k: str(v) for k, v in variables.items()})
    if DRY:
        log(
            "DRY-RUN would sbatch %s [%s]"
            % (script, ", ".join("%s=%s" % (k, str(v)[:60]) for k, v in variables.items()))
        )
        return "DRY%d" % (abs(hash(name + script)) % 1000)
    command = (
        "sbatch --parsable --chdir=%s --job-name=%s --output=%s/logs/%s-%%j.log --export=ALL %s/src/%s"
        % (WORK, name, WORK, name, WORK, script)
    )
    for attempt in (1, 2, 3):
        code, out, err = sh(command, env=env)
        if code == 0 and out.split(";")[0].isdigit():
            jid = out.split(";")[0]
            log("submitted %s as job %s" % (name, jid))
            return jid
        log("WARNING sbatch failed (attempt %d of 3): %s %s" % (attempt, out[:100], err[:150]))
        time.sleep(60)
    raise RuntimeError("sbatch failed three times for %s" % name)


def job_state(jid):
    """'' once the job has left the queue, its state while it is in it, 'UNKNOWN' if Slurm could not be asked.

    A transient squeue failure must NOT read as 'finished': that would resubmit a duplicate of a job that is
    still running. Only Slurm's explicit 'Invalid job id' answer means the job is gone."""
    if str(jid).startswith("DRY"):
        return ""
    code, out, err = sh("squeue -h -j %s -o %%T" % jid)
    if code == 0:
        return out
    return "" if "Invalid job id" in err else "UNKNOWN"


def wait(jobs, outputs_ok, label):
    """Block until every job has left the queue; return the ids whose expected output is missing."""
    warned = set()
    started = last_beat = time.time()
    while True:
        states = {j: job_state(j) for j in jobs}
        if all(not s for s in states.values()):
            break
        minutes = (time.time() - started) / 60
        if time.time() - last_beat > 600:  # silence must be detectable by whoever is watching the log
            log(
                "alive: waiting for %s (%s)" % (label, ", ".join("%s=%s" % (j, s) for j, s in states.items()))
            )
            last_beat = time.time()
        for jid, state in states.items():
            if state == "PENDING" and minutes > PENDING_WARN_MIN and jid not in warned:
                log(
                    "WARNING %s: job %s has been pending %.0f min (queue contention?)" % (label, jid, minutes)
                )
                warned.add(jid)
        time.sleep(POLL_SECONDS)
    return [j for j in jobs if not outputs_ok(j)]


def run_with_retry(name, script, variables, outputs_ok, stage, state):
    """Run one job to a verified output, resuming a known job after a restart.

    Returns the job id, or None if it failed twice. The caller skips it, because one bad job must not
    waste the night."""
    by_name = dict(state.get(stage).get("by_name", {}))
    for attempt in (1, 2):
        jid = by_name.get(name) if attempt == 1 else None
        if jid is not None and not (job_state(jid) or outputs_ok(jid)):
            jid = None  # a known id, but the job is gone and left no output: it failed, so submit afresh
        if jid is None:
            jid = submit(name, script, variables)
        else:
            log("resuming %s with job %s" % (name, jid))
        by_name[name] = jid
        state.set(stage, by_name=by_name, jobs=list(by_name.values()))
        if DRY:
            return jid
        if not wait([jid], outputs_ok, name):
            return jid
        log("job %s (%s) finished without its expected output (attempt %d)" % (jid, name, attempt))
    log("STOP: %s failed twice and is skipped; later stages continue" % name)
    return None


# ----------------------------------------------------------------------------- inputs
def sweep_designs(root):
    """Designs of one finished sweep: name -> record (sequence, positions), from its queries.json."""
    path = os.path.join(root, "queries.json")
    if not os.path.exists(path):
        return {}
    return {r["name"]: r for r in json.load(open(path)) if r.get("kind") == "design"}


def write_fasta(entries, path):
    with open(path, "w") as handle:
        for label, record in entries:
            handle.write(
                ">%s base=%d oxy=%d\n%s\n"
                % (label, record["base_position"], record["donor_position"], record["sequence"])
            )
    log("wrote %s with %d sequences" % (path, len(entries)))


def replicated_sequences():
    """Sequences with a COMPLETE replication (all 5 seeds). A partial run, such as a 2-seed smoke test, does
    not count: counting it would silently drop its designs from the real replication list."""
    seen = set()
    for root in [JOB47] + glob.glob(WORK + "/results/replicate-*"):
        counts = {}
        paths = glob.glob(root + "/seed*_pinned/queries.json") or glob.glob(root + "/seed[0-9]/queries.json")
        for path in paths:
            for record in json.load(open(path)):
                if record.get("kind") == "design":
                    counts[record["sequence"]] = counts.get(record["sequence"], 0) + 1
        seen.update(sequence for sequence, n in counts.items() if n >= 5)
    return seen


def setup(dry):
    for folder in ("src", "inputs", "logs", "results", "tmp", "cache", "arm_inputs"):
        os.makedirs(os.path.join(WORK, folder), exist_ok=True)
    env_sh = os.path.join(WORK, "env.sh")
    if not os.path.exists(env_sh):
        with open(env_sh, "w") as handle:
            handle.write("#!/usr/bin/env bash\nexport PDH_WORKSPACE=%s\nsource %s\n" % (WORK, REF_ENV))
            for var, sub in (
                ("XDG_CACHE_HOME", ""),
                ("HF_HOME", "/huggingface"),
                ("TORCH_HOME", "/torch"),
                ("TORCH_EXTENSIONS_DIR", "/torch-extensions"),
                ("TRITON_CACHE_DIR", "/triton"),
                ("CUDA_CACHE_PATH", "/cuda"),
                ("PIP_CACHE_DIR", "/pip"),
                ("CONDA_PKGS_DIRS", "/conda"),
            ):
                handle.write('export %s="$PDH_WORKSPACE/cache%s"\n' % (var, sub))
            handle.write('export TMPDIR="$PDH_WORKSPACE/tmp"\nexport PYTHONDONTWRITEBYTECODE=1\n')
            handle.write(
                'export PATH="$(dirname -- "$MMSEQS"):$PATH"\nsource "$CONDA_ROOT/etc/profile.d/conda.sh"\n'
            )
    for name in ("kemp.pdb", "fixed_residues.txt", "sequence.json"):
        target = os.path.join(WORK, "inputs", name if name != "kemp.pdb" else "backbone.pdb")
        if not os.path.exists(target):
            sh("cp %s/%s %s" % (BRIDGE, name, target))
    need = [
        os.path.join(WORK, "src", f)
        for f in (
            "oversample.sbatch",
            "replicate_seeds.sbatch",
            "make_arm_inputs.py",
            "geometry_vs_crystal.py",
            "measure_boltz_outputs.py",
            "build_boltz_queries.py",
        )
    ]
    missing = [n for n in need if not os.path.exists(n)]
    if missing:
        raise SystemExit("missing deployed files: %s" % missing)


# ----------------------------------------------------------------------------- stages
def rank_existing():
    """Every already-swept design with its D, best first (uses the committed full-geometry table)."""
    rows = read_tsv(os.path.join(WORK, "inputs", "geometry_full_existing.tsv"))
    ranked = []
    for row in rows:
        if row["sweep"].startswith("rep") or row["sweep"] not in EXISTING:
            continue
        row["D"] = deviation(row)
        ranked.append(row)
    return sorted(ranked, key=lambda r: r["D"])


def stage_repl1(state, count=20):
    if state.get("repl1").get("status") == "done":
        return
    designs = {label: sweep_designs(root) for label, root in EXISTING.items()}
    done = replicated_sequences()
    picked = []
    for row in rank_existing():
        record = designs[row["sweep"]].get(row["name"])
        if record and record["sequence"] not in done and "base_position" in record:
            picked.append(("%s_%s" % (row["sweep"], row["name"]), record))
        if len(picked) == count:
            break
    log(
        "repl1: replicating %d existing designs, best D first: %s"
        % (len(picked), ", ".join(p[0] for p in picked[:8]))
    )
    fasta = os.path.join(WORK, "inputs", "repl1.fasta")
    write_fasta(picked, fasta)
    state.set("repl1", status="running", started=now().isoformat(), count=len(picked))

    jid = run_with_retry(
        "repl1",
        "replicate_seeds.sbatch",
        {"RS_FASTA": fasta, "RS_SEEDS": "1 2 3 4 5"},
        lambda j: replication_ok("repl1", j),
        "repl1",
        state,
    )
    state.set("repl1", status="done" if jid else "failed", finished=now().isoformat(), job=jid)


ARMS = ["baseline", "aromatic", "polar", "close", "ckpt005"]


def arm_variables(arm, offset):
    base = {
        "OS_BACKBONE": os.path.join(WORK, "inputs", "backbone.pdb"),
        "OS_FIXED": "A52 A86",
        "OS_SEQUENCE": os.path.join(WORK, "inputs", "sequence.json"),
        "OS_TEMPERATURES": "0.3",
        "OS_BATCH": 8,
        "OS_NBATCHES": 9,
        "OS_SEED_OFFSET": offset,
    }
    inputs = os.path.join(WORK, "arm_inputs")
    if arm == "aromatic":
        base["OS_EXTRA_ARGS"] = "--bias_AA_per_residue %s/bias_aromatic.json" % inputs
    elif arm == "polar":
        base["OS_EXTRA_ARGS"] = "--bias_AA_per_residue %s/bias_polar_down.json" % inputs
    elif arm == "close":
        base["OS_EXTRA_ARGS"] = "--bias_AA_per_residue %s/bias_close_s024.json" % inputs
    elif arm == "ckpt005":
        base["OS_CKPT"] = CKPT_005
    return base


def replication_ok(name, jid):
    """A replication job is complete when its log ends with the marker the sbatch script prints last."""
    logs = glob.glob("%s/logs/%s-%s.log" % (WORK, name, jid))
    return bool(logs) and "REPLICATION COMPLETE" in open(logs[0]).read()


def sweep_ok(jid):
    path = "%s/results/oversample-%s/geometry_full.tsv" % (WORK, jid)
    return os.path.exists(path) and os.path.getsize(path) > 0


def stage_arms(state):
    if state.get("arms").get("status") == "done":
        return
    code, out, err = in_env(
        "$ENV_ROOT/env-rfd3/bin/python -W ignore %s/src/make_arm_inputs.py %s/inputs/backbone.pdb "
        "%s/queries.json s024 %s/arm_inputs 7" % (WORK, WORK, EXISTING["seed4"], WORK)
    )
    log("arm inputs: %s" % (out.splitlines()[-1] if out else err[:200]))
    needed = [
        os.path.join(WORK, "arm_inputs", f)
        for f in ("bias_aromatic.json", "bias_polar_down.json", "bias_close_s024.json")
    ]
    if not all(os.path.exists(n) for n in needed):
        log("STOP: arm input files are missing (%s); the arms stage is skipped" % (err or out)[:200])
        state.set("arms", status="failed")
        return
    state.set("arms", status="running", started=now().isoformat(), jobs=state.get("arms").get("jobs", []))
    jobs = {}
    for i, arm in enumerate(ARMS):
        jid = run_with_retry(
            "arm-" + arm, "oversample.sbatch", arm_variables(arm, 7 + 4 * i), sweep_ok, "arms", state
        )
        if jid:
            jobs[arm] = jid
    summary = {}
    for arm, jid in jobs.items():
        rows = read_tsv("%s/results/oversample-%s/geometry_full.tsv" % (WORK, jid))
        scores = [deviation(r) for r in rows]
        summary[arm] = {
            "job": jid,
            "n": len(scores),
            "median_D": median(scores),
            "frac_good": sum(1 for s in scores if s <= GOOD_D) / max(1, len(scores)),
            "n_good": sum(1 for s in scores if s <= GOOD_D),
        }
    winner = pick_winner(summary) if "baseline" in summary else "baseline"
    summary["winner"] = winner
    log("arms: %s" % json.dumps(summary))
    log("arms: winner is '%s'" % winner)
    if not DRY:
        json.dump(summary, open(os.path.join(WORK, "arms_summary.json"), "w"), indent=1)
    state.set("arms", status="done", finished=now().isoformat(), winner=winner)


def pick_winner(summary):
    """Pre-registered: an arm wins if its median D is >= 20 % lower than the baseline's AND it has at least
    double the baseline's number of good designs (and at least 2 more). The lowest median D among winners."""
    base = summary["baseline"]
    winners = [
        a
        for a in ARMS
        if a != "baseline"
        and a in summary
        and summary[a]["median_D"] <= 0.8 * base["median_D"]
        and summary[a]["n_good"] >= max(2 * base["n_good"], base["n_good"] + 2)
    ]
    return min(winners, key=lambda a: summary[a]["median_D"]) if winners else "baseline"


def stage_main(state):
    if state.get("main").get("status") == "done":
        return
    arm = state.get("arms").get("winner", "baseline")
    log("main: 216 sequences using the '%s' settings, as two jobs of 108" % arm)
    state.set(
        "main", status="running", started=now().isoformat(), arm=arm, jobs=state.get("main").get("jobs", [])
    )
    for i in range(2):
        variables = arm_variables(arm, 101 + 6 * i)
        variables.update({"OS_BATCH": 9, "OS_NBATCHES": 12})
        run_with_retry("main-%d" % i, "oversample.sbatch", variables, sweep_ok, "main", state)
    state.set("main", status="done", finished=now().isoformat())


def stage_repl2(state, count=25):
    if state.get("repl2").get("status") == "done":
        return
    done = replicated_sequences()
    pool = []
    for stage in ("arms", "main"):
        for jid in state.get(stage).get("jobs", []):
            root = "%s/results/oversample-%s" % (WORK, jid)
            designs = sweep_ok(jid) and sweep_designs(root) or {}
            for row in read_tsv(root + "/geometry_full.tsv"):
                record = designs.get(row["name"])
                if record and record["sequence"] not in done:
                    pool.append((deviation(row), "%s_%s_%s" % (stage, jid, row["name"]), record))
    pool.sort(key=lambda t: t[0])
    unique, seen = [], set()
    for _score, label, record in pool:
        if record["sequence"] not in seen:
            seen.add(record["sequence"])
            unique.append((label, record))
        if len(unique) == count:
            break
    log(
        "repl2: replicating the best %d new designs; best single-fold D values %s"
        % (len(unique), [round(t[0], 1) for t in pool[:6]])
    )
    fasta = os.path.join(WORK, "inputs", "repl2.fasta")
    write_fasta(unique, fasta)
    state.set("repl2", status="running", started=now().isoformat(), count=len(unique))

    jid = run_with_retry(
        "repl2",
        "replicate_seeds.sbatch",
        {"RS_FASTA": fasta, "RS_SEEDS": "1 2 3 4 5"},
        lambda j: replication_ok("repl2", j),
        "repl2",
        state,
    )
    state.set("repl2", status="done" if jid else "failed", finished=now().isoformat(), job=jid)


# ----------------------------------------------------------------------------- final
def replicate_dirs():
    """(label, per-seed directories) for job 47 and every replicate job this pipeline ran."""
    found = [("job47", sorted(glob.glob(JOB47 + "/seed*_pinned")))]
    for root in sorted(glob.glob(WORK + "/results/replicate-*")):
        found.append((os.path.basename(root), sorted(glob.glob(root + "/seed[0-9]"))))
    return found


def aggregate():
    """Per replicated sequence: seeds with both distances in window, mean D, how often OD2 is nearer."""
    table = {}
    for label, dirs in replicate_dirs():
        for directory in dirs:
            names = {
                r["name"]: r
                for r in json.load(open(directory + "/queries.json"))
                if r.get("kind") == "design"
            }
            pinned = {r["name"]: r for r in read_tsv(directory + "/geometry.tsv")}
            full = {r["name"]: r for r in read_tsv(directory + "/geometry_full.tsv")}
            for name, record in names.items():
                if name not in pinned or name not in full:
                    continue
                entry = table.setdefault(
                    record["sequence"], {"label": "%s:%s" % (label, name), "record": record, "seeds": []}
                )
                p, f = pinned[name], full[name]
                try:
                    base, donor = float(p["pinned_base"]), float(p["pinned_donor"])
                except ValueError:
                    continue
                entry["seeds"].append(
                    {
                        "both": BASE_WINDOW[0] <= base <= BASE_WINDOW[1]
                        and DONOR_WINDOW[0] <= donor <= DONOR_WINDOW[1],
                        "D": deviation(f),
                        "od2_nearest": abs(base - float(f["base_d"])) <= 0.02,
                        "ipde": float(p["complex_ipde"]) if p.get("complex_ipde") else float("nan"),
                    }
                )
    rows = []
    for sequence, entry in table.items():
        seeds = entry["seeds"]
        if len(seeds) < 5:
            continue
        ipdes = [s["ipde"] for s in seeds if not math.isnan(s["ipde"])]
        row = {
            "label": entry["label"],
            "n_seeds": len(seeds),
            "seeds_both": sum(s["both"] for s in seeds),
            "mean_D": sum(s["D"] for s in seeds) / len(seeds),
            "best_D": min(s["D"] for s in seeds),
            "od2_nearest": sum(s["od2_nearest"] for s in seeds),
            "mean_ipde": sum(ipdes) / len(ipdes) if ipdes else float("nan"),
            "base_position": entry["record"]["base_position"],
            "donor_position": entry["record"]["donor_position"],
            "sequence": sequence,
        }
        row["passes_rule"] = (
            row["seeds_both"] >= RULE["min_seeds_both"]
            and row["mean_D"] <= RULE["max_mean_d"]
            and row["od2_nearest"] >= RULE["min_od2_nearest"]
        )
        rows.append(row)
    return sorted(rows, key=lambda r: r["mean_D"])


def stage_final(state):
    rows = aggregate()
    columns = [
        "label",
        "n_seeds",
        "seeds_both",
        "mean_D",
        "best_D",
        "od2_nearest",
        "mean_ipde",
        "passes_rule",
        "base_position",
        "donor_position",
        "sequence",
    ]
    path = os.path.join(WORK, "final_candidates.tsv")
    if not DRY:
        with open(path, "w") as handle:
            handle.write("\t".join(columns) + "\n")
            for row in rows:
                handle.write(
                    "\t".join(
                        ("%.2f" % row[c]) if isinstance(row[c], float) else str(row[c]) for c in columns
                    )
                    + "\n"
                )
    passing = [r for r in rows if r["passes_rule"]][: RULE["max_designs"]]
    log(
        "final: %d replicated designs, %d pass the rule "
        "(>=%d/5 seeds both in window, mean D <= %.0f, OD2 nearest >= %d/5)"
        % (len(rows), len(passing), RULE["min_seeds_both"], RULE["max_mean_d"], RULE["min_od2_nearest"])
    )
    for row in rows[:12]:
        log(
            "   %-34s both %d/5  meanD %5.1f  OD2 %d/5  iPDE %.2f  %s"
            % (
                row["label"][:34],
                row["seeds_both"],
                row["mean_D"],
                row["od2_nearest"],
                row["mean_ipde"],
                "PASS" if row["passes_rule"] else "",
            )
        )
    if passing and not DRY:
        fasta = os.path.join(WORK, "designs_candidate.fasta")
        with open(fasta, "w") as handle:
            for i, row in enumerate(passing, 1):
                handle.write(
                    ">auto_%02d base=%d oxy=%d\n%s\n"
                    % (i, row["base_position"], row["donor_position"], row["sequence"])
                )
        code, out, err = sh("python3 %s %s" % (VALIDATOR, fasta))
        log("final: validator says: %s" % (out.splitlines()[0] if out else err[:200]))
        log(
            "final: candidate file %s (NOT uploaded; the novelty gate and upload are a human/supervisor step)"
            % fasta
        )
    state.set("final", status="done", finished=now().isoformat(), passing=len(passing))


def time_ok(stage):
    need = timedelta(minutes=ESTIMATE_MIN[stage] + 15)
    if now() + need > STOP_BY:
        log(
            "time guard: '%s' needs ~%d min and would not finish before %s; skipping"
            % (stage, ESTIMATE_MIN[stage], STOP_BY.strftime("%H:%M UTC"))
        )
        return False
    return True


def main():
    global DRY, STOP_BY
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--stop-by", help="UTC time like 2026-11-22T08:00; no stage starts that cannot finish by then"
    )
    parser.add_argument("--only", choices=["repl1", "arms", "main", "repl2", "final"])
    args = parser.parse_args()
    DRY = args.dry_run
    if args.stop_by:
        STOP_BY = datetime.strptime(args.stop_by, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
    setup(DRY)
    state = State()
    log("autopilot start (dry-run=%s, stop-by=%s)" % (DRY, STOP_BY.strftime("%m-%d %H:%M UTC")))
    order = [("repl1", stage_repl1), ("arms", stage_arms), ("main", stage_main), ("repl2", stage_repl2)]
    for name, function in order:
        if args.only and args.only != name:
            continue
        if state.get(name).get("status") != "done" and not time_ok(name):
            break
        try:
            function(state)
        except Exception:
            log("STOP: stage %s crashed and is skipped:\n%s" % (name, traceback.format_exc()))
            state.set(name, status="failed")
    if not args.only or args.only == "final":
        try:
            stage_final(state)
        except Exception:
            log("STOP: the final stage crashed:\n%s" % traceback.format_exc())
    log(
        "autopilot finished; stages: %s"
        % json.dumps({k: v.get("status") for k, v in state.data["stages"].items()})
    )


if __name__ == "__main__":
    main()
