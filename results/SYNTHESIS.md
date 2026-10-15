# Synthesis: what the decompose-regenerate data support (2026-09-10, updated 2026-09-11 after the overnight close of data collection and the DeepSeek V4 Pro comparator at 11:23)

This document collects the findings that hold across the sixteen analysis scripts in this
workspace, states how each should be read, and lists what the data cannot say. Every number
below is copied from a table in `analysis/<script>/` and names that table. The script's own
README carries the full method, the tables and the conservative reading for each. Nothing
here is typed from memory; where a number is quoted it can be found in the named csv.

## 1. The design behind the tables

The question: when a small language model is adapted to one author, what does each mechanism
(prompting arms A0-A5, a pair-6 LoRA adapter), each parameter count, each model family and
each corpus buy in voice, in construction, in adherence to the brief and in detectability,
and which instruments can see it.

Data on disk (`data/master/runs.csv`, `authors.csv`, `schema.json`):

| item | count |
|---|---:|
| main runs | 110 (Qwen3: 46 base, 42 adapter; Ministral 3: 13 base, 9 adapter) |
| replicate runs (the same configuration generated twice) | 10: Qwen3 at 4B (three), 8B and 14B (one each); Ministral 3 at 3B (two), 8B and 14B (one each) |
| authors | 13 usable (6 period, 5 contemporary, 3 private) plus `patrick` (the v1 chunking control) |
| test briefs passed | 546 of 635 |
| generated passages (cells) | 40,726 |
| main analysis set (arm A0, non-replicate, base and adapter) | 7,876 |
| runs with 2AFC judge and coverage records | 108 of 110, both families, both judges, sample 0; rubric records for every Ministral run and every series run |
| within-author corpus-size series | 16 runs: Chesterton 25/50/100/150 briefs; doctorow 25/50/100/150/215/300/525 plus 50 with a second seed; patrick_v2 25/50/75 plus 50 with a second seed |
| frontier comparator runs | 40: deepseek-v4-flash-0731 (F0 and F5) on 14 authors, gpt-5.6-luna (F0) and deepseek-v4-pro (F0) on the 13 usable authors |
| adapter serving | 42 LoRA (Qwen3), 9 merged weights (Ministral 3) |

Parameter counts: Qwen3 1.7B, 4B, 8B, 14B; Ministral 3 3B, 8B, 14B. Ministral covers three
authors only (chesterton, doctorow, patrick_v2). Training briefs per author run from 25
(sui_sin_far) to 525 (doctorow), capped at 1,290 fit examples. Qwen3 1.7B exists for one
author (patrick_v2) and is excluded from every pooled claim below.

## 2. Conventions every number below obeys

- Authors are the unit of replication for any claim about a model, a size or a family; briefs
  are the cluster within an author. A pooled estimate is a bootstrap over authors; a
  within-author estimate is a cluster bootstrap over briefs.
- Every adapter-versus-base contrast is read against the replicate floor of its measure: the
  largest absolute mean difference between two generations of the same run with the same
  settings (`10_inventory_integrity/replicate_floors.csv`). A contrast under its floor is
  "within noise" whatever its p-value. The Qwen3 floors rest on five pairs (three at 4B, one
  each at 8B and 14B) and the Ministral floors on four (two at 3B, one each at 8B and 14B), so
  no floor is borrowed across sizes.
- p-values are BH-FDR adjusted within each script's family of tests; "survives" means q < 0.05
  in that family. Script 22 applies a second, programme-wide correction across 4,420
  harvested contrasts and reports what survives that stricter layer.
- Judge scores (rubric, 2AFC win and fool rates, coverage) are relative instruments, never
  absolute quality. Two judges are not one instrument.
- Eval-cache measures (proposition echo, event order, paragraph shape, cadence, lexical
  diversity, constructional features) and rubric subscores exist for arm A0 only.
- A single generated passage is about half sampling noise: the sample-0 versus sample-1
  Spearman over briefs within a run has a median of 0.53 for StyleDistance, 0.41 for LUAR,
  0.24 for proposition echo and 0.10 for truncation (`10_inventory_integrity/test_retest_summary.csv`).
  Cell-level claims below are always aggregates over briefs and samples.

## 3. Data caveats established today (LOG.md; FIDELITY_SYNTHESIS.md, Amendments)

1. The stranger pool used by the pipeline is fourteen period authors for every study author.
   Contemporary and private authors were therefore positioned against a different century.
   Script 23 builds a register-matched pool from the stored embeddings; the positions it
   gives those authors are lower than the pipeline's, by more than the adapter gain in most
   cells (section 5.N). Period authors cannot be positioned against their own class with the
   data on disk.
2. The per-run embedding files (`emb_*.npy`) are not row-aligned with `scores.jsonl` in 76 of
   127 run directories: an anchor block of 2 x n_test_briefs rows sits between the generations
   and the reference rows. Script 23 applies the repair; it reproduces every stored cosine to
   1e-4 in 103 of 103 runs checked (`23_register_matched_pool/alignment_check.csv`). Any
   analysis that reads the npy files row-for-row without it mislabels every reference
   embedding in those runs.
3. Proposition echo is close to permutation-invariant. The sentence-shuffled author floor
   prescribed in FIDELITY_SYNTHESIS section 2 fails its own manipulation check (for cather the
   W1 distance shuffled-versus-author is 0.0034 against 0.0184 for strangers-versus-author,
   `24_reference_measures/shuffle_manipulation_check.csv`), so no fidelity value F may be
   quoted for proposition echo; raw rates and region membership only.
