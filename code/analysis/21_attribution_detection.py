"""21_attribution_detection.py -- can an attributor name the author, and can a detector name the machine.

Attribution: how often each of the three style embeddings and Burrows Delta rank the target
author first among the reference authors, by configuration, with Wilson and brief-cluster
intervals and a brief-paired adapter-versus-base contrast against the replicate floor; which
author each instrument confuses the target with. Copying: memorisation flag, 8-gram overlap and
longest common substring by kind and size. Detection: the detector-tell dissociation table from
data/eval_results/dtd.md parsed and set beside the winsorised tell index, the hard-tell index
and the template rate for the same runs and configurations.

Reads data/ only; writes analysis/21_attribution_detection/ only.
"""
from __future__ import annotations

import math
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (AUTHOR_CLASS, EVAL, VARIABLES, bh_fdr, cohens_d, cliffs_delta,  # noqa: E402
                 load_all, main_cells, md_table, outdir, replicate_floor, savefig,
                 write_readme, write_table)

OUTD = outdir("21_attribution_detection")
Z95 = 1.959963984540054
ATTRIB = {"luar_attrib": "LUAR", "wegmann_attrib": "Wegmann", "styledist_attrib": "StyleDistance",
          "delta_top1": "Burrows Delta"}
NEAREST = {"luar_attrib": "luar_nearest", "wegmann_attrib": "wegmann_nearest",
           "styledist_attrib": "styledist_nearest", "delta_top1": "delta_nearest"}
TELLS = ["arti_w", "arti_hard_w", "template_rate", "staccato_anaphora", "rfpd_w"]


def wilson(k, n, z=Z95):
    k, n = float(k), float(n)
    if n <= 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
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


def paired_gain(g, measure, seed=0):
    w = g.pivot_table(index="id", columns="kind", values=measure, aggfunc="mean").dropna()
    if len(w) < 5 or "adapter" not in w.columns or "base" not in w.columns:
        return None
    diff = (w["adapter"] - w["base"]).values
    pt, lo, hi = cluster_boot(w.index.values, diff, np.mean, n=800, seed=seed)
    return {"n_briefs": int(len(w)), "base_mean": float(w["base"].mean()),
            "adapter_mean": float(w["adapter"].mean()), "adapter_minus_base": pt,
            "ci_low": lo, "ci_high": hi,
            "cohens_d": cohens_d(w["adapter"].values, w["base"].values),
            "cliffs_delta": cliffs_delta(w["adapter"].values, w["base"].values)}


def floor_for(cells, measure):
    t = replicate_floor(cells, measure)
    out = {}
    for fam in ["Qwen3", "Ministral3"]:
        sub = t[t.family == fam] if len(t) else t
        out[fam] = float(sub.abs_mean_diff.max()) if len(sub) else np.nan
    return out


# ------------------------------------------------------------------ load
print("loading ...")
cells, runs, authors, briefs, refs = load_all()
cells = cells.copy()
cells["delta_top1"] = (cells.delta_rank <= 1).astype(int)   # derived here, per the plan's definition
d = main_cells(cells).copy()
d["delta_nearest_is_author"] = (d.delta_nearest == d.author)
# The candidate pool is per run: the "other:<author>" reference groups scored inside that run,
# plus the target. It is NOT the union of nearest labels across runs (22 names), which would
# understate chance; the largest observed delta_rank is the check.
pool = refs.groupby("run", observed=True).group.apply(
    lambda s: len({x for x in s if str(x).startswith("other:")}) + 1).rename("pool_size")
d = d.merge(pool, on="run", how="left")
pool_min, pool_max = int(pool.min()), int(pool.max())
chance = float((1.0 / d.pool_size).mean())
n_names_seen = int(pd.concat([d.luar_nearest, d.wegmann_nearest, d.styledist_nearest, d.delta_nearest]).nunique())
max_delta_rank = int(cells.delta_rank.max())

# ================================================================== 1. attribution rates
print("1. attribution rates ...")
rows = []
for keys, g in d.groupby(["family", "params_b", "kind"], observed=True):
    for col, name in ATTRIB.items():
        k, n = int(g[col].sum()), int(len(g))
        p, lo, hi = wilson(k, n)
        _, blo, bhi = cluster_boot(g.id.values, g[col].values.astype(float), np.mean, n=800, seed=2)
        au = g.groupby("author", observed=True)[col].mean()
        apt, alo, ahi = cluster_boot(au.index.values, au.values, np.mean, n=1000, seed=4)
        rows.append({"family": keys[0], "params_b": keys[1], "kind": keys[2], "instrument": name,
                     "n_cells": n, "n_correct": k, "rate": p, "wilson_low": lo, "wilson_high": hi,
                     "brief_ci_low": blo, "brief_ci_high": bhi, "n_authors": g.author.nunique(),
                     "author_mean_rate": apt, "author_ci_low": alo, "author_ci_high": ahi,
                     "chance": float((1.0 / g.pool_size).mean()),
                     "pool_size_min": int(g.pool_size.min()), "pool_size_max": int(g.pool_size.max())})
