# RunPod Docker-Native Migration Audit

**Status:** superseded and rejected after the direct-image RunPod proof of
concept failed. Do not build or deploy the image described below. See
`RUNPOD_DOCKER_NATIVE_IMAGE_REAUDIT.md` for the replacement source-artifact
design and mandatory validation gates.

The failed Pod did not contain AlphaPulldown, either required CLI, or JAX.
Statements below describing `kosinskilab/alphafold2:2.5.0` as a suitable
runtime are retained only as historical audit context.

**Decision trigger:** RunPod support confirmed that Pods cannot execute Apptainer/Singularity SIFs, cannot enable unprivileged user namespaces, and cannot use Docker-in-Docker. The existing Apptainer/SIF handoff is therefore not executable on the target platform.

## Scope and fixed boundary

This audit concerns only the runtime model for the pinned upstream workflow:

- `KosinskiLab/AlphaPulldownSnakemake` tag `2.5.0`, commit
  `23cbba5f151f843d800b5cffaa7a3a3908c35d9e`.
- `kosinskilab/alphafold2:2.5.0` as the AlphaFold2 runtime image.

Milestone 2 remains closed and benchmark-only. The migration must continue to use:

- scenario manifest: `data/processed/benchmarks/milestone2_scenarios.json`;
- benchmark FASTA manifest:
  `data/processed/benchmarks/fasta/fasta_manifest.tsv`;
- benchmark inputs:
  `data/processed/benchmarks/alphapulldown_inputs/`;
- the eight versioned human scenarios only.

The Chlamydomonas scenario remains blocked. The runtime must never read, generate, or fall back to `data/processed/fasta/fasta_manifest.tsv`, the 62-target universe manifest.

## Evidence inspected

| Source | Relevant evidence | Consequence |
| --- | --- | --- |
| Upstream `workflow/Snakefile:27-47` | `--data_pipeline` selects AF2 `*.pkl`/`*.pkl.xz` versus AF3 `*_af3_input.json` output semantics. | The Docker-native runner must preserve the resolved Milestone 2 AF2 + MMseqs2 + `.pkl.xz` plan exactly. |
| Upstream `workflow/Snakefile:423-471` | `create_features` invokes `create_individual_features.py` in `config["prediction_container"]`. | The base image needs the AlphaPulldown feature command; the current Snakemake rule cannot run unchanged without a container backend. |
| Upstream `workflow/Snakefile:479-577` | `structure_inference` invokes `run_structure_prediction.py` in the same prediction container and consumes `features/`. | CPU feature and GPU prediction can use the same native AlphaFold2 image, with features persisted on `/workspace`. |
| Upstream `workflow/Snakefile:579-658` | structure analysis invokes `alphajudge` in a distinct `analysis_container`. | Automatic AlphaJudge analysis cannot be assumed in a one-image native run. It needs an explicitly designed second native image or a future combined image. |
| Upstream `workflow/rules/common.smk:385-420` | the workflow prepares `APPTAINER_*`/`SINGULARITY_*` binds and GPU settings. | This is specifically an Apptainer/Singularity integration point; it is not a Docker-native execution mode. |
| Upstream `workflow/envs/alphapulldown.yaml` | orchestration environment contains Python 3.12, Snakemake 9.*, Snakedeploy, and `alphapulldown-input-parser`; it does not install AlphaPulldown itself. | The workflow environment is orchestration-only. The prediction image supplies AlphaPulldown commands. |
| Upstream `README.md:28-33, 412-435` | documented Snakedeploy deployment and explicit AF2/MMseqs2 feature flags. | Keep pinned source and argument semantics as evidence, but do not invoke its container rules on RunPod. |
| Docker Registry v2 image manifest/config inspection, 2026-07-29 | `kosinskilab/alphafold2:2.5.0` resolves to an `linux/amd64` image; config has `/opt/nvidia/nvidia_entrypoint.sh` entrypoint, `/AlphaPulldown` working directory, CUDA 12.2.2 environment, and no default command. Build history installs Python 3.11, Kalign, ModelCIF, HMMER, HHsuite, OpenMM, JAX CUDA 12, then clones and installs AlphaPulldown. | The image is a plausible RunPod custom Pod image and AlphaPulldown runtime base. It needs an explicit long-running Pod command and runtime validation of its installed AlphaPulldown revision. |
| RunPod Pod documentation | RunPod Pods accept compatible registry images, configure an image, entrypoint/start command, environment, GPU, container disk, and a network-volume mount. RunPod itself runs Docker and does not support Docker Compose/Docker-in-Docker. | Docker is the outer Pod runtime only. No `docker run`, Docker socket, Apptainer, or SIF execution is part of the design. |

