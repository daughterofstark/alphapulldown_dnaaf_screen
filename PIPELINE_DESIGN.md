# Pipeline Design

This document describes the planned computational stages. Implementation is deferred until the planning phase is complete.

## Stage 1: Target Manifest Curation

Inputs:

- Literature survey.
- Curator-reviewed target list.
- Species and isoform policies.

Outputs:

- `data/manifest/targets.yaml`.
- Review notes in `docs/literature/`.

Validation:

- Unique record identifiers.
- Valid protein groups.
- Required fields present.

Failure modes:

- Duplicate genes.
- Ambiguous aliases.
- Missing species or accession policy.

Runtime:

- Human curation; minutes for automated schema validation.

Required software:

- Python validation CLI, YAML parser.

GPU:

- None.

## Stage 2: UniProt Retrieval

Inputs:

- Target manifest.

Outputs:

- Raw UniProt records in `data/raw/uniprot/`.
- Retrieval metadata and checksums.

Validation:

- Accession resolves.
- Species and gene match manifest.
- Reviewed/canonical status is recorded.

Failure modes:

- API outage.
- Deprecated accession.
- Multiple matching records.
- Species mismatch.

Runtime:

- Seconds to minutes for dozens of proteins.

Required software:

- Python HTTP client, UniProt REST API.

GPU:

- None.

## Stage 3: Metadata Validation

Inputs:

- Raw UniProt records.
- Target manifest.

Outputs:

- Validated JSON/TSV manifests.
- Validation report.

Validation:

- Sequence length and checksum.
- Canonical isoform.
- Domain annotations if available.

Failure modes:

- Missing sequence.
- Inconsistent isoform.
- Unexpected sequence drift.

Runtime:

- Seconds.

Required software:

- Python, schema validation.

GPU:

- None.

## Stage 4: FASTA Generation

Inputs:

- Validated target records.

Outputs:

- AlphaPulldown-compatible FASTA files.
- FASTA checksum manifest.

Validation:

- FASTA headers match stable record IDs.
- Sequence alphabet contains valid amino-acid symbols.

Failure modes:

- Invalid characters.
- Missing target record.

Runtime:

- Seconds.

Required software:

- Python.

GPU:

- None.

## Stage 5: Pair Matrix Generation

Inputs:

- Validated targets.
- Screen configuration.
- Control-pair configuration.

Outputs:

- Pair TSV files for control, targeted, and full screens.

Validation:

- No self-pairs unless explicitly configured.
- Positive and negative controls present.
- No duplicate pair IDs.

Failure modes:

- Missing bait or prey.
- Conflicting control labels.

Runtime:

- Seconds.

Required software:

- Python.

GPU:

- None.

## Stage 6: AlphaPulldown Feature and MSA Generation

Inputs:

- FASTA files.
- AlphaPulldown configuration.
- AlphaFold/ColabFold database paths or server settings.

Outputs:

- Feature files and MSAs.
- Logs and provenance snapshots.

Validation:

- MSA exists for each protein.
- Feature files are readable.
- Database/software versions captured.

Failure modes:

- Database path missing.
- MSA server unavailable.
- Poor MSA depth.
- Sequence too long.

Runtime:

- Minutes to hours depending on database strategy.

Required software:

- AlphaPulldown, AlphaFold/ColabFold dependencies, MMseqs2 or configured MSA backend.

GPU:

- Usually none for MSA, unless backend requires GPU acceleration.

## Stage 7: AlphaFold-Multimer Prediction

Inputs:

- Feature files.
- Pair matrix.
- Model configuration.

Outputs:

- Ranked models.
- PDB/mmCIF files.
- PAE JSON/NPY files.
- Ranking JSON.
- Logs.

Validation:

- Expected number of models per pair.
- Ranking confidence present.
- PAE output present.

Failure modes:

- GPU out-of-memory.
- Job timeout.
- Corrupt output.
- Missing chain labels.
- Stochastic model disagreement.

Runtime:

- Highly variable; minutes to hours per pair depending on length and sampling.

Required software:

- AlphaPulldown, AlphaFold-Multimer, CUDA/JAX stack, model parameters, sequence databases.

GPU:

- Required for practical inference. Memory requirements depend on total sequence length.

## Stage 8: Score Extraction

Inputs:

- Prediction directories.

Outputs:

- Normalized score tables.
- Failed-output manifest.

Validation:

- Every configured pair has complete, partial, or failed status.
- ipTM, pTM, ranking confidence, and model IDs parsed.

Failure modes:

- Version-specific output format changes.
- Missing metrics.

Runtime:

- Seconds to minutes.

Required software:

- Python, pandas/polars.

GPU:

- None.

## Stage 9: PAE Analysis

Inputs:

- PAE matrices.
- Chain-residue mappings.
- Score tables.

Outputs:

- PAE summaries.
- Inter-chain PAE metrics.
- Heatmaps.

Validation:

- Matrix dimensions match total modeled residues.
- Chain slicing is correct.

Failure modes:

- Chain-order mismatch.
- Missing residue ranges for truncated models.

Runtime:

- Seconds to minutes.

Required software:

- Python, NumPy, matplotlib/seaborn.

GPU:

- None.

## Stage 10: Interface Extraction

Inputs:

- Ranked structures.
- Chain maps.
- Confidence-filtered model list.

Outputs:

- Interface residue tables.
- Contact maps.
- Buried surface area and bond metrics when tools are configured.

Validation:

- Only models passing confidence gates are analyzed by default.
- Residues map back to canonical coordinates.

Failure modes:

- Missing external tool.
- Low-confidence interface geometry.
- Alternate chain naming.

Runtime:

- Seconds to minutes per model.

Required software:

- FreeSASA/NACCESS/PISA/Arpeggio or equivalent, depending on final choice.

GPU:

- None.

## Stage 11: Biological Annotation

Inputs:

- Interface tables.
- Domain annotations.
- Conservation scores.
- Disease-variant tables.
- Literature annotations.

Outputs:

- Annotated candidate table.
- Prioritization features.

Validation:

- All annotations include source and date.
- Coordinate systems are explicit.

Failure modes:

- Residue numbering mismatch.
- Variant source ambiguity.

Runtime:

- Minutes to hours depending on external analyses.

Required software:

- Python, optional ConSurf/HMMER integrations.

GPU:

- None.

## Stage 12: Visualization and Reports

Inputs:

- Scores, structures, PAE summaries, interface annotations.

Outputs:

- Figures.
- HTML/PDF reports.
- Supplementary tables.

Validation:

- Figures are generated from source data.
- Report includes run metadata and limitations.

Failure modes:

- Missing figure inputs.
- Non-reproducible manual edits.

Runtime:

- Minutes.

Required software:

- Python plotting libraries, Quarto/Jupyter/Sphinx as selected.

GPU:

- None.

