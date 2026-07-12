# Implementation Log

## 2026-07-13

Task: Begin Milestone 1 CPU-side preparation layer on `feature/alphapulldown-implementation`.

Result:

- Confirmed local macOS is preparation-only; no AlphaPulldown inference or CUDA installation should be attempted locally.
- Inspected existing verified UniProt metadata and raw local UniProt JSON sequence snapshots.
- Found that tracked verified JSON contains metadata and checksums but not sequences; FASTA generation must use raw UniProt sequence snapshots or regenerated raw records.

Issues:

- `data/processed/uniprot/TARGET_VERIFICATION_REPORT.md` had pre-existing local modifications. These were not overwritten.

Next steps:

- Implement target loading, FASTA generation, screen definitions, AlphaPulldown input writers, provenance records, tests, and documentation.

Task: Implement CPU-side preparation layer.

Result:

- Added typed target loading and validation modules.
- Added deterministic FASTA generation.
- Added control benchmark, targeted transport, and future full-screen pair definitions.
- Added AlphaPulldown-compatible accession input writers.
- Added provenance records for generated artifacts.
- Added configuration template for future Linux GPU execution.
- Added synthetic offline tests and CLI smoke tests.

Issues:

- Local `pytest`, `ruff`, and `mypy` executables are not installed. Validation used standard-library `unittest`, `py_compile`, and line-length checks instead.
- Local macOS inference remains out of scope because the machine lacks NVIDIA CUDA.

Next steps:

- Review generated CPU-side artifacts.
- Commit this as a CPU-preparation milestone.
- On Linux GPU access, use `config/alphapulldown.example.yaml` as the starting point for machine-specific AlphaPulldown execution.

Task: Implement remote-execution handoff layer.

Result:

- Added strict remote shell scripts for environment bootstrap, validation, feature generation, prediction, and result collection.
- Added remote configuration templates for paths, feature generation, and prediction.
- Added Python helpers for remote config parsing, command construction, feature coverage checks, full-screen deferral, and provenance creation.
- Added documentation for remote execution, feature generation, GPU inference, and data transfer.
- Added offline tests for remote handoff behavior without AlphaPulldown, Snakemake, CUDA, internet, or GPU dependencies.

Issues:

- Scripts are designed for Linux remote execution and intentionally reject local macOS execution.
- Actual Snakemake rule names and workflow-specific output names must be confirmed on the Linux host after deploying the pinned AlphaPulldownSnakemake workflow.

Next steps:

- Push branch to GitHub.
- On Linux GPU host, copy `config/remote/paths.example.env` to `config/remote/paths.env`, edit paths, validate environment, then dry-run feature generation.
