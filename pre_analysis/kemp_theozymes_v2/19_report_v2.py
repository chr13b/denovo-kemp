#!/usr/bin/env python3
"""Step 19: report/index.html for v2. Every number is read from the pickles / summary.json written by steps 15-17."""
import csv, html, json, math, os, pickle
import numpy as np
from lib2 import *

e = html.escape
final = pickle.load(open(os.path.join(HERE2, "report", "final.pkl"), "rb")); picked = {cd["id"]: (slot, cd) for slot, desc, cd in pickle.load(open(os.path.join(HERE2, "report", "picked.pkl"), "rb"))}
S = json.load(open(os.path.join(HERE2, "report", "summary.json"))); SCH = list(json.load(open(os.path.join(HERE2, "schemes.json"))))
real = list(csv.DictReader(open(os.path.join(HERE2, "real_substrate_contacts.csv"))))
grid = lambda c: c["sampled"] and not c["src"].endswith("~"); root = lambda c: c["id"].split("~")[0]
def lab(q): return f'{q["res"]} {q["resid"]}' + ("*" if grid(q) else ("~" if q["sampled"] else "")) + f' <span class="m">{e(q["src"].rstrip("~"))}</span>'

REC = [
 ("V00001", "1 · HG-lineage full set", "Recommended first",
  "Asp127 base, Trp44 stacked on the nitro group, Met237 backbone N–H to the nitro oxygen, Gln50 donor to the ring-oxygen side: the active-site composition of HG3.17 and its relatives. Rank 1 of 3,402 distinct observed combinations under the default and evidence-heavy weightings and rank 5 under substrate-heavy. With the real substrate the C3–H points at the base (H···O 1.48 Å, 160°).",
  "A composite of lineage parts, not one observed site: Trp44 is placed as in HG-2 (3NYD); in HG3.17-lineage crystals (6SRY) Trp44 sits 3.7 Å off the nitro and would score 0.10. Both donors are small perturbations (≤12°, ≤0.25 Å) of observed ones. The HG3.17 activity (≈2.3×10⁵) is from a web summary. Geometry-only it ranks 162nd."),
 ("V00009", "2 · The same without the nitro donor", "Recommended: simpler version",
  "Asp127 + nitro-stacking Trp44 + Gln50 leaving-group donor. Rank 3 of 3,402 by default, 3 under substrate-heavy, 7 under evidence-heavy. Drops the Met contact whose benefit is the least certain.",
  "Same composite caveat as 1. The Gln50 donor adds little on its own: across 430 matched pairs a leaving-group donor raised the total in 66% of cases by a median of only 0.008."),
 ("V00023", "3 · KE59-type minimal (Glu231 + Trp110 on the ring)", "Recommended: second family",
  "The most robust on the real-substrate check: best proton-transfer geometry of any observed base (C3–H···O 1.58 Å at 164°, score 0.98), rank 1 under substrate-heavy weighting. Both parts come from one crystal structure (KE59 R13, 3UZJ); Trp110 stacks on the ring at 3.76 Å with a 16° tilt. KE59 reached 60,430 M⁻¹s⁻¹.",
  "The source ligand (3UZJ) is plain benzotriazole with no nitro, so the nitro region is empty. Structure is from an evolved variant. As a minimal theozyme it ranks 7th by default, below the HG composites."),
 ("V00128", "4 · KE59-type plus a Gln50 leaving-group donor", "Recommended: KE59 with the new contact",
  "Adds the Gln50 NE2 donor (3.1 Å, in plane) to the KE59-type pair. Distinct rank 21 by default and 9 under substrate-heavy.",
  "The donor comes from HG3.17 (7K4Z) and was never seen with an IGPS-fold base; the IGPS pocket may not accommodate it."),
 ("V00236", "5 · Minimal HG-type (Asp127 + nitro-stacking Trp44)", "Rules-only reference",
  "Meets rules 1–3 only, with the stacker on the nitro group: scores 0.899 against 0.795 for the same base with a ring stacker, so idea 4 matters most for this base.",
  "Distinct rank 39; the optional contacts in 1 and 2 score higher. Same Trp44 caveat as 1."),
 ("V00367", "6 · Sandwich: ring Phe49 + nitro Trp44 + Gln50", "Optional",
  "One aromatic on each site (Phe49 from KE70 on the ring, Trp44 on the nitro group). Distinct rank 59.",
  "None of the 10,411 observed sandwich candidates reaches the top 25 distinct combinations: with the π score a mean over stackers, a second stacker cannot raise it, and the extra residue only adds clash risk."),
 ("V10561", "7 · Des27.7-type base (Asp162) + Phe48 nitro stack + Met NH + Gln50", "Optional: geometry end of the front",
  "Highest geometry-only rank among observed-component candidates (1), on the Pareto front. Des27.7 is the best computational-only design (12,700 M⁻¹s⁻¹).",
  "The Asp162 pose is a Rosetta model built from the same constraint file used for scoring, so its geometry score is partly circular. Evidence rank 1,745; overall distinct rank 209."),
 ("V13877", "8 · His–Asp dyad (KE70-type) + Phe48 nitro stack", "Alternative base chemistry",
  "The only dyad template (8FOR). With the real substrate the His N sits 2.0 Å from C3–H at 146° and needs no retraction (0.04 Å), a more relaxed fit than the carboxylates.",
  "One template, no variation within the class. Distinct rank 287 by default."),
 ("V00189", "9 · A donor seen with the real substrate (His123, KSI 7EPO)", "Optional: real-substrate-derived",
  "Replaces the Met N–H with His123 NE2, which donates to the nitro oxygen in the real-substrate KSI complex (2.75 Å, 150°). Distinct rank 30.",
  "KSI is a different enzyme, and the substrate in that complex is not in a productive arrangement (see below)."),
 ("V00552", "10 · Grid-sampled Glu base", "Exploratory: no precedent",
  "A Glu carboxylate placed on the parameter grid (scores 0.9+ on base geometry), with Trp44 nitro stack, Met NH and Gln50 as in 1. Shows what continuous sampling adds when the base is free to move.",
  "No crystal precedent and a base score built from the same targets it is judged on. Evidence score is low by design. Not recommended before an observed variant has been tried."),
 ("V64285", "11 · Control: N1-side base (KempTIM1 Asp24)", "Rejected by the substrate check",
  "A TSA complex with the carboxylate on the ring-oxygen side. With the real substrate the C3–H···O distance is 5.7 Å at 22°: the C–H points away from the base.",
  "Included to show the crosscheck working. Rank 64,285 of 84,271."),
]
def bar(v, lab_):
    return f'<div class="bar"><span class="bl">{lab_}</span><span class="bt"><span class="bf" style="width:{(v or 0)*100:.0f}%"></span></span><span class="bv">{"–" if v is None else f"{v:.2f}"}</span></div>'
