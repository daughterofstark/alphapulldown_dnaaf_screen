# EVIDENCE_AUDIT_ODA_IFT_INTERACTIONS.md

*An independent verification of the proposed first-pass AlphaPulldown interaction list. Scope: confirm or refute each claim against primary literature; verify exact citations/DOIs/PMIDs; and separate direct binding from physical association, functional dependence, and inference. Reviews are used only as pointers back to primary papers and are labelled as such.*

---

## 1. Executive verdict

**The proposed first-pass list is scientifically sound and well-constructed. Its category assignments hold up under audit, with three refinements the reviewer should apply before committing compute.**

1. **The strongest single positive control is correct, but the species matters.** *Chlamydomonas* ODA16–IFT46 is a genuinely direct, structurally-defined interaction (crystal + ITC, Kd = 200 nM, mapped interface). It is the best positive benchmark in this set. But the **human** ODA16–IFT46 pairing is a *demonstrated in-vitro negative* (Wang et al. 2020), so it must be modelled as a species-divergence test, never assumed conserved.

2. **The most valuable novel hypothesis (DNAAF9–IFT74/IFT81) is real evidence, but it is NOT proven binary binding.** The support is IP-MS + co-IP in human airway cells plus a *ternary* SEC reconstitution (ODA–Shulin + IFT74/81). No experiment isolates a DNAAF9–IFT74 or DNAAF9–IFT81 two-protein complex. This is a strong candidate, but the audit downgrades the directness claim from "likely direct" to "physical association whose directness is unresolved."

3. **Two claims must be labelled clearly as non-direct:** LRRC56–IFT88 rests on a *single co-IP of overexpressed tagged proteins* in HEK293 (not direct binding), and TTC25–IFT rests on a *co-IP described by its own authors as "association."* Both are legitimate to test; neither is an established binary complex.

The negative controls (CCDC103/DNAAF19) and internal positive controls (IFT74–IFT81, IFT-B core) are correctly chosen. No claim in the set was found to be outright false; the corrections are about **directness and species**, which is exactly where an AlphaPulldown screen is most easily misled.

**Key citation corrections vs. the prior draft:**
- Wang et al. 2020 (human ODA16) is **Protein Science 29(6):1502–1510, DOI 10.1002/pro.3864** — the "Phil Trans R Soc B 20190158" alternative floated earlier is **wrong** and should be removed.
- Issa et al. 2025 is now **formally published** in *Nat Struct Mol Biol* 32:2454–2464, DOI 10.1038/s41594-025-01680-9, PMID 41023246 (no longer preprint-only).

---

## 2. Claim-by-claim audit table

