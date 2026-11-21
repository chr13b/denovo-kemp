"""The whole argument in one figure: the backbone refolds, the ligand does not stay.

Usage:
    uv run python scripts/34_plot_contact_vs_rmsd.py results/oversample_a_seed4_job27.tsv [more.tsv ...]

Plots base contact against CA RMSD for every sequence in a sweep, with the crystal window
(2.41-2.69 A, measured across 23 structures) drawn as a band. One panel per input file.

What it shows, and why it is the figure for the talk: the points pile up at low CA RMSD - the
protein refolds reliably, sequence after sequence - while the base contact scatters over tens of
angstroms. Those two facts together are the project's finding. The pipeline's own single sequence is
marked, and it sits outside the band that two of its 72 siblings land inside.

Writes results/<stem>_contact_vs_rmsd.png.
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BASE_WINDOW = (2.41, 2.69)
FAMILY_MEDIAN = 2.51
# Each backbone's own single-sequence result from the end-to-end pipeline, for reference.
ORIGINAL = {
    "oversample_a_seed4_job27": ("seed 4, the pipeline's one sequence", 0.7042, 3.3200),
    "oversample_b_trp44_job31": ("zonghu job 7, one sequence", 4.2600, 11.9900),
    "oversample_rescue_s5_job40": ("seed 5, one sequence", 13.6700, 14.8800),
}


def read_tsv(path):
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        row = dict(zip(header, line.split("\t"), strict=False))
        for key, value in list(row.items()):
            if value == "":
                row[key] = None
            else:
                try:
                    row[key] = float(value)
                except ValueError:
                    pass
        rows.append(row)
    return rows


def number(row, key):
    value = row.get(key)
    return value if isinstance(value, float) and math.isfinite(value) else None


def contact(row):
    return number(row, "pinned_base") or number(row, "scan_base")


paths = [Path(p) for p in sys.argv[1:]]
if not paths:
    sys.exit(__doc__)

figure, axes = plt.subplots(1, len(paths), figsize=(6.2 * len(paths), 5.4), squeeze=False)
for axis, path in zip(axes[0], paths, strict=False):
    rows = [r for r in read_tsv(path) if r.get("status") == "measured" and r.get("kind") == "design"]
    xs, ys, colours = [], [], []
    for row in rows:
        x, y = number(row, "ca_rmsd"), contact(row)
        if x is None or y is None:
            continue
        xs.append(x)
        ys.append(y)
        colours.append("#1b7f4f" if BASE_WINDOW[0] <= y <= BASE_WINDOW[1] else "#5a6b7a")

    axis.axhspan(
        *BASE_WINDOW,
        color="#1b7f4f",
        alpha=0.16,
        zorder=0,
        label=f"crystal window {BASE_WINDOW[0]}–{BASE_WINDOW[1]} Å (23 structures)",
    )
    axis.axhline(
        FAMILY_MEDIAN, color="#1b7f4f", lw=1.1, ls="--", zorder=1, label=f"family median {FAMILY_MEDIAN} Å"
    )
    inside = sum(1 for c in colours if c == "#1b7f4f")
    axis.scatter(
        xs,
        ys,
        c=colours,
        s=46,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
        label=f"{len(xs)} sampled sequences ({inside} in window)",
    )

    reference = ORIGINAL.get(path.stem)
    if reference:
        label, rx, ry = reference
        axis.scatter(
            [rx],
            [ry],
            marker="X",
            s=210,
            c="#b3261e",
            edgecolor="white",
            linewidth=1.2,
            zorder=4,
            label=label,
        )

    # Log y, because the contact spans 2.4 to 23 A and a linear axis hides the whole bottom end
    # where the question is decided. Explicit plain-number ticks: "2 x 10^1" is unreadable on a
    # slide, and these are angstroms, not orders of magnitude.
    axis.set_yscale("log")
    axis.set_xscale("log")
    axis.set_yticks([2.5, 3, 4, 5, 7, 10, 15, 20])
    axis.set_yticklabels(["2.5", "3", "4", "5", "7", "10", "15", "20"])
    axis.set_xticks([0.5, 1, 2, 4, 8, 16])
    axis.set_xticklabels(["0.5", "1", "2", "4", "8", "16"])
    axis.minorticks_off()
    axis.set_xlabel("CA RMSD from the designed backbone (Å)  →  did the protein refold?")
    axis.set_ylabel("base contact: Asp O → 6NT N3 (Å)  →  did the ligand stay?")
    axis.set_title(path.stem.replace("_", " "), fontsize=11)
    axis.grid(alpha=0.25, which="both", lw=0.5)
    axis.legend(loc="upper left", fontsize=8, framealpha=0.95)

figure.suptitle(
    "One backbone, many sequences: the fold is reproduced, the catalytic contact is not",
    fontsize=13,
    y=0.99,
)
figure.tight_layout(rect=(0, 0, 1, 0.96))
out = Path("results") / f"{paths[0].stem}_contact_vs_rmsd.png"
figure.savefig(out, dpi=170)
print(f"wrote {out}")
for path in paths:
    rows = [r for r in read_tsv(path) if r.get("status") == "measured" and r.get("kind") == "design"]
    rmsds = [number(r, "ca_rmsd") for r in rows if number(r, "ca_rmsd")]
    bases = [contact(r) for r in rows if contact(r)]
    if rmsds and bases:
        print(
            f"  {path.stem}: CA RMSD {min(rmsds):.2f}–{max(rmsds):.2f} Å, "
            f"base contact {min(bases):.2f}–{max(bases):.2f} Å"
        )
