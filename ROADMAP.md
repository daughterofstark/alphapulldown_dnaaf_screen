# Roadmap

## Completed

### Repository and input preparation

- Established a version-controlled project structure, configuration templates,
  target-validation code, FASTA generation, screen definitions, provenance,
  and offline tests.
- Prepared a verified human target universe and a separate Milestone 2
  benchmark manifest. The benchmark cannot fall back to the 62-target screen.

### AlphaPulldown runtime validation

- Audited AlphaPulldown and AlphaPulldownSnakemake 2.5.0.
- Built and validated a Docker-native AlphaPulldown 2.5.0 / AlphaFold2 runtime
  on AWS with CPU and GPU smoke tests.
- Generated reusable MMseqs2 feature files for nine human benchmark proteins.

### Milestone 2 pilot

- Completed four AlphaFold2-Multimer prediction sets.
- Parsed native AlphaPulldown outputs into ipTM, ranking confidence, mean
  pLDDT, and coarse inter-chain PAE summaries.
- Recorded one host-RAM-limited incomplete run and deferred larger assemblies.

See [Milestone 2 Pilot Results](docs/validation/MILESTONE2_PILOT_RESULTS.md).

## Current Decision Point

Review the four ranked structures and PAE plots with the supervisor. The
completed pilot supports workflow validation and hypothesis generation, not a
claim of direct interaction for the exploratory assemblies.

## Future Work

### 1. Resource planning for larger assemblies

Select a Linux GPU host with adequate system RAM before rerunning the incomplete
DNAAF9 + IFT46 + IFT74 + IFT81 assembly or attempting the remaining larger
complexes. Record the resource plan before compute begins.

### 2. Evidence-guided structural review

For any candidate selected after review:

- inspect PAE and ranked structures in ChimeraX;
- assess interface geometry and biological plausibility;
- compare against literature and conservation evidence; and
- define any construct boundaries from evidence rather than arbitrary truncation.

### 3. Expand only after the pilot review

The larger DNAAF x ODA x IFT screen remains out of scope until the pilot is
reviewed and the target universe, construct policy, compute budget, and
interpretation criteria are approved.
