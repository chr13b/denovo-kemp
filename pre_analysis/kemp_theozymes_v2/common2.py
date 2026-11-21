"""v2 helpers: re-use v1 library (kemp_theozymes/common.py) and add v2 paths."""
import sys, os
HERE2 = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.abspath(os.path.join(HERE2, "..", "kemp_theozymes"))
sys.path.insert(0, V1)
from common import *            # noqa  (parse_pdb, read_cif_atoms, kabsch, ring_frame, angle, dihedral, write_pdb, AA, BB, CORE, ...)
V1T = os.path.join(V1, "templates")
T2 = os.path.join(HERE2, "templates")
