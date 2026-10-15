# Methods: decompose-and-regenerate evaluation of voice conditioning on a local 4B model

Version 0.1, 2026-09-03. Written before any data was generated. Citation keys in
square brackets resolve in `CITATIONS.md`. Own prior results are cited as files.

## 0. The question

Given a content brief that carries no style, how close does a small local model
get to a specific author's prose under each way of telling it about the author,
and does a per-author adapter add anything once the best prompt-side conditioning
is in place?

The design decomposes what mimesis does into separable components (retrieval,
qualitative guide, quantitative targets, and the gate) so that each can be costed
and each can be combined with a trained adapter. The mimesis tool itself is not
used; only its principle is.

Three prior facts shape the design.

1. The July adapters were trained by plain causal language modelling on the
   author's raw prose, cut into 512-token blocks, in 4-bit. POLARIS [polaris]
   measured that procedure on Qwen3.5-9B with 1,388 professionally edited human
   stories: story quality fell from +18.5 (base) to -60.6. REDESIGN §10 calls it
   "the exact procedure we ran". So the earlier "LoRA writes abhorrently" result
   is a result about raw-target SFT, not about adapters. The trainer here trains
   on a raw passage only as a labelled control (§7).
2. The 2026-09-03 overnight battery (`overnight_0903/out/RESULTS.md`) validated
   which instruments read style and which read order: LUAR and Wegmann are
   order-blind (CIs contain zero under sentence permutation), StyleDistance is
   not, and LUAR gives 0.905 macro-F1 nearest-centroid attribution across the
   fourteen public-domain authors. LUAR is therefore the sealed primary here.
3. A brief that is a compression of the target carries recoverable traces of it
   [gururangan2018]; a prompt that quotes the source hands style to the model
   for free. The Aug `make_prompts.py` guard (no shared 5-gram) is kept and
   extended into numeric leakage gates (§3.2).

## 1. Design summary

Within-passage, repeated measures. Every test passage is regenerated under every
arm, so content is held constant across arms and the passage is the blocking
unit.

| factor | levels (base phase) | levels (adapter phase) |
|---|---|---|
| model | base 4B | base 4B, +LoRA(pair), +LoRA(mix), +LoRA(raw-careful) |
| conditioning | A0 bare, A1 named, A2 retrieval, A3 guide, A4 quant, A5 full | same six |
| comparators | F0 frontier bare, F5 frontier full | - |
| passages | 50 held-out per author | same 50 |
| samples | 2 per cell, seeds fixed | same |

Base phase: 6 arms x 50 passages x 2 samples = 600 local generations plus 200
API generations. Adapter phase: 3 adapters x 6 arms x 50 x 2 = 1,800 local
generations. One author first (Gate 0), then the same pipeline over further
authors (Gate 6), then Patrick's own corpus, which is the use case the
public-domain authors stand in for.

## 2. Materials

### 2.1 Corpus

`data/authors_v2/<author>.jsonl` (built 2026-09-03, `CORPUS_REPORT.md`):
sixteen original-English public-domain authors, 300-800-word chunks on paragraph
boundaries, 5,000 words per work as one contiguous span, block-level cleaning
with per-rule drop counts. Fourteen authors clear 30,000 words.

### 2.2 Author selection for the test run

Proposed: Edith Wharton. Reasons, in order of weight:

* Volume. 289 chunks over 14 Gutenberg volumes and 43 works gives a train split
  of roughly 190 passages after 50 test and 40 reference passages are held out.
  Cather (137) would leave about 50 for training, which is thin for the recipe
  comparison in §7.
* Memorisation. Chang et al. [chang2023] show that what a model has memorised
  of a book tracks the book's popularity on the web, with pre-1930 public-domain
  fiction the most memorised class. Pride and Prejudice, Ulysses, Moby-Dick and
  Mrs Dalloway sit at the top of that list; Wharton's novels are well known but
  not in that tier. Memorisation is a confound for the named arm (A1) and for any
  arm at all when the brief is close enough to a famous scene: the model
  reconstructs from memory rather than writes. §8.5 measures it regardless.
* Voice. Wharton's sentences are long, subordinated and ironic in a way that is
  far from the 4B's default register, so there is room for an arm to move.
* Representation. Patrick asked for women and non-Western authors in the
  eventual set; the test run should not default to a canonical man.

Cather is the second choice (plainer style, less data). Mansfield is
short-story-only with four volumes, which makes a volume-level split brittle.

### 2.3 Splits

