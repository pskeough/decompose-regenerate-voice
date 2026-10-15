"""17_length_truncation.py -- length as a confound, and the truncation that produces it.

Truncation and preface rates by family x size x kind x arm with Wilson and brief-cluster
intervals; the words and len_ratio distributions; what predicts an adapter run's truncation
(training examples, probe delta, parameter count, family); which dictionary measures move with
passage length; and the length null: does the adapter-versus-base contrast survive the 600-word
cap (per vs per_uncapped), survive adding words as a covariate, and survive deleting every
truncated cell.

Reads data/ only; writes analysis/17_length_truncation/ only.
"""
from __future__ import annotations

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (ARMS, VARIABLES, bh_fdr, cluster_bootstrap, cohens_d, load_all,  # noqa: E402
                 main_cells, md_table, mixed_model, outdir, replicate_floor, savefig,
                 write_readme, write_table)

OUTD = outdir("17_length_truncation")
Z95 = 1.959963984540054
CORE = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "styledist_cos_source",
        "geo_index", "otd_js", "per", "hapax_w300", "open_entropy", "pct_short8", "coverage"]


def wilson(k, n, z=Z95):
    k, n = float(k), float(n)
    if n <= 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    # clamp so the interval always contains the point estimate (float noise at k = 0)
    return (p, min(p, max(0.0, centre - half)), max(p, min(1.0, centre + half)))


def cluster_boot(keys, values, fn=np.mean, n=800, seed=0):
    keys = np.asarray(keys)
    vals = np.asarray(values, float)
    uk, inv = np.unique(keys, return_inverse=True)
    groups = [np.where(inv == i)[0] for i in range(len(uk))]
    point = fn(vals)
    if len(uk) < 3:
        return float(point), np.nan, np.nan
    rng = np.random.default_rng(seed)
    boots = np.empty(n)
    for b in range(n):
        pick = rng.integers(0, len(uk), size=len(uk))
        boots[b] = fn(vals[np.concatenate([groups[i] for i in pick])])
    return float(point), float(np.nanquantile(boots, 0.025)), float(np.nanquantile(boots, 0.975))


def cluster_boot_rho(keys, x, y, n=200, seed=0):
    """Bootstrap a Spearman rho over clusters."""
    keys = np.asarray(keys)
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    uk, inv = np.unique(keys, return_inverse=True)
    groups = [np.where(inv == i)[0] for i in range(len(uk))]
    point = spearmanr(x, y)[0]
    if len(uk) < 3:
        return float(point), np.nan, np.nan
    rng = np.random.default_rng(seed)
    boots = np.empty(n)
    for b in range(n):
        pick = rng.integers(0, len(uk), size=len(uk))
        sel = np.concatenate([groups[i] for i in pick])
        boots[b] = spearmanr(x[sel], y[sel])[0]
    return float(point), float(np.nanquantile(boots, 0.025)), float(np.nanquantile(boots, 0.975))


def paired_gain(g, measure, seed=0):
    """Brief-paired adapter minus base for one author x family x size block."""
    w = g.pivot_table(index="id", columns="kind", values=measure, aggfunc="mean").dropna()
    if len(w) < 5 or "adapter" not in w.columns or "base" not in w.columns:
        return None
    diff = (w["adapter"] - w["base"]).values
    pt, lo, hi = cluster_boot(w.index.values, diff, np.mean, n=800, seed=seed)
    return {"n_briefs": int(len(w)), "adapter_minus_base": pt, "ci_low": lo, "ci_high": hi,
            "base_mean": float(w["base"].mean()), "adapter_mean": float(w["adapter"].mean()),
            "cohens_d": cohens_d(w["adapter"].values, w["base"].values)}


def floor_for(cells, measure):
    """Replicate floor per family from the scored replicate pairs (Ministral 3: two pairs at 3B)."""
    t = replicate_floor(cells, measure)
    out = {}
    for fam in ["Qwen3", "Ministral3"]:
        sub = t[t.family == fam] if len(t) else t
        out[fam] = float(sub.abs_mean_diff.max()) if len(sub) else np.nan
    return out


# ------------------------------------------------------------------ load
print("loading ...")
cells, runs, authors, briefs, refs = load_all()
allc = cells[~cells.replicate].copy()
a0 = main_cells(cells)
n_cells = len(cells)
fl = floor_for(cells, "truncated")
have_ministral_floor = fl["Ministral3"] == fl["Ministral3"]
unscored_reps = runs[(runs.replicate) & (~runs.scored.astype(bool))].run.tolist()

# ================================================================== 1. truncation and preface
print("1. truncation and preface ...")
rows = []
for keys, g in allc.groupby(["family", "params_b", "kind", "arm"], observed=True):
    for flag in ["truncated", "preface"]:
        k, n = int(g[flag].sum()), int(len(g))
        p, lo, hi = wilson(k, n)
        pt, clo, chi = cluster_boot(g.id.values, g[flag].values.astype(float), np.mean, n=600, seed=3)
        rows.append({"family": keys[0], "params_b": keys[1], "kind": keys[2], "arm": keys[3], "flag": flag,
                     "n_cells": n, "n_flagged": k, "rate": p, "wilson_low": lo, "wilson_high": hi,
                     "brief_ci_low": clo, "brief_ci_high": chi, "n_authors": g.author.nunique()})
trunc_tab = pd.DataFrame(rows).sort_values(["flag", "family", "params_b", "kind", "arm"]).reset_index(drop=True)
trunc_tab["replicate_floor"] = trunc_tab.family.map(fl)
write_table(trunc_tab, os.path.join(OUTD, "truncation_by_config.csv"))

