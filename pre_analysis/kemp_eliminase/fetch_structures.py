#!/usr/bin/env python3
"""Re-create the gitignored downloads of pre_analysis/kemp_eliminase (structures, ligands, third-party code).

    python3 fetch_structures.py            # download whatever is missing
    python3 fetch_structures.py --dry-run  # only list what is missing

What it fetches (all public; nothing is overwritten if it already exists):
  structures/core/      29 RCSB entries, .cif + .pdb       (tier 'core' in metadata/entries.csv)
  structures/extended/  71 RCSB entries, .cif only         (tier 'extended')
  structures/scaffolds/ 9 parent / source folds, .cif + .pdb
  ligands/              CCD definitions (.cif) and ideal geometries (.sdf) of the TSAs, substrate and product
  code/denovoKemp/      github.com/Fleishman-Lab/denovoKemp pinned to the commit used (no licence file: do not redistribute)
  code/zenodo_14563437/ Zenodo 10.5281/zenodo.14563437 (CC-BY-4.0), unpacked
  theozyme/rosetta_denovoKemp/  the 12 theozyme / matcher files copied from the clone (same licence caveat)
The aligned copies in structures/aligned_on_substrate/ are NOT downloaded: theozyme/align_full_structures.py makes them.
RCSB files carry no checksum here; they are versioned by release date (see wiki/data.md).
"""
import csv
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DRY = "--dry-run" in sys.argv
SCAFFOLDS = "1THF 1JCL 1A53 1GOR 1LBF 1I4A 1JCM 1VC4 4FB7".split()
LIGANDS = "6NT 3NY 0CU 0CT VWF H5J 6VP".split()
DENOVO_COMMIT = "c2a74217e57f8e8f1ae620efa551b7e18bf7c6f0"
ZENODO = ["README.txt", "EVB_Simulations.zip", "Classical_MD_Simulations.zip"]
THEOZYME_FILES = [
    "README.md", "2.MatchDesign/1.Match/theozime.cst", "2.MatchDesign/1.Match/UNK_virt.params",
    "2.MatchDesign/1.Match/bb1000_0001.pos", "2.MatchDesign/1.Match/matcher_flags", "2.MatchDesign/1.Match/example.cmd",
    "2.MatchDesign/1.Match/scripts/findAlignedPos.py", "2.MatchDesign/1.Match/scripts/pymol_alignment.py",
    "2.MatchDesign/1.Match/scripts/struct_align.py", "2.MatchDesign/2.Design/deNovo_design.xml",
    "2.MatchDesign/2.Design/enzdes_flags", "2.MatchDesign/2.Design/example.cmd",
]
missing = 0


def get(url, dest):
    global missing
    dest = os.path.join(HERE, dest)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    missing += 1
    print("missing:", os.path.relpath(dest, HERE))
    if DRY:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())


rows = list(csv.DictReader(open(os.path.join(HERE, "metadata", "entries.csv"))))
for r in rows:
    pid = r["pdb_id"]
    sub = "core" if r["tier"] == "core" else "extended"
    get(f"https://files.rcsb.org/download/{pid}.cif", f"structures/{sub}/{pid}.cif")
    if sub == "core":
        get(f"https://files.rcsb.org/download/{pid}.pdb", f"structures/core/{pid}.pdb")
for pid in SCAFFOLDS:
    for ext in ("cif", "pdb"):
        get(f"https://files.rcsb.org/download/{pid}.{ext}", f"structures/scaffolds/{pid}.{ext}")
for c in LIGANDS:
    get(f"https://files.rcsb.org/ligands/download/{c}.cif", f"ligands/{c}.cif")
    get(f"https://files.rcsb.org/ligands/download/{c}_ideal.sdf", f"ligands/{c}_ideal.sdf")
for f in ZENODO:
    get(f"https://zenodo.org/records/14563437/files/{f}?download=1", f"code/zenodo_14563437/{f}")

clone = os.path.join(HERE, "code", "denovoKemp")
if not os.path.isdir(clone):
    missing += 1
    print("missing: code/denovoKemp (git clone)")
    if not DRY:
        os.makedirs(os.path.dirname(clone), exist_ok=True)
        subprocess.run(["git", "clone", "https://github.com/Fleishman-Lab/denovoKemp.git", clone], check=True)
        subprocess.run(["git", "-C", clone, "checkout", DENOVO_COMMIT], check=True)
        shutil.rmtree(os.path.join(clone, ".git"))  # a nested .git would make the parent repo treat it as a submodule
for z in ("EVB_Simulations", "Classical_MD_Simulations"):
    zp = os.path.join(HERE, "code", "zenodo_14563437", z + ".zip")
    if os.path.exists(zp) and not os.path.isdir(os.path.join(HERE, "code", "zenodo_14563437", z)) and not DRY:
        with zipfile.ZipFile(zp) as zf:
            zf.extractall(os.path.join(HERE, "code", "zenodo_14563437", z), members=[m for m in zf.namelist() if "__MACOSX" not in m and ".DS_Store" not in m])
if os.path.isdir(clone):
    for f in THEOZYME_FILES:
        dst = os.path.join(HERE, "theozyme", "rosetta_denovoKemp", f)
        if not os.path.exists(dst):
            missing += 1
            print("missing:", os.path.relpath(dst, HERE))
            if not DRY:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(os.path.join(clone, f), dst)
print(f"{missing} item(s) {'missing' if DRY else 'fetched'}; nothing to do." if not missing else f"{missing} item(s) {'missing' if DRY else 'fetched'}.")
