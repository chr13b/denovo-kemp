#!/usr/bin/env python3
"""Assemble figures/data/data.json (+ designs.csv) for the design-vs-activity charts.

Every kcat/KM is taken from theozyme/THEOZYME_ORIGIN.md section 3b (which cites the papers).
Residue evidence tags:  x = observed in a TSA/substrate complex in this collection,
                        d = from the design papers (design numbering), m = modelled pose.
Run make_geometry.py first (writes data/geometry.csv).
"""
import csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__))

# group: evo = directed evolution in the loop; comp = computational only (no library screening)
# start/end kinds: design | best | derived (bound computed by me from a stated fold-change) | lower (stated lower bound) | none
ROWS = [
    # ---- directed evolution
    dict(id="HG3", name="HG3 → HG3.17", group="evo", base="asp", start=125, startKind="design", end=2.3e5, endKind="best",
         scaffold="xylanase (1GOR)", baseRes="Asp127", src="Start: JACS 2024 abstract (HG3 = 125). End: web-search summary of Blomberg 2013; not verified in the paper text.",
         note="17 rounds of evolution. HG-3 measured 425 in Privett 2012 under other conditions."),
    dict(id="KE59", name="KE59", group="evo", base="glu", start=160, startKind="design", end=60430, endKind="best",
         scaffold="IGPS (1A53)", baseRes="Glu230", src="Khersonsky 2012 PNAS Table 1 (R13-3/11H, 5-nitrobenzisoxazole).",
         note="13 rounds. With the more reactive 5,7-dichlorobenzisoxazole the same variant reaches 573,090."),
    dict(id="KE70", name="KE70", group="evo", base="his", start=126, startKind="design", end=55000, endKind="best",
         scaffold="DERA (1JCL)", baseRes="His17–Asp45", src="Khersonsky 2011 JMB Table 1 (design 126 ± 4; best listed R6 4/8B 57,300 ± 6,140; text ≈5.5×10⁴).",
         note="Computational redesign plus evolution; the text of that paper gives the design as ≈80."),
    dict(id="KE07", name="KE07", group="evo", base="glu", start=12, startKind="design", end=2600, endKind="best",
         scaffold="HisF (1THF)", baseRes="Glu", src="Khersonsky 2012 PNAS (12 → 2.6×10³).", note="Other passages give the design as ≤10."),
    # ---- computational only
    dict(id="D27X", name="Des27.7 + one extra residue", group="comp", base="asp", start=12700, startKind="design", end=1e5, endKind="lower",
         scaffold="IGPS chimera", baseRes="Asp162", src="Listov 2025 abstract: efficiency 'more than 10⁵' after designing one further residue.",
         note="Lower bound. Which residue was changed was not read."),
    dict(id="TIME", name="KempTIM + ensemble redesign", group="comp", base="asp", start=20, startKind="derived", end=32000, endKind="best",
         scaffold="de novo TIM barrel", baseRes="Asp24", src="CANVAS paper abstract (10.1038/s41589-026-02250-w): >1,600-fold gain to 32,000.",
         note="Parent value ≤20 is derived (32,000 ÷ 1,600), not stated."),
    dict(id="HGE", name="HG3 ensemble design", group="comp", base="asp", start=125, startKind="design", end=31250, endKind="derived",
         scaffold="xylanase (1GOR)", baseRes="Asp127", src="JACS 2024 abstract: designs improved 100–250-fold over HG3 (125).",
         note="End value derived as 125 × 250, an upper bound; best exact value not read."),
    dict(id="TIMB", name="KempTIM best direct design", group="comp", base="asp", start=None, startKind="none", end=21000, endKind="best",
         scaffold="de novo TIM barrel", baseRes="Asp24", src="CANVAS paper abstract: most active of nine lid designs.", note="No parent value."),
    dict(id="KEE", name="KE70 ensemble design", group="comp", base="his", start=57, startKind="design", end=14250, endKind="derived",
         scaffold="DERA (1JCL)", baseRes="His17–Asp45", src="JACS 2024 abstract: KE70 = 57, designs improved 100–250-fold.",
         note="End value derived as 57 × 250, an upper bound."),
    dict(id="D27", name="Des27 → Des27.7", group="comp", base="asp", start=130, startKind="design", end=12700, endKind="best",
         scaffold="IGPS chimera", baseRes="Asp162", src="Listov 2025 (full text): 130 → 12,700; kcat 2.85 s⁻¹.", note="Seven mutations; crystal structure 9HVB."),
    dict(id="D61", name="Des61 → best redesign", group="comp", base="unk", start=210, startKind="design", end=3600, endKind="best",
         scaffold="IGPS chimera", baseRes="base not retrieved", src="Listov 2025 (full text): 210 → 3,600; kcat 0.85 s⁻¹.", note=""),
    dict(id="A532", name="1A53-2 (design only)", group="comp", base="glu", start=64.2, startKind="design", end=None, endKind="none",
         scaffold="IGPS (1A53)", baseRes="Glu178", src="Privett 2012 PNAS Table 1 (kcat 0.09 s⁻¹, KM 1.4 mM).",
         note="No optimised variant in this collection."),
]

