# Development Guide

## Coding Standards

- Use Python 3.11 or later unless AlphaPulldown compatibility requires otherwise.
- Prefer typed, testable modules under `src/alphapulldown_dnaaf_screen/`.
- Keep notebooks exploratory; production logic belongs in package modules and scripts.
- Use explicit schemas for manifests and configuration.
- Avoid manual editing of generated data.
- Preserve provenance for every external data retrieval and prediction run.

## Formatting and Linting

Planned tools:

- Ruff for linting and formatting.
- Black-compatible formatting through Ruff.
- mypy or pyright for type checking once the package stabilizes.
- pre-commit for local checks.

## Branch Strategy

Suggested branches:

- `main`: stable, documented, and passing CI.
- `develop` or short-lived feature branches: optional depending on team size.
- `feature/<topic>`: focused work.
- `docs/<topic>`: documentation-only work.
- `analysis/<topic>`: reproducible analysis additions.

Avoid committing large generated results to Git.

## GitHub Workflow

- Open issues for new features, bugs, data-curation questions, and scientific decisions.
- Use pull requests for all changes to `main`.
- Require CI to pass before merge once implementation begins.
- Include provenance notes for data-affecting changes.
- Review scientific assumptions separately from code mechanics when needed.

## Testing

Test categories:

- Unit tests for pure functions and schemas.
- Integration tests with small fixtures.
- Slow tests for external tools.
- GPU tests marked separately and skipped by default.

Every bug fix should include a regression test when practical.

## Documentation

Documentation should be updated in the same pull request as behavior changes. Scientific assumptions, threshold changes, target-list changes, and accession changes require explicit documentation.

## Commit Conventions

Use concise conventional-style commits where practical:

- `docs: add validation plan`
- `feat: add target manifest schema`
- `fix: correct IFT-B duplicate target validation`
- `test: add PAE slicing fixtures`
- `chore: update pre-commit config`

## Release Strategy

Early releases should be clearly labeled:

- `v0.1.0`: documentation and manifest schema.
- `v0.2.0`: UniProt retrieval and validation.
- `v0.3.0`: control-pair AlphaPulldown workflow.
- `v1.0.0`: reproducible full screen and report generation.

Each release should include:

- Changelog.
- Git tag.
- Environment lock files.
- Data/provenance manifest.
- Citation metadata update.

## Data and Result Governance

- Raw external records are immutable snapshots.
- Processed files must be regenerated from scripts.
- Large prediction outputs should be stored outside Git with checksums.
- Any manually curated record must include reviewer and source notes.

