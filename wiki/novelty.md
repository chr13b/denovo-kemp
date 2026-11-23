# Novelty: the one hard gate

Every other scoring term is a ranking. This one disqualifies. From
`raw/20261121_organizers_submission.md`:

> backbone TM-score ≤ 0.7 to any published structure **AND** sequence ≤ 70 % identity

Both conditions must hold. `challenge.md` also records that HG3.17 itself does not
qualify — which matters to us, because our theozymes are carved out of **7K4U, an
HG3 structure**. If RFdiffusion reproduces an HG3-like fold, the design is out
however good its catalytic geometry is.

**Check novelty before a design takes one of our 20 slots, not after.**

## Status, 2026-11-22

Measured over all 15 Boltz-2 structures the team had produced at that point
(zonghu-03). Evidence: `results/criteria/foldseek_tm_vs_7k4u.tsv`.

| Design | TM vs 7K4U | Gate |
|---|---|---|
| `chris_seedsweep_s3` | **0.705** | ⛔ **fails** |
| `zonghu_ms_s2` | 0.692 | ✅ narrowly |
| `zonghu_g10_s3` | 0.658 | ✅ narrowly |
| `zonghu_g10_s2` | 0.646 | ✅ narrowly |
| `zonghu_vA_s2` | 0.634 | ✅ |
| `zonghu_vA_s3` | 0.467 | ✅ |
| `chris_seedsweep_s5` | 0.465 | ✅ |
| `zonghu_trpopt_s1` | 0.451 | ✅ |
| `zonghu_ms_s3` | 0.422 | ✅ |
| `zonghu_hb_s1` | 0.411 | ✅ |
| `zonghu_ms_s1` | 0.380 | ✅ |
| `zonghu_vA_s1` | 0.374 | ✅ |
| `zonghu_g10_s5` | 0.337 | ✅ |
| `chris_seedsweep_s4` | 0.300 | ✅ |

`chris_seedsweep_s2` produced no alignment at all — foldseek found nothing above
threshold, which means *more* novel, not less.

**Two findings worth acting on:**

1. **`chris_seedsweep_s3` is over the line.** It ranks 5th of 15 on contact
   distances, so without this check it could plausibly have been submitted.
2. **A quarter of all designs sit between 0.63 and 0.71.** Motif scaffolding from
   an HG3 motif pulls the fold back toward HG3 often enough that this is a
   routine risk, not an edge case.

Sequence identity is not the binding half: **32–36 %** against HG3, HG3.7 and
HG3.17, and `fident` inside the structural alignments is 2–10 %. Comfortably
under 70 % for every design.

## How to run it

### TM-score (the binding half)

`foldseek` is **not** part of the organizers' cluster image. Installed once into
our own area, from the official release:

```bash
curl -sSL https://mmseqs.com/foldseek/foldseek-linux-avx2.tar.gz | tar xz
cp foldseek/bin/foldseek /mnt/work/software/bin/foldseek
```

Then, structure-to-structure with the TMalign backend:

```bash
foldseek easy-search <designs_dir> <reference.pdb> out.tsv tmp \
  --alignment-type 1 \
  --format-output "query,target,alntmscore,qtmscore,ttmscore,fident,alnlen"
```

`--alignment-type 1` is what makes the TM-score meaningful; the default 3Di
alignment reports a different quantity.

### Sequence identity

`scripts/32_check_sequence_novelty.py` does pairwise global alignment against the
HG-series FASTAs in `results/affinity/`. It needs no cluster and no GPU.

## Limits of what has been checked

These are real gaps, not caveats for form's sake:

- **Only 7K4U was used as the reference.** The rule says "any published
  structure". A full check needs the PDB as a foldseek database; HG3 was chosen
  first because it is where our motif comes from and therefore the most likely
  way to fail. **"OK" in the table above means "not HG3-like", not "novel".**
- **The normalization is ambiguous and it decides the borderline case.** foldseek
  reports `alntmscore` 0.707, `qtmscore` 0.705 and `ttmscore` 0.705 for
  `chris_seedsweep_s3`. TM-score is normally normalized by the reference length,
  but `challenge.md` does not say which the organizers use. At 0.705 against a
  0.70 gate, that choice is the difference between qualified and not. **Open
  question for the organizers.**
- **The sequence aligner is crude** — match/mismatch ±1, gap −1, identity over
  the shorter sequence. Fine for "is this the same protein" at 35 %; it would be
  the wrong tool near the 70 % line. Use MMseqs2 if a design ever gets close.

## Related

- `wiki/scoring.md` — the five scored criteria, which are a ranking, unlike this
- `wiki/challenge.md` — the rules this gate comes from
- `wiki/submission.md` — where the gate has to be applied
- `wiki/experiments/zonghu-03_trp-flexibility-and-dyad-geometry.md` — the designs measured here
