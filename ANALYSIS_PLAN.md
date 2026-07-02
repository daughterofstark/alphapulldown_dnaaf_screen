# Analysis Plan

## Confidence Metrics

### ipTM

ipTM is the primary AlphaFold-Multimer interaction-confidence metric. Proposed initial tiers:

- High confidence: `ipTM >= 0.80`.
- Candidate/grey zone: `0.60 <= ipTM < 0.80`.
- Low confidence: `ipTM < 0.60`.

These thresholds are starting points, not immutable truth. They must be calibrated using positive and negative controls.

### pTM

pTM describes global complex confidence. It is useful as a sanity check but can be less informative for binary interactions involving one small partner and one large or flexible protein. pTM should not override poor inter-chain PAE or implausible interface geometry.

### Ranking Confidence

AlphaFold ranking confidence should be parsed exactly as produced by the model version. The report should preserve:

- Model rank.
- Model name.
- ipTM.
- pTM.
- Combined ranking confidence.
- Random seed when available.
- Recycling and model preset.

### pLDDT

pLDDT should be summarized globally and at interface residues. Interface residues with low pLDDT weaken confidence even when ipTM appears strong.

## PAE Analysis

Predicted Aligned Error is central for distinguishing confident chain placement from coincidental docking. Planned outputs:

- Full PAE heatmap per top-ranked model.
- Inter-chain PAE submatrix summary.
- Minimum, median, and percentile inter-chain PAE for interface-residue pairs.
- Low-PAE contact block detection.

Candidate interactions should require low inter-chain PAE in the interface region, not merely favorable global ranking.

## Interface Confidence

An interaction should be promoted only when multiple signals agree:

- ipTM or corrected interface metric supports the pair.
- Inter-chain PAE is low at the predicted interface.
- Interface residues have acceptable pLDDT.
- Buried surface area is plausible.
- The interface includes specific contacts rather than a small hydrophobic touch.
- The biological context supports co-localization and assembly-stage compatibility.

## Buried Surface Area

Buried surface area (BSA) should be computed for confidence-filtered models. Preliminary interpretation:

- `BSA < 300 A^2`: likely weak or incidental for most stable complexes.
- `300-500 A^2`: possible transient/small-domain interaction.
- `500-800 A^2`: plausible interaction requiring supporting evidence.
- `> 800 A^2`: stronger structural support, especially with low PAE.

Thresholds should be adjusted by protein size, domain size, and known transient-adaptor biology.

## Interface Residues

For every promoted candidate:

- Extract residues within a configurable distance cutoff, initially 4-5 A.
- Map residues to canonical coordinates.
- Annotate residue pLDDT, domain, conservation, known variants, and post-translational modifications when available.
- Export chain-specific interface residue tables.

## Hydrogen Bonds and Salt Bridges

Hydrogen bonds and salt bridges should be computed with a documented tool and fixed geometry criteria. These contacts should support interpretation but not serve as standalone proof. Reports should distinguish predicted contacts from experimentally observed contacts.

## Replicate and Robustness Criteria

Future analyses should evaluate:

- Agreement across the five AlphaFold-Multimer models.
- Agreement across seeds.
- Agreement across full-length and domain-level constructs.
- Agreement across AF2-Multimer and AF3 for top candidates.
- Sensitivity to MSA depth and template settings.

## Corrected Metrics for Disordered Proteins

DNAAFs often contain intrinsically disordered regions. Global metrics may penalize true structured-domain interfaces. The pipeline should evaluate or leave extension points for:

- actifpTM.
- ipSAE.
- Interface-only PAE summaries.
- Disorder-aware domain truncation.

## Integration With PISA

PISA or PDBePISA should be considered for:

- BSA.
- Interface energetics.
- Hydrogen bonds.
- Salt bridges.
- Complexation significance.

Because predicted structures are not crystallographic asymmetric units, PISA outputs must be interpreted cautiously and reported as computational descriptors rather than experimental thermodynamics.

## Integration With ConSurf

ConSurf can help prioritize conserved interfaces. Planned workflow:

- Build ortholog sets from ciliated eukaryotes.
- Compute residue conservation.
- Map conservation to predicted interface residues.
- Promote candidates where low-PAE interfaces are also conserved.

Species-specific biology must be preserved. A non-conserved human interface may still be relevant if the function evolved in mammals.

## AlphaFold3 Cross-Validation

AlphaFold3 should be used for top candidates when feasible:

- Re-predict positive controls.
- Re-predict top high-confidence candidates.
- Re-predict grey-zone candidates with strong biological rationale.
- Compare interface geometry, not just confidence score.

AF3 results should be labeled as a separate backend, with version, access method, and model settings documented.

## ChimeraX Visualization

ChimeraX should be used for reproducible structural scenes:

- Interface close-ups.
- Surface representations colored by chain and confidence.
- Interface residues highlighted.
- PAE/contact confidence included in captions.

ChimeraX command scripts should be version controlled so figures can be regenerated.

## Prioritization Score

A future composite score may combine:

- ipTM or corrected interface metric.
- Inter-chain PAE.
- Interface pLDDT.
- BSA.
- Contact specificity.
- Model replicate consistency.
- Conservation.
- Disease-variant overlap.
- Literature support.
- Biological plausibility.

Composite scores must remain transparent: reports should show component values, not only a final rank.