| # | Claim | Verdict | Best supporting paper | Exact evidence | Species | Directness | Confidence | Implication for AlphaPulldown |
|---|-------|---------|----------------------|----------------|---------|-----------|-----------|------------------------------|
| 1 | DNAAF9/Shulin–**IFT74** supported by human airway IP-MS/co-IP and/or reconstitution | **True** (as an *association*; not proven binary) | Issa et al. 2025, NSMB | Fig 2a,b IP-MS (IFT-B enriched); Fig 2g co-IP western validates IFT74; Ext Data Fig 8 ternary SEC (ODA–Shulin + IFT74/81) | Human (airway ECs); *Tetrahymena* ODA in reconstitution | Physical association; **not** isolated binary binding | Strong (for association) | Include. Model DNAAF9+IFT74 and DNAAF9+IFT74/81; treat a hit as hypothesis-generating for the interface |
| 2 | DNAAF9/Shulin–**IFT81** supported by human airway IP-MS/co-IP and/or reconstitution | **True** (as an *association*) | Issa et al. 2025, NSMB | Fig 2a,b IP-MS; Fig 2h co-IP western validates IFT81; Ext Data Fig 8 ternary SEC | Human; *Tetrahymena* ODA | Physical association; directness unresolved | Strong (for association) | Include. IFT74/81 form an obligate dimer — model DNAAF9 against the heterodimer, not IFT81 alone |
| 3 | *Chlamydomonas* ODA16/DNAAF18–IFT46 is a strong positive benchmark (direct biochem/structural) | **True** | Taschner et al. 2017, JBC (+ Ahmed et al. 2008, JCB) | Crystal structure 5MZH; ITC Kd = 200 nM (N=0.96); ODA16 N-term + β-propeller bind IFT46 N-terminal 147 aa; Ahmed: Y2H + GST pulldown + co-IP | *C. reinhardtii* (Y2H used mammalian homologues) | **Direct** (structural + ITC) | Very strong | Ideal positive control. Must score high or pipeline is miscalibrated |
| 4 | Human ODA16/DNAAF18–IFT46 not clearly conserved; may be negative/divergent | **True** | Wang et al. 2020, Protein Science | SEC + pulldown of purified human proteins **failed** to detect interaction; human ODA16 N-terminal domain disordered (no density) in 5NNZ | Human | Demonstrated **non-interaction** in vitro | Strong (for divergence) | Species-divergence test. A low score corroborates biochemistry; do NOT treat as a positive control |
| 5 | LRRC56/DNAAF12–IFT88 has evidence, but likely co-IP/cargo not direct binary | **True (mostly)** | Bonnefoy et al. 2018, AJHG | Fig 1D: co-IP of overexpressed LRRC56-V5 + IFT88-eYFP in HEK293 (anti-GFP IP). Trypanosoma: IFT-cargo behaviour (Bonnefoy 2024) | Human (co-IP); *T. brucei* (cargo); *Chlamydomonas* ODA8 | **Co-IP / functional**, not direct | Moderate | Include as exploratory. A negative does not exclude an indirect in-vivo association |
| 6 | DNAAF19/CCDC103–IFT: no strong evidence; better as negative control | **True** | Panizzi et al. 2012, Nat Genet; King & Patel-King 2015 | CCDC103 is a tightly-bound **axonemal** dynein-arm attachment factor with 12-nm MT-binding periodicity; **no reported IFT interaction** | Zebrafish, human, *Chlamydomonas* | No IFT interaction reported (acts in axoneme) | Strong (for "no interaction") | Ideal negative control to estimate false-positive rate |
| 7 | DNAI1/DNAI2 with IFT74/81/46 are plausible exploratory ODA-cargo, not established direct | **True** | Dai et al. 2018, MBoC (transport); Ahmed 2008 (co-precip) | DNAI2/IC2-mNeonGreen moves by IFT in vivo; ODA16-HA co-precipitates IFT46+IFT81 from flagellar matrix (adaptor-bridged, not DNAI-direct) | *Chlamydomonas* | Cargo transport / inference; **no direct binary DNAI–IFT shown** | Weak→Moderate | Exploratory only. IC/N-terminal domains are the sensible constructs |
| 8 | DNAH5/DNAH9 with IFT should not be modelled full-length initially (size) | **True** | UniProt (DNAH5 Q8TE73 ~4624 aa; DNAH9 Q9NYC9 ~4486 aa); Mali 2021 (Shulin binds dynein **tails**) | No direct DNAH–IFT interaction exists in literature; heavy chains are ~4500–4600 aa (too large for reliable full-length co-folding) | Human (sequence); *Tetrahymena* (Shulin biology) | No direct interaction shown; claim is a modelling constraint | N/A (practical) | Defer / construct-review. Use defined tail/tail-domain fragments only |
| 9 | IFT74–IFT81 is an internal positive control (direct structural/biochem) | **True** | Bhogaraju et al. 2013, Science; Lucker et al. 2005, JBC | IFT74/IFT81 form a coiled-coil heterodimer (Lucker 2005 "direct interaction"); Bhogaraju: crystal of IFT81N, IFT81N–IFT74N heterodimer | Human/*Chlamydomonas* | **Direct** | Very strong | Excellent positive control |
| 10 | IFT46–IFT52 and IFT88–IFT52 are useful IFT-B internal positive controls | **True** | Taschner et al. 2014, JCB (IFT52/46, PDB 4UZZ); Taschner et al. 2011, JBC (IFT52 direct to IFT46/70/88/57) | Crystal structure of IFT52C–IFT46C; biochemical mapping shows IFT52 binds directly to IFT88 | *Tetrahymena*/*Chlamydomonas* | **Direct** | Very strong (IFT46–IFT52); Strong (IFT88–IFT52) | Good positive controls. Confirm the exact interacting fragments |
| 11 | TTC25/ODAD4–IFT may be a relevant docking/IFT candidate, not necessarily direct | **True** | Xu et al. 2015, PLoS One | Fig 6A: TTC25 co-IP shows "strong interaction" / "association" with tested IFT-A and IFT-B components (over-expressed, pre-incubated) | Mouse/human proteins; zebrafish morphants | **Co-IP / association**, not direct | Moderate | Include as exploratory. TTC25–CCDC114 (Wallmeier 2016) is the better-anchored physical pair |
| 12 | CCDC151/ODAD3–IFT links are functional/indirect, not proven physical | **True** | Jerber et al. 2014, Hum Mol Genet; Hjeij et al. 2014, AJHG | CCDC151 "required for IFT-dependent motile cilia" = cilia *type*, not a CCDC151–IFT complex; CCDC151 co-IPs **CCDC114** (ODA-DC), not IFT | *Drosophila*, zebrafish, human, mouse | **Functional dependence**; no direct CCDC151–IFT physical interaction | Weak (for any IFT interaction) | Low priority. Better modelled against ODA-DC (CCDC114) than IFT |

