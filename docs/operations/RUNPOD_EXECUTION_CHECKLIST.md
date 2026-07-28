# RunPod Execution Checklist

This checklist separates container preparation, feature generation, and GPU inference so the A40 pod is used only when GPU inference is actually needed.

Frozen architecture:

- Mac: repository maintenance, input preparation, local review.
- Cheap x86_64 CPU Linux: AlphaFold2 SIF preparation and optional MMseqs2 feature generation.
- Persistent storage: completed SIF, checksum, inspect metadata, features, configs, logs, provenance.
- A40 GPU: inference only, plus optional downstream analysis.

Use `tmux` for every long-running remote command:

```bash
tmux new -s alphapulldown
```

## Before Any Remote Machine

Confirm:

- Git branch: `feature/alphapulldown-implementation`.
- Planned panel: `data/processed/alphapulldown/girish_refined_runpod_first_run.tsv`.
- First biological control: human DNAAF18/ODA16-IFT46 negative/species-divergence control.
- Feature mode: `mmseqs2` unless local AlphaFold databases are explicitly available.
- Persistent storage location for SIF/features/logs/provenance.
- Budget for CPU instance and separate A40 GPU pod.

Do not start an A40 pod until Phase A has produced a valid SIF.

A valid SIF is not sufficient: the target host must also be able to execute it.
The RunPod CPU host observed on 2026-07-28 could inspect the SIF but could not
create an unprivileged user namespace, so it could not run Apptainer at all.
This is host policy, not a repository or image defect.

## Phase A - CPU Container Preparation

Use a cheap x86_64 Linux CPU machine with:

- Apptainer installed.
- Internet access.
- At least 35-40 GiB free on local non-FUSE storage for the AlphaFold2 OCI-to-SIF conversion.
- Persistent storage for the completed SIF and metadata.

Fresh RunPod Ubuntu CPU pods do not include Apptainer. Install it before Phase A
container preparation:

```bash
cd /tmp
wget -O apptainer_1.5.3_amd64.deb \
  https://github.com/apptainer/apptainer/releases/download/v1.5.3/apptainer_1.5.3_amd64.deb
apt-get install -y ./apptainer_1.5.3_amd64.deb
apptainer --version
```

Clone the repository:

```bash
tmux new -s alphapulldown-cpu
git clone <REPOSITORY_URL> alphapulldown
cd alphapulldown
git checkout feature/alphapulldown-implementation
cp config/remote/paths.example.env config/remote/paths.env
```

Edit `config/remote/paths.env` for the CPU machine:

```bash
REMOTE_PROJECT_ROOT="<absolute path to repo>"
AP_WORKFLOW_DIR="<absolute persistent path>/workflows/AlphaPulldownSnakemake"
REMOTE_EXECUTION_STAGE="cpu"
FEATURE_MODE="mmseqs2"
DATABASES_DIR=""
BACKEND_WEIGHTS_DIR=""

OUTPUT_DIR="<absolute persistent path>/alphapulldown_results/alphapulldown"
FEATURE_DIR="${OUTPUT_DIR}/features"
LOG_DIR="<absolute persistent path>/alphapulldown_results/logs"
TMP_DIR="<absolute persistent path>/alphapulldown_results/tmp"
PROVENANCE_DIR="<absolute persistent path>/alphapulldown_results/provenance"

APPTAINER_IMAGE_DIR="<absolute persistent path>/alphapulldown_results/containers"
APPTAINER_PERSISTENT_CACHE_DIR="<absolute persistent path>/alphapulldown_results/apptainer_cache"
APPTAINER_PREFIX="${APPTAINER_IMAGE_DIR}/snakemake_apptainer"
APPTAINER_LOCAL_BUILD_DIR="<absolute local non-FUSE build path>"
APPTAINER_MIN_LOCAL_FREE_GB="35"
APPTAINER_PREDICTION_IMAGE="docker://kosinskilab/alphafold2:2.5.0"
APPTAINER_PREDICTION_SIF="${APPTAINER_IMAGE_DIR}/kosinskilab_alphafold2_2.5.0.sif"
```

