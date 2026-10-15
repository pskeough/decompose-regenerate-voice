"""18_cross_family.py - Qwen3 vs Ministral 3 overlay on chesterton, doctorow, patrick_v2.

Base A0, adapter A0 and the brief-paired adapter gain at three matched size rungs, with both
families' noise floors; the gap-closing regression of gain on head-room to the author's own
held-out ceiling; TOST equivalence of the two families' adapter endpoints; family x size
interaction on gain; base-level family differences; and the run-level family record (probe
delta, eval loss, truncation, length).

The judged rows are in this overlay too. Both families now carry judged brief coverage and the
2AFC fool rate on the same three authors: the Ministral 3 judge records were produced on
2026-09-10 and 2026-09-11 with the same two judges, the same prompts and the same sample-0
protocol as the Qwen3 records. Coverage and fool_vs_source are therefore treated as ordinary
measures here, brief-paired inside an author and read against each family's own replicate floor.

Reads data/master/* and data/runs/<run>/gens.jsonl (length floor kept as a fallback for the
Ministral replicates; both families now have scored replicate pairs, so it does not fire).
Writes analysis/18_cross_family/ only.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib

matplotlib.use("Agg")

import json
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from lib import (ARM_DESC, DATA, RUNS, VARIABLES, bootstrap_ci, bh_fdr, cliffs_delta, cluster_bootstrap,
                 cohens_d, load_all, main_cells, md_table, mixed_model, outdir, parse_run,
                 replicate_floor, savefig, spearman_ci, tost, write_readme, write_table)

T0 = time.time()
OUTD = outdir("18_cross_family")

CF = ["chesterton", "doctorow", "patrick_v2"]
# matched size rungs: the Ministral 3B run mirrors the Qwen 4B run (CROSS_FAMILY_PLAN.md)
RUNG = {("Qwen3", 4.0): 0, ("Ministral3", 3.0): 0,
        ("Qwen3", 8.0): 1, ("Ministral3", 8.0): 1,
        ("Qwen3", 14.0): 2, ("Ministral3", 14.0): 2}
RUNG_TICK = {0: "4B | 3B", 1: "8B | 8B", 2: "14B | 14B"}
RUNG_NAME = {0: "small", 1: "mid", 2: "large"}
FAMS = ["Qwen3", "Ministral3"]

MEASURES = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "wegmann_cos_ref",
            "styledist_cos_source", "geo_index", "otd_js", "hapax_w300", "per", "per_uncapped",
            "coverage", "fool_vs_source", "len_ratio", "truncated", "words"]
# the two LLM-judged rows, present for both families since the 2026-09-10/11 Ministral judging
JUDGED = ["coverage", "fool_vs_source"]
CEIL_MEASURES = ["luar_cos_ref", "wegmann_cos_ref"]
FIG_VOICE = ["luar_cos_ref", "wegmann_cos_source"]
FIG_CONSTR = ["per", "otd_js"]


def lab(m):
    return VARIABLES[m][0] if m in VARIABLES else m


def direction(m):
    return VARIABLES[m][3] if m in VARIABLES else "0"


def fmt(v, nd=4):
    return "n/a" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{nd}f}"


# ---------------------------------------------------------------- load
cells, runs, authors, briefs, refs = load_all()
cells = cells.copy()
for c in ("truncated", "preface", "replicate"):
    if cells[c].dtype == bool and c != "replicate":
        cells[c] = cells[c].astype(float)

d = main_cells(cells)  # arm A0, non-replicate, base + adapter
cf = d[d.author.isin(CF)].copy()
cf["rung"] = [RUNG.get((f, p), np.nan) for f, p in zip(cf.family, cf.params_b)]
cf_off = cf[cf.rung.isna()].copy()          # Qwen3 1.7B on patrick_v2: no Ministral counterpart
cfp = cf[cf.rung.notna()].copy()
cfp["rung"] = cfp["rung"].astype(int)

# brief means: average the two samples inside a cell so the brief is the unit
BT = cfp.groupby(["author", "family", "params_b", "rung", "kind", "id"], as_index=False)[MEASURES].mean()


# ---------------------------------------------------------------- floors
def seed_floor(cn, measure, family, min_n=8, min_runs=3, only_authors=None):
    """|mean(sample 0) - mean(sample 1)| inside a base run: two seeds, one server, same briefs."""
    sub = cn[(cn.family == family) & (cn.kind == "base") & (cn.arm == "A0") & (~cn.replicate)]
    if only_authors is not None:
        sub = sub[sub.author.isin(only_authors)]
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
    """Length-only floor rows from gens.jsonl for the Ministral replicate pairs; used only when no scored pair exists (both were scored 2026-09-10)."""
    pairs = [("chesterton_basem3b", "chesterton_basem3b_r2"), ("patrick_v2_basem3b", "patrick_v2_basem3b_r2")]
    out = []
    for a, b in pairs:
        rec = {}
        for tag, run in (("a", a), ("b", b)):
            p = os.path.join(RUNS, run, "gens.jsonl")
            if not os.path.exists(p):
                rec = None
                break
            w, lr, tr = [], [], []
            with open(p, encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    if r.get("arm") != "A0":
                        continue
                    w.append(r.get("n_words", np.nan))
                    lr.append(r.get("len_ratio", np.nan))
                    tr.append(1.0 if "truncated" in (r.get("flags") or []) else 0.0)
            rec[tag] = {"words": np.nanmean(w), "len_ratio": np.nanmean(lr), "truncated": np.nanmean(tr), "n": len(w)}
        if rec:
            for m in ("words", "len_ratio", "truncated"):
                out.append({"measure": m, "family": "Ministral3", "pair": f"{a} vs {b}",
                            "n": min(rec["a"]["n"], rec["b"]["n"]), "abs_mean_diff": abs(rec["a"][m] - rec["b"][m])})
    return pd.DataFrame(out)


mlf = ministral_length_floor()
floor_rows = []
pair_rows = []
n_mlf_used = 0
FLOOR_COLS = ["measure", "pair", "family", "n", "abs_mean_diff"]
for m in MEASURES:
    t = replicate_floor(cells, m)
    if not len(t) or "family" not in t.columns:
        t = pd.DataFrame(columns=FLOOR_COLS)
    if len(mlf) and m in set(mlf.measure) and not (len(t) and (t.family == "Ministral3").any()):
        t = pd.concat([t, mlf[mlf.measure == m]], ignore_index=True)   # fallback only while no scored Ministral pair exists
        n_mlf_used += int((mlf.measure == m).sum())
    for _, r in t.iterrows():
        pa = parse_run(str(r.pair).split(" vs ")[0])
        pair_rows.append({"measure": m, "family": r.family, "pair": r.pair,
                          "params_b": pa["params_b"] if pa else np.nan,
                          "n_briefs": int(r.n), "abs_mean_diff": float(r.abs_mean_diff)})
    for fam in FAMS:
        tf = t[t.family == fam] if len(t) else t
        regen = float(tf.abs_mean_diff.max()) if len(tf) else np.nan
        sfl, nruns = seed_floor(cells, m, fam, only_authors=CF)          # matched scope: the overlay authors
        sall, nall = seed_floor(cells, m, fam)                            # every base run in the family
        used = np.nanmax([v for v in (regen, sfl) if v == v]) if any(v == v for v in (regen, sfl)) else np.nan
        floor_rows.append({"measure": m, "family": fam, "floor_regen": regen,
                           "n_regen_pairs": int(len(tf)) if len(tf) else 0,
                           "floor_seed_overlay": sfl, "n_seed_runs_overlay": nruns,
                           "floor_seed_all_runs": sall, "n_seed_runs_all": nall, "floor_used": used})
FLOORS = pd.DataFrame(floor_rows)
FLOOR_PAIRS = pd.DataFrame(pair_rows)
FL = {(r.measure, r.family): r.floor_used for r in FLOORS.itertuples()}


def floor_of(measure, family):
    v = FL.get((measure, family), np.nan)
    return v if v == v else np.nan


def pair_sizes(measure, family):
    """Which size rungs the regeneration pairs for one measure and family actually sit at."""
    s = FLOOR_PAIRS[(FLOOR_PAIRS.measure == measure) & (FLOOR_PAIRS.family == family)]
    sz = sorted(set(s.params_b.dropna()))
    return (", ".join(f"{v:g}B" for v in sz) if sz else "no rung"), int(len(s))


# ---------------------------------------------------------------- paired contrast helper
def paired(bt, measure, sel_left, sel_right):
    """Brief-paired left minus right on brief means; returns (frame, n_briefs)."""
    a = bt[sel_left].set_index("id")[measure]
    b = bt[sel_right].set_index("id")[measure]
    idx = a.index.intersection(b.index)
    fr = pd.DataFrame({"id": idx, "diff": (a.loc[idx] - b.loc[idx]).values}).dropna(subset=["diff"])
    return fr, len(fr)


def paired_stats(fr, raw_left, raw_right):
    if len(fr) < 4:
        return dict(mean=np.nan, lo=np.nan, hi=np.nan, se=np.nan, d=np.nan, delta=np.nan, p=np.nan, n_briefs=len(fr))
    pt, lo, hi = cluster_bootstrap(fr, "diff", "id")
    se = float(fr["diff"].std(ddof=1) / np.sqrt(len(fr)))
    try:
        p = float(stats.wilcoxon(fr["diff"].values).pvalue) if fr["diff"].abs().sum() > 0 else 1.0
    except Exception:
        p = np.nan
    return dict(mean=pt, lo=lo, hi=hi, se=se, d=cohens_d(raw_left, raw_right), delta=cliffs_delta(raw_left, raw_right),
                p=p, n_briefs=len(fr))


# ---------------------------------------------------------------- 1. overlay means
rows = []
for (au, fam, rung, kind), g in BT.groupby(["author", "family", "rung", "kind"]):
    pb = float(cfp[(cfp.author == au) & (cfp.family == fam) & (cfp.rung == rung)].params_b.iloc[0])
    for m in MEASURES:
        pt, lo, hi = cluster_bootstrap(g, m, "id")
        rows.append({"author": au, "family": fam, "params_b": pb, "rung": rung, "rung_name": RUNG_NAME[rung],
                     "kind": kind, "measure": m, "mean": pt, "ci_low": lo, "ci_high": hi,
                     "n_briefs": int(g[m].notna().sum())})
OVERLAY = pd.DataFrame(rows)
write_table(OVERLAY, os.path.join(OUTD, "overlay_means.csv"), floats=5)

# ---------------------------------------------------------------- 2. adapter gain, brief-paired
rows = []
for (au, fam, rung), g in BT.groupby(["author", "family", "rung"]):
    pb = float(cfp[(cfp.author == au) & (cfp.family == fam) & (cfp.rung == rung)].params_b.iloc[0])
    rawsel = (cfp.author == au) & (cfp.family == fam) & (cfp.rung == rung)
    for m in MEASURES:
        fr, n = paired(g, m, g.kind == "adapter", g.kind == "base")
        st = paired_stats(fr, cfp.loc[rawsel & (cfp.kind == "adapter"), m].values,
                          cfp.loc[rawsel & (cfp.kind == "base"), m].values)
        fl = floor_of(m, fam)
        rows.append({"author": au, "family": fam, "params_b": pb, "rung": rung, "rung_name": RUNG_NAME[rung],
                     "measure": m, "direction": direction(m), "gain": st["mean"], "ci_low": st["lo"],
                     "ci_high": st["hi"], "se": st["se"], "cohens_d": st["d"], "cliffs_delta": st["delta"],
                     "p_wilcoxon": st["p"], "n_briefs": st["n_briefs"], "floor": fl,
                     "within_noise": (abs(st["mean"]) < fl) if (st["mean"] == st["mean"] and fl == fl) else np.nan})
GAIN = pd.DataFrame(rows)
GAIN["q_bh"] = bh_fdr(GAIN["p_wilcoxon"].values)
GAIN["fdr_family"] = "adapter_gain_by_author_x_rung_x_family"
write_table(GAIN, os.path.join(OUTD, "adapter_gain_paired.csv"), floats=5)

# the off-ladder Qwen3 1.7B point, reported separately
rows = []
if len(cf_off):
    bt17 = cf_off.groupby(["author", "family", "params_b", "kind", "id"], as_index=False)[MEASURES].mean()
    for (au, fam, pb), g in bt17.groupby(["author", "family", "params_b"]):
        for m in MEASURES:
            fr, n = paired(g, m, g.kind == "adapter", g.kind == "base")
            st = paired_stats(fr, cf_off.loc[(cf_off.kind == "adapter"), m].values,
                              cf_off.loc[(cf_off.kind == "base"), m].values)
            rows.append({"author": au, "family": fam, "params_b": pb, "measure": m, "gain": st["mean"],
                         "ci_low": st["lo"], "ci_high": st["hi"], "n_briefs": st["n_briefs"],
                         "floor": floor_of(m, fam)})
OFFLADDER = pd.DataFrame(rows)
if len(OFFLADDER):
    write_table(OFFLADDER, os.path.join(OUTD, "offladder_qwen17b.csv"), floats=5)

# ---------------------------------------------------------------- 3. cross-family differences
rows_gain, rows_base, rows_tost = [], [], []
for (au, rung), g in BT.groupby(["author", "rung"]):
    gq, gm = g[g.family == "Qwen3"], g[g.family == "Ministral3"]
    rawq = cfp[(cfp.author == au) & (cfp.rung == rung) & (cfp.family == "Qwen3")]
    rawm = cfp[(cfp.author == au) & (cfp.rung == rung) & (cfp.family == "Ministral3")]
    for m in MEASURES:
        # base level, Qwen minus Ministral
        a = gq[gq.kind == "base"].set_index("id")[m]
        b = gm[gm.kind == "base"].set_index("id")[m]
        idx = a.index.intersection(b.index)
        frb = pd.DataFrame({"id": idx, "diff": (a.loc[idx] - b.loc[idx]).values}).dropna(subset=["diff"])
        stb = paired_stats(frb, rawq.loc[rawq.kind == "base", m].values, rawm.loc[rawm.kind == "base", m].values)
        bound = np.nanmax([floor_of(m, "Qwen3"), floor_of(m, "Ministral3")])
        rows_base.append({"author": au, "rung": rung, "rung_name": RUNG_NAME[rung], "measure": m,
                          "base_qwen_minus_ministral": stb["mean"], "ci_low": stb["lo"], "ci_high": stb["hi"],
                          "p_wilcoxon": stb["p"], "n_briefs": stb["n_briefs"], "floor_max": bound,
                          "within_noise": (abs(stb["mean"]) < bound) if (stb["mean"] == stb["mean"] and bound == bound) else np.nan})
        # adapter endpoint, Qwen minus Ministral, plus TOST
        a = gq[gq.kind == "adapter"].set_index("id")[m]
        b = gm[gm.kind == "adapter"].set_index("id")[m]
        idx = a.index.intersection(b.index)
        fra = pd.DataFrame({"id": idx, "diff": (a.loc[idx] - b.loc[idx]).values}).dropna(subset=["diff"])
        sta = paired_stats(fra, rawq.loc[rawq.kind == "adapter", m].values, rawm.loc[rawm.kind == "adapter", m].values)
        p_eq = tost(sta["mean"], -bound, bound, sta["se"]) if (sta["se"] == sta["se"] and sta["se"] > 0 and bound == bound) else np.nan
        rows_tost.append({"author": au, "rung": rung, "rung_name": RUNG_NAME[rung], "measure": m,
                          "adapter_qwen_minus_ministral": sta["mean"], "ci_low": sta["lo"], "ci_high": sta["hi"],
                          "se": sta["se"], "equiv_bound": bound, "p_equivalence": p_eq,
                          "equivalent": (p_eq < 0.05) if p_eq == p_eq else np.nan,
                          "diff_exceeds_bound": (abs(sta["mean"]) > bound) if (sta["mean"] == sta["mean"] and bound == bound) else np.nan,
                          "n_briefs": sta["n_briefs"]})
        # gain difference across families (unpaired across families at the gain level)
        gq_gain = GAIN[(GAIN.author == au) & (GAIN.rung == rung) & (GAIN.family == "Qwen3") & (GAIN.measure == m)]
        gm_gain = GAIN[(GAIN.author == au) & (GAIN.rung == rung) & (GAIN.family == "Ministral3") & (GAIN.measure == m)]
        if len(gq_gain) and len(gm_gain):
            gqv, gmv = float(gq_gain.gain.iloc[0]), float(gm_gain.gain.iloc[0])
            se = float(np.sqrt(np.nansum([gq_gain.se.iloc[0] ** 2, gm_gain.se.iloc[0] ** 2])))
            rows_gain.append({"author": au, "rung": rung, "rung_name": RUNG_NAME[rung], "measure": m,
                              "gain_qwen": gqv, "gain_ministral": gmv, "gain_diff": gqv - gmv, "se_diff": se,
                              "ci_low": gqv - gmv - 1.96 * se, "ci_high": gqv - gmv + 1.96 * se,
                              "floor_max": bound,
                              "within_noise": (abs(gqv - gmv) < bound) if bound == bound else np.nan})
BASEDIFF = pd.DataFrame(rows_base)
BASEDIFF["q_bh"] = bh_fdr(BASEDIFF["p_wilcoxon"].values)
BASEDIFF["fdr_family"] = "base_level_family_difference"
TOSTT = pd.DataFrame(rows_tost)
GAINDIFF = pd.DataFrame(rows_gain)
write_table(BASEDIFF, os.path.join(OUTD, "base_family_diff.csv"), floats=5)
write_table(TOSTT, os.path.join(OUTD, "tost_adapter_endpoints.csv"), floats=5)
write_table(GAINDIFF, os.path.join(OUTD, "cross_family_gain_diff.csv"), floats=5)

# ---------------------------------------------------------------- 3b. the judged rows, both families
# coverage and the 2AFC fool rate exist on sample 0 only, so the brief mean inside a cell is that
# one sample. Both are brief-paired inside an author, and pooled over the three shared authors
# with the (author, id) pair as the cluster. Every row carries its own family's replicate floor.
jrows = []
for m in JUDGED:
    for (au, fam, rung), g in BT.groupby(["author", "family", "rung"]):
        pb = float(cfp[(cfp.author == au) & (cfp.family == fam) & (cfp.rung == rung)].params_b.iloc[0])
        fr, n = paired(g, m, g.kind == "adapter", g.kind == "base")
        if n < 4:
            continue
        st = paired_stats(fr, g.loc[g.kind == "adapter", m].values, g.loc[g.kind == "base", m].values)
        fl = floor_of(m, fam)
        jrows.append({"measure": m, "scope": "author", "author": au, "family": fam, "params_b": pb,
                      "rung": rung, "rung_name": RUNG_NAME[rung], "n_authors": 1, "n_briefs": st["n_briefs"],
                      "base_mean": float(g.loc[g.kind == "base", m].mean()),
                      "adapter_mean": float(g.loc[g.kind == "adapter", m].mean()),
                      "adapter_minus_base": st["mean"], "ci_low": st["lo"], "ci_high": st["hi"],
                      "p_wilcoxon": st["p"], "floor": fl,
                      "within_noise": (abs(st["mean"]) < fl) if (st["mean"] == st["mean"] and fl == fl) else np.nan})
    for (fam, rung), g in BT.groupby(["family", "rung"]):
        pb = float(cfp[(cfp.family == fam) & (cfp.rung == rung)].params_b.iloc[0])
        w = g.pivot_table(index=["author", "id"], columns="kind", values=m, aggfunc="mean")
        if "adapter" not in w.columns or "base" not in w.columns:
            continue
        w = w.dropna(subset=["adapter", "base"])
        if len(w) < 4:
            continue
        fr = pd.DataFrame({"id": [f"{a}|{i}" for a, i in w.index],
                           "diff": (w["adapter"] - w["base"]).values})
        st = paired_stats(fr, w["adapter"].values, w["base"].values)
        fl = floor_of(m, fam)
        jrows.append({"measure": m, "scope": f"pooled over {g.author.nunique()} shared authors",
                      "author": "+".join(sorted(g.author.unique())), "family": fam, "params_b": pb,
                      "rung": rung, "rung_name": RUNG_NAME[rung],
                      "n_authors": int(g.author.nunique()), "n_briefs": st["n_briefs"],
                      "base_mean": float(w["base"].mean()), "adapter_mean": float(w["adapter"].mean()),
                      "adapter_minus_base": st["mean"], "ci_low": st["lo"], "ci_high": st["hi"],
                      "p_wilcoxon": st["p"], "floor": fl,
                      "within_noise": (abs(st["mean"]) < fl) if (st["mean"] == st["mean"] and fl == fl) else np.nan})
JUDGEDIFF = pd.DataFrame(jrows)
JUDGEDIFF["q_bh"] = np.nan
for m, g in JUDGEDIFF.groupby("measure"):
    JUDGEDIFF.loc[g.index, "q_bh"] = bh_fdr(g.p_wilcoxon.values)
JUDGEDIFF["fdr_family"] = "judged_adapter_gain_per_measure"
JUDGEDIFF = JUDGEDIFF.sort_values(["measure", "scope", "family", "rung", "author"]).reset_index(drop=True)
write_table(JUDGEDIFF, os.path.join(OUTD, "judged_adapter_minus_base.csv"), floats=5)
JPOOL = JUDGEDIFF[JUDGEDIFF.scope.str.startswith("pooled")]


def jline(measure, fam):
    s = JPOOL[(JPOOL.measure == measure) & (JPOOL.family == fam)].sort_values("rung")
    return "; ".join(f"{r.params_b:g}B {r.adapter_minus_base:+.3f} [{r.ci_low:+.3f}, {r.ci_high:+.3f}]"
                     for r in s.itertuples()) if len(s) else "no rows"


def jcell(measure, fam, rung, field="adapter_minus_base"):
    s = JPOOL[(JPOOL.measure == measure) & (JPOOL.family == fam) & (JPOOL.rung == rung)]
    return float(s[field].iloc[0]) if len(s) else float("nan")

# ---------------------------------------------------------------- 4. gap-closing regression
CEIL = (refs[refs.group == "source"].groupby("author")[CEIL_MEASURES].mean()
        .rename(columns={c: c + "_ceiling" for c in CEIL_MEASURES}))
CEIL_REF = (refs[refs.group == "ref"].groupby("author")[CEIL_MEASURES].mean()
            .rename(columns={c: c + "_ceiling_refgroup" for c in CEIL_MEASURES}))


def gap_points(overlay_df, gain_df, measure, ceiling_map):
    pts = []
    for (au, fam, rung), g in gain_df[gain_df.measure == measure].groupby(["author", "family", "rung"]):
        b = overlay_df[(overlay_df.author == au) & (overlay_df.family == fam) & (overlay_df.rung == rung) &
                       (overlay_df.kind == "base") & (overlay_df.measure == measure)]
        a = overlay_df[(overlay_df.author == au) & (overlay_df.family == fam) & (overlay_df.rung == rung) &
                       (overlay_df.kind == "adapter") & (overlay_df.measure == measure)]
        if not len(b) or not len(a) or au not in ceiling_map.index:
            continue
        ceil = float(ceiling_map.loc[au, measure + "_ceiling"])
        pts.append({"author": au, "family": fam, "rung": rung, "params_b": float(g.params_b.iloc[0]),
                    "measure": measure, "base": float(b["mean"].iloc[0]), "adapter": float(a["mean"].iloc[0]),
                    "ceiling": ceil, "headroom": ceil - float(b["mean"].iloc[0]), "gain": float(g.gain.iloc[0]),
                    "gain_se": float(g.se.iloc[0])})
    return pd.DataFrame(pts)


def ols_fit(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 4:
        return np.nan, np.nan, np.nan
    b, a = np.polyfit(x[m], y[m], 1)
    yhat = a + b * x[m]
    ss = 1 - np.sum((y[m] - yhat) ** 2) / np.sum((y[m] - y[m].mean()) ** 2) if np.var(y[m]) > 0 else np.nan
    return float(b), float(a), float(ss)


def fit_with_ci(pts, n=2000, seed=0):
    x, y = pts["headroom"].values, pts["gain"].values
    b, a, r2 = ols_fit(x, y)
    rng = np.random.default_rng(seed)
    bb, aa = [], []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        bi, ai, _ = ols_fit(x[i], y[i])
        if bi == bi:
            bb.append(bi); aa.append(ai)
    # cluster bootstrap over authors
    aus = sorted(pts.author.unique())
    bbc = []
    for _ in range(n):
        pick = rng.integers(0, len(aus), len(aus))
        sub = pd.concat([pts[pts.author == aus[i]] for i in pick])
        bi, _a, _r = ols_fit(sub["headroom"].values, sub["gain"].values)
        if bi == bi:
            bbc.append(bi)
    loo = {}
    for au in aus:
        bi, _a, _r = ols_fit(pts[pts.author != au]["headroom"].values, pts[pts.author != au]["gain"].values)
        loo[au] = bi
    return dict(slope=b, slope_lo=float(np.quantile(bb, .025)) if bb else np.nan,
                slope_hi=float(np.quantile(bb, .975)) if bb else np.nan,
                slope_lo_authorclust=float(np.quantile(bbc, .025)) if bbc else np.nan,
                slope_hi_authorclust=float(np.quantile(bbc, .975)) if bbc else np.nan,
                intercept=a, intercept_lo=float(np.quantile(aa, .025)) if aa else np.nan,
                intercept_hi=float(np.quantile(aa, .975)) if aa else np.nan, r2=r2, n_points=int(len(pts)),
                loo_slope_min=float(np.nanmin(list(loo.values()))), loo_slope_max=float(np.nanmax(list(loo.values()))))


gap_rows, gap_pts_all = [], []
for m in CEIL_MEASURES:
    pts = gap_points(OVERLAY, GAIN, m, CEIL)
    pts["scope"] = "cross-family overlay (3 authors x 3 rungs x 2 families)"
    gap_pts_all.append(pts)
    f = fit_with_ci(pts)
    r, rlo, rhi, rp, rn = spearman_ci(pts["headroom"].values, pts["gain"].values)
    gap_rows.append({"measure": m, "scope": "overlay", **f, "spearman": r, "spearman_lo": rlo,
                     "spearman_hi": rhi, "p_spearman": rp})
    for fam in FAMS:
        sub = pts[pts.family == fam]
        f2 = fit_with_ci(sub)
        gap_rows.append({"measure": m, "scope": f"overlay:{fam}", **f2, "spearman": np.nan,
                         "spearman_lo": np.nan, "spearman_hi": np.nan, "p_spearman": np.nan})

# supplementary: the full Qwen sweep (all authors, three sizes), same regression
dq = d[(d.family == "Qwen3") & (d.params_b.isin([4.0, 8.0, 14.0])) & (d.author != "patrick")].copy()
btq = dq.groupby(["author", "family", "params_b", "kind", "id"], as_index=False)[CEIL_MEASURES].mean()
qrows = []
for (au, pb), g in btq.groupby(["author", "params_b"]):
    for m in CEIL_MEASURES:
        b = g[g.kind == "base"].set_index("id")[m]
        a = g[g.kind == "adapter"].set_index("id")[m]
        idx = a.index.intersection(b.index)
        if not len(idx) or au not in CEIL.index:
            continue
        ceil = float(CEIL.loc[au, m + "_ceiling"])
        qrows.append({"author": au, "family": "Qwen3", "rung": {4.0: 0, 8.0: 1, 14.0: 2}[pb], "params_b": pb,
                      "measure": m, "base": float(b.loc[idx].mean()), "adapter": float(a.loc[idx].mean()),
                      "ceiling": ceil, "headroom": ceil - float(b.loc[idx].mean()),
                      "gain": float((a.loc[idx] - b.loc[idx]).mean()), "gain_se": np.nan,
                      "scope": "full Qwen3 sweep (13 authors x 3 sizes)"})
QPTS = pd.DataFrame(qrows)
for m in CEIL_MEASURES:
    sub = QPTS[QPTS.measure == m]
    if len(sub) >= 6:
        f = fit_with_ci(sub)
        r, rlo, rhi, rp, rn = spearman_ci(sub["headroom"].values, sub["gain"].values)
        gap_rows.append({"measure": m, "scope": "full_qwen_sweep", **f, "spearman": r, "spearman_lo": rlo,
                         "spearman_hi": rhi, "p_spearman": rp})
GAPFIT = pd.DataFrame(gap_rows)
GAPPTS = pd.concat(gap_pts_all + [QPTS], ignore_index=True)
write_table(GAPFIT, os.path.join(OUTD, "gap_closing_fits.csv"), floats=5)
write_table(GAPPTS, os.path.join(OUTD, "gap_closing_points.csv"), floats=5)


# gain and head-room share the base term, so the fit is partly mechanical: diagnose it
def slope_ci(x, y, n=2000, seed=0):
    x = np.asarray(x, float); y = np.asarray(y, float)
    b, a, r2 = ols_fit(x, y)
    rng = np.random.default_rng(seed)
    bb = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        bi, _a, _r = ols_fit(x[i], y[i])
        if bi == bi:
            bb.append(bi)
    return b, (float(np.quantile(bb, .025)) if bb else np.nan), (float(np.quantile(bb, .975)) if bb else np.nan), a, r2


diag_rows = []
for scope_name, frame in [("overlay", GAPPTS[GAPPTS.scope.str.startswith("cross-family")]), ("full_qwen_sweep", QPTS)]:
    for m in CEIL_MEASURES:
        s = frame[frame.measure == m]
        if len(s) < 6:
            continue
        b, blo, bhi, a, r2 = slope_ci(s["base"].values, s["adapter"].values)
        diag_rows.append({"measure": m, "scope": scope_name, "n_points": int(len(s)),
                          "slope_adapter_on_base": b, "ci_low": blo, "ci_high": bhi,
                          "intercept_adapter_on_base": a, "r2_adapter_on_base": r2,
                          "implied_gap_slope_1_minus": 1 - b,
                          "sd_ceiling": float(np.std(s["ceiling"], ddof=1)),
                          "sd_base": float(np.std(s["base"], ddof=1)),
                          "sd_adapter": float(np.std(s["adapter"], ddof=1)),
                          "sd_headroom": float(np.std(s["headroom"], ddof=1)),
                          "corr_headroom_minus_base": float(np.corrcoef(s["headroom"], -s["base"])[0, 1])})
GAPDIAG = pd.DataFrame(diag_rows)
write_table(GAPDIAG, os.path.join(OUTD, "gap_closing_diagnostics.csv"), floats=5)

# ---------------------------------------------------------------- 5. mixed models (family x rung)
mm_rows = []
for m in ["luar_cos_ref", "luar_cos_source", "wegmann_cos_source", "otd_js", "per", "hapax_w300", "len_ratio", "truncated"]:
    gr = []
    for (au, fam, rung), g in BT.groupby(["author", "family", "rung"]):
        a = g[g.kind == "adapter"].set_index("id")[m]
        b = g[g.kind == "base"].set_index("id")[m]
        idx = a.index.intersection(b.index)
        for i in idx:
            v = a.loc[i] - b.loc[i]
            if v == v:
                gr.append({"author": au, "family": fam, "rung": float(rung), "fam_m": 1.0 if fam == "Ministral3" else 0.0,
                           "gain": float(v), "id": i})
    gr = pd.DataFrame(gr)
    _r, tidy = mixed_model(gr, "gain ~ rung * fam_m", groups="author")
    if len(tidy):
        tidy["measure"] = m
        tidy["model"] = "gain ~ rung * fam_m + (1|author)"
        rv = float(np.asarray(_r.cov_re)[0, 0]) if _r is not None else np.nan
        tidy["re_var_author"] = rv
        tidy["singular_re"] = (rv < 1e-8) if rv == rv else True
        mm_rows.append(tidy)
    lv = []
    for (au, fam, rung, kind), g in BT.groupby(["author", "family", "rung", "kind"]):
        if kind != "base":
            continue
        for i, v in g.set_index("id")[m].items():
            if v == v:
                lv.append({"author": au, "family": fam, "rung": float(rung),
                           "fam_m": 1.0 if fam == "Ministral3" else 0.0, "level": float(v), "id": i})
    lv = pd.DataFrame(lv)
    _r2, tidy2 = mixed_model(lv, "level ~ rung * fam_m", groups="author")
    if len(tidy2):
        tidy2["measure"] = m
        tidy2["model"] = "base level ~ rung * fam_m + (1|author)"
        rv2 = float(np.asarray(_r2.cov_re)[0, 0]) if _r2 is not None else np.nan
        tidy2["re_var_author"] = rv2
        tidy2["singular_re"] = (rv2 < 1e-8) if rv2 == rv2 else True
        mm_rows.append(tidy2)
MIXED = pd.concat(mm_rows, ignore_index=True) if mm_rows else pd.DataFrame()
if len(MIXED):
    write_table(MIXED, os.path.join(OUTD, "mixed_models.csv"), floats=5)

# ---------------------------------------------------------------- 6. run-level family record
rcols = ["run", "author", "family", "params_b", "kind", "replicate", "n_gens", "arms", "truncated_pct",
         "preface_pct", "adapter_served", "gate_generation_ok", "train_examples", "train_steps", "eval_first",
         "eval_best", "probe_delta", "gate_training_ok", "scored"]
RUNLEVEL = runs[runs.author.isin(CF)][[c for c in rcols if c in runs.columns]].sort_values(["author", "family", "params_b", "kind"])
write_table(RUNLEVEL, os.path.join(OUTD, "run_level_family.csv"), floats=5)

fam_rows = []
runs_cf = runs[runs.author.isin(CF)]
for fam in FAMS:
    ad = RUNLEVEL[(RUNLEVEL.family == fam) & (RUNLEVEL.kind == "adapter") & (~RUNLEVEL.replicate)]
    ba = RUNLEVEL[(RUNLEVEL.family == fam) & (RUNLEVEL.kind == "base") & (~RUNLEVEL.replicate)]
    sub = cfp[cfp.family == fam]
    rf = runs_cf[runs_cf.family == fam]
    fam_rows.append({"family": fam, "n_adapter_runs": len(ad), "n_base_runs": len(ba),
                     "probe_delta_mean": float(ad.probe_delta.mean()), "probe_delta_min": float(ad.probe_delta.min()),
                     "probe_delta_max": float(ad.probe_delta.max()),
                     "eval_improvement_mean": float((ad.eval_first - ad.eval_best).mean()),
                     "train_steps_mean": float(ad.train_steps.mean()),
                     "truncated_pct_base_mean": float(ba.truncated_pct.mean()),
                     "truncated_pct_adapter_mean": float(ad.truncated_pct.mean()),
                     "trunc_rate_A0_base": float(sub[sub.kind == "base"].truncated.mean()),
                     "trunc_rate_A0_adapter": float(sub[sub.kind == "adapter"].truncated.mean()),
                     "len_ratio_A0_base": float(sub[sub.kind == "base"].len_ratio.mean()),
                     "len_ratio_A0_adapter": float(sub[sub.kind == "adapter"].len_ratio.mean()),
                     "adapter_served": ",".join(sorted(set(ad.adapter_served.dropna()))),
                     "n_authors": int(sub.author.nunique()),
                     "n_runs_judged_2afc": int(rf.judged_2afc.fillna(False).sum()),
                     "n_runs_with_coverage": int(rf.has_coverage.fillna(False).sum()),
                     "n_runs_total": int(len(rf)),
                     "coverage_cells_A0": int(sub.coverage.notna().sum()),
                     "fool_cells_A0": int(sub.fool_vs_source.notna().sum()),
                     "rubric_cells_A0": int(sub.rubric_S.notna().sum()),
                     "coverage_A0_base": float(sub[sub.kind == "base"].coverage.mean()),
                     "coverage_A0_adapter": float(sub[sub.kind == "adapter"].coverage.mean()),
                     "fool_A0_base": float(sub[sub.kind == "base"].fool_vs_source.mean()),
                     "fool_A0_adapter": float(sub[sub.kind == "adapter"].fool_vs_source.mean())})
FAMSUM = pd.DataFrame(fam_rows)
write_table(FAMSUM, os.path.join(OUTD, "family_summary.csv"), floats=5)
write_table(FLOORS, os.path.join(OUTD, "floors.csv"), floats=6)
write_table(FLOOR_PAIRS, os.path.join(OUTD, "floor_pairs.csv"), floats=6)

# ---------------------------------------------------------------- figures
STYLE = {"Qwen3": dict(ls="-", marker="o"), "Ministral3": dict(ls="--", marker="s")}
KCOL = {"base": "tab:blue", "adapter": "tab:red"}


def overlay_fig(measures, fname, title):
    fig, axes = plt.subplots(len(measures), len(CF), figsize=(4.2 * len(CF), 3.4 * len(measures)), squeeze=False)
    for i, m in enumerate(measures):
        for j, au in enumerate(CF):
            ax = axes[i][j]
            for fam in FAMS:
                for kind in ("base", "adapter"):
                    s = OVERLAY[(OVERLAY.author == au) & (OVERLAY.family == fam) & (OVERLAY.kind == kind) &
                                (OVERLAY.measure == m)].sort_values("rung")
                    if not len(s):
                        continue
                    ax.errorbar(s.rung, s["mean"], yerr=[s["mean"] - s.ci_low, s.ci_high - s["mean"]],
                                color=KCOL[kind], capsize=2, lw=1.6, ms=5, label=f"{fam} {kind}", **STYLE[fam])
            if m in CEIL.columns.str.replace("_ceiling", "", regex=False).tolist() and au in CEIL.index:
                ax.axhline(float(CEIL.loc[au, m + "_ceiling"]), color="k", lw=1, ls=":", label="author ceiling")
            ax.set_xticks([0, 1, 2]); ax.set_xticklabels([RUNG_TICK[k] for k in (0, 1, 2)], fontsize=8)
            ax.set_title(f"{au}", fontsize=10)
            if j == 0:
                ax.set_ylabel(lab(m), fontsize=8)
            ax.grid(alpha=.25)
    h, l = axes[0][0].get_legend_handles_labels()
    seen, hh, ll = set(), [], []
    for a, b in zip(h, l):
        if b not in seen:
            seen.add(b); hh.append(a); ll.append(b)
    fig.legend(hh, ll, loc="lower center", ncol=len(ll), fontsize=8, frameon=False)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=[0, 0.05, 1, 0.97])
    return savefig(fig, os.path.join(OUTD, fname))


f_voice = overlay_fig(FIG_VOICE, "fig_overlay_voice.png", "Qwen3 (solid) vs Ministral 3 (dashed), arm A0, brief-cluster 95% CI")
f_constr = overlay_fig(FIG_CONSTR, "fig_overlay_construction.png", "Construction and structure, arm A0, brief-cluster 95% CI")

# gain by rung
GM = ["luar_cos_ref", "luar_cos_source", "wegmann_cos_source", "otd_js", "per", "hapax_w300"]
fig, axes = plt.subplots(2, 3, figsize=(14, 7.5), squeeze=False)
for k, m in enumerate(GM):
    ax = axes[k // 3][k % 3]
    for fi, fam in enumerate(FAMS):
        for ai, au in enumerate(CF):
            s = GAIN[(GAIN.measure == m) & (GAIN.family == fam) & (GAIN.author == au)].sort_values("rung")
            if not len(s):
                continue
            off = (fi - .5) * .22 + (ai - 1) * .06
            ax.errorbar(s.rung + off, s.gain, yerr=[s.gain - s.ci_low, s.ci_high - s.gain],
                        color=f"C{ai}", capsize=2, lw=1.3, ms=5, label=f"{au} {fam}" if k == 0 else None, **STYLE[fam])
    fl = floor_of(m, "Qwen3"); flm = floor_of(m, "Ministral3")
    ax.axhline(0, color="k", lw=.8)
    ax.axhspan(-max(fl, flm), max(fl, flm), color="gray", alpha=.18)
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels([RUNG_TICK[k2] for k2 in (0, 1, 2)], fontsize=8)
    ax.set_title(lab(m), fontsize=9)
    ax.set_ylabel("adapter minus base", fontsize=8)
    ax.grid(alpha=.25)
h, l = axes[0][0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=6, fontsize=8, frameon=False)
fig.suptitle("Brief-paired adapter gain; grey band = the larger of the two families' noise floors", fontsize=11)
fig.tight_layout(rect=[0, 0.06, 1, 0.96])
f_gain = savefig(fig, os.path.join(OUTD, "fig_gain_by_rung.png"))

# gap closing
fig, axes = plt.subplots(1, len(CEIL_MEASURES), figsize=(6 * len(CEIL_MEASURES), 4.6), squeeze=False)
for k, m in enumerate(CEIL_MEASURES):
    ax = axes[0][k]
    pts = GAPPTS[(GAPPTS.measure == m) & (GAPPTS.scope.str.startswith("cross-family"))]
    q = QPTS[QPTS.measure == m]
    ax.scatter(q.headroom, q.gain, s=18, c="lightgray", marker="^", label="full Qwen3 sweep")
    for ai, au in enumerate(CF):
        for fam in FAMS:
            s = pts[(pts.author == au) & (pts.family == fam)]
            ax.scatter(s.headroom, s.gain, s=70, c=f"C{ai}", marker="o" if fam == "Qwen3" else "s",
                       edgecolor="k", lw=.6, label=f"{au} {fam}")
    f = GAPFIT[(GAPFIT.measure == m) & (GAPFIT.scope == "overlay")].iloc[0]
    xs = np.linspace(pts.headroom.min(), pts.headroom.max(), 50)
    ax.plot(xs, f.intercept + f.slope * xs, "k-", lw=1.6,
            label=f"overlay fit: slope {f.slope:.2f} [{f.slope_lo:.2f}, {f.slope_hi:.2f}]")
    ax.plot(xs, xs, color="gray", ls=":", lw=1.2, label="full gap closed (slope 1)")
    ax.axhline(0, color="k", lw=.6)
    ax.set_xlabel(f"head-room: author ceiling minus base mean ({lab(m)})", fontsize=8)
    ax.set_ylabel("adapter minus base", fontsize=8)
    ax.set_title(lab(m), fontsize=10)
    ax.legend(fontsize=7, frameon=False)
    ax.grid(alpha=.25)
fig.suptitle("Gap closing: does the adapter buy more where the base sits further from the author?", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.95])
f_gap = savefig(fig, os.path.join(OUTD, "fig_gap_closing.png"))

# length and truncation
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
for ax, m in zip(axes, ["truncated", "len_ratio"]):
    for fam in FAMS:
        for kind in ("base", "adapter"):
            s = (OVERLAY[(OVERLAY.family == fam) & (OVERLAY.kind == kind) & (OVERLAY.measure == m)]
                 .groupby("rung")["mean"].mean())
            ax.plot(s.index, s.values, color=KCOL[kind], label=f"{fam} {kind}", lw=1.8, ms=6, **STYLE[fam])
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels([RUNG_TICK[k] for k in (0, 1, 2)], fontsize=8)
    ax.set_ylabel(lab(m), fontsize=9); ax.grid(alpha=.25)
    ax.set_title(lab(m), fontsize=10)
axes[0].legend(fontsize=8, frameon=False)
fig.suptitle("Length behaviour by family (mean over the three overlay authors, arm A0)", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.94])
f_len = savefig(fig, os.path.join(OUTD, "fig_length_truncation.png"))

# TOST forest
TM = ["luar_cos_ref", "luar_cos_source", "wegmann_cos_source", "otd_js", "per", "hapax_w300"]
fig, axes = plt.subplots(1, len(TM), figsize=(3.1 * len(TM), 4.6), sharey=True)
for ax, m in zip(np.atleast_1d(axes), TM):
    s = TOSTT[TOSTT.measure == m].sort_values(["rung", "author"]).reset_index(drop=True)
    ypos = np.arange(len(s))
    ax.errorbar(s.adapter_qwen_minus_ministral, ypos,
                xerr=[s.adapter_qwen_minus_ministral - s.ci_low, s.ci_high - s.adapter_qwen_minus_ministral],
                fmt="o", color="tab:purple", capsize=2, ms=4)
    b = float(s.equiv_bound.iloc[0]) if len(s) else np.nan
    ax.axvspan(-b, b, color="gray", alpha=.18)
    ax.axvline(0, color="k", lw=.8)
    ax.set_yticks(ypos); ax.set_yticklabels([f"{r.author} {RUNG_NAME[r.rung]}" for r in s.itertuples()], fontsize=7)
    ax.set_title(lab(m), fontsize=8)
    ax.grid(alpha=.25)
fig.suptitle("Adapter endpoint, Qwen3 minus Ministral 3 (brief-paired); grey = equivalence bound", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.93])
f_tost = savefig(fig, os.path.join(OUTD, "fig_tost_endpoints.png"))

# the judged rows, both families, pooled over the three shared authors
fig, axes = plt.subplots(1, len(JUDGED), figsize=(6.2 * len(JUDGED), 4.4), squeeze=False)
for ax, m in zip(axes[0], JUDGED):
    for fam in FAMS:
        s = JPOOL[(JPOOL.measure == m) & (JPOOL.family == fam)].sort_values("rung")
        if not len(s):
            continue
        ax.errorbar(s.rung, s.adapter_minus_base,
                    yerr=[s.adapter_minus_base - s.ci_low, s.ci_high - s.adapter_minus_base],
                    capsize=2, lw=1.5, ms=6, label=f"{fam} (n={int(s.n_authors.iloc[0])} authors)", **STYLE[fam])
        fl = floor_of(m, fam)
        if fl == fl:
            ax.axhspan(-fl, fl, color="tab:blue" if fam == "Qwen3" else "tab:orange", alpha=.10)
    ax.axhline(0, color="k", lw=.8)
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels([RUNG_TICK[k] for k in (0, 1, 2)], fontsize=8)
    ax.set_ylabel("adapter minus base", fontsize=8)
    ax.set_title(lab(m), fontsize=9)
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=.25)
fig.suptitle("Judged rows across both families, brief-paired; shaded bands are each family's replicate floor", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.93])
f_judged = savefig(fig, os.path.join(OUTD, "fig_judged_contrasts.png"))

# ---------------------------------------------------------------- README numbers
def gsel(measure, fam=None, rung=None):
    s = GAIN[GAIN.measure == measure]
    if fam:
        s = s[s.family == fam]
    if rung is not None:
        s = s[s.rung == rung]
    return s


WN = GAIN["within_noise"].fillna(True).astype(bool)
n_gain_sig = int(((GAIN.q_bh < 0.05) & (~WN)).sum())
n_gain_tot = int(GAIN.p_wilcoxon.notna().sum())
n_noise = int(GAIN["within_noise"].fillna(False).astype(bool).sum())

lr_q = gsel("luar_cos_ref", "Qwen3"); lr_m = gsel("luar_cos_ref", "Ministral3")
ls_q = gsel("luar_cos_source", "Qwen3"); ls_m = gsel("luar_cos_source", "Ministral3")
per_q = gsel("per", "Qwen3"); per_m = gsel("per", "Ministral3")
otd_q = gsel("otd_js", "Qwen3"); otd_m = gsel("otd_js", "Ministral3")

gap_lr = GAPFIT[(GAPFIT.measure == "luar_cos_ref") & (GAPFIT.scope == "overlay")].iloc[0]
gap_wg = GAPFIT[(GAPFIT.measure == "wegmann_cos_ref") & (GAPFIT.scope == "overlay")].iloc[0]
gd_lr = GAPDIAG[(GAPDIAG.measure == "luar_cos_ref") & (GAPDIAG.scope == "overlay")].iloc[0]
gd_wg = GAPDIAG[(GAPDIAG.measure == "wegmann_cos_ref") & (GAPDIAG.scope == "overlay")].iloc[0]
n_mixfits = int(MIXED[["measure", "model"]].drop_duplicates().shape[0]) if len(MIXED) else 0
n_singular = int(MIXED[MIXED["singular_re"].fillna(True).astype(bool)][["measure", "model"]].drop_duplicates().shape[0]) \
    if ("singular_re" in MIXED.columns and len(MIXED)) else 0
gap_lr_full = GAPFIT[(GAPFIT.measure == "luar_cos_ref") & (GAPFIT.scope == "full_qwen_sweep")]
n_equiv = int(TOSTT["equivalent"].fillna(False).astype(bool).sum()); n_tost = int(TOSTT.p_equivalence.notna().sum())
n_exceed = int(TOSTT["diff_exceeds_bound"].fillna(False).astype(bool).sum())

fq = FAMSUM[FAMSUM.family == "Qwen3"].iloc[0]
fm = FAMSUM[FAMSUM.family == "Ministral3"].iloc[0]

# README-only descriptors, all read back off the tables this script just wrote
def _npairs(fam, measure):
    s = FLOORS[(FLOORS.family == fam) & (FLOORS.measure == measure)]
    return int(s.n_regen_pairs.iloc[0]) if len(s) else 0


n_regen_q = _npairs("Qwen3", "luar_cos_ref")
n_regen_q_cov = _npairs("Qwen3", "coverage")
n_regen_m = _npairs("Ministral3", "luar_cos_ref")
n_regen_m_len = _npairs("Ministral3", "words")
sizes_q, npairs_q = pair_sizes("luar_cos_ref", "Qwen3")
sizes_m, npairs_m = pair_sizes("luar_cos_ref", "Ministral3")
sizes_q_cov, npairs_q_cov = pair_sizes("coverage", "Qwen3")
sizes_m_cov, npairs_m_cov = pair_sizes("coverage", "Ministral3")
sizes_q_fool, npairs_q_fool = pair_sizes("fool_vs_source", "Qwen3")
sizes_m_fool, npairs_m_fool = pair_sizes("fool_vs_source", "Ministral3")
_mf = FLOORS[FLOORS.family == "Ministral3"].dropna(subset=["floor_regen", "floor_seed_overlay"])
m_regen_below_seed = bool((_mf.floor_regen < _mf.floor_seed_overlay).all()) if len(_mf) else False
n_judged_cells = int(JUDGEDIFF[JUDGEDIFF.scope == "author"].shape[0])
n_judged_noise = int(JUDGEDIFF[JUDGEDIFF.scope == "author"]["within_noise"].fillna(False).astype(bool).sum())


def jnoise(measure, fam):
    s = JPOOL[(JPOOL.measure == measure) & (JPOOL.family == fam)]
    return int(s["within_noise"].fillna(False).astype(bool).sum()), int(len(s))


def jbigger(measure):
    """True when |Qwen3 contrast| exceeds |Ministral 3 contrast| at every matched rung."""
    q = JPOOL[(JPOOL.measure == measure) & (JPOOL.family == "Qwen3")].set_index("rung").adapter_minus_base
    m = JPOOL[(JPOOL.measure == measure) & (JPOOL.family == "Ministral3")].set_index("rung").adapter_minus_base
    idx = q.index.intersection(m.index)
    return bool(len(idx)) and bool((q.loc[idx].abs() > m.loc[idx].abs()).all())


cov_noise_q, cov_rungs_q = jnoise("coverage", "Qwen3")
cov_noise_m, cov_rungs_m = jnoise("coverage", "Ministral3")
fool_noise_q, fool_rungs_q = jnoise("fool_vs_source", "Qwen3")
fool_noise_m, fool_rungs_m = jnoise("fool_vs_source", "Ministral3")
n_gapfull_authors = int(GAPPTS[GAPPTS.scope.str.startswith("full")].author.nunique())
trunc_over = RUNLEVEL[(RUNLEVEL.truncated_pct > 20) & (~RUNLEVEL.replicate)]
trunc_over_txt = ", ".join(f"{r.run} {r.truncated_pct:.1f}%" for r in trunc_over.itertuples()) or "none"
n_gate_ok_over = int(trunc_over["gate_generation_ok"].fillna(False).astype(bool).sum()) if len(trunc_over) else 0
probe_pos = RUNLEVEL[RUNLEVEL.probe_delta > 0]
probe_pos_txt = ", ".join(sorted(probe_pos.run)) or "none"
train_ex = RUNLEVEL[RUNLEVEL.kind == "adapter"].groupby("author").train_examples.max().dropna()
train_ex_txt = ", ".join(f"{a} {int(v)}" for a, v in train_ex.items()) or "n/a"


def signcount(measure, fam):
    """How many author x rung cells move up, down, or sit inside the floor, on one measure."""
    s = GAIN[(GAIN.measure == measure) & (GAIN.family == fam)]
    fl = float(floor_of(measure, fam))
    up = int(((s.gain > fl) & (s.q_bh < 0.05)).sum())
    dn = int(((s.gain < -fl) & (s.q_bh < 0.05)).sum())
    noise = int(s["within_noise"].fillna(False).astype(bool).sum())
    aus_up = sorted(s[(s.gain > fl) & (s.q_bh < 0.05)].author.unique())
    aus_dn = sorted(s[(s.gain < -fl) & (s.q_bh < 0.05)].author.unique())
    return dict(up=up, dn=dn, noise=noise, n=len(s), authors_up=aus_up, authors_dn=aus_dn)


sc_lr_q, sc_lr_m = signcount("luar_cos_ref", "Qwen3"), signcount("luar_cos_ref", "Ministral3")
sc_pe_q, sc_pe_m = signcount("per", "Qwen3"), signcount("per", "Ministral3")
sc_hx_q, sc_hx_m = signcount("hapax_w300", "Qwen3"), signcount("hapax_w300", "Ministral3")


def mixterm(measure, term, model="gain ~ rung * fam_m + (1|author)"):
    if not len(MIXED):
        return None
    s = MIXED[(MIXED.measure == measure) & (MIXED.term == term) & (MIXED.model == model)]
    return s.iloc[0] if len(s) else None


mx_lr_rung = mixterm("luar_cos_ref", "rung")
mx_lr_int = mixterm("luar_cos_ref", "rung:fam_m")
mx_pe_rung = mixterm("per", "rung")

mix_int = MIXED[(MIXED.term == "rung:fam_m")] if len(MIXED) else pd.DataFrame()

top_tables = [
    ("Adapter gain, brief-paired, by author x rung x family (voice anchor luar_cos_ref)",
     GAIN[GAIN.measure == "luar_cos_ref"][["author", "family", "params_b", "gain", "ci_low", "ci_high",
                                           "cohens_d", "cliffs_delta", "q_bh", "floor", "within_noise", "n_briefs"]]),
    ("Adapter gain on the construction row (per, 600-word cap; lower is better)",
     GAIN[GAIN.measure == "per"][["author", "family", "params_b", "gain", "ci_low", "ci_high", "cohens_d",
                                  "q_bh", "floor", "within_noise", "n_briefs"]]),
    ("Gap-closing fits", GAPFIT[["measure", "scope", "n_points", "slope", "slope_lo", "slope_hi",
                                 "slope_lo_authorclust", "slope_hi_authorclust", "intercept", "r2",
                                 "loo_slope_min", "loo_slope_max"]]),
    ("Gap-closing diagnostics: the adapter endpoint regressed on the base level", GAPDIAG),
    ("Equivalence of the two families' adapter endpoints (TOST, bound = larger floor)",
     TOSTT[TOSTT.measure.isin(TM)][["author", "rung_name", "measure", "adapter_qwen_minus_ministral", "ci_low",
                                    "ci_high", "equiv_bound", "p_equivalence", "equivalent", "diff_exceeds_bound"]]),
    ("The judged rows, adapter minus base, both families, pooled over the three shared authors",
     JPOOL[["measure", "family", "params_b", "rung_name", "n_authors", "n_briefs", "base_mean", "adapter_mean",
            "adapter_minus_base", "ci_low", "ci_high", "q_bh", "floor", "within_noise"]]),
    ("The same judged contrasts per author", JUDGEDIFF[JUDGEDIFF.scope == "author"][
        ["measure", "author", "family", "params_b", "base_mean", "adapter_mean", "adapter_minus_base",
         "ci_low", "ci_high", "q_bh", "floor", "within_noise", "n_briefs"]]),
    ("Noise floors used", FLOORS),
    ("Replicate pairs behind the regeneration floors, with the rung each sits at",
     FLOOR_PAIRS[FLOOR_PAIRS.measure.isin(["luar_cos_ref"] + JUDGED)]),
    ("Family summary from the run records", FAMSUM.T.map(lambda v: round(v, 4) if isinstance(v, float) else v).reset_index().rename(columns={"index": "field", 0: "Qwen3", 1: "Ministral3"})),
]
MIXCOLS = [c for c in ["measure", "model", "estimate", "se", "ci_low", "ci_high", "p", "n_obs", "n_groups"] if c in mix_int.columns]
if len(mix_int) and MIXCOLS:
    top_tables.insert(3, ("Family x size interaction on gain (MixedLM, groups = author, 3 groups)", mix_int[MIXCOLS]))

figs = [("Base and adapter across the two families", f_voice),
        ("Construction and structure across the two families", f_constr),
        ("Adapter gain by rung, with the noise band", f_gain),
        ("Gap closing", f_gap),
        ("Length and truncation by family", f_len),
        ("Adapter endpoints, family difference with equivalence bounds", f_tost),
        ("The judged rows in both families, against each family's floor", f_judged)]

runtime = time.time() - T0

what = f"""
Overlays the Ministral 3 replication on the Qwen3 sweep for the three authors that were run in
both families ({', '.join(CF)}) at three matched size rungs (Qwen3 4B against Ministral 3B, then
8B against 8B, 14B against 14B). It reports, on arm A0 (brief only): the base level and the
adapter level in each family, the brief-paired adapter gain, the difference between the two
families at both the base level and the adapter endpoint, an equivalence test on the adapter
endpoints, the regression of gain on the head-room left to the author's own held-out ceiling,
a family x size interaction on gain, and the run-level record of each family (probe delta,
evaluation loss, truncation, length ratio).

