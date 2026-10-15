"""30 Anchored cache-measure positions, read by size.

The exploratory pass R16 (2026-09-11) scored the authors' own held-out and reference passages on
the eval-cache measures so those instruments could be placed on the author scale. That scoring was
subsumed by script 24, which does the same job with a register-matched stranger pool and a
per-author floor. What script 24 does not report, and what R16 did, is the reading by model size:
the pooled sentence-opener effect hides a 4B gain against a 14B reversal, and proposition echo
fails its anchor test.

This script reads script 24's tables only and produces that reading, so the numbers are quotable
without re-running the pipeline's measure code. It does not score anything.

Outputs (analysis/30_cache_measure_anchors/):
  anchor_quality.csv       per measure: median separation over floor, share of usable anchors
  position_by_size.csv     per measure x family x size x kind: median position on the author scale
  opener_by_size.csv       the opener-class reading beside cadence and paragraph, adapter vs base
  proposition_echo_anchor.csv  the anchor failure for proposition echo, per measure row
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from lib import *  # noqa

HERE = outdir("30_cache_measure_anchors")
SRC = os.path.join(OUT, "24_reference_measures")

pos = pd.read_csv(os.path.join(SRC, "positions_by_configuration.csv"))
fid = pd.read_csv(os.path.join(SRC, "fidelity_by_measure.csv"))

# ------------------------------------------------------------------ anchor quality
aq = (pos.groupby(["measure", "construct", "definition"])
      .agg(n_rows=("pos", "size"), n_authors=("author", "nunique"),
           median_separation_over_floor=("separation_over_floor", "median"),
           share_anchor_usable=("anchor_usable", "mean"),
           median_floor=("floor", "median")).reset_index()
      .sort_values("median_separation_over_floor", ascending=False))
aq["position_usable"] = aq["median_separation_over_floor"] > 2
write_table(aq, os.path.join(HERE, "anchor_quality.csv"), floats=4)
print("anchor_quality", aq.shape)

# ------------------------------------------------------------------ position by size
pbs = (pos.groupby(["measure", "construct", "family", "params_b", "kind"], dropna=False)
       .agg(n_authors=("author", "nunique"), median_pos=("pos", "median"), mean_pos=("pos", "mean"),
            median_separation_over_floor=("separation_over_floor", "median")).reset_index())
write_table(pbs, os.path.join(HERE, "position_by_size.csv"), floats=4)
print("position_by_size", pbs.shape)

# ------------------------------------------------------------------ opener reading by size
FOCUS = ["otd_js", "burst_an_diff", "cv_diff", "w1_logpara", "cpd_z", "pub_cv_words", "para_cv_words"]
rows = []
for m in FOCUS:
    d = pos[pos.measure == m]
    if not len(d):
        continue
    for (fam, pb), g in d.groupby(["family", "params_b"], observed=True):
        b = g[g.kind == "base"]["pos"]
        a = g[g.kind == "adapter"]["pos"]
        if not len(b) and not len(a):
            continue
        rows.append(dict(measure=m, construct=g["construct"].iloc[0], family=fam, params_b=float(pb),
                         n_authors_base=int(g[g.kind == "base"].author.nunique()),
                         n_authors_adapter=int(g[g.kind == "adapter"].author.nunique()),
                         median_pos_base=float(b.median()) if len(b) else np.nan,
                         median_pos_adapter=float(a.median()) if len(a) else np.nan,
                         adapter_minus_base=(float(a.median()) - float(b.median())) if len(b) and len(a) else np.nan))
ob = pd.DataFrame(rows)
# pooled over sizes, which is the sentence the exploratory pass corrected
pooled = []
for m in FOCUS:
    d = ob[ob.measure == m]
    if not len(d):
        continue
    bb, aa = d["median_pos_base"].dropna(), d["median_pos_adapter"].dropna()
    pooled.append(dict(measure=m, construct=d["construct"].iloc[0], family="pooled", params_b=np.nan,
                       n_authors_base=int(d.n_authors_base.max()), n_authors_adapter=int(d.n_authors_adapter.max()),
                       median_pos_base=float(bb.median()) if len(bb) else np.nan,
                       median_pos_adapter=float(aa.median()) if len(aa) else np.nan,
                       adapter_minus_base=(float(aa.median()) - float(bb.median())) if len(bb) and len(aa) else np.nan))
ob = pd.concat([ob, pd.DataFrame(pooled)], ignore_index=True)
write_table(ob, os.path.join(HERE, "opener_by_size.csv"), floats=4)
print("opener_by_size", ob.shape)

# ------------------------------------------------------------------ proposition echo anchor
pe = pos[pos.measure.isin(["per", "per_uncapped"])][
    ["measure", "construct", "definition", "author", "author_class", "family", "params_b", "kind",
     "floor", "separation", "separation_over_floor", "anchor_usable", "pos", "pos_lo", "pos_hi"]]
pe_sum = (pe.groupby(["measure", "definition"])
          .agg(n=("pos", "size"), median_separation_over_floor=("separation_over_floor", "median"),
               share_anchor_usable=("anchor_usable", "mean"), median_pos=("pos", "median")).reset_index())
write_table(pe_sum, os.path.join(HERE, "proposition_echo_anchor.csv"), floats=4)
print("proposition_echo_anchor", pe_sum.shape)

opener = ob[(ob.measure == "otd_js")]
write_readme(
    HERE, "30 Anchored cache-measure positions, read by size",
    """
    Script 24 put the eval-cache instruments on the author scale and gave each an anchor. This
    script reads those tables the way the exploratory R16 pass did: it reports, for each anchored
    measure, how far the anchor separates author from register-matched stranger in floor units, and
    it reads the adapter's position by model size rather than pooled. The reason is a correction the
    exploratory pass made to the workspace: the pooled sentence-opener result hides a 4B gain against
    a 14B reversal, so a pooled 'opener distance did not move' is an average of two opposite signs.
    """,
    """
    Nothing is scored here. `positions_by_configuration.csv` from script 24 carries one row per
    author, configuration, arm and measure with `pos` on the author scale (1 = the author's own
    mean, 0 = the register-matched stranger mean) and `separation_over_floor` for the anchor. The
    by-size table groups those rows by family, parameter count and kind and takes the median. The
    proposition-echo table reports its anchor separation beside its position, which is what fails.
    """,
    """
    Read an anchor only where it clears twice its floor (`position_usable`). The opener-class
    separation here is measured against the register-matched pool of script 24, which is a stricter
    comparison than the all-authors pool the exploratory R16 pass used, so its floor count is lower
    than the exploratory number and the exploratory number should not be quoted as the workspace
    figure. Proposition echo is not an author instrument; its anchor does not separate, and it should
    be reported as a raw rate, not as a position.
    """,
    caveats=[
        "Reads only script 24's outputs; it does not re-score any passage. The measure code lives in the pipeline, not here.",
        "The register-matched pool is used, so separation_over_floor is smaller than the exploratory R16 figure computed against all other authors.",
        "Only arm A0 has eval-cache measures, so nothing here speaks to the prompting arms.",
        "Thirteen authors; private authors have a pool of one.",
    ],
    tables=[("Anchor quality, per measure", aq),
            ("Opener-class position by size", opener)])
print("wrote", HERE)