4. The event-order tau ceiling on the authors' own passages is 0.57 (sui_sin_far) to 0.83
   (stross), mean about 0.75 (`24_reference_measures/event_order_ceiling.csv`). A generated
   passage cannot be expected to exceed it.
5. Ten Qwen3 runs' coverage and 2AFC records were error rows from the 2026-09-09 credit
   outage; they were re-judged on 2026-09-10. The Ministral family was judged on 2026-09-10/11
   with the same judges, prompts and sample-0 protocol as Qwen. Chesterton's deepseek frontier
   run had been scored on 2026-09-05 with 8 of its 39 briefs; it was rescored on 2026-09-11.
6. `doctorow_basem8b` exceeds the 20% truncation gate and is flagged, not
   excluded. `chesterton_paire6_m8b` has a positive probe delta (the adapter changed nothing
   measurable on held-out loss) and is in the tables as an adapter run.
7. Thirteen authors, not the number of tests, is the limit of the study (section 5.M).
8. Three of thirteen integrity flags fail, all documentation gaps rather than data faults: 7
   runs over the truncation gate carry no pod verdict, 18 local runs carry no provenance
   block, 6 runs record no sampling temperature (`10_inventory_integrity/integrity_flags.csv`).

## 4. The one-paragraph answer

Across thirteen authors the pair-6 adapter moves a Qwen3 model toward the author on the
embedding instruments and away from the brief on construction and adherence, at every
parameter count, and the size of the model does not change either effect. What changes both
is the corpus: the voice gain and the adherence loss track the number of training briefs,
with the loss shrinking past roughly 50 to 110 briefs. No prompt matches the adapter's voice
gain: showing the model the author (the name, three retrieved exemplars) buys a small
above-floor gain, about sixty percent of the 4B adapter's LUAR gain at a fifth of its
adherence cost, while describing the author (the style guide, the quantitative block) is inert
or harmful; the adapter cannot keep the adherence that every prompt keeps (sentence revised
2026-09-11 12:46 after R1 and R9 read the arm tables; the earlier wording said prompting cannot
buy the voice gain at all). The second family replicates the
direction of every effect on three authors, with a smaller voice gain that shrinks with
size, and on the private author the adapter does nothing the embeddings can see in either
family. Against three hosted models (deepseek-v4-flash, gpt-5.6-luna, deepseek-v4-pro), the
4B adapter matches them on the embedding instruments once the corpus passes about a hundred
briefs and loses to them below fifty, while the hosted models keep the brief (44 to 45
coverage points ahead), never truncate, and are picked over the source more often by the
2AFC judges. The three hosted models sit within a floor of one another on every voice
instrument, so the hosted price tier buys no voice. The instruments disagree with
one another often enough, and the judges with each other always, that no single number
should be quoted as "fidelity".

## 5. Findings that survive across scripts

Each finding names the scripts that carry it and the table with the number. "Authors" is
the count behind a pooled estimate.

### A. What the adapter buys and what it costs (scripts 11, 14, 19, 22)

Brief-paired adapter-minus-base differences, arm A0, Qwen3, pooled over authors
(`11_scale_curves/gain.csv`, aggregated by measure x size; floors from `floors.csv`):

| measure (direction) | 4B, 14 authors | 8B, 13 | 14B, 13 | floor | surviving cells (4B/8B/14B) |
|---|---:|---:|---:|---:|---|
| LUAR cosine to source (+) | +0.049 | +0.066 | +0.046 | 0.023 | 10 / 10 / 11 |
| StyleDistance cosine to source (+) | +0.029 | +0.027 | +0.017 | 0.011 | 11 / 11 / 10 |
| Wegmann cosine to source (+) | +0.017 | +0.026 | -0.027 | 0.041 | 10 / 9 / 8, pooled means inside the floor |
| proposition echo, per (-) | +0.052 | +0.117 | +0.111 | 0.010 | 7 / 13 / 13 |
| coverage, judged (+) | -27.4 | -33.3 | -34.3 | 1.97 | 14 / 13 / 13 |
| truncated share (-) | +0.085 | +0.143 | +0.279 | 0.012 | 6 / 8 / 10 |
| hapax share (0) | -0.056 | -0.097 | -0.110 | 0.015 | 13 / 13 / 13 |

The random-effects pool over authors agrees (`19_author_heterogeneity/pooled_dl.csv`): LUAR
source +0.054 [0.022, 0.086] at 4B, +0.067 [0.036, 0.098] at 8B, +0.048 [0.019, 0.077] at
14B; proposition echo +0.048, +0.101, +0.081; coverage -27.9, -32.9, -33.4. On the two
composite axes of script 14 (`author_level_tests.csv`, 13 authors per size) the construction
axis falls by -0.28 [-0.47, -0.13] at 4B, -0.46 [-0.74, -0.26] at 8B and -0.46 [-0.72, -0.27]
at 14B with at most one author moving the other way (sign-test q <= 0.012), while the voice
axis rises by +0.17, +0.15 and +0.02 with intervals that span zero (q >= 0.41). The
programme-wide correction leaves these standing: of the 599 author-level gain contrasts in
script 11, 459 survive both the own-script and the programme q and clear their floor
(`22_multiple_comparisons_and_sensitivity/survival_summary.csv`).

How to read it. The voice gain is real in the pooled sense and unreliable in the individual
sense: of the 40 LUAR author-size cells at 4B and above, 31 are positive, 27 have an interval
above zero, and 6 have an interval below zero (cather, link, patrick, patrick_v2 and
sui_sin_far each appear among the negatives). The construction and adherence losses are the
more uniform effect: no author escapes the coverage loss at any size. Wegmann does not see a
pooled adapter effect above its own floor at any size.

