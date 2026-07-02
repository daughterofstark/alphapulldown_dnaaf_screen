# Roadmap

This roadmap prioritizes understanding and presenting AlphaPulldown before any large biological screen. The project should first produce a working, reproducible AlphaPulldown installation and a clear explanation of how the pipeline behaves, what it generates, and how its outputs should be interpreted.

## Milestone 0: Repository Setup

Objective: establish a professional, reproducible open-source project structure.

Deliverables:

- Directory structure for docs, data, configuration, workflows, source, tests, results, and environment files.
- README, contributing guide, code of conduct, changelog, citation metadata, license placeholder, issue templates, pull request template, CI skeleton, and pre-commit configuration.
- Initial planning documentation describing the scientific objective and reproducibility expectations.

Dependencies:

- None.

Risks:

- Premature scientific screening before the toolchain and interpretation framework are understood.

Estimated effort:

- 0.5-1 day.

Validation criteria:

- Repository initializes cleanly with Git.
- Documentation and governance files are present.
- Empty directories are tracked through `.gitkeep` files where needed.

## Milestone 1: AlphaPulldown Implementation and Pipeline Characterization

Objective: install AlphaPulldown from source, validate that it can run in the intended environment, and deeply document how the pipeline works before using it for biological discovery.

This milestone treats AlphaPulldown itself as the first object of study. The output should be suitable for explaining the pipeline to a supervisor or lab audience with confidence.

Deliverables:

- `ALPHAPULLDOWN_OVERVIEW.md`: conceptual overview of AlphaPulldown, AlphaFold-Multimer, supported screening modes, and how this project will use the tool.
- `INSTALLATION_GUIDE.md`: source installation procedure, dependency map, environment variables, database paths, version-pinning strategy, and local Mac versus GPU/cluster notes.
- `ALPHAPULLDOWN_PIPELINE.md`: step-by-step description of feature generation, MSA generation, model invocation, prediction, ranking, and report generation.
- `OUTPUT_REFERENCE.md`: annotated directory tree of every generated AlphaPulldown output file and what each file means.
- `SCORING_GUIDE.md`: explanation of ipTM, pTM, pLDDT, ranking confidence, PAE, and which outputs are most useful for downstream biology.
- Presentation-ready workflow diagram showing inputs, AlphaPulldown stages, AlphaFold-Multimer execution, outputs, and interpretation checkpoints.
- Annotated example AlphaPulldown directory tree, even if initially generated from a tiny toy/example run rather than project proteins.
- Notes on ChimeraX inspection workflow and which structural files should be opened first.
- Troubleshooting guide for common installation, database, MSA, GPU, and output-parsing failures.

Dependencies:

- Repository setup.
- Access to a machine suitable for installation testing. Local Mac is acceptable for documentation, source inspection, configuration review, and non-GPU dry runs; GPU or cluster access is required for realistic AlphaFold-Multimer prediction.
- AlphaPulldown source repository and official documentation.

Risks:

- AlphaPulldown, AlphaFold, CUDA/JAX, and database versions may be tightly coupled.
- AlphaFold databases are large and may not fit local storage.
- Local Mac may be insufficient for actual inference.
- Documentation can become stale if it does not record exact AlphaPulldown versions and command outputs.

Estimated effort:

- 1-2 weeks, depending on GPU/database availability.

Validation criteria:

- AlphaPulldown can be installed reproducibly from source or through a documented source-based workflow.
- All major command-line entry points and options are documented.
- Required databases and optional databases are distinguished.
- The feature-generation workflow is explained well enough for a new developer to trace inputs to generated features.
- The mechanism by which AlphaFold-Multimer is invoked is documented.
- Expected runtime and hardware requirements are described for toy, benchmark, and future large-scale runs.
- Every generated output file from an example run is identified and explained.
- Ranking and confidence metrics are explained in presentation-ready language.
- Known failure modes and troubleshooting steps are documented.

## Milestone 2: Pipeline Validation on a Small Benchmark

Objective: validate the understood AlphaPulldown workflow on a very small, biologically motivated benchmark before finalizing the full DNAAF x ODA x IFT screen.

