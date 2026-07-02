# Contributing

Thank you for helping build this project carefully. The repository is intended to become a reproducible computational biology toolkit, so changes should preserve provenance, transparency, and scientific interpretability.

## Before Contributing

- Read `PROJECT_CONTEXT.md`, `IMPLEMENTATION_PLAN.md`, and `DEVELOPMENT_GUIDE.md`.
- Open an issue for major scientific, architectural, or data-curation decisions.
- Do not commit large generated AlphaFold/AlphaPulldown outputs.

## Development Setup

Implementation has not started yet. The expected future setup is:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Pull Requests

Pull requests should include:

- A concise description of the change.
- Relevant issue links.
- Tests or a rationale for why tests are not needed.
- Documentation updates when behavior, data schema, or scientific assumptions change.
- Notes about provenance for data-affecting changes.

## Data Rules

- Do not manually edit generated FASTA or derived metadata files.
- Raw downloaded records must include source, retrieval date, database release, and checksum.
- Sequence and accession changes require review.

## Scientific Review

Changes to target lists, scoring thresholds, controls, validation criteria, or biological interpretation should be reviewed as scientific decisions, not only code changes.