The two LLM-judged rows are in the overlay on the same footing as the automatic ones. Judged
brief coverage and the 2AFC fool rate exist for both families now: {int(fm.n_runs_judged_2afc)}
of the {int(fm.n_runs_total)} Ministral 3 runs on these authors carry 2AFC verdicts and
{int(fm.n_runs_with_coverage)} carry coverage, produced on 2026-09-10 and 2026-09-11 by the same
two judges on the same prompts and the same sample-0 protocol as the Qwen3 records. That gives
{int(fm.coverage_cells_A0)} judged coverage cells and {int(fm.fool_cells_A0)} judged fool cells
on Ministral 3 in this A0 set, against {int(fq.coverage_cells_A0)} and {int(fq.fool_cells_A0)}
on Qwen3. judged_adapter_minus_base.csv holds the adapter-minus-base contrast on both rows, per
author and pooled over the three shared authors, in both families, each against its own family's
replicate floor.

{len(GAIN)} adapter-vs-base contrasts ({len(MEASURES)} measures x {GAIN[['author','family','rung']].drop_duplicates().shape[0]}
author x rung x family cells) and {n_tost} cross-family endpoint tests were computed. These
{len(CF)} authors are the whole Ministral 3 sample in the study, so every statement about a family
in this folder is a statement about {len(CF)} authors. The Qwen3 1.7B run on patrick_v2 has no
Ministral counterpart and is reported off the ladder in offladder_qwen17b.csv, not in the paired
tables.
"""

how = f"""
Data: data/master/cells.parquet, arm A0, non-replicate rows, both samples; brief means are taken
first (the two samples of a cell are averaged) so that the brief is the unit inside an author.
Base and adapter runs share the same brief set in every cell here:
{', '.join(f'{a} {int(v)}' for a, v in GAIN[GAIN.measure == 'luar_cos_ref'].groupby('author').n_briefs.max().items())}
briefs. Coverage and fool_vs_source are the exception: they are LLM-judged, present on sample 0
only, so the brief mean of a judged cell is that single sample rather than an average of two.
Both are present in both families ({int(fq.coverage_cells_A0)} and {int(fm.coverage_cells_A0)}
judged coverage cells, {int(fq.fool_cells_A0)} and {int(fm.fool_cells_A0)} judged fool cells,
Qwen3 and Ministral 3 respectively).

