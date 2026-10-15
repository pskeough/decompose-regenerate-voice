# 28 Loop-and-landing profile (Layer 1)

## What this does

A per-passage integrity profile over every generation in the study, all arms and both samples:
a repeated 8-gram span of at least 24 words for a loop, a landing flag, a content-saturation
point, and the share of the final 100 words inside a repeated span for a truncated cell. It
separates two failures the study had been reporting as one column, because the `truncated` flag
means opposite things in the two model families.

## How it does it

Metadata comes from `data/master/runs.csv` for the main runs and the run-level columns inside
`cells_series.parquet` and `cells_frontier.parquet` for the size-series and hosted runs; a cell whose
run is in no master table is marked `meta_source=none` and excluded from every aggregate. The
`truncated` flag is joined back onto each cell from the master tables on (run, id, arm, sample).
The loop threshold is calibrated on the authors' own held-out passages in
`data/authors/<author>/test.jsonl`: at a 24-word span it flags none of the 635 human
passages (the count is printed at run time). Contrasts are cluster bootstrapped over briefs within
author and then bootstrapped over authors, exactly as in the exploratory pass.

### Adapter-minus-base loop share and arm contrasts, pooled over authors

| contrast | estimate | lo | hi |
|---|---|---|---|
| A1_minus_A0 | 0.029 | 0.0155 | 0.0427 |
| A2_minus_A0 | 0.066 | 0.0513 | 0.0817 |
| A3_minus_A0 | 0.117 | 0.0798 | 0.1535 |
| A4_minus_A0 | 0.037 | 0.0246 | 0.0502 |
| A5_minus_A0 | 0.097 | 0.0718 | 0.1257 |

## How to read the result, conservatively

Over the joined cells, 0.1141 carry a loop and 0.0704 carry the truncation flag.
The family split is the strongest single result and it is a family effect, not a size or arm effect.
Loop share falls with corpus size in the within-author series, more steeply than the truncation flag,
so the thin-data failure is larger than the flag shows. The replicate floor for loop share is
dominated by one pair and is printed in `layer1_contrasts.csv`. Read the loop rate as a floor for
degeneration and an over-count for Chesterton-like parallelism.

## Caveats

- Promoted from an exploratory pass (scratch/R10, 2026-09-11); the loop detector is a lexical-repetition instrument with a measured zero false-positive rate on 635 human passages and at least one qualitative false positive on parallel prose.
- The loop flag is a floor for degeneration; the landing flag depends on a last-sentence heuristic that fails on dialogue and ellipsis.
- loop_share measures from onset to the end of the passage, so a mid-passage repeat followed by recovery scores high; loop_span_words is the honest quantity and both are in the cell file.
- The replicate floor for loop share rests on nine pairs and the mansfield 4B pair is several times larger than any other, so the Qwen3 4B floor is either 0.122 or 0.013 depending on which pair is believed.
