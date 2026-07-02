# Data Specification

## Scope

This project requires curated metadata for DNAAF, ODA, and IFT proteins before any sequence or prediction workflow is implemented. Canonical sequences must not be typed into this repository by hand. They must be retrieved from authoritative databases and validated by scripts.

## Required Dataset Classes

### Target Protein Manifest

Authoritative source: `data/manifest/targets.yaml`.

Each record must include:

- `record_id`: stable project identifier, for example `HUMAN_DNAAF9`.
- `gene`: approved gene symbol.
- `aliases`: legacy names and common aliases.
- `protein_group`: `DNAAF`, `ODA`, `ODAD`, `IFT_A`, `IFT_B`, `CONTROL`, or future groups.
- `species`: scientific name.
- `taxon_id`: NCBI taxonomy identifier.
- `uniprot_accession`: reviewed UniProt accession when available.
- `uniprot_entry_name`: UniProt entry mnemonic.
- `canonical_sequence`: generated field, never manually edited.
- `isoform`: canonical or specific isoform identifier.
- `sequence_length`: generated field validated against UniProt.
- `domains`: curated domain annotations with source.
- `subcellular_context`: cytoplasm, DynAP, ODA, IFT train, axoneme, basal body, or unknown.
- `biological_role`: concise role in dynein assembly or transport.
- `known_partners`: known direct or indirect partners with evidence type.
- `references`: source identifiers or citation keys.
- `notes`: curator notes.
- `validation_status`: pending, validated, deprecated, or excluded.

### Pair Manifest

Generated source: `data/processed/pairs/*.tsv`.

Each pair must include:

- `pair_id`.
- `bait_record_id`.
- `prey_record_id`.
- `screen_name`.
- `control_type`: positive, negative, benchmark, discovery, or excluded.
- `species_policy`: same-species, orthologous, or mixed-species.
- `priority`.
- `rationale`.

### Raw UniProt Records

Storage: `data/raw/uniprot/`.

Required formats:

- Raw JSON or XML from UniProt.
- Raw FASTA only as downloaded evidence, not as final generated FASTA.
- Retrieval metadata containing query URL, date, database release, and checksum.

### Generated FASTA

Storage: `data/processed/fasta/`.

Rules:

- FASTA headers must use stable project identifiers.
- Header metadata should include gene, species, UniProt accession, isoform, and sequence checksum.
- FASTA files must be generated from validated records only.

## Initial Target Universe

### DNAAF Targets

| Record ID | Gene | Aliases | Domains / Notes | Species | UniProt accession | Sequence policy |
| --- | --- | --- | --- | --- | --- | --- |
| HUMAN_DNAAF1 | DNAAF1 | LRRC50, ODA7 | LRR repeats; dynein heavy-chain stability | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF2 | DNAAF2 | KTU, PF13 | PIH1 + CS; R2TP-like co-chaperone | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF3 | DNAAF3 | PF22 | methyltransferase-like fold | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF4 | DNAAF4 | DYX1C1, PF23 | TPR + CS; HSP90 client | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF5 | DNAAF5 | HEATR2 | HEAT repeats | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF6 | DNAAF6 | PIH1D3 | PIH1 + CS; X-linked PCD | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF7 | DNAAF7 | ZMYND10 | MYND zinc finger | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF8 | DNAAF8 | C16orf71 | disordered; DynAP-associated | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF9 | DNAAF9 | SHULIN, C20orf194 | ODA packaging; IFT74/IFT81 contacts | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF10 | DNAAF10 | WDR92 | WD40 repeats; R2TP-prefoldin bridge | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF11 | DNAAF11 | LRRC6, MOT47 | LRR + p23 crystallin-like domain | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF12 | DNAAF12 | LRRC56, ODA8 | LRR repeats; late ODA transport | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF13 | DNAAF13 | SPAG1 | TPR + RPAP3_C; R2SP | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF14 | DNAAF14 | PIH1D1, MOT48 | canonical R2TP PIH subunit | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF15 | DNAAF15 | PIH1D2 | PIH1 + CS; R2SP-associated | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF16 | DNAAF16 | CFAP298, C21orf59 | ubiquitin-like and bilobed core | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF17 | DNAAF17 | CFAP300, C11orf70 | IFT-linked ODA distribution | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF18 | DNAAF18 | DAW1, ODA16 | beta-propeller; ODA-IFT adaptor context | Homo sapiens | To be resolved by script | Canonical reviewed |
| HUMAN_DNAAF19 | DNAAF19 | CCDC103 | RPAP3_C-like; microtubule binding | Homo sapiens | To be resolved by script | Canonical reviewed |

### ODA and ODAD Targets

Initial ODA/ODAD genes:

- Heavy chains: DNAH5, DNAH9, DNAH11, DNAH8, DNAH17.
- Intermediate chains: DNAI1, DNAI2.
- Light chains: DYNLL1, DYNLL2, DYNLT1, DYNLRB1, DYNLRB2, DNAL1, DNAL4.
- Light-intermediate chain: DNALI1.
- Docking complex: ODAD1/CCDC114, ODAD2/ARMC4, ODAD3/CCDC151, ODAD4/TTC25.

For very large heavy chains, the manifest must support both full-length canonical records and domain/region records. Domain/region records must include residue boundaries and the reason for truncation.

### IFT Targets

Initial IFT-A genes:

- IFT144, IFT140, IFT139, IFT122, IFT121, IFT43.

Initial IFT-B genes:

- IFT172, IFT88, IFT81, IFT80, IFT74, IFT57, IFT56, IFT54, IFT52, IFT46, IFT38/CLUAP1, IFT27, IFT25, IFT22, IFT20.

Before implementation, confirm whether the intended IFT-B set has 15 or 16 human records and resolve duplicate listing of IFT57 in the survey-derived draft. The manifest validator should reject duplicate record identifiers.

## Validation Rules

- Gene symbol must match an approved HGNC symbol or documented alias.
- UniProt accession must resolve to the intended species.
- Reviewed Swiss-Prot records are preferred; use TrEMBL only with explicit rationale.
- Canonical sequence length must match UniProt.
- Isoform-specific usage requires documented biological rationale.
- Sequence checksums must be generated and stored.
- No sequence may be edited manually.
- Records with ambiguous accessions must fail validation.
- Duplicate gene/species/isoform combinations must fail validation.
- Large-protein truncations must include residue boundaries and preserve mapping to canonical coordinates.

## References and Evidence

Each record should eventually link to citation keys in `docs/references/` or a future BibTeX file. Evidence categories should distinguish:

- Direct biochemical interaction.
- Proximity or co-localization.
- Genetic interaction.
- Orthologous evidence.
- Structural prediction.
- Curator inference.

