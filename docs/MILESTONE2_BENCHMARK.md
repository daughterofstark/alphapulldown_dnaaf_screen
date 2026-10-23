# Milestone 2 Benchmark

## Design

Milestone 2 is a fixed, small benchmark used to validate the computational
workflow before any large DNAAF x ODA x IFT screen. Its machine-readable
definition is `data/processed/benchmarks/milestone2_scenarios.json`.

The benchmark is independent of the 62-target universe. It has its own FASTA
manifest and AlphaPulldown input sheet, and the runner rejects attempts to fall
back to the full target set.

## Scenarios

| Scenario | Role | Outcome |
| --- | --- | --- |
| Chlamydomonas DNAAF18/ODA16 + IFT46 | Direct positive benchmark in the literature | Blocked: versioned algal records are not present |
| Human DNAAF18 + IFT46 | Species-divergence comparator | Complete |
| Human DNAAF9 + IFT74 + IFT81 | Known-association benchmark | Complete |
| Human DNAAF9 + IFT46 + IFT74 + IFT81 | Exploratory | Incomplete: host RAM limit |
| Human DNAAF9 + IFT80 + IFT172 | Exploratory | Deferred |
| Human DNAI1 + IFT46 + IFT74 + IFT81 | Exploratory | Complete |
| Human DNAI2 + IFT46 + IFT74 + IFT81 | Exploratory | Complete |
| Human DNAI1 + DNAI2 + IFT46 + IFT74 + IFT81 | Exploratory | Deferred |
| Human DNAI1 + DNAI2 + IFT80 + IFT172 | Exploratory | Deferred |

IFT74 and IFT81 were modelled together because they form an IFT-B subcomplex.
The human DNAAF18 + IFT46 condition is a comparator for a reported
species-dependent interaction.