cards = ""
for vid, title, role, why, risk in REC:
    if vid not in picked: continue
    slot, cd = picked[vid]; sc, sb = cd["sc"], cd["sub"]
    comp = "".join(f'<tr><td>{n}</td><td>{lab(q)}</td></tr>' for n, q in zip([{"base": "Base", "ring": "Stacker (TSA ring)", "npi": "Stacker (nitro)", "hb": "Nitro donor", "lg": "Leaving-group donor"}[q["kind"]] for q in cd["group"]], cd["group"]))
    dr = cd.get("drank"); rk = " · ".join(f'{s.replace("_", " ")}: <b>{dr[s]:,}</b>' for s in SCH) if dr else "not ranked in the observed pool (contains a grid-sampled component or an N1-side control)"
    cards += f'''<article class="card"><div class="img"><img src="img/{vid}.png" alt="{e(title)}" loading="lazy"><div class="cap">TSA yellow, real substrate gray; red: base contact, green: C3–H···O, black: donors, orange dashed: π centroid.</div></div>
<div class="body"><div class="role">{e(role)}</div><h3>{e(title)}</h3><div class="id">{vid} · default rank {cd["rank"]["default"]:,} of {len(final):,} · total {cd["tot"]["default"]:.3f}</div>
<table class="ct">{comp}</table><div class="bars">{bar(sc["base"], "base")}{bar(sc["pi"], "π stack")}{bar(sc["subs"], "substrate")}{bar(sc["fit"], "fit")}{bar(sc["evidence"], "evidence")}{bar(sc["hb"], "nitro don.")}{bar(sc["lg"], "LG donor")}</div>
<p class="geo">real substrate: C3–H···O {sb["h_o"]:.2f} Å at {sb["ang"]:.0f}° · retraction for a ground-state fit {sb["retraction"]:.2f} Å · proton-transfer score {sb["pt"]:.2f}</p>
<p><b>Why.</b> {e(why)}</p><p><b>Risks.</b> {e(risk)}</p><div class="rk">Rank among 3,402 distinct observed combinations: {rk}</div></div></article>'''

