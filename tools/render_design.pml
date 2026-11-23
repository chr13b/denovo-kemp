# Render the design figure's two views with PyMOL (one of five seeds of design s010, picked for illustration).
#
# Input : seed 2 of results/candidates/arms_98_s010.zip, saved as s010.cif next to this file
#         (design s010 = `arms_98_s010`, Boltz-2 refold, base=86 Asp, donor=52 Gln, ligand 6NT = chain B).
# Run   : pymol -cq render_design.pml          (PyMOL open-source 3.x; produced overview.png and closeup.png)
# Then  : uv run python tools/compose_design_figure.py <folder> docs/img/design_s010.png
load s010.cif, s010
bg_color white
hide everything
set ray_opaque_background, on
set antialias, 2
set ray_trace_mode, 0
set ray_shadows, 0
set ambient, 0.5
set specular, 0.25
set depth_cue, 0
set cartoon_fancy_helices, 1
set cartoon_loop_radius, 0.26
set stick_radius, 0.22
set sphere_scale, 0.9
set float_labels, on
set label_color, 0x111518
set label_size, 15
set label_font_id, 7
select prot, s010 and chain A
select lig, s010 and chain B
show cartoon, prot
spectrum count, rainbow, prot
set cartoon_transparency, 0.45, prot
show sticks, lig
color 0xBA76DD, lig and elem C
show sticks, prot and resi 86+52
color 0x00B386, prot and resi 86 and elem C
color 0x0A8FD6, prot and resi 52 and elem C
util.cnc lig
util.cnc prot and resi 86+52
distance base, (prot and resi 86 and name OD2), (lig and name N3)
distance donor, (prot and resi 52 and name NE2), (lig and name N1)
hide labels
set dash_color, 0x111518
set dash_radius, 0.075
set dash_gap, 0.22
python
from pymol import cmd
for name, a, b in (("base", "prot and resi 86 and name OD2", "lig and name N3"), ("donor", "prot and resi 52 and name NE2", "lig and name N1")):
    d = cmd.get_distance(a, b)
    p = cmd.get_coords(a)[0]
    q = cmd.get_coords(b)[0]
    m = [float(x) for x in (p + q) / 2.0]
    cmd.pseudoatom("lab_" + name, pos=m, label="%.2f Å" % d)
print("base/donor", cmd.get_distance("prot and resi 86 and name OD2", "lig and name N3"), cmd.get_distance("prot and resi 52 and name NE2", "lig and name N1"))
python end
hide labels, base or donor
hide everything, lab_base or lab_donor
python
cmd.label("lab_base", repr(u"2.52 \u00c5"))
cmd.label("lab_donor", repr(u"3.06 \u00c5"))
cmd.set("label_position", [1.6, 1.3, 2.0], "lab_base")
cmd.set("label_position", [-1.2, -3.4, 2.0], "lab_donor")
python end
# overview: protein as translucent ribbon, ligand as spheres so it is visible
orient prot
turn y, 25
show spheres, lig
set sphere_transparency, 0
zoom prot, 2
hide labels
png overview.png, 1500, 1500, dpi=200, ray=1
# close-up: stick ligand, labels on, slab to drop the front helices
hide spheres, lig
set cartoon_transparency, 0.7, prot
zoom (lig or (prot and resi 86+52)), 6
clip near, -2
clip far, 9
show labels, lab_base or lab_donor
png closeup.png, 1500, 1500, dpi=200, ray=1
quit