### B. Parameter count buys the base model adherence and buys the adapter nothing (scripts 11, 19)

Mixed models of the brief-paired gain on log2(parameters) with the author as a random effect
(`11_scale_curves/tests.csv`, 14 groups): none of the 12 gain slopes survives correction
(smallest q 0.155, geo_index). Per-author OLS slopes agree (`slopes_summary.csv`, 13 Qwen
authors): the LUAR gain changes by -0.002 [-0.008, +0.003] per doubling; the truncation cost
grows by +0.097 [0.032, 0.180] per doubling (10 of 13 authors positive), the proposition-echo
cost by +0.031 [0.012, 0.054] (11 of 13) and the opener-distance cost by +0.033 [0.025, 0.042]
(13 of 13). What size does buy is the base level: base coverage rises 6.4 points per doubling
[5.5, 7.4] and base truncation 0.062 [0.049, 0.075], both q < 0.001; the adapter level of
coverage rises 4.9 per doubling [3.4, 6.4], so the adapter keeps pace without closing the gap.
Author rankings on the voice instruments are the same at every size (Spearman between sizes
0.94 to 0.99 for LUAR and StyleDistance, 0.77 to 0.92 for Wegmann;
`19_author_heterogeneity/rank_stability.csv`, 13 authors).

How to read it. "Flat in parameters" is a null on 13 authors with wide intervals; the 8B point
estimate for LUAR is the largest at every level of aggregation but its interval overlaps
both neighbours. The one size effect that is not a null is on the cost side: larger Qwen
adapters truncate more (pooled truncation share 0.083, 0.118, 0.292 at 4B, 8B, 14B;
`pooled_dl.csv`).

### C. Corpus size is the moderator that survives (scripts 13, 19, 25)

Across 14 corpora (patrick v1 included) the adapter's improvement correlates with the number
of training briefs, pooled over Qwen sizes (`13_corpus_data_effects/gain_vs_corpus_spearman.csv`):
coverage rho 0.86 [0.54, 0.97], StyleDistance 0.81, truncation 0.80, proposition echo 0.77,
LUAR source 0.72 [0.24, 0.95], geo_index 0.73, opener distance 0.72, Wegmann 0.70, LUAR
reference 0.59 [0.07, 0.91]; all q <= 0.04. The meta-regression on log2(fit examples) gives
the same answer at every size (`19_author_heterogeneity/metareg_train_examples.csv`, 13
authors): LUAR source +0.043, +0.040, +0.040 per doubling (q <= 0.008), proposition echo
-0.065, -0.077, -0.068 (q < 0.001), coverage +8.6, +15.0, +16.7 points. With size, family and
author class in the same model (`metareg_multi.csv`), log2(fit examples) keeps its sign and
interval (+0.039 [0.023, 0.054] on LUAR source), log2(parameters) is +0.002 [-0.016, +0.020],
and neither author-class term excludes zero.

A piecewise fit locates the bend (`13_corpus_data_effects/gain_piecewise_breakpoint.csv`,
permutation p corrected over the nine measures searched): the coverage loss flattens between
56 and 111 briefs, proposition echo between 43 and 115, truncation between 66 and 113, opener
distance between 46 and 100, geo_index between 40 and 178; the LUAR, StyleDistance and
Wegmann gains show no identified breakpoint (bootstrap range 34 to 200 briefs, q >= 0.12), so
for the embedding gain a log-linear description is the honest one: +0.036 [0.014, 0.054] LUAR
reference per doubling of briefs (`gain_loglinear_fits.csv`, r2 0.49).

Within one author the same curve appears. Chesterton adapters trained on 25, 50, 100, 150
and all 235 briefs at 4B (`25_series_and_frontier/size_series.csv`, arm A0, 39
briefs, brief-paired): LUAR gain +0.022 [-0.008, +0.051] at 25 briefs, +0.085 at 50, +0.103 at
100, +0.102 at 150, +0.119 at 235; coverage -58.8 at 25, -26.2 at 50, -24.9 at 100, -16.6 at
150, -11.3 [-19.4, -3.6] at 235; truncation 0.27 at 25 falling to 0.03 at 235. Wegmann does not
clear its floor until the full corpus (+0.064 [0.017, 0.110]).

The same curve appears in the two series added on 2026-09-10, one contemporary and one
private author (`25_series_and_frontier/size_series.csv`, arm A0, seed-0 points; the existing
capped adapters are excluded from this table):

| training briefs | doctorow LUAR gain | doctorow coverage | patrick_v2 LUAR gain | patrick_v2 coverage |
|---:|---:|---:|---:|---:|
| 25 | -0.041 | -58.2 | -0.111 | -37.5 |
| 50 | +0.068 | -33.4 | 0.000 | -23.2 |
| 75 / 100 | +0.078 | -23.2 | -0.002 | -18.2 |
| 150 | +0.083 | -16.4 | | |
| 215 | +0.091 | -19.9 | | |
| 300 | +0.086 | -22.2 | | |
| 525 | +0.088 | -15.6 | | |

Doctorow's voice gain is bought by 50 briefs and flat from 100 to 525; the 300 and 525
points sit above the sweep's 1,290-example cap and add nothing, so the cap did not limit the
main sweep. The adherence cost shrinks to about 150 briefs and then stops, for both authors,
where it stopped for Chesterton. Patrick's adapter has no LUAR gain at any size, with a loss
at 25, so the embedding-blind private author is a property of the corpus and not of one
adapter. Two adapters trained on different draws of 50 briefs
(`size_seed_replicates.csv`) differ by 0.001 (doctorow) and 0.018 (patrick_v2) on LUAR,
inside the 0.023 floor, but by 4 to 10 coverage points, outside its 2-point floor: the
adherence curve carries real subset noise at the small end.