Unit and interval. Every contrast is brief-paired inside one author x rung x family and its 95%
interval is a cluster bootstrap over briefs (lib.cluster_bootstrap, 2000 resamples, seed 0).
Cohen's d and Cliff's delta are computed on the raw cell distributions of the two conditions.
p-values are Wilcoxon signed-rank on the per-brief differences and are BH-FDR adjusted inside the
script's two families of tests (adapter gain: {n_gain_tot} tests; base-level family difference:
{int(BASEDIFF.p_wilcoxon.notna().sum())} tests). A q below 0.05 means survival inside one of those
two families of tests in this one script, not across the programme. The unit for any claim about a
family is the author, and there are {len(CF)} of them here.

Noise floors. Both families' floors are in floors.csv, each with the number of pairs or runs behind
it, and every pair behind them is listed in floor_pairs.csv with the rung it sits at. The
regeneration floor is what lib.replicate_floor computes from a family's twice-generated base
configurations: {npairs_q} pairs on Qwen3 at {sizes_q} and {npairs_m} pairs on Ministral 3 at
{sizes_m} for the automatic measures. The judged rows have fewer, because a replicate run has to
have been judged as well as scored: coverage has {npairs_q_cov} Qwen3 pairs at {sizes_q_cov} and
{npairs_m_cov} Ministral 3 pairs at {sizes_m_cov}, fool_vs_source {npairs_q_fool} at
{sizes_q_fool} and {npairs_m_fool} at {sizes_m_fool}. No floor is borrowed across rungs any more:
the 2026-09-11 overnight added a chesterton replicate pair at 8B and at 14B in both families, so
each rung in the overlay has a same-size pair behind its family's floor. The seed-split floor is
the second floor: inside one base run,
the mean over sample 0 against the mean over sample 1, maximised over that family's base runs. It
is computed for both families over the same {len(CF)} authors ({int(FLOORS.n_seed_runs_overlay.max())} Qwen base runs
against {int(FLOORS[FLOORS.family == 'Ministral3'].n_seed_runs_overlay.max())} Ministral ones) so that the two families are not judged against
maxima taken over different numbers of runs; the floor over every Qwen base run in the study is
carried in the same table as floor_seed_all_runs and is larger. The floor quoted for a family is
the larger of the two floors available to it, and a contrast smaller than its floor is marked
within_noise whatever its q. On Ministral the regeneration floor sits below the seed-split floor on
{'every measure that carries both' if m_regen_below_seed else 'some but not all measures that carry both'},
so the seed-split floor is the one in force there; on Qwen the two alternate, and floor_used names
which one applies to each row. A gens.jsonl length-only fallback for the Ministral replicates is
still in the script for words, len_ratio and truncated, and it did not fire
({n_mlf_used} fallback rows used): those measures now have {n_regen_m_len} scored Ministral pairs
of their own. The judged rows have no seed-split floor at all, because they exist on sample 0
only, so their floor is the regeneration floor and nothing else.

