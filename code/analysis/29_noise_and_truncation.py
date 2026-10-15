"""29 noise term, three-state truncation, and brief-level controls.

Promoted 2026-09-12 from the exploratory pass `exploration_2026-09-11/scratch/R14`
(`p1_floor_interval.py`, `p1b_signed_sd.py`, `p2_truncation_three_state.py`,
`p3_best_of_two.py`, `p4_brief_nulls.py`; finding `findings/R14_floor_and_controls.md`).
Reads `data/master/cells.parquet`, the frozen tables of scripts 10 and 20, and the loop layer of
script 28. Nothing outside `data/` and the analysis folders is read.

Four things, each attached to a measure's own replicate floor:

  1. the floor's precision           the two-sample term (a lower bound on run-to-run noise) with
                                     an interval, a two-part variance decomposition, and which
                                     replicate pair supplies each floor
  2. the truncation column split     cut-inside-loop, cut-live-prose, landed-inside-loop, by
                                     family, size and kind, using script 28's loop detector
  3. a best-of-two rejection rule    measured on the two samples already on disk
  4. brief-level nulls               every brief-level statistic in script 20 read against a
                                     replicate-pair null, and a regression-to-the-mean control

Outputs (analysis/29_noise_and_truncation/):
  floor_with_interval.csv       per measure x family: the existing floor, the sampling term, the signed sd
  vc_components.csv             nested variance decomposition: author, brief, configuration, sample
  floor_pair_dominance.csv      each replicate pair's contribution to each floor
  truncation_three_state.csv    rates and adapter-minus-base contrasts on the four states
  best_of_two.csv               truncation, length band and LUAR under four sample-selection rules
  brief_level_nulls.csv         observed brief-level statistics against their replicate nulls
"""
from __future__ import annotations

import os
import sys
import zlib

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from lib import *  # noqa

HERE = outdir("29_noise_and_truncation")

PAIRS = [("base4b", "base4b_r2"), ("chesterton_base4b", "chesterton_base4bc"),
         ("mansfield_base4b", "mansfield_base4b_r2"),
         ("chesterton_basem3b", "chesterton_basem3b_r2"), ("patrick_v2_basem3b", "patrick_v2_basem3b_r2"),
         ("chesterton_base8b", "chesterton_base8b_r2"), ("chesterton_base14b", "chesterton_base14b_r2"),
         ("chesterton_basem8b", "chesterton_basem8b_r2"), ("chesterton_basem14b", "chesterton_basem14b_r2")]
FLOORS = os.path.join(OUT, "10_inventory_integrity", "replicate_floors.csv")
L1 = os.path.join(OUT, "28_loop_and_landing", "layer1_cells.csv.gz")
BRIEFSLOPES = os.path.join(OUT, "20_brief_covariates", "slopes_pooled_over_authors.csv")
BRIEFAGREE = os.path.join(OUT, "20_brief_covariates", "difficulty_agreement.csv")

cells = pd.read_parquet(os.path.join(MASTER, "cells.parquet"))
floors = pd.read_csv(FLOORS)
MEAS = sorted(floors["measure"].unique())
A0 = cells[cells["arm"] == "A0"].copy()


def seed_of(a, b):
    return zlib.crc32((str(a) + "|" + str(b)).encode()) % (2 ** 32)


# ================================================================ 1. floor with interval
def run_pairs(measure, family):
    d = A0[A0.family == family][["run", "author", "family", "params_b", "kind", "id", "sample", measure]].copy()
    d[measure] = pd.to_numeric(d[measure], errors="coerce")
    w = d.pivot_table(index=["run", "author", "family", "params_b", "kind", "id"], columns="sample",
                      values=measure, aggfunc="mean")
    if 0 not in w.columns or 1 not in w.columns:
        return None
    w = w.dropna(subset=[0, 1]).reset_index()
    w["diff"] = w[0] - w[1]
    pr = w.groupby("run")["diff"].agg(["mean", "count"]).reset_index()
    return w, pr


