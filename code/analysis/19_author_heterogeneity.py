"""19_author_heterogeneity.py - how much of the adapter effect is the author, not the model.

Per author x family x size: the brief-paired adapter-vs-base effect on the core measures with a
cluster-bootstrap interval, Cohen's d and Cliff's delta. Across authors: DerSimonian-Laird
random-effects pooling with I-squared, tau-squared and a prediction interval, moderator analyses
(author class, log training examples, family), leave-one-author-out sensitivity, and the rank
stability of the per-author effect across sizes. Forest plots per measure and size.

Reads data/master/* and data/runs/<run>/gens.jsonl (length floor for the two unscored Ministral
replicates only). Writes analysis/19_author_heterogeneity/ only.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from lib import (RUNS, VARIABLES, bh_fdr, cliffs_delta, cluster_bootstrap, cohens_d, load_all, main_cells,
                 md_table, outdir, replicate_floor, savefig, spearman_ci, write_readme, write_table)

T0 = time.time()
OUTD = outdir("19_author_heterogeneity")

MEASURES = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "styledist_cos_source", "geo_index",
            "otd_js", "hapax_w300", "per", "mattr", "coverage", "truncated"]
FOREST = ["luar_cos_source", "luar_cos_ref", "otd_js", "per"]
CONTROL_AUTHOR = "patrick"        # the v1 chunking control; kept in the tables, out of every pool
QWEN_SIZES = [4.0, 8.0, 14.0]
MIN_SEC = ["Qwen3", "Ministral3"]


def lab(m):
    return VARIABLES[m][0] if m in VARIABLES else m


def direction(m):
    return VARIABLES[m][3] if m in VARIABLES else "0"


def toward(m):
    """sign multiplier that turns a raw difference into 'moved toward the author'."""
    return -1.0 if direction(m) == "-" else 1.0


def fmt(v, nd=4):
    return "n/a" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{nd}f}"


# ---------------------------------------------------------------- load
cells, runs, authors, briefs, refs = load_all()
cells = cells.copy()
for c in ("truncated", "preface"):
    if cells[c].dtype == bool:
        cells[c] = cells[c].astype(float)
d = main_cells(cells).copy()          # arm A0, non-replicate, base + adapter
AUTH = authors.set_index("author")

BT = d.groupby(["author", "author_class", "family", "params_b", "kind", "id"], as_index=False)[MEASURES].mean()


# ---------------------------------------------------------------- floors
def seed_floor(cn, measure, family, min_n=8, min_runs=3):
    sub = cn[(cn.family == family) & (cn.kind == "base") & (cn.arm == "A0") & (~cn.replicate)]
    vals = []
    for run, g in sub.groupby("run"):
        a = g.loc[g["sample"] == 0, measure].dropna()
        b = g.loc[g["sample"] == 1, measure].dropna()
        if len(a) >= min_n and len(b) >= min_n:
            vals.append(abs(float(a.mean()) - float(b.mean())))
    if len(vals) < min_runs:
        return np.nan, len(vals)
    return float(max(vals)), len(vals)


def ministral_length_floor():
    pairs = [("chesterton_basem3b", "chesterton_basem3b_r2"), ("patrick_v2_basem3b", "patrick_v2_basem3b_r2")]
    out = []
    for a, b in pairs:
        rec = {}
        for tag, run in (("a", a), ("b", b)):
            p = os.path.join(RUNS, run, "gens.jsonl")
            if not os.path.exists(p):
                rec = None
                break
            tr = []
            with open(p, encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    if r.get("arm") == "A0":
                        tr.append(1.0 if "truncated" in (r.get("flags") or []) else 0.0)
            rec[tag] = {"truncated": float(np.mean(tr)) if tr else np.nan, "n": len(tr)}
        if rec:
            out.append({"measure": "truncated", "family": "Ministral3", "pair": f"{a} vs {b}",
                        "n": min(rec["a"]["n"], rec["b"]["n"]),
                        "abs_mean_diff": abs(rec["a"]["truncated"] - rec["b"]["truncated"])})
    return pd.DataFrame(out)


mlf = ministral_length_floor()
FLOOR_COLS = ["measure", "pair", "family", "n", "abs_mean_diff"]
floor_rows = []
for m in MEASURES:
    t = replicate_floor(cells, m)
    if not len(t) or "family" not in t.columns:
        t = pd.DataFrame(columns=FLOOR_COLS)
    if len(mlf) and m in set(mlf.measure) and not (len(t) and (t.family == "Ministral3").any()):
        t = pd.concat([t, mlf[mlf.measure == m]], ignore_index=True)   # fallback only while no scored Ministral pair exists
    for fam in MIN_SEC:
        tf = t[t.family == fam] if len(t) else t
        regen = float(tf.abs_mean_diff.max()) if len(tf) else np.nan
        sfl, nruns = seed_floor(cells, m, fam)
        used = np.nanmax([v for v in (regen, sfl) if v == v]) if any(v == v for v in (regen, sfl)) else np.nan
        floor_rows.append({"measure": m, "family": fam, "floor_regen": regen, "n_regen_pairs": int(len(tf)),
                           "floor_seed": sfl, "n_seed_runs": nruns, "floor_used": used})
FLOORS = pd.DataFrame(floor_rows)
FL = {(r.measure, r.family): r.floor_used for r in FLOORS.itertuples()}


def floor_of(m, fam):
    v = FL.get((m, fam), np.nan)
    return float(v) if v == v else np.nan


# ---------------------------------------------------------------- per-author effects
rows = []
for (au, cls, fam, pb), g in BT.groupby(["author", "author_class", "family", "params_b"]):
    raw = d[(d.author == au) & (d.family == fam) & (d.params_b == pb)]
    for m in MEASURES:
        a = g[g.kind == "adapter"].set_index("id")[m]
        b = g[g.kind == "base"].set_index("id")[m]
        idx = a.index.intersection(b.index)
        fr = pd.DataFrame({"id": idx, "diff": (a.loc[idx] - b.loc[idx]).values}).dropna(subset=["diff"])
        if len(fr) < 4:
            continue
        pt, lo, hi = cluster_bootstrap(fr, "diff", "id")
        se_boot = (hi - lo) / (2 * 1.959964) if np.isfinite(hi) and np.isfinite(lo) else np.nan
        try:
            p = float(stats.wilcoxon(fr["diff"].values).pvalue) if fr["diff"].abs().sum() > 0 else 1.0
        except Exception:
            p = np.nan
        fl = floor_of(m, fam)
        rows.append({"author": au, "author_class": cls, "family": fam, "params_b": pb, "measure": m,
                     "direction": direction(m), "effect": pt, "ci_low": lo, "ci_high": hi, "se_boot": se_boot,
                     "effect_toward_author": pt * toward(m),
                     "cohens_d": cohens_d(raw.loc[raw.kind == "adapter", m].values, raw.loc[raw.kind == "base", m].values),
                     "cliffs_delta": cliffs_delta(raw.loc[raw.kind == "adapter", m].values, raw.loc[raw.kind == "base", m].values),
                     "p_wilcoxon": p, "n_briefs": len(fr), "floor": fl,
                     "within_noise": (abs(pt) < fl) if (pt == pt and fl == fl) else np.nan,
                     "is_control_author": au == CONTROL_AUTHOR,
                     "train_examples_max": float(AUTH.loc[au, "train_examples_max"]) if au in AUTH.index else np.nan,
                     "train_briefs_passed": float(AUTH.loc[au, "train_briefs_passed"]) if au in AUTH.index else np.nan,
                     "words_total": float(AUTH.loc[au, "words_total"]) if au in AUTH.index else np.nan})
EFF = pd.DataFrame(rows)
EFF["cohens_d_toward_author"] = EFF["cohens_d"] * [toward(m) for m in EFF.measure]
EFF["q_bh"] = bh_fdr(EFF["p_wilcoxon"].values)
EFF["fdr_family"] = "per_author_adapter_contrast"
write_table(EFF, os.path.join(OUTD, "author_effects.csv"), floats=5)

POOLABLE = EFF[(~EFF.is_control_author) & EFF.se_boot.notna() & (EFF.se_boot > 0)]


# ---------------------------------------------------------------- DerSimonian-Laird
def dersimonian_laird(y, v):
    y = np.asarray(y, float); v = np.asarray(v, float)
    keep = np.isfinite(y) & np.isfinite(v) & (v > 0)
    y, v = y[keep], v[keep]
    k = int(len(y))
    if k == 0:
        return None
    w = 1.0 / v
    fixed = float((w * y).sum() / w.sum())
    Q = float((w * (y - fixed) ** 2).sum())
    df = k - 1
    C = float(w.sum() - (w ** 2).sum() / w.sum())
    tau2 = max(0.0, (Q - df) / C) if (C > 0 and df > 0) else 0.0
    ws = 1.0 / (v + tau2)
    pooled = float((ws * y).sum() / ws.sum())
    se = float(np.sqrt(1.0 / ws.sum()))
    I2 = float(max(0.0, (Q - df) / Q) * 100) if Q > 0 and df > 0 else 0.0
    z = pooled / se if se > 0 else np.nan
    p = float(2 * (1 - stats.norm.cdf(abs(z)))) if np.isfinite(z) else np.nan
    q_p = float(1 - stats.chi2.cdf(Q, df)) if df > 0 else np.nan
    if k >= 3 and df > 0:
        tcrit = float(stats.t.ppf(0.975, df - 1)) if df > 1 else np.nan
        half = tcrit * np.sqrt(tau2 + se ** 2) if np.isfinite(tcrit) else np.nan
        pi_lo, pi_hi = (pooled - half, pooled + half) if np.isfinite(half) else (np.nan, np.nan)
    else:
        pi_lo = pi_hi = np.nan
    return dict(k=k, pooled=pooled, se=se, ci_low=pooled - 1.959964 * se, ci_high=pooled + 1.959964 * se,
                fixed=fixed, Q=Q, df=df, p_Q=q_p, tau2=tau2, tau=float(np.sqrt(tau2)), I2=I2,
                z=z, p=p, pred_low=pi_lo, pred_high=pi_hi)


pool_rows, loo_rows = [], []
for (m, fam, pb), g in POOLABLE.groupby(["measure", "family", "params_b"]):
    r = dersimonian_laird(g.effect.values, g.se_boot.values ** 2)
    if r is None or r["k"] < 2:
        continue
    fl = floor_of(m, fam)
    pool_rows.append({"measure": m, "family": fam, "params_b": pb, "direction": direction(m), **r,
                      "pooled_toward_author": r["pooled"] * toward(m), "floor": fl,
                      "within_noise": abs(r["pooled"]) < fl if fl == fl else np.nan,
                      "n_authors": int(g.author.nunique()),
                      "authors": ",".join(sorted(g.author.unique()))})
    if r["k"] >= 3:
        for au in sorted(g.author.unique()):
            s = g[g.author != au]
            r2 = dersimonian_laird(s.effect.values, s.se_boot.values ** 2)
            if r2:
                loo_rows.append({"measure": m, "family": fam, "params_b": pb, "dropped_author": au,
                                 "pooled": r2["pooled"], "ci_low": r2["ci_low"], "ci_high": r2["ci_high"],
                                 "I2": r2["I2"], "k": r2["k"], "pooled_full": r["pooled"],
                                 "shift_from_full": r2["pooled"] - r["pooled"],
                                 "shift_over_floor": (r2["pooled"] - r["pooled"]) / fl if fl == fl and fl > 0 else np.nan})
POOL = pd.DataFrame(pool_rows)
POOL["q_bh"] = bh_fdr(POOL["p"].values)
POOL["fdr_family"] = "dl_pooled_effect"
LOO = pd.DataFrame(loo_rows)
write_table(POOL.drop(columns=["authors"]), os.path.join(OUTD, "pooled_dl.csv"), floats=5)
write_table(POOL[["measure", "family", "params_b", "n_authors", "authors"]], os.path.join(OUTD, "pooled_dl_authors.csv"), floats=5)
if len(LOO):
    write_table(LOO, os.path.join(OUTD, "loo_sensitivity.csv"), floats=5)
    LOOSUM = (LOO.groupby(["measure", "family", "params_b"])
              .apply(lambda s: pd.Series({"pooled_full": s.pooled_full.iloc[0], "loo_min": s.pooled.min(),
                                          "loo_max": s.pooled.max(), "max_abs_shift": s["shift_from_full"].abs().max(),
                                          "max_shift_author": s.loc[s["shift_from_full"].abs().idxmax(), "dropped_author"],
                                          "max_shift_over_floor": s.shift_over_floor.abs().max(),
                                          "sign_flips": int(((s.pooled * s.pooled_full) < 0).sum())}),
                     include_groups=False)
              .reset_index())
    write_table(LOOSUM, os.path.join(OUTD, "loo_summary.csv"), floats=5)
else:
    LOOSUM = pd.DataFrame()


# ---------------------------------------------------------------- moderators
def meta_reg(y, v, X, names):
    """Weighted meta-regression, DL tau2 from the intercept-only model."""
    y = np.asarray(y, float); v = np.asarray(v, float); X = np.asarray(X, float)
    keep = np.isfinite(y) & np.isfinite(v) & (v > 0) & np.isfinite(X).all(axis=1)
    y, v, X = y[keep], v[keep], X[keep]
    if len(y) <= X.shape[1]:
        return pd.DataFrame()
    base = dersimonian_laird(y, v)
    tau2 = base["tau2"] if base else 0.0
    W = np.diag(1.0 / (v + tau2))
    XtW = X.T @ W
    cov = np.linalg.pinv(XtW @ X)
    beta = cov @ (XtW @ y)
    se = np.sqrt(np.diag(cov))
    z = beta / se
    p = 2 * (1 - stats.norm.cdf(np.abs(z)))
    return pd.DataFrame({"term": names, "estimate": beta, "se": se, "ci_low": beta - 1.96 * se,
                         "ci_high": beta + 1.96 * se, "z": z, "p": p, "n_points": len(y), "tau2": tau2})


# (a) author class as a subgroup, inside each Qwen size
sub_rows = []
for (m, fam, pb), g in POOLABLE.groupby(["measure", "family", "params_b"]):
    tot = dersimonian_laird(g.effect.values, g.se_boot.values ** 2)
    if tot is None or tot["k"] < 4:
        continue
    qw, parts = 0.0, 0
    for cls, gc in g.groupby("author_class"):
        r = dersimonian_laird(gc.effect.values, gc.se_boot.values ** 2)
        if r is None:
            continue
        sub_rows.append({"measure": m, "family": fam, "params_b": pb, "author_class": cls, "k": r["k"],
                         "pooled": r["pooled"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "I2": r["I2"],
                         "tau2": r["tau2"], "floor": floor_of(m, fam)})
        if r["k"] >= 2:
            qw += r["Q"]; parts += 1
    if parts >= 2:
        qb = max(0.0, tot["Q"] - qw)
        dfb = parts - 1
        sub_rows.append({"measure": m, "family": fam, "params_b": pb, "author_class": "_between_", "k": tot["k"],
                         "pooled": np.nan, "ci_low": np.nan, "ci_high": np.nan, "I2": np.nan, "tau2": np.nan,
                         "Q_between": qb, "df_between": dfb, "p_between": float(1 - stats.chi2.cdf(qb, dfb)),
                         "floor": floor_of(m, fam)})
SUBG = pd.DataFrame(sub_rows)
if len(SUBG):
    SUBG["q_bh"] = np.nan
    mask = SUBG.author_class == "_between_"
    SUBG.loc[mask, "q_bh"] = bh_fdr(SUBG.loc[mask, "p_between"].values)
    SUBG["fdr_family"] = "author_class_Q_between"
    write_table(SUBG, os.path.join(OUTD, "subgroup_author_class.csv"), floats=5)

# (b) corpus size as a continuous moderator, inside each measure x family x size
mr_rows = []
for (m, fam, pb), g in POOLABLE.groupby(["measure", "family", "params_b"]):
    g = g[g.train_examples_max.notna()]
    if g.author.nunique() < 5:
        continue
    x = np.log2(g.train_examples_max.values)
    X = np.column_stack([np.ones(len(g)), x - x.mean()])
    t = meta_reg(g.effect.values, g.se_boot.values ** 2, X, ["intercept", "log2_train_examples_centred"])
    if len(t):
        t["measure"] = m; t["family"] = fam; t["params_b"] = pb
        t["n_authors"] = g.author.nunique()
        mr_rows.append(t)
METAREG = pd.concat(mr_rows, ignore_index=True) if mr_rows else pd.DataFrame()
if len(METAREG):
    slope = METAREG.term == "log2_train_examples_centred"
    METAREG["q_bh"] = np.nan
    METAREG.loc[slope, "q_bh"] = bh_fdr(METAREG.loc[slope, "p"].values)
    METAREG["fdr_family"] = "metareg_log_train_examples"
    write_table(METAREG, os.path.join(OUTD, "metareg_train_examples.csv"), floats=5)

# (c) one model per measure over every author x size x family point: class, corpus, family, size
mm_rows = []
for m, g in POOLABLE.groupby("measure"):
    g = g[g.train_examples_max.notna()].copy()
    if g.author.nunique() < 6:
        continue
    x = np.log2(g.train_examples_max.values)
    X = np.column_stack([np.ones(len(g)), x - x.mean(), np.log2(g.params_b.values) - np.log2(g.params_b.values).mean(),
                         (g.family == "Ministral3").astype(float).values,
                         (g.author_class == "contemporary").astype(float).values,
                         (g.author_class == "private").astype(float).values])
    t = meta_reg(g.effect.values, g.se_boot.values ** 2, X,
                 ["intercept", "log2_train_examples_centred", "log2_params_centred", "family_Ministral3",
                  "class_contemporary", "class_private"])
    if len(t):
        t["measure"] = m
        t["n_authors"] = g.author.nunique()
        mm_rows.append(t)
METAMULTI = pd.concat(mm_rows, ignore_index=True) if mm_rows else pd.DataFrame()
if len(METAMULTI):
    nonint = METAMULTI.term != "intercept"
    METAMULTI["q_bh"] = np.nan
    METAMULTI.loc[nonint, "q_bh"] = bh_fdr(METAMULTI.loc[nonint, "p"].values)
    METAMULTI["fdr_family"] = "metareg_multi_moderator"
    write_table(METAMULTI, os.path.join(OUTD, "metareg_multi.csv"), floats=5)

# ---------------------------------------------------------------- rank stability across sizes
rank_rows = []
for m in MEASURES:
    s = POOLABLE[(POOLABLE.measure == m) & (POOLABLE.family == "Qwen3") & (POOLABLE.params_b.isin(QWEN_SIZES))]
    w = s.pivot_table(index="author", columns="params_b", values="effect")
    for i, p1 in enumerate(QWEN_SIZES):
        for p2 in QWEN_SIZES[i + 1:]:
            if p1 in w.columns and p2 in w.columns:
                sub = w[[p1, p2]].dropna()
                if len(sub) >= 5:
                    r, lo, hi, p, n = spearman_ci(sub[p1].values, sub[p2].values)
                    rank_rows.append({"measure": m, "family": "Qwen3", "size_a": p1, "size_b": p2,
                                      "spearman": r, "ci_low": lo, "ci_high": hi, "p": p, "n_authors": n})
RANK = pd.DataFrame(rank_rows)
if len(RANK):
    RANK["q_bh"] = bh_fdr(RANK["p"].values)
    RANK["fdr_family"] = "rank_stability_across_sizes"
    write_table(RANK, os.path.join(OUTD, "rank_stability.csv"), floats=5)
write_table(FLOORS, os.path.join(OUTD, "floors.csv"), floats=6)

# ---------------------------------------------------------------- figures
def forest(measure, family, sizes, fname):
    s = EFF[(EFF.measure == measure) & (EFF.family == family) & (EFF.params_b.isin(sizes))]
    if not len(s):
        return None
    order = (s[s.params_b == sizes[0]].sort_values("effect").author.tolist()
             if len(s[s.params_b == sizes[0]]) else sorted(s.author.unique()))
    order += [a for a in sorted(s.author.unique()) if a not in order]
    fig, axes = plt.subplots(1, len(sizes), figsize=(4.4 * len(sizes), 0.36 * len(order) + 3.0), sharey=True, sharex=True)
    axes = np.atleast_1d(axes)
    fl = floor_of(measure, family)
    for ax, pb in zip(axes, sizes):
        g = s[s.params_b == pb].set_index("author")
        ys, xs, lo, hi, cols = [], [], [], [], []
        for i, au in enumerate(order):
            if au not in g.index:
                continue
            r = g.loc[au]
            ys.append(len(order) - i); xs.append(r.effect); lo.append(r.effect - r.ci_low); hi.append(r.ci_high - r.effect)
            cols.append("tab:gray" if r.is_control_author else
                        {"period": "tab:blue", "contemporary": "tab:orange", "private": "tab:green"}[r.author_class])
        ax.axvspan(-fl, fl, color="gray", alpha=.16)
        ax.axvline(0, color="k", lw=.8)
        for y, x, l, h, c in zip(ys, xs, lo, hi, cols):
            ax.errorbar(x, y, xerr=[[l], [h]], fmt="o", color=c, capsize=2, ms=5)
        p = POOL[(POOL.measure == measure) & (POOL.family == family) & (POOL.params_b == pb)]
        if len(p):
            pr = p.iloc[0]
            ax.errorbar(pr.pooled, 0.2, xerr=[[pr.pooled - pr.ci_low], [pr.ci_high - pr.pooled]], fmt="D",
                        color="k", capsize=3, ms=7)
            ax.plot([pr.pred_low, pr.pred_high], [0.2, 0.2], color="k", lw=1, ls=":")
            ax.set_title(f"{family} {pb:g}B\nDL {pr.pooled:+.3f} [{pr.ci_low:+.3f}, {pr.ci_high:+.3f}], "
                         f"I2 {pr.I2:.0f}%, k={int(pr.k)}", fontsize=8)
        else:
            ax.set_title(f"{family} {pb:g}B", fontsize=8)
        ax.set_yticks([len(order) - i for i in range(len(order))])
        ax.set_yticklabels(order, fontsize=8)
        ax.set_xlabel("adapter minus base", fontsize=8)
        ax.grid(alpha=.2, axis="x")
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=t) for t, c in
               [("period", "tab:blue"), ("contemporary", "tab:orange"), ("private", "tab:green"),
                (f"{CONTROL_AUTHOR} (control, not pooled)", "tab:gray")]]
    handles.append(plt.Line2D([], [], marker="D", ls="", color="k", label="DL pooled"))
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=7, frameon=False)
    fig.suptitle(f"{lab(measure)} - per-author adapter effect, brief-cluster 95% CI\n"
                 f"grey band = replicate floor; black diamond = DerSimonian-Laird pooled, dotted = prediction interval",
                 fontsize=10)
    fig.tight_layout(rect=[0, 0.05, 1, 0.93])
    return savefig(fig, os.path.join(OUTD, fname))


figs = []
for m in FOREST:
    p = forest(m, "Qwen3", QWEN_SIZES, f"fig_forest_qwen_{m}.png")
    if p:
        figs.append((f"Forest, Qwen3, {lab(m)}", p))
for m in ["luar_cos_ref", "per"]:
    p = forest(m, "Ministral3", [3.0, 8.0, 14.0], f"fig_forest_ministral_{m}.png")
    if p:
        figs.append((f"Forest, Ministral 3, {lab(m)}", p))

# I2 summary
fig, ax = plt.subplots(figsize=(11, 4.6))
piv = POOL[POOL.family == "Qwen3"].pivot_table(index="measure", columns="params_b", values="I2")
piv = piv.reindex([m for m in MEASURES if m in piv.index])
w = 0.26
for i, pb in enumerate(sorted(piv.columns)):
    ax.bar(np.arange(len(piv)) + (i - 1) * w, piv[pb].values, width=w, label=f"Qwen3 {pb:g}B")
ax.set_xticks(np.arange(len(piv))); ax.set_xticklabels(piv.index, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("I-squared (% of variance between authors)", fontsize=9)
ax.axhline(75, color="k", ls=":", lw=1)
ax.set_ylim(0, 122); ax.set_xlim(-0.6, len(piv) - 0.4)
ax.legend(fontsize=8, frameon=False, ncol=3, loc="upper center"); ax.grid(alpha=.25, axis="y")
ax.set_title("How much of the adapter effect is the author: I-squared across authors, by measure and size", fontsize=10)
fig.tight_layout()
f_i2 = savefig(fig, os.path.join(OUTD, "fig_i2_by_measure.png"))
figs.append(("Between-author heterogeneity by measure", f_i2))

# author profile heatmap (Cohen's d, signed toward the author, Qwen mean over sizes)
prof = (EFF[(EFF.family == "Qwen3") & (EFF.params_b.isin(QWEN_SIZES))]
        .pivot_table(index="author", columns="measure", values="cohens_d_toward_author", aggfunc="mean"))
prof = prof[[m for m in MEASURES if m in prof.columns]]
fig, ax = plt.subplots(figsize=(1.05 * len(prof.columns) + 3.5, 0.42 * len(prof) + 2.4))
vmax = float(np.nanmax(np.abs(prof.values)))
im = ax.imshow(prof.values, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
ax.set_xticks(range(len(prof.columns)))
ax.set_xticklabels([c + (" (raw)" if direction(c) == "0" else "") for c in prof.columns], rotation=40, ha="right", fontsize=8)
ax.set_yticks(range(len(prof.index))); ax.set_yticklabels(prof.index, fontsize=8)
for i in range(prof.shape[0]):
    for j in range(prof.shape[1]):
        v = prof.values[i, j]
        if v == v:
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=6,
                    color="white" if abs(v) > .6 * vmax else "black")
fig.colorbar(im, ax=ax, label="Cohen's d, signed toward the author")
ax.set_title("Adapter effect per author (Qwen3, mean over 4B/8B/14B); red = toward the author.\n"
             "Measures marked (raw) have no better/worse direction in the dictionary, so their sign is the raw difference.",
             fontsize=9)
fig.tight_layout()
f_prof = savefig(fig, os.path.join(OUTD, "fig_author_profile.png"))
figs.append(("Author profile of the adapter effect", f_prof))

# corpus-size moderator scatter
fig, axes = plt.subplots(1, 4, figsize=(17, 4.2))
for ax, m in zip(axes, FOREST):
    s = POOLABLE[(POOLABLE.measure == m) & (POOLABLE.family == "Qwen3") & (POOLABLE.params_b.isin(QWEN_SIZES))]
    for cls, c in [("period", "tab:blue"), ("contemporary", "tab:orange"), ("private", "tab:green")]:
        g = s[s.author_class == cls]
        ax.errorbar(g.train_examples_max, g.effect, yerr=[g.effect - g.ci_low, g.ci_high - g.effect],
                    fmt="o", color=c, ms=4, capsize=2, alpha=.85, label=cls)
    fl = floor_of(m, "Qwen3")
    ax.axhspan(-fl, fl, color="gray", alpha=.16); ax.axhline(0, color="k", lw=.8)
    ax.set_xscale("log", base=2); ax.set_xlabel("fit examples (capped at 1290)", fontsize=8)
    ax.set_ylabel("adapter minus base", fontsize=8); ax.set_title(lab(m), fontsize=9); ax.grid(alpha=.25)
axes[0].legend(fontsize=7, frameon=False)
fig.suptitle("Per-author adapter effect against corpus size, Qwen3, all three sizes", fontsize=10)
fig.tight_layout(rect=[0, 0, 1, 0.93])
f_corp = savefig(fig, os.path.join(OUTD, "fig_effect_vs_corpus.png"))
figs.append(("Effect against corpus size", f_corp))

# ---------------------------------------------------------------- README numbers
def prow(m, fam, pb):
    s = POOL[(POOL.measure == m) & (POOL.family == fam) & (POOL.params_b == pb)]
    return s.iloc[0] if len(s) else None


n_auth_pool = int(POOLABLE.author.nunique())
n_auth_qwen = int(POOLABLE[POOLABLE.family == "Qwen3"].author.nunique())
n_auth_min = int(POOLABLE[POOLABLE.family == "Ministral3"].author.nunique())
cap_examples = int(AUTH.train_examples_max.max())
n_at_cap = int((AUTH.train_examples_max == AUTH.train_examples_max.max()).sum())
_f19 = FLOORS[FLOORS.measure == "luar_cos_ref"]
n_regen_q19 = int(_f19[_f19.family == "Qwen3"].n_regen_pairs.iloc[0])
n_regen_m19 = int(_f19[_f19.family == "Ministral3"].n_regen_pairs.iloc[0])
n_seed_q19 = int(_f19[_f19.family == "Qwen3"].n_seed_runs.iloc[0])
n_seed_m19 = int(_f19[_f19.family == "Ministral3"].n_seed_runs.iloc[0])
n_seed_used = int((FLOORS.floor_used == FLOORS.floor_seed).sum())
n_floor_rows = int(FLOORS.floor_used.notna().sum())
n_eff = int(len(EFF))
n_noise = int(EFF["within_noise"].fillna(False).astype(bool).sum())
n_sig = int(((EFF.q_bh < 0.05) & (~EFF["within_noise"].fillna(True).astype(bool))).sum())
i2_qwen = POOL[POOL.family == "Qwen3"].groupby("measure").I2.mean().sort_values(ascending=False)
hi_i2 = i2_qwen.head(3)
lo_i2 = i2_qwen.tail(3)
p_lr8 = prow("luar_cos_ref", "Qwen3", 8.0)
p_ls8 = prow("luar_cos_source", "Qwen3", 8.0)
p_per8 = prow("per", "Qwen3", 8.0)
p_hx8 = prow("hapax_w300", "Qwen3", 8.0)
n_pool_sig = int(((POOL.q_bh < 0.05) & (~POOL["within_noise"].fillna(True).astype(bool))).sum())
n_pool = int(len(POOL))
n_i2_high = int((POOL[POOL.family == "Qwen3"].I2 > 75).sum())
n_pool_q = int(len(POOL[POOL.family == "Qwen3"]))

mr_slope = METAREG[METAREG.term == "log2_train_examples_centred"] if len(METAREG) else pd.DataFrame()
n_mr_sig = int((mr_slope.q_bh < 0.05).sum()) if len(mr_slope) else 0


def mrs(measure, pb, fam="Qwen3"):
    s = mr_slope[(mr_slope.measure == measure) & (mr_slope.params_b == pb) & (mr_slope.family == fam)] if len(mr_slope) else pd.DataFrame()
    return s.iloc[0] if len(s) else None


mr_lr8, mr_per8, mr_cov8, mr_tr14 = mrs("luar_cos_ref", 8.0), mrs("per", 8.0), mrs("coverage", 8.0), mrs("truncated", 14.0)
mm_fam = METAMULTI[METAMULTI.term == "family_Ministral3"] if len(METAMULTI) else pd.DataFrame()
mm_fam_lr = mm_fam[mm_fam.measure == "luar_cos_ref"].iloc[0] if len(mm_fam[mm_fam.measure == "luar_cos_ref"]) else None
mm_class = METAMULTI[METAMULTI.term.isin(["class_contemporary", "class_private"])] if len(METAMULTI) else pd.DataFrame()
n_class_sig = int((mm_class.q_bh < 0.05).sum()) if len(mm_class) else 0
n_class_tests = int(len(mm_class))
n_between_sig = int((SUBG[SUBG.author_class == "_between_"].q_bh < 0.05).sum()) if len(SUBG) else 0
n_between = int((SUBG.author_class == "_between_").sum()) if len(SUBG) else 0
cls8 = SUBG[(SUBG.measure == "luar_cos_ref") & (SUBG.params_b == 8.0) & (SUBG.author_class != "_between_")] if len(SUBG) else pd.DataFrame()
cls8_txt = "; ".join(f"{r.author_class} {r.pooled:+.3f} [{r.ci_low:+.3f}, {r.ci_high:+.3f}] (k={int(r.k)})"
                     for r in cls8.itertuples()) if len(cls8) else "n/a"
n_flips = int(LOOSUM.sign_flips.sum()) if len(LOOSUM) else 0
rank_med = float(RANK.spearman.median()) if len(RANK) else np.nan
rank_lo = float(RANK.spearman.min()) if len(RANK) else np.nan
rank_hi = float(RANK.spearman.max()) if len(RANK) else np.nan
loo_worst = LOOSUM.sort_values("max_shift_over_floor", ascending=False).head(1) if len(LOOSUM) else pd.DataFrame()

tables = [
    ("DerSimonian-Laird pooled adapter effect by measure, family and size",
     POOL[["measure", "family", "params_b", "k", "pooled", "ci_low", "ci_high", "tau", "I2", "p_Q", "q_bh",
           "pred_low", "pred_high", "floor", "within_noise"]]),
    ("Per-author effects on the content-free voice anchor (luar_cos_ref)",
     EFF[EFF.measure == "luar_cos_ref"][["author", "author_class", "family", "params_b", "effect", "ci_low",
                                         "ci_high", "cohens_d", "cliffs_delta", "q_bh", "floor", "within_noise"]]),
    ("Author class as a subgroup, with the between-class Q test",
     SUBG[["measure", "family", "params_b", "author_class", "k", "pooled", "ci_low", "ci_high", "I2"] +
          ([c for c in ["Q_between", "df_between", "p_between", "q_bh"] if c in SUBG.columns])] if len(SUBG) else pd.DataFrame()),
    ("Corpus size as a moderator (meta-regression slope per doubling of fit examples)",
     mr_slope[["measure", "family", "params_b", "n_authors", "estimate", "se", "ci_low", "ci_high", "p", "q_bh"]] if len(mr_slope) else pd.DataFrame()),
    ("All moderators in one model per measure", METAMULTI[["measure", "term", "estimate", "ci_low", "ci_high", "p", "q_bh", "n_points"]] if len(METAMULTI) else pd.DataFrame()),
    ("Leave-one-author-out sensitivity of the pooled effect", LOOSUM),
    ("Is the same author helped at every size? Rank stability of the per-author effect", RANK),
    ("Noise floors used", FLOORS),
]

runtime = time.time() - T0

what = f"""
Takes the adapter-versus-base contrast apart by author. For every author x family x size cell it
computes the brief-paired effect on {len(MEASURES)} measures with a cluster-bootstrap interval, Cohen's d
and Cliff's delta ({n_eff} contrasts in all), then pools those per-author effects with a
DerSimonian-Laird random-effects model per measure, family and size, reporting tau, I-squared, the
between-author Q test and a prediction interval. It then asks what predicts an author's effect
(author class, log fit examples, family, size), how much the pooled number depends on any single
author (leave-one-out), and whether the same authors are helped at every size (rank stability).

