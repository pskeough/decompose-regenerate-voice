# 30 Anchored cache-measure positions, read by size

## What this does

Script 24 put the eval-cache instruments on the author scale and gave each an anchor. This
script reads those tables the way the exploratory R16 pass did: it reports, for each anchored
measure, how far the anchor separates author from register-matched stranger in floor units, and
it reads the adapter's position by model size rather than pooled. The reason is a correction the
exploratory pass made to the workspace: the pooled sentence-opener result hides a 4B gain against
a 14B reversal, so a pooled 'opener distance did not move' is an average of two opposite signs.

## How it does it

Nothing is scored here. `positions_by_configuration.csv` from script 24 carries one row per
author, configuration, arm and measure with `pos` on the author scale (1 = the author's own
mean, 0 = the register-matched stranger mean) and `separation_over_floor` for the anchor. The
by-size table groups those rows by family, parameter count and kind and takes the median. The
proposition-echo table reports its anchor separation beside its position, which is what fails.

### Anchor quality, per measure

| measure | construct | definition | n_rows | n_authors | median_separation_over_floor | share_anchor_usable | median_floor | position_usable |
|---|---|---|---|---|---|---|---|---|
| otd_js | voice_structure | ref-anchored | 98 | 13 | 5.059 | 0.816 | 0.006 | True |
| burst_an_diff | voice_structure | ref-anchored | 98 | 13 | 3.855 | 0.755 | 0.017 | True |
| cv_diff | voice_structure | ref-anchored | 98 | 13 | 3.348 | 0.633 | 0.044 | True |
| para_cv_words | voice_structure | absolute | 98 | 13 | 3.348 | 0.633 | 0.044 | True |
| arti_w | tell | calibration-z | 98 | 13 | 1.608 | 0.204 | 0.048 | False |
| per | construction | absolute | 98 | 13 | 1.548 | 0.388 | 0.010 | False |
| rfpd_w | voice_structure | calibration-z | 98 | 13 | 1.249 | 0.265 | 0.047 | False |
| hapax_w300 | voice_structure | absolute | 98 | 13 | 1.220 | 0.449 | 0.015 | False |
| cpd_z | voice_structure | ref-anchored | 98 | 13 | 1.203 | 0.204 | 0.114 | False |
| per_uncapped | construction | absolute | 98 | 13 | 0.624 | 0.061 | 0.025 | False |
| w1_logpara | voice_structure | ref-anchored | 98 | 13 | 0.605 | 0.265 | 0.177 | False |

### Opener-class position by size

| measure | construct | family | params_b | n_authors_base | n_authors_adapter | median_pos_base | median_pos_adapter | adapter_minus_base |
|---|---|---|---|---|---|---|---|---|
| otd_js | voice_structure | Ministral3 | 3.000 | 3 | 3 | 0.837 | 1.415 | 0.578 |
| otd_js | voice_structure | Ministral3 | 8.000 | 3 | 3 | 0.760 | 1.462 | 0.702 |
| otd_js | voice_structure | Ministral3 | 14.000 | 3 | 3 | 1.086 | 1.493 | 0.407 |
| otd_js | voice_structure | Qwen3 | 1.700 | 1 | 1 | -0.350 | 1.155 | 1.506 |
| otd_js | voice_structure | Qwen3 | 4.000 | 13 | 13 | -0.444 | 1.711 | 2.154 |
| otd_js | voice_structure | Qwen3 | 8.000 | 13 | 13 | 0.806 | 1.791 | 0.985 |
| otd_js | voice_structure | Qwen3 | 14.000 | 13 | 13 | 1.474 | 1.935 | 0.461 |
| otd_js | voice_structure | pooled |  | 13 | 13 | 0.806 | 1.493 | 0.687 |

## How to read the result, conservatively

Read an anchor only where it clears twice its floor (`position_usable`). The opener-class
separation here is measured against the register-matched pool of script 24, which is a stricter
comparison than the all-authors pool the exploratory R16 pass used, so its floor count is lower
than the exploratory number and the exploratory number should not be quoted as the workspace
figure. Proposition echo is not an author instrument; its anchor does not separate, and it should
be reported as a raw rate, not as a position.

## Caveats

- Reads only script 24's outputs; it does not re-score any passage. The measure code lives in the pipeline, not here.
- The register-matched pool is used, so separation_over_floor is smaller than the exploratory R16 figure computed against all other authors.
- Only arm A0 has eval-cache measures, so nothing here speaks to the prompting arms.
- Thirteen authors; private authors have a pool of one.