rows = []
for m in MEAS:
    if m not in A0.columns:
        continue
    for fam in ("Qwen3", "Ministral3"):
        rp = run_pairs(m, fam)
        if rp is None:
            continue
        w, pr = rp
        per_run = pr[pr["count"] >= 8]
        if len(per_run) < 5:
            continue
        absd = per_run["mean"].abs().values
        point = float(absd.mean())
        by_run = {r: g["diff"].values for r, g in w.groupby("run") if len(g) >= 8}
        keys = list(by_run)
        rng = np.random.default_rng(seed_of(m, fam))
        boots = []
        for _ in range(1000):
            pick = rng.integers(0, len(keys), size=len(keys))
            vals = []
            for i in pick:
                v = by_run[keys[i]]
                vals.append(abs(v[rng.integers(0, len(v), size=len(v))].mean()))
            boots.append(np.mean(vals))
        lo, hi = float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))
        ex = floors[(floors.measure == m) & (floors.family == fam)]
        if not len(ex):
            continue
        ex = ex.iloc[0]
        exf = float(ex.floor_abs_mean_diff)
        # signed run-level sd of the sample-0 minus sample-1 mean difference
        sd = float(per_run["mean"].std(ddof=1)) if len(per_run) > 2 else np.nan
        rows.append(dict(measure=m, family=fam, construct=str(ex.construct),
                         existing_floor_max=exf, existing_floor_mean_over_pairs=float(ex.mean_abs_mean_diff),
                         n_replicate_pairs=int(ex.n_pairs), between_sample_mean_abs=point,
                         bs_lo=lo, bs_hi=hi, bs_p95_abs=float(np.quantile(absd, 0.95)), bs_max_abs=float(absd.max()),
                         n_runs=int(len(per_run)), n_brief_pairs=int(len(w)), sd_pair_diff=float(w["diff"].std()),
                         bs_signed_sd_run=sd, bs_halfnormal_mean_abs=sd * np.sqrt(2 / np.pi) if sd == sd else np.nan,
                         ratio_floor_over_bs=exf / point if point > 0 else np.nan,
                         ratio_floor_over_signed_sd=exf / sd if sd == sd and sd > 0 else np.nan,
                         floor_pctile_in_bs=float((absd <= exf).mean() * 100),
                         sd_A0_base=float(ex.sd_A0_base), floor_over_sd=float(ex.floor_over_sd),
                         bs_over_sd=point / float(ex.sd_A0_base) if float(ex.sd_A0_base) > 0 else np.nan))
fi = pd.DataFrame(rows).sort_values(["family", "construct", "measure"])
write_table(fi, os.path.join(HERE, "floor_with_interval.csv"), floats=6)
print("floor_with_interval", fi.shape,
      "median floor/signed_sd", round(float(fi.ratio_floor_over_signed_sd.median()), 3),
      "n<1", int((fi.ratio_floor_over_signed_sd < 1).sum()), "of", len(fi))