{n_auth_pool} authors enter the pools. {CONTROL_AUTHOR} (the v1 chunking control) is computed and kept in
author_effects.csv but excluded from every pooled estimate, since its runs differ from
{CONTROL_AUTHOR}_v2 only in how the corpus was chunked.
"""

how = f"""
Data: data/master/cells.parquet, arm A0, non-replicate rows, both samples. The two samples of a
cell are averaged first so the brief is the unit inside an author, then base and adapter are paired
on the brief.

Effect and interval. The per-author effect is the brief-paired mean difference (adapter minus
base). Its interval is a cluster bootstrap over briefs (lib.cluster_bootstrap, 2000 resamples,
seed 0) and its variance for the meta-analysis is the squared bootstrap standard error, taken as
the interval width divided by 2 x 1.96. Cohen's d and Cliff's delta come from the raw cell
distributions. p-values are Wilcoxon signed-rank on the per-brief differences.

Pooling. DerSimonian-Laird is implemented in the script: Q from the fixed-effect weights, tau2 =
max(0, (Q - df) / C) with C = sum(w) - sum(w^2)/sum(w), random-effects weights 1/(v + tau2), and
I-squared = max(0, (Q - df)/Q). The prediction interval uses t on df - 1 and sqrt(tau2 + se^2); it
is the interval to quote for "what would the next author do", and it is much wider than the
confidence interval whenever tau is non-zero.

