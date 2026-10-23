# Methods

## Inputs

Protein records are versioned in `data/processed/targets/validated_targets.json`.
Canonical FASTA files are generated deterministically from those records. The
Milestone 2 benchmark uses its own scenario manifest, FASTA manifest, and input
sheet under `data/processed/benchmarks/`; it does not read the full-screen
FASTA manifest.

## Feature Generation

Individual AlphaPulldown features were generated once per human benchmark
protein using the MMseqs2 option of AlphaPulldown 2.5.0. The resulting
compressed `.pkl.xz` files were reused across predictions. This avoids
recomputing sequence features for every complex.

## Structure Prediction

Predictions used AlphaPulldown 2.5.0 with the AlphaFold2-Multimer v3 backend.
For each completed scenario, five multimer parameter models were run once. The
workflow produced ranked and unrelaxed PDB files, ranking information,
per-residue confidence, PAE files and plots, timings, and result pickles.

The runtime was a Docker image built from pinned dependencies and tested for
AlphaPulldown command availability, JAX, and GPU visibility before biological
runs. The project Python package and the AlphaFold runtime use separate Python
environments.

## Interpretation

The primary model-level measures are:

- **ipTM:** confidence in the relative placement of chains; higher is better.
- **pTM:** global fold/complex confidence.
- **pLDDT:** local structural confidence for individual residues.
- **PAE:** expected positional error between residues; low inter-chain PAE is
  needed before a proposed interface is taken seriously.

Scores were interpreted together with chain placement, PAE plots, biological
context, and published evidence. No fixed score threshold is treated as proof
of a physical interaction.
