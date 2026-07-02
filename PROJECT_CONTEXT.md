# Project Context

## Scientific Motivation

This project will develop a reproducible computational structural biology pipeline for screening direct protein-protein interactions among mammalian Dynein Axonemal Assembly Factors (DNAAFs), Outer Dynein Arm (ODA) proteins, and Intraflagellar Transport (IFT) proteins. The biological motivation is to understand how cytoplasmic dynein arm pre-assembly is connected to IFT-mediated delivery into motile cilia.

Axonemal dynein arms power ciliary beating. These multi-megadalton complexes are assembled in the cytoplasm rather than inside cilia, then transported into the axoneme by IFT trains. Mutations affecting ODA structural proteins or DNAAFs cause Primary Ciliary Dyskinesia (PCD), with clinical manifestations including chronic respiratory disease, infertility, and laterality defects. Despite extensive genetics and cell biology, most direct DNAAF-ODA and DNAAF-IFT interfaces remain unknown.

The long-term goal is to produce a ranked, transparent, experimentally actionable map of candidate direct interactions. Computational predictions are hypotheses, not conclusions. Every output must preserve provenance, uncertainty, and enough metadata to support future wet-lab validation and publication.

## Biological Questions

1. Which mammalian DNAAFs make direct physical contacts with ODA proteins during cytoplasmic pre-assembly?
2. Which DNAAFs contact IFT-B or IFT-A proteins during ODA loading and ciliary transport?
3. Can known interactions such as DNAAF9-IFT74, DNAAF9-IFT81, DNAAF2-DNAAF4, and DNAI1-DNAI2 be reproduced with high-confidence AlphaFold-Multimer or AlphaFold3 predictions?
4. Can expected negative controls, including human DNAAF18-IFT46, be correctly deprioritized?
5. Are there uncharacterized transport interfaces involving DNAAF16, DNAAF17, DNAAF18, DNAAF19, or DNAAF8?
6. Do predicted interfaces overlap PCD-associated variants, conserved residues, or known functional domains?

## Current Literature Context

The project is grounded in several converging areas of literature:

- DNAAF nomenclature and biology: the DNAAF1-DNAAF19 framework, including legacy aliases such as KTU, DYX1C1, HEATR2, LRRC6, SPAG1, PIH1D3, ODA16, and CCDC103.
- Dynein pre-assembly: cytoplasmic folding and assembly involving HSP70, HSP90, R2TP-like co-chaperone complexes, DynAP/kl-granule/R2HAD compartments, and transient DNAAF scaffolding.
- ODA biology: mammalian ODA heavy chains, intermediate chains, light chains, light-intermediate chains, and ODAD docking-complex proteins.
- IFT biology: IFT-B as the main anterograde train module, IFT-A as a retrograde and membrane-cargo module, and IFT-B core subunits as likely ODA loading contacts.
- AlphaFold-based PPI screening: AlphaFold-Multimer, AlphaPulldown, AlphaFastPPi, AlphaFold3 cross-validation, interface-specific confidence metrics, and known limitations for transient or disordered interactions.

## Known Interactions and Controls

Positive controls should be included early and rerun whenever scoring or software versions change:

- DNAAF9-Shulin with IFT74.
- DNAAF9-Shulin with IFT81.
- DNAAF2 with DNAAF4.
- DNAI1 with DNAI2.
- DNAAF12 with IFT88, marked as species/context sensitive because the strongest evidence is non-human.
- DNAAF18/ODA16 with IFT46 in Chlamydomonas, used as an orthologous positive but not as a human positive.

Negative controls should test whether the pipeline avoids biologically implausible positives:

- Human DNAAF18 with human IFT46.
- DNAAF7 with IFT43.
- Randomized or length-matched unrelated cytoplasmic proteins.
- Same-species proteins with incompatible localization or no plausible assembly-stage overlap.

## Unknown Interaction Space

The core planned screen is 19 DNAAFs against approximately 39 ODA and IFT partners, yielding roughly 741 binary predictions. Priority discovery areas include:

- DNAAF17 contacts with IFT-B subunits.
- DNAAF16 contacts with DNAI1, DNAI2, or IFT-B proteins.
- DNAAF19 contacts with dynein heavy-chain regions or R2TP-related machinery.
- DNAAF8 interactions, because it is poorly characterized and likely enriched for disordered regions.
- Additional DNAAF9 contacts beyond IFT74 and IFT81.
- DNAAF3 substrate-recognition interfaces on ODA heavy-chain regions.

## Expected Computational Workflow

The final automated workflow should execute the following stages:

1. Protein target manifest definition.
2. UniProt retrieval and accession validation.
3. Canonical sequence and isoform validation.
4. FASTA generation.
5. AlphaPulldown feature generation.
6. MSA generation.
7. AlphaFold-Multimer prediction.
8. Model ranking and confidence extraction.
9. PAE and interface confidence analysis.
10. Interface extraction and structural annotation.
11. Conservation, disease-variant, and literature annotation.
12. Visualization.
13. Ranking and triage.
14. Reproducible report generation.
15. Export of publication-ready tables and figures.

No intermediate files should be manually edited. Derived files should be reproducible from manifests, configuration files, scripts, and pinned software environments.

## Scientific Assumptions

- Canonical human UniProt sequences are the primary reference unless a biologically justified isoform is documented.
- Binary predictions are useful for hypothesis generation even though many biological assemblies are higher-order, transient, regulated, or chaperone-dependent.
- AlphaFold confidence metrics are informative but insufficient alone; ipTM must be interpreted with PAE, pLDDT, interface geometry, conservation, and biological context.
- DNAAF intrinsically disordered regions may suppress global metrics despite meaningful structured-domain interactions.
- Species-specific interactions are common enough that human, mouse, zebrafish, and algal orthology must not be conflated without evidence.

## Expected Outputs

- Validated protein manifests with accessions, aliases, isoforms, domains, lengths, and references.
- FASTA files generated from source manifests.
- AlphaPulldown-compatible inputs.
- Per-pair prediction directories with full provenance.
- Summary score tables with ipTM, pTM, pLDDT, PAE-derived metrics, interface metrics, and run metadata.
- PAE heatmaps and structural interface visualizations.
- Ranked candidate interaction lists with confidence tiers.
- Negative-control and positive-control benchmark reports.
- Publication-ready figures, tables, and reproducible analysis notebooks.

## Limitations

- AlphaFold predictions do not prove binding.
- Flexible, transient, post-translationally regulated, membrane-associated, or condensate-mediated interactions may be missed.
- Large ODA heavy chains may require domain-level modeling for tractability and interpretability.
- AlphaPulldown/AlphaFold outputs can be sensitive to MSA depth, template availability, random seeds, model version, and recycling parameters.
- Interface metrics such as buried surface area and hydrogen bonds can be misleading if the global complex pose is uncertain.

## Future Extensions

- AlphaFold3 cross-validation for top candidates.
- Orthologous screens in mouse, zebrafish, Chlamydomonas, Tetrahymena, and Paramecium.
- Domain-level screens for ODA heavy chains and long/disordered DNAAFs.
- Integration with PISA, ConSurf, AlphaMissense, ClinVar, gnomAD, and PCD variant databases.
- Expansion to inner dynein arm proteins, radial-spoke proteins, N-DRC proteins, central-pair proteins, and ciliary cargo adaptors.
- Export to Cytoscape, NDEx, and manuscript-ready network figures.

