"""14_style_construction_tradeoff -- does an adapter buy voice at construction's expense?

Per configuration (author x family x size x kind, arm A0) the script builds a voice axis
(luar_cos_ref, wegmann_cos_source, 1 - otd_js normalised) and a construction axis
(1 - per, 1 - terminal_missing; extended with coverage/100 and rubric_C/10 where they
exist), takes the brief-paired adapter-minus-base delta on both axes, tests the sign of
the pair over authors, and fits the slope of construction change on voice change.

Reads data/master only. Writes analysis/14_style_construction_tradeoff only.
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *  # noqa: F401,F403

from scipy.stats import wilcoxon, binomtest, spearmanr

T0 = time.time()
OUTD = outdir("14_style_construction_tradeoff")
RNG = 0
NBOOT = 2000

# ---------------------------------------------------------------- components
# name: (source column, orientation transform, axis, label)
VOICE_CORE = ["luar_cos_ref", "wegmann_cos_source", "otd_inv"]
CONSTR_CORE = ["per_inv", "term_ok"]
CONSTR_EXT = ["per_inv", "term_ok", "cov_frac", "rubric_C10"]
COMP_LABEL = {
    "luar_cos_ref": "LUAR cosine to the author's reference set",
    "wegmann_cos_source": "Wegmann cosine to the source",
    "otd_inv": "1 - opener-class distance (normalised)",
    "per_inv": "1 - proposition-echo rate (600-word cap)",
    "term_ok": "last brief event present",
    "cov_frac": "judged brief coverage / 100",
    "rubric_C10": "rubric construction block / 10",
}
COMP_RAW = {  # component -> the raw dictionary measure its replicate floor is taken on
    "luar_cos_ref": "luar_cos_ref", "wegmann_cos_source": "wegmann_cos_source", "otd_inv": "otd_js",
    "per_inv": "per", "term_ok": "terminal_missing", "cov_frac": "coverage", "rubric_C10": "rubric_C",
}
KEYS = ["author", "family", "params_b"]

print("[14] loading", flush=True)
cells, runs, authors, briefs, refs = load_all()
d = main_cells(cells).copy()                      # arm A0, non-replicate, both kinds, both samples
n_cells_a0 = len(d)
n_runs_a0 = d.run.nunique()

# ---------------------------------------------------------------- build components
otd_q95 = float(np.nanquantile(d["otd_js"], 0.95))
d["otd_inv"] = 1.0 - d["otd_js"] / otd_q95
d["per_inv"] = 1.0 - d["per"]
d["term_ok"] = 1.0 - d["terminal_missing"]
d["cov_frac"] = d["coverage"] / 100.0
d["rubric_C10"] = d["rubric_C"] / 10.0
ALL_COMP = VOICE_CORE + CONSTR_EXT

# configuration-level means (the unit the axis scale is calibrated on)
cfg = (d.groupby(KEYS + ["kind"], as_index=False)
         .agg(n_cells=("id", "size"), n_briefs=("id", "nunique"),
              **{c: (c, "mean") for c in ALL_COMP},
              words=("words", "mean"), author_class=("author_class", "first"), run=("run", "first")))

# robust affine scale per component: 0 = 5th pct configuration, 1 = 95th pct configuration
scale = {}
for c in ALL_COMP:
    lo, hi = np.nanquantile(cfg[c], 0.05), np.nanquantile(cfg[c], 0.95)
    if not np.isfinite(hi - lo) or hi - lo <= 0:
        lo, hi = np.nanmin(cfg[c]), np.nanmax(cfg[c])
    scale[c] = (float(lo), float(hi))
    d[c + "_s"] = (d[c] - lo) / (hi - lo)
    cfg[c + "_s"] = (cfg[c] - lo) / (hi - lo)

scale_tbl = pd.DataFrame([{"component": c, "measure": COMP_RAW[c], "axis": ("voice" if c in VOICE_CORE else "construction"),
                           "label": COMP_LABEL[c], "q05_config_mean": scale[c][0], "q95_config_mean": scale[c][1],
                           "cells_with_value": int(d[c].notna().sum()),
                           "configs_with_value": int(cfg[c].notna().sum())} for c in ALL_COMP])
write_table(scale_tbl, os.path.join(OUTD, "axis_components.csv"), floats=5)

# cell-level axes (core components only: present on essentially every cell, so the paired
# delta is like-for-like); extended construction axis is built at configuration level only.
d["voice_axis"] = d[[c + "_s" for c in VOICE_CORE]].mean(axis=1)
d["constr_axis"] = d[[c + "_s" for c in CONSTR_CORE]].mean(axis=1)
cfg["voice_axis"] = cfg[[c + "_s" for c in VOICE_CORE]].mean(axis=1)
cfg["constr_axis"] = cfg[[c + "_s" for c in CONSTR_CORE]].mean(axis=1)
cfg["constr_axis_ext"] = cfg[[c + "_s" for c in CONSTR_EXT]].mean(axis=1, skipna=True)
cfg["ext_n_components"] = cfg[[c + "_s" for c in CONSTR_EXT]].notna().sum(axis=1)
cfg["dist_to_11"] = np.sqrt((1 - cfg.voice_axis) ** 2 + (1 - cfg.constr_axis) ** 2)

cfg_out = cfg[KEYS + ["kind", "run", "author_class", "n_cells", "n_briefs", "words"] + ALL_COMP +
              ["voice_axis", "constr_axis", "constr_axis_ext", "ext_n_components", "dist_to_11"]].sort_values(KEYS + ["kind"])
write_table(cfg_out, os.path.join(OUTD, "configuration_axes.csv"), floats=5)
n_cfg = len(cfg_out)

# ---------------------------------------------------------------- replicate floors
floor_rows = []
for c in ALL_COMP + ["voice_axis", "constr_axis"]:
    # floors are computed on the master cells table so the replicate runs are present
    base = cells.copy()
    if c == "otd_inv":
        base["otd_inv"] = 1.0 - base["otd_js"] / otd_q95
    elif c == "per_inv":
        base["per_inv"] = 1.0 - base["per"]
    elif c == "term_ok":
        base["term_ok"] = 1.0 - base["terminal_missing"]
    elif c == "cov_frac":
        base["cov_frac"] = base["coverage"] / 100.0
    elif c == "rubric_C10":
        base["rubric_C10"] = base["rubric_C"] / 10.0
    elif c in ("voice_axis", "constr_axis"):
        base["otd_inv"] = 1.0 - base["otd_js"] / otd_q95
        base["per_inv"] = 1.0 - base["per"]
        base["term_ok"] = 1.0 - base["terminal_missing"]
        for cc in ALL_COMP:
            if cc in base.columns:
                lo, hi = scale[cc]
                base[cc + "_s"] = (base[cc] - lo) / (hi - lo)
        base["voice_axis"] = base[[x + "_s" for x in VOICE_CORE]].mean(axis=1)
        base["constr_axis"] = base[[x + "_s" for x in CONSTR_CORE]].mean(axis=1)
    t = replicate_floor(base, c)
    if len(t):
        for fam, g in t.groupby("family"):
            floor_rows.append({"component": c, "family": fam, "n_pairs": len(g),
                               "floor_max_abs_mean_diff": float(g.abs_mean_diff.max()),
                               "floor_median": float(g.abs_mean_diff.median())})
    else:
        floor_rows.append({"component": c, "family": "Qwen3", "n_pairs": 0,
                           "floor_max_abs_mean_diff": np.nan, "floor_median": np.nan})
floors = pd.DataFrame(floor_rows)
n_floor_pairs_qwen = int(floors[floors.family == 'Qwen3'].n_pairs.max())
n_floor_pairs_min = int(floors[floors.family == 'Ministral3'].n_pairs.max()) if (floors.family == 'Ministral3').any() else 0
# no Ministral replicate pair survives in cells.parquet; record that explicitly
fams_with_floor = sorted(floors[floors.n_pairs > 0].family.unique())
missing_fam_floor = [f for f in ["Qwen3", "Ministral3"] if f not in fams_with_floor]
for f in missing_fam_floor:
    for c in ALL_COMP + ["voice_axis", "constr_axis"]:
        q = floors[(floors.component == c) & (floors.family == "Qwen3")]
        floors = pd.concat([floors, pd.DataFrame([{
            "component": c, "family": f, "n_pairs": 0,
            "floor_max_abs_mean_diff": float(q.floor_max_abs_mean_diff.iloc[0]) if len(q) else np.nan,
            "floor_median": float(q.floor_median.iloc[0]) if len(q) else np.nan}])], ignore_index=True)
floors["borrowed_from_Qwen3"] = floors.n_pairs.eq(0)
write_table(floors.sort_values(["component", "family"]), os.path.join(OUTD, "replicate_floors.csv"), floats=5)
FLOOR = {(r.component, r.family): r.floor_max_abs_mean_diff for r in floors.itertuples()}

# ---------------------------------------------------------------- brief-paired deltas
print(f"[14] pairing base/adapter, {n_cfg} configurations", flush=True)
pair_cols = ALL_COMP + ["voice_axis", "constr_axis", "words"]
bas = d[d.kind == "base"][KEYS + ["id", "sample", "author_class"] + pair_cols]
ada = d[d.kind == "adapter"][KEYS + ["id", "sample"] + pair_cols]
pair = bas.merge(ada, on=KEYS + ["id", "sample"], suffixes=("_base", "_ada"))
for c in pair_cols:
    pair["d_" + c] = pair[c + "_ada"] - pair[c + "_base"]
n_pairs_total = len(pair)

rows = []
for (au, fam, pb), g in pair.groupby(KEYS):
    for c in ["voice_axis", "constr_axis"] + ALL_COMP:
        col = "d_" + c
        gg = g[g[col].notna()]
        if not len(gg):
            rows.append({"author": au, "family": fam, "params_b": pb, "measure": c, "n_pairs": 0,
                         "n_briefs": 0, "delta": np.nan, "ci_low": np.nan, "ci_high": np.nan,
                         "cohens_d": np.nan, "cliffs_delta": np.nan, "p_perm": np.nan})
            continue
        pt, lo, hi = cluster_bootstrap(gg, col, "id", n=NBOOT, seed=RNG)
        obs, p = permutation_test(gg[c + "_ada"], gg[c + "_base"], n=2000, seed=RNG)
        rows.append({"author": au, "family": fam, "params_b": pb, "measure": c,
                     "n_pairs": int(len(gg)), "n_briefs": int(gg.id.nunique()),
                     "delta": pt, "ci_low": lo, "ci_high": hi,
                     "cohens_d": cohens_d(gg[c + "_ada"], gg[c + "_base"]),
                     "cliffs_delta": cliffs_delta(gg[c + "_ada"], gg[c + "_base"]),
                     "p_perm": p})
per_cfg = pd.DataFrame(rows)
per_cfg["q_bh"] = np.nan
for m, idx in per_cfg.groupby("measure").groups.items():
    per_cfg.loc[idx, "q_bh"] = bh_fdr(per_cfg.loc[idx, "p_perm"].values)
per_cfg["floor"] = [FLOOR.get((r.measure, r.family), np.nan) for r in per_cfg.itertuples()]
per_cfg["floor_known"] = per_cfg.floor.notna()
per_cfg["above_floor"] = per_cfg.delta.abs() > per_cfg.floor
per_cfg["verdict"] = np.where(~per_cfg.above_floor, "within noise",
                              np.where((per_cfg.q_bh < 0.05), "moves", "not significant"))
per_cfg.loc[~per_cfg.floor_known, "verdict"] = "no replicate floor for this component"
per_cfg = per_cfg.sort_values(["measure", "family", "params_b", "author"])
write_table(per_cfg, os.path.join(OUTD, "paired_deltas_by_configuration.csv"), floats=5)

# ---------------------------------------------------------------- author-level tests
USABLE = sorted(set(d.author.unique()) - {"patrick"})   # patrick is the v1-chunking control


def author_tests(sub, measure, label):
    """Sign test + Wilcoxon over authors on the per-author paired delta."""
    x = sub[sub.measure == measure].dropna(subset=["delta"])
    v = x.delta.values
    if len(v) < 2:
        return {"group": label, "measure": measure, "n_authors": int(len(v)), "mean_delta": float(np.mean(v)) if len(v) else np.nan,
                "ci_low": np.nan, "ci_high": np.nan, "median_delta": float(np.median(v)) if len(v) else np.nan,
                "n_positive": int((v > 0).sum()), "p_sign": np.nan, "p_wilcoxon": np.nan}
    m, lo, hi = bootstrap_ci(v, n=NBOOT, seed=RNG)
    npos = int((v > 0).sum()); nnz = int((v != 0).sum())
    p_sign = binomtest(npos, nnz, 0.5).pvalue if nnz else np.nan
    try:
        p_w = wilcoxon(v).pvalue if nnz >= 2 else np.nan
    except Exception:
        p_w = np.nan
    return {"group": label, "measure": measure, "n_authors": int(len(v)), "mean_delta": m, "ci_low": lo, "ci_high": hi,
            "median_delta": float(np.median(v)), "n_positive": npos, "p_sign": float(p_sign) if p_sign == p_sign else np.nan,
            "p_wilcoxon": float(p_w) if p_w == p_w else np.nan}


auth = per_cfg[per_cfg.author.isin(USABLE)]
rows = []
for meas in ["voice_axis", "constr_axis"] + ALL_COMP:
    for (fam, pb), g in auth.groupby(["family", "params_b"]):
        rows.append({**author_tests(g, meas, f"{fam}-{pb:g}B"), "family": fam, "params_b": pb})
    for fam, g in auth.groupby("family"):
        rows.append({**author_tests(g, meas, f"{fam} pooled"), "family": fam, "params_b": np.nan})
    rows.append({**author_tests(auth, meas, "all configurations"), "family": "both", "params_b": np.nan})
signtests = pd.DataFrame(rows)
signtests["q_sign_bh"] = bh_fdr(signtests.p_sign.values)
signtests["q_wilcoxon_bh"] = bh_fdr(signtests.p_wilcoxon.values)
def _floor_both(m):
    vals = [FLOOR.get((m, f), np.nan) for f in ("Qwen3", "Ministral3")]
    vals = [v for v in vals if v == v]
    return max(vals) if vals else np.nan          # pooled rows are read against the larger family floor


signtests["floor"] = [FLOOR.get((r.measure, r.family), np.nan) if r.family in ("Qwen3", "Ministral3") else _floor_both(r.measure)
                      for r in signtests.itertuples()]
signtests["floor_known"] = signtests.floor.notna()
signtests["above_floor"] = signtests.mean_delta.abs() > signtests.floor    # False where the floor is unknown; see floor_known
write_table(signtests, os.path.join(OUTD, "author_level_tests.csv"), floats=5)

# sensitivity: include patrick (v1 chunking control)
rows = []
for meas in ["voice_axis", "constr_axis"]:
    rows.append({**author_tests(per_cfg, meas, "all configurations, patrick(v1) included"), "family": "both", "params_b": np.nan})
sens_patrick = pd.DataFrame(rows).drop(columns=["params_b"])
write_table(sens_patrick, os.path.join(OUTD, "sensitivity_include_patrick_v1.csv"), floats=5)

# ---------------------------------------------------------------- trade-off slope
wide = (per_cfg[per_cfg.measure.isin(["voice_axis", "constr_axis"])]
        .pivot_table(index=KEYS, columns="measure", values="delta").reset_index().dropna())
wide = wide.merge(d[["author", "author_class"]].drop_duplicates(), on="author", how="left")


def slope_ci(sub, n=NBOOT, seed=RNG):
    """OLS slope of construction delta on voice delta; bootstrap over authors."""
    # fewer than four points cannot support a slope: a three-point Spearman is +-1 by
    # construction and scipy returns p = 0 for it, which is an artefact, not a result.
    sub = sub.dropna(subset=["voice_axis", "constr_axis"])
    if len(sub) < 4 or sub.author.nunique() < 3:
        return dict(n_points=len(sub), n_authors=int(sub.author.nunique()), slope=np.nan, slope_lo=np.nan,
                    slope_hi=np.nan, intercept=np.nan, rho=np.nan, rho_p=np.nan)
    x, y = sub.voice_axis.values, sub.constr_axis.values
    b, a = np.polyfit(x, y, 1)
    aus = sorted(sub.author.unique()); rng = np.random.default_rng(seed); bs = []
    for _ in range(n):
        pick = rng.integers(0, len(aus), size=len(aus))
        s = pd.concat([sub[sub.author == aus[i]] for i in pick])
        if s.voice_axis.nunique() < 2:
            continue
        bs.append(np.polyfit(s.voice_axis.values, s.constr_axis.values, 1)[0])
    r, p = spearmanr(x, y)
    return dict(n_points=int(len(sub)), n_authors=int(sub.author.nunique()), slope=float(b),
                slope_lo=float(np.quantile(bs, 0.025)) if bs else np.nan,
                slope_hi=float(np.quantile(bs, 0.975)) if bs else np.nan,
                intercept=float(a), rho=float(r), rho_p=float(p))


srows = [{"group": "all configurations", **slope_ci(wide[wide.author.isin(USABLE)])}]
for fam, g in wide[wide.author.isin(USABLE)].groupby("family"):
    srows.append({"group": f"{fam} pooled", **slope_ci(g)})
for (fam, pb), g in wide[wide.author.isin(USABLE)].groupby(["family", "params_b"]):
    srows.append({"group": f"{fam}-{pb:g}B", **slope_ci(g)})
for ac, g in wide[wide.author.isin(USABLE)].groupby("author_class"):
    srows.append({"group": f"author_class = {ac}", **slope_ci(g)})
slopes = pd.DataFrame(srows)
slopes["q_bh"] = bh_fdr(slopes.rho_p.values)
write_table(slopes, os.path.join(OUTD, "tradeoff_slope.csv"), floats=5)

# ---------------------------------------------------------------- length flags
lrows = []
for c in ALL_COMP + ["voice_axis", "constr_axis"]:
    r, lo, hi, p, n = spearman_ci(d[c], d["words"], n=500, seed=RNG)
    lrows.append({"measure": c, "rho_with_words": r, "ci_low": lo, "ci_high": hi, "p": p, "n": n,
                  "length_flag": abs(r) >= 0.4 if r == r else False})
lenflags = pd.DataFrame(lrows)
lenflags["q_bh"] = bh_fdr(lenflags.p.values)
write_table(lenflags, os.path.join(OUTD, "length_flags.csv"), floats=5)
flagged = sorted(lenflags[lenflags.length_flag].measure.tolist())

# length null: adapter-vs-base on the axes with words as a covariate, author random effect
import warnings as _warnings
import statsmodels.formula.api as _smf


def _fit_lib(sub, formula):
    """lib.mixed_model (MixedLM, method=['lbfgs']), with singular fits recorded as such."""
    with _warnings.catch_warnings(record=True) as w:
        _warnings.simplefilter("always")
        _, tidy = mixed_model(sub, formula, groups="author")
    msgs = {str(x.message)[:70] for x in w}
    note = "; ".join(sorted(m for m in msgs if any(k in m.lower() for k in ("singular", "boundary", "hessian"))))
    if len(tidy):
        tidy["optimizer"] = "lib.mixed_model (lbfgs)"
        tidy["fit_note"] = note or "converged"
    return tidy


def _fit_default(sub, formula):
    """The same MixedLM with statsmodels' default optimiser, as a convergence check."""
    with _warnings.catch_warnings(record=True) as w:
        _warnings.simplefilter("always")
        try:
            r = _smf.mixedlm(formula, sub, groups=sub["author"]).fit(reml=True)
        except Exception as e:
            return pd.DataFrame([{"term": "fit_failed", "optimizer": "statsmodels default", "fit_note": repr(e)[:160]}])
    msgs = {str(x.message)[:70] for x in w}
    note = "; ".join(sorted(m for m in msgs if any(k in m.lower() for k in ("singular", "boundary", "hessian"))))
    ci = r.conf_int()
    tidy = pd.DataFrame({"term": r.params.index, "estimate": r.params.values, "se": r.bse.values,
                         "ci_low": ci[0].values, "ci_high": ci[1].values, "p": r.pvalues.values})
    tidy["n_obs"] = int(r.nobs); tidy["n_groups"] = int(sub.author.nunique())
    tidy["optimizer"] = "statsmodels default"; tidy["fit_note"] = note or "converged"
    return tidy


