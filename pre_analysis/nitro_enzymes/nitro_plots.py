"""Figures summarising contact geometry to nitro groups. Reads nitro_polar_geometry.csv / nitro_local_frame.csv
(written by nitro_geometry.py) and writes PNGs to figures/.
Colours: validated categorical order (blue, orange, aqua, yellow, magenta, green, violet, red) on the light surface."""
import os
import numpy as np, pandas as pd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
SURF, INK, INK2, GRID, GRAY = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1", "#b9b8b2"
BLUE, BLUE_D, BLUE_L = "#2a78d6", "#104281", "#9ec5f4"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
mpl.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "text.color": INK,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 10.5, "axes.titlesize": 11.5,
                     "axes.titleweight": "bold", "axes.titlelocation": "left", "legend.frameon": False})

MIN_D = 2.4  # below this an N/O...O contact is a clash / disordered / covalent partner, not an H-bond-range contact
p = pd.read_csv("nitro_polar_geometry.csv")
loc = pd.read_csv("nitro_local_frame.csv")
fold = {"Arg/Lys N+": "Arg/Lys/other N,O", "Other": "Arg/Lys/other N,O", "Cofactor / other ligand": "Cofactor (FMN/FAD/...)",
        "Acceptor O": "Protein acceptor O", "Backbone N-H": "Backbone N-H", "Water": "Water"}
p["cat"] = p.category.replace(fold)
loc["cat"] = loc.category.replace(fold)
ORDER = ["Backbone N-H", "Ser/Thr/Tyr OH", "Asn/Gln NH2", "His N", "Arg/Lys/other N,O", "Water", "Protein acceptor O", "Cofactor (FMN/FAD/...)"]
COL = dict(zip(ORDER, SERIES))
n_short = int((p.d_O_X < MIN_D).sum())
q = p[p.d_O_X >= MIN_D].copy()
prot = q[~q.cat.isin(["Water", "Cofactor (FMN/FAD/...)"])]
N = f"n = {len(q)} contacts, {q.groupby(['pdb_id', 'nitro_ligand', 'nitro_group']).ngroups} nitro groups, {q.pdb_id.nunique()} entries"
FOOT = f"Contacts: any N/O atom within 3.5 Å of a nitro O (closest O). {n_short} contacts < {MIN_D} Å omitted (clash / covalent). Asymmetric-unit copies are counted separately."

def save(fig, name):
    fig.savefig(f"figures/{name}.png", dpi=170, bbox_inches="tight"); plt.close(fig)

def legend_handles(cats):
    return [mpl.patches.Patch(facecolor=COL[c], edgecolor=SURF, label=f"{c} ({int((q.cat == c).sum())})") for c in cats]

# ---------------------------------------------------------------- Fig 1: distance
fig, (a, b) = plt.subplots(1, 2, figsize=(13.5, 4.8), gridspec_kw={"width_ratios": [1.1, 1], "wspace": 0.62})
bins = np.arange(2.4, 3.55, 0.1)
bottom = np.zeros(len(bins) - 1)
for c in ORDER:
    h, _ = np.histogram(q[q.cat == c].d_O_X, bins)
    a.bar(bins[:-1], h, width=0.1, bottom=bottom, align="edge", color=COL[c], edgecolor=SURF, linewidth=1.2)
    bottom += h
a.set(xlabel="distance nitro O ··· X  (Å)", ylabel="contacts", xlim=(2.4, 3.5))
a.set_title("Where contacts sit: most are 2.8–3.3 Å")
a.set_ylim(0, a.get_ylim()[1] * 1.12)
a.axvspan(2.6, 3.1, color=BLUE_L, alpha=0.3, lw=0, zorder=0)
a.text(2.85, a.get_ylim()[1] * 0.99, "typical H-bond range 2.6–3.1 Å", ha="center", va="top", color=INK2, fontsize=9)
a.legend(handles=legend_handles(ORDER), fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, title="partner type (n)", title_fontsize=9, columnspacing=1.2)
rng = np.random.default_rng(1)
for i, c in enumerate(ORDER[::-1]):
    d = q[q.cat == c].d_O_X.values
    b.scatter(d, i + rng.uniform(-0.2, 0.2, len(d)), s=22, color=COL[c], edgecolor=SURF, linewidth=0.8, alpha=0.9, zorder=3)
    if len(d): b.plot([np.median(d)] * 2, [i - 0.33, i + 0.33], color=INK, lw=2, zorder=4)
b.set_yticks(range(len(ORDER))); b.set_yticklabels(ORDER[::-1]); b.set_xlim(2.4, 3.55)
b.set_xlabel("distance nitro O ··· X  (Å);  bar = median"); b.set_title("Distance by partner type")
b.grid(axis="y", visible=False)
fig.suptitle("Distance of contacting atoms to the nitro oxygens", x=0.01, ha="left", fontsize=14, fontweight="bold", y=1.02)
fig.text(0.01, -0.30, N + "\n" + FOOT, fontsize=8.5, color=INK2, ha="left", va="top")
save(fig, "fig1_distance_by_partner")