Per author, by work, seeded. A novel is one work and is never split; each story
in a collection is its own work. That is the boundary the corpus was built
around (`CORPUS_REPORT.md` §2), and assigning whole works keeps a novel's
characters and invented vocabulary on one side of every split, which n-gram
decontamination alone cannot guarantee [gururangan2018]. A work is capped at
5,000 words, so the overshoot at each boundary is at most about seven chunks.

| split | role | size target |
|---|---|---|
| TEST | passages decomposed and regenerated; the source passage is the scoring target | 50 chunks, 400-800 words |
| REF | held-out author prose for centroids, the quantitative targets' validation, and the judge's reference passage | >= 40 chunks |
| TRAIN | adapter training pairs, retrieval pool, style-guide input, quantitative-target derivation | everything else |

TRAIN is further split by work into TRAIN-fit (90%) and TRAIN-val (10%) for
checkpoint selection in §7. Nothing in REF or TEST is ever seen by the trainer,
the retriever, the guide writer or the target calculator.

Other authors' centroids for attribution use their full `authors_v2` file capped
at 100 chunks each; they are never generated from.

## 3. Decomposition

### 3.1 The brief

An API model (`deepseek/deepseek-v4-flash`, temperature 0, prompt in
`PROMPTS.md` §1) turns each passage into a content brief: setting, characters,
narrative stance (person and tense), target length in words, the events in
order, what the reader learns, and what the passage is doing in the story. It
is instructed to paraphrase every proposition in plain register, to quote
nothing, and to say nothing about the prose. Names are content and are kept.
Paragraph count and dialogue proportion are not given, because paragraphing and
the choice between direct and reported speech are decisions the author makes.

This is the neutralise-then-restyle pattern of STRAP [strap], which paraphrases
to strip style and then re-styles with a per-author inverse paraphraser, and of
Patel et al. [patel2022], who apply it to non-famous authors with LLMs. A brief
is a stronger neutralisation than a paraphrase: it removes lexis and syntax
entirely and leaves the model to reconstruct both. That is deliberate, because
the target use case is a writer handing a model an outline, not a draft.

The decomposer is a different model family from the generator. The Aug build
noted that a Qwen summariser feeding a Qwen generator can pass same-family
register through in ways n-gram checks cannot see (`CORPUS_REPORT.md` §7). The
same decomposer, prompt and temperature produce the training briefs in §7, so
train and test conditionals match.

### 3.2 Leakage gates

Each brief is tested before use. Gates a-d are hard: a failing brief is
regenerated with a stricter reminder, up to twice, then dropped and the drop is
logged. Gate e is reported, not enforced.

| gate | measure | threshold | reason |
|---|---|---|---|
| a | any word 6-gram shared with the source | 0 | quotation |
| b | fraction of the brief's word 4-grams present in the source | <= 0.03 | near-quotation |
| c | brief words / source words | <= 0.35 | a brief at 0.8 of the source is a paraphrase, not a brief; STRAP's whole point is the information bottleneck [strap] |
| d | style-descriptor scan: a fixed list of words about prose ("lyrical", "terse", "rhythm", "sentence", "vivid", "evocative", "prose", "tone", "voice", ...) | 0 | the Aug 4B summariser leaked a mood adjective in 12% of briefs; here it is a hard fail with regeneration |
| e | nearest-centroid attribution of the brief itself over the 14 author centroids (LUAR) | reported | with one author it is a diagnostic; across authors, attribution accuracy on briefs above chance means the briefs still carry author signal |

Gate a is the Aug `make_prompts.py` guard tightened from 5 to 6 words and paired
with b, which the old guard could not express.

## 4. Conditioning materials

All three are derived from TRAIN only and frozen with a content hash before any
generation.

### 4.1 Retrieval (A2)

Three exemplars per brief from the TRAIN pool, ranked by BM25 with the brief as
the query, one exemplar per work, each cut to its first 350 words on a paragraph
boundary. Content-similar retrieval mirrors what mimesis and every practical
RAG pipeline does, and it also gives the model domain vocabulary; random
exemplars are a later sub-arm. Exemplars never come from TEST or REF volumes,
which the split guarantees by construction rather than by filtering.

### 4.2 Qualitative guide (A3)

One guide per author, written once by an API model from twelve TRAIN passages
(prompt in `PROMPTS.md` §2), about 400 words, covering sentence rhythm, syntax
habits, diction, punctuation, figurative habits, paragraphing, dialogue
handling, and a short list of things the author does not do. The author is not
named in the guide. This is the natural-language style description that LISA
[lisa] showed is a usable interface between style and an LLM. It is the
"qualitative" component of mimesis.

