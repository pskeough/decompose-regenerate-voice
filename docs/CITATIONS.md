# Citations

Keys used in `METHODS.md`. The `verified` column is filled by an agent that
resolves each identifier and checks the title; "own" means a file in this
project. Anything marked `TO VERIFY` is cited from memory and must not reach a
manuscript until the column says `yes` with a date.

| key | reference | id | verified |
|---|---|---|---|
| polaris | Rajendhran, Russell, Iyyer, Wieting (2026). POLARIS: Guiding Small Models to Write Long Stories. EMNLP 2026 Main. SFT on 1,388 human-written stories collapses Qwen3.5-9B story quality (+18.5 to -60.6); GRPO recovers. Quoted in `Voice_Style_Retune/REDESIGN.md` §10 | arXiv 2606.04095 | FIXED 2026-09-03: id was correct but the row carried no title or authors, only a results gloss; added the real title, author list and venue |
| strap | Krishna, Wieting, Iyyer (2020). Reformulating Unsupervised Style Transfer as Paraphrase Generation. EMNLP 2020 | arXiv 2010.05700 | yes 2026-09-03 |
| patel2022 | Patel, Andrews, Callison-Burch (2022). Low-Resource Authorship Style Transfer: Can Non-Famous Authors Be Imitated? | arXiv 2212.08986 | yes 2026-09-03 |
| humpback | Li et al. (2023). Self-Alignment with Instruction Backtranslation | arXiv 2308.06259 | yes 2026-09-03 |
| longform | Koksal et al. (2023). LongForm: Effective Instruction Tuning with Reverse Instructions | arXiv 2304.08460 | yes 2026-09-03 |
| lora | Hu et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models | arXiv 2106.09685 | yes 2026-09-03 |
| qlora | Dettmers et al. (2023). QLoRA: Efficient Finetuning of Quantized LLMs | arXiv 2305.14314 | yes 2026-09-03 |
| biderman2024 | Biderman et al. (2024). LoRA Learns Less and Forgets Less | arXiv 2405.09673 | yes 2026-09-03 |
| shuttleworth2024 | Shuttleworth et al. (2024). LoRA vs Full Fine-tuning: An Illusion of Equivalence | arXiv 2410.21228 | yes 2026-09-03 |
| lee2022 | Lee et al. (2022). Deduplicating Training Data Makes Language Models Better. ACL 2022 | arXiv 2107.06499 | yes 2026-09-03 |
| physics31 | Allen-Zhu, Li (2023). Physics of Language Models: Part 3.1, Knowledge Storage and Extraction | arXiv 2309.14316 | yes 2026-09-03 |
| suri | Pham et al. (2024). Suri: Multi-constraint Instruction Following for Long-form Text Generation | arXiv 2406.19371 | yes 2026-09-03 |
| gururangan2018 | Gururangan et al. (2018). Annotation Artifacts in Natural Language Inference Data. NAACL 2018 | arXiv 1803.02324 | yes 2026-09-03 |
| chang2023 | Chang, Cramer, Soni, Bamman (2023). Speak, Memory: An Archaeology of Books Known to ChatGPT/GPT-4. EMNLP 2023 | arXiv 2305.00118 | yes 2026-09-03 |
| carlini2023 | Carlini et al. (2023). Quantifying Memorization Across Neural Language Models. ICLR 2023 | arXiv 2202.07646 | yes 2026-09-03 |
| luar | Rivera-Soto et al. (2021). Learning Universal Authorship Representations. EMNLP 2021 | aclanthology 2021.emnlp-main.70 | yes 2026-09-03 |
| wegmann2022 | Wegmann, Schraagen, Nguyen (2022). Same Author or Just Same Topic? Towards Content-Independent Style Representations | arXiv 2204.04907 | yes 2026-09-03 |
| stel | Wegmann, Nguyen (2021). Does It Capture STEL? A Modular, Similarity-Based Linguistic Style Evaluation Framework. EMNLP 2021 | arXiv 2109.04817 | yes 2026-09-03 |
| styledistance | Patel et al. (2024). StyleDistance: Stronger Content-Independent Style Embeddings with Synthetic Parallel Examples. NAACL 2025 | arXiv 2410.12757 | yes 2026-09-03 |
| lisa | Patel, Rao, Kothary, McKeown, Callison-Burch (2023). Learning Interpretable Style Embeddings via Prompting LLMs | arXiv 2305.12696 | FIXED 2026-09-03: author list was wrong. Third author is Ansh Kothary, not "Kim", and Kathleen McKeown was missing |
| burrows2002 | Burrows (2002). 'Delta': a Measure of Stylistic Difference and a Guide to Likely Authorship. Literary and Linguistic Computing 17(3), 267-287 | doi 10.1093/llc/17.3.267 | yes 2026-09-03 |
| evert2017 | Evert et al. (2017). Understanding and explaining Delta measures for authorship attribution. Digital Scholarship in the Humanities 32(suppl 2), ii4-ii16 | doi 10.1093/llc/fqx023 | yes 2026-09-03 |
| binoculars | Hans et al. (2024). Spotting LLMs With Binoculars: Zero-Shot Detection of Machine-Generated Text. ICML 2024 | arXiv 2401.12070 | yes 2026-09-03 |
| fastdetectgpt | Bao et al. (2024). Fast-DetectGPT: Efficient Zero-Shot Detection of Machine-Generated Text via Conditional Probability Curvature. ICLR 2024 | arXiv 2310.05130 | yes 2026-09-03 |
| mtmm | Campbell, Fiske (1959). Convergent and discriminant validation by the multitrait-multimethod matrix. Psychological Bulletin 56(2), 81-105 | doi 10.1037/h0046016 | yes 2026-09-03 |
| holm1979 | Holm (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics 6(2), 65-70 | jstor 4615733 | yes 2026-09-03 |
| sawant | Sawant (2026). Theory-Grounded Evaluation Exposes the Authorship Gap in LLM Personalization. CTB Workshop, ICML 2026. Four inference-time personalization methods, 50 authors, 1,000 generations; three metric traditions produce near-zero pairwise correlations (abs r < 0.07), so metric choice determines the conclusion | arXiv 2604.26460 | FIXED 2026-09-03: filled from `litsweep`. The "28-point content-leakage confound" gloss in the placeholder table is not supported anywhere in the sweep; see the verification log |
| chakrabarty | Chakrabarty, Ginsburg, Dhillon (2025/2026). Readers Prefer Outputs of AI Trained on Copyrighted Books over Expert Human Writers. Preprint under review, v1 15 Oct 2025, v4 17 Mar 2026 | arXiv 2510.13939 | FIXED 2026-09-03: filled from `litsweep`. This is the sweep's Chakrabarty-first-author paper; it is not about "idiosyncrasies and editing" as the placeholder said, see the verification log |
| judgebias1 | Tutone, Franceschelli, Musolesi (2026). The Limits of Automatic Evaluation of Creativity in Large Language Models. LLM judges show "a systematic preference for AI-generated stories, consistently favoring their stylistic characteristics over the unpredictability and other qualities of human-authored texts" | arXiv 2608.23705 | yes 2026-09-03 |
| judgebias2 | Ferstler, Podoxin, Brassington, Grundkiewicz, Taboada, Karpinska (2026). AI translation of literary texts is "fine", but readers still prefer human translations. "Automatic metrics, including LLM-as-a-judge approaches, fail to recover reader preferences and favor MT" | arXiv 2606.26040 | yes 2026-09-03 |
| judgebias3 | Norman, Rivera, Hughes (2026). Reliability without Validity: A Systematic, Large-Scale Evaluation of LLM-as-a-Judge Models Across Agreement, Consistency, and Bias. 21 judges, 9 providers, 118 runs, ~541,000 judgements; kappa deflation 33-41 pp, rankings shift up to 14 positions, "consistency-bias paradox" | arXiv 2606.19544 | yes 2026-09-03 |
| overnight0903 | Overnight instrument battery, 2026-09-03: order-invariance, attribution, detector sweep | `overnight_0903/out/RESULTS.md`, `FOLLOWUPS.md` | own |
| fieldreport | Field report with decision cards D1-D13, 2026-09-02 | `C:\Claude_Personal_Conv\notes\voice-retune-field-report-2026-09-02.md` | own |
| litsweep | Literature blindspot sweep, 2026-09-02 (238 KB, eight sub-sweeps) | `C:\Claude_Personal_Conv\notes\voice-retune-lit-blindspots-2026-09-02.md` | own |
| corpusreport | Multi-author corpus v2 build report | `Voice_Style_Retune/data/authors_v2/CORPUS_REPORT.md` | own |
| redesign | REDESIGN.md, 2026-08, §10 on POLARIS | `Voice_Style_Retune/REDESIGN.md` | own |

## To be filled from the lit sweep

These are cited in conversation and in `litsweep` but the exact references
have not been copied here. An agent fills them from the sweep file, not from
memory.

| key | what it is |
|---|---|
| onlyif | the step transition at ~300 unique instructions (cited in `scripts/build_views.py`) |

**Note, 2026-09-03.** `onlyif` is NOT in `litsweep`. Grepping the sweep file for
"Only-IF", "OnlyIF", "unique instructions", "300 unique" and "instruction
diversity" returns nothing; the sweep's fourteen "instruction" hits are all
other papers. The reference the project actually uses comes from
`Voice_Style_Retune/REDESIGN.md` line 32, which cites arXiv **2410.04717**.
That id was resolved as a cross-check and is real: *Only-IF: Revealing the
Decisive Effect of Instruction Diversity on Generalization*, Dylan Zhang,
Justin Wang, Francois Charton, 7 Oct 2024 (v3 18 Oct 2024). Caveat before this
is promoted to a full row: the arXiv abstract states the diversity result but
does **not** state the "fewer than 300 unique instructions" threshold, so the
specific number used in `scripts/build_views.py`, `scripts/build_api_views.py`
and `scripts/train_views.py` still needs to be located in the paper body.

## Verification log 2026-09-03

Each identifier was resolved directly (arxiv.org/abs, Crossref for DOIs, ACL
Anthology, JSTOR/search for the Holm entry) and the returned title and first
author compared against the row.

- **polaris** — arXiv 2606.04095 resolves to *POLARIS: Guiding Small Models to Write Long Stories*, Rishanth Rajendhran, Jenna Russell, Mohit Iyyer, John Frederick Wieting, 2 Jun 2026 (v2 30 Aug 2026), accepted to EMNLP 2026 Main as a long paper. The id in the row was correct and is on-topic (GRPO recipe, small-model long-form story quality, LLM-judge Story Quality rubric, human-reference injection), matching the REDESIGN.md §10 use. The row itself carried only a results gloss, no title or authors, so it was rewritten with the real bibliographic data. FIXED.
- **strap** — arXiv 2010.05700, *Reformulating Unsupervised Style Transfer as Paraphrase Generation*, Kalpesh Krishna, John Wieting, Mohit Iyyer, EMNLP 2020. Title and first author match. yes.
- **patel2022** — arXiv 2212.08986, *Low-Resource Authorship Style Transfer: Can Non-Famous Authors Be Imitated?*, Ajay Patel, Nicholas Andrews, Chris Callison-Burch, Dec 2022. Match. yes.
- **humpback** — arXiv 2308.06259, *Self-Alignment with Instruction Backtranslation*, Xian Li et al., Aug 2023. Match. yes.
- **longform** — arXiv 2304.08460, *LongForm: Effective Instruction Tuning with Reverse Instructions*, Abdullatif Köksal, Timo Schick, Anna Korhonen, Hinrich Schütze, Apr 2023. Match (row spells the first author without diacritics, left as-is). Note for a manuscript: the paper was later accepted to EMNLP 2024 Findings, so a venue line should say 2024, not 2023. yes.
- **lora** — arXiv 2106.09685, *LoRA: Low-Rank Adaptation of Large Language Models*, Edward J. Hu et al., Jun 2021. Match. yes.
- **qlora** — arXiv 2305.14314, *QLoRA: Efficient Finetuning of Quantized LLMs*, Tim Dettmers et al., May 2023. Match. yes.
- **biderman2024** — arXiv 2405.09673, *LoRA Learns Less and Forgets Less*, Dan Biderman et al., 2024. Match. yes.
- **shuttleworth2024** — arXiv 2410.21228, *LoRA vs Full Fine-tuning: An Illusion of Equivalence*, Reece Shuttleworth, Jacob Andreas, Antonio Torralba, Pratyusha Sharma, Oct 2024. Match. yes.
- **lee2022** — arXiv 2107.06499, *Deduplicating Training Data Makes Language Models Better*, Katherine Lee et al. The preprint is 2021; the row's ACL 2022 venue is correct. Match. yes.
- **physics31** — arXiv 2309.14316, *Physics of Language Models: Part 3.1, Knowledge Storage and Extraction*, Zeyuan Allen-Zhu, Yuanzhi Li, Sep 2023. Match. yes.
- **suri** — arXiv 2406.19371, *Suri: Multi-constraint Instruction Following for Long-form Text Generation*, Chau Minh Pham, Simeng Sun, Mohit Iyyer, Jun 2024 (EMNLP 2024 Findings). Match. yes.
- **gururangan2018** — arXiv 1803.02324, *Annotation Artifacts in Natural Language Inference Data*, Suchin Gururangan et al., Mar 2018, NAACL 2018. Match. yes.
- **chang2023** — arXiv 2305.00118, *Speak, Memory: An Archaeology of Books Known to ChatGPT/GPT-4*, Kent K. Chang, Mackenzie Cramer, Sandeep Soni, David Bamman, 2023. Match, including the full four-author order in the row. yes.
- **carlini2023** — arXiv 2202.07646, *Quantifying Memorization Across Neural Language Models*, Nicholas Carlini et al., Feb 2022, ICLR 2023. Match; the row's ICLR 2023 venue is correct. yes.
- **luar** — aclanthology 2021.emnlp-main.70, *Learning Universal Authorship Representations*, Rafael A. Rivera-Soto et al., EMNLP 2021. Match. yes.
- **wegmann2022** — arXiv 2204.04907, *Same Author or Just Same Topic? Towards Content-Independent Style Representations*, Anna Wegmann, Marijn Schraagen, Dong Nguyen, Apr 2022. Match. yes.
- **stel** — arXiv 2109.04817, *Does It Capture STEL? A Modular, Similarity-based Linguistic Style Evaluation Framework*, Anna Wegmann, Dong Nguyen, Sep 2021, EMNLP 2021. Match. yes.
- **styledistance** — arXiv 2410.12757, *StyleDistance: Stronger Content-Independent Style Embeddings with Synthetic Parallel Examples*, Ajay Patel et al., Oct 2024. Match; NAACL 2025 venue added to the row.  yes.
- **lisa** — arXiv 2305.12696, *Learning Interpretable Style Embeddings via Prompting LLMs*. Title and first author (Ajay Patel) match, but the real author list is Ajay Patel, Delip Rao, Ansh Kothary, Kathleen McKeown, Chris Callison-Burch. The row named a nonexistent "Kim" and dropped McKeown. Author list corrected. FIXED.
- **burrows2002** — doi 10.1093/llc/17.3.267 resolves via Crossref to *'Delta': a Measure of Stylistic Difference and a Guide to Likely Authorship*, J. Burrows, Literary and Linguistic Computing 17(3), 267-287, 2002. Match; page range added. yes.
- **evert2017** — doi 10.1093/llc/fqx023 resolves to *Understanding and explaining Delta measures for authorship attribution*, Stefan Evert, Fotis Jannidis, Thomas Proisl, Isabella Reger, Steffen Pielström, Christof Schöch, Thorsten Vitt, Digital Scholarship in the Humanities 32(suppl_2), ii4-ii16, 2017. Match; page range added. yes.
- **binoculars** — arXiv 2401.12070, *Spotting LLMs With Binoculars: Zero-Shot Detection of Machine-Generated Text*, Abhimanyu Hans et al., Jan 2024, ICML 2024. Match. yes.
- **fastdetectgpt** — arXiv 2310.05130, *Fast-DetectGPT: Efficient Zero-Shot Detection of Machine-Generated Text via Conditional Probability Curvature*, Guangsheng Bao et al., Oct 2023, ICLR 2024. Match. yes.
- **mtmm** — doi 10.1037/h0046016 resolves via Crossref to *Convergent and discriminant validation by the multitrait-multimethod matrix*, Donald T. Campbell, Donald W. Fiske, Psychological Bulletin 56(2), 81-105, 1959. Every field in the row matches. yes.
- **holm1979** — JSTOR's own page would not render for the fetcher, so the record was confirmed by search against the stable id: jstor.org/stable/4615733 is *A Simple Sequentially Rejective Multiple Test Procedure*, Sture Holm, Scandinavian Journal of Statistics 6(2), 65-70, 1979. Title, author, journal, volume, issue, pages and year all match the row. yes.
- **sawant** (new, from `litsweep` line 453) — arXiv 2604.26460, *Theory-Grounded Evaluation Exposes the Authorship Gap in LLM Personalization*, Yash Ganpat Sawant, 29 Apr 2026 (rev 14 Aug 2026), CTB Workshop at ICML 2026. Id resolves and the sweep's summary matches the abstract. **Discrepancy flagged:** the placeholder described this key as "the 28-point content-leakage confound in style-prompting evaluation". No such claim exists in the sweep. Grepping the sweep for "content leakage", "content-leakage", "confound", "28-point" and "style prompting" returns only (a) an UNVERIFIED entry at line 1508, *Beyond semantics: Content leakage mitigation using synthetic hard negatives for style embeddings*, Expert Systems with Applications Aug 2026, which the sweep itself says has no located DOI and must not be cited, and (b) one unrelated use of "confound" about length at line 824. The sweep carries two Sawant papers and neither reports a 28-point content-leakage effect; the second is *PersonalBench: Measuring the Authorship Gap in LLM Personalization*, arXiv 2608.19746, 20 Aug 2026 (also resolved and real). 2604.26460 was chosen because it is the evaluation-confound paper (metric choice determines the conclusion in style-prompting evaluation), which is the nearest real referent. The "28-point" figure should be treated as unsourced until Patrick says where it came from. FIXED.
- **chakrabarty** (new, from `litsweep` lines 240 and 1418) — arXiv 2510.13939, *Readers Prefer Outputs of AI Trained on Copyrighted Books over Expert Human Writers*, Tuhin Chakrabarty, Jane C. Ginsburg, Paramveer Dhillon, v1 15 Oct 2025, v4 17 Mar 2026, preprint under review. Id resolves, title and first author match. **Discrepancy flagged:** the placeholder said "Chakrabarty et al. on LLM creative writing idiosyncrasies and editing". That description fits *StoryScope: Investigating idiosyncrasies in AI fiction* (arXiv 2604.03136, sweep lines 1141 and 1362), whose authors are Russell, Rajendhran, Pham, Iyyer, Wieting with no Chakrabarty; and it also resembles the "salvaged / through edits" paper, which is not in the sweep at all. The sweep's only Chakrabarty-first-author paper is 2510.13939, so that is what was filled in. If the intended citation was the idiosyncrasies-and-edits paper, this row is the wrong one and needs replacing. FIXED.
- **judgebias1** (new, from `litsweep` lines 125, 962 and 1388) — arXiv 2608.23705, *The Limits of Automatic Evaluation of Creativity in Large Language Models*, Alessandro Tutone, Giorgio Franceschelli, Mirco Musolesi, 24 Aug 2026 (v2 27 Aug 2026). Id resolves; the abstract carries the quoted systematic-preference-for-AI-stories finding verbatim. yes.
- **judgebias2** (new, from `litsweep` lines 132 and 1416) — arXiv 2606.26040, *AI translation of literary texts is "fine", but readers still prefer human translations*, Yves Ferstler, Adam Podoxin, Ty Brassington, Roman Grundkiewicz, Maite Taboada, Marzena Karpinska, 24 Jun 2026. Id resolves; the abstract confirms that automatic metrics including LLM-as-a-judge fail to recover reader preferences and favour MT. yes.
- **judgebias3** (new, from `litsweep` lines 126, 964 and 1392) — arXiv 2606.19544, *Reliability without Validity: A Systematic, Large-Scale Evaluation of LLM-as-a-Judge Models Across Agreement, Consistency, and Bias*, Justin D. Norman, Michael U. Rivera, D. Alex Hughes, 17 Jun 2026. Id resolves; 21 judges, kappa deflation 33-41 pp and the "consistency-bias paradox" all confirmed. This one is judge unreliability and position bias rather than a machine-prose preference, so it belongs with judgebias1 and judgebias2 rather than standing alone for that claim. yes.
- **onlyif** — not filled. See the note above the log: absent from `litsweep`, so it stays in the "To be filled" table.
- **overnight0903, fieldreport, litsweep, corpusreport, redesign** — `own`, not re-checked as citations. File existence was confirmed for `litsweep` and `redesign`, which were both read during this pass.
