#### Walkthrough of your Team Cluster

We provide pre-installed environments, state-of-the-art tools with their respective weights, relevant data for MSAs, and an end-to-end example for your convenience. This helps you get started quickly without wasting time on setup.

Please do not hesitate to ask us if something is unclear or you need help :)

Note: We ask you to use only the provided computing resources for fairness reasons.

#### Infrastructure and Workflows

##### Where your work happens

~~~text
YOUR LAPTOP                    AWS TEAM CLUSTER
SSH terminal / VS Code ------> Head node: edit files and submit jobs
                                      |
                                      +--> Slurm assigns a GPU worker
                                      |
Head and worker share: /mnt/ref  = prepared software and reference data
                       /mnt/work = your inputs, code, caches and results
~~~

- You have access to a high-performance computing (HPC) cluster with GPUs, provided by Perlin courtesy of AWS. You work on the cluster with prepared tools, data and examples, without relying on your laptop’s computing power or paying for compute.
- SSH opens a terminal on the head node. You use it to edit files, prepare inputs and submit jobs. Once connected, your commands run on the cluster.
- Slurm is the job scheduler. It queues your calculation and assigns a GPU worker. Run model calculations and all heavy calculations on compute nodes through Slurm. Never run heavy calculations on the head node; it has no GPU.
- The head node and workers see the same /mnt/ref and /mnt/work folders. Files stay on the cluster until you copy them elsewhere.

##### Computing Resources

- **Your team can run 8 logical CPUs of GPU workers at a time.** That is either one g6.2xlarge, or two g6.xlarge. Every g6 size carries the same single NVIDIA L4 with 24 GB of VRAM, so two g6.xlarge give your team **two GPUs at once** and one g6.2xlarge gives you one. Prefer the pair unless you need the larger host memory.
- The larger host matters for one step only: building an MSA with MMseqs2 needs about 28 GB of system RAM, so that step must run on the g6.2xlarge. RFD3, LigandMPNN and Boltz-2 all fit comfortably on a g6.xlarge.
- CPU and memory values below are per node. Counts are configured capacity, not a guarantee that a worker is free the moment you ask.

| Role | Instance type | Configured count | Logical CPUs | System RAM | GPU and GPU memory |
| --- | --- | --- | --- | --- | --- |
| Head node | m7i.2xlarge | 1 | 8 | 32 GiB | None |
| GPU worker | g6.xlarge | 2 | 4 | 16 GiB | 1 NVIDIA L4, 24 GB |
| GPU worker | g6.2xlarge | 1 | 8 | 32 GiB | 1 NVIDIA L4, 24 GB |
| GPU worker | g6.4xlarge | Not available | 16 | 64 GiB | 1 NVIDIA L4, 24 GB |

- Logical CPUs are the processing threads available to the operating system. RAM holds ordinary working data; GPU memory, also called VRAM, holds data used by the GPU.
- The g6.4xlarge queue (`l4big` in Slurm) is above your team's allocation. A job sent there waits in the queue indefinitely rather than failing, so do not use it.
- Instance specifications: [AWS G6](https://aws.amazon.com/ec2/instance-types/g6/) and [AWS M7i](https://aws.amazon.com/ec2/instance-types/m7i/).

##### Your reference library and workbench

- /mnt/ref is the prepared, read-only reference library. It contains the installed tools, their environments, model weights and sequence data. An environment supplies a tool with its Python interpreter and libraries; weights are the learned model parameters.
- /mnt/work is your writable workbench. Put your inputs, code, caches and results here.

~~~text
/mnt/ref/
├── software/                  Installed tools and their environments
├── data_weights/              Model weights and reference data
└── hackathon/                 Prepared example and participant tools

/mnt/work/
├── kemp_example/              Your team’s working copy of the example
└── projects/                  Your own project folders
~~~

##### Provided tools

- The supplied example runs RFD3 to generate a 260-residue structure, LigandMPNN to design its sequence, MMseqs2 to build a multiple sequence alignment (MSA), and Boltz-2 to predict the protein-ligand structure. The competition allows sequences up to 260 amino acids.
- The participant entry points are setup.sh, status.sh, new-project.sh and run.sh. The next two sections show when to use each one.
- These tools and the example workflow help you get started, especially if you are new to enzyme design. You may use other tools within the law and explore different pipelines and design approaches. Use only the provided computing resources for fairness :)

