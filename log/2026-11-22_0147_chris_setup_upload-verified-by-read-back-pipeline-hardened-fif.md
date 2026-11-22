# [2026-11-22 01:47] setup | Upload verified by read-back; pipeline hardened; fifth arm added from the crystal pocket analysis (chris)

- TODO

- **Upload verified by read-back.** `head-object` on our key: 294 bytes, ETag equal to the local file's MD5
  (`8e274d94...`), the S3 version id matches, last modified 23:15:30 UTC. Byte-identical.
- **Autopilot hardened before an unattended night**, after re-reading it for silent failures: a transient `squeue`
  error was read as "job finished" and would have resubmitted a duplicate (now `UNKNOWN`, keep waiting); a failed
  `sbatch` crashed the driver (now 3 retries); a restart re-ran every arm (now resumes by job name); one job
  failing twice halted everything (now that job is skipped and later stages continue); no heartbeat (now every 10
  min); a stage crash killed the run (now logged and skipped). 11 behaviour tests pass on the cluster.
  Rule change worth knowing: I had said "halts if a job fails twice"; it now skips that job and carries on.
- **A bug the dry run caught:** the 2-seed smoke replicate of s042 and s004 made the driver treat them as already
  replicated, so the real replication would have skipped the two best candidates. A design now counts as replicated
  only with all 5 seeds; smoke output moved to `results/_smoke/`.
- **All four arm paths verified through the real Slurm script:** aromatic (bias, seed offset), close variants (89 and
  94 % identity to s024), checkpoint 005 (the log shows `ligandmpnn_v_32_005_25.pt` was loaded, the close arm used 010),
  and the new polar-down arm (2 polar residues at the pocket in all 3 sequences against a baseline mean of 4.1).
- **Crystal pocket analysis (primer g11):** nine residues touch the ligand in all 25 copies (Trp44, Pro45, Glu46,
  Gln50, Gly83, Asp127, Leu236, Met237, Thr265). Designs with the ligand roughly in place have about twice the
  polar content of the crystals (4.5 vs 2.1 residues) and the same size and aromatic content, which became arm 5.
  Stacking evidence is weak (strict test passes 10 of 25 crystal copies).
- Plan is now 5 arms, estimated 125 min for that stage and ~5 h for the whole run.