attrib_tab = pd.DataFrame(rows).sort_values(["instrument", "family", "params_b", "kind"]).reset_index(drop=True)
write_table(attrib_tab, os.path.join(OUTD, "attribution_rates.csv"))

# per author x family x size x kind, for the heterogeneity behind the pooled number
rows = []
for keys, g in d.groupby(["author", "family", "params_b", "kind"], observed=True):
    row = {"author": keys[0], "author_class": AUTHOR_CLASS.get(keys[0], ""), "family": keys[1],
           "params_b": keys[2], "kind": keys[3], "n_cells": len(g)}
    for col, name in ATTRIB.items():
        row[name] = float(g[col].mean())
    rows.append(row)
attrib_author = pd.DataFrame(rows).sort_values(["author", "family", "params_b", "kind"]).reset_index(drop=True)
write_table(attrib_author, os.path.join(OUTD, "attribution_by_author.csv"))

# ================================================================== 2. adapter minus base
print("2. adapter minus base ...")
FLOORS = {c: floor_for(cells, c) for c in ATTRIB}
gain_rows = []
for keys, g in d.groupby(["family", "params_b", "author"], observed=True):
    for col, name in ATTRIB.items():
        r = paired_gain(g, col, seed=6)
        if r is None:
            continue
        fam = keys[0]
        fl = FLOORS[col][fam]
        fl_src = "own family"
        if fl != fl:
            fl, fl_src = FLOORS[col]["Qwen3"], "Qwen3 stand-in (no Ministral replicate)"
        gain_rows.append({"family": fam, "params_b": keys[1], "author": keys[2], "instrument": name,
                          **r, "replicate_floor": fl, "floor_source": fl_src,
                          "above_floor": bool(abs(r["adapter_minus_base"]) > fl),
                          "ci_excludes_zero": bool(r["ci_low"] > 0 or r["ci_high"] < 0)})
gain_tab = pd.DataFrame(gain_rows)
write_table(gain_tab, os.path.join(OUTD, "attribution_adapter_minus_base.csv"))

# pooled over authors, per instrument x family x size: the author is the unit
pool_rows = []
for keys, g in gain_tab.groupby(["instrument", "family", "params_b"], observed=True):
    pt, lo, hi = cluster_boot(g.author.values, g.adapter_minus_base.values, np.mean, n=2000, seed=8)
    pool_rows.append({"instrument": keys[0], "family": keys[1], "params_b": keys[2],
                      "n_authors": g.author.nunique(), "mean_gain": pt, "ci_low": lo, "ci_high": hi,
                      "n_authors_positive": int((g.adapter_minus_base > 0).sum()),
                      "n_above_floor": int(g.above_floor.sum()),
                      "replicate_floor": float(g.replicate_floor.iloc[0])})
pool_tab = pd.DataFrame(pool_rows).sort_values(["instrument", "family", "params_b"]).reset_index(drop=True)
write_table(pool_tab, os.path.join(OUTD, "attribution_gain_pooled.csv"))

# ================================================================== 3. nearest-author confusion
print("3. nearest-author confusion ...")
conf_rows = []
for col, name in ATTRIB.items():
    ncol = NEAREST[col]
    for (au, kind), g in d.groupby(["author", "kind"], observed=True):
        vc = g[ncol].value_counts()
        total = int(vc.sum())
        for target, cnt in vc.head(4).items():
            conf_rows.append({"instrument": name, "author": au, "kind": kind, "n_cells": total,
                              "nearest": target, "count": int(cnt), "share": float(cnt / total),
                              "is_self": bool(target == au)})
conf_tab = pd.DataFrame(conf_rows)
write_table(conf_tab, os.path.join(OUTD, "nearest_author_confusion.csv"))
# the single most common wrong answer per instrument
wrong = conf_tab[~conf_tab.is_self].groupby(["instrument", "nearest"], observed=True)["count"].sum().reset_index()
wrong_top = wrong.sort_values("count", ascending=False).groupby("instrument", observed=True).head(3)
write_table(wrong_top, os.path.join(OUTD, "nearest_author_top_wrong.csv"))

# the attractor: one reference author that most base runs' generations drift towards
attr_rows = []
for col, name in ATTRIB.items():
    ncol = NEAREST[col]
    for kind, g in d.groupby("kind", observed=True):
        vc = g[ncol].value_counts(normalize=True)
        off = vc[[i for i in vc.index if i not in set(g.author.unique())] or vc.index[:0]]
        attr_rows.append({"instrument": name, "kind": kind, "n_cells": len(g),
                          "self_rate": float((g[ncol] == g.author).mean()),
                          "top_target": vc.index[0], "top_target_share": float(vc.iloc[0]),
                          "top_non_study_target": off.index[0] if len(off) else "",
                          "top_non_study_share": float(off.iloc[0]) if len(off) else np.nan,
                          "n_authors_whose_top_is_this": int(sum(
                              1 for _, gg in g.groupby("author", observed=True)
                              if len(gg) and gg[ncol].value_counts().index[0] == vc.index[0]))})
