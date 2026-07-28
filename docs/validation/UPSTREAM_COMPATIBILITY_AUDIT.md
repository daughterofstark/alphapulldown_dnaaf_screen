# Upstream Compatibility Audit

Date: 2026-07-13

Scope: strict source/documentation audit of the local remote-execution handoff against pinned upstream repositories. No AlphaPulldown installation, Snakemake execution, database download, or inference was performed locally.

## Pinned Upstream Versions

| Repository | Tag | Commit inspected |
|---|---:|---|
| `KosinskiLab/AlphaPulldown` | `2.5.0` | `1c99b15ce3fef42374c24a5bd83ce8241117d5f6` |
| `KosinskiLab/AlphaPulldownSnakemake` | `2.5.0` | `23cbba5f151f843d800b5cffaa7a3a3908c35d9e` |

Note: the AlphaPulldown tag object resolved to `f838dce8351465a2dac7e7c0cdb151a61f7c9ca3`; the checked-out commit was `1c99b15ce3fef42374c24a5bd83ce8241117d5f6`.

## Files Inspected

AlphaPulldownSnakemake:

- `README.md`
- `config/config.yaml`
- `config/profiles/desktop/config.yaml`
- `config/profiles/slurm/config.yaml`
- `workflow/Snakefile`
- `workflow/rules/common.smk`

AlphaPulldown:

- `alphapulldown/scripts/create_individual_features.py`
- `alphapulldown/scripts/run_structure_prediction.py`
- `alphapulldown/folding_backend/alphafold2_backend.py`
- `alphapulldown/utils/output_paths.py`
- `alphapulldown/analysis_pipeline/diagnostics.py`
- `alphapulldown/utils/post_modelling.py`

## Exact Verified Commands

Upstream environment creation:

```bash
conda env create \
  -n snake \
  -f https://raw.githubusercontent.com/KosinskiLab/AlphaPulldownSnakemake/2.5.0/workflow/envs/alphapulldown.yaml
conda activate snake
```

Upstream workflow deployment:

```bash
snakedeploy deploy-workflow \
  https://github.com/KosinskiLab/AlphaPulldownSnakemake \
  AlphaPulldownSnakemake \
  --tag 2.5.0
cd AlphaPulldownSnakemake
```

Upstream desktop run:

```bash
snakemake --profile config/profiles/desktop --cores 8
```

Upstream SLURM run:

```bash
snakemake \
  --executor slurm \
  --profile config/profiles/slurm \
  --jobs 200 \
  --restart-times 5
```

This repository's wrappers now materialize resolved config files and invoke the same Snakefile/profile structure with explicit paths:

```bash
snakemake \
  --snakefile <AP_WORKFLOW_DIR>/workflow/Snakefile \
  --directory <AP_WORKFLOW_DIR> \
  --configfile <results/provenance/run_id/*.config.json> \
  --profile <AP_WORKFLOW_DIR>/config/profiles/desktop \
  --cores 8
```

## Compatibility Findings

