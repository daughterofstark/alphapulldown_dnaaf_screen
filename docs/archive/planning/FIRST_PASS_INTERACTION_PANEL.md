# First-Pass Interaction Panel

## Purpose

This panel converts the evidence audit in `docs/validation/EVIDENCE_AUDIT_ODA_IFT_INTERACTIONS.md` into a small, biologically justified AlphaPulldown test set. It is not the full DNAAF x ODA x IFT screen. Its purpose is to calibrate the remote AlphaPulldown workflow against known positives, known negatives or divergence tests, and a short list of high-value mechanistic hypotheses before any large-scale screen is attempted.

The panel is deliberately conservative. It preserves the audit's distinction between direct binding, physical association, functional association, and lack of reported interaction. AlphaPulldown predictions generated from this panel should be treated as hypotheses, not experimental evidence.

Machine-readable files:

- `data/processed/screens/first_pass_interaction_panel.tsv`
- `data/processed/screens/first_pass_interaction_panel.json`

## Evidence Classes

The panel uses the following evidence levels:

- `direct_structural`: crystal or structural evidence supports a direct interface.
- `direct_biochemical`: biochemical mapping supports a direct interaction.
- `physical_association`: co-IP, IP-MS, co-elution, or related evidence supports association but not necessarily isolated binary binding.
- `functional_association`: genetic, transport, or localization evidence supports pathway coupling without physical directness.
- `inference`: biologically motivated modelling constraint or hypothesis without direct interaction evidence.
- `negative_evidence`: an interaction was specifically tested and not detected.
- `no_reported_interaction`: no IFT interaction has been reported despite known biology of the protein.

Directness is recorded separately because evidence can be real without proving a binary interface. For example, DNAAF9 association with IFT74/IFT81 is supported, but isolated two-protein binding is not established.

## Species-Specificity

The audit identifies species divergence as a central design issue. Chlamydomonas ODA16-IFT46 is direct and structurally mapped, whereas purified human ODA16/DAW1-DNAAF18 and human IFT46 fail to interact in vitro. The panel therefore separates the algal interaction as an external positive benchmark from the human pair as a species-divergence test.

Only verified human targets are included as executable first-run rows. Non-human rows are retained only as external benchmarks or documentation anchors unless their sequences are explicitly reviewed and added later.

## Category Rationale

### Positive Controls

Chlamydomonas ODA16/DNAAF18-IFT46 is the strongest positive-control evidence in the audit: Taschner et al. 2017 report a crystal structure, PDB 5MZH, and ITC affinity around 200 nM for the algal interaction. It is included as an external benchmark because the current verified target universe is human-only. No Chlamydomonas accession is invented in the machine-readable panel.

Human IFT74-IFT81, IFT46-IFT52, and IFT88-IFT52 are included as internal IFT-B positive controls. These are better suited to immediate execution because all human proteins are present in the verified target universe. Fragment or domain constructs may be preferable for publication-grade modelling, but the rows are marked executable for first-pass calibration.

The optional IFT81/IFT74-tubulin control is omitted because tubulin is not part of the verified target universe. It should not be added without explicit target review.

### Strong Candidates

DNAAF9/Shulin-IFT74 and DNAAF9/Shulin-IFT81 are high-value candidates based on Issa et al. 2025: IP-MS, co-IP validation, and ternary SEC support association between DNAAF9/Shulin, ODAs, and human IFT74/IFT81. The audit is explicit that this is not proof of isolated binary binding. Therefore these rows use `physical_association` and `association_not_binary`, not `direct`.

The DNAAF9-IFT74/IFT81 heterodimer row is represented as a complex-level hypothesis. This better reflects the biology because IFT74/IFT81 form an obligate IFT-B module, and the supporting reconstitution evidence is not a clean two-protein DNAAF9-IFT experiment.

### Species-Divergence Test

Human ODA16/DAW1-DNAAF18-IFT46 is not a positive control. Wang et al. 2020 report that purified human ODA16 and human IFT46 failed to interact by SEC and pulldown. The row is therefore labelled `species_divergence_test`, with `negative_evidence` and `not_detected`.

### Exploratory Candidates

LRRC56/DNAAF12-IFT88 is supported by co-IP and IFT-cargo association, not direct binary binding. It is included to test whether AlphaPulldown nominates a plausible interface, but a negative prediction would not refute an indirect in-vivo association.

TTC25/ODAD4-IFT88, IFT52, IFT57, and IFT140 are included as association-level docking/transport hypotheses based on Xu et al. 2015. The audit describes this evidence as co-IP/association, not direct binding.

DNAI1 and DNAI2 with IFT74, IFT81, and IFT46 are exploratory ODA-cargo contact hypotheses. The audit supports ODA transport by IFT, especially for DNAI2/IC2 in Chlamydomonas, but does not identify direct DNAI-IFT binary interactions. These rows are therefore `functional_association` and `functional_only`.

### Negative Controls

CCDC103/DNAAF19 is an axonemal dynein-arm attachment factor with no reported IFT interaction. It is therefore used as the main negative-control protein against IFT46, IFT74, IFT81, and IFT88. These rows are labelled `no_reported_interaction` and `none_reported`, never candidate positives.

CCDC151/ODAD3 is present in the verified human target universe, so one ODAD3-IFT row is included. The audit describes CCDC151-IFT evidence as functional/indirect rather than a physical complex; the row is a negative control for direct binary IFT binding, not a claim that ODAD3 lacks ciliary relevance.

### Defer / Construct Review

DNAH5 and DNAH9 full-length IFT models are deferred. Their canonical human proteins are about 4,600 and 4,500 residues respectively, and the audit reports no direct DNAH-IFT interaction. Full-length co-folding would be computationally expensive and scientifically under-specified. The panel therefore includes representative DNAH5/DNAH9-IFT rows only as `defer_construct_review`, with `construct_review_required` and `include_in_first_run=false`.

Future heavy-chain modelling should use literature- or structure-guided tail/domain constructs, reviewed before execution.

## Omitted or External Items

- Chlamydomonas ODA16-IFT46 is retained as an external benchmark, not an executable human target row.
- IFT74/IFT81-tubulin is omitted because tubulin is outside the verified target universe.
- No non-human UniProt accessions are invented.
- No DNAH5/DNAH9 full-length rows are included in the executable first run.

## Execution Policy

Rows with `include_in_first_run=true` are eligible for the first remote AlphaPulldown run after environment validation and dry runs. Rows with `include_in_first_run=false` are documentation or construct-review rows only.

Before execution, convert eligible rows to AlphaPulldown input syntax using the existing remote preparation layer. Do not modify the verified target universe to force optional or external controls into the run.