Gap-closing diagnostic. Gain (adapter minus base) and head-room (ceiling minus base) both contain
the base term, so a slope near 1 arises whenever the adapter endpoint is insensitive to where the
base started. gap_closing_diagnostics.csv therefore regresses the adapter endpoint on the base
level directly: its slope a, and 1 - a, is the mechanical part of the gap-closing slope when the
ceiling varies little across points, and the table reports the standard deviations of ceiling,
base and adapter so the reader can see which term is doing the work.

Gap closing. The ceiling for an author is the mean of that author's own held-out passages
(references.parquet, group = source, {int(refs[refs.group == 'source'].groupby(['author', 'run']).size().median())} passages per author per run)
on the same measure; it is identical across runs, so it is one number per author. Head-room is
ceiling minus the base mean; gain is the brief-paired adapter minus base. The fit is OLS over the
{int(gap_lr.n_points)} author x rung x family points with a point bootstrap CI, an author-cluster bootstrap
CI ({len(CF)} clusters, so it is wide), and a leave-one-author-out range. The same fit over the full
Qwen3 sweep ({int(gap_lr_full.n_points.iloc[0]) if len(gap_lr_full) else 0} points, {n_gapfull_authors} authors x 3 sizes) is reported as a
supplement.

Equivalence. For each author x rung x measure the two families' adapter endpoints are paired by
brief; TOST bounds are +/- the larger of the two families' floors, and the standard error is the
paired standard deviation over briefs divided by the root of the brief count.

