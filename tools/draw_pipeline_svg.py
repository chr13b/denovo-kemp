"""Draw the README's pipeline graphic (`docs/img/pipeline.svg`): six stage cards and the feedback loop.

Usage:
    uv run python tools/draw_pipeline_svg.py docs/img/pipeline.svg

Pure standard library. The numbers on the cards are the ones in the README and `wiki/approach.md`.
"""

# ruff: noqa: E501  (the lines are SVG markup)

import sys
from xml.sax.saxutils import escape

FONT = "Segoe UI, Helvetica, Arial, sans-serif"
W, H = 1280, 470
CARD_W, GAP, X0, Y0, CARD_H = 180, 24, 40, 76, 248
CARDS = [
    (
        "1",
        "#0151E2",
        "TARGET",
        "Asp + Gln + 6NT",
        ["23 crystal structures,", "43 ligand copies"],
        "0.28 Å",
        "base-contact window",
    ),
    (
        "2",
        "#018FE1",
        "BACKBONE",
        "RFdiffusion3",
        ["all-atom motif", "scaffolding, 260 aa"],
        "0.013 Å",
        "motif recovery",
    ),
    (
        "3",
        "#02C4F4",
        "SEQUENCE",
        "LigandMPNN",
        ["steered logits,", "Asp / Gln pinned"],
        "11 vs 1",
        "good designs, steered",
    ),
    ("4", "#01EE92", "COFOLD", "Boltz-2", ["one-fold screen,", "MSA-free"], "19 s", "per fold"),
    (
        "5",
        "#9EDE2E",
        "REPLICATE",
        "5 seeds",
        ["then fresh seeds,", "winner's-curse control"],
        "8 of 20",
        "stay good, fresh seeds",
    ),
    (
        "6",
        "#FE6101",
        "GATES",
        "Novelty gate",
        ["TM ≤ 0.70, index", "check, validator"],
        "TM ≤ 0.61",
        "best 8 designs",
    ),
]
out = []
a = out.append
a(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
)
a('<title id="t">How the pipeline works</title>')
a(
    '<desc id="d">Six stages from the catalytic motif to replicated designs: target, backbone, sequence, cofold, replicate, gates. Replicated parents feed back into the sequence stage.</desc>'
)
a(
    "<defs>"
    '<linearGradient id="strip" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0151E2"/><stop offset="0.2" stop-color="#02C4F4"/>'
    '<stop offset="0.4" stop-color="#01EE92"/><stop offset="0.6" stop-color="#9EDE2E"/><stop offset="0.8" stop-color="#FE6101"/><stop offset="1" stop-color="#E32B06"/></linearGradient>'
    '<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="#C9D3DB"/></marker>'
    "</defs>"
)
a(f'<rect width="{W}" height="{H}" rx="18" fill="#0B1220"/>')
a(
    f'<text x="40" y="46" font-family="{FONT}" font-size="14" font-weight="700" letter-spacing="2" fill="#7F8E99">FROM CATALYTIC MOTIF TO REPLICATED DESIGNS</text>'
)
a('<rect x="960" y="26" width="280" height="26" rx="13" fill="#111B2E" stroke="#1E2B44"/>')
a(
    f'<text x="1100" y="44" text-anchor="middle" font-family="{FONT}" font-size="13" font-weight="600" fill="#C9D3DB">output: designs.fasta, at most 20</text>'
)
centers = []
for i, (num, color, label, tool, desc, metric, mlabel) in enumerate(CARDS):
    x = X0 + i * (CARD_W + GAP)
    centers.append(x + CARD_W / 2)
    a(f'<rect x="{x}" y="{Y0}" width="{CARD_W}" height="{CARD_H}" rx="14" fill="#111B2E" stroke="#1E2B44"/>')
    a(f'<rect x="{x + 16}" y="{Y0}" width="{CARD_W - 32}" height="4" rx="2" fill="{color}"/>')
    a(f'<circle cx="{x + 32}" cy="{Y0 + 36}" r="14" fill="{color}"/>')
    a(
        f'<text x="{x + 32}" y="{Y0 + 41}" text-anchor="middle" font-family="{FONT}" font-size="15" font-weight="800" fill="#0B1220">{num}</text>'
    )
    a(
        f'<text x="{x + 56}" y="{Y0 + 41}" font-family="{FONT}" font-size="13" font-weight="700" letter-spacing="1.4" fill="#7F8E99">{label}</text>'
    )
    a(
        f'<text x="{x + 16}" y="{Y0 + 84}" font-family="{FONT}" font-size="16" font-weight="700" fill="#FFFFFF">{escape(tool)}</text>'
    )
    for k, line in enumerate(desc):
        a(
            f'<text x="{x + 16}" y="{Y0 + 108 + 19 * k}" font-family="{FONT}" font-size="13" fill="#C9D3DB">{escape(line)}</text>'
        )
    a(f'<line x1="{x + 16}" y1="{Y0 + 158}" x2="{x + CARD_W - 16}" y2="{Y0 + 158}" stroke="#1E2B44"/>')
    a(
        f'<text x="{x + 16}" y="{Y0 + 198}" font-family="{FONT}" font-size="26" font-weight="800" fill="{color}">{escape(metric)}</text>'
    )
    a(
        f'<text x="{x + 16}" y="{Y0 + 220}" font-family="{FONT}" font-size="12.5" fill="#7F8E99">{escape(mlabel)}</text>'
    )
    if i < len(CARDS) - 1:
        cx, cy = x + CARD_W + GAP / 2, Y0 + CARD_H / 2
        a(
            f'<path d="M {cx - 4} {cy - 10} L {cx + 4} {cy} L {cx - 4} {cy + 10}" fill="none" stroke="#7F8E99" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        )
# feedback loop: replicated parents steer the next round of sequences (card 5 -> card 3)
y_bot = Y0 + CARD_H
x5, x3 = centers[4], centers[2]
yl = y_bot + 46
a(
    f'<path d="M {x5} {y_bot + 2} L {x5} {yl - 14} Q {x5} {yl} {x5 - 14} {yl} L {x3 + 14} {yl} Q {x3} {yl} {x3} {yl - 14} L {x3} {y_bot + 8}" '
    f'fill="none" stroke="#C9D3DB" stroke-width="2" stroke-dasharray="7 6" marker-end="url(#arrow)"/>'
)
a(f'<rect x="{(x5 + x3) / 2 - 160}" y="{yl - 12}" width="320" height="24" rx="12" fill="#0B1220"/>')
a(
    f'<text x="{(x5 + x3) / 2}" y="{yl + 5}" text-anchor="middle" font-family="{FONT}" font-size="13" font-style="italic" fill="#C9D3DB">replicated parents steer the next sequences</text>'
)
# phase strip
ys = H - 52
a(f'<rect x="40" y="{ys}" width="1200" height="6" rx="3" fill="url(#strip)"/>')
for label, cx in (
    ("DESIGN", (centers[0] + centers[2]) / 2),
    ("SCREEN", centers[3]),
    ("VERIFY", (centers[4] + centers[5]) / 2),
):
    a(
        f'<text x="{cx}" y="{ys + 28}" text-anchor="middle" font-family="{FONT}" font-size="12.5" font-weight="700" letter-spacing="2" fill="#7F8E99">{label}</text>'
    )
a("</svg>")
open(sys.argv[1], "w", encoding="utf8").write("\n".join(out) + "\n")