Positive controls:

- DNAAF9 with IFT74.
- DNAAF9 with IFT81.
- DNAAF2 with DNAAF4.
- DNAI1 with DNAI2.

Negative controls:

- DNAAF18 with IFT46 in the human context.
- One or two additional biologically implausible pairs selected and documented before running.

Deliverables:

- `PIPELINE_VALIDATION_REPORT.md`: end-to-end report describing benchmark setup, commands, software versions, runtime, outputs, confidence interpretation, and lessons learned.
- `CONTROL_RESULTS.md`: pair-by-pair summary of positive and negative controls, including all relevant metrics.
- `CHIMERAX_WORKFLOW.md`: reproducible structure-inspection protocol, including how to open ranked models, color chains, inspect interfaces, and capture figures.
- Example AlphaPulldown output directory with annotations and provenance notes.
- PAE analysis for every benchmark prediction.
- Structure-inspection notes for every benchmark prediction.
- Confidence summary for each pair, including whether the result supports, contradicts, or fails to resolve the expected biology.

Dependencies:

- Milestone 1 completed.
- Verified sequences for benchmark proteins.
- AlphaPulldown installation with access to required databases and inference hardware.

Risks:

- Positive controls may fail because of construct length, disorder, missing cofactors, MSA quality, or model/backend limitations.
- Negative controls may produce misleading high scores that require careful interpretation.
- Large ODA or DNAAF proteins may need domain-level constructs even in validation.
- GPU runtime and storage usage may exceed initial expectations.

Estimated effort:

- 1-2 weeks including compute scheduling and manual structural review.

Validation criteria:

- All benchmark predictions have complete output directories or documented failure reasons.
- Every generated metric is explained for every benchmark prediction.
- PAE plots are reviewed and summarized.
- Ranked structures are inspected in ChimeraX.
- Positive-control recovery and negative-control behavior are interpreted cautiously and transparently.
- Lessons learned are fed back into installation, scoring, output-reference, and troubleshooting documentation.

## Milestone 3: Target Universe Finalization

Objective: finalize the complete biological target set only after the AlphaPulldown workflow and benchmark behavior are understood.

Deliverables:

- `TARGET_REVIEW.md`: included proteins, excluded/deferred proteins, unresolved decisions, and final first-pass screen scope.
- Final decision on IFT70 paralogs (`TTC30A` and `TTC30B`).
- Final ODA heavy-chain strategy: full-length, domain-level, staged, or deferred.
- Final DNAAF isoform policy.
- Final IFT-A versus IFT-B scope for the first biological screen.
- Updated target manifest and validation report.

Dependencies:

- Milestone 2 lessons learned.
- UniProt verification outputs.
- Supervisor/lab review of screen scope.

Risks:

- Biological target enthusiasm may outpace compute feasibility.
- Full-length proteins may be technically impractical.
- Ambiguous aliases or isoforms may lead to wrong input sequences.

Estimated effort:

- 3-5 days.

Validation criteria:

- Every target has a stable identifier, verified accession, species, isoform policy, and inclusion rationale.
- Deferred targets are explicitly documented rather than silently omitted.
- The screen scope is small enough to be computationally realistic and large enough to answer the biological question.

## Milestone 4: Reproducible Input Generation

Objective: generate validated AlphaPulldown-ready inputs for the finalized biological screen.

Deliverables:

- Scripted UniProt retrieval and validation workflow.
- FASTA generation from validated records.
- Pair matrices for controls, targeted screens, and full screens.
- Configuration files for AlphaPulldown or AlphaPulldownSnakemake.
- Input provenance report with checksums.

Dependencies:

- Final target universe.
- Milestone 1 installation documentation.

Risks:

- Sequence drift between UniProt releases.
- Manual editing of intermediate files.
- Pair matrix explosion if the scope is not controlled.

Estimated effort:

- 3-5 days.

Validation criteria:

- Inputs are regenerated from scripts with no manual sequence edits.
- Checksums and database release metadata are captured.
- Control pairs and discovery pairs are clearly separated.

## Milestone 5: Targeted Biological Screen