### 4.3 Quantitative targets (A4)

Computed from TRAIN with the project's own surface instruments and rendered as
plain sentences with numbers (`PROMPTS.md` §3): mean and spread of sentence
length, share of sentences under 9 words and over 30, commas per sentence,
semicolons per hundred sentences, share of sentences carrying quoted speech,
mean paragraph length, distinct sentence openers per hundred sentences, and
dashes per hundred words. Nine features. These are the SHOWN set; §8.3 explains
why they are then excluded from the geometry outcome.

### 4.4 Full (A5)

A2 + A3 + A4 in one prompt, in that order. This is the mimesis principle
without its gate; the gate (best-of-n selection by a style verifier) is a later
arm because it needs a split verifier to avoid scoring on the selector.

### 4.5 Naming (A1)

The author's name and nothing else. A1 is a probe of parametric knowledge, and
it only means something for an author who is in the pretraining corpus. It is
the arm most papers on "write like X" actually test. For Patrick's corpus it is
undefined and is dropped.

A2-A5 do not name the author. The question those arms answer is what in-context
material does; naming would confound it with memory.

## 5. Arms

| arm | prompt content | what it isolates |
|---|---|---|
| A0 bare | brief | the model's default register on this content; the AI anchor for §8.3 |
| A1 named | brief + author name | parametric knowledge |
| A2 retrieval | brief + 3 exemplars | in-context imitation |
| A3 guide | brief + qualitative guide | described style |
| A4 quant | brief + numeric targets | instructed statistics |
| A5 full | brief + exemplars + guide + targets | the decomposed mimesis stack |
| F0 | A0 prompt to the frontier comparator | a large model with nothing |
| F5 | A5 prompt to the frontier comparator | a large model with the stack |

System prompt and output constraints are identical across arms (`PROMPTS.md`
§4). Only the user message changes.

## 6. Generation protocol

* Model: `Qwen/Qwen3-4B` instruct, bf16, chat template, thinking disabled (Qwen3.5-4B was the first choice; its linear-attention fast path has no Windows build, see `DECISIONS.md` G0 amendment).
  Any `<think>` block that appears anyway is stripped and the event counted.