# ================================================================ 2. variance components
vcrows = []
for m in MEAS:
    if m not in A0.columns:
        continue
    for fam in ("Qwen3", "Ministral3"):
        d = A0[A0.family == fam][["run", "author", "id", "sample", m]].copy()
        d[m] = pd.to_numeric(d[m], errors="coerce")
        d = d.dropna(subset=[m])
        if d.author.nunique() < 3:
            continue
        w = d.pivot_table(index=["run", "author", "id"], columns="sample", values=m, aggfunc="mean")
        if 0 not in w.columns or 1 not in w.columns:
            continue
        w = w.dropna(subset=[0, 1]).reset_index()
        if len(w) < 100:
            continue
        v_sample = float(((w[0] - w[1]) ** 2).mean() / 2.0)
        w["cell"] = (w[0] + w[1]) / 2.0
        gb = w.groupby(["author", "id"])["cell"]
        within = gb.apply(lambda s: s.var(ddof=1) if len(s) > 1 else np.nan).dropna()
        n_cfg = gb.size()
        v_cfg = float(max(within.mean() - v_sample / 2.0, 0.0)) if len(within) else np.nan
        brief = w.groupby(["author", "id"])["cell"].mean().reset_index()
        kbar = float(n_cfg.mean()) if len(n_cfg) else 1.0
        bv = brief.groupby("author")["cell"].apply(lambda s: s.var(ddof=1) if len(s) > 1 else np.nan).dropna()
        v_brief = float(max(bv.mean() - (v_cfg + v_sample / 2.0) / max(kbar, 1.0), 0.0)) if len(bv) else np.nan
        auth = brief.groupby("author")["cell"].mean()
        nb = brief.groupby("author").size().mean()
        v_auth = float(max(auth.var(ddof=1) - (v_brief + (v_cfg + v_sample / 2.0) / max(kbar, 1.0)) / max(nb, 1.0), 0.0)) if len(auth) > 1 else np.nan
        tot = np.nansum([v_auth, v_brief, v_cfg, v_sample])
        vcrows.append(dict(measure=m, family=fam, n_cells=int(len(w)), n_authors=int(w.author.nunique()),
                           n_runs=int(w.run.nunique()), var_author=v_auth, var_brief_in_author=v_brief,
                           var_configuration=v_cfg, var_sample=v_sample, var_total=tot,
                           pct_author=100 * v_auth / tot if tot else np.nan,
                           pct_brief=100 * v_brief / tot if tot else np.nan,
                           pct_config=100 * v_cfg / tot if tot else np.nan,
                           pct_sample=100 * v_sample / tot if tot else np.nan,
                           sd_sample=np.sqrt(v_sample), sd_config=np.sqrt(v_cfg) if v_cfg == v_cfg else np.nan))
vc = pd.DataFrame(vcrows).sort_values(["family", "measure"])
write_table(vc, os.path.join(HERE, "vc_components.csv"), floats=6)
print("vc_components", vc.shape)


# ================================================================ 3. floor pair dominance
dom = []
for m in MEAS:
    if m not in A0.columns:
        continue
    for fam in ("Qwen3", "Ministral3"):
        vals = []
        for A, B in PAIRS:
            x = pd.to_numeric(A0[(A0.run == A)][m], errors="coerce")
            y = pd.to_numeric(A0[(A0.run == B)][m], errors="coerce")
            if len(x) and len(y) and A0.loc[A0.run == A, "family"].iloc[0] == fam:
                vals.append((f"{A} vs {B}", abs(float(x.mean()) - float(y.mean()))))
        if not vals:
            continue
        vals.sort(key=lambda t: t[1], reverse=True)
        top = vals[0][1]
        second = vals[1][1] if len(vals) > 1 else np.nan
        for pair, v in vals:
            dom.append(dict(measure=m, family=fam, pair=pair, abs_mean_diff=v,
                            is_max=(v == top), ratio_to_second=top / second if second and second > 0 else np.nan))
dp = pd.DataFrame(dom)
dom_summary = (dp[dp.is_max].groupby(["measure", "family"])
               .agg(max_pair=("pair", "first"), max_value=("abs_mean_diff", "max"),
                    ratio_to_second=("ratio_to_second", "max"), n_pairs=("pair", "size")).reset_index())
write_table(dp, os.path.join(HERE, "floor_pair_dominance.csv"), floats=6)
print("floor_pair_dominance", dp.shape, "floors with a dominant pair >2x second:",
      int((dom_summary.ratio_to_second > 2).sum()))


# ================================================================ 4. three-state truncation
l1 = pd.read_csv(L1, usecols=["run", "id", "arm", "sample", "loop", "loop_span_words", "loop_share", "ends_mid_sentence"])
d = cells.merge(l1, on=["run", "id", "arm", "sample"], how="left", suffixes=("", "_l1"))
print("three-state merge", len(d), "unmatched loop", int(d.loop.isna().sum()))
d = d[d.loop.notna()].copy()
d["trunc"] = pd.to_numeric(d.truncated, errors="coerce").fillna(0).astype(int)
d["loop"] = pd.to_numeric(d.loop, errors="coerce").fillna(0).astype(int)


def state(r):
    if r.trunc == 1 and r.loop == 1:
        return "cut_inside_loop"
    if r.trunc == 1:
        return "cut_live_prose"
    if r.loop == 1:
        return "landed_inside_loop"
    return "landed_clean"