How to read it. Corpus size is confounded with author identity (each author has one corpus
size) and with class (the largest corpora are contemporary). The three series are one author
each at one size, one per author class, all at 4B, and cannot be pooled. The breakpoints are
located on 13 points and the bootstrap ranges are wide; "50 to 150 briefs" is the interval,
not a threshold.

### D. Prompting and adapters buy different things (script 12)

Across 144 measure x size cells the bare brief (A0) has the best mean rank of the six
prompting arms (2.95; `12_arm_effects/arm_rank_summary.csv`), the quantitative style block A4
the worst on voice (mean rank 4.80 of 6 on the voice measures) and the style guide A3 the
worst overall (4.30). At Qwen3 14B pooled over 13 authors (`arm_contrasts_pooled.csv`), A4
lowers LUAR by -0.047 [-0.054, -0.040], StyleDistance by -0.037 and Wegmann by -0.065; A3
lowers Wegmann by -0.067 and geo_index by -0.18; the author's name alone (A1, 11 authors)
raises LUAR by +0.019 [0.013, 0.025] and retrieved exemplars (A2) by +0.015, with Wegmann
+0.022. No arm moves coverage at 14B by more than one point (floor 2 to 5 points).

Against the adapter (`prompt_vs_adapter_pooled.csv`), the bare-brief base beats the adapter on
coverage by 27.5 [21.4, 35.0] points at 4B (14 authors), 33.3 at 8B and 34.3 at 14B, and by
0.03 to 0.10 on the lexical-diversity gap (`best_prompt_vs_adapter.csv`); the adapter beats
every prompt on the embedding measures (section A). Conditioning on top of the adapter costs
more coverage (A5 on adapter: -19.5 [-23.2, -15.5] at 4B, -18.3 at 8B, -11.3 at 14B, 13
authors; `adapter_arm_contrasts_pooled.csv`) and adds nothing on the embeddings that survives
correction. The arms that state the author's numbers (A3, A4) leave the generations further
from those numbers than A2 or A5 do (`compliance_shown_dist.csv`, Qwen: 2.67 and 2.58 against
1.54 and 1.63).

How to read it. Arm rankings depend on the denominator (A1 exists for 11 authors) and
`mean_rank` and `times_best` pick different winners; the construction verdict rests mostly on
n-gram measures that correlate with length. The prompt-versus-adapter coverage gap is the
most robust single contrast in the study: it clears its floor by more than ten times at every
size and no author reverses it.

### E. The second family replicates the direction and not the size (script 18)

On the three shared authors (`18_cross_family/adapter_gain_paired.csv`, brief-paired, floors
per family): the Chesterton adapter gains +0.119, +0.129, +0.105 LUAR source on Qwen3 4B, 8B,
14B and +0.068, +0.049, +0.042 on Ministral 3B, 8B, 14B; Doctorow +0.093, +0.110, +0.077
against +0.045, +0.035, +0.024; patrick_v2 is within noise on Qwen (+0.001, +0.012, -0.001)
and negative on Ministral (-0.034, -0.019, -0.014). The Qwen-minus-Ministral gain difference
for Chesterton is +0.051 [0.016, 0.085], +0.080 and +0.063 (`cross_family_gain_diff.csv`),
above the larger family floor at every rung. The losses travel: hapax falls in both families
(Chesterton -0.065 to -0.128 Qwen, -0.171 to -0.185 Ministral) and proposition echo rises in
both. The Ministral bases start closer to the author (Chesterton base LUAR is higher on
Ministral by 0.041 to 0.067; `base_family_diff.csv`), and the adapter endpoints are
equivalent within the floor for LUAR at the small and large rungs (TOST,
`tost_adapter_endpoints.csv`: 24 of 54 voice and construction endpoint tests equivalent, 6
different, 24 undecided). The Ministral adapters shorten output (len_ratio 1.11 base to 0.94
adapter) where the Qwen adapters lengthen it (0.95 to 1.09), and the Ministral 14B adapters
truncate less than their bases (-0.171, 3 authors) where the Qwen adapters truncate more.
Probe deltas are smaller by a factor of four (mean -0.14 against -0.59; `family_summary.csv`).

With judges on both families (`18_cross_family/judged_adapter_minus_base.csv`, three shared
authors, brief-paired, each family's own coverage floor): the Qwen adapters lose 16.6 [12.3,
20.7], 14.8 and 16.8 coverage points at 4B, 8B and 14B against a floor of 1.97; the Ministral
adapters lose 4.4 and 4.3 points at 8B and 14B and gain 1.7 at 3B, all inside the Ministral
coverage floor of 6.28. The judged fool rate against the author's own passage moves in
opposite directions under the two judges (`16_judges/afc_fool_adapter_minus_base.csv`):
Gemini's rate falls under the Ministral adapter (-0.02 to -0.05, inside its 0.05 floor) while
MiniMax's rises (+0.06, +0.10, +0.17 at 3B, 8B, 14B, above the floor at 8B and 14B); on the
same three Qwen authors Gemini is inside its floor and MiniMax rises by +0.08 to +0.10.

The gap-closing slope is mostly mechanical: the adapter-minus-base gain regressed on the
base-to-ceiling headroom has slope 1.15 [0.93, 1.47] over the 18 overlay points, but the
adapter endpoint regressed on the base level has slope -0.41 [-0.69, -0.05] with r2 0.24
(`gap_closing_diagnostics.csv`), which is regression to the mean with a small real component;
for Wegmann the endpoint slope is 0.01 [-0.68, 0.71] and the whole gap-closing pattern is
arithmetic.

