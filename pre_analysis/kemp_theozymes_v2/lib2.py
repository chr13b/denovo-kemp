"""v2 scoring library: component geometry, scores, clash test and the real-substrate crosscheck.

Component = dict(id, kind in {base, ring, npi, hb, lg}, res, resid, src, atoms=[(name, el, xyz)], plus kind-specific fields and provenance
(families, members, real, sampled, modelled)). Every score is in [0, 1].
"""
import json, csv, math, os
import numpy as np
from common2 import *

g = lambda z2: math.exp(-0.5 * z2)
def wrap180(x): return (x + 180) % 360 - 180
def adiff(a, b): return abs(wrap180(a - b))
def d(a, b): return float(np.linalg.norm(a - b))

# ---------------------------------------------------------------- fixed geometry: TSA and the real substrate in the common frame
TSA = {a["name"]: a["xyz"] for a in parse_pdb(os.path.join(V1T, "tsa_6NT.pdb"))}
TSA_EL = {a["name"]: a["el"] for a in parse_pdb(os.path.join(V1T, "tsa_6NT.pdb"))}
SUBJ = json.load(open(os.path.join(T2, "substrate.json"))); SUB = {a[0]: np.array(a[2]) for a in SUBJ["atoms"]}; SUB_EL = {a[0]: a[1] for a in SUBJ["atoms"]}
BIC = np.array([TSA[k] for k in CORE]); BIC_C, BIC_N = ring_frame(BIC)
NIT_N = TSA["NO1"]; NIT_NZ = unit(np.cross(TSA["O11"] - NIT_N, TSA["O21"] - NIT_N))
NSTAT = {(r["residue"], r["contact_type"]): r for r in csv.DictReader(open(os.path.join(V1T, "nitro_stats.csv")))}
TSA_XYZ = np.array(list(TSA.values())); TSA_NAMES = list(TSA.keys())
SUB_XYZ = np.array([SUB[k] for k in SUB]); SUB_NAMES = list(SUB.keys()); SUB_ISH = np.array([SUB_EL[k] == "H" for k in SUB])
POLAR = {"N", "O"}

def A(comp):   # numpy view of a component's atoms
    if "_a" not in comp:
        comp["_a"] = (np.array([a[2] for a in comp["atoms"]], float), np.array([a[1] in POLAR for a in comp["atoms"]]), [a[0] for a in comp["atoms"]])
    return comp["_a"]
def atom(comp, name):
    for a in comp["atoms"]:
        if a[0] == name: return np.array(a[2], float)
    return None

# ---------------------------------------------------------------- base
def measure_base(c):
    at = {a[0]: np.array(a[2]) for a in c["atoms"]}
    site, A2 = (TSA["N3"], TSA["C3A"]) if c["side"] == "N3" else (TSA["N1"], TSA["C7A"]); A3 = TSA["N2"]
    if c["bkind"] == "carboxylate":
        names = ("OD1", "OD2") if c["res"] == "ASP" else ("OE1", "OE2"); C = "CG" if c["res"] == "ASP" else "CD"; Bp = "CB" if c["res"] == "ASP" else "CG"
        o = min(names, key=lambda n: d(at[n], site)); O = at[o]
        return dict(d=d(O, site), angA=angle(A2, site, O), angB=angle(site, O, at[C]), torA=dihedral(A3, A2, site, O), torB=dihedral(site, O, at[C], at[Bp]), atom=o)
    hn = {n: at[n] for n in ("ND1", "NE2") if n in at}
    near = min(hn, key=lambda n: d(hn[n], site)); other = [n for n in hn if n != near][0]
    acid = [np.array(a[2]) for a in c["atoms"][c["his_atoms"]:] if a[0] in ("OD1", "OD2", "OE1", "OE2")]
    return dict(d=d(hn[near], site), d_dyad=min(d(x, hn[other]) for x in acid), angA=angle(A2, site, hn[near]), torA=dihedral(A3, A2, site, hn[near]), atom=near)
