# Control Benchmark Design

## Purpose

The control benchmark validates AlphaPulldown behavior before any large biological screen. It is not intended to discover new biology.

## Positive Controls

- DNAAF9 + IFT74
- DNAAF9 + IFT81
- DNAAF2 + DNAAF4
- DNAI1 + DNAI2

## Human Non-Conserved Benchmark Candidate

- Human DNAAF18 + human IFT46

This pair should not be described as a universally proven negative. The Chlamydomonas ODA16/IFT46 interaction is biologically important, but human conservation requires cautious interpretation.

## Future Curated Negatives

The screen definition includes a placeholder for one or two future curated negative controls. They should be added only with explicit biological rationale.

## Success Criteria

- All control pairs appear in `control_sample_sheet.csv`.
- AlphaPulldown syntax validates.
- No heavy-chain construct-review target appears in the first executable control benchmark.
- All metrics and outputs from future benchmark predictions are documented before biological screening.

