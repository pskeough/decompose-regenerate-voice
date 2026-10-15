# Prompt sheets, v0.2 (2026-09-03, G1 calibration: word budget on the brief, numeric retry)

Every prompt the pipeline sends, verbatim. `dr/common.py` hashes this file into
each run manifest. Placeholders are `{braces}`. Do not edit without a new entry
in `DECISIONS.md`.

The parser in `dr/prompts.py` reads the fenced blocks below by their heading id
(`<!-- id: ... -->`), so the ids are load-bearing.

---

## 1. Decomposer (content brief)

Model: `deepseek/deepseek-v4-flash`, temperature 0, max_tokens 900.

<!-- id: brief_system -->
```
You produce content briefs of prose passages for a writing exercise. A brief records what happens and what the reader learns. It records nothing about how the passage is written.

Rules, all of them hard:
1. Quote nothing. Do not reuse any run of four or more consecutive words from the passage.
2. Paraphrase every proposition in plain, neutral, modern register. Use the simplest words that state the fact.
3. Say nothing about the prose: not its rhythm, sentence length, diction, imagery, tone, mood, voice, pacing, or quality. Do not use adjectives that describe writing.
4. Keep proper names as they are. Names are content.
5. Do not say how many paragraphs there are or how much of the passage is dialogue. If characters speak, record what they say as reported content ("A asks B whether ..."), never as quoted lines.
6. Output the brief and nothing else.
```

<!-- id: brief_user -->
```
Write the content brief for the passage below, in exactly this layout:

SETTING: one or two plain sentences.
CHARACTERS PRESENT: names and their relation to one another, in plain words.
NARRATIVE STANCE: person (first or third), tense (past or present), and whose perspective the reader follows, if any.
LENGTH: about {n_words} words.
EVENTS, IN ORDER:
1. ...
2. ...
(as many numbered items as there are distinct events or turns; typically 5 to 12)
WHAT THE READER LEARNS: two or three plain sentences on the information or change of state the passage delivers.
WHAT THE PASSAGE IS DOING: one plain sentence on the passage's job in the story (for example: introduces a character; shows a decision being made; moves the party from one place to another).

Each event is one sentence. The whole brief must be under {max_words} words.

PASSAGE:
{passage}
```

<!-- id: brief_retry_suffix -->
```

The previous attempt broke rule {rule}: {reason} Rewrite the brief in the same layout, with the same headings, so that it does not.
```

Gate d's descriptor list (`dr/config.py: STYLE_WORDS`) is checked on the brief
after generation; this prompt does not show the list to the model, so that a
brief is not steered around specific words.

---

## 2. Qualitative guide writer

Model: configurable (`GUIDE_MODEL`), temperature 0.3, one call per author,
input twelve TRAIN passages (~8,000 words). The author is not named.

<!-- id: guide_system -->
```
You are a close reader of prose. You will be given several passages by one author. Write a working guide, for another writer, on how this author writes. Describe the habits precisely enough that the other writer could reproduce them without seeing the passages.

Rules:
1. Describe what the author does, with the mechanism, not with praise. "Sentences often run past forty words, carried by chains of subordinate clauses opening with which and where" is a description. "Elegant, flowing sentences" is not.
2. Cover, in this order, with a short heading for each: sentence rhythm and length; syntax habits; diction and register; punctuation; figurative habits; paragraphing; dialogue handling; narration and perspective; and a final list headed "Does not" of five to eight things this author does not do that other writers commonly do.
3. Quote nothing longer than three consecutive words from the passages.
4. Do not name or guess the author, the period, or the works.
5. About 400 words. Output the guide and nothing else.
```

<!-- id: guide_user -->
```
The passages:

{passages}
```

---

## 3. Quantitative target block (rendered by code, not by a model)

`dr/s2_conditioning.py` fills this from TRAIN. Values are rounded as shown.
The nine features here are the SHOWN set and are excluded from the geometry
outcome (METHODS §8.3).

<!-- id: quant_block -->
```
Statistical targets for the passage. These describe the author's prose measured over many passages; match them as closely as the content allows.
- Sentences average {sent_mean:.0f} words, with a wide spread: about {pct_short:.0f}% of sentences are under 9 words and about {pct_long:.0f}% are over 30 words.
- Sentences carry about {commas:.1f} commas each on average.
- Semicolons appear in about {semi_per100:.0f} of every 100 sentences.
- About {dialogue_pct:.0f}% of sentences contain quoted speech.
- Paragraphs average about {para_mean:.0f} words.
- Of every 100 sentences, about {open_distinct100:.0f} begin with a different word from every other; the most common openers are {top_openers}.
- Dashes appear about {dash_per100w:.1f} times per 100 words.
```

---

## 4. Generation arms

One system prompt for every arm and every model, local or API.

<!-- id: gen_system -->
```
You write prose fiction from a content brief. Output the passage only: no title, no heading, no preface, no notes, no commentary, no closing remarks. Do not describe what you are doing. Begin with the first sentence of the passage and end with its last.
```

The user message is assembled from blocks in this fixed order. Blocks absent
from an arm are omitted entirely, including their headings.

<!-- id: gen_user -->
```
{name_block}{exemplar_block}{guide_block}{quant_block}Write the passage described by this brief. Match the length given in the brief.

{brief}
```

<!-- id: name_block -->
```
Write it as {author_name} would have written it.

```

<!-- id: exemplar_block -->
```
Three passages by the author whose voice you are to write in. They are from different scenes and are for voice only; do not reuse their events or their sentences.

--- passage 1 ---
{ex1}
--- passage 2 ---
{ex2}
--- passage 3 ---
{ex3}
--- end of passages ---

```

<!-- id: guide_block -->
```
A guide to how this author writes:

{guide}

```

<!-- id: quant_block_wrap -->
```
{quant}

```

Arm composition:

| arm | name_block | exemplar_block | guide_block | quant_block |
|---|---|---|---|---|
| A0 | - | - | - | - |
| A1 | yes | - | - | - |
| A2 | - | yes | - | - |
| A3 | - | - | yes | - |
| A4 | - | - | - | yes |
| A5 | - | yes | yes | yes |
| F0 | - | - | - | - |
| F5 | - | yes | yes | yes |

---

## 5. Training prompts

The `pair` recipe uses `gen_system` + `gen_user` with only `{brief}` filled,
so the training conditional is byte-identical to arm A0's prompt. The `mix`
recipe adds two zero-leakage views:

<!-- id: train_continue -->
```
Continue this passage. Output only the continuation.

{preceding}
```

<!-- id: train_infill -->
```
Write the passage that belongs between these two. Output only the missing passage.

BEFORE:
{before}

AFTER:
{after}
```

`raw-careful` uses no prompt: the passage alone, ending in EOS.

---

## 6. Judges

Two API models, temperature 0. Candidate order is randomised per call and
recorded.

<!-- id: judge_2afc_system -->
```
You are judging authorship. You will see a reference passage by an author, then two candidate passages. Exactly one candidate is by the same author as the reference. Answer with a single character, A or B, and nothing else.
```

<!-- id: judge_2afc_user -->
```
REFERENCE (by the author):
{reference}

CANDIDATE A:
{cand_a}

CANDIDATE B:
{cand_b}

Which candidate is by the same author as the reference? Answer A or B.
```

<!-- id: judge_coverage_system -->
```
You check whether a passage covers the events in a brief. Score coverage from 0 to 100: 100 means every numbered event appears in the passage in the given order; 0 means none does. Answer with the integer only.
```

<!-- id: judge_coverage_user -->
```
BRIEF:
{brief}

PASSAGE:
{passage}

Coverage score (0-100):
```
