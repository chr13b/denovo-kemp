"""The two figures at the top of the README, drawn from tracked result files only.

Usage:
    uv run python scripts/35_plot_readme_figures.py

Reads  results/oversample_a_seed4_job27.tsv        (72 sequences on one backbone, one Boltz-2 fold each)
       results/ranking_combined_all_seeds.tsv      (every design folded on our instrument, by job)
Writes docs/img/refold_gap.png      one backbone, 72 sequences: how many refolds land in the crystal window
       docs/img/fresh_seeds.png     designs folded again on seeds nobody selected on, by design approach

No number is typed in here except the crystal window (2.41-2.69 A, `results/kemp_family_geometry.tsv`) and
the "good design" cut D <= 8.7 (95th percentile of the unbiased baseline, `wiki/approach.md` section 2).
"""

import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import NullFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "img"
WINDOW = (2.41, 2.69)  # base contact, Asp O -> 6NT N3, over the engaged crystal copies
GOOD_D = 8.7
FRESH_JOB = "replicate-106"

INK, BODY, LINE = "#111518", "#49555D", "#D5DBDF"
GREEN = "#0E9F6E"
# Designs are shown by design approach, not by author. Each source in the tables used exactly one approach:
# the theozyme route, sequence sampling on one backbone (the evolutionary route; it also produced the 128 new
# sequences `ns4_*` on the same backbone), or the combinatorial route. Letters prefix the design ids.
APPROACH_OF_SOURCE = {"JJ": "T", "Chris": "E", "Zonghu": "E", "Mario": "C"}
APPROACH = {
    "T": ("Theoretical: one site from the literature", "#FE6101"),
    "E": ("Evolutionary: one backbone, many sequences", "#0151E2"),
    "C": ("Combinatorial: site assembled from many structures", "#01A98C"),
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.edgecolor": LINE,
        "axes.labelcolor": BODY,
        "xtick.color": BODY,
        "ytick.color": BODY,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def read_tsv(path):
    with open(path) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def job_number(job):
    digits = re.findall(r"\d+", job)
    return int(digits[-1]) if digits else 0


def refold_gap():
    rows = [r for r in read_tsv(ROOT / "results" / "oversample_a_seed4_job27.tsv") if r["kind"] == "design"]
    base = sorted(float(r["pinned_base"]) for r in rows if r["pinned_base"])
    inside = [d for d in base if WINDOW[0] <= d <= WINDOW[1]]
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=200)
    ax.axhspan(*WINDOW, color=GREEN, alpha=0.18, lw=0)
    ax.axhline(2.51, color=GREEN, lw=1, ls="--")
    colors = [GREEN if WINDOW[0] <= d <= WINDOW[1] else "#8A97A0" for d in base]
    ax.scatter(range(1, len(base) + 1), base, c=colors, s=46, zorder=3, edgecolor="white", linewidth=0.8)
    ax.set_yscale("log")
    ax.set_yticks([2.5, 3, 4, 5, 7, 10, 15, 20])
    ax.set_yticklabels(["2.5", "3", "4", "5", "7", "10", "15", "20"])
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(0, len(base) + 1)
    ax.set_xlabel("72 LigandMPNN sequences on the same backbone, sorted by contact distance", fontsize=10)
    ax.set_ylabel("Boltz-2 refold: Asp O to 6NT N3 (A)", fontsize=10)
    ax.grid(axis="y", color=LINE, lw=0.6)
    ax.set_axisbelow(True)
    ax.text(
        len(base) + 0.5,
        2.55,
        "crystal window 2.41-2.69 A (23 structures)",
        ha="right",
        va="bottom",
        color=GREEN,
        fontsize=9,
    )
    ax.text(
        1,
        max(base) * 0.93,
        "%d of %d refold into the window.\nThe designed backbone is the same for all of them."
        % (len(inside), len(base)),
        va="top",
        fontsize=11,
        color=INK,
        fontweight="bold",
    )
    fig.suptitle(
        "The generator is exact. The sequence decides whether the refold keeps the geometry.",
        x=0.06,
        ha="left",
        fontsize=12.5,
        color=INK,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT / "refold_gap.png")
    plt.close(fig)
    return len(inside), len(base)