Objective: run a focused biological screen before the full DNAAF x ODA x IFT matrix.

Suggested first focus:

- DNAAF9 and DNAAF18 with IFT-B proteins, especially IFT74, IFT81, and IFT46.
- Additional transport-linked DNAAFs such as DNAAF12 and DNAAF17 if compute budget allows.

Deliverables:

- Targeted screen configuration.
- Ranked score table.
- PAE and interface figures.
- Biological triage memo.
- Updated lessons learned for full-screen design.

Dependencies:

- Milestone 2 benchmark validation.
- Finalized target scope and input generation.

Risks:

- Binary IFT subunit predictions may not capture full IFT-train context.
- Species-specific interactions may be overinterpreted.

Estimated effort:

- 1 week plus compute time.

Validation criteria:

- Known DNAAF9 interactions are reproduced or failures are explained.
- DNAAF18-IFT46 is interpreted in human-specific context.
- New candidates are classified by confidence tier and biological plausibility.

## Milestone 6: Large-Scale DNAAF x ODA x IFT Screen

Objective: run the full approved biological interaction matrix.

Deliverables:

- Full pair matrix.
- Prediction outputs.
- Score and provenance database.
- Failed-run report and rerun queue.
- Versioned screen manifest.

Dependencies:

- Validated controls.
- Targeted-screen lessons learned.
- Compute budget and storage plan.

Risks:

- GPU time, disk usage, long proteins, failed MSAs, and incomplete predictions.
- False positives from overconfident models.
- False negatives for transient, disordered, or multi-component interactions.

Estimated effort:

- 2-4 weeks depending on hardware and sampling strategy.

Validation criteria:

- At least 95% of configured pairs complete or have documented failure reasons.
- Outputs are traceable to exact inputs, configurations, and software versions.

## Milestone 7: Interface Analysis

Objective: convert ranked models into interpretable interface evidence.

Deliverables:

- Interface residue tables.
- Buried surface area, hydrogen bond, salt bridge, and contact metrics.
- PAE-derived interface confidence summaries.
- Interface figures for high-confidence candidates.

Dependencies:

- Prediction outputs.
- Scoring guide from Milestone 1.

Risks:

- Interface metrics computed for low-confidence poses can create false certainty.

Estimated effort:

- 1-2 weeks.

Validation criteria:

- Interface analysis runs only on models passing configurable confidence gates.
- Tables include model identifiers and chain-residue mapping.

## Milestone 8: Visualization and Ranking

Objective: produce interpretable visual and tabular outputs for scientific review.

Deliverables:

- PAE heatmaps.
- ChimeraX/PyMOL scenes.
- Network plots.
- Candidate ranking tables.
- Supervisor-facing presentation figures.

Dependencies:

- Interface analysis.

Risks:

- Figures may overstate model certainty.

Estimated effort:

- 1-2 weeks.

Validation criteria:

- Every figure has source data and generation code.
- Confidence tiers are visually explicit.

## Milestone 9: Report Generation

Objective: generate reproducible reports for internal review and publication preparation.

Deliverables:

- HTML/PDF reports.
- Supplementary tables.
- Methods text draft.
- Reproducibility checklist.

Dependencies:

- Ranking and visualization outputs.

Risks:

- Manual report editing breaks reproducibility.

Estimated effort:

- 1 week.

Validation criteria:

- Reports are generated from version-controlled templates and data.
- Reports distinguish computational hypotheses from experimental evidence.

## Milestone 10: Publication-Ready Analyses

Objective: prepare a final computational study package suitable for manuscript submission.

Deliverables:

- Frozen release tag.
- Archived input manifests.
- Zenodo-ready artifact bundle.
- Final methods and supplementary tables.
- Reproducibility checklist.

Dependencies:

- Complete analysis and validation.

Risks:

- Late-stage changes to accessions, software versions, scoring thresholds, or target scope.

Estimated effort:

- 1-2 weeks.

Validation criteria:

- A fresh clone can regenerate all non-GPU summary analyses from archived raw outputs.
- GPU-derived outputs are archived with checksums, configuration, and provenance.

