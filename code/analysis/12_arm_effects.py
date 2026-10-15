"""12_arm_effects: what each prompting arm buys, and whether any prompt reaches the adapter.

Within base runs: brief-paired contrasts of A1..A5 against A0 on every measure that is
actually recomputed per arm, per family x size, with cluster-bootstrap intervals over briefs
(author level) and over authors (pooled level), BH-FDR within each family of tests, and the
Qwen3 replicate floor printed beside every contrast.

Then: the arm ranking; the best prompting arm against the adapter A0 (voice and construction);
A4/A5 numeric compliance (shown_dist) and whether obeying the shown numbers helps voice; the
adapter's own arms A0/A1/A5; arm x size x family interactions by mixed model.

Run:  C:\\Python314\\python.exe scripts\\12_arm_effects.py
"""
from __future__ import annotations

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

from lib import (VARIABLES, load_all, bh_fdr, cliffs_delta, cluster_bootstrap, cohens_d,
                 mixed_model, outdir, replicate_floor, savefig, tost, write_readme, write_table)

warnings.filterwarnings("ignore")

T0 = time.time()
OUTD = outdir("12_arm_effects")
ARMS_K = ["A1", "A2", "A3", "A4", "A5"]
ALL_ARMS = ["A0"] + ARMS_K

# ---------------------------------------------------------------- measures
# Only measures that scores.jsonl / coverage.jsonl recompute for every arm can carry an arm
# contrast.  The eval-cache block (per, otd_js, hapax_w300, tau, arti_w, ...) and the rubric
# block were computed on the A0 passage only and broadcast across arms by the master build;
# they are excluded here and the check that establishes that is written to broadcast_check.csv.
EXCLUDED_BROADCAST = ["per", "per_uncapped", "otd_js", "hapax_w300", "tau", "terminal_missing",
                      "events_present", "arti_w", "rfpd_w", "cpd_z", "burst_an_diff",
                      "w1_logpara", "para_cv_words", "rubric_C", "rubric_S"]

# direction: '+' higher is closer to the author, '-' lower is closer, '0' descriptive.
# geo_index is carried as '+': the dictionary records '-' but the authors' own passages score
# highest on it and the generations lowest (see geo_index_direction.csv).
RAW_MEASURES = {
    "luar_cos_source": "+", "luar_cos_ref": "+", "wegmann_cos_source": "+",
    "wegmann_cos_ref": "+", "styledist_cos_source": "+", "luar_cos_ai": "-",
    "geo_index": "+", "delta_own": "-",
    "distinct_3": "+", "rep_4": "-", "sent_echo": "-",
    "template_rate": "-", "staccato_anaphora": "-",
    "coverage": "+", "shown_dist": "-", "truncated": "-",
    "words": "0", "len_ratio": "0",
}
DIST_BASE = ["open_entropy", "pct_short8", "cr_pos", "mattr", "sent_len_cv"]
DIST_MEASURES = {f"d_{m}": "-" for m in DIST_BASE}
MEASURES = {**RAW_MEASURES, **DIST_MEASURES}
RANKABLE = [m for m, d in MEASURES.items() if d in "+-"]
VOICE_CORE = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "styledist_cos_source", "geo_index"]
CONSTR_CORE = ["distinct_3", "sent_echo", "rep_4", "coverage"]


def label(m):
    if m.startswith("d_") and m[2:] in VARIABLES:
        return "|" + VARIABLES[m[2:]][0] + " - author ref|"
    return VARIABLES[m][0] if m in VARIABLES else m


def short(m):
    return m.replace("styledist", "sd").replace("wegmann", "weg").replace("_cos_", " ")


def sd(x):
    """seed from a label, stable across runs"""
    return abs(hash(x)) % (2 ** 31)