Mixed models. lib.mixed_model (statsmodels MixedLM), gain ~ rung * fam_m with a random intercept
per author. There are {len(CF)} authors, so the random-effect variance is descriptive only.
"""

reading = f"""
Unit of replication. {len(CF)} authors, which is the whole Ministral 3 sample. Every cross-family
statement in this folder rests on {', '.join(CF)}, and the brief-level intervals are much narrower
than the author-level uncertainty they sit inside. The adapters were fitted on {train_ex_txt}
examples respectively (train_examples in run_level_family.csv), so the corpus-size axis is not
crossed with family here.

What the numbers say, conservatively.

1. The voice gain is not a family-level effect in these {len(CF)} authors. On luar_cos_ref, of the {sc_lr_q['n']}
Qwen3 author x rung cells {sc_lr_q['up']} move toward the author beyond the floor at q < 0.05
({', '.join(sc_lr_q['authors_up']) or 'none'}), {sc_lr_q['dn']} move away
({', '.join(sc_lr_q['authors_dn']) or 'none'}) and {sc_lr_q['noise']} sit inside the floor; of the {sc_lr_m['n']}
Ministral cells {sc_lr_m['up']} move toward the author ({', '.join(sc_lr_m['authors_up']) or 'none'}),
{sc_lr_m['dn']} move away ({', '.join(sc_lr_m['authors_dn']) or 'none'}) and {sc_lr_m['noise']} sit
inside the floor. Cells that clear the floor without clearing BH-FDR fall into none of those
counts. Qwen3 gains run
{fmt(lr_q.gain.min(), 3)} to {fmt(lr_q.gain.max(), 3)} (floor {fmt(float(floor_of('luar_cos_ref', 'Qwen3')), 3)})
and Ministral gains {fmt(lr_m.gain.min(), 3)} to {fmt(lr_m.gain.max(), 3)}
(floor {fmt(float(floor_of('luar_cos_ref', 'Ministral3')), 3)}, and that floor is the smaller of the
two, so a Ministral cell clears its floor more easily than a Qwen one of the same size). The sign
tracks the author rather than the family: with {len(CF)} authors that is a description of
{len(CF)} cases, not a rate.

