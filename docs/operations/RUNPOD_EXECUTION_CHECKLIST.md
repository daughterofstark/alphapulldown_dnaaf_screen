# RunPod Docker-Native Execution Checklist

RunPod Pods use one native Docker image. They do not execute SIF files and do
not launch Docker, Apptainer, Singularity, or Snakemake containers from inside
the Pod.

Use `tmux` for every remote validation or scientific stage.

## Fixed Milestone 2 boundary

The RunPod runtime is limited to:

- `data/processed/benchmarks/milestone2_scenarios.json`;
- `data/processed/benchmarks/fasta/fasta_manifest.tsv`;
- `data/processed/benchmarks/alphapulldown_inputs/`;
- eight ready human scenarios.

The Chlamydomonas scenario remains blocked because versioned sequence records
are absent. The 62-target manifest at
`data/processed/fasta/fasta_manifest.tsv` is prohibited.

## Phase 0 - Direct-image proof of concept

Before building a derived image, start a short-lived GPU Pod using:

```text
image: kosinskilab/alphafold2:2.5.0
architecture: linux/amd64
volume mount: /workspace
container disk: at least 50 GB
start command: sleep infinity
```

In `tmux`, run only these no-data checks:

```bash
set -euo pipefail
nvidia-smi
pwd
python - <<'PY'
import importlib.metadata as metadata
print("alphapulldown=", metadata.version("alphapulldown"))
PY
git -C /AlphaPulldown rev-parse HEAD 2>/dev/null || true
command -v create_individual_features.py
command -v run_structure_prediction.py
create_individual_features.py --help >/dev/null
run_structure_prediction.py --help >/dev/null
python - <<'PY'
import jax
print("jax_devices=", jax.devices())
PY
```

Record the image digest, AlphaPulldown version/revision, CLI locations, JAX
devices, GPU, driver, and CUDA report. Stop the Pod immediately. These checks
must not retrieve sequences, generate features, or run inference.

## Phase A - Build and publish the derived image

Build outside RunPod from the repository root on an amd64 Docker builder:

```bash
docker buildx build \
  --platform linux/amd64 \
  --file deployment/runpod/Dockerfile \
  --tag <registry>/alphapulldown-runpod-af2:2.5.0-project \
  --load \
  .
```

Inspect and test the built image outside RunPod:

```bash
docker image inspect <registry>/alphapulldown-runpod-af2:2.5.0-project
docker run --rm \
  <registry>/alphapulldown-runpod-af2:2.5.0-project \
  python -m alphapulldown_dnaaf_screen.native_cli --help
```

Push only after review, then record the immutable registry digest in:

- `deployment/runpod/image-lock.json`;
- `ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST` in the uncommitted remote `paths.env`;
- the RunPod template image reference, preferably by digest.

Do not build images inside a RunPod Pod.

## Phase B - CPU MMseqs2 feature generation

Create a CPU Pod from the approved derived image. Attach the persistent volume
at `/workspace`. Outbound HTTPS is required for the MMseqs2 service.

```bash
tmux new -s alphapulldown-features
cd /workspace/alphapulldown
git checkout feature/alphapulldown-implementation
cp config/benchmarks/milestone2_remote.example.env config/remote/paths.env
```

Edit only machine/image identity values. Required settings include:

```bash
CONTAINER_RUNTIME="docker-native"
REMOTE_EXECUTION_STAGE="cpu"
FEATURE_MODE="mmseqs2"
NATIVE_DATA_PIPELINE="alphafold2"
NATIVE_FOLD_BACKEND="alphafold2"
NATIVE_ENABLE_ALPHAJUDGE="false"
FEATURE_FILE_PATTERN="{record_id}.pkl.xz"
ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST="sha256:<derived-image-digest>"
ALPHAPULLDOWN_EXPECTED_REVISION="<revision-confirmed-by-phase-0>"
```

Validate and dry-run:

```bash
bash scripts/remote/bootstrap_remote_environment.sh \
  --env-file config/remote/paths.env
bash scripts/remote/validate_remote_environment.sh \
  --env-file config/remote/paths.env
bash scripts/remote/run_native_stage.sh \
  --stage features \
  --env-file config/remote/paths.env \
  --dry-run
```

The dry run must show only `create_individual_features.py` commands with:

```text
--compress_features=True
--data_pipeline=alphafold2
--use_mmseqs2=True
--skip_existing=True
```

After explicit approval, feature generation is:

```bash
bash scripts/remote/run_native_stage.sh \
  --stage features \
  --env-file config/remote/paths.env
```

Preserve on `/workspace`:

- `results/milestone2_benchmark/features/*.pkl.xz`;
- `results/milestone2_benchmark/logs/`;
- `results/provenance/milestone2_benchmark/`;
- the exact uncommitted `paths.env` used for the run, copied into provenance
  with secrets removed.

## Phase C - A40 inference

Start the A40 only after all benchmark feature files exist. Use the same
derived image digest and persistent `/workspace` volume.

Update the uncommitted configuration:

```bash
REMOTE_EXECUTION_STAGE="gpu"
ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST="sha256:<same-derived-image-digest>"
```

Validate GPU and feature coverage without inference:

```bash
tmux new -s alphapulldown-predict
cd /workspace/alphapulldown
bash scripts/remote/validate_remote_environment.sh \
  --env-file config/remote/paths.env
bash scripts/remote/run_native_stage.sh \
  --stage predict \
  --env-file config/remote/paths.env \
  --dry-run
```

The dry run must show exactly eight `run_structure_prediction.py` commands,
each using:

```text
--features_directory=/workspace/alphapulldown/results/milestone2_benchmark/features
--fold_backend=alphafold2
```

After explicit approval, inference is:

```bash
bash scripts/remote/run_native_stage.sh \
  --stage predict \
  --env-file config/remote/paths.env
```

Stop the Pod immediately after inference or any blocking infrastructure error.
Preserve predictions, logs, and provenance on `/workspace`.

## Analysis boundary

AlphaJudge is not included in this runtime. The pinned upstream workflow uses a
separate analysis image, which cannot be launched inside the Pod. Interface
analysis requires a separately approved native image or local workflow.

## Historical Apptainer artifacts

Do not delete the completed SIF, checksum, inspect metadata, or historical
audits. They document earlier work but are not RunPod execution inputs.

These scripts are historical non-RunPod paths:

- `prepare_apptainer_image.sh`;
- `run_feature_generation.sh`;
- `run_prediction.sh`;
- AlphaPulldownSnakemake deployment/bootstrap when
  `CONTAINER_RUNTIME=apptainer`.