trunc_a0 = trunc_tab[(trunc_tab.flag == "truncated") & (trunc_tab.arm == "A0")]
preface_total = int(allc.preface.sum())
worst_trunc = trunc_tab[trunc_tab.flag == "truncated"].sort_values("rate").iloc[-1]

# per run, arm A0: the runs that ran into the cap
run_trunc = allc[allc.arm == "A0"].groupby(["run", "author", "family", "params_b", "kind"], observed=True).agg(
    n_cells=("truncated", "size"), truncated=("truncated", "sum"), words_mean=("words", "mean"),
    len_ratio_mean=("len_ratio", "mean")).reset_index()
run_trunc["truncation_rate"] = run_trunc.truncated / run_trunc.n_cells
run_trunc = run_trunc.merge(runs[["run", "probe_delta", "eval_best", "train_examples", "train_steps", "adapter_served"]],
                            on="run", how="left")
run_trunc = run_trunc.merge(authors[["author", "train_examples_max", "words_total", "train_briefs_passed"]],
                            on="author", how="left")
write_table(run_trunc.sort_values("truncation_rate", ascending=False), os.path.join(OUTD, "truncation_by_run.csv"))

# ================================================================== 2. length distributions
print("2. length distributions ...")
len_rows = []
for keys, g in a0.groupby(["family", "params_b", "kind"], observed=True):
    pt, lo, hi = cluster_bootstrap(g, "words", "id", n=800, seed=5)
    len_rows.append({"family": keys[0], "params_b": keys[1], "kind": keys[2], "n_cells": len(g),
                     "words_mean": pt, "words_ci_low": lo, "words_ci_high": hi,
                     "words_sd": float(g.words.std()), "words_p10": float(g.words.quantile(0.10)),
                     "words_median": float(g.words.median()), "words_p90": float(g.words.quantile(0.90)),
                     "len_ratio_mean": float(g.len_ratio.mean()), "len_ratio_median": float(g.len_ratio.median()),
                     "share_len_ratio_lt_0.8": float((g.len_ratio < 0.8).mean()),
                     "share_len_ratio_gt_1.2": float((g.len_ratio > 1.2).mean()),
                     "truncation_rate": float(g.truncated.mean())})
len_tab = pd.DataFrame(len_rows).sort_values(["family", "params_b", "kind"]).reset_index(drop=True)
write_table(len_tab, os.path.join(OUTD, "length_distributions.csv"))

words_gain_rows = []
for keys, g in a0.groupby(["family", "params_b", "author"], observed=True):
    r = paired_gain(g, "words", seed=7)
    if r:
        words_gain_rows.append({"family": keys[0], "params_b": keys[1], "author": keys[2], **r})
words_gain = pd.DataFrame(words_gain_rows)
write_table(words_gain, os.path.join(OUTD, "words_adapter_minus_base.csv"))
wg_q = words_gain[words_gain.family == "Qwen3"]
wg_m = words_gain[words_gain.family == "Ministral3"]

# ================================================================== 3. what predicts truncation
print("3. truncation predictors ...")
ad = run_trunc[run_trunc.kind == "adapter"].copy()
ad["log2_params"] = np.log2(ad.params_b)
ad["log_train_examples"] = np.log(ad.train_examples_max.clip(lower=1))
pred_rows = []
# Spearman is invariant to monotone transforms, so log_train_examples is not tested separately
for pred in ["train_examples_max", "probe_delta", "eval_best", "params_b", "words_total", "train_steps"]:
    d = ad[[pred, "truncation_rate"]].dropna()
    if len(d) < 6:
        continue
    r, p = spearmanr(d[pred], d.truncation_rate)
    boots = []
    rng = np.random.default_rng(11)
    for _ in range(2000):
        i = rng.integers(0, len(d), len(d))
        boots.append(spearmanr(d[pred].values[i], d.truncation_rate.values[i])[0])
    pred_rows.append({"predictor": pred, "n_runs": len(d), "spearman": float(r),
                      "ci_low": float(np.nanquantile(boots, 0.025)), "ci_high": float(np.nanquantile(boots, 0.975)),
                      "p": float(p)})
pred_tab = pd.DataFrame(pred_rows)
pred_tab["q_bh"] = bh_fdr(pred_tab.p.values)
write_table(pred_tab, os.path.join(OUTD, "truncation_predictors.csv"))

# same within family, and a cell-level linear probability model with author random effects
ad_cells = a0[a0.kind == "adapter"].merge(
    runs[["run", "probe_delta"]], on="run", how="left").merge(
    authors[["author", "train_examples_max"]], on="author", how="left", suffixes=("", "_au"))
ad_cells["log2_params"] = np.log2(ad_cells.params_b)
ad_cells["log_train"] = np.log(ad_cells.train_examples_max.fillna(ad_cells.train_examples_max.median()).clip(lower=1))
ad_cells["trunc"] = ad_cells.truncated.astype(float)
_, trunc_mm = mixed_model(ad_cells, "trunc ~ log2_params + log_train + probe_delta", groups="author")
if len(trunc_mm):
    write_table(trunc_mm, os.path.join(OUTD, "truncation_mixed_model.csv"))

# ================================================================== 4. what moves with length
print("4. correlation with words ...")
NUM = [v for v in VARIABLES
       if v in a0.columns and a0[v].dtype.kind in "fib" and v not in ("words", "n_sent", "len_ratio")]
