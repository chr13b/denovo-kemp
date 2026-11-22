#!/usr/bin/env python3
"""Turn replicated results into a candidate submission: rule, novelty gate, index check, validator. No upload.

Runs ON THE CLUSTER'S HEAD NODE (stdlib only, Python 3.8 compatible; the novelty search is foldseek, which the
organizers' guide allows there because it is a short query against a prebuilt database):

    python3 finalize.py [--max 20]

It re-reads every replication result through the same aggregator the driver's final stage uses, so it can be
run at any moment, including while the pipeline is still going, to see what the submission would be right now.

For every design that passes the pre-registered selection rule (>= 3/5 seeds with both distances in window,
mean D <= 15, OD2 the nearest carboxylate oxygen in >= 4/5 seeds) it then:
  1. runs the novelty gate on a predicted structure (qTM <= 0.70 against the Kemp family AND the PDB
     representatives);
  2. checks that the residue at base= is D/E and at oxy= is Q/N/S/T/Y/K/R: an off-by-one is NOT rejected by
     the scorer, it silently measures an unrelated residue;
  3. writes designs_final.fasta (best mean D first) and runs the organizers' validator on it.

Writes final_report.tsv and designs_final.fasta into the autopilot project directory. It never uploads: the
upload is one deliberate command (see the end of the output), run only when the new file is at least as good
as what is already there.
"""

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autopilot as ap  # noqa: E402

NOVELTY = os.path.join(ap.WORK, "src", "novelty_check.sh")
GATE = 0.70
BASE_OK, DONOR_OK = set("DE"), set("QNSTYKR")


def structure_for(label):
    """The seed-1 predicted structure of a design, from its 'replicate-NN:name' or 'job47:name' label."""
    root, name = label.split(":", 1)
    if root == "job47":
        base = ap.JOB47
    else:
        base = os.path.join(ap.WORK, "results", root)
    path = "%s/seed1/boltz/boltz_results_queries/predictions/%s/%s_model_0.cif" % (base, name, name)
    return path if os.path.exists(path) else None


def novelty(path):
    """(family qTM, PDB-representatives qTM): the best query-normalised TM-score against each, or None."""
    done = subprocess.run(["bash", NOVELTY, path], capture_output=True, text=True)
    found = re.findall(r"(PASSES|FAILS).*?qTM ([0-9.]+)", done.stdout)
    values = [float(v) for _, v in found]
    return (values[0] if len(values) > 0 else None, values[1] if len(values) > 1 else None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=ap.RULE["max_designs"])
    parser.add_argument(
        "--also",
        nargs="*",
        default=[],
        help="labels to add OUTSIDE the rule, e.g. replicate-100:d_arms_98_s010",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="output fasta name (default designs_final.fasta, or designs_proposed.fasta with --also)",
    )
    args = parser.parse_args()
    ap.log = lambda message: print(message, flush=True)  # print only; do not append to the driver's log

    rows = ap.aggregate()
    passing = [r for r in rows if r["passes_rule"]][: args.max]
    by_label = {r["label"]: r for r in rows}
    for label in args.also:
        if label not in by_label:
            print("  --also %s: no such fully replicated design, ignored" % label)
        elif by_label[label] not in passing:
            passing.append(by_label[label])
            print(
                "  --also %s: added OUTSIDE the pre-registered rule (mean D %.1f, both-in-window %d/5)"
                % (label, by_label[label]["mean_D"], by_label[label]["seeds_both"])
            )
    passing.sort(key=lambda r: r["mean_D"])
    print("%d designs replicated over 5 seeds; %d pass the selection rule" % (len(rows), len(passing)))

    kept = []
    report = [
        [
            "label",
            "mean_D",
            "seeds_both",
            "od2_nearest",
            "mean_ipde",
            "qTM_family",
            "qTM_pdb",
            "index_ok",
            "kept",
        ]
    ]
    for row in passing:
        seq, base, oxy = row["sequence"], row["base_position"], row["donor_position"]
        index_ok = seq[base - 1] in BASE_OK and seq[oxy - 1] in DONOR_OK
        path = structure_for(row["label"])
        family, pdb = novelty(path) if path else (None, None)
        novel = path is not None and all(v is not None and v <= GATE for v in (family, pdb))
        keep = bool(index_ok and novel)
        print(
            "  %-30s meanD %5.1f  both %d/5  OD2 %d/5  qTM family %s pdb %s  index %s  -> %s"
            % (
                row["label"][:30],
                row["mean_D"],
                row["seeds_both"],
                row["od2_nearest"],
                family,
                pdb,
                "ok" if index_ok else "BAD",
                "KEEP" if keep else "DROP",
            )
        )
        report.append(
            [
                row["label"],
                "%.2f" % row["mean_D"],
                row["seeds_both"],
                row["od2_nearest"],
                "%.2f" % row["mean_ipde"],
                family,
                pdb,
                index_ok,
                keep,
            ]
        )
        if keep:
            kept.append(row)

    with open(os.path.join(ap.WORK, "final_report.tsv"), "w") as handle:
        for line in report:
            handle.write("\t".join(str(c) for c in line) + "\n")
    if not kept:
        print("nothing passes every gate; no file written")
        return
    name = args.out or ("designs_proposed.fasta" if args.also else "designs_final.fasta")
    fasta = os.path.join(ap.WORK, name)
    with open(fasta, "w") as handle:
        for i, row in enumerate(kept, 1):
            handle.write(
                ">kemp_%02d base=%d oxy=%d\n%s\n"
                % (i, row["base_position"], row["donor_position"], row["sequence"])
            )
    check = subprocess.run(["python3", ap.VALIDATOR, fasta], capture_output=True, text=True)
    print()
    print((check.stdout or check.stderr).strip().splitlines()[0])
    print("\nwrote %s (%d designs, best mean D first) and %s/final_report.tsv" % (fasta, len(kept), ap.WORK))
    print("NOT uploaded. To upload, after confirming it is at least as good as the file already there:")
    print("  cd %s && ./submit-designs.sh %s" % (os.path.dirname(ap.VALIDATOR), fasta))


if __name__ == "__main__":
    main()