attractor = pd.DataFrame(attr_rows)
write_table(attractor, os.path.join(OUTD, "nearest_author_attractor.csv"))
att_luar_base = attractor[(attractor.instrument == "LUAR") & (attractor.kind == "base")].iloc[0]
att_luar_ad = attractor[(attractor.instrument == "LUAR") & (attractor.kind == "adapter")].iloc[0]

# ================================================================== 4. copying
print("4. copying ...")
copy_rows = []
for keys, g in d.groupby(["family", "params_b", "kind"], observed=True):
    k, n = int(g.memo_flag.sum()), int(len(g))
    p, lo, hi = wilson(k, n)
    m8, m8lo, m8hi = cluster_boot(g.id.values, g.memo_8gram.values, np.mean, n=600, seed=10)
    lcs, lcslo, lcshi = cluster_boot(g.id.values, g.memo_lcs.values, np.mean, n=600, seed=12)
    copy_rows.append({"family": keys[0], "params_b": keys[1], "kind": keys[2], "n_cells": n,
                      "memo_flag_count": k, "memo_flag_rate": p, "wilson_low": lo, "wilson_high": hi,
                      "memo_8gram_mean": m8, "memo_8gram_lo": m8lo, "memo_8gram_hi": m8hi,
                      "memo_8gram_max": float(g.memo_8gram.max()),
                      "memo_lcs_mean": lcs, "memo_lcs_lo": lcslo, "memo_lcs_hi": lcshi,
                      "memo_lcs_max": float(g.memo_lcs.max())})
copy_tab = pd.DataFrame(copy_rows).sort_values(["family", "params_b", "kind"]).reset_index(drop=True)
write_table(copy_tab, os.path.join(OUTD, "copying_rates.csv"))
memo_flagged = d[d.memo_flag == 1][["run", "author", "family", "params_b", "kind", "id", "memo_8gram", "memo_lcs", "words"]]
write_table(memo_flagged, os.path.join(OUTD, "copying_flagged_cells.csv"))
n_memo = int(d.memo_flag.sum())
memo_by_kind = d.groupby("kind", observed=True).memo_flag.sum()

# ================================================================== 5. tells by configuration
print("5. tells by configuration ...")
tell_rows = []
TELL_FLOORS = {t: floor_for(cells, t) for t in TELLS}
for keys, g in d.groupby(["family", "params_b", "kind"], observed=True):
    row = {"family": keys[0], "params_b": keys[1], "kind": keys[2], "n_cells": len(g)}
    for t in TELLS:
        pt, lo, hi = cluster_boot(g.id.values, g[t].values, np.mean, n=600, seed=14)
        row[t] = pt
        row[f"{t}_lo"] = lo
        row[f"{t}_hi"] = hi
    tell_rows.append(row)
tell_tab = pd.DataFrame(tell_rows).sort_values(["family", "params_b", "kind"]).reset_index(drop=True)
write_table(tell_tab, os.path.join(OUTD, "tells_by_config.csv"))

tell_gain_rows = []
for keys, g in d.groupby(["family", "params_b", "author"], observed=True):
    for t in TELLS:
        r = paired_gain(g, t, seed=16)
        if r is None:
            continue
        fam = keys[0]
        fl = TELL_FLOORS[t][fam]
        fl_src = "own family"
        if fl != fl:
            fl, fl_src = TELL_FLOORS[t]["Qwen3"], "Qwen3 stand-in (no Ministral replicate)"
        tell_gain_rows.append({"family": fam, "params_b": keys[1], "author": keys[2], "measure": t, **r,
                               "replicate_floor": fl, "floor_source": fl_src,
                               "above_floor": bool(abs(r["adapter_minus_base"]) > fl)})
tell_gain = pd.DataFrame(tell_gain_rows)
write_table(tell_gain, os.path.join(OUTD, "tells_adapter_minus_base.csv"))
tell_pool_rows = []
for keys, g in tell_gain.groupby(["measure", "family", "params_b"], observed=True):
    pt, lo, hi = cluster_boot(g.author.values, g.adapter_minus_base.values, np.mean, n=2000, seed=18)
    tell_pool_rows.append({"measure": keys[0], "family": keys[1], "params_b": keys[2],
                           "n_authors": g.author.nunique(), "mean_gain": pt, "ci_low": lo, "ci_high": hi,
                           "n_above_floor": int(g.above_floor.sum()),
                           "replicate_floor": float(g.replicate_floor.iloc[0])})