# catalytic-constellation matrix (best activity = same end value as above; evidence tags in the strings)
MATRIX = [
    dict(name="HG3.17", sub="xylanase 1GOR", base="asp", baseTxt="Asp127 ·x", pi="Trp44 ·x  5.1 → 6.3 Å (HG3 → HG3.17)",
         polar="Met237 NH ·x, Gln50 (HG3.17)", side="N3", best=2.3e5, bestNote="HG3.17 (value not verified in paper text)"),
    dict(name="KE59", sub="IGPS 1A53", base="glu", baseTxt="Glu230 ·d  (Glu231 ·x)", pi="Trp109 ·d  Trp110 3.6 Å ·x",
         polar="Ser179, Ser210 ·d", side="n/d", best=60430, bestNote="R13-3/11H, 5-nitrobenzisoxazole"),
    dict(name="KE70", sub="DERA 1JCL", base="his", baseTxt="His17–Asp45 ·d", pi="Tyr48 ·d  Phe48 3.8 Å (8FOR) ·x",
         polar="Ser138 ·d", side="N3 (His)", best=55000, bestNote="evolved + computational redesign"),
    dict(name="KempTIM", sub="de novo TIM barrel", base="asp", baseTxt="Asp24 ·x", pi="none within 5.5 Å ·x",
         polar="Gly97 NH, Val71 O ·x", side="N1", best=32000, bestNote="best of the family, a related variant (9TZD is KempTIM1)"),
    dict(name="Des27.7", sub="IGPS chimera", base="asp", baseTxt="Asp162 ·x", pi="Phe113 3.9 Å ·m",
         polar="none (omitted by design)", side="C3 ·m", best=12700, bestNote="computational only; +1 residue reaches >10⁵"),
    dict(name="KE07", sub="HisF 1THF", base="glu", baseTxt="Glu ·d", pi="not retrieved", polar="not retrieved", side="no complex",
         best=2600, bestNote="evolved"),
    dict(name="1A53-2", sub="IGPS 1A53", base="glu", baseTxt="Glu178 ·x", pi="Trp110 + Trp210 ·x", polar="Arg53 NE, Ala81 O (6NW4) ·x",
         side="N1", best=64.2, bestNote="design only"),
    dict(name="KABLE", sub="de novo, 127 aa", base="asp", baseTxt="Asp49 ·x", pi="none within 5.5 Å ·x", polar="Trp20 NE1 ·x",
         side="N3", best=None, bestNote="no kinetics found"),
]

geom = list(csv.DictReader(open(os.path.join(HERE, "data", "geometry.csv"))))
for g in geom:
    for k in ("kcat_KM", "base_dist", "pi_dist", "pi_angle"): g[k] = float(g[k])

out = dict(rows=ROWS, matrix=MATRIX, geometry=geom)
json.dump(out, open(os.path.join(HERE, "data", "data.json"), "w"), indent=1, ensure_ascii=False)
with open(os.path.join(HERE, "data", "designs.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["design", "group", "scaffold", "catalytic_base", "start_kcat_KM", "start_kind", "end_kcat_KM", "end_kind", "source", "note"])
    for r in ROWS:
        w.writerow([r["name"], r["group"], r["scaffold"], r["baseRes"], r["start"], r["startKind"], r["end"], r["endKind"], r["src"], r["note"]])
print(len(ROWS), "design rows,", len(MATRIX), "matrix rows,", len(geom), "geometry rows")
