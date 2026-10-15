"""22_multiple_comparisons_and_sensitivity -- how much of the programme survives one correction,
and how much of it survives having its data changed.

Three things happen here.

1. The script computes its own pooled adapter-versus-base contrast for every primary measure at
   every family x size, with the author as the unit. This never depends on another script, so
   the script runs whether or not its siblings have finished.
2. It harvests the primary contrast tables the other scripts wrote, where they exist, and
   records which were present. Pooled adapter-versus-base rows from every source are put in one
   BH-FDR family and corrected together, which is a stricter test than each script's own
   correction.
3. It recomputes the pooled contrast under five data changes -- private authors dropped,
   gate-failed runs dropped, truncated cells dropped, sample 0 alone, sample 1 alone -- and
   reports which verdicts flip. Minimum detectable effects close the file: the replicate floor
   and the width of the pooled interval per measure.

Outputs into analysis/22_multiple_comparisons_and_sensitivity/:
    inputs_present.csv        which sibling tables existed when this ran
    own_pooled_contrasts.csv  this script's own pooled adapter-vs-base contrasts
    harvested_contrasts.csv   the sibling contrasts, normalised to one schema
    programme_fdr.csv         pooled contrasts, BH-FDR across the whole programme
    programme_fdr_author.csv  the same for author-level contrasts, corrected separately
    survival_summary.csv      how many survive, by source and by measure
    sensitivity.csv           the pooled contrast under each data change
    sensitivity_flips.csv     contrasts whose verdict changes under a data change
    mde.csv                   minimum detectable effect per measure and family
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
from scipy.stats import t as tdist, wilcoxon

from lib import *  # noqa: F401,F403

T0 = time.time()
OUTD = outdir("22_multiple_comparisons_and_sensitivity")

PRIMARY = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "wegmann_cos_ref",
           "styledist_cos_source", "styledist_cos_ref", "geo_index", "open_entropy",
           "pct_short8", "otd_js", "hapax_w300", "mattr", "cr_pos", "per", "distinct_3",
           "rep_4", "coverage", "tau", "terminal_missing", "arti_w", "template_rate",
           "luar_attrib", "truncated", "len_ratio", "words"]
PRIVATE_AUTHORS = sorted(PRIVATE)

cells, runs, authors, briefs, refs = load_all()
d = main_cells(cells).copy()
for c in ("truncated", "preface", "luar_attrib"):
    d[c] = d[c].astype(float)
run_meta = runs.set_index("run")
d["gate_generation_ok"] = d.run.map(run_meta.gate_generation_ok)

# ---------------------------------------------------------------- floors
floor_rows = []
for m in PRIMARY:
    t = replicate_floor(cells, m, arm="A0")
    for fam, g in t.groupby("family", observed=True):
        floor_rows.append({"measure": m, "family": fam, "floor": float(g.abs_mean_diff.max()),
                           "n_pairs": int(g.pair.nunique()), "floor_source": "measured"})
floors = pd.DataFrame(floor_rows)
qwen_floor = floors[floors.family == "Qwen3"].set_index("measure").floor.to_dict()
for m in PRIMARY:
    for fam in sorted(d.family.unique()):
        if not ((floors.measure == m) & (floors.family == fam)).any() and m in qwen_floor:
            floors.loc[len(floors)] = [m, fam, qwen_floor[m], 0, "borrowed from Qwen3"]
FLOOR = {(r.measure, r.family): r.floor for r in floors.itertuples()}
FLOOR_SRC = {(r.measure, r.family): r.floor_source for r in floors.itertuples()}

# ---------------------------------------------------------------- paired table (built once)
key = ["author", "family", "params_b", "id", "sample"]
keep = key + PRIMARY + ["author_class", "run", "gate_generation_ok"]
pair = (d[d.kind == "base"][keep]
        .merge(d[d.kind == "adapter"][keep], on=key, suffixes=("_b", "_a")))
pair["private"] = pair.author.isin(PRIVATE)
pair["gate_ok_both"] = ~((pair.gate_generation_ok_b == False) | (pair.gate_generation_ok_a == False))  # noqa: E712
pair["either_truncated"] = (pair.truncated_b > 0) | (pair.truncated_a > 0)

VARIANTS = {
    "all cells": lambda p: p,
    "private authors dropped": lambda p: p[~p.private],
    "gate-failed runs dropped": lambda p: p[p.gate_ok_both],
    "truncated cells dropped": lambda p: p[~p.either_truncated],
    "sample 0 only": lambda p: p[p["sample"] == 0],
    "sample 1 only": lambda p: p[p["sample"] == 1],
}


def pooled_contrast(sub, m, fam, pb, variant):
    """Author-level pooled adapter-minus-base contrast for one measure x family x size."""
    cols = [f"{m}_b", f"{m}_a"]
    s = sub[["author"] + cols].dropna()
    if not len(s):
        return None
    s = s.assign(diff=s[cols[1]] - s[cols[0]])
    per_author = s.groupby("author")["diff"].mean()
    k = len(per_author)
    if k == 0:
        return None
    pt, lo, hi = bootstrap_ci(per_author.values, np.mean, n=4000, seed=23) if k > 1 else (float(per_author.iloc[0]), np.nan, np.nan)
    se = float(per_author.std(ddof=1) / np.sqrt(k)) if k > 1 else np.nan
    p = np.nan
    if k >= 5 and per_author.nunique() > 1:
        try:
            p = float(wilcoxon(per_author.values).pvalue)
        except Exception:
            p = np.nan
    floor = FLOOR.get((m, fam), np.nan)
    dirn = VARIABLES[m][3] if m in VARIABLES else "0"
    toward = pt if dirn != "-" else -pt
    return {"measure": m, "family": fam, "params_b": pb, "variant": variant, "direction": dirn,
            "n_authors": k, "n_pairs": int(len(s)), "estimate": pt, "ci_low": lo, "ci_high": hi,
            "se_authors": se, "p_wilcoxon_authors": p,
            "estimate_toward_author": toward if dirn != "0" else np.nan,
            "floor": floor, "floor_source": FLOOR_SRC.get((m, fam), "none"),
            "abs_over_floor": abs(pt) / floor if floor and floor == floor else np.nan,
            "within_noise": bool(abs(pt) < floor) if floor == floor else None,
            "ci_excludes_zero": bool(lo > 0 or hi < 0) if lo == lo else None}


rows = []
for variant, fn in VARIANTS.items():
    p_v = fn(pair)
    for (fam, pb), g in p_v.groupby(["family", "params_b"], observed=True):
        for m in PRIMARY:
            r = pooled_contrast(g, m, fam, pb, variant)
            if r:
                rows.append(r)
sens = pd.DataFrame(rows)
own = sens[sens.variant == "all cells"].drop(columns=["variant"]).copy()
own["q_own_family"] = bh_fdr(own.p_wilcoxon_authors.values)
own = own.sort_values(["measure", "family", "params_b"])
write_table(own, os.path.join(OUTD, "own_pooled_contrasts.csv"), floats=6)
write_table(sens.sort_values(["measure", "family", "params_b", "variant"]),
            os.path.join(OUTD, "sensitivity.csv"), floats=6)

# ---------------------------------------------------------------- harvest siblings
def spec(path, scope, contrast, measure=None, const_measure=None, family=None, params_b=None,
         author=None, estimate=None, ci_low="ci_low", ci_high="ci_high", p=None, q_own=None,
         floor=None, n=None, extra=None):
    return dict(path=path, scope=scope, contrast=contrast, measure=measure,
                const_measure=const_measure, family=family, params_b=params_b, author=author,
                estimate=estimate, ci_low=ci_low, ci_high=ci_high, p=p, q_own=q_own,
                floor=floor, n=n, extra=extra or [])


REGISTRY = [
    spec("11_scale_curves/gain.csv", "author", "adapter vs base", measure="measure",
         family="family", params_b="params_b", author="author", estimate="gain",
         p="p_wilcoxon_brief", q_own="q_wilcoxon", floor="floor", n="n_briefs"),
    spec("12_arm_effects/arm_contrasts_pooled.csv", "pooled", "arm vs A0 (base runs)",
         measure="measure", family="family", params_b="params_b", estimate="mean_diff",
         p="p_wilcoxon", q_own="q_bh", floor="floor_qwen", n="n_authors", extra=["arm"]),
    spec("12_arm_effects/prompt_vs_adapter_pooled.csv", "pooled", "best prompt vs adapter",
         measure="measure", family="family", params_b="params_b", estimate="base_minus_adapter",
         p="p_wilcoxon", q_own="q_bh", floor="floor_qwen", n="n_authors", extra=["arm"]),
    spec("13_corpus_data_effects/adapter_gain_by_author.csv", "author", "adapter vs base",
         measure="measure", family="family", params_b="params_b", author="author",
         estimate="gain", p="p_wilcoxon", q_own="q_bh", floor="floor_qwen", n="n_briefs"),
    spec("14_style_construction_tradeoff/author_level_tests.csv", "pooled",
         "adapter vs base (voice/construction axis)", measure="measure", family="family",
         params_b="params_b", estimate="mean_delta", p="p_wilcoxon", q_own="q_wilcoxon_bh",
         floor="floor", n="n_authors", extra=["group"]),
    spec("14_style_construction_tradeoff/paired_deltas_by_configuration.csv", "author",
         "adapter vs base (voice/construction axis)", measure="measure", family="family",
         params_b="params_b", author="author", estimate="delta", p="p_perm", q_own="q_bh",
         floor="floor", n="n_briefs"),
    spec("16_judges/coverage_adapter_minus_base.csv", "author", "adapter vs base",
         const_measure="coverage", family="family", params_b="params_b", author="author",
         estimate="adapter_minus_base", n="n_briefs"),
    spec("17_length_truncation/words_adapter_minus_base.csv", "author", "adapter vs base",
         const_measure="words", family="family", params_b="params_b", author="author",
         estimate="adapter_minus_base", n="n_briefs"),
    spec("18_cross_family/adapter_gain_paired.csv", "author", "adapter vs base",
         measure="measure", family="family", params_b="params_b", author="author",
         estimate="gain", p="p_wilcoxon", q_own="q_bh", floor="floor", n="n_briefs",
         extra=["rung_name"]),
    spec("18_cross_family/base_family_diff.csv", "author", "Qwen3 base vs Ministral3 base",
         measure="measure", author="author", estimate="base_qwen_minus_ministral",
         p="p_wilcoxon", q_own="q_bh", floor="floor_max", n="n_briefs", extra=["rung_name"]),
    spec("19_author_heterogeneity/author_effects.csv", "author", "adapter vs base",
         measure="measure", family="family", params_b="params_b", author="author",
         estimate="effect", p="p_wilcoxon", q_own="q_bh", floor="floor", n="n_briefs"),
    spec("19_author_heterogeneity/pooled_dl.csv", "pooled",
         "adapter vs base (DerSimonian-Laird)", measure="measure", family="family",
         params_b="params_b", estimate="pooled", p="p", q_own="q_bh", floor="floor",
         n="n_authors"),
    spec("20_brief_covariates/brief_predictors.csv", "pooled", "brief covariate effect",
         measure="measure", estimate="estimate", p="p", q_own="q_bh"),
    spec("21_attribution_detection/attribution_by_config.csv", "pooled",
         "attribution / detection rate", measure="measure", family="family",
         params_b="params_b", estimate="rate", n="n"),
]

present_rows, harvest_rows = [], []
for s in REGISTRY:
    full = os.path.join(OUT, s["path"].replace("/", os.sep))
    folder = s["path"].split("/")[0]
    if not os.path.exists(full):
        present_rows.append({"input": s["path"], "folder_exists": os.path.isdir(os.path.join(OUT, folder)),
                             "file_present": False, "scope": s["scope"], "contrast": s["contrast"],
                             "n_rows": 0, "n_with_p": 0, "note": "not written when this script ran"})
        continue
    try:
        t = pd.read_csv(full)
    except Exception as e:
        present_rows.append({"input": s["path"], "folder_exists": True, "file_present": True,
                             "scope": s["scope"], "contrast": s["contrast"], "n_rows": 0,
                             "n_with_p": 0, "note": f"unreadable: {type(e).__name__}"})
        continue
    out = pd.DataFrame(index=t.index)
    out["source"] = s["path"]
    out["scope"] = s["scope"]
    out["contrast"] = s["contrast"]
    out["measure"] = t[s["measure"]] if s["measure"] and s["measure"] in t.columns else s["const_measure"]
    for name in ("family", "params_b", "author"):
        col = s[name]
        out[name] = t[col] if col and col in t.columns else np.nan
    for name, col in (("estimate", s["estimate"]), ("ci_low", s["ci_low"]), ("ci_high", s["ci_high"]),
                      ("p", s["p"]), ("q_own", s["q_own"]), ("floor", s["floor"]), ("n", s["n"])):
        out[name] = pd.to_numeric(t[col], errors="coerce") if col and col in t.columns else np.nan
    out["extra"] = ""
    for col in s["extra"]:
        if col in t.columns:
            out["extra"] = out["extra"].str.cat(col + "=" + t[col].astype(str), sep=";").str.strip(";")
    out = out[out.measure.notna() & out.estimate.notna()]
    harvest_rows.append(out)
    present_rows.append({"input": s["path"], "folder_exists": True, "file_present": True,
                         "scope": s["scope"], "contrast": s["contrast"], "n_rows": int(len(out)),
                         "n_with_p": int(out.p.notna().sum()),
                         "note": "" if out.p.notna().any() else "no p-values; estimates and intervals only"})

inputs = pd.DataFrame(present_rows).sort_values("input")
write_table(inputs, os.path.join(OUTD, "inputs_present.csv"))
harvest = pd.concat(harvest_rows, ignore_index=True) if harvest_rows else pd.DataFrame(
    columns=["source", "scope", "contrast", "measure", "family", "params_b", "author",
             "estimate", "ci_low", "ci_high", "p", "q_own", "floor", "n", "extra"])
harvest["within_noise"] = np.where(harvest.floor.notna(), harvest.estimate.abs() < harvest.floor, None)
write_table(harvest, os.path.join(OUTD, "harvested_contrasts.csv"), floats=6)

# ---------------------------------------------------------------- programme-wide FDR
own_as_harvest = own.assign(
    source="22 (own, computed from cells.parquet)", scope="pooled", contrast="adapter vs base",
    author=np.nan, p=own.p_wilcoxon_authors, q_own=own.q_own_family, n=own.n_authors, extra="")[
    ["source", "scope", "contrast", "measure", "family", "params_b", "author", "estimate",
     "ci_low", "ci_high", "p", "q_own", "floor", "n", "extra", "within_noise"]]

allc = pd.concat([own_as_harvest, harvest], ignore_index=True)
allc["is_adapter_vs_base"] = allc.contrast.str.startswith("adapter vs base")


def apply_programme_fdr(df, label):
    df = df[df.p.notna()].copy()
    if not len(df):
        df["q_programme"] = np.nan
        return df
    df["q_programme"] = bh_fdr(df.p.values)
    df["fdr_family"] = label
    df["n_in_family"] = len(df)
    df["survives_own_q05"] = df.q_own < 0.05
    df["survives_programme_q05"] = df.q_programme < 0.05
    df["survives_and_above_floor"] = df.survives_programme_q05 & (df.within_noise == False)  # noqa: E712
    return df


pooled_fdr = apply_programme_fdr(allc[allc.scope == "pooled"], "programme-wide, pooled contrasts")
author_fdr = apply_programme_fdr(allc[allc.scope == "author"], "programme-wide, author-level contrasts")
avb_fdr = apply_programme_fdr(allc[(allc.scope == "pooled") & allc.is_adapter_vs_base],
                              "programme-wide, pooled adapter-vs-base only")
write_table(pooled_fdr.sort_values("q_programme"), os.path.join(OUTD, "programme_fdr.csv"), floats=6)
write_table(author_fdr.sort_values("q_programme"), os.path.join(OUTD, "programme_fdr_author.csv"), floats=6)
write_table(avb_fdr.sort_values("q_programme"), os.path.join(OUTD, "programme_fdr_adapter_vs_base.csv"), floats=6)

surv_rows = []
for label, df in (("pooled, all primary contrasts", pooled_fdr),
                  ("pooled, adapter-vs-base only", avb_fdr),
                  ("author-level", author_fdr)):
    for src, g in df.groupby("source", observed=True):
        surv_rows.append({"level": label, "source": src, "n_tests": int(len(g)),
                          "n_p_below_05": int((g.p < 0.05).sum()),
                          "n_own_q_below_05": int(g.survives_own_q05.fillna(False).sum()),
                          "n_programme_q_below_05": int(g.survives_programme_q05.sum()),
                          "n_programme_q_and_above_floor": int(g.survives_and_above_floor.fillna(False).sum()),
                          "n_no_floor": int(g.floor.isna().sum())})
survival = pd.DataFrame(surv_rows).sort_values(["level", "source"])
write_table(survival, os.path.join(OUTD, "survival_summary.csv"))

by_measure = (avb_fdr.groupby("measure", observed=True)
              .agg(n_tests=("p", "size"), n_survive=("survives_programme_q05", "sum"),
                   n_survive_above_floor=("survives_and_above_floor", "sum"),
                   min_q=("q_programme", "min"))
              .reset_index().sort_values("min_q"))
write_table(by_measure, os.path.join(OUTD, "survival_by_measure.csv"))

# ---------------------------------------------------------------- sensitivity flips
base_v = sens[sens.variant == "all cells"].set_index(["measure", "family", "params_b"])
flip_rows = []
for variant in [v for v in VARIANTS if v != "all cells"]:
    v = sens[sens.variant == variant].set_index(["measure", "family", "params_b"])
    idx = base_v.index.intersection(v.index)
    for i in idx:
        b, a = base_v.loc[i], v.loc[i]
        if isinstance(b, pd.DataFrame) or isinstance(a, pd.DataFrame):
            continue
        sign_flip = bool(np.sign(b.estimate) != np.sign(a.estimate)) and abs(a.estimate) > 0
        floor_flip = (b.within_noise is not None and a.within_noise is not None
                      and bool(b.within_noise) != bool(a.within_noise))
        ci_flip = (b.ci_excludes_zero is not None and a.ci_excludes_zero is not None
                   and bool(b.ci_excludes_zero) != bool(a.ci_excludes_zero))
        rel = abs(a.estimate - b.estimate) / abs(b.estimate) if b.estimate else np.nan
        floor = FLOOR.get((i[0], i[1]), np.nan)
        # dropping truncated cells makes the truncation rate identically zero: not a finding
        degenerate = bool(variant == "truncated cells dropped" and i[0] == "truncated")
        big_enough = bool(max(abs(b.estimate), abs(a.estimate)) > floor) if floor == floor else True
        any_flip = bool(sign_flip or floor_flip or ci_flip)
        flip_rows.append({"measure": i[0], "family": i[1], "params_b": i[2], "variant": variant,
                          "estimate_all": b.estimate, "estimate_variant": a.estimate,
                          "floor": floor, "rel_change": rel, "n_authors_all": b.n_authors,
                          "n_authors_variant": a.n_authors, "n_pairs_all": b.n_pairs,
                          "n_pairs_variant": a.n_pairs, "sign_flip": sign_flip,
                          "floor_verdict_flip": floor_flip, "ci_verdict_flip": ci_flip,
                          "any_flip": any_flip,
                          "degenerate_by_construction": degenerate,
                          "underpowered_variant": bool(a.n_authors < 3),
                          "flip_matters": bool(any_flip and big_enough and not degenerate
                                               and a.n_authors >= 3)})
flips = pd.DataFrame(flip_rows)
write_table(flips.sort_values(["variant", "measure", "family", "params_b"]),
            os.path.join(OUTD, "sensitivity_flips.csv"), floats=6)

flip_summary = (flips.groupby("variant", observed=True)
                .agg(n_contrasts=("measure", "size"), n_sign_flip=("sign_flip", "sum"),
                     n_floor_flip=("floor_verdict_flip", "sum"), n_ci_flip=("ci_verdict_flip", "sum"),
                     n_any_flip=("any_flip", "sum"),
                     n_degenerate=("degenerate_by_construction", "sum"),
                     n_underpowered=("underpowered_variant", "sum"),
                     n_flip_matters=("flip_matters", "sum"),
                     median_rel_change=("rel_change", "median"))
                .reset_index())
write_table(flip_summary, os.path.join(OUTD, "sensitivity_flip_summary.csv"))

# ---------------------------------------------------------------- minimum detectable effects
mde_rows = []
a0_base = main_cells(cells, kinds=("base",))
for m in PRIMARY:
    sd_all = float(pd.to_numeric(a0_base[m], errors="coerce").std())
    for fam in sorted(d.family.unique()):
        g = own[(own.measure == m) & (own.family == fam)]
        if not len(g):
            continue
        floor = FLOOR.get((m, fam), np.nan)
        half = float(((g.ci_high - g.ci_low) / 2).median())
        se = float(g.se_authors.median())
        k = int(g.n_authors.median())
        mde80 = np.nan
        if k > 1 and se == se:
            mde80 = float((tdist.ppf(0.975, k - 1) + tdist.ppf(0.80, k - 1)) * se)
        mde_rows.append({"measure": m, "construct": VARIABLES[m][1] if m in VARIABLES else "",
                         "family": fam, "median_n_authors": k, "sd_A0_base": sd_all,
                         "replicate_floor": floor, "floor_source": FLOOR_SRC.get((m, fam), "none"),
                         "median_ci_half_width": half, "median_se_over_authors": se,
                         "mde_80pct_power": mde80,
                         "binding_limit": max([v for v in (floor, half, mde80) if v == v], default=np.nan),
                         "binding_limit_in_sd": (max([v for v in (floor, half, mde80) if v == v], default=np.nan) / sd_all) if sd_all else np.nan})
mde = pd.DataFrame(mde_rows).sort_values(["family", "binding_limit_in_sd"], ascending=[True, False])
write_table(mde, os.path.join(OUTD, "mde.csv"), floats=6)

# ---------------------------------------------------------------- figures
figs = []
sub = avb_fdr.sort_values("p")
if len(sub):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(1, len(sub) + 1)
    ax.plot(x, sub.p.values, ".", ms=4, label="raw p")
    ax.plot(x, sub.q_own.values, ".", ms=4, label="q within the originating script")
    ax.plot(x, sub.q_programme.values, ".", ms=4, label="q across the whole programme")
    ax.axhline(0.05, color="k", ls="--", lw=0.9, label="0.05")
    ax.set_yscale("log"); ax.set_xlabel("pooled adapter-vs-base contrasts, ordered by raw p")
    ax.set_ylabel("p or q (log scale)")
    ax.set_title(f"Correcting once across the programme: {len(sub)} pooled adapter-vs-base contrasts")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    figs.append(("Raw p against within-script and programme-wide q",
                 savefig(fig, os.path.join(OUTD, "fig_fdr_survival.png"))))

sens_core = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "styledist_cos_source",
             "otd_js", "per", "coverage", "truncated", "hapax_w300"]
fig, axes = plt.subplots(3, 3, figsize=(15, 11), sharey=False)
vorder = list(VARIANTS)
for ax, m in zip(axes.ravel(), sens_core):
    sm = sens[(sens.measure == m) & (sens.family == "Qwen3")]
    for j, pb in enumerate(sorted(sm.params_b.unique())):
        g = sm[sm.params_b == pb].set_index("variant").reindex(vorder)
        ax.plot(np.arange(len(vorder)) + j * 0.08, g.estimate.values, "o-", ms=4,
                label=f"{pb:g}B", lw=1.1)
    floor = FLOOR.get((m, "Qwen3"), np.nan)
    ax.axhspan(-floor, floor, color="k", alpha=0.08)
    ax.axhline(0, color="k", lw=0.7)
    ax.set_title(m, fontsize=10)
    ax.set_ylabel("adapter - base (authors pooled)", fontsize=7)
    ax.set_xticks(np.arange(len(vorder)))
    ax.set_xticklabels(vorder, rotation=35, ha="right", fontsize=7)
    ax.grid(alpha=0.25)
axes[0, 0].legend(fontsize=7, ncol=2)
fig.suptitle("Qwen3 pooled adapter gain under each data change, with the replicate floor shaded", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.97])
figs.append(("Pooled gain under each sensitivity variant",
             savefig(fig, os.path.join(OUTD, "fig_sensitivity.png"))))

fig, ax = plt.subplots(figsize=(9, 7))
mq = mde[mde.family == "Qwen3"].dropna(subset=["binding_limit_in_sd"]).sort_values("binding_limit_in_sd")
y = np.arange(len(mq))
ax.barh(y - 0.2, (mq.replicate_floor / mq.sd_A0_base).values, height=0.38, label="replicate floor")
ax.barh(y + 0.2, (mq.mde_80pct_power / mq.sd_A0_base).values, height=0.38,
        label="effect detectable at 80% power over authors")
ax.set_yticks(y); ax.set_yticklabels(mq.measure, fontsize=8)
ax.set_xlabel("in standard deviations of the measure across A0 base cells")
ax.set_title("What the design can see: Qwen3, author as the unit")
ax.legend(fontsize=8); ax.grid(axis="x", alpha=0.3)
figs.append(("Minimum detectable effects", savefig(fig, os.path.join(OUTD, "fig_mde.png"))))

# ---------------------------------------------------------------- README
runtime = time.time() - T0
runs_over_gate = (d.groupby("run", observed=True)
                  .agg(trunc_rate=("truncated", "mean"), gate=("gate_generation_ok", "first"))
                  .reset_index())
runs_over_gate = runs_over_gate[(runs_over_gate.trunc_rate > 0.20) & runs_over_gate.gate.isna()]
n_present = int(inputs.file_present.sum()); n_expected = len(inputs)
missing = inputs[~inputs.file_present].input.tolist()
n_pooled = len(pooled_fdr)
n_pool_own = int((pooled_fdr.q_own < 0.05).sum())
n_pool_prog = int(pooled_fdr.survives_programme_q05.sum())
n_pool_floor = int(pooled_fdr.survives_and_above_floor.fillna(False).sum())
n_auth = len(author_fdr)
n_auth_prog = int(author_fdr.survives_programme_q05.sum())
n_auth_floor = int(author_fdr.survives_and_above_floor.fillna(False).sum())
n_avb = len(avb_fdr)
n_avb_own = int((avb_fdr.q_own < 0.05).sum())
n_avb_prog = int(avb_fdr.survives_programme_q05.sum())
n_avb_floor = int(avb_fdr.survives_and_above_floor.fillna(False).sum())
own_avb = own[own.p_wilcoxon_authors.notna()]
n_own_sig = int((own.q_own_family < 0.05).sum())
worst_variant = flip_summary.sort_values("n_flip_matters", ascending=False).iloc[0] if len(flip_summary) else None

# README string helpers only; no table is recomputed here.
n_own_with_p = int(own.p_wilcoxon_authors.notna().sum())
n_variants = len(VARIANTS)
n_changes = n_variants - 1
n_q_auth = int(own[own.family == "Qwen3"].n_authors.max())
n_m_auth = int(own[own.family == "Ministral3"].n_authors.max()) if (own.family == "Ministral3").any() else 0
pair_authors = sorted(pair.author.unique())
n_dup_chunk = len([a for a in pair_authors if a in ("patrick", "patrick_v2")])
n_distinct_corpora = len(pair_authors) - (n_dup_chunk - 1 if n_dup_chunk > 1 else 0)
trunc_flagged = sorted(runs[runs.truncation_gate_ok == False].run)  # noqa: E712
judge_primary = sorted(m for m in PRIMARY if m in ("coverage",))
floor_fams_measured = sorted(floors[floors.floor_source == "measured"].family.unique())
n_floor_borrowed = int((floors.floor_source != "measured").sum())
floor_pairs_txt = "; ".join(f"{f} {int(g.n_pairs.max())} replicate pairs"
                            for f, g in floors[floors.floor_source == "measured"].groupby("family", observed=True))

hl = (own[own.measure.isin(sens_core)]
      [["measure", "family", "params_b", "n_authors", "estimate", "ci_low", "ci_high",
        "floor", "abs_over_floor", "p_wilcoxon_authors", "q_own_family"]]
      .sort_values(["measure", "family", "params_b"]))

write_readme(
    OUTD,
    "22 -- One correction across the programme, and what survives changing the data",
    f"""
    This script does the arithmetic that each individual analysis cannot do for itself: it
    corrects every primary contrast in the programme once, together, and then asks whether the
    surviving contrasts still hold when the data underneath them is changed.

    It computed {len(own)} pooled adapter-versus-base contrasts of its own from
    `cells.parquet` ({len(PRIMARY)} measures over
    {own.groupby(["family", "params_b"]).ngroups} family-and-size combinations, author as the
    unit, wherever the measure exists in that cell). {n_own_with_p} of those carry a Wilcoxon
    test at all, because a test is computed only where at least five authors are available and
    their means are not all identical; {n_own_sig} of them reach q < 0.05 within this script's
    own family of {n_own_with_p} tests. The rest are estimates with an interval and no test.

    It then looked for {n_expected} sibling contrast tables and found {n_present}.
    {("Missing when it ran: " + ", ".join(missing) + ".") if missing else "All were present."}

    The headline family is the one the plan asks for: pooled adapter-versus-base contrasts per
    measure x size x family, from every source. There are {n_avb} of them carrying a p-value.
    {n_avb_own} clear q < 0.05 under their originating script's own correction; {n_avb_prog}
    still clear it once that whole family is corrected together, and {n_avb_floor} of those are
    also larger than their measure's replicate floor.

    Two wider families are corrected alongside it and reported separately. All pooled primary
    contrasts, which adds the prompting-arm contrasts: {n_pool_prog} of {n_pooled} survive,
    {n_pool_floor} above the floor. All author-level contrasts, a much larger family:
    {n_auth_prog} of {n_auth} survive, {n_auth_floor} of them above the floor.

    Under the {n_changes} data changes, the variant that moves the most verdicts is
    {"'" + str(worst_variant.variant) + "' (" + str(int(worst_variant.n_flip_matters)) + " of " + str(int(worst_variant.n_contrasts)) + " contrasts change sign or cross a verdict boundary, counting only contrasts where at least one of the two estimates clears the replicate floor and the variant still has three authors)" if worst_variant is not None else "none"}.
    """,
    f"""
    Own contrasts. Arm A0, non-replicate cells. Base and adapter cells are matched on
    (author, family, size, brief, sample); the per-brief differences are averaged within an
    author, and the author is then the observation. The pooled estimate is the mean over
    authors with a bootstrap over authors (4000 draws) and a Wilcoxon signed-rank test over the
    author means, computed only where at least five authors are available. `estimate_toward_author`
    flips the sign for measures whose dictionary direction is `-`, so that positive always means
    closer to the author; measures marked `0` in the dictionary have no such orientation and the
    column is left empty for them.

    Harvest. `inputs_present.csv` lists every sibling table this script looked for, whether it
    existed, how many rows it contributed and whether those rows carry p-values. Each table is
    mapped onto one schema (source, scope, contrast, measure, family, params_b, author,
    estimate, interval, p, the script's own q, floor, n). Two tables contribute estimates with
    no p-value at all and are carried in `harvested_contrasts.csv` but excluded from every FDR
    family. Nothing is read outside `data/` and the siblings' own csv outputs, and nothing
    outside this folder is written.

    Correction. Two layers, and every survival count in this folder names the layer it belongs
    to. The first layer is each originating script's own BH-FDR inside its own smaller family;
    that is the `q_own` column, and each script's README states its own family size. The second
    layer is this script's programme-wide BH-FDR, the `q_programme` column, run over three
    families kept apart because mixing them would let the larger ones swamp the smaller: pooled
    adapter-versus-base only ({n_avb} tests, the headline), all pooled primary contrasts
    ({n_pooled} tests) and author-level contrasts ({n_auth} tests). "Survives" without a
    qualifier in the tables below always means q_programme < 0.05 inside the family named in the
    row, which is the stricter of the two.

    Judge and adherence measures. `coverage` is scored by an LLM judge, and the rubric and 2AFC
    columns that arrive from sibling tables are judge instruments with known failure modes
    (order effects, a preference for the base model over an author's own prose). None of them is
    a measure of absolute quality here, and none of them is cross-family: Ministral3 runs carry
    no judge data anywhere in the programme, so every judged row in these families is Qwen3 only.
    The judge-derived primary measures corrected here are: {', '.join(judge_primary)}.

    Floors. `lib.replicate_floor` on arm A0, from the twice-generated base runs. Measured
    floors now exist for {', '.join(floor_fams_measured)} ({floor_pairs_txt}), and
    {n_floor_borrowed} floor rows are borrowed from another family; the `floor_source` column on
    every contrast records which. A contrast is counted in `survives_and_above_floor` only if it
    clears q < 0.05 across the programme and also exceeds its floor.

    Sensitivity. Every own contrast is recomputed {n_variants} ways: all cells; private authors
    ({", ".join(PRIVATE_AUTHORS)}) dropped; runs failing the generation gate dropped; pairs where
    either the base or the adapter passage hit the token cap dropped; sample 0 alone; sample 1
    alone. `sensitivity_flips.csv` records sign changes and crossings of the floor and zero-interval
    verdicts against the all-cells baseline.

    Minimum detectable effect. Per measure and family, `mde.csv` reports the replicate floor,
    the median half-width of the pooled interval, and the effect a paired test over authors
    would detect at 80% power given the observed between-author standard error. `binding_limit`
    is the largest of the three; anything smaller than that cannot be seen by this design,
    regardless of the p-value.

    Runtime {runtime:.0f} s.
    """,
    f"""
    Unit of replication. Every pooled row here is an average over authors, and the number of
    authors is small: {n_q_auth} at most for Qwen3 and {n_m_auth} for Ministral3. Those are rows
    of `authors.csv` rather than distinct writers. `patrick` and `patrick_v2` are the same
    private corpus under two chunkings, so a {n_q_auth}-author row rests on
    {n_distinct_corpora} independent corpora and two of its observations are not independent of
    each other; read the pooled interval as the wider of what it prints and what
    {n_distinct_corpora} corpora would give. A Wilcoxon signed-rank test over {n_m_auth} authors
    cannot reach q < 0.05 at any effect size, so a Ministral3 row that does not clear the
    threshold is a statement about the design and not about Ministral3.

    Interval width and the floor. Read `mde.csv` before reading any q. The median binding limit
    across the {len(mde[mde.family == "Qwen3"])} primary measures on Qwen3 is
    {float(mde[mde.family == "Qwen3"].binding_limit_in_sd.median()):.2f} standard deviations of
    the measure; a gain smaller than that is outside this design's reach whatever its p-value.
    On {int((mde[mde.family == "Qwen3"].replicate_floor >= mde[mde.family == "Qwen3"].mde_80pct_power).sum())}
    of the {len(mde[mde.family == "Qwen3"])} the binding limit is the replicate floor; on the
    rest it is the number of authors and the spread between them. The limit on this design is
    therefore {n_distinct_corpora} corpora rather than the machine's jitter, the number of
    briefs or the multiplicity correction, and generating more passages per author would not
    move it. Every contrast in the tables also carries `floor` and `within_noise`: a contrast
    marked within noise is inside the twice-generated replicate difference of its measure and is
    reported as such whatever its q.

    What would overturn this. The programme-wide correction is applied over the contrasts that
    happened to exist when this script ran. Adding the missing scripts adds tests to the family
    and can only make the q values larger, never smaller, so the surviving count reported here
    is an upper bound on what will survive once the programme is complete. Re-running this
    script after the remaining folders exist is the honest final number.

    What this does not show. It does not adjudicate between scripts that measured the same
    contrast differently; where two sources test the same measure at the same size, both rows
    are kept and both are counted as tests, which makes the correction more conservative rather
    than less. It says nothing about whether a surviving effect matters to a reader, and the
    sensitivity variants are re-analyses of one dataset, not replications.
    """,
    caveats=[
        f"{n_expected - n_present} of the {n_expected} expected sibling tables did not exist when this ran"
        + (f" ({', '.join(missing)}), so the programme-wide family is incomplete and every q here will rise when they are added." if missing else "."),
        f"{int(((inputs.n_with_p == 0) & inputs.file_present).sum())} harvested tables carry estimates without p-values (coverage and words adapter-minus-base) and are excluded from the FDR families while remaining in harvested_contrasts.csv.",
        "Where several scripts report the same contrast, the duplicate rows are all kept in the FDR family; that is deliberately conservative and inflates the test count relative to the number of distinct questions asked.",
        f"Ministral3 has at most {int(own[own.family == 'Ministral3'].n_authors.max()) if (own.family == 'Ministral3').any() else 0} authors, below the five-author minimum this script requires before it will compute a Wilcoxon p, so every Ministral3 row is an estimate with an interval and no test.",
        f"Ministral3 floors are measured from its own replicate pairs and are smaller than the Qwen3 floors on most measures, so the same absolute difference clears the floor more easily on Ministral3 than on Qwen3. Read `floor` and `floor_source` together with every above-floor verdict, and remember that Ministral3 rows rest on {n_m_auth} authors with no test attached.",
        f"The `sample 0 only` and `sample 1 only` variants halve the data, so their intervals are wider by construction; a verdict flip there is weaker evidence of instability than one under `truncated cells dropped`, which removed {int(pair.either_truncated.sum())} of {len(pair)} pairs.",
        f"`private authors dropped` leaves Ministral3 with two authors, so all {int(flips[(flips.variant == 'private authors dropped') & flips.underpowered_variant].shape[0])} Ministral3 rows under that variant are marked `underpowered_variant` and excluded from the flip count that matters; they are still in sensitivity_flips.csv.",
        "Dropping truncated cells makes the truncation rate identically zero, so those rows are marked `degenerate_by_construction` rather than counted as instability.",
        f"`gate-failed runs dropped` only removes the {int((runs.gate_generation_ok == False).sum())} runs explicitly marked failed. {int(runs.gate_generation_ok.isna().sum())} runs carry no gate verdict at all, and {len(runs_over_gate)} of those exceed the stated 20% truncation threshold on arm A0 (worst {float(runs_over_gate.trunc_rate.max()) * 100:.0f}%), so that variant is weaker than it sounds; `truncated cells dropped` is the more honest robustness check of the two.",
        "`coverage` is judged on sample 0 only, so its `sample 1 only` row rests on the handful of runs that scored coverage on both samples and should not be compared with the others.",
        "Coverage and 2AFC rows for a set of Qwen3 runs were error rows from the 2026-09-09 credit outage and are being rerun (LOG.md); those runs currently drop out of the coverage contrasts, which is why the coverage rows show fewer authors than the structural rows at the same size. Every coverage and judge number in these families is provisional until the rerun lands.",
        "The eval-cache and rubric columns in cells.parquet are merged on arm and carry values for arm A0 only; arms A1 to A5 are NaN. Only arm A0 is used here, and no A1-A5 effect on per, otd_js, psd, cpd, lexdiv, event order, the constructional features or any rubric subscore can be claimed from this table or any other.",
        "Proposition echo is close to permutation-invariant, so the shuffled-author floor fails its own manipulation check (script 24). `per` enters these families as a raw brief-paired difference against its replicate floor; no F value for it may be quoted from anywhere in the programme.",
        f"{len(trunc_flagged)} runs exceed the 20 per cent truncation gate on the data-derived `truncation_gate_ok` column of runs.csv and are flagged and kept, not excluded: {', '.join(trunc_flagged)}. Only the {int((runs.gate_generation_ok == False).sum())} runs with an explicit failed pod verdict are dropped by the `gate-failed runs dropped` variant.",  # noqa: E712
    ],
    tables=[
        ("Sibling inputs this script looked for", inputs[["input", "file_present", "scope", "contrast", "n_rows", "n_with_p", "note"]]),
        ("How many survive, by source", survival),
        ("How many survive, by measure (pooled adapter-vs-base only)", by_measure),
        ("Own pooled adapter-vs-base contrasts, core measures", hl),
        ("Verdict flips under each data change", flip_summary),
        ("Flips that matter: at least one estimate above the floor, three or more authors left",
         flips[flips.flip_matters][["measure", "family", "params_b", "variant", "estimate_all",
                                    "estimate_variant", "floor", "n_authors_variant",
                                    "sign_flip", "floor_verdict_flip", "ci_verdict_flip"]]),
        ("Minimum detectable effects, Qwen3",
         mde[mde.family == "Qwen3"][["measure", "median_n_authors", "replicate_floor",
                                     "median_ci_half_width", "mde_80pct_power",
                                     "binding_limit_in_sd"]]),
    ],
    figures=figs,
)

print(f"[22] wrote {len(os.listdir(OUTD))} files to {OUTD} in {runtime:.1f}s")
print(inputs[["input", "file_present", "n_rows", "n_with_p"]].to_string(index=False))
print()
print(survival.to_string(index=False))
print()
print(flip_summary.to_string(index=False))
