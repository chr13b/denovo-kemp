#!/usr/bin/env python3
"""Rank every five-seed design on ONE instrument, with the source of each design on every row.

Runs ON THE CLUSTER'S HEAD NODE (stdlib only, Python 3.8 compatible; it reads small result files and does no
modelling):

    python3 rank_candidates.py [out.tsv] [--novelty DIR ...]

Why a new script. `autopilot.aggregate()` merges every fold of the same SEQUENCE across jobs. That is right
for "how good is this sequence", but it hides whether the instrument reproduces from one job to the next,
and it cannot say who made a design. Here the key is (job, sequence): a control that was folded again
in a later job appears as its own row, flagged, next to its first row.

Source of a design, read from the query name the job was submitted with:

    d_jj_*       JJ     (Janis; RFD4-Proteina designs scored with Boltz-2)
    d_mario_*    Mario  (his top-20 list)
    d_zonghu_*   Zonghu (our teammate's own sequences, folded here as a control)
    d_chris_*    Chris  (our own designs, folded again in the same batch as a control)
    anything else in an older job is one of OUR designs (Chris)

Columns: the pre-registered quantities (seeds with both contacts in window, mean D, OD2 nearest, iPDE), plus
the two terms D lacked (D2 = worse of approach and in-plane per contact; A_over = degrees outside the crystal
range of the angle at the heteroatom) and burial, plus the novelty gate and the pre-registered rule.

`--novelty DIR` (repeatable, later ones win): directories holding `<name>.txt` raw reports of
`novelty_check.sh` (the name without the leading `d_`). The qTM and the structural identity of the best hit
are read from them.
"""

import glob
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autopilot as ap  # noqa: E402
import rescore_replicated as rr  # noqa: E402

SOURCES = (("d_jj_", "JJ"), ("d_mario_", "Mario"), ("d_zonghu_", "Zonghu"), ("d_chris_", "Chris"))
CONTROL_PREFIXES = ("d_zonghu_", "d_chris_")
HIT = re.compile(r"^\s+\S+\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+[0-9]+\s")


def source_of(name):
    for prefix, label in SOURCES:
        if name.startswith(prefix):
            return label, prefix in CONTROL_PREFIXES
    return "Chris", False


def read_novelty(directories):
    """name -> {family_qtm, family_ident, pdb_qtm, pdb_ident, from}; later directories win."""
    found = {}
    for directory in directories:
        for path in glob.glob(os.path.join(directory, "*.txt")):
            name = os.path.basename(path)[:-4]
            section, values = None, {}
            for line in open(path):
                if "Kemp eliminase family" in line:
                    section = "family"
                elif "PDB representatives" in line:
                    section = "pdb"
                match = HIT.match(line)
                if match and section and section not in values:
                    values[section] = (float(match.group(1)), float(match.group(4)))
            if "family" in values and "pdb" in values:
                found[name] = {
                    "family_qtm": values["family"][0],
                    "family_ident": values["family"][1],
                    "pdb_qtm": values["pdb"][0],
                    "pdb_ident": values["pdb"][1],
                    "from": os.path.basename(directory.rstrip("/")),
                }
    return found


def collect():
    """One entry per (job, sequence) with its per-seed measurements."""
    entries = {}
    for job, dirs in ap.replicate_dirs():
        for directory in dirs:
            if not os.path.exists(directory + "/geometry_full.tsv"):
                continue
            records = {
                r["name"]: r
                for r in json.load(open(directory + "/queries.json"))
                if r.get("kind") == "design"
            }
            pinned = {r["name"]: r for r in ap.read_tsv(directory + "/geometry.tsv")}
            full = {r["name"]: r for r in ap.read_tsv(directory + "/geometry_full.tsv")}
            for name, record in records.items():
                if name not in full or name not in pinned:
                    continue
                p, f = pinned[name], full[name]
                try:
                    base, donor = float(p["pinned_base"]), float(p["pinned_donor"])
                    seed = {
                        "base": base,
                        "donor": donor,
                        "both": ap.BASE_WINDOW[0] <= base <= ap.BASE_WINDOW[1]
                        and ap.DONOR_WINDOW[0] <= donor <= ap.DONOR_WINDOW[1],
                        "D": ap.deviation(f),
                        "D2": rr.deviation_worst(f),
                        "A_over": rr.angle_over(f),
                        "od2": abs(base - float(f["base_d"])) <= 0.02,
                        "ipde": float(p["complex_ipde"]) if p.get("complex_ipde") else float("nan"),
                        "iptm": float(p["iptm"]) if p.get("iptm") else float("nan"),
                    }
                except (KeyError, ValueError):
                    continue
                cif = "%s/boltz/boltz_results_queries/predictions/%s/%s_model_0.cif" % (directory, name, name)
                seed["burial"] = rr.burial(cif, record["base_position"])
                key = (job, record["sequence"])
                entry = entries.setdefault(key, {"job": job, "name": name, "record": record, "seeds": []})
                entry["seeds"].append(seed)
                if os.path.basename(directory) == "seed1":
                    entry["seed1_cif"] = cif
    return entries


def mean(values):
    values = [v for v in values if v is not None and not math.isnan(v)]
    return sum(values) / len(values) if values else float("nan")


