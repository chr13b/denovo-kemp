#!/usr/bin/env python3
"""Step 7: report/index.html (recommendations, Pareto plot, score breakdown, sensitivity, caveats). Numbers come from the pickles."""
import pickle, json, os, html, math, collections
from common import *

rows = pickle.load(open(os.path.join(HERE, "report", "rows.pkl"), "rb")); byid = {r["id"]: r for r in rows}
retro = json.load(open(os.path.join(HERE, "report", "retrospective.json")))
SCH = ["default", "geometry_only", "evidence_heavy", "base_first", "ignore_nitro"]
e = html.escape

REC = [  # id, title, role, why, risks
    ("T00001", "1 · KE59-type minimal theozyme", "Recommended first",
     "Best default score and the only candidate in the top 25 under four of the five weightings. Base and stacker were seen together in one crystal structure (KE59 R13, 3UZJ). Glu O to N3 is 2.67 Å and in the TSA plane; Trp110 stacks at 3.76 Å with a 16° tilt. The KE59 lineage reached 60,430 M⁻¹s⁻¹ with 5-nitrobenzisoxazole.",
     "The source ligand (3UZJ) is plain benzotriazole with no nitro group, so nothing in the template touches the nitro position. The structure is from an evolved variant, not the original KE59 design."),
    ("T00003", "2 · The same, with a backbone-NH nitro anchor", "Recommended: stabiliser version",
     "Adds a Met backbone N–H taken from the nitro data (6SRY, HG series): N···O 2.86 Å, angle 102°, 52° above the nitro plane, which reproduces the source contact (2.82 Å, 106°, 47°). Best-scoring candidate that has a stabiliser; Met backbone NH is also the contact seen in the Kemp eliminase entries.",
     "Des27.7, the best computational-only enzyme, has no polar contact at all, so the benefit of this anchor is untested. The Met comes from a different protein family and was never seen with this base and stacker."),
    ("T00015", "3 · Des27.7 as designed (Asp162 + Phe113)", "Recommended: computational-only reference",
     "The theozyme of the best published computational-only design (12,700 M⁻¹s⁻¹; crystal structure 9HVB confirms Asp162). Highest base-geometry score (0.95) and top rank under base-first weighting.",
     "The substrate pose is a Rosetta model built with the same constraint file used to score it, so the 0.95 is partly circular. Phe113 stacks less tightly (4.23 Å, 19°) than Trp110, and it falls to rank 239 under geometry-only weighting."),
    ("T00031", "4 · Hybrid: Asp162 + Trp110 + Met NH", "Recommended: geometry-optimised hybrid",
     "On the Pareto front. Keeps the Des27.7 base geometry, swaps in the tighter Trp110 stack (3.76 Å) and adds the Met NH anchor. Rank 3 under base-first and 21 under geometry-only.",
     "A chimera: components come from three proteins and were never seen together. It drops to rank 487 when evidence dominates."),
    ("T01327", "5 · HG-series native set (Asp127 + Trp44 + Met237 NH)", "Reference, not a first pick",
     "All three components co-observed in one crystal structure (6SRY), from the lineage with the highest published activity (≈2.3×10⁵, HG3.17; value not verified in the paper text). Evidence score 1.0, rank 9 when evidence dominates.",
     "Geometrically loose: Trp44 is 4.46 Å away with a 31° tilt and 2.9 Å lateral offset (π score 0.39), so it ranks 5,063rd on geometry. The retrospective check (below) shows this lineage's activity does not come from clean static geometry."),
    ("T00094", "6 · His–Asp dyad (KE70-type) + Phe stack", "Alternative base chemistry",
     "The only dyad template (8FOR, KE70-core): His ND1 to N3 3.02 Å, Asp to His 2.75 Å, Phe49 stacked at 3.92 Å (5° tilt). KE70 reached 55,000 M⁻¹s⁻¹ after nine rounds.",
     "One template only, so no variation within the class. Rank 94 by default and 1,136 under base-first weighting; the dyad geometry scores 0.75."),
    ("T00072", "7 · Asp162 + Phe49 (geometry-first)", "Optional",
     "Rank 2 under both geometry-only and base-first weightings: the Des27.7 base geometry with a tight, nearly parallel Phe stack (3.92 Å, 5° tilt).",
     "Another chimera with the same circularity caveat on the base, and weak evidence support (rank 1,743 when evidence dominates)."),
    ("T00089", "8 · HG Asp127 + Phe49", "Optional",
     "HG-type syn Asp127 (N···O 2.54 Å) paired with the same tight Phe stack: tests whether the HG base would work with a tighter stacker than Trp44.",
     "Never observed together. Middling under every weighting (ranks 89–406)."),
]
def bar(v, lab):
    return f'<div class="bar"><span class="bl">{lab}</span><span class="bt"><span class="bf" style="width:{(v or 0)*100:.0f}%"></span></span><span class="bv">{"–" if v in (None, "") else f"{float(v):.2f}"}</span></div>'