d["state"] = [state(r) for r in d.itertuples()]
write_table(d[["run", "author", "family", "params_b", "kind", "arm", "id", "sample", "replicate",
               "trunc", "loop", "state", "words", "len_ratio"]],
            os.path.join(HERE, "three_state_cells.csv.gz"), floats=4)

STATES = ["landed_clean", "cut_live_prose", "cut_inside_loop", "landed_inside_loop"]
a0d = d[d.arm == "A0"]
floors_state = {}
for st in STATES + ["trunc"]:
    for fam in ("Qwen3", "Ministral3"):
        col = a0d[st] if st in a0d.columns else (a0d.state == st).astype(int)
        tmp = a0d.assign(_v=col.values if st != "trunc" else a0d.trunc.values)
        vals = []
        for A, B in PAIRS:
            x, y = tmp[tmp.run == A]._v, tmp[tmp.run == B]._v
            if len(x) and len(y) and tmp.loc[tmp.run == A, "family"].iloc[0] == fam:
                vals.append(abs(x.mean() - y.mean()))
        floors_state[(st, fam)] = max(vals) if vals else np.nan

main = a0d[(~a0d.replicate) & a0d.kind.isin(["base", "adapter"])].copy()
brows = []
for (fam, pb, kind), g in main.groupby(["family", "params_b", "kind"], observed=True):
    rec = dict(family=fam, params_b=float(pb), kind=kind, n_cells=len(g), n_authors=g.author.nunique())
    for st in STATES:
        rec[f"rate_{st}"] = float((g.state == st).mean())
    rec["rate_trunc_any"] = float(g.trunc.mean())
    rec["rate_loop_any"] = float(g.loop.mean())
    for st in ["cut_live_prose", "cut_inside_loop"]:
        gg = g.assign(_v=(g.state == st).astype(float))
        pt, lo, hi = cluster_bootstrap(gg, "_v", "author", n=1000)
        rec[f"{st}_lo"], rec[f"{st}_hi"] = lo, hi
    brows.append(rec)
by = pd.DataFrame(brows)

crows = []
for (fam, pb), g in main.groupby(["family", "params_b"], observed=True):
    b, a = g[g.kind == "base"], g[g.kind == "adapter"]
    common = sorted(set(b.author) & set(a.author))
    if not common:
        continue
    for st in STATES + ["trunc_any", "loop_any"]:
        def rate(x, st=st):
            if st == "trunc_any":
                return x.trunc.mean()
            if st == "loop_any":
                return x.loop.mean()
            return (x.state == st).mean()
        per_auth = np.array([rate(a[a.author == au]) - rate(b[b.author == au]) for au in common], float)
        pt, lo, hi = bootstrap_ci(per_auth, n=2000)
        fl = floors_state.get((st if st in STATES else "trunc", fam), np.nan)
        crows.append(dict(family=fam, params_b=float(pb), state=st, n_authors=len(common),
                          base_rate=float(np.mean([rate(b[b.author == au]) for au in common])),
                          adapter_rate=float(np.mean([rate(a[a.author == au]) for au in common])),
                          adapter_minus_base=pt, ci_low=lo, ci_high=hi, floor=fl,
                          in_floor_units=pt / fl if fl == fl and fl > 0 else np.nan,
                          above_floor=bool(abs(pt) > fl) if fl == fl and fl > 0 else None))
con = pd.DataFrame(crows)
by["table"] = "rates_by_config"
con["table"] = "adapter_minus_base"
t3 = pd.concat([by, con], ignore_index=True)
write_table(t3, os.path.join(HERE, "truncation_three_state.csv"), floats=5)
print("truncation_three_state", t3.shape)


# ================================================================ 5. best-of-two rejection
bo = cells[(cells.arm == "A0") & (cells.kind == "adapter") & (~cells.replicate)].copy()
cols = ["truncated", "len_ratio", "luar_cos_source", "luar_cos_ref", "styledist_cos_source", "words"]
for c in cols:
    bo[c] = pd.to_numeric(bo[c], errors="coerce")
