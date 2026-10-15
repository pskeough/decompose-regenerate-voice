# Master table schema (generated)

Built by scripts/01_build_master.py on 2026-09-11 11:15. 7876 A0 non-replicate base/adapter cells form the main analysis set.

## cells.parquet

40726 rows x 176 columns. One row per generated passage. Keys: run, author, family, params_b, tag, kind, replicate, arm, id, sample.

| column | dtype | non-null | example |
|---|---|---:|---|
| id | str | 1.00 | wharton__166_00_0000 |
| arm | str | 1.00 | A3 |
| sample | int64 | 1.00 | 1 |
| words | int64 | 1.00 | 615 |
| len_ratio | float64 | 1.00 | 0.811 |
| n_sent | int64 | 1.00 | 51 |
| sent_len_mean | float64 | 1.00 | 12.058823529411764 |
| sent_len_cv | float64 | 1.00 | 0.5136718935253302 |
| pct_short8 | float64 | 1.00 | 0.3333333333333333 |
| open_distinct | float64 | 1.00 | 0.21568627450980393 |
| open_top_share | float64 | 1.00 | 0.39215686274509803 |
| open_entropy | float64 | 1.00 | 0.45749921459480547 |
| staccato_anaphora | float64 | 1.00 | 0.018867924528301886 |
| short_run_max | float64 | 1.00 | 5.0 |
| em_dashes_per_100w | float64 | 1.00 | 0.0 |
| commas_per_sent | float64 | 1.00 | 1.0588235294117647 |
| template_rate | float64 | 1.00 | 0.6271637816245007 |
| cr_pos | float64 | 1.00 | 6.70856102003643 |
| mattr | float64 | 1.00 | 0.7661617900172116 |
| mtld | float64 | 1.00 | 62.589957767561216 |
| open2_distinct | float64 | 1.00 | 0.7647058823529411 |
| distinct_3 | float64 | 1.00 | 0.9395866454689984 |
| rep_4 | float64 | 1.00 | 0.041401273885350316 |
| max_repeat | float64 | 1.00 | 7.0 |
| sent_echo | float64 | 1.00 | 0.0 |
| shown_sent_mean | float64 | 1.00 | 12.058823529411764 |
| shown_pct_short | float64 | 1.00 | 33.333333333333336 |
| shown_pct_long | float64 | 1.00 | 0.0 |
| shown_commas | float64 | 1.00 | 1.0588235294117647 |
| shown_semi_per100 | float64 | 1.00 | 0.0 |
| shown_dialogue_pct | float64 | 1.00 | 15.686274509803921 |
| shown_para_mean | float64 | 1.00 | 68.33333333333333 |
| shown_open_distinct100 | float64 | 1.00 | 27.45098039215686 |
| shown_dash_per100w | float64 | 1.00 | 0.0 |
| shown_dist | float64 | 1.00 | 1.0105046941152735 |
| delta_own | float64 | 1.00 | 0.8643140159045027 |
| delta_rank | int64 | 1.00 | 3 |
| delta_nearest | str | 1.00 | chopin |
| luar_cos_source | float64 | 1.00 | 0.7501738667488098 |
| luar_cos_ref | float64 | 1.00 | 0.7349675893783569 |
| luar_cos_ai | float64 | 1.00 | 0.8438409566879272 |
| luar_nearest | str | 1.00 | cather |
| luar_attrib | int64 | 1.00 | 0 |
| wegmann_cos_source | float64 | 1.00 | 0.5145635604858398 |
| wegmann_cos_ref | float64 | 1.00 | 0.8461018800735474 |
| wegmann_cos_ai | float64 | 1.00 | 0.9447535276412964 |
| wegmann_nearest | str | 1.00 | sui_sin_far |
| wegmann_attrib | int64 | 1.00 | 0 |
| styledist_cos_source | float64 | 1.00 | 0.9485755562782288 |
| styledist_cos_ref | float64 | 1.00 | 0.9673240184783936 |
| styledist_cos_ai | float64 | 1.00 | 0.9768029451370239 |
| styledist_nearest | str | 1.00 | joyce |
| styledist_attrib | int64 | 1.00 | 0 |
| memo_lcs | int64 | 1.00 | 5 |
| memo_8gram | float64 | 1.00 | 0.0 |
| memo_flag | int64 | 1.00 | 0 |
| geo_index | float64 | 1.00 | 0.29808443213106817 |
| geo_overshoot | float64 | 1.00 | 0.0 |
| geo_n | int64 | 1.00 | 12 |
| nll_instruct_4bx4b | float64 | 0.07 | 1.5921564102172852 |
| nll_base_4bx4b | float64 | 0.07 | 1.527709722518921 |
| binoculars_4bx4b | float64 | 0.07 | 0.8075153231620789 |
| fastdetectgpt_4bx4b | float64 | 0.07 | 4.53901481628418 |
| tokens_4bx4b | float64 | 0.07 | 512.0 |
| run | str | 1.00 | base4b |
| author | str | 1.00 | wharton |
| family | str | 1.00 | Qwen3 |
| params_b | float64 | 1.00 | 4.0 |
| tag | str | 1.00 | 4b |
| kind | str | 1.00 | base |
| replicate | bool | 1.00 | False |
| size_key | str | 1.00 | Qwen3-4B |
| author_class | str | 1.00 | period |
| truncated | bool | 1.00 | False |
| preface | bool | 1.00 | False |
| length_flag | bool | 1.00 | False |
| gen_tokens | int64 | 1.00 | 761 |
| prompt_tokens | int64 | 1.00 | 1262 |
| target_words | int64 | 1.00 | 758 |
| n_words_gen | int64 | 1.00 | 615 |
| coverage | float64 | 0.50 | 100.0 |
| fool_vs_source | float64 | 0.50 | 0.0 |
| win_vs_A0 | float64 | 0.40 | 1.0 |
| n_judges_2afc | int64 | 1.00 | 0 |
| per | float64 | 0.21 | 0.08 |
| per_n_sent | float64 | 0.21 | 25.0 |
| per_uncapped | float64 | 0.21 | 0.10344827586206896 |
| otd_js | float64 | 0.21 | 0.35729981051817056 |
| abs_cv_diff | float64 | 0.21 | 0.5613444642427948 |
| cv_diff | float64 | 0.21 | -0.5613444642427948 |
| w1_logpara | float64 | 0.21 | 1.3460339177731526 |
| mean_sents_diff | float64 | 0.21 | 3.8 |
| psd_z | float64 | 0.21 | 1.7205037901619655 |
| burst_an_diff | float64 | 0.21 | -0.2278753104036283 |
| cpd_z | float64 | 0.21 | 1.6862530607333686 |
| lag1_diff | float64 | 0.21 | -0.1670942083681919 |
| lag2_diff | float64 | 0.21 | -0.19760230685720187 |
| lag3_diff | float64 | 0.21 | -0.6085072516509636 |
| q50_q10_diff | float64 | 0.21 | 0.04285714285714226 |
| q90_q50_diff | float64 | 0.21 | -0.8516129032258062 |
| hapax_w300 | float64 | 0.21 | 0.32666666666666666 |
| ttr_w300 | float64 | 0.21 | 0.4633333333333333 |
| mattr50_w300 | float64 | 0.21 | 0.7533067729083666 |
| mtld_w300 | float64 | 0.21 | 57.068437180796735 |
| tau | float64 | 0.21 | 0.2 |
| terminal_missing | float64 | 0.21 | 0.0 |
| events_present | float64 | 0.21 | 1.0 |
| n_events_cache | float64 | 0.21 | 6.0 |
| arti | float64 | 0.21 | 0.7233356087036289 |
| arti_w | float64 | 0.21 | 0.21015672855555212 |
| arti_hard | float64 | 0.21 | 0.41848613399545254 |
| arti_hard_w | float64 | 0.21 | 0.41848613399545254 |
| rfpd | float64 | 0.21 | 0.9134575395377852 |
| rfpd_w | float64 | 0.21 | 0.40027865938970847 |
| z_it_is_opener | float64 | 0.21 | -0.8746213688508299 |
| z_way_simile | float64 | 0.21 | -0.026258090774219804 |
| z_declarative_rating | float64 | 0.21 | 0.0 |
| z_reversal | float64 | 0.21 | 1.6739445359818101 |
| z_self_explanation | float64 | 0.21 | -0.18602919514627278 |
| z_triad | float64 | 0.21 | -0.08602777006169682 |
| z_antithesis | float64 | 0.21 | -0.5387936115548668 |
| z_cleft | float64 | 0.21 | -0.14168742679197016 |
| z_closing_flourish | float64 | 0.21 | 0.0 |
| z_nominalization_pickup | float64 | 0.21 | -0.24477666142533325 |
| z_meta_aside | float64 | 0.21 | 0.0 |
| z_self_rating | float64 | 0.21 | -0.1416035998761357 |
| z_absence_punch | float64 | 0.21 | -0.04483188570295342 |
| z_comma_chain | float64 | 0.21 | -0.14108776520845434 |
| z_participial_triad | float64 | 0.21 | 0.0 |
| z_negation_template | float64 | 0.21 | -0.23892009231145878 |
| z_intensifier | float64 | 0.21 | -0.8202491673927863 |
| z_generator_phrase | float64 | 0.21 | 0.0 |
| z_fragment_couplet | float64 | 0.21 | -0.23953617040104783 |
| z_personification | float64 | 0.21 | -0.06660684527531449 |
| z_colon_twist | float64 | 0.21 | 0.0 |
| z_tail_twist | float64 | 0.21 | -0.12198089118754048 |
| z_question_fragment | float64 | 0.21 | -0.4871776060395804 |
| z_then_opener | float64 | 0.21 | -0.5441292490808036 |
| z_pointer_verdict | float64 | 0.21 | 0.0 |
| z_announcer | float64 | 0.21 | 0.0 |
| z_does_pair | float64 | 0.21 | 0.0 |
| z_parallel_address | float64 | 0.21 | 0.0 |
| z_conversion | float64 | 0.21 | 0.0 |
| z_rhetorical_question | float64 | 0.21 | -1.3297063204458945 |
| z_anaphora2 | float64 | 0.21 | 21.934903044886532 |
| z_long_short | float64 | 0.21 | 0.10805895212345439 |
| z_copula_density | float64 | 0.21 | 0.15316855422795597 |
| rubric_C1 | float64 | 0.06 | 7.666666666666667 |
| rubric_C2 | float64 | 0.06 | 5.666666666666667 |
| rubric_C3 | float64 | 0.06 | 6.666666666666667 |
| rubric_C4 | float64 | 0.06 | 7.0 |
| rubric_C5 | float64 | 0.06 | 5.0 |
| rubric_S1 | float64 | 0.06 | 2.6666666666666665 |
| rubric_S2 | float64 | 0.06 | 3.6666666666666665 |
| rubric_S3 | float64 | 0.06 | 4.0 |
| rubric_S4 | float64 | 0.06 | 3.3333333333333335 |
| rubric_S5 | float64 | 0.06 | 5.333333333333333 |
| rubric_S6 | float64 | 0.06 | 6.333333333333333 |
| rubric_S7 | float64 | 0.06 | 3.6666666666666665 |
| rubric_C | float64 | 0.06 | 6.3999999999999995 |
| rubric_S | float64 | 0.06 | 4.142857142857143 |
| n_rubric_records | float64 | 0.06 | 3.0 |
| rubric_C_gemini | float64 | 0.06 | 7.8 |
| rubric_S_gemini | float64 | 0.06 | 4.357142857142858 |
| rubric_C_minimax | float64 | 0.06 | 3.6 |
| rubric_S_minimax | float64 | 0.06 | 3.7142857142857144 |
| arm_desc | str | 1.00 | A3 |
| source_words | int64 | 1.00 | 758 |
| brief_words | int64 | 1.00 | 323 |
| n_events | int64 | 1.00 | 6 |
| dialogue_share | float64 | 1.00 | 0.23809523809523808 |
| work_key | str | 1.00 | 166_00 |
| train_briefs_passed | int64 | 1.00 | 168 |
| test_briefs_passed | int64 | 1.00 | 44 |
| words_total | int64 | 1.00 | 202353 |
| n_works_train | int64 | 1.00 | 28 |