def summarize(entry, novelty, labels):
    seeds = entry["seeds"]
    name = entry["name"]
    source, control = source_of(name)
    short = re.sub(r"^d_(jj_|mario_|zonghu_|chris_)?", "", name)
    short = labels.get(entry["record"]["sequence"], short)
    nov = novelty.get(re.sub(r"^d_", "", name)) or novelty.get(short) or {}
    row = {
        "source": source,
        "design": short,
        "job": entry["job"],
        "control_refold": control,
        "length": entry["record"]["length"],
        "base": entry["record"]["base_position"],
        "oxy": entry["record"]["donor_position"],
        "n_seeds": len(seeds),
        "seeds_both": sum(s["both"] for s in seeds),
        "od2_nearest": sum(s["od2"] for s in seeds),
        "mean_D": mean([s["D"] for s in seeds]),
        "worst_D": max(s["D"] for s in seeds),
        "mean_D2": mean([s["D2"] for s in seeds]),
        "mean_A_over": mean([s["A_over"] for s in seeds]),
        "burial": mean([s["burial"] for s in seeds]),
        "mean_base": mean([s["base"] for s in seeds]),
        "mean_donor": mean([s["donor"] for s in seeds]),
        "mean_ipde": mean([s["ipde"] for s in seeds]),
        "mean_iptm": mean([s["iptm"] for s in seeds]),
        "qtm_family": nov.get("family_qtm", float("nan")),
        "qtm_pdb": nov.get("pdb_qtm", float("nan")),
        "ident_max": max(nov.get("family_ident", float("nan")), nov.get("pdb_ident", float("nan")))
        if nov
        else float("nan"),
        "novelty_from": nov.get("from", "-"),
        "sequence": entry["record"]["sequence"],
    }
    sequence = row["sequence"]
    row["index_ok"] = sequence[row["base"] - 1] in "DE" and sequence[row["oxy"] - 1] in "QNSTYKR"
    row["novel"] = (
        "yes" if nov and max(nov["family_qtm"], nov["pdb_qtm"]) <= 0.70 else ("NO" if nov else "unchecked")
    )
    row["passes_rule"] = (
        row["n_seeds"] >= 5
        and row["seeds_both"] >= ap.RULE["min_seeds_both"]
        and row["mean_D"] <= ap.RULE["max_mean_d"]
        and row["od2_nearest"] >= ap.RULE["min_od2_nearest"]
        and row["index_ok"]
    )
    return row


COLUMNS = [
    "rank",
    "source",
    "design",
    "job",
    "control_refold",
    "length",
    "base",
    "oxy",
    "n_seeds",
    "seeds_both",
    "od2_nearest",
    "mean_D",
    "worst_D",
    "mean_D2",
    "mean_A_over",
    "burial",
    "mean_base",
    "mean_donor",
    "mean_ipde",
    "mean_iptm",
    "qtm_family",
    "qtm_pdb",
    "ident_max",
    "novelty_from",
    "novel",
    "index_ok",
    "passes_rule",
    "rank_D",
    "rank_D2",
    "rank_A_over",
    "sequence",
]


def main():
    args = sys.argv[1:]
    novelty_dirs, positional = [], []
    while args:
        item = args.pop(0)
        if item == "--novelty":
            novelty_dirs.append(args.pop(0))
        else:
            positional.append(item)
    out = positional[0] if positional else os.path.join(ap.WORK, "ranking_all.tsv")
    ap.log = lambda message: print(message, flush=True)

    # our own designs are named in the older jobs by their sweep name; give them the names used in the notes
    labels = {}
    repl3 = os.path.join(ap.WORK, "inputs", "repl3.fasta")
    if os.path.exists(repl3):
        name = None
        for line in open(repl3):
            line = line.strip()
            if line.startswith(">"):
                name = re.sub(r"^r3_", "", line[1:].split()[0])
            elif name:
                labels[line] = name

    novelty = read_novelty(novelty_dirs)
    rows = [summarize(e, novelty, labels) for e in collect().values() if len(e["seeds"]) >= 3]
    for key in ("mean_D", "mean_D2", "mean_A_over"):
        for position, row in enumerate(sorted(rows, key=lambda r: r[key]), 1):
            row["rank_" + {"mean_D": "D", "mean_D2": "D2", "mean_A_over": "A_over"}[key]] = position
    rows.sort(key=lambda r: r["mean_D"])
    for position, row in enumerate(rows, 1):
        row["rank"] = position
    with open(out, "w") as handle:
        handle.write("\t".join(COLUMNS) + "\n")
        for row in rows:
            handle.write(
                "\t".join(("%.2f" % row[c]) if isinstance(row[c], float) else str(row[c]) for c in COLUMNS)
                + "\n"
            )
    print("%d (job, design) rows -> %s" % (len(rows), out))
    print(
        "%3s %-7s %-16s %-9s %2s %4s %4s" % ("#", "source", "design", "job", "n", "both", "OD2")
        + " %6s %6s %6s %6s %5s %5s %-9s %s" % ("D", "D2", "Aover", "burial", "iPDE", "qTM", "novel", "rule")
    )
    for row in rows[:45]:
        qtm = max(row["qtm_family"], row["qtm_pdb"]) if row["novelty_from"] != "-" else float("nan")
        print(
            "%3d %-7s %-16s %-9s %2d %4d %4d %6.1f %6.1f %6.1f %6.1f %5.2f %5.2f %-9s %s%s"
            % (
                row["rank"],
                row["source"],
                row["design"][:16],
                row["job"].replace("replicate-", "rep-"),
                row["n_seeds"],
                row["seeds_both"],
                row["od2_nearest"],
                row["mean_D"],
                row["mean_D2"],
                row["mean_A_over"],
                row["burial"],
                row["mean_ipde"],
                qtm,
                row["novel"],
                "PASS" if row["passes_rule"] else "-",
                "  (control re-fold)" if row["control_refold"] else "",
            )
        )


if __name__ == "__main__":
    main()