Moderators. Three passes, all weighted by 1/(v + tau2): author class as a subgroup with a
between-class Q test inside each measure x family x size; log2 fit examples as a continuous
moderator inside each measure x family x size (authors with a recorded cap only); and one model per
measure over every author x size x family point with log2 fit examples, log2 parameters, family and
two author-class dummies. With {n_auth_pool} authors these are descriptive fits, and the multi-moderator
model reuses each author three times, so its standard errors are optimistic.

Correction and floors. BH-FDR is applied inside each family of tests separately and the family is
named in the fdr_family column: per-author contrasts ({int(EFF.p_wilcoxon.notna().sum())} tests), pooled DL
effects ({n_pool} tests), between-class Q ({n_between} tests), the corpus-size slope
({int(len(mr_slope))} tests), the multi-moderator terms and the rank-stability correlations. A q below
0.05 means survival inside that one family of tests in this one script, not across the programme.

Every effect is printed beside the replicate floor of its measure in its family. Two floors are
computed per measure and family and the larger of the two is the one used (floor_used in
floors.csv): a regeneration floor from lib.replicate_floor over the twice-generated base
configurations ({n_regen_q19} pairs on Qwen3, {n_regen_m19} on Ministral 3, and both Ministral pairs
sit at the 3B rung and were scored on 2026-09-10, so the 8B and 14B Ministral rows are read against
a floor measured at 3B); and a seed-split floor, the mean over sample 0 against the mean over
sample 1 inside one base run, maximised over that family's base runs ({n_seed_q19} Qwen runs,
{n_seed_m19} Ministral runs). The seed-split floor is the larger on {n_seed_used} of the
{n_floor_rows} measure x family rows that carry a floor at all, so it is usually the one in force;
coverage has no seed-split floor and falls back to its single regeneration pair.
"""

reading = f"""
Unit of replication. The author. There are {n_auth_qwen} of them in the Qwen3 pools and
{n_auth_min} in the Ministral pools, so a pooled number is an average over {n_auth_qwen} cases at
best, and the prediction interval, not the confidence interval, is what applies to an author who
is not one of them.

