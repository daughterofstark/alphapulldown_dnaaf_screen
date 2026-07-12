# AlphaPulldown DNAAF-ODA-IFT Screen

Research-grade planning repository for a reproducible AlphaPulldown pipeline to screen candidate protein-protein interactions among mammalian DNAAFs, Outer Dynein Arm proteins, and Intraflagellar Transport proteins.

## Motivation

Axonemal dynein arms are assembled in the cytoplasm by DNAAFs and delivered into motile cilia by IFT trains. Many PCD-associated genes are involved in this pathway, but most direct DNAAF-ODA and DNAAF-IFT interfaces remain unmapped. This project will develop a transparent computational workflow for generating structural hypotheses that can later be tested experimentally.

This repository is currently in the architecture and planning phase. It does not yet implement the scientific pipeline.

The current implemented layer is CPU-side preparation only. It validates verified UniProt targets, writes deterministic FASTA files, builds AlphaPulldown-compatible input files, and records provenance. AlphaPulldown inference is intentionally deferred to a Linux host with NVIDIA CUDA.

## Planned Features

- Curated target manifests for all 19 mammalian DNAAFs, ODA proteins, ODAD proteins, and IFT proteins.
- Scripted UniProt retrieval and validation.
- Reproducible FASTA generation.
- AlphaPulldown-compatible pair generation.
- CPU-side preparation CLI for target validation, FASTA generation, screen definitions, and AlphaPulldown input files.
- Positive and negative control validation.
- AlphaFold-Multimer prediction orchestration.
- Score extraction for ipTM, pTM, ranking confidence, pLDDT, and PAE.
- Interface analysis including residues, buried surface area, hydrogen bonds, and salt bridges.
- Conservation, disease-variant, and literature annotation.
- Publication-ready reports and figures.

## Installation

Implementation has not started. A future installation will likely use:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

AlphaPulldown, AlphaFold databases, CUDA, and GPU environment setup will be documented before prediction workflows are implemented.

CPU-side preparation commands:

```bash
PYTHONPATH=src python -m alphapulldown_dnaaf_screen.cli validate-targets
PYTHONPATH=src python -m alphapulldown_dnaaf_screen.cli write-fastas
PYTHONPATH=src python -m alphapulldown_dnaaf_screen.cli build-screens
PYTHONPATH=src python -m alphapulldown_dnaaf_screen.cli prepare-alphapulldown
```

## Directory Structure

```text
docs/                  project documentation, design notes, protocols
data/raw/              immutable downloaded records
data/processed/        generated validated metadata and FASTA files
data/benchmark/        controls and benchmark datasets
data/manifest/         curated target manifests
config/                pipeline configuration
workflows/             future Snakemake/Nextflow/GitHub workflow assets
scripts/               future command-line utilities
src/                   Python package source
notebooks/             exploratory analyses
results/               generated outputs, ignored by Git
tests/                 automated tests
environment/           environment and container specifications
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for milestones. The immediate local priority is CPU-side preparation and AlphaPulldown input characterization; AlphaPulldown installation, inference, and official-example execution are deferred to a Linux GPU environment.

## Scientific Status

Computational predictions from this project will be treated as hypotheses. Candidate interactions must be evaluated using multiple evidence types, including AlphaFold confidence metrics, PAE, interface geometry, conservation, literature context, and future wet-lab validation.

## Citation

Citation metadata is provided in [CITATION.cff](CITATION.cff) with placeholder project details. Update it before public release.

## License

No final open-source license has been chosen yet. See [LICENSE](LICENSE) for the current placeholder. Choose a license before public distribution.
