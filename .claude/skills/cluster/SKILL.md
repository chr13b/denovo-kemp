---
name: cluster
description: Run a design job on the team's GPU cluster, follow it, and bring the results back. Use when the user wants to generate designs, run RFD3/LigandMPNN/Boltz-2, submit a Slurm job, check a job, or asks "run it on the cluster".
---

# Run a job on the cluster

Background and all paths: `wiki/cluster.md`. Never print the contents of the `.pem` key.

1. **Connect and look before acting.** `ssh pdh-team` (everything below runs there).
   - `squeue` — is something of ours already queued or running? Our team can use 2 GPU workers at once.
   - `ls /mnt/work/projects` — which project folders exist?
   - `test -f /mnt/work/kemp_example/status.sh` — is the example prepared?
2. **If the example is not prepared yet** (once per team):
   `bash /mnt/ref/hackathon/setup.sh`, note the job number, then poll
   `bash /mnt/work/kemp_example/status.sh` until it prints `VERIFIED: ...`.
   Do not submit a second setup job while the first is queued. Never modify `/mnt/work/kemp_example`.
3. **Make a fresh project** (never edit the example, never edit a project whose job is running):
   `bash /mnt/ref/hackathon/new-project.sh /mnt/work/kemp_example /mnt/work/projects/<handle>_<topic>`
4. **Edit inputs deliberately.** Read `inputs/Kemp.json`, `inputs/HG3_17_kemp_motif.pdb` and
   `src/kemp-e2e.sbatch` first. Length: `contig` in the `Kemp_HG3_17_base_donor` entry (max 260).
   Sampling: `seed` in `src/kemp-e2e.sbatch`. State in chat exactly what you changed and why.
5. **Record the plan before running.** `python tools/new.py exp <slug>` locally, and put the project path,
   the input changes and the seed on that page. Commit before running so the run is traceable.
6. **Submit and follow:** `bash /mnt/work/projects/<handle>_<topic>/run.sh` prints JOB_NUMBER.
   `squeue -j JOB_NUMBER`, then `tail -n 50 .../logs/kemp-JOB_NUMBER.log`.
   Never run model commands directly on the head node, and never use the `l4big` queue.
7. **Read the result honestly.** `cat .../results/kemp-JOB_NUMBER/summary.json`.
   Report `pipeline_completed`, `status`, and **every** entry in `validation_warnings`
   (`completed_with_warnings` is normal, but the warnings matter — the scripts never repair outputs).
   Quote only numbers you actually read from these files.
8. **Bring it back.** Copy the sequence, `summary.json` and any small figures into `results/`
   (`/mnt/work` is not backed up). Big raw outputs stay on the cluster; note their path on the experiment page.
9. **Write it up.** Fill in Result and Verdict on the experiment page, add the design to
   `results/designs.jsonl` if it is a submission candidate, then
   `python tools/new.py log experiment "<id> <title>"` and `make check`.
