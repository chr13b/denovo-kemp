# [2026-11-22 02:03] experiment | Autopilot launched: replicate, five arms, main sweep, replicate, rank (chris)

- TODO

- **Launched 2026-11-22 01:02 UTC** on go from the team lead (fifth arm included, no auto-upload: they will be awake
  before 08:00 UTC). Detached with `nohup setsid`, PID 356890, project `/mnt/work/projects/chris_autopilot`.
- Pre-flight: all 7 deployed files matched the repo by sha256, queue empty, no stale state, arm inputs present.
  A "driver already running: 1" reading was my own `pgrep` matching itself; confirmed 0 real driver processes
  before starting.
- First action: `repl1` replicates the 20 best existing designs by geometry D (s042, s004, s006, s019, s069,
  seed12_s001, seed12_s003, seed3_s035, ...), with s024 and s059 correctly excluded as already replicated. Job 90.
- Plan and timings are in `wiki/cluster.md` (about 5 h serial on one GPU; stop-by 08:00 UTC). Watching
  `autopilot.log` with a watcher that reports stage changes, warnings, a dead driver or 30 min of silence.
- Selection rule (pre-registered, unchanged): >= 3/5 seeds with both distances in window, mean D <= 15, OD2 the
  nearest carboxylate oxygen in >= 4/5 seeds, qTM <= 0.70, validator accepts. Upload only validator-accepted
  files, and only when the set improves.