Inspect candidate local filesystems before choosing `APPTAINER_LOCAL_BUILD_DIR`:

```bash
df -hT /
df -hT /tmp
df -hT /dev/shm
findmnt -T / -no TARGET,FSTYPE,SIZE,AVAIL
findmnt -T /tmp -no TARGET,FSTYPE,SIZE,AVAIL
findmnt -T /dev/shm -no TARGET,FSTYPE,SIZE,AVAIL
findmnt -T <candidate-local-build-path> -no TARGET,FSTYPE,SIZE,AVAIL
```

Do not use FUSE/network storage for `APPTAINER_LOCAL_BUILD_DIR`. Do not blindly use `/tmp`; on the failed RunPod it shared the same 30 GB overlay as `/`.

Prepare only the container image. This step requires Apptainer but does not
require Conda, Snakemake, CUDA, or a GPU:

```bash
cd <repo>

bash scripts/remote/prepare_apptainer_image.sh --dry-run
bash scripts/remote/prepare_apptainer_image.sh
```

Required Phase A artifacts:

- `${APPTAINER_PREDICTION_SIF}`; the verified RunPod CPU build produced
  `/workspace/alphapulldown/results/containers/kosinskilab_alphafold2_2.5.0.sif`
  at 6.9 GB from `kosinskilab/alphafold2:2.5.0` for `amd64`.
- `${APPTAINER_PREDICTION_SIF}.sha256`
- `${APPTAINER_PREDICTION_SIF}.inspect.txt`
- `config/remote/paths.env` for the CPU machine
- logs under the configured log/provenance locations

Verify:

```bash
apptainer inspect "${APPTAINER_PREDICTION_SIF}"
sha256sum -c "${APPTAINER_PREDICTION_SIF}.sha256"
apptainer exec "${APPTAINER_PREDICTION_SIF}" true
```