corr_rows = []
for v in NUM:
    d = a0[[v, "words", "run", "kind"]].dropna()
    if len(d) < 100 or d[v].nunique() < 3:
        continue
    r, p = spearmanr(d[v], d.words)
    dc = d.copy()
    dc["a"] = dc[v] - dc.groupby("run")[v].transform("mean")
    dc["b"] = dc.words - dc.groupby("run").words.transform("mean")
    r_within = spearmanr(dc.a, dc.b)[0]
    _, lo, hi = cluster_boot_rho(d.run.values, d[v].values, d.words.values, n=200, seed=13)
    rb = spearmanr(d[d.kind == "base"][v], d[d.kind == "base"].words)[0] if (d.kind == "base").sum() > 50 else np.nan
    ra = spearmanr(d[d.kind == "adapter"][v], d[d.kind == "adapter"].words)[0] if (d.kind == "adapter").sum() > 50 else np.nan
    corr_rows.append({"measure": v, "label": VARIABLES[v][0], "construct": VARIABLES[v][1], "n": len(d),
                      "spearman_with_words": float(r), "ci_low": lo, "ci_high": hi,
                      "spearman_within_run": float(r_within), "spearman_base": float(rb) if rb == rb else np.nan,
                      "spearman_adapter": float(ra) if ra == ra else np.nan, "p": float(p)})
corr_tab = pd.DataFrame(corr_rows)
corr_tab["q_bh"] = bh_fdr(corr_tab.p.values)
corr_tab["length_flag"] = corr_tab.spearman_with_words.abs() >= 0.4
# a measure can be clean pooled and length-bound inside a run or inside one kind; flag the max
corr_tab["max_abs_rho"] = corr_tab[["spearman_with_words", "spearman_within_run",
                                    "spearman_base", "spearman_adapter"]].abs().max(axis=1)
corr_tab["length_flag_any"] = corr_tab.max_abs_rho >= 0.4
corr_tab = corr_tab.reindex(corr_tab.max_abs_rho.sort_values(ascending=False).index).reset_index(drop=True)
write_table(corr_tab, os.path.join(OUTD, "words_correlations.csv"))
flagged = corr_tab[corr_tab.length_flag].measure.tolist()
flagged_any = corr_tab[corr_tab.length_flag_any].measure.tolist()
flagged_within = corr_tab[corr_tab.spearman_within_run.abs() >= 0.4].measure.tolist()
flagged_adapter_only = corr_tab[corr_tab.length_flag_any & ~corr_tab.length_flag].measure.tolist()

# ================================================================== 5. the length null on PER
print("5. length null: per vs per_uncapped ...")
null_rows = []
for keys, g in a0.groupby(["family", "params_b", "author"], observed=True):
    row = {"family": keys[0], "params_b": keys[1], "author": keys[2]}
    ok = True
    for measure in ["per", "per_uncapped"]:
        r = paired_gain(g, measure, seed=17)
        if r is None:
            ok = False
            break
        row[f"{measure}_gain"] = r["adapter_minus_base"]
        row[f"{measure}_lo"] = r["ci_low"]
        row[f"{measure}_hi"] = r["ci_high"]
        row["n_briefs"] = r["n_briefs"]
    if ok:
        row["sign_agrees"] = bool(np.sign(row["per_gain"]) == np.sign(row["per_uncapped_gain"]))
        null_rows.append(row)
null_tab = pd.DataFrame(null_rows)
per_floor = floor_for(cells, "per")
peru_floor = floor_for(cells, "per_uncapped")
null_tab["per_floor"] = null_tab.family.map(per_floor)
null_tab["per_uncapped_floor"] = null_tab.family.map(peru_floor)
null_tab["per_above_floor"] = null_tab.per_gain.abs() > null_tab.per_floor.fillna(per_floor["Qwen3"])
null_tab["per_uncapped_above_floor"] = null_tab.per_uncapped_gain.abs() > null_tab.per_uncapped_floor.fillna(peru_floor["Qwen3"])
write_table(null_tab, os.path.join(OUTD, "length_null_per.csv"))
n_sign_agree = int(null_tab.sign_agrees.sum())
n_null_rows = len(null_tab)
r_per_pair = spearmanr(null_tab.per_gain, null_tab.per_uncapped_gain)[0]
# the cap changes the magnitude even when it does not change the sign
_pos = null_tab[null_tab.per_gain > 0.01]
inflate = float((_pos.per_uncapped_gain / _pos.per_gain).median()) if len(_pos) else np.nan
n_inflate = len(_pos)