cards = ""
for tid, title, role, why, risk in REC:
    r = byid[tid]; ranks = " · ".join(f'{k.replace("_", " ")}: <b>{r["rank_"+k]:,}</b>' for k in SCH)
    comp = f'<table class="ct"><tr><td>Base</td><td>{e(r["base"].replace("  ", " "))} <span class="m">{e(r["base_src"])} · {e(r["base_class"])}</span></td></tr><tr><td>π stacker</td><td>{e(r["pi"].replace("  ", " "))} <span class="m">{e(r["pi_src"])}</span></td></tr><tr><td>Nitro stabiliser</td><td>{e(r["nitro"])} <span class="m">{e(r["nitro_src"])}</span></td></tr></table>'
    cards += f'''<article class="card"><div class="img"><img src="img/{tid}.png" alt="{e(title)}" loading="lazy"></div><div class="body"><div class="role">{e(role)}</div><h3>{e(title)}</h3>
<div class="id">{tid} · rank {r["rank"]:,} of {len(rows):,} · total {r["T_default"]:.3f}</div>{comp}
<div class="bars">{bar(r["s_base"], "base")}{bar(r["s_pi"], "π stack")}{bar(r["s_nitro"] if r["s_nitro"] != "" else None, "nitro")}{bar(r["s_compat"], "fit")}{bar(r["s_evidence"], "evidence")}</div>
<p class="geo">{e(r["geometry"])}</p><p><b>Why.</b> {e(why)}</p><p><b>Risks.</b> {e(risk)}</p><div class="rk">Rank under each weighting: {ranks}</div></article>'''

# Pareto plot (inline SVG)
W, H, ml, mr, mt, mb = 900, 520, 72, 30, 20, 56
G = lambda v: ml + (v - 0.1) / (1.0 - 0.1) * (W - ml - mr); E_ = lambda v: H - mb - (v - 0.0) / 1.0 * (H - mt - mb)
seen = set(); dots = ""
for r in rows:
    k = (round(r["T_geometry_only"], 2), round(r["s_evidence"], 2))
    if k in seen: continue
    seen.add(k); dots += f'<circle cx="{G(k[0]):.1f}" cy="{E_(k[1]):.1f}" r="2.2" class="gp"/>'
front = []; be = -1
for r in sorted(rows, key=lambda r: (-r["T_geometry_only"], -r["s_evidence"])):
    if r["s_evidence"] > be + 1e-9: front.append(r); be = r["s_evidence"]
fp = " ".join(f'{G(r["T_geometry_only"]):.1f},{E_(r["s_evidence"]):.1f}' for r in front)
cls = lambda r: "asp" if r["base_class"].startswith("Asp") else ("glu" if r["base_class"].startswith("Glu") else "his")
lab = {"T00001": (10, -10, "start"), "T00003": (10, 14, "start"), "T00015": (-10, 18, "end"), "T00031": (10, -12, "start"), "T01327": (10, -8, "start"), "T00094": (10, 14, "start"), "T00072": (-12, 4, "end"), "T00089": (-10, -10, "end"), "T00650": (-10, 18, "end")}
pts = ""
for tid, (dx, dy, an) in lab.items():
    r = byid[tid]; x, y = G(r["T_geometry_only"]), E_(r["s_evidence"]); isf = r in front
    pts += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" class="pt {cls(r)}"/><text x="{x+dx:.1f}" y="{y+dy:.1f}" text-anchor="{an}" class="pl">{tid}</text>'
