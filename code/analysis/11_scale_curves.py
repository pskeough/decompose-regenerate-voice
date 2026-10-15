"""11_scale_curves -- what parameter count buys, for the base model and for the adapter.

Arm A0 only, non-replicate cells. For every author x family, the base and adapter means of the
core measures against log2(parameters); the brief-paired adapter-minus-base gain at each size
with its replicate floor; the slope of that gain on size per author and pooled.

Outputs into analysis/11_scale_curves/:
    means.csv               author x family x size x kind x measure: mean with brief-cluster CI
    gain.csv                brief-paired adapter - base per author x family x size x measure
    slopes_per_author.csv   OLS of gain on log2(params) within an author x family
    pooled_models.csv       mixed models: gain, base level and adapter level on log2(params)
    tests.csv               the BH-FDR family for this script
    floors.csv              the replicate floor used for each measure and family
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from lib import *  # noqa: F401,F403

T0 = time.time()
OUTD = outdir("11_scale_curves")

CORE = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "styledist_cos_source",
        "geo_index", "open_entropy", "pct_short8", "otd_js", "per", "hapax_w300",
        "coverage", "truncated"]
LABEL = {m: (VARIABLES[m][0] if m in VARIABLES else m) for m in CORE}
DIRN = {m: (VARIABLES[m][3] if m in VARIABLES else "0") for m in CORE}
NBOOT = 2000

cells, runs, authors, briefs, refs = load_all()
d = main_cells(cells).copy()          # arm A0, non-replicate, base + adapter
d["truncated"] = d.truncated.astype(float)
d["log2_params"] = np.log2(d.params_b)

# ---------------------------------------------------------------- replicate floors
fl_rows = []
for m in CORE:
    t = replicate_floor(cells, m, arm="A0")
    for fam, g in t.groupby("family", observed=True):
        fl_rows.append({"measure": m, "family": fam, "n_pairs": int(g.pair.nunique()),
                        "floor": float(g.abs_mean_diff.max()), "floor_source": "measured"})
fl = pd.DataFrame(fl_rows)
have = set(zip(fl.measure, fl.family))
qwen = fl[fl.family == "Qwen3"].set_index("measure").floor.to_dict()
for m in CORE:
    for fam in sorted(d.family.unique()):
        if (m, fam) not in have and m in qwen:
            fl = pd.concat([fl, pd.DataFrame([{"measure": m, "family": fam, "n_pairs": 0,
                                               "floor": qwen[m], "floor_source": "borrowed from Qwen3"}])],
                           ignore_index=True)
write_table(fl, os.path.join(OUTD, "floors.csv"), floats=6)
FLOOR = {(r.measure, r.family): (r.floor, r.floor_source) for r in fl.itertuples()}

# ---------------------------------------------------------------- 1. means with CI
mean_rows = []
for (au, fam, pb, kind), g in d.groupby(["author", "family", "params_b", "kind"], observed=True):
    for m in CORE:
        sub = g[["id", m]].dropna()
        if not len(sub):
            mean_rows.append({"author": au, "family": fam, "params_b": pb, "kind": kind,
                              "measure": m, "n_cells": 0, "n_briefs": 0,
                              "mean": np.nan, "ci_low": np.nan, "ci_high": np.nan})
            continue
        pt, lo, hi = cluster_bootstrap(sub, m, "id", n=NBOOT, seed=7)
        mean_rows.append({"author": au, "family": fam, "params_b": pb, "kind": kind, "measure": m,
                          "n_cells": int(len(sub)), "n_briefs": int(sub.id.nunique()),
                          "mean": pt, "ci_low": lo, "ci_high": hi})
means = pd.DataFrame(mean_rows)
means["author_class"] = means.author.map(AUTHOR_CLASS)
means["log2_params"] = np.log2(means.params_b)
means["ci_width"] = means.ci_high - means.ci_low
means = means.sort_values(["measure", "family", "params_b", "author", "kind"])
write_table(means, os.path.join(OUTD, "means.csv"))

# ---------------------------------------------------------------- 2. brief-paired gain
base = d[d.kind == "base"]
adap = d[d.kind == "adapter"]
key = ["author", "family", "params_b", "id", "sample"]
pair = base.merge(adap, on=key, suffixes=("_b", "_a"))

gain_rows = []
for (au, fam, pb), g in pair.groupby(["author", "family", "params_b"], observed=True):
    for m in CORE:
        sub = g[["id", f"{m}_b", f"{m}_a"]].dropna()
        if len(sub) < 4:
            continue
        sub = sub.assign(diff=sub[f"{m}_a"] - sub[f"{m}_b"])
        pt, lo, hi = cluster_bootstrap(sub, "diff", "id", n=NBOOT, seed=11)
        per_brief = sub.groupby("id")["diff"].mean()
        try:
            p = float(wilcoxon(per_brief.values).pvalue) if per_brief.nunique() > 1 else np.nan
        except Exception:
            p = np.nan
        floor, fsrc = FLOOR.get((m, fam), (np.nan, "none"))
        gain_rows.append({"author": au, "author_class": AUTHOR_CLASS[au], "family": fam,
                          "params_b": pb, "log2_params": float(np.log2(pb)), "measure": m,
                          "n_pairs": int(len(sub)), "n_briefs": int(sub.id.nunique()),
                          "base_mean": float(sub[f"{m}_b"].mean()),
                          "adapter_mean": float(sub[f"{m}_a"].mean()),
                          "gain": pt, "ci_low": lo, "ci_high": hi,
                          "cohens_d": cohens_d(sub[f"{m}_a"], sub[f"{m}_b"]),
                          "cliffs_delta": cliffs_delta(sub[f"{m}_a"].values, sub[f"{m}_b"].values),
                          "p_wilcoxon_brief": p, "floor": floor, "floor_source": fsrc,
                          "abs_gain_over_floor": abs(pt) / floor if floor and floor == floor else np.nan,
                          "within_noise": bool(abs(pt) < floor) if floor == floor else None,
                          "ci_excludes_zero": bool(lo > 0 or hi < 0),
                          "direction": DIRN[m]})
gain = pd.DataFrame(gain_rows)
gain["q_wilcoxon"] = np.nan
for m, g in gain.groupby("measure", observed=True):
    gain.loc[g.index, "q_wilcoxon"] = bh_fdr(g.p_wilcoxon_brief.values)
gain["survives"] = (gain.q_wilcoxon < 0.05) & (~gain.within_noise.fillna(True)) & gain.ci_excludes_zero
gain = gain.sort_values(["measure", "family", "params_b", "author"])
write_table(gain, os.path.join(OUTD, "gain.csv"))

# ---------------------------------------------------------------- 3. per-author slope of gain on size
slope_rows = []
for (au, fam, m), g in gain.groupby(["author", "family", "measure"], observed=True):
    g = g.dropna(subset=["gain"])
    if g.params_b.nunique() < 3:
        continue
    x = g.log2_params.values; y = g.gain.values
    A = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ coef
    dof = len(x) - 2
    se = np.nan
    if dof > 0:
        s2 = float(resid @ resid) / dof
        cov = s2 * np.linalg.pinv(A.T @ A)
        se = float(np.sqrt(cov[1, 1]))
    ss_tot = float(((y - y.mean()) ** 2).sum())
    slope_rows.append({"author": au, "author_class": AUTHOR_CLASS[au], "family": fam, "measure": m,
                       "n_sizes": int(g.params_b.nunique()), "intercept": float(coef[0]),
                       "slope_per_doubling": float(coef[1]), "slope_se": se,
                       "r2": float(1 - (resid @ resid) / ss_tot) if ss_tot > 0 else np.nan,
                       "gain_at_min_size": float(g.sort_values("params_b").gain.iloc[0]),
                       "gain_at_max_size": float(g.sort_values("params_b").gain.iloc[-1])})
slopes = pd.DataFrame(slope_rows).sort_values(["measure", "family", "author"])
write_table(slopes, os.path.join(OUTD, "slopes_per_author.csv"))

slope_summary = []
for (m, fam), g in slopes.groupby(["measure", "family"], observed=True):
    pt, lo, hi = bootstrap_ci(g.slope_per_doubling.values, np.mean, n=NBOOT, seed=13)
    slope_summary.append({"measure": m, "family": fam, "n_authors": int(g.author.nunique()),
                          "mean_slope_per_doubling": pt, "ci_low": lo, "ci_high": hi,
                          "n_authors_positive": int((g.slope_per_doubling > 0).sum())})
slope_summary = pd.DataFrame(slope_summary)
write_table(slope_summary, os.path.join(OUTD, "slopes_summary.csv"))

# ---------------------------------------------------------------- 4. pooled mixed models
model_rows, test_rows = [], []


def add_model(measure, label, df, formula, groups="author"):
    res, tidy = mixed_model(df, formula, groups=groups)
    if not len(tidy):
        model_rows.append({"measure": measure, "model": label, "term": "fit_failed",
                           "estimate": np.nan, "se": np.nan, "ci_low": np.nan, "ci_high": np.nan,
                           "p": np.nan, "n_obs": len(df), "n_groups": df[groups].nunique(),
                           "note": "too few groups or rows"})
        return
    if "fit_failed" in set(tidy.term):
        tidy = tidy.assign(measure=measure, model=label)
        model_rows.extend(tidy.to_dict("records"))
        return
    tidy = tidy.assign(measure=measure, model=label)
    model_rows.extend(tidy.to_dict("records"))
    for term in tidy.term:
        if term in ("Intercept", "Group Var"):
            continue
        r = tidy[tidy.term == term].iloc[0]
        test_rows.append({"measure": measure, "model": label, "term": term,
                          "estimate": float(r.estimate), "ci_low": float(r.ci_low),
                          "ci_high": float(r.ci_high), "p": float(r.p),
                          "n_obs": int(r.n_obs), "n_groups": int(r.n_groups)})


for m in CORE:
    g = gain[gain.measure == m].dropna(subset=["gain"]).copy()
    if len(g) >= 20 and g.author.nunique() >= 3:
        if g.family.nunique() > 1:
            add_model(m, "gain ~ log2_params * family + (1|author)", g, "gain ~ log2_params * C(family)")
        else:
            add_model(m, "gain ~ log2_params + (1|author)", g, "gain ~ log2_params")
    for kind in ("base", "adapter"):
        cellsk = d[d.kind == kind][["author", "family", "log2_params", m]].dropna().copy()
        cellsk = cellsk.rename(columns={m: "y"})
        if len(cellsk) >= 20 and cellsk.author.nunique() >= 3:
            if cellsk.family.nunique() > 1:
                add_model(m, f"{kind} level ~ log2_params * family + (1|author)", cellsk,
                          "y ~ log2_params * C(family)")
            else:
                add_model(m, f"{kind} level ~ log2_params + (1|author)", cellsk, "y ~ log2_params")

models = pd.DataFrame(model_rows)
write_table(models, os.path.join(OUTD, "pooled_models.csv"), floats=6)

tests = pd.DataFrame(test_rows)
tests["q"] = bh_fdr(tests.p.values)
tests["significant_q05"] = tests.q < 0.05
tests["term_kind"] = np.where(tests.term.str.contains(":"), "family x size interaction",
                              np.where(tests.term == "log2_params", "size slope", "family main effect"))
tests = tests.sort_values(["model", "measure", "term"])
write_table(tests, os.path.join(OUTD, "tests.csv"), floats=6)

# ---------------------------------------------------------------- figures
AU_COLORS = {a: plt.cm.tab20(i % 20) for i, a in enumerate(sorted(d.author.unique()))}
STYLE = {"Qwen3": "-", "Ministral3": "--"}
FAM_COLOR = {"Qwen3": "C1", "Ministral3": "C0"}


def grid(values, title, fname, ylab_fn):
    fig, axes = plt.subplots(4, 3, figsize=(15, 15), sharex=True)
    for ax, m in zip(axes.ravel(), CORE):
        sub = values[values.measure == m]
        for (au, fam), g in sub.groupby(["author", "family"], observed=True):
            g = g.sort_values("log2_params")
            if len(g) < 2:
                ax.plot(g.log2_params, g.y, "o", color=AU_COLORS[au], ms=4)
                continue
            ax.plot(g.log2_params, g.y, STYLE.get(fam, ":"), color=AU_COLORS[au], lw=1.3,
                    marker="o", ms=3.5)
        ax.set_title(m, fontsize=10)
        ax.set_ylabel(ylab_fn(m), fontsize=7)
        ax.grid(alpha=0.25)
        ax.axhline(0, color="k", lw=0.6) if values is gains_long else None
    for ax in axes[-1]:
        ax.set_xlabel("log2(parameters, B)")
        ax.set_xticks(sorted(values.log2_params.unique()))
        ax.set_xticklabels([f"{2 ** v:g}" for v in sorted(values.log2_params.unique())], fontsize=7)
    handles = [plt.Line2D([], [], color=AU_COLORS[a], lw=2, label=a) for a in sorted(values.author.unique())]
    handles += [plt.Line2D([], [], color="k", ls=STYLE[f], lw=1.5, label=f) for f in sorted(values.family.unique())]
    fig.legend(handles=handles, loc="lower center", ncol=8, fontsize=8, frameon=False)
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=[0, 0.05, 1, 0.98])
    return savefig(fig, os.path.join(OUTD, fname))


gains_long = gain.rename(columns={"gain": "y"})
figs = []
for kind, fname, title in [("base", "fig_scale_base.png", "Base model, arm A0: measure against parameter count"),
                           ("adapter", "fig_scale_adapter.png", "Pair-6 adapter, arm A0: measure against parameter count")]:
    v = means[means.kind == kind].rename(columns={"mean": "y"})
    figs.append((title, grid(v, title, fname, lambda m: textwrap.fill(LABEL[m], 34))))
figs.append(("Adapter minus base gain against parameter count",
             grid(gains_long, "Adapter minus base (brief-paired), arm A0", "fig_gain_vs_size.png",
                  lambda m: textwrap.fill("adapter - base, " + LABEL[m], 34))))

# floor-referenced gain summary figure
fig, axes = plt.subplots(4, 3, figsize=(15, 14), sharex=True)
for ax, m in zip(axes.ravel(), CORE):
    sub = gain[gain.measure == m]
    for fam, g in sub.groupby("family", observed=True):
        agg = g.groupby("params_b").gain.agg(["mean", "count"]).reset_index()
        x = np.log2(agg.params_b) + (0.03 if fam == "Qwen3" else -0.03)
        ax.plot(x, agg["mean"], STYLE.get(fam, ":"), marker="s", label=fam, color=FAM_COLOR[fam])
        floor = FLOOR.get((m, fam), (np.nan, ""))[0]
        ax.axhspan(-floor, floor, color=FAM_COLOR[fam], alpha=0.10)
    ax.axhline(0, color="k", lw=0.7)
    ax.set_title(m, fontsize=9); ax.grid(alpha=0.25)
    ax.set_ylabel("mean gain over authors", fontsize=7)
for ax in axes[-1]:
    ax.set_xlabel("log2(parameters, B)")
axes[0, 0].legend(fontsize=7)
fig.suptitle("Adapter gain averaged over authors, with the replicate floor shaded", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.97])
figs.append(("Mean gain over authors against the replicate floor",
             savefig(fig, os.path.join(OUTD, "fig_gain_vs_floor.png"))))

# ---------------------------------------------------------------- README numbers
runtime = time.time() - T0
n_gain = len(gain)
n_survive = int(gain.survives.sum())
n_below_floor = int(gain.within_noise.fillna(False).sum())
failed = models[models.term == "fit_failed"].reindex(columns=["measure", "model", "note"])  # `note` exists only when a fit failed
size_slope = tests[(tests.term == "log2_params") & (tests.model.str.startswith("gain"))]
base_slope = tests[(tests.term == "log2_params") & (tests.model.str.startswith("base level"))]
adap_slope = tests[(tests.term == "log2_params") & (tests.model.str.startswith("adapter level"))]
inter = tests[tests.term_kind == "family x size interaction"]

headline = (gain.groupby(["measure", "family", "params_b"])
            .agg(mean_gain=("gain", "mean"), n_authors=("author", "nunique"),
                 n_survive=("survives", "sum"), floor=("floor", "first"))
            .reset_index())
headline["mean_gain_over_floor"] = headline.mean_gain.abs() / headline.floor
hl_voice = headline[headline.measure.isin(["luar_cos_source", "luar_cos_ref", "wegmann_cos_source",
                                           "styledist_cos_source", "otd_js", "per", "coverage", "truncated"])]

best = gain[gain.measure == "luar_cos_source"].groupby("params_b").gain.mean()
q_min_size = size_slope.sort_values("q").head(12)[["measure", "estimate", "ci_low", "ci_high", "p", "q", "n_groups"]]

# ---- README-only helpers. Every number in the written piece is read back out of the tables
# this script wrote; none of it is typed by hand.
_sv = gain[gain.survives].copy()
_sv["toward"] = _sv.direction.map({"+": 1.0, "-": -1.0}) * np.sign(_sv.gain)
n_toward = int((_sv.toward > 0).sum())
n_away = int((_sv.toward < 0).sum())
n_directionless = int(len(_sv) - n_toward - n_away)
away_by_measure = _sv[_sv.toward < 0].groupby("measure").size().sort_values(ascending=False)
cov_surv = int((_sv.measure == "coverage").sum())
cov_away = int(away_by_measure.get("coverage", 0))
n_size_slope_terms = int(len(size_slope))
n_size_slope_q05 = int((size_slope.q < 0.05).sum())
base_q05 = sorted(base_slope.loc[base_slope.q < 0.05, "measure"])
adap_q05 = sorted(adap_slope.loc[adap_slope.q < 0.05, "measure"])
floors_measured = fl[fl.floor_source == "measured"]
floors_borrowed = fl[fl.floor_source != "measured"]
borrowed_desc = ", ".join(sorted(f"{r.measure} on {r.family}" for r in floors_borrowed.itertuples()))
_pair_names = sorted(set(replicate_floor(cells, "luar_cos_source", arm="A0").pair))
_npq = floors_measured[floors_measured.family == "Qwen3"].n_pairs
_npm = floors_measured[floors_measured.family == "Ministral3"].n_pairs
pairs_qwen = int(_npq.max()) if len(_npq) else 0
pairs_min = int(_npm.max()) if len(_npm) else 0
max_gain_family = int(gain.groupby("measure").size().max())
q14 = gain[(gain.measure == "luar_cos_source") & (gain.params_b == 14) & (gain.family == "Qwen3")]
q04 = gain[(gain.measure == "luar_cos_source") & (gain.params_b == 4) & (gain.family == "Qwen3")]
min_authors = sorted(gain[gain.family == "Ministral3"].author.unique())
dup_authors = sorted(set(gain.author.unique()) & {"patrick", "patrick_v2"})
gate_fail_runs = sorted(runs.loc[runs.gate_generation_ok == False, "run"])  # noqa: E712
_dm8 = runs[runs.run == "doctorow_basem8b"]
_cm8 = runs[runs.run == "chesterton_paire6_m8b"]

write_readme(
    OUTD,
    "11 Scale curves: what parameter count buys",
    f"""
    For each author and model family, the base and adapter means of {len(CORE)} core measures
    against parameter count (arm A0, non-replicate cells), the brief-paired adapter-minus-base
    gain at each size, and whether that gain changes as the model gets bigger.

    Across {n_gain} author x family x size x measure contrasts, {n_survive} clear all three
    hurdles at once (BH-FDR q < 0.05 within the measure, a bootstrap interval excluding zero,
    and a gain larger than the measure's replicate floor). {n_below_floor} sit inside the floor
    and are reported as within noise whatever their p-value.

    Clearing the hurdles is not the same as moving toward the author. Of the {n_survive}
    surviving contrasts, {n_toward} move in the direction the variable dictionary marks as
    closer to the author, {n_away} move away from it, and {n_directionless} are on measures the
    dictionary marks directionless, where a difference has no better or worse. The largest
    blocks moving away are {", ".join(f"{m} ({n})" for m, n in away_by_measure.head(4).items())}.
    """,
    f"""
    Data. `data/master/cells.parquet`, arm A0 only, replicates excluded: {len(d)} cells over
    {d.author.nunique()} author rows, {d.family.nunique()} families and
    {d.params_b.nunique()} parameter counts. `truncated` is treated as a 0/1 rate.
    `coverage` exists on sample 0 only, so its contrasts rest on half the cells, and it is an
    LLM judge's reading of how much of the brief is present rather than a mechanical count.

    Unit. Within an author, the brief (`id`) is the cluster: every mean and every gain carries a
    cluster bootstrap over briefs ({NBOOT} draws). For any statement about models rather than
    about one author, the author is the unit: the per-author slopes are averaged with a
    bootstrap over authors, and the pooled models take one gain estimate per author x size as
    the observation with a random intercept for the author.

    Gain. Base and adapter cells are matched on (author, family, size, brief, sample) before
    subtracting, so the gain is a within-brief difference and the brief's own difficulty
    cancels. Effect sizes accompany it: Cohen's d and Cliff's delta over the unpaired cell
    values, and a Wilcoxon signed-rank test over the per-brief mean differences.

    Model. `lib.mixed_model` (statsmodels MixedLM, groups = author). Where both families are
    present the formula is `gain ~ log2_params * C(family)`; where only Qwen3 is present the
    interaction is dropped. Base and adapter levels are modelled the same way on cell-level
    values. With {gain.author.nunique()} authors the random-effect variances are descriptive.
    {len(failed)} of the {len(models[["measure", "model"]].drop_duplicates())}
    fitted models returned a singular matrix and are recorded as `fit_failed` in
    `pooled_models.csv` rather than being quietly dropped
    ({", ".join(f"{r.measure} ({r.model.split(' ~ ')[0]})" for r in failed.itertuples()) or "none"}).

    Correction. BH-FDR is applied twice and separately: within a measure across its
    author x family x size contrasts in `gain.csv` (at most {max_gain_family} tests in one such
    family), and across the {len(tests)} model terms in `tests.csv` that make up this script's
    own hypothesis family. A q below 0.05 means "within that family", not across the programme;
    the programme-wide correction is script 22's job.

    Floors. `lib.replicate_floor` on arm A0, from the twice-generated configurations
    ({", ".join(_pair_names)}), at most {pairs_qwen} pairs on Qwen3 and {pairs_min} on
    Ministral3. {len(floors_measured)} of the {len(fl)} measure x family floors in `floors.csv`
    are measured{"" if not len(floors_borrowed) else "; " + str(len(floors_borrowed)) + " (" + borrowed_desc + ") has no replicate pair of its own and carries the Qwen3 value, marked `borrowed from Qwen3`"}.
    A borrowed floor is an assumption, not a measurement.

    Runtime {runtime:.0f} s.
    """,
    f"""
    Unit of replication. Any claim of the form "adapters gain X at size S" is an author-level
    claim and has to be read off the author-level rows. On luar_cos_source it rests on
    {int(q14.author.nunique())} Qwen3 authors at 14B and {int(q04.author.nunique())} at 4B, not
    on the thousands of cells beneath them. Ministral3 rests on {len(min_authors)} authors at
    every size ({", ".join(min_authors)}), so no Ministral3 row here is a statement about the
    family. The per-cell rows in `gain.csv` are inputs to those author counts, not independent
    evidence.

    Size. Of the {n_size_slope_terms} measures modelled, {n_size_slope_q05} size slopes on the
    gain reach q < 0.05 within this script's family of {len(tests)} terms, so nothing here
    supports the statement that an adapter buys more at 14B than at 4B on any measure. What does
    move with size is the base model on {len(base_q05)} measures ({", ".join(base_q05) or "none"})
    and the adapter endpoint on {len(adap_q05)} ({", ".join(adap_q05) or "none"}). Coverage and
    truncation are among them, which is consistent with larger base models following the brief
    and running longer, not with larger models being closer to the author.

    Interval width. A typical brief-cluster interval on a single author's gain in
    luar_cos_source is about
    {float((gain[(gain.measure == 'luar_cos_source')].ci_high - gain[(gain.measure == 'luar_cos_source')].ci_low).median()):.3f}
    wide, against a Qwen3 mean gain at 14B of {float(q14.gain.mean()):.3f} over
    {int(q14.author.nunique())} authors. Intervals that wide can hide a doubling or a halving of
    the effect. The families are not pooled in that comparison: their 14B means differ, and a
    mean over both would describe neither.

    Floor. The floor is the largest mean difference between a run and its own regeneration. A
    gain smaller than that is indistinguishable from generating the same configuration twice.
    In `gain.csv` the column `abs_gain_over_floor` is the number to read first; anything under
    1.0 should not be described as an effect, whatever its q.
    {"" if not len(floors_borrowed) else "The one borrowed floor (" + borrowed_desc + ") is probably too small, because Ministral3 truncates more often than Qwen3, and that is the direction that would widen its true jitter."}

    Judged measures. `coverage` is an LLM judge's reading of brief adherence, so a coverage gain
    is a judge's reading and not a measurement. {cov_away} of the {cov_surv} surviving coverage
    contrasts move away from the author's brief, which is the largest single block of adverse
    survivors in this script. No 2AFC or rubric measure enters this script at all.

    What would overturn this. A third generation of any configuration at 8B or 14B, where no
    replicate pair exists (every pair behind these floors is a 4B or 3B run); a measured floor
    for {borrowed_desc or "the borrowed cells"}; or dropping the {len(gate_fail_runs)} runs that
    fail the generation gate, several of which are 14B adapters with high truncation. Any of
    those could move a size slope's sign for the measures whose gains sit near the floor.

    What this does not show. Nothing about prompting arms (A0 only here), nothing about which
    adapter is better in a human's judgement, and nothing causal about parameter count: the
    sizes are three or four fixed checkpoints of two model families, not a manipulated variable,
    and the 1.7B point exists for one author only. A gain is a difference between two runs of
    the same author, so it says the adapter changed the text, not that the change is one a
    reader would call the author's voice.
    """,
    caveats=[
        f"Only Qwen3 has more than {len(min_authors)} authors at any size; the Ministral3 columns are {', '.join(min_authors)} throughout, so a Ministral3 size slope is an average over {len(min_authors)} corpora and is reported as such, never as a family result.",
        f"`patrick` and `patrick_v2` are the same corpus at two chunk sizes, so the {int(d.author.nunique())} author rows here are {int(d.author.nunique()) - (1 if len(dup_authors) > 1 else 0)} independent corpora; any pooled author count that includes both is counting one person twice.",
        f"Qwen3 1.7B exists for patrick_v2 alone ({int(d[(d.family == 'Qwen3') & (d.params_b == 1.7)].shape[0])} cells) and enters the pooled models as a single author; the per-author slopes for every other author span 4B, 8B and 14B only.",
        "`per`, `otd_js` and `hapax_w300` come from the eval cache, which was computed on arm A0 only; they carry values on A0 and NaN on A1 to A5. That is why this script is arm-A0 only, and it is why no A1 to A5 effect on those measures can be claimed anywhere in the programme.",
        f"`coverage` is an LLM-judged measure on sample 0 only, so its gains use {int(gain[gain.measure == 'coverage'].n_pairs.median())} paired cells per configuration at the median rather than twice that. Judge measures are relative instruments with known failures and are never read here as absolute quality.",
        "Coverage rows for several Qwen3 runs were error rows from the 2026-09-09 credit outage and were being refilled while this was written, so every coverage gain in these tables is provisional until the final rerun.",
        f"The two Ministral3 3B replicate runs behind the Ministral3 floors were scored on 2026-09-10, after the rest of the grid. The Ministral3 floors are therefore new and rest on 3B pairs only; nothing measures Ministral3 jitter at 8B or 14B, where the Ministral3 gains in this script are computed.",
        (f"`doctorow_basem8b` exceeds the 20% truncation gate ({float(_dm8.truncated_pct.iloc[0]):.1f}% truncated) and is flagged rather than excluded; it is the base half of the doctorow Ministral3 8B gain, so that row compares an adapter against a base that was cut off in a quarter of its passages."
         if len(_dm8) and pd.notna(_dm8.truncated_pct.iloc[0]) else
         "`doctorow_basem8b` exceeds the 20% truncation gate and is flagged rather than excluded."),
        (f"`chesterton_paire6_m8b` has a positive probe delta ({float(_cm8.probe_delta.iloc[0]):+.4f}), meaning training moved the probe the wrong way and the adapter changed nothing the probe could measure; the chesterton Ministral3 8B gains rest on that adapter."
         if len(_cm8) and pd.notna(_cm8.probe_delta.iloc[0]) else
         "`chesterton_paire6_m8b` has a positive probe delta; the chesterton Ministral3 8B gains rest on that adapter."),
        f"{len(gate_fail_runs)} runs fail the generation gate and are included here without adjustment; the highest-truncation adapter run reaches {float(runs.truncated_pct.max()):.0f}% truncated, which will distort any length-sensitive measure in that cell.",
        "The `*_cos_ref` and attribution measures are anchored against a stranger pool of fourteen period authors for every study author, so the contemporary and private authors are positioned against another century. `scripts/23_register_matched_pool.py` holds the register-matched repair; the luar_cos_ref rows here have not had it applied.",
        "Per-author slopes are fitted on three points (four for patrick_v2), so their standard errors have one or two degrees of freedom and are reported for completeness, not for inference.",
        "The replicate floor is a maximum over a handful of pairs, so it is a lower bound on the true run-to-run jitter more often than an upper one.",
        f"The limit on every pooled statement here is the number of author corpora, not the number of tests: {int(gain.author.nunique())} authors carry the whole grid, and BH-FDR within a family of {max_gain_family} does nothing about that.",
    ],
    tables=[
        ("Mean adapter gain by measure, family and size, against the replicate floor", hl_voice),
        ("Does the gain change with size (mixed model, log2_params term, BH-FDR within the script)", q_min_size),
        ("Does the base model improve with size (log2_params term)",
         base_slope[["measure", "estimate", "ci_low", "ci_high", "p", "q", "significant_q05"]]),
        ("Does the adapter endpoint improve with size (log2_params term)",
         adap_slope[["measure", "estimate", "ci_low", "ci_high", "p", "q", "significant_q05"]]),
        ("Family x size interactions", inter[["measure", "model", "term", "estimate", "ci_low", "ci_high", "p", "q"]]),
        ("Mixed models that failed to fit", failed),
        ("Mean per-author slope of gain on log2(params)", slope_summary),
        ("Contrasts that clear q < 0.05, a non-zero interval and the replicate floor",
         gain[gain.survives][["author", "family", "params_b", "measure", "gain", "ci_low", "ci_high",
                              "floor", "abs_gain_over_floor", "q_wilcoxon"]].sort_values(
             "abs_gain_over_floor", ascending=False)),
    ],
    figures=figs,
)

print(f"[11] wrote {len(os.listdir(OUTD))} files to {OUTD} in {runtime:.1f}s")
print(hl_voice.to_string(index=False))