def score_base(c, m=None):
    m = m or measure_base(c)
    if c["bkind"] == "carboxylate":
        z = [((m["d"] - 2.6) / 0.3, 1.0), ((m["angA"] - 127.6) / 10, 1.0), ((m["angB"] - 120) / 12, 1.0), (adiff(m["torA"], 180) / 15, 1.0),
             (min(adiff(m["torB"], 180), adiff(m["torB"], 0)) / 20, 0.5)]   # carboxylate in plane: syn or anti both accepted
    else:
        z = [((m["d"] - 3.0) / 0.3, 1.0), ((m["d_dyad"] - 2.75) / 0.25, 1.0), ((m["angA"] - 127.6) / 15, 1.0), (adiff(m["torA"], 180) / 25, 1.0)]
    s = g(sum(w * x * x for x, w in z) / sum(w for _, w in z))
    return s * (0.75 if c["side"] == "N1" else 1.0)

# ---------------------------------------------------------------- ring stacker (on the TSA bicycle) and nitro stacker
def ring_xyz(c, ring_names):
    at = {a[0]: np.array(a[2]) for a in c["atoms"]}
    return np.array([at[n] for n in ring_names]) if all(n in at for n in ring_names) else None
def best_ring(c, ref_c, ref_n, key):
    best = None
    for ring in AR_RINGS[c["res"]]:
        P = ring_xyz(c, ring)
        if P is None: continue
        cen, nrm = ring_frame(P)
        if best is None or d(cen, ref_c) < best[0]: best = (d(cen, ref_c), cen, nrm)
    return best
def measure_ring(c):
    b = best_ring(c, BIC_C, BIC_N, "ring")
    if b is None: return None
    dist, cen, nrm = b; rel = cen - BIC_C
    return dict(dist=dist, tilt=math.degrees(math.acos(min(1, abs(float(nrm @ BIC_N))))), lat=float(np.linalg.norm(rel - (rel @ BIC_N) * BIC_N)), h=float(rel @ BIC_N))
def score_ring(c, m=None):
    m = m or measure_ring(c)
    if m is None: return 0.0
    zd, zt, zl = (m["dist"] - 3.8) / 0.5, max(0.0, m["tilt"] - 10) / 15, max(0.0, m["lat"] - 1.5) / 1.0
    return g((zd * zd + zt * zt + zl * zl) / 3)
def measure_npi(c):
    b = best_ring(c, NIT_N, NIT_NZ, "npi")
    if b is None: return None
    _, cen, nrm = b; rel = cen - NIT_N
    return dict(z=abs(float(rel @ NIT_NZ)), lat=float(np.linalg.norm(rel - (rel @ NIT_NZ) * NIT_NZ)), tilt=math.degrees(math.acos(min(1, abs(float(nrm @ NIT_NZ))))))
def score_npi(c, m=None):
    m = m or measure_npi(c)
    if m is None: return 0.0
    zz, zl, zt = (m["z"] - 3.5) / 0.4, max(0.0, m["lat"] - 2.0) / 0.8, max(0.0, m["tilt"] - 15) / 15
    return g((zz * zz + zl * zl + zt * zt) / 3)

# ---------------------------------------------------------------- nitro H-bond stabiliser and leaving-group stabiliser
def measure_hb(c):
    xn = c["partner"]; X = atom(c, xn)
    o = min(("O11", "O21"), key=lambda n: d(X, TSA[n]))
    v = X - TSA[o]
    return dict(d=d(X, TSA[o]), ang=angle(NIT_N, TSA[o], X), elev=abs(math.degrees(math.asin(max(-1, min(1, float(unit(v) @ NIT_NZ)))))), o=o)
def score_hb(c, m=None):
    m = m or measure_hb(c)
    st = NSTAT.get((c["res"], c["contact"]))
    if st is None: st = NSTAT.get((c["res"], "sidechain")) or NSTAT[("HIS", "sidechain")]
    z = [(m["d"] - float(st["d_med"])) / float(st["d_sd"]), (m["ang"] - float(st["ang_med"])) / float(st["ang_sd"]), (m["elev"] - float(st["elev_med"])) / float(st["elev_sd"])]
    geom = g(sum(x * x for x in z) / 3); freq = min(1.0, math.sqrt(float(st["share_of_all_hbonds"]) / 0.244))
    return 0.5 * geom + 0.2 * freq + 0.15 * (1.0 if c.get("kemp") else 0.0) + 0.15 * (1.0 if c.get("arom", True) else 0.6)
