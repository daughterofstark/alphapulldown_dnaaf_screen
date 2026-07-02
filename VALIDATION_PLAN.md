# Validation Plan

## Principles

Validation must be designed before discovery-scale screening. The goal is not to prove AlphaFold is always right, but to define where predictions are reliable enough to prioritize experiments.

## Positive Controls

Primary positive controls:

- DNAAF9 with IFT74.
- DNAAF9 with IFT81.
- DNAAF2 with DNAAF4.
- DNAI1 with DNAI2.

Secondary/contextual positives:

- DNAAF12 with IFT88, with species context documented.
- Chlamydomonas DNAAF18/ODA16 with Chlamydomonas IFT46, if orthologous workflows are added.

Success criteria:

- Positive controls should produce high or interpretable confidence.
- PAE should show a clear inter-chain low-error block at the interface.
- Interface residues should be structurally plausible and not dominated by low-confidence disorder.

## Negative Controls

Primary negative controls:

- Human DNAAF18 with human IFT46.
- DNAAF7 with IFT43.
- Biologically unrelated cytoplasmic proteins matched for size where possible.
- Same-protein-family but incompatible assembly-stage pairs.

Success criteria:

- Negative controls should not rank as high-confidence human direct interactions.
- Any high score in a negative control triggers manual review of PAE, interface geometry, and literature assumptions.

## Benchmark Datasets

Internal benchmark:

- Known DNAAF, ODA, and IFT interactions from the literature survey.
- Known non-interactions or species-specific non-conserved interactions.

External benchmark candidates:

- AlphaPulldown example datasets.
- Published AlphaFold-Multimer PPI benchmark subsets.
- Curated PDB dimers with similar size and domain architecture.

Benchmark datasets should be stored under `data/benchmark/` with provenance and license notes.

## Expected Successful Predictions

The pipeline should plausibly recover:

- DNAI1-DNAI2 intermediate-chain dimer.
- DNAAF2-DNAAF4 R2TP-like interaction.
- DNAAF9-IFT74 and DNAAF9-IFT81 transport-associated interactions.

Recovery may depend on whether full-length or domain-level constructs are used.

## Expected Failures

The pipeline may fail or under-rank:

- Transient interactions that require post-translational states.
- Interactions mediated by additional proteins.
- Condensate-driven interactions involving disordered regions.
- Large dynein heavy-chain interactions requiring domain context.
- Species-specific interactions translated incorrectly to human proteins.

Expected failures should be reported, not hidden.

## Cross-Validation

Candidate predictions should be cross-validated with:

- Replicate AlphaFold-Multimer models.
- Alternative seeds.
- Domain-level predictions.
- AlphaFold3 for selected top candidates.
- Orthologous predictions for conserved mechanisms.
- Literature, localization, and co-expression evidence.

## Future Wet-Lab Validation

Computational outputs should support tiered experimental validation:

- Pull-down assays using predicted interaction domains.
- Co-IP in HAECs or transfected HEK293T cells.
- Proximity ligation or BioID during ciliogenesis.
- SEC-MALS or native PAGE for stable complexes.
- HDX-MS for interface mapping.
- Interface-disrupting mutagenesis.
- CRISPR knock-in rescue or disruption assays.
- Ciliary localization and motility assays.

## Prioritization Criteria

Interactions should be prioritized for experiments when they satisfy several of:

- High ipTM or corrected interface confidence.
- Low inter-chain PAE at the interface.
- Replicate consistency.
- BSA and contact patterns consistent with a real interface.
- Conserved interface residues.
- PCD variant overlap.
- Strong biological rationale.
- Novelty and mechanistic importance.
- Feasible recombinant expression or cell-based assay design.

## Reporting Validation Results

Every validation report should include:

- Control-pair list.
- Software versions and model settings.
- Score distributions.
- PAE heatmaps.
- Representative structures.
- Pass/fail interpretation.
- Limitations and rerun recommendations.