---

## 3. Paper-by-paper evidence notes

**Ahmed et al. 2008, *J Cell Biol* 183(2):313–322.** *C. reinhardtii.* Proteins: ODA16 (DAW1/WDR69), IFT46, IFT81, FLA10. ODA16–IFT46 identified by **yeast two-hybrid using mammalian homologues**, confirmed by **GST pulldown** (GST-ODA16 pulls IFT46 from flagellar matrix) and **co-IP** (ODA16-HA co-precipitates IFT46, IFT81, FLA10). One-sentence interpretation: establishes ODA16 as a cargo-specific IFT adaptor physically linked to IFT-B, with the ODA16–IFT46 contact treated as direct. *Relevance:* underpins the positive-control status of the algal interaction; the co-precipitation of IFT81 is complex-level, not a direct ODA16–IFT81 contact.

**Hou et al. 2007, *J Cell Biol* 176(5):653–665.** *C. reinhardtii.* IFT46 null has short paralysed flagella lacking dynein arms; a suppressor restoring an N-terminally truncated IFT46 rebuilds flagella that **specifically lack ODAs**. One-sentence interpretation: genetic proof that IFT46 (its N-terminus) is required to transport ODAs — functional, not a binary-binding result. *(The follow-up, "The N-terminus of IFT46 mediates IFT of outer arm dynein and its adaptor ODA16," MBoC 2017, DOI 10.1091/mbc.e17-03-0172, reinforces this.)*

**Taschner et al. 2017, *J Biol Chem* 292(18):7462–7473.** *C. reinhardtii.* Proteins: CrODA16, CrIFT46. Crystal structure of CrODA16 (**PDB 5MZH**); ODA16's 80-aa N-terminal domain + C-terminal 8-bladed β-propeller both required to bind the **N-terminal 147 residues of IFT46**; **ITC Kd = 200 nM (N=0.96, ≈217 nM)**; β-propeller (not N-domain) binds ODAs. One-sentence interpretation: the single most rigorous, structurally-mapped ODA-adaptor–IFT interaction in the field — the gold-standard positive control (algal only).

**Wang et al. 2020, *Protein Science* 29(6):1502–1510.** Human. Proteins: human ODA16 (DAW1), human IFT46. Crystal structure of human ODA16 (**PDB 5NNZ**); the N-terminal domain that forms the IFT46-binding cleft in algae is **disordered (no density)**; **SEC + pulldown of purified proteins failed to detect any human ODA16–IFT46 interaction**. One-sentence interpretation: a demonstrated in-vitro **negative** in human — the empirical basis for treating human ODA16–IFT46 as a species-divergence test, not a positive control.

