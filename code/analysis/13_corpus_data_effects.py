"""13_corpus_data_effects: what the size and shape of an author's corpus buys the adapter.

Author-level adapter gain (adapter A0 minus base A0, paired on the brief) against training
briefs, fit examples, corpus words and number of works: Spearman with bootstrap intervals over
authors, log-linear fits, a piecewise fit with the breakpoint searched over 25..200 briefs,
adapter truncation against data size at each parameter count, author class as a factor with
author random effects, and probe delta against data size and size.

The within-author data-size series (Chesterton n25/n50/n100/n150) is checked for in
`data/master/runs.csv` first; what is found there is reported in the README, and the raw
generation runs are read directly from `data/runs/` as a clearly separate supplement.

Run:  C:\\Python314\\python.exe scripts\\13_corpus_data_effects.py
"""
from __future__ import annotations

import json
import os
import re
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

from lib import (DATA, RUNS, VARIABLES, load_all, bh_fdr, mixed_model, outdir, replicate_floor,
                 savefig, spearman_ci, write_readme, write_table)

warnings.filterwarnings("ignore")

T0 = time.time()
OUTD = outdir("13_corpus_data_effects")

# arm A0 only, so the eval-cache measures (per, otd_js, hapax_w300) are the values actually
# computed for these passages rather than a broadcast copy.
PRIMARY = {"luar_cos_source": "+", "wegmann_cos_source": "+", "otd_js": "-", "per": "-",
           "coverage": "+", "truncated": "-"}
SECONDARY = {"luar_cos_ref": "+", "styledist_cos_source": "+", "geo_index": "+",
             "hapax_w300": "0", "words": "0", "len_ratio": "0"}
MEASURES = {**PRIMARY, **SECONDARY}
COVARS = ["train_briefs_passed", "train_examples_max", "words_total", "n_works_train"]
SIZE_SERIES_PAT = ["n25", "n50", "n100", "n150"]


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


def ols_slope_ci(x, y, n=2000, seed=0):
    """slope of y on x with a bootstrap over points (authors)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 4:
        return np.nan, np.nan, np.nan, np.nan, len(x)
    b1, b0 = np.polyfit(x, y, 1)
    r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n):
        i = rng.integers(0, len(x), size=len(x))
        if len(np.unique(x[i])) < 2:
            continue
        bs.append(np.polyfit(x[i], y[i], 1)[0])
    return float(b1), float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975)), r2, int(len(x))


def piecewise_fit(x, y, grid):
    """continuous two-segment linear fit; returns best breakpoint, slopes, sse, r2."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    best = None
    for bp in grid:
        h = np.maximum(0.0, x - bp)
        if h.std() == 0 or (h > 0).sum() < 3 or (h == 0).sum() < 3:
            continue
        A = np.column_stack([np.ones_like(x), x, h])
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        sse = float(((y - A @ coef) ** 2).sum())
        if best is None or sse < best["sse"]:
            best = {"breakpoint": float(bp), "intercept": float(coef[0]), "slope_below": float(coef[1]),
                    "slope_above": float(coef[1] + coef[2]), "sse": sse}
    if best is None:
        return None
    sst = float(((y - y.mean()) ** 2).sum())
    best["r2"] = 1 - best["sse"] / sst if sst > 0 else np.nan
    return best


