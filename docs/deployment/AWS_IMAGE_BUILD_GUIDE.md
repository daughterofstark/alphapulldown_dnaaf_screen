# AWS Image Build Guide

This is the AWS route for the isolated Milestone 2 AlphaPulldown benchmark.
It does not authorise feature generation or prediction until the candidate image
passes both smoke tests.

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

The first build records the exact resolved Conda and pip packages inside the
image at `/opt/alphapulldown-runtime/`. Those records must be copied out and
reviewed before the candidate image is promoted as the scientific runtime.

## CPU build gate

On an AWS x86_64 Linux CPU machine with Docker installed, from the repository
root:

```bash
bash scripts/aws/build_candidate_image.sh \
  <your-ecr-image-uri>:alphapulldown-af2-candidate
```

This builds the image for `linux/amd64` and reruns its CPU smoke test. The
smoke test checks AlphaPulldown 2.5.0, AlphaFold, ColabFold, JAX, OpenMM, the
feature-generation module, and `create_individual_features.py --help`. It
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

Only after this succeeds should the derived image digest be copied into
`deployment/aws/image-lock.json` and the Milestone 2 remote configuration.

## Not yet allowed

- Do not run the 62-target universe.
- Do not run the blocked Chlamydomonas scenario.
- Do not run AlphaFold3 or AlphaJudge.
- Do not generate features or make predictions.
- Do not use the former RunPod Dockerfile or SIF workflow.