1. Between-author heterogeneity dominates every pooled estimate here. I-squared over authors is above 75% in
{n_i2_high} of the {n_pool_q} Qwen3 measure x size pools. The measures with the most between-author variance are
{', '.join(f'{m} ({v:.0f}%)' for m, v in hi_i2.items())}; the least are
{', '.join(f'{m} ({v:.0f}%)' for m, v in lo_i2.items())}. Where I-squared is that high the pooled mean
describes no author in particular: read the forest plot and the prediction interval instead.

2. The pooled voice effect at Qwen3 8B is {fmt(p_lr8.pooled, 4) if p_lr8 is not None else 'n/a'}
[{fmt(p_lr8.ci_low, 4) if p_lr8 is not None else 'n/a'}, {fmt(p_lr8.ci_high, 4) if p_lr8 is not None else 'n/a'}]
on luar_cos_ref with tau {fmt(p_lr8.tau, 4) if p_lr8 is not None else 'n/a'} and a prediction interval of
[{fmt(p_lr8.pred_low, 4) if p_lr8 is not None else 'n/a'}, {fmt(p_lr8.pred_high, 4) if p_lr8 is not None else 'n/a'}]
against a floor of {fmt(floor_of('luar_cos_ref', 'Qwen3'), 4)}. The prediction interval spanning zero is
the honest statement: the next author might gain, and might not.