* Sampling: temperature 0.8, top_p 0.95, no repetition penalty (a repetition
  penalty suppresses an author's real repetitions; Wharton's "and" chains and
  Austen's "very" are style), max_new_tokens = min(1,500, 2.2 x target tokens).
* Two samples per cell with seeds 0 and 1. Same seeds across arms.
* Post-processing: strip a leading title line or "Here is" preface if present
  and count it; strip trailing notes after a blank line that begin with a
  bracket or "Note". Every strip is logged per arm because instruction-following
  failure is a result, not noise.
* Exclusion: an output under 40% or over 200% of the target length is scored
  but flagged; the primary analysis includes it, a sensitivity analysis drops it.
  Exclusion rates per arm are reported.
* Adapter deployment check: before any adapter generation, one probe passage
  is scored with the adapter enabled and disabled (PEFT `disable_adapter`) and
  the mean per-token log-likelihood difference and the first 40 generated
  tokens are recorded to the run manifest. An adapter whose enabled and disabled
  outputs are identical is not deployed; this is the check the July pipeline
  did not have.

## 7. Adapter training

### 7.1 What went wrong before, precisely

`pipeline.train_user_lora`: concatenate all REF passages with EOS separators,
tokenise as one stream, cut into 512-token blocks, plain causal LM loss on every
token, 4-bit NF4 at every model size, alpha=2r; ~90 optimiser steps at 1.7B.
`scripts/train_lora.py`: same objective, alpha defaulting to r. Three separate
faults:

1. Objective. Loss on raw human prose with no conditional. POLARIS [polaris]
   is the direct measurement of that objective's effect on writing quality.
2. Segmentation. Blocks cut mid-sentence and across work boundaries, so the
   model learns to continue fragments and to start a new novel mid-paragraph.
   Suri [suri] documents truncated targets producing incomplete narratives.
3. Deployment. No check that the adapter changed anything at inference.

### 7.2 Recipes

Three adapters, identical hyperparameters, differing only in the training
conditional. The comparison is itself a result: it answers whether pairing the
loss to a content brief prevents the collapse that raw-target SFT produces.

| recipe | example | loss on | matches eval? |
|---|---|---|---|
| pair | A0 prompt (brief) -> passage, chat template | assistant tokens only | yes, exactly |
| mix | pair + continue (preceding 200-400 words -> passage) + infill (150 before, 150 after -> passage); 2 views per target per epoch, resampled | assistant tokens only | pair view matches; the others are zero-leakage augmentations by construction |
| raw-careful | the passage alone, whole, one example, EOS, no template | every token | no; this is the July objective done without faults 2 and 3 |

Pair is instruction backtranslation [humpback] with the brief as the generated
instruction and the author's passage as the fixed response; LongForm [longform]
built a general instruction set the same way from corpus text. The view
multiplicity in mix follows Allen-Zhu and Li [physics31]: a fact seen through one
phrasing is stored but not extractable, and several rewrites make it
extractable. Resampling two views per target per epoch keeps each passage's
exposure to roughly six passes over three epochs, below the duplication regime
where verbatim emission rises [lee2022].

If raw-careful writes as badly as July, fault 1 is confirmed as the cause. If
it writes as well as pair, the fault was segmentation and deployment and the
objective question is open. Either way the answer is measured rather than
assumed.

### 7.3 Hyperparameters

| setting | value | reason |
|---|---|---|
| base | Qwen3-4B instruct, bf16 | quantisation is a memory tool and 4B fits; NF4 dequantises on every matmul and gradient checkpointing pays it twice |
| LoRA | r=16, alpha=32, dropout 0.05, q k v o gate up down | alpha=2r cuts intruder dimensions, which correlate with forgetting [shuttleworth2024]; all-linear targets outperform attention-only [qlora]; r=16 is the Biderman et al. regime where LoRA matches full fine-tuning on style-level adaptation [biderman2024] |
| optimiser | AdamW, lr 1e-4, cosine, warmup 3%, weight decay 0 | Biderman et al. show LoRA's LR sensitivity; 1e-4 with alpha=2r is their stable setting |
| batch | 1 x accumulation 8, max_len 2048 | 16 GB card; prompt truncated from the left, target never truncated |
| epochs | 3, val loss every 20 steps, best checkpoint by val loss, patience 3 | selection is by held-out loss on TRAIN-val works; overfit is visible as val rising while train falls |
| seed | 0 | fixed; a second seed is a Gate 5 replication |
| checks | label-mask fraction, tokens per example, peak VRAM per step, adapter-active probe | logged to `run.json` |

With ~190 TRAIN passages, pair gives ~170 fit examples and ~17 val; three epochs
at effective batch 8 is ~65 steps. That is small, and it is the regime a writer
with one book has. Mix triples the example count at the same target exposure.

### 7.4 What is not done

No replay of general instruction data. Forgetting of instruction-following is
measured in §6 (strip and exclusion rates per adapter) rather than prevented,
because preventing it changes the recipe and the point of the test run is to
see the recipe's failure modes. If pair loses instruction-following at 4B, a
10% replay mix is the Gate 5 fix.

## 8. Outcomes

### 8.1 Instruments

All computed by `dr/s5_score.py`, which imports the overnight battery's family
functions unchanged so that the instrument is the one that was validated.

| family | instruments | reads |
|---|---|---|
| embedding | LUAR-MUD [luar], Wegmann [wegmann2022], StyleDistance [styledistance] | cosine to the source passage; cosine to the author REF centroid; cosine to the A0 centroid; nearest-centroid attribution over 14 authors |
| stylometric | Burrows's Delta [burrows2002, evert2017] on 150 function words, z-scored against the 14-author reference | Delta distance to own author, rank of own author |
| surface | sentence length mean/CV, short-sentence share, opener distinctness/entropy, commas per sentence, dash rate, staccato anaphora, short-run max | the SHOWN and SEALED halves are listed in 8.3 |
| syntax | cr_pos, MTLD, MATTR, template rate, open2 distinct | learned-instrument set from the overnight battery |
| degeneracy | distinct-3, rep-4, max repeat, sentence echo | collapse and looping |
| detection | Binoculars [binoculars], Fast-DetectGPT [fastdetectgpt] with the Qwen3.5-9B observer pair | machine-likeness; same-family caveat in §12 |
| memorisation | longest common word substring with the source; 8-gram overlap fraction | §8.5 |
| judge | two API judges, 2AFC | §8.6 |

### 8.2 Primary and secondary outcomes, pre-registered

Primary: LUAR cosine between the regeneration and its own source passage.
Same content on both sides, so the difference is style plus whatever the brief
lost. LUAR was the best-validated instrument in the overnight battery
(order-blind, 0.905 macro attribution) and nothing in any prompt refers to it.

Secondary, in order:

1. Geometry index on the SEALED feature set (§8.3).
2. LUAR nearest-centroid attribution to the target author (hit rate).
3. Delta rank of the target author.
4. Judge fooling rate against the source (§8.6).
5. Detector AUROC of arm outputs against REF.

Everything else is exploratory and labelled so.

### 8.3 The geometry index and the shown/sealed split

For each numeric feature f, with mu_author the mean over REF passages and mu_ai
the mean over A0 outputs for the same author:

    pos_f(x) = (f(x) - mu_ai) / (mu_author - mu_ai), clipped to [-1, 2]

REF scores 1 by construction, A0 scores 0. A feature is dropped from the index
when |mu_author - mu_ai| < 0.2 pooled SD, because it does not separate the
populations and its position is noise. The index is the mean of pos_f over the
retained SEALED features; overshoot is the share of features with pos_f > 1.25,
reported alongside, because caricature is the characteristic failure of style
prompting and a mean hides it.

The SHOWN set is the nine features written into the A4 and A5 prompts. Those
arms are optimising those numbers directly, so scoring on them is circular. The
index is therefore computed on the SEALED set only: cr_pos, MTLD, MATTR,
template rate, opener entropy, open2 distinct, staccato anaphora, short-run max,
distinct-3, rep-4, sentence echo, and the Delta distance. Compliance with the
SHOWN targets is reported separately as its own table (did the model hit the
numbers it was given), which is a different question from whether hitting them
moved the sealed instruments. This is the split-verifier rule from the field
report (D-cards, `notes/voice-retune-field-report-2026-09-02.md`) applied to
prompting rather than to reward.

### 8.4 Content fidelity

Not an outcome; a check. An API judge scores each output for coverage of the
brief's listed events (0-100). Reported per arm. An arm that scores well on
style by dropping the content is reported as such.

### 8.5 Memorisation

Longest common word substring between output and source, and the fraction of
the output's 8-grams present in the source. An output with a common substring
of 12 or more words is flagged as reconstructed; flagged outputs are kept in the
primary analysis and removed in a sensitivity analysis, and the flag rate per
arm is a result (it is the A1 result, mostly). Thresholds follow the extraction
literature's convention of 50-token verbatim runs scaled down to passage length
[carlini2023].

### 8.6 Judges

Two cheap API models from families other than the decomposer's (proposed:
`google/gemini-3.1-flash-lite-preview` and `openai/gpt-5-nano`). Each sees one
REF passage by the author and two candidates in random order and picks the one
by the same author. Two comparisons per output: against the source passage
(fooling rate; 0.5 means indistinguishable to that judge) and against the A0
output for the same brief (relative gain). Judge agreement is reported. Judges
are treated as instruments with a known bias toward machine prose (the sweep in
`notes/voice-retune-lit-blindspots-2026-09-02.md` collects that evidence); they
are a data point on who is fooled, not the criterion.