grid = "".join(f'<line x1="{ml}" x2="{W-mr}" y1="{E_(v):.1f}" y2="{E_(v):.1f}" class="gl"/><text x="{ml-8}" y="{E_(v)+4:.1f}" text-anchor="end" class="tk">{v:.1f}</text>' for v in (0, .2, .4, .6, .8, 1.0))
grid += "".join(f'<line x1="{G(v):.1f}" x2="{G(v):.1f}" y1="{mt}" y2="{H-mb}" class="gl"/><text x="{G(v):.1f}" y="{H-mb+18}" text-anchor="middle" class="tk">{v:.1f}</text>' for v in (.2, .4, .6, .8, 1.0))
pareto = f'<svg viewBox="0 0 {W} {H}" class="pareto" role="img" aria-label="Scatter of geometric quality against published evidence for all valid theozymes with the Pareto front highlighted">{grid}{dots}<polyline points="{fp}" class="front"/>{pts}<text x="{(ml+W-mr)/2}" y="{H-12}" text-anchor="middle" class="ax">Geometric quality (geometry-only total, no kinetics)</text><text transform="rotate(-90 18 {(mt+H-mb)/2})" x="18" y="{(mt+H-mb)/2}" text-anchor="middle" class="ax">Published evidence (lineage kcat/KM + co-observation)</text></svg>'

# base-class x stabiliser-class heat table
cells = collections.defaultdict(lambda: None)
for r in rows:
    k = (r["base_class"], r["nitro_class"])
    if cells[k] is None or r["T_default"] > cells[k]["T_default"]: cells[k] = r
bcs = sorted({r["base_class"] for r in rows}); ncs = ["none", "backbone NH", "side chain"]
heat = '<table class="heat"><tr><th>Best total score</th>' + "".join(f"<th>{n}</th>" for n in ncs) + "</tr>"
for b in sorted(bcs, key=lambda b: -max(cells[(b, n)]["T_default"] for n in ncs if cells[(b, n)])):
    heat += f"<tr><th>{e(b)}</th>"
    for n in ncs:
        c = cells[(b, n)]
        heat += f'<td style="--v:{(c["T_default"]-0.45)/0.5:.2f}">{c["T_default"]:.3f}<span>{c["id"]} · rank {c["rank"]:,}</span></td>' if c else "<td>–</td>"
    heat += "</tr>"
heat += "</table>"
retro_tab = "".join(f'<tr><td>{e(t["lineage"])}</td><td>{t["geometry_only"]:.3f}</td><td>{t["kcat_KM"]:,.0f}</td></tr>' for t in retro["table"])

