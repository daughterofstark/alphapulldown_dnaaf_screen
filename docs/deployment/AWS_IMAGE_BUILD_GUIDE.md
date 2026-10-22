# AWS Runtime Guide

## Purpose

The completed Milestone 2 pilot used a Docker-native AWS EC2 runtime. This
document records the validated environment and the minimum checks required
before a future execution. It does not replace the pilot-results report.

## Validated Runtime

- AlphaPulldown: 2.5.0
- Folding backend: AlphaFold2-Multimer v3
- Feature mode: MMseqs2 with compressed per-protein `.pkl.xz` features
- Container: `alphapulldown-af2:candidate` on the EBS-backed EC2 host
- GPU smoke test: NVIDIA A10G with JAX 0.5.3 reporting `CudaDevice(id=0)`
- Docker GPU runtime: NVIDIA Container Toolkit

The image definition and smoke checks are versioned under `deployment/aws/`.
The project package and the AlphaFold2 container use separate Python versions:
the package requires Python 3.11 or later, while the pinned AlphaPulldown 2.5.0
runtime uses Python 3.10.

## Execution Stages

1. **Feature generation:** CPU stage. Generates reusable AlphaPulldown feature
   files once for each benchmark protein.
2. **Prediction:** GPU stage. Uses the precomputed feature directory and
   AlphaFold model parameters.
3. **Analysis:** Local CPU stage. Parses complete output directories and
   reviews ranked structures and PAE plots.

The Milestone 2 wrapper is intentionally limited to the benchmark manifest and
rejects the 62-target universe, AlphaFold3 selectors, AlphaJudge, and the
blocked Chlamydomonas scenario.

## Preflight Checks

From the repository root on the target Linux host:

```bash
git pull --ff-only origin feature/alphapulldown-implementation
docker image inspect alphapulldown-af2:candidate
nvidia-smi
bash scripts/aws/run_milestone2_stage.sh --stage predict --dry-run
```

For feature generation, use `--stage features --dry-run` first. A dry run
validates the image, paths, feature coverage, and benchmark isolation without
starting an AlphaPulldown computation.

## Resource Planning

GPU memory alone is not sufficient for large multimer assemblies. One
DNAAF9 + IFT46 + IFT74 + IFT81 prediction was terminated by the host kernel on
a 32 GiB RAM EC2 instance despite adequate L40S GPU VRAM. Future large runs
require a host with more system RAM and a documented resource plan.

## Result Handling

Transfer only the required output files: ranked and unrelaxed PDBs, PAE and
confidence JSON files, PAE plots, `ranking_debug.json`, `timings.json`, logs,
and provenance. Do not transfer databases, Docker layers, credentials, or
machine-specific `paths.env` files.

See [Milestone 2 Pilot Results](../validation/MILESTONE2_PILOT_RESULTS.md) for
the completed outputs and [Compute Environment Requirements](REMOTE_ACCESS_REQUIREMENTS.md)
for host requirements.
