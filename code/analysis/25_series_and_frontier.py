"""25_series_and_frontier.py: the two side tables the main parser leaves out.

(a) Data-size series within an author. Every author that has one is covered: adapters trained
    on a graded number of that author's own training briefs at Qwen3 4B, each compared with
    that author's 4B base run on the same briefs, plus that author's existing full adapter as
    a comparison row. Chesterton was run locally on 2026-09-06; doctorow and patrick_v2 were
    run on RunPod on 2026-09-10. Every other data-size claim in the programme is across
    authors. These are the within-author series, brief-paired, with the same briefs at every
    training size. Each series is one author and the series are never pooled.
(b) Frontier arms: every hosted chat model in cells_frontier.parquet, given the brief only (F0)
    or the full conditioning (F5), against each author's own Qwen3 4B base A0/A5 and adapter A0
    on the same briefs. Each model carries its own `frontier_label` and every contrast is
    computed inside one label, so the models are compared with the local runs separately and
    with each other directly. The F5 arm exists only for the label that was run with it.

    python scripts/25_series_and_frontier.py
"""
from __future__ import annotations

import os
import sys
import textwrap

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (VARIABLES, bh_fdr, cluster_bootstrap, load_all, load_frontier, load_series, md_table, outdir, replicate_floor,  # noqa: E402
                 savefig, write_readme, write_table)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MEASURES = ["luar_cos_ref", "luar_cos_source", "wegmann_cos_source", "styledist_cos_source", "geo_index", "open_entropy", "pct_short8",
            "otd_js", "per", "hapax_w300", "sent_echo", "coverage", "fool_vs_source", "truncated", "len_ratio", "words"]
# the measures the series figure draws, in panel order; any without rows is dropped
FIG_MEASURES = ["luar_cos_source", "wegmann_cos_source", "styledist_cos_source", "coverage", "truncated", "per", "hapax_w300"]
# measures whose values come out of the eval cache and exist only where that cache was computed
CACHE_MEASURES = ["per", "otd_js", "hapax_w300"]
# measures that are readings from an LLM judge, never a quality score
JUDGE_MEASURES = ["coverage", "fool_vs_source"]
SHARED_TABLE_MEASURES = ["luar_cos_ref", "luar_cos_source", "wegmann_cos_source", "styledist_cos_source", "coverage", "truncated"]
# the measures the frontier figure draws, in panel order; any without rows is dropped
FRONTIER_FIG_MEASURES = ["luar_cos_source", "wegmann_cos_source", "styledist_cos_source", "coverage", "truncated", "per"]
# the v1 chunking control: it keeps its own rows and never enters a pooled row
CONTROL_AUTHOR = "patrick"


def paired_delta(a, b, measure, key=("id", "sample")):
    """brief-paired mean difference a - b with brief-cluster bootstrap; both frames one arm."""
    m = a[list(key) + [measure]].merge(b[list(key) + [measure]], on=list(key), suffixes=("_a", "_b")).dropna()
    if not len(m):
        return {"n_pairs": 0}
    m["d"] = m[f"{measure}_a"].astype(float) - m[f"{measure}_b"].astype(float)
    pt, lo, hi = cluster_bootstrap(m, "d", "id", n=1000)
    try:
        p = wilcoxon(m.groupby("id").d.mean()).pvalue if m.id.nunique() >= 6 else np.nan
    except Exception:
        p = np.nan
    return {"n_pairs": int(len(m)), "n_briefs": int(m.id.nunique()), "delta": pt, "ci_low": lo, "ci_high": hi, "p_wilcoxon_briefs": p}


def paired_rows(a, b, measure, key=("id", "sample")):
    """the per-row paired differences behind paired_delta, as a numpy array."""
    m = a[list(key) + [measure]].merge(b[list(key) + [measure]], on=list(key), suffixes=("_a", "_b")).dropna()
    if not len(m):
        return np.array([], float)
    return m[f"{measure}_a"].astype(float).values - m[f"{measure}_b"].astype(float).values


def local_run(cells, au, kind, tag="4b"):
    """The author's own non-replicate run of that kind at that model size, by name, or None.

    The frontier arms are compared with whatever local run the author actually has, so the
    legacy run names (base4b, cather_pair4b, patrick_pair4b) are resolved from the table rather
    than listed here."""
    d = cells[(cells.author == au) & (cells.tag == tag) & (cells.kind == kind) & (~cells.replicate)]
    if not len(d):
        return None
    return str(d.groupby("run").size().sort_values(ascending=False).index[0])


def adapter_better(delta, floor, measure):
    """True where the local adapter beats the frontier arm by more than the measure's floor.

    `delta` is frontier minus adapter, so the sign that favours the adapter depends on the
    measure's direction in the variable dictionary. Measures marked descriptive ('0') have no
    better direction and return NaN."""
    direction = VARIABLES.get(measure, ("", "", "", "0", False, ""))[3]
    if direction not in ("+", "-") or delta != delta or floor != floor:
        return np.nan
    return bool(delta < -floor) if direction == "+" else bool(delta > floor)


def prepare_series(series):
    """Fill the columns the 2026-09-10 builder added, so an older parquet still runs."""
    if not len(series):
        return series
    s = series.copy()
    if "targets_seed" not in s.columns:
        s["targets_seed"] = 0
    s["targets_seed"] = pd.to_numeric(s["targets_seed"], errors="coerce").fillna(0).astype(int)
    if "series_platform" not in s.columns:
        s["series_platform"] = "local"
    s["series_platform"] = s["series_platform"].fillna("local").replace({"": "local"})
    s["train_briefs_n"] = pd.to_numeric(s["train_briefs_n"], errors="coerce")
    return s[s.train_briefs_n.notna()].copy()


def _platform_of(run_row):
    p = str(run_row.get("provenance_platform") or "")
    if p.startswith("Windows"):
        return "local"
    if p.startswith("Linux"):
        return "runpod"
    return "unknown"


def author_points(s, cells, runs, authors, au):
    """Every adapter point for one author: the seeded series levels, then the existing full adapter."""
    pts = []
    for (n, seed), g in s[s.author == au].groupby(["train_briefs_n", "targets_seed"], sort=True):
        rec = g.iloc[0]
        pts.append({"train_briefs": int(n), "targets_seed": int(seed), "point_kind": "series", "run": str(rec["run"]),
                    "series_platform": str(rec.get("series_platform", "local")), "train_examples": rec.get("train_examples"),
                    "train_targets": np.nan, "train_steps": rec.get("train_steps"), "probe_delta": rec.get("probe_delta"),
                    "eval_best": rec.get("eval_best"), "frame": g})
    full_run = f"{au}_paire6_4b"
    full = cells[cells.run == full_run]
    if len(full):
        arow = authors[authors.author == au]
        rrow = runs[runs.run == full_run]
        n_full = float(arow.train_briefs_passed.iloc[0]) if len(arow) and pd.notna(arow.train_briefs_passed.iloc[0]) else np.nan
        if n_full != n_full and len(rrow) and pd.notna(rrow.train_targets.iloc[0]):
            n_full = float(rrow.train_targets.iloc[0])
        if n_full == n_full:
            r0 = rrow.iloc[0] if len(rrow) else pd.Series(dtype=object)
            pts.append({"train_briefs": int(n_full), "targets_seed": 0, "point_kind": "existing_adapter", "run": full_run,
                        "series_platform": _platform_of(r0), "train_examples": r0.get("train_examples"),
                        "train_targets": r0.get("train_targets"), "train_steps": r0.get("train_steps"),
                        "probe_delta": r0.get("probe_delta"), "eval_best": r0.get("eval_best"), "frame": full})
    pts.sort(key=lambda d: (d["train_briefs"], d["targets_seed"], d["point_kind"] != "series"))
    return pts


