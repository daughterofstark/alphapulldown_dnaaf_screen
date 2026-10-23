# Project Overview

## Question

Motile cilia require axonemal dynein arms, which are assembled in the cytoplasm
and transported into cilia. This project tests whether AlphaPulldown and
AlphaFold2-Multimer can generate useful structural hypotheses for interactions
between dynein axonemal assembly factors (DNAAFs), dynein-arm proteins, and
intraflagellar transport (IFT) proteins.

The work is hypothesis-generating. A predicted complex is not evidence that two
proteins bind directly in cells.

## What Was Built

- A versioned human target set with validated accessions, deterministic FASTA
  files, and checksums.
- A separate Milestone 2 benchmark that cannot silently use the larger target
  universe.
- A Docker-based AlphaPulldown 2.5.0 / AlphaFold2-Multimer workflow validated
  on AWS.
- Reusable MMseqs2-derived features for the nine human proteins required by the
  benchmark.
- A parser that extracts scores and PAE summaries only from complete prediction
  directories.

## Current Status

Four benchmark predictions were completed and archived. The known-association
benchmark, DNAAF9 + IFT74 + IFT81, ranked higher than the human DNAAF18 + IFT46
species-divergence comparator. However, all four completed models had high
global inter-chain predicted aligned error (PAE), so none establishes a
confident direct interface.

The completed work is sufficient to demonstrate a reproducible pilot workflow
and to support a supervised review of the ranked structures and PAE plots. It
does not justify expansion to a large interaction screen without a clearer
resource plan and biological review.
