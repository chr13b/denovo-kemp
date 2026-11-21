# pymol -cq 06_render.py   (run from kemp_theozymes/)  -> report/img/*.png and report/theozymes.pse
import os, glob, pickle, csv
from pymol import cmd
import numpy as np
HERE = os.getcwd(); IMG = os.path.join(HERE, "report", "img"); os.makedirs(IMG, exist_ok=True)
SHOW = ["T00001", "T00003", "T00015", "T00031", "T01327", "T00094", "T00072", "T00089"]
rows = {r["id"]: r for r in csv.DictReader(open("candidates_scored.csv"))}
COL = {"A": "yellow", "B": "marine", "C": "lightblue", "D": "orange", "E": "forest"}
cmd.set("ray_opaque_background", 1); cmd.bg_color("white"); cmd.set("stick_radius", 0.17); cmd.set("label_size", -0.6); cmd.set("label_color", "black")
cmd.set("dash_gap", 0.25); cmd.set("dash_radius", 0.06); cmd.set("depth_cue", 0)
for tid in SHOW:
    f = glob.glob(f"candidates/*__{tid}.pdb") or glob.glob(f"candidates/top*__{tid}.pdb")
    if not f: print("missing", tid); continue
    f = sorted(f)[0]; cmd.delete("all"); cmd.load(f, tid)
    r = rows[tid]
    for ch, c in COL.items(): cmd.color(c, f"{tid} and chain {ch} and elem C")
    cmd.show("sticks", tid); cmd.set("stick_radius", 0.17)
    cmd.distance("polar", f"{tid} and chain A", f"{tid} and chain E and not elem C", 3.6, mode=2); cmd.color("black", "polar"); cmd.hide("labels", "polar")
    cmd.distance("basec", f"{tid} and chain A and name N1+N3", f"{tid} and (chain B or chain C) and elem N+O and not name N+O+OXT", 3.5); cmd.color("red", "basec"); cmd.hide("labels", "basec")
    cmd.distance("dyad", f"{tid} and chain B and resn HIS and elem N and not name N", f"{tid} and chain C and elem O and not name O", 3.4); cmd.color("red", "dyad"); cmd.hide("labels", "dyad")
    # pi centroid dashed line to TSA bicycle centroid
    def cen(sel): m = cmd.get_model(sel); return np.mean([a.coord for a in m.atom], 0)
    tsa_c = cen(f"{tid} and chain A and not name NO1+O11+O21")
    ring = "name CD2+CE2+CZ2+CH2+CZ3+CE3" if r["pi"].startswith("TRP") else "name CG+CD1+CD2+CE1+CE2+CZ"
    pc = cen(f"{tid} and chain D and {ring}")
    cmd.pseudoatom("pc", pos=list(pc)); cmd.pseudoatom("tc", pos=list(tsa_c)); cmd.distance("pi", "pc", "tc"); cmd.color("orange", "pi"); cmd.hide("labels", "pi"); cmd.hide("everything", "pc or tc")
    for ch, txt in (("B", r["base"].replace("  ", " ") + " " + r["base_src"]), ("D", r["pi"].replace("  ", " ") + " " + r["pi_src"]), ("E", r["nitro"].split("(")[0] + " " + r["nitro_src"] if r["nitro"] != "none" else None)):
        if txt: cmd.pseudoatom("lab" + ch, pos=list(cen(f"{tid} and chain {ch}") + np.array([0, 0, 1.2])), label=txt); cmd.hide("everything", "lab" + ch); cmd.show("labels", "lab" + ch)
    cmd.orient(f"{tid} and chain A"); cmd.turn("x", -62); cmd.zoom(tid, 0)
    cmd.png(os.path.join(IMG, f"{tid}.png"), 900, 720, dpi=130, ray=0)
    cmd.save(os.path.join(IMG, f"{tid}.pse"))
# combined session: all shown candidates in one frame
cmd.delete("all")
for tid in SHOW:
    f = sorted(glob.glob(f"candidates/*__{tid}.pdb"))[0]; cmd.load(f, tid)
cmd.show("sticks"); cmd.util.cbc(); cmd.save("report/theozymes.pse"); print("rendered", SHOW)