# ================================================================== 6. words as a covariate
print("6. adapter effect with words as a covariate ...")
adj_rows = []
targets = sorted(set(CORE) | set(flagged_any))
FLOORS = {m: floor_for(cells, m) for m in targets}
for (fam, pb), g in a0.groupby(["family", "params_b"], observed=True):
    if g.author.nunique() < 3:
        continue
    for measure in targets:
        d = g[[measure, "words", "kind", "author", "id"]].dropna()
        if len(d) < 60 or d.kind.nunique() < 2 or d.author.nunique() < 3:
            continue
        d = d.copy()
        d["is_adapter"] = (d.kind == "adapter").astype(float)
        d["words_c"] = (d.words - d.words.mean()) / d.words.std()
        _, t_raw = mixed_model(d, f"{measure} ~ is_adapter", groups="author")
        _, t_adj = mixed_model(d, f"{measure} ~ is_adapter + words_c", groups="author")
        if not len(t_raw) or not len(t_adj) or "is_adapter" not in set(t_raw.term) or "is_adapter" not in set(t_adj.term):
            continue
        r0 = t_raw[t_raw.term == "is_adapter"].iloc[0]
        r1 = t_adj[t_adj.term == "is_adapter"].iloc[0]
        wc = t_adj[t_adj.term == "words_c"]
        adj_rows.append({"family": fam, "params_b": pb, "measure": measure, "n_obs": int(r0.n_obs),
                         "n_authors": int(r0.n_groups),
                         "adapter_effect_raw": float(r0.estimate), "raw_lo": float(r0.ci_low), "raw_hi": float(r0.ci_high),
                         "adapter_effect_adj_words": float(r1.estimate), "adj_lo": float(r1.ci_low), "adj_hi": float(r1.ci_high),
                         "words_coefficient": float(wc.estimate.iloc[0]) if len(wc) else np.nan,
                         "attenuation": float(abs(r1.estimate) - abs(r0.estimate)),
                         "sign_flips": bool(np.sign(r0.estimate) != np.sign(r1.estimate)),
                         "p_raw": float(r0.p), "p_adj": float(r1.p)})
adj_tab = pd.DataFrame(adj_rows)
if len(adj_tab):
    adj_tab["q_raw"] = bh_fdr(adj_tab.p_raw.values)
    adj_tab["q_adj"] = bh_fdr(adj_tab.p_adj.values)
    adj_tab["floor"] = [FLOORS[m][f] for m, f in zip(adj_tab.measure, adj_tab.family)]
    adj_tab["raw_above_floor"] = adj_tab.adapter_effect_raw.abs() > adj_tab.floor
write_table(adj_tab, os.path.join(OUTD, "words_covariate_contrasts.csv"))
n_flip = int(adj_tab.sign_flips.sum()) if len(adj_tab) else 0
n_lost = int(((adj_tab.q_raw < 0.05) & (adj_tab.q_adj >= 0.05)).sum()) if len(adj_tab) else 0

# ================================================================== 7. drop truncated cells
print("7. sensitivity: drop truncated cells ...")
sens_rows = []
for keys, g in a0.groupby(["family", "params_b", "author"], observed=True):
    # a brief is dropped if either side of the pair was truncated
    bad = set(g[g.truncated].id.unique())
    gk = g[~g.id.isin(bad)]
    for measure in CORE:
        full = paired_gain(g, measure, seed=19)
        keep = paired_gain(gk, measure, seed=19)
        if full is None:
            continue
        sens_rows.append({"family": keys[0], "params_b": keys[1], "author": keys[2], "measure": measure,
                          "n_briefs_all": full["n_briefs"], "gain_all": full["adapter_minus_base"],
                          "all_lo": full["ci_low"], "all_hi": full["ci_high"],
                          "n_briefs_clean": keep["n_briefs"] if keep else 0,
                          "gain_no_truncated": keep["adapter_minus_base"] if keep else np.nan,
                          "clean_lo": keep["ci_low"] if keep else np.nan,
                          "clean_hi": keep["ci_high"] if keep else np.nan,
                          "share_briefs_dropped": float(len(bad) / max(g.id.nunique(), 1))})
sens_tab = pd.DataFrame(sens_rows)
CORE_FLOORS = {m: floor_for(cells, m) for m in CORE}
sens_tab["gain_shift"] = sens_tab.gain_no_truncated - sens_tab.gain_all
sens_tab["floor"] = [CORE_FLOORS[m][f] for m, f in zip(sens_tab.measure, sens_tab.family)]
sens_tab["floor_source"] = ["own family" if v == v else "Qwen3 (no Ministral replicate)"
                           for v in sens_tab.floor]
sens_tab["floor"] = [CORE_FLOORS[m][f] if CORE_FLOORS[m][f] == CORE_FLOORS[m][f] else CORE_FLOORS[m]["Qwen3"]
                     for m, f in zip(sens_tab.measure, sens_tab.family)]
sens_tab["sign_flips"] = np.sign(sens_tab.gain_all) != np.sign(sens_tab.gain_no_truncated)
sens_tab["shift_above_floor"] = sens_tab.gain_shift.abs() > sens_tab.floor
write_table(sens_tab, os.path.join(OUTD, "truncation_sensitivity.csv"))
sens_ok = sens_tab.dropna(subset=["gain_no_truncated"])
n_sens_flip = int(sens_ok.sign_flips.sum())
n_sens_rows = len(sens_ok)
n_shift_above_floor = int(sens_ok.shift_above_floor.fillna(False).sum())
worst_drop = sens_tab.sort_values("share_briefs_dropped").iloc[-1]

# ================================================================== figures
print("figures ...")
FIGS = []

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), sharey=True)
for ax, fam in zip(axes, ["Qwen3", "Ministral3"]):
    sub = trunc_tab[(trunc_tab.flag == "truncated") & (trunc_tab.family == fam) & (trunc_tab.arm == "A0")]
    for kind, g in sub.groupby("kind", observed=True):
        g = g.sort_values("params_b")
        ax.errorbar(g.params_b, g.rate, yerr=[g.rate - g.wilson_low, g.wilson_high - g.rate],
                    marker="o", ls="-" if kind == "base" else "--", capsize=3, label=kind)
    f = fl.get(fam)
    if f == f:
        ax.axhline(f, color="#8c8c8c", lw=0.8, ls=":", label=f"replicate floor {f:.3f}")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("parameters (B, log2)")
    ax.set_title(f"{fam} (arm A0)")
    ax.legend(fontsize=8)