## references.parquet

148681 rows x 62 columns. The authors' own passages and the period pool as scored per run. Keys: run, group, id.

| column | dtype | non-null | example |
|---|---|---:|---|
| id | str | 1.00 | wharton__166_00_0000 |
| group | str | 1.00 | source |
| arm | str | 0.00 |  |
| sample | str | 0.00 |  |
| words | int64 | 1.00 | 758 |
| len_ratio | str | 0.00 |  |
| flags | str | 0.00 |  |
| n_sent | int64 | 1.00 | 42 |
| sent_len_mean | float64 | 1.00 | 18.047619047619047 |
| sent_len_cv | float64 | 1.00 | 0.6725541393752371 |
| pct_short8 | float64 | 1.00 | 0.2857142857142857 |
| open_distinct | float64 | 1.00 | 0.5675675675675675 |
| open_top_share | float64 | 1.00 | 0.21621621621621623 |
| open_entropy | float64 | 1.00 | 0.7638919416860231 |
| staccato_anaphora | float64 | 1.00 | 0.0 |
| short_run_max | float64 | 1.00 | 5.0 |
| em_dashes_per_100w | float64 | 1.00 | 0.2638522427440633 |
| commas_per_sent | float64 | 1.00 | 1.1428571428571428 |
| template_rate | float64 | 1.00 | 0.5720620842572062 |
| cr_pos | float64 | 1.00 | 6.009485094850948 |
| mattr | float64 | 1.00 | 0.79836389280677 |
| mtld | float64 | 1.00 | 88.56653359946773 |
| open2_distinct | float64 | 1.00 | 0.9459459459459459 |
| distinct_3 | float64 | 1.00 | 0.9960526315789474 |
| rep_4 | float64 | 1.00 | 0.0 |
| max_repeat | float64 | 1.00 | 0.0 |
| sent_echo | float64 | 1.00 | 0.0 |
| shown_sent_mean | float64 | 1.00 | 18.047619047619047 |
| shown_pct_short | float64 | 1.00 | 28.571428571428573 |
| shown_pct_long | float64 | 1.00 | 14.285714285714286 |
| shown_commas | float64 | 1.00 | 1.1428571428571428 |
| shown_semi_per100 | float64 | 1.00 | 19.047619047619047 |
| shown_dialogue_pct | float64 | 1.00 | 26.19047619047619 |
| shown_para_mean | float64 | 1.00 | 50.53333333333333 |
| shown_open_distinct100 | float64 | 1.00 | 50.0 |
| shown_dash_per100w | float64 | 1.00 | 0.2638522427440633 |
| shown_dist | float64 | 1.00 | 0.35830370638214293 |
| delta_own | float64 | 1.00 | 0.7050622495181266 |
| delta_rank | int64 | 1.00 | 5 |
| delta_nearest | str | 1.00 | cather |
| luar_cos_ref | float64 | 1.00 | 0.9428333044052124 |
| luar_cos_ai | float64 | 1.00 | 0.8647742867469788 |
| luar_nearest | str | 1.00 | cather |
| luar_attrib | int64 | 1.00 | 0 |
| wegmann_cos_ref | float64 | 1.00 | 0.8208745718002319 |
| wegmann_cos_ai | float64 | 1.00 | 0.6430639624595642 |
| wegmann_nearest | str | 1.00 | wells |
| wegmann_attrib | int64 | 1.00 | 0 |
| styledist_cos_ref | float64 | 1.00 | 0.9689547419548035 |
| styledist_cos_ai | float64 | 1.00 | 0.9545645117759705 |
| styledist_nearest | str | 1.00 | chesterton |
| styledist_attrib | int64 | 1.00 | 0 |
| geo_index | float64 | 1.00 | 0.9645234477361336 |
| geo_overshoot | float64 | 1.00 | 0.08333333333333333 |
| geo_n | int64 | 1.00 | 12 |
| nll_instruct_4bx4b | float64 | 0.07 | 3.097452163696289 |
| nll_base_4bx4b | float64 | 0.07 | 3.0314042568206787 |
| binoculars_4bx4b | float64 | 0.07 | 0.9656041860580444 |
| fastdetectgpt_4bx4b | float64 | 0.07 | 0.9908640384674072 |
| tokens_4bx4b | float64 | 0.07 | 512.0 |
| run | str | 1.00 | base4b |
| author | str | 1.00 | wharton |

