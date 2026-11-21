# pymol -cq 18_render_v2.py   (run from kemp_theozymes_v2/)
import os, glob, pickle, json
import numpy as np
from pymol import cmd
IDS = ["V00001", "V00009", "V00023", "V00128", "V00236", "V00367", "V10561", "V00189", "V13877", "V00552", "V64285"]
picked = {cd["id"]: (slot, cd) for slot, desc, cd in pickle.load(open("report/picked.pkl", "rb"))}
COL = {"A": "yellow", "B": "marine", "C": "lightblue", "D": "orange", "E": "brightorange", "F": "forest", "G": "magenta"}
cmd.set("ray_opaque_background", 1); cmd.bg_color("white"); cmd.set("label_size", -0.55); cmd.set("label_color", "black"); cmd.set("dash_gap", 0.25); cmd.set("dash_radius", 0.06); cmd.set("depth_cue", 0)
def cen(sel): return np.mean([a.coord for a in cmd.get_model(sel).atom], 0)
for vid in IDS:
    if vid not in picked: print("not selected:", vid); continue
    slot, cd = picked[vid]; f = glob.glob(f"candidates/{slot}__{vid}.pdb")[0]
    cmd.delete("all"); cmd.load(f, "t"); cmd.load("templates/substrate_5NBI.pdb", "sub")
    for ch, c in COL.items(): cmd.color(c, f"t and chain {ch} and elem C")
    cmd.show("sticks", "t"); cmd.set("stick_radius", 0.17)
    cmd.show("lines", "sub"); cmd.color("gray50", "sub"); cmd.set("line_width", 2.5)
    # contacts: base to TSA (red), donors to nitro / N1 (black), substrate C3-H...O (green)
    cmd.distance("basec", "t and chain A and name N1+N3", "t and (chain B or chain C) and elem N+O and not name N+O+OXT", 3.5); cmd.color("red", "basec"); cmd.hide("labels", "basec")
    cmd.distance("donor", "t and chain A", "t and (chain F or chain G) and elem N+O and not elem C", 3.6, mode=0); cmd.color("black", "donor"); cmd.hide("labels", "donor")
    cmd.distance("pt", "sub and name H3", "t and (chain B or chain C) and elem N+O and not name N+O+OXT", 2.4); cmd.color("green", "pt"); cmd.hide("labels", "pt")
    kinds = [q["kind"] for q in cd["group"] if q["kind"] in ("ring", "npi")]
    for ch, k in zip(("D", "E"), kinds):
        res = cmd.get_model(f"t and chain {ch} and name CA").atom[0].resn if cmd.count_atoms(f"t and chain {ch} and name CA") else ""
        ring = "name CD2+CE2+CZ2+CH2+CZ3+CE3" if res == "TRP" else "name CG+CD1+CD2+CE1+CE2+CZ"
        tgt = cen("t and chain A and not name NO1+O11+O21") if k == "ring" else cen("t and chain A and name NO1")
        cmd.pseudoatom("pc" + ch, pos=list(cen(f"t and chain {ch} and {ring}"))); cmd.pseudoatom("tc" + ch, pos=list(tgt)); cmd.distance("pi" + ch, "pc" + ch, "tc" + ch); cmd.color("orange", "pi" + ch); cmd.hide("labels", "pi" + ch); cmd.hide("everything", "pc" + ch + " or tc" + ch)
    names = {"B": "base", "C": "dyad Asp", "D": "stacker", "E": "stacker 2", "F": "nitro donor", "G": "LG donor"}
    for ch in "BCDEFG":
        if cmd.count_atoms(f"t and chain {ch}"):
            resn = cmd.get_model(f"t and chain {ch} and name CA").atom[0].resn if cmd.count_atoms(f"t and chain {ch} and name CA") else ""
            cmd.pseudoatom("lab" + ch, pos=list(cen(f"t and chain {ch}") + np.array([0, 0, 1.4])), label=f"{resn} ({names[ch]})"); cmd.hide("everything", "lab" + ch); cmd.show("labels", "lab" + ch)
    cmd.orient("t and chain A"); cmd.turn("x", -62); cmd.zoom("t", 0); cmd.png(f"report/img/{vid}.png", 900, 720, dpi=130, ray=0)
print("rendered")
