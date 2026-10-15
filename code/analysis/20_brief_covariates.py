"""20_brief_covariates: which briefs are hard, and are they the same briefs for every configuration.

Brief-level predictors (source_words, n_events, dialogue_share, brief_words) of adherence
(coverage, tau, terminal_missing, len_ratio), truncation and voice (luar_cos_source, otd_js),
fitted inside every configuration and pooled over authors; interactions with kind and parameter
count; mixed models with author random effects and a brief variance component, with work_key as
a variance component where an author has more than one work; and the difficulty question: rank
correlation of per-brief difficulty across every configuration of the same author.

Arm A0 only, so tau, terminal_missing and otd_js are the values actually computed for these
passages rather than the A0 copy the master build broadcasts onto the other arms.

Run:  C:\\Python314\\python.exe scripts\\20_brief_covariates.py
"""
from __future__ import annotations

import itertools
import os
import sys
import time
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from lib import (VARIABLES, load_all, bh_fdr, mixed_model, outdir, savefig, spearman_ci,
                 write_readme, write_table)

warnings.filterwarnings("ignore")

T0 = time.time()
OUTD = outdir("20_brief_covariates")

PREDICTORS = ["source_words", "n_events", "dialogue_share", "brief_words"]
OUTCOMES = {"coverage": "+", "tau": "+", "terminal_missing": "-", "len_ratio": "0",
            "truncated": "-", "luar_cos_source": "+", "otd_js": "-"}
DIFFICULTY = {"coverage": "-", "truncated": "+", "per": "+", "terminal_missing": "+"}  # sign that makes it "harder"


def sd(x):
    return abs(hash(x)) % (2 ** 31)


def boot_mean(x, n=2000, seed=0):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan, np.nan, np.nan, 0
    if len(x) == 1:
        return float(x[0]), np.nan, np.nan, 1
    rng = np.random.default_rng(seed)
    b = x[rng.integers(0, len(x), size=(n, len(x)))].mean(axis=1)
    return float(x.mean()), float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975)), int(len(x))


def zs(s):
    sd_ = s.std(ddof=0)
    return (s - s.mean()) / sd_ if sd_ and sd_ > 0 else s * 0.0


