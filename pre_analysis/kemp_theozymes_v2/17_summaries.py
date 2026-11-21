#!/usr/bin/env python3
"""Step 17: measured effect of each new idea -> report/summary.json (and printed)."""
import json, pickle, collections, os
import numpy as np
from lib2 import *
final = pickle.load(open(os.path.join(HERE2, "report", "final.pkl"), "rb")); comps = json.load(open(os.path.join(T2, "components.json")))
grid = lambda c: c["sampled"] and not c["src"].endswith("~"); root = lambda c: c["id"].split("~")[0]
obs = [c for c in final if not any(grid(q) for q in c["group"])]
S = {}
cnt = collections.Counter((c["kind"], "grid-sampled" if grid(c) else ("perturbed" if c["sampled"] else "observed")) for c in comps)
S["components"] = {f"{k}|{t}": v for (k, t), v in sorted(cnt.items())}
S["n_final"], S["n_observed_only"] = len(final), len(obs)

# idea 4: the Trp44 case. Same atoms scored as ring stacker vs nitro stacker
rows = []
for c in comps:
    if c["kind"] == "ring" and c["res"] == "TRP" and c["resid"] in ("A44",) and not c["sampled"]:
        rows.append((c["id"], c["src"], round(score_ring(c), 3), round(score_npi(c), 3), round(measure_ring(c)["dist"], 2), round(measure_npi(c)["z"], 2), round(measure_npi(c)["lat"], 2)))
S["trp44_ring_vs_nitro"] = rows
print("Trp44 (HG) scored as TSA-ring stacker vs nitro stacker [id src ring-score nitro-score ring-dist nitro-z nitro-lat]:"); [print("  ", r) for r in rows]

# idea 1: effect of a leaving-group donor on identical base + stackers
def sig(c): return (root(c["group"][0]),) + tuple(sorted(root(q) for q in c["group"][1:] if q["kind"] in ("ring", "npi", "hb")))
best_with, best_without = {}, {}
for c in obs:
    k = sig(c); has = any(q["kind"] == "lg" for q in c["group"])
    d_ = best_with if has else best_without
    if k not in d_ or c["tot"]["default"] > d_[k]["tot"]["default"]: d_[k] = c
both = [k for k in best_with if k in best_without]
dl = [best_with[k]["tot"]["default"] - best_without[k]["tot"]["default"] for k in both]
S["lg_effect"] = dict(n=len(both), median_delta=float(np.median(dl)), frac_up=float(np.mean(np.array(dl) > 0)))
print(f"\nleaving-group donor added to the same base+stackers: {len(both)} combos, median change in total {np.median(dl):+.4f}, improved in {100*np.mean(np.array(dl)>0):.0f}%")
lg = collections.defaultdict(list)
for c in comps:
    if c["kind"] == "lg" and not c["sampled"]: lg[(c["res"], c["partner"], "real" if c["real"] else "TSA")].append(round(score_lg(c), 2))
S["lg_scores"] = {" ".join(k): v for k, v in lg.items()}; print("standalone leaving-group scores:", dict(lg))
# idea 4 effect: nitro stacker as the only stacker vs ring stacker, same base
def bestby(pred):
    r = [c for c in obs if pred(c)]; return max(r, key=lambda c: c["tot"]["default"]) if r else None
for fam, bs in (("HG Asp127", ("B02", "B03", "B05", "B06", "B08")), ("KE59 Glu231", ("B13", "B14"))):
    a = bestby(lambda c: c["group"][0]["id"] in bs and len(c["group"]) == 2 and c["group"][1]["kind"] == "ring")
    b = bestby(lambda c: c["group"][0]["id"] in bs and len(c["group"]) == 2 and c["group"][1]["kind"] == "npi")
    print(f"{fam}: best minimal with ring stacker {a['tot']['default']:.3f} ({a['group'][1]['res']}{a['group'][1]['resid']}) vs nitro stacker {b['tot']['default']:.3f} ({b['group'][1]['res']}{b['group'][1]['resid']})")
    S[f"minimal_{fam}"] = dict(ring=a["tot"]["default"], npi=b["tot"]["default"])
sand = [c for c in obs if len([q for q in c["group"] if q["kind"] in ("ring", "npi")]) == 2]
S["sandwich"] = dict(n=len(sand), best=max(c["tot"]["default"] for c in sand), best_rank=min(c["rank"]["default"] for c in sand))
print("sandwiches (observed):", S["sandwich"])