w = bo.pivot_table(index=["run", "author", "family", "params_b", "id"], columns="sample",
                   values=cols, aggfunc="mean")
w.columns = [f"{a}_s{b}" for a, b in w.columns]
w = w.reset_index().dropna(subset=["truncated_s0", "truncated_s1", "len_ratio_s0", "len_ratio_s1",
                                   "luar_cos_source_s0", "luar_cos_source_s1"])
print("best_of_two briefs with both samples", len(w), "runs", w.run.nunique(), "authors", w.author.nunique())
LO, HI = 0.6, 1.5


def pick(rule):
    t0, t1 = w.truncated_s0.values, w.truncated_s1.values
    r0, r1 = w.len_ratio_s0.values, w.len_ratio_s1.values
    l0, l1 = w.luar_cos_source_s0.values, w.luar_cos_source_s1.values
    if rule == "reject_truncated":
        return np.where((t0 > 0) & (t1 == 0), 1, 0)
    if rule == "band_len_ratio":
        in0, in1 = (r0 >= LO) & (r0 <= HI), (r1 >= LO) & (r1 <= HI)
        return np.where((~in0) & in1, 1, 0)
    if rule == "max_luar":
        return np.where(l1 > l0, 1, 0)
    return np.zeros(len(w), int)


RULES = ["single_sample0", "reject_truncated", "band_len_ratio", "max_luar", "oracle_both_mean"]
frames = []
for rule in RULES:
    sel = None if rule == "oracle_both_mean" else (np.zeros(len(w), int) if rule == "single_sample0" else pick(rule))
    g = w[["run", "author", "family", "params_b", "id"]].copy()
    for c in cols:
        a, b = w[f"{c}_s0"].values, w[f"{c}_s1"].values
        g[c] = (a + b) / 2.0 if sel is None else np.where(sel == 1, b, a)
    g["rule"] = rule
    g["in_band"] = ((g.len_ratio >= LO) & (g.len_ratio <= HI)).astype(float)
    frames.append(g)
sim = pd.concat(frames, ignore_index=True)
write_table(sim, os.path.join(HERE, "best_of_two_cells.csv.gz"), floats=4)

brows = []
for (fam, pb, rule), g in sim.groupby(["family", "params_b", "rule"], observed=True):
    rec = dict(family=fam, params_b=float(pb), rule=rule, n_authors=g.author.nunique(), n_briefs=len(g))
    for metric in ["truncated", "in_band", "len_ratio", "luar_cos_source", "luar_cos_ref", "words"]:
        am = g.groupby("author")[metric].mean().values
        pt, lo, hi = bootstrap_ci(am, n=2000)
        rec[metric] = pt
        rec[f"{metric}_lo"], rec[f"{metric}_hi"] = lo, hi
    rec["len_ratio_p10"] = float(g.len_ratio.quantile(0.10))
    rec["len_ratio_p90"] = float(g.len_ratio.quantile(0.90))
    brows.append(rec)
by2 = pd.DataFrame(brows)

base = sim[sim.rule == "single_sample0"]
drows = []
for rule in [r for r in RULES if r != "single_sample0"]:
    alt = sim[sim.rule == rule]
    for (fam, pb), gb in base.groupby(["family", "params_b"], observed=True):
        ga = alt[(alt.family == fam) & (alt.params_b == pb)]
        for metric in ["truncated", "in_band", "luar_cos_source", "luar_cos_ref", "styledist_cos_source", "len_ratio"]:
            mb, ma = gb.groupby("author")[metric].mean(), ga.groupby("author")[metric].mean()
            common = mb.index.intersection(ma.index)
            dif = (ma[common] - mb[common]).values
            pt, lo, hi = bootstrap_ci(dif, n=2000)
            drows.append(dict(family=fam, params_b=float(pb), rule=rule, metric=metric,
                              n_authors=len(common), delta_vs_single=pt, ci_low=lo, ci_high=hi))