How to read it. Three authors, replicate pairs at 3B, 8B and 14B, merged weights instead of
LoRA serving, FP8 checkpoints dequantised on load. The claim that survives is directional:
adapters land both families at about the same LUAR for the two public authors, the private
author is embedding-blind in both, and the adherence cost is a Qwen-sized effect on Qwen and
a within-floor effect on Ministral, whose bases start with lower coverage (77 against 87
points at A0) and higher truncation. Which judge is asked decides the sign of the fool-rate
change on both families.

### F. Authors differ more than sizes or families do (script 19)

I2 in the Qwen pools runs from 73% to 97.5% (`pooled_dl.csv`), and the 95% prediction interval
for a new author spans zero for every voice measure at every size (LUAR source at 8B:
prediction interval [-0.061, +0.195]). Leaving one author out never flips the sign of the
coverage, hapax or proposition-echo pools (`loo_summary.csv`); the largest single-author
shift on Qwen coverage is 3.6 points (cather at 14B), under two floors. Author class shows
between-group differences on coverage and geo_index in the subgroup Q tests
(`subgroup_author_class.csv`, coverage at 4B p 0.0002) that vanish once corpus size is in the
model (section C).

How to read it. With k = 13 the tau2 estimates are descriptive. The contemporary authors have
the largest corpora, so "contemporary authors gain more" and "larger corpora gain more"
cannot be separated on this design.

### G. Voice and construction move in opposite directions, and length carries part of it (scripts 14, 17)

Across the 40 Qwen author-size configurations the construction change regressed on the
voice change has slope +0.84 [0.53, 1.18] with intercept -0.49 and Spearman 0.70
(`14_style_construction_tradeoff/tradeoff_slope.csv`, 13 authors; both axes oriented so that
higher is closer to the author): construction falls in nearly every configuration, and it
falls least where the voice gain is largest. The two means move in opposite directions; the
covariance across configurations runs the same way, which is a corpus-size gradient that moves
both axes and not a trade of one for the other (corrected 2026-09-11 12:38; the earlier
sentence had the covariance reversed). With words as a covariate the adapter's construction-axis effect is -0.209
[-0.230, -0.188] against -0.247 without it (`length_null_mixed_models.csv`, 13 groups), so
about a sixth of the construction loss travels with the extra length; the voice effect does
not change (+0.147 either way). Qwen adapters add 145 to 166 words at 4B for cather and
chesterton (`17_length_truncation/words_adapter_minus_base.csv`); several measures are bound
to length (`words_correlations.csv`: clause-rhythm position rho 0.71, rubric construction
-0.47, rubric craft -0.44, coverage -0.39) and are flagged wherever they are quoted. The
600-word cap on proposition echo changes the sign in 3 of 50 cells, all inside the floor
(`length_null_per.csv`). Dropping truncated cells flips the sign of 5 of 172 harvested
contrasts (`22_multiple_comparisons_and_sensitivity/sensitivity_flip_summary.csv`).

How to read it. The opposite-direction claim is about the two means; across configurations the axes co-move. On
Ministral the construction axis does not fall (+0.02 [-0.07, +0.12], 9 points, 3 authors)
because the terminal-event component improves there (+0.11 [0.02, 0.21]) while proposition
echo still rises (-0.035 [-0.046, -0.023] on the inverted scale); which component drives the
axis depends on the family.

### H. The instruments are not interchangeable (scripts 15, 23, 24)

The three style embeddings rank the 50 author-size gains alike only in part (Spearman of
gains: LUAR-Wegmann 0.49 [0.22, 0.70], LUAR-StyleDistance 0.69, Wegmann-StyleDistance 0.85;
`15_instrument_agreement_and_fidelity/embedding_gain_agreement.csv`) and disagree on the
direction of the adapter for particular authors (`embedding_disagreement.csv`: for link,
Wegmann falls by -0.24 to -0.37 while LUAR is near zero; for patrick_v2, Wegmann rises +0.08
to +0.10 while LUAR is zero or negative). Of 34 instruments, 20 have author and stranger
anchors separated by more than twice their floor and 14 do not (`anchor_separation.csv`);
four (the AI-cosine columns and geo_index) take run-dependent values on the same reference
passage (`anchor_stability.csv`, share 0.92) and cannot serve as fixed anchors. The
instrument correlation matrix has a first principal component carrying 23% of the variance
and ten components above the parallel-analysis line (`pca_parallel_analysis.csv`); the pairs
above 0.85 (`redundancy_pairs.csv`) are within-construct duplicates (mattr-mtld 0.98,
distinct-3-versus-rep-4 -0.96) plus rubric construction against rubric craft (0.85).

The author-region rate R (the share of generations closer to the author's own passages than
to the stranger floor, on the calibratable instruments; `author_region_summary.csv`, Qwen,
13-14 authors) is 0.33, 0.29, 0.33 for bases and 0.51, 0.54, 0.54 for adapters at 4B, 8B, 14B,
against a stranger floor of 0.38 to 0.39 and an author ceiling of 0.76: base generations fall
in the author's region less often than strangers do, adapters about a third to a half of the
way from the floor to the ceiling. On the eval-cache measures computed on the authors' own
passages (script 24, `author_region_summary.csv`, five instruments) the order reverses:
adapters sit inside the region 0.056 to 0.072 of the time against 0.062 to 0.131 for bases.

