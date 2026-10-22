# Milestone 2 Benchmark Rationale

## Purpose

Milestone 2 uses a small, explicitly defined benchmark to validate the
AlphaPulldown workflow before any large screen. The machine-readable scenario
manifest is `data/processed/benchmarks/milestone2_scenarios.json`.

The benchmark is independent of the 62-target universe. It does not substitute
missing Chlamydomonas sequences with human records.

## Scenario Set

| Scenario | Role | Status |
| --- | --- | --- |
| Chlamydomonas DNAAF18/ODA16 + IFT46 | Positive benchmark | Blocked: required versioned sequence records are absent |
| Human DNAAF18 + IFT46 | Species-divergence comparator | Complete |
| Human DNAAF9 + IFT74 + IFT81 | Known-association benchmark | Complete |
| Human DNAAF9 + IFT46 + IFT74 + IFT81 | Exploratory | Incomplete: host RAM limit |
| Human DNAAF9 + IFT80 + IFT172 | Exploratory | Deferred |
| Human DNAI1 + IFT46 + IFT74 + IFT81 | Exploratory | Complete |
| Human DNAI2 + IFT46 + IFT74 + IFT81 | Exploratory | Complete |
| Human DNAI1 + DNAI2 + IFT46 + IFT74 + IFT81 | Exploratory | Deferred |
| Human DNAI1 + DNAI2 + IFT80 + IFT172 | Exploratory | Deferred |

## Biological Rationale

IFT74 and IFT81 form an obligate IFT-B heterodimer. DNAAF9 is therefore tested
in the IFT74/IFT81 context rather than as separate DNAAF9-IFT74 and
DNAAF9-IFT81 binary predictions. The broader IFT46/IFT74/IFT81 and
IFT80/IFT172 assemblies test candidate interactions in multichain transport
contexts.

Human DNAAF18 + IFT46 is a species-divergence comparator. It must not be
presented as universal evidence that binding is impossible.

## Heavy-Chain Policy

DNAH5 and DNAH9 are deferred. Full-length prediction is not a substitute for
evidence-guided construct design. Any future construct must be literature- or
structure-guided and reviewed before execution.

## Interpretation Boundary

These models generate structural hypotheses. Scores, PAE, chain placement,
literature evidence, and experimental context must be considered together
before prioritizing a candidate.
