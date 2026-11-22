#!/usr/bin/env python3
"""Markdown tables from `ranking_all.tsv` (rank_candidates.py) and, optionally, Zonghu's `zh_all.tsv`.

Stdlib only. Runs anywhere:

    python3 format_ranking.py ranking_all.tsv [zh_all.tsv] [--fresh-job replicate-106]

Every design appears once per table with its source (Chris, Zonghu, JJ, Mario) in bold. Two tables:

  1. the designs folded again on fresh seeds (the job given by --fresh-job): the seeds-1-5 result that
     picked them next to the fresh-seed result, and the pooled mean over every fold of that sequence;
  2. every design on seeds 1-5 (the selection evidence), best mean D first.

D is the summed overshoot beyond the crystal windows (see wiki/approach.md); lower is better. Pooled means are
exact (means over seeds weighted by the number of seeds in each row).
"""

import csv
import re
import sys


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def fmt(value, digits=1):
    value = number(value)
    return "-" if value != value else ("%." + str(digits) + "f") % value


def job_number(job):
    digits = re.findall(r"\d+", job)
    return int(digits[-1]) if digits else 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fresh_job = "replicate-106"
    if "--fresh-job" in sys.argv:
        fresh_job = sys.argv[sys.argv.index("--fresh-job") + 1]
        args = [a for a in args if a != fresh_job]
    rows = list(csv.DictReader(open(args[0]), delimiter="\t"))
    zh = {}
    if len(args) > 1:
        for r in csv.DictReader(open(args[1]), delimiter="\t"):
            zh[(r["job"], r["sequence"])] = r

    by_sequence = {}
    for r in rows:
        by_sequence.setdefault(r["sequence"], []).append(r)

    def selection_row(group):
        """The row that picked the design: the newest job that is not the fresh job."""
        pool = [r for r in group if r["job"] != fresh_job]
        return max(pool, key=lambda r: job_number(r["job"])) if pool else None

    def pooled(group, key):
        total = sum(int(r["n_seeds"]) for r in group)
        return sum(number(r[key]) * int(r["n_seeds"]) for r in group) / total, total

    def novelty(r):
        if r["novelty_from"] == "-":
            return "-"
        return fmt(max(number(r["qtm_family"]), number(r["qtm_pdb"])), 2)

    out = []
    fresh = []
    for group in by_sequence.values():
        f = [r for r in group if r["job"] == fresh_job]
        if f:
            fresh.append((f[0], selection_row(group), group))
    fresh.sort(key=lambda t: number(t[0]["mean_D"]))
    out.append(
        "### Table 1. Re-folded on fresh seeds (6, 7, 8, 9, 0): selection result next to fresh result\n"
    )
    out.append(
        "| # | Source | Design | seeds 1-5: mean D | **fresh: mean D** | fresh: D2 | "
        "fresh: angle over (deg) | "
        "fresh: both in window | fresh: OD2 nearest | fresh: iPDE | fresh: worst-seed D | "
        "pooled mean D (n) | "
        "Zonghu K1-K5 (fresh) | novelty qTM |"
    )
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, (f, sel, group) in enumerate(fresh, 1):
        pool_d, n = pooled(group, "mean_D")
        z = zh.get((f["job"], f["sequence"]))
        nov = novelty(f) if novelty(f) != "-" else (novelty(sel) if sel else "-")
        out.append(
            "| %d | **%s** | %s | %s | **%s** | %s | %s | %s/5 | %s/5 | %s | %s | %s (%d) | %s | %s |"
            % (
                i,
                f["source"],
                f["design"],
                fmt(sel["mean_D"]) if sel else "- (first fold)",
                fmt(f["mean_D"]),
                fmt(f["mean_D2"]),
                fmt(f["mean_A_over"], 0),
                f["seeds_both"],
                f["od2_nearest"],
                fmt(f["mean_ipde"], 2),
                fmt(f["worst_D"]),
                fmt(pool_d),
                n,
                fmt(z["K1_K5"], 3) if z else "-",
                nov,
            )
        )

    latest = []
    for group in by_sequence.values():
        sel = selection_row(group)
        if sel is not None:
            latest.append((sel, group))
    latest.sort(key=lambda t: number(t[0]["mean_D"]))
    out.append("\n### Table 2. Every design on seeds 1-5 (the selection evidence), best mean D first\n")
    out.append(
        "| # | Source | Design | Len | both in window | OD2 nearest | mean D | mean D2 | angle over (deg) | "
        "burial | "
        "iPDE | Zonghu K1-K5 | novelty qTM | re-folded fresh |"
    )
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, (r, group) in enumerate(latest[:45], 1):
        z = zh.get((r["job"], r["sequence"]))
        again = any(g["job"] == fresh_job for g in group)
        out.append(
            "| %d | **%s** | %s%s | %s | %s/%s | %s/%s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                i,
                r["source"],
                r["design"],
                " (control, newest batch)" if r["control_refold"] == "True" else "",
                r["length"],
                r["seeds_both"],
                r["n_seeds"],
                r["od2_nearest"],
                r["n_seeds"],
                fmt(r["mean_D"]),
                fmt(r["mean_D2"]),
                fmt(r["mean_A_over"], 0),
                fmt(r["burial"], 0),
                fmt(r["mean_ipde"], 2),
                fmt(z["K1_K5"], 3) if z else "-",
                novelty(r),
                "yes" if again else "no",
            )
        )
    print("\n".join(out))


if __name__ == "__main__":
    main()
