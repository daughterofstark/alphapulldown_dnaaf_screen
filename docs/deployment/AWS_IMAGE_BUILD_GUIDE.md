# AWS Image Build Guide

This is the AWS route for the isolated Milestone 2 AlphaPulldown benchmark.
Feature generation and prediction remain separate, explicitly approved stages.

## What AWS is for

AWS provides normal Linux machines. We will use:

1. a CPU machine to build and test the Docker image; and
2. later, a short GPU machine session to confirm that the tested image can see
   an NVIDIA GPU.

The $100 account credit can be applied to eligible usage after the account is
on a Paid plan. It is not necessary to use a GPU for the CPU image build.

## Files that define the image

- `deployment/aws/Dockerfile`: candidate image definition.
- `deployment/aws/environment-af2.yml`: native AlphaFold2 dependencies.
- `deployment/aws/requirements-af2.txt`: Python runtime constraints.
- `deployment/aws/smoke_cpu.py`: no-data build test.
- `deployment/aws/smoke_gpu.py`: no-data GPU test.

The image uses an immutable NVIDIA CUDA amd64 base and verifies the SHA-256 of
the official AlphaPulldown 2.5.0 wheel. It does not rely on the rejected public
`kosinskilab/alphafold2:2.5.0` image.

The repository's planning package deliberately is not installed in this image:
it requires Python 3.11 or later, while the pinned AlphaPulldown 2.5.0
AlphaFold2 runtime uses Python 3.10. The candidate image contains only the
AlphaPulldown runtime required for the smoke gates.

The first build records the exact resolved Conda and pip packages inside the
image at `/opt/alphapulldown-runtime/`.

## Completed validation

On 2026-08-29, the local image `alphapulldown-af2:candidate` passed both
no-data smoke gates on AWS EC2. The Docker local image ID is recorded in
`deployment/aws/image-lock.json`:

- CPU gate: AlphaPulldown `2.5.0`, AlphaFold dependencies, and
  `create_individual_features.py` loaded successfully.
- GPU gate: an AWS `g5.xlarge` NVIDIA A10G was passed into Docker; JAX `0.5.3`
  reported `CudaDevice(id=0)` and `run_structure_prediction.py` loaded.

This proves the runtime can execute AlphaPulldown on the target platform. It
does not constitute a feature-generation or prediction result.

## CPU build gate

On an AWS x86_64 Linux CPU machine with Docker installed, from the repository
root:

```bash
bash scripts/aws/build_candidate_image.sh \
  <your-ecr-image-uri>:alphapulldown-af2-candidate
```

This builds the image for `linux/amd64` and reruns its CPU smoke test. The
smoke test checks AlphaPulldown 2.5.0, AlphaFold, ColabFold, JAX, OpenMM, the
feature-generation module, and `create_individual_features.py --help`. The
upstream CLI may return status `1` after printing valid help, so the smoke test
also requires its `use_mmseqs2` option to be present. It
does not read project sequences, contact MMseqs2, create features, download
model parameters, or predict structures.

If this command fails, stop. Do not start a GPU machine. Preserve the Docker
build log.

## GPU gate

After the CPU image is pushed to a registry and pulled onto an AWS NVIDIA GPU
machine:

```bash
bash scripts/aws/smoke_gpu_image.sh \
  <your-ecr-image-uri>:alphapulldown-af2-candidate
```

This runs `nvidia-smi`, confirms JAX 0.5.3 sees an NVIDIA GPU, imports the
prediction module, and runs `run_structure_prediction.py --help`. It uses no
biological data and starts no AlphaFold prediction.

The resulting local Docker image ID is now locked in
`deployment/aws/image-lock.json`. It is an image ID on the existing EC2 disk,
not an ECR registry digest; do not assume it exists on a different machine.

## Safe AWS resume and dry-run

The validated image remains on the EC2 instance's EBS volume while the
instance is stopped. For CPU feature work, change the same instance back to a
CPU type such as `c6i.xlarge` before starting it; this avoids paying for an
idle GPU during the MMseqs2 feature stage. Once connected to that instance:

```bash
cd ~/alphapulldown_dnaaf_screen
git pull --ff-only origin feature/alphapulldown-implementation
bash scripts/aws/configure_milestone2_runtime.sh
bash scripts/aws/run_milestone2_stage.sh --stage features --dry-run
```

The dry-run starts the validated Docker image only to validate its identity,
mount the benchmark-only paths, render the nine individual AF2/MMseqs2 feature
commands, and write dry-run provenance. It does not contact MMseqs2 or write
feature files.

Only after review and explicit approval, the CPU feature-generation command is:

```bash
bash scripts/aws/run_milestone2_stage.sh --stage features
```

For later GPU prediction, change the same stopped instance back to `g5.xlarge`,
then run a prediction dry-run before any prediction command:

```bash
bash scripts/aws/run_milestone2_stage.sh --stage predict --dry-run
```

The wrapper bind-mounts the checkout at its identical absolute host path. It
rejects a mismatched image ID, non-benchmark manifests, AF3 selectors,
AlphaJudge, the blocked Chlamydomonas scenario, and the 62-target manifest.

## Not yet allowed

- Do not run the 62-target universe.
- Do not run the blocked Chlamydomonas scenario.
- Do not run AlphaFold3 or AlphaJudge.
- Do not generate features or make predictions.
- Do not use the former RunPod Dockerfile or SIF workflow.
