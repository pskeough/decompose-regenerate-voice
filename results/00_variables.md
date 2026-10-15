# Variable dictionary

Built by scripts/01_build_master.py. 63 of 64 dictionary variables are present in cells.parquet; eval-cache measures (per, otd_js, psd, cpd, lexdiv, event order, constructional) exist for arm A0 only.

| variable | label | construct | source | direction | order_sensitive | note |
|---|---|---|---|---|---|---|
| luar_cos_source | LUAR cosine to the source passage | voice_embed | scores.jsonl | + | False | primary in the pre-registration; content-inflated (same brief), see luar_cos_ref |
| luar_cos_ref | LUAR cosine to the author's reference set | voice_embed | scores.jsonl | + | False | content-free voice anchor |
| luar_cos_ai | LUAR cosine to generic AI prose | voice_embed | scores.jsonl | - | False |  |
| luar_attrib | LUAR attribution: author ranked first among reference authors | attribution | scores.jsonl | + | False | 1/0 per passage |
| luar_nearest | LUAR nearest reference author | attribution | scores.jsonl | 0 | False | categorical |
| wegmann_cos_source | Wegmann style-embedding cosine to the source | voice_embed | scores.jsonl | + | False | content-independent style embedding |
| wegmann_cos_ref | Wegmann cosine to the author's reference set | voice_embed | scores.jsonl | + | False |  |
| wegmann_cos_ai | Wegmann cosine to generic AI prose | voice_embed | scores.jsonl | - | False |  |
| wegmann_attrib | Wegmann attribution: author ranked first | attribution | scores.jsonl | + | False |  |
| styledist_cos_source | StyleDistance cosine to the source | voice_embed | scores.jsonl | + | False |  |
| styledist_cos_ref | StyleDistance cosine to the reference set | voice_embed | scores.jsonl | + | False |  |
| styledist_cos_ai | StyleDistance cosine to generic AI prose | voice_embed | scores.jsonl | - | False |  |
| styledist_attrib | StyleDistance attribution: author ranked first | attribution | scores.jsonl | + | False |  |
| geo_index | Sealed geometry index: position on the author-versus-AI feature axis (authors' own passages about 0.92, other authors 0.83, bare 4B generations 0.14) | voice_structure | scores.jsonl | + | True | higher = closer to the author (direction corrected 2026-09-10 from the data); coherence rows never enter it |
| delta_own | Burrows Delta to the author's own profile | voice_structure | scores.jsonl | - | False |  |
| delta_nearest | Burrows Delta to the nearest other author | attribution | scores.jsonl | 0 | False |  |
| delta_rank | Burrows Delta rank of the author among references | attribution | scores.jsonl | - | False | 1 = author is nearest |
| cr_pos | Clause-rhythm position (order-sensitive) | voice_structure | scores.jsonl | 0 | True | qualified at AUC 0.87-1.00; direction author-specific, use distance to the author's reference |
| open_entropy | Entropy of sentence-opener distribution | voice_structure | scores.jsonl | 0 | True | opener monotony instrument; AUC 0.82-1.00 |
| open_top_share | Share of sentences starting with the most common opener | voice_structure | scores.jsonl | - | True |  |
| open_distinct | Distinct sentence openers / sentences | voice_structure | scores.jsonl | 0 | True |  |
| open2_distinct | Distinct two-word openers / sentences | voice_structure | scores.jsonl | 0 | True |  |
| pct_short8 | Share of sentences of eight words or fewer | voice_structure | scores.jsonl | 0 | True | the one measure ordering all five blind grades on 2026-08-15 |
| sent_len_mean | Mean sentence length (words) | voice_structure | scores.jsonl | 0 | False |  |
| sent_len_cv | Coefficient of variation of sentence length | voice_structure | scores.jsonl | 0 | False |  |
| short_run_max | Longest run of consecutive short sentences | voice_structure | scores.jsonl | - | True |  |
| staccato_anaphora | Anaphoric short-sentence runs | tell | scores.jsonl | - | True |  |
| template_rate | Rate of templated constructions | tell | scores.jsonl | - | True |  |
| mattr | Moving-average type-token ratio (window 50) | voice_structure | scores.jsonl | 0 | False | lexical diversity; adapters narrow it |
| mtld | Measure of textual lexical diversity | voice_structure | scores.jsonl | 0 | False |  |
| distinct_3 | Distinct trigram ratio | construction | scores.jsonl | + | False | length-contaminated (rho with words -0.44) |
| rep_4 | Repeated 4-gram rate | construction | scores.jsonl | - | False | length-contaminated |
| sent_echo | Sentence echo: near-duplicate sentence share | construction | scores.jsonl | - | True | uncapped degeneracy row; PER (600-word cap) is the primary coherence row |
| max_repeat | Longest repeated span | construction | scores.jsonl | - | False |  |
| memo_8gram | 8-gram overlap with the author's training text | tell | scores.jsonl | - | False | copying / memorisation |
| memo_lcs | Longest common substring with training text | tell | scores.jsonl | - | False |  |
| memo_flag | Memorisation flag | tell | scores.jsonl | - | False |  |
| commas_per_sent | Commas per sentence | voice_structure | scores.jsonl | 0 | False |  |
| em_dashes_per_100w | Em dashes per 100 words | voice_structure | scores.jsonl | 0 | False | glyph fold applied in eval measures |
| words | Generated words | length | scores.jsonl | 0 | False |  |
| len_ratio | Generated / target word ratio | length | scores.jsonl | 0 | False |  |
| n_sent | Sentence count | length | scores.jsonl | 0 | False |  |
| truncated | Hit the token cap | length | gens flags | - | False | gate: <= 20% per run on Qwen; reported not gated on Ministral |
| preface | Preface / meta text before the passage | tell | gens flags | - | False |  |
| shown_dist | Distance of the passage from the shown style numbers | adherence | scores.jsonl | - | False | compliance on A4/A5 only |
| per | Proposition-echo rate (600-word cap): share of sentence pairs restating each other | construction | eval cache per_A0_cap600 | - | True | S6; PASS; item-1 coherence +0.95 |
| per_uncapped | Proposition-echo rate, uncapped | construction | eval cache per_A0 | - | True | length-contaminated, kept for the length null |
| otd_js | Opener-class distance (sqrt JSD of fronting-class distribution vs the author's reference) | voice_structure | eval cache otd_A0 | - | True | S4; PASS; ratio 13.7 |
| para_cv_words | Paragraph-length coefficient of variation | voice_structure | eval cache psd_A0 | 0 | False | S2; architecture outcome, not quality |
| cv_diff | Paragraph CV difference from the source | voice_structure | eval cache psd_A0 | 0 | False |  |
| w1_logpara | Wasserstein-1 of log paragraph lengths vs the source | voice_structure | eval cache psd_A0 | - | False |  |
| burst_an_diff | Corrected burstiness A_n difference from the source | voice_structure | eval cache cpd_A0 | 0 | True | S3; PASS ratio 10.4 |
| cpd_z | Cadence z-score vs the author | voice_structure | eval cache cpd_A0 | - | True |  |
| hapax_w300 | Hapax share in 300-token windows | voice_structure | eval cache lexdiv_A0 | 0 | False | S8; PASS; adapters narrow vocabulary |
| tau | Kendall tau-a of brief event order in the passage | adherence | eval cache event_order_A0 | + | True | S7 exploratory; ceiling 0.75 on the authors' own passages |
| terminal_missing | Last brief event missing from the passage | adherence | eval cache event_order_A0 | - | True | usable flag |
| events_present | Share of brief events found | adherence | eval cache event_order_A0 | + | True |  |
| arti_w | Constructional tell index, winsorised (AI-typical constructions per 1k words, z vs the author) | tell | eval cache constructional_A0 | - | True | S5; marginal as an aggregate; per-feature table is the instrument |
| rfpd_w | Rhetorical-figure profile distance, winsorised | voice_structure | eval cache constructional_A0 | - | True |  |
| coverage | Brief coverage judged (share of brief items present) | adherence | coverage.jsonl | + | False | LLM judge on sample 0 |
| fool_vs_source | 2AFC: judge picked the generation over the author's own passage | judge | judge.jsonl | + | False | sample 0; two judges |
| win_vs_A0 | 2AFC: judge picked this arm over the A0 arm | judge | judge.jsonl | + | False |  |
| rubric_C | Rubric construction block mean (C1-C5) | construction | eval_results/judge | + | False | shuffle-test validated; report relative to the author's calibration items |
| rubric_S | Rubric craft block mean (S1-S7) | judge | eval_results/judge | + | False | judges rank the 14B base above the private author; never absolute |

## Keys

run, author, family (Qwen3 / Ministral3), params_b, tag, kind (base / adapter), replicate, arm (A0-A5), id (brief), sample (0/1).

## Counts

| family | kind | cells |
|---|---|---|
| Ministral3 | adapter | 2808 |
| Ministral3 | base | 6120 |
| Qwen3 | adapter | 10872 |
| Qwen3 | base | 20926 |

| arm | cells |
|---|---|
| A0 | 8682 |
| A1 | 6872 |
| A2 | 5526 |
| A3 | 5526 |
| A4 | 5526 |
| A5 | 8594 |