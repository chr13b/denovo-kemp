# [2026-11-21 20:06] experiment | threshold review: the base contact is the binding gate, 0 of 6 (zonghu)

- **Replaying our stage-3 gates over all 6 tracked cofolds costs no GPU and answers the question
  a run would have**: 0/6 pass, and the **binding gate is the base contact (5/6)**, not confidence.
  `uv run python scripts/31_screen_summaries.py`. Provenance for every threshold:
  [wiki/design-filters.md](../wiki/design-filters.md).
- **The organizers' own verified reference fails** (base 5.91 Å), and so does every design we have.
  Expected cost of "run until one passes" is **> 138 min of serial big-node time per hit and
  plausibly unbounded** — which is why I stopped before launching rather than after burning it.
- **Lowered the pLDDT gate 85 → 80** on an independent document (`kemp_rfd3_workflow/README.md`:
  "keep pLDDT > 80, ideally > 85"), since a gate at 85 rejects the organizers' working example at
  83.6. **It changes no verdict** — the base contact still rejects everything.
- **Did NOT widen the donor window to rescue sweep_kemp-4.** It fails by 0.35 Å (3.75 vs ≤ 3.4),
  and widening to 3.9 Å would make it "pass". That is fitting a threshold to the one design we
  want, and chris-02 had already flagged that contact as "longer than ideal H-bond geometry".
  The gate stays where the chemistry puts it.
- **The gate is right; the designs are wrong.** Real Kemp eliminases sit at **2.5–2.6 Å** on the
  base contact — Broom et al. report that for all six HG variants across a 1000-fold activity
  range, and our own 7K4U crystal measures 2.53 Å. A gate that accepted 5.91 Å would not be a
  better gate, it would accept non-enzymes.
- **The challenge ranks, it does not gate** ([challenge.md](../wiki/challenge.md): terms multiply,
  "there is an optimum, not a direction", novelty is the only true gate). So binary pass/fail is
  right for triage and wrong for selection. Three tiers proposed in the wiki: triage (clashes,
  folded, novelty) → ranked (contacts, pLDDT, burial) → report-only (packing, topology, GRAVY/pI).
  **Under ranking, sweep_kemp-4 is already our best candidate** — the same conclusion chris-02
  reached, without moving any threshold.
- Next lever is the input, not the sample size: RFD3 is handed the base contact and returns it at
  2.53 Å every time, so it is Boltz-2 that loses it. Trying `_trpopt2` from
  [zonghu-01](../wiki/experiments/zonghu-01_trp-stack-theozyme-vs-crystal.md) is free.
