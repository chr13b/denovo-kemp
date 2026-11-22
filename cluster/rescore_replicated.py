#!/usr/bin/env python3
"""Rescore every replicated design with the two terms D lacked: burial (K4) and "worse of the two decides".

Runs ON THE CLUSTER'S HEAD NODE (stdlib only, Python 3.8 compatible; it reads about 250 small structure files
and does no modelling, so it is not heavy compute):

    python3 rescore_replicated.py [out.tsv]

Why. The organizers write that the angle term and the in-plane term "do not average: the worse of the
two decides", and that active-site packing (CA atoms around the catalytic base, up to 12 A) is a scored
term. Our D adds the angle and in-plane overshoots of every contact, and the pipeline never measured
burial. Zonghu's scorer (origin/zonghu, `scripts/40_score_metrics_pack.py`) has both. This script adds
both to ours, per design, from the same five seeds:

  D        our original sum of the overshoots of all six geometry terms
  D2       distances as before, but per contact the approach and in-plane angles are combined with max()
  A_over   how far the angle AT THE HETEROATOM (his definition: C-O...N3 base, C-N...N1 donor)
           lies outside the 25 crystal copies' range (A1 125.1-133.1 deg, A4 130.4-145.0 deg), the worse
           of the two
  burial   CA atoms within 12 A of the declared base's OD2 (his default), averaged over the seeds
  ...plus how often both contacts are in window, how often OD2 is the nearest oxygen, and iPDE, taken from the
  aggregator.

The three scores are reported side by side so a design is only trusted when it ranks well under all of them:
the organizers do not say which angle definition they use.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autopilot as ap  # noqa: E402

A1_RANGE = (125.13, 133.08)  # angle C-OD2...N3 at the oxygen over the 25 engaged crystal copies (min, max)
A4_RANGE = (130.40, 145.01)  # angle C-NE2...N1 at the nitrogen, same copies
BURIAL_RADIUS = 12.0


def overshoot(key, row):
    """One geometry term's overshoot in tolerance units, the way deviation() counts it."""
    low, high, tolerance, weight = ap.RANGES[key]
    value = float(row[key])
    if value < low:
        return weight * (low - value) / tolerance
    if value > high:
        return (value - high) / tolerance
    return 0.0


def deviation_worst(row):
    """D2: per contact, the angle and the in-plane terms are not summed, the worse one decides."""
    return (
        overshoot("base_d", row)
        + overshoot("donor_d", row)
        + max(overshoot("base_approach", row), overshoot("base_oop", row))
        + max(overshoot("donor_approach", row), overshoot("donor_oop", row))
    )


def outside(value, bounds):
    return max(0.0, bounds[0] - value, value - bounds[1])


def angle_over(row):
    """Degrees outside the crystal range for the angle at the heteroatom, the worse of base and donor."""
    return max(outside(float(row["A1"]), A1_RANGE), outside(float(row["A4"]), A4_RANGE))


def atoms_of(cif):
    """(CA coordinates by residue number, OD2 coordinates by residue number) of chain A, from an mmCIF."""
    names, ca, od2, in_loop, header = [], {}, {}, False, True
    with open(cif) as handle:
        for line in handle:
            if line.startswith("loop_"):
                names, in_loop, header = [], True, True
                continue
            if in_loop and header and line.startswith("_atom_site."):
                names.append(line.strip()[len("_atom_site.") :])
                continue
            if in_loop and names and line.startswith(("#", "_")) and not line.startswith("_atom_site."):
                if "group_PDB" in names:
                    break
                in_loop = False
                continue
            if in_loop and names:
                header = False
                if "group_PDB" not in names:
                    continue
                cells = line.split()
                if len(cells) < len(names) or cells[names.index("group_PDB")] != "ATOM":
                    continue
                row = dict(zip(names, cells))  # noqa: B905 (strict= needs Python 3.10; the head node is older)
                if row["label_asym_id"] != "A":
                    continue
                atom, residue = row["label_atom_id"], row["label_seq_id"]
                xyz = (float(row["Cartn_x"]), float(row["Cartn_y"]), float(row["Cartn_z"]))
                if atom == "CA":
                    ca[residue] = xyz
                elif atom == "OD2":
                    od2[residue] = xyz
    return ca, od2