| Component | Current assumption | Upstream evidence | Status | Required change |
|---|---|---|---|---|
| Workflow deployment | Deploy AlphaPulldownSnakemake with `snakedeploy` into a configurable directory. | README uses `snakedeploy deploy-workflow https://github.com/KosinskiLab/AlphaPulldownSnakemake AlphaPulldownSnakemake --tag 2.5.0`. | Compatible after clarification | Keep configurable target directory; document that upstream example names the directory `AlphaPulldownSnakemake`. |
| Conda environment name | Local wrapper defaulted to `alphapulldown`. | README creates `-n snake`. | Corrected | Default `CONDA_ENV_NAME=snake`. |
| Snakemake working directory | Wrapper used the project repository as `--directory`. | Snakefile has `configfile: "config/config.yaml"` and profiles live inside deployed workflow. | Incorrect | Run Snakemake with `--directory <AP_WORKFLOW_DIR>` and `--snakefile <AP_WORKFLOW_DIR>/workflow/Snakefile`. |
| Desktop profile | Optional local profile path. | README/profile path is `config/profiles/desktop` under deployed workflow. | Corrected | Default `SNAKEMAKE_PROFILE=${AP_WORKFLOW_DIR}/config/profiles/desktop`. |
| SLURM profile | Optional local profile path. | README/profile path is `config/profiles/slurm`; command uses `--executor slurm --jobs 200 --restart-times 5`. | Corrected | Default `SLURM_PROFILE=${AP_WORKFLOW_DIR}/config/profiles/slurm`; wrapper supports `--executor slurm --jobs`. |
| Feature-only stage | Project-local `feature_mode`/`feature_dir` Snakemake config keys. | Snakefile sets `required_targets = required_feature_paths` only when `config.get("only_generate_features", False)` is true. | Incorrect | Use resolved upstream config with `only_generate_features: true`; do not pass project-local keys to Snakemake. |
| Feature output directory | Separate arbitrary `FEATURE_DIR`. | Snakefile writes generated features to `<output_directory>/features`; `feature_directory` means directories of precomputed features to symlink. | Corrected | Default `FEATURE_DIR=${OUTPUT_DIR}/features`; document `feature_directory` semantics. |
| Feature output pattern | `{record_id}.pkl`. | Snakefile uses `{fasta_basename}_af3_input.json` for AF3 and `{fasta_basename}.pkl`/`.pkl.xz` for AF2 depending on compression. | Incorrect | Default AF3 pattern is `{record_id}_af3_input.json`; MMseqs2/AF2 default is `{record_id}.pkl.xz`. |
| Prediction screen selection | Project-local `screen=controls` passed through `--config`. | Upstream only consumes `input_files`; multi-file pulldown inputs are supported by README and `generate_fold_specifications`. | Incorrect | Wrapper materializes screen-specific upstream config files with correct `input_files`. |
| Accessions vs FASTA paths | Use accession pair files directly for prediction. | Upstream features are keyed by input feature basename. FASTA path inputs produce `HUMAN_*` feature names; accession inputs produce accession-named features/downloaded data. | Incorrect | Wrapper rewrites accession screens to absolute FASTA path inputs so predictions use verified FASTA-derived features. |
| UniProt retrieval | Safe to rely on accessions for remote workflow. | Snakefile has `download_uniprot` for UniProt IDs; this would bypass the verified local FASTA sequences. | Corrected | Use FASTA path mode for resolved remote configs. |
| Local database mode | Use AlphaFold-compatible local databases. | `create_individual_features.py` requires `data_dir` unless `--use_mmseqs2` is true. | Compatible | Keep `DATABASES_DIR` required for `FEATURE_MODE=localdb`. |
| Remote MMseqs2 mode | Use `--use_mmseqs2` with default AF3 data pipeline. | `create_individual_features.py` raises if `--data_pipeline alphafold3` and `--use_mmseqs2`. | Incorrect | Resolve MMseqs2 mode to `--data_pipeline alphafold2`, `--fold_backend alphafold2`, AF2 container, and compressed AF2 feature pattern. |
| `--skip_existing` | Supported AlphaPulldown flag. | `create_individual_features.py` defines `skip_existing`; Snakefile passes `create_feature_arguments` to the CLI. | Compatible | Keep only under `create_feature_arguments`, not as a project-local Snakemake key. |
| `--save_msa_files` | Supported AlphaPulldown flag. | `create_individual_features.py` defines `save_msa_files`; Snakefile passes it through. | Compatible | Keep under `create_feature_arguments`. |
| `--use_precomputed_msas` | Supported AlphaPulldown flag. | `create_individual_features.py` defines `use_precomputed_msas`. | Compatible | Keep under `create_feature_arguments`. |
| `--db_preset` | Supported AlphaPulldown flag. | `create_individual_features.py` defines `db_preset`. | Compatible, unused | May be added under `create_feature_arguments` if a remote database layout requires reduced DBs. |
| Prediction backend key | Generic project `model.backend`. | Upstream uses `structure_inference_arguments: --fold_backend`. | Incorrect | Use `structure_inference_arguments: {"--fold_backend": ...}`. |
| Model preset/recycles/seeds | Top-level project model keys. | `run_structure_prediction.py` defines flags such as `model_preset`, `num_predictions_per_model`, `random_seed`; Snakefile passes `structure_inference_arguments`. | Corrected by omission | Do not expose unsupported top-level keys; add as `structure_inference_arguments` only after remote review. |
| Recursive report output | Collect generic CSVs. | Snakefile writes `reports/all_interfaces.csv` when `generate_recursive_report: true`. | Corrected | Collector targets `reports/all_interfaces.csv`. |
| Per-fold interface output | Assumed `interfaces.csv`. | Snakefile `analyze_structure` writes `predictions/<fold>/interfaces.csv`. | Compatible | Collector targets verified path. |
| Ranked structures | Collect `ranked_*.pdb/cif/mmcif`. | AF2 backend writes `ranked_<idx>.pdb`; README broadly mentions PDB/CIF, AF3 container may write backend-specific structure files. | Partially verified | Collector includes verified `ranked_*.pdb`; CIF/mmCIF collection should be revisited after AF3 remote run. |
| PAE outputs | Generic `pae*.json/png`. | AF2 backend writes `pae_<model>.json` and `pae_plot_ranked_<idx>.png`. | Corrected | Collector targets these verified patterns. |
| Result pickles | Always copy selected pickles. | AF2 backend writes `result_<model>.pkl`; post-processing may compress to `.pkl.gz`/`.pkl.xz`. | Corrected | Copy only if `COLLECT_RESULT_PICKLES=1`. |
| APLit root | Output/predictions. | README launches `aplit --directory output/predictions`. | Compatible | Keep docs pointing to `<output_directory>/predictions`. |

