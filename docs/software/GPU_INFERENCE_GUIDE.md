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

Control definitions are read from:

```text
data/processed/alphapulldown/control_sample_sheet.csv
```

Before Snakemake is invoked, the wrapper rewrites those accession pairs to a run-local file containing absolute FASTA paths. This keeps prediction aligned with the verified FASTA-derived features.

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

## Upstream Invocation

Desktop mode uses the deployed upstream profile:

```bash
snakemake --snakefile <AP_WORKFLOW_DIR>/workflow/Snakefile --directory <AP_WORKFLOW_DIR> --configfile <resolved-config> --profile <AP_WORKFLOW_DIR>/config/profiles/desktop --cores 8
```

SLURM mode follows the upstream executor style:

```bash
snakemake --snakefile <AP_WORKFLOW_DIR>/workflow/Snakefile --directory <AP_WORKFLOW_DIR> --configfile <resolved-config> --profile <AP_WORKFLOW_DIR>/config/profiles/slurm --executor slurm --jobs 200
```

## Resume and Retry

Resume is handled by Snakemake's `rerun-incomplete` profile settings and by reusing the same output directory. Retry policy for SLURM is provided by Snakemake flags such as `--restart-times`; add it deliberately on the remote host after the first dry run if needed.

Use dry runs after any resume/retry change.

## Expected Outputs

For AlphaPulldown/AlphaPulldownSnakemake `2.5.0`, expected outputs include:

- `predictions/<fold>/ranked_*.pdb`
- `predictions/<fold>/ranking_debug.json`
- `predictions/<fold>/pae_*.json`
- `predictions/<fold>/pae_plot_ranked_*.png`
- `predictions/<fold>/confidence_*.json`
- `predictions/<fold>/interfaces.csv`
- `reports/all_interfaces.csv` when recursive reporting is enabled
- `predictions/<fold>/result_*.pkl*` only when selected result pickles are needed

Collect only lightweight outputs needed for local analysis.
