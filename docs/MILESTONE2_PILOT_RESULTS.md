# Milestone 2 Pilot Results

## Completed Output Sets

The recovered AWS result archive was SHA-256 verified before summary. It
contains complete native AlphaPulldown outputs for four scenarios: five ranked
PDBs, five unrelaxed PDBs, ranking data, confidence and PAE JSON files, PAE
plots, and timing records per scenario.

| Scenario | Best ipTM | Ranking confidence | Mean pLDDT | Mean inter-chain PAE | Summary |
| --- | ---: | ---: | ---: | ---: | --- |
| Human DNAAF18 + IFT46 | 0.168 | 0.254 | 72.4 | 29.1 A | Low interface confidence; useful comparator. |
| Human DNAAF9 + IFT74 + IFT81 | 0.369 | 0.403 | 69.8 | 29.4 A | Higher than comparator, but chain placement remains uncertain. |
| Human DNAI1 + IFT46 + IFT74 + IFT81 | 0.280 | 0.290 | 63.3 | 30.0 A | Exploratory, low-confidence arrangement. |
| Human DNAI2 + IFT46 + IFT74 + IFT81 | 0.335 | 0.340 | 65.4 | 29.3 A | Exploratory; insufficient evidence for direct binding. |

`ranked_0.pdb` is the top-ranked model reported by AlphaFold-Multimer. Mean
inter-chain PAE is a coarse summary of the cross-chain portion of the PAE
matrix; it cannot replace inspection of PAE plots and structures.

## Interpretation

The DNAAF9 + IFT74 + IFT81 benchmark scored above the DNAAF18 + IFT46
comparator, demonstrating that the workflow can recover a useful difference
between two biologically distinct conditions. At the same time, the high
inter-chain PAE values in all four models mean that relative chain positions
are not well defined.

Accordingly, the models should be presented as pilot structural hypotheses, not
as validated protein-protein interfaces. The exploratory complexes should not
be prioritised for experimental work without structure review and independent
biological evidence.

## Reproducing the Summary

The raw archive is distributed separately from the repository. After extraction:

```bash
PYTHONPATH=src python3 scripts/summarize_milestone2_results.py \
  --results-root /path/to/predictions \
  --output pilot_summary.json
```

The parser rejects incomplete prediction directories rather than silently
including partial output.