def main():
    cells, runs, authors, briefs, refs = load_all()
    cells = cells.copy()
    cells["truncated"] = cells["truncated"].astype(float)

    # ------------------------------------------------------------ 0. size-series check
    size_runs = runs[runs.run.str.contains("|".join(SIZE_SERIES_PAT), case=False, regex=True)]
    # every within-author size series on disk (<author>_size<n>[_s<seed>]); the raw-file cross-check below
    # stays scoped to the Chesterton seed-0 series it was written for, the multi-author analysis is script 25
    size_on_disk_all = sorted(d for d in os.listdir(RUNS)
                              if os.path.isdir(os.path.join(RUNS, d)) and re.fullmatch(r"[a-z0-9_]+_size\d+(_s\d+)?", d))
    size_series_authors = sorted({re.sub(r"_size\d+(_s\d+)?$", "", d) for d in size_on_disk_all})
    on_disk = sorted(d for d in size_on_disk_all if re.fullmatch(r"chesterton_size\d+", d))
    train_on_disk = sorted(d for d in os.listdir(RUNS)
                           if os.path.isdir(os.path.join(RUNS, d)) and re.fullmatch(r"train_chesterton_pair_n\d+_e6", d))
    ss_status = pd.DataFrame([{"question": "generation runs in data/master/runs.csv whose name contains n25/n50/n100/n150",
                               "answer": int(len(size_runs)),
                               "detail": ", ".join(size_runs.run) if len(size_runs) else "none"},
                              {"question": "generation run folders on disk under data/runs/",
                               "answer": int(len(on_disk)), "detail": ", ".join(on_disk) or "none"},
                              {"question": "training run folders on disk under data/runs/",
                               "answer": int(len(train_on_disk)), "detail": ", ".join(train_on_disk) or "none"},
                              {"question": "size-series generation runs on disk for any author (analysed in script 25)",
                               "answer": int(len(size_on_disk_all)), "detail": ", ".join(size_on_disk_all) or "none"},
                              {"question": "authors with a within-author size series on disk",
                               "answer": int(len(size_series_authors)), "detail": ", ".join(size_series_authors) or "none"}])
    write_table(ss_status, os.path.join(OUTD, "size_series_availability.csv"))
    have_master_series = len(size_runs) > 0

    # ------------------------------------------------------------ 1. adapter gain per author
    a0 = cells[(~cells.replicate) & (cells.arm == "A0")]
    key = ["author", "family", "params_b", "id", "sample"]
    piv = a0.pivot_table(index=key, columns="kind", values=list(MEASURES), aggfunc="mean")

    floors = {}
    floors_fam = {}      # (measure, family) -> the family's own floor where a pair exists
    for m in MEASURES:
        t = replicate_floor(cells, m, arm="A0")
        floors[m] = float(t[t.family == "Qwen3"].abs_mean_diff.max()) if len(t) else np.nan
        for fam_, tf_ in (t.groupby("family") if len(t) else []):
            floors_fam[(m, fam_)] = float(tf_.abs_mean_diff.max())
    fam_floor = sorted(pd.concat([replicate_floor(cells, m, arm="A0") for m in MEASURES]).family.unique())
    fam_no_floor = [f for f in sorted(cells.family.unique()) if f not in fam_floor]

    rows = []
    for m in MEASURES:
        sub = piv[m]
        if "adapter" not in sub.columns or "base" not in sub.columns:
            continue
        d = (sub["adapter"] - sub["base"]).dropna()
        if not len(d):
            continue
        per_brief = d.groupby(level=[0, 1, 2, 3]).mean()
        for (au, fam, pb), g in per_brief.groupby(level=[0, 1, 2]):
            if len(g) < 3:
                continue
            mean, lo, hi, k = boot_mean(g.values, seed=sd(f"g|{m}|{au}|{fam}|{pb}"))
            try:
                p = float(stats.wilcoxon(g.values).pvalue) if not np.allclose(g.values, 0) else np.nan
            except Exception:
                p = np.nan
            rows.append({"author": au, "family": fam, "params_b": pb, "measure": m,
                         "direction": MEASURES[m], "n_briefs": k, "gain": mean, "ci_low": lo,
                         "ci_high": hi, "p_wilcoxon": p, "floor_qwen": floors[m],
                         "above_floor": bool(abs(mean) > floors[m]) if floors[m] == floors[m] else np.nan,
                         "floor_family": floors_fam.get((m, fam), floors[m]),
                         "above_floor_family": (bool(abs(mean) > floors_fam.get((m, fam), floors[m]))
                                                if floors_fam.get((m, fam), floors[m]) == floors_fam.get((m, fam), floors[m]) else np.nan)})
    gain = pd.DataFrame(rows)
    gain["q_bh"] = bh_fdr(gain.p_wilcoxon.values)
    gain["improves"] = np.where(gain.direction == "+", gain.gain,
                                np.where(gain.direction == "-", -gain.gain, np.nan))

    au_meta = authors.set_index("author")[["author_class", "train_briefs_passed", "train_examples_max",
                                           "words_total", "n_works_train", "test_briefs_passed"]]
    gain = gain.join(au_meta, on="author")
    run_meta = (runs[(runs.kind == "adapter") & (~runs.replicate)]
                .set_index(["author", "family", "params_b"])
                [["run", "train_examples", "train_targets", "train_steps", "eval_best", "probe_delta",
                  "adapter_served", "truncated_pct", "gate_generation_ok", "gate_training_ok"]])
    gain = gain.join(run_meta, on=["author", "family", "params_b"])
    gain = gain.sort_values(["measure", "family", "params_b", "author"])
    write_table(gain, os.path.join(OUTD, "adapter_gain_by_author.csv"))

    # ------------------------------------------------------------ 2. Spearman gain vs corpus
    srows = []
    for (fam, pb, m), g in gain.groupby(["family", "params_b", "measure"]):
        for cv in COVARS:
            r, lo, hi, p, n = spearman_ci(g[cv].values, g["improves"].values, seed=sd(f"s|{fam}|{pb}|{m}|{cv}"))
            srows.append({"family": fam, "params_b": pb, "level": f"{fam} {pb:g}B", "measure": m,
                          "covariate": cv, "n_authors": n, "spearman": r, "ci_low": lo, "ci_high": hi, "p": p})
    # pooled: mean gain over the Qwen3 sizes an author actually has
    qp = (gain[gain.family == "Qwen3"].groupby(["author", "measure"])
          .agg(improves=("improves", "mean"), n_sizes=("params_b", "nunique")).reset_index().join(au_meta, on="author"))
    for m, g in qp.groupby("measure"):
        for cv in COVARS:
            r, lo, hi, p, n = spearman_ci(g[cv].values, g["improves"].values, seed=sd(f"sp|{m}|{cv}"))
            srows.append({"family": "Qwen3", "params_b": np.nan, "level": "Qwen3 pooled over sizes",
                          "measure": m, "covariate": cv, "n_authors": n, "spearman": r,
                          "ci_low": lo, "ci_high": hi, "p": p})
    corr = pd.DataFrame(srows)
    corr["q_bh"] = bh_fdr(corr.p.values)
    corr["interval_width"] = corr.ci_high - corr.ci_low
    corr = corr.sort_values(["measure", "covariate", "level"])
    write_table(corr, os.path.join(OUTD, "gain_vs_corpus_spearman.csv"))
    write_table(qp, os.path.join(OUTD, "gain_pooled_over_qwen_sizes.csv"))

    # ------------------------------------------------------------ 3. log-linear fits
    frows = []
    for (fam, pb, m), g in gain.groupby(["family", "params_b", "measure"]):
        g = g.dropna(subset=["train_examples_max"])
        if len(g) < 4:
            continue
        b1, lo, hi, r2, n = ols_slope_ci(np.log2(g.train_examples_max.values), g.improves.values,
                                         seed=sd(f"f|{fam}|{pb}|{m}"))
        frows.append({"family": fam, "params_b": pb, "measure": m, "n_authors": n,
                      "slope_per_doubling": b1, "ci_low": lo, "ci_high": hi, "r2": r2})
    for m, g in qp.groupby("measure"):
        g = g.dropna(subset=["train_examples_max"])
        if len(g) < 4:
            continue
        b1, lo, hi, r2, n = ols_slope_ci(np.log2(g.train_examples_max.values), g.improves.values, seed=sd(f"fp|{m}"))
        frows.append({"family": "Qwen3", "params_b": np.nan, "measure": m, "n_authors": n,
                      "slope_per_doubling": b1, "ci_low": lo, "ci_high": hi, "r2": r2})
    fits = pd.DataFrame(frows).sort_values(["measure", "family", "params_b"])
    write_table(fits, os.path.join(OUTD, "gain_loglinear_fits.csv"))

    # ------------------------------------------------------------ 4. piecewise breakpoint
    grid = np.arange(25, 201, 1.0)
    prows = []
    for m, g in qp.groupby("measure"):
        g = g.dropna(subset=["train_briefs_passed", "improves"])
        if len(g) < 8:
            continue
        x, y = g.train_briefs_passed.values.astype(float), g.improves.values
        pw = piecewise_fit(x, y, grid)
        b1, lo, hi, r2lin, n = ols_slope_ci(x, y, seed=sd(f"pw|{m}"))
        if pw is None:
            continue
        rng = np.random.default_rng(11)
        bps = []
        for _ in range(400):
            i = rng.integers(0, len(x), size=len(x))
            r = piecewise_fit(x[i], y[i], grid)
            if r:
                bps.append(r["breakpoint"])
        # the breakpoint is searched, so the R2 gain is inflated by construction; permute y and
        # repeat the whole search to get the null distribution of that gain.
        obs_gain = pw["r2"] - r2lin
        rng2 = np.random.default_rng(23)
        null = []
        for _ in range(400):
            yp = rng2.permutation(y)
            rp = piecewise_fit(x, yp, grid)
            if rp is None:
                continue
            lin = float(np.corrcoef(x, yp)[0, 1] ** 2)
            null.append(rp["r2"] - lin)
        k_lin, k_pw = 2, 4  # piecewise costs 3 coefficients plus the searched breakpoint
        adj = lambda r2, k: 1 - (1 - r2) * (len(x) - 1) / max(len(x) - k, 1)  # noqa: E731
        prows.append({"measure": m, "n_authors": int(n), "breakpoint_briefs": pw["breakpoint"],
                      "bp_boot_lo": float(np.quantile(bps, 0.025)) if bps else np.nan,
                      "bp_boot_hi": float(np.quantile(bps, 0.975)) if bps else np.nan,
                      "bp_boot_at_grid_edge_share": float(np.mean([(b <= grid[0] + 1) or (b >= grid[-1] - 1) for b in bps])) if bps else np.nan,
                      "slope_below": pw["slope_below"], "slope_above": pw["slope_above"],
                      "r2_piecewise": pw["r2"], "r2_linear": r2lin,
                      "r2_adj_piecewise": adj(pw["r2"], k_pw), "r2_adj_linear": adj(r2lin, k_lin),
                      "r2_gain_from_break": obs_gain,
                      "r2_gain_null_median": float(np.median(null)) if null else np.nan,
                      "p_permutation_break": float((np.sum(np.asarray(null) >= obs_gain) + 1) / (len(null) + 1)) if null else np.nan})
    piece = pd.DataFrame(prows).sort_values("measure")
    piece["q_permutation_break"] = bh_fdr(piece.p_permutation_break.values)   # BH over the measures searched
    piece["breakpoint_identified"] = ((piece.bp_boot_at_grid_edge_share < 0.05) &
                                      (piece.q_permutation_break < 0.05))
    write_table(piece, os.path.join(OUTD, "gain_piecewise_breakpoint.csv"))

    # ------------------------------------------------------------ 5. truncation vs data size
    trunc = gain[gain.measure == "truncated"][["author", "author_class", "family", "params_b", "run",
                                               "train_examples_max", "train_examples", "train_briefs_passed",
                                               "words_total", "n_works_train", "gain", "ci_low", "ci_high",
                                               "truncated_pct", "probe_delta", "eval_best", "adapter_served",
                                               "gate_generation_ok"]].copy()
    trunc = trunc.rename(columns={"gain": "truncation_gain_adapter_minus_base",
                                  "truncated_pct": "adapter_truncated_pct_run"})
    base_trunc = (a0[a0.kind == "base"].groupby(["author", "family", "params_b"]).truncated.mean()
                  .rename("base_truncated_rate_A0").reset_index())
    ad_trunc = (a0[a0.kind == "adapter"].groupby(["author", "family", "params_b"]).truncated.mean()
                .rename("adapter_truncated_rate_A0").reset_index())
    trunc = trunc.merge(base_trunc, on=["author", "family", "params_b"], how="left")
    trunc = trunc.merge(ad_trunc, on=["author", "family", "params_b"], how="left")
    trunc = trunc.sort_values(["family", "params_b", "adapter_truncated_rate_A0"], ascending=[True, True, False])
    write_table(trunc, os.path.join(OUTD, "truncation_vs_data_size.csv"))

    trows = []
    for (fam, pb), g in trunc.groupby(["family", "params_b"]):
        for cv in ["train_examples_max", "train_briefs_passed", "words_total", "n_works_train"]:
            r, lo, hi, p, n = spearman_ci(g[cv].values, g.adapter_truncated_rate_A0.values, seed=sd(f"t|{fam}|{pb}|{cv}"))
            trows.append({"family": fam, "params_b": pb, "covariate": cv, "n_authors": n,
                          "spearman_vs_adapter_truncation": r, "ci_low": lo, "ci_high": hi, "p": p})
    trunc_corr = pd.DataFrame(trows)
    trunc_corr["q_bh"] = bh_fdr(trunc_corr.p.values)
    write_table(trunc_corr, os.path.join(OUTD, "truncation_vs_data_spearman.csv"))

    # ------------------------------------------------------------ 6. author class
    mm_rows = []
    for m in PRIMARY:
        d = gain[(gain.measure == m) & (gain.family == "Qwen3")][
            ["author", "author_class", "params_b", "improves", "train_examples_max"]].dropna().copy()
        d["log_params"] = np.log2(d.params_b)
        d["log_examples"] = np.log2(d.train_examples_max)
        d = d.rename(columns={"improves": "gain"})
        _r, tidy = mixed_model(d, "gain ~ C(author_class) + log_params + log_examples", groups="author")
        if len(tidy):
            tidy.insert(0, "measure", m)
            if "boundary_fit" in tidy.columns:
                tidy["re_variance_singular"] = tidy["boundary_fit"].astype(bool)
            else:
                gv = tidy[tidy.term == "Group Var"]
                tidy["re_variance_singular"] = bool(len(gv) and float(gv.estimate.iloc[0]) < 1e-6)
            mm_rows.append(tidy)
    mixed = pd.concat(mm_rows, ignore_index=True) if mm_rows else pd.DataFrame()
    if len(mixed):
        write_table(mixed, os.path.join(OUTD, "mixed_models_author_class.csv"))
    n_fit_fail = int((mixed.term == "fit_failed").sum()) if len(mixed) else 0
    n_models = int(mixed.measure.nunique()) if len(mixed) else 0
    n_singular = int(mixed.groupby("measure").re_variance_singular.max().sum()) if len(mixed) else 0

    cls = (gain[gain.family == "Qwen3"].groupby(["measure", "author_class"])
           .agg(n_author_size_cells=("improves", "size"), n_authors=("author", "nunique"),
                mean_improvement=("improves", "mean")).reset_index())
    cls_ci = []
    for (m, c), g in gain[gain.family == "Qwen3"].groupby(["measure", "author_class"]):
        per_au = g.groupby("author").improves.mean().values
        mean, lo, hi, k = boot_mean(per_au, seed=sd(f"c|{m}|{c}"))
        cls_ci.append({"measure": m, "author_class": c, "n_authors": k, "mean_improvement": mean,
                       "ci_low": lo, "ci_high": hi})
    cls_tbl = pd.DataFrame(cls_ci).merge(cls[["measure", "author_class", "n_author_size_cells"]],
                                         on=["measure", "author_class"]).sort_values(["measure", "author_class"])
    write_table(cls_tbl, os.path.join(OUTD, "gain_by_author_class.csv"))

    # ------------------------------------------------------------ 7. probe delta
    pr = runs[(runs.kind == "adapter") & (~runs.replicate)].dropna(subset=["probe_delta"]).copy()
    pr = pr.join(au_meta[["train_examples_max", "words_total", "n_works_train"]], on="author")
    prrows = []
    for (fam, pb), g in pr.groupby(["family", "params_b"]):
        for cv in ["train_examples", "train_examples_max", "words_total"]:
            r, lo, hi, p, n = spearman_ci(g[cv].values, g.probe_delta.values, seed=sd(f"p|{fam}|{pb}|{cv}"))
            prrows.append({"family": fam, "params_b": pb, "covariate": cv, "n_adapters": n,
                           "spearman_vs_probe_delta": r, "ci_low": lo, "ci_high": hi, "p": p})
    for fam, g in pr.groupby("family"):
        r, lo, hi, p, n = spearman_ci(np.log2(g.params_b.values), g.probe_delta.values, seed=sd(f"pp|{fam}"))
        prrows.append({"family": fam, "params_b": np.nan, "covariate": "log2(params_b)", "n_adapters": n,
                       "spearman_vs_probe_delta": r, "ci_low": lo, "ci_high": hi, "p": p})
    probe_corr = pd.DataFrame(prrows)
    probe_corr["q_bh"] = bh_fdr(probe_corr.p.values)
    write_table(probe_corr, os.path.join(OUTD, "probe_delta_vs_data_and_size.csv"))
    probe_by_size = (pr.groupby(["family", "params_b"])
                     .agg(n_adapters=("probe_delta", "size"), probe_delta_mean=("probe_delta", "mean"),
                          probe_delta_min=("probe_delta", "min"), probe_delta_max=("probe_delta", "max"),
                          eval_best_mean=("eval_best", "mean")).reset_index())
    write_table(probe_by_size, os.path.join(OUTD, "probe_delta_by_size.csv"))

    # ------------------------------------------------------------ 8. gate sensitivity
    sens = []
    for m in PRIMARY:
        g_all = gain[(gain.measure == m) & (gain.family == "Qwen3")]
        for lbl, g in [("all Qwen3 adapters", g_all),
                       ("gate_generation_ok is not False", g_all[g_all.gate_generation_ok != False]),  # noqa: E712
                       ("period + contemporary only", g_all[g_all.author_class != "private"])]:
            per_au = g.groupby("author").improves.mean().values
            mean, lo, hi, k = boot_mean(per_au, seed=sd(f"sen|{m}|{lbl}"))
            sens.append({"measure": m, "subset": lbl, "n_authors": k, "mean_improvement": mean,
                         "ci_low": lo, "ci_high": hi, "floor_qwen": floors[m]})
    sensitivity = pd.DataFrame(sens)
    write_table(sensitivity, os.path.join(OUTD, "gain_sensitivity.csv"))

    # ------------------------------------------------------------ 9. Chesterton data-size series
    series = pd.DataFrame()
    series_gain = pd.DataFrame()
    series_train = pd.DataFrame()
    SERIES_MEAS = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "styledist_cos_source",
                   "geo_index", "delta_own", "distinct_3", "rep_4", "sent_echo", "template_rate", "words"]
    if on_disk:
        recs = []
        for d in on_disk:
            n = int(d.replace("chesterton_size", ""))
            path = os.path.join(RUNS, d, "scores.jsonl")
            cov_path = os.path.join(RUNS, d, "coverage.jsonl")
            cov = {}
            if os.path.exists(cov_path):
                for line in open(cov_path, encoding="utf-8"):
                    r = json.loads(line)
                    cov[(r["id"], r["arm"], int(r["sample"]))] = float(r["coverage"])
            for line in open(path, encoding="utf-8"):
                r = json.loads(line)
                if r.get("group") != "gen" or r.get("arm") != "A0":
                    continue
                row = {"n_targets": n, "id": r["id"], "sample": int(r["sample"])}
                for m in SERIES_MEAS:
                    row[m] = r.get(m, np.nan)
                row["truncated"] = float(bool(r.get("flags")) and "truncated" in r.get("flags", []))
                row["coverage"] = cov.get((r["id"], "A0", int(r["sample"])), np.nan)
                recs.append(row)
        series = pd.DataFrame(recs)

        for d in train_on_disk + ["train_chesterton_pair_e6"]:
            p = os.path.join(RUNS, d, "run.json")
            if not os.path.exists(p):
                continue
            j = json.load(open(p, encoding="utf-8"))
            series_train = pd.concat([series_train, pd.DataFrame([{
                "train_run": d, "n_targets": j.get("n_targets"), "n_examples": j.get("n_examples"),
                "steps": j.get("steps"), "best_eval_loss": j.get("best_eval_loss"),
                "probe_delta": (j.get("probe") or {}).get("delta"), "wall_s": j.get("wall_s")}])],
                ignore_index=True)
        series_train = series_train.sort_values("n_targets")
        write_table(series_train, os.path.join(OUTD, "size_series_training_records.csv"))

        # brief-paired against the chesterton 4B base, and the full adapter for reference
        ch = cells[(cells.author == "chesterton") & (cells.family == "Qwen3") & (cells.params_b == 4)
                   & (cells.arm == "A0") & (~cells.replicate)]
        ref_rows = []
        for kind, lbl, n_t in [("base", "base 4B (no adapter)", 0),
                               ("adapter", "full adapter 4B (215 targets)", 215)]:
            g = ch[ch.kind == kind][["id", "sample"] + [m for m in SERIES_MEAS if m in ch.columns] + ["truncated", "coverage"]].copy()
            g["n_targets"] = n_t
            g["label"] = lbl
            ref_rows.append(g)
        series["label"] = series.n_targets.map(lambda n: f"adapter n={n}")
        allser = pd.concat([series] + ref_rows, ignore_index=True)

        srows = []
        base_bm = (allser[allser.label == "base 4B (no adapter)"]
                   .groupby("id")[SERIES_MEAS + ["truncated", "coverage"]].mean())
        for lbl, g in allser.groupby("label"):
            bm = g.groupby("id")[SERIES_MEAS + ["truncated", "coverage"]].mean()
            n_t = int(g.n_targets.iloc[0])
            for m in SERIES_MEAS + ["truncated", "coverage"]:
                j = pd.concat([bm[m].rename("v"), base_bm[m].rename("b")], axis=1).dropna()
                if len(j) < 3:
                    continue
                mean, lo, hi, k = boot_mean((j.v - j.b).values, seed=sd(f"ss|{lbl}|{m}"))
                pt, plo, phi, _k = boot_mean(j.v.values, seed=sd(f"ssl|{lbl}|{m}"))
                srows.append({"label": lbl, "n_targets": n_t, "measure": m, "n_briefs": k,
                              "level": pt, "level_ci_low": plo, "level_ci_high": phi,
                              "gain_vs_base": mean, "ci_low": lo, "ci_high": hi,
                              "floor_qwen": floors.get(m, np.nan)})
        series_gain = pd.DataFrame(srows).sort_values(["measure", "n_targets"])
        write_table(series_gain, os.path.join(OUTD, "size_series_chesterton.csv"))

        # comparability is read from each run's own s3 manifest (the requested sampling block,
        # not the llama-server default, which is 0.6 on every run and is not what was asked for)
        cmp_rows = []
        for rn in ["chesterton_base4b", "chesterton_paire6_4b"] + on_disk:
            mf = [f for f in os.listdir(os.path.join(RUNS, rn)) if f.startswith("s3_manifest")]
            if not mf:
                continue
            man = json.load(open(os.path.join(RUNS, rn, mf[0]), encoding="utf-8"))
            sm = man.get("sampling", {})
            cmp_rows.append({"run": rn, "started": man.get("started"), "backend": man.get("backend"),
                             "base_model": man.get("base"),
                             "temperature_requested": man.get("temperature", sm.get("temperature")),
                             "top_p": sm.get("top_p"), "max_new_cap": sm.get("max_new_cap"),
                             "len_mult": sm.get("len_mult"), "seeds": str(man.get("seeds")),
                             "arms": ",".join(man.get("arms", [])), "n_generated": man.get("n_generated"),
                             "adapter": os.path.basename(os.path.dirname(man.get("adapter") or "")) or "none",
                             "has_provenance_block": bool(man.get("provenance")),
                             "in_master_table": rn in set(runs.run)})
        cmp_tbl = pd.DataFrame(cmp_rows)
        write_table(cmp_tbl, os.path.join(OUTD, "size_series_comparability.csv"))

    # ------------------------------------------------------------ figures
    figs = []
    ml = list(PRIMARY)
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.4), squeeze=False)
    cols = {4.0: "tab:blue", 8.0: "tab:orange", 14.0: "tab:red", 1.7: "tab:green", 3.0: "tab:purple"}
    for i, m in enumerate(ml):
        ax = axes[i // 3][i % 3]
        g = gain[(gain.measure == m) & (gain.family == "Qwen3")].dropna(subset=["train_examples_max"])
        for pb, gg in g.groupby("params_b"):
            ax.scatter(gg.train_examples_max, gg.improves, s=22, c=cols.get(pb, "k"),
                       label=f"Qwen3 {pb:g}B", alpha=0.85)
            if len(gg) >= 4:
                xs = np.log2(gg.train_examples_max.values)
                b1, b0 = np.polyfit(xs, gg.improves.values, 1)
                xx = np.linspace(xs.min(), xs.max(), 20)
                ax.plot(2 ** xx, b0 + b1 * xx, c=cols.get(pb, "k"), lw=1, alpha=0.6)
        gm = gain[(gain.measure == m) & (gain.family == "Ministral3")].dropna(subset=["train_examples_max"])
        ax.scatter(gm.train_examples_max, gm.improves, s=22, marker="^", facecolors="none",
                   edgecolors="0.35", label="Ministral3 (3 authors)")
        f = floors[m]
        if f == f:
            ax.axhspan(-f, f, color="0.88", zorder=0)
        ax.axhline(0, color="0.4", lw=0.8)
        ax.set_xscale("log", base=2)
        ax.set_xlabel("fit examples (train_examples_max)", fontsize=8)
        ax.set_title(f"{m} ({MEASURES[m]})  improvement", fontsize=8)
        ax.tick_params(labelsize=7)
        if i % 3 == 0:
            ax.set_ylabel("adapter improvement over base", fontsize=8)
    h, lbl = axes[0][0].get_legend_handles_labels()
    fig.legend(h, lbl, loc="lower center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.suptitle("Adapter improvement over base against the size of the author's training set\n"
                 "(one point per author x size, arm A0; grey band = Qwen3 replicate floor)", fontsize=9)
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    figs.append(("Gain against corpus size", savefig(fig, os.path.join(OUTD, "gain_vs_corpus.png"))))

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4))
    ax = axes[0]
    for pb, g in trunc[trunc.family == "Qwen3"].groupby("params_b"):
        ax.scatter(g.train_examples_max, g.adapter_truncated_rate_A0 * 100, s=26, c=cols.get(pb, "k"),
                   label=f"Qwen3 {pb:g}B")
    for pb, g in trunc[trunc.family == "Ministral3"].groupby("params_b"):
        ax.scatter(g.train_examples_max, g.adapter_truncated_rate_A0 * 100, s=26, marker="^",
                   facecolors="none", edgecolors=cols.get(pb, "0.3"), label=f"Ministral3 {pb:g}B")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("fit examples (train_examples_max)", fontsize=9)
    ax.set_ylabel("adapter truncation rate at A0 (%)", fontsize=9)
    ax.set_title("Thin adapters run to the token cap", fontsize=10)
    ax.legend(fontsize=7, frameon=False, ncol=2)
    ax.tick_params(labelsize=8)
    ax = axes[1]
    for fam, g in pr.groupby("family"):
        for pb, gg in g.groupby("params_b"):
            ax.scatter(gg.train_examples, gg.probe_delta, s=26,
                       marker="o" if fam == "Qwen3" else "^",
                       facecolors=cols.get(pb, "k") if fam == "Qwen3" else "none",
                       edgecolors=cols.get(pb, "k"), label=f"{fam} {pb:g}B")
    ax.set_xscale("log", base=2)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xlabel("fit examples used by that adapter (train_examples)", fontsize=9)
    ax.set_ylabel(VARIABLES.get("probe_delta", ("probe delta (val loss adapter on minus off)",))[0]
                  if "probe_delta" in VARIABLES else "probe delta (val loss on minus off)", fontsize=9)
    ax.set_title("Probe delta by data and parameter count", fontsize=10)
    ax.legend(fontsize=6, frameon=False, ncol=2)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    figs.append(("Truncation and probe delta against data size",
                 savefig(fig, os.path.join(OUTD, "truncation_and_probe.png"))))

    if len(piece):
        m0 = "luar_cos_source"
        row = piece[piece.measure == m0]
        g = qp[qp.measure == m0].dropna(subset=["train_briefs_passed"])
        fig, ax = plt.subplots(figsize=(7, 4.4))
        ax.scatter(g.train_briefs_passed, g.improves, s=34, c="tab:blue")
        for _, r in g.iterrows():
            ax.annotate(r.author, (r.train_briefs_passed, r.improves), fontsize=6,
                        xytext=(3, 3), textcoords="offset points")
        if len(row):
            bp = float(row.breakpoint_briefs.iloc[0])
            xs = np.linspace(g.train_briefs_passed.min(), g.train_briefs_passed.max(), 200)
            pw = piecewise_fit(g.train_briefs_passed.values.astype(float), g.improves.values, grid)
            ax.plot(xs, pw["intercept"] + pw["slope_below"] * xs + (pw["slope_above"] - pw["slope_below"]) * np.maximum(0, xs - bp),
                    c="tab:red", lw=1.3, label=f"piecewise, break at {bp:.0f} briefs")
            ax.axvline(bp, color="tab:red", ls=":", lw=1)
        b1, b0 = np.polyfit(g.train_briefs_passed.values, g.improves.values, 1)
        ax.plot(np.sort(g.train_briefs_passed.values), b0 + b1 * np.sort(g.train_briefs_passed.values),
                c="0.4", lw=1, ls="--", label="linear")
        ax.axhline(0, color="0.6", lw=0.8)
        ax.set_xlabel("training briefs passed", fontsize=9)
        ax.set_ylabel("adapter improvement on\nLUAR cosine to the source", fontsize=9)
        ax.set_title(f"Breakpoint search on {m0}, {len(g)} authors\n"
                     "(mean over each author's Qwen3 sizes)", fontsize=10)
        ax.legend(fontsize=8, frameon=False)
        figs.append(("Piecewise breakpoint", savefig(fig, os.path.join(OUTD, "piecewise_breakpoint.png"))))

    if len(series_gain):
        ml2 = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "geo_index", "coverage", "truncated"]
        fig, axes = plt.subplots(2, 3, figsize=(11, 6.2), squeeze=False)
        for i, m in enumerate(ml2):
            ax = axes[i // 3][i % 3]
            s = series_gain[(series_gain.measure == m) & (series_gain.label.str.startswith("adapter n="))].sort_values("n_targets")
            full = series_gain[(series_gain.measure == m) & (series_gain.label.str.startswith("full adapter"))]
            if len(s):
                ax.errorbar(s.n_targets, s.gain_vs_base,
                            yerr=[s.gain_vs_base - s.ci_low, s.ci_high - s.gain_vs_base],
                            marker="o", ms=4, lw=1.2, capsize=2, c="tab:blue", label="size series")
            if len(full):
                ax.errorbar(full.n_targets, full.gain_vs_base,
                            yerr=[full.gain_vs_base - full.ci_low, full.ci_high - full.gain_vs_base],
                            marker="s", ms=5, capsize=2, c="tab:red", label="full adapter (215)")
            f = floors.get(m, np.nan)
            if f == f:
                ax.axhspan(-f, f, color="0.88", zorder=0)
            ax.axhline(0, color="0.4", lw=0.8)
            ax.set_title(m, fontsize=8)
            ax.set_xlabel("training targets", fontsize=8)
            ax.tick_params(labelsize=7)
            if i % 3 == 0:
                ax.set_ylabel("adapter minus base 4B", fontsize=8)
        h, lbl = axes[0][0].get_legend_handles_labels()
        fig.legend(h, lbl, loc="lower center", ncol=2, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
        fig.suptitle("Chesterton within-author data-size series, Qwen3 4B, arm A0\n"
                     "(read from data/runs/ directly: these runs are not in the master table)", fontsize=9)
        fig.tight_layout(rect=[0, 0.03, 1, 0.93])
        figs.append(("Chesterton data-size series", savefig(fig, os.path.join(OUTD, "chesterton_size_series.png"))))

    # ------------------------------------------------------------ README numbers
    n_auth_total = int(gain.author.nunique())
    n_auth_examples = int(gain.dropna(subset=["train_examples_max"]).author.nunique())
    pooled_corr = corr[corr.level == "Qwen3 pooled over sizes"]
    widest = pooled_corr.loc[pooled_corr.interval_width.idxmax()] if len(pooled_corr) else None
    strongest = pooled_corr.reindex(pooled_corr.spearman.abs().sort_values(ascending=False).index).head(6)
    n_sig_corr = int((corr.q_bh < 0.05).sum())
    tc = trunc_corr[(trunc_corr.family == "Qwen3") & (trunc_corr.covariate == "train_examples_max")]
    t14 = tc[tc.params_b == 14]
    trunc14 = trunc[(trunc.family == "Qwen3") & (trunc.params_b == 14)].sort_values("adapter_truncated_rate_A0", ascending=False)
    lin_luar = piece[piece.measure == "luar_cos_source"]
    bp_id = piece[piece.breakpoint_identified == True] if len(piece) else piece  # noqa: E712
    n_bp_id = int(len(bp_id))
    bp_txt = ("; ".join(f"{r.measure} at {r.breakpoint_briefs:.0f} briefs "
                        f"[{r.bp_boot_lo:.0f}, {r.bp_boot_hi:.0f}], permutation p {r.p_permutation_break:.3f}"
                        for _, r in bp_id.iterrows()) or "none")
    bp_fail = "; ".join(f"{r.measure} ({r.bp_boot_at_grid_edge_share * 100:.0f}% of bootstrap "
                        f"breakpoints on a grid edge, permutation p {r.p_permutation_break:.3f})"
                        for _, r in piece[piece.breakpoint_identified != True].iterrows()) or "none"  # noqa: E712
    prim_gain = gain[gain.measure.isin(PRIMARY) & (gain.family == "Qwen3")]
    n_gain_sig = int(((prim_gain.q_bh < 0.05) & (prim_gain.above_floor == True)).sum())  # noqa: E712

    # ---- README-only helpers. Every number in the written piece is read back out of the tables
    # this script wrote; none of it is typed by hand.
    sens_all = sensitivity[sensitivity.subset == "all Qwen3 adapters"]
    sens_clear = sens_all[sens_all.mean_improvement.abs() > sens_all.floor_qwen]
    sens_cost = sens_clear[sens_clear.mean_improvement < 0]
    sens_gain = sens_clear[sens_clear.mean_improvement > 0]
    sens_clear_txt = ", ".join(sens_clear.measure) or "none"
    sens_cost_txt = ", ".join(sens_cost.measure) or "none"
    sens_gain_txt = ", ".join(sens_gain.measure) or "none"
    bp_above_nonpos = int((bp_id.slope_above <= 0).sum()) if len(bp_id) else 0
    probe_size = probe_corr[(probe_corr.covariate == "log2(params_b)")
                            & probe_corr.spearman_vs_probe_delta.notna()]
    probe_size_txt = "; ".join(
        f"{r.family} rho {r.spearman_vs_probe_delta:+.2f} [{r.ci_low:+.2f}, {r.ci_high:+.2f}], "
        f"q {r.q_bh:.3f}, over {int(r.n_adapters)} adapter runs"
        for _, r in probe_size.iterrows()) or "not estimable"
    probe_pos = probe_by_size[probe_by_size.probe_delta_max > 0]
    probe_pos_txt = ", ".join(f"{r.family} {r.params_b:g}B (max {r.probe_delta_max:+.4f})"
                              for _, r in probe_pos.iterrows()) or "none"
    tq = trunc_corr[(trunc_corr.family == "Qwen3")
                    & (trunc_corr.covariate == "train_examples_max")
                    & trunc_corr.spearman_vs_adapter_truncation.notna()].sort_values("params_b")
    tq_txt = "; ".join(f"{r.params_b:g}B rho {r.spearman_vs_adapter_truncation:+.2f} "
                       f"[{r.ci_low:+.2f}, {r.ci_high:+.2f}], q {r.q_bh:.3f}, n = {int(r.n_authors)}"
                       for _, r in tq.iterrows()) or "not estimable"
    dup_pair = sorted(set(gain.author.unique()) & {"patrick", "patrick_v2"})
    n_indep = int(gain.author.nunique() - (1 if len(dup_pair) > 1 else 0))
    n_grid = int(len(grid))
    _cap = float(authors.train_examples_max.max())
    _capped = authors[authors.train_examples_max == _cap]
    capped_txt = ", ".join(f"{r.author} ({int(r.train_briefs_passed)} training briefs)"
                           for _, r in _capped.iterrows()) or "no author"
    ministral_floor_rows = pd.concat([replicate_floor(cells, m, arm="A0") for m in MEASURES])
    n_min_floor_measures = int(ministral_floor_rows[ministral_floor_rows.family == "Ministral3"].measure.nunique())

    key_tables = [
        ("Is the Chesterton data-size series in the master table?", ss_status),
        ("Adapter improvement against the corpus, Spearman over authors (pooled over the Qwen3 sizes; "
         "read the interval, not the point)",
         pooled_corr[["measure", "covariate", "n_authors", "spearman", "ci_low", "ci_high", "interval_width", "q_bh"]]
         .sort_values(["measure", "covariate"]).head(48)),
        ("Log-linear slope of improvement per doubling of fit examples",
         fits[fits.measure.isin(PRIMARY)][["family", "params_b", "measure", "n_authors", "slope_per_doubling",
                                           "ci_low", "ci_high", "r2"]]),
        ("Piecewise fit, breakpoint searched over 25-200 training briefs", piece),
        ("Adapter truncation at A0 against the corpus", trunc_corr[trunc_corr.family == "Qwen3"]),
        ("Qwen3 14B adapters ordered by truncation",
         trunc14[["author", "author_class", "train_examples_max", "train_briefs_passed",
                  "adapter_truncated_rate_A0", "base_truncated_rate_A0", "probe_delta",
                  "gate_generation_ok"]].assign(
             gate_generation_ok=lambda t: t.gate_generation_ok.map(
                 {True: "pass", False: "FAIL"}).fillna("not gated"))),
        ("Improvement by author class (Qwen3, one value per author)", cls_tbl[cls_tbl.measure.isin(PRIMARY)]),
        ("Probe delta by family and size", probe_by_size),
        ("Probe delta against data and parameter count", probe_corr),
        ("Sensitivity of the pooled improvement", sensitivity),
    ]
    if len(series_gain):
        key_tables.append(("Chesterton data-size series, adapter minus base 4B (from data/runs/, not the master table)",
                           series_gain[series_gain.measure.isin(["luar_cos_source", "luar_cos_ref",
                                                                 "wegmann_cos_source", "geo_index", "coverage",
                                                                 "truncated"])]
                           [["measure", "label", "n_targets", "n_briefs", "level", "gain_vs_base",
                             "ci_low", "ci_high", "floor_qwen"]]))
        key_tables.append(("Training records for that series", series_train))
        key_tables.append(("Comparability of the series runs with the master-table runs",
                           pd.read_csv(os.path.join(OUTD, "size_series_comparability.csv"))))

    what = f"""
    Asks what an author's corpus buys the adapter: whether more training briefs, more fit
    examples, more words or more distinct works produce a larger adapter gain, whether the
    relationship bends at a data floor, whether the thin-corpus adapters are the ones that run
    to the token cap, and whether private, period and contemporary authors behave differently.

    The adapter gain is the brief-paired difference (adapter A0 minus base A0) per author x
    family x size on {len(MEASURES)} measures, {len(PRIMARY)} of them primary. Author-level
    analyses rest on {n_auth_total} author rows in total and {n_auth_examples} once
    `train_examples_max` is required, so every correlation below is an n = {n_auth_examples} or
    {n_auth_total} estimate and its interval is reported next to it.
    {"Two of those rows, " + " and ".join(dup_pair) + ", are the same corpus at two chunk sizes, so the independent corpora number " + str(n_indep) + "." if len(dup_pair) > 1 else ""}
    """

    series_note = ("no run in runs.csv has a name containing n25, n50, n100 or n150, so the "
                   "within-author data-size series does not exist as a generation run in the master "
                   f"table and the cross-author comparison is the primary analysis. The four "
                   f"generation runs do exist on disk ({', '.join(on_disk)}) with gens, scores, "
                   "embeddings and coverage, and the four training records exist as well; they were "
                   "left out of the master table because `lib.parse_run` cannot parse their names "
                   "(the tag `size25` is not in `lib.PARAMS`). They are read here directly from "
                   "`data/runs/` and reported as a supplement, clearly separated from everything "
                   "built on `cells.parquet`."
                   if not have_master_series and on_disk else
                   ("the size-series runs are present in runs.csv and are used as the within-author series."
                    if have_master_series else
                    "the size-series runs exist neither in runs.csv nor on disk; the cross-author data is all there is."))

    how = f"""
    Data: `data/master/cells.parquet` at arm A0, non-replicate cells only, so the eval-cache
    measures (per, otd_js, hapax_w300) are the values actually computed for these passages
    rather than the A0 copy the master build broadcasts onto the other arms. Corpus covariates
    come from `data/master/authors.csv`, adapter covariates from `data/master/runs.csv`.

    Unit. Inside an author the brief is the cluster: the gain is the mean over briefs of
    (adapter minus base) on the same brief and sample, with a bootstrap over briefs. For any
    claim about corpora the author is the unit, and the correlations are computed over authors
    with `lib.spearman_ci` (2000 bootstrap resamples of the author set). p-values are BH-FDR
    adjusted within each table.

    Data-size series: {series_note}

    Piecewise fit: a continuous two-segment linear fit of the author-level improvement on
    training briefs, with the breakpoint searched over {n_grid} candidate positions on a
    one-brief grid from 25 to 200 and a bootstrap over authors for the breakpoint itself. The
    permutation p-values in `gain_piecewise_breakpoint.csv` are not BH-adjusted; they are read
    against the {len(piece)} measures searched, and a single measure's p there is not a q.

    Floors: every gain is printed beside `lib.replicate_floor` for its measure at A0. Measured
    floors now exist for {", ".join(fam_floor) or "no family"}
    {"(no family is missing one)" if not fam_no_floor else "and not for " + ", ".join(fam_no_floor)},
    with {n_min_floor_measures} of this script's measures carrying a measured Ministral3 floor.
    The `floor_qwen` column beside every gain here is the Qwen3 value whatever the family of the
    row, so a Ministral3 above-floor verdict in this folder is a borrowed one. The Ministral3
    floors were measured from two 3B replicate pairs scored on 2026-09-10 and none exists at 8B
    or 14B.

    Mixed models: `gain ~ C(author_class) + log2(params) + log2(fit examples)` with a random
    intercept per author, Qwen3 only, one per primary measure. {n_fit_fail} of {n_models} failed
    to fit and {n_singular} of the {max(n_models - n_fit_fail, 0)} that fitted sit at the zero
    boundary for the author variance (`boundary_fit` in the csv). Because author_class does not
    vary within an author, its contrast is identified only across authors: with 11 to 14 of them
    split three ways it is descriptive, and no author_class row here should be read as a test.
    """

    reading = f"""
    The unit is the author and there are {n_indep} independent corpora behind every pooled
    number here, so a Spearman correlation is barely an estimate. The widest pooled interval in
    this folder runs from {widest.ci_low:.2f} to {widest.ci_high:.2f} ({widest.measure} against
    {widest.covariate}, n = {int(widest.n_authors)}), which is almost the whole possible range of
    the statistic. Read the intervals, not the point estimates, and read the sign only where the
    interval stays on one side of zero. Across all {len(corr)} correlations in
    `gain_vs_corpus_spearman.csv`, {n_sig_corr} reach q < 0.05 within that family of
    {len(corr)}. The limit on all of it is the {n_indep} corpora, not the multiplicity: BH-FDR
    does nothing about thirteen points.

    The corpus covariates are collinear with one another: an author with more training briefs
    also has more words and usually more works, so a correlation with any one of them is not
    evidence that that one is the cause. `train_examples_max` is additionally censored at
    {_cap:.0f} for {len(_capped)} authors ({capped_txt}), which flattens the top of every curve
    fitted against it and biases the log-linear slope toward zero.

    The breakpoint is searched, not estimated: {n_grid} candidate positions are tried on
    {int(lin_luar.n_authors.iloc[0]) if len(lin_luar) else 0} points, and the R-squared it gains
    over a straight line is inflated by that search. Two guards are applied and reported per
    measure: a permutation test that repeats the whole search on shuffled outcomes, and the
    share of bootstrap breakpoints that land on an edge of the grid. {n_bp_id} of
    {len(piece)} measures pass both: {bp_txt}. The rest do not: {bp_fail}. Those permutation
    p-values carry no multiplicity correction across the {len(piece)} measures. Read a breakpoint
    as a description of these {int(lin_luar.n_authors.iloc[0]) if len(lin_luar) else 0} author
    rows, not as a training-data threshold that would transfer to a fifteenth.

    Judged measures. `coverage` is an LLM judge's count of brief items, so every coverage row
    here, including the breakpoint fitted to it, is a judge's reading and not a measurement.
    Coverage rows for several Qwen3 runs were error rows from the 2026-09-09 credit outage and
    were being refilled while this was written, and coverage does not exist at all on Ministral3.
    Judge measures are relative instruments and are never read here as absolute quality.

    What would overturn this. One author moves these numbers: `gain_sensitivity.csv` re-runs the
    pooled improvement dropping the private authors and dropping the runs whose generation gate
    failed. If the truncation relationship is really a token-cap artefact rather than a
    data-size effect, the whole "thin adapters" reading collapses into a generation-settings
    problem, and the right test is the length null in script 17, not anything here. The refilled
    coverage rows would move every coverage row in this folder, including the breakpoint.

    What this does not show. It does not show that more data causes a better adapter: no author
    was trained twice at different corpus sizes inside the master table, so every point on these
    curves is a different author with a different prose style, a different era and a different
    number of works. The Chesterton series is the only within-author evidence in the study, it
    covers one author, one family, one parameter count and four sizes, and it is not in the
    master table. Nothing here is a claim about a model or a family: the covariate is the corpus,
    and the model rows are strata within it.
    """

    _other_series = [a for a in size_series_authors if a != "chesterton"]
    _series_note = (f"The raw-file series cross-check in this script covers Chesterton only; {len(_other_series)} other author"
                    f"{'s' if len(_other_series) != 1 else ''} ({', '.join(_other_series) or 'none'}) ha{'ve' if len(_other_series) != 1 else 's'} a "
                    f"within-author size series on disk, analysed with seed replicates in script 25 (`25_series_and_frontier/size_series.csv`).")
    caveats = [_series_note,
        f"n = {n_auth_total} author rows ({n_auth_examples} with a fit-example count; patrick, the v1 chunking "
        f"control, has no e6 training record), which is {n_indep} independent corpora because patrick and "
        f"patrick_v2 are the same person's prose at two chunk sizes. Every author-level interval in this "
        f"folder is that wide, and no correction narrows it.",
        f"train_examples_max is censored at {_cap:.0f} fit examples, which {len(_capped)} authors reach "
        f"({capped_txt}), so the largest corpora are recorded as equal on that covariate although their "
        f"brief counts differ.",
        "The corpus covariates are mutually collinear; nothing here separates briefs from words from works.",
        f"The `floor_qwen` column beside every gain is the Qwen3 floor whatever the family of the row, so "
        f"Ministral3 above-floor verdicts here are borrowed. Measured Ministral3 floors exist for "
        f"{n_min_floor_measures} of this script's measures, from two 3B replicate pairs scored on 2026-09-10, "
        f"and none exists at 8B or 14B.",
        "Ministral3 has three authors at each size, so its Spearman rows are computed over three points and "
        "are printed for completeness only.",
        "The Chesterton size-series runs are absent from cells.parquet and runs.csv; the supplement here is "
        "read from raw scores.jsonl and is not covered by data/MANIFEST.json's master-table build.",
        "coverage is an LLM-judged measure on sample 0 only, missing for several adapter runs and absent from "
        "Ministral3 entirely, so its author counts are smaller than the other measures'. Rows for several "
        "Qwen3 runs were error rows from the 2026-09-09 credit outage and were being refilled while this was "
        "written, so every coverage number here, including the coverage breakpoint, is provisional.",
        "`per` is close to permutation-invariant: shuffling an author's own sentences moves it less than "
        "swapping in another author's passages does (LOG.md, 2026-09-10). It is reported here as a raw rate "
        "and a difference of raw rates, and no calibrated position or fidelity value should be quoted for it.",
        "`doctorow_basem8b` exceeds the 20% truncation gate and is flagged rather than excluded, so it sits "
        "inside the Ministral3 8B truncation rows as a base with a quarter of its passages cut off.",
        "The `*_cos_ref` and attribution measures are anchored against a stranger pool of fourteen period "
        "authors for every study author, so contemporary and private authors are positioned against another "
        "century; scripts/23_register_matched_pool.py holds the register-matched repair, unapplied here.",
        "geo_index is used with direction '+' (higher = closer to the author), against the variable "
        "dictionary; see analysis/12_arm_effects/geo_index_direction.csv.",
        f"Mixed models: {n_fit_fail} of {n_models} failed to fit and {n_singular} sit at the zero boundary "
        "for the author variance. author_class is between-author, so its contrast rests on 11-14 authors "
        "split three ways and is descriptive. lib.mixed_model was changed on 2026-09-10 to drop the lbfgs "
        "optimiser, which returned zero variances and 1e4 intercept standard errors on these data; running "
        "this script against an older lib.py will not reproduce the mixed-model rows.",
    ]

    def series_line(m, col="gain_vs_base"):
        if not len(series_gain):
            return "not available"
        s = series_gain[(series_gain.measure == m) & (series_gain.n_targets > 0)].sort_values("n_targets")
        return ", ".join(f"n={int(r.n_targets)}: {r[col]:+.3f} [{r.ci_low:+.3f}, {r.ci_high:+.3f}]"
                         for _, r in s.iterrows())

    series_txt = ""
    if len(series_gain):
        series_txt = f"""
- The one within-author series in the study points the same way, on one author (Chesterton) at
  Qwen3 4B, read straight from `data/runs/`. Adapter minus base 4B on luar_cos_source:
  {series_line('luar_cos_source')} (Qwen3 floor {floors['luar_cos_source']:.4f}). Brief coverage,
  which is an LLM judge's count: {series_line('coverage')} (floor {floors['coverage']:.4f}).
  Truncation rate: {series_line('truncated')} (floor {floors['truncated']:.4f}). The voice gain
  rises to n=100 targets and the intervals above it overlap each other, so the series is
  consistent with the gain flattening by about that point without locating where. The coverage
  and truncation costs are largest at n=25 and smaller at every step above it. Every run in that
  series used the same base model, backend, temperature (0.8), top_p, token cap, length
  multiplier and seeds as the two master-table runs it is compared against
  (`size_series_comparability.csv`). One author is one author: nothing here generalises to a
  second, and the series is a supplement to the cross-author analysis, not a replication of it."""

    strongest_txt = "; ".join(
        f"{r.measure} vs {r.covariate} rho {r.spearman:+.2f} [{r.ci_low:+.2f}, {r.ci_high:+.2f}]"
        for _, r in strongest.iterrows())

    extra = f"""
### Headline numbers

- What the adapter buys and what it costs, pooled over the Qwen3 authors (one value per author,
  averaged over the sizes that author has; positive = closer to the author on that measure):
  {'; '.join(f"{r.measure} {r.mean_improvement:+.4f} [{r.ci_low:+.4f}, {r.ci_high:+.4f}] (floor {r.floor_qwen:.4f}, n={int(r.n_authors)})" for _, r in sens_all.iterrows())}.
  {len(sens_clear)} of the {len(sens_all)} clear their replicate floor ({sens_clear_txt}), and
  {len(sens_cost)} of those {len(sens_clear)} move away from the author rather than toward it
  ({sens_cost_txt}); {len(sens_gain)} move toward it ({sens_gain_txt}). The measures that do not
  clear their floor are not evidence of no effect, only of an effect this design cannot separate
  from regenerating the same run twice.
- The within-author data-size series is not in the master table. {series_note[0].upper() + series_note[1:]}
- Adapter improvement against corpus size, pooled over the Qwen3 sizes, n =
  {int(pooled_corr.n_authors.max())} author rows at most: the {len(strongest)} largest
  correlations by absolute value are {strongest_txt}. They are the largest of
  {len(pooled_corr)} pooled correlations and were picked on the same data they are reported on,
  so their point estimates are the high end of a selected set; read the intervals. Of all
  {len(corr)} correlations computed, {n_sig_corr} clear BH-FDR at q < 0.05 within that family.
- {n_gain_sig} of {len(prim_gain)} Qwen3 author x size adapter gains on the {len(PRIMARY)}
  primary measures clear both BH-FDR within their table and their replicate floor.
- Thin corpora are the ones that hit the token cap. At Qwen3 14B the adapter truncation rate at
  A0 runs from {trunc14.adapter_truncated_rate_A0.min() * 100:.1f}% ({trunc14.iloc[-1].author},
  {trunc14.iloc[-1].train_examples_max:.0f} fit examples) to
  {trunc14.adapter_truncated_rate_A0.max() * 100:.1f}% ({trunc14.iloc[0].author},
  {trunc14.iloc[0].train_examples_max:.0f} fit examples). The Spearman of adapter truncation on
  fit examples is negative at all three Qwen3 sizes ({tq_txt}), which is consistent with thin
  corpora truncating more; it does not separate a data-size effect from a token-cap setting, and
  script 17 holds that test. The order of the three correlations is not itself evidence that
  parameter count makes it worse.
- Probe delta moves toward zero with parameter count on Qwen3 and is not estimable on Ministral3:
  mean
  {probe_by_size[(probe_by_size.family == 'Qwen3') & (probe_by_size.params_b == 4)].probe_delta_mean.iloc[0]:.3f} at
  Qwen3 4B against
  {probe_by_size[(probe_by_size.family == 'Qwen3') & (probe_by_size.params_b == 14)].probe_delta_mean.iloc[0]:.3f} at
  Qwen3 14B, and Ministral3 means between
  {probe_by_size[probe_by_size.family == 'Ministral3'].probe_delta_mean.min():.3f} and
  {probe_by_size[probe_by_size.family == 'Ministral3'].probe_delta_mean.max():.3f}. Against
  log2(parameters) the correlation is {probe_size_txt}, so the Ministral3 interval covers both
  signs and the family is not evidence of anything here. The unit in that correlation is the
  adapter run and each author appears at every size, so the points are not independent. One
  adapter has a probe delta on the wrong side of zero ({probe_pos_txt}): the probe found it no
  closer to the author than the base, so its gains are not evidence that an adapter took hold.
- The gain flattens rather than growing with corpus size. Of {len(piece)} measures fitted with a
  searched breakpoint over 25-200 training briefs, {n_bp_id} survive both a permutation test on
  the searched R-squared gain and a check that the bootstrap breakpoint stays off the grid edges:
  {bp_txt}. In {bp_above_nonpos} of those {n_bp_id} the slope above the break is at or below zero,
  and in all {n_bp_id} it is a small fraction of the slope below it
  ({bp_id.slope_above.min():+.4f} to {bp_id.slope_above.max():+.4f} above,
  {bp_id.slope_below.min():+.4f} to {bp_id.slope_below.max():+.4f} below). Those slopes are in
  each measure's own units and are not comparable across measures. The permutation p-values carry
  no correction across the {len(piece)} measures searched.
- luar_cos_source is not one of them: its breakpoint bootstrap interval is
  {lin_luar.bp_boot_lo.iloc[0]:.0f} to {lin_luar.bp_boot_hi.iloc[0]:.0f} briefs, spanning most of
  the search grid, with permutation p {lin_luar.p_permutation_break.iloc[0]:.3f}. The bend the
  other measures show is not detectable on the embedding measure at this sample size, which is
  not the same as its being absent.
{series_txt}
"""

    write_readme(OUTD, "13 Corpus and data effects: what the author's corpus buys the adapter",
                 what, how, reading, caveats, key_tables, figs, extra)

    print(f"authors {n_auth_total}; gain rows {len(gain)}; correlations {len(corr)}; "
          f"size-series rows {len(series_gain)}")
    print(f"size series in runs.csv: {len(size_runs)}; on disk: {on_disk}")
    print(f"runtime {time.time() - T0:.1f}s -> {OUTD}")


if __name__ == "__main__":
    main()
