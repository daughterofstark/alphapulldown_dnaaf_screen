# Roadmap

This roadmap intentionally separates repository design, data curation, pipeline validation, and biological discovery. Each milestone should end with reviewable artifacts and validation criteria.

## Milestone 0: Repository Setup

Objective: establish a professional, reproducible open-source project structure.

Deliverables:

- Directory structure for docs, data, configuration, workflows, source, tests, results, and environment files.
- README, contributing guide, code of conduct, changelog, citation metadata, license placeholder, issue templates, pull request template, CI skeleton, and pre-commit configuration.

Dependencies:

- None.

Risks:

- Premature implementation before project conventions are defined.

Estimated effort:

- 0.5-1 day.

Validation criteria:

- Repository initializes cleanly with Git.
- Documentation and governance files are present.
- Empty directories are tracked through `.gitkeep` files where needed.

## Milestone 1: Protein Database Specification

Objective: define the authoritative target universe before sequence retrieval.

Deliverables:

- Curated target manifest schema.
- Initial DNAAF, ODA, and IFT target lists.
- Required metadata fields and validation rules.
- Placeholder records for every planned protein.

Dependencies:

- Project context and literature survey.

Risks:

- Ambiguous gene names, outdated aliases, missing isoform decisions, and accidental inclusion of non-canonical orthologs.

Estimated effort:

- 2-4 days.

Validation criteria:

- Every protein has a stable identifier, species, intended isoform policy, and evidence notes.
- Review checklist catches duplicate genes, duplicated IFT57-style entries, and inconsistent naming.

## Milestone 2: UniProt Retrieval

Objective: implement reproducible retrieval of canonical protein records.

Deliverables:

- Scripted UniProt query workflow.
- Raw UniProt JSON/XML/FASTA snapshots.
- Retrieval logs with dates, query parameters, and database release information.

Dependencies:

- Protein manifest schema.

Risks:

- UniProt accession updates, reviewed/unreviewed ambiguity, isoform-specific records, and API changes.

Estimated effort:

- 2-3 days.

Validation criteria:

- Retrieval is deterministic for a pinned manifest.
- All raw records are stored under `data/raw/uniprot/`.
- No manually edited sequence files are required.

## Milestone 3: Metadata Validation

Objective: validate sequences and annotations before modeling.

Deliverables:

- Metadata validation module.
- Reports for missing fields, accession mismatches, length discrepancies, sequence changes, and non-canonical isoforms.
- Machine-readable validated manifest in `data/processed/`.

Dependencies:

- UniProt retrieval.

Risks:

- Silent sequence drift between database releases.
- Confusing species-specific orthologs with human targets.

Estimated effort:

- 3-5 days.

Validation criteria:

- Tests cover schema errors and accession/sequence mismatches.
- Validation report is suitable for supplementary-methods documentation.

## Milestone 4: AlphaPulldown Installation and Environment

Objective: define a reproducible compute environment without running the biological screen.

Deliverables:

- Environment files for local CPU utilities and GPU inference environment.
- Installation notes for AlphaPulldown, AlphaFold databases, CUDA, and container options.
- Version pinning strategy.

Dependencies:

- Architecture plan.

Risks:

- GPU driver/CUDA incompatibility, large database storage requirements, and mismatch between AlphaPulldown and AlphaFold versions.

Estimated effort:

- 2-5 days depending on compute environment.

Validation criteria:

- Environment can run AlphaPulldown example or tiny smoke test.
- Versions are captured in logs and reports.

## Milestone 5: Pipeline Validation on Controls

Objective: validate the computational workflow on known positive and negative controls.

Deliverables:

- Control-pair configuration.
- Prediction outputs for positive and negative controls.
- Score extraction and PAE visualization.
- Control validation report.

Dependencies:

- Sequence validation and AlphaPulldown environment.

Risks:

- False negatives for transient interactions; false positives from overconfident models.

Estimated effort:

- 1-2 weeks including compute scheduling.

Validation criteria:

- DNAAF9-IFT74, DNAAF9-IFT81, DNAAF2-DNAAF4, and DNAI1-DNAI2 are recovered or failures are explained.
- Human DNAAF18-IFT46 is not ranked as a high-confidence human interaction.

## Milestone 6: Targeted IFT-B Screen

Objective: prioritize DNAAF9 and DNAAF18 interactions with IFT-B proteins.

Deliverables:

- Targeted screen configuration.
- Ranked score table.
- PAE and interface figures.
- Biological triage memo.

Dependencies:

- Validated controls.

Risks:

- Misinterpreting IFT-B train context from binary subunit predictions.

Estimated effort:

- 1 week.

Validation criteria:

- Known DNAAF9 interactions are reproduced.
- New candidates are classified by confidence tier and biological plausibility.

## Milestone 7: Large-Scale Screen

Objective: run the full 19 DNAAF by ODA/IFT target matrix.

Deliverables:

- Full pair matrix.
- Prediction outputs.
- Score and provenance database.
- Failed-run report and rerun queue.

Dependencies:

- Validated targeted screen and compute budget.

Risks:

- GPU time, disk usage, long proteins, failed MSAs, and incomplete predictions.

Estimated effort:

- 2-4 weeks depending on hardware and sampling strategy.

Validation criteria:

- At least 95% of configured pairs complete or have documented failure reasons.
- Outputs are traceable to exact inputs and software versions.

## Milestone 8: Interface Analysis

Objective: convert ranked models into interpretable interface evidence.

Deliverables:

- Interface residue tables.
- Buried surface area, hydrogen bond, salt bridge, and contact metrics.
- PAE-derived interface confidence summaries.

Dependencies:

- Prediction outputs.

Risks:

- Interface metrics computed for low-confidence poses can create false certainty.

Estimated effort:

- 1-2 weeks.

Validation criteria:

- Interface analysis runs only on models passing configurable confidence gates.
- Tables include model identifiers and chain-residue mapping.

## Milestone 9: Visualization and Ranking

Objective: produce interpretable visual and tabular outputs for scientific review.

Deliverables:

- PAE heatmaps.
- ChimeraX/PyMOL scenes.
- Network plots.
- Candidate ranking tables.

Dependencies:

- Interface analysis.

Risks:

- Figures may overstate model certainty.

Estimated effort:

- 1-2 weeks.

Validation criteria:

- Every figure has source data and generation code.
- Confidence tiers are visually explicit.

## Milestone 10: Report Generation

Objective: generate reproducible reports for internal review and publication preparation.

Deliverables:

- HTML/PDF reports.
- Supplementary tables.
- Methods text draft.

Dependencies:

- Ranking and visualization outputs.

Risks:

- Manual report editing breaks reproducibility.

Estimated effort:

- 1 week.

Validation criteria:

- Reports are generated from version-controlled templates and data.

## Milestone 11: Publication-Ready Analyses

Objective: prepare a final computational study package suitable for manuscript submission.

Deliverables:

- Frozen release tag.
- Archived input manifests.
- Zenodo-ready artifact bundle.
- Reproducibility checklist.

Dependencies:

- Complete analysis and validation.

Risks:

- Late-stage changes to accessions, software versions, or scoring thresholds.

Estimated effort:

- 1-2 weeks.

Validation criteria:

- A fresh clone can regenerate all non-GPU summary analyses from archived raw outputs.