tell_pool = pd.DataFrame(tell_pool_rows).sort_values(["measure", "family", "params_b"]).reset_index(drop=True)
write_table(tell_pool, os.path.join(OUTD, "tells_gain_pooled.csv"))

# does being attributable go with being tell-free?
link_rows = []
for col, name in ATTRIB.items():
    for t in TELLS + ["luar_cos_ref"]:
        cfg = d.groupby(["run", "family", "params_b", "kind", "author"], observed=True)[[col, t]].mean().reset_index()
        if len(cfg) < 8:
            continue
        r, p = spearmanr(cfg[col], cfg[t])
        link_rows.append({"instrument": name, "measure": t, "n_configs": len(cfg),
                          "spearman_config_level": float(r), "p": float(p)})
link_tab = pd.DataFrame(link_rows)
link_tab["q_bh"] = bh_fdr(link_tab.p.values)
write_table(link_tab, os.path.join(OUTD, "attribution_vs_tells.csv"))

# ================================================================== 6. detector-tell dissociation
print("6. detector-tell dissociation ...")
dtd_path = os.path.join(EVAL, "dtd.md")
dtd_text = open(dtd_path, encoding="utf-8").read()
dtd_rows = []
for line in dtd_text.splitlines():
    if not line.startswith("|") or line.startswith("| run") or set(line) <= set("|-: "):
        continue
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(parts) < 9:
        continue
    m = re.match(r"\[([+-][0-9.]+),\s*([+-][0-9.]+)\]", parts[8])
    dtd_rows.append({"run": parts[0], "author": parts[1], "size": parts[2], "kind": parts[3],
                     "n_gen": int(parts[4]), "auroc_detector": float(parts[5]), "auroc_tell": float(parts[6]),
                     "dtd": float(parts[7]),
                     "dtd_ci_low": float(m.group(1)) if m else np.nan,
                     "dtd_ci_high": float(m.group(2)) if m else np.nan})
dtd = pd.DataFrame(dtd_rows)
# attach the same runs' tell measures and voice measures from the master table
side = d[d.run.isin(dtd.run)].groupby("run", observed=True).agg(
    family=("family", "first"), params_b=("params_b", "first"), n_cells=("id", "size"),
    arti_w=("arti_w", "mean"), arti_hard_w=("arti_hard_w", "mean"), template_rate=("template_rate", "mean"),
    staccato_anaphora=("staccato_anaphora", "mean"), luar_cos_ref=("luar_cos_ref", "mean"),
    luar_attrib=("luar_attrib", "mean"), words=("words", "mean")).reset_index()
dtd = dtd.merge(side, on="run", how="left")
write_table(dtd, os.path.join(OUTD, "dtd_with_tells.csv"))
n_dtd_pos = int((dtd.dtd_ci_low > 0).sum())
inv_row = dtd.sort_values("auroc_tell").iloc[0]
n_tell_inverted = int((dtd.auroc_tell < 0.5).sum())
r_dtd_arti = spearmanr(dtd.auroc_tell, dtd.arti_w)[0] if dtd.arti_w.notna().sum() > 4 else np.nan
r_dtd_tmpl = spearmanr(dtd.auroc_tell, dtd.template_rate)[0] if dtd.template_rate.notna().sum() > 4 else np.nan

# ================================================================== figures
print("figures ...")
FIGS = []

fig, axes = plt.subplots(1, 4, figsize=(16, 4.2), sharey=True)
for ax, (col, name) in zip(axes, ATTRIB.items()):
    sub = attrib_tab[attrib_tab.instrument == name]
    for (fam, kind), g in sub.groupby(["family", "kind"], observed=True):
        g = g.sort_values("params_b")
        ax.errorbar(g.params_b, g.rate, yerr=[g.rate - g.brief_ci_low, g.brief_ci_high - g.rate],
                    marker="o" if fam == "Qwen3" else "s", ls="-" if kind == "base" else "--",
                    capsize=2, label=f"{fam} {kind}")
    ax.axhline(chance, color="#8c8c8c", lw=0.8, ls=":")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("parameters (B, log2)")
    ax.set_title(name, fontsize=10)
axes[0].set_ylabel(f"share of passages with the author ranked first\n(dotted = chance, {chance:.3f})")
axes[-1].legend(fontsize=7.5)
fig.suptitle("Attribution: does the instrument name the right author (arm A0, brief-cluster intervals)")
FIGS.append(("Attribution rate by configuration", savefig(fig, os.path.join(OUTD, "fig_attribution.png"))))