3. What survives. {n_sig} of the {n_eff} per-author contrasts clear both their floor and BH-FDR at q < 0.05
inside the {int(EFF.p_wilcoxon.notna().sum())}-test per-author family; {n_noise} sit inside the floor.
Among the pooled estimates, {n_pool_sig} of {n_pool} clear both.

4. Of the moderators tested here, corpus size is the one with the widest support. The
meta-regression slope per doubling of fit examples is fitted on Qwen3 only and survives BH-FDR in
{n_mr_sig} of {int(len(mr_slope))} measure x size fits, with the same sign at all three sizes on every measure:
at Qwen3 8B, luar_cos_ref
{fmt(mr_lr8.estimate, 4) if mr_lr8 is not None else 'n/a'} [{fmt(mr_lr8.ci_low, 4) if mr_lr8 is not None else 'n/a'}, {fmt(mr_lr8.ci_high, 4) if mr_lr8 is not None else 'n/a'}]
per doubling (more data, more voice), per {fmt(mr_per8.estimate, 4) if mr_per8 is not None else 'n/a'}
[{fmt(mr_per8.ci_low, 4) if mr_per8 is not None else 'n/a'}, {fmt(mr_per8.ci_high, 4) if mr_per8 is not None else 'n/a'}]
(more data, less echo damage), coverage {fmt(mr_cov8.estimate, 2) if mr_cov8 is not None else 'n/a'}
[{fmt(mr_cov8.ci_low, 2) if mr_cov8 is not None else 'n/a'}, {fmt(mr_cov8.ci_high, 2) if mr_cov8 is not None else 'n/a'}]
points (more data, less coverage lost) and, at 14B, truncation
{fmt(mr_tr14.estimate, 4) if mr_tr14 is not None else 'n/a'}
[{fmt(mr_tr14.ci_low, 4) if mr_tr14 is not None else 'n/a'}, {fmt(mr_tr14.ci_high, 4) if mr_tr14 is not None else 'n/a'}].
Corpus size was not assigned, it is capped at {cap_examples} fit examples for {n_at_cap} of the
authors, and there are {n_auth_qwen} authors carrying the whole slope, so this is an observed
association across {n_auth_qwen} corpora, consistent with more data buying more voice and less
echo, and it is not a dose-response curve. Coverage is an LLM-judged adherence measure, so the
coverage row is a judge reading rather than a count of covered events. 13_corpus_data_effects is
where the corpus question belongs; this script only locates where the between-author variance sits.

