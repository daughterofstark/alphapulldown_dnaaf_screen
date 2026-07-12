# Feature Generation Guide

## What Features Are

AlphaPulldown separates per-protein feature generation from pairwise structure prediction. Features include sequence-derived inputs such as MSAs and template information that can be reused across many pair jobs.

Computing features once per protein prevents repeated MSA/template work when the same protein appears in many pairwise screens.

## Inputs

- Canonical FASTA files from `data/processed/fasta/`.
- FASTA manifest from `data/processed/fasta/fasta_manifest.tsv`.
- Remote configuration from `config/remote/paths.env`.
- Feature-generation template from `config/remote/feature_generation.example.yaml`.

## Modes

### Local Database Mode

Use this when AlphaFold-compatible sequence/template databases already exist on the Linux host.

Required path:

- `DATABASES_DIR`

This mode should be preferred on a well-provisioned cluster because it avoids dependence on external MSA services.

### Remote MMseqs2 Mode

Use this when local AlphaFold databases are unavailable and the selected AlphaPulldown workflow supports `--use_mmseqs2`.

Requirements:

- Do not overwrite existing MSAs silently.
- Keep `SKIP_EXISTING=1` unless deliberately regenerating.
- Preserve logs and provenance.
- Record that MMseqs2 was used.

## Expected Outputs

The exact file names are workflow-version dependent. The project uses a configurable feature pattern:

```text
FEATURE_FILE_PATTERN="{record_id}.pkl"
```

Adjust this in `config/remote/paths.env` if the deployed workflow writes a different feature filename.

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