mm_rows = []
n_singular = n_fits = 0
for meas in ["voice_axis", "constr_axis"] + flagged:
    if meas not in d.columns:
        continue
    sub = d[d.author.isin(USABLE)][[meas, "kind", "words", "author", "params_b", "family"]].dropna()
    sub = sub.rename(columns={meas: "y"})
    sub["is_adapter"] = (sub.kind == "adapter").astype(float)
    sub["words_c"] = (sub.words - sub.words.mean()) / sub.words.std()
    for label, formula in [(meas, "y ~ is_adapter + words_c"), (meas + " (no words covariate)", "y ~ is_adapter")]:
        for fit in (_fit_lib, _fit_default):
            tidy = fit(sub, formula)
            if len(tidy):
                tidy.insert(0, "measure", label)
                n_fits += 1
                n_singular += int(tidy.fit_note.iloc[0] != "converged")
                mm_rows.append(tidy)
length_null = pd.concat(mm_rows, ignore_index=True) if mm_rows else pd.DataFrame()
if len(length_null):
    write_table(length_null, os.path.join(OUTD, "length_null_mixed_models.csv"), floats=5)


def mm_get(measure, term, col, opt="statsmodels default"):
    x = length_null[(length_null.measure == measure) & (length_null.term == term) & (length_null.optimizer == opt)]
    return float(x[col].iloc[0]) if len(x) else float("nan")

