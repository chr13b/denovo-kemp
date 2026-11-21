# [2026-11-21 13:15] ingest | kickoff slides ingested: 4 scoring terms, burial definition, lab validation; one-command onboarding (chris)

Source added: [../raw/20261121_organizers_challenge-slides.pdf](../raw/20261121_organizers_challenge-slides.pdf)
(8 slides, Lucas Merlicek / Perlin Bio). **Image-only — no text layer**, so it must be rendered to images
to read. Everything decision-relevant is distilled into [../wiki/challenge.md](../wiki/challenge.md).

- **Scoring is four terms, and the slides resolve a contradiction in the organizers' own written doc**
  (it says "four criteria" then lists five): items 1 and 2 of the doc are the two halves of one **Geometry**
  term. The four: Geometry (distance, angle, **dihedral** vs ideal approach geometry) · iPDE ·
  **Catalytic base burial** · Consistency.
- **Burial now has an exact definition: "number of CA atoms close to the catalytic base (up to 12 Å)".**
  This is the one scoring term we can compute exactly, locally, from a predicted structure, with no model
  and no GPU. Highest value-per-GPU-minute available to us — assigned to the Scoring track in
  [../wiki/team.md](../wiki/team.md).
- **Consistency = "metrics reproduced across multiple Boltz-2 seeds", and scoring uses 5 replicates per
  sequence.** That is the same procedure as chris-02, so the sweep measures a real scoring term, not just
  a diagnostic.
- **Two open questions closed.** The `oxy` target is **not** an oxygen: 6NT is 6-nitrobenzo**triazole**,
  a TS *analogue* with no ring oxygen, and the reference pipeline measures base → `6NT_N3`,
  donor → `6NT_N1`. And "active-site packing" is the burial count above.
- **New strategic fact:** *"Every team will have the chance to submit at least 5 designs for lab
  validation, independent of score."* A few of our 20 slots can be scientifically interesting rather than
  score-maximising. **We do not know how those 5 are nominated** — added to the open questions.
- **Tension recorded rather than resolved:** the written doc says MSAs mean a natural scaffold is "not
  handicapped" versus de novo; slide 7 says "MSA depth for de novo design can impact folding confidence".
  Our own run supports the slide (design MSA depth 1 vs control 301). Since iPDE and consistency both
  depend on folding confidence, a maximally novel design may pay for novelty in two of four terms while
  the novelty gate forbids staying close to known enzymes. Genuine strategic question, not settled.
- **Onboarding is now one command:** [../onboard.sh](../onboard.sh) (`make onboard`). Installs uv if
  missing, syncs the locked env, installs hooks, writes `KEMP_HANDLE` to `.env`, adds the person's row to
  `wiki/team.md`, installs the cluster key from a path **outside** the repo, writes the SSH config,
  **verifies the host fingerprint against the published one** instead of teaching people to type "yes",
  connects, and runs the tests. Idempotent; ✓/✗ per step. Tested end to end on this machine, and the
  team.md insertion tested separately for a new handle.
- `wiki/team.md` is now `merge=union` so simultaneous row additions do not conflict.
- SETUP.md gained a 3-minute fast path, a copy-paste starter prompt for any assistant, and a short section
  on keeping secrets out of a session transcript (by path, never by content) — which is both the security
  rule and what stops assistants stalling mid-task on key handling.
