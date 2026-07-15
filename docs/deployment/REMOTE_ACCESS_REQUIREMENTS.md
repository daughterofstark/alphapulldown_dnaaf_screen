# Remote Access Requirements

This document specifies what must be available on a remote Linux compute environment before this repository can run AlphaPulldown feature generation or structure prediction. It is intended for supervisors, Oxford systems administrators, HPC support engineers, and lab members provisioning the environment.

No Oxford-specific paths, partitions, accounts, or infrastructure assumptions are made here. Items marked "to be confirmed on the target system" must be verified with the actual compute provider before execution.

## 1. Project Overview

This project is a reproducible computational structural biology pipeline for screening protein-protein interaction hypotheses among mammalian Dynein Axonemal Assembly Factors, Outer Dynein Arm proteins, and Intraflagellar Transport proteins.

AlphaPulldown is required because it provides a systematic way to prepare AlphaFold-compatible protein features and run high-throughput multimer predictions from defined bait/prey or pairwise input sets.

Linux with NVIDIA GPU support is required because AlphaFold/AlphaPulldown inference depends on CUDA-capable acceleration. The local macOS machine is used only for validated input preparation, documentation, and downstream analysis.

Current repository status:

- CPU-side preparation layer is complete.
- Verified target FASTAs and AlphaPulldown input definitions are generated.
- Remote execution scripts and configuration templates are present.
- The remote workflow is pinned to AlphaPulldown/AlphaPulldownSnakemake `2.5.0`.
- AlphaPulldown has not been installed or run locally.

## 2. Minimum Compute Requirements

| Requirement | Minimum | Recommended / Notes |
|---|---|---|
| Operating system | Linux | Recent long-term-support server distribution. Exact distribution to be confirmed on the target system. |
| Linux distribution | Ubuntu, Rocky, AlmaLinux, RHEL, CentOS Stream, or equivalent | Must support NVIDIA drivers, CUDA runtime, Conda/Mamba, and container execution. |
| CPU | 8 cores | 16+ cores for feature generation and Snakemake orchestration. |
| RAM | 64 GB | 128 GB+ preferred for large proteins and database-backed MSA generation. |
| GPU | NVIDIA CUDA-capable GPU | A100/H100/L40S/A40/RTX 3090-class or comparable; exact supported models to be confirmed. |
| GPU memory | 24 GB minimum for small controls | 40-80 GB recommended for larger complexes; very large proteins may exceed practical limits. |
| CUDA version | Compatible with selected AlphaPulldown/AlphaFold container | Exact minimum to be confirmed from container and driver compatibility. |
| Recommended CUDA version | Modern CUDA stack supported by the deployed container | To be confirmed on the target system with `nvidia-smi` and container test. |
| Persistent storage | 200 GB+ for repository, features, logs, and selected results | More if storing many predictions or result pickles. |
| Scratch space | 500 GB+ recommended | Temporary MSA/template work can be large; quota to be confirmed. |
| Internet access | Required for initial Git clone, Conda environment creation, workflow deployment, containers, and optional MMseqs2 mode | If compute nodes lack internet, downloads must be staged by administrators. |
| Container support | Apptainer/Singularity or Docker | HPC environments usually prefer Apptainer/Singularity. |
| Python | Python compatible with AlphaPulldownSnakemake environment | Installed via the pinned Conda environment where possible. |
| Conda/Mamba | One of Conda or Mamba required | Mamba preferred for faster environment solving. |
| Snakemake | Installed by pinned workflow environment | Do not rely on a random system Snakemake without version confirmation. |

## 3. Required Software

### Required

- Git: clone the repository and track the exact branch/commit.
- Conda or Mamba: create the pinned remote workflow environment.
- Snakemake: workflow orchestration, installed through the pinned environment.
- Snakedeploy: deploy `KosinskiLab/AlphaPulldownSnakemake` tag `2.5.0`.
- AlphaPulldownSnakemake `2.5.0`: official Snakemake workflow.
- AlphaPulldown `2.5.0`: installed through the workflow/container environment.
- AlphaFold backend: AlphaFold2 or AlphaFold3 backend as selected for the run.
- NVIDIA driver and CUDA runtime compatible with the selected backend/container.
- Container runtime: Apptainer/Singularity or Docker, depending on the site.
- HHsuite: required for AlphaFold2-style database/template workflows.
- HMMER: required for sequence and template search workflows.
- Kalign: required by AlphaFold-style preprocessing.
- OpenMM: required for relaxation where enabled.
- ModelCIF support: required where backend output conversion uses ModelCIF.