# ---------------------------------------------------------------- fast cluster bootstrap
def boot_mean(x, n=2000, seed=0):
    """Bootstrap over the elements of x (one value per brief, or one per author)."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan, np.nan, np.nan, np.nan, 0
    if len(x) == 1:
        return float(x[0]), np.nan, np.nan, np.nan, 1
    rng = np.random.default_rng(seed)
    b = x[rng.integers(0, len(x), size=(n, len(x)))].mean(axis=1)
    return float(x.mean()), float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975)), float(b.std(ddof=1)), int(len(x))


def wilcox_p(x):
    x = np.asarray([v for v in x if v == v], float)
    if len(x) < 3 or np.allclose(x, 0):
        return np.nan
    try:
        return float(stats.wilcoxon(x, zero_method="wilcox", alternative="two-sided").pvalue)
    except Exception:
        return np.nan


def boot_spearman_by_cluster(df, xcol, ycol, cluster, n=400, seed=7):
    """Spearman with a bootstrap over clusters, done on index arrays rather than concatenation."""
    x = df[xcol].to_numpy(float)
    y = df[ycol].to_numpy(float)
    codes, _ = pd.factorize(df[cluster])
    order = np.argsort(codes, kind="stable")
    codes_s = codes[order]
    starts = np.searchsorted(codes_s, np.arange(codes_s.max() + 1), side="left")
    ends = np.searchsorted(codes_s, np.arange(codes_s.max() + 1), side="right")
    idx_by_cluster = [order[s:e] for s, e in zip(starts, ends)]
    k = len(idx_by_cluster)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n):
        pick = rng.integers(0, k, size=k)
        idx = np.concatenate([idx_by_cluster[i] for i in pick])
        r = stats.spearmanr(x[idx], y[idx])[0]
        boots.append(r)
    return float(np.nanquantile(boots, 0.025)), float(np.nanquantile(boots, 0.975))


def main():
    cells, runs, authors, briefs, refs = load_all()

    # ------------------------------------------------------------ 0. broadcast check
    probe_runs = ["chesterton_base4b", "wharton_base8b", "doctorow_base14b", "patrick_v2_basem8b"]
    pr = cells[(~cells.replicate) & (cells.run.isin(probe_runs))]
    bc = []
    for c in EXCLUDED_BROADCAST + ["luar_cos_source", "template_rate", "shown_dist", "coverage", "win_vs_A0"]:
        if c not in pr.columns:
            continue
        p = pr.pivot_table(index=["run", "id", "sample"], columns="arm", values=c, aggfunc="first").dropna(how="all")
        p = p[p.notna().sum(axis=1) >= 2]          # an A0-only column cannot be "identical across arms"
        if not len(p):
            bc.append({"column": c, "rows_checked": 0, "share_identical_across_arms": np.nan,
                       "distinct_values_overall": int(pr[c].nunique()), "verdict": "present on one arm only, undecidable"})
            continue
        share = float((p.nunique(axis=1) <= 1).mean())
        nd = int(pr[c].nunique())
        # nd >= 2 (not > 2): terminal_missing and memo_flag are binary, and a distinct-value
        # count above two would miss a broadcast binary column. nd == 1 means the column is
        # globally constant here, which is not evidence of broadcasting either way.
        bc.append({"column": c, "rows_checked": int(len(p)), "share_identical_across_arms": share,
                   "distinct_values_overall": nd,
                   "verdict": "A0 value broadcast to all arms" if share > 0.99 and nd >= 2 else
                              ("globally constant, undecidable" if nd < 2 else "varies by arm")})
    bcheck = pd.DataFrame(bc).sort_values("share_identical_across_arms", ascending=False)
    write_table(bcheck, os.path.join(OUTD, "broadcast_check.csv"))
    n_broadcast = int((bcheck.verdict == "A0 value broadcast to all arms").sum())
    # the exclusion is decided by the check, not by the constant: if the master table is ever
    # rebuilt so that one of these columns is scored per arm, reinstate it rather than silently
    # keeping it out
    vd = bcheck.set_index("column").verdict.to_dict()
    reinstated = [c for c in EXCLUDED_BROADCAST if vd.get(c) == "varies by arm" and c in VARIABLES]
    for c in reinstated:
        MEASURES[c] = VARIABLES[c][3]
        if VARIABLES[c][3] in "+-" and c not in RANKABLE:
            RANKABLE.append(c)
    still_excluded = [c for c in EXCLUDED_BROADCAST if vd.get(c) == "A0 value broadcast to all arms"]

    # ------------------------------------------------------------ 0b. geo_index direction
    own = refs[refs.group.isin(["source", "ref"])]
    oth = refs[refs.group.astype(str).str.startswith("other:")]
    gen = cells[(~cells.replicate) & (cells.arm == "A0")]
    gd = pd.DataFrame([{"measure": m, "authors_own_passages": float(own[m].mean()),
                        "other_authors_passages": float(oth[m].mean()), "generations_A0": float(gen[m].mean()),
                        "dictionary_direction": VARIABLES[m][3],
                        "direction_used_here": MEASURES.get(m, VARIABLES[m][3])}
                       for m in ["geo_index", "delta_own", "luar_cos_ref", "template_rate"]])
    write_table(gd, os.path.join(OUTD, "geo_index_direction.csv"))
    geo_own = float(gd.loc[gd.measure == "geo_index", "authors_own_passages"].iloc[0])
    geo_oth = float(gd.loc[gd.measure == "geo_index", "other_authors_passages"].iloc[0])
    geo_gen = float(gd.loc[gd.measure == "geo_index", "generations_A0"].iloc[0])

    # ------------------------------------------------------------ 1. derived distances
    cells = cells.copy()
    cells["truncated"] = cells["truncated"].astype(float)
    for m in DIST_BASE:
        ref_mean = own.groupby("author")[m].mean()
        cells[f"d_{m}"] = (cells[m] - cells["author"].map(ref_mean)).abs()
    write_table(own.groupby("author")[DIST_BASE].mean().reset_index(), os.path.join(OUTD, "author_reference_means.csv"))

    meta = runs.set_index("run")[["author", "family", "params_b", "kind", "author_class"]]

    # ------------------------------------------------------------ 2. replicate floors
    fl = []
    for m in MEASURES:
        for arm in ALL_ARMS:
            t = replicate_floor(cells, m, arm=arm)
            for fam, g in t.groupby("family") if len(t) else []:
                fl.append({"measure": m, "arm": arm, "family": fam, "n_pairs": int(len(g)),
                           "floor_abs_mean_diff": float(g.abs_mean_diff.max())})
    floors = pd.DataFrame(fl)
    fam_with_floor = sorted(floors.family.unique()) if len(floors) else []
    fam_all = sorted(cells.family.unique())
    fam_no_floor = [f for f in fam_all if f not in fam_with_floor]
    floors_q = floors[floors.family == "Qwen3"].set_index(["measure", "arm"]).floor_abs_mean_diff.to_dict()
    floors_f = floors.set_index(["family", "measure", "arm"]).floor_abs_mean_diff.to_dict() if len(floors) else {}
    write_table(floors, os.path.join(OUTD, "replicate_floors.csv"))

    def floor_for(m, arm, fam="Qwen3"):
        """The family's own replicate floor for (measure, arm), falling back to its A0 floor, then to Qwen3."""
        for k in ((fam, m, arm), (fam, m, "A0")):
            if k in floors_f and floors_f[k] == floors_f[k]:
                return floors_f[k]
        return floors_q.get((m, arm), floors_q.get((m, "A0"), np.nan))

    # ------------------------------------------------------------ 3. brief-paired arm diffs
    base = cells[(~cells.replicate) & (cells.kind == "base")]
    piv = base.pivot_table(index=["run", "id", "sample"], columns="arm", values=list(MEASURES), aggfunc="mean")

    def by_brief(pivot, m):
        """brief-level means per arm: index (run, id), columns = arms present."""
        return pivot[m].groupby(level=[0, 1]).mean()

    rows = []
    for m in MEASURES:
        bm = by_brief(piv, m)
        if "A0" not in bm.columns:
            continue
        for arm in ARMS_K:
            if arm not in bm.columns:
                continue
            w = bm[[arm, "A0"]].dropna()
            if not len(w):
                continue
            w = w.assign(diff=w[arm] - w["A0"])
            for run, g in w.groupby(level=0):
                v = g["diff"].to_numpy(float)
                if len(v) < 3:
                    continue
                mean, lo, hi, se, k = boot_mean(v, seed=sd(f"{m}|{arm}|{run}"))
                s = np.nanstd(v, ddof=1)
                rows.append({"run": run, "arm": arm, "measure": m, "direction": MEASURES[m],
                             "n_briefs": k, "mean_diff": mean, "ci_low": lo, "ci_high": hi, "se": se,
                             "dz_paired": float(np.nanmean(v) / s) if s > 0 else np.nan,
                             "cohens_d": cohens_d(g[arm].to_numpy(float), g["A0"].to_numpy(float)),
                             "cliffs_delta": cliffs_delta(g[arm].to_numpy(float), g["A0"].to_numpy(float)),
                             "p_wilcoxon": wilcox_p(v)})
    by_author = pd.DataFrame(rows).join(meta, on="run")
    by_author["q_bh"] = bh_fdr(by_author.p_wilcoxon.values)
    by_author["floor_qwen"] = [floor_for(m, a, f) for m, a, f in zip(by_author.measure, by_author.arm, by_author.family)]
    by_author["above_floor"] = by_author.mean_diff.abs() > by_author.floor_qwen
    by_author = by_author[["author", "family", "params_b", "author_class", "run", "arm", "measure", "direction",
                           "n_briefs", "mean_diff", "ci_low", "ci_high", "se", "dz_paired", "cohens_d",
                           "cliffs_delta", "p_wilcoxon", "q_bh", "floor_qwen", "above_floor"]].sort_values(
        ["measure", "arm", "family", "params_b", "author"])
    write_table(by_author, os.path.join(OUTD, "arm_contrasts_by_author.csv"))

    # ------------------------------------------------------------ 4. pooled over authors
    prows = []
    for (fam, pb, arm, m), g in by_author.groupby(["family", "params_b", "arm", "measure"]):
        v = g.mean_diff.values
        mean, lo, hi, se, k = boot_mean(v, seed=sd(f"pool|{fam}|{pb}|{arm}|{m}"))
        f = floor_for(m, arm, fam)
        prows.append({"family": fam, "params_b": pb, "arm": arm, "measure": m, "direction": MEASURES[m],
                      "n_authors": k, "mean_diff": mean, "ci_low": lo, "ci_high": hi, "se": se,
                      "p_wilcoxon": wilcox_p(v), "floor_qwen": f,
                      "above_floor": bool(abs(mean) > f) if f == f else np.nan,
                      "ci_excludes_zero": bool((lo > 0) or (hi < 0)) if lo == lo else np.nan})
    pooled = pd.DataFrame(prows)
    pooled["q_bh"] = bh_fdr(pooled.p_wilcoxon.values)
    pooled["improves"] = np.where(pooled.direction == "+", pooled.mean_diff,
                                  np.where(pooled.direction == "-", -pooled.mean_diff, np.nan))
    pooled = pooled.sort_values(["measure", "family", "params_b", "arm"])
    write_table(pooled, os.path.join(OUTD, "arm_contrasts_pooled.csv"))
    survivors = pooled[(pooled.q_bh < 0.05) & (pooled.above_floor == True)]  # noqa: E712

    # ------------------------------------------------------------ 5. arm ranking
    rk = []
    for (m, fam, pb), g in pooled[pooled.measure.isin(RANKABLE)].groupby(["measure", "family", "params_b"]):
        s = g.set_index("arm").improves.to_dict()
        s["A0"] = 0.0
        order = sorted(s, key=lambda a: -s[a])
        for i, a in enumerate(order):
            rk.append({"measure": m, "family": fam, "params_b": pb, "arm": a, "rank": i + 1,
                       "improvement_vs_A0": s[a], "best": i == 0})
    ranks = pd.DataFrame(rk)

    def rank_sum(sub):
        return (sub.groupby("arm").agg(mean_rank=("rank", "mean"), times_best=("best", "sum"),
                                       n_cells=("rank", "size"), mean_improvement=("improvement_vs_A0", "mean"))
                .reset_index().sort_values("mean_rank"))

    rank_summary = rank_sum(ranks)
    voice_rank = rank_sum(ranks[ranks.measure.isin(VOICE_CORE)])
    constr_rank = rank_sum(ranks[ranks.measure.isin(CONSTR_CORE)])
    write_table(ranks, os.path.join(OUTD, "arm_ranks_by_cell.csv"))
    write_table(rank_summary, os.path.join(OUTD, "arm_rank_summary.csv"))
    write_table(voice_rank, os.path.join(OUTD, "arm_rank_summary_voice.csv"))
    write_table(constr_rank, os.path.join(OUTD, "arm_rank_summary_construction.csv"))

    # ------------------------------------------------------------ 6. best prompt vs adapter A0
    key = ["author", "family", "params_b", "id", "sample"]
    ad = cells[(~cells.replicate) & (cells.kind == "adapter") & (cells.arm == "A0")]
    adk = ad.groupby(key)[list(MEASURES)].mean()
    bak = base.groupby(key + ["arm"])[list(MEASURES)].mean()
    vrows = []
    for m in MEASURES:
        a0 = adk[m].rename("adapter")
        for arm in ALL_ARMS:
            if arm not in bak.index.get_level_values("arm").unique():
                continue
            b = bak.xs(arm, level="arm")[m].rename("baseline")
            j = pd.concat([b, a0], axis=1, join="inner").dropna()
            if not len(j):
                continue
            per_brief = (j["baseline"] - j["adapter"]).groupby(level=[0, 1, 2, 3]).mean()
            for (au, fam, pb), g in per_brief.groupby(level=[0, 1, 2]):
                if len(g) < 3:
                    continue
                mean, lo, hi, se, k = boot_mean(g.values, seed=sd(f"vs|{m}|{arm}|{au}|{fam}|{pb}"))
                vrows.append({"author": au, "family": fam, "params_b": pb, "arm": arm, "measure": m,
                              "direction": MEASURES[m], "n_briefs": k, "base_minus_adapter": mean,
                              "ci_low": lo, "ci_high": hi, "se": se, "p_wilcoxon": wilcox_p(g.values)})
    vs_ad = pd.DataFrame(vrows)
    vs_ad["floor_qwen"] = [floor_for(m, a) for m, a in zip(vs_ad.measure, vs_ad.arm)]
    write_table(vs_ad, os.path.join(OUTD, "prompt_vs_adapter_by_author.csv"))

    prows = []
    for (fam, pb, arm, m), g in vs_ad.groupby(["family", "params_b", "arm", "measure"]):
        v = g.base_minus_adapter.values
        mean, lo, hi, se, k = boot_mean(v, seed=sd(f"vsp|{fam}|{pb}|{arm}|{m}"))
        f = floor_for(m, arm)
        eq = tost(mean, -f, f, se) if (se == se and se > 0 and f == f and f > 0) else np.nan
        sgn = 1.0 if MEASURES[m] == "+" else (-1.0 if MEASURES[m] == "-" else np.nan)
        prows.append({"family": fam, "params_b": pb, "arm": arm, "measure": m, "direction": MEASURES[m],
                      "n_authors": k, "base_minus_adapter": mean, "ci_low": lo, "ci_high": hi, "se": se,
                      "prompt_better": sgn * mean,
                      "prompt_better_lo": sgn * (lo if sgn > 0 else hi), "prompt_better_hi": sgn * (hi if sgn > 0 else lo),
                      "p_wilcoxon": wilcox_p(v), "floor_qwen": f, "p_equivalence_tost": eq,
                      "equivalent_at_floor": bool(eq < 0.05) if eq == eq else np.nan})
    vs_ad_pooled = pd.DataFrame(prows)
    vs_ad_pooled["q_bh"] = bh_fdr(vs_ad_pooled.p_wilcoxon.values)
    vs_ad_pooled = vs_ad_pooled.sort_values(["measure", "family", "params_b", "arm"])
    write_table(vs_ad_pooled, os.path.join(OUTD, "prompt_vs_adapter_pooled.csv"))

    best_tbl = []
    for (fam, pb, m), g in vs_ad_pooled[vs_ad_pooled.measure.isin(RANKABLE)].groupby(["family", "params_b", "measure"]):
        top = g.sort_values("prompt_better", ascending=False).iloc[0]
        f = top.floor_qwen
        best_tbl.append({"family": fam, "params_b": pb, "measure": m, "direction": top.direction,
                         "best_arm": top.arm, "prompt_better_than_adapter": top.prompt_better,
                         "ci_low": top.prompt_better_lo, "ci_high": top.prompt_better_hi,
                         "n_authors": top.n_authors, "floor_qwen": f,
                         "p_equivalence_tost": top.p_equivalence_tost,
                         "verdict": ("prompt beats adapter" if top.prompt_better > f else
                                     ("adapter beats every prompt" if top.prompt_better < -f else
                                      "within the replicate floor"))})
    best_vs_ad = pd.DataFrame(best_tbl).sort_values(["measure", "family", "params_b"])
    write_table(best_vs_ad, os.path.join(OUTD, "best_prompt_vs_adapter.csv"))

    # ------------------------------------------------------------ 7. A4/A5 numeric compliance
    crows = []
    for (fam, arm), g in base.groupby(["family", "arm"]):
        pt, lo, hi = cluster_bootstrap(g, "shown_dist", "id")
        crows.append({"family": fam, "arm": arm, "n_cells": int(len(g)), "n_briefs": int(g.id.nunique()),
                      "shown_dist_mean": pt, "ci_low": lo, "ci_high": hi})
    compl = pd.DataFrame(crows).sort_values(["family", "arm"])
    write_table(compl, os.path.join(OUTD, "compliance_shown_dist.csv"))

    srows = []
    for arm in ["A0", "A4", "A5"]:
        for fam in sorted(base.family.unique()):
            g = base[(base.arm == arm) & (base.family == fam)]
            for m in ["luar_cos_ref", "luar_cos_source", "wegmann_cos_source", "geo_index",
                      "d_open_entropy", "d_pct_short8"]:
                z = g[["author", "id", "shown_dist", m]].dropna()
                if z.id.nunique() < 8:
                    continue
                z = z.copy()
                for c in ["shown_dist", m]:
                    z[c] = z.groupby("author")[c].transform(
                        lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else 0.0)
                r, p = stats.spearmanr(z.shown_dist, z[m])
                lo, hi = boot_spearman_by_cluster(z, "shown_dist", m, "id")
                srows.append({"family": fam, "arm": arm, "measure": m, "n_cells": int(len(z)),
                              "n_briefs": int(z.id.nunique()), "spearman_shown_dist_vs_measure": float(r),
                              "ci_low": lo, "ci_high": hi, "p": float(p)})
    compl_corr = pd.DataFrame(srows)
    if len(compl_corr):
        compl_corr["q_bh"] = bh_fdr(compl_corr.p.values)
    write_table(compl_corr, os.path.join(OUTD, "compliance_vs_voice.csv"))

    # ------------------------------------------------------------ 8. adapter arms
    adp = cells[(~cells.replicate) & (cells.kind == "adapter")]
    pivA = adp.pivot_table(index=["run", "id", "sample"], columns="arm", values=list(MEASURES), aggfunc="mean")
    arows = []
    for m in MEASURES:
        bm = by_brief(pivA, m)
        if "A0" not in bm.columns:
            continue
        for arm in ARMS_K:
            if arm not in bm.columns:
                continue
            w = bm[[arm, "A0"]].dropna()
            if not len(w):
                continue
            w = w.assign(diff=w[arm] - w["A0"])
            for run, g in w.groupby(level=0):
                v = g["diff"].to_numpy(float)
                if len(v) < 3:
                    continue
                mean, lo, hi, se, k = boot_mean(v, seed=sd(f"ad|{m}|{arm}|{run}"))
                arows.append({"run": run, "arm": arm, "measure": m, "direction": MEASURES[m], "n_briefs": k,
                              "mean_diff": mean, "ci_low": lo, "ci_high": hi, "se": se,
                              "p_wilcoxon": wilcox_p(v)})
    ad_by_author = pd.DataFrame(arows).join(meta, on="run")
    arows = []
    for (fam, pb, arm, m), g in ad_by_author.groupby(["family", "params_b", "arm", "measure"]):
        v = g.mean_diff.values
        mean, lo, hi, se, k = boot_mean(v, seed=sd(f"adp|{fam}|{pb}|{arm}|{m}"))
        f = floor_for(m, arm)
        arows.append({"family": fam, "params_b": pb, "arm": arm, "measure": m, "direction": MEASURES[m],
                      "n_authors": k, "mean_diff": mean, "ci_low": lo, "ci_high": hi, "se": se,
                      "p_wilcoxon": wilcox_p(v), "floor_qwen": f,
                      "above_floor": bool(abs(mean) > f) if f == f else np.nan})
    adapter_arms = pd.DataFrame(arows)
    adapter_arms["q_bh"] = bh_fdr(adapter_arms.p_wilcoxon.values)
    adapter_arms["improves"] = np.where(adapter_arms.direction == "+", adapter_arms.mean_diff,
                                        np.where(adapter_arms.direction == "-", -adapter_arms.mean_diff, np.nan))
    adapter_arms = adapter_arms.sort_values(["measure", "family", "params_b", "arm"])
    write_table(ad_by_author, os.path.join(OUTD, "adapter_arm_contrasts_by_author.csv"))
    write_table(adapter_arms, os.path.join(OUTD, "adapter_arm_contrasts_pooled.csv"))

    # ------------------------------------------------------------ 9. mixed models
    mm_rows = []
    md = by_author.copy()
    md["log_params"] = np.log2(md.params_b)
    for m in ["luar_cos_source", "luar_cos_ref", "geo_index", "coverage", "distinct_3", "d_open_entropy"]:
        d = md[md.measure == m][["author", "family", "params_b", "log_params", "arm", "mean_diff"]].dropna()
        d = d.rename(columns={"mean_diff": "diff"})
        _r, tidy = mixed_model(d, "diff ~ C(arm) * log_params + C(arm) * C(family)", groups="author")
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
        write_table(mixed, os.path.join(OUTD, "mixed_models_arm_size_family.csv"))
    n_fit_fail = int((mixed.term == "fit_failed").sum()) if len(mixed) else 0
    n_singular = int(mixed.groupby("measure").re_variance_singular.max().sum()) if len(mixed) else 0
    n_models = int(mixed.measure.nunique()) if len(mixed) else 0
    mm_sig = mixed[(mixed.term.str.contains(":", na=False)) & (mixed.p < 0.05)] if len(mixed) else pd.DataFrame()

    # ------------------------------------------------------------ 10. bootstrap cross-check
    chk = []
    for m in ["luar_cos_source", "geo_index", "coverage"]:
        for run in ["chesterton_base4b", "wharton_base8b", "doctorow_base14b"]:
            g = base[(base.run == run) & (base.arm.isin(["A0", "A5"]))][["id", "arm", m]].dropna()
            if g.id.nunique() < 5:
                continue
            w = g.pivot_table(index="id", columns="arm", values=m, aggfunc="mean").dropna()
            w["diff"] = w["A5"] - w["A0"]
            v, lo, hi, _se, _k = boot_mean(w["diff"].values, seed=1)
            cp, cl, ch = cluster_bootstrap(w.reset_index(), "diff", "id", seed=1)
            chk.append({"measure": m, "run": run, "vectorised_mean": v, "vectorised_lo": lo, "vectorised_hi": hi,
                        "lib_cluster_mean": cp, "lib_cluster_lo": cl, "lib_cluster_hi": ch,
                        "abs_mean_gap": abs(v - cp), "abs_ci_gap": max(abs(lo - cl), abs(hi - ch))})
    bootchk = pd.DataFrame(chk)
    write_table(bootchk, os.path.join(OUTD, "bootstrap_crosscheck.csv"))

    # ------------------------------------------------------------ figures
    figs = []

    def skey(fam, pb):
        return f"{fam} {pb:g}B"

    def panel(ax, sub, m, xarms, vcol, locol, hicol):
        for (fam, pb), g in sub.groupby(["family", "params_b"]):
            g = g.set_index("arm").reindex(xarms)
            x = np.arange(len(xarms))
            ls = "-" if fam == "Qwen3" else "--"
            ax.errorbar(x, g[vcol].values,
                        yerr=[g[vcol].values - g[locol].values, g[hicol].values - g[vcol].values],
                        marker="o", ms=3.5, lw=1.2, ls=ls, capsize=2, label=skey(fam, pb))
        f = floor_for(m, "A0")
        if f == f:
            ax.axhspan(-f, f, color="0.85", zorder=0)
        ax.axhline(0, color="0.4", lw=0.8)
        ax.set_xticks(np.arange(len(xarms)))
        ax.set_xticklabels(xarms, fontsize=8)
        ax.set_title(f"{short(m)} ({MEASURES[m]})", fontsize=8)
        ax.tick_params(labelsize=7)

    def grid(mlist, frame, ylab, title, fname, xarms=ARMS_K, vcol="mean_diff", locol="ci_low", hicol="ci_high"):
        ncol = 3
        nrow = int(np.ceil(len(mlist) / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(3.1 * ncol, 2.5 * nrow), squeeze=False)
        for i, m in enumerate(mlist):
            ax = axes[i // ncol][i % ncol]
            panel(ax, frame[frame.measure == m], m, xarms, vcol, locol, hicol)
            if i % ncol == 0:
                ax.set_ylabel(ylab, fontsize=8)
        for j in range(len(mlist), nrow * ncol):
            axes[j // ncol][j % ncol].axis("off")
        h, lbl = axes[0][0].get_legend_handles_labels()
        fig.legend(h, lbl, loc="lower center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.04))
        fig.suptitle(title, fontsize=9)
        fig.tight_layout(rect=[0, 0.03, 1, 0.93])
        return savefig(fig, os.path.join(OUTD, fname))

    figs.append(("Arm profile, voice",
                 grid(VOICE_CORE + ["delta_own"], pooled, "arm minus A0",
                      "Voice: base prompting arms against A0\n(author-level mean, 95% bootstrap CI over authors; "
                      "grey band = Qwen3 replicate floor)", "arm_profile_voice.png")))
    figs.append(("Arm profile, structure, construction and adherence",
                 grid(["d_open_entropy", "d_pct_short8", "d_mattr", "distinct_3", "sent_echo", "template_rate",
                       "coverage", "shown_dist", "truncated"], pooled, "arm minus A0",
                      "Structure, construction, adherence: base prompting arms against A0\n"
                      "(author-level mean, 95% CI over authors; grey band = Qwen3 replicate floor)",
                      "arm_profile_structure.png")))
    figs.append(("Prompting arms against the adapter",
                 grid(["luar_cos_ref", "wegmann_cos_source", "geo_index", "distinct_3", "sent_echo", "coverage"],
                      vs_ad_pooled, "base arm minus adapter A0",
                      "Every base prompting arm against the adapter at A0\n"
                      "(author-level, 95% CI over authors; zero = the adapter; grey band = Qwen3 floor)",
                      "prompt_vs_adapter.png", xarms=ALL_ARMS, vcol="base_minus_adapter")))
    figs.append(("Adapter arms",
                 grid(["luar_cos_source", "luar_cos_ref", "geo_index", "distinct_3", "coverage", "truncated"],
                      adapter_arms, "adapter arm minus adapter A0",
                      "Conditioning on top of the adapter: adapter arms against adapter A0\n"
                      "(author-level, 95% CI over authors; grey band = Qwen3 floor)", "adapter_arms.png")))

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    ax = axes[0]
    w = 0.35
    for i, fam in enumerate(sorted(compl.family.unique())):
        g = compl[compl.family == fam].set_index("arm").reindex(ALL_ARMS)
        x = np.arange(6) + (i - 0.5) * w
        ax.bar(x, g.shown_dist_mean.values, width=w,
               yerr=[g.shown_dist_mean.values - g.ci_low.values, g.ci_high.values - g.shown_dist_mean.values],
               capsize=2, label=fam)
    ax.set_xticks(np.arange(6))
    ax.set_xticklabels(ALL_ARMS)
    ax.set_ylabel(VARIABLES["shown_dist"][0], fontsize=8)
    ax.set_title("Distance from the shown style numbers, by arm\n(A4 and A5 are the arms that show them;\n"
                 "cluster bootstrap over briefs)", fontsize=9)
    ax.legend(fontsize=8, frameon=False)
    ax.tick_params(labelsize=8)
    ax = axes[1]
    if len(compl_corr):
        sub = compl_corr[compl_corr.arm.isin(["A4", "A5"])].reset_index(drop=True)
        y = np.arange(len(sub))
        ax.errorbar(sub.spearman_shown_dist_vs_measure, y,
                    xerr=[sub.spearman_shown_dist_vs_measure - sub.ci_low, sub.ci_high - sub.spearman_shown_dist_vs_measure],
                    fmt="o", ms=3, capsize=2, lw=1)
        ax.axvline(0, color="0.4", lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{r.family[:4]} {r.arm} {short(r.measure)}" for _, r in sub.iterrows()], fontsize=6)
        ax.set_xlabel("Spearman rho (within-author z), shown_dist vs the measure", fontsize=8)
        ax.set_title("Does hitting the shown numbers go with voice?\n(bootstrap over briefs)", fontsize=9)
        ax.tick_params(labelsize=7)
    fig.tight_layout()
    figs.append(("A4/A5 numeric compliance", savefig(fig, os.path.join(OUTD, "compliance.png"))))

    # ------------------------------------------------------------ README numbers
    def pk(fam, pb, arm, m, col="mean_diff", frame=None):
        f = pooled if frame is None else frame
        r = f[(f.family == fam) & (f.params_b == pb) & (f.arm == arm) & (f.measure == m)]
        return float(r[col].iloc[0]) if len(r) else np.nan

    best_arm_overall = rank_summary.iloc[0]
    best_voice_arm = voice_rank.iloc[0]
    worst_voice_arm = voice_rank.iloc[-1]
    multi = pooled.n_authors >= 3  # the 1.7B cells are one author and are not estimates
    a2 = pooled[multi & (pooled.arm == "A2") & (pooled.measure == "luar_cos_source")]
    a5 = pooled[multi & (pooled.arm == "A5") & (pooled.measure == "luar_cos_source")]
    geo_arms = pooled[(pooled.measure == "geo_index") & (pooled.family == "Qwen3") & (pooled.params_b >= 4)]
    geo_neg = int((geo_arms.mean_diff < 0).sum())
    n_pooled = len(pooled)
    n_sig = int((pooled.q_bh < 0.05).sum())
    n_sig_floor = len(survivors)
    nauth = by_author.groupby(["family", "params_b"]).author.nunique()
    nauth_txt = ", ".join(f"{f} {p:g}B: {n}" for (f, p), n in nauth.items())
    nauth_main = sorted(nauth[(nauth.index.get_level_values(0) == "Qwen3") &
                              (nauth.index.get_level_values(1) >= 4)].unique())

    cq = compl[compl.family == "Qwen3"].set_index("arm")
    a3_gain = float(cq.loc["A3", "shown_dist_mean"] - cq.loc["A0", "shown_dist_mean"])
    a4_gain = float(cq.loc["A4", "shown_dist_mean"] - cq.loc["A0", "shown_dist_mean"])
    a5_gain = float(cq.loc["A5", "shown_dist_mean"] - cq.loc["A0", "shown_dist_mean"])

    def cc(fam, arm, meas):
        r = compl_corr[(compl_corr.family == fam) & (compl_corr.arm == arm) & (compl_corr.measure == meas)]
        return (f"{r.spearman_shown_dist_vs_measure.iloc[0]:+.2f} "
                f"[{r.ci_low.iloc[0]:+.2f}, {r.ci_high.iloc[0]:+.2f}]") if len(r) else "n/a"

    verd = best_vs_ad.verdict.value_counts().to_dict()
    voice_verd = best_vs_ad[best_vs_ad.measure.isin(VOICE_CORE)].verdict.value_counts().to_dict()
    constr_verd = best_vs_ad[best_vs_ad.measure.isin(CONSTR_CORE)].verdict.value_counts().to_dict()
    cov_rows = vs_ad_pooled[(vs_ad_pooled.measure == "coverage") & (vs_ad_pooled.arm == "A0")]
    ad_sig = adapter_arms[(adapter_arms.q_bh < 0.05) & (adapter_arms.above_floor == True)]  # noqa: E712
    ad_a5_luar = adapter_arms[(adapter_arms.arm == "A5") & (adapter_arms.measure == "luar_cos_source")
                              & (adapter_arms.n_authors >= 3)]
    ad_testable = adapter_arms[adapter_arms.p_wilcoxon.notna()]
    ad_strong = adapter_arms[(adapter_arms.n_authors >= 8) & (adapter_arms.above_floor == True) &  # noqa: E712
                             ((adapter_arms.ci_low > 0) | (adapter_arms.ci_high < 0))]
    ad_top = ad_strong.sort_values("p_wilcoxon").head(3)
    ad_top_txt = "; ".join(
        f"{r.arm} on {r.measure} at {r.family} {r.params_b:g}B, {r.mean_diff:+.4f} "
        f"[{r.ci_low:+.4f}, {r.ci_high:+.4f}] against a floor of {r.floor_qwen:.4f} "
        f"({int(r.n_authors)} authors, q = {r.q_bh:.2f})" for _, r in ad_top.iterrows()) or "none"

    def verd_txt(d):
        return ", ".join(f"{v} {k}" for k, v in sorted(d.items(), key=lambda kv: -kv[1]))

    # ---- README-only helpers. Every number in the written piece is read back out of the tables
    # this script wrote; none of it is typed by hand.
    geo_pos = geo_arms[geo_arms.mean_diff > 0]
    geo_pos_txt = ", ".join(f"{r.arm} at {r.params_b:g}B" for _, r in geo_pos.iterrows()) or "none"
    geo_above = int((geo_arms.above_floor == True).sum())  # noqa: E712
    geo_q = int((geo_arms.q_bh < 0.05).sum())
    a2_above = int((a2.above_floor == True).sum())  # noqa: E712
    a2_q = int((a2.q_bh < 0.05).sum())
    a5_above = int((a5.above_floor == True).sum())  # noqa: E712
    a5_q = int((a5.q_bh < 0.05).sum())
    a2_fams = ", ".join(f"{k} {v}" for k, v in a2.groupby("family").size().items())
    rank_ncells = rank_summary.set_index("arm").n_cells.to_dict()
    rank_unequal = sorted(a for a, n in rank_ncells.items() if n != max(rank_ncells.values()))
    most_best = rank_summary.sort_values("times_best", ascending=False).iloc[0]
    constr_counts = best_vs_ad[best_vs_ad.measure.isin(CONSTR_CORE)].groupby("measure").size()
    constr_counts_txt = ", ".join(f"{m} {n}" for m, n in constr_counts.items())
    cov_multi = cov_rows[cov_rows.n_authors >= 3]
    cov_single = cov_rows[cov_rows.n_authors < 3]
    cov_fams = ", ".join(sorted(cov_rows.family.unique())) or "no family"
    cov_lo = float(cov_multi.base_minus_adapter.min()) if len(cov_multi) else float("nan")
    cov_hi = float(cov_multi.base_minus_adapter.max()) if len(cov_multi) else float("nan")
    cov_amin = int(cov_multi.n_authors.min()) if len(cov_multi) else 0
    cov_amax = int(cov_multi.n_authors.max()) if len(cov_multi) else 0
    cov_floor = float(cov_multi.floor_qwen.iloc[0]) if len(cov_multi) else float("nan")
    ministral_floors = floors[floors.family == "Ministral3"]
    dup_pair = sorted(set(by_author.author.unique()) & {"patrick", "patrick_v2"})
    cc_briefs = int(compl_corr.n_briefs.max()) if len(compl_corr) else 0
    cc_family_n = len(compl_corr)
    _base_arms = base.groupby("author").arm.apply(lambda s: set(s))
    _ad_arms = adp.groupby("author").arm.apply(lambda s: set(s))
    no_a1_base = sorted(a for a, v in _base_arms.items() if "A1" not in v)
    ad_wide = sorted(a for a, v in _ad_arms.items() if {"A2", "A3", "A4"} <= v)

    key_tables = [
        ("Arms against A0, pooled over authors: the voice measures at Qwen3 14B",
         pooled[(pooled.family == "Qwen3") & (pooled.params_b == 14) & (pooled.measure.isin(VOICE_CORE))]
         [["arm", "measure", "n_authors", "mean_diff", "ci_low", "ci_high", "floor_qwen", "above_floor", "q_bh"]]),
        ("Arm ranking over all rankable measures and all seven family x size cells (rank 1 of 6 = best)",
         rank_summary),
        ("Arm ranking on the five voice measures only", voice_rank),
        ("Arm ranking on construction and coverage only", constr_rank),
        ("The best prompting arm against the adapter (positive = the prompt is closer to the author)",
         best_vs_ad[["family", "params_b", "measure", "best_arm", "prompt_better_than_adapter", "ci_low",
                     "ci_high", "n_authors", "floor_qwen", "verdict"]].head(45)),
        ("Distance from the shown style numbers, by arm and family",
         compl[["family", "arm", "n_cells", "n_briefs", "shown_dist_mean", "ci_low", "ci_high"]]),
        (f"Conditioning on top of the adapter: the contrasts above their floor with an interval off "
         f"zero on eight or more authors ({len(ad_sig)} of the {len(ad_testable)} testable adapter-arm "
         f"contrasts clear BH-FDR at q < 0.05 within that family)",
         ad_strong.sort_values("p_wilcoxon")[["family", "params_b", "arm", "measure", "n_authors",
                                              "mean_diff", "ci_low", "ci_high", "floor_qwen",
                                              "p_wilcoxon", "q_bh"]].head(30)),
        ("Columns the master build broadcast from A0 to every arm (why they are excluded here)",
         bcheck.head(20)),
        ("Vectorised bootstrap against lib.cluster_bootstrap on the same contrasts", bootchk),
    ]

    what = f"""
    Asks what each prompting arm buys over the bare brief (A0), whether any prompt reaches the
    LoRA adapter, whether showing a model its target style numbers makes it hit them, and
    whether conditioning still helps once the adapter is in place.

    Five arms are contrasted against A0 inside every base run: A1 (+ the author's name), A2
    (+ three retrieved exemplars), A3 (+ the style guide), A4 (+ the quantitative style block),
    A5 (everything). {len(MEASURES)} measures are used, {len(RANKABLE)} of them with a defined
    direction. {n_pooled} pooled contrasts are computed; {n_sig} reach q < 0.05 under BH-FDR
    within that family of {n_pooled}, and {n_sig_floor} of those are also larger than the
    replicate floor of their measure. A contrast that clears both is a difference this design
    can see, not a difference a reader would notice.
    """

    how = f"""
    Data: `data/master/cells.parquet`, non-replicate cells; base runs for the arm contrasts,
    adapter runs for the adapter-arm contrasts. Author reference means for the descriptive
    structure measures come from `data/master/references.parquet` (rows with group `source` or
    `ref`, pooled per author so base and adapter share one anchor).

    Measures. Only measures recomputed for every arm can carry an arm contrast. The eval-cache
    block (per, per_uncapped, otd_js, hapax_w300, tau, terminal_missing, events_present, arti_w,
    rfpd_w, cpd_z, burst_an_diff, w1_logpara, para_cv_words) and the whole rubric block were
    computed on the arm-A0 passage only. In `broadcast_check.csv` {n_broadcast} such columns show
    a single value across the six arms of a (run, brief, sample), while luar_cos_source,
    template_rate, shown_dist, coverage and win_vs_A0 vary; the {len(still_excluded)} the check
    flags are excluded. The check counts a column as identical when the arms it finds do not
    disagree, so a column that carries a value on A0 and nothing on A1 to A5 is flagged the same
    way as one whose A0 value was copied across every arm. The two cases differ in the master
    table and not in what they permit: an arm contrast on any of them is a structural zero either
    way, and no A1 to A5 effect on an eval-cache or rubric measure can be claimed from these
    data. The exclusion is decided by the check at run time, not by a hard-coded list:
    {len(reinstated)} columns were reinstated on this build because the check found them varying
    by arm{(' (' + ', '.join(reinstated) + ')') if reinstated else ''}.

    Five descriptive structure measures (open_entropy, pct_short8, cr_pos, mattr, sent_len_cv)
    have no direction on their own; they are carried as the absolute distance from the author's
    own reference mean (`d_*`, lower = closer to the author). `geo_index` is used with direction
    "+": the variable dictionary records "-", but the authors' own passages score {geo_own:.3f} on
    it, other authors' passages {geo_oth:.3f} and the A0 generations {geo_gen:.3f}, so higher is
    closer to the author (`geo_index_direction.csv`).

    Unit and model. Inside an author the brief is the cluster: an arm contrast is the mean over
    briefs of (arm minus A0), both arms generated from the same brief and sample, with a
    bootstrap over briefs (2000 resamples), Cohen's d and Cliff's delta on the brief means. For
    any claim about a model the author is the unit: the pooled contrast is the mean over authors
    of those per-author values with a bootstrap over authors. Authors per family x size cell:
    {nauth_txt}. The Qwen3 4B/8B/14B cells, which carry the study, have
    {nauth_main[0]} or {nauth_main[-1]} authors; Qwen3 1.7B is patrick_v2 alone and is a single
    point, not an estimate.{" Two of those author rows, " + " and ".join(dup_pair) + ", are the same corpus at two chunk sizes, so the independent corpora number one fewer than the author count in any cell that holds both." if len(dup_pair) > 1 else ""}
    p-values are Wilcoxon signed-rank on the per-brief (author level) or per-author (pooled)
    differences, BH-FDR adjusted within each table separately: a q here means "within this
    table's family", not across the script and not across the programme.

    Bootstrap. The per-contrast interval uses a vectorised resample over briefs rather than
    `lib.cluster_bootstrap`, which would take minutes over {len(by_author)} author-level
    contrasts; `bootstrap_crosscheck.csv` runs both on the same contrasts and the largest gap
    between the two point estimates is
    {bootchk.abs_mean_gap.max() if len(bootchk) else float('nan'):.2e} and between the interval
    endpoints {bootchk.abs_ci_gap.max() if len(bootchk) else float('nan'):.2e}.

    Floors. Every contrast is printed beside a replicate floor for its measure at its arm.
    `replicate_floors.csv` now carries measured floors for {", ".join(fam_with_floor) or "no family"}
    {"(no family is missing one)" if not fam_no_floor else "and none for " + ", ".join(fam_no_floor)},
    {len(ministral_floors)} of them on Ministral3. The `floor_qwen` column beside every contrast
    in this script's other tables holds the row's own family floor where that family has a
    measured pair for the measure (the column name is historical), and the Qwen3 value where it
    does not; a Ministral3 row is therefore judged against a floor measured at 3B whatever its
    size, since the two Ministral pairs are both 3B.
    The Ministral3 floors were measured from two 3B replicate pairs scored on 2026-09-10, so
    there is no measured Ministral3 floor at 8B or 14B in either table.

    Adapter comparison. Each base arm is paired brief-by-brief against the same author's adapter
    at A0, so the difference is a like-for-like swap of mechanism holding the brief fixed.
    Equivalence is `lib.tost` with bounds equal to the measure's replicate floor.

    Mixed models: `diff ~ C(arm) * log2(params) + C(arm) * C(family)` with a random intercept per
    author, one per headline measure. {n_fit_fail} of {n_models} failed to fit and {n_singular} of
    the {n_models - n_fit_fail} that fitted sit at the zero boundary for the author variance
    (`boundary_fit` in the csv), which is a fit that carries no author variance rather than a
    finding of none. With 13 or 14 authors the random-effect variance is descriptive whether or
    not it is at the boundary, so the interaction terms are read as pattern and never as a test.
    """

    reading = f"""
    The unit of replication is the author, not the passage. Every pooled number rests on
    {nauth_main[0]}-{nauth_main[-1]} authors on Qwen3 4B-14B, three on Ministral3 and one at
    Qwen3 1.7B, and the intervals are correspondingly wide: at Qwen3 14B the A5-minus-A0 interval on
    luar_cos_source spans {pk('Qwen3', 14, 'A5', 'luar_cos_source', 'ci_low'):.4f} to
    {pk('Qwen3', 14, 'A5', 'luar_cos_source', 'ci_high'):.4f} around a point estimate of
    {pk('Qwen3', 14, 'A5', 'luar_cos_source'):+.4f}. Three authors carry every Ministral3 cell, so
    the Ministral3 rows are descriptive; a Wilcoxon test on three values cannot reach q < 0.05
    whatever the effect size.

    Read a contrast as real only when its interval excludes zero, its q is below 0.05 within its
    own table, and its magnitude exceeds the floor in the same row. Of {n_pooled} pooled arm
    contrasts, {n_sig_floor} meet all three. They are not evenly spread, and the embedding
    measures and the structural ones do not agree on the sign of what prompting does, which is
    consistent with the two instrument families reading different things rather than with either
    of them being wrong.

    The ranking is a ranking, not a test. `arm_rank_summary.csv` carries no interval, and the
    arms are not ranked on the same set of cells:
    {"every arm is ranked on the same " + str(max(rank_ncells.values())) + " cells" if not rank_unequal else ", ".join(rank_unequal) + " appear in fewer cells than the rest (" + ", ".join(f"{a}: {rank_ncells[a]}" for a in sorted(rank_ncells)) + ")"},
    so a mean-rank difference between two arms with different denominators is not a comparison
    of like with like. The same table disagrees with itself depending on which column is read:
    the lowest mean rank is {best_arm_overall.arm} while the arm that comes first most often is
    {most_best.arm} ({int(most_best.times_best)} of {int(most_best.n_cells)} cells). Neither
    column is a measurement of quality.

    Floors. A contrast smaller than the replicate floor of its measure is within the range of
    generating the same configuration twice, whatever its q. The `floor_qwen` column carries the
    row's own family floor where one is measured and the Qwen3 value otherwise; on Ministral3
    rows the floor is a 3B measurement applied at 8B and 14B as well.

    Judged measures. `coverage` is an LLM judge's count of brief items, so every coverage row in
    this folder is a judge's reading and not a measurement, and the coverage rows for several
    Qwen3 runs were error rows from the 2026-09-09 credit outage that were still being refilled
    when this was written. Ministral3 has no judge data at all, so no coverage row exists for
    that family. Judge measures are relative instruments with known failures and are never read
    here as absolute quality.

    What would overturn this. The arm ranking is computed on pooled author means with A0 pinned
    at zero, so one author with a large opposite effect can move an arm by a rank inside a cell;
    `arm_ranks_by_cell.csv` shows the spread. The best-arm-versus-adapter table selects the
    winning arm on the same authors it then reports, which biases it toward the prompt; the
    unselected per-arm version is `prompt_vs_adapter_pooled.csv` and should be read first. If the
    geo_index sign in the variable dictionary is right and the reference passages are wrong, the
    dissociation reported below reverses into agreement.

    What this does not show. Nothing here speaks to construction as the eval cache measures it
    (PER, OTD, hapax, event order): those exist for A0 only, so "does A5 restate itself more than
    A0" cannot be answered from this master table in either direction. What stands in for
    construction here is {", ".join(CONSTR_CORE)}, and three of those are n-gram measures the
    variable dictionary marks as length-contaminated, so a construction verdict in this folder is
    partly a verdict about passage length. Nor does it speak to judged craft by arm: the rubric
    was run on arm A0, sample 0 alone. The 2AFC column win_vs_A0 does vary by arm and belongs to
    script 16. And nothing here is evidence about absolute quality.
    """

    caveats = [
        f"{n_broadcast} columns in cells.parquet carry no usable arm variation (the eval cache and the whole "
        "rubric block, computed on arm A0 alone). They are excluded from every contrast in this script; see "
        "broadcast_check.csv, whose 'broadcast' verdict covers both a copied A0 value and an A0-only column.",
        f"The `floor_qwen` column in every contrast table here is the row's own family floor where one is measured "
        f"and the Qwen3 value otherwise. The Ministral3 floors ({len(ministral_floors)} rows in replicate_floors.csv) "
        f"come from two 3B replicate pairs scored on 2026-09-10 and are applied to the 8B and 14B rows of that family "
        f"as well, so a Ministral3 above_floor verdict at 8B or 14B rests on a floor measured at another size.",
        "Ministral3 cells rest on three authors (chesterton, doctorow, patrick_v2); their pooled intervals are "
        "bootstraps over three values and their Wilcoxon p-values cannot fall below 0.25.",
        f"`doctorow_basem8b` exceeds the 20% truncation gate and is flagged rather than excluded, and "
        f"`chesterton_paire6_m8b` has a positive probe delta (the adapter changed nothing the probe could "
        f"measure). Both sit inside the Ministral3 8B cells, which already rest on three authors.",
        "The `*_cos_ref` and attribution measures are anchored against a stranger pool of fourteen period authors "
        "for every study author, so contemporary and private authors are positioned against another century; "
        "scripts/23_register_matched_pool.py holds the register-matched repair, which has not been applied here.",
        f"Arm coverage is not balanced across authors: A1 is missing from the base runs of "
        f"{', '.join(no_a1_base) or 'no author'}, and A2, A3 and A4 exist on the adapter runs of "
        f"{', '.join(ad_wide) or 'no author'} only. Rows in the ranking therefore rest on different arm sets "
        f"for different authors, which is why the arms in arm_rank_summary.csv do not share one denominator.",
        "coverage is an LLM-judged measure on sample 0 only, so its brief pairing has half the rows of the other "
        "measures, it is missing entirely for some adapter runs, and it does not exist at all on Ministral3. Rows "
        "for several Qwen3 runs were error rows from the 2026-09-09 credit outage and were being refilled while "
        "this was written, so every coverage number in this folder is provisional until the final rerun.",
        f"`{', '.join(CONSTR_CORE)}` stand in for construction here because the eval-cache construction measures "
        f"exist on arm A0 only. Three of them are n-gram measures the variable dictionary marks length-"
        f"contaminated (distinct_3 correlates with words at rho -0.44), so a construction verdict in this folder "
        f"is partly a length verdict; script 17 holds the length null.",
        "geo_index is used with the opposite sign to the variable dictionary; every geo_index row in this folder "
        "flips if the dictionary is right.",
        "The d_* distances use one reference mean per author, so an author whose own passages are widely spread "
        "on a measure gets a noisier distance than one whose are tight.",
        f"The adapter-arm BH-FDR runs over {len(ad_testable)} testable contrasts, of which "
        f"{int((ad_testable.n_authors < 4).sum())} rest on three authors or fewer and cannot reach q < 0.05 "
        "however large the effect. Nothing in that table survives the correction, so its above-floor rows "
        "are reported with intervals and uncorrected p-values and should be treated as leads, not findings.",
        f"Mixed models: {n_fit_fail} of {n_models} failed to fit and {n_singular} sit at the zero boundary for "
        "the author variance. With 13-14 authors every random-effect variance here is descriptive. "
        "lib.mixed_model was changed on 2026-09-10 to drop the lbfgs optimiser, which returned zero variances "
        "and 1e4 intercept standard errors on these data; running this script against an older lib.py will not "
        "reproduce the mixed-model rows.",
    ]

    extra = f"""
### Headline numbers

- Prompting and structure do not agree about the sign. Across the {len(a2)} family x size cells
  that rest on more than one author ({a2_fams}), A2 and A5 raise luar_cos_source in every one (A2
  {a2.mean_diff.min():+.4f} to {a2.mean_diff.max():+.4f}, {a2_above} of {len(a2)} above the floor
  and {a2_q} at q < 0.05; A5 {a5.mean_diff.min():+.4f} to {a5.mean_diff.max():+.4f}, {a5_above}
  above the floor and {a5_q} at q < 0.05; the floor is {floor_for('luar_cos_source', 'A0'):.4f}),
  while {geo_neg} of the {len(geo_arms)} arm x size cells on Qwen3 4B and above lower geo_index
  ({geo_arms.mean_diff.min():+.3f} to {geo_arms.mean_diff.max():+.3f}, {geo_above} above the
  floor and {geo_q} at q < 0.05; the exceptions are {geo_pos_txt}). The embedding reads the
  prompted passage as closer to the author and the sealed geometry reads it as further away.
  Half of those cells are Ministral3 cells resting on three authors, so this is a statement about
  {int(a2.n_authors.min())} to {int(a2.n_authors.max())} authors per cell, not about either
  family as a whole.
- Arm ranking, which carries no interval and is not a test. Lowest mean rank overall across
  {int(best_arm_overall.n_cells)} measure x cell rankings: **{best_arm_overall.arm}**
  ({best_arm_overall.mean_rank:.2f} of 6, first in {int(best_arm_overall.times_best)}); the arm
  that comes first most often is **{most_best.arm}** ({int(most_best.times_best)}), so the two
  columns of the same table pick different winners. On the {len(VOICE_CORE)} voice measures the lowest mean
  rank is **{best_voice_arm.arm}** ({best_voice_arm.mean_rank:.2f}, first in
  {int(best_voice_arm.times_best)} of {int(best_voice_arm.n_cells)}) and the highest is
  **{worst_voice_arm.arm}** ({worst_voice_arm.mean_rank:.2f}). Arms are not ranked on identical
  cell sets, so the gaps between adjacent arms are not comparisons of like with like.
- Showing a model its target numbers does not bring it closer to them. On Qwen3 the mean distance
  from the shown style numbers is {a4_gain:+.3f} higher at A4 (the arm that shows the numbers)
  than at A0, {a3_gain:+.3f} higher at A3 (the style guide) and {a5_gain:+.3f} at A5. These are
  differences of two point estimates from `compliance_shown_dist.csv`, each bootstrapped over
  briefs with the authors pooled: the unit is the brief, no interval is computed on the
  difference itself, and no replicate floor exists for a between-arm difference of pooled means.
- Compliance with the shown numbers tracks the structure it is built from and not the embedding.
  Within Qwen3 A4 cells, shown_dist correlates with the structural distances it is built from
  (d_pct_short8 {cc('Qwen3', 'A4', 'd_pct_short8')}, d_open_entropy
  {cc('Qwen3', 'A4', 'd_open_entropy')}) and with geo_index in the expected direction
  ({cc('Qwen3', 'A4', 'geo_index')}), while its correlation with the embedding runs the other
  way: luar_cos_ref {cc('Qwen3', 'A4', 'luar_cos_ref')}, so on the arm that shows the numbers the
  passages landing closest to them are the ones LUAR scores furthest from the author. At A5 that
  reverses to {cc('Qwen3', 'A5', 'luar_cos_ref')}. These are brief-level correlations over
  {cc_briefs} briefs with each author standardised separately and the authors then pooled, BH-FDR
  over the {cc_family_n} correlations in `compliance_vs_voice.csv`; the unit is the brief within
  an author, so no author-level interval stands behind them.
- Best prompt against the adapter, over {len(best_vs_ad)} measure x cell rows:
  {verd_txt(verd)}. On voice alone: {verd_txt(voice_verd)}. On construction and coverage:
  {verd_txt(constr_verd)}, spread over {constr_counts_txt}. The construction verdict rests mostly
  on n-gram measures the dictionary marks length-contaminated rather than on coverage, and the
  eval-cache construction measures cannot enter it at all. Read it as: the adapter is ahead on
  the embedding measures, the prompts are ahead on the n-gram and coverage measures.
- The adapter costs brief coverage as an LLM judge counts it. Base A0 minus adapter A0 on
  coverage runs {cov_lo:+.1f} to {cov_hi:+.1f} points over the {len(cov_multi)} cells that rest
  on three or more authors ({cov_amin} to {cov_amax} authors each), against a floor of
  {cov_floor:.2f}. The {len(cov_single)} single-author cell is left out of that range. Every one
  of these cells is {cov_fams}: coverage does not exist on the other family, so this is not a
  statement about adapters in general.
- Conditioning on top of the adapter buys very little. {len(ad_sig)} of the
  {len(ad_testable)} testable adapter-arm contrasts clear BH-FDR at q < 0.05, and the smallest q
  in the whole table is {adapter_arms.q_bh.min():.2f}: the correction runs over
  {len(ad_testable)} tests, {int((ad_testable.n_authors < 4).sum())} of them on three authors or
  fewer. The largest effects that clear their floor with an interval off zero on eight or more
  authors are {ad_top_txt}; where those rows are coverage rows they are a judge's reading of
  brief adherence, not a measurement. A5 on the adapter moves luar_cos_source by
  {ad_a5_luar.mean_diff.min():+.4f} to {ad_a5_luar.mean_diff.max():+.4f} across the multi-author
  cells, at or below the floor of {floor_for('luar_cos_source', 'A5'):.4f}, which is the range
  in which regenerating the same configuration would land.
- {len(mm_sig)} interaction terms in the mixed models reach p < 0.05 without correction, with
  {n_singular} of the {n_models - n_fit_fail} fitted models at the zero boundary for the author
  variance. On {nauth_main[0]}-{nauth_main[-1]} authors these are descriptive, not tests.
"""

    write_readme(OUTD, "12 Arm effects: what prompting buys, and whether it reaches the adapter",
                 what, how, reading, caveats, key_tables, figs, extra)

    print(f"rows: by_author {len(by_author)}, pooled {len(pooled)}, vs_adapter {len(vs_ad_pooled)}, "
          f"adapter_arms {len(adapter_arms)}, mixed {len(mixed)}")
    print(f"floors available for: {fam_with_floor}; missing for: {fam_no_floor}")
    print(f"pooled contrasts q<0.05 and above floor: {n_sig_floor}/{n_pooled}")
    print(f"runtime {time.time() - T0:.1f}s -> {OUTD}")


if __name__ == "__main__":
    main()