## 9. Analysis plan

* Unit: passage. Samples are averaged within a passage-by-arm cell before
  modelling; a second analysis keeps samples as a nested level.
* Model: outcome ~ arm + (1 | passage), fit by REML where `statsmodels` is
  available; otherwise a passage-level cluster bootstrap with 5,000 resamples.
  Both are run and reported when both are possible.
* Contrasts: each arm against A0 (what the conditioning buys) and against A1
  (what it buys over naming). Holm correction [holm1979] across the five
  contrasts of the primary outcome. Secondary outcomes are reported with
  unadjusted CIs and labelled.
* Effect size: paired Cohen's d on passage means.
* Power: 50 passages gives 0.80 power for paired d = 0.40 at alpha = 0.05
  two-sided. The overnight spectrum moved LUAR cosine by 0.028 (d roughly 0.3
  on that bank); an arm that matters here should move it by more than a
  training-set swap did.
* Adapter phase adds a model factor: outcome ~ arm * model + (1 | passage).
  The interaction is the question (does the adapter add on top of the best
  prompt).

## 10. Gates

| gate | what is produced | what Patrick sees | decision |
|---|---|---|---|
| G0 | this document, the prompts, the scaffold | the frame | author, model, arms, primary outcome |
| G1 | briefs for 10 TEST passages with gate stats | 3 briefs beside their sources | is the brief content-only; are the thresholds right |
| G2 | guide, quant block, retrieval sanity for 3 briefs | the guide, one full A5 prompt | is the material fair to the model |
| G3 | base run, 8 arms | the results table, 2 outputs per arm read blind | which arms survive; proceed to adapters |
| G4 | three adapters, val curves, probe outputs | curves, 5 generations per adapter read blind | which recipes deploy |
| G5 | adapter x arm run | the interaction table | is the adapter worth its cost |
| G6 | replication over 3 more authors | the cross-author table | proceed to Patrick's corpus |

