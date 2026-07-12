# Remote Execution Guide

## Scope

Local macOS is used for preparation, validation, documentation, and later result analysis. AlphaPulldown feature generation and AlphaFold-Multimer inference should run on a Linux host. GPU inference requires NVIDIA CUDA.

Do not install AlphaPulldown locally on macOS for this project.

## End-to-End Workflow

```text
Mac preparation
-> git push
-> clone on Linux
-> configure paths
-> validate environment
-> dry run
-> generate per-protein features on CPU
-> verify feature coverage
-> run GPU predictions
-> collect outputs
-> rsync selected results back
```

## Remote First-Time Setup

On the Linux host:

```bash
git clone <REPOSITORY_URL> alphapulldown
cd alphapulldown
git checkout feature/alphapulldown-implementation
cp config/remote/paths.example.env config/remote/paths.env
```

Edit `config/remote/paths.env` for that host. Do not commit it.

Bootstrap the official workflow:

```bash
bash scripts/remote/bootstrap_remote_environment.sh --dry-run
bash scripts/remote/bootstrap_remote_environment.sh
```

Validate:

```bash
bash scripts/remote/validate_remote_environment.sh
```

## Feature Generation

```bash
bash scripts/remote/run_feature_generation.sh --dry-run
bash scripts/remote/run_feature_generation.sh
```

## Prediction

Run controls first:

```bash
bash scripts/remote/run_prediction.sh --screen controls --dry-run
bash scripts/remote/run_prediction.sh --screen controls
```

Then the targeted transport screen:

```bash
bash scripts/remote/run_prediction.sh --screen transport --dry-run
bash scripts/remote/run_prediction.sh --screen transport
```

The full screen is intentionally rejected by the remote helper until it is explicitly reviewed and approved.

## Collection

On the remote host:

```bash
bash scripts/remote/collect_results.sh --dry-run
bash scripts/remote/collect_results.sh
```

Then from macOS, use `rsync` to transfer the collected directory back. Do not transfer AlphaFold databases, MSA caches, or full temporary work directories.

## Provenance

Remote run provenance is written under:

```text
results/provenance/<run_id>/
```

Each run captures command text, Git state, input checksums, config locations, timestamps, and workflow settings.

