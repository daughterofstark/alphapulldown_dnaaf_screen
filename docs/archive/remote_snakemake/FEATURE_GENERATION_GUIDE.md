# Feature Generation Guide

## What Features Are

AlphaPulldown separates per-protein feature generation from pairwise structure prediction. Features include sequence-derived inputs such as MSAs and template information that can be reused across many pair jobs.

Computing features once per protein prevents repeated MSA/template work when the same protein appears in many pairwise screens.

> **RunPod Milestone 2:** use
> `scripts/remote/run_native_stage.sh --stage features`. It directly invokes
> `create_individual_features.py` inside the Pod image and is locked to the
> independent benchmark manifest, AF2, MMseqs2, and compressed `*.pkl.xz`
> outputs. The Snakemake material below applies only to compatible non-RunPod
> environments.

For `KosinskiLab/AlphaPulldownSnakemake` tag `2.5.0`, feature-only execution is exposed by the upstream config key:

```yaml
only_generate_features: true
```

The Snakefile then targets the required feature files and does not run `run_structure_prediction.py`.

## Inputs

- Canonical FASTA files from `data/processed/fasta/`.
- FASTA manifest from `data/processed/fasta/fasta_manifest.tsv`.
- Remote configuration from `config/remote/paths.env`.
- Feature-generation template from `config/remote/feature_generation.example.yaml`.

The remote helper writes a resolved `feature_inputs.txt` containing absolute paths to the verified FASTA files. This prevents the workflow from downloading UniProt sequences during this stage.

## Modes

### Local Database Mode

Use this when AlphaFold-compatible sequence/template databases already exist on the Linux host.

Required path:

- `DATABASES_DIR`

This mode should be preferred on a well-provisioned cluster because it avoids dependence on external MSA services.

### Remote MMseqs2 Mode

Use this when local AlphaFold databases are unavailable and the selected AlphaPulldown workflow supports `--use_mmseqs2`.

Pinned AlphaPulldown `2.5.0` rejects `--use_mmseqs2` with `--data_pipeline alphafold3`. Therefore this project resolves MMseqs2 mode to the AlphaFold2 data pipeline/backend and expects compressed AF2 feature pickles unless overridden after a real remote dry run.

Requirements:

- Do not overwrite existing MSAs silently.
- Keep `SKIP_EXISTING=1` unless deliberately regenerating.
- Preserve logs and provenance.
- Record that MMseqs2 was used.

## Expected Outputs

For the default local-database AlphaFold3 mode in AlphaPulldownSnakemake `2.5.0`, generated individual feature files are expected under:

```text
<output_directory>/features/{record_id}_af3_input.json
```

For AlphaFold2/MMseqs2 mode with compressed features, the expected pattern is:

```text
<output_directory>/features/{record_id}.pkl.xz
```

Adjust `FEATURE_FILE_PATTERN` in `config/remote/paths.env` only after confirming the deployed workflow output.

## Dry Run

```bash
bash scripts/remote/run_feature_generation.sh --dry-run
```

Dry run validates paths and prints the Snakemake command without starting feature generation.

## Failure Modes

- Missing databases in local database mode.
- Remote MMseqs2 service unavailable.
- Existing MSA files overwritten unintentionally.
- FASTA manifest out of sync with FASTA directory.
- Insufficient temporary storage.
- Workflow version changes feature output naming.