How to read it. "Closer to the author" depends on which instrument is asked. The embeddings
say the adapter moves toward the author; the cache measures (proposition echo, hapax,
paragraph shape) say it moves away, because the adapter's construction losses are exactly
what those measures see. No single fidelity index can be quoted; the disagreement is a
result.

### I. The judges are relative instruments with known failures (script 16)

The rubric separates the author's own passages from sentence-shuffled versions in 15 of 16
author-by-judge cells (`16_judges/rubric_calibration.csv`; the exception is patrick_v2 under
MiniMax). It prefers a generation to the author's own passages in 2 of 108 cells, both the
Qwen 14B base for patrick_v2 on the construction block (+1.13 [0.34, 1.89];
`rubric_vs_author_items.csv`). The two judges agree on the rubric with quadratic-weighted
kappa 0.23 (opening move) to 0.70 (figure restraint) (`rubric_interjudge_kappa.csv`, 2,586
pairs), and item order moves the score on 22 of 24 judge-subscore rows by up to 1.6 points
on a ten-point scale (`rubric_order_effect.csv`). On the 2AFC task the two judges agree on the
win-versus-A0 verdict 54% of the time (kappa 0.08) and on the fool-versus-source verdict 90%
of the time (kappa 0.10, because both rarely pick the generation;
`afc_judge_agreement.csv`). Win-versus-A0 rates are 0.53 and 0.52 (`afc_rates_by_judge.csv`),
which is chance. Author-unit fool rates rise under the adapter (0.041, 0.052, 0.082 at 4B, 8B,
14B against 0.030, 0.023, 0.029 for bases; `afc_fool_by_author_unit.csv`) and correlate weakly
with LUAR (rho 0.09 pooled, 0.36 at configuration level; `afc_fool_vs_measures.csv`). Coverage
falls under the adapter for every author at every size (`coverage_adapter_minus_base.csv`,
from -11.3 for chesterton to -59.1 for h_private at 4B).

On the Ministral family the same judges behave less well (`rubric_calibration_by_family.csv`,
`afc_judge_agreement.csv`, `afc_rates_by_judge.csv`): the rubric shuffle gate passes 4 of 6
author-by-judge cells against 15 of 16 on Qwen, and both failures are patrick_v2, where the
Ministral generations outscore the author's own passages by 0.24 (Gemini) and 0.18 (MiniMax);
the two judges agree on the win-versus-A0 verdict 51% of the time (kappa 0.02); Gemini's
win-versus-A0 rate is 0.59 on Ministral against 0.53 on Qwen, and its fool rate against the
source is 0.096 against 0.019, which is a judge-by-family interaction, not a family result.

How to read it. The rubric is a usable construction instrument (it tracks coverage at rho
0.46 to 0.53 and proposition echo at -0.17 to -0.47) and an invalid voice criterion. The 2AFC
win rate carries no signal. Nothing here is a measurement of quality.

### J. Attribution is the largest robust effect; copying is absent (script 21)

LUAR nearest-author attribution of a generation to its target author rises from an
author-mean 0.33 to 0.60 at Qwen3 4B (14 authors, chance 0.07; `21_attribution_detection/attribution_rates.csv`),
with pooled gains of +0.26 to +0.29 at every Qwen size (intervals above zero;
`attribution_gain_pooled.csv`) and +0.45 to +0.51 on Ministral (3 authors). Burrows Delta,
StyleDistance and Wegmann move the same way with smaller gains. No cell is flagged for
memorisation and the 8-gram overlap with the training corpus never exceeds 0.01
(`copying_rates.csv`). Mis-attributions have attractors: base generations are called
watanna by LUAR (25%), chopin by Burrows Delta (43%), sui_sin_far by Wegmann (31%) and cather
by StyleDistance (28%) (`nearest_author_attractor.csv`), all period authors because the pool
is. Style-tell markers rise under the adapter at 8B and 14B (+0.10 and +0.09 on the
tell-weight index, 8 to 9 of 13 authors above the floor; `tells_gain_pooled.csv`).

How to read it. Attribution rates are the attribution model's own nearest-neighbour ranks
over a fourteen-author period pool, not a provenance claim; the register-matched pool of
script 23 gives Ministral adapters 0.49 to 0.61 against 0.05 to 0.11 for bases on the same
three authors (`23_register_matched_pool/attribution_accuracy_summary.csv`).

### K. Brief difficulty is real, weak and shared (script 20)

Of 56 pooled brief-covariate slopes, 5 are consistent across authors
(`20_brief_covariates/slopes_pooled_over_authors.csv`, 14 authors): coverage falls with
dialogue share for both kinds (-0.15 and -0.17 standardised) and with source length for the
base; length ratio and truncation rise with source length. Configurations agree on which
briefs are hard only modestly (`difficulty_agreement.csv`: mean Spearman between two
configurations 0.24 to 0.42 for base-base pairs, 0.11 to 0.29 for base-adapter pairs).
Ignoring the brief cluster shrinks standard errors by up to 1.9 times for event-order tau
(`se_inflation_from_repeated_briefs.csv`).

### L. Frontier and local (script 25, thirteen authors, three hosted models)

Three hosted models stand in for what a writer would otherwise use: deepseek-v4-flash-0731 (F0
bare brief and F5 full conditioning, 14 authors), gpt-5.6-luna (F0, 13 authors) and
deepseek-v4-pro (F0, 13 authors, added 2026-09-11). Flash and luna are chat-tier by price; V4
Pro is the larger and dearer DeepSeek model. None is a closed flagship. Brief-paired against
the author's own Qwen3 4B runs, the v1 control excluded, pooled over 13 authors
(`25_series_and_frontier/frontier_vs_adapter_by_author.csv`, `frontier_contrasts.csv`; the
fool rate is the 2AFC judge rate against the real source passage, higher meaning the judges
picked the generation more often):