1b. Scale. The rung term in the mixed model on luar_cos_ref gain is
{fmt(mx_lr_rung.estimate, 4) if mx_lr_rung is not None else 'n/a'}
[{fmt(mx_lr_rung.ci_low, 4) if mx_lr_rung is not None else 'n/a'}, {fmt(mx_lr_rung.ci_high, 4) if mx_lr_rung is not None else 'n/a'}]
per rung and the rung x family interaction is
{fmt(mx_lr_int.estimate, 4) if mx_lr_int is not None else 'n/a'}
[{fmt(mx_lr_int.ci_low, 4) if mx_lr_int is not None else 'n/a'}, {fmt(mx_lr_int.ci_high, 4) if mx_lr_int is not None else 'n/a'}],
both against a floor of {fmt(float(floor_of('luar_cos_ref', 'Qwen3')), 3)} for one whole rung's worth of
movement. Read that as no size trend large enough to see at this floor, not as evidence that the
size effect is zero. The random intercept is estimated from {len(CF)} groups (n_groups and
re_var_author in mixed_models.csv), so the interaction p-values are descriptive.

2. {n_noise} of the {n_gain_tot} adapter-vs-base contrasts are smaller than their own noise floor and are
reported as within noise regardless of q; {n_gain_sig} clear the floor and survive BH-FDR at q < 0.05
within this script's family of {n_gain_tot} gain tests. The remainder clear the floor without
clearing the correction. Read the floor column before the q column, and note that q here is
corrected within one script, not across the programme (see 22_multiple_comparisons_and_sensitivity).