## runs.csv

110 rows x 46 columns. One row per run. Keys: run.

| column | dtype | non-null | example |
|---|---|---:|---|
| run | str | 1.00 | base4b |
| author | str | 1.00 | wharton |
| tag | str | 1.00 | 4b |
| kind | str | 1.00 | base |
| replicate | bool | 1.00 | False |
| family | str | 1.00 | Qwen3 |
| params_b | float64 | 1.00 | 4.0 |
| size_key | str | 1.00 | Qwen3-4B |
| n_gens | int64 | 1.00 | 528 |
| arms | str | 1.00 | A0,A1,A2,A3,A4,A5 |
| n_arms | int64 | 1.00 | 6 |
| n_briefs | int64 | 1.00 | 44 |
| n_samples | int64 | 1.00 | 2 |
| truncated_pct | float64 | 1.00 | 0.946969696969697 |
| preface_pct | float64 | 1.00 | 0.0 |
| scored | bool | 1.00 | True |
| judged_2afc | bool | 1.00 | True |
| has_coverage | bool | 1.00 | True |
| backend | str | 1.00 | llamacpp |
| base_model | str | 1.00 | Qwen/Qwen3-4B |
| temperature | float64 | 0.94 | 0.8 |
| adapter_served | str | 1.00 | none |
| provenance_platform | str | 0.84 | Windows-11-10.0.26200-SP0 |
| provenance_gpu | str | 0.84 | NVIDIA GeForce RTX 5060 Ti, 616.64, 16311 MiB |
| provenance_transformers | str | 0.84 | 5.14.1 |
| llama_server | str | 0.84 | local-default-b10435 |
| provenance_hash | str | 0.84 | 4666ddb2bf6199a6 |
| gate_generation_ok | boolean | 0.61 | True |
| train_run | str | 0.46 | train_cather_pair_r16_s0 |
| train_examples | float64 | 0.46 | 78.0 |
| train_targets | float64 | 0.46 | 26.0 |
| train_steps | float64 | 0.46 | 10.0 |
| train_wall_min | float64 | 0.46 | 4.196450114250183 |
| eval_first | float64 | 0.46 | 2.84932017326355 |
| eval_best | float64 | 0.46 | 2.848632335662842 |
| probe_delta | float64 | 0.46 | -0.8759293556213379 |
| probe_loss_on | float64 | 0.46 | 2.7227823734283447 |
| probe_loss_off | float64 | 0.46 | 3.5987117290496826 |
| lora_rank | float64 | 0.46 | 16.0 |
| lora_alpha | float64 | 0.46 | 32.0 |
| lr | float64 | 0.46 | 0.0001 |
| epochs | float64 | 0.46 | 3.0 |
| gate_training_ok | str | 0.23 | True |
| author_class | str | 1.00 | period |
| probe_delta_positive | bool | 1.00 | False |
| truncation_gate_ok | bool | 1.00 | True |

