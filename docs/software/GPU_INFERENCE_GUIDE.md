# GPU Inference Guide

## Scope

GPU inference consumes precomputed per-protein features and runs AlphaFold-Multimer pair predictions through the remote AlphaPulldown workflow.

This stage requires Linux with NVIDIA CUDA. It must not be run on the local macOS machine.

## Execution Order

1. Controls.
2. Targeted transport screen.
3. Full screen only after explicit approval.

## Controls

```bash
bash scripts/remote/run_prediction.sh --screen controls --dry-run
bash scripts/remote/run_prediction.sh --screen controls
```

Control inputs are read from:

```text
data/processed/alphapulldown/control_sample_sheet.csv
```

## Targeted Transport Screen

```bash
bash scripts/remote/run_prediction.sh --screen transport --dry-run
bash scripts/remote/run_prediction.sh --screen transport
```

This uses:

- `transport_baits.txt`
- `ift_b_preys.txt`

## Feature Coverage

Before prediction submission, the remote helper checks that expected feature files exist for every accession in the requested screen. Missing feature files cause a non-zero exit before GPU jobs start.

## Desktop and SLURM

Desktop mode:

```bash
bash scripts/remote/run_prediction.sh --screen controls --executor desktop
```

SLURM mode:

```bash
bash scripts/remote/run_prediction.sh --screen controls --executor slurm
```

SLURM settings are configured in `config/remote/paths.env`; no partition, account, or cluster path is hardcoded.

## Resume and Retry

The configuration templates expose:

- `skip_existing`
- `restart_times`
- model settings
- seed settings
- output paths

Use dry runs after any resume/retry change.

## Expected Outputs

Workflow-version-specific outputs may include:

- ranked structures
- PAE files
- ranking JSON
- score tables
- logs
- provenance
- selected result pickles

Collect only lightweight outputs needed for local analysis.