luar_conf = conf_tab[conf_tab.instrument == "LUAR"]
cols = sorted(luar_conf.nearest.unique())
fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.4), sharey=True)
for ax, kind in zip(axes, ["base", "adapter"]):
    piv = luar_conf[luar_conf.kind == kind].pivot_table(index="author", columns="nearest", values="share",
                                                        aggfunc="mean").reindex(columns=cols).fillna(0.0)
    im = ax.imshow(piv.values, cmap="viridis", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index, fontsize=7)
    ax.set_xlabel("LUAR nearest reference author")
    ax.set_title(kind)
axes[0].set_ylabel("target author")
fig.colorbar(im, ax=axes, label="share of passages", fraction=0.025)
fig.suptitle("Who the generations look like (LUAR, top-4 nearest per author; the diagonal is the target)")
FIGS.append(("LUAR nearest-author confusion, base and adapter",
             savefig(fig, os.path.join(OUTD, "fig_nearest_confusion.png"))))

fig, ax = plt.subplots(figsize=(7.2, 5.6))
for kind, g in dtd.groupby("kind", observed=True):
    ax.scatter(g.auroc_tell, g.auroc_detector, s=70, label=kind, marker="o" if kind == "base" else "s", zorder=3)
offsets = [(6, 6), (6, -12), (-6, 8), (6, 8), (-8, -12), (6, -6), (-10, 6), (6, 4)]
for i, r in enumerate(dtd.sort_values("auroc_tell").itertuples()):
    ax.annotate(f"{r.author} {r.kind}", (r.auroc_tell, r.auroc_detector), fontsize=7,
                xytext=offsets[i % len(offsets)], textcoords="offset points")
ax.plot([0.3, 1.02], [0.3, 1.02], color="#8c8c8c", lw=0.8, ls=":")
ax.axvline(0.5, color="k", lw=0.5)
ax.set_xlim(0.28, 1.02)
ax.set_ylim(0.70, 1.035)
ax.set_xlabel("AUROC of the winsorised tell index (source vs generation)")
ax.set_ylabel("AUROC of the Binoculars detector (source vs generation)")
ax.set_title("Detector-tell dissociation: the machine is easy to find,\nthe tells are not (points above the diagonal)")
ax.legend(fontsize=8)
FIGS.append(("Detector-tell dissociation", savefig(fig, os.path.join(OUTD, "fig_dtd.png"))))

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
for ax, t in zip(axes, ["arti_w", "template_rate"]):
    for (fam, kind), g in tell_tab.groupby(["family", "kind"], observed=True):
        g = g.sort_values("params_b")
        ax.errorbar(g.params_b, g[t], yerr=[g[t] - g[f"{t}_lo"], g[f"{t}_hi"] - g[t]],
                    marker="o" if fam == "Qwen3" else "s", ls="-" if kind == "base" else "--",
                    capsize=2, label=f"{fam} {kind}")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("parameters (B, log2)")
    ax.set_ylabel(VARIABLES[t][0] if t in VARIABLES else t)
    ax.legend(fontsize=7.5)
fig.suptitle("Constructional tells by configuration (arm A0)")
FIGS.append(("Tells by configuration", savefig(fig, os.path.join(OUTD, "fig_tells.png"))))

# ================================================================== README
print("readme ...")
luar = attrib_tab[attrib_tab.instrument == "LUAR"]
luar_b = luar[luar.kind == "base"]
luar_a = luar[luar.kind == "adapter"]
luar_b_multi = luar_b[luar_b.n_authors > 1]
luar_a_multi = luar_a[luar_a.n_authors > 1]
att_base = attractor[attractor.kind == "base"].sort_values("top_target_share", ascending=False)
best_inst = attrib_tab[attrib_tab.kind == "adapter"].groupby("instrument", observed=True).rate.mean().sort_values()
pool_luar = pool_tab[pool_tab.instrument == "LUAR"]
n_gain_pos = int((gain_tab.adapter_minus_base > 0).sum())
n_gain_rows = len(gain_tab)
n_gain_above = int(gain_tab.above_floor.sum())
worst_conf = wrong_top.iloc[0]
arti_q = tell_pool[(tell_pool.measure == "arti_w") & (tell_pool.family == "Qwen3")]
tmpl_q = tell_pool[(tell_pool.measure == "template_rate") & (tell_pool.family == "Qwen3")]

# README-only descriptors, read back off the tables written above
pool_multi = pool_tab[pool_tab.n_authors > 1]
n_pool_multi = int(len(pool_multi))
n_pool_multi_pos = int((pool_multi.mean_gain > 0).sum())
n_pool_multi_excl = int((pool_multi.ci_low > 0).sum())
n_floor_zero = int((gain_tab.replicate_floor <= 0).sum())
n_auth_min21 = int(d[d.family == "Ministral3"].author.nunique())
n_auth_qwen21 = int(d[d.family == "Qwen3"].author.nunique())
n_dtd_auth = int(dtd.author.nunique())
dtd_sizes = ", ".join(sorted(set(str(s) for s in dtd["size"])))
_cls = d.groupby("author_class", observed=True).author.nunique()
cls_txt = ", ".join(f"{int(v)} {k}" for k, v in _cls.items())
n_nonperiod = int(d[d.author_class != "period"].author.nunique())