The final command must succeed before moving to Phase B. If it reports that a
user namespace cannot be created, stop before Snakemake. Do not modify
`/proc/sys/kernel/unprivileged_userns_clone` from inside a pod. Ask the platform
administrator for a supported runtime: Apptainer documents unprivileged user
namespaces as necessary for non-SUID operation, and documents the official
`apptainer-suid` package as the supported alternative where appropriate.
See the [Apptainer installation guide](https://apptainer.org/docs/admin/latest/installation.html)
and [user namespace requirements](https://apptainer.org/docs/admin/main/user_namespace.html).

## Phase B - CPU Feature Generation

Feature generation in MMseqs2 mode is CPU/network work. It should run on the CPU machine after the local SIF exists.

If the CPU machine uses a RunPod-compatible `/workspace` layout, runtime
tooling can be rebuilt with:

```bash
bash scripts/remote/rebuild_runpod_runtime.sh --dry-run
bash scripts/remote/rebuild_runpod_runtime.sh
```

On a generic Linux CPU VM, use a site/local Miniforge or Mamba installation and
create the pinned `snake` environment from the AlphaPulldownSnakemake `2.5.0`
environment YAML. Keep the installation on persistent storage if feature
generation may be resumed later.

Validate without starting jobs:

```bash
export PATH="<miniforge>/bin:$PATH"
source <miniforge>/etc/profile.d/conda.sh
conda activate snake
cd <repo>

bash scripts/remote/bootstrap_remote_environment.sh --dry-run
bash scripts/remote/validate_remote_environment.sh
bash scripts/remote/run_feature_generation.sh --dry-run
```

`validate_remote_environment.sh` now distinguishes an installed Apptainer
binary from an executable configured SIF. It runs the harmless preflight
`apptainer exec "${APPTAINER_PREDICTION_SIF}" true`; failure is blocking and
must be resolved by the platform administrator before any feature job starts.

For the completed RunPod CPU Phase A, `config/remote/paths.env` should include:

```bash
REMOTE_EXECUTION_STAGE="cpu"
REMOTE_PROJECT_ROOT="/workspace/alphapulldown"
AP_WORKFLOW_DIR="/workspace/workflows/AlphaPulldownSnakemake"
FEATURE_MODE="mmseqs2"
DATABASES_DIR=""
BACKEND_WEIGHTS_DIR=""
APPTAINER_PREDICTION_SIF="/workspace/alphapulldown/results/containers/kosinskilab_alphafold2_2.5.0.sif"
APPTAINER_PREFIX="/workspace/alphapulldown/results/containers/snakemake_apptainer"
FEATURE_DIR="/workspace/alphapulldown/results/alphapulldown/features"
OUTPUT_DIR="/workspace/alphapulldown/results/alphapulldown"
LOG_DIR="/workspace/alphapulldown/results/logs"
TMP_DIR="/workspace/alphapulldown/results/tmp"
PROVENANCE_DIR="/workspace/alphapulldown/results/provenance"
```

For the Milestone 2 benchmark, use the benchmark-only remote environment so
feature generation cannot fall back to the 62-target universe:

```bash
cp config/benchmarks/milestone2_remote.example.env config/remote/paths.env
sed -n '1,220p' config/remote/paths.env
```

Confirm these benchmark-specific paths before any dry run:

```bash
grep -E '^(FASTA_MANIFEST|ALPHAPULLDOWN_INPUT_DIR|FEATURE_DIR|OUTPUT_DIR|LOG_DIR|TMP_DIR|PROVENANCE_DIR)=' \
  config/remote/paths.env
```

Expected Milestone 2 path wiring:

- `FASTA_MANIFEST=/workspace/alphapulldown/data/processed/benchmarks/fasta/fasta_manifest.tsv`
- `ALPHAPULLDOWN_INPUT_DIR=/workspace/alphapulldown/data/processed/benchmarks/alphapulldown_inputs`
- `FEATURE_DIR=/workspace/alphapulldown/results/milestone2_benchmark/features`
- `OUTPUT_DIR=/workspace/alphapulldown/results/milestone2_benchmark/alphapulldown`
- `LOG_DIR=/workspace/alphapulldown/results/milestone2_benchmark/logs`
- `TMP_DIR=/workspace/alphapulldown/results/milestone2_benchmark/tmp`
- `PROVENANCE_DIR=/workspace/alphapulldown/results/provenance/milestone2_benchmark`

Run feature generation only after the dry run resolves `prediction_container` to the local SIF path, not `docker://kosinskilab/alphafold2:2.5.0`:

```bash
bash scripts/remote/bootstrap_remote_environment.sh --dry-run
bash scripts/remote/validate_remote_environment.sh
bash scripts/remote/run_feature_generation.sh
```

Check Milestone 2 feature coverage after feature generation:

```bash
PYTHONPATH=src python -m alphapulldown_dnaaf_screen.remote_cli \
  --config config/remote/paths.env \
  check-feature-coverage \
  --screen milestone2 \
  --json
```

Required Phase B artifacts:

- `${FEATURE_DIR}/*.pkl.xz`
- resolved feature config under `${PROVENANCE_DIR}/feature-*/feature_generation.config.json`
- feature input file under `${PROVENANCE_DIR}/feature-*/feature_inputs.txt`
- feature-generation logs under `${LOG_DIR}`
- provenance under `${PROVENANCE_DIR}`
- completed SIF and its `.sha256` / `.inspect.txt`

Transfer CPU artifacts to persistent storage or the future GPU pod:

```bash
rsync -avh --progress "${APPTAINER_IMAGE_DIR}/" <gpu-or-persistent-host>:"${APPTAINER_IMAGE_DIR}/"
rsync -avh --progress "${FEATURE_DIR}/" <gpu-or-persistent-host>:"${FEATURE_DIR}/"
rsync -avh --progress "${LOG_DIR}/" <gpu-or-persistent-host>:"${LOG_DIR}/"
rsync -avh --progress "${PROVENANCE_DIR}/" <gpu-or-persistent-host>:"${PROVENANCE_DIR}/"
```

Do not transfer Apptainer temporary build directories or OCI extraction directories.

## Phase C - GPU Inference

Start the A40 GPU pod only after Phase A has a valid SIF and Phase B has either completed features or a deliberate decision to generate features elsewhere.

Immediately record for reimbursement:

- Pod ID.
- GPU type.
- Hourly rate.
- Template/container tag if visible.
- Volume size.
- Start time.
- Screenshot or receipt filename.

On the A40 pod:

```bash
tmux new -s alphapulldown-gpu
cd /workspace
git clone <REPOSITORY_URL> alphapulldown
cd /workspace/alphapulldown
git checkout feature/alphapulldown-implementation
cp config/remote/paths.example.env config/remote/paths.env
```

Edit `config/remote/paths.env` so the GPU machine points at the transferred artifacts:

```bash
FEATURE_MODE="mmseqs2"
REMOTE_EXECUTION_STAGE="gpu"
DATABASES_DIR=""
BACKEND_WEIGHTS_DIR=""
APPTAINER_PREDICTION_SIF="/workspace/alphapulldown_results/containers/kosinskilab_alphafold2_2.5.0.sif"
APPTAINER_PREFIX="/workspace/alphapulldown_results/containers/snakemake_apptainer"
FEATURE_DIR="/workspace/alphapulldown_results/alphapulldown/features"
OUTPUT_DIR="/workspace/alphapulldown_results/alphapulldown"
LOG_DIR="/workspace/alphapulldown_results/logs"
TMP_DIR="/workspace/alphapulldown_results/tmp"
PROVENANCE_DIR="/workspace/alphapulldown_results/provenance"
```

If RunPod host migration corrupts Conda, rebuild runtime tooling only:

```bash
bash scripts/remote/rebuild_runpod_runtime.sh --dry-run
bash scripts/remote/rebuild_runpod_runtime.sh
```

Validate existing SIF/features before inference:

```bash
export PATH="/workspace/miniforge3/bin:$PATH"
source /workspace/miniforge3/etc/profile.d/conda.sh
conda activate snake
cd /workspace/alphapulldown

sha256sum -c "${APPTAINER_PREDICTION_SIF}.sha256"
apptainer inspect "${APPTAINER_PREDICTION_SIF}"
apptainer exec "${APPTAINER_PREDICTION_SIF}" true
bash scripts/remote/bootstrap_remote_environment.sh --dry-run
bash scripts/remote/validate_remote_environment.sh
bash scripts/remote/run_prediction.sh --screen milestone2 --dry-run
```

Run the Milestone 2 benchmark first:

```bash
bash scripts/remote/run_prediction.sh --screen milestone2
```

After controls:

- Inspect logs.
- Confirm output directories were created.
- Confirm score/ranking files exist.
- Confirm no GPU out-of-memory or feature-coverage failures occurred.
- Stop the pod immediately if infrastructure fails before inference begins.

Only then proceed to Girish-refined candidate jobs marked `include_by_default=true`.

## Collect Outputs

Dry-run collection:

```bash
bash scripts/remote/collect_results.sh --dry-run
```

Collect outputs:

```bash
bash scripts/remote/collect_results.sh
```

Save:

- `results/provenance/`
- `results/logs/`
- collected structures and score tables
- PAE files
- RunPod receipt or screenshot

## Stop the GPU Pod

When the run is complete or paused:

1. Copy required outputs to persistent storage or local machine.
2. Confirm reimbursement log is updated.
3. Stop the pod.
4. Confirm billing has stopped.
5. Record stop time and final estimated cost.

## Minimum Run Record

For every CPU or GPU session, record:

- Date.
- Machine/provider.
- GPU type, if any.
- Hourly rate, if any.
- Start and stop time.
- Commands run.
- Outputs generated.
- Issues encountered.
- Receipt or screenshot filename, if applicable.
