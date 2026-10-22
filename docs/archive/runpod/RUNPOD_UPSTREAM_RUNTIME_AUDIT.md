# RunPod Upstream Runtime Audit

Date: 2026-07-25

Scope: debug the RunPod deployment path for `KosinskiLab/AlphaPulldownSnakemake` tag `2.5.0` without running AlphaPulldown, downloading databases, or starting paid heavy compute.

## Upstream Files Inspected

Pinned upstream source:

- `KosinskiLab/AlphaPulldownSnakemake` tag `2.5.0`
- `README.md`
- `workflow/Snakefile`
- `workflow/envs/alphapulldown.yaml`
- `config/config.yaml`
- `config/profiles/desktop/config.yaml`
- `config/profiles/slurm/config.yaml`

Source locations:

- <https://raw.githubusercontent.com/KosinskiLab/AlphaPulldownSnakemake/2.5.0/README.md>
- <https://raw.githubusercontent.com/KosinskiLab/AlphaPulldownSnakemake/2.5.0/workflow/Snakefile>
- <https://raw.githubusercontent.com/KosinskiLab/AlphaPulldownSnakemake/2.5.0/workflow/envs/alphapulldown.yaml>
- <https://raw.githubusercontent.com/KosinskiLab/AlphaPulldownSnakemake/2.5.0/config/config.yaml>

## Runtime Architecture

AlphaPulldownSnakemake uses two layers:

1. **Orchestration environment**
   - Created from the pinned `workflow/envs/alphapulldown.yaml`.
   - Provides Snakemake, Snakemake plugins, Snakedeploy-compatible tooling, and `alphapulldown-input-parser`.
   - Does **not** need to provide an importable `alphapulldown` Python package.

2. **Rule runtime containers**
   - The upstream Snakefile uses Snakemake `container:` directives.
   - Feature generation and prediction shell commands call AlphaPulldown entry points such as `create_individual_features.py` and `run_structure_prediction.py` inside configured containers.
   - Example container config keys are `prediction_container` and `analysis_container`.

Therefore `import alphapulldown` inside the `snake` orchestration environment is not a valid blocking requirement. The expected import in `snake` is `alphapulldown_input_parser`.

## Snakedeploy Layout

On RunPod, `snakedeploy deploy-workflow` produced a deployed workflow containing:

```text
/workspace/workflows/AlphaPulldownSnakemake/
  workflow/
    Snakefile
```

The deployed Snakefile may be a Snakemake module wrapper pointing back to:

```text
github("KosinskiLab/AlphaPulldownSnakemake", path="workflow/Snakefile", tag="2.5.0")
```

This is compatible with Snakedeploy. It is not the same as a full Git clone of the upstream repository, and it may not contain:

```text
workflow/envs/
config/profiles/desktop/
config/profiles/slurm/
```

Profiles are therefore optional in this repository's RunPod path. For single-node RunPod execution, use `snakemake --cores <N>` rather than requiring upstream profile directories.

## Incorrect Assumptions Found

| Area | Incorrect assumption | Correction |
|---|---|---|
| Orchestration env | `snake` must import `alphapulldown`. | `snake` must run Snakemake and import `alphapulldown_input_parser`; AlphaPulldown is provided inside rule containers. |
| Workflow deployment | Snakedeploy copies all upstream directories. | Snakedeploy may deploy a module wrapper; validate `workflow/Snakefile`, not `workflow/envs/`. |
| Profiles | `config/profiles/desktop` and `config/profiles/slurm` always exist after deployment. | They may be absent. Profiles must be optional for RunPod. |
| Conda YAML | Creating env directly from URL always works. | RunPod observed remote URL pip handling failure; support a local downloaded pinned YAML via `AP_ENV_YAML`. |
| Local Python package | Remote CLI requires repo package installed. | Shell helper should set `PYTHONPATH=<repo>/src` for fresh clones. |
| RunPod parallelism | `SNAKEMAKE_JOBS=200` is acceptable. | Single A40 RunPod should default to `SNAKEMAKE_JOBS=1`; local execution uses `--cores`. |