for rule in [r for r in RULES if r != "single_sample0"]:
    alt = sim[sim.rule == rule]
    for metric in ["truncated", "in_band", "luar_cos_source", "luar_cos_ref", "styledist_cos_source", "len_ratio"]:
        mb = base.groupby(["author", "family", "params_b"])[metric].mean()
        ma = alt.groupby(["author", "family", "params_b"])[metric].mean()
        common = mb.index.intersection(ma.index)
        dif = (ma[common] - mb[common]).values
        pt, lo, hi = bootstrap_ci(dif, n=4000)
        drows.append(dict(family="pooled", params_b=np.nan, rule=rule, metric=metric,
                          n_authors=len(common), delta_vs_single=pt, ci_low=lo, ci_high=hi))
de = pd.DataFrame(drows)
by2["table"] = "levels"
de["table"] = "delta_vs_single_sample0"
bo_out = pd.concat([by2, de], ignore_index=True)
write_table(bo_out, os.path.join(HERE, "best_of_two.csv"), floats=5)
print("best_of_two", bo_out.shape)


# ================================================================ 6. brief-level nulls
PRED = ["source_words", "brief_words", "n_events", "dialogue_share"]
OUTC = ["coverage", "len_ratio", "luar_cos_source", "otd_js", "tau", "terminal_missing", "truncated", "per"]
a0 = cells[cells.arm == "A0"].copy()
for c in OUTC + PRED:
    if c in a0.columns:
        a0[c] = pd.to_numeric(a0[c], errors="coerce")


def brief_level(run):
    g = a0[a0.run == run]
    if not len(g):
        return None
    agg = g.groupby("id").agg({**{c: "mean" for c in OUTC if c in g.columns},
                               **{p: "first" for p in PRED if p in g.columns}})
    agg["author"] = g.author.iloc[0]
    agg["family"] = g.family.iloc[0]
    return agg.reset_index()


nrows = []

# A. slope nulls
obs_slopes = pd.read_csv(BRIEFSLOPES)
null_slope = {}
for A, B in PAIRS:
    da, db = brief_level(A), brief_level(B)
    if da is None or db is None:
        continue
    m = da.merge(db, on="id", suffixes=("_a", "_b"))
    X = m[[f"{p}_a" for p in PRED]].astype(float)
    X = ((X - X.mean()) / X.std(ddof=0)).dropna(axis=1, how="any")
    if X.shape[1] == 0:
        continue
    Xm = np.column_stack([np.ones(len(X)), X.values])
    for o in OUTC:
        ca, cb = f"{o}_a", f"{o}_b"
        if ca not in m.columns or cb not in m.columns:
            continue
        y = (m[ca] - m[cb]).astype(float).values
        ok = np.isfinite(y) & np.isfinite(Xm).all(axis=1)
        if ok.sum() < 12 or np.nanstd(y[ok]) == 0:
            continue
        beta, *_ = np.linalg.lstsq(Xm[ok], y[ok], rcond=None)
        for j, p in enumerate(X.columns):
            sdy = float(np.nanstd(y[ok], ddof=1))
            null_slope.setdefault((o, p[:-2]), []).append(beta[j + 1] / sdy if sdy > 0 else np.nan)

for (o, p), vals in null_slope.items():
    v = np.array([x for x in vals if np.isfinite(x)])
    if not len(v):
        continue
    pt, lo, hi = bootstrap_ci(v, n=2000)
    for kind in ["base", "adapter"]:
        obs = obs_slopes[(obs_slopes.outcome == o) & (obs_slopes.predictor == p) & (obs_slopes.kind == kind)]
        if not len(obs):
            continue
        obs = obs.iloc[0]
        nrows.append(dict(family_of_stat="slope_outcome_on_brief_predictor", statistic=f"{kind}:{o}~{p}",
                          observed=float(obs.slope_std), obs_lo=float(obs.ci_low), obs_hi=float(obs.ci_high),
                          obs_q=float(obs.q_bh), null_replicate=pt, null_lo=lo, null_hi=hi, n_null_pairs=int(len(v)),
                          survives=bool((float(obs.ci_low) > hi) or (float(obs.ci_high) < lo)),
                          source_obs="20_brief_covariates/slopes_pooled_over_authors.csv"))