what = f"""
Two separate questions. Can an authorship instrument put the target author first among the
{pool_min}-{pool_max} candidates scored in its own run, and does the adapter move that. Can a
machine-text detector tell the generation from the author's own prose, and does the constructional
tell index see the same thing the detector sees.

Attribution is measured four ways (LUAR, Wegmann, StyleDistance, Burrows Delta rank 1) by
family x size x kind, per author, and as a brief-paired adapter-versus-base contrast against
each measure's replicate floor. Copying is measured three ways (memorisation flag, 8-gram
overlap with the training text, longest common substring). Detection comes from the study's own
detector-tell dissociation table, re-parsed from `data/eval_results/dtd.md` and joined to the
tell index, the hard-tell index, the template rate and the LUAR numbers for the same runs.

The short answer on attribution: the adapter cell is above the base cell in
{n_pool_multi_pos} of the {n_pool_multi} pooled family x size x instrument cells that hold more
than one author, and the author-bootstrapped interval excludes zero in {n_pool_multi_excl} of
them. Excluding the single-author 1.7B cell, LUAR's author-mean rate runs
{luar_b_multi.author_mean_rate.min():.3f}-{luar_b_multi.author_mean_rate.max():.3f} on the base
and {luar_a_multi.author_mean_rate.min():.3f}-{luar_a_multi.author_mean_rate.max():.3f} on the
adapter, against a chance rate of {chance:.3f}. The Ministral cells hold {n_auth_min21} authors
each, so their intervals are wide and the direction there is a description of {n_auth_min21}
cases. The short answer on copying: {n_memo} of {len(d)} cells trip the memorisation flag, which
is an n-gram overlap check against the training text rather than a provenance test, so what it
rules out is verbatim reuse at that n-gram length.

The confusion table says which candidate the instruments pick when they are not picking the
target. Under LUAR, the single most common nearest author for a base generation is
`{att_luar_base.top_target}`
({att_luar_base.top_target_share:.3f} of base passages, and the top answer for
{int(att_luar_base.n_authors_whose_top_is_this)} of the {d.author.nunique()} target authors),
against a self-rate of {att_luar_base.self_rate:.3f}. For adapter generations the most common
answer is `{att_luar_ad.top_target}` ({att_luar_ad.top_target_share:.3f}) and the self-rate is
{att_luar_ad.self_rate:.3f}. So the adapter passages are ranked to the target more often and are
spread more evenly over the rest of the pool. Both numbers are the attribution model's own ranks
over a fixed candidate list, not a finding about who wrote the passage.

Each instrument has a different attractor, which is the reason to distrust the level rather than
the gain: on base generations the most common answer is
{', '.join(f'`{r.top_target}` for {r.instrument} ({r.top_target_share:.3f})' for r in att_base.itertuples())}.
Four instruments scoring the same passages name four different authors, which is consistent with
part of the base rate being the instrument's own prior over the reference pool rather than
anything in the passage. Every one of those attractors is a period author, and so is every
candidate in the pool.
"""

how = f"""
Data. `data/master/cells.parquet` at arm A0, non-replicate, both kinds ({len(d)} cells,
{d.author.nunique()} authors, {d.run.nunique()} runs); `data/eval_results/dtd.md` parsed as a
table ({len(dtd)} rows). `delta_top1` is derived here as `delta_rank <= 1`, matching the plan's
definition; the three `*_attrib` columns come from the scoring pass.

Unit. Rates are given three ways: a Wilson interval over cells (optimistic, since two samples of
one brief are not independent), a bootstrap over briefs, and an author-mean rate bootstrapped
over authors, which is the one to quote for any claim about a model or a family. Every
adapter-versus-base contrast is brief-paired inside one author x family x size block, then
pooled over authors with a bootstrap over authors. Cohen's d and Cliff's delta accompany each
paired contrast.

Statistics. Bootstrap intervals throughout, 800 to 2000 replicates; Spearman with BH-FDR across
the {len(link_tab)} attribution-versus-tell tests, which is the family that q is corrected within.
Each contrast is printed beside its replicate floor and the floor's origin is named in the
floor_source column. Both families now have a floor of their own; the Ministral one comes from the
two 3B replicate pairs scored on 2026-09-10 and is applied at 8B and 14B as well, and on a rate
measure a floor built from that few pairs can come out at or near zero, in which case clearing it
means nothing.

The dissociation table is taken as given, not recomputed: it reports the AUROC of a same-family
Binoculars observer and of the winsorised tell index at separating the author's own passages
from that run's generations, with a paired passage bootstrap. This script adds the tell-side
context - the mean tell index, hard-tell index and template rate for the same runs - so the
AUROC can be read against the level of the measure it was computed from.
"""