# idea 7: sampled vs observed single-component quality
for kind, fn in (("base", score_base), ("ring", score_ring), ("hb", score_hb), ("lg", score_lg)):
    o = [fn(c) for c in comps if c["kind"] == kind and not c["sampled"] and not vs_tsa_hard(c)]; sg = [fn(c) for c in comps if c["kind"] == kind and grid(c)]
    pt = [fn(c) for c in comps if c["kind"] == kind and c["sampled"] and not grid(c)]
    S[f"quality_{kind}"] = dict(observed_median=float(np.median(o)) if o else None, observed_max=float(max(o)) if o else None, n_obs=len(o), grid_median=float(np.median(sg)) if sg else None, grid_n=len(sg),
                               perturbed_median=float(np.median(pt)) if pt else None, perturbed_n=len(pt))
    print(f"{kind:5} observed n={len(o)} median {np.median(o) if o else float('nan'):.2f} max {max(o) if o else float('nan'):.2f} | grid-sampled n={len(sg)} median {np.median(sg) if sg else float('nan'):.2f} | perturbed n={len(pt)} median {np.median(pt) if pt else float('nan'):.2f}")
# perturbation vs its parent: does perturbing improve the score by selection?
par = {c["id"]: c for c in comps if not c["sampled"]}; ups = []
for c in comps:
    if c["sampled"] and c["src"].endswith("~"):
        p = par.get(c["id"].split("~")[0])
        if p and c["kind"] in ("hb", "lg", "npi"):
            fn = {"hb": score_hb, "lg": score_lg, "npi": score_npi}[c["kind"]]; ups.append(fn(c) - fn(p))
S["perturbation_delta"] = dict(n=len(ups), median=float(np.median(ups)), frac_up=float(np.mean(np.array(ups) > 0)), max=float(max(ups)))
print(f"perturbed vs parent template score: n={len(ups)} median change {np.median(ups):+.3f}, improved in {100*np.mean(np.array(ups)>0):.0f}%, max {max(ups):+.3f}")

# idea 9: real-substrate crosscheck by base class and for the observed bases
byb = collections.defaultdict(list)
for c in final: b = c["group"][0]; byb[(b["id"] if not grid(b) else "sampled " + b["res"], b["res"], b["side"], b["src"] if not grid(b) else "")].append(c)
S["subs_by_base"] = {}
for k, v in sorted(byb.items(), key=lambda kv: -np.median([x["sc"]["subs"] for x in kv[1]])):
    S["subs_by_base"][" | ".join(k)] = dict(n=len(v), H_O=float(np.median([x["sub"]["h_o"] for x in v])), ang=float(np.median([x["sub"]["ang"] for x in v])), retraction=float(np.median([x["sub"]["retraction"] for x in v])),
                                            pt=float(np.median([x["sub"]["pt"] for x in v])), subs=float(np.median([x["sc"]["subs"] for x in v])))
print("\nreal-substrate crosscheck by base:"); [print(f"  {k:48} n={v['n']:>6} H..O {v['H_O']:.2f} C-H..O {v['ang']:.0f} retract {v['retraction']:.2f} pt {v['pt']:.2f} subs {v['subs']:.2f}") for k, v in S["subs_by_base"].items() if not k.startswith("sampled") or True]
top = [c for c in obs][:300]
dist = {}
for c in sorted(obs, key=lambda c: c["rank"]["default"]):
    k = (root(c["group"][0]),) + tuple(sorted(root(q) for q in c["group"][1:]))
    if k not in dist: dist[k] = c
    if len(dist) >= 25: break
t25 = list(dist.values())
S["top25_distinct"] = dict(with_lg=sum(any(q["kind"] == "lg" for q in c["group"]) for c in t25), with_hb=sum(any(q["kind"] == "hb" for q in c["group"]) for c in t25),
                           with_npi=sum(any(q["kind"] == "npi" for q in c["group"]) for c in t25), sandwich=sum(len([q for q in c["group"] if q["kind"] in ("ring", "npi")]) == 2 for c in t25),
                           asp=sum(c["group"][0]["res"] == "ASP" for c in t25), glu=sum(c["group"][0]["res"] == "GLU" for c in t25))
print("\ntop-25 distinct observed combinations:", S["top25_distinct"])
json.dump(S, open(os.path.join(HERE2, "report", "summary.json"), "w"), indent=1, default=float)
