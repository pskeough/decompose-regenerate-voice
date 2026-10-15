# 29 Noise term, three-state truncation, brief-level controls

## What this does

Four corrections to how the study's own evidence is read. First, the replicate floor is a
worst case only on the embedding instruments; against the sample-to-sample difference inside a
single run it sits at about one standard deviation of ordinary sampling noise, and one pair
supplies a disproportionate share of the floors. Second, the truncation column is two different
failures: joined to script 28's loop detector it splits into cut-inside-loop, cut-live-prose and
landed-inside-loop, and the two model families fail in different kinds. Third, rejecting the
truncated one of the two samples already on disk removes part of the truncation at no measurable
voice cost. Fourth, every brief-level statistic in script 20 is read against a replicate-pair
null, which separates the adapter's voice gains (real) from its adherence losses (regression to
the mean on difficult briefs).

## How it does it

The floor's sampling term is the run-level standard deviation of the sample-0 minus sample-1
mean difference; the floor is the maximum over replicate pairs, so the comparison between them
says how conservative the floor is. The variance decomposition is a moment-based nested
decomposition (author > brief > configuration > sample), with negative components truncated at
zero. The three-state split joins `28_loop_and_landing/layer1_cells.csv.gz` to `cells.parquet`
on (run, id, arm, sample). Best-of-two resamples the two stored samples under four selection
rules and one oracle, with authors as the unit. The nulls use the nine replicate pairs as the
exchangeable baseline. Bootstrap seeds are derived from the measure and family with crc32, so
the run is reproducible across processes.

### Floor vs sampling term, LUAR-to-source

| family | existing_floor_max | between_sample_mean_abs | bs_signed_sd_run | ratio_floor_over_signed_sd |
|---|---|---|---|---|
| Ministral3 | 0.011 | 0.007 | 0.008 | 1.333 |
| Qwen3 | 0.023 | 0.010 | 0.013 | 1.704 |

### Adapter-minus-base by truncation state

| family | params_b | state | base_rate | adapter_rate | adapter_minus_base | ci_low | ci_high | floor | in_floor_units | above_floor |
|---|---|---|---|---|---|---|---|---|---|---|
| Ministral3 | 3.000 | cut_live_prose | 0.065 | 0.072 | 0.006 | -0.038 | 0.036 | 0.038 | 0.169 | False |
| Ministral3 | 3.000 | cut_inside_loop | 0.000 | 0.004 | 0.004 | 0.000 | 0.013 | 0.000 |  | nan |
| Ministral3 | 3.000 | trunc_any | 0.065 | 0.076 | 0.011 | -0.026 | 0.036 | 0.038 | 0.280 | False |
| Ministral3 | 8.000 | cut_live_prose | 0.089 | 0.078 | -0.011 | -0.083 | 0.038 | 0.038 | -0.293 | False |
| Ministral3 | 8.000 | cut_inside_loop | 0.000 | 0.008 | 0.008 | 0.000 | 0.012 | 0.000 |  | nan |
| Ministral3 | 8.000 | trunc_any | 0.089 | 0.085 | -0.004 | -0.071 | 0.038 | 0.038 | -0.093 | False |
| Ministral3 | 14.000 | cut_live_prose | 0.217 | 0.038 | -0.179 | -0.274 | -0.122 | 0.038 | -4.654 | True |
| Ministral3 | 14.000 | cut_inside_loop | 0.000 | 0.008 | 0.008 | 0.000 | 0.013 | 0.000 |  | nan |
| Ministral3 | 14.000 | trunc_any | 0.217 | 0.046 | -0.171 | -0.274 | -0.111 | 0.038 | -4.447 | True |
| Qwen3 | 1.700 | cut_live_prose | 0.000 | 0.178 | 0.178 | 0.178 | 0.178 | 0.012 | 14.578 | True |
| Qwen3 | 1.700 | cut_inside_loop | 0.078 | 0.056 | -0.022 | -0.022 | -0.022 | 0.024 | -0.911 | False |
| Qwen3 | 1.700 | trunc_any | 0.078 | 0.233 | 0.156 | 0.156 | 0.156 | 0.012 | 12.756 | True |
| Qwen3 | 4.000 | cut_live_prose | 0.001 | 0.044 | 0.043 | 0.021 | 0.067 | 0.012 | 3.514 | True |
| Qwen3 | 4.000 | cut_inside_loop | 0.021 | 0.063 | 0.042 | 0.002 | 0.087 | 0.024 | 1.724 | True |
| Qwen3 | 4.000 | trunc_any | 0.022 | 0.107 | 0.085 | 0.048 | 0.125 | 0.012 | 6.963 | True |
| Qwen3 | 8.000 | cut_live_prose | 0.000 | 0.029 | 0.029 | 0.010 | 0.049 | 0.012 | 2.341 | True |
| Qwen3 | 8.000 | cut_inside_loop | 0.001 | 0.115 | 0.114 | 0.048 | 0.193 | 0.024 | 4.689 | True |
| Qwen3 | 8.000 | trunc_any | 0.001 | 0.144 | 0.143 | 0.082 | 0.212 | 0.012 | 11.719 | True |
| Qwen3 | 14.000 | cut_live_prose | 0.000 | 0.066 | 0.066 | 0.040 | 0.094 | 0.012 | 5.417 | True |
| Qwen3 | 14.000 | cut_inside_loop | 0.000 | 0.213 | 0.213 | 0.075 | 0.394 | 0.024 | 8.733 | True |
| Qwen3 | 14.000 | trunc_any | 0.000 | 0.279 | 0.279 | 0.150 | 0.451 | 0.012 | 22.882 | True |

