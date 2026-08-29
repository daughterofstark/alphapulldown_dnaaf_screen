# AWS Runtime Validation

## Scope

This records environment validation only. No project FASTA was read, no MSA was
generated, and no AlphaFold prediction was run.

## Validated runtime

Date: 2026-08-29

- Host: AWS EC2 `g5.xlarge`
- GPU: NVIDIA A10G, 23028 MiB usable VRAM
- Host driver: 595.91.07
- Host-reported CUDA compatibility: 13.2
- Docker GPU runtime: NVIDIA Container Toolkit 1.19.1
- Candidate image: `alphapulldown-af2:candidate`
- Docker local image ID:
  `sha256:458537ff9ac8363406f0ce545c74d5a954595de651f1a0dc770577ec49e70759`
- AlphaPulldown: 2.5.0
- JAX: 0.5.3

## Checks passed

1. CPU image smoke test imported AlphaPulldown, AlphaFold, ColabFold, JAX, and
   OpenMM, then loaded `create_individual_features.py` and confirmed the
   `use_mmseqs2` CLI option.
2. `nvidia-smi` detected the A10G on the host.
3. A CUDA container successfully ran `nvidia-smi` with `--gpus all`.
4. GPU image smoke test imported the AlphaPulldown prediction module and JAX
   reported `CudaDevice(id=0)`.
5. `run_structure_prediction.py` loaded and reported an AlphaFold2 default
   folding backend.

## Consequences

The former RunPod nested-Apptainer restriction no longer blocks execution. The
AWS image is local to this EBS volume; stop, rather than terminate, the EC2
instance to preserve it. A different host requires rebuilding the image or a
separately approved registry transfer.

## Next gate

Run the benchmark-only CPU dry-run documented in
`docs/deployment/AWS_IMAGE_BUILD_GUIDE.md`. Do not begin real feature generation
or prediction without explicit approval.