# scatter: distinct observed combinations, geometry-only total vs evidence
obs = [c for c in final if not any(grid(q) for q in c["group"])]
best = {}
for c in obs:
    k = (root(c["group"][0]),) + tuple(sorted(root(q) for q in c["group"][1:]))
    if k not in best or c["tot"]["default"] > best[k]["tot"]["default"]: best[k] = c
W, H, ml, mr, mt, mb = 900, 480, 72, 30, 20, 56
Gx = lambda v: ml + (v - 0.5) / 0.5 * (W - ml - mr); Ey = lambda v: H - mb - v * (H - mt - mb)
dots = "".join(f'<circle cx="{Gx(c["tot"]["geometry_only"]):.1f}" cy="{Ey(c["sc"]["evidence"]):.1f}" r="2.3" class="gp"/>' for c in best.values() if c["tot"]["geometry_only"] >= 0.5)
pts = ""
lab_off = {"V00001": (10, -8, "start"), "V00009": (-10, -8, "end"), "V00023": (10, 14, "start"), "V00128": (10, 14, "start"), "V10561": (-10, -8, "end"), "V13877": (10, 14, "start"), "V00236": (-10, 14, "end")}
for vid, (dx, dy, an) in lab_off.items():
    if vid in picked:
        c = picked[vid][1]; x, y = Gx(c["tot"]["geometry_only"]), Ey(c["sc"]["evidence"])
        pts += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" class="pt"/><text x="{x+dx:.1f}" y="{y+dy:.1f}" text-anchor="{an}" class="pl">{vid}</text>'
grid_l = "".join(f'<line x1="{ml}" x2="{W-mr}" y1="{Ey(v):.1f}" y2="{Ey(v):.1f}" class="gl"/><text x="{ml-8}" y="{Ey(v)+4:.1f}" text-anchor="end" class="tk">{v:.1f}</text>' for v in (0, .2, .4, .6, .8, 1))
grid_l += "".join(f'<line x1="{Gx(v):.1f}" x2="{Gx(v):.1f}" y1="{mt}" y2="{H-mb}" class="gl"/><text x="{Gx(v):.1f}" y="{H-mb+18}" text-anchor="middle" class="tk">{v:.1f}</text>' for v in (.5, .6, .7, .8, .9, 1.0))
scatter = f'<svg viewBox="0 0 {W} {H}" class="pareto" role="img" aria-label="Geometry-only total against evidence for 3,402 distinct observed theozyme combinations, recommended variants labelled">{grid_l}{dots}{pts}<text x="{(ml+W-mr)/2}" y="{H-12}" text-anchor="middle" class="ax">Geometric quality (geometry-only total, no kinetics)</text><text transform="rotate(-90 18 {(mt+H-mb)/2})" x="18" y="{(mt+H-mb)/2}" text-anchor="middle" class="ax">Published evidence</text></svg>'

# tables
sb = S["subs_by_base"]; rows_sub = ""
for k, v in sb.items():
    if k.startswith("sampled"): continue
    p = k.split(" | "); rows_sub += f'<tr><td>{e(p[1])} {e(p[3])} <span class="m">{p[0]}</span></td><td>{p[2]}</td><td>{v["H_O"]:.2f}</td><td>{v["ang"]:.0f}°</td><td>{v["retraction"]:.2f}</td><td>{v["subs"]:.2f}</td></tr>'
