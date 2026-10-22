# RunPod Container Offload Audit

> **Superseded for RunPod:** RunPod support confirmed that Pods cannot execute
> Apptainer/Singularity SIFs. This document is retained as historical evidence.
> Current RunPod execution uses the Docker-native design in
> `RUNPOD_DOCKER_NATIVE_MIGRATION_AUDIT.md` and
> `docs/operations/RUNPOD_EXECUTION_CHECKLIST.md`.

Date: 2026-07-25

Scope: determine whether AlphaPulldownSnakemake `2.5.0` container preparation can be moved off the A40 RunPod GPU pod before restarting paid GPU infrastructure.

## Current RunPod Failure

Observed facts:

- GPU pod: x86_64 Linux, NVIDIA A40.
- `/workspace`: persistent FUSE/network storage.
- `/` and `/tmp`: same 30 GB local overlay.
- `/dev/shm`: 26 GB.
- `docker://kosinskilab/alphafold2:2.5.0` was pulled by Apptainer.
- OCI extraction reached about 21 GB under `/workspace/apptainer/tmp`.
- SIF construction stalled during `proot -> mksquashfs`; the target SIF remained 0 bytes.
- No useful GPU compute occurred during this stage.

Conclusion: the failed step was container conversion, not AlphaFold inference. Paying for an A40 while Apptainer converts an OCI image is wasteful and risky.

## Upstream Evidence Inspected

Pinned upstream sources:

- `KosinskiLab/AlphaPulldownSnakemake` tag `2.5.0`
- `workflow/Snakefile`
- `config/config.yaml`
- `workflow/envs/alphapulldown.yaml`
- `README.md`

Relevant upstream behavior:

- `workflow/Snakefile` defines `container: config["prediction_container"]` for both `create_features` and `structure_inference`.
- `workflow/Snakefile` defines `container: config["analysis_container"]` for `analyze_structure` and `recursive_report`.
- `workflow/Snakefile` invokes `create_individual_features.py` in `rule create_features`; this is MSA/template/feature generation and does not call `nvidia-smi`.
- `workflow/Snakefile` invokes `run_structure_prediction.py` in `rule structure_inference`; this rule exports JAX/XLA GPU-related variables and queries `nvidia-smi`.
- `config/config.yaml` exposes `prediction_container` and `analysis_container` as ordinary config keys.
- `workflow/envs/alphapulldown.yaml` creates the orchestration environment with Snakemake, Snakedeploy, the SLURM plugin, and `alphapulldown-input-parser`; it does not install AlphaPulldown itself.
- The README documents local Snakemake execution and SLURM execution, but does not document a Docker-native profile for rule containers.

Supporting Snakemake/Apptainer behavior:

- Snakemake executes `container:` directives via software deployment, documented as `--software-deployment-method apptainer` / `--sdm apptainer`.
- Snakemake's CLI documents `--apptainer-prefix` as the directory where Apptainer/Singularity images are stored.
- Apptainer `pull` supports `docker://` sources but converts them into SIF images.
- Apptainer cache documentation says cache location is controlled by `APPTAINER_CACHEDIR` and should have enough space and atomic rename support; network filesystems can be problematic.

## Direct Prebuilt SIF Availability

I found no upstream AlphaPulldownSnakemake `2.5.0` evidence that `kosinskilab/alphafold2:2.5.0` is published as a directly downloadable SIF via `https://`, `oras://`, `library://`, or another SIF-native artifact.

The pinned workflow config uses:

```yaml
prediction_container: docker://kosinskilab/alphafold2:2.5.0
```

for AlphaFold2 mode, meaning the officially exposed artifact is an OCI/Docker image reference. If a prebuilt SIF exists privately or in an undocumented registry, it must be supplied explicitly by the lab or administrator and verified with `apptainer inspect`.

Current design assumption: no official prebuilt SIF is available.

## Can AlphaPulldownSnakemake Use Docker Directly on RunPod?

