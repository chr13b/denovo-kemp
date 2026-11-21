# [2026-11-21 14:04] experiment | flavia-01 theozyme target geometry measured from 7K4Z (flavia)

- Measured the catalytic geometry of a working Kemp eliminase so our designs have a target instead of
  an assumption: **base 2.51 Å / 5.3° in-plane / 7.3° out-of-plane**, **donor 3.10 Å / 6.5° / 2.8°**,
  base burial **47 CA within 12 Å**. Source PDB 7K4Z (HG3.17 + 6NT, 1.08 Å), registered in `wiki/data.md`.
  Full page and caveats: `wiki/experiments/flavia-01_theozyme-target-geometry.md`.
- New: `scripts/30_measure_theozyme_geometry.py` + `configs/flavia-01.json`, `src/kemp/geometry.py`,
  `tests/test_geometry.py` (10 tests), and curated outputs `results/theozyme_7k4z.pdb`,
  `results/theozyme_7k4z_geometry.json`, `results/theozyme_viewer.html` (a standalone 3D page).
  Runs in ~0.3 s on a laptop; **no cluster or GPU time**.
- Roles are assigned by contact, not by residue number: the script takes the nearest allowed base to
  6NT N3 and the nearest allowed donor to N1, and recovers ASP127 and GLN50 on its own. It refuses to
  emit a target if either contact falls outside hydrogen-bonding range, because a wrong target is worse
  than none. The crystal's modelled H3 on N3 confirms the ring-atom mapping independently.
- **This sharpens [chris-01](../wiki/experiments/chris-01_reference-pipeline-baseline.md).** Its base
  contact was 2.53 Å in RFD3's output and 5.91 Å after the Boltz-2 refold. RFD3 landed within 0.02 Å of
  what a real enzyme holds, and the refold — the thing that gets scored — threw it away. The donor
  survived (3.09 → 2.94 Å against a 3.10 Å target). So chris-02's drift is the highest-weighted contact
  moving off a target we can now name, not a small wobble in a roughly-right pose.
- Judgement call worth flagging: the geometry primitives went into `src/kemp/geometry.py` rather than
  staying in the script, against the "two scripts first" rule. They are foundational (PDB parsing,
  vector maths) and the Scoring-track filter is the second consumer, but say so if you disagree and I
  will fold them back into the script.