rows_real = "".join(f'<tr><td>{e(r["pdb"])}<br><span class="m">{e(r["enzyme"])}</span></td><td>{e(r["nearest_base"].replace("deg", "°"))}</td><td>{e(r["nitro_contacts"])}</td><td>{e(r["o1_contacts"])}</td></tr>' for r in real)
t = S["top25_distinct"]; q = {k: S[f"quality_{k}"] for k in ("base", "ring", "hb", "lg")}; cmp_ = S["components"]
n_comp = lambda kind, typ: cmp_.get(f"{kind}|{typ}", 0)
trp = S["trp44_ring_vs_nitro"]; pert = S["perturbation_delta"]

page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kemp theozymes v2</title>
<style>
:root{{color-scheme:light;--bg:#f7f6f3;--card:#fcfcfb;--t1:#0b0b0b;--t2:#52514e;--t3:#6f6e69;--line:#e6e5e1;--a:#2a78d6;--gray:#b9b8b2}}
@media (prefers-color-scheme:dark){{:root{{color-scheme:dark;--bg:#121211;--card:#1a1a19;--t1:#fff;--t2:#c3c2b7;--t3:#9a9990;--line:#2c2c2a;--a:#3987e5;--gray:#4a4a46}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--t1);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}main{{max-width:1060px;margin:0 auto;padding:28px 16px 72px}}
h1{{font-size:25px;margin:0 0 6px}}h2{{font-size:17px;margin:34px 0 8px}}h3{{margin:2px 0 4px;font-size:17px}}.lede{{color:var(--t2);max-width:78ch;margin:0 0 16px}}
.box{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0}}.grid4{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}}.grid4 div{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-size:14px}}.grid4 b{{display:block;color:var(--t2);font-size:12px;margin-bottom:2px}}
.card{{display:grid;grid-template-columns:minmax(260px,430px) 1fr;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin:14px 0}}@media(max-width:820px){{.card{{grid-template-columns:1fr}}}}
.img img{{width:100%;border-radius:8px;border:1px solid var(--line);background:#fff}}.cap{{font-size:11.5px;color:var(--t3);margin-top:4px}}.role{{font-size:12px;color:var(--a);font-weight:650;text-transform:uppercase;letter-spacing:.05em}}.id{{color:var(--t3);font-size:13px;margin-bottom:6px}}
.ct{{border-collapse:collapse;font-size:13.5px;margin:4px 0 8px}}.ct td{{padding:2px 10px 2px 0;vertical-align:top;border:0}}.ct td:first-child{{color:var(--t2);white-space:nowrap}}.m{{color:var(--t3);font-size:12.5px}}
.bars{{margin:6px 0}}.bar{{display:grid;grid-template-columns:78px 1fr 36px;gap:8px;align-items:center;font-size:12.5px}}.bl{{color:var(--t2)}}.bt{{height:8px;background:var(--line);border-radius:4px;overflow:hidden}}.bf{{display:block;height:100%;background:var(--a);border-radius:4px}}.bv{{text-align:right;color:var(--t2)}}
.geo{{font:12px ui-monospace,Menlo,monospace;color:var(--t2);margin:6px 0}}.rk{{font-size:12.5px;color:var(--t2)}}.card p{{margin:6px 0;font-size:14px}}
.pareto{{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:12px}}.gp{{fill:var(--gray);opacity:.6}}.gl{{stroke:var(--line);stroke-width:1}}.tk{{fill:var(--t2);font-size:11px}}.ax{{fill:var(--t2);font-size:12px}}.pl{{fill:var(--t1);font-size:11.5px;font-weight:600}}.pt{{fill:var(--a);stroke:var(--card);stroke-width:2}}
table{{border-collapse:collapse;font-size:13.5px}}th,td{{border-bottom:1px solid var(--line);padding:5px 10px;text-align:left;vertical-align:top}}th{{color:var(--t2);font-weight:600}}.tw{{overflow-x:auto}}ul{{padding-left:20px}}li{{margin:5px 0}}.methods li{{margin:9px 0}}.methods code{{font-size:12.5px}}.reading ul{{margin:6px 0 0}}
</style></head><body><main>
<h1>Kemp theozymes v2: leaving-group donors, nitro stackers, continuous sampling</h1>
<p class="lede">This report compares {len(final):,} candidate theozymes. A theozyme here is a small set of residues placed around the 6-nitrobenzotriazole transition-state analog (TSA, our stand-in for the substrate): a catalytic base, an aromatic stacker, and optional hydrogen-bond donors. Each candidate is also tested against a model of the real substrate, 5-nitro-1,2-benzisoxazole.</p>
<div class="box reading"><b>Reading this report</b><ul>
<li><b>Components</b> are the residues a theozyme is built from. Each has one of three sources: <b>observed</b> (a real residue from a crystal structure), <b>perturbed</b> (marked ~: an observed residue nudged by up to 12° and 0.25 Å) or <b>grid-sampled</b> (marked *: a real side-chain conformation placed at a computed position that no crystal structure contains).</li>
<li><b>Ranks</b> are among 3,402 <b>distinct combinations</b> (unique residue sets, ignoring tiny perturbations) built from observed and perturbed components only, unless stated otherwise.</li>
<li><b>Evidence</b> is how much published activity, and co-occurrence in one structure, backs a candidate's components. <b>Retraction</b> is how far the base must move back from the substrate's C3 for the real substrate to fit without clashes.</li></ul></div>
<div class="grid4"><div><b>Idea 1 · leaving-group donor</b>A hydrogen-bond donor beside the ring-oxygen side of the TSA, where negative charge builds as the ring opens. {n_comp("lg","observed")} observed examples, e.g. Gln50 in HG3.17.</div><div><b>Idea 4 · nitro stacker</b>An aromatic ring stacked on the nitro group instead of, or as well as, on the TSA ring. {n_comp("npi","observed")} observed examples from the nitro-enzyme data.</div><div><b>Idea 7 · beyond observed positions</b>{n_comp("base","grid-sampled")} grid-sampled bases and {n_comp("ring","grid-sampled")} grid-sampled ring stackers, plus {n_comp("hb","perturbed")+n_comp("lg","perturbed")+n_comp("npi","perturbed")} perturbed copies of observed donors and stackers.</div><div><b>Idea 9 · real-substrate check</b>Each candidate is re-tested with the real substrate in place of the TSA: does the C3–H point at the base, and does the substrate fit without clashes?</div></div>

<h2>What to take away</h2>
<div class="box"><ul>
<li><b>Treating Trp44 as a nitro stacker changes the HG picture.</b> Forced into the ring-stacker slot its π score was 0.39 (v1); as a nitro stacker (3NYD placement) it is 0.99, and the HG set rises from rank 1,327 to rank 1. But the HG3.17-lineage crystals place Trp44 further from the nitro (3.7 Å lateral offset), so the top candidate is a composite of parts from related structures, not a single observed site.</li>
<li><b>The real substrate fits the N3-side bases and rejects the N1-side ones.</b> N3-side observed bases put C3–H 1.2–2.0 Å from the base oxygen at 111–179° and the base must be moved back 0.4–0.8 Å for the real substrate to fit (see table); every N1-side base gives H···O 5.4–5.7 Å at 22–31° (proton-transfer score 0.00: the C–H points away from the base).</li>
<li><b>None of the three real-substrate crystal complexes shows a productive arrangement</b> (below), so the crosscheck is a model check, not validation against a structure.</li>
<li><b>Each new contact adds a small, measurable amount.</b> A Gln50-type leaving-group donor raised the total in {S["lg_effect"]["frac_up"]*100:.0f}% of {S["lg_effect"]["n"]} matched pairs (median +{S["lg_effect"]["median_delta"]:.3f}); sandwiches (a stacker on both the ring and the nitro group) never reached the top 25 distinct combinations; {t["with_lg"]} of the top 25 contain a leaving-group donor and {t["with_npi"]} a nitro stacker.</li>
<li><b>Grid-sampled components cannot be judged on geometry.</b> They score near 1.0 (bases {q["base"]["grid_median"]:.2f}, stackers {q["ring"]["grid_median"]:.2f}) because they are built from the scoring targets; the observed medians are {q["base"]["observed_median"]:.2f} and {q["ring"]["observed_median"]:.2f}. They carry no evidence, so none appears in the recommended set before the observed ones.</li></ul></div>

<h2>Recommended variants</h2>{cards}

<h2>Geometry against evidence</h2><p class="lede">3,402 distinct observed combinations (the best variant of each). Recommended variants are labelled; the top-left corner needs both geometry and evidence.</p>{scatter}

<h2>Cross-check with the real substrate</h2>
<p class="lede">The real substrate (H5J) superposes on the TSA with 0.045 Å RMSD (C3 lies 0.11 Å from N3). For each candidate the base is tested for proton transfer (H···O, C–H···O angle) and, because TSA geometry is compressed relative to a ground-state complex, how far it must retract along C3→O for the substrate to fit without clashes.</p>
<div class="tw"><table><tr><th>Observed base</th><th>Side</th><th>H···O (Å)</th><th>C–H···O</th><th>Retraction (Å)</th><th>Substrate score</th></tr>{rows_sub}</table></div>
<p class="lede" style="margin-top:14px">Real-substrate crystal complexes, superposed on the same frame (<code>real_substrate_contacts.csv</code>):</p>
<div class="tw"><table><tr><th>Complex</th><th>Nearest base candidate to C3</th><th>Nitro contacts</th><th>Ring-oxygen (O1) contacts</th></tr>{rows_real}</table></div>
<ul><li><b>6DNJ (KE07 round 5):</b> no carboxylate or His within 5 Å of C3, and the nearest aromatic ring is 5.8 Å from the benzo ring; the substrate sits away from any base.</li><li><b>7EPO (KSI):</b> Glu127 is 2.75 Å from O1 (the N1 side); to its nearest oxygen the C3–H···O angle is 45° with H···O 4.05 Å; Trp48 NE1 donates to O1 (2.8 Å) and His123 NE2 to the nitro (2.75 Å). Not a Kemp-productive pose, but a real set of donors.</li><li><b>7Y9J (P450 BM3):</b> no base near C3; Tyr76 stacks at 5.3 Å and Lys439 NZ donates to the nitro.</li></ul>

<h2>What changed from v1</h2>
<div class="tw"><table><tr><th>Item</th><th>v1</th><th>v2</th></tr>
<tr><td>Components</td><td>15 bases, 17 ring stackers, 88 nitro donors</td><td>see the component table below</td></tr>
<tr><td>Score components</td><td>base, π, nitro, fit, evidence</td><td>adds the real-substrate check and a leaving-group term; six weightings</td></tr>
<tr><td>Best theozyme</td><td>Glu231 + Trp110 (T00001)</td><td>HG composite (V00001); the v1 winner is V00023, rank 7 of 3,402 distinct</td></tr>
<tr><td>Candidates</td><td>16,650</td><td>{len(final):,}</td></tr></table></div>
<p class="lede" style="margin-top:14px">Component libraries in v2 (the counts the generator chooses from):</p>
<div class="tw"><table><tr><th>Component</th><th>Observed</th><th>Perturbed copies (~)</th><th>Grid-sampled (*)</th></tr>
<tr><td>Base (carboxylate, or His–Asp dyad)</td><td>{n_comp("base","observed")}: 15 from TSA complexes, 1 Glu from the KSI complex</td><td>0</td><td>{n_comp("base","grid-sampled")} (70 Asp, 70 Glu)</td></tr>
<tr><td>Ring stacker (Trp/Phe/Tyr on the TSA ring)</td><td>{n_comp("ring","observed")}</td><td>0</td><td>{n_comp("ring","grid-sampled")} (50 each of Trp, Phe, Tyr)</td></tr>
<tr><td>Nitro stacker (aromatic on the nitro group)</td><td>{n_comp("npi","observed")}</td><td>{n_comp("npi","perturbed")}</td><td>0</td></tr>
<tr><td>Nitro donor (hydrogen-bond donor to the nitro)</td><td>{n_comp("hb","observed")}: 88 from the nitro data, 3 from real-substrate complexes</td><td>{n_comp("hb","perturbed")}</td><td>0</td></tr>
<tr><td>Leaving-group donor (ring-oxygen side)</td><td>{n_comp("lg","observed")}</td><td>{n_comp("lg","perturbed")}</td><td>0</td></tr></table></div>

<h2>Limitations</h2>
<div class="box"><ul>
<li>Weights are my choices. Observed candidates are ranked within their own pool because grid-sampled ones are scored against the targets they were built from. Geometry-only ranks of the recommended variants are low (e.g. rank 162 of 3,402 for V00001); the recommendations rest on the combination of evidence and the substrate check.</li>
<li>The "~" donors are perturbations (≤12°, ≤0.25 Å) and the top candidates are partly selected from them; across {pert["n"]} perturbed templates the median score change was {pert["median"]:+.3f} ({pert["frac_up"]*100:.0f}% up, best {pert["max"]:+.3f}), so this is mild selection, not systematic optimisation.</li>
<li>The substrate check is a model: the real substrate is placed by the TSA overlay and the base is retracted rigidly. It does not model the transition state or the protein's response.</li>
<li>Des27 substrate poses are Rosetta models built with the constraint file used for scoring (circular). HG3.17 activity is from a web summary. One dyad template exists.</li>
<li>The v1 retrospective result still applies: geometry scores did not predict lineage activity (ρ = −0.10, n = 5).</li></ul></div>
<h2>Methods</h2>
<ol class="methods">
<li><b>Common frame.</b> Every structure was superposed on the TSA of 7K4Q chain A (6-nitrobenzotriazole, 1.28 Å) using its nine ring atoms plus the nitro nitrogen (0.01–0.06 Å RMSD; 36 TSA complexes, plus the 2 modelled Des27 substrate complexes). The real substrate (ideal geometry of CCD H5J) was superposed on the same atoms, with C3 mapped to N3, N2 to N2 and the ring oxygen to N1 (0.045 Å RMSD).</li>
<li><b>Observed components.</b> From those complexes and 3 real-substrate complexes (6DNJ, 7EPO, 7Y9J): a base is an Asp/Glu carboxylate oxygen or a His nitrogen within 3.6 Å of N3 (or N1), with a His–Asp dyad needing an Asp oxygen within 3.4 Å of the other His nitrogen; a ring stacker is a Trp/Phe/Tyr ring within 6.2 Å of the TSA ring and tilted ≤45°; a leaving-group donor is an N–H or O–H within 3.6 Å of N1 (backbone carbonyls and carboxylates excluded). Copies within 0.6 Å side-chain RMSD (0.8 Å for donors) were merged, keeping the best resolution. Nitro donors and nitro stackers come from <code>nitro_enzymes/motif_table.csv</code> (82 hydrogen-bond and 14 π observations): each source nitro group was superposed on the TSA nitro group in both oxygen assignments, and a placement was kept only if it reproduced the tabulated distance (within 0.2 Å) or height and offset (within 0.3 and 0.5 Å) and did not clash with the TSA.</li>
<li><b>Grid sampling.</b> A rotamer library was clustered (0.5 Å) from about 9,600 Asp, Glu, Trp, Phe and Tyr residues in the project structures (494 conformations). For bases, 432 target carboxylate groups were generated around N3 (distance 2.45–2.85 Å, two angles, two torsions, syn/anti); for stackers, 270 target rings above the TSA (two faces, height 3.4–4.2 Å, nine lateral positions, five tilts, twelve in-plane orientations). Each rotamer was superposed rigidly on each target (247,080 base and 660,960 stacker placements); placements scoring ≥0.8 (bases) or ≥0.5 (stackers) without TSA clashes were clustered (1.0 and 1.3 Å) and capped per residue type.</li>
<li><b>Perturbation.</b> Each observed nitro donor, leaving-group donor and nitro stacker was rotated by 4–12° about its contact atom and shifted by up to 0.25 Å at random (seeded), up to 2, 3 and 2 accepted copies respectively, keeping the contact distance in range and avoiding TSA clashes.</li>
<li><b>Scores</b> (each 0–1; Gaussian penalties on deviation from a target):
<div class="tw"><table><tr><th>Score</th><th>Targets</th></tr>
<tr><td>Base</td><td>Carboxylate: O···N3 2.6 Å (σ 0.3), angle at N3 127.6° (σ 10), angle at O 120° (σ 12), in-plane torsion 180° (σ 15), carboxylate in the TSA plane, syn or anti (σ 20, half weight). Angles follow the Rosetta constraint of Listov 2025 with roughly doubled tolerances. Dyad: His N···N3 3.0 Å, Asp O···His N 2.75 Å. N1-side bases ×0.75.</td></tr>
<tr><td>Ring stacker</td><td>Centroid distance 3.8 Å (σ 0.5), tilt ≤10°, lateral offset ≤1.5 Å (penalised beyond).</td></tr>
<tr><td>Nitro stacker</td><td>Height above the nitro plane 3.5 Å (σ 0.4), lateral offset ≤2.0 Å, tilt ≤15°.</td></tr>
<tr><td>Nitro donor</td><td>Distance, angle N–O···X and elevation against the median and robust spread of its residue and contact class in the nitro data; plus class frequency, support in Kemp eliminase entries and aromatic-nitro source.</td></tr>
<tr><td>Leaving-group donor</td><td>N1···X 3.1 Å (σ 0.3), both angles at N1 125° (σ 20), elevation ≤25°; small credit for Kemp precedent.</td></tr>
<tr><td>Fit</td><td>Rejected if any atoms are closer than 2.2 Å (Cα···Cα 3.6 Å); otherwise a penalty for overlaps under 3.3 Å (2.6 Å for polar pairs).</td></tr>
<tr><td>Evidence</td><td>0.6 × best published kcat/KM of the base and stacker lineages (log scale, 64 to 2.3×10⁵ M⁻¹s⁻¹; 0.15 if grid-sampled) + 0.4 × co-observation (same structure 1, same lineage 0.5, otherwise 0); ×0.85 if a component is a model. Values: <code>kemp_eliminase/theozyme/THEOZYME_ORIGIN.md</code> §3b.</td></tr></table></div></li>
<li><b>Real-substrate check.</b> The substrate replaces the TSA. Proton transfer is scored from the C3–H···O distance (target 1.7 Å, σ 0.4) and angle (≥165°); ×0.2 for N1-side bases. Retraction is the distance the base must move along C3→O so that C3···O ≥3.0 Å and H···O ≥2.0 Å; the retracted base must then clash with neither the other residues nor the substrate. Substrate score = 0.5 × proton transfer + 0.3 × fit after retraction (reduced if the retraction exceeds 0.8 Å) + 0.2 × clash term.</li>
<li><b>Assembly.</b> All base × primary-stacker pairs were scored (156 × 214, 29,620 sterically valid). Optional contacts were then added in stages: a second stacker (best 30 of the other kind), a nitro donor (best 90, at most 6 per residue type), a leaving-group donor (best 24, at most 4 per type). After each stage about the top 1,700 candidates and the top 250 under each weighting were kept, plus the top 120 of every base class and 30 of every observed base, so no class was pruned by score alone. Result: {len(final):,} candidates.</li>
<li><b>Ranking.</b> The total is the weighted mean of the components present. Default weights: base 0.28, π 0.20, substrate 0.12, fit 0.08, evidence 0.17, nitro donor 0.05, leaving-group donor 0.05. Five alternatives were also ranked: geometry-only (evidence 0), evidence-heavy (0.45), base-first (base 0.50), substrate-heavy (substrate 0.32) and ignore-optional (donor weights 0). Candidates without grid-sampled components were ranked in their own pool, and by distinct combination (the best variant of each residue set).</li>
<li><b>Software.</b> Python 3 with numpy (scoring, sampling, ranking); PyMOL for superposition and images. Scripts <code>10</code>–<code>19</code> in this folder reproduce everything; see <code>README.md</code>.</li></ol>
</main></body></html>'''
open(os.path.join(HERE2, "report", "index.html"), "w").write(page); print("report written", len(page) // 1024, "KB")