## Configuration Key Classification

Valid upstream top-level keys retained in templates:

`input_files`, `protein_delimiter`, `exclude_permutations`, `output_directory`, `databases_directory`, `backend_weights_directory`, `feature_directory`, `only_generate_features`, `enable_structure_analysis`, `generate_recursive_report`, `recursive_report_arguments`, `create_feature_arguments`, `structure_inference_arguments`, `analyze_structure_arguments`, memory/resource keys, length-filter keys, SLURM keys, `prediction_container`, and `analysis_container`.

Project-local keys are now namespaced only under:

```yaml
project_local:
  ...
```

Invalid or removed top-level keys:

`stage`, `workflow`, `mode`, `inputs`, `outputs`, `gpu`, `resume_retry`, `snakemake`, `provenance`, `model`, `execution_order`, `feature_mode`, `feature_dir`, `fasta_dir`, and `screen`.

## Feature Reuse and Organism Pairing

Source-confirmed behavior:

- Individual feature artifacts are produced by `create_features` from one FASTA input and written under `<output_directory>/features`.
- In AF3 data-pipeline mode, feature artifacts are JSON files named `{fasta_basename}_af3_input.json`.
- In AF2 data-pipeline mode, feature artifacts are pickles named `{fasta_basename}.pkl` or compressed as `{fasta_basename}.pkl.xz`.
- `run_structure_prediction.py` consumes precomputed feature files via `--features_directory`.
- Multi-file pulldown input expansion is supported by the upstream input parser and documented in the README.

Correction:

- Organism-aware sequence pairing should not be described as a persisted pair-specific artifact in this repository until a remote run confirms the exact backend behavior for the selected AF2/AF3 path. The wrapper now documents reusable per-protein features only.

## Unresolved Questions Requiring Remote Dry Run

- Confirm whether the AF3 prediction container writes additional `.cif`/`.mmcif` ranked structure files beyond the source-verified AF2 `ranked_*.pdb` behavior.
- Confirm exact logs emitted by Snakemake containers on the target Linux system.
- Confirm whether site-specific Singularity/Apptainer bind paths are required for database and output paths.
- Confirm whether `--restart-times 5` should be included by default for this cluster or supplied manually after observing retry behavior.
- Confirm GPU memory behavior for the selected backend/container and whether unified memory defaults are appropriate on the remote host.

## Local Corrections Made

- Remote command construction now uses the deployed workflow directory and upstream Snakefile/profile paths.
- Remote CLI materializes resolved upstream config files in `results/provenance/<run_id>/`.
- Feature-only runs use `only_generate_features: true`.
- Project-local keys are not passed directly to Snakemake.
- Accession screens are rewritten to FASTA-path screen files before Snakemake execution.
- Default feature patterns now match upstream AF3 and AF2/MMseqs2 naming.
- MMseqs2 mode now resolves to AlphaFold2 pipeline/backend for tag `2.5.0`.
- Result collection now targets source-verified output paths and makes result pickle transfer opt-in.