axes[0].set_ylabel(VARIABLES["truncated"][0] + " (rate)")
fig.suptitle("Truncation rate by size and kind, Wilson intervals")
FIGS.append(("Truncation rate by configuration", savefig(fig, os.path.join(OUTD, "fig_truncation.png"))))

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), sharey=True)
for ax, fam in zip(axes, ["Qwen3", "Ministral3"]):
    sub = a0[a0.family == fam]
    data, labels = [], []
    for pb in sorted(sub.params_b.unique()):
        for kind in ["base", "adapter"]:
            v = sub[(sub.params_b == pb) & (sub.kind == kind)].words.dropna().values
            if len(v):
                data.append(v)
                labels.append(f"{pb:g}B\n{kind}")
    if data:
        bp = ax.boxplot(data, positions=np.arange(len(data)), tick_labels=labels,
                        showfliers=False, patch_artist=True,
                        medianprops={"color": "k", "lw": 1.2})
        for patch, lab in zip(bp["boxes"], labels):
            patch.set_facecolor("#2b6cb0" if "base" in lab else "#dd8452")
        ax.set_xlim(-0.6, len(data) - 0.4)
    ax.set_title(fam)
    ax.tick_params(axis="x", labelsize=7.5)
axes[0].set_ylabel(VARIABLES["words"][0])
fig.suptitle("Generated length by size and kind (arm A0); adapters run long on Qwen3, short on Ministral 3")
FIGS.append(("Length distribution by configuration", savefig(fig, os.path.join(OUTD, "fig_words_distribution.png"))))

fig, ax = plt.subplots(figsize=(8.4, 7.8))
top = corr_tab.head(28).iloc[::-1]
ys = np.arange(len(top))
ax.barh(ys, top.spearman_with_words, color=["#c44e52" if f else "#8c8c8c" for f in top.length_flag_any],
        label="pooled (red = flagged at |rho| >= 0.4 on any split)")
ax.barh(ys, top.spearman_within_run, height=0.35, color="#2b6cb0", label="within run")
ax.axvline(0.4, color="k", lw=0.8, ls=":")
ax.axvline(-0.4, color="k", lw=0.8, ls=":")
ax.set_yticks(ys)
ax.set_yticklabels(top.measure, fontsize=7.5)
ax.set_xlabel("Spearman rho with generated words (arm A0)")
ax.set_title("What moves with passage length")
ax.legend(fontsize=8, loc="lower right")
FIGS.append(("Correlation with passage length", savefig(fig, os.path.join(OUTD, "fig_words_correlations.png"))))

fig, ax = plt.subplots(figsize=(6.2, 5.6))
for fam, g in null_tab.groupby("family", observed=True):
    ax.scatter(g.per_gain, g.per_uncapped_gain, s=30, label=fam,
               marker="o" if fam == "Qwen3" else "s")
lim = float(np.nanmax(np.abs(np.concatenate([null_tab.per_gain.values, null_tab.per_uncapped_gain.values])))) * 1.1
ax.plot([-lim, lim], [-lim, lim], color="#8c8c8c", lw=0.8, ls=":")
ax.axhline(0, color="k", lw=0.6)
ax.axvline(0, color="k", lw=0.6)
ax.set_xlabel("adapter minus base on " + VARIABLES["per"][0].split(":")[0])
ax.set_ylabel("adapter minus base on per_uncapped")
ax.set_title(f"The length null: the 600-word cap does not change the sign\n({n_sign_agree} of {n_null_rows} author x size cells agree in sign)")
ax.legend(fontsize=8)
FIGS.append(("Length null on proposition echo", savefig(fig, os.path.join(OUTD, "fig_length_null.png"))))

# ================================================================== README
print("readme ...")
q_ad = trunc_a0[(trunc_a0.family == "Qwen3") & (trunc_a0.kind == "adapter")].sort_values("params_b")
q_ba = trunc_a0[(trunc_a0.family == "Qwen3") & (trunc_a0.kind == "base")].sort_values("params_b")
m_ad = trunc_a0[(trunc_a0.family == "Ministral3") & (trunc_a0.kind == "adapter")].sort_values("params_b")
m_ba = trunc_a0[(trunc_a0.family == "Ministral3") & (trunc_a0.kind == "base")].sort_values("params_b")
best_pred = pred_tab.reindex(pred_tab.spearman.abs().sort_values(ascending=False).index).iloc[0]
top_len = corr_tab.iloc[0]

# README-only bookkeeping (no table, figure or computation is changed by these)
_tr_piv = trunc_a0.pivot_table(index=["family", "params_b"], columns="kind", values="rate")
_trd = pd.DataFrame([{"family": f, "params_b": p, "diff": float(r["adapter"] - r["base"]), "floor": float(fl[f])}
                     for (f, p), r in _tr_piv.iterrows()])