# ---------------------------------------------------------------- Fig 2: angles
fig, axs = plt.subplots(1, 3, figsize=(14.5, 4.6), gridspec_kw={"wspace": 0.28})
short = q[q.d_O_X <= 3.1]
def hist2(ax, col, rng_, w, data_all, data_short, xl, title, band=None, note=None):
    bn = np.arange(rng_[0], rng_[1] + w, w)
    ax.hist(data_all[col].dropna(), bn, color=BLUE_L, edgecolor=SURF, linewidth=1.2, zorder=2, label=f"all ≤ 3.5 Å (n={data_all[col].notna().sum()})")
    ax.hist(data_short[col].dropna(), bn, color=BLUE_D, edgecolor=SURF, linewidth=1.2, zorder=3, label=f"short ≤ 3.1 Å (n={data_short[col].notna().sum()})")
    top = ax.get_ylim()[1] * 1.7; ax.set_ylim(0, top)
    if band:
        ax.axvspan(*band, color=GRAY, alpha=0.3, lw=0, zorder=0)
        ax.text(np.mean(band), top * 0.80, note, ha="center", va="top", fontsize=8.5, color=INK2)
    ax.set(xlabel=xl, ylabel="contacts"); ax.set_title(title); ax.legend(fontsize=8.5, loc="upper left")
hist2(axs[0], "ang_N_O_X", (50, 180), 10, q, short, "angle N–O ··· X at the nitro O  (°)", "Approach angle at O",
      band=(110, 140), note="sp2 O lone pair\n≈ 120–130°")
hist2(axs[1], "ang_X", (40, 180), 10, prot, prot[prot.d_O_X <= 3.1], "angle Y–X ··· O at the partner atom X  (°)", "Angle at the protein partner",
      band=(120, 180), note="donor H pointing\nat O (≥ 120°)")
hist2(axs[2], "elev_deg", (0, 90), 10, q, short, "elevation of O→X above nitro plane  (°; 0 = in plane)", "Out-of-plane elevation")
fig.suptitle("Angular geometry of contacts to the nitro group", x=0.01, ha="left", fontsize=14, fontweight="bold", y=1.03)
fig.text(0.01, -0.06, N + ";  middle panel = protein atoms only (no water/cofactor), Y = bonded heavy neighbour of X (max over neighbours).\n" + FOOT, fontsize=8.5, color=INK2, ha="left", va="top")
save(fig, "fig2_angles")

# ---------------------------------------------------------------- Fig 3: distance vs angle, one panel per partner type
for yname, ylab, fname, title, cats, ylim in [
        ("ang_N_O_X", "angle N–O ··· X at the nitro O (°)", "fig3a_distance_vs_angle_at_O", "Distance vs approach angle at the nitro O", ORDER, (50, 180)),
        ("ang_X", "angle Y–X ··· O at partner X (°)", "fig3b_distance_vs_angle_at_X", "Distance vs angle at the partner atom X",
         [c for c in ORDER if c != "Water"], (40, 180))]:
    fig, axs = plt.subplots(2, 4, figsize=(14, 6.4), sharex=True, sharey=True)
    for ax, c in zip(axs.ravel(), ORDER if len(cats) == len(ORDER) else cats + [None]):
        if c is None: ax.axis("off"); continue
        ax.scatter(q.d_O_X, q[yname], s=9, color=GRAY, alpha=0.45, linewidth=0)
        s = q[q.cat == c]
        ax.scatter(s.d_O_X, s[yname], s=30, color=COL[c], edgecolor=SURF, linewidth=0.8, zorder=3)
        ax.set_title(f"{c}  (n={s[yname].notna().sum()})", fontsize=10); ax.set_xlim(2.35, 3.55); ax.set_ylim(*ylim)
        if yname == "ang_N_O_X": ax.axhspan(110, 140, color=GRAY, alpha=0.18, lw=0)
        else: ax.axhspan(120, 180, color=GRAY, alpha=0.18, lw=0)
    for ax in axs[-1]: ax.set_xlabel("O ··· X distance (Å)")
    for ax in axs[:, 0]: ax.set_ylabel(ylab)
    fig.suptitle(title, x=0.01, ha="left", fontsize=14, fontweight="bold", y=0.995)
    fig.text(0.01, 0.0, "Grey dots = all contacts (context); coloured = this partner type. Shaded band = " +
             ("110–140°, sp2 O lone-pair direction." if yname == "ang_N_O_X" else "≥ 120°, donor pointing at O (water has no Y).") + "\n" + FOOT,
             fontsize=8.5, color=INK2, va="top")
    fig.tight_layout(rect=(0, 0.01, 1, 0.98)); save(fig, fname)

