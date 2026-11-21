#!/usr/bin/env python3
"""Step 16: choose distinct variants for each design question and export them.

Per selected candidate two PDBs (candidates/):  <slot>__<id>.pdb         TS-like model: TSA in chain A
                                                <slot>__<id>__michaelis.pdb  the REAL substrate (chain S) with the base retracted along C3->O until
                                                                         the ground-state clash is gone (see subs_retraction_A)
Chains: A = 6NT (or S = substrate), B = base (C = dyad Asp), D = first stacker, E = second stacker, F = nitro H-bond donor, G = leaving-group donor.
"""
import csv, json, math, os, pickle
import numpy as np
from lib2 import *

final = pickle.load(open(os.path.join(HERE2, "report", "final.pkl"), "rb"))
OUT = os.path.join(HERE2, "candidates"); os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith(".pdb"): os.remove(os.path.join(OUT, f))
def grid(c): return c["sampled"] and not c["src"].endswith("~")
def root(c): return c["id"].split("~")[0]
def key(cd): return (root(cd["group"][0]),) + tuple(sorted(root(q) for q in cd["group"][1:]))
def kinds(cd, k): return [q for q in cd["group"] if q["kind"] == k]
def obs_only(cd): return not any(grid(q) for q in cd["group"])
def lin(cd, name): return name in cd["lin"]
FAM = {"HG": ("3NYD", "4BS0", "5RGA", "6SRY", "6SRW", "7K4Q", "7K4X", "7K4Z", "8RD5", "8USF", "8FOS"), "KE59": ("3UZJ", "3UXD", "3UZ5"), "DES": ("Des27.7_sub", "Des27_sub")}
def srcs(q): return q["src"].rstrip("~").split("_")[0] if not q["src"].startswith("Des") else q["src"].rstrip("~")
def basefam(cd):
    s = cd["group"][0]["src"]
    return "HG" if s in FAM["HG"] else "KE59" if s in FAM["KE59"] else "DES" if s.startswith("Des27") else "KE70" if s in ("8FOR", "3Q2D") else "other"
for cd in final: cd["bf"] = basefam(cd)
SCH = list(json.load(open(os.path.join(HERE2, "schemes.json"))))
_pool = [c for c in final if obs_only(c)]
for s_ in SCH:
    for i, c in enumerate(sorted(_pool, key=lambda c: -c["tot"][s_]), 1): c.setdefault("orank", {})[s_] = i
for c in _pool:
    r = list(c["orank"].values()); c["omean"] = float(np.mean(r)); c["ostable"] = sum(x <= 25 for x in r); c["oworst"] = max(r)
print(len(_pool), "observed-only candidates ranked within their own pool")
# distinct combinations: one entry per (base, stackers, donors) identity, best variant under each weighting; ranked per weighting
_best = {}
for c in _pool:
    k = key(c); b_ = _best.setdefault(k, {s_: -1 for s_ in SCH})
    for s_ in SCH: b_[s_] = max(b_[s_], c["tot"][s_])
for s_ in SCH:
    for i, k in enumerate(sorted(_best, key=lambda k: -_best[k][s_]), 1): _best[k][s_ + "_rank"] = i
for c in _pool:
    b_ = _best[key(c)]; c["drank"] = {s_: b_[s_ + "_rank"] for s_ in SCH}; c["dstable"] = sum(v <= 25 for v in c["drank"].values()); c["dmean"] = float(np.mean(list(c["drank"].values())))
print(len(_best), "distinct observed combinations")
def first(pred, pool=None):
    for cd in (pool or final):
        if pred(cd): return cd
    return None
