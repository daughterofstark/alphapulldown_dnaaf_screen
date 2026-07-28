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

The bootstrap script follows the pinned upstream command:

```bash
conda env create -n snake -f https://raw.githubusercontent.com/KosinskiLab/AlphaPulldownSnakemake/2.5.0/workflow/envs/alphapulldown.yaml
snakedeploy deploy-workflow https://github.com/KosinskiLab/AlphaPulldownSnakemake <AP_WORKFLOW_DIR> --tag 2.5.0
```

Validate:

```bash
bash scripts/remote/validate_remote_environment.sh
```

The validator checks both SIF integrity and execution capability. A successful
`apptainer inspect` does not prove that the host can execute containers; the
validator also runs `apptainer exec <SIF> true` before Snakemake can start. If
that fails because unprivileged user namespaces are disabled, stop and ask the
platform administrator for a supported Apptainer runtime (for example, the
official SUID helper package or a pod configuration that permits Apptainer
execution). Do not change host sysctl settings from inside a pod. The relevant
host requirements are documented by [Apptainer](https://apptainer.org/docs/admin/latest/installation.html).

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

## Upstream Compatibility Notes

The remote helpers materialize resolved AlphaPulldownSnakemake config files under `results/provenance/<run_id>/` before invoking Snakemake. This avoids passing project-local keys such as `screen` or `feature_mode` to upstream Snakemake. Feature generation is selected with the verified upstream key `only_generate_features: true`.

Prediction inputs are rewritten from accession lists to absolute FASTA paths so the workflow consumes the verified repository FASTAs and reuses feature files named from the stable `HUMAN_*` FASTA basenames.