# ---------------------------------------------------------------- figures
SIZE_ORDER = [("Qwen3", 1.7), ("Qwen3", 4.0), ("Qwen3", 8.0), ("Qwen3", 14.0),
              ("Ministral3", 3.0), ("Ministral3", 8.0), ("Ministral3", 14.0)]
CLS_COLOR = {"period": "#1f77b4", "contemporary": "#d62728", "private": "#2ca02c"}

print("[14] figures", flush=True)
fig, axes = plt.subplots(2, 4, figsize=(19, 9.5), sharex=True, sharey=True)
for ax, (fam, pb) in zip(axes.ravel(), SIZE_ORDER):
    b = cfg[(cfg.family == fam) & (cfg.params_b == pb) & (cfg.kind == "base")].set_index("author")
    a = cfg[(cfg.family == fam) & (cfg.params_b == pb) & (cfg.kind == "adapter")].set_index("author")
    for au in sorted(set(b.index) & set(a.index)):
        col = CLS_COLOR.get(b.loc[au, "author_class"], "#666666")
        ax.annotate("", xy=(a.loc[au, "voice_axis"], a.loc[au, "constr_axis"]),
                    xytext=(b.loc[au, "voice_axis"], b.loc[au, "constr_axis"]),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.4, alpha=0.85))
        ax.scatter([b.loc[au, "voice_axis"]], [b.loc[au, "constr_axis"]], s=16, c=col, marker="o", zorder=3)
        ax.scatter([a.loc[au, "voice_axis"]], [a.loc[au, "constr_axis"]], s=26, c=col, marker="*", zorder=3)
        ax.annotate(au[:9], (a.loc[au, "voice_axis"], a.loc[au, "constr_axis"]), fontsize=6,
                    xytext=(2, 2), textcoords="offset points", color=col)
    ax.set_title(f"{fam} {pb:g}B  (n authors = {len(set(b.index) & set(a.index))})", fontsize=10)
    ax.grid(alpha=0.25, lw=0.5)
    ax.margins(0.10)