def curve_points(pts):
    """The seed-0 points that make the dose-response curve. The existing full adapter is kept
    only where no seeded level sits at the same brief count, so a capped full adapter never
    doubles a seeded point of the same nominal size."""
    seeded = {p["train_briefs"] for p in pts if p["point_kind"] == "series" and p["targets_seed"] == 0}
    keep = []
    for p in pts:
        if p["targets_seed"] != 0:
            continue
        if p["point_kind"] == "existing_adapter" and p["train_briefs"] in seeded:
            continue
        keep.append(p)
    return keep


def main():
    out = outdir("25_series_and_frontier")
    cells, runs, authors, briefs, refs = load_all()
    series = prepare_series(load_series())
    frontier = load_frontier()
    floors = {m: replicate_floor(cells, m) for m in MEASURES}
    qfloor = {m: (float(f[f.family == "Qwen3"].abs_mean_diff.max()) if len(f[f.family == "Qwen3"]) else np.nan) for m, f in floors.items()}
    tables, figures = [], []
    notes = []

    # ---------------------------------------------------------------- (a) data-size series
    ser_rows, trend_rows, train_rows, seed_rows = [], [], [], []
    ser = tr = trn = seedrep = gain = pd.DataFrame()
    series_authors, skipped_authors = [], []
    if len(series):
        for au in sorted(series.author.unique()):
            base = cells[cells.run == f"{au}_base4b"]
            if not len(base):
                skipped_authors.append(au)
                notes.append(f"{au}: no {au}_base4b run in cells.parquet, so that series has no base to pair against and is not in the tables.")
                continue
            series_authors.append(au)
            arms = [a for a in sorted(series[series.author == au].arm.unique())]
            pts = author_points(series, cells, runs, authors, au)
            if not any(p["point_kind"] == "existing_adapter" for p in pts):
                notes.append(f"{au}: no {au}_paire6_4b run in cells.parquet, so the series has no existing-adapter comparison row.")
            for p in pts:
                train_rows.append({"author": au, "train_briefs": p["train_briefs"], "targets_seed": p["targets_seed"], "point_kind": p["point_kind"],
                                   "run": p["run"], "series_platform": p["series_platform"], "train_examples": p["train_examples"],
                                   "train_targets": p["train_targets"], "train_steps": p["train_steps"], "probe_delta": p["probe_delta"],
                                   "eval_best": p["eval_best"]})
            # every adapter point against the base, brief-paired, one row per arm x measure
            for arm in arms:
                b = base[base.arm == arm]
                if not len(b):
                    continue
                for p in pts:
                    d = p["frame"][p["frame"].arm == arm]
                    if not len(d):
                        continue
                    for m in MEASURES:
                        if m not in d.columns or d[m].notna().sum() < 10:
                            continue
                        r = paired_delta(d, b, m)
                        if not r.get("n_pairs", 0):
                            continue
                        ser_rows.append({"author": au, "arm": arm, "train_briefs": p["train_briefs"], "targets_seed": p["targets_seed"],
                                         "point_kind": p["point_kind"], "run": p["run"], "series_platform": p["series_platform"],
                                         "measure": m, "adapter_mean": float(d[m].astype(float).mean()), "base_mean": float(b[m].astype(float).mean()),
                                         **r, "floor_qwen": qfloor[m], "above_floor": abs(r["delta"]) > qfloor[m] if qfloor[m] == qfloor[m] else np.nan})
            # trend of the paired delta over the curve, seed 0 only
            curve = curve_points(pts)
            for arm in arms:
                b = base[base.arm == arm]
                if not len(b):
                    continue
                for m in MEASURES:
                    xs, ys, lv = [], [], []
                    for p in curve:
                        d = p["frame"][p["frame"].arm == arm]
                        if m not in d.columns or d[m].notna().sum() < 10:
                            continue
                        dd = paired_rows(d, b, m)
                        if not len(dd):
                            continue
                        xs.extend([np.log2(p["train_briefs"])] * len(dd)); ys.extend(dd.tolist()); lv.append(p["train_briefs"])
                    if len(set(lv)) >= 2 and len(xs) >= 20:
                        rho, pv = spearmanr(xs, ys)
                        trend_rows.append({"author": au, "arm": arm, "measure": m, "n_levels": len(set(lv)), "n_cells": len(xs),
                                           "rho_delta_vs_log2_briefs": rho, "p": pv})
            # seed replicates: seed 1 against seed 0 at the same training size
            for n in sorted({p["train_briefs"] for p in pts if p["point_kind"] == "series" and p["targets_seed"] == 1}):
                s0 = [p for p in pts if p["point_kind"] == "series" and p["train_briefs"] == n and p["targets_seed"] == 0]
                s1 = [p for p in pts if p["point_kind"] == "series" and p["train_briefs"] == n and p["targets_seed"] == 1]
                if not (s0 and s1):
                    continue
                for arm in arms:
                    x = s1[0]["frame"][s1[0]["frame"].arm == arm]; y = s0[0]["frame"][s0[0]["frame"].arm == arm]
                    if not len(x) or not len(y):
                        continue
                    for m in MEASURES:
                        if m not in x.columns or x[m].notna().sum() < 10 or y[m].notna().sum() < 10:
                            continue
                        r = paired_delta(x, y, m)
                        if not r.get("n_pairs", 0):
                            continue
                        seed_rows.append({"author": au, "arm": arm, "train_briefs": int(n), "measure": m, "run_seed1": s1[0]["run"],
                                          "run_seed0": s0[0]["run"], "seed1_mean": float(x[m].astype(float).mean()),
                                          "seed0_mean": float(y[m].astype(float).mean()), **r, "floor_qwen": qfloor[m],
                                          "above_floor": abs(r["delta"]) > qfloor[m] if qfloor[m] == qfloor[m] else np.nan})

        ser = pd.DataFrame(ser_rows)
        if len(ser):
            ser["q_bh"] = bh_fdr(ser.p_wilcoxon_briefs.values)
            write_table(ser, os.path.join(out, "size_series.csv"))
        tr = pd.DataFrame(trend_rows)
        if len(tr):
            tr["q_bh"] = bh_fdr(tr.p.values)
            write_table(tr, os.path.join(out, "size_trend.csv"))
            tables.append(("Trend of the adapter-minus-base delta with training briefs, arm A0 (brief-level Spearman against log2 briefs, seed 0 only)",
                           tr[tr.arm == "A0"].round(4)))
        trn = pd.DataFrame(train_rows)
        if len(trn):
            write_table(trn, os.path.join(out, "size_training.csv"))
            tables.append(("Training records at every point of every series", trn.round(4)))
        seedrep = pd.DataFrame(seed_rows, columns=["author", "arm", "train_briefs", "measure", "run_seed1", "run_seed0", "seed1_mean",
                                                   "seed0_mean", "n_pairs", "n_briefs", "delta", "ci_low", "ci_high",
                                                   "p_wilcoxon_briefs", "floor_qwen", "above_floor"])
        seedrep["q_bh"] = bh_fdr(seedrep.p_wilcoxon_briefs.values) if len(seedrep) else pd.Series(dtype=float)
        write_table(seedrep, os.path.join(out, "size_seed_replicates.csv"))
        if len(seedrep):
            tables.append(("Two adapters trained on different draws of the same number of briefs (seed 1 minus seed 0, brief-paired)",
                           seedrep[["author", "arm", "train_briefs", "measure", "delta", "ci_low", "ci_high", "floor_qwen", "above_floor", "q_bh"]].round(4)))
        # cross-author comparison at the training sizes more than one author reached
        if len(ser):
            g = ser[(ser.point_kind == "series") & (ser.targets_seed == 0)]
            wide = g.pivot_table(index=["measure", "arm", "train_briefs"], columns="author", values="delta", aggfunc="first")
            wide.columns = [f"delta_{c}" for c in wide.columns]
            wide = wide.reset_index()
            dcols = [c for c in wide.columns if c.startswith("delta_")]
            wide["n_authors"] = wide[dcols].notna().sum(axis=1)
            wide["mean_delta"] = wide[dcols].mean(axis=1, skipna=True)
            wide["floor_qwen"] = wide.measure.map(qfloor)
            gain = wide[wide.n_authors >= 2].sort_values(["measure", "arm", "train_briefs"]).reset_index(drop=True)
            write_table(gain, os.path.join(out, "size_gain_by_author.csv"))
            if len(gain):
                tables.append(("Adapter minus base at the training sizes at least two authors share (one column per author, no pooling beyond the mean)",
                               gain[gain.measure.isin(SHARED_TABLE_MEASURES) & (gain.arm == "A0")].round(4)))
            key = ser[(ser.arm == "A0") & ser.measure.isin(SHARED_TABLE_MEASURES)]
            tables.append(("Adapter minus base at A0 along each series (brief-paired, 95% cluster bootstrap)",
                           key[["author", "train_briefs", "targets_seed", "point_kind", "measure", "delta", "ci_low", "ci_high",
                                "floor_qwen", "above_floor", "q_bh"]].round(4)))
            # figure: one panel per measure, one line per author, seed-1 draws as hollow markers
            fm = [m for m in FIG_MEASURES if len(ser[(ser.measure == m) & (ser.arm == "A0")])]
            if fm:
                ncol = min(3, len(fm)); nrow = int(np.ceil(len(fm) / ncol))
                fig, axes = plt.subplots(nrow, ncol, figsize=(4.6 * ncol, 3.6 * nrow), squeeze=False, layout="constrained")
                colours = {a: c for a, c in zip(series_authors, plt.rcParams["axes.prop_cycle"].by_key()["color"])}
                handles = {}
                for ax, m in zip(axes.ravel(), fm):
                    for au in series_authors:
                        k = ser[(ser.author == au) & (ser.arm == "A0") & (ser.measure == m)].sort_values("train_briefs")
                        c = colours.get(au)
                        line = k[(k.targets_seed == 0) & (k.point_kind == "series")]
                        if len(line):
                            eb = ax.errorbar(line.train_briefs, line.delta, yerr=[line.delta - line.ci_low, line.ci_high - line.delta],
                                             marker="o", ls="-", capsize=2, color=c, label=au, lw=1.2, ms=4)
                            handles.setdefault(au, eb)
                        exist = k[k.point_kind == "existing_adapter"]
                        if len(exist):
                            ax.plot(exist.train_briefs, exist.delta, marker="s", ls="none", color=c, ms=6)
                        rep = k[k.targets_seed == 1]
                        if len(rep):
                            ax.plot(rep.train_briefs, rep.delta, marker="o", ls="none", mfc="none", mec=c, ms=8, mew=1.4)
                    ax.axhline(0, color="k", lw=0.6); ax.set_xscale("log", base=2); ax.set_xlabel("training briefs")
                    ax.set_ylabel("adapter minus base")
                    ax.set_title("\n".join(textwrap.wrap(VARIABLES.get(m, (m,))[0].split("(")[0].strip(), 40)[:2]), fontsize=9)
                    if qfloor.get(m) == qfloor.get(m):
                        ax.axhspan(-qfloor[m], qfloor[m], color="grey", alpha=0.15)
                spare = list(axes.ravel()[len(fm):])
                for ax in spare:
                    ax.axis("off")
                leg_kw = dict(handles=list(handles.values()), labels=list(handles.keys()), fontsize=9, title="author")
                if spare:
                    spare[0].legend(loc="center", **leg_kw)
                else:
                    fig.legend(loc="outside lower center", ncol=max(1, len(handles)), **leg_kw)
                fig.suptitle("Qwen3 4B, arm A0: adapter minus base by training briefs\n"
                             "filled circle = seeded series point, hollow circle = second draw at the same size, "
                             "square = existing full adapter, grey band = replicate floor", fontsize=10)
                figures.append(("Series figure", savefig(fig, os.path.join(out, "size_series.png"))))
        for stale in ("chesterton_size_series.csv", "chesterton_size_trend.csv", "chesterton_size_training.csv", "chesterton_size_series.png"):
            if os.path.exists(os.path.join(out, stale)) and len(ser):
                os.remove(os.path.join(out, stale))
    else:
        notes.append("cells_series.parquet absent: rebuild the master tables to create it.")

    # ---------------------------------------------------------------- (b) frontier arms
    # Every contrast is computed inside one frontier_label, so two hosted models are never
    # merged into one frontier row. The control author keeps its rows and is flagged out of
    # every pooled row.
    fr_rows, fva_rows, fmc_rows = [], [], []
    fr = fva = fmc = pd.DataFrame()
    fr_labels, fr_models, fr_f5_labels = [], {}, []
    tb_passed = (authors.set_index("author").train_briefs_passed if "train_briefs_passed" in authors.columns
                 else pd.Series(dtype=float))
    if len(frontier):
        fr_labels = sorted(frontier.frontier_label.dropna().astype(str).unique())
        if not fr_labels:
            fr_labels = ["unlabelled"]
            frontier = frontier.assign(frontier_label="unlabelled")
        for lab in fr_labels:
            mods = sorted(frontier[frontier.frontier_label == lab].frontier_model.dropna().astype(str).unique())
            fr_models[lab] = mods[0] if mods else "unknown"
            if len(mods) > 1:
                notes.append(f"frontier label {lab} carries more than one model string ({', '.join(mods)}); "
                             f"the tables print the first one.")
            if len(frontier[(frontier.frontier_label == lab) & (frontier.arm == "F5")]):
                fr_f5_labels.append(lab)
        for lab in fr_labels:
            fl = frontier[frontier.frontier_label == lab]
            for au in sorted(fl.author.unique()):
                f = fl[fl.author == au]
                base_run, ad_run = local_run(cells, au, "base"), local_run(cells, au, "adapter")
                if base_run is None or ad_run is None:
                    missing = " and ".join(k for k, v in (("base", base_run), ("adapter", ad_run)) if v is None)
                    notes.append(f"{au}: no Qwen3 4B {missing} run in cells.parquet, so the {lab} frontier rows for "
                                 f"that author are missing the matching local comparison.")
                b = cells[cells.run == base_run] if base_run else cells.iloc[:0]
                a = cells[cells.run == ad_run] if ad_run else cells.iloc[:0]
                f0, f5 = f[f.arm == "F0"], f[f.arm == "F5"]
                comps = [("F0 vs base A0", f0, b[b.arm == "A0"]), ("F0 vs adapter A0", f0, a[a.arm == "A0"])]
                if len(f5):
                    comps += [("F5 vs base A5", f5, b[b.arm == "A5"]), ("F5 vs adapter A0", f5, a[a.arm == "A0"]),
                              ("F5 vs F0", f5, f0)]
                for label, x, y in comps:
                    for m in MEASURES:
                        if m not in x.columns or x[m].notna().sum() < 10 or m not in y.columns or y[m].notna().sum() < 10:
                            continue
                        r = paired_delta(x, y, m)
                        if r.get("n_pairs", 0):
                            fr_rows.append({"frontier_label": lab, "frontier_model": fr_models[lab], "author": au,
                                            "is_control": au == CONTROL_AUTHOR, "contrast": label, "measure": m,
                                            "x_mean": float(x[m].astype(float).mean()), "y_mean": float(y[m].astype(float).mean()),
                                            **r, "floor_qwen": qfloor[m],
                                            "above_floor": abs(r["delta"]) > qfloor[m] if qfloor[m] == qfloor[m] else np.nan})
        # ------------------------------------------------ the two frontier models against each other
        # same briefs and samples, one label minus another, on the authors both labels cover
        for i in range(len(fr_labels)):
            for j in range(i + 1, len(fr_labels)):
                lab_y, lab_x = fr_labels[i], fr_labels[j]
                fx = frontier[(frontier.frontier_label == lab_x) & (frontier.arm == "F0")]
                fy = frontier[(frontier.frontier_label == lab_y) & (frontier.arm == "F0")]
                for au in sorted(set(fx.author.unique()) & set(fy.author.unique())):
                    x, y = fx[fx.author == au], fy[fy.author == au]
                    for m in MEASURES:
                        if m not in x.columns or x[m].notna().sum() < 10 or m not in y.columns or y[m].notna().sum() < 10:
                            continue
                        r = paired_delta(x, y, m)
                        if r.get("n_pairs", 0):
                            fmc_rows.append({"label_x": lab_x, "model_x": fr_models[lab_x], "label_y": lab_y,
                                             "model_y": fr_models[lab_y], "contrast": f"{lab_x} F0 minus {lab_y} F0",
                                             "author": au, "is_control": au == CONTROL_AUTHOR, "measure": m,
                                             "x_mean": float(x[m].astype(float).mean()), "y_mean": float(y[m].astype(float).mean()),
                                             **r, "floor_qwen": qfloor[m],
                                             "above_floor": abs(r["delta"]) > qfloor[m] if qfloor[m] == qfloor[m] else np.nan})
        fr = pd.DataFrame(fr_rows)
        if len(fr):
            fr["q_bh"] = bh_fdr(fr.p_wilcoxon_briefs.values)
            write_table(fr, os.path.join(out, "frontier_contrasts.csv"))
            keyf = fr[fr.measure.isin(["luar_cos_ref", "luar_cos_source", "wegmann_cos_source", "coverage", "truncated"])
                      & fr.contrast.isin(["F0 vs base A0", "F0 vs adapter A0"])]
            tables.append(("Frontier arms against the 4B base and adapter, per hosted model (brief-paired; positive = the frontier arm is higher)",
                           keyf[["frontier_label", "author", "is_control", "contrast", "measure", "delta", "ci_low", "ci_high",
                                 "floor_qwen", "above_floor", "q_bh"]].round(4)))
            # ------------------------------------------------ (b2) frontier F0 against the local adapter, by author
            va = fr[fr.contrast == "F0 vs adapter A0"]
            for lab in fr_labels:
                for m in [mm for mm in MEASURES if len(va[(va.frontier_label == lab) & (va.measure == mm)])]:
                    k = va[(va.frontier_label == lab) & (va.measure == m)].sort_values("author")
                    for r in k.itertuples():
                        fva_rows.append({"frontier_label": lab, "frontier_model": fr_models[lab], "measure": m,
                                         "row_kind": "author", "author": r.author, "is_control": r.is_control,
                                         "train_briefs_passed": float(tb_passed.get(r.author, np.nan)),
                                         "n_authors": np.nan, "n_briefs": r.n_briefs,
                                         "delta_frontier_minus_adapter": r.delta, "ci_low": r.ci_low, "ci_high": r.ci_high,
                                         "floor_qwen": r.floor_qwen, "above_floor": r.above_floor,
                                         "adapter_better": adapter_better(r.delta, r.floor_qwen, m),
                                         "n_authors_adapter_better": np.nan})
                    pool = k[~k.is_control]
                    if not len(pool):
                        continue
                    pt, lo, hi = cluster_bootstrap(pool, "delta", "author", n=1000)
                    n_better = sum(1 for v, fo in zip(pool.delta, pool.floor_qwen) if adapter_better(v, fo, m) is True)
                    fva_rows.append({"frontier_label": lab, "frontier_model": fr_models[lab], "measure": m,
                                     "row_kind": "pooled", "author": "", "is_control": False,
                                     "train_briefs_passed": np.nan, "n_authors": int(len(pool)),
                                     "n_briefs": int(pool.n_briefs.sum()),
                                     "delta_frontier_minus_adapter": pt, "ci_low": lo, "ci_high": hi,
                                     "floor_qwen": qfloor[m],
                                     "above_floor": abs(pt) > qfloor[m] if qfloor[m] == qfloor[m] and pt == pt else np.nan,
                                     "adapter_better": adapter_better(pt, qfloor[m], m),
                                     "n_authors_adapter_better": n_better})
            fva = pd.DataFrame(fva_rows)
            if len(fva):
                write_table(fva, os.path.join(out, "frontier_vs_adapter_by_author.csv"))
                tables.append(("Frontier F0 minus the author's own 4B adapter A0, author by author against corpus size "
                               "(the pooled row is a mean over the usable authors with a bootstrap over authors, the control excluded)",
                               fva[fva.measure.isin(["luar_cos_source", "wegmann_cos_source", "coverage"])][
                                   ["frontier_label", "measure", "row_kind", "author", "is_control", "train_briefs_passed",
                                    "n_authors", "delta_frontier_minus_adapter", "ci_low", "ci_high", "floor_qwen",
                                    "adapter_better", "n_authors_adapter_better"]].round(4)))
        fmc = pd.DataFrame(fmc_rows)
        if len(fmc):
            fmc["q_bh"] = bh_fdr(fmc.p_wilcoxon_briefs.values)
            write_table(fmc, os.path.join(out, "frontier_model_contrast.csv"))
            tables.append(("One hosted model against the other on the same briefs and samples, F0 only (positive = the first model is higher)",
                           fmc[fmc.measure.isin(["luar_cos_source", "wegmann_cos_source", "styledist_cos_source", "coverage", "truncated"])][
                               ["contrast", "author", "measure", "delta", "ci_low", "ci_high", "floor_qwen", "above_floor", "q_bh"]].round(4)))
        # ------------------------------------------------ (b3) figure: the gap against corpus size
        if len(fva):
            fmz = [m for m in FRONTIER_FIG_MEASURES if len(fva[(fva.measure == m) & (fva.row_kind == "author")])]
            if fmz:
                ncol = min(3, len(fmz)); nrow = int(np.ceil(len(fmz) / ncol))
                fig, axes = plt.subplots(nrow, ncol, figsize=(4.6 * ncol, 3.6 * nrow), squeeze=False, layout="constrained")
                pal = plt.rcParams["axes.prop_cycle"].by_key()["color"]
                style = {lab: (pal[i % len(pal)], ["o", "^", "s", "D"][i % 4]) for i, lab in enumerate(fr_labels)}
                handles = {}
                for ax, m in zip(axes.ravel(), fmz):
                    for lab in fr_labels:
                        k = fva[(fva.measure == m) & (fva.row_kind == "author") & (fva.frontier_label == lab)
                                & fva.train_briefs_passed.notna()].sort_values("train_briefs_passed")
                        if not len(k):
                            continue
                        colour, marker = style[lab]
                        for is_ctrl, kk in k.groupby("is_control"):
                            eb = ax.errorbar(kk.train_briefs_passed, kk.delta_frontier_minus_adapter,
                                             yerr=[kk.delta_frontier_minus_adapter - kk.ci_low,
                                                   kk.ci_high - kk.delta_frontier_minus_adapter],
                                             marker=marker, ls="none", capsize=2, color=colour, lw=0.8, ms=5, alpha=0.85,
                                             mfc="none" if is_ctrl else colour)
                            if not is_ctrl:
                                handles.setdefault(f"{lab} ({fr_models[lab]})", eb)
                    ax.axhline(0, color="k", lw=0.6); ax.set_xscale("log", base=2)
                    ax.set_xlabel("training briefs (author corpus)"); ax.set_ylabel("frontier minus adapter")
                    ax.set_title("\n".join(textwrap.wrap(VARIABLES.get(m, (m,))[0].split("(")[0].strip(), 40)[:2]), fontsize=9)
                    if qfloor.get(m) == qfloor.get(m):
                        ax.axhspan(-qfloor[m], qfloor[m], color="grey", alpha=0.15)
                spare = list(axes.ravel()[len(fmz):])
                for ax in spare:
                    ax.axis("off")
                leg_kw = dict(handles=list(handles.values()), labels=list(handles.keys()), fontsize=8, title="frontier model")
                if spare:
                    spare[0].legend(loc="center", **leg_kw)
                else:
                    fig.legend(loc="outside lower center", ncol=max(1, len(handles)), **leg_kw)
                fig.suptitle("Frontier F0 minus the author's own Qwen3 4B adapter A0, by that author's training briefs\n"
                             "one marker series per hosted model, hollow marker = the v1 chunking control, "
                             "grey band = replicate floor, bars = 95% cluster bootstrap over briefs", fontsize=10)
                figures.append(("Frontier figure", savefig(fig, os.path.join(out, "frontier_vs_adapter.png"))))
        for lab in fr_labels:
            fl = frontier[frontier.frontier_label == lab]
            notes.append(f"frontier label {lab} = {fr_models[lab]}, arms {', '.join(sorted(fl.arm.dropna().unique()))}, "
                         f"{fl.author.nunique()} authors; briefs per author: "
                         + ", ".join(f"{au} {n}" for au, n in fl.groupby('author').id.nunique().items()))
    else:
        notes.append("cells_frontier.parquet absent: rebuild the master tables to create it.")

    # ------------------------------------------------------- README strings
    # Every helper below only assembles README text; no table is recomputed here.
    frd = fr if len(fr) else pd.DataFrame(columns=["p_wilcoxon_briefs", "measure", "author", "contrast", "frontier_label"])
    n_trend = int(tr.p.notna().sum()) if len(tr) else 0
    n_ser_fam = int(ser.p_wilcoxon_briefs.notna().sum()) if len(ser) else 0
    n_seed_fam = int(seedrep.p_wilcoxon_briefs.notna().sum()) if len(seedrep) else 0
    n_fr_fam = int(frd.p_wilcoxon_briefs.notna().sum()) if len(frd) else 0
    n_ser_auth = len(series_authors)
    ser_auth = ", ".join(series_authors) if series_authors else "none"
    ser_auth_word = "author" if n_ser_auth == 1 else "authors"
    ser_auth_is = "is" if n_ser_auth == 1 else "are"
    ser_cfg = (f"{sorted(series.family.dropna().unique())[0]} {float(series.params_b.dropna().iloc[0]):g}B" if len(series) else "the local model")
    per_auth = []
    for au in series_authors:
        k = ser[ser.author == au] if len(ser) else pd.DataFrame()
        lv = sorted(k[(k.point_kind == "series") & (k.targets_seed == 0)].train_briefs.unique()) if len(k) else []
        ex = sorted(k[k.point_kind == "existing_adapter"].train_briefs.unique()) if len(k) else []
        ar = ", ".join(sorted(k.arm.unique())) if len(k) else "none"
        rp = sorted(k[k.targets_seed == 1].train_briefs.unique()) if len(k) else []
        per_auth.append(f"{au}: levels {', '.join(str(int(v)) for v in lv) if lv else 'none'}"
                        + (f", plus the existing full adapter at {int(ex[0])}" if ex else ", no existing full adapter")
                        + f", arms {ar}"
                        + (f", second draw at {', '.join(str(int(v)) for v in rp)}" if rp else ", no second draw"))
    per_auth_txt = "; ".join(per_auth) if per_auth else "none"
    n_levels_total = int(ser[(ser.point_kind == "series")].groupby("author").train_briefs.nunique().sum()) if len(ser) else 0
    n_arms_total = int(ser.arm.nunique()) if len(ser) else 0
    plat = sorted({f"{a} {p}" for a, p in ser[ser.point_kind == "series"][["author", "series_platform"]].drop_duplicates().itertuples(index=False)}) if len(ser) else []
    plat_txt = ", ".join(plat) if plat else "none"
    plat_kinds = sorted({p for _, p in ser[ser.point_kind == "series"][["author", "series_platform"]].drop_duplicates().itertuples(index=False)}) if len(ser) else []
    plat_caveat = (f"Generation platform differs across the series ({plat_txt})."
                   if len(plat_kinds) > 1 else
                   f"Every series in this build was generated on one platform ({plat_txt}).")
    epochs_set = sorted({int(round(r.train_examples / r.train_briefs)) for r in trn.itertuples()
                         if r.point_kind == "series" and r.train_examples == r.train_examples and r.train_briefs}) if len(trn) else []
    epochs_txt = " and ".join(str(e) for e in epochs_set) if epochs_set else "an unrecorded number of"
    cache_have = sorted({m for m in CACHE_MEASURES if len(ser) and len(ser[(ser.measure == m) & (ser.point_kind == "series")])})
    cache_only_full = sorted({m for m in CACHE_MEASURES if len(ser) and len(ser[(ser.measure == m) & (ser.point_kind == "existing_adapter")]) and m not in cache_have})
    cache_txt = (", ".join(f"`{m}`" for m in cache_have) if cache_have else "none")
    cache_full_txt = (", ".join(f"`{m}`" for m in cache_only_full) if cache_only_full else "none")
    n_seed_rows = int(len(seedrep))
    n_seed_above = int(seedrep.above_floor.fillna(False).sum()) if len(seedrep) else 0
    seed_auth = ", ".join(sorted(seedrep.author.unique())) if len(seedrep) else "none"
    seed_ns = ", ".join(str(int(v)) for v in sorted(seedrep.train_briefs.unique())) if len(seedrep) else "none"
    seed_read = (f"There are {n_seed_rows} such contrasts, on {seed_auth} at {seed_ns} briefs, and {n_seed_above} of "
                 f"them exceed the replicate floor of their measure."
                 if n_seed_rows else
                 "No author in this build has a second draw at any training size, so the draw is unmeasured here and "
                 "every point on every curve should be read as one draw with unknown spread.")
    gain_ns = ", ".join(str(int(v)) for v in sorted(gain.train_briefs.unique())) if len(gain) else "none"
    gain_max_auth = int(gain.n_authors.max()) if len(gain) else 0
    gain_how = (f"at the training sizes at least two authors reached ({gain_ns}); the only pooling in it is an "
                f"unweighted mean printed next to the author count, which reaches {gain_max_auth}."
                if len(gain) else
                "at the training sizes at least two authors reached. In this build no training size is shared by two "
                "authors, so that table has its header and no rows.")
    gain_read = (f"The cross-author table exists so the shape of the curves can be compared by eye at the shared "
                 f"sizes ({gain_ns}); with at most {gain_max_auth} authors at any size, a shape that repeats is a "
                 f"reason to look again and not an estimate of anything."
                 if len(gain) else
                 "The cross-author table is empty in this build because only one author has a series, so there is no "
                 "shape to compare across authors yet.")
    cache_ser_txt = (f"they are present for {cache_txt}" if cache_have else "none of them is present")
    cache_full_sent = (f"{cache_full_txt} appear only on the existing full adapters, so those rows carry no dose-response."
                       if cache_only_full else "None of them appears on an existing full adapter either.")
    n_fr_auth = int(frontier.author.nunique()) if len(frontier) else 0
    fr_auth_txt = ", ".join(sorted(frontier.author.unique())) if len(frontier) else "none"
    n_fr_cov = int(frd[frd.measure == "coverage"].author.nunique()) if len(frd) else 0
    fr_gate = sorted(runs[(runs.truncation_gate_ok == False) & runs.author.isin(frontier.author.unique())  # noqa: E712
                          & (runs.params_b == 4.0)].run) if len(frontier) else []
    # ---- part (b) counts, every one of them read back off the three frontier tables
    n_fr_lab = len(fr_labels)
    fr_lab_word = "model" if n_fr_lab == 1 else "models"
    fr_model_txt = "; ".join(f"`{lab}` is {fr_models[lab]}" for lab in fr_labels) if fr_labels else "none"
    fr_lab_auth = {lab: sorted(frontier[frontier.frontier_label == lab].author.unique()) for lab in fr_labels}
    fr_lab_counts = "; ".join(f"{lab} covers {len(v)} authors, {len([a for a in v if a != CONTROL_AUTHOR])} of them usable"
                              for lab, v in fr_lab_auth.items()) if fr_labels else "none"
    fr_usable = sorted({a for v in fr_lab_auth.values() for a in v} - {CONTROL_AUTHOR})
    n_fr_usable = len(fr_usable)
    fr_ctrl_in = sorted(lab for lab, v in fr_lab_auth.items() if CONTROL_AUTHOR in v)
    fr_ctrl_txt = (f"`{CONTROL_AUTHOR}` is the v1 chunking control and appears under {', '.join(fr_ctrl_in)}"
                   if fr_ctrl_in else f"`{CONTROL_AUTHOR}` has no frontier rows in this build")
    f5_txt = ", ".join(f"{lab} ({fr_models[lab]})" for lab in fr_f5_labels) if fr_f5_labels else "no label"
    no_f5 = [lab for lab in fr_labels if lab not in fr_f5_labels]
    no_f5_txt = ", ".join(no_f5) if no_f5 else "none"
    n_fr_rows = int(len(frd))
    n_fr_contrasts = int(frd.contrast.nunique()) if len(frd) else 0
    fr_contrast_txt = ", ".join(sorted(frd.contrast.unique())) if len(frd) else "none"
    n_fmc_rows = int(len(fmc))
    n_fmc_fam = int(fmc.p_wilcoxon_briefs.notna().sum()) if len(fmc) else 0
    n_fmc_auth = int(fmc.author.nunique()) if len(fmc) else 0
    fmc_pairs = ", ".join(sorted(fmc.contrast.unique())) if len(fmc) else "none"
    fr_meas = sorted(frd.measure.unique()) if len(frd) else []
    fr_meas_floor = [m for m in fr_meas if qfloor.get(m) == qfloor.get(m)]
    fr_meas_nofloor = [m for m in fr_meas if m not in fr_meas_floor]
    fr_floor_txt = (", ".join(f"`{m}` {qfloor[m]:.4f}" for m in fr_meas_floor) if fr_meas_floor else "none")
    fr_nofloor_txt = (", ".join(f"`{m}`" for m in fr_meas_nofloor) if fr_meas_nofloor else "none")
    fr_missing_meas = [m for m in MEASURES if m not in fr_meas]
    fr_missing_txt = ", ".join(f"`{m}`" for m in fr_missing_meas) if fr_missing_meas else "none"
    fr_judge_have = [m for m in JUDGE_MEASURES if m in fr_meas]
    fr_judge_txt = ", ".join(f"`{m}`" for m in fr_judge_have) if fr_judge_have else "none"

    def _pooled(lab, measure, field):
        if not len(fva):
            return np.nan
        k = fva[(fva.frontier_label == lab) & (fva.measure == measure) & (fva.row_kind == "pooled")]
        return k[field].iloc[0] if len(k) else np.nan

    def _beat_txt(measure):
        out_ = []
        for lab in fr_labels:
            n = _pooled(lab, measure, "n_authors_adapter_better"); na = _pooled(lab, measure, "n_authors")
            if n == n and na == na:
                out_.append(f"{lab} {int(n)} of {int(na)}")
        return "; ".join(out_) if out_ else "no pooled row"

    def _pool_delta_txt(measure):
        out_ = []
        for lab in fr_labels:
            d, lo, hi = (_pooled(lab, measure, "delta_frontier_minus_adapter"), _pooled(lab, measure, "ci_low"),
                         _pooled(lab, measure, "ci_high"))
            if d == d:
                out_.append(f"{lab} {d:+.4f} (95% CI {lo:.4f} to {hi:.4f})")
        return "; ".join(out_) if out_ else "no pooled row"
    beat_luar = _beat_txt("luar_cos_source")
    beat_weg = _beat_txt("wegmann_cos_source")
    beat_sd = _beat_txt("styledist_cos_source")
    pool_luar = _pool_delta_txt("luar_cos_source")
    n_fva_rows = int(len(fva))
    n_fva_pooled = int((fva.row_kind == "pooled").sum()) if len(fva) else 0
    fva_meas = ", ".join(f"`{m}`" for m in sorted(fva[fva.row_kind == "pooled"].measure.unique())) if len(fva) else "none"
    fr_briefs_txt = "; ".join(f"{lab} " + ", ".join(f"{au} {n}" for au, n in
                                                    frontier[frontier.frontier_label == lab].groupby("author").id.nunique().items())
                              for lab in fr_labels) if fr_labels else "none"

    what = f"""
    Two analyses the main tables leave out. Both rest on very few authors, and the author count
    is stated with every claim.

    (a) The within-author data-size series. {n_ser_auth} {ser_auth_word} ({ser_auth}) at {ser_cfg}.
    Each author has adapters trained on a graded number of that author's own training briefs,
    every one of them compared with that author's own {ser_cfg} base run on the same briefs.
    The levels, the existing full adapter and the arms differ by author: {per_auth_txt}. That is
    {n_levels_total} seeded training levels across the series and {n_arms_total} arms in total.
    Each series is one author. The series are reported side by side and are never pooled into a
    single curve, because {n_ser_auth} {ser_auth_word} chosen for other reasons {ser_auth_is} not
    a sample of authors.

    (b) The frontier arms. {n_fr_lab} hosted {fr_lab_word} ({fr_model_txt}) given the brief only
    (F0) or the full conditioning (F5), each compared with the same authors' own Qwen3 4B base
    and adapter runs on the same briefs. {fr_lab_counts}. Across both labels {n_fr_auth} authors
    have frontier rows, {n_fr_usable} of them usable; {fr_ctrl_txt}, and it is flagged by
    `is_control` and held out of every pooled row. The F5 arm was run for {f5_txt} only, so the
    F5 contrasts and the F5-versus-F0 contrast exist for that model alone and the label {no_f5_txt}
    has F0 rows only. Every contrast is computed inside one label and the two models are never
    averaged into a single frontier row. Both models are the everyday chat tier of their
    provider. Neither is the strongest model that provider hosts, so these rows say what a
    cheap hosted model does with these briefs and not what the best available model would do.
    """
    how = f"""
    Brief-paired mean differences with a 1,000-resample cluster bootstrap over briefs, a Wilcoxon
    test on the per-brief means, and the Qwen3 replicate floor of each measure printed beside
    every contrast. BH-FDR is applied within each table separately and each table is its own
    family: {n_ser_fam} tests in the series contrast table, {n_trend} in the trend table,
    {n_seed_fam} in the seed-replicate table, {n_fr_fam} in the frontier contrast table and
    {n_fmc_fam} in the model-against-model table. A q below
    0.05 therefore means survival inside that one table. The programme-wide correction is a
    separate and stricter layer applied in script 22, and no number here has passed it.

    `size_series.csv` carries one row per author, arm, training level and measure. `point_kind`
    separates the seeded series points from the author's existing full adapter, which is
    included as a comparison row labelled by that author's full training-brief count.
    `targets_seed` is 0 for the main nested subsets and 1 for a second draw at the same size.
    The size trend in `size_trend.csv` is a brief-level Spearman correlation between
    log2(training briefs) and the paired delta, fitted on seed-0 points only and on at least two
    levels; a full adapter that sits at the same brief count as a seeded level is dropped from
    that fit so one nominal size is not counted twice. `size_seed_replicates.csv` contrasts the
    seed-1 adapter with the seed-0 adapter at the same training size on the same briefs.
    `size_gain_by_author.csv` puts the seed-0 adapter-minus-base delta of each author side by
    side {gain_how}

    Every adapter along a series was trained for the same {epochs_txt} epochs, so the training
    examples scale with the brief count and the smallest point on each curve is also the least
    trained point. Size and training length are not separable here.

    The eval-cache measures (`per`, `otd_js`, `hapax_w300`) exist only where that cache was
    computed. In the series points {cache_ser_txt}. {cache_full_sent} No F value is quoted for
    `per` anywhere in this folder: proposition echo is close to permutation-invariant and has no
    working floor (script 24), so it appears only as a raw brief-paired difference. `coverage` is
    an LLM-judged adherence reading and `fool_vs_source` is a 2AFC judge rate. Both are
    instrument readings from a judge model, they are relative measures with known failures, and
    neither is a measure of writing quality.

    `series_platform` records where each series was generated: {plat_txt}. The RunPod runs and
    the local runs were produced by the same code verified by hash, and the platform column is
    there so a platform difference can be checked rather than assumed away.

    The frontier tables use the same brief-paired method, computed inside one `frontier_label` at
    a time. `frontier_contrasts.csv` carries {n_fr_rows} rows over {n_fr_contrasts} contrasts
    ({fr_contrast_txt}), with `frontier_label` and `frontier_model` in front of `author` and
    `is_control` marking the v1 chunking control. `frontier_vs_adapter_by_author.csv` holds the
    F0-minus-adapter-A0 delta of each author beside that author's `train_briefs_passed`, so the
    sign of the frontier-versus-local gap can be read against corpus size; it has {n_fva_rows}
    rows, of which {n_fva_pooled} are pooled rows, one per label and measure ({fva_meas}). A
    pooled row is an unweighted mean over the {n_fr_usable} usable authors with a 1,000-resample
    bootstrap over authors, and it counts the authors whose local adapter beats the frontier arm
    by more than the floor, using the measure's direction in the variable dictionary.
    `frontier_model_contrast.csv` puts the two hosted models against each other on the same
    briefs and the same samples at F0: {n_fmc_rows} rows over {n_fmc_auth} authors, {fmc_pairs}.

    Frontier floors are the same Qwen3 replicate floors used everywhere in this folder, printed
    as `floor_qwen` on every row: {fr_floor_txt}. Measures in the frontier tables with no usable
    floor: {fr_nofloor_txt}. Measures in the script's list that have no frontier rows at all:
    {fr_missing_txt}. The judge-scored measures present in the frontier tables are {fr_judge_txt}.
    `coverage` is an LLM judge's reading of how much of the brief is present and `fool_vs_source`
    is a 2AFC rate from LLM judges. Both are instrument readings with known failure modes and
    neither is a measure of writing quality.

    A blank `q_bh` cell means no Wilcoxon was computed for that row, either because the paired
    differences were identically zero or because fewer than six briefs were available.
    """
    reading = f"""
    Each series is one author. Read a series as a dose-response check inside one corpus: a delta
    that grows with training briefs and stays above the replicate floor from some size onward is
    consistent with the cross-author data-floor claim in script 13, and a flat line does not
    refute it. Nothing in one author's curve says anything about another author's curve.
    {gain_read}

    Clearing the floor and surviving the correction are separate verdicts and the table prints
    both. A row above its floor with q above 0.05 is an effect about the size of the measure's
    own generation noise with no test behind it.

    The seeded subsets at each level are nested draws from the same corpus, not independent
    samples, so the curve is one path through the data rather than an average over paths. The
    seed-1 rows are the only measurement of how much of a level's value is the particular draw.
    {seed_read} A difference between two adapters trained on different draws of the same number
    of briefs is a lower bound on the noise in every point of the curve above it. Any step in a
    curve smaller than the matching seed contrast is not a size effect.

    The frontier rows are {n_fr_lab} hosted {fr_lab_word} on {n_fr_auth} authors, read one label
    and one author at a time. {fr_lab_counts}. The pooled rows in
    `frontier_vs_adapter_by_author.csv` are means over {n_fr_usable} authors, which is a small
    number of corpora chosen for other reasons, so the interval on a pooled row is wide and the
    author count beside it is the number to read first. The control author is excluded from every
    pooled row and keeps its own rows under `is_control`.

    On the F0-minus-adapter gap the count that carries the comparison is the number of authors
    whose own 4B adapter beats the hosted model by more than the replicate floor. On
    `luar_cos_source` that is {beat_luar}; on `wegmann_cos_source` {beat_weg}; on
    `styledist_cos_source` {beat_sd}. The pooled F0-minus-adapter delta on `luar_cos_source` is
    {pool_luar}. A count of authors is a count, not a rate for authors in general.

    What these tables can carry is a voice, adherence and length comparison on those authors.
    They cannot carry a construction comparison. The eval-cache measures ({fr_missing_txt}) have
    no frontier rows at all, `per` is the construction row among them, and `rubric_C` is not
    scored for these runs either. `coverage` exists for {n_fr_cov} of the {n_fr_auth} authors.
    Where coverage does exist it is adherence to the brief as scored by an LLM judge, and
    `fool_vs_source` is a 2AFC rate from LLM judges. Neither is a measure of writing quality.
    Both hosted models are chat-tier models rather than the strongest models their providers
    host, so a local adapter beating one of them is not a statement about the frontier of hosted
    models.

    `frontier_model_contrast.csv` compares the two hosted models on the same briefs and samples
    at F0. A difference there is a difference between two everyday models on this task, held to
    the same floors as everything else in the folder.

    Every difference is read against the `floor_qwen` value in its own row. A difference smaller
    than that is inside the twice-generated replicate noise of the measure and is reported as
    within the floor, whatever its q.
    """
    caveats = [f"The series cover {n_ser_auth} {ser_auth_word} ({ser_auth}) at {ser_cfg} only, and each one is a separate result. Nothing here is pooled across authors beyond a printed mean with the author count.",
               f"Per author the levels and arms differ: {per_auth_txt}. A measure missing at a level is missing from that author's trend fit, not imputed.",
               f"Every adapter in a series was trained for the same {epochs_txt} epochs at every level, so the low-brief points are also the low-step points and the two cannot be separated.",
               f"The training subsets at each level are nested draws, so the levels of one series are not independent of each other. Only the seed-1 points measure the draw, and there are {n_seed_rows} such contrasts in this build.",
               f"The eval-cache measures are stored for arm A0 only and only where the cache was computed. In the series points that is {cache_txt}.",
               "`coverage` and `fool_vs_source` are LLM-judge readings, not quality scores; the judge was not rerun for the series points.",
               f"{plat_caveat} The code is the same by hash, and the column is kept so this can be checked rather than assumed away.",
               f"Frontier arms exist for {n_fr_auth} authors across {n_fr_lab} hosted {fr_lab_word} ({fr_model_txt}). {fr_lab_counts}. Coverage and 2AFC rows exist for {n_fr_cov} of those authors; Ministral3 runs carry no judge data anywhere in the programme, so no judge comparison in this folder is cross-family.",
               "Both hosted models are chat-tier models, not the strongest models their providers host, so every frontier row is a reading on that tier and not on the best available hosted model.",
               f"The F5 arm was run for {f5_txt} only. The F5-versus-base-A5, F5-versus-adapter-A0 and F5-versus-F0 contrasts therefore exist for that model alone, and the two labels are not comparable at F5.",
               f"The frontier authors are not a sample. {n_fr_usable} usable corpora are pooled in the pooled rows, the v1 chunking control is held out of them, and the per-author rows are the result.",
               f"Briefs per author differ and are not equalised: {fr_briefs_txt}. An author with few briefs contributes a wide interval to its own row and one equal vote to a pooled row.",
               "Frontier generations were produced through an API with its own sampling defaults; only the brief and the conditioning are matched, not decoding. The model-against-model table shares briefs and samples but not decoding.",
               "Coverage and 2AFC rows for a set of Qwen3 runs were error rows from the 2026-09-09 credit outage and are being rerun (LOG.md); `sui_sin_far_paire6_4b`, the adapter in the sui_sin_far frontier comparison, is one of them, so every judged row that touches it is provisional until the rerun lands.",
               f"Local 4B runs for the frontier authors that exceed the 20 per cent truncation gate in runs.csv are flagged and kept, not excluded: {', '.join(fr_gate) if fr_gate else 'none'}. The frontier-minus-adapter truncation rows are partly a statement about those runs.",
               "Thirteen authors, not multiplicity, is what limits the programme; these two tables sit far below even that."] + notes
    write_readme(out, "25 Within-author data-size series and frontier arms", what, how, reading, caveats=caveats, tables=tables, figures=figures)
    print("->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