page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kemp theozyme candidates</title>
<style>
:root{{color-scheme:light;--bg:#f7f6f3;--card:#fcfcfb;--t1:#0b0b0b;--t2:#52514e;--t3:#6f6e69;--line:#e6e5e1;--a:#2a78d6;--o:#eb6834;--g:#1baf7a;--gray:#b9b8b2}}
@media (prefers-color-scheme:dark){{:root{{color-scheme:dark;--bg:#121211;--card:#1a1a19;--t1:#fff;--t2:#c3c2b7;--t3:#9a9990;--line:#2c2c2a;--a:#3987e5;--o:#d95926;--g:#199e70;--gray:#4a4a46}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--t1);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}main{{max-width:1040px;margin:0 auto;padding:28px 16px 72px}}
h1{{font-size:25px;margin:0 0 6px;letter-spacing:-.01em}}h2{{font-size:17px;margin:34px 0 8px}}h3{{margin:2px 0 4px;font-size:17px}}.lede{{color:var(--t2);max-width:75ch;margin:0 0 18px}}
.box{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0}}.rules{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}}.rules div{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-size:14px}}.rules b{{display:block;color:var(--t2);font-size:12px;margin-bottom:2px}}
.card{{display:grid;grid-template-columns:minmax(260px,420px) 1fr;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin:14px 0}}@media(max-width:820px){{.card{{grid-template-columns:1fr}}}}
.img img{{width:100%;border-radius:8px;border:1px solid var(--line);background:#fff}}.role{{font-size:12px;color:var(--a);font-weight:650;text-transform:uppercase;letter-spacing:.05em}}.id{{color:var(--t3);font-size:13px;margin-bottom:6px}}
.ct{{border-collapse:collapse;font-size:13.5px;margin:4px 0 8px}}.ct td{{padding:2px 10px 2px 0;vertical-align:top}}.ct td:first-child{{color:var(--t2);white-space:nowrap}}.m{{color:var(--t3);font-size:12.5px}}
.bars{{margin:6px 0}}.bar{{display:grid;grid-template-columns:62px 1fr 38px;gap:8px;align-items:center;font-size:12.5px}}.bl{{color:var(--t2)}}.bt{{height:8px;background:var(--line);border-radius:4px;overflow:hidden}}.bf{{display:block;height:100%;background:var(--a);border-radius:4px}}.bv{{text-align:right;color:var(--t2)}}
.geo{{font:12px ui-monospace,Menlo,monospace;color:var(--t2);margin:6px 0}}.rk{{font-size:12.5px;color:var(--t2)}}.card p{{margin:6px 0;font-size:14px}}
.pareto{{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:12px}}.gp{{fill:var(--gray);opacity:.55}}.gl{{stroke:var(--line);stroke-width:1}}.tk{{fill:var(--t2);font-size:11px}}.ax{{fill:var(--t2);font-size:12px}}.pl{{fill:var(--t1);font-size:11.5px;font-weight:600}}
.front{{fill:none;stroke:var(--t2);stroke-width:1.5;stroke-linejoin:round}}.pt{{stroke:var(--card);stroke-width:2}}.pt.asp{{fill:var(--a)}}.pt.glu{{fill:var(--o)}}.pt.his{{fill:var(--g)}}
table{{border-collapse:collapse;font-size:13.5px}}th,td{{border-bottom:1px solid var(--line);padding:5px 10px;text-align:left}}th{{color:var(--t2);font-weight:600}}.heat td{{background:color-mix(in srgb,var(--a) calc(var(--v)*60%),var(--card));min-width:130px}}.heat td span{{display:block;font-size:11px;color:var(--t2)}}
ul{{padding-left:20px}}li{{margin:4px 0}}.legend{{font-size:13px;color:var(--t2);display:flex;gap:16px;flex-wrap:wrap;margin:6px 0}}.legend i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}}
</style></head><body><main>
<h1>Kemp eliminase theozyme candidates</h1>
<p class="lede">{len(rows):,} sterically valid theozymes assembled from observed components around a 6-nitrobenzotriazole transition-state analog, scored, ranked and checked for stability under five different weightings. Eight variants are recommended below, with the reasons and the risks.</p>
<div class="rules"><div><b>Rule 1 · centre</b>6-nitrobenzotriazole (TSA) in the middle; it stands in for the substrate.</div><div><b>Rule 2 · base</b>Asp/Glu carboxylate, or a His–Asp dyad, taken from published TSA-complex structures.</div><div><b>Rule 3 · π stack</b>Trp, Phe or Tyr ring on a face of the TSA, from the same structures.</div><div><b>Rule 4 · optional nitro anchor</b>Residue, distance and angles chosen from the nitro-enzyme data and placed by superposing the observed nitro group.</div></div>

<h2>What to take away</h2>
<div class="box"><ul>
<li><b>The ranking depends on what you weigh.</b> Only 1 of {len(rows):,} candidates (T00001) stays in the top 25 under four of five weightings. Geometry-only favours the Des27.7 Asp162 base; evidence-heavy favours the HG and KE59 lineages. That is why the recommendations come from the Pareto front, not from one total.</li>
<li><b>The score does not predict activity.</b> Scoring each lineage's native base + stacker pair on geometry alone, with no kinetics, gives Spearman ρ = {retro["rho"]:.2f} against the lineages' best kcat/KM (n = {retro["n"]}). The most active lineage (HG) has the loosest stack. Treat the score as "how close to clean, observed contacts", not as predicted activity.</li>
<li><b>Stabilising the nitro group is optional, not obviously helpful.</b> A backbone-NH anchor (Met, Gly, Thr) fits the geometry well and is the most Kemp-relevant contact, but the best computational-only design has no polar contact at all.</li>
<li><b>N1-side bases are not recommended.</b> They sit 4.5–4.7 Å from N3 and rank 631 or lower. If the real substrate bound like the TSA does there, the base could not reach the C3–H.</li></ul></div>

<h2>Recommended variants</h2>
<div class="legend"><span><i style="background:var(--a)"></i>Asp base</span><span><i style="background:var(--o)"></i>Glu base</span><span><i style="background:var(--g)"></i>His–Asp dyad</span><span>Images: TSA yellow, base blue (dyad Asp light blue), stacker orange, stabiliser green. Red dashes: base contacts, black: nitro contact, orange: π centroid.</span></div>
{cards}

<h2>Geometry against evidence</h2>
<p class="lede">Every valid candidate (grey) with the Pareto front (line): no candidate beats a front point on both axes.</p>{pareto}

<h2>Best score by base and stabiliser class</h2>{heat}

<h2>Retrospective check</h2>
<p class="lede">Geometry-only score of each lineage's native base + stacker pair (both from one crystal structure, no stabiliser) against that lineage's best kcat/KM. ρ = {retro["rho"]:.2f}, n = {retro["n"]}: no relationship, so the score is not a predictor.</p>
<table><tr><th>Lineage</th><th>Geometry-only score</th><th>Best kcat/KM (M⁻¹s⁻¹)</th></tr>{retro_tab}</table>

<h2>How the score is built</h2>
<table><tr><th>Component</th><th>What it measures</th><th>Target and source</th></tr>
<tr><td>base (0.35)</td><td>Carboxylate approach: O···N distance, angle at N, in-plane torsion, carboxylate orientation. Dyad: His N···N3 and Asp O···His N.</td><td>Listov 2025 Rosetta constraint (<code>theozime.cst</code>: 127.6°, 120°, 180°) with 2× its tolerances; distance 2.6 Å, the observed TSA-complex median; syn and anti both accepted. N1-side bases ×0.75.</td></tr>
<tr><td>π (0.25)</td><td>Ring-centroid distance, tilt, lateral offset to the TSA.</td><td>3.8 Å, ≤10° tilt, ≤1.5 Å offset: the tight stackers in the crystal structures (IGPS Trp110/Trp210, KE70 Phe).</td></tr>
<tr><td>nitro (0.10, only if present)</td><td>Typicality of d(O···X), angle N–O···X and elevation within its residue/contact class, class frequency, Kemp-entry support, aromatic-nitro source.</td><td>Median ± robust spread of the 82 H-bond contacts in <code>nitro_enzymes/motif_table.csv</code>.</td></tr>
<tr><td>fit (0.10)</td><td>Steric compatibility; clashes below 2.2 Å are rejected, overlaps penalised.</td><td>van der Waals-style limits, 3.3 Å (2.6 Å for polar pairs).</td></tr>
<tr><td>evidence (0.20)</td><td>Best published kcat/KM of the lineage(s) of base and stacker, plus whether components were seen together.</td><td><code>kemp_eliminase/theozyme/THEOZYME_ORIGIN.md</code> section 3b; modelled structures ×0.85.</td></tr></table>
<p class="lede">The total is the weighted mean of the components present. The weights are my choices, not fitted to data. Four alternative weightings test how much that matters.</p>

<h2>Limitations</h2>
<div class="box"><ul>
<li>All components are real observations, but each pairing is a hypothesis: most candidates combine residues from different proteins that were never seen together.</li>
<li>The Des27.7 substrate pose is a Rosetta model built with the constraint file used for scoring, so its base score is partly circular. The crystal structure 9HVB confirms Asp162's position but has no ligand.</li>
<li>HG-series activity (≈2.3×10⁵) comes from a web summary of Blomberg 2013, not the paper text. Lineage activities come from different papers and conditions.</li>
<li>Only one His–Asp dyad template exists, so that class has no internal variation. The nitro data are redundant (many copies per entry) and mostly from non-Kemp enzymes.</li>
<li>Theozymes are static idealisations. The HG3 lineage's activity depends on conformational ensembles (Otten 2020), which none of this captures.</li></ul></div>
</main></body></html>'''
open(os.path.join(HERE, "report", "index.html"), "w").write(page)
print("report written;", len(page) // 1024, "KB")
