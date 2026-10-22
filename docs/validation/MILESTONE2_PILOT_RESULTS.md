# Milestone 2 Pilot Results

## Scope and Status

This report records the completed portion of the closed Milestone 2
AlphaPulldown benchmark. It is a pipeline-validation and hypothesis-generation
exercise, not evidence of direct interaction on its own.

The benchmark scenario manifest is intentionally isolated from the 62-target
universe at
[`data/processed/benchmarks/milestone2_scenarios.json`](../../data/processed/benchmarks/milestone2_scenarios.json).
The recovered remote output archive was verified before analysis:

```text
milestone2_completed_outputs_20261015.tar.gz
SHA-256: 9bb8c1f618f0a7c7365cc1d4eedcbc9465b065673b2c9967c55a61bc23a2d613
```

The archive contains raw PDB, PAE, confidence, timing, and ranking files for
four completed scenarios. Raw remote outputs remain outside Git; the parser at
[`scripts/summarize_milestone2_results.py`](../../scripts/summarize_milestone2_results.py)
regenerates the numerical summary from those files.

## Execution Summary

- Feature generation: AlphaPulldown individual-feature generation using
  MMseqs2; the nine versioned human target features were generated once and
  reused.
- Prediction backend: AlphaPulldown 2.5.0 with AlphaFold2-Multimer v3 models.
- Completed prediction policy: five multimer parameter models, one prediction
  per model; `ranked_0.pdb` is the model placed first by AlphaFold-Multimer
  ranking confidence.
- Evaluation: ipTM, ranking confidence (`iptm+ptm`), mean per-residue pLDDT,
  and PAE were read from the native AlphaPulldown outputs.

`mean inter-chain PAE` below is the mean of all cross-chain entries in the
top-ranked model's PAE matrix. `<=10 A` is the fraction of those entries at or
below 10 Angstrom. These are coarse summaries of a matrix and do not replace
visual inspection of the PAE plot or interface.

## Completed Predictions

| Scenario | Chains in `ranked_0` | Best model | ipTM | Ranking confidence | Mean pLDDT | Mean inter-chain PAE | Inter-chain PAE <=10 A | Interpretation |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Human DNAAF18 + IFT46, negative/species-divergence benchmark | DNAAF18 (415), IFT46 (304) | model 3 | 0.168 | 0.254 | 72.4 | 29.1 A | 0.0% | Very low interface confidence; a suitable low-confidence comparator, not proof that interaction is impossible. |
| Human DNAAF9 + IFT74 + IFT81, known association benchmark | DNAAF9 (1177), IFT74 (600), IFT81 (676) | model 4 | 0.369 | 0.403 | 69.8 | 29.4 A | 0.6% | Scores higher than the human DNAAF18-IFT46 comparator, but global inter-chain PAE remains high. The run does not define a confident DNAAF9 interface. |
| Human DNAI1 + IFT46 + IFT74 + IFT81, exploratory | DNAI1 (699), IFT46 (304), IFT74 (600), IFT81 (676) | model 5 | 0.280 | 0.290 | 63.3 | 30.0 A | 1.5% | Low-confidence exploratory arrangement; not prioritized as a direct-interaction hypothesis without stronger independent evidence. |
| Human DNAI2 + IFT46 + IFT74 + IFT81, exploratory | DNAI2 (605), IFT46 (304), IFT74 (600), IFT81 (676) | model 3 | 0.335 | 0.340 | 65.4 | 29.3 A | 1.5% | Low-to-moderate interface score, but high global inter-chain PAE; exploratory only. |

## Interpretation

1. The completed outputs are technically complete: each has five unrelaxed
   models, five ranked PDBs, a ranking file, confidence JSON, PAE JSON/plots,
   and timings.
2. The known DNAAF9-IFT74-IFT81 benchmark ranks above the human
   DNAAF18-IFT46 comparator. This is an encouraging pipeline-level contrast.
3. A high local pLDDT or a folded individual chain does **not** establish the
   confidence of a protein-protein interface. The high cross-chain PAE values
   mean relative chain placement is uncertain in all four top-ranked models.
4. None of the exploratory assemblies should be described as a validated
   direct interaction. Structure inspection and independent experimental or
   literature evidence remain required before prioritization.

## Unfinished and Blocked Scenarios

| Scenario | Status | Reason |
| --- | --- | --- |
| Chlamydomonas DNAAF18/ODA16 + IFT46 positive benchmark | Blocked | Required Chlamydomonas sequence records are not versioned in this repository. No substitute human target set was used. |
| Human DNAAF9 + IFT46 + IFT74 + IFT81 | Incomplete, excluded from analysis | On an AWS `g6e.xlarge`, the host kernel OOM-killed AlphaPulldown after the fifth model began output processing. The L40S GPU had sufficient VRAM; the 32 GiB host RAM was insufficient. No ranking file, ranked PDBs, or PAE outputs were produced. |
| Human DNAAF9 + IFT80 + IFT172 | Deferred | Larger assembly; requires a host with more RAM and a pre-run resource plan. |
| Human DNAI1 + DNAI2 + IFT46 + IFT74 + IFT81 | Deferred | Larger assembly; requires a host with more RAM and a pre-run resource plan. |
| Human DNAI1 + DNAI2 + IFT80 + IFT172 | Deferred | Larger assembly; requires a host with more RAM and a pre-run resource plan. |

## Reproducible Local Analysis

After transferring and verifying a results archive, run:

```bash
PYTHONPATH=src python3 scripts/summarize_milestone2_results.py \
  --results-root /path/to/predictions \
  --output results/milestone2_benchmark/analysis/pilot_summary.json
```

The script refuses incomplete output directories rather than silently treating
partial outputs as results.

## Logical Endpoint for This Pilot

Milestone 2 demonstrates a working, reproducible preparation and execution
path through AlphaPulldown and produces four interpretable, bounded pilot
outputs. The next research decision is not to expand the screen automatically.
It is to review the PAE plots and structures with the supervisor, determine
whether any hypothesis merits evidence-guided construct design or experimental
follow-up, and obtain suitable host-RAM capacity before attempting larger
assemblies.
