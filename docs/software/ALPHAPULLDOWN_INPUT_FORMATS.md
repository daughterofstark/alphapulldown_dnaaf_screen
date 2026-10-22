# AlphaPulldown Input Formats

## Accession Pair Syntax

For explicit pair jobs, this project writes one AlphaPulldown job per line using UniProt accession syntax:

```text
Q5TEA3+Q96LB3
```

This example represents DNAAF9 plus IFT74.

## Generated Files

### `control_sample_sheet.csv`

Explicit benchmark pairs. Each line is a pair job in `ACCESSION+ACCESSION` form.

### `transport_baits.txt`

One bait accession per line:

```text
Q5TEA3
Q8N136
```

### `ift_b_preys.txt`

One verified IFT-B prey accession per line. IFT70A (`TTC30A`) and IFT70B (`TTC30B`) are retained separately.

### `full_screen_pairs.tsv`

A future screen definition table. It is not a direct AlphaPulldown sample sheet and should not be executed blindly. Rows include `executable` and `requires_construct_review` fields.

## FASTA-Path Mode

The CPU pipeline writes canonical FASTA files under `data/processed/fasta/`. Future configuration may use FASTA paths instead of UniProt accessions if the selected AlphaPulldown workflow requires local files.