def burial(cif, base_position):
    """CA atoms within BURIAL_RADIUS of the declared base's OD2; None if the structure cannot be read."""
    try:
        ca, od2 = atoms_of(cif)
    except (OSError, ValueError):
        return None
    point = od2.get(str(base_position))
    if point is None:
        return None
    limit = BURIAL_RADIUS**2
    total = 0
    for xyz in ca.values():
        if sum((a - b) ** 2 for a, b in zip(xyz, point)) <= limit:  # noqa: B905 (3.8: no strict=)
            total += 1
    return total


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ap.WORK, "rescored.tsv")
    ap.log = lambda message: print(message, flush=True)
    table = {}
    for label, dirs in ap.replicate_dirs():
        for directory in dirs:
            import json

            records = {
                r["name"]: r
                for r in json.load(open(directory + "/queries.json"))
                if r.get("kind") == "design"
            }
            full = {r["name"]: r for r in ap.read_tsv(directory + "/geometry_full.tsv")}
            for name, record in records.items():
                if name not in full:
                    continue
                f = full[name]
                cif = "%s/boltz/boltz_results_queries/predictions/%s/%s_model_0.cif" % (directory, name, name)
                entry = table.setdefault(
                    record["sequence"], {"label": "%s:%s" % (label, name), "record": record, "seeds": []}
                )
                try:
                    entry["seeds"].append(
                        {
                            "D": ap.deviation(f),
                            "D2": deviation_worst(f),
                            "A_over": angle_over(f),
                            "burial": burial(cif, record["base_position"]),
                        }
                    )
                except (KeyError, ValueError):
                    continue
    aggregated = {r["label"]: r for r in ap.aggregate()}
    rows = []
    for entry in table.values():
        seeds = entry["seeds"]
        base = aggregated.get(entry["label"])
        if len(seeds) < 5 or base is None:
            continue
        burials = [s["burial"] for s in seeds if s["burial"] is not None]
        rows.append(
            {
                "label": entry["label"],
                "mean_D": sum(s["D"] for s in seeds) / len(seeds),
                "mean_D2": sum(s["D2"] for s in seeds) / len(seeds),
                "worst_D2": max(s["D2"] for s in seeds),
                "mean_A_over": sum(s["A_over"] for s in seeds) / len(seeds),
                "burial": sum(burials) / len(burials) if burials else float("nan"),
                "seeds_both": base["seeds_both"],
                "od2_nearest": base["od2_nearest"],
                "mean_ipde": base["mean_ipde"],
            }
        )
    for key in ("mean_D", "mean_D2", "mean_A_over"):
        for position, row in enumerate(sorted(rows, key=lambda r: r[key]), 1):
            row["rank_" + key] = position
    for row in rows:
        row["worst_rank"] = max(row["rank_mean_D"], row["rank_mean_D2"], row["rank_mean_A_over"])
    rows.sort(key=lambda r: r["mean_D2"])
    columns = [
        "label",
        "mean_D",
        "mean_D2",
        "worst_D2",
        "mean_A_over",
        "burial",
        "seeds_both",
        "od2_nearest",
        "mean_ipde",
        "rank_mean_D",
        "rank_mean_D2",
        "rank_mean_A_over",
        "worst_rank",
    ]
    with open(out, "w") as handle:
        handle.write("\t".join(columns) + "\n")
        for row in rows:
            handle.write(
                "\t".join(("%.2f" % row[c]) if isinstance(row[c], float) else str(row[c]) for c in columns)
                + "\n"
            )
    print("%d designs rescored -> %s" % (len(rows), out))
    print(
        "%-30s %6s %6s %7s %7s %6s %5s %5s %5s | ranks D D2 Aover worst"
        % ("design", "D", "D2", "worstD2", "A_over", "burial", "both", "OD2", "iPDE")
    )
    for row in rows[:16]:
        print(
            "%-30s %6.1f %6.1f %7.1f %7.1f %6.1f %5d %5d %5.2f | %9d %2d %5d %5d"
            % (
                row["label"][-30:],
                row["mean_D"],
                row["mean_D2"],
                row["worst_D2"],
                row["mean_A_over"],
                row["burial"],
                row["seeds_both"],
                row["od2_nearest"],
                row["mean_ipde"],
                row["rank_mean_D"],
                row["rank_mean_D2"],
                row["rank_mean_A_over"],
                row["worst_rank"],
            )
        )


if __name__ == "__main__":
    main()