4b. Author class is a much weaker descriptor than its Q test suggests. The between-class Q rejects
in {n_between_sig} of {n_between} fits, but that test uses fixed-effect weights and at I-squared near 95% it is
anti-conservative; the class pools themselves overlap heavily (luar_cos_ref at Qwen3 8B:
{cls8_txt}). In the random-effects multi-moderator model the class terms survive correction in
{n_class_sig} of {n_class_tests} tests. Where the two disagree, believe the weaker claim. Author class is also
confounded with the reference pool: every author is anchored against the same period stranger pool,
so the contemporary and private classes are positioned against a different century from their own.
The family term in that same model survives correction in {int((mm_fam.q_bh < 0.05).sum()) if len(mm_fam) else 0} of
{len(mm_fam)} measures: on luar_cos_ref it is
{fmt(mm_fam_lr.estimate, 4) if mm_fam_lr is not None else 'n/a'}
[{fmt(mm_fam_lr.ci_low, 4) if mm_fam_lr is not None else 'n/a'}, {fmt(mm_fam_lr.ci_high, 4) if mm_fam_lr is not None else 'n/a'}]
for Ministral 3 against Qwen3. That term rests on the {n_auth_min} authors run in both families, so
it is the cross-family result of script 18 arriving by another route on {n_auth_min} authors, not an
independent replication of it.

