# Implementation Plan

This document specifies the future architecture. It does not authorize implementing the scientific pipeline during the repository-initialization phase.

## Directory Structure

```text
alphapulldown/
  docs/
    literature/       # survey notes and source summaries
    design/           # design decisions and ADRs
    protocols/        # computational SOPs
    presentations/    # talks and lab-meeting materials
    meeting_notes/    # project decisions and reviews
    architecture/     # detailed technical architecture docs
    validation/       # control-pair and benchmark plans
    references/       # curated bibliographic notes
  data/
    raw/              # immutable downloaded source records
    processed/        # generated validated manifests and tables
    benchmark/        # controls and benchmark datasets
    manifest/         # hand-reviewed target manifests, no sequences by hand
  config/             # YAML/TOML configuration
  workflows/          # Snakemake/Nextflow/GitHub workflow support
  scripts/            # CLI entry points and utility scripts
  src/alphapulldown_dnaaf_screen/
  notebooks/          # exploratory notebooks only, not core pipeline
  results/            # generated outputs, mostly ignored by Git
  tests/
  environment/        # conda/container/pip lock files
```

## Software Architecture

The future implementation should be a Python package with small command-line tools. The package should separate scientific data models, external-service adapters, workflow orchestration, and analysis logic.

Proposed modules:

- `targets`: schema models for proteins, target sets, pairs, controls, species, isoforms, and domains.
- `uniprot`: UniProt retrieval clients, raw-record storage, release capture, and accession validation.
- `fasta`: FASTA generation from validated records.
- `pairs`: pair-matrix generation for pull-down and all-vs-all modes.
- `alphapulldown`: wrappers that write AlphaPulldown-compatible input files and submit jobs.
- `provenance`: run metadata, environment capture, database versions, command-line hashes, and config hashes.
- `scores`: parsing of AlphaFold/AlphaPulldown ranking outputs.
- `pae`: PAE matrix loading, slicing, summarization, and visualization.
- `interfaces`: interface residue extraction, BSA/contact integration, and chain mapping.
- `annotation`: literature, domain, conservation, and disease-variant annotations.
- `reports`: reproducible report generation.
- `cli`: Typer or argparse command entry points.

## Data Flow

1. `data/manifest/targets.yaml` defines protein targets by gene, species, accession policy, and group.
2. Retrieval commands download raw source records to `data/raw/uniprot/`.
3. Validation commands produce `data/processed/targets.validated.json` and `data/processed/targets.validated.tsv`.
4. FASTA generation creates `data/raw/fasta/` or `data/processed/fasta/` files from validated records.
5. Pair generation writes `data/processed/pairs/*.tsv`.
6. AlphaPulldown preparation writes feature-generation inputs.
7. Prediction jobs write run directories under `results/predictions/<run_id>/`.
8. Score extraction writes normalized tables under `results/tables/<run_id>/`.
9. Analysis steps write figures, interface tables, and reports under `results/analysis/<run_id>/`.

Raw downloaded records should be immutable. Processed outputs may be regenerated. Results should be too large for Git and should be tracked through manifests, checksums, or external artifact storage.

## Configuration Strategy

Use layered configuration:

- `config/project.yaml`: species, target groups, default thresholds, output roots.
- `config/controls.yaml`: positive and negative controls.
- `config/alphapulldown.yaml`: model presets, recycling, seeds, database paths, and GPU settings.
- `config/scoring.yaml`: confidence tiers and interface thresholds.
- `config/reporting.yaml`: figure themes and report sections.

Every command should accept `--config` and write a resolved configuration snapshot into its run directory.

## Logging and Provenance

Use structured logging with JSON lines for pipeline commands and human-readable console output for interactive use. Every run should capture:

- UTC timestamp and local timezone.
- Git commit SHA and dirty-worktree status.
- Command-line arguments.
- Resolved configuration.
- Python version and package versions.
- AlphaPulldown, AlphaFold, CUDA, database, and model versions.
- Input file checksums.
- Output file checksums for final artifacts.

## Error Handling

Failures should be explicit, typed, and resumable. Expected failure categories include:

- Missing or ambiguous UniProt accession.
- Species mismatch.
- Sequence-length mismatch.
- Duplicate gene symbol.
- Failed MSA generation.
- GPU out-of-memory.
- Missing AlphaFold database path.
- Corrupt prediction output.
- Missing PAE or ranking file.

The pipeline should produce a failed-run manifest with enough information to rerun only failed jobs.

## Parallelization and GPU Usage

The design should support three execution modes:

- Local serial execution for validation and development.
- Local multi-process execution for retrieval, parsing, and analysis.
- Cluster or workflow-engine execution for feature generation and GPU predictions.

GPU jobs should be isolated by pair or small batches. Runtime configuration should include GPU memory expectations, maximum sequence length, number of models, recycling count, random seeds, and retry limits. Long ODA heavy chains may require domain-level or staged modeling policies.

## Checkpointing

Every expensive stage should have checkpoint files:

- Retrieval complete marker with source checksums.
- Validation report.
- Feature-generation completion marker.
- Prediction completion marker per pair.
- Score extraction table with model count verification.
- Analysis completion marker.

Checkpoint validity should depend on input checksums and resolved configuration hashes, not only file existence.

## Output Organization

Prediction outputs should be grouped by run identifier:

```text
results/
  predictions/<run_id>/<bait>__<prey>/
  tables/<run_id>/
  figures/<run_id>/
  reports/<run_id>/
  logs/<run_id>/
  provenance/<run_id>/
```

Use stable pair identifiers such as `HUMAN_DNAAF9__HUMAN_IFT74`. Avoid spaces and alias-dependent names in paths.

## Testing Strategy

Testing should scale with risk:

- Unit tests for schema validation, pair generation, FASTA writing, accession parsing, score parsing, and PAE slicing.
- Snapshot tests for small validated manifests.
- Integration tests using tiny mock AlphaPulldown outputs.
- Optional GPU smoke tests marked separately and excluded from normal CI.
- Regression tests for scoring thresholds and confidence-tier classification.

## Continuous Integration

CI should initially run formatting, linting, type checks, and tests. GPU and external database tests should not run on standard GitHub-hosted runners. Later CI can include:

- Manifest schema validation.
- Documentation link checks.
- Notebook execution for lightweight examples.
- Release artifact validation.

## Future Extensibility

Design choices should allow:

- Additional species.
- Ortholog screens.
- Domain-level screens.
- AF3 or other model backends.
- Workflow engines such as Snakemake or Nextflow.
- Interface tools including PISA, FreeSASA, NACCESS, Arpeggio, and ChimeraX.
- Export to Cytoscape, NDEx, CSV/TSV, JSON, and publication tables.