### Optional

- Mamba: preferred replacement for Conda environment solving.
- Docker: useful on workstations; often not allowed on shared HPC compute nodes.
- Apptainer/Singularity: preferred on HPC if Docker is unavailable.
- APLit: optional downstream interactive browser for AlphaPulldown predictions.
- Existing local AlphaFold installation: optional if the workflow/container provides the backend.
- Existing local AlphaPulldown installation: optional; must match pinned version if used.
- Existing Snakemake profile: optional; must be reviewed before use.

## 4. Required Databases

The exact database set depends on whether the run uses AlphaFold2-style local database mode, AlphaFold3-style local database mode, or remote MMseqs2 mode. Database versions and layout must be confirmed on the target system.

| Database | Purpose | Requirement | Approximate storage / notes |
|---|---|---|---|
| UniRef90 | Sequence search/MSA generation | Mandatory for local database mode | Large; exact installed size depends on release. |
| MGnify | Metagenomic sequence search | Mandatory for local database mode | Large; release must match backend expectations. |
| BFD | Deep sequence database for AF2 full databases | Mandatory for AF2 full database mode | Very large, commonly hundreds of GB. |
| Small BFD | Reduced sequence database | Optional or mandatory for reduced DB mode | Smaller alternative to full BFD; exact use depends on `db_preset`. |
| PDB70 | Template search for AF2 | Mandatory for AF2 template workflow | Required for HHsearch-style template search. |
| PDB seqres | Template/sequence search | Mandatory for local database mode | Required by current AlphaPulldown database mapping. |
| UniProt | Multimer/sequence features | Mandatory for local database mode | Required by AlphaFold multimer-style pipelines. |
| Template mmCIF | Structure templates | Mandatory when templates are enabled | Includes mmCIF files; large and many small files. |
| Obsolete structures | Template filtering | Mandatory for AF2 template workflow | Usually `obsolete.dat` or equivalent. |

Expected database location:

```text
databases/
```

or another administrator-provided persistent directory configured as `DATABASES_DIR` in `config/remote/paths.env`.

Do not copy databases through this repository. Use existing centrally managed AlphaFold databases if available. If databases are absent, the administrator should provision them using site-approved procedures.

Remote MMseqs2 mode can reduce local database requirements, but for AlphaPulldown `2.5.0` this project treats MMseqs2 as an AlphaFold2 data-pipeline mode. Its availability and suitability are to be confirmed on the target system.

## 5. Required Permissions

The user or service account needs:

- SSH access to the remote host or login node.
- Read/write access to a project directory.
- Write access to persistent results storage.
- Write access to temporary scratch storage.
- Permission to create Conda/Mamba environments.
- Permission to execute Snakemake workflows.
- Permission to submit GPU jobs if using a scheduler.
- Permission to run containerized workloads if containers are used.
- Permission to access centrally installed AlphaFold databases.
- Permission to transfer selected results back using `rsync` or equivalent.

No secrets, credentials, or machine-specific paths should be committed to Git.

## 6. Scheduler

### Direct Workstation

A direct Linux workstation is acceptable if it has:

- NVIDIA GPU visible via `nvidia-smi`.
- Sufficient local storage and scratch space.
- Conda/Mamba and container support.
- Permission to run long jobs directly.

The workflow can run with the desktop Snakemake profile. Runtime limits and background-session handling are to be confirmed on the target system.

### SLURM Cluster

A SLURM cluster is acceptable if the following can be configured:

- GPU partition or QoS: to be confirmed.
- GPU request syntax: to be confirmed.
- GPU model availability: to be confirmed.
- GPU memory per model: to be confirmed.
- CPU and memory requests for feature generation: to be confirmed.
- Wall-time limits for feature generation and inference: to be confirmed.
- Job arrays or Snakemake job submission support: to be confirmed.
- Scratch directory policy: to be confirmed.
- Environment activation policy for Conda/Mamba: to be confirmed.
- Container execution policy and bind mounts: to be confirmed.

The repository provides SLURM-capable wrapper support, but it does not assume any site-specific partition, account, QoS, or path.

## 7. Data Layout

Recommended high-level layout:

```text
project/
  alphapulldown/
  databases/
  results/
  logs/
  scratch/
  containers/
```

Directory purposes:

- `project/`: parent directory controlled by the user or lab.
- `alphapulldown/`: Git clone of this repository.
- `databases/`: centrally installed or project-accessible AlphaFold databases; may be outside the project directory.
- `results/`: persistent AlphaPulldown outputs, generated features, score tables, and selected structures.
- `logs/`: Snakemake, job scheduler, and wrapper logs.
- `scratch/`: temporary working directory for large intermediate files.
- `containers/`: optional local container image cache or site-approved container location.

Actual paths must be entered in `config/remote/paths.env` on the remote system and should not be committed.

## 8. Data Transfer

Use Git for source code and tracked small data:

```bash
git clone <REPOSITORY_URL> alphapulldown
cd alphapulldown
git checkout feature/alphapulldown-implementation
```

Use `rsync` for generated FASTAs, prepared inputs, logs, and selected outputs when needed:

```bash
rsync -av data/processed/fasta/ <remote>:/path/to/project/alphapulldown/data/processed/fasta/
rsync -av data/processed/alphapulldown/ <remote>:/path/to/project/alphapulldown/data/processed/alphapulldown/
```

Do not transfer:

- Full AlphaFold databases.
- Large shared database caches.
- Large temporary scratch directories.
- Secrets or credentials.

Results copied back to local analysis should be limited to score tables, PAE files, ranked structures, logs, provenance, and selected result pickles only when needed.

## 9. Environment Validation

Run these checks before starting AlphaPulldown. Expected output should confirm availability and versions; failures should be resolved before feature generation or inference.

```bash
git --version
```

Expected: Git version is printed.

```bash
python3 --version
```

Expected: Python version is printed. The workflow environment may provide its own Python.

```bash
conda --version
mamba --version
```

Expected: at least one of Conda or Mamba is available.

```bash
snakemake --version
```

Expected: Snakemake version is printed after activating the workflow environment.

```bash
nvidia-smi
```

Expected: GPU model, driver version, CUDA compatibility, and GPU memory are visible.

```bash
docker --version
```

Expected: Docker version is printed if Docker is supported. Docker may be unavailable on HPC systems.

```bash
apptainer --version
singularity --version
```

Expected: at least one command works if the site uses Apptainer/Singularity.

Repository validation command after `paths.env` is configured:

```bash
bash scripts/remote/validate_remote_environment.sh
```

Expected: required paths, GPU, workflow, databases, Python, Snakemake, and AlphaPulldown availability are reported. Blocking failures return non-zero.

## 10. First Execution Checklist

1. Confirm remote Linux host or cluster allocation.
2. Confirm NVIDIA GPU availability and access.
3. Confirm AlphaFold database location or MMseqs2 policy.
4. Clone this repository.
5. Check out `feature/alphapulldown-implementation`.
6. Copy `config/remote/paths.example.env` to `config/remote/paths.env`.
7. Edit `config/remote/paths.env` with target-system paths.
8. Run `bash scripts/remote/bootstrap_remote_environment.sh --dry-run`.
9. Run `bash scripts/remote/bootstrap_remote_environment.sh`.
10. Run `bash scripts/remote/validate_remote_environment.sh`.
11. Run `bash scripts/remote/run_feature_generation.sh --dry-run`.
12. Run `bash scripts/remote/run_feature_generation.sh`.
13. Verify expected feature files under the configured output feature directory.
14. Run `bash scripts/remote/run_prediction.sh --screen controls --dry-run`.
15. Run `bash scripts/remote/run_prediction.sh --screen controls`.
16. Inspect control outputs and logs.
17. Run `bash scripts/remote/collect_results.sh --dry-run`.
18. Run `bash scripts/remote/collect_results.sh`.
19. Transfer selected collected outputs back with `rsync`.
20. Record the deployment in the log template below.

