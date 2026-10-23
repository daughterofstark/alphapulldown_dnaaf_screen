# Limitations and Next Steps

## Limits of This Pilot

- AlphaFold-Multimer predictions are structural hypotheses, not binding assays.
- The completed scenarios have high global inter-chain PAE, limiting confidence
  in the placement of protein chains relative to one another.
- The positive Chlamydomonas DNAAF18/ODA16 + IFT46 benchmark was not run because
  the required algal sequence records were not versioned in this project.
- A four-protein DNAAF9 + IFT46 + IFT74 + IFT81 run was stopped by host-RAM
  exhaustion on a 32 GiB AWS machine. It produced no complete result set and
  is excluded from the analysis.
- Larger assemblies were deferred rather than treated as failed biological
  predictions.

## Recommended Next Step

Review the four completed structures and PAE plots with the biological context
in mind. Only then decide whether any condition warrants a targeted rerun,
evidence-guided construct design, or experimental follow-up.

Any expansion should first define: an approved target set, a host-RAM and GPU
resource plan, a repeat/seed policy, and criteria for combining structural
confidence with independent evidence.