reading = f"""
Unit of replication. The pooled attribution rate is a mean over authors, and the author counts
are the constraint: {n_auth_qwen21} for Qwen3 and
{n_auth_min21} for Ministral 3, which is the whole Ministral sample. The Ministral column is
{n_auth_min21} authors, so its interval is wide by construction and its point estimate should not be
compared with the Qwen3 one as if both were estimates of the same precision. The n_authors column
in each table gives the count behind that row and it is not the same in every row. Within an
author, the cluster is the brief.

Interval width and floor. Of {n_gain_rows} author x size x instrument contrasts,
{n_gain_pos} are positive, {n_gain_above} exceed their own replicate floor and
{int(gain_tab.ci_excludes_zero.sum())} have an interval excluding zero. The floors are small
relative to these contrasts, so the floor is rarely what decides them. Read the floor column
before the comparison: {n_floor_zero} of the {n_gain_rows} contrasts are measured
against a replicate floor of zero, where clearing the floor carries no information at all.

Chance is not 0.5. Each run scores a generation against {pool_min} to {pool_max} candidates
(the target plus that run's reference authors; the largest Burrows Delta rank observed anywhere
is {max_delta_rank}, which confirms the pool size), so chance is {chance:.3f}. The base model
already sits well above it for LUAR
({luar_b.rate.min():.3f} to {luar_b.rate.max():.3f}). A base rate above chance is consistent with
the instrument picking up something the brief and the source passage share, and it is not evidence
that the bare model has the author's voice, so the number that carries the claim is the paired
gain, not the level.

What attribution does not mean. Ranking the author first among {pool_max} candidates is a
closed-set task with a small and unusual candidate list: every candidate is a period author, so
the contemporary and private targets are ranked against a list drawn from a different century
(see the caveats). It is not evidence that a passage would be attributed to the author in the open
world, it is not evidence a reader would recognise the voice, and it is the attribution model's
own ranking rather than a statement about provenance. The instruments also disagree with each
other: pooled over adapters they run from
{best_inst.iloc[0]:.3f} ({best_inst.index[0]}) to {best_inst.iloc[-1]:.3f}
({best_inst.index[-1]}), on the same passages.

What would overturn this. An open-set attribution test, or the same closed-set test with a
larger and better-matched candidate pool. If the confusions are driven by the candidate pool
rather than by style, adding authors near the target would collapse the rates; the single most
frequent wrong answer across all instruments is currently
`{worst_conf.nearest}` ({int(worst_conf['count'])} passages), which is a candidate-pool fact
as much as a style fact.

Detection. Every one of the {len(dtd)} dissociation rows has a detector AUROC above its tell
AUROC and {n_dtd_pos} of {len(dtd)} have an interval excluding zero, so on these rows a
machine-text detector separates the passages from the author's prose better than the
constructional tell index does. That is a statement about two instruments, not about how
detectable the prose would be to a person, and the dissociation table covers
{len(dtd)} runs over {n_dtd_auth} authors at one size ({dtd_sizes}) in one family, so it does not
speak to 8B, to 14B or to Ministral 3 at all. One row is worth naming:
on {inv_row.author} ({inv_row.kind}) the tell index runs backwards, AUROC
{inv_row.auroc_tell:.3f}, meaning that author's own passages carry more of the AI-typical
constructions than the model's do. A tell index that inverts on one author out of
{dtd.author.nunique()} is not a detector; it is a per-author profile, and it should be read as
distance from that author rather than as a machine-text score.
"""

caveats = [
    f"The candidate pool for attribution is {pool_min} to {pool_max} candidates per run (the target plus that run's reference authors); {n_names_seen} distinct names appear as a nearest answer across all runs, but no single run offers that many. Chance is {chance:.3f} and the task is closed-set; nothing here transfers to open-set attribution.",
    "The `*_attrib` flags and `delta_rank` were computed in the scoring pass; this script re-derives only `delta_top1` and takes the rest as given.",
    f"The detector-tell dissociation table covers {len(dtd)} runs over {n_dtd_auth} authors, all at size {dtd_sizes}, {int((dtd.kind == 'adapter').sum())} of them adapters. It is quoted, not recomputed, and it does not cover Ministral 3 or any larger size.",
    f"Memorisation is measured as n-gram overlap and a flag derived from it, not as a provenance or licensing check ({n_memo} flagged cells of {len(d)}; max 8-gram overlap {d.memo_8gram.max():.4f}). The copying tables are a null result at that n-gram length and cannot support a contrast between kinds, and they say nothing about paraphrased reuse.",
    f"The Ministral floors come from the two 3B replicate pairs scored on 2026-09-10 and are applied at 8B and 14B as well; floor_source records which family each floor came from. Because these are rate measures estimated from few pairs, {n_floor_zero} of the {n_gain_rows} contrasts sit against a floor of zero, where above_floor is true by construction.",
    f"Every attribution candidate pool is the same period stranger pool plus the target, so the {n_nonperiod} non-period targets ({cls_txt}) are ranked against candidates from a different century, and every nearest-author attractor reported here is a period author. The base rates, the attractors and the confusion table are therefore partly a fact about the pool. 23_register_matched_pool holds the register-matched comparison.",
    "The nearest-author confusion table keeps the top four nearest authors per author x kind, so the shares in it do not sum to one and the heatmap is not a complete confusion matrix.",
    "Attribution and tell measures here are arm A0 only; the eval-cache tell measures (arti_w, rfpd_w) do not exist for the other arms.",
    f"{n_tell_inverted} of the {len(dtd)} dissociation rows has a tell AUROC below 0.5 ({inv_row.author} {inv_row.kind}, {inv_row.auroc_tell:.3f}), i.e. the tell index scores that author's own prose as more AI-typical than the model's. The aggregate index should not be used as a standalone detector.",
    f"The Qwen3 1.7B cells rest on a single author (patrick_v2), so their pooled intervals are empty by construction; the tables show `n_authors = 1` rather than an interval.",
]

