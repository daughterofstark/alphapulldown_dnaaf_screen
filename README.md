# AlphaPulldown DNAAF-ODA-IFT Screen

This repository contains the reproducible computational framework and pilot
results for a structural-biology study of candidate interactions among
mammalian dynein axonemal assembly factors (DNAAFs), outer dynein-arm (ODA)
proteins, and intraflagellar-transport (IFT) proteins.

The project uses AlphaPulldown with AlphaFold2-Multimer to generate structural
hypotheses. Predictions are not treated as evidence of direct binding without
confidence assessment, biological context, and experimental follow-up.

## Current Status

The completed Milestone 2 pilot established a Docker-native AWS execution
path, generated reusable MMseqs2 features for nine human proteins, and
produced four complete AlphaPulldown prediction output sets.

| Scenario | Status | Best ipTM |
| --- | --- | ---: |
| Human DNAAF18 + IFT46 comparator | Complete | 0.168 |
| Human DNAAF9 + IFT74 + IFT81 known-association benchmark | Complete | 0.369 |
| Human DNAI1 + IFT46 + IFT74 + IFT81 exploratory assembly | Complete | 0.280 |
| Human DNAI2 + IFT46 + IFT74 + IFT81 exploratory assembly | Complete | 0.335 |

The known-association benchmark scored above the DNAAF18-IFT46 comparator, but
all completed models had high global inter-chain PAE. The pilot therefore
validates the computational workflow and provides structural hypotheses; it
does not establish a confident direct interface for the exploratory assemblies.

Read the full report in [Milestone 2 Pilot Results](docs/MILESTONE2_PILOT_RESULTS.md).

## Repository Contents

```text
config/       versioned configuration templates and benchmark definitions
data/         validated target metadata, FASTA manifests, and screen inputs
deployment/   Docker image definition and AWS runtime checks
docs/         active methods, design, deployment, and validation documents
scripts/      reproducible preparation, execution, and result-summary commands
src/          Python package for target validation and runtime orchestration
tests/        offline regression tests
```

Generated outputs, databases, credentials, and machine-specific configuration
are intentionally excluded from Git.

## Reproduce the Pilot Summary

The raw AWS output archive is distributed separately from this repository.
After extracting it, summarize complete prediction directories with:

```bash
PYTHONPATH=src python3 scripts/summarize_milestone2_results.py \
  --results-root /path/to/predictions \
  --output pilot_summary.json
```

The command rejects incomplete output directories. The benchmark boundary and
completed outputs are described in [Milestone 2 Benchmark](docs/MILESTONE2_BENCHMARK.md)
and [Milestone 2 Pilot Results](docs/MILESTONE2_PILOT_RESULTS.md).

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=src python -m unittest discover -s tests -v
```

The project package requires Python 3.11 or later. The pinned AlphaPulldown
2.5.0 AlphaFold2 runtime uses Python 3.10 inside its Docker image; the two
environments are kept separate deliberately.

## Scientific Scope

The current pilot is a closed benchmark. It is isolated from the larger
62-target universe and does not substitute unversioned Chlamydomonas records
with human targets. Larger assemblies remain deferred until an appropriate
host-RAM plan and a supervised review of the completed structures and PAE plots.

## Documentation

The concise scientific record is in [docs/](docs/README.md): project overview,
methods, benchmark design, results, limitations, and references.