SLOTS = [
    ("A_top_observed", "Top-ranked candidate built only from observed or lightly perturbed components", lambda c: obs_only(c)),
    ("B_minimal", "Best observed theozyme with no optional contacts (rules 1-3 only)", lambda c: obs_only(c) and len(c["group"]) == 2),
    ("B2_minimal_nitro_stack", "Best minimal theozyme whose only stacker sits on the nitro group (HG-type), no optional contacts", lambda c: obs_only(c) and len(c["group"]) == 2 and c["group"][1]["kind"] == "npi"),
    ("C_with_LG", "Best observed with a leaving-group (Gln50-type) donor and no nitro donor", lambda c: obs_only(c) and kinds(c, "lg") and not kinds(c, "hb")),
    ("D_full", "Best observed with every optional contact: nitro donor + leaving-group donor", lambda c: obs_only(c) and kinds(c, "lg") and kinds(c, "hb")),
    ("E_nitro_stack_only", "Best with the nitro-stacking aromatic as the only stacker (HG-type)", lambda c: obs_only(c) and len(kinds(c, "ring")) == 0 and len(kinds(c, "npi")) == 1 and len(c["group"]) > 2),
    ("F_sandwich", "Best sandwich: one stacker on the TSA ring and one on the nitro group", lambda c: obs_only(c) and kinds(c, "ring") and kinds(c, "npi")),
    ("G_KE59_type", "KE59-type base (Glu231) with a ring stacker, best of any optional contacts", lambda c: obs_only(c) and c["bf"] == "KE59" and kinds(c, "ring") and not kinds(c, "npi")),
    ("G2_KE59_plus_LG", "KE59-type base (Glu231) + ring stacker + leaving-group donor", lambda c: obs_only(c) and c["bf"] == "KE59" and kinds(c, "ring") and kinds(c, "lg") and not kinds(c, "npi") and not kinds(c, "hb")),
    ("H_Des27_type", "Des27.7-type base (Asp162), best of any stackers and contacts", lambda c: obs_only(c) and c["bf"] == "DES"),
    ("I_dyad", "His-Asp dyad (KE70-type), best of any stackers and contacts", lambda c: obs_only(c) and c["group"][0]["bkind"] == "dyad"),
    ("J_real_substrate_part", "Best candidate with a component taken from a real-substrate crystal complex (6DNJ / 7EPO / 7Y9J)", lambda c: any(q.get("real") for q in c["group"]) and c["group"][0]["side"] == "N3"),
    ("K_N1_mode", "Best N1-side (ring-oxygen-side) base, to show what the real-substrate check does to it", lambda c: c["group"][0]["side"] == "N1" and obs_only(c)),
    ("L_sampled_base", "Best with a grid-sampled carboxylate base and observed everything else", lambda c: grid(c["group"][0]) and all(not grid(q) for q in c["group"][1:])),
    ("M_sampled_ring", "Best with a grid-sampled ring stacker and an observed base", lambda c: not grid(c["group"][0]) and any(grid(q) for q in kinds(c, "ring")) and all(not grid(q) for q in c["group"] if q["kind"] != "ring")),
    ("N_all_sampled", "Best with both a sampled base and a sampled stacker (geometry-ideal, no precedent)", lambda c: grid(c["group"][0]) and any(grid(q) for q in kinds(c, "ring"))),
]
# Pareto front: geometry-only total vs evidence, restricted to candidates with no grid-sampled component
pts = sorted([c for c in final if obs_only(c)], key=lambda c: (-c["tot"]["geometry_only"], -c["sc"]["evidence"])); front, be = [], -1
for c in pts:
    if c["sc"]["evidence"] > be + 1e-9: front.append(c); be = c["sc"]["evidence"]
for i, c in enumerate(front, 1): SLOTS.append((f"P{i:02d}_pareto", f"Pareto front {i}/{len(front)} (observed components): geometry {c['tot']['geometry_only']:.3f} vs evidence {c['sc']['evidence']:.3f}", lambda x, cid=c["id"]: x["id"] == cid))

def fixhint(q):
    if q["kind"] in ("hb", "lg"): return "backbone N,CA,C,O" if q.get("contact") == "bb_NH" else "side chain + CA"
    return "side chain + CA"
def blocks_for(cd, sub_model=False):
    group = cd["group"]; b = group[0]; bl = []
    if not sub_model: bl.append(("A", 1, "6NT", True, [(k, TSA_EL[k].title(), v.tolist()) for k, v in TSA.items()]))
    else: bl.append(("S", 1, "5NB", True, [(n, SUBJ_EL[n].title(), x.tolist()) for n, x in SUB.items()]))
    ba = b["atoms"]
    if sub_model:
        base_atom = measure_base(b)["atom"]; X = np.array([a[2] for a in ba if a[0] == base_atom][0]); v = unit(X - SUB["C3"])
        need = max(0.0, 3.0 - d(SUB["C3"], X), 2.0 - d(SUB["H3"], X)); ba = [(n, e, (np.array(x) + v * need).tolist()) for n, e, x in ba]
    if b["bkind"] == "dyad":
        h = b["his_atoms"]; bl += [("B", 1, "HIS", False, [(a[0], a[1].title(), a[2]) for a in ba[:h]]), ("C", 1, b["res"].split("+")[1], False, [(a[0], a[1].title(), a[2]) for a in ba[h:]])]
    else: bl.append(("B", 1, b["res"], False, [(a[0], a[1].title(), a[2]) for a in ba]))
    chain = {"ring": ["D", "E"], "npi": ["D", "E"]}; pi_i = 0
    for q in group[1:]:
        if q["kind"] in ("ring", "npi"): ch = ["D", "E"][pi_i]; pi_i += 1
        else: ch = "F" if q["kind"] == "hb" else "G"
        bl.append((ch, 1, q["res"], False, [(a[0], a[1].title(), a[2]) for a in q["atoms"]]))
    return bl