def fresh_seeds():
    rows = read_tsv(ROOT / "results" / "ranking_combined_all_seeds.tsv")
    by_sequence = {}
    for row in rows:
        by_sequence.setdefault(row["sequence"], []).append(row)
    entries = []
    for group in by_sequence.values():
        fresh = [r for r in group if r["job"] == FRESH_JOB]
        if not fresh:
            continue
        earlier = [r for r in group if r["job"] != FRESH_JOB]
        first = min(earlier, key=lambda r: job_number(r["job"])) if earlier else None
        name = re.sub(r"^(arms_9\d_|seed4_|JJ)", "", fresh[0]["design"])
        approach = APPROACH_OF_SOURCE[fresh[0]["source"]]
        entries.append((float(fresh[0]["mean_D"]), approach, name, float(first["mean_D"]) if first else None))
    entries.sort()
    fig, ax = plt.subplots(figsize=(10, 6.6), dpi=200)
    ax.axvspan(0, GOOD_D, color=GREEN, alpha=0.10, lw=0)
    ax.axvline(GOOD_D, color=GREEN, lw=1, ls="--")
    ax.text(GOOD_D + 0.3, -0.95, "good: D <= 8.7", color=GREEN, fontsize=9, va="center")
    for i, (fresh_d, approach, _name, first_d) in enumerate(entries):
        color = APPROACH[approach][1]
        ax.barh(i, fresh_d, height=0.62, color=color, zorder=2)
        if first_d is not None:
            ax.plot([first_d, fresh_d], [i, i], color=INK, lw=0.9, zorder=3, alpha=0.55)
            ax.scatter(
                [first_d], [i], marker="D", s=34, facecolor="white", edgecolor=INK, linewidth=1.2, zorder=4
            )
        ax.text(
            fresh_d + 0.6 if first_d is None or first_d < fresh_d else max(first_d, fresh_d) + 0.6,
            i,
            "%.1f" % fresh_d,
            va="center",
            fontsize=8.5,
            color=INK,
        )
    ax.set_yticks(range(len(entries)))
    ax.set_yticklabels(["%s-%s" % (e[1], e[2]) for e in entries], fontsize=9)
    for tick, entry in zip(ax.get_yticklabels(), entries, strict=True):
        tick.set_color(APPROACH[entry[1]][1])
        tick.set_fontweight("bold")
    ax.invert_yaxis()
    ax.set_ylim(len(entries) - 0.4, -1.6)
    ax.set_xlim(0, 44)
    ax.set_xlabel(
        "geometry error D on five fresh seeds (summed overshoot beyond the crystal windows; lower is better)",
        fontsize=9.5,
    )
    ax.grid(axis="x", color=LINE, lw=0.6)
    ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _label, c in APPROACH.values()]
    handles.append(
        plt.Line2D(
            [], [], marker="D", ls="", markerfacecolor="white", markeredgecolor=INK, markeredgewidth=1.2
        )
    )
    labels = [*(label for label, _c in APPROACH.values()), "first look (selection fold)"]
    ax.legend(handles, labels, loc="upper right", bbox_to_anchor=(1.0, 0.86), frameon=False, fontsize=9)
    fig.suptitle(
        "Fresh seeds separate robust designs from lucky ones",
        x=0.04,
        ha="left",
        fontsize=13,
        color=INK,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT / "fresh_seeds.png")
    plt.close(fig)
    return entries


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inside, total = refold_gap()
    entries = fresh_seeds()
    good = [e for e in entries if e[0] <= GOOD_D]
    print("refold_gap.png: %d of %d sequences in the window" % (inside, total))
    print("fresh_seeds.png: %d designs, %d with D <= %.1f" % (len(entries), len(good), GOOD_D))
    for fresh_d, approach, name, first_d in entries:
        print(
            "  %-7s %-10s fresh %5.1f first %s"
            % (approach, name, fresh_d, "-" if first_d is None else "%.1f" % first_d)
        )


if __name__ == "__main__":
    main()
