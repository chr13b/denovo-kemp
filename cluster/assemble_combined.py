#!/usr/bin/env python3
"""Build the combined submission file (our designs plus JJ's, Mario's and Zonghu's) from `ranking_all.tsv`.

Runs ON THE CLUSTER'S HEAD NODE (stdlib only, Python 3.8 compatible). It never uploads:

    python3 assemble_combined.py [--ranking ranking_all.tsv] [--out designs_combined.fasta]
                                 [--mode rule|top] [--n 10] [--min 5]

The pre-registered rule is the same one finalize.py applies (fixed before any JJ or Mario design was folded):
at least 3 of 5 seeds with both contacts in window, mean D <= 15, OD2 the nearest oxygen in >= 4 of 5 seeds,
the residue at base=/oxy= of the right type. On top of it, one gate that finalize.py runs separately: novelty
(qTM <= 0.70 against the Kemp family AND the PDB representatives) measured on OUR OWN refold of the sequence.

    --mode rule   every design that passes the rule and the novelty gate, best mean D first, at most 20.
                  If fewer than --min pass, the best of the rest (mean D <= 15, gates passed) fill up to --min
                  and are printed as OUTSIDE the rule.
    --mode top    the best --n designs by mean D that pass the hard gates (not the 3-of-5 rule): for when the
                  strict window box rejects designs whose mean D is good.
    --fresh-job J only designs folded again in job J (fresh seeds nobody selected on) are candidates, and
                  their row from J is the one that counts. This is the rule written down in
                  wiki/experiments/chris-08 before the fresh seeds existed.
    --max-d D     with --mode top: take every design whose mean D is at most D instead of a fixed --n.

One row per sequence: a control that was folded twice contributes the row from the newest job (the same batch
as the new designs). The name in the file is `<source>_<design>`, so the submitted file shows who made what.
Names are letters, digits, `_` and `-` only (the organizers' rule), at most 64 characters.
"""

import argparse
import csv
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autopilot as ap  # noqa: E402

GATE = 0.70


def newest_job_key(row):
    digits = re.findall(r"\d+", row["job"])
    return int(digits[-1]) if digits else 0


def load(path):
    with open(path) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def number(value):
    try:
        return float(value)
    except ValueError:
        return float("nan")


def gates(row, fresh_job=None):
    """The hard gates every design must clear. Returns a list of reasons it fails (empty = passes)."""
    reasons = []
    if int(row["n_seeds"]) < 5:
        reasons.append("fewer than 5 seeds")
    if fresh_job and row["job"] != fresh_job:
        reasons.append("no fresh-seed fold")
    if int(row["od2_nearest"]) < ap.RULE["min_od2_nearest"]:
        reasons.append("OD2 not the nearest oxygen in >= %d seeds" % ap.RULE["min_od2_nearest"])
    if row["index_ok"] != "True":
        reasons.append("base=/oxy= residue type")
    if row["novel"] != "yes":
        reasons.append("novelty %s" % row["novel"])
    if row["novelty_from"] in ("-", "novelty_provided"):
        reasons.append("novelty not measured on our own refold")
    return reasons


def passes_rule(row):
    return (
        int(row["seeds_both"]) >= ap.RULE["min_seeds_both"] and number(row["mean_D"]) <= ap.RULE["max_mean_d"]
    )


def file_name(row):
    prefix = {"Chris": "chris", "JJ": "jj", "Mario": "mario", "Zonghu": "zonghu"}[row["source"]]
    design = re.sub(r"^(jj_|mario_|zonghu_|chris_)", "", row["design"])
    return re.sub(r"[^A-Za-z0-9_-]", "_", "%s_%s" % (prefix, design))[:64]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranking", default=os.path.join(ap.WORK, "ranking_all.tsv"))
    parser.add_argument("--out", default="designs_combined.fasta")
    parser.add_argument("--mode", choices=("rule", "top"), default="rule")
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--min", type=int, default=5)
    parser.add_argument("--fresh-job", default=None)
    parser.add_argument("--max-d", type=float, default=None)
    args = parser.parse_args()

    all_rows = load(args.ranking)
    fresh_sequences = (
        {r["sequence"] for r in all_rows if r["job"] == args.fresh_job} if args.fresh_job else set()
    )
    by_sequence = {}
    for row in all_rows:
        if row["sequence"] in fresh_sequences and row["job"] != args.fresh_job:
            continue  # the fresh-seed row replaces every earlier row of that sequence
        old = by_sequence.get(row["sequence"])
        if old is None or newest_job_key(row) > newest_job_key(old):
            by_sequence[row["sequence"]] = row
    rows = sorted(by_sequence.values(), key=lambda r: number(r["mean_D"]))

    eligible, rejected = [], []
    for row in rows:
        reasons = gates(row, args.fresh_job)
        (rejected if reasons else eligible).append((row, reasons))

    if args.mode == "rule":
        chosen = [(r, "") for r, _ in eligible if passes_rule(r)][: ap.RULE["max_designs"]]
        fill = [r for r, _ in eligible if not passes_rule(r) and number(r["mean_D"]) <= ap.RULE["max_mean_d"]]
        while len(chosen) < args.min and fill:
            chosen.append((fill.pop(0), "OUTSIDE the 3-of-5 rule"))
    else:
        pool = [r for r, _ in eligible if args.max_d is None or number(r["mean_D"]) <= args.max_d]
        chosen = [(r, "" if passes_rule(r) else "outside the 3-of-5 rule") for r in pool][
            : args.n if args.max_d is None else None
        ]

    print(
        "%d unique sequences ranked; %d clear the hard gates; %d chosen (mode %s)"
        % (len(rows), len(eligible), len(chosen), args.mode)
    )
    print("\nrejected by a hard gate:")
    for row, reasons in rejected[:60]:
        print(
            "  %-7s %-18s meanD %5.1f  both %s/5  -> %s"
            % (
                row["source"],
                row["design"][:18],
                number(row["mean_D"]),
                row["seeds_both"],
                "; ".join(reasons),
            )
        )

    fasta = os.path.join(ap.WORK, args.out)
    used = set()
    with open(fasta, "w") as handle:
        print("\nchosen:")
        for position, (row, note) in enumerate(chosen, 1):
            name = file_name(row)
            assert name not in used, "duplicate name " + name
            used.add(name)
            handle.write(">%s base=%s oxy=%s\n%s\n" % (name, row["base"], row["oxy"], row["sequence"]))
            print(
                "  %2d %-26s from %-7s meanD %5.1f D2 %5.1f both %s/5 OD2 %s/5 Aover %5.1f iPDE %s %s"
                % (
                    position,
                    name,
                    row["source"],
                    number(row["mean_D"]),
                    number(row["mean_D2"]),
                    row["seeds_both"],
                    row["od2_nearest"],
                    number(row["mean_A_over"]),
                    row["mean_ipde"],
                    note,
                )
            )
    check = subprocess.run(["python3", ap.VALIDATOR, fasta], capture_output=True, text=True)
    print()
    print((check.stdout or check.stderr).strip().splitlines()[0])
    print("wrote %s. NOT uploaded." % fasta)


if __name__ == "__main__":
    main()