# B. difficulty agreement ceiling
agree = pd.read_csv(BRIEFAGREE)
ceil = {}
for A, B in PAIRS:
    da, db = brief_level(A), brief_level(B)
    if da is None or db is None:
        continue
    m = da.merge(db, on="id", suffixes=("_a", "_b"))
    for o in OUTC:
        ca, cb = f"{o}_a", f"{o}_b"
        if ca not in m.columns:
            continue
        x, y = m[ca].astype(float).values, m[cb].astype(float).values
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() < 12 or np.nanstd(x[ok]) == 0 or np.nanstd(y[ok]) == 0:
            continue
        r = spearmanr(x[ok], y[ok])[0]
        if np.isfinite(r):
            ceil.setdefault(o, []).append(r)
for o, vals in ceil.items():
    v = np.array(vals)
    pt, lo, hi = bootstrap_ci(v, n=2000)
    for _, r in agree[agree.measure == o].iterrows():
        nrows.append(dict(family_of_stat="brief_difficulty_agreement", statistic=f"{o}:{r.pair_kind}",
                          observed=float(r.mean_spearman), obs_lo=float(r.ci_low), obs_hi=float(r.ci_high),
                          obs_q=np.nan, null_replicate=pt, null_lo=lo, null_hi=hi, n_null_pairs=int(len(v)),
                          survives=bool(float(r.ci_low) > hi),
                          source_obs="20_brief_covariates/difficulty_agreement.csv"))

# C. level-versus-delta (regression to the mean)
obs_rows = []
for o in OUTC:
    per_auth = []
    for (au, fam, pb), g in a0[(~a0.replicate) & a0.kind.isin(["base", "adapter"])].groupby(
            ["author", "family", "params_b"], observed=True):
        if o not in g.columns:
            continue
        b = g[g.kind == "base"].groupby("id")[o].mean()
        ad = g[g.kind == "adapter"].groupby("id")[o].mean()
        idx = b.index.intersection(ad.index)
        x, y = b[idx].values.astype(float), (ad[idx] - b[idx]).values.astype(float)
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() < 10 or np.nanstd(x[ok]) == 0 or np.nanstd(y[ok]) == 0:
            continue
        r = spearmanr(x[ok], y[ok])[0]
        if np.isfinite(r):
            per_auth.append(r)
    if len(per_auth) >= 3:
        pt, lo, hi = bootstrap_ci(np.array(per_auth), n=2000)
        obs_rows.append((o, pt, lo, hi, len(per_auth)))

null_rtm = {}
for A, B in PAIRS:
    da, db = brief_level(A), brief_level(B)
    if da is None or db is None:
        continue
    m = da.merge(db, on="id", suffixes=("_a", "_b"))
    for o in OUTC:
        ca, cb = f"{o}_a", f"{o}_b"
        if ca not in m.columns:
            continue
        x = m[ca].astype(float).values
        y = (m[cb] - m[ca]).astype(float).values
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() < 12 or np.nanstd(x[ok]) == 0 or np.nanstd(y[ok]) == 0:
            continue
        r = spearmanr(x[ok], y[ok])[0]
        if np.isfinite(r):
            null_rtm.setdefault(o, []).append(r)

for o, pt, lo, hi, na in obs_rows:
    v = np.array(null_rtm.get(o, []))
    if not len(v):
        continue
    npt, nlo, nhi = bootstrap_ci(v, n=2000)
    nrows.append(dict(family_of_stat="level_vs_delta_regression_to_mean",
                      statistic=f"rho(base {o}, adapter-base {o})", observed=pt, obs_lo=lo, obs_hi=hi, obs_q=np.nan,
                      null_replicate=npt, null_lo=nlo, null_hi=nhi, n_null_pairs=int(len(v)),
                      survives=bool(pt < nlo or pt > nhi),
                      verdict=("stronger than the null" if hi < nlo else
                               "weaker than the null" if lo > nhi else "indistinguishable from the null"),
                      source_obs="computed here from cells.parquet, matches R6 a5_adapter_loss_vs_brief_difficulty.csv for coverage"))