5. The author effect is more stable across model size than across measure. The per-author effect at
one Qwen size correlates with the same author's effect at another at a median Spearman of
{fmt(rank_med, 2)} over {len(RANK)} measure x size-pair fits (range {fmt(rank_lo, 2)} to {fmt(rank_hi, 2)},
{n_auth_qwen} authors per fit), which is consistent with the authors the adapter suits being the
same ones at every scale. The author profile figure shows the same author moving toward their
reference on one instrument and away on another.

6. Single authors move the pool. {'The largest leave-one-out shift is ' + str(loo_worst.iloc[0]['max_shift_author']) + ' on ' + str(loo_worst.iloc[0]['measure']) + ' at ' + f"{loo_worst.iloc[0]['family']} {loo_worst.iloc[0]['params_b']:g}B" + f", which moves the pooled effect by {loo_worst.iloc[0]['max_abs_shift']:.4f}, or {loo_worst.iloc[0]['max_shift_over_floor']:.1f} floors." if len(loo_worst) else 'Leave-one-out was not computable.'}
Check loo_summary.csv before quoting any pooled number.

What would overturn this. More authors. Nothing in this folder is limited by briefs: the per-author intervals are already narrow relative to the spread between authors. A
pooled effect whose I-squared is above 75% could change sign or size with a different set of
{n_auth_qwen} authors, and the sign_flips column in loo_summary.csv counts {n_flips} pooled estimates that
change sign when a single author is dropped.

