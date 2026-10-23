# Contributing

This repository records a defined AlphaPulldown pilot. Changes should preserve
the separation between the Milestone 2 benchmark and the broader target set.

- Keep target records, FASTA files, and generated inputs reproducible.
- Do not commit credentials, cloud configuration, databases, or raw prediction
  outputs.
- Add a regression test when changing validation, configuration, or result
  parsing behaviour.
- Update the concise documents in `docs/` when a scientific conclusion or
  documented method changes.

Before opening a pull request, run:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```
