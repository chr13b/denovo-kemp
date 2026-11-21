# [2026-11-21 12:58] experiment | chris-02 seed sweep launched; GitHub protection ruled out on private free plan (chris)

- **chris-02 launched:** cluster jobs `2, 3, 4, 5` = seeds 2–5, to test whether the RFD3 → Boltz-2 catalytic
  contact drift found in chris-01 (n = 1) is systematic. Projects
  `/mnt/work/projects/chris_seedsweep_s{2,3,4,5}`, copied from the verified reference with `new-project.sh`;
  the **only** change is the seed, at all three call sites (RFD3, LigandMPNN, Boltz-2). Verified before
  submitting that exactly those three lines differ and `inputs/Kemp.json` is byte-identical.
- **They run serially, not in parallel.** The sbatch asks `--constraint=g6.2xlarge --cpus-per-task=8
  --mem=30G` = our whole allocation. ~23 min each, ~90 min total. `scancel <jobid>` frees a GPU if a
  teammate needs one. The 30 G is for the MMseqs2 step; the other stages would fit a `g6.xlarge`.
- **Decision rule is written down before the results** on the experiment page, so the verdict can't be
  fitted to the numbers: ≥ 3 of 4 runs with base Δ > +1.5 Å ⇒ filter on Boltz-2 geometry; ≤ 1 of 4 ⇒
  chris-01 was an outlier and RFD3 geometry is a usable cheap pre-filter; 2 of 4 ⇒ inconclusive.
- **Known confound, stated up front:** all three seeds move together, so design variance and Boltz-2
  prediction variance are not separated. Follow-up that does separate them: fix the design, vary only the
  Boltz-2 seed — which also measures the pose-consistency scoring term.
- **GitHub-side branch protection: not available to us.** Confirmed `chr13b/kemp-challenge` is private
  (unauthenticated API returns 404). GitHub allows protection/rulesets on private repos only on Pro/Team/
  Enterprise. Worse, on a private repo under a free account a ruleset can show **Active and enforce
  nothing**, so "I added the rule" is not evidence it works. The local `no-commit-to-main` hook (verified
  working) plus CI on every push is what we rely on. Options and a no-authenticator-app `gh` login via
  personal access token are now in [../CONTRIBUTING.md](../CONTRIBUTING.md) §6.
- **Key handling:** `pdh-team-01.pem` stays out of git by design — it is installed at `~/.ssh/` (mode 600)
  and wired into `~/.ssh/config` as `pdh-team`. Re-verified the `detect-private-key` hook blocks a `.pem`
  even when force-added past `.gitignore` (tested with a fake key, not the real one).