def measure_lg(c):
    X = atom(c, c["partner"]); N1, N2, C7A = TSA["N1"], TSA["N2"], TSA["C7A"]
    return dict(d=d(X, N1), a2=angle(N2, N1, X), a7=angle(C7A, N1, X), elev=abs(math.degrees(math.asin(max(-1, min(1, float(unit(X - N1) @ BIC_N)))))))
def score_lg(c, m=None):
    m = m or measure_lg(c)
    z = [(m["d"] - 3.1) / 0.3, (m["a2"] - 125) / 20, (m["a7"] - 125) / 20, max(0.0, m["elev"] - 25) / 20]
    freq = 1.0 if c["res"] in ("GLN", "HIS", "TRP", "ASN") else 0.8
    return 0.8 * g(sum(x * x for x in z) / 4) + 0.1 * (1.0 if c.get("kemp") else 0.0) + 0.1 * freq

# ---------------------------------------------------------------- clash tests (vectorised)
def pair_clash(c1, c2):
    X1, P1, n1 = A(c1); X2, P2, n2 = A(c2)
    D = np.linalg.norm(X1[:, None, :] - X2[None, :, :], axis=2)
    if D.min() < 2.2: return True, 9.0
    ca1 = [i for i, n in enumerate(n1) if n == "CA"]; ca2 = [j for j, n in enumerate(n2) if n == "CA"]
    for i in ca1:
        for j in ca2:
            if D[i, j] < 3.6: return True, 9.0
    lim = np.where(P1[:, None] & P2[None, :], 2.6, 3.3)
    return False, float((np.maximum(0, lim - D) ** 2).sum())
def vs_tsa_hard(c, allow_contact=()):
    X, P, names = A(c); D = np.linalg.norm(X[:, None, :] - TSA_XYZ[None, :, :], axis=2)
    return bool(D.min() < 2.1)
def clash_all(comps):
    pen = 0.0
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            h, p = pair_clash(comps[i], comps[j])
            if h: return True, 9.0
            pen += p
    return False, pen

# ---------------------------------------------------------------- real-substrate crosscheck
def substrate_check(comps):
    """The real substrate (5-nitro-1,2-benzisoxazole) replaces the TSA. Returns dict(pt, retract, retraction, clash_pen, hard, h_o, ang)."""
    C3, H3 = SUB["C3"], SUB["H3"]
    base = next(c for c in comps if c["kind"] == "base"); m = measure_base(base)
    X = atom(base, m["atom"])
    h_o, ang = d(H3, X), angle(C3, H3, X)
    pt = g((((h_o - 1.7) / 0.4) ** 2 + ((min(ang, 180) - 165) / 20) ** 2 * (1 if ang < 165 else 0)) / 2)
    if base["side"] == "N1":   # base on the ring-oxygen side: C3-H points away from it
        pt *= 0.2
    # ground state: the base must sit >= 3.0 A from C3 and >= 2.0 A from H3; retract it along C3 -> O
    v = unit(X - C3); need = max(0.0, 3.0 - d(C3, X), 2.0 - h_o)
    moved = dict(base); moved["atoms"] = [(n, e, (np.array(x) + v * need).tolist()) for n, e, x in base["atoms"]]; moved.pop("_a", None)
    others = [c for c in comps if c is not base]
    hard, pen = False, 0.0
    for c in others:
        h, p = pair_clash(moved, c)
        hard |= h; pen += p
    # all residues vs the substrate atoms (base after retraction): hydrogens use a shorter limit
    spen, shard = 0.0, False
    for c in [moved] + others:
        Xc, Pc, names = A(c)
        D = np.linalg.norm(Xc[:, None, :] - SUB_XYZ[None, :, :], axis=2)
        lim = np.where(SUB_ISH[None, :], 2.2, np.where(Pc[:, None], 2.6, 3.0))
        if c is moved: lim = lim + 0.0
        spen += float((np.maximum(0, lim - D) ** 2).sum()); shard |= bool(D[:, ~SUB_ISH].min() < 2.2)
    retract_ok = (not hard) and (not shard)
    ret_score = (1.0 if retract_ok else 0.0) * g(((max(0.0, need - 0.8)) / 0.5) ** 2)
    return dict(pt=pt, retract=ret_score, retraction=need, subs_pen=spen, hard=hard or shard, h_o=h_o, ang=ang,
                subs=0.5 * pt + 0.3 * ret_score + 0.2 * g(spen / 0.4))