**Dai et al. 2018, *Mol Biol Cell* 29(21):2553–2565.** *C. reinhardtii.* Proteins: IC2/**DNAI2**-mNeonGreen (ODA reporter), ODA16, IFT46. In-vivo TIRF shows DNAI2 moves with IFT; transport frequency reduced in *oda16* and *ift46ΔN*. One-sentence interpretation: proves ODAs are IFT cargo and that ODA16/IFT46 are needed for their transport — a cargo/functional result, **not** a DNAI2–IFT binary-binding result.

**Mali et al. 2021, *Science* 371(6532):910–916.** *Tetrahymena thermophila.* Proteins: Shulin (Q22YU3 = TTHERM_00122270, "**C20ORF194-like**" = ortholog of human DNAAF9), ODA subunits. Cryo-EM of the ODA–Shulin complex (**PDB 6ZYX**, EMD-11579); Shulin binds **dynein tails**, locking the three motors closed and inhibiting activity; released upon ciliary incorporation. One-sentence interpretation: defines Shulin/DNAAF9 as an ODA packaging chaperone; contains **no IFT interaction** (that comes from the 2025 paper).

**Issa (Housseini B Issa) et al. 2025, *Nat Struct Mol Biol* 32:2454–2464.** Human airway epithelial cells (ALI ECs d17/19, MCs d45) + *Tetrahymena* ODA. Proteins: DNAAF9 (Shulin/C20orf194), IFT74, IFT81, ARL3, ODA subunits. **Fig 2a,b** endogenous DNAAF9 IP-MS/TMT → IFT-B enriched GO term; **Fig 2g,h** co-IP western validates **IFT74 and IFT81** as DNAAF9 interactors in ECs; **Ext Data Fig 8** SEC reconstitution shows a **ternary ODA–Shulin + human IFT74/81** complex co-eluting (ODA holocomplex + strep-Shulin + His-ZZ-IFT81 + untagged IFT74). DNAAF9/Shulin preferentially bind **Arl3-GTP** (Arl3-Q70L co-elution/pulldown, neg-stain EM, AlphaFold modelling; Arl3-GTP displaces Shulin from ODAs); **no Kd reported for any pair**. One-sentence interpretation: strong multi-method evidence that DNAAF9 associates with IFT74/81 and couples packaged ODAs to IFT trains — but **directness of DNAAF9↔IFT74 or ↔IFT81 is not isolated**; the reconstituted complex is ternary and could be ODA-bridged. *Preprint lineage: bioRxiv 2024.08.15.608058; Research Square rs-5233849.*

**Bonnefoy et al. 2018, *Am J Hum Genet* 103(5):727–739.** Human + *T. brucei* + *Chlamydomonas*. Proteins: LRRC56 (DNAAF12/ODA8), IFT88. **Fig 1D**: co-IP of overexpressed LRRC56-V5 with IFT88-eYFP in **HEK293** (anti-GFP IP). In *T. brucei*, LRRC56 co-localises with IFT trains and is required for adding ODAs to the distal axoneme. One-sentence interpretation: a real physical **association by co-IP of tagged, over-expressed proteins** plus functional IFT linkage — not evidence of direct binary binding, and the figure legend's "interact in vitro" overstates a cellular co-IP.

**Bonnefoy et al. 2024, *Mol Biol Cell* 35(9), DOI 10.1091/mbc.E23-11-0425.** *T. brucei* (+ *Chlamydomonas oda8*). LRRC56 is a **transient IFT cargo** required to assemble the distal ODA docking complex; in *Chlamydomonas oda8*, DNAI2/IC2-mNG ODA-transport frequency is strongly reduced. One-sentence interpretation: reframes LRRC56 as an IFT *cargo* coupled to distal docking-complex assembly — consistent with an indirect LRRC56–IFT relationship.

**Bhogaraju et al. 2013, *Science* 341(6149):1009–1012.** Human/*Chlamydomonas.* Proteins: IFT81 (CH domain), IFT74 (basic N-terminus), αβ-tubulin. Crystal of IFT81N; IFT81N binds tubulin **Kd ≈ 16 µM**, enhanced ~18× by IFT74N (**heterodimer Kd ≈ 0.9 µM**); IFT74/IFT81 heterodimerise via coiled-coils (direct interaction originally Lucker et al. 2005, JBC 280:27688). One-sentence interpretation: the paradigm cargo-adaptation module and a direct, structurally-defined IFT74–IFT81 interaction — excellent internal positive controls.

**Taschner et al. 2014, *J Cell Biol* 207(2):269–282.** *Tetrahymena/Chlamydomonas.* Crystal structures of IFT70/52 and **IFT52/46** (**PDB 4UZZ**) — direct IFT46C–IFT52C interface. One-sentence interpretation: direct structural evidence for the IFT-B1 core, giving a clean positive control. *(Direct IFT52–IFT88 binding is from Taschner et al. 2011, JBC 286:26344–26352, "IFT52 binds directly to four other IFT-B subunits.")*

**Xu et al. 2015, *PLoS One* 10(4):e0124378.** Mouse/human proteins; zebrafish morphants. **Fig 6A**: FLAG-TTC25 co-IP shows "strong interaction"/"association" with tested IFT-A and IFT-B components (proteins pre-incubated to allow complex formation). Note the same paper demonstrates **direct** GST pulldowns for BBS7–TTC4/TTC9c (S6 Fig) but **not** for TTC25–IFT. One-sentence interpretation: TTC25–IFT is a co-IP-level association, explicitly not shown to be direct.

**Wallmeier et al. 2016, *Am J Hum Genet* 99(2):460–469.** Human + mouse. Proteins: TTC25 (**ODAD4**), CCDC114 (ODAD1). Reciprocal **co-IP** shows CCDC114–TTC25 interaction; TTC25 loss removes ODAs and the ODA-DC (CCDC114/CCDC151/ARMC4). One-sentence interpretation: places TTC25 in the ODA-DC via a CCDC114 co-IP — a docking-complex physical link, distinct from (and better-anchored than) the TTC25–IFT association.

**Jerber et al. 2014, *Hum Mol Genet* 23(3):563–577.** *Drosophila*, zebrafish, mouse cells. CCDC151 is "associated with motile **IFT-dependent** cilia" and required for dynein-arm assembly; it is an ODA-DC-related protein (co-IPs CCDC114 per Hjeij et al. 2014, AJHG 95(3):257–274). One-sentence interpretation: the "IFT" in the title denotes the cilia type, not a CCDC151–IFT physical complex — the IFT relationship is functional/indirect.

**King & Patel-King 2015, *J Biol Chem* 290(12):7388–7401** (+ **2020, *Cytoskeleton* 77(1-2):25–35**). *Chlamydomonas.* CCDC103 (Pr46b) is an unusually stable, self-oligomerising **axonemal** protein binding microtubules with 12-nm periodicity to generate ODA-attachment sites. One-sentence interpretation: CCDC103 acts inside the axoneme downstream of transport, with **no** IFT interaction — supports its use as a negative control.

**Panizzi et al. 2012, *Nat Genet* 44(6):714–719.** Zebrafish (*schmalhans*), human, *Chlamydomonas.* CCDC103 mutations cause PCD via failed **dynein-arm attachment**; Ccdc103 is a tightly axoneme-bound protein. One-sentence interpretation: establishes CCDC103 as an axonemal attachment factor — no transport/IFT role, consistent with negative-control status.

---

## 4. Corrected first-pass interaction list

**Positive controls (must score high; calibrate true positives)**
- **ODA16(Cr)–IFT46(Cr)** — direct, structurally mapped, Kd 200 nM (Taschner 2017). Primary calibrator.
- **IFT74–IFT81** (coiled-coil heterodimer; model N-terminal region) — direct (Lucker 2005; Bhogaraju 2013).
- **IFT46–IFT52** (PDB 4UZZ) — direct (Taschner 2014).
- **IFT88–IFT52** — direct biochemical (Taschner 2011); confirm interacting fragments.
- *(Optional)* **IFT81N/IFT74N–αβ-tubulin** — direct, structurally defined cargo-adaptation control (Bhogaraju 2013).

**Strong candidates (highest-value unknowns)**
- **DNAAF9–IFT74** (human) — model against IFT74, and separately against the IFT74/81 dimer.
- **DNAAF9–IFT81** (human) — same; IFT74/81 is an obligate heterodimer, so the dimer is the biologically meaningful target.
- *(Conservation check)* **DNAAF9/Shulin(Tt or Cr ortholog)–IFT74/81** — tests whether any predicted interface is conserved.

**Exploratory candidates**
- **LRRC56(DNAAF12)–IFT88** (human) — resolve direct vs. bridged.
- **TTC25(ODAD4)–IFT88 / –IFT52 / –IFT57** and **TTC25–IFT140** (IFT-A) — docking-complex/IFT adaptation.
- **TTC25(ODAD4)–CCDC114(ODAD1)** — better-anchored physical positive within the ODA-DC (Wallmeier 2016).
- **DNAI2/DNAI1 (IC / N-terminal domains)–IFT74 / IFT81 / IFT46** — potential direct ODA-subunit–IFT contact; exploratory only.

**Species-divergence tests**
- **ODA16(human/DAW1)–IFT46(human)** — expected low/negative (Wang 2020); a discriminative benchmark, not a positive control.
- **ODA16(Cr)–IFT46(Cr) vs. ODA16(human)–IFT46(human)** side-by-side — quantifies how well AlphaPulldown reproduces a known conservation break.

**Negative controls**
- **CCDC103(DNAAF19)–IFT46 / IFT74 / IFT81 / IFT88** — axonemal attachment factor, no IFT role.
- **CCDC151(ODAD3)–IFT** — functional-only; expected negative as a direct binary pair.
- *(Optional)* a cytoplasmic non-ciliary decoy pair, to estimate the false-positive floor.

**Defer / construct-review only**
- **DNAH5–IFT**, **DNAH9–IFT** — do **not** model full-length (~4624 / ~4486 aa). If tested, restrict to defined tail domains (Shulin/DNAAF9 engages dynein *tails*), and expect low reliability.

---

## 5. Exact references

*IDs marked "verify" were not independently confirmed to the digit in this audit; the DOI and/or PMC ID given are confirmed and sufficient to locate the paper. No citation here is fabricated.*

1. Ahmed NT, Gao C, Lucker BF, Cole DG, Mitchell DR. ODA16 aids axonemal outer row dynein assembly through an interaction with the intraflagellar transport machinery. *J Cell Biol.* 2008;183(2):313–322. DOI: 10.1083/jcb.200802025. PMID: 18852297. PMC2568026.
2. Hou Y, Qin H, Follit JA, Pazour GJ, Rosenbaum JL, Witman GB. Functional analysis of an individual IFT protein: IFT46 is required for transport of outer dynein arms into flagella. *J Cell Biol.* 2007;176(5):653–665. DOI: 10.1083/jcb.200608041. PMID: 17312020.
3. Taschner M, Mourão A, Awasthi M, Basquin J, Lorentzen E. Structural basis of outer dynein arm intraflagellar transport by the transport adaptor protein ODA16 and the intraflagellar transport protein IFT46. *J Biol Chem.* 2017;292(18):7462–7473. DOI: 10.1074/jbc.M117.780155. PMID: 28298440. (PDB 5MZH.)
4. Wang J, Taschner M, Petriman NA, Andersen MB, Basquin J, Bhogaraju S, Vetter M, Wachter S, Lorentzen A, Lorentzen E. Purification and crystal structure of human ODA16: implications for ciliary import of outer dynein arms by the intraflagellar transport machinery. ***Protein Science.* 2020;29(6):1502–1510. DOI: 10.1002/pro.3864.** PMC7255517. PMID: 32297394 (verify). (PDB 5NNZ.) — **Corrects the prior draft's "Phil Trans R Soc B" citation, which is wrong.**
5. Dai J, Barbieri F, Mitchell DR, Lechtreck KF. In vivo analysis of outer arm dynein transport reveals cargo-specific intraflagellar transport properties. *Mol Biol Cell.* 2018;29(21):2553–2565. DOI: 10.1091/mbc.E18-05-0291. PMID: 30133350. PMC6254574.
6. Mali GR, Ali FA, Lau CK, Begum F, Boulanger J, Howe JD, Chen ZA, Rappsilber J, Skehel M, Carter AP. Shulin packages axonemal outer dynein arms for ciliary targeting. *Science.* 2021;371(6532):910–916. DOI: 10.1126/science.abe0526. PMID: 33632841. PMC7116892. (PDB 6ZYX; EMD-11579.)
7. Housseini B Issa K, Ren M, et al. (Mali GR, corresponding). Molecular basis for the activation of outer dynein arms in cilia. ***Nat Struct Mol Biol.* 2025;32(12):2454–2464. DOI: 10.1038/s41594-025-01680-9. PMID: 41023246.** Preprints: bioRxiv 2024.08.15.608058 (DOI 10.1101/2024.08.15.608058); Research Square rs-5233849. — **Confirmed formally published (not preprint-only).**
8. Bonnefoy S, Watson CM, Kernohan KD, et al. Biallelic mutations in *LRRC56*, encoding a protein associated with intraflagellar transport, cause mucociliary clearance and laterality defects. *Am J Hum Genet.* 2018;103(5):727–739. DOI: 10.1016/j.ajhg.2018.10.003. PMID: 30388400.
9. Bonnefoy S, et al. LRRC56 is an IFT cargo required for assembly of the distal dynein docking complex in *Trypanosoma brucei*. *Mol Biol Cell.* 2024;35(9). DOI: 10.1091/mbc.E23-11-0425. PMC11321045. PMID (verify).
10. Bhogaraju S, Cajanek L, Fort C, Blisnick T, Weber K, Taschner M, Mizuno N, Lamla S, Bastin P, Nigg EA, Lorentzen E. Molecular basis of tubulin transport within the cilium by IFT74 and IFT81. *Science.* 2013;341(6149):1009–1012. DOI: 10.1126/science.1240985. PMID: 23990561.
11. Lucker BF, Behal RH, Qin H, Siron LC, Taggart WD, Rosenbaum JL, Cole DG. Characterization of the intraflagellar transport complex B core: direct interaction of the IFT81 and IFT74/72 subunits. *J Biol Chem.* 2005;280(30):27688–27696. DOI: 10.1074/jbc.M505062200. PMID: 15955805 (verify).
12. Taschner M, Kotsis F, Braeuer P, Kuehn EW, Lorentzen E. Crystal structures of IFT70/52 and IFT52/46 provide insight into intraflagellar transport B core complex assembly. *J Cell Biol.* 2014;207(2):269–282. DOI: 10.1083/jcb.201408002. PMID: 25349261. (PDB 4UZZ.)
13. Taschner M, Bhogaraju S, Vetter M, Morawetz M, Lorentzen E. Biochemical mapping of interactions within the intraflagellar transport (IFT) B core complex: IFT52 binds directly to four other IFT-B subunits. *J Biol Chem.* 2011;286(30):26344–26352. DOI: 10.1074/jbc.M111.254714 (verify). PMID: 21606493 (verify).
14. Xu Y, Cao J, Huang S, Feng D, Zhang W, Zhu X, Yan X. Characterization of tetratricopeptide repeat-containing proteins critical for cilia formation and function. *PLoS One.* 2015;10(4):e0124378. DOI: 10.1371/journal.pone.0124378. PMID: 25860617. PMC4393279.
15. Wallmeier J, Shiratori H, Dougherty GW, et al. TTC25 deficiency results in defects of the outer dynein arm docking machinery and primary ciliary dyskinesia with left-right body asymmetry randomization. *Am J Hum Genet.* 2016;99(2):460–469. DOI: 10.1016/j.ajhg.2016.06.014. PMID: 27486780.
16. Jerber J, Baas D, Soulavie F, Chhin B, Cortier E, Vesque C, Thomas J, Durand B. The coiled-coil domain containing protein CCDC151 is required for the function of IFT-dependent motile cilia in animals. *Hum Mol Genet.* 2014;23(3):563–577. DOI: 10.1093/hmg/ddt445. PMID: 24067530.
17. Hjeij R, Onoufriadis A, Watson CM, et al. CCDC151 mutations cause primary ciliary dyskinesia by disruption of the outer dynein arm docking complex formation. *Am J Hum Genet.* 2014;95(3):257–274. DOI: 10.1016/j.ajhg.2014.08.005. PMID: 25192045.
18. King SM, Patel-King RS. The oligomeric outer dynein arm assembly factor CCDC103 is tightly integrated within the ciliary axoneme and exhibits periodic binding to microtubules. *J Biol Chem.* 2015;290(12):7388–7401. DOI: 10.1074/jbc.M114.616425. PMID: 25572396.
19. King SM, Patel-King RS. The outer dynein arm assembly factor CCDC103 forms molecular scaffolds through multiple self-interaction sites. *Cytoskeleton (Hoboken).* 2020;77(1-2):25–35. DOI: 10.1002/cm.21591. PMID: 31743573 (verify).
20. Panizzi JR, Becker-Heck A, Castleman VH, et al. CCDC103 mutations cause primary ciliary dyskinesia by disrupting assembly of ciliary dynein arms. *Nat Genet.* 2012;44(6):714–719. DOI: 10.1038/ng.2277. PMID: 22581229.
21. Braschi B, Omran H, Witman GB, Pazour GJ, Pfister KK, Bruford EA, King SM. Consensus nomenclature for dyneins and associated assembly factors. *J Cell Biol.* 2022;221(2):e202109014. DOI: 10.1083/jcb.202109014. PMID: 35006274 (verify). *(Background/nomenclature.)*
22. **Background/review, not primary evidence:** (a) the IFT46-N-terminus MBoC paper, DOI 10.1091/mbc.e17-03-0172, PMC5576905, on the functional role of IFT46's N-terminus in ODA/ODA16 transport; (b) Wang J, et al. Integrative in silico and biochemical analyses demonstrate direct Arl3-mediated ODA16 release from the intraflagellar transport machinery. *J Biol Chem.* 2025. PMC11879689 — *notable because it uses AlphaPulldown itself and independently restates that human ODA16 does not bind human IFT46.*

---

## 6. Unresolved uncertainties

1. **Directness of DNAAF9–IFT74/IFT81 is not established.** Every experiment (IP-MS, co-IP, ternary SEC) is consistent with DNAAF9 reaching IFT74/81 *through* the ODA it packages. No two-protein (DNAAF9 + IFT74, or DNAAF9 + IFT81) reconstitution exists. AlphaPulldown could uniquely nominate whether a *direct* DNAAF9–IFT74/81 interface is plausible — but a negative prediction would not refute the (real) association, and a positive prediction is a hypothesis, not confirmation.
2. **No Kd exists for any DNAAF9/Shulin–IFT or Shulin–Arl3 pair.** The 2025 paper is qualitative (co-elution, displacement, EM). Affinity/interface remain open.
3. **The physical ODA→IFT-train contact point is unknown.** IFT74/81 is the leading candidate site, but no structure resolves how an ODA (or ODA–Shulin) docks onto a train. This is the single biggest mechanistic gap the screen could probe.
4. **The human ODA-import adaptor is unidentified.** Human ODA16 does not bind human IFT46, so either an unknown adaptor exists, DNAAF9 partly fills this role, or human import uses a different logic. Untested structurally.
5. **LRRC56–IFT88 directness is unresolved.** The only physical datum is an overexpression co-IP; whether binding is direct, or bridged by endogenous IFT/ODA/docking components, is unknown. Species phenotypes also differ (distal-only ODA loss in *T. brucei* vs. dyskinesia-without-ultrastructural-defect in human).
6. **TTC25–IFT interface is undefined**, and whether TTC25 physically bridges IFT-A and IFT-B (vs. associating with each separately) is untested.
7. **DNAI1/DNAI2–IFT: no direct binary interaction has ever been shown** — only cargo transport (via the ODA16/DNAAF9 adaptor systems). Whether any ODA subunit contacts an IFT protein directly is open.
8. **Gene-identity caveats to carry into modelling:** DNAAF9 = C20orf194 = Shulin (confirmed); DNAAF18 = DAW1 = ODA16 = WDR69 (HGNC-approved symbol is DAW1); DNAAF12 = LRRC56 (HGNC lists DNAAF12 as an alias of the approved symbol LRRC56); DNAAF19 = CCDC103 (approved symbol CCDC103). Use the correct human ortholog sequence, and never let an alias mask a species swap.
9. **Un-reconfirmed identifiers.** Several PMIDs/DOIs above are flagged "verify" (Wang 2020 PMID; Bonnefoy 2024 PMID; Lucker 2005 PMID; Taschner 2011 DOI/PMID; King & Patel-King 2020 PMID; Braschi 2022 PMID). Confirm these against PubMed before they enter a manuscript; the DOIs/PMC IDs not flagged were seen directly in this audit.
10. **AlphaPulldown predictions are not evidence.** Nothing in this audit treats an AlphaFold/AlphaPulldown score as experimental support; the Wang 2025 JBC paper is cited only to note prior methodological use, not as validation of any interaction.