3. The gap-closing slope on luar_cos_ref is {fmt(gap_lr.slope, 3)} [{fmt(gap_lr.slope_lo, 3)}, {fmt(gap_lr.slope_hi, 3)}]
(author-cluster interval [{fmt(gap_lr.slope_lo_authorclust, 3)}, {fmt(gap_lr.slope_hi_authorclust, 3)}], leave-one-author-out
range {fmt(gap_lr.loo_slope_min, 3)} to {fmt(gap_lr.loo_slope_max, 3)}), and on wegmann_cos_ref it is
{fmt(gap_wg.slope, 3)} [{fmt(gap_wg.slope_lo, 3)}, {fmt(gap_wg.slope_hi, 3)}], against a slope of 1 for a mechanism that
closes the whole distance to the author. Read this with the diagnostic, not on its own: gain and
head-room share the base term, so the slope is close to 1 exactly when the adapter lands in the
same place whatever the base did. Regressing the adapter endpoint on the base level gives a slope
of {fmt(gd_lr.slope_adapter_on_base, 3)} [{fmt(gd_lr.ci_low, 3)}, {fmt(gd_lr.ci_high, 3)}] on luar_cos_ref and
{fmt(gd_wg.slope_adapter_on_base, 3)} [{fmt(gd_wg.ci_low, 3)}, {fmt(gd_wg.ci_high, 3)}] on wegmann_cos_ref, with the
adapter endpoint varying by {fmt(gd_lr.sd_adapter, 3)} (SD) against {fmt(gd_lr.sd_base, 3)} for the base and
{fmt(gd_lr.sd_ceiling, 3)} for the ceiling. The honest statement is about where the adapter arrives, not
about a distance it travels: the endpoint is largely independent of the starting point, and the
intercept {fmt(gap_lr.intercept, 3)} [{fmt(gap_lr.intercept_lo, 3)}, {fmt(gap_lr.intercept_hi, 3)}] is what the adapter
buys once there is no head-room left. With {int(gap_lr.n_points)} points and three authors this is a
descriptive slope, not an estimate of a population parameter.

4. Equivalence is not established by a wide interval. {n_equiv} of {n_tost} endpoint comparisons pass TOST
at the floor-width bound and {n_exceed} have a difference larger than the bound; the rest are simply
undecided at this sample size. Do not read a failed TOST as a family difference or a passed TOST
as identity.