What this does not show. It does not show that corpus size causes the difference: the {n_at_cap} authors
at the top of the corpus axis are also the ones whose fit examples were capped at {cap_examples},
and no author was assigned a corpus. It does not compare adapters with prompting arms (12_arm_effects), and it says
nothing about arms other than A0, or about judged quality except through the coverage rows, which
exist on Qwen only and on a subset of its cells. It does not separate the adapter from the
generation length it produces.
"""

n_zero_se = int(len(EFF[~EFF.is_control_author]) - len(POOLABLE))
caveats = [
    f"{n_zero_se} non-control cell{'s' if n_zero_se != 1 else ''} ha{'ve' if n_zero_se != 1 else 's'} a bootstrap interval of zero width (the per-brief difference is constant, which happens when neither condition ever truncates) and cannot carry an inverse-variance weight, so they are dropped from the pools. That is why k is below the author count in some rows of pooled_dl.csv; pooled_dl_authors.csv lists the authors actually pooled.",
    "The between-class Q test decomposes the fixed-effect Q (Q total minus the sum of the within-class Q), so it ignores tau2. At the I-squared levels seen here it rejects easily and should not be read as evidence that class matters; the random-effects class terms in metareg_multi.csv are the test to quote.",
    f"The bootstrap standard error is taken as the interval width over 2 x 1.96. Where a per-brief difference distribution is very skewed (truncation and coverage in particular) that overstates the symmetry of the interval, and the DL weights inherit it.",
    f"Coverage is an LLM-judged adherence measure, not a ground-truth count of covered events, and it is judged on a subset of cells and on no Ministral cell at all, so its pools rest on fewer authors than the other measures ({int(POOL[POOL.measure == 'coverage'].k.max()) if len(POOL[POOL.measure == 'coverage']) else 0} at most) and its floor comes from a single Qwen replicate pair. Ten runs' coverage rows were error rows from the 2026-09-09 credit outage and are being regenerated, so the coverage pools will move when that rerun lands.",
    f"The Ministral regeneration floor rests on {n_regen_m19} replicate pairs (chesterton_basem3b_r2, patrick_v2_basem3b_r2), both at the 3B rung and scored on 2026-09-10, and the truncated row counts those pairs a second time from a gens.jsonl recomputation. There is no Ministral replicate at 8B or 14B, so a 3B floor is what the larger Ministral rows are read against.",
    f"Ministral pools have k = {n_auth_min} authors. tau2, I-squared and the prediction interval are barely identified at that k and are reported for completeness, not for quotation. Ministral runs carry no judge data at all.",
    "Every author is anchored against the same fourteen-author period stranger pool, so contemporary and private authors are positioned against a different century from their own. Author class is a moderator here, which puts that confound directly inside the class comparison; 23_register_matched_pool holds the register-matched version, where contemporary and private authors move down by more than the adapter gain.",
    "Proposition echo is close to permutation-invariant, so the per rows measure restatement between sentences and not the order those sentences arrive in. The eval-cache measures (per, otd_js, hapax_w300) exist for arm A0 only, which is the arm this script uses.",
    f"{CONTROL_AUTHOR} is the v1 chunking control and shares an underlying corpus with {CONTROL_AUTHOR}_v2; it is excluded from every pool but kept in author_effects.csv, and it exists at 4B only.",
    "The multi-moderator model uses each author once per size and per family, so its points are not independent; its p-values are optimistic and are reported as descriptive.",
    "Qwen3 1.7B exists for one author only, so it never enters a pool; its per-author rows are in author_effects.csv.",
    "Cohen's d is computed on the raw cell distributions of the two conditions, not on the paired differences, so it is a between-condition standardised difference and is not the standardisation implied by the paired interval.",
    "Truncation rates differ by family and by kind; any measure that moves with length carries that confound into its per-author effect here (see 17_length_truncation).",
]

write_readme(OUTD, "19_author_heterogeneity - the adapter effect author by author", what, how, reading,
             caveats, tables, figs,
             extra=f"Runtime {runtime:.1f} s. {n_eff} per-author contrasts, {n_pool} pooled estimates, "
                   f"{n_auth_pool} authors in the pools.")

print(f"[19_author_heterogeneity] done in {runtime:.1f}s -> {OUTD}")
print(f"  per-author contrasts {n_eff}, within noise {n_noise}, survive FDR+floor {n_sig}")
print(f"  pooled rows {n_pool}; I2 > 75% in {n_i2_high}/{n_pool_q} Qwen pools")
if p_lr8 is not None:
    print(f"  luar_cos_ref Qwen3 8B pooled {p_lr8.pooled:+.4f} [{p_lr8.ci_low:+.4f}, {p_lr8.ci_high:+.4f}] "
          f"I2 {p_lr8.I2:.0f}% pred [{p_lr8.pred_low:+.4f}, {p_lr8.pred_high:+.4f}]")