fig.supxlabel("voice axis: LUAR-to-reference, Wegmann-to-source, 1 - opener-class distance (study-span scale)", fontsize=10)
fig.supylabel("construction axis: 1 - proposition echo, last brief event present (study-span scale)", fontsize=10)
axes.ravel()[-1].axis("off")
h = [plt.Line2D([], [], color=c, marker="o", ls="", label=k) for k, c in CLS_COLOR.items()]
h += [plt.Line2D([], [], color="k", marker="o", ls="", label="base (circle)"),
      plt.Line2D([], [], color="k", marker="*", ls="", label="adapter (star)")]
axes.ravel()[-1].legend(handles=h, loc="center", fontsize=9, frameon=False)
fig.suptitle("Trade-off plane, arm A0: base -> adapter per author, one panel per model size", fontsize=12)
f1 = savefig(fig, os.path.join(OUTD, "tradeoff_plane_by_size.png"))

fig, axes = plt.subplots(2, 4, figsize=(19, 9), sharex=True, sharey=True)
for ax, (fam, pb) in zip(axes.ravel(), SIZE_ORDER):
    g = wide[(wide.family == fam) & (wide.params_b == pb)]
    for _, r in g.iterrows():
        ax.scatter(r.voice_axis, r.constr_axis, s=30, c=CLS_COLOR.get(r.author_class, "#666"), zorder=3)
        ax.annotate(r.author[:9], (r.voice_axis, r.constr_axis), fontsize=6, xytext=(2, 2), textcoords="offset points")
    title = f"{fam} {pb:g}B  (n = {len(g)})"
    if len(g) >= 3:
        s = slope_ci(g, n=400)
        if s["slope"] == s["slope"]:
            xs = np.linspace(g.voice_axis.min(), g.voice_axis.max(), 20)
            ax.plot(xs, s["intercept"] + s["slope"] * xs, color="k", lw=1.2, alpha=0.8)
            title = f"{fam} {pb:g}B  slope = {s['slope']:.2f}  (n = {len(g)})"
    ax.set_title(title, fontsize=10)
    ax.axhline(0, color="grey", lw=0.6); ax.axvline(0, color="grey", lw=0.6)
    ax.grid(alpha=0.25, lw=0.5)