## authors.csv

14 rows x 23 columns. One row per author. Keys: author.

| column | dtype | non-null | example |
|---|---|---:|---|
| author | str | 1.00 | cather |
| name | str | 1.00 | Willa Cather |
| author_class | str | 1.00 | period |
| private | bool | 1.00 | False |
| n_test_chunks | int64 | 1.00 | 50 |
| n_ref_chunks | int64 | 1.00 | 42 |
| n_train_chunks | int64 | 1.00 | 39 |
| test_briefs_passed | int64 | 1.00 | 44 |
| train_briefs_passed | int64 | 1.00 | 33 |
| words_test | int64 | 1.00 | 35041 |
| words_ref | int64 | 1.00 | 29536 |
| words_train | int64 | 1.00 | 28170 |
| words_total | int64 | 1.00 | 92747 |
| n_works_train | int64 | 1.00 | 6 |
| n_works_test | int64 | 1.00 | 8 |
| n_works_ref | int64 | 1.00 | 6 |
| chunk_words_mean | float64 | 1.00 | 707.9923664122138 |
| retrieval_fallback_rows | int64 | 1.00 | 0 |
| within_work_test | bool | 1.00 | False |
| split_seed | int64 | 1.00 | 20260903 |
| in_qwen_sweep | bool | 1.00 | True |
| in_ministral_sweep | bool | 1.00 | False |
| train_examples_max | float64 | 0.93 | 156.0 |

## briefs.csv

635 rows x 13 columns. One row per test brief. Keys: author, id.