n_q_sizes = int((_trd.family == "Qwen3").sum())
n_q_ada_above = int(((_trd.family == "Qwen3") & (_trd["diff"] > _trd.floor)).sum())
n_m_sizes = int((_trd.family == "Ministral3").sum())
_m_above = _trd[(_trd.family == "Ministral3") & (_trd["diff"].abs() > _trd.floor)]
n_m_above = int(len(_m_above))
m_above_sizes = ", ".join(f"{p:g}B" for p in _m_above.params_b) or "no size"
n_q_authors = int(a0[a0.family == "Qwen3"].author.nunique())
n_m_authors = int(a0[a0.family == "Ministral3"].author.nunique())
n_sens_all_rows = int(len(sens_tab))
n_own_floor = int((sens_tab.floor_source == "own family").sum())
_rf_trunc = replicate_floor(cells, "truncated")
n_pairs_q = int((_rf_trunc.family == "Qwen3").sum()) if len(_rf_trunc) else 0
n_pairs_m = int((_rf_trunc.family == "Ministral3").sum()) if len(_rf_trunc) else 0
_gate_fail = runs[~runs.truncation_gate_ok.astype(bool)]
n_gate_fail = int(len(_gate_fail))
n_gate_fail_base = int((_gate_fail.kind == "base").sum())
gate_fail_base = ", ".join(sorted(_gate_fail[_gate_fail.kind == "base"].run.tolist())) or "none"
gate_fail_worst = _gate_fail.sort_values("truncated_pct", ascending=False).iloc[0] if n_gate_fail else None
_rt = run_trunc.merge(runs[["run", "truncated_pct"]], on="run", how="left")
_rt["pooled"] = _rt.truncated_pct / 100.0
_rt["gap"] = (_rt.truncation_rate - _rt.pooled).abs()
worst_gap = _rt.sort_values("gap", ascending=False).iloc[0]
_rubric_len = corr_tab[corr_tab.measure.isin(["rubric_C", "rubric_S"]) & corr_tab.length_flag].measure.tolist()
_author_level_preds = [p for p in pred_tab.predictor if p in ("train_examples_max", "words_total", "train_briefs_passed")]
author_level_preds = ", ".join("`" + p + "`" for p in _author_level_preds) or "none"

what = f"""
Length is the study's most obvious confound and truncation is where it comes from, so this
script measures both before any other script leans on a length-sensitive measure. Four parts.
(1) How often a generation hit the token cap or opened with a preface, by family, size, kind
and arm, with Wilson intervals on cells and a bootstrap over briefs, next to the replicate
floor of the truncation flag itself. (2) What the length distributions look like, and how much
of the adapter's length change is paired within a brief. (3) What predicts an adapter run's
truncation: training examples, probe delta, parameter count, family. (4) The length null in
three forms: which dictionary measures move with `words` at all; whether the adapter-versus-base
contrast on proposition echo survives the 600-word cap (per against per_uncapped); whether it
survives adding length as a covariate; and whether it survives deleting every brief where
either side was truncated.

The headline is that the truncation pattern differs between the two families, on {n_q_authors} Qwen3
authors and {n_m_authors} Ministral 3 authors. On Qwen3 the base rarely truncates at A0 ({q_ba.rate.min():.3f} to
{q_ba.rate.max():.3f}) and the adapter truncates more ({q_ad.rate.min():.3f} to {q_ad.rate.max():.3f}), by more than the replicate floor at
{n_q_ada_above} of {n_q_sizes} sizes. On Ministral 3 the base range is {m_ba.rate.min():.3f} to {m_ba.rate.max():.3f} and the adapter range
{m_ad.rate.min():.3f} to {m_ad.rate.max():.3f}, and the two differ by more than the floor at {n_m_above} of {n_m_sizes} sizes ({m_above_sizes}), where the
base is the one that truncates. At the other Ministral sizes base and adapter sit inside the
floor of each other, so a statement that the two families truncate in opposite directions rests
on one Ministral size and {n_m_authors} authors, not on the family.
"""

how = f"""
Data. `data/master/cells.parquet` (non-replicate rows; arm A0 for anything that uses the
eval-cache measures), `runs.csv` for probe delta and training size, `authors.csv` for
`train_examples_max`.

Unit. Flag rates are computed over cells and given two intervals: a Wilson interval, which
assumes cells are independent, and a bootstrap over briefs, which does not. Every
adapter-versus-base contrast is brief-paired inside one author x family x size block and
bootstrapped over briefs ({n_sens_all_rows} rows in `truncation_sensitivity.csv`, {len(sens_ok)} of them with a usable
no-truncation counterpart). Truncation predictors are correlated at the run level ({len(ad)} adapter
runs), where the unit is a run: those runs come from {n_q_authors} Qwen3 and {n_m_authors} Ministral authors at
several sizes each, and {len(_author_level_preds)} of the {len(pred_tab)} predictors ({author_level_preds}) are author-level
constants, so a run-level correlation with one of those repeats an author's value once per
size and its interval is narrower than the number of authors warrants. The cell-level
linear probability model with author random effects asks the same question with the author as
the grouping factor and is the one to quote.

Statistics. Spearman with bootstrap intervals; BH-FDR within each family of tests
({len(pred_tab)} predictor tests, {len(corr_tab)} length correlations,
{len(adj_tab) if len(adj_tab) else 0} covariate-adjusted contrasts). The words correlation is
reported pooled and again after centring both variables within run, because a pooled
correlation over cells that differ in configuration will read length differences that are
really configuration differences. Mixed models are statsmodels MixedLM with the author as the
grouping factor; with three to fourteen authors the random-effect variance is descriptive only.
Every contrast is printed next to the replicate floor of its measure.

Replicate floors. `lib.replicate_floor` finds {'both families' if have_ministral_floor else 'Qwen3 pairs only'}: {n_pairs_q} twice-generated
Qwen3 base pairs and {n_pairs_m} Ministral 3 pairs on the truncation flag. The Ministral replicate runs
were scored on 2026-09-10, so contrasts here are compared with their own family's floor rather
than a borrowed one: {n_own_floor} of the {n_sens_all_rows} rows in `truncation_sensitivity.csv` carry
`floor_source = own family`. Both floors are thin and the Ministral one is the thinner, so a
verdict that sits just either side of a floor should not be leaned on.
"""