#### Connecting to the Cluster and Setup

##### Before you connect

- Your organisers give your team one packet containing a private key file and a CONNECT.txt with your head-node address, your login name and the server fingerprint to check. Everything in this section uses values from that packet.
- Your laptop needs an SSH client. VS Code with Remote SSH is optional. You do not need local AWS CLI, ParallelCluster, Conda, Python, CUDA or WSL for this prepared-cluster workflow.
- Allow about 15 minutes of hands-on preparation after access is ready. GPU startup, queueing and model runtime are additional time.

##### Your team key

- Your team is issued one key by the organisers. You do not generate a key and there is nothing to register. Everyone on the team uses the same key file, so keep it within the team and do not post it anywhere.
- Open PowerShell on Windows, or Terminal on macOS/Linux. Check that the SSH client exists:

~~~text
ssh -V
~~~

- -V prints the client version. On Windows, install OpenSSH Client through Optional Features if it is missing, then reopen PowerShell. [Microsoft instructions](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse)
- macOS normally includes the client. On Ubuntu/Debian Linux, install a missing client with sudo apt install openssh-client.
- Copy the key file from your packet into your .ssh folder, then restrict its permissions. SSH refuses to use a private key that other accounts on your machine can read.
- Windows PowerShell, from the folder holding the key:

~~~powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
Copy-Item .\pdh-team-NN.pem "$env:USERPROFILE\.ssh\"
icacls "$env:USERPROFILE\.ssh\pdh-team-NN.pem" /inheritance:r /grant:r "$env:USERNAME:R"
~~~

- macOS/Linux Terminal:

~~~bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cp ./pdh-team-NN.pem ~/.ssh/
chmod 600 ~/.ssh/pdh-team-NN.pem
~~~

- Replace NN with your team number. chmod 700 restricts the folder to your user and chmod 600 restricts the key to your user; icacls does the equivalent on Windows by removing inherited permissions and granting only yourself read access.

##### Connect to the head node

- On your laptop, edit C:\Users\YOUR_WINDOWS_USER\.ssh\config on Windows, or ~/.ssh/config on macOS/Linux. Create the file if needed and preserve existing entries.
- Add this block, replacing YOUR_HEAD_NODE_ADDRESS and NN with the values from your packet:

~~~text
Host pdh-team
    HostName YOUR_HEAD_NODE_ADDRESS
    User ec2-user
    IdentityFile ~/.ssh/pdh-team-NN.pem
    IdentitiesOnly yes
~~~

- Host gives the connection a shortcut name. HostName and User select the server and remote account. IdentityFile selects your private key; IdentitiesOnly restricts authentication to that identity.
- Windows SSH and WSL SSH use separate configuration files. Configure the client you actually use. Windows VS Code normally uses Windows SSH.
- Connect from your laptop:

~~~text
ssh pdh-team
~~~

- On the first connection SSH prints the server fingerprint. Compare it with the one in your CONNECT.txt before accepting. If it does not match, stop and tell an organiser. The fingerprint identifies the server; the key identifies your team.
- For "Permission denied", check the username is ec2-user, that the config points at your team's key file, and that the key's permissions are restricted as above. For "Connection timed out", ask the organiser to check the address and network access.
- You are now on the head node. Run the remaining setup and design commands in this remote terminal. To see the computer and your login name:

~~~bash
hostname
whoami
~~~

