# ADR 0001: Planning-First Repository Initialization

## Status

Accepted

## Context

The project aims to become a reproducible AlphaPulldown pipeline for DNAAF, ODA, and IFT interaction screening. The scientific risk of premature implementation is high because sequence choices, isoform policies, controls, scoring thresholds, and output provenance all affect biological interpretation.

## Decision

Initialize the repository with documentation, governance, configuration placeholders, and test/CI scaffolding before implementing the scientific workflow.

## Consequences

- Future development can proceed from explicit design documents.
- Target curation and validation can be reviewed before compute-heavy prediction.
- The repository starts with publication-oriented reproducibility practices.