write_readme(
    OUTD, "21_attribution_detection: closed-set attribution and machine-text detection",
    what, how, reading, caveats,
    tables=[("Attribution rate by configuration", attrib_tab),
            ("Adapter minus base, pooled over authors", pool_tab),
            ("Most common wrong nearest author per instrument", wrong_top),
            ("Where the prose sits: the nearest-author attractor by kind", attractor),
            ("Copying", copy_tab),
            ("Constructional tells by configuration", tell_tab[["family", "params_b", "kind", "n_cells"] + TELLS]),
            ("Tell contrasts pooled over authors", tell_pool),
            ("Detector-tell dissociation with the tell levels behind it", dtd)],
    figures=FIGS)

print(f"""
=== 21_attribution_detection summary ===
A0 cells {len(d)}; authors {d.author.nunique()}; per-run candidate pool {pool_min}-{pool_max} (chance {chance:.3f}); {n_names_seen} distinct nearest names; max delta_rank {max_delta_rank}
LUAR attribution: base {luar_b.rate.min():.3f}-{luar_b.rate.max():.3f}, adapter {luar_a.rate.min():.3f}-{luar_a.rate.max():.3f}
instrument means over adapters: {', '.join(f'{k} {v:.3f}' for k, v in best_inst.items())}
adapter-minus-base contrasts: {n_gain_pos}/{n_gain_rows} positive, {n_gain_above} above floor, {int(gain_tab.ci_excludes_zero.sum())} with CI excluding zero
pooled LUAR gain by size: {'; '.join(f"{r.family} {r.params_b:g}B {r.mean_gain:+.3f} [{r.ci_low:+.3f}, {r.ci_high:+.3f}] (n={r.n_authors})" for r in pool_luar.itertuples())}
top wrong nearest per instrument: {'; '.join(f"{inst}->{g.iloc[0].nearest} ({int(g.iloc[0]['count'])})" for inst, g in wrong_top.groupby('instrument', observed=True))}
LUAR attractor: base top answer `{att_luar_base.top_target}` {att_luar_base.top_target_share:.3f} (top for {int(att_luar_base.n_authors_whose_top_is_this)}/{d.author.nunique()} authors), self-rate {att_luar_base.self_rate:.3f}; adapter self-rate {att_luar_ad.self_rate:.3f}
copying: memo_flag {n_memo}/{len(d)} cells ({dict(memo_by_kind)}), max 8gram {d.memo_8gram.max():.4f}, max lcs {int(d.memo_lcs.max())}
tells (Qwen3 pooled gain): arti_w {'; '.join(f"{r.params_b:g}B {r.mean_gain:+.3f} [{r.ci_low:+.3f}, {r.ci_high:+.3f}] floor {r.replicate_floor:.3f}" for r in arti_q.itertuples())}
              template_rate {'; '.join(f"{r.params_b:g}B {r.mean_gain:+.3f} [{r.ci_low:+.3f}, {r.ci_high:+.3f}]" for r in tmpl_q.itertuples())}
DTD: {len(dtd)} runs, detector AUROC {dtd.auroc_detector.min():.3f}-{dtd.auroc_detector.max():.3f}, tell AUROC {dtd.auroc_tell.min():.3f}-{dtd.auroc_tell.max():.3f}, DTD {dtd.dtd.min():+.3f}-{dtd.dtd.max():+.3f}, {n_dtd_pos}/{len(dtd)} intervals exclude zero
  tell AUROC vs mean arti_w rho {r_dtd_arti:+.2f}; vs template_rate rho {r_dtd_tmpl:+.2f}
outputs -> {OUTD}
""")