### Best-of-two, pooled deltas vs single sample

| rule | metric | delta_vs_single | ci_low | ci_high |
|---|---|---|---|---|
| reject_truncated | truncated | -0.088 | -0.112 | -0.065 |
| reject_truncated | in_band | 0.056 | 0.039 | 0.075 |
| reject_truncated | luar_cos_source | 0.001 | -0.000 | 0.002 |
| reject_truncated | luar_cos_ref | 0.000 | -0.001 | 0.002 |
| reject_truncated | styledist_cos_source | 0.001 | 0.000 | 0.001 |
| reject_truncated | len_ratio | -0.052 | -0.072 | -0.035 |
| band_len_ratio | truncated | -0.056 | -0.075 | -0.039 |
| band_len_ratio | in_band | 0.118 | 0.098 | 0.139 |
| band_len_ratio | luar_cos_source | 0.002 | 0.001 | 0.003 |
| band_len_ratio | luar_cos_ref | 0.001 | -0.000 | 0.002 |
| band_len_ratio | styledist_cos_source | 0.001 | -0.000 | 0.001 |
| band_len_ratio | len_ratio | -0.040 | -0.056 | -0.026 |
| max_luar | truncated | -0.003 | -0.015 | 0.010 |
| max_luar | in_band | 0.012 | -0.004 | 0.027 |
| max_luar | luar_cos_source | 0.030 | 0.027 | 0.034 |
| max_luar | luar_cos_ref | 0.020 | 0.017 | 0.023 |
| max_luar | styledist_cos_source | 0.006 | 0.004 | 0.007 |
| max_luar | len_ratio | -0.005 | -0.017 | 0.008 |
| oracle_both_mean | truncated | 0.001 | -0.009 | 0.011 |
| oracle_both_mean | in_band | 0.085 | 0.064 | 0.107 |
| oracle_both_mean | luar_cos_source | 0.001 | -0.001 | 0.003 |
| oracle_both_mean | luar_cos_ref | -0.001 | -0.002 | 0.001 |
| oracle_both_mean | styledist_cos_source | 0.001 | 0.000 | 0.002 |
| oracle_both_mean | len_ratio | -0.001 | -0.010 | 0.008 |

### Regression-to-the-mean nulls

| statistic | observed | obs_lo | obs_hi | null_replicate | null_lo | null_hi | verdict |
|---|---|---|---|---|---|---|---|
| rho(base coverage, adapter-base coverage) | -0.437 | -0.485 | -0.390 | -0.512 | -0.637 | -0.409 | indistinguishable from the null |
| rho(base len_ratio, adapter-base len_ratio) | -0.343 | -0.388 | -0.297 | -0.428 | -0.530 | -0.331 | indistinguishable from the null |
| rho(base luar_cos_source, adapter-base luar_cos_source) | -0.677 | -0.720 | -0.633 | -0.320 | -0.396 | -0.233 | stronger than the null |
| rho(base otd_js, adapter-base otd_js) | -0.588 | -0.633 | -0.542 | -0.345 | -0.438 | -0.253 | stronger than the null |
| rho(base tau, adapter-base tau) | -0.521 | -0.581 | -0.460 | -0.370 | -0.447 | -0.276 | stronger than the null |
| rho(base terminal_missing, adapter-base terminal_missing) | -0.441 | -0.488 | -0.392 | -0.520 | -0.589 | -0.455 | indistinguishable from the null |
| rho(base truncated, adapter-base truncated) | -0.593 | -0.707 | -0.476 | -0.602 | -0.691 | -0.513 | indistinguishable from the null |
| rho(base per, adapter-base per) | -0.301 | -0.369 | -0.235 | -0.473 | -0.580 | -0.358 | indistinguishable from the null |

## How to read the result, conservatively

Read the floor against the sampling term, not as a constant currency: it is generous on the
embedding instruments and thin on the rate-like and eval-cache measures. Read the truncation
states separately, not the single flag. The best-of-two numbers are a lower bound at n of 2 and
cannot report coverage, which exists at sample 0 only. The brief-level nulls are the control the
workspace needed before quoting any brief-difficulty claim: the adherence losses are regression
to the mean, the voice gains are not.

## Caveats

- Promoted from an exploratory pass (scratch/R14, 2026-09-11); the between-sample difference is a lower bound on run-to-run noise, not the same quantity as the regeneration floor.
- Bootstrap seeds are crc32 of (measure, family) here, where the exploratory pass used Python's salted hash, so intervals can differ from the exploratory numbers in the third decimal while point estimates match.
- The variance components are a moment-based decomposition, not a fitted mixed model; coverage and fool_vs_source rows rest on few runs.
- Best-of-two is a lower bound at n of 2 and cannot report coverage or any judge measure; the LUAR selection rule is evaluated partly on the instrument it selects on.
- The three-state split inherits script 28's loop detector and its threshold.
- Thirteen authors bound every pooled statement here.