## Corrected RunPod `paths.env` Model

Use `/workspace` for all installation, workflow, results, scratch, and provenance paths.

Recommended key decisions:

```text
FEATURE_MODE=mmseqs2
FEATURE_FILE_PATTERN={record_id}.pkl.xz
SNAKEMAKE_CORES=8
SNAKEMAKE_JOBS=1
SNAKEMAKE_PROFILE=
SLURM_PROFILE=
```

Rationale:

- No local AlphaFold databases are available.
- AlphaPulldown `2.5.0` rejects `--use_mmseqs2` with the AlphaFold3 data pipeline.
- The project wrapper maps `FEATURE_MODE=mmseqs2` to AlphaFold2 feature generation and `docker://kosinskilab/alphafold2:2.5.0`.
- A single A40 / 9-vCPU RunPod is not a SLURM cluster.

## Expected Files After Deployment

Minimum expected:

```text
${AP_WORKFLOW_DIR}/workflow/Snakefile
```

Optional and not required on RunPod:

```text
${AP_WORKFLOW_DIR}/workflow/envs/
${AP_WORKFLOW_DIR}/config/profiles/desktop/
${AP_WORKFLOW_DIR}/config/profiles/slurm/
```

Project-side required files:

```text
/workspace/alphapulldown/config/remote/paths.env
/workspace/alphapulldown/data/processed/fasta/fasta_manifest.tsv
/workspace/alphapulldown/data/processed/alphapulldown/
```

## Corrected Commands

Activate Miniforge and the tooling environment:

```bash
export PATH="/workspace/miniforge3/bin:$PATH"
conda activate snakedeploy-tools
```

Validate the workflow deployment and orchestration tools:

```bash
cd /workspace/alphapulldown
bash scripts/remote/bootstrap_remote_environment.sh --dry-run
bash scripts/remote/validate_remote_environment.sh
```

Generate the Snakemake dry-run command without running jobs:

```bash
bash scripts/remote/run_feature_generation.sh --dry-run
```

This writes a resolved config and prints a Snakemake dry-run command. It should not run MSA generation or prediction.

## Exact Next Commands for RunPod

These commands do not start AlphaPulldown feature generation or GPU inference:

```bash
export PATH="/workspace/miniforge3/bin:$PATH"
cd /workspace/alphapulldown
conda activate snakedeploy-tools
git status --short --branch
bash scripts/remote/bootstrap_remote_environment.sh --dry-run
bash scripts/remote/validate_remote_environment.sh
bash scripts/remote/run_feature_generation.sh --dry-run
```

If `validate_remote_environment.sh` fails only because the workflow has not yet been deployed, deploy with the already available tooling environment:

```bash
bash scripts/remote/bootstrap_remote_environment.sh
```

This creates or confirms the `snake` orchestration env and deploys the workflow. It is ordinary setup, not AlphaPulldown prediction.

## Actions That Begin Billable Heavy Compute

These may start long CPU/GPU work and should not be run until explicitly approved:

```bash
bash scripts/remote/run_feature_generation.sh
bash scripts/remote/run_prediction.sh --screen controls
bash scripts/remote/run_prediction.sh --screen transport
```

Feature generation may be CPU/network-heavy and may invoke containers and remote MMseqs2. Prediction starts GPU inference.

## Remaining Runtime Blockers to Confirm

- Whether RunPod image supports the container runtime needed by Snakemake for `container:` directives.
- Whether Docker or Apptainer/Singularity will be used for actual rule execution.
- Whether remote MMseqs2 API access is available from the pod.
- Whether the AlphaFold2 prediction container can run on the A40/CUDA 12.8 driver stack.
- Whether `snakemake --dry-run` resolves module-wrapped workflow paths correctly from the deployed Snakedeploy directory.
