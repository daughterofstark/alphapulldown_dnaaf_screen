# Implementation Log

| Date | Work completed | Outcome |
| --- | --- | --- |
| 2026-07-13 | Created the repository structure and planning documents. | Established reproducibility, data governance, and documentation conventions before biological screening. |
| 2026-07-13 | Implemented CPU-side target validation, deterministic FASTA generation, screen definitions, provenance records, and offline tests. | Local macOS workflow prepared inputs without AlphaFold inference. |
| 2026-07-13 | Added remote handoff scripts and audited AlphaPulldown/AlphaPulldownSnakemake 2.5.0 behavior. | Identified the required AlphaFold2/MMseqs2 feature semantics and isolated project-local configuration from upstream settings. |
| 2026-08-29 | Built the Docker-native AWS AlphaPulldown runtime and passed CPU and GPU no-data smoke tests. | Confirmed AlphaPulldown 2.5.0, feature-generation CLI, JAX, and NVIDIA GPU visibility. |
| 2026-08-29 to 2026-10-15 | Generated benchmark features and completed four AlphaFold2-Multimer prediction sets. | Produced ranked structures, PAE, confidence, timing, and feature-metadata outputs for four scenarios. |
| 2026-10-19 | Retrieved and SHA-256 verified the AWS output archive; added offline result parsing and the pilot report. | Established a reproducible, cautious summary of the completed outputs. |

## Recorded Limitations

- The Chlamydomonas DNAAF18/ODA16 + IFT46 control is blocked because the
  required versioned sequence records are absent.
- The four-protein DNAAF9 + IFT46 + IFT74 + IFT81 assembly was terminated by
  host-system RAM exhaustion on a 32 GiB AWS instance and was excluded from
  analysis.
- Remaining large assemblies are deferred pending an appropriate resource plan.