RunPod documentation: [Pods overview](https://docs.runpod.io/pods/overview), [Pod creation fields](https://docs.runpod.io/api-reference/pods/POST/pods), and [container command reference](https://docs.runpod.io/tutorials/introduction/containers/docker-commands).

## What the published AlphaFold2 image can do

### Direct custom image suitability

`kosinskilab/alphafold2:2.5.0` is suitable for a short **GPU Pod proof of concept** because it is an amd64 NVIDIA CUDA image, its working directory is `/AlphaPulldown`, and its build history installs AlphaPulldown with AF2-relevant runtime dependencies.

The image has:

- NVIDIA entrypoint: `/opt/nvidia/nvidia_entrypoint.sh`;
- no default `CMD`, so a RunPod template must supply one;
- Conda Python 3.11 on `PATH`;
- AlphaPulldown installed from a source checkout during image build;
- Kalign, ModelCIF, HMMER, HHsuite, OpenMM, and CUDA-enabled JAX in visible build history.

This establishes that it is the correct *runtime base* for the pinned AF2 workflow. It does **not** prove the exact installed AlphaPulldown Git commit, the availability of every command, or remote-MMseqs2 success. The image build history clones AlphaPulldown without a visible explicit checkout. Before any scientific job, a no-data proof of concept must record:

```bash
python - <<'PY'
import importlib.metadata as metadata
print("alphapulldown=", metadata.version("alphapulldown"))
PY
git -C /AlphaPulldown rev-parse HEAD 2>/dev/null || true
command -v create_individual_features.py
command -v run_structure_prediction.py
create_individual_features.py --help >/dev/null
run_structure_prediction.py --help >/dev/null
```

These commands do not retrieve sequences, generate features, or run inference.

### Does it include MMseqs2 feature-generation capability?

The image contains the documented AlphaPulldown feature-generation dependencies for a local-database AF2 path. The pinned workflow documents `--use_mmseqs2` as a remote API mode that skips local JackHMMER/HHsearch database lookups. That means the CPU stage does not require an NVIDIA GPU or local AlphaFold databases when this mode is selected.

However, the image metadata alone cannot prove the remote API path works from a particular Pod. The proof of concept must first confirm the CLI accepts `--use_mmseqs2`; a later, explicitly approved one-protein smoke test would be required to confirm outbound-network access and service compatibility. Do not claim MMseqs2 availability until that test is completed.

### Does it include the orchestration layer?

Not as a verified runtime contract. The pinned upstream orchestration environment explicitly installs Snakemake, Snakedeploy, and `alphapulldown-input-parser`, whereas the AlphaFold2 image’s visible build history does not install Snakemake or Snakedeploy. More importantly, installing Snakemake inside the image does not solve the problem: the pinned Snakefile contains `container:` directives, so running it would still request an inner container runtime.

Therefore:

- **Do not** use Docker-in-Docker.
- **Do not** invoke the current `run_feature_generation.sh` or `run_prediction.sh` implementation on RunPod after the migration; both construct Apptainer-based Snakemake commands.
- **Do not** attempt to reinterpret `docker://` in `prediction_container` as a direct Docker execution command. In the pinned workflow it is consumed by the Apptainer/Singularity container mechanism.

## Required Docker-native execution architecture

### Chosen model: one native runtime image, no nested containers

Build and publish a project-controlled, versioned image derived from the public runtime image. The Pod runs this one image directly; commands execute in the Pod container process namespace.

```text
FROM kosinskilab/alphafold2:2.5.0@<recorded-amd64-image-digest>

# Add pinned orchestration/parsing dependencies and project-native runner only.
# Do not install Docker, Apptainer, Singularity, or Snakemake container plugins.
```

The derived image must be built on an amd64-capable builder and published to a registry RunPod can pull. Pin the base image by its observed digest in the Dockerfile and record the derived image digest in provenance. The tag alone is insufficient for publication-grade reproducibility.

The derived image should add:

1. the pinned orchestration/parser dependencies from
   `workflow/envs/alphapulldown.yaml` (Python version compatibility must be resolved against the base image’s Python 3.11);
2. a small project-native runner that calls **only** the already pinned upstream CLIs:
   `create_individual_features.py` and `run_structure_prediction.py`;
3. a runtime validator that checks the installed AlphaPulldown package/commit, commands, resolved config, benchmark-only paths, and GPU availability for inference;
4. no source FASTAs, benchmark data, credentials, database, features, or results baked into the image.

The runner must parse the existing resolved JSON configuration rather than rebuilding biological inputs. It must reject:

- `alphafold3`, `_af3_input.json`, or any AF3 key in Milestone 2;
- a missing `--data_pipeline=alphafold2`, `--use_mmseqs2=True`, or `--skip_existing=True`;
- every non-Milestone 2 input path;
- the 62-target manifest path;
- the blocked Chlamydomonas scenario;
- an attempt to invoke analysis until a native AlphaJudge design is explicitly approved.

### Why not run the upstream Snakefile inside the derived image?

Snakemake can orchestrate native shell rules only after the upstream `container:` directives are removed or bypassed. Removing them in a fork would create a project-specific workflow variant that must be maintained against upstream. The smallest robust design is instead a narrow runner that preserves upstream CLI syntax and existing resolved config semantics, while bypassing only the unavailable nested-container layer.

This is a deliberate compatibility boundary:

- upstream source stays pinned and unmodified;
- the project does not change AlphaPulldown itself;
- the project-owned runner is tested against the upstream `create_features` and `structure_inference` command semantics;
- provenance records both upstream and derived-image identities.

### Structure analysis is a separate decision

The pinned workflow uses `docker://kosinskilab/alphajudge:latest` for analysis. A native single-container Pod cannot pull or launch that image itself. Initial native Milestone 2 execution should set the equivalent of `enable_structure_analysis: false` and stop after feature generation or inference outputs.

Before automated interface analysis is restored, choose and document one of:

1. a separately versioned, native AlphaJudge analysis Pod image that reads results from the persistent volume; or
2. a combined, pinned derived image that includes compatible AlphaJudge packages and has its license/dependency compatibility reviewed.

Manual local inspection and downstream analysis remain outside this migration plan.

## Pod configuration

### Persistent mount and data layout

Attach the same RunPod network volume to both CPU and GPU Pods at `/workspace`. Do not rely on the container disk for reproducible artifacts; RunPod documents persistent volume configuration separately from the container disk.

```text
/workspace/
  alphapulldown/                         # checked-out repository, pinned commit
  alphapulldown/data/processed/benchmarks/
    fasta/fasta_manifest.tsv             # benchmark-only manifest
    alphapulldown_inputs/                # benchmark-only inputs
  alphapulldown/results/milestone2_benchmark/
    features/                            # reusable *.pkl.xz features
    alphapulldown/predictions/           # inference outputs
    logs/
    tmp/
  alphapulldown/results/provenance/milestone2_benchmark/
  alphapulldown/runtime/                 # resolved native-run configs, image metadata
```

The Pod must not receive a mount or environment variable pointing to the 62-target manifest. The native runner should use explicit absolute benchmark paths and log all input paths before work begins.

### Required RunPod template settings

| Setting | CPU feature Pod | GPU prediction Pod |
| --- | --- | --- |
| Image | `<registry>/alphapulldown-runpod-af2:2.5.0-<project-revision>` | same immutable image digest |
| Architecture | `linux/amd64` | `linux/amd64` |
| Network volume mount | `/workspace` | same volume at `/workspace` |
| Container disk | at least 50 GB, to be confirmed against pulled-image unpacking | at least 50 GB, to be confirmed against pulled-image unpacking |
| Persistent volume | at least 150 GB initially; expand according to feature/prediction measurement | same volume, at least 150 GB initially |
| CPU / RAM | 8-16 vCPU and at least 64 GB RAM recommended; to be confirmed by one approved small feature test | at least 8 vCPU and 64 GB host RAM recommended; to be confirmed against the largest approved benchmark complex |
| GPU | none | one NVIDIA A40 (48 GB) or compatible GPU with at least 48 GB VRAM |
| CUDA | not required | host driver must be compatible with the base image CUDA 12.2.2 runtime; the previously observed RunPod driver/CUDA 12.8 is a candidate, not a guarantee |
| Start command | explicit idle command such as `bash -lc 'exec sleep infinity'`; confirm RunPod command-field escaping in the console | same |
| Network | outbound HTTPS required for remote MMseqs2 feature mode and registry pull | only if it must retrieve model weights or perform remote services; otherwise preserve results-only operation |

The 50 GB container-disk and 150 GB persistent-volume values are conservative starting recommendations, not measured requirements. Persistent needs will depend on model weights, temporary files, number of models, PAE files, and retained logs. Record actual peak usage after an approved one-scenario run.

### Environment variables

RunPod injects GPU access for a GPU Pod. Do not manually mount host device files or invoke Docker. Configure only project variables and documented NVIDIA runtime variables if the base image does not already set them:

```bash
HOME=/workspace/.home
TMPDIR=/workspace/alphapulldown/results/milestone2_benchmark/tmp
PYTHONPATH=/workspace/alphapulldown/src
REMOTE_EXECUTION_STAGE=cpu                 # change to gpu on the GPU Pod
FEATURE_MODE=mmseqs2
NVIDIA_VISIBLE_DEVICES=all                 # GPU Pod only; base image already declares this
NVIDIA_DRIVER_CAPABILITIES=compute,utility # GPU Pod only; base image already declares this
XLA_PYTHON_CLIENT_PREALLOCATE=false        # GPU Pod; validate with first inference
TF_FORCE_UNIFIED_MEMORY=true               # GPU Pod; validate with first inference
```

Do not store tokens, registry credentials, or API keys in versioned environment files. Registry authentication belongs in RunPod’s registry configuration, if required.

## Stage separation

| Stage | Image and host | GPU | Inputs | Outputs | Notes |
| --- | --- | --- | --- | --- | --- |
| Mac preparation | local repository tools | no | versioned records | benchmark FASTAs/inputs/configs | unchanged; no container runtime required |
| CPU feature generation | derived Docker image on x86_64 CPU Pod | no | independent benchmark FASTA manifest and input files | `features/*.pkl.xz`, logs, provenance | uses AF2 + remote MMseqs2 only; outbound network required |
| GPU inference | same derived image on GPU Pod | yes | existing `.pkl.xz` features and benchmark pair input | prediction directories, ranked structures, confidence/PAE files, provenance | must not regenerate MSA/features unless an explicit future flag permits it |
| Interface analysis | separate future native analysis image or local workflow | no expected | prediction outputs | `interfaces.csv` / reports if approved | not part of first native proof of concept |

The CPU and GPU Pods share no container cache or SIF. Their only handoff is the mounted persistent volume: verified benchmark inputs, resolved configuration, `.pkl.xz` features, logs, and provenance.

## Smallest safe proof of concept

Use a short-lived GPU Pod for this exact image-only validation because the base image uses NVIDIA runtime plumbing. This incurs only Pod startup time and performs no feature generation, inference, sequence retrieval, or database download.

1. Create a GPU Pod using the public image `kosinskilab/alphafold2:2.5.0`, attach the existing network volume at `/workspace`, and set an explicit idle start command.
2. In `tmux`, run:

```bash
set -euo pipefail
nvidia-smi
pwd
printf 'working directory: %s\n' "$PWD"
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
try:
    import jax
    print("jax_devices=", jax.devices())
except Exception as exc:
    raise SystemExit(f"JAX GPU preflight failed: {exc}")
PY
```

3. Record stdout, `nvidia-smi`, package version, AlphaPulldown source revision if available, and image digest under `results/provenance/milestone2_benchmark/`.
4. Stop the Pod immediately after the check.

Passing this proof of concept establishes only that the direct image can run as a RunPod Pod and expose the expected AlphaPulldown/JAX commands. It does not validate remote MMseqs2, feature generation, model weights, prediction, or analysis.

## Implementation plan after approval

1. Add a Docker-native execution specification and immutable image lock file under `deployment/` or `config/remote/`. The lock records base-image manifest digest, derived-image digest, upstream commits, and package versions.
2. Add a derived Dockerfile and build documentation. Build outside a Pod or through a registry-supported build process; never build Docker images inside RunPod.
3. Add a minimal Python/shell native runner with two commands: `features` and `predict`. It consumes current benchmark-only resolved JSON, directly invokes the two AlphaPulldown scripts, and writes provenance.
4. Add an explicit `CONTAINER_RUNTIME=docker-native` configuration mode. It must reject all `APPTAINER_*` variables and prevent old remote scripts from running in that mode.
5. Update remote validation to check the outer container identity, command availability, stage-specific GPU availability, benchmark isolation, feature coverage, and writable persistent paths. It must not check for Docker, Apptainer, SIFs, Snakemake profiles, or nested execution.
6. Replace the old RunPod checklist with Docker-native CPU and GPU phases. Mark all SIF conversion and Apptainer procedures as retired for RunPod; keep them only as historic non-RunPod documentation if useful.
7. Add offline tests for strict Milestone 2 path isolation, exact AF2/MMseqs2 argument assembly, native image metadata validation, no Apptainer/Docker-in-Docker command construction, CPU/GPU stage gates, and provenance identity.
8. Run the direct-image proof of concept before building the derived image. Only after it passes, build and test the derived image. Feature generation and inference each require separate explicit approval.

## Proposed changed files

No files below are changed in this audit. They are the minimal expected change set after approval.

| File | Proposed change |
| --- | --- |
| `deployment/runpod/Dockerfile` | New pinned amd64 derived image based on `kosinskilab/alphafold2:2.5.0`, adding only required orchestration/parser and project runner dependencies. |
| `deployment/runpod/image-lock.json` | New immutable base/derived image digests, package versions, upstream commits, and build timestamp. |
| `scripts/remote/run_native_stage.sh` | New direct native feature/prediction wrapper; no Snakemake container execution, Docker CLI, Apptainer, or SIF handling. |
| `src/alphapulldown_dnaaf_screen/native_runtime.py` | New validated command/config construction for direct AlphaPulldown CLI invocation. |
| `src/alphapulldown_dnaaf_screen/remote.py` | Refactor only after approval: retain preparation/benchmark selection helpers but separate or retire Apptainer-specific execution path. |
| `scripts/remote/validate_remote_environment.sh` | Add Docker-native outer-runtime preflight; remove RunPod requirement for Apptainer/SIF execution in the new mode. |
| `config/remote/paths.example.env` | Add explicit runtime mode and native-image variables; do not make a silent default change. |
| `config/benchmarks/milestone2_remote.example.env` | Preserve benchmark paths; replace Apptainer-only variables after native runner exists. |
| `docs/operations/RUNPOD_EXECUTION_CHECKLIST.md` | Replace SIF phases with image proof-of-concept, CPU native feature stage, and GPU native inference stage. |
| `docs/validation/RUNPOD_CONTAINER_OFFLOAD_AUDIT.md` | Mark the SIF recommendation superseded for RunPod, not deleted. |
| `tests/test_native_runtime.py` | New offline tests for command construction, no nested runtime, AF2/MMseqs2 enforcement, and benchmark isolation. |

## Risks and recovery

| Risk | Mitigation |
| --- | --- |
| Base image tag does not correspond to the intended AlphaPulldown source revision | Record package version and `/AlphaPulldown` commit during no-data POC; reject image promotion if it cannot be reconciled with the pinned release. |
| Public image lacks a needed CLI or remote MMseqs2 dependency | POC checks `--help`; then use one explicitly approved minimal test before scientific production. Do not patch production image ad hoc. |
| GPU/JAX incompatibility | Run `jax.devices()` before data work; retain complete environment/provenance; choose a compatible RunPod GPU/driver if it fails. |
| Remote MMseqs2 unavailable from Pods | Treat as a network/service blocker. Do not fall back to local databases or different feature pipelines silently. |
| Persistent volume insufficient | Monitor volume usage and preserve only agreed artifacts. Never retain OCI/SIF caches in this design. |
| Old Apptainer wrappers accidentally used | Require explicit `CONTAINER_RUNTIME=docker-native`, reject `APPTAINER_*` in the native runner, and test the rejection. |
| Analysis output expected automatically | Disable upstream analysis in initial native stages and state clearly that AlphaJudge needs a separately approved native design. |

## Decision requested before implementation

Approve these two decisions explicitly:

1. build a project-derived amd64 Docker image from the public AlphaFold2 image and run AlphaPulldown feature/prediction CLIs directly in the Pod; and
2. defer automated AlphaJudge analysis until a separate native analysis runtime has been pinned and validated.

Until then, the completed SIF is preserved as a historical artifact but is not a RunPod execution input. No biological records, benchmark scenarios, FASTAs, or outputs should change.