def main():
    cells, runs, authors, briefs, refs = load_all()
    cells = cells.copy()
    cells["truncated"] = cells["truncated"].astype(float)

    a0 = cells[(~cells.replicate) & (cells.arm == "A0")]
    cols = list(OUTCOMES) + ["per"] + PREDICTORS
    brief_lvl = (a0.groupby(["run", "author", "author_class", "family", "params_b", "kind", "id", "work_key"],
                            as_index=False)
                 .agg(**{c: (c, "mean") for c in cols}, n_samples=("sample", "nunique")))
    brief_lvl["log_params"] = np.log2(brief_lvl.params_b)
    write_table(brief_lvl, os.path.join(OUTD, "brief_level_cells.csv"))

    # ---------------------------------------------------------- 0. predictor description
    per_brief = (brief_lvl.groupby(["author", "id"])[PREDICTORS].first().reset_index())
    desc = per_brief[PREDICTORS].describe().T.reset_index().rename(columns={"index": "predictor"})
    pc = per_brief[PREDICTORS].corr(method="spearman").round(3).reset_index().rename(columns={"index": "predictor"})
    within = (per_brief.groupby("author")[PREDICTORS].std().mean() / per_brief[PREDICTORS].std())
    desc["within_author_sd_over_total_sd"] = desc.predictor.map(within)
    src_at_cap = float((per_brief.source_words >= 800).mean())
    write_table(desc, os.path.join(OUTD, "predictor_description.csv"))
    write_table(pc, os.path.join(OUTD, "predictor_correlations.csv"))

    # ---------------------------------------------------------- 1. per-configuration slopes
    rows = []
    for (run, au, ac, fam, pb, kind), g in brief_lvl.groupby(
            ["run", "author", "author_class", "family", "params_b", "kind"]):
        X = g[PREDICTORS].copy()
        if len(g) < 12 or X.std(ddof=0).min() == 0:
            continue
        Xz = X.apply(zs)
        A = np.column_stack([np.ones(len(g))] + [Xz[p].values for p in PREDICTORS])
        for out in OUTCOMES:
            y = g[out].values.astype(float)
            m = np.isfinite(y)
            if m.sum() < 12 or np.nanstd(y[m]) == 0:
                continue
            Am, ym = A[m], y[m]
            coef, *_ = np.linalg.lstsq(Am, ym, rcond=None)
            resid = ym - Am @ coef
            dof = len(ym) - Am.shape[1]
            if dof < 3:
                continue
            s2 = float(resid @ resid) / dof
            try:
                cov = s2 * np.linalg.inv(Am.T @ Am)
            except np.linalg.LinAlgError:
                continue
            se = np.sqrt(np.diag(cov))
            ysd = float(np.std(ym, ddof=0))
            r2 = 1 - float(resid @ resid) / float(((ym - ym.mean()) ** 2).sum()) if ym.std() > 0 else np.nan
            for i, p in enumerate(PREDICTORS, start=1):
                rows.append({"run": run, "author": au, "author_class": ac, "family": fam, "params_b": pb,
                             "kind": kind, "outcome": out, "direction": OUTCOMES[out], "predictor": p,
                             "n_briefs": int(m.sum()), "slope_raw_per_sd": float(coef[i]),
                             "slope_std": float(coef[i] / ysd) if ysd > 0 else np.nan,
                             "se_raw": float(se[i]), "model_r2": r2})
    slopes = pd.DataFrame(rows)
    write_table(slopes, os.path.join(OUTD, "slopes_by_configuration.csv"))

    # author is the unit: average an author's configurations first
    au_slopes = (slopes.groupby(["author", "author_class", "kind", "outcome", "direction", "predictor"],
                                as_index=False)
                 .agg(slope_std=("slope_std", "mean"), slope_raw_per_sd=("slope_raw_per_sd", "mean"),
                      n_configs=("run", "nunique"), n_briefs=("n_briefs", "mean")))
    write_table(au_slopes, os.path.join(OUTD, "slopes_by_author.csv"))

    prows = []
    for (kind, out, pred), g in au_slopes.groupby(["kind", "outcome", "predictor"]):
        v = g.slope_std.values
        mean, lo, hi, k = boot_mean(v, seed=sd(f"p|{kind}|{out}|{pred}"))
        raw, rlo, rhi, _ = boot_mean(g.slope_raw_per_sd.values, seed=sd(f"pr|{kind}|{out}|{pred}"))
        try:
            p = float(stats.wilcoxon(v).pvalue) if len(v) >= 3 and not np.allclose(v, 0) else np.nan
        except Exception:
            p = np.nan
        prows.append({"kind": kind, "outcome": out, "direction": OUTCOMES[out], "predictor": pred,
                      "n_authors": k, "slope_std": mean, "ci_low": lo, "ci_high": hi,
                      "slope_raw_per_sd": raw, "raw_ci_low": rlo, "raw_ci_high": rhi,
                      "p_wilcoxon": p, "n_authors_positive": int((v > 0).sum())})
    pooled = pd.DataFrame(prows)
    pooled["q_bh"] = bh_fdr(pooled.p_wilcoxon.values)
    pooled["consistent"] = (pooled.q_bh < 0.05) & ((pooled.ci_low > 0) | (pooled.ci_high < 0))
    pooled = pooled.sort_values(["outcome", "predictor", "kind"])
    write_table(pooled, os.path.join(OUTD, "slopes_pooled_over_authors.csv"))

    # by size as well
    srows = []
    au_slopes_sz = (slopes.groupby(["author", "kind", "family", "params_b", "outcome", "predictor"], as_index=False)
                    .agg(slope_std=("slope_std", "mean")))
    for (fam, pb, kind, out, pred), g in au_slopes_sz.groupby(["family", "params_b", "kind", "outcome", "predictor"]):
        mean, lo, hi, k = boot_mean(g.slope_std.values, seed=sd(f"sz|{fam}|{pb}|{kind}|{out}|{pred}"))
        srows.append({"family": fam, "params_b": pb, "kind": kind, "outcome": out, "predictor": pred,
                      "n_authors": k, "slope_std": mean, "ci_low": lo, "ci_high": hi})
    pooled_size = pd.DataFrame(srows).sort_values(["outcome", "predictor", "family", "params_b", "kind"])
    write_table(pooled_size, os.path.join(OUTD, "slopes_pooled_by_size.csv"))

    # ---------------------------------------------------------- 2. does the slope move with kind or size
    mrows = []
    for (out, pred), g in au_slopes_sz.groupby(["outcome", "predictor"]):
        d = g.dropna(subset=["slope_std"]).copy()
        d["log_params"] = np.log2(d.params_b)
        _r, tidy = mixed_model(d, "slope_std ~ C(kind) + log_params + C(family)", groups="author")
        if len(tidy):
            tidy.insert(0, "outcome", out)
            tidy.insert(1, "predictor", pred)
            mrows.append(tidy)
    slope_mod = pd.concat(mrows, ignore_index=True) if mrows else pd.DataFrame()
    if len(slope_mod):
        write_table(slope_mod, os.path.join(OUTD, "slope_moderators.csv"))
    kind_terms = slope_mod[slope_mod.term.str.startswith("C(kind)", na=False)].copy() if len(slope_mod) else pd.DataFrame()
    if len(kind_terms):
        kind_terms["q_bh"] = bh_fdr(kind_terms.p.values)
        write_table(kind_terms, os.path.join(OUTD, "slope_kind_contrast.csv"))

    # ---------------------------------------------------------- 3. cell-level mixed models
    d = brief_lvl.copy()
    for p in PREDICTORS:
        d["z_" + p] = zs(d[p])
    zterms = " + ".join("z_" + p for p in PREDICTORS)
    multi_work = [a for a, n in d.groupby("author").work_key.nunique().items() if n >= 2]
    n_multi_work = len(multi_work)
    mm = []
    for out in OUTCOMES:
        dd = d.dropna(subset=[out]).copy()
        specs = [("author RE only", f"{out} ~ {zterms}", None),
                 ("author RE + brief VC", f"{out} ~ {zterms}", {"brief": "0 + C(id)"}),
                 ("author RE + work VC", f"{out} ~ {zterms}", {"work": "0 + C(work_key)"}),
                 ("kind interaction", f"{out} ~ ({zterms}) * C(kind)", {"brief": "0 + C(id)"}),
                 ("size interaction", f"{out} ~ ({zterms}) * log_params + C(kind)", {"brief": "0 + C(id)"})]
        for lbl, formula, vc in specs:
            use = dd[dd.author.isin(multi_work)] if lbl == "author RE + work VC" else dd
            _r, tidy = mixed_model(use, formula, groups="author", vc=vc)
            if len(tidy):
                tidy.insert(0, "outcome", out)
                tidy.insert(1, "spec", lbl)
                mm.append(tidy)
    mixed = pd.concat(mm, ignore_index=True) if mm else pd.DataFrame()
    if len(mixed):
        write_table(mixed, os.path.join(OUTD, "mixed_models.csv"))
    n_mm_fail = int((mixed.term == "fit_failed").sum()) if len(mixed) else 0
    n_mm = int(mixed.groupby(["outcome", "spec"]).ngroups) if len(mixed) else 0
    n_mm_boundary = (int(mixed.groupby(["outcome", "spec"]).boundary_fit.max().sum())
                     if len(mixed) and "boundary_fit" in mixed.columns else 0)

    # how much the SE changes when the repeated brief is acknowledged
    se_cmp = []
    if len(mixed):
        for out in OUTCOMES:
            a = mixed[(mixed.outcome == out) & (mixed.spec == "author RE only")].set_index("term")
            b = mixed[(mixed.outcome == out) & (mixed.spec == "author RE + brief VC")].set_index("term")
            for p in PREDICTORS:
                t = "z_" + p
                if t in a.index and t in b.index:
                    se_cmp.append({"outcome": out, "predictor": p,
                                   "estimate_author_re": float(a.loc[t, "estimate"]),
                                   "se_author_re": float(a.loc[t, "se"]),
                                   "estimate_with_brief_vc": float(b.loc[t, "estimate"]),
                                   "se_with_brief_vc": float(b.loc[t, "se"]),
                                   "se_ratio": float(b.loc[t, "se"]) / float(a.loc[t, "se"]) if float(a.loc[t, "se"]) else np.nan})
    se_table = pd.DataFrame(se_cmp)
    if len(se_table):
        write_table(se_table, os.path.join(OUTD, "se_inflation_from_repeated_briefs.csv"))

    # ---------------------------------------------------------- 4. brief difficulty
    diff_rows = []
    for (run, au, fam, pb, kind), g in brief_lvl.groupby(["run", "author", "family", "params_b", "kind"]):
        for out, sign in DIFFICULTY.items():
            y = g[out]
            if y.notna().sum() < 8 or y.std(ddof=0) == 0:
                continue
            z = zs(y) * (1.0 if sign == "+" else -1.0)
            for i, v in zip(g.id.values, z.values):
                diff_rows.append({"run": run, "author": au, "family": fam, "params_b": pb, "kind": kind,
                                  "measure": out, "id": i, "difficulty_z": v})
    diff = pd.DataFrame(diff_rows)
    write_table(diff, os.path.join(OUTD, "brief_difficulty_z.csv"))

    # pairwise agreement of the difficulty ordering across configurations, within an author
    pair_rows = []
    for (au, meas), g in diff.groupby(["author", "measure"]):
        wide = g.pivot_table(index="id", columns="run", values="difficulty_z")
        cfgs = list(wide.columns)
        kinds = g.groupby("run").kind.first().to_dict()
        for a, b in itertools.combinations(cfgs, 2):
            j = wide[[a, b]].dropna()
            if len(j) < 8:
                continue
            r, p = stats.spearmanr(j[a], j[b])
            pair_rows.append({"author": au, "measure": meas, "run_a": a, "run_b": b,
                              "pair_kind": "base-base" if kinds[a] == kinds[b] == "base" else
                                           ("adapter-adapter" if kinds[a] == kinds[b] == "adapter" else "base-adapter"),
                              "n_briefs": int(len(j)), "spearman": float(r), "p": float(p)})
    pairs = pd.DataFrame(pair_rows)
    write_table(pairs, os.path.join(OUTD, "difficulty_agreement_pairs.csv"))

    agr_rows = []
    for (meas, pk), g in pairs.groupby(["measure", "pair_kind"]):
        per_au = g.groupby("author").spearman.mean().values
        mean, lo, hi, k = boot_mean(per_au, seed=sd(f"ag|{meas}|{pk}"))
        agr_rows.append({"measure": meas, "pair_kind": pk, "n_authors": k, "n_pairs": int(len(g)),
                         "mean_spearman": mean, "ci_low": lo, "ci_high": hi,
                         "median_pair_spearman": float(g.spearman.median())})
    agreement = pd.DataFrame(agr_rows).sort_values(["measure", "pair_kind"])
    write_table(agreement, os.path.join(OUTD, "difficulty_agreement.csv"))

    # leave-one-configuration-out: each configuration against the mean of the others
    loo_rows = []
    for (au, meas), g in diff.groupby(["author", "measure"]):
        wide = g.pivot_table(index="id", columns="run", values="difficulty_z")
        if wide.shape[1] < 3:
            continue
        for c in wide.columns:
            others = wide.drop(columns=[c]).mean(axis=1)
            j = pd.concat([wide[c].rename("this"), others.rename("rest")], axis=1).dropna()
            if len(j) < 8:
                continue
            r, _p = stats.spearmanr(j["this"], j["rest"])
            loo_rows.append({"author": au, "measure": meas, "run": c, "n_briefs": int(len(j)),
                             "spearman_vs_other_configs": float(r)})
    loo = pd.DataFrame(loo_rows)
    write_table(loo, os.path.join(OUTD, "difficulty_leave_one_config_out.csv"))
    loo_sum = []
    for meas, g in loo.groupby("measure"):
        per_au = g.groupby("author").spearman_vs_other_configs.mean().values
        mean, lo, hi, k = boot_mean(per_au, seed=sd(f"loo|{meas}"))
        loo_sum.append({"measure": meas, "n_authors": k, "n_configs": int(len(g)),
                        "mean_spearman_vs_rest": mean, "ci_low": lo, "ci_high": hi})
    loo_summary = pd.DataFrame(loo_sum)
    write_table(loo_summary, os.path.join(OUTD, "difficulty_consistency_summary.csv"))

    # the hardest briefs, and whether the covariates explain difficulty
    hard = (diff.groupby(["author", "measure", "id"], as_index=False)
            .agg(mean_difficulty_z=("difficulty_z", "mean"), n_configs=("run", "nunique")))
    hard = hard.merge(per_brief, on=["author", "id"], how="left")
    hard["rank_within_author"] = hard.groupby(["author", "measure"]).mean_difficulty_z.rank(ascending=False)
    write_table(hard.sort_values(["measure", "author", "rank_within_author"]),
                os.path.join(OUTD, "brief_difficulty_ranked.csv"))
    hardest = (hard[hard.measure == "coverage"].sort_values("mean_difficulty_z", ascending=False)
               .groupby("author").head(2).sort_values(["author", "mean_difficulty_z"], ascending=[True, False]))
    write_table(hardest, os.path.join(OUTD, "hardest_briefs_by_author.csv"))

    dcor_rows = []
    for meas in DIFFICULTY:
        sub = hard[hard.measure == meas]
        for pred in PREDICTORS:
            per_au_r = []
            for au, g in sub.groupby("author"):
                if g[pred].notna().sum() < 8 or g[pred].std(ddof=0) == 0:
                    continue
                per_au_r.append(stats.spearmanr(g[pred], g.mean_difficulty_z)[0])
            per_au_r = [v for v in per_au_r if v == v]
            mean, lo, hi, k = boot_mean(per_au_r, seed=sd(f"dc|{meas}|{pred}"))
            try:
                p = float(stats.wilcoxon(per_au_r).pvalue) if len(per_au_r) >= 3 else np.nan
            except Exception:
                p = np.nan
            dcor_rows.append({"difficulty_measure": meas, "predictor": pred, "n_authors": k,
                              "mean_within_author_spearman": mean, "ci_low": lo, "ci_high": hi, "p": p})
    dcor = pd.DataFrame(dcor_rows)
    dcor["q_bh"] = bh_fdr(dcor.p.values)
    write_table(dcor, os.path.join(OUTD, "difficulty_vs_predictors.csv"))

    # ---------------------------------------------------------- figures
    figs = []
    outs = [o for o in OUTCOMES]
    fig, axes = plt.subplots(1, len(outs), figsize=(2.15 * len(outs), 4.2), sharey=True)
    for i, out in enumerate(outs):
        ax = axes[i]
        sub = pooled[pooled.outcome == out]
        ys, lbls = [], []
        for j, pred in enumerate(PREDICTORS):
            for k, kind in enumerate(["base", "adapter"]):
                r = sub[(sub.predictor == pred) & (sub.kind == kind)]
                if not len(r):
                    continue
                r = r.iloc[0]
                y = j * 2.4 + (0.45 if kind == "adapter" else -0.45)
                ax.errorbar(r.slope_std, y, xerr=[[r.slope_std - r.ci_low], [r.ci_high - r.slope_std]],
                            fmt="o" if kind == "base" else "s", ms=4, capsize=2, lw=1.1,
                            color="tab:blue" if kind == "base" else "tab:red",
                            label=kind if i == 0 and j == 0 else None)
                ys.append(y)
                lbls.append(pred)
        ax.axvline(0, color="0.4", lw=0.8)
        ax.set_title(f"{out} ({OUTCOMES[out]})", fontsize=8)
        ax.set_xlabel("SD of outcome\nper SD of predictor", fontsize=7)
        ax.tick_params(labelsize=7)
    # the y axis is shared, so the ticks are set once at the end; setting them inside the loop
    # lets the last panel's empty label list wipe the first panel's names
    axes[0].set_yticks([j * 2.4 for j in range(len(PREDICTORS))])
    axes[0].set_yticklabels(PREDICTORS, fontsize=7)
    axes[0].set_ylim(-1.3, (len(PREDICTORS) - 1) * 2.4 + 1.3)
    h, lbl = axes[0].get_legend_handles_labels()
    fig.legend(h, lbl, loc="lower center", ncol=2, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Brief covariates as predictors, fitted inside every configuration and pooled over authors\n"
                 "(arm A0; partial standardised slopes; 95% bootstrap CI over authors)", fontsize=9)
    fig.tight_layout(rect=[0, 0.04, 1, 0.9])
    figs.append(("Brief covariate slopes", savefig(fig, os.path.join(OUTD, "brief_covariate_slopes.png"))))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ax = axes[0]
    order = list(DIFFICULTY)
    for i, pk in enumerate(["base-base", "adapter-adapter", "base-adapter"]):
        sub = agreement[agreement.pair_kind == pk].set_index("measure").reindex(order)
        x = np.arange(len(order)) + (i - 1) * 0.26
        ax.bar(x, sub.mean_spearman.values, width=0.25,
               yerr=[sub.mean_spearman.values - sub.ci_low.values, sub.ci_high.values - sub.mean_spearman.values],
               capsize=2, label=pk)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(order, fontsize=8)
    ax.set_ylabel("mean Spearman between two configurations\nof the same author", fontsize=8)
    ax.set_title("Do configurations agree about which briefs are hard?\n"
                 "(author is the unit; 95% CI over authors)", fontsize=9)
    ax.legend(fontsize=7, frameon=False)
    ax.tick_params(labelsize=8)
    ax = axes[1]
    for i, meas in enumerate(order):
        g = loo[loo.measure == meas]
        if not len(g):
            continue
        ax.scatter(np.full(len(g), i) + np.random.default_rng(3).normal(0, 0.06, len(g)),
                   g.spearman_vs_other_configs, s=10, alpha=0.55)
        s = loo_summary[loo_summary.measure == meas]
        if len(s):
            ax.errorbar([i], s.mean_spearman_vs_rest.values,
                        yerr=[s.mean_spearman_vs_rest.values - s.ci_low.values,
                              s.ci_high.values - s.mean_spearman_vs_rest.values],
                        fmt="D", ms=6, color="k", capsize=3)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(order, fontsize=8)
    ax.set_ylabel("Spearman of one configuration against\nthe mean of the author's others", fontsize=8)
    ax.set_title("Leave-one-configuration-out consistency\n(one point per configuration)", fontsize=9)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    figs.append(("Difficulty consistency", savefig(fig, os.path.join(OUTD, "difficulty_consistency.png"))))

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, (out, pred) in zip(axes, [("coverage", "n_events"), ("len_ratio", "source_words"),
                                      ("truncated", "brief_words")]):
        sub = brief_lvl.dropna(subset=[out, pred])
        for kind, c in [("base", "tab:blue"), ("adapter", "tab:red")]:
            gg = sub[sub.kind == kind]
            gg = gg.groupby("id", as_index=False).agg(**{out: (out, "mean"), pred: (pred, "first")})
            ax.scatter(gg[pred], gg[out], s=9, alpha=0.4, c=c, label=kind)
            if len(gg) > 10:
                b1, b0 = np.polyfit(gg[pred], gg[out], 1)
                xx = np.linspace(gg[pred].min(), gg[pred].max(), 20)
                ax.plot(xx, b0 + b1 * xx, c=c, lw=1.4)
        ax.set_xlabel(pred, fontsize=8)
        ax.set_ylabel(out, fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7, frameon=False)
    fig.suptitle("Three brief-level relationships, briefs averaged over the configurations of each kind (arm A0)",
                 fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    figs.append(("Brief-level relationships", savefig(fig, os.path.join(OUTD, "brief_relationships.png"))))

    # ---------------------------------------------------------- README numbers
    n_auth = int(slopes.author.nunique())
    n_cfg = int(slopes.run.nunique())
    consistent = pooled[pooled.consistent]
    top = consistent.reindex(consistent.slope_std.abs().sort_values(ascending=False).index)
    top_txt = "; ".join(
        f"{r.predictor} on {r.outcome} ({r.kind}) {r.slope_std:+.2f} SD "
        f"[{r.ci_low:+.2f}, {r.ci_high:+.2f}], {int(r.n_authors_positive)} of {int(r.n_authors)} authors "
        f"with a positive slope, q = {r.q_bh:.3f}" for _, r in top.iterrows())
    dia_cov = pooled[(pooled.outcome == "coverage") & (pooled.predictor == "dialogue_share")]
    lr_src = pooled[(pooled.outcome == "len_ratio") & (pooled.predictor == "source_words")]
    agr_best = agreement.loc[agreement.mean_spearman.idxmax()]
    agr_worst = agreement.loc[agreement.mean_spearman.idxmin()]
    n_trunc_base = int(pooled[(pooled.outcome == "truncated") & (pooled.kind == "base")].n_authors.iloc[0])
    se_med = float(se_table.se_ratio.median()) if len(se_table) else np.nan
    se_max = float(se_table.se_ratio.max()) if len(se_table) else np.nan
    agr_cov = agreement[agreement.measure == "coverage"]
    work_counts = brief_lvl.groupby("author").work_key.nunique().sort_values()
    single_work = ", ".join(work_counts[work_counts == 1].index) or "none"
    thin_work = ", ".join(f"{a} ({int(v)})" for a, v in work_counts[(work_counts > 1) & (work_counts <= 3)].items()) or "none"
    max_cfg_per_brief = int(brief_lvl.groupby(["author", "id"]).run.nunique().max())
    src_cap = float(desc.set_index("predictor").loc["source_words", "max"])
    agr_thin = agreement[agreement.n_authors < 10]
    agr_thin_txt = ", ".join(f"{r.measure} {r.pair_kind} (n = {int(r.n_authors)} authors)"
                             for r in agr_thin.itertuples()) or "none"
    n_agr_thin_negmed = int((agr_thin.median_pair_spearman < 0).sum()) if len(agr_thin) else 0
    agr_p = agreement.pivot(index="measure", columns="pair_kind", values="mean_spearman")
    n_agr_meas = int(len(agr_p))
    n_bb_top = int((agr_p["base-base"] >= agr_p.max(axis=1)).sum())
    n_ba_low = int((agr_p["base-adapter"] <= agr_p.min(axis=1)).sum())
    loo_txt = "; ".join(f"{r.measure} {r.mean_spearman_vs_rest:+.2f} [{r.ci_low:+.2f}, {r.ci_high:+.2f}] "
                        f"(n = {int(r.n_authors)} authors)" for _, r in loo_summary.iterrows())
    dcor_sig = dcor[(dcor.q_bh < 0.05)]

    key_tables = [
        ("Brief covariates pooled over authors (partial standardised slopes; author is the unit)",
         pooled[["outcome", "predictor", "kind", "n_authors", "slope_std", "ci_low", "ci_high",
                 "n_authors_positive", "q_bh", "consistent"]].head(56)),
        ("The predictors themselves", desc),
        ("How correlated the predictors are with one another (Spearman, one row per brief)", pc),
        ("Does the slope change between base and adapter? (mixed model on the per-author slopes)",
         kind_terms[["outcome", "predictor", "term", "estimate", "se", "ci_low", "ci_high", "p", "q_bh",
                     "n_groups"]].head(30) if len(kind_terms) else pd.DataFrame()),
        ("What acknowledging the repeated brief does to the standard errors", se_table),
        ("Do configurations agree about which briefs are hard?", agreement),
        ("Leave-one-configuration-out consistency", loo_summary),
        ("Does difficulty follow the brief covariates? (within-author Spearman, author is the unit)", dcor),
        ("The two hardest briefs per author on coverage",
         hardest[["author", "id", "mean_difficulty_z", "n_configs", "source_words", "n_events",
                  "dialogue_share", "brief_words"]]),
    ]

    what = f"""
    Asks what makes a brief hard: whether the length of the source passage, the number of events,
    the share of dialogue or the length of the brief itself predict how well a configuration
    covers the brief, keeps its event order, hits the target length, avoids the token cap or
    lands the author's voice; whether those relationships differ between base and adapter and
    across parameter counts; and whether the briefs that are hard for one configuration are the
    same ones that are hard for all the others.

    {len(slopes)} within-configuration regressions across {n_cfg} configurations and
    {n_auth} authors, pooled to {len(pooled)} author-level statements. {int(pooled.consistent.sum())}
    of those clear BH-FDR with an interval clear of zero.
    """

    how = f"""
    Data: `data/master/cells.parquet`, arm A0 and non-replicate cells only, averaged over the two
    samples to one row per (configuration, brief). Arm A0 matters here: tau, terminal_missing,
    otd_js and per are eval-cache measures that exist for arm A0 alone, so nothing in this folder
    can be read as an A1-A5 effect. Coverage is an LLM-judged adherence measure (share of brief
    items the judge found), scored on sample 0 only; it is a judge reading, not a count.

    Unit and model. The primary estimate is not a single regression over all cells. Each of the
    {n_cfg} configurations gets its own regression of the outcome on all four predictors, each
    predictor standardised within that configuration so an author with a narrow spread of briefs
    is not compared on a different scale to one with a wide spread. Those slopes are averaged
    within an author (so the author, not the brief and not the run, is the unit of replication)
    and pooled with a bootstrap over authors, Wilcoxon signed-rank over authors for the p-value,
    BH-FDR across the pooled table.

    This matters because each brief appears in up to {int(brief_lvl.groupby(['author', 'id']).run.nunique().max())}
    configurations of its author, so a cell-level regression treats one brief as dozens of
    independent observations. `mixed_models.csv` fits the cell-level models anyway, once with an
    author random intercept alone and once with a variance component for the brief, and
    `se_inflation_from_repeated_briefs.csv` shows the difference: acknowledging the repeated brief
    multiplies the standard errors by a median of {se_med:.1f} and up to {se_max:.1f}.

    work_key is added as a variance component for the {n_multi_work} of {int(d.author.nunique())}
    authors whose test briefs come from more than one work; {single_work} draw all their test
    briefs from a single work, so a work effect is not identified for them at all.

    Floors. The pooled estimates here are standardised slopes and rank correlations, not level
    differences, so the replicate floors in 10_inventory_integrity/replicate_floors.csv do not
    convert to them directly and none is quoted. The comparison that does apply to the difficulty
    agreement is the within-run test-retest correlation between the two samples of one
    configuration (10_inventory_integrity/test_retest.csv): two configurations cannot agree about
    brief difficulty more than one configuration agrees with itself, so read every agreement number
    below against that ceiling.

    Interactions. Two routes: a mixed model of the per-author slope on kind, log2(params) and
    family (`slope_moderators.csv`, `slope_kind_contrast.csv`), and cell-level models carrying
    the interaction terms directly (`mixed_models.csv`, specs "kind interaction" and "size
    interaction"). {n_mm_fail} of {n_mm} cell-level model fits failed outright and
    {n_mm_boundary} sit at the zero boundary for the author variance. These are supplementary:
    the per-configuration route above is the primary estimate because it keeps the author as the
    unit of replication.

    Difficulty. Within each configuration, each outcome is z-scored across that configuration's
    briefs and signed so that a higher value means a harder brief. Agreement is the Spearman
    between two configurations of the same author over their shared briefs, summarised first
    within an author and then bootstrapped over authors; the leave-one-out version correlates each
    configuration with the mean of the author's remaining configurations.
    """

    reading = f"""
    The unit is the author: {n_auth} of them, so every pooled interval here is a bootstrap over
    at most {n_auth} values and is wide. Two of those {n_auth} are patrick and patrick_v2, which are
    the same corpus chunked two ways, so the effective number of independent corpora is one lower
    than the count in n_authors. `n_authors_positive` in the pooled table says how many authors
    had a slope of the reported sign, and it is a better guide to consistency than the p-value.

    Two of the relationships are partly definitional and must not be read as findings.
    target_words equals source_words for every cell, so len_ratio is generated words divided by
    source_words and its slope on source_words ({lr_src.slope_std.mean():+.2f} standardised) is
    largely arithmetic. And source_words is capped: {src_at_cap * 100:.0f}% of briefs sit at the
    {src_cap:.0f}-word ceiling, so its upper tail is censored and any slope on it is attenuated.

    The four predictors are correlated with each other (source_words with brief_words at Spearman
    {float(pc.set_index('predictor').loc['source_words', 'brief_words']):.2f}, brief_words with
    n_events at {float(pc.set_index('predictor').loc['brief_words', 'n_events']):.2f}), so these
    are partial slopes and none of them isolates a mechanism. A brief with more events is also a
    longer brief.

    What would overturn this. The pooled slopes average an author's configurations before
    pooling, which hides any configuration where the relationship reverses;
    `slopes_by_configuration.csv` is the unaggregated version. If the difficulty agreement is
    driven by a handful of degenerate briefs (a brief every configuration truncates, say), the
    rank correlations would stay high while meaning much less; `brief_difficulty_ranked.csv` lists
    every brief's mean difficulty so that can be checked.

    What this does not show. It says nothing about which briefs a reader would find hard: every
    outcome here is either an automatic measure or an LLM judge's count of brief items, and the
    judge is a relative instrument with its own failure modes. It says nothing about arms other
    than A0, and nothing about the eval-cache measures on any other arm, because they do not exist
    there. And a consistent difficulty ordering is not evidence that the brief caused the
    difficulty: briefs from the same work share a source text, and work_key is only separable for
    {n_multi_work} of the {int(d.author.nunique())} authors.
    """

    caveats = [
        "target_words equals source_words exactly in every cell, so len_ratio regressed on "
        "source_words is close to an identity and is reported for completeness only.",
        f"source_words is censored at {src_cap:.0f} words for {src_at_cap * 100:.0f}% of briefs.",
        "The four predictors are mutually correlated; the slopes are partial and do not separate "
        "length from event count.",
        f"Every brief appears in up to {max_cfg_per_brief} configurations of its author. The pooled estimates "
        "handle this by making the author the unit; the cell-level mixed models are reported with and "
        "without a brief variance component precisely because the naive version understates the "
        "standard errors.",
        f"work_key is not identified for {single_work} (one work each) and is thin for {thin_work}; "
        f"the work variance component uses the {n_multi_work} authors with more than one work.",
        "truncated and terminal_missing are rates in {0, 0.5, 1} at the brief level; the regressions on "
        "them are linear probability models, not logistic.",
        "coverage exists on sample 0 only and is missing for several adapter runs, so its configuration "
        "count is lower than the other outcomes'. Ten runs' coverage rows were error rows from the "
        "2026-09-09 credit outage and are being regenerated; a missing coverage cell is a judge call "
        "that never returned, not a run that covered nothing, and the coverage slopes will move when "
        "that rerun lands.",
        f"Base truncation has no variance at all in most base configurations (the 8B and 14B base runs "
        f"almost never hit the cap), so the truncated-on-base rows rest on {n_trunc_base} authors rather "
        f"than {n_auth}; configurations with a constant outcome are dropped before fitting rather than "
        "contributing a zero slope.",
        f"The difficulty-agreement cells do not all rest on the same number of authors: {len(agr_thin)} of "
        f"{len(agreement)} are bootstrapped over fewer than ten authors ({agr_thin_txt}). On "
        f"{n_agr_thin_negmed} of those the median_pair_spearman column in the same table is negative "
        "while the author mean is positive, so the mean is carried by a minority of pairs.",
        "per (proposition echo) is close to permutation-invariant, so as a difficulty measure it "
        "registers restatement between sentences and not the order the sentences arrive in.",
        "Difficulty is defined per configuration by z-scoring within that configuration, which removes "
        "every level difference between configurations by construction; this analysis is about the "
        "ordering of briefs, never about which configuration is better.",
    ]

    extra = f"""
### Headline numbers

- The brief covariates predict the adherence and length outcomes and not the voice ones.
  {int(pooled.consistent.sum())} of {len(pooled)} pooled outcome x predictor x kind slopes clear
  BH-FDR inside this table's family of {len(pooled)} tests with an interval clear of zero, and all
  of them sit in the adherence and length outcomes:
  {', '.join(sorted(consistent.outcome.unique()))}. Each rests on at most {n_auth} authors.
- Ranked by size, the ones that survive are: {top_txt}.
- Dialogue share is the only predictor whose coverage slope clears correction under both
  mechanisms, at almost the same size: {dia_cov[dia_cov.kind == 'base'].slope_std.iloc[0]:+.2f} SD of coverage per SD of
  dialogue share on base runs
  [{dia_cov[dia_cov.kind == 'base'].ci_low.iloc[0]:+.2f}, {dia_cov[dia_cov.kind == 'base'].ci_high.iloc[0]:+.2f}]
  and {dia_cov[dia_cov.kind == 'adapter'].slope_std.iloc[0]:+.2f}
  [{dia_cov[dia_cov.kind == 'adapter'].ci_low.iloc[0]:+.2f}, {dia_cov[dia_cov.kind == 'adapter'].ci_high.iloc[0]:+.2f}]
  on adapter runs, with only
  {int(dia_cov[dia_cov.kind == 'base'].n_authors_positive.iloc[0])} and
  {int(dia_cov[dia_cov.kind == 'adapter'].n_authors_positive.iloc[0])} of
  {int(dia_cov[dia_cov.kind == 'base'].n_authors.iloc[0])} authors going the
  other way. This is consistent with dialogue-heavy briefs scoring lower on the judged coverage
  measure whether or not the model has been fine-tuned on the author. Coverage is an LLM judge's
  reading, the predictors were not assigned, and the slope is partial, so it does not establish
  what the model does with dialogue.
- The brief covariates carry little of the voice measures. The pooled standardised slopes on
  luar_cos_source run from {pooled[pooled.outcome == 'luar_cos_source'].slope_std.min():+.3f} to
  {pooled[pooled.outcome == 'luar_cos_source'].slope_std.max():+.3f} and on otd_js from
  {pooled[pooled.outcome == 'otd_js'].slope_std.min():+.3f} to
  {pooled[pooled.outcome == 'otd_js'].slope_std.max():+.3f}, none of them consistent across
  authors.
- Configurations agree about which briefs are hard, but only weakly, and the agreement varies
  more across measures than across pair kinds. Across the four difficulty measures the
  mean within-author Spearman between two configurations runs from
  {agr_worst.mean_spearman:+.2f} [{agr_worst.ci_low:+.2f}, {agr_worst.ci_high:+.2f}]
  ({agr_worst.measure}, {agr_worst.pair_kind}) to
  {agr_best.mean_spearman:+.2f} [{agr_best.ci_low:+.2f}, {agr_best.ci_high:+.2f}]
  ({agr_best.measure}, {agr_best.pair_kind}). Every one of the {len(agreement)} agreement cells is
  positive with an interval clear of zero, so the ordering of briefs is not noise, but at these
  correlations most of what makes a passage hard is not the brief. Read them against the
  within-run test-retest correlation in 10_inventory_integrity/test_retest.csv, and note that
  {len(agr_thin)} of the {len(agreement)} cells rest on fewer than ten authors.
- Two runs of the same kind agree about difficulty more than a base run and an adapter run do.
  base-base is the highest of the three pair kinds on {n_bb_top} of the {n_agr_meas} difficulty
  measures and base-adapter is the lowest on {n_ba_low}. On coverage difficulty:
  {', '.join(f"{r.pair_kind} {r.mean_spearman:+.2f} [{r.ci_low:+.2f}, {r.ci_high:+.2f}]" for _, r in agr_cov.iterrows())}.
  Part of the shared ordering therefore belongs to the mechanism and not only to the brief.
  Leave-one-configuration-out: {loo_txt}.
- Difficulty is only weakly explained by the covariates that are supposed to describe it:
  {len(dcor_sig)} of {len(dcor)} within-author difficulty-covariate correlations clear BH-FDR
  {'(' + '; '.join(f"{r.difficulty_measure} vs {r.predictor} {r.mean_within_author_spearman:+.2f} [{r.ci_low:+.2f}, {r.ci_high:+.2f}]" for _, r in dcor_sig.iterrows()) + ')' if len(dcor_sig) else ''}.
- Ignoring that briefs repeat across configurations would shrink the standard errors by a median
  factor of {se_med:.1f} (up to {se_max:.1f}). A cell-level p-value computed without a brief term
  in this folder is optimistic by about that much.
"""

    write_readme(OUTD, "20 Brief covariates: what makes a brief hard, and for whom",
                 what, how, reading, caveats, key_tables, figs, extra)

    print(f"configurations {n_cfg}, authors {n_auth}, slopes {len(slopes)}, pooled {len(pooled)}, "
          f"consistent {int(pooled.consistent.sum())}")
    print(f"difficulty pairs {len(pairs)}, loo rows {len(loo)}")
    print(f"runtime {time.time() - T0:.1f}s -> {OUTD}")


if __name__ == "__main__":
    main()