5. The construction cost is the part that appears in both families. On per (proposition echo, lower
is better) {sc_pe_q['up']} of {sc_pe_q['n']} Qwen cells and {sc_pe_m['up']} of {sc_pe_m['n']} Ministral cells get worse
beyond the floor while {sc_pe_q['dn']} and {sc_pe_m['dn']} get better; on hapax_w300 the adapter narrows
vocabulary in {sc_hx_q['dn']} of {sc_hx_q['n']} Qwen cells and {sc_hx_m['dn']} of {sc_hx_m['n']} Ministral cells, and the
Ministral mean is the larger of the two (Qwen {fmt(GAIN[(GAIN.measure == 'hapax_w300') & (GAIN.family == 'Qwen3')].gain.mean(), 3)}
mean against Ministral {fmt(GAIN[(GAIN.measure == 'hapax_w300') & (GAIN.family == 'Ministral3')].gain.mean(), 3)},
Cohen's d down to {fmt(GAIN[GAIN.measure == 'hapax_w300'].cohens_d.min(), 2)}). Those are counts of
author x rung cells over {len(CF)} authors, not a rate over authors, and the two families' floors
differ, so read this as the narrowing and the echo cost being present in both families rather than
as a measured family difference. Proposition echo is close to permutation-invariant, so per
registers restatement between sentences and not the order they arrive in.

6. The judged rows now exist in both families, and they say different things. On judged brief
coverage, pooled over the three shared authors and brief-paired, the adapter costs
{jline('coverage', 'Qwen3')} on Qwen3 and {jline('coverage', 'Ministral3')} on Ministral 3
(judged_adapter_minus_base.csv), against coverage floors of
{fmt(float(floor_of('coverage', 'Qwen3')), 2)} and {fmt(float(floor_of('coverage', 'Ministral3')), 2)}
points. {cov_noise_q} of the {cov_rungs_q} pooled Qwen3 rungs sit inside the Qwen3 floor and
{cov_noise_m} of the {cov_rungs_m} Ministral 3 rungs sit inside the larger Ministral 3 floor. The
Qwen3 contrast is larger in absolute size than the Ministral 3 one at
{'every matched rung' if jbigger('coverage') else 'some but not all matched rungs'}. That is a
description of these {len(CF)} authors and two recipes, not a family law: the two families were
tuned differently and their floors differ by a factor of
{fmt(float(floor_of('coverage', 'Ministral3')) / float(floor_of('coverage', 'Qwen3')), 1)}.
On the 2AFC fool rate the adapter moves it
{jline('fool_vs_source', 'Qwen3')} on Qwen3 and {jline('fool_vs_source', 'Ministral3')} on
Ministral 3, against floors of {fmt(float(floor_of('fool_vs_source', 'Qwen3')), 3)} and
{fmt(float(floor_of('fool_vs_source', 'Ministral3')), 3)}; {fool_noise_q} of {fool_rungs_q} Qwen3
rungs and {fool_noise_m} of {fool_rungs_m} Ministral 3 rungs sit inside their own family's floor.
Both are readings from one pair of judges whose own levels differ by a factor of about three
(16_judges, afc_rates_by_judge.csv), and cells.parquet averages the two judges into one
fool_vs_source value, so the per-judge split lives in 16_judges and not here. The sign and the
ordering across rungs are what this supports, not the level. {n_judged_noise} of the
{n_judged_cells} per-author judged contrasts sit inside their own family's floor.

What would overturn this. A fourth and fifth author in the second family would move the
author-level uncertainty more than any additional brief could: every cross-family number here
rests on {len(CF)} authors. A second judge pair, or a human 2AFC panel, would settle whether the
judged rows are measuring anything a reader would call adherence or voice; the fool rate in
particular is a judge endpoint, not a human one. The Ministral adapters are served as merged F16
weights rather than runtime LoRA, so a difference between families is a difference between two
whole serving paths, not between two adapters.

What this does not show. It does not show that one family emulates authors better than the other:
the second family was deliberately not tuned, its judge rows come from a later batch than the
Qwen3 ones even though the judges, prompts and protocol are the same, and its truncation gate was
report-only. It says nothing about arms other than A0.
"""

caveats = [
    f"The gap-closing regression is partly mechanical: gain and head-room share the base term. With the ceiling varying by {fmt(gd_lr.sd_ceiling, 3)} (SD) against {fmt(gd_lr.sd_base, 3)} for the base on luar_cos_ref, a slope near 1 is what an adapter endpoint that ignores its starting point produces. gap_closing_diagnostics.csv gives the adapter-on-base regression that says so directly; quote that, or quote the slope only alongside it.",
    f"{n_singular} of the {n_mixfits} mixed models have a singular author random-effect variance (singular_re in mixed_models.csv). Whatever that count, the random intercept is fitted over {len(CF)} groups, so its variance is descriptive rather than an estimate of between-author spread, and the p-values on the interaction terms should be read the same way.",
    f"The regeneration floors now rest on same-size pairs in both families: {npairs_m} Ministral 3 pairs at {sizes_m} and {npairs_q} Qwen3 pairs at {sizes_q} on the automatic measures, {npairs_m_cov} and {npairs_q_cov} on coverage, {npairs_m_fool} and {npairs_q_fool} on fool_vs_source (floor_pairs.csv lists every pair and its rung). No floor is borrowed across rungs. Each rung's floor is still one pair per family per size, and every 8B and 14B pair is chesterton, so a floor is an estimate from one author at that rung.",
    f"Both families are judged, but on {len(CF)} authors only, and the Ministral 3 judge records come from a later batch (2026-09-10 and 2026-09-11) than the Qwen3 ones. The judges, prompts, item orders and sample-0 protocol are identical, so this is one instrument read twice, but nothing here measures judge drift between batches.",
    f"Coverage and fool_vs_source are LLM-judged relative instruments, not ground truth. Coverage is not a check that the brief was covered and the fool rate is not a measurement of how often a reader would be fooled; the two judges differ by a factor of about three on the fool rate (16_judges). Ten runs' coverage and 2AFC rows were error rows from the 2026-09-09 credit outage and are being regenerated; until that rerun lands, a missing judged cell here is a missing judge call, not a run that scored zero.",
    f"The judged rows exist on sample 0 only, so they have no seed-split floor and no within-cell test-retest of their own. Their floor is the regeneration floor alone: {fmt(float(floor_of('coverage', 'Qwen3')), 2)} and {fmt(float(floor_of('coverage', 'Ministral3')), 2)} coverage points, {fmt(float(floor_of('fool_vs_source', 'Qwen3')), 3)} and {fmt(float(floor_of('fool_vs_source', 'Ministral3')), 3)} on the fool rate. The Ministral floors are the larger of the two on both rows, so a Ministral judged contrast has to be bigger to clear its own noise.",
    "Two of the three overlay authors are not period authors (doctorow contemporary, patrick_v2 private) and the pipeline anchors every author against the same fourteen-author period stranger pool, so their position relative to other authors, and geo_index with it, is measured against a different century. The ceilings and the *_cos_ref anchors used here come from each author's own held-out passages and do not depend on that pool; 23_register_matched_pool holds the register-matched comparison, where contemporary and private authors move down by more than the adapter gain.",
    f"Ministral adapters are served as merged F16 weights (adapter_served = {fm.adapter_served}) while Qwen adapters are runtime LoRA (adapter_served = {fq.adapter_served}); the Ministral checkpoints are FP8 and were dequantised for training and for serving. A family contrast therefore contains a serving-path contrast.",
    f"The Ministral training probe is far weaker than the Qwen one (probe delta mean {fmt(fm.probe_delta_mean, 3)}, range {fmt(fm.probe_delta_min, 3)} to {fmt(fm.probe_delta_max, 3)}, against {fmt(fq.probe_delta_mean, 3)} and {fmt(fq.probe_delta_min, 3)} to {fmt(fq.probe_delta_max, 3)} on Qwen), and {len(probe_pos)} adapter ({probe_pos_txt}) has a positive probe delta, meaning its training probe moved the wrong way and the fit changed nothing the probe could measure. The recipe was not tuned for the family; that is the design, not a defect, but it caps how much of a null result can be attributed to the family rather than to the recipe.",
    f"Truncation was gated on Qwen and report-only on Ministral. {len(trunc_over)} runs in run_level_family.csv sit above the 20 percent truncation criterion ({trunc_over_txt}), {n_gate_ok_over} of them still carrying gate_generation_ok = True, so the stored gate verdict and the recorded percentage do not agree on every run. truncated_pct pools all arms while the cells analysed here are A0 only; the A0 rates are trunc_rate_A0_base and trunc_rate_A0_adapter in family_summary.csv. Truncation is not balanced across families, so any measure that moves with length is confounded with it here (see 17_length_truncation).",
    "Size rungs are matched by position on the ladder, not by parameter count: the Ministral 3B run stands opposite the Qwen 4B run. The mixed models use the rung index; a fit on log parameters would put those two points 0.4 log units apart.",
    "The Qwen3 1.7B run on patrick_v2 has no Ministral counterpart and is excluded from every paired table.",
    "Ceilings come from the authors' own held-out passages scored inside each run; the ref-group passages score higher than the source-group passages on the same anchor (self-inclusion), so the source group is used and the ceiling is the conservative choice of the two.",
]

write_readme(OUTD, "18_cross_family - Qwen3 against Ministral 3", what, how, reading, caveats, top_tables, figs,
             extra=f"Runtime {runtime:.1f} s. Rows in cells.parquet used: {len(cfp)} (arm A0, non-replicate, three overlay authors, matched rungs).")

print(f"[18_cross_family] done in {runtime:.1f}s -> {OUTD}")
print(f"  contrasts {len(GAIN)}, within-noise {n_noise}, survive FDR+floor {n_gain_sig}")
print(f"  gap slope luar_cos_ref {gap_lr.slope:.3f} [{gap_lr.slope_lo:.3f}, {gap_lr.slope_hi:.3f}], "
      f"wegmann {gap_wg.slope:.3f} [{gap_wg.slope_lo:.3f}, {gap_wg.slope_hi:.3f}]")
print(f"  TOST equivalent {n_equiv}/{n_tost}, exceeds bound {n_exceed}")
print(f"  judged cells A0: coverage Qwen3 {int(fq.coverage_cells_A0)} / Ministral3 {int(fm.coverage_cells_A0)}; "
      f"fool Qwen3 {int(fq.fool_cells_A0)} / Ministral3 {int(fm.fool_cells_A0)}; "
      f"2AFC-judged runs {int(fq.n_runs_judged_2afc)}/{int(fq.n_runs_total)} and {int(fm.n_runs_judged_2afc)}/{int(fm.n_runs_total)}")
print(f"  coverage adapter-minus-base (pooled, {len(CF)} authors): Qwen3 {jline('coverage', 'Qwen3')} | "
      f"Ministral3 {jline('coverage', 'Ministral3')}")
print(f"  fool adapter-minus-base (pooled, {len(CF)} authors): Qwen3 {jline('fool_vs_source', 'Qwen3')} | "
      f"Ministral3 {jline('fool_vs_source', 'Ministral3')}")
print(f"  judged floors: coverage {fmt(float(floor_of('coverage', 'Qwen3')), 3)} / "
      f"{fmt(float(floor_of('coverage', 'Ministral3')), 3)} ({npairs_q_cov} pairs at {sizes_q_cov}; "
      f"{npairs_m_cov} pairs at {sizes_m_cov}); fool {fmt(float(floor_of('fool_vs_source', 'Qwen3')), 3)} / "
      f"{fmt(float(floor_of('fool_vs_source', 'Ministral3')), 3)}")
print(f"  regeneration pairs luar_cos_ref: Qwen3 {npairs_q} at {sizes_q}; Ministral3 {npairs_m} at {sizes_m}")