## 11. Questions for the HPC Administrator

- Which NVIDIA GPU models are available?
- How much GPU memory is available per model?
- What NVIDIA driver and CUDA compatibility version are installed?
- Is Apptainer or Singularity available?
- Is Docker available or prohibited?
- Are AlphaFold databases already installed?
- Where are the databases located?
- Which database versions/releases are installed?
- What is the scratch quota?
- What is the home/project storage quota?
- What is the maximum wall time for CPU jobs?
- What is the maximum wall time for GPU jobs?
- What is the maximum GPU count per job?
- Is internet access available from login nodes?
- Is internet access available from compute nodes?
- Are outbound HTTPS requests allowed for Conda, GitHub, containers, or MMseqs2?
- Is AlphaPulldown already installed?
- Is AlphaFold already installed?
- Is Snakemake already installed?
- Is a site-supported Snakemake profile available?
- Are container bind paths required for database, scratch, or results directories?
- Are there restrictions on long-running Snakemake controller processes?

## 12. Questions for My Supervisor

- Which compute resource should be preferred for the first execution?
- Should the first remote run use AlphaFold2 or AlphaFold3 backend?
- Does the lab already have an AlphaPulldown installation?
- Does the lab already have an AlphaFold installation?
- Does the lab already maintain AlphaFold databases?
- Are approved containers already available?
- Are existing SLURM scripts available from previous AlphaFold or AlphaPulldown work?
- Where should persistent outputs be stored?
- Which benchmark controls should be run first?
- Should feature generation use local databases or remote MMseqs2?
- Is runtime speed or strict reproducibility more important for the first validation run?
- Who should review the first control predictions before targeted screening begins?

## 13. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Database version mismatch | Features and templates may differ from expected results. | Record database paths and release versions; use one database set consistently. |
| Container mismatch | Workflow may fail or produce different output layout. | Pin container tags where possible and record image digests when available. |
| CUDA mismatch | JAX/AlphaFold inference may fail or run poorly. | Validate with `nvidia-smi` and a workflow dry run before submitting predictions. |
| Driver mismatch | Container may not see or use GPUs correctly. | Confirm driver-container compatibility with HPC support. |
| Insufficient storage | Feature generation or prediction may fail mid-run. | Confirm persistent and scratch quotas before execution. |
| Feature incompatibility | Prediction may not find generated feature files. | Use repository wrappers that rewrite inputs to verified FASTA paths and validate feature coverage. |
| Version drift | Upstream behavior may change if unpinned software is used. | Use pinned AlphaPulldown/AlphaPulldownSnakemake `2.5.0`; record commit SHA and environment versions. |
| Scheduler policy mismatch | Jobs may be rejected or killed. | Confirm partition, time, memory, GPU, and container policies before first submission. |
| Internet restrictions | Conda, GitHub, container pulls, or MMseqs2 may fail. | Stage environments, workflow, and containers through administrator-approved channels. |

## 14. Future Deployment Log

Copy and complete this template for each deployment attempt.

```text
Deployment ID:
Date:
Operator:
Machine / cluster:
Login node:
Compute node type:
Scheduler:

Repository URL:
Repository branch:
Repository commit:
Dirty worktree:

Operating system:
CPU architecture:
Python version:
Conda/Mamba version:
Snakemake version:

AlphaPulldown version:
AlphaPulldownSnakemake version:
AlphaFold backend:
Container runtime:
Container image/tag:

NVIDIA driver:
CUDA compatibility version:
GPU model:
GPU memory:
GPU count used:

Database root:
Database release/version:
Database completeness notes:

Persistent output path:
Scratch path:
Log path:

Command run:
Dry-run result:
Feature-generation result:
Prediction result:
Collection result:

Issues encountered:
Resolution:
Remaining follow-up:
Reviewer:
```