Not without changing the execution model.

The pinned workflow uses Snakemake `container:` directives. Snakemake's documented local container execution path for `container:` rules is Apptainer/Singularity via:

```bash
snakemake --software-deployment-method apptainer
```

Although the container URI begins with `docker://`, that URI is an Apptainer-supported source format; it does not mean Docker is used directly by Snakemake.

No upstream `2.5.0` profile was found that runs these rule containers through Docker directly. Snakemake has broader container/plugin capabilities, but using those would be a new execution architecture and should not be introduced before the first validated run.

Recommendation: do not try to make the A40 RunPod use Docker directly for this project milestone. Use Apptainer with a prebuilt local SIF.

## Can We Build the SIF Off-GPU?

Yes. The SIF should be built once on a cheap x86_64 CPU-only Linux machine with:

- Apptainer installed.
- Enough local non-FUSE disk for OCI extraction and `mksquashfs`.
- Persistent or transferable storage for the completed SIF.
- No GPU requirement.

The container build is architecture-specific. The RunPod GPU host is x86_64, so the SIF should be built on x86_64 Linux. Once built and verified, copy the completed SIF to persistent `/workspace` storage and configure AlphaPulldownSnakemake to use that local SIF path instead of the `docker://` URI.

This avoids OCI-to-SIF conversion on the A40 pod entirely.

## Snakemake Image Cache Strategy

Two strategies exist:

1. Pre-populate Snakemake's Apptainer cache for the `docker://kosinskilab/alphafold2:2.5.0` URI.
2. Preferable: override the workflow config key `prediction_container` to point directly at the completed local SIF path.

The second strategy is safer and more transparent because the pinned Snakefile uses:

```python
container: config["prediction_container"]
```

Therefore a resolved config can use:

```yaml
prediction_container: "/workspace/alphapulldown_results/containers/kosinskilab_alphafold2_2.5.0.sif"
```

Snakemake then receives a local image path rather than a `docker://` source, so it should not pull or convert that image. This also avoids depending on Snakemake's internal hash/cache naming. The SIF path, checksum, and `apptainer inspect` output can be recorded as project provenance.

If we still need to pre-populate Snakemake's own cache, that should be verified on the exact remote Snakemake version with a small test image first. Do not rely on guessed cache filenames for the production AlphaFold2 image.

## Compute Split by Stage

| Stage | GPU required? | Recommended machine | Notes |
|---|---:|---|---|
| Repository input preparation | No | Local Mac | Already implemented; deterministic FASTAs, manifests, sample sheets, configs. |
| Miniforge/Snakemake orchestration env | No | Cheap x86_64 CPU instance or GPU pod only after SIF exists | No AlphaPulldown import expected in `snake`. |
| Apptainer OCI-to-SIF conversion | No | Cheap x86_64 CPU instance | Needs local non-FUSE disk; avoid A40 rental. |
| MMseqs2 MSA / feature generation | No GPU expected | Cheap x86_64 CPU instance | Network/CPU/RAM heavy; uses `create_individual_features.py` inside prediction container. |
| Template search in MMseqs2 mode | No GPU expected | Cheap x86_64 CPU instance | Remote MMseqs2/API behavior may dominate runtime. |
| AlphaFold2/Multimer inference | Yes | A40 GPU pod | First truly GPU-dependent stage. |
| AlphaJudge / interface analysis | No GPU expected | CPU instance or after inference on GPU pod | Uses `analysis_container`; can be copied back and run CPU-side if configured. |
| Local review / APLit / ChimeraX | No | Local Mac | Use transferred structures, scores, PAE, logs, provenance. |

## Apple Silicon Mac Assessment

Building the production x86_64 SIF on Apple Silicon is not recommended.

Reasons:

- The target container is for Linux `amd64`/x86_64.
- The Mac is arm64.
- Apptainer on macOS requires a Linux VM such as Lima.
- Cross-architecture conversion would require emulation and large filesystem activity.
- The image already expands to about 21 GB before SIF construction, so this is not a small test case.
- Any subtle architecture mismatch would waste more time than renting a cheap x86_64 CPU instance.