reading = f"""
Unit of replication. Truncation rates are read per configuration, and a configuration is one
run, so the interval that matters is the brief-cluster one, not the Wilson one - for the worst
cell ({worst_trunc.family} {worst_trunc.params_b:g}B {worst_trunc.kind} arm {worst_trunc.arm},
rate {worst_trunc.rate:.3f}) the Wilson interval is
[{worst_trunc.wilson_low:.3f}, {worst_trunc.wilson_high:.3f}] and the brief bootstrap is
[{worst_trunc.brief_ci_low:.3f}, {worst_trunc.brief_ci_high:.3f}]. For any claim about a model
family rather than a run, the unit drops to authors: Qwen3 has up to
{int(a0[a0.family == 'Qwen3'].author.nunique())} of them and Ministral 3 has
{int(a0[a0.family == 'Ministral3'].author.nunique())}, so the Ministral column is {n_m_authors} points and
should be read as an illustration, not an estimate.

Interval width and floor. The truncation flag's own replicate floor is
{fl['Qwen3']:.3f} on Qwen3 and {fl['Ministral3']:.3f} on Ministral 3 (largest absolute difference between two
runs of the same configuration, from {n_pairs_q} and {n_pairs_m} pairs). Truncation differences smaller than
their family's number are noise, and a floor from one or three pairs is itself an estimate. On the measures, the floors
are printed in `truncation_sensitivity.csv` and `words_covariate_contrasts.csv` beside every
contrast; of {n_sens_rows} sensitivity contrasts, {n_shift_above_floor} moved by more than
their own floor when truncated briefs were dropped, and {n_sens_flip} changed sign.

What the length null does and does not settle. The 600-word cap does the job it was added
for: the paired adapter effect on capped proposition echo and on uncapped proposition echo
agree in sign in {n_sign_agree} of {n_null_rows} author x size cells and correlate at rho {r_per_pair:.2f}, which is
consistent with the coherence result not being an artefact of the adapter writing longer. The
cap does change the size of it: over the {n_inflate} cells with a clearly positive capped gain, the
uncapped gain is a median {inflate:.2f} times the capped one, so an uncapped proposition-echo number
reports a larger coherence cost than the capped one by that factor.
Adding length as a covariate changed the sign of the adapter effect in {n_flip} of
{len(adj_tab) if len(adj_tab) else 0} contrasts and moved {n_lost} from q < 0.05 to q >= 0.05 within this script's family of
{len(adj_tab) if len(adj_tab) else 0} tests. Length is a real covariate and most of the adapter effect does not travel with
it. That does not show that the flagged measures are safe, and the covariate model cannot
separate length as a confound from length as part of what the adapter changed, because the
adapter changes length. {len(flagged)} measures correlate with words at |rho| >= 0.4 pooled
({', '.join(flagged)}), {len(flagged_within)} do so after centring within run, and {len(flagged_any)} cross the threshold on at
least one of the four splits (pooled, within run, base only, adapter only). The extra ones
({', '.join(flagged_adapter_only)}) are clean pooled and cross the threshold inside the adapter arm,
which is the worst case for this study, because the adapter is the thing being tested and it is
also the thing that changes length. Read those as length results until shown otherwise.
{'`rubric_C` and `rubric_S` are among the pooled-flagged measures. They are judge scores, so the correlation is the judges reading length, and it is a property of the instrument rather than of the prose.' if _rubric_len else ''}

What would overturn this. Regenerating the truncating runs with a larger token cap. If the
Qwen3 14B adapter's truncation ({q_ad[q_ad.params_b == 14].rate.iloc[0]:.3f} at A0) is a cap
artefact rather than a property of the adapter, every 14B adapter measure that correlates with
words changes. A second Ministral 3 replicate pair, and pairs at more than one size, would say
whether the Ministral floor used here is the right width; the pair that exists was scored on
2026-09-10 and covers one size.

What this does not show. Nothing here says truncation is bad prose or that a long passage is a
good one. `truncated` is a flag on hitting the generation cap, so it is confounded with the
brief's target length; `len_ratio` is the measure that carries the target, and it is reported
next to it.
"""