fig.supxlabel("adapter minus base, voice axis (study-span scale)", fontsize=10)
fig.supylabel("adapter minus base, construction axis (study-span scale)", fontsize=10)
axes.ravel()[-1].axis("off")
axes.ravel()[-1].legend(handles=[plt.Line2D([], [], color=c, marker="o", ls="", label=k) for k, c in CLS_COLOR.items()],
                        loc="center", fontsize=9, frameon=False)
fig.suptitle("Adapter-minus-base displacement: construction change against voice change", fontsize=12)
f2 = savefig(fig, os.path.join(OUTD, "delta_delta_by_size.png"))

comp_plot = [c for c in ALL_COMP]
fig, axes = plt.subplots(1, len(comp_plot), figsize=(3.0 * len(comp_plot), 5.0), sharey=True)
for ax, c in zip(np.atleast_1d(axes), comp_plot):
    sub = signtests[(signtests.measure == c) & (signtests.group.str.contains("B$", regex=True))].copy()
    sub = sub.sort_values(["family", "params_b"])
    y = np.arange(len(sub))
    ax.errorbar(sub.mean_delta, y, xerr=[sub.mean_delta - sub.ci_low, sub.ci_high - sub.mean_delta],
                fmt="o", ms=5, lw=1.2, color="#333333")
    fl = FLOOR.get((c, "Qwen3"), np.nan)
    if fl == fl:
        ax.axvspan(-fl, fl, color="#cccccc", alpha=0.55, lw=0)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels(sub.group, fontsize=8)
    ax.set_title(COMP_LABEL[c], fontsize=8, wrap=True)
    ax.grid(alpha=0.25, lw=0.5, axis="x")
    ax.set_xlabel("adapter - base (author mean)", fontsize=8)
fig.suptitle("Component-wise adapter-minus-base deltas, authors as the unit; grey band = Qwen3 replicate floor", fontsize=11)
f3 = savefig(fig, os.path.join(OUTD, "component_deltas.png"))

# ---------------------------------------------------------------- README numbers
def g1(tbl, group, meas, col):
    x = tbl[(tbl.group == group) & (tbl.measure == meas)]
    return float(x[col].iloc[0]) if len(x) else float("nan")


# README-only bookkeeping (no table, figure or computation is changed by these)
_fq = floors[floors.family == "Qwen3"].set_index("component").floor_max_abs_mean_diff
_fm = floors[floors.family == "Ministral3"].set_index("component").floor_max_abs_mean_diff
_both_fam = [c for c in _fq.index if c in _fm.index and _fq[c] == _fq[c] and _fm[c] == _fm[c]]
n_floor_both_fam = len(_both_fam)
n_qwen_floor_larger = int(sum(1 for c in _both_fam if _fq[c] >= _fm[c]))
n_floor_single_pair = int((floors.n_pairs == 1).sum())
n_floor_no_pair = int((floors.n_pairs == 0).sum())


def _npairs(component):
    x = floors[floors.component == component].n_pairs
    return int(x.max()) if len(x) else 0


thin_floor_components = ", ".join("`" + c + "` (" + str(_npairs(c)) + ")"
                                  for c in sorted(floors.component.unique()) if _npairs(c) <= 1) or "none"
_fitnotes = length_null.groupby(["measure", "optimizer"], as_index=False).fit_note.first()
n_boundary_fits = int(_fitnotes.fit_note.str.contains("boundary", case=False).sum())
boundary_measures = sorted(set(_fitnotes[_fitnotes.fit_note.str.contains("boundary", case=False)].measure))
_opt_piv = length_null.pivot_table(index=["measure", "term"], columns="optimizer", values="estimate")
n_opt_terms = int(len(_opt_piv))
n_opt_same = int(((_opt_piv.iloc[:, 0] - _opt_piv.iloc[:, 1]).abs() < 1e-4).sum()) if _opt_piv.shape[1] == 2 else 0
n_cfg_per_author = float(signtests[(signtests.group == "all configurations") & (signtests.measure == "voice_axis")].n_authors.iloc[0]) / max(len(USABLE), 1)
_runs_used = set(cfg_out.run.dropna())
_gate_fail_used = runs[(~runs.truncation_gate_ok.astype(bool)) & (runs.run.isin(_runs_used))]
n_gate_fail_used = int(len(_gate_fail_used))
gate_fail_worst = _gate_fail_used.sort_values("truncated_pct", ascending=False).iloc[0] if n_gate_fail_used else None
_probe_pos_used = runs[runs.probe_delta_positive.astype(bool) & runs.run.isin(_runs_used)] if "probe_delta_positive" in runs.columns else runs.iloc[0:0]
probe_pos_used = ", ".join(sorted(_probe_pos_used.run.tolist())) or "none"

all_v = signtests[(signtests.group == "all configurations") & (signtests.measure == "voice_axis")].iloc[0]
all_c = signtests[(signtests.group == "all configurations") & (signtests.measure == "constr_axis")].iloc[0]
sl_all = slopes[slopes.group == "all configurations"].iloc[0]

n_up_voice = int(((wide[wide.author.isin(USABLE)].voice_axis > 0)).sum())
n_tot_wide = int(len(wide[wide.author.isin(USABLE)]))
n_down_constr = int(((wide[wide.author.isin(USABLE)].constr_axis < 0)).sum())
n_both = int(((wide[wide.author.isin(USABLE)].voice_axis > 0) & (wide[wide.author.isin(USABLE)].constr_axis < 0)).sum())

key_authors = (signtests[(signtests.measure.isin(["voice_axis", "constr_axis"])) & (signtests.group.str.endswith("B"))]
               [["group", "measure", "n_authors", "mean_delta", "ci_low", "ci_high", "n_positive", "p_sign", "q_sign_bh", "floor", "above_floor"]]
               .sort_values(["measure", "group"]))
