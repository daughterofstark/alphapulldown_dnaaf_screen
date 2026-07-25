# Girish-Refined First Run Panel

## Purpose

This document records Girish's final biological decision for the first AlphaPulldown RunPod execution. It supersedes the broader 30-row first-pass evidence panel as the practical first execution plan, while preserving the earlier evidence audit for traceability.

The refined plan is intentionally small: nine initial interaction sets plus explicit future construct-review notes for DNAH5 and DNAH9. It prioritizes biologically meaningful multichain contexts over isolated binaries that would be easier to run but less faithful to the biology.

Machine-readable files:

- `data/processed/screens/girish_refined_first_run_panel.tsv`
- `data/processed/screens/girish_refined_first_run_panel.json`
- `data/processed/alphapulldown/girish_refined_runpod_first_run.tsv`

## Final 9 Interaction Sets

1. **Chlamydomonas DNAAF18/ODA16 - IFT46**
   - Role: positive control.
   - Status: external benchmark requiring reviewed Chlamydomonas sequences.
   - Rationale: direct structural/biochemical evidence from Taschner et al. 2017, including PDB 5MZH and ITC affinity around 200 nM.

2. **Human DNAAF18/ODA16 - IFT46**
   - Role: negative/species-divergence control.
   - Status: immediately executable using verified human targets.
   - Rationale: Wang et al. 2020 did not detect interaction between purified human ODA16 and IFT46.

3. **Human DNAAF9 - IFT74/IFT81 heterodimer**
   - Role: strong candidate.
   - Status: primary multichain/ternary test.
   - Rationale: Issa et al. 2025 supports DNAAF9 association with IFT74/IFT81 by IP-MS/co-IP and ternary SEC context, but not isolated binary binding.

4. **Human DNAAF9 - IFT46/IFT74/IFT81**
   - Role: new candidate.
   - Status: primary multichain test if AlphaPulldown input handling validates.
   - Rationale: tests DNAAF9 against a broader IFT-B context that may be more informative than IFT74/81 alone.

5. **Human DNAAF9 - IFT80/IFT172**
   - Role: new candidate.
   - Status: primary ternary test if AlphaPulldown input handling validates.
   - Rationale: probes a second IFT-B subcomplex context suggested for first RunPod exploration.

6. **Human DNAI1 - IFT46/IFT74/IFT81**
   - Role: new candidate.
   - Status: primary multichain test if AlphaPulldown input handling validates.
   - Rationale: tests a possible ODA intermediate-chain cargo contact in a biologically relevant IFT-B context.

7. **Human DNAI2 - IFT46/IFT74/IFT81**
   - Role: new candidate.
   - Status: primary multichain test if AlphaPulldown input handling validates.
   - Rationale: DNAI2/IC2 is the better-supported ODA transport reporter from prior IFT cargo literature.

8. **Human DNAI1/DNAI2 - IFT46/IFT74/IFT81**
   - Role: new candidate.
   - Status: primary multichain complex if supported.
   - Rationale: tests the intermediate-chain pair in the IFT46/IFT74/IFT81 context rather than reducing the biology to single-chain binaries.

9. **Human DNAI1/DNAI2 - IFT80/IFT172**
   - Role: new candidate.
   - Status: primary multichain complex if supported.
   - Rationale: tests the DNAI1/DNAI2 pair against the IFT80/IFT172 context.

## Removed or Deprioritized Tests

### Isolated DNAAF9-IFT74 and DNAAF9-IFT81

These are no longer primary first-run tests. Girish's key refinement is that IFT74 and IFT81 form an obligate heterodimer, so DNAAF9 should be tested against the IFT74/IFT81 context. Isolated DNAAF9-IFT74 and DNAAF9-IFT81 rows may appear only as fallback diagnostics if multichain input handling fails; they must not be interpreted as the primary biological test.

### IFT74-IFT81 Alone

IFT74-IFT81 is already known to work as a direct IFT-B interaction and does not answer the first RunPod biological question. It remains valuable as a general calibration control, but Girish's refined first run does not spend compute on rerunning this known interaction alone.

### DNAAF19/CCDC103-IFT Negative Controls

DNAAF19/CCDC103 remains a good future negative-control rationale because it is an axonemal dynein-arm attachment factor with no reported IFT interaction. It is not part of the first executable RunPod panel. Human DNAAF18/ODA16-IFT46 is the practical first negative/species-divergence control because there is direct in-vitro non-interaction evidence for the human pair.

## DNAH5 and DNAH9 Deferral

DNAH5 and DNAH9 remain future construct-review/truncation work only. Full-length models are deferred because the proteins are very large, the evidence audit found no direct DNAH-IFT interaction, and a biologically meaningful run would require literature- or structure-guided tail/domain construct design. The refined panel records these as `future_construct_review`, not as executable RunPod jobs.

## Multichain Input Handling

The refined biological plan depends on multichain contexts such as:

- `DNAAF9 + IFT74 + IFT81`
- `DNAAF9 + IFT46 + IFT74 + IFT81`
- `DNAI1 + DNAI2 + IFT46 + IFT74 + IFT81`

The RunPod TSV therefore separates:

- primary intended multichain jobs
- the external Chlamydomonas benchmark requiring additional sequences
- the immediately executable binary human DNAAF18-IFT46 control
- fallback-only decompositions

Fallback rows are not equivalent to the primary biological hypotheses. They exist only to preserve a troubleshooting path if the deployed AlphaPulldown/Snakemake run cannot validate multichain input syntax on the target system.

## Execution Guidance

Run only the rows marked `include_by_default=true` in `data/processed/alphapulldown/girish_refined_runpod_first_run.tsv` after the remote environment validates. Start with the human DNAAF18-IFT46 negative/species-divergence control and a dry run of the multichain jobs. Do not run fallback decompositions unless the multichain jobs fail validation or Girish explicitly requests a reduced diagnostic set.