caveats = [
    f"The Ministral 3 replicate pair was scored on 2026-09-10, so both families now have a floor ({n_pairs_q} Qwen3 pairs, {n_pairs_m} Ministral). Any reading of this folder written before that date compared Ministral contrasts with a borrowed Qwen3 number; the `floor_source` column records which floor each row actually used.",
    f"Truncation is measured as a flag per cell; the run-level `truncated_pct` in runs.csv pools all arms and can differ from the A0 number in these tables. The largest gap is {worst_gap.run}: A0 {worst_gap.truncation_rate:.3f} against {worst_gap.pooled:.3f} pooled. Quote the A0 rate from these tables when comparing configurations at A0.",
    f"Preface is almost never flagged ({preface_total} cells of {len(allc)}), so the preface columns in these tables are descriptive and cannot support a contrast.",
    "Pooled correlations with words mix within-configuration and between-configuration variation; the within-run column is the conservative one and it is smaller for almost every measure.",
    "The covariate-adjusted contrasts use a linear model on measures that are bounded (rates, cosines), so the adjusted coefficient is a local approximation, not a properly linked estimate.",
    "Coverage exists for Qwen3 only, so the coverage row of the sensitivity table has no Ministral counterpart.",
    "Dropping truncated briefs removes whole briefs from both arms to keep the pairing, so the clean estimate is computed on a smaller and slightly easier set of briefs, not on the same set minus a few cells.",
    (f"{n_gate_fail} runs fail the study's 20% truncation gate (`truncation_gate_ok` in runs.csv) and are in these tables flagged rather than excluded; the worst is {gate_fail_worst.run} at {gate_fail_worst.truncated_pct:.1f}%. {n_gate_fail_base} of them are base runs ({gate_fail_base}), and the Ministral 3 base column is the one carrying the reading that the Ministral base truncates, so that reading rests partly on runs the study's own gate rejects."
     if n_gate_fail else "No run fails the study's 20% truncation gate."),
    "Coverage is an LLM-judged adherence rate, not a measurement, and the Qwen3 runs listed under the 2026-09-09 credit outage in LOG.md carry error rows for it and are being rejudged; the coverage row of the sensitivity table changes when that rerun lands.",
    f"The run-level truncation predictors are correlated over adapter runs, not over authors, and {len(_author_level_preds)} of the {len(pred_tab)} predictors ({author_level_preds}) are author-level constants repeated once per size; treat those intervals as optimistic and read the mixed model beside them.",
    "The predictors are observational: an author with more training data also has a different corpus, a different register and a different brief set, so a correlation between training size and truncation is consistent with several accounts and settles none of them.",
    f"The number of authors, {n_q_authors} on Qwen3 and {n_m_authors} on Ministral 3, is what limits every claim here. BH-FDR is applied within each family of tests in this script and does not buy back replication across authors.",
]

write_readme(
    OUTD, "17_length_truncation: how much of the result is length",
    what, how, reading, caveats,
    tables=[("Truncation rate by configuration (arm A0)", trunc_tab[(trunc_tab.flag == 'truncated') & (trunc_tab.arm == 'A0')].drop(columns=["flag"])),
            ("Length distributions (arm A0)", len_tab),
            ("Adapter minus base on generated words", words_gain),
            ("What predicts an adapter run's truncation", pred_tab),
            ("Measures that move with passage length (top 20 by the largest |rho| on any split)",
             corr_tab.head(20).drop(columns=["label", "construct"])),
            ("The length null on proposition echo", null_tab),
            ("Adapter effect with and without words as a covariate", adj_tab),
            ("Core contrasts with truncated briefs dropped (first 40)", sens_tab.head(40))],
    figures=FIGS)

print(f"""
=== 17_length_truncation summary ===
cells {len(allc)} non-replicate; A0 {len(a0)}
Qwen3 A0 truncation: base {q_ba.rate.min():.3f}-{q_ba.rate.max():.3f}, adapter {q_ad.rate.min():.3f}-{q_ad.rate.max():.3f} (14B adapter {q_ad[q_ad.params_b == 14].rate.iloc[0]:.3f})
Ministral3 A0 truncation: base {m_ba.rate.min():.3f}-{m_ba.rate.max():.3f}, adapter {m_ad.rate.min():.3f}-{m_ad.rate.max():.3f}
worst cell: {worst_trunc.family} {worst_trunc.params_b:g}B {worst_trunc.kind} {worst_trunc.arm} = {worst_trunc.rate:.3f} [{worst_trunc.brief_ci_low:.3f}, {worst_trunc.brief_ci_high:.3f}]
truncation replicate floor: Qwen3 {fl['Qwen3']:.4f}, Ministral3 {'none (replicate runs unscored)' if not have_ministral_floor else f"{fl['Ministral3']:.4f}"}
preface flagged {preface_total} of {len(allc)} cells
words adapter-minus-base: Qwen3 {wg_q.adapter_minus_base.mean():+.0f} mean over {len(wg_q)} cells; Ministral3 {wg_m.adapter_minus_base.mean():+.0f} over {len(wg_m)}
best truncation predictor: {best_pred.predictor} rho {best_pred.spearman:+.2f} [{best_pred.ci_low:+.2f}, {best_pred.ci_high:+.2f}] q={best_pred.q_bh:.3f} (n={best_pred.n_runs} adapter runs)
length-flagged measures (pooled |rho|>=0.4): {len(flagged)} of {len(corr_tab)} -> {', '.join(flagged)}
  flagged on any split (pooled/within-run/base/adapter): {len(flagged_any)} -> {', '.join(flagged_any)}
  flagged within run: {len(flagged_within)} -> {', '.join(flagged_within)}
  strongest: {top_len.measure} rho {top_len.spearman_with_words:+.2f} (within-run {top_len.spearman_within_run:+.2f}, adapter-only {top_len.spearman_adapter:+.2f})
length null: per vs per_uncapped sign agrees {n_sign_agree}/{n_null_rows}, rho {r_per_pair:+.2f}, uncapped gain median {inflate:.2f}x capped (n={n_inflate})
words covariate: {n_flip} sign flips, {n_lost} contrasts lost q<0.05, of {len(adj_tab)}
drop-truncated sensitivity: {n_sens_flip}/{n_sens_rows} sign flips, {n_shift_above_floor} shifts above floor; worst brief loss {worst_drop.share_briefs_dropped:.2f} ({worst_drop.author} {worst_drop.family} {worst_drop.params_b:g}B)
outputs -> {OUTD}
""")