| column | dtype | non-null | example |
|---|---|---:|---|
| author | str | 1.00 | cather |
| id | str | 1.00 | cather__13555_00_0000 |
| passed | bool | 1.00 | True |
| source_words | int64 | 1.00 | 641 |
| brief_words | int64 | 1.00 | 282 |
| n_events | int64 | 1.00 | 11 |
| dialogue_share | float64 | 1.00 | 0.09375 |
| work | str | 1.00 | Youth and the Bright Medusa: A WAGNER MATINÉE |
| work_key | str | 1.00 | 13555_00 |
| chunk_idx | int64 | 1.00 | 0 |
| form | str | 1.00 | short_stories |
| attempts | str | 1.00 | [{'k': 0, 'ok': True, 'fails': [], 'stats': {'shared6': 0, ' |
| brief_model | str | 1.00 | deepseek/deepseek-v4-flash-0731 |

## cells_series.parquet

2688 rows x 172 columns. Chesterton training-size series (side table). Keys: run, arm, id, sample.

| column | dtype | non-null | example |
|---|---|---:|---|
| id | str | 1.00 | chesterton__1695_00_0001 |
| arm | str | 1.00 | A0 |
| sample | int64 | 1.00 | 1 |
| words | int64 | 1.00 | 741 |
| len_ratio | float64 | 1.00 | 0.929 |
| n_sent | int64 | 1.00 | 47 |
| sent_len_mean | float64 | 1.00 | 15.76595744680851 |
| sent_len_cv | float64 | 1.00 | 0.57260380914706 |
| pct_short8 | float64 | 1.00 | 0.2978723404255319 |
| open_distinct | float64 | 1.00 | 0.4411764705882353 |
| open_top_share | float64 | 1.00 | 0.17647058823529413 |
| open_entropy | float64 | 1.00 | 0.7166069776170741 |
| staccato_anaphora | float64 | 1.00 | 0.0 |
| short_run_max | float64 | 1.00 | 4.0 |
| em_dashes_per_100w | float64 | 1.00 | 0.0 |
| commas_per_sent | float64 | 1.00 | 0.8297872340425532 |
| template_rate | float64 | 1.00 | 0.5430167597765363 |
| cr_pos | float64 | 1.00 | 6.28757225433526 |
| mattr | float64 | 1.00 | 0.7528067700987306 |
| mtld | float64 | 1.00 | 54.2994129840269 |
| open2_distinct | float64 | 1.00 | 0.8529411764705882 |
| distinct_3 | float64 | 1.00 | 0.9564643799472295 |
| rep_4 | float64 | 1.00 | 0.04227212681638045 |
| max_repeat | float64 | 1.00 | 9.0 |
| sent_echo | float64 | 1.00 | 0.0 |
| shown_sent_mean | float64 | 1.00 | 15.76595744680851 |
| shown_pct_short | float64 | 1.00 | 29.78723404255319 |
| shown_pct_long | float64 | 1.00 | 2.127659574468085 |
| shown_commas | float64 | 1.00 | 0.8297872340425532 |
| shown_semi_per100 | float64 | 1.00 | 10.638297872340425 |
| shown_dialogue_pct | float64 | 1.00 | 34.04255319148936 |
| shown_para_mean | float64 | 1.00 | 61.75 |
| shown_open_distinct100 | float64 | 1.00 | 53.191489361702125 |
| shown_dash_per100w | float64 | 1.00 | 0.0 |
| shown_dist | float64 | 1.00 | 0.7778233128921016 |
| delta_own | float64 | 1.00 | 0.7492049184011432 |
| delta_rank | int64 | 1.00 | 1 |
| delta_nearest | str | 1.00 | chesterton |
| luar_cos_source | float64 | 1.00 | 0.9418116807937622 |
| luar_cos_ref | float64 | 1.00 | 0.9020348787307739 |
| luar_cos_ai | float64 | 1.00 | 0.8554713726043701 |
| luar_nearest | str | 1.00 | melville |
| luar_attrib | int64 | 1.00 | 0 |
| wegmann_cos_source | float64 | 1.00 | 0.9939601421356201 |
| wegmann_cos_ref | float64 | 1.00 | 0.9131984710693359 |
| wegmann_cos_ai | float64 | 1.00 | 0.8885886669158936 |
| wegmann_nearest | str | 1.00 | mansfield |
| wegmann_attrib | int64 | 1.00 | 0 |
| styledist_cos_source | float64 | 1.00 | 0.9871008396148682 |
| styledist_cos_ref | float64 | 1.00 | 0.9578713178634644 |
| styledist_cos_ai | float64 | 1.00 | 0.9452641010284424 |
| styledist_nearest | str | 1.00 | mansfield |
| styledist_attrib | int64 | 1.00 | 0 |
| memo_lcs | int64 | 1.00 | 4 |
| memo_8gram | float64 | 1.00 | 0.0 |
| memo_flag | int64 | 1.00 | 0 |
| geo_index | float64 | 1.00 | 0.6910152811067727 |
| geo_overshoot | float64 | 1.00 | 0.16666666666666666 |
| geo_n | int64 | 1.00 | 12 |
| run | str | 1.00 | chesterton_size100 |
| author | str | 1.00 | chesterton |
| family | str | 1.00 | Qwen3 |
| params_b | float64 | 1.00 | 4.0 |
| tag | str | 1.00 | 4b |
| kind | str | 1.00 | adapter |
| replicate | bool | 1.00 | False |
| size_key | str | 1.00 | Qwen3-4B |
| author_class | str | 1.00 | period |
| truncated | bool | 1.00 | False |
| preface | bool | 1.00 | False |
| length_flag | bool | 1.00 | False |
| gen_tokens | float64 | 1.00 | 896.0 |
| prompt_tokens | float64 | 1.00 | 523.0 |
| target_words | int64 | 1.00 | 798 |
| n_words_gen | int64 | 1.00 | 741 |
| coverage | float64 | 0.61 | 85.0 |
| fool_vs_source | float64 | 0.61 | 0.0 |
| win_vs_A0 | float64 | 0.31 | 0.0 |
| n_judges_2afc | int64 | 1.00 | 2 |
| per | float64 | 0.50 | 0.02857142857142857 |
| per_n_sent | float64 | 0.50 | 35.0 |
| per_uncapped | float64 | 0.50 | 0.047619047619047616 |
| otd_js | float64 | 0.50 | 0.3195487493011379 |
| abs_cv_diff | float64 | 0.50 | 0.11317418069924612 |
| cv_diff | float64 | 0.50 | -0.11317418069924612 |
| w1_logpara | float64 | 0.50 | 0.5583945168606551 |
| mean_sents_diff | float64 | 0.50 | 1.3928571428571428 |
| psd_z | float64 | 0.50 | 0.9271632888651595 |
| burst_an_diff | float64 | 0.50 | -0.09228624633296756 |
| cpd_z | float64 | 0.50 | 1.6478562385448567 |
| lag1_diff | float64 | 0.50 | -0.08967466428856577 |
| lag2_diff | float64 | 0.50 | -0.5273978151714831 |
| lag3_diff | float64 | 0.50 | -0.6269390816149327 |
| q50_q10_diff | float64 | 0.50 | -1.4666666666666668 |
| q90_q50_diff | float64 | 0.50 | -0.173214285714286 |
| hapax_w300 | float64 | 0.49 | 0.38 |
| ttr_w300 | float64 | 0.49 | 0.56 |
| mattr50_w300 | float64 | 0.49 | 0.7930677290836653 |
| mtld_w300 | float64 | 0.49 | 79.02542372881356 |
| tau | float64 | 0.49 | 1.0 |
| terminal_missing | float64 | 0.49 | 0.0 |
| events_present | float64 | 0.49 | 0.8888888888888888 |
| n_events_cache | float64 | 0.49 | 9.0 |
| arti | float64 | 0.50 | 0.2415328791122299 |
| arti_w | float64 | 0.50 | 0.2415328791122299 |
| arti_hard | float64 | 0.50 | 0.0 |
| arti_hard_w | float64 | 0.50 | 0.0 |
| rfpd | float64 | 0.50 | 0.41564445631623825 |
| rfpd_w | float64 | 0.50 | 0.41564445631623825 |
| z_it_is_opener | float64 | 0.50 | -0.7434284831330442 |
| z_way_simile | float64 | 0.50 | -0.031512150084655605 |
| z_declarative_rating | float64 | 0.50 | 0.0 |
| z_reversal | float64 | 0.50 | -0.3434576164269533 |
| z_self_explanation | float64 | 0.50 | -0.351233109900128 |
| z_triad | float64 | 0.50 | -0.2493343657249882 |
| z_antithesis | float64 | 0.50 | 1.0407847364211054 |
| z_cleft | float64 | 0.50 | 4.416657258628392 |
| z_closing_flourish | float64 | 0.50 | -0.016594480675727254 |
| z_nominalization_pickup | float64 | 0.50 | -0.3459549622538477 |
| z_meta_aside | float64 | 0.50 | 0.0 |
| z_self_rating | float64 | 0.50 | -0.20025950811508117 |
| z_absence_punch | float64 | 0.50 | 0.0 |
| z_comma_chain | float64 | 0.50 | -0.26838562493821 |
| z_participial_triad | float64 | 0.50 | 0.0 |
| z_negation_template | float64 | 0.50 | -0.2137594546427408 |
| z_intensifier | float64 | 0.50 | -0.8649825349014887 |
| z_generator_phrase | float64 | 0.50 | -0.0618356960170939 |
| z_fragment_couplet | float64 | 0.50 | -0.2721790983716315 |
| z_personification | float64 | 0.50 | -0.023293733985557886 |
| z_colon_twist | float64 | 0.50 | 0.0 |
| z_tail_twist | float64 | 0.50 | -0.16570435927721644 |
| z_question_fragment | float64 | 0.50 | -0.154675582728283 |
| z_then_opener | float64 | 0.50 | -0.5526881715438242 |
| z_pointer_verdict | float64 | 0.50 | -0.0165508109897385 |
| z_announcer | float64 | 0.50 | 0.0 |
| z_does_pair | float64 | 0.50 | 0.0 |
| z_parallel_address | float64 | 0.50 | 0.0 |
| z_conversion | float64 | 0.50 | 0.0 |
| z_rhetorical_question | float64 | 0.50 | 0.12641895775607195 |
| z_anaphora2 | float64 | 0.50 | 1.0731271135557363 |
| z_long_short | float64 | 0.50 | -0.8698523040220653 |
| z_copula_density | float64 | 0.50 | 1.3135969443422801 |
| rubric_C1 | float64 | 0.25 | 2.25 |
| rubric_C2 | float64 | 0.25 | 1.5 |
| rubric_C3 | float64 | 0.25 | 2.0 |
| rubric_C4 | float64 | 0.25 | 1.75 |
| rubric_C5 | float64 | 0.25 | 1.0 |
| rubric_S1 | float64 | 0.25 | 2.0 |
| rubric_S2 | float64 | 0.25 | 1.75 |
| rubric_S3 | float64 | 0.25 | 1.5 |
| rubric_S4 | float64 | 0.25 | 2.0 |
| rubric_S5 | float64 | 0.25 | 2.0 |
| rubric_S6 | float64 | 0.25 | 1.75 |
| rubric_S7 | float64 | 0.25 | 1.5 |
| rubric_C | float64 | 0.25 | 1.7000000000000002 |
| rubric_S | float64 | 0.25 | 1.7857142857142858 |
| n_rubric_records | float64 | 0.25 | 4.0 |
| rubric_C_gemini | float64 | 0.25 | 1.9000000000000001 |
| rubric_S_gemini | float64 | 0.25 | 1.8571428571428572 |
| rubric_C_minimax | float64 | 0.25 | 1.5 |
| rubric_S_minimax | float64 | 0.25 | 1.7142857142857144 |
| arm_desc | str | 1.00 | A0 |
| series | str | 1.00 | series |
| train_briefs_n | float64 | 1.00 | 100.0 |
| targets_seed | int64 | 1.00 | 0 |
| series_platform | str | 1.00 | local |
| frontier_model | str | 1.00 | deepseek/deepseek-v4-flash-0731 |
| frontier_label | str | 0.00 |  |
| train_examples | float64 | 1.00 | 600.0 |
| train_steps | float64 | 1.00 | 75.0 |
| probe_delta | float64 | 1.00 | -0.7161874771118164 |
| eval_best | float64 | 1.00 | 2.6410446166992188 |

## cells_frontier.parquet

4184 rows x 172 columns. Frontier-model arms F0/F5 (side table). Keys: run, arm, id, sample.

| column | dtype | non-null | example |
|---|---|---:|---|
| id | str | 1.00 | wharton__166_00_0000 |
| arm | str | 1.00 | F0 |
| sample | int64 | 1.00 | 0 |
| words | int64 | 1.00 | 780 |
| len_ratio | float64 | 1.00 | 1.029 |
| n_sent | int64 | 1.00 | 54 |
| sent_len_mean | float64 | 1.00 | 14.444444444444445 |
| sent_len_cv | float64 | 1.00 | 0.6659957175973342 |
| pct_short8 | float64 | 1.00 | 0.3888888888888889 |
| open_distinct | float64 | 1.00 | 0.32608695652173914 |
| open_top_share | float64 | 1.00 | 0.30434782608695654 |
| open_entropy | float64 | 1.00 | 0.5792231210592945 |
| staccato_anaphora | float64 | 1.00 | 0.03333333333333333 |
| short_run_max | float64 | 1.00 | 4.0 |
| em_dashes_per_100w | float64 | 1.00 | 0.1282051282051282 |
| commas_per_sent | float64 | 1.00 | 1.4074074074074074 |
| template_rate | float64 | 1.00 | 0.6225026288117771 |
| cr_pos | float64 | 1.00 | 6.714899713467049 |
| mattr | float64 | 1.00 | 0.7546361185983829 |
| mtld | float64 | 1.00 | 59.94499635435655 |
| open2_distinct | float64 | 1.00 | 0.8260869565217391 |
| distinct_3 | float64 | 1.00 | 0.9746835443037974 |
| rep_4 | float64 | 1.00 | 0.012674271229404309 |
| max_repeat | float64 | 1.00 | 5.0 |
| sent_echo | float64 | 1.00 | 0.0 |
| shown_sent_mean | float64 | 1.00 | 14.444444444444445 |
| shown_pct_short | float64 | 1.00 | 38.888888888888886 |
| shown_pct_long | float64 | 1.00 | 3.7037037037037037 |
| shown_commas | float64 | 1.00 | 1.4074074074074074 |
| shown_semi_per100 | float64 | 1.00 | 0.0 |
| shown_dialogue_pct | float64 | 1.00 | 27.77777777777778 |
| shown_para_mean | float64 | 1.00 | 60.0 |
| shown_open_distinct100 | float64 | 1.00 | 37.03703703703704 |
| shown_dash_per100w | float64 | 1.00 | 0.1282051282051282 |
| shown_dist | float64 | 1.00 | 0.9063573187400893 |
| delta_own | float64 | 1.00 | 0.8128342071238388 |
| delta_rank | int64 | 1.00 | 12 |
| delta_nearest | str | 1.00 | chopin |
| luar_cos_source | float64 | 1.00 | 0.8503320217132568 |
| luar_cos_ref | float64 | 1.00 | 0.8589253425598145 |
| luar_cos_ai | float64 | 1.00 | 0.9150782823562622 |
| luar_nearest | str | 1.00 | cather |
| luar_attrib | int64 | 1.00 | 0 |
| wegmann_cos_source | float64 | 1.00 | 0.6309126615524292 |
| wegmann_cos_ref | float64 | 1.00 | 0.9253920316696167 |
| wegmann_cos_ai | float64 | 1.00 | 0.930262565612793 |
| wegmann_nearest | str | 1.00 | sui_sin_far |
| wegmann_attrib | int64 | 1.00 | 0 |
| styledist_cos_source | float64 | 1.00 | 0.9478771686553955 |
| styledist_cos_ref | float64 | 1.00 | 0.9538527131080627 |
| styledist_cos_ai | float64 | 1.00 | 0.9620556831359863 |
| styledist_nearest | str | 1.00 | mansfield |
| styledist_attrib | int64 | 1.00 | 0 |
| memo_lcs | int64 | 1.00 | 4 |
| memo_8gram | float64 | 1.00 | 0.0 |
| memo_flag | int64 | 1.00 | 0 |
| geo_index | float64 | 1.00 | 0.3253140405766372 |
| geo_overshoot | float64 | 1.00 | 0.0 |
| geo_n | int64 | 1.00 | 12 |
| run | str | 1.00 | base4b_frontier |
| author | str | 1.00 | wharton |
| family | str | 1.00 | frontier |
| params_b | float64 | 0.00 |  |
| tag | str | 1.00 | 4b |
| kind | str | 1.00 | frontier |
| replicate | bool | 1.00 | False |
| size_key | str | 1.00 | frontier |
| author_class | str | 1.00 | period |
| truncated | bool | 1.00 | False |
| preface | bool | 1.00 | False |
| length_flag | bool | 1.00 | False |
| gen_tokens | float64 | 0.00 |  |
| prompt_tokens | float64 | 0.00 |  |
| target_words | int64 | 1.00 | 758 |
| n_words_gen | int64 | 1.00 | 780 |
| coverage | float64 | 0.50 | 100.0 |
| fool_vs_source | float64 | 0.50 | 0.0 |
| win_vs_A0 | float64 | 0.00 |  |
| n_judges_2afc | int64 | 1.00 | 2 |
| per | float64 | 0.00 |  |
| per_n_sent | float64 | 0.00 |  |
| per_uncapped | float64 | 0.00 |  |
| otd_js | float64 | 0.00 |  |
| abs_cv_diff | float64 | 0.00 |  |
| cv_diff | float64 | 0.00 |  |
| w1_logpara | float64 | 0.00 |  |
| mean_sents_diff | float64 | 0.00 |  |
| psd_z | float64 | 0.00 |  |
| burst_an_diff | float64 | 0.00 |  |
| cpd_z | float64 | 0.00 |  |
| lag1_diff | float64 | 0.00 |  |
| lag2_diff | float64 | 0.00 |  |
| lag3_diff | float64 | 0.00 |  |
| q50_q10_diff | float64 | 0.00 |  |
| q90_q50_diff | float64 | 0.00 |  |
| hapax_w300 | float64 | 0.00 |  |
| ttr_w300 | float64 | 0.00 |  |
| mattr50_w300 | float64 | 0.00 |  |
| mtld_w300 | float64 | 0.00 |  |
| tau | float64 | 0.00 |  |
| terminal_missing | float64 | 0.00 |  |
| events_present | float64 | 0.00 |  |
| n_events_cache | float64 | 0.00 |  |
| arti | float64 | 0.00 |  |
| arti_w | float64 | 0.00 |  |
| arti_hard | float64 | 0.00 |  |
| arti_hard_w | float64 | 0.00 |  |
| rfpd | float64 | 0.00 |  |
| rfpd_w | float64 | 0.00 |  |
| z_it_is_opener | float64 | 0.00 |  |
| z_way_simile | float64 | 0.00 |  |
| z_declarative_rating | float64 | 0.00 |  |
| z_reversal | float64 | 0.00 |  |
| z_self_explanation | float64 | 0.00 |  |
| z_triad | float64 | 0.00 |  |
| z_antithesis | float64 | 0.00 |  |
| z_cleft | float64 | 0.00 |  |
| z_closing_flourish | float64 | 0.00 |  |
| z_nominalization_pickup | float64 | 0.00 |  |
| z_meta_aside | float64 | 0.00 |  |
| z_self_rating | float64 | 0.00 |  |
| z_absence_punch | float64 | 0.00 |  |
| z_comma_chain | float64 | 0.00 |  |
| z_participial_triad | float64 | 0.00 |  |
| z_negation_template | float64 | 0.00 |  |
| z_intensifier | float64 | 0.00 |  |
| z_generator_phrase | float64 | 0.00 |  |
| z_fragment_couplet | float64 | 0.00 |  |
| z_personification | float64 | 0.00 |  |
| z_colon_twist | float64 | 0.00 |  |
| z_tail_twist | float64 | 0.00 |  |
| z_question_fragment | float64 | 0.00 |  |
| z_then_opener | float64 | 0.00 |  |
| z_pointer_verdict | float64 | 0.00 |  |
| z_announcer | float64 | 0.00 |  |
| z_does_pair | float64 | 0.00 |  |
| z_parallel_address | float64 | 0.00 |  |
| z_conversion | float64 | 0.00 |  |
| z_rhetorical_question | float64 | 0.00 |  |
| z_anaphora2 | float64 | 0.00 |  |
| z_long_short | float64 | 0.00 |  |
| z_copula_density | float64 | 0.00 |  |
| rubric_C1 | float64 | 0.00 |  |
| rubric_C2 | float64 | 0.00 |  |
| rubric_C3 | float64 | 0.00 |  |
| rubric_C4 | float64 | 0.00 |  |
| rubric_C5 | float64 | 0.00 |  |
| rubric_S1 | float64 | 0.00 |  |
| rubric_S2 | float64 | 0.00 |  |
| rubric_S3 | float64 | 0.00 |  |
| rubric_S4 | float64 | 0.00 |  |
| rubric_S5 | float64 | 0.00 |  |
| rubric_S6 | float64 | 0.00 |  |
| rubric_S7 | float64 | 0.00 |  |
| rubric_C | float64 | 0.00 |  |
| rubric_S | float64 | 0.00 |  |
| n_rubric_records | float64 | 0.00 |  |
| rubric_C_gemini | float64 | 0.00 |  |
| rubric_S_gemini | float64 | 0.00 |  |
| rubric_C_minimax | float64 | 0.00 |  |
| rubric_S_minimax | float64 | 0.00 |  |
| arm_desc | str | 1.00 | F0 |
| series | str | 1.00 | frontier |
| train_briefs_n | float64 | 0.00 |  |
| targets_seed | int64 | 1.00 | 0 |
| series_platform | str | 0.00 |  |
| frontier_model | str | 1.00 | deepseek/deepseek-v4-flash-0731 |
| frontier_label | str | 1.00 | base4b |
| train_examples | float64 | 0.00 |  |
| train_steps | float64 | 0.00 |  |
| probe_delta | float64 | 0.00 |  |
| eval_best | float64 | 0.00 |  |