- Optional editor: install VS Code and Remote - SSH. Press F1, choose Remote-SSH: Connect to Host, select pdh-team and choose Linux if prompted. Open /mnt/work, then Terminal, New Terminal. That terminal also runs on the cluster. [VS Code instructions](https://code.visualstudio.com/docs/remote/ssh)

##### Prepare the example

- Run this once for your team’s working example. The organisers have made /mnt/work and /mnt/work/projects available for your team. If a teammate has already prepared /mnt/work/kemp_example, check its status below instead.

~~~bash
bash /mnt/ref/hackathon/setup.sh
~~~

- Setup checks the prepared installation, copies the example code and inputs to /mnt/work/kemp_example, and creates folders for logs, results, caches and temporary files. It uses the installed environments without reinstalling software.
- It submits one Slurm job that runs three small model tests and then the complete Kemp example. This setup verification uses strict checks and exactly 260 residues. Keep the terminal connected until setup prints the job number. Submission means the job is queued, not that the tests have passed.

~~~text
Reference example: /mnt/ref/hackathon/example_e2e_kemp/
                    ↓ setup copies code and inputs
Working example:   /mnt/work/kemp_example/
                    ↓ new-project copies a clean starting point
Your project:      /mnt/work/projects/my_first_design/
~~~

- If setup stops before printing a job number, keep the terminal output and ask the organiser to inspect it. Do not delete a workspace to retry.
- Once submitted, the job continues if SSH disconnects. Closing your laptop does not stop the cluster.

##### Check that setup succeeded

- Run this on the head node:

~~~bash
bash /mnt/work/kemp_example/status.sh
~~~

- While the job is queued or running, status.sh reports that verification is incomplete. Wait and check again; do not submit another job just because the first is waiting.
- The expected success message is:

~~~text
VERIFIED: three independent GPU smoke tests and the Kemp pipeline passed.
~~~

- status.sh checks the queue and the saved success evidence. A job disappearing from the queue alone does not mean it succeeded.
- To inspect progress or a failure, replace JOB_NUMBER with the number printed by setup:

~~~bash
tail -n 50 /mnt/work/kemp_example/logs/verify-JOB_NUMBER.log
~~~

- tail -n 50 prints the last fifty log lines. The log appears after the worker starts. If verification fails, keep the files and share the job number and final log lines with the organiser.

#### Run Your Designs

##### Create a clean project

- Keep the verified working example unchanged as a reference. Choose a new project name that your teammates are not using. Replace my_first_design in these commands with that name:

~~~bash
bash /mnt/ref/hackathon/new-project.sh /mnt/work/kemp_example /mnt/work/projects/my_first_design
~~~

- The first path selects the source workspace; the second selects the new project. The destination must not exist and its parent must be writable.
- This copies the code, inputs and run settings. It creates empty output folders and does not copy previous results, caches or verification history. It does not submit a job.
- Open your project folder in VS Code, or edit it from the remote terminal:

~~~text
/mnt/work/projects/my_first_design/
├── inputs/                 Editable model input and motif files
├── src/                    Editable pipeline and helper code
├── results/                Separate output folder for each job
├── logs/                   Job output and error messages
├── cache/ and tmp/         Runtime working data
├── env.sh                  Workspace and environment settings
└── run.sh                  Submit this project’s Kemp pipeline
~~~

- Start by reading inputs/Kemp.json, inputs/HG3_17_kemp_motif.pdb and src/kemp-e2e.sbatch together.
- This launcher starts from one 260-residue Kemp design with the catalytic base, donor and Kemp ligand fixed. To change the length, edit contig in the Kemp_HG3_17_base_donor entry of inputs/Kemp.json: 200-200 means exactly 200 residues; 150-260 samples a length within that range. Use positive lengths; zero is not a meaningful protein. The competition limit is 260. In project mode, our checks warn about invalid ranges or lengths above 260 without rejecting the input; the model may still be unable to process it.
- The downstream steps follow the actual generated length. The supplied seed makes sampling reproducible; change seed in src/kemp-e2e.sbatch to explore different samples. You can also edit model settings there, such as LigandMPNN temperature.
- In project mode, all our validation checks are warnings, including model hand-off checks. For example, if you request 150-260 residues and RFD3 produces 270, the script warns and passes on the actual structure. Sequence, alignment, fixed-residue and geometry mismatches also warn. The scripts do not pad, trim or repair outputs to make them pass. Warnings appear in the job log and validation-warnings.jsonl inside that run’s results folder.
- Setup verification remains strict at exactly 260 residues. In project runs, failed model commands or missing or unreadable essential files can still prevent the next step from running. This remains a single-design Kemp workflow: different motifs, ligands or multiple designs require matching changes to the inputs and helper code.
- Separate project folders organise your files. They do not create private accounts; participants sharing a Linux login have the same permissions.

##### Submit and follow a run

- Run on the head node:

~~~bash
bash /mnt/work/projects/my_first_design/run.sh
~~~

- run.sh selects the model environments and submits the pipeline through Slurm. It prints a new job number and the paths for that job’s log and results.
- Do not change a project’s inputs or code while its job is queued or running. Use another project folder for concurrent changes.
- Replace JOB_NUMBER below with the new job number:

~~~bash
squeue -j JOB_NUMBER
tail -n 50 /mnt/work/projects/my_first_design/logs/kemp-JOB_NUMBER.log
~~~

- squeue shows a queued or running job. Once the job finishes, inspect its summary:

~~~bash
cat /mnt/work/projects/my_first_design/results/kemp-JOB_NUMBER/summary.json
~~~

- A finished project run writes a summary with pipeline_completed set to true. The status is passed when checks pass, or completed_with_warnings when they reported problems. validation_passed and pipeline_execution_passed are false if warnings remain; that does not stop the project run. Read validation_warnings in the summary. If the summary is missing, inspect the log and ask for help. The example’s status.sh checks only the initial setup verification; it does not track these later runs.
- Results include the RFD3 structure, LigandMPNN sequence, MSA and Boltz-2 prediction. A designed sequence may have no database homologues and use a query-only alignment. The setup verification also requires database hits for a natural-protein control.
- This small example checks execution and data flow. It does not establish enzyme activity or competitive design quality.

##### Optional interactive environment

- The scripts load their own environments. For interactive inspection, load your project settings and activate the tool you need:

~~~bash
source /mnt/work/projects/my_first_design/env.sh
conda activate /mnt/ref/software/envs/env-rfd3
~~~

- source loads settings into your current shell. conda activate selects an environment. The other prepared environments are env-ligandmpnn and env-boltz2 under /mnt/ref/software/envs. Continue to submit GPU calculations through Slurm.

##### Save your work

- After a run finishes, open PowerShell on Windows or Terminal on macOS/Linux on your laptop in the folder where you want to save your work. These scp commands work on all three systems and copy your inputs, code, settings and results through the same SSH connection:

~~~text
mkdir my_first_design_export
scp -r pdh-team:/mnt/work/projects/my_first_design/inputs pdh-team:/mnt/work/projects/my_first_design/src pdh-team:/mnt/work/projects/my_first_design/results my_first_design_export
scp pdh-team:/mnt/work/projects/my_first_design/env.sh pdh-team:/mnt/work/projects/my_first_design/run.sh my_first_design_export
~~~

- scp copies files between your laptop and the cluster; -r includes folders. Check the local files before cluster storage is removed. For large exports, ask the organiser for the approved shared destination.
- The prepared reference snapshot can restore /mnt/ref. It does not back up your new files in /mnt/work; follow the team’s work-backup policy.

#### Submitting Your Designs

- Designs are submitted as one FASTA file to a shared S3 bucket. **SUBMISSION.md**, alongside this guide, is the complete instruction: the file format, the catalytic residues you must declare in each header, the eligibility rules, what is scored, and the upload commands.
- Read it early rather than at the deadline. It ships with a validator you can run on your own machine, with no AWS and no network, which tells you whether your file would be accepted.
