"""Superpose all TSA-bound active-site shells (extracted/*_shell.pdb) onto one TSA frame with PyMOL.
Run:  pymol -cq theozyme/superpose_theozyme.py   (from kemp_eliminase/)
Output: theozyme/extracted/aligned/*.pdb and theozyme/theozyme_ensemble.pse
Reference frame: 7K4Q chain A TSA (HG3 + 6NT, 1.28 A). Alignment uses the 9 benzotriazole core atoms;
0CT/0CU atoms are mapped to the 6NT/3NY labels by connectivity.
"""
import glob, os
from pymol import cmd
base = os.path.join(os.getcwd(), "theozyme", "extracted")
os.makedirs(os.path.join(base, "aligned"), exist_ok=True)
CORE = ["N1", "N2", "N3", "C3A", "C7A", "C4", "C5", "C6", "C7"]
MAP = {"6NT": dict(zip(CORE, CORE)), "3NY": dict(zip(CORE, CORE)),
       "0CT": dict(zip(CORE, ["NAG", "NAE", "NAF", "CAH", "CAI", "CAC", "CAA", "CAB", "CAD"])),  # unsubstituted ring is symmetric: N3 := the N the base contacts (NAF in 3UZJ)
       "0CU": dict(zip(CORE, ["NAG", "NAE", "NAF", "CAJ", "CAK", "CAD", "CAH", "CAC", "CAI"]))}
files = sorted(glob.glob(os.path.join(base, "*_shell.pdb")))
ref = "7K4Q_A401"
cmd.reset()
for f in files:
    tag = os.path.basename(f).replace("_shell.pdb", "")
    cmd.load(f, tag)
tsa = lambda t: cmd.get_model(f"{t} and hetatm").atom[0].resn
for f in files:
    tag = os.path.basename(f).replace("_shell.pdb", "")
    if tag == ref: continue
    mm, rm = MAP[tsa(tag)], MAP[tsa(ref)]
    # pair_fit takes mobile, target, mobile, target ... in selection syntax
    args = []
    for k in CORE:
        args += [f"{tag} and hetatm and name {mm[k]}", f"{ref} and hetatm and name {rm[k]}"]
    cmd.pair_fit(*args)
for f in files:
    tag = os.path.basename(f).replace("_shell.pdb", "")
    cmd.save(os.path.join(base, "aligned", f"{tag}_aligned.pdb"), tag)
cmd.hide("everything"); cmd.show("sticks"); cmd.util.cbc()
cmd.save(os.path.join(os.getcwd(), "theozyme", "theozyme_ensemble.pse"))
print("aligned", len(files), "shells onto", ref)