SUBJ_EL = {a[0]: a[1] for a in json.load(open(os.path.join(T2, "substrate.json")))["atoms"]}
def label(q): return f'{q["res"]}{q["resid"]}{"*" if grid(q) else ("~" if q["sampled"] else "")}[{q["src"].rstrip("~")}]'
def export(cd, slot, tag, michaelis=False):
    sc, s = cd["sc"], cd["sub"]
    rem = [f'Kemp theozyme {cd["id"]}  default rank {cd["rank"]["default"]:,} of {len(final):,}  total {cd["tot"]["default"]:.3f}  [{slot}]',
           "components: " + "; ".join(f'{q["kind"]}:{label(q)}' for q in cd["group"]),
           "scores: " + " ".join(f'{k}={v:.2f}' for k, v in sc.items() if v is not None),
           f'real-substrate check: H3...O {s["h_o"]:.2f} A, C3-H...O {s["ang"]:.0f} deg, retraction needed {s["retraction"]:.2f} A, proton-transfer score {s["pt"]:.2f}',
           "* grid-sampled (no crystal precedent), ~ small perturbation of an observed template",
           "chains: A=6NT (or S=substrate) B=base C=dyad Asp D/E=stackers F=nitro donor G=leaving-group donor",
           "fix atoms for motif scaffolding: " + "; ".join(f'{q["res"]}: {fixhint(q)}' for q in cd["group"] if q["kind"] != "base")]
    if michaelis: rem.append(f'MICHAELIS MODEL: real substrate; base retracted {s["retraction"]:.2f} A along C3->O')
    write_pdb(os.path.join(OUT, f"{slot}__{cd['id']}{'__michaelis' if michaelis else ''}.pdb"), blocks_for(cd, michaelis), rem)

picked = []
for slot, desc, pred in SLOTS:
    cd = first(pred)
    if cd is None: print("slot", slot, "-> none"); continue
    picked.append((slot, desc, cd)); export(cd, slot, "ts"); export(cd, slot, "ts", michaelis=True)
# top 25 distinct observed
seen, top = set(), []
for cd in final:
    if not obs_only(cd): continue
    k = key(cd)
    if k in seen: continue
    seen.add(k); top.append(cd)
    if len(top) >= 25: break
for i, cd in enumerate(top, 1): export(cd, f"top{i:02d}_observed", "ts")
pickle.dump(picked, open(os.path.join(HERE2, "report", "picked.pkl"), "wb")); pickle.dump(top, open(os.path.join(HERE2, "report", "top_observed.pkl"), "wb"))
cols = ["slot", "id", "rank", "obs_rank_default", "obs_rank_geometry_only", "obs_rank_evidence_heavy", "obs_rank_substrate_heavy", "obs_rank_mean", "obs_stable_top25", "distinct_rank_default", "distinct_rank_geometry_only", "distinct_rank_evidence_heavy", "distinct_rank_substrate_heavy", "distinct_stable_top25", "total", "geometry_only", "evidence", "base", "pi", "hb", "lg", "s_base", "s_pi", "s_subs", "s_fit", "s_hb", "s_lg", "H3_O", "CHO_angle", "retraction", "description"]
with open(os.path.join(HERE2, "selected_variants_v2.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(cols)
    for slot, desc, cd in picked:
        b = cd["group"][0]; pis = [q for q in cd["group"] if q["kind"] in ("ring", "npi")]; hb = kinds(cd, "hb"); lg = kinds(cd, "lg"); sc = cd["sc"]
        w.writerow([slot, cd["id"], cd["rank"]["default"], cd.get("orank", {}).get("default", ""), cd.get("orank", {}).get("geometry_only", ""), cd.get("orank", {}).get("evidence_heavy", ""), cd.get("orank", {}).get("substrate_heavy", ""), round(cd.get("omean", 0), 1) if "omean" in cd else "", cd.get("ostable", ""), cd.get("drank", {}).get("default", ""), cd.get("drank", {}).get("geometry_only", ""), cd.get("drank", {}).get("evidence_heavy", ""), cd.get("drank", {}).get("substrate_heavy", ""), cd.get("dstable", ""), round(cd["tot"]["default"], 3), round(cd["tot"]["geometry_only"], 3), round(sc["evidence"], 3),
                    label(b), " + ".join(f'{label(q)}({"nitro" if q["kind"]=="npi" else "ring"})' for q in pis), label(hb[0]) if hb else "", label(lg[0]) if lg else "", round(sc["base"], 3), round(sc["pi"], 3), round(sc["subs"], 3), round(sc["fit"], 3),
                    "" if sc["hb"] is None else round(sc["hb"], 3), "" if sc["lg"] is None else round(sc["lg"], 3), round(cd["sub"]["h_o"], 2), round(cd["sub"]["ang"]), round(cd["sub"]["retraction"], 2), desc])
print(f'{"slot":24}{"id":8}{"rank":>7}{"distinct: def":>14}{"geo":>6}{"evid":>6}{"subs":>6}{"stab":>5}{"total":>7}  components')
for slot, desc, cd in picked:
    o = cd.get("drank", {})
    print(f'{slot:24}{cd["id"]:8}{cd["rank"]["default"]:>7}{o.get("default", "-"):>14}{o.get("geometry_only", "-"):>6}{o.get("evidence_heavy", "-"):>6}{o.get("substrate_heavy", "-"):>6}{cd.get("dstable", "-"):>5}{cd["tot"]["default"]:7.3f}  ' + " | ".join(f'{q["kind"]}:{label(q)}' for q in cd["group"]))
print(len(os.listdir(OUT)), "PDB files written")