bl = pd.DataFrame(nrows)
write_table(bl, os.path.join(HERE, "brief_level_nulls.csv"), floats=4)
print("brief_level_nulls", bl.shape)
print(bl.groupby("family_of_stat").size().to_string())


# ================================================================ README
summary = fi[(fi.measure == "luar_cos_source")][["family", "existing_floor_max", "between_sample_mean_abs",
                                                 "bs_signed_sd_run", "ratio_floor_over_signed_sd"]]
three = con[con.state.isin(["trunc_any", "cut_live_prose", "cut_inside_loop"])][
    ["family", "params_b", "state", "base_rate", "adapter_rate", "adapter_minus_base", "ci_low", "ci_high",
     "floor", "in_floor_units", "above_floor"]]
best = de[de.family == "pooled"][["rule", "metric", "delta_vs_single", "ci_low", "ci_high"]]
rtm = bl[bl.family_of_stat == "level_vs_delta_regression_to_mean"][
    ["statistic", "observed", "obs_lo", "obs_hi", "null_replicate", "null_lo", "null_hi", "verdict"]]
write_readme(
    HERE, "29 Noise term, three-state truncation, brief-level controls",
    """
    Four corrections to how the study's own evidence is read. First, the replicate floor is a
    worst case only on the embedding instruments; against the sample-to-sample difference inside a
    single run it sits at about one standard deviation of ordinary sampling noise, and one pair
    supplies a disproportionate share of the floors. Second, the truncation column is two different
    failures: joined to script 28's loop detector it splits into cut-inside-loop, cut-live-prose and
    landed-inside-loop, and the two model families fail in different kinds. Third, rejecting the
    truncated one of the two samples already on disk removes part of the truncation at no measurable
    voice cost. Fourth, every brief-level statistic in script 20 is read against a replicate-pair
    null, which separates the adapter's voice gains (real) from its adherence losses (regression to
    the mean on difficult briefs).
    """,
    """
    The floor's sampling term is the run-level standard deviation of the sample-0 minus sample-1
    mean difference; the floor is the maximum over replicate pairs, so the comparison between them
    says how conservative the floor is. The variance decomposition is a moment-based nested
    decomposition (author > brief > configuration > sample), with negative components truncated at
    zero. The three-state split joins `28_loop_and_landing/layer1_cells.csv.gz` to `cells.parquet`
    on (run, id, arm, sample). Best-of-two resamples the two stored samples under four selection
    rules and one oracle, with authors as the unit. The nulls use the nine replicate pairs as the
    exchangeable baseline. Bootstrap seeds are derived from the measure and family with crc32, so
    the run is reproducible across processes.
    """,
    """
    Read the floor against the sampling term, not as a constant currency: it is generous on the
    embedding instruments and thin on the rate-like and eval-cache measures. Read the truncation
    states separately, not the single flag. The best-of-two numbers are a lower bound at n of 2 and
    cannot report coverage, which exists at sample 0 only. The brief-level nulls are the control the
    workspace needed before quoting any brief-difficulty claim: the adherence losses are regression
    to the mean, the voice gains are not.
    """,
    caveats=[
        "Promoted from an exploratory pass (scratch/R14, 2026-09-11); the between-sample difference is a lower bound on run-to-run noise, not the same quantity as the regeneration floor.",
        "Bootstrap seeds are crc32 of (measure, family) here, where the exploratory pass used Python's salted hash, so intervals can differ from the exploratory numbers in the third decimal while point estimates match.",
        "The variance components are a moment-based decomposition, not a fitted mixed model; coverage and fool_vs_source rows rest on few runs.",
        "Best-of-two is a lower bound at n of 2 and cannot report coverage or any judge measure; the LUAR selection rule is evaluated partly on the instrument it selects on.",
        "The three-state split inherits script 28's loop detector and its threshold.",
        "Thirteen authors bound every pooled statement here.",
    ],
    tables=[("Floor vs sampling term, LUAR-to-source", summary),
            ("Adapter-minus-base by truncation state", three.head(24)),
            ("Best-of-two, pooled deltas vs single sample", best),
            ("Regression-to-the-mean nulls", rtm)])
print("wrote", HERE)