comp_summary = (signtests[(signtests.group == "all configurations")]
                [["measure", "n_authors", "mean_delta", "ci_low", "ci_high", "n_positive", "p_sign", "q_sign_bh", "floor", "above_floor"]])

worst = cfg_out[cfg_out.kind == "adapter"].nsmallest(6, "constr_axis")[KEYS + ["voice_axis", "constr_axis", "per_inv", "term_ok"]]

write_readme(
    OUTD,
    "14 - Style / construction trade-off",
    f"""
    Asks whether a pair-6 LoRA adapter buys voice at construction's expense, and how the
    exchange rate changes with model size and family. Every configuration in the study
    (author x family x size x kind at arm A0, {n_cfg} configurations over {n_cells_a0:,} cells from
    {n_runs_a0} runs) is placed on two axes: a **voice axis** built from LUAR cosine to the
    author's reference set, Wegmann cosine to the source and the inverted opener-class
    distance, and a **construction axis** built from the inverted proposition-echo rate
    (600-word cap) and the presence of the last brief event. Judged coverage and the rubric
    construction block enter an extended construction axis at configuration level only,
    because they exist for {int(cfg.cov_frac.notna().sum())} and {int(cfg.rubric_C10.notna().sum())} of the {n_cfg} configurations. Both of those are
    LLM-judged: coverage is a judged adherence rate and the rubric block is a relative judge
    instrument, so neither is read here as a level of quality.
    """,
    f"""
    **Data.** `data/master/cells.parquet`, arm A0, non-replicate, both samples, both kinds:
    {n_cells_a0:,} cells, {d.author.nunique()} authors, {n_cfg} configurations. `per`, `otd_js` and
    `terminal_missing` exist for arm A0 only, which is why the whole script is A0.

    **Axis construction.** Each component is oriented so that higher is closer to the author
    (`otd_inv = 1 - otd_js / {otd_q95:.4f}`, the 95th percentile of otd_js over these cells;
    `per_inv = 1 - per`; `term_ok = 1 - terminal_missing`). Each component is then put on a
    common scale by a fixed affine map in which 0 is the 5th-percentile and 1 the
    95th-percentile *configuration mean* of that component (`axis_components.csv` carries the
    two constants). The axes are the unweighted mean of their components. The scale is the
    study's own span, not an absolute fidelity scale: only differences and directions on it
    mean anything, and cell-level values may fall outside [0, 1].

    **Unit.** The brief (`id`) is the cluster within an author; the author is the unit for
    every claim about models. Base and adapter cells are paired on (author, family, size,
    brief, sample), giving {n_pairs_total:,} paired cells. Per-configuration deltas carry a
    cluster bootstrap over briefs ({NBOOT} resamples), Cohen's d, Cliff's delta and a
    permutation p-value; author-level claims use a sign test and Wilcoxon over the
    {len(USABLE)} usable authors (`patrick`, the v1-chunking control, is excluded from the
    author-level tests and reported separately in `sensitivity_include_patrick_v1.csv`).

    **Correction.** BH-FDR within each family of tests: across configurations within a
    measure in `paired_deltas_by_configuration.csv`, across the whole sign-test grid in
    `author_level_tests.csv`, across the slope table.

    **Floors.** `replicate_floors.csv` gives the replicate floor of every component and both
    axes, per family, with the number of twice-generated base pairs behind each one: at most
    {n_floor_pairs_qwen} pairs on Qwen3 and {n_floor_pairs_min} on Ministral3. {n_floor_single_pair} rows rest on a single pair and
    {n_floor_no_pair} on none at all; a row with no pair carries the Qwen3 number and is marked
    `borrowed_from_Qwen3`. Per-configuration deltas are compared with their own family's floor.
    The pooled and per-size rows of `author_level_tests.csv` use the Qwen3 floor, which is the
    larger of the two families on {n_qwen_floor_larger} of the {n_floor_both_fam} components that have both. Any delta
    smaller than its floor is labelled "within noise" whatever its p-value.

    **Length.** `length_flags.csv` reports the Spearman correlation of every component with
    generated words; flagged components (|rho| >= 0.4) are {', '.join(flagged) if flagged else 'none'}, and
    `cov_frac` sits just under the threshold at {lenflags[lenflags.measure == 'cov_frac'].rho_with_words.iloc[0]:+.3f}, so it should be read as
    length-sensitive as well. `length_null_mixed_models.csv` repeats the adapter-vs-base
    contrast on the two axes with standardised words as a covariate and the author as a random
    effect. Length is downstream of the adapter as well as of the measure, so that model
    removes an amount that travels with length, not a confound established as external to the
    adapter.
    """,
    f"""
    **Unit of replication.** The author, not the passage. The pooled row rests on
    {int(all_v.n_authors)} author-by-configuration points from {len(USABLE)} distinct authors, and the
    Ministral3 rows rest on {int(auth[(auth.family == 'Ministral3') & (auth.measure == 'voice_axis')].author.nunique())} authors ({', '.join(sorted(auth[auth.family == 'Ministral3'].author.unique()))}) - a
    {int(auth[(auth.family == 'Ministral3') & (auth.measure == 'voice_axis') & (auth.params_b == 3.0)].shape[0])}-point sign test cannot reach q < 0.05 on its own, so read those rows as descriptive.

    **What the intervals are.** The per-configuration intervals are cluster bootstraps over
    briefs, which is the right width for "would this author's other briefs give the same
    answer"; they are not the width for "would another author". The per-size rows hold one
    point per author and are the ones to quote for a claim about a model size. The pooled
    "all configurations" row is not an author-level test: its {int(all_v.n_authors)} points are the same
    {len(USABLE)} authors counted about {n_cfg_per_author:.1f} times each, once per family-by-size configuration, and
    both its bootstrap and its sign test treat those repeats as independent, so the pooled
    interval is narrower and the pooled sign test more confident than {len(USABLE)} authors warrant. The
    column is named `n_authors` in `author_level_tests.csv` but holds the number of
    configuration points on the row.
    On the voice axis the two disagree in the way that matters: the pooled mean is
    {all_v.mean_delta:+.4f} with a bootstrap interval [{all_v.ci_low:+.4f}, {all_v.ci_high:+.4f}] that contains
    zero, while the sign test on the same {int(all_v.n_authors)} points is
    {all_v.n_positive}/{int(all_v.n_authors)} positive at q = {all_v.q_sign_bh:.3g}. The direction is consistent;
    the size is not estimated well enough to quote a magnitude. On the construction axis both
    agree ({all_c.mean_delta:+.4f} [{all_c.ci_low:+.4f}, {all_c.ci_high:+.4f}], {all_c.n_positive}/{int(all_c.n_authors)} positive).

    **The floor.** Voice-axis floor {FLOOR.get(('voice_axis','Qwen3'), float('nan')):.4f}, construction-axis floor
    {FLOOR.get(('constr_axis','Qwen3'), float('nan')):.4f} (Qwen3, {n_floor_pairs_qwen} replicate pairs). The pooled voice delta
    {all_v.mean_delta:+.4f} is {'above' if abs(all_v.mean_delta) > (FLOOR.get(('voice_axis','Qwen3')) or 0) else 'below'} its floor;
    the pooled construction delta {all_c.mean_delta:+.4f} is
    {'above' if abs(all_c.mean_delta) > (FLOOR.get(('constr_axis','Qwen3')) or 0) else 'below'} its floor. A floor
    estimated from {n_floor_pairs_qwen} pairs at one size and one family is itself uncertain, and it is the
    weakest link in every "within noise" verdict here.

    **What would overturn it.** A different weighting of the components. The axes are
    unweighted means of three and two components on a study-span scale; the trade-off slope
    of {sl_all.slope:+.2f} [{sl_all.slope_lo:+.2f}, {sl_all.slope_hi:+.2f}] would change if the
    construction axis were dominated by `per` alone or if coverage were included everywhere.
    The component table exists so that the reader can check each piece separately, and the
    component rows of `author_level_tests.csv` are the primary evidence; the axis rows are a
    summary of them.

    **What it does not show.** It does not show that adapters are worse. The construction
    axis is built from two automatic proxies for holding together (proposition echo and one
    adherence flag), not from a reading. It says nothing about arms A1-A5, nothing about
    absolute quality (no judge score is quoted as a level anywhere here), and nothing about
    whether a reader would prefer the adapter's prose. The plane's origin is a percentile of
    this study's own configurations, so a point at 1.0 is "the best configuration in this
    study on this component", not "the author".
    """,
    caveats=[
        "Arm A0 only, because `per`, `otd_js` and `terminal_missing` were only computed for A0.",
        f"Ministral3 has {int(auth[auth.family == 'Ministral3'].author.nunique())} authors at each of {int(auth[auth.family == 'Ministral3'].params_b.nunique())} sizes; every Ministral3 row is a {int(auth[auth.family == 'Ministral3'].author.nunique())}-author claim.",
        f"Qwen3 1.7B is one author (patrick_v2); its row is a single point and no test is meaningful.",
        f"Replicate floors rest on {n_floor_pairs_qwen} twice-generated Qwen3 pairs and {n_floor_pairs_min} Ministral3 pairs, and the Ministral3 pairs were scored on 2026-09-10. These components have one pair or none behind them: {thin_floor_components}. A component with no pair has no floor, and its `above_floor` column reads False for want of one, not because the delta is small.",
        "The pooled and per-size sign-test rows carry the Qwen3 floor even where they are Ministral3 rows, because the family column on those rows is a group label; the per-configuration table in `paired_deltas_by_configuration.csv` uses each family's own floor and is the one to read for a Ministral3 contrast.",
        f"The extended construction axis (with judged coverage and the rubric block) covers only {int((cfg.ext_n_components == 4).sum())} of {n_cfg} configurations, all Qwen3; it is reported in `configuration_axes.csv` and never used for a contrast.",
        "The axis scale is a percentile span of this study's configurations, so the numbers are comparable within this table and nowhere else.",
        "`patrick` (v1 chunking) is excluded from author-level tests; `patrick_v2` is the usable private corpus.",
        f"{n_singular} of {n_fits} mixed-model fits in `length_null_mixed_models.csv` carry a convergence warning; `fit_note` reproduces it verbatim. All {n_boundary_fits} are the boundary warning on {', '.join('`' + m + '`' for m in boundary_measures)}, under both optimisers, so the random-effect variance on those rows sits at an edge of the parameter space and must not be quoted. Every model was fitted twice, once through `lib.mixed_model` (which passes `method=['lbfgs']`) and once under statsmodels' default optimiser; on this data the two agree to 1e-4 on {n_opt_same} of {n_opt_terms} terms, so the optimiser is not carrying any result here. Both are in the table with an `optimizer` column; lib.py was not modified.",
        "No slope is fitted for a group with fewer than four author points, because a three-point Spearman is +-1 by construction and scipy returns p = 0 for it; that is why the Ministral3 per-size rows, the private author class and Qwen3 1.7B are blank in `tradeoff_slope.csv`.",
        "The `cov_frac` rows are judged brief coverage, an LLM-judged adherence rate rather than a measured one. The Qwen3 runs listed under the 2026-09-09 credit outage in LOG.md carry error rows for coverage and are being rejudged; the coverage component and the extended construction axis change when that rerun lands, and no other component in this folder is affected by it.",
        "The `rubric_C10` rows are a relative judge instrument with known failures (the same rubric ranks a 14B base above one author's own prose, and two judges are not one instrument), so its delta is a statement about the judges' preferences and not about the prose. It exists for Qwen3 only.",
        f"{n_gate_fail_used} of the {n_cfg} configurations here are runs that fail the study's 20% truncation gate (`truncation_gate_ok` in runs.csv), the worst at {gate_fail_worst.truncated_pct:.1f}%. They are flagged rather than excluded, so every length-sensitive component in those cells carries a truncation artefact." if n_gate_fail_used else "No configuration here fails the study's truncation gate.",
        f"Adapter runs with a non-negative probe delta ({probe_pos_used}) changed nothing measurable on their own training probe, and they sit inside the pooled and per-size rows like any other adapter.",
        "The pooled sign test and the pooled bootstrap resample configuration points, several per author. Only the per-size rows hold one point per author, so a claim about adapters in general should be read off those rows and the number of authors stated with it.",
    ],
    tables=[
        ("Adapter minus base on both axes, authors as the unit, by family and size", key_authors),
        ("Adapter minus base on every component, pooled over all configurations", comp_summary),
        ("Trade-off slope: construction change regressed on voice change", slopes[["group", "n_points", "n_authors", "slope", "slope_lo", "slope_hi", "rho", "rho_p", "q_bh"]]),
        ("Length: Spearman of each component with generated words", lenflags[["measure", "rho_with_words", "ci_low", "ci_high", "n", "length_flag"]]),
        ("Replicate floors", floors.sort_values(["component", "family"])[["component", "family", "n_pairs", "floor_max_abs_mean_diff", "borrowed_from_Qwen3"]]),
        ("Length null: the same contrast with and without generated words as a covariate (statsmodels default optimiser)",
         length_null[(length_null.optimizer == "statsmodels default") & (length_null.term.isin(["is_adapter", "words_c"]))]
         [["measure", "term", "estimate", "se", "ci_low", "ci_high", "p", "n_obs", "n_groups", "fit_note"]]),
        ("The six adapter configurations lowest on the construction axis", worst),
    ],
    figures=[("Trade-off plane, base -> adapter, one panel per size", f1),
             ("Displacement: construction change against voice change", f2),
             ("Component-wise deltas with the replicate floor", f3)],
    extra=f"""
### Headline numbers

- Pooled over {int(all_v.n_authors)} author-by-configuration points ({len(USABLE)} authors), the adapter moves the
  voice axis by {all_v.mean_delta:+.4f} [{all_v.ci_low:+.4f}, {all_v.ci_high:+.4f}]
  ({all_v.n_positive}/{all_v.n_authors} positive, sign test q = {all_v.q_sign_bh:.4g}) and the construction axis by
  {all_c.mean_delta:+.4f} [{all_c.ci_low:+.4f}, {all_c.ci_high:+.4f}]
  ({all_c.n_positive}/{all_c.n_authors} positive, sign test q = {all_c.q_sign_bh:.4g}).
- {n_both} of {n_tot_wide} configurations move up on voice and down on construction at the same time;
  {n_up_voice} of {n_tot_wide} move up on voice at all, {n_down_constr} of {n_tot_wide} move down on construction.
- The slope of construction change on voice change over all configurations is
  {sl_all.slope:+.3f} [{sl_all.slope_lo:+.3f}, {sl_all.slope_hi:+.3f}] with Spearman rho =
  {sl_all.rho:+.3f} (n = {int(sl_all.n_points)} points, {int(sl_all.n_authors)} authors, bootstrap over authors) and an
  intercept of {sl_all.intercept:+.3f}. The slope is positive, which is consistent with the
  configurations that gained the most voice also losing the least construction rather than with
  a fixed exchange of one for the other. The level of the construction change sits in the
  intercept: at zero voice change the fitted construction axis is {sl_all.intercept:+.3f}, and
  {n_down_constr} of {n_tot_wide} configurations move down on construction at all. The Qwen3 per-size slopes are
  ordered by parameter count
  ({slopes[slopes.group == 'Qwen3-4B'].slope.iloc[0]:+.2f} at 4B, {slopes[slopes.group == 'Qwen3-8B'].slope.iloc[0]:+.2f} at 8B,
  {slopes[slopes.group == 'Qwen3-14B'].slope.iloc[0]:+.2f} at 14B), on {len(USABLE)} authors per size, with bootstrap intervals that
  overlap each other; the ordering is descriptive and no test of the difference between sizes
  is run here.
- The pooled voice gain is carried by one instrument. LUAR-to-reference moves
  {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'luar_cos_ref', 'mean_delta'):+.4f} against a floor of
  {FLOOR.get(('luar_cos_ref','Qwen3'), float('nan')):.4f}; Wegmann-to-source moves
  {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'wegmann_cos_source', 'mean_delta'):+.4f} against a floor of
  {FLOOR.get(('wegmann_cos_source','Qwen3'), float('nan')):.4f} and the inverted opener distance
  {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'otd_inv', 'mean_delta'):+.4f} against a floor of
  {FLOOR.get(('otd_inv','Qwen3'), float('nan')):.4f} - both within noise. LUAR is the only one of the three whose mean delta
  clears its floor, and its own sign test does not survive correction
  ({g1(comp_summary.assign(group='all configurations'), 'all configurations', 'luar_cos_ref', 'n_positive'):.0f}/{int(all_v.n_authors)} positive, q = {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'luar_cos_ref', 'q_sign_bh'):.3g} across the {len(signtests)} tests in this grid), while the Wegmann sign
  test does survive (q = {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'wegmann_cos_source', 'q_sign_bh'):.3g}) on a delta smaller than its own floor. The three
  instruments do not agree, and the voice axis is an average taken over that disagreement.
- **Part of the construction loss is length.** Only `rubric_C10` clears the |rho| >= 0.4
  length flag ({lenflags[lenflags.measure == 'rubric_C10'].rho_with_words.iloc[0]:+.3f} with generated words), but the construction axis is
  correlated with words at {lenflags[lenflags.measure == 'constr_axis'].rho_with_words.iloc[0]:+.3f}, and putting standardised words into the model
  shrinks the adapter effect on it from {mm_get('constr_axis (no words covariate)', 'is_adapter', 'estimate'):+.4f} to
  {mm_get('constr_axis', 'is_adapter', 'estimate'):+.4f} (words coefficient {mm_get('constr_axis', 'words_c', 'estimate'):+.4f}, {int(mm_get('constr_axis', 'is_adapter', 'n_groups'))} authors as a random effect).
  About {100 * (1 - mm_get('constr_axis', 'is_adapter', 'estimate') / mm_get('constr_axis (no words covariate)', 'is_adapter', 'estimate')):.0f}% of the raw construction loss travels with length; the rest does not.
  The voice-axis effect does not move at all
  ({mm_get('voice_axis (no words covariate)', 'is_adapter', 'estimate'):+.4f} to {mm_get('voice_axis', 'is_adapter', 'estimate'):+.4f}).
- Component-wise, the two construction components move by {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'per_inv', 'mean_delta'):+.4f}
  (1 - PER) and {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'term_ok', 'mean_delta'):+.4f}
  (last event present); the three voice components by
  {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'luar_cos_ref', 'mean_delta'):+.4f} (LUAR-ref),
  {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'wegmann_cos_source', 'mean_delta'):+.4f} (Wegmann-source) and
  {g1(comp_summary.assign(group='all configurations'), 'all configurations', 'otd_inv', 'mean_delta'):+.4f} (inverted opener distance).
""",
)

print(f"[14] done in {time.time() - T0:.1f}s -> {OUTD}", flush=True)