# ---------------------------------------------------------------- Fig 4: nitro local frame
R = 4.5
l = loc[loc.d_N <= R].copy()
polar_mask = l.element.isin(["N", "O"]) & (l.d_Omin <= 3.5) & (l.d_Omin >= MIN_D)
rows = [("Protein N/O within 3.5 Å of a nitro O", polar_mask & ~l.cat.isin(["Water", "Cofactor (FMN/FAD/...)"]), SERIES[0], "o"),
        ("Water within 3.5 Å of a nitro O", polar_mask & (l.cat == "Water"), SERIES[1], "^"),
        ("Cofactor N/O within 3.5 Å of a nitro O", polar_mask & (l.cat == "Cofactor (FMN/FAD/...)"), SERIES[2], "s")]
fig, axs = plt.subplots(3, 2, figsize=(11.5, 15.5))
ox, oy = 1.23 * np.cos(np.radians(62.5)), 1.23 * np.sin(np.radians(62.5))
for r_i, (lab, m, colr, mk) in enumerate(rows):
    for ax, (xc, yc, yl, ttl) in zip(axs[r_i], [("lx", "ly", "y: in plane (Å)", "top view"), ("lx", "lz", "z: out of plane (Å)", "side view (edge-on)")]):
        rest = l[~polar_mask]
        ax.scatter(rest[xc], rest[yc], s=7, color=GRAY, alpha=0.45, linewidth=0, zorder=1)
        s_ = l[m]
        ax.scatter(s_[xc], s_[yc], s=40, color=colr, marker=mk, edgecolor=SURF, linewidth=0.9, zorder=4, alpha=0.95)
        if yc == "ly":
            for sgn in (1, -1): ax.plot([0, ox], [0, sgn * oy], color=INK, lw=2.5, zorder=5)
            ax.plot([-1.47, 0], [0, 0], color=INK, lw=2.5, zorder=5)
            ax.text(-0.15, -0.35, "N", fontsize=9, color=INK, ha="right", zorder=6)
            ax.text(ox + 0.12, oy, "O", fontsize=9, color=INK, va="center"); ax.text(ox + 0.12, -oy, "O", fontsize=9, color=INK, va="center")
            ax.text(-1.55, 0.2, "C", fontsize=9, color=INK, ha="right")
        else:
            ax.plot([0], [0], "o", color=INK, ms=4, zorder=6); ax.axhline(0, color=INK, lw=1.2, zorder=5, alpha=0.6)
        ax.set_aspect("equal"); ax.set_xlim(-4.6, 4.6); ax.set_ylim(-4.6, 4.6)
        ax.set_xlabel("x: along substituent → N axis (Å)"); ax.set_ylabel(yl)
        ax.set_title(f"{lab} (n={len(s_)}) – {ttl}", fontsize=10)
fig.suptitle("Where contacting atoms sit around the nitro group (all nitro groups superposed)", x=0.01, ha="left", fontsize=14, fontweight="bold", y=0.995)
fig.tight_layout(rect=(0, 0.035, 1, 0.985))
fig.text(0.01, 0.025, f"{loc.groupby(['pdb_id','nitro_ligand','nitro_group']).ngroups} nitro groups, each in its own frame: origin = N, x = substituent→N bond, z = nitro-plane normal. "
         "Grey = all other atoms ≤ 4.5 Å from N (context).\nOne row per partner type; a polar atom is assigned by its distance to the nearest nitro O. Atoms of the nitro-bearing residue excluded.",
         fontsize=8.5, color=INK2, va="top")
save(fig, "fig4_local_frame")

# ---------------------------------------------------------------- Fig 5: by enzyme family
fam_order = (prot.groupby("family").size().sort_values().index.tolist())
short_name = {f: f.split(" (")[0] for f in fam_order}
fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 5.2), sharey=True)
for ax, col, xl, t in [(a, "d_O_X", "distance O ··· X (Å)", "Distance, protein partners"), (b, "ang_N_O_X", "angle N–O ··· X (°)", "Approach angle at O, protein partners")]:
    for i, f in enumerate(fam_order):
        s = prot[prot.family == f]
        ax.scatter(s[col], i + rng.uniform(-0.22, 0.22, len(s)), s=26, color=BLUE, edgecolor=SURF, linewidth=0.8, alpha=0.9, zorder=3)
        if len(s): ax.plot([s[col].median()] * 2, [i - 0.33, i + 0.33], color=INK, lw=2, zorder=4)
    ax.set_title(t); ax.set_xlabel(xl + ";  bar = median"); ax.grid(axis="y", visible=False)
a.set_yticks(range(len(fam_order)))
a.set_yticklabels([f"{short_name[f]}  (n={int((prot.family == f).sum())})" for f in fam_order])
b.axvspan(110, 140, color=GRAY, alpha=0.2, lw=0)
a.set_xlim(2.35, 3.55)
fig.suptitle("Protein contacts to the nitro O by enzyme family", x=0.01, ha="left", fontsize=14, fontweight="bold", y=1.0)
fig.text(0.01, -0.02, "Protein N/O atoms only (no water, no cofactor); n = contacts. Families are dominated by repeated entries of the same enzyme (e.g. Kemp eliminase variants, PETN reductase).\n" + FOOT,
         fontsize=8.5, color=INK2, va="top")
fig.tight_layout(); save(fig, "fig5_by_family")
print("figures written:", sorted(os.listdir("figures")))