Recommendation: use the Mac for repository preparation and analysis only. Use a cheap x86_64 Linux CPU VM for SIF build and feature generation.

## Recommended Architecture

1. Local Mac
   - Maintain repository.
   - Generate/validate FASTAs and AlphaPulldown inputs.
   - Review logs/results.

2. Cheap x86_64 CPU Linux instance
   - Install Miniforge/Snakemake/Apptainer.
   - Build `kosinskilab/alphafold2:2.5.0` into a SIF on local disk.
   - Verify SIF with `apptainer inspect`.
   - Copy completed SIF to persistent storage.
   - Optionally run MMseqs2 feature generation if internet and runtime are acceptable.

3. Persistent storage
   - Preserve repository clone or Git revision.
   - Preserve completed SIF.
   - Preserve generated per-protein feature files.
   - Preserve resolved configs, logs, and provenance.

4. A40 GPU pod
   - Pull latest repository changes.
   - Reuse the completed SIF.
   - Validate feature coverage.
   - Run inference only.

## Persistent Artifacts to Preserve

Required:

- `config/remote/paths.env` for the target machine, not committed.
- Completed AlphaFold2 SIF:
  - example: `/workspace/alphapulldown_results/containers/kosinskilab_alphafold2_2.5.0.sif`
- SIF checksum:
  - `sha256sum kosinskilab_alphafold2_2.5.0.sif`
- SIF inspection metadata:
  - `apptainer inspect kosinskilab_alphafold2_2.5.0.sif`
- Resolved feature config with `prediction_container` pointing at the local SIF.
- Per-protein feature outputs:
  - MMseqs2/AF2 mode: expected compressed feature pattern `*.pkl.xz`.
- Snakemake logs.
- Repository provenance:
  - commit SHA, branch, dirty state.

Optional:

- Apptainer OCI layer cache. This can save rebuild time but is not required once a valid SIF exists.
- Local build scratch. This should not be preserved.

Do not preserve:

- Partial `.building.*` SIF files.
- Zero-byte SIF targets.
- OCI extraction directories.
- Full AlphaFold databases on this project storage unless intentionally using local database mode.

## Disk Requirements

Conservative planning numbers:

- AlphaFold2 OCI extraction observed: about 21 GB.
- Local SIF build workspace: at least 35-40 GB free local non-FUSE disk recommended.
- Completed SIF: to be measured after successful build; reserve at least 15-25 GB.
- Apptainer persistent cache: reserve 25-40 GB if keeping OCI layers.
- Per-protein AF2/MMseqs2 feature files: variable; reserve at least 10-50 GB for the first panel, more for larger screens.
- Snakemake logs/provenance: small compared with features/containers.

RunPod A40 local overlay of 30 GB is too tight for safe OCI extraction plus SIF construction. `/dev/shm` at 26 GB is also too tight. Do not build the SIF there unless a smaller measured build requirement is proven.

## Failure and Recovery Plan

Container build failures:

- Build only on explicit local non-FUSE disk.
- Build to a temporary local SIF path.
- Validate with `apptainer inspect`.
- Move the completed SIF to persistent storage only after validation.
- If interrupted, move invalid/partial SIF files aside with a timestamp.
- Never overwrite a valid existing SIF unless explicitly forced.

Feature-generation failures:

- Reuse completed SIF.
- Keep `--skip_existing` in MMseqs2 feature mode.
- Preserve feature directory and logs.
- Rerun only missing features.

GPU inference failures:

- Validate SIF and feature coverage before starting GPU pod work.
- Run controls first.
- Keep inference output and logs on persistent storage.
- Stop the GPU pod immediately after a blocking infrastructure failure.

## Exact Next Commands for a Cheap x86_64 CPU Machine

Assumptions:

- CPU machine is x86_64 Linux.
- It has internet access.
- It has Apptainer.
- It has at least 40 GB free on a local non-FUSE disk, represented below as `/local_nvme`.
- It can write to persistent storage that can later be copied to RunPod `/workspace`.

Start a durable shell:

```bash
tmux new -s alphapulldown-cpu
```

Clone and configure:

```bash
git clone <REPOSITORY_URL> alphapulldown
cd alphapulldown
git checkout feature/alphapulldown-implementation
cp config/remote/paths.example.env config/remote/paths.env
```

Edit `config/remote/paths.env`:

```bash
FEATURE_MODE="mmseqs2"
DATABASES_DIR=""
BACKEND_WEIGHTS_DIR=""
APPTAINER_IMAGE_DIR="/persistent/alphapulldown/containers"
APPTAINER_PERSISTENT_CACHE_DIR="/persistent/alphapulldown/apptainer_cache"
APPTAINER_LOCAL_BUILD_DIR="/local_nvme/apptainer_build"
APPTAINER_MIN_LOCAL_FREE_GB="35"
APPTAINER_PREDICTION_IMAGE="docker://kosinskilab/alphafold2:2.5.0"
APPTAINER_PREDICTION_SIF="${APPTAINER_IMAGE_DIR}/kosinskilab_alphafold2_2.5.0.sif"
```

Verify local disk:

```bash
df -hT /local_nvme
findmnt -T /local_nvme -no TARGET,FSTYPE,SIZE,AVAIL
```

Build/verify SIF only:

```bash
bash scripts/remote/prepare_apptainer_image.sh --dry-run
bash scripts/remote/prepare_apptainer_image.sh
apptainer inspect /persistent/alphapulldown/containers/kosinskilab_alphafold2_2.5.0.sif
sha256sum /persistent/alphapulldown/containers/kosinskilab_alphafold2_2.5.0.sif \
  > /persistent/alphapulldown/containers/kosinskilab_alphafold2_2.5.0.sif.sha256
```

Optional CPU feature generation after SIF exists:

```bash
bash scripts/remote/rebuild_runpod_runtime.sh --dry-run
bash scripts/remote/rebuild_runpod_runtime.sh
source /workspace/miniforge3/etc/profile.d/conda.sh  # adjust if not using /workspace
conda activate snake
bash scripts/remote/bootstrap_remote_environment.sh --dry-run
bash scripts/remote/validate_remote_environment.sh
bash scripts/remote/run_feature_generation.sh --dry-run
```

Do not run feature generation until the container path override is implemented in the resolved Snakemake config.

## Proposed Repository Changes

Do not implement until reviewed:

1. Add `APPTAINER_PREDICTION_SIF` to remote config loading.
2. When `FEATURE_MODE=mmseqs2` and `APPTAINER_PREDICTION_SIF` is set, emit:

   ```yaml
   prediction_container: "/path/to/kosinskilab_alphafold2_2.5.0.sif"
   ```

   instead of `docker://kosinskilab/alphafold2:2.5.0`.

3. Add validation that the SIF exists and passes `apptainer inspect` before feature generation or prediction.
4. Keep `prepare_apptainer_image.sh` as the only script allowed to pull/convert the container.
5. Add `--software-deployment-method apptainer` and `--apptainer-prefix` explicitly to Snakemake command construction if not already present after current branch review.
6. Add offline tests that resolved configs use the local SIF path when configured.
7. Update RunPod checklist to split CPU-only SIF build, optional CPU feature generation, and GPU inference.

## Recommendation

Do not restart the A40 pod for container preparation.

Use a cheap x86_64 CPU Linux machine with enough local disk to build the SIF once. Preserve the completed SIF and its checksum on persistent storage. Then configure AlphaPulldownSnakemake to use that local SIF path directly. Use the A40 only after:

- the SIF exists,
- `apptainer inspect` passes,
- feature generation dry-run passes,
- feature files are present or ready to be generated,
- prediction dry-run passes.