| contrast, F0 | LUAR source | coverage | truncated | words | fool rate |
|---|---:|---:|---:|---:|---:|
| flash minus 4B base | +0.056 (13 of 13 above floor) | +15.4 | -0.024 | +157 | +0.049 (5 of 13) |
| luna minus 4B base | +0.065 (13 of 13) | +17.2 | -0.024 | -12 | +0.168 (11 of 13) |
| pro minus 4B base | +0.066 (13 of 13) | +17.1 | -0.024 | +144 | +0.117 (11 of 13) |
| flash minus 4B adapter | +0.003 [-0.024, +0.039], adapter ahead for 7 of 13 | +43.7 [37.3, 50.4] | -0.114 | +65 | +0.034 [-0.004, +0.076] |
| luna minus 4B adapter | +0.012 [-0.015, +0.047], adapter ahead for 4 of 13 | +45.6 [39.4, 52.6] | -0.114 | -104 | +0.152 [+0.082, +0.229] |
| pro minus 4B adapter | +0.014 [-0.011, +0.046], adapter ahead for 5 of 13 | +45.4 [39.8, 52.2] | -0.114 | +52 | +0.101 [+0.051, +0.159] |

Against the bare 4B base all three hosted models are ahead on every voice instrument for
every author. Against the adapter the pooled LUAR difference is inside the 0.023 floor for
all three, and the sign follows the corpus. On flash the adapter is ahead for every author
with 100 or more training briefs (mansfield -0.059, wharton -0.024, watts -0.034, chesterton
-0.055, rucker -0.045, doctorow -0.040) and behind for every author under 51 (sui_sin_far
+0.118, cather +0.094, link +0.054, chopin +0.043), with h_private (38 briefs, -0.034) and
stross (71, -0.012) the exceptions. On V4 Pro the adapter is ahead for mansfield (-0.040),
watts (-0.029), chesterton (-0.034), rucker (-0.035) and doctorow (-0.031), wharton sits
inside the floor (-0.012), the hosted model is ahead for every author under 51 (sui_sin_far
+0.124, cather +0.096, chopin +0.050, link +0.048) and for patrick_v2 (107 briefs, +0.028, the
private author on whom the adapter does nothing the embeddings can see), with h_private
(+0.005) and stross (+0.006) inside the floor. Luna shows the same pattern with the smallest
adapter lead (four authors clear the floor). What the adapter cannot match is adherence: the
hosted models keep 44 to 46 more coverage points than the adapter and truncate nothing where
the adapter truncates 11% of its passages. The 2AFC judges add a reading the embeddings do
not give: luna and V4 Pro are picked over the real source more often than the adapter is
(+0.15 and +0.10, both intervals clear of zero; flash +0.03, interval crossing zero). That is
the judge instrument with the failures section I documents, and it is the one voice reading
on which two of the hosted models beat the adapter rather than tie it. Full conditioning on
flash (F5) adds nothing on voice (+0.022 LUAR against F0, 7 of 13 above floor, Wegmann
-0.053) and costs 4 coverage points. The three hosted models differ from one another by
less than a floor on every embedding measure (`frontier_model_contrast.csv`: luna minus flash
LUAR +0.009, 1 of 13 above floor; pro minus flash +0.010, 1 of 13; pro minus luna +0.002, 0 of
13) and by under 2 coverage points; they differ in length (luna 169 words shorter than flash,
pro 13 shorter) and on the judged fool rate (luna +0.12 over flash, 12 of 13 above floor; pro
+0.07, 9 of 13; pro -0.05 against luna, 5 of 13).

How to read it. This is the paper's democratisation claim and no more: a writer-owned 4B
adapter reaches the voice of the hosted models on the embedding instruments once the corpus
passes about a hundred briefs, pays for it in adherence and truncation, and is picked over
the source less often than luna or V4 Pro by the 2AFC judges. Moving from the chat-tier
DeepSeek to its top model moves no embedding instrument by more than a floor, so the
comparison does not hinge on which hosted tier is called the frontier; the judged fool rate
is the one reading that separates the hosted tiers. The comparison still says nothing about
the closed flagships (Claude Sonnet 5 or GPT-5.6-terra were priced at about USD 32 per pass
and not run). Coverage and the fool rate are LLM-judged instrument readings; the frontier
runs were judged by both judges at sample 0 like every other run.

### M. Multiplicity is not the limit (script 22)

The programme-wide BH layer over the harvested contrasts changes few verdicts: 202 of the
618 pooled arm contrasts survive their own script's q and 201 the programme q, but only 138
clear their floor; of script 22's own 75 pooled contrasts, 44 survive the adapter-only layer
and 38 the all-contrasts layer (`survival_summary.csv`). The floors bind more often than the
correction does. Minimum detectable effects with three Ministral authors are 1 to 3
standard deviations of the base distribution (`mde.csv`); dropping the private authors
flips 14 of 147 signs with a median relative change of 14% (`sensitivity_flip_summary.csv`),
the largest sensitivity of the five variants tried.

### N. Register matching moves the contemporary and private positions (script 23)

