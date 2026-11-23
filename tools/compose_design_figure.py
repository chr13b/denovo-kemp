"""Compose the README's design figure from two PyMOL renders (`tools/render_design.pml`).

Usage:
    uv run python tools/compose_design_figure.py <folder with overview.png, closeup.png> <out.png>

Left panel: the whole protein. Right panel: the active site with the two catalytic contacts.
The captions say what the structure is (design s010, Boltz-2 refold, seed 2 of 5) and that the
seed was picked for illustration.
"""

import sys

import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

INK, BODY = "#111518", "#49555D"
TITLE = "A de novo design, refolded by Boltz-2 around its target"
SUBTITLE = (
    "Design s010: backbone generated de novo, sequence designed from scratch. "
    "TM-score to the closest known structure 0.57 (novelty gate: 0.70)."
)
CAPTIONS = (
    "Left: whole protein, N-terminus blue to C-terminus red, ligand 6NT as spheres.   "
    "Right: catalytic Asp86 and Gln52 holding 6NT; crystal medians are 2.51 and 3.03 Å.",
    "Boltz-2 refold, seed 2 of 5, chosen for illustration: both contacts are inside the crystal "
    "windows here, and in 2 of the 5 seeds.",
)


def crop(path, box=None):
    image = Image.open(path).convert("RGB")
    if box is None:
        array = np.asarray(image)
        ys, xs = np.where((array < 245).any(axis=2))
        pad = 30
        box = (
            max(xs.min() - pad, 0),
            max(ys.min() - pad, 0),
            min(xs.max() + pad, array.shape[1]),
            min(ys.max() + pad, array.shape[0]),
        )
    return image.crop(box)


def main():
    folder, out = sys.argv[1], sys.argv[2]
    overview = crop(f"{folder}/overview.png")
    closeup = crop(f"{folder}/closeup.png", (80, 380, 1500, 1060))
    fig = plt.figure(figsize=(12, 5.4), dpi=200)
    ratios = [overview.width / overview.height, closeup.width / closeup.height]
    grid = fig.add_gridspec(
        1, 2, width_ratios=ratios, wspace=0.04, left=0.01, right=0.99, top=0.84, bottom=0.12
    )
    for slot, image in zip(grid, (overview, closeup), strict=True):
        ax = fig.add_subplot(slot)
        ax.imshow(image)
        ax.axis("off")
    fig.text(0.02, 0.945, TITLE, fontsize=14, fontweight="bold", color=INK)
    fig.text(0.02, 0.895, SUBTITLE, fontsize=9.5, color=BODY)
    for y, caption in zip((0.06, 0.025), CAPTIONS, strict=True):
        fig.text(0.02, y, caption, fontsize=8.8, color=BODY)
    fig.savefig(out)


if __name__ == "__main__":
    main()
