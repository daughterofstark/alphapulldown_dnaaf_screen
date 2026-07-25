# RunPod Execution Checklist

This checklist is for the first remote AlphaPulldown execution on RunPod. Use a **Pod**, not Serverless. Do not start predictions until the environment validates and dry runs pass.

## Before Creating the Pod

Record the planned run:

- Git branch: `feature/alphapulldown-implementation`
- Planned panel: `data/processed/alphapulldown/girish_refined_runpod_first_run.tsv`
- First biological control to run: human DNAAF18/ODA16-IFT46 negative/species-divergence control
- First candidate group: Girish-refined multichain jobs marked `include_by_default=true`

Confirm:

- RunPod budget or spending limit.
- Whether persistent storage/network volume is available.
- Whether AlphaFold databases will be local, mounted, or unavailable.
- Whether local database mode or MMseqs2 mode will be used.

## Create the Pod

1. Create a **Pod**, not a Serverless endpoint.
2. Choose an official PyTorch/CUDA-capable template.
3. Select an NVIDIA GPU with sufficient VRAM for the first controls and multichain tests.
4. Attach persistent storage or a network volume if available.
5. Choose enough disk space for repository, environment, logs, features, and selected outputs.
6. Start the pod.

Immediately record for reimbursement:

- Pod ID.
- GPU type.
- Hourly rate.
- Template name.
- Template/container tag if visible.
- Volume size.
- Start time.
- Screenshot or receipt filename.

## Repository Setup

On the pod:

```bash
git clone <REPOSITORY_URL> alphapulldown
cd alphapulldown
git checkout feature/alphapulldown-implementation
```

Confirm the expected files exist:

```bash
ls data/processed/screens/girish_refined_first_run_panel.tsv
ls data/processed/alphapulldown/girish_refined_runpod_first_run.tsv
```

## Configure Paths

```bash
cp config/remote/paths.example.env config/remote/paths.env
```

Edit `config/remote/paths.env` for the pod:

- `REMOTE_PROJECT_ROOT`
- `AP_WORKFLOW_DIR`
- `DATABASES_DIR`
- `BACKEND_WEIGHTS_DIR`
- `OUTPUT_DIR`
- `FEATURE_DIR`
- `LOG_DIR`
- `TMP_DIR`
- `PROVENANCE_DIR`
- `FEATURE_MODE`

Do not commit `paths.env`.

## Bootstrap and Validate

Run bootstrap dry-run:

```bash
bash scripts/remote/bootstrap_remote_environment.sh --dry-run
```

If the dry-run is sensible, run bootstrap:

```bash
bash scripts/remote/bootstrap_remote_environment.sh
```

Validate the environment:

```bash
bash scripts/remote/validate_remote_environment.sh
```

Record:

- Python version.
- Snakemake version.
- AlphaPulldown version.
- CUDA version from `nvidia-smi`.
- GPU model and memory.
- Database path validation result.

## Feature Generation

Run feature-generation dry-run:

```bash
bash scripts/remote/run_feature_generation.sh --dry-run
```

If the dry-run passes, generate features:

```bash
bash scripts/remote/run_feature_generation.sh
```

Save:

- Feature-generation log.
- Provenance directory.
- Any warnings about missing databases, MSA generation, or feature output naming.

## Prediction Dry Run

Before prediction, inspect the RunPod panel:

```bash
column -t -s $'\t' data/processed/alphapulldown/girish_refined_runpod_first_run.tsv | less -S
```

Run controls dry-run first:

```bash
bash scripts/remote/run_prediction.sh --screen controls --dry-run
```

For Girish-refined jobs, verify the resolved AlphaPulldown specs in the TSV before manually converting them to the remote workflow input file. Multichain rows must remain multichain; do not silently replace them with binary jobs.

## First Prediction Execution

Run controls only first:

```bash
bash scripts/remote/run_prediction.sh --screen controls
```

After controls:

- Inspect logs.
- Confirm output directories were created.
- Confirm score/ranking files exist.
- Confirm no GPU out-of-memory or feature-coverage failures occurred.

Only then proceed to Girish-refined candidate jobs marked `include_by_default=true`.

## Collect Outputs

Dry-run collection:

```bash
bash scripts/remote/collect_results.sh --dry-run
```

Collect outputs:

```bash
bash scripts/remote/collect_results.sh
```

Save:

- `results/provenance/`
- `results/logs/`
- collected structures and score tables
- PAE files
- RunPod receipt or screenshot

## Stop the Pod

When the run is complete or paused:

1. Copy required outputs to persistent storage or local machine.
2. Confirm reimbursement log is updated.
3. Stop the pod.
4. Confirm billing has stopped.
5. Record stop time and final estimated cost.

## Minimum Run Record

For every RunPod session, record:

- Date.
- Pod ID.
- GPU type.
- Hourly rate.
- Start and stop time.
- Commands run.
- Outputs generated.
- Issues encountered.
- Receipt or screenshot filename.