A gate closes only on Patrick's word, recorded in `DECISIONS.md`.

## 11. Budget and runtime

| item | count | cost | time |
|---|---|---|---|
| briefs (TEST 50 + TRAIN ~190, with retries) | ~300 calls | < USD 0.30 | 10 min |
| guide | 1 call | < USD 0.05 | 1 min |
| frontier comparators F0/F5 | 200 calls | ~USD 0.30 | 10 min |
| judges (2 x 2 comparisons x 600) | ~2,400 calls | ~USD 1.50 | 40 min |
| local generation, base phase | 600 | - | ~1.5 h at 4B bf16 batched |
| adapter training, three recipes | 3 | - | ~20 min each |
| local generation, adapter phase | 1,800 | - | ~4.5 h |
| scoring | all | - | ~30 min, 9B detector pass dominates |

Total API under USD 3 per author. Pangram is not in this run.

## 12. Threats to validity

* Same-family detection. Generator is Qwen 4B, detector observer is Qwen 9B.
  Same-family pairs detect more easily. The detector outcome is fifth in the
  hierarchy for this reason and a cross-family observer is a follow-up.
* Brief information loss. A brief that omits an event makes the source and the
  regeneration differ in content, which every embedding reads partly as style.
  Held constant across arms by design; §8.4 measures it; the REF-centroid
  comparison is the content-independent backstop.
* Memorisation. §8.5. Wharton was chosen partly to reduce it; it cannot be
  removed for a public-domain author, which is why Patrick's corpus is the
  destination.
* Decomposer register. A different family from the generator, gates a-e, and
  the brief is short; residual register transfer is not excluded and is
  measured by gate e across authors.
* Sampling temperature. Fixed at 0.8 across arms; a temperature sweep on A0
  and A5 is a follow-up, since temperature alone moves surface features.
* Single author, single seed, single base. The test run is a test of the
  machinery and a first effect estimate. No claim leaves it until G6.

## 13. Not tested here

Best-of-n gating (needs a split verifier), random-exemplar retrieval, the
9B and 2B rungs, replay mixing, human raters, Patrick's own corpus, translated
authors, temperature.

## 14. Tracking

Every run writes `runs/<run_id>/manifest.json` with: content hashes of
`PROMPTS.md`, `dr/config.py`, the split file, the brief file and the
conditioning files; model ids and revisions; sampling parameters; the adapter
path and its `run.json`; wall time; and the command line. `dr/common.py`
refuses to start a stage whose upstream hashes do not match the manifest it is
reading from.

## 15. Amendments, 2026-09-05

**Text normalisation before scoring.** Every text that is embedded, judged
or shown to a rater is passed through `core.normalise_punct`: Gutenberg's
`--` becomes an em dash and `_italics_` loses its underscores. Reason: in
the pilot the real Wharton passages carried `--` in 53-68% and underscores
in 42-47% of texts and no model output carried either, so the encoding
alone separated real from generated. The primary shifts by +0.015 to
+0.032 uniformly under normalisation with every gap intact
(`runs/punct_sensitivity_wharton.md`); judge fooling rates on normalised
text stay within 0.03 of the raw ones. Raw-text results are retained as
`*_raw.*` files and reported as a sensitivity table.

**Cross-author transfer control (§8.7).** For each adapter, the shift in
cosine to the author's own REF centroid is compared with the shift toward
every other author's centroid. The Wharton adapter's shift toward Cather is
0.83 of its shift toward Wharton on LUAR (0.87 on Wegmann), so most of the
adapter's movement is shared period register; the author-specific residual
is reported separately (own shift minus mean same-period shift). With the
multi-author run this becomes a nearest-centroid attribution of each
adapter's outputs among the period authors, chance 1/k, which is the
author-specific outcome. The raw cosine gain is a register-plus-author
outcome and is labelled as such from here on.

**Recipe held fixed for replication.** Further authors run pair at 6
epochs, adapter arms A0, A1, A5, so the cross-author table has one adapter
column; mix is reported for Wharton and Patrick only until replicated.
