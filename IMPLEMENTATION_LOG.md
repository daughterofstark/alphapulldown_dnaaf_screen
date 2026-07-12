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

Task: Audit remote handoff against pinned upstream AlphaPulldown and AlphaPulldownSnakemake `2.5.0`.

Result:

- Inspected pinned upstream source and documentation for AlphaPulldown commit `1c99b15ce3fef42374c24a5bd83ce8241117d5f6` and AlphaPulldownSnakemake commit `23cbba5f151f843d800b5cffaa7a3a3908c35d9e`.
- Corrected remote command construction to run the deployed upstream Snakefile from `AP_WORKFLOW_DIR` with upstream profile paths.
- Replaced project-local Snakemake config overrides with resolved upstream config files written under `results/provenance/<run_id>/`.
- Corrected feature-only execution to use `only_generate_features: true`.
- Corrected feature naming assumptions to AF3 `{record_id}_af3_input.json` by default and AF2/MMseqs2 `{record_id}.pkl.xz`.
- Corrected prediction wiring so accession screen definitions are rewritten to absolute verified FASTA paths before Snakemake execution.
- Corrected MMseqs2 mode to use the AlphaFold2 data pipeline/backend because AlphaPulldown `2.5.0` rejects `--use_mmseqs2` with `--data_pipeline alphafold3`.
- Added `docs/validation/UPSTREAM_COMPATIBILITY_AUDIT.md`.

Issues:

- Local `pytest` executable is not installed; validation used `python3 -m unittest`.
- AF3 container-specific structure filenames beyond source-verified AF2 `ranked_*.pdb` must be confirmed during a real remote dry run/execution.
- Cluster-specific Singularity/Apptainer bind paths and retry settings remain remote-environment decisions.

Next steps:

- Commit the compatibility audit and remote wrapper corrections.
- On Linux, deploy the pinned workflow, validate the environment, and run the wrapper dry runs before any real feature generation or inference.