With a register-matched stranger pool built from the stored embeddings, the share of
author-instrument anchors separated by more than two floors falls (LUAR, period authors:
0.71 with the pipeline's 13-author pool, 0.29 with the class pool;
`median_position_by_class_pool.csv`), and the contemporary class moves down on every
embedding: LUAR -0.56 [-0.81, -0.24] (5 authors), StyleDistance -2.7 [-4.4, -1.5], Wegmann
-4.5 [-6.8, -2.2] (`pool_effect_tests.csv`; none of the nine tests reaches q < 0.05 after
correction, the smallest q is 0.075). The private class (2 authors) moves down on Wegmann
(-3.3 [-4.6, -1.9]) and StyleDistance (-0.32 [-0.60, -0.05]) and up on LUAR (+0.33 [+0.27,
+0.39]), so the direction of the pool effect is class- and instrument-specific (corrected
2026-09-11 12:32 after a read of the table; the earlier sentence said every non-period class
moves down). The shifts are larger than the adapter gains in the same cells.

How to read it. The register-matched pool has 4 or 5 authors per class and 1 for the private
class, so its floors are thin; the direction is the finding, the size is not.

## 6. What the study cannot say

- Anything about a model, size or family beyond thirteen authors; every pooled interval is
  wide because k is 13, and the prediction interval for a new author spans zero on every
  voice measure.
- Whether corpus size or author identity drives the gain; they are confounded by design, and
  the one within-author series is one author at one size.
- Whether the Ministral adherence cost is small or absent; the pooled coverage contrasts sit
  inside a floor of 6.3 points measured on four pairs, on three authors.
- Anything absolute about quality; the judges are relative and disagree, the rubric ranks a
  14B base above the private author's own prose on construction, the 2AFC win rate is
  chance, and on the second family the two judges move the fool rate in opposite directions.
- A single fidelity number; the embeddings and the cache measures move in opposite
  directions under the adapter and the register-matched pool moves the positions by more
  than the gain.
- Anything about period authors against their own register, or about contemporary and
  private authors with a wide pool; the pool on disk is fourteen period authors.
- Anything from proposition echo beyond raw rates; its shuffled floor is invalid.
- Anything about the closed flagship models (Claude Sonnet 5, GPT-5.6-terra); the frontier
  comparison covers two chat-tier models and DeepSeek's top open-weight model.

## 7. What would change the picture

Done on 2026-09-10/11 from the earlier version of this list: within-author series for a
contemporary and a private author with a seed replicate; judges on the Ministral family;
replicate pairs at 8B and 14B in both families; frontier comparators on all thirteen
authors, including DeepSeek V4 Pro as a top open-weight tier (it moved no embedding
instrument by more than a floor against flash). Still open:

1. A register-matched reference pool inside the pipeline, with at least ten authors per
   class, so positions for contemporary and private authors rest on more than four or five
   strangers.
2. A human 2AFC on a subset, since neither judge carries a usable win signal and the two
   disagree on the direction of the fool-rate change.
3. A closed flagship model (Claude Sonnet 5 or GPT-5.6-terra, about USD 32 per pass at F0) if
   a sentence about those models specifically is wanted; the open-weight top tier is covered.
4. A second seed at every series size, not only at 50, if the adherence curve's subset noise
   is to be bounded along the whole curve.

## 8. Index of scripts

| script | question | tables to open first |
|---|---|---|
| 10 | what exists, what is missing, how noisy a cell is | `integrity_flags.csv`, `replicate_floors.csv`, `test_retest_summary.csv` |
| 11 | what parameter count buys | `gain.csv`, `tests.csv`, `slopes_summary.csv` |
| 12 | what each prompting arm buys against the adapter | `arm_rank_summary*.csv`, `prompt_vs_adapter_pooled.csv`, `arm_contrasts_pooled.csv` |
| 13 | what corpus size buys | `gain_vs_corpus_spearman.csv`, `gain_piecewise_breakpoint.csv`, `gain_by_author_class.csv` |
| 14 | the voice-construction tradeoff | `author_level_tests.csv`, `tradeoff_slope.csv`, `length_null_mixed_models.csv` |
| 15 | which instruments agree, which anchor, fidelity plane | `anchor_separation.csv`, `embedding_disagreement.csv`, `author_region_summary.csv` |
| 16 | what the judges measure, both families | `rubric_calibration_by_family.csv`, `afc_judge_agreement.csv`, `afc_fool_adapter_minus_base.csv`, `rubric_order_effect.csv` |
| 17 | length and truncation as confounds | `words_correlations.csv`, `truncation_by_config.csv`, `truncation_sensitivity.csv` |
| 18 | does the second family replicate | `adapter_gain_paired.csv`, `cross_family_gain_diff.csv`, `judged_adapter_minus_base.csv`, `gap_closing_diagnostics.csv` |
| 19 | how much authors differ, which moderators survive | `pooled_dl.csv`, `metareg_multi.csv`, `loo_summary.csv` |
| 20 | brief difficulty and covariates | `slopes_pooled_over_authors.csv`, `difficulty_agreement.csv` |
| 21 | attribution, copying, tells | `attribution_gain_pooled.csv`, `copying_rates.csv`, `nearest_author_attractor.csv` |
| 22 | programme-wide correction and sensitivity | `survival_summary.csv`, `sensitivity_flip_summary.csv`, `mde.csv` |
| 23 | register-matched stranger pool, npy repair | `alignment_check.csv`, `pool_effect_tests.csv`, `median_position_by_class_pool.csv` |
| 24 | eval-cache measures on the authors' own passages | `event_order_ceiling.csv`, `shuffle_manipulation_check.csv`, `author_region_summary.csv` |
| 25 | three size series and the three hosted models | `size_series.csv`, `size_seed_replicates.csv`, `frontier_vs_adapter_by_author.csv`, `frontier_model_contrast.csv` |
