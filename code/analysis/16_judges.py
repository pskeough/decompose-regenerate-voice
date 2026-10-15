"""16_judges.py -- what the LLM judges actually measure.

Rubric: shuffle calibration per author, judge and family, inter-judge quadratic-weighted kappa,
rubric-order effect, factor structure of the twelve subscores, correlation of each subscore
with the mechanical measures, and the "judge ranks the bare model above the author" check.
2AFC: fool-vs-source and win-vs-A0 rates by configuration with Wilson and brief-cluster
intervals, per family and per judge, judge agreement and judge self-consistency, and the
relation of the fool rate to LUAR and to proposition echo. Coverage by configuration.

Both model families carry judge data. The Ministral 3 rubric, 2AFC and coverage records were
produced on 2026-09-10 and 2026-09-11 with the same two judges, the same prompts and the same
sample-0 protocol as the Qwen3 records, so every table here carries `family` as a grouping
column and the Qwen3-versus-Ministral3 comparison is made on the three authors run in both
families (chesterton, doctorow, patrick_v2).

Reads data/ only; writes analysis/16_judges/ only.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (ARMS, EVAL, MASTER, RUNS, VARIABLES, bh_fdr, cluster_bootstrap,  # noqa: E402
                 load_all, load_series, main_cells, md_table, outdir, parse_run,
                 replicate_floor, savefig, write_readme, write_table)

OUTD = outdir("16_judges")
# the three authors generated in both families; every cross-family statement is about these
SHARED = ["chesterton", "doctorow", "patrick_v2"]
FAMS = ["Qwen3", "Ministral3"]
POOL = "both families"
SCOPES = [POOL] + FAMS
# measures with a judged value and a replicate pair, so a judged contrast can be read against a floor
JUDGE_MEASURES = ["coverage", "fool_vs_source", "rubric_C", "rubric_S"]
C_ITEMS = [f"C{i}" for i in range(1, 6)]
S_ITEMS = [f"S{i}" for i in range(1, 8)]
ITEMS = C_ITEMS + S_ITEMS
ITEM_LABEL = {"C1": "referent clarity", "C2": "advancement", "C3": "event/state consistency",
              "C4": "arc completion", "C5": "circling", "S1": "opening move", "S2": "figure execution",
              "S3": "figure restraint", "S4": "register movement", "S5": "sentence-level stopping",
              "S6": "perspective control", "S7": "immersion"}
JUDGE_SHORT = {"google/gemini-3.1-flash-lite-preview": "gemini", "minimax/minimax-m3": "minimax"}
Z95 = 1.959963984540054


# ------------------------------------------------------------------ small helpers
def wilson(k, n, z=Z95):
    """Wilson score interval for a binomial proportion."""
    k, n = float(k), float(n)
    if n <= 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    # clamp so the interval always contains the point estimate (float noise at k = 0)
    return (p, min(p, max(0.0, centre - half)), max(p, min(1.0, centre + half)))


def qwk(a, b, lo=0, hi=10):
    """Quadratic-weighted kappa on integer ratings in [lo, hi]."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = np.rint(a[m]).astype(int), np.rint(b[m]).astype(int)
    if len(a) < 5:
        return np.nan, len(a)
    a = np.clip(a, lo, hi)
    b = np.clip(b, lo, hi)
    if len(set(a.tolist())) < 2 and len(set(b.tolist())) < 2:
        return np.nan, len(a)
    try:
        k = cohen_kappa_score(a, b, weights="quadratic", labels=list(range(lo, hi + 1)))
    except Exception:
        return np.nan, len(a)
    return float(k), int(len(a))


def cluster_boot_stat(keys, values, fn, n=1000, seed=0):
    """Bootstrap a statistic over clusters given parallel key/value arrays."""
    keys = np.asarray(keys)
    uk, inv = np.unique(keys, return_inverse=True)
    idx_by_cluster = [np.where(inv == i)[0] for i in range(len(uk))]
    point = fn(values)
    if len(uk) < 3:
        return float(point), np.nan, np.nan
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n):
        pick = rng.integers(0, len(uk), size=len(uk))
        sel = np.concatenate([idx_by_cluster[i] for i in pick])
        boots.append(fn(values[sel]))
    boots = np.asarray(boots, float)
    return float(point), float(np.nanquantile(boots, 0.025)), float(np.nanquantile(boots, 0.975))


def two_sample_boot_diff(x, y, n=2000, seed=0):
    """Bootstrap CI for mean(x) - mean(y) with independent resampling of each sample."""
    x = np.asarray([v for v in x if v == v], float)
    y = np.asarray([v for v in y if v == v], float)
    if len(x) < 2 or len(y) < 2:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    bx = x[rng.integers(0, len(x), size=(n, len(x)))].mean(axis=1)
    by = y[rng.integers(0, len(y), size=(n, len(y)))].mean(axis=1)
    d = bx - by
    return (float(x.mean() - y.mean()), float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975)))


def centre_within(df, col, by):
    """Value minus its group mean; strips between-configuration variance."""
    return df[col] - df.groupby(by)[col].transform("mean")


# ------------------------------------------------------------------ load
print("loading ...")
cells, runs, authors, briefs, refs = load_all()

# rubric records, one row per (run, id, sample, judge, order); the mistral judge is excluded
rub_rows = []
for path in sorted(glob.glob(os.path.join(EVAL, "judge", "*.jsonl"))):
    if "mistral" in os.path.basename(path):
        continue
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            d.pop("evidence", None)
            d.pop("raw", None)
            rub_rows.append(d)
rub = pd.DataFrame(rub_rows)
rub["judge_short"] = rub.judge.map(JUDGE_SHORT).fillna(rub.judge)
rub["ok"] = rub.ok.fillna(False).astype(bool)
n_rub_all = len(rub)
n_rub_fail = int((~rub.ok).sum())
rub_ok = rub[rub.ok].copy()
rub_ok["C_mean"] = rub_ok[C_ITEMS].mean(axis=1)
rub_ok["S_mean"] = rub_ok[S_ITEMS].mean(axis=1)
rub_ok["all_mean"] = rub_ok[ITEMS].mean(axis=1)

# family of every judged run, read off the master tables rather than guessed from the run name:
# runs.csv covers the main ladder, cells_series.parquet the Qwen3 corpus-size adapters. The
# calibration rows ("<author> CAL") belong to no run and keep a null family.
_meta = runs.set_index("run")[["family", "params_b", "kind", "replicate"]].copy()
_meta["on_ladder"] = True
_ser = load_series()
if len(_ser):
    _s = _ser.drop_duplicates("run").set_index("run")[["family", "params_b", "kind", "replicate"]].copy()
    _s["on_ladder"] = False
    _meta = pd.concat([_meta, _s[~_s.index.isin(_meta.index)]])
RUNMETA = _meta
rub_ok["family"] = rub_ok.run.map(RUNMETA["family"])
rub_ok["params_b"] = rub_ok.run.map(RUNMETA["params_b"])
rub_ok["run_kind"] = rub_ok.run.map(RUNMETA["kind"])
rub_ok["on_ladder"] = rub_ok.run.map(RUNMETA["on_ladder"]).fillna(False).astype(bool)
rub_ok["replicate"] = rub_ok.run.map(RUNMETA["replicate"]).fillna(False).astype(bool)

_gen_all = rub_ok[rub_ok.kind == "gen"].copy()
n_gen_replicate = int(_gen_all.replicate.sum())
# the programme's convention is non-replicate cells; the replicate base runs are the floor material
gen_rub = _gen_all[~_gen_all.replicate].copy()
cal_rub = rub_ok[rub_ok.kind.isin(["author", "shuffled"])].copy()
n_gen_series = int((~gen_rub.on_ladder).sum())
n_gen_unmapped = int(gen_rub.family.isna().sum())
gen_fam_counts = gen_rub[gen_rub.on_ladder].groupby("family", observed=True).size().to_dict()


def gen_scope(scope, authors_only=None):
    """Generation-side rubric rows for one scope. `both families` is every judged non-replicate
    generation; a family name is that family's main-ladder runs only, so the two families are
    compared on the same design (the Qwen3 corpus-size adapters are off the ladder and enter
    only the pool)."""
    g = gen_rub if scope == POOL else gen_rub[(gen_rub.family == scope) & gen_rub.on_ladder]
    if authors_only is not None:
        g = g[g.author.isin(authors_only)]
    return g

# rubric cells: judging ran on arm A0 sample 0 only; the master table broadcasts the same
# record over every arm of the run, so restrict to A0 before joining anything to it.
rc = cells[(cells.arm == "A0") & (cells["sample"] == 0) & (~cells.replicate) & cells.rubric_S.notna()].copy()
n_rubric_cells_all_arms = int(cells.rubric_S.notna().sum())
n_rubric_cells_a0 = len(rc)
rc_fam_cells = rc.groupby("family", observed=True).size().to_dict()
rc_fam_authors = {f: int(g.author.nunique()) for f, g in rc.groupby("family", observed=True)}


def rc_scope(scope):
    """Cell-level rubric rows for one scope (arm A0, sample 0, non-replicate)."""
    return rc if scope == POOL else rc[rc.family == scope]

# 2AFC raw records
afc_frames = []
for path in sorted(glob.glob(os.path.join(RUNS, "*", "judge.jsonl"))):
    run = os.path.basename(os.path.dirname(path))
    try:
        d = pd.read_json(path, lines=True)
    except ValueError:
        continue
    if len(d) == 0:
        continue
    d["run"] = run
    afc_frames.append(d)
afc_raw = pd.concat(afc_frames, ignore_index=True)
KEY = ["run", "id", "arm", "sample", "judge", "comparison"]
n_afc_raw = len(afc_raw)

# duplicated keys are retries; count how often a repeat of the same item flipped the verdict
dup_mask = afc_raw.duplicated(KEY, keep=False)
dups = afc_raw[dup_mask & afc_raw.picked_gen.notna()]
dgrp = dups.groupby(KEY).picked_gen.agg(["nunique", "size"])
n_repeat_pairs = int((dgrp["size"] >= 2).sum())
n_repeat_flip = int(((dgrp["size"] >= 2) & (dgrp["nunique"] > 1)).sum())

afc = afc_raw.sort_values("picked_gen", na_position="last").drop_duplicates(KEY, keep="first").copy()
afc["judge_short"] = afc.judge.map(JUDGE_SHORT).fillna(afc.judge)
meta = pd.DataFrame([m for m in (parse_run(r) for r in afc.run.unique()) if m])
afc = afc.merge(meta, on="run", how="left")
n_afc_unparsed = int(afc.family.isna().sum())
afc_use = afc[afc.family.notna() & afc.arm.isin(ARMS) & (~afc.replicate.astype(bool)) & (afc["sample"] == 0)].copy()
n_afc_use = len(afc_use)
n_afc_missing = int(afc_use.picked_gen.isna().sum())
afc_ok = afc_use[afc_use.picked_gen.notna()].copy()
afc_ok["picked_gen"] = afc_ok.picked_gen.astype(int)
afc_fam_counts = afc_ok.groupby("family", observed=True).size().to_dict()
afc_fam_runs = {f: int(g.run.nunique()) for f, g in afc_ok.groupby("family", observed=True)}

print(f"  rubric records {n_rub_all} ({n_rub_fail} unparsed); 2AFC raw {n_afc_raw}, usable {n_afc_use}")
print(f"  families judged: rubric {sorted(k for k in gen_fam_counts)}, 2AFC {sorted(afc_fam_counts)}")

# ================================================================== 0. replicate floors for the judged measures
print("0. replicate floors for the judged measures ...")
floor_rows = []
for meas in JUDGE_MEASURES:
    t = replicate_floor(cells, meas)
    for _, r in t.iterrows():
        pa = parse_run(str(r.pair).split(" vs ")[0])
        floor_rows.append({"measure": meas, "family": r.family, "pair": r.pair,
                           "params_b": pa["params_b"] if pa else np.nan, "n_briefs": int(r.n),
                           "abs_mean_diff": float(r.abs_mean_diff)})
floor_pairs = pd.DataFrame(floor_rows)
write_table(floor_pairs, os.path.join(OUTD, "judge_replicate_floor_pairs.csv"), floats=5)
floors_tab = (floor_pairs.groupby(["measure", "family"], observed=True)
              .agg(n_pairs=("pair", "size"), floor=("abs_mean_diff", "max"),
                   sizes_b=("params_b", lambda s: ", ".join(f"{v:g}B" for v in sorted(set(s.dropna())))))
              .reset_index())
write_table(floors_tab, os.path.join(OUTD, "judge_replicate_floors.csv"), floats=5)
FL = {(r.measure, r.family): float(r.floor) for r in floors_tab.itertuples()}


def floor_of(measure, family):
    v = FL.get((measure, family), np.nan)
    return float(v) if v == v else np.nan


def floor_sizes(measure, family):
    s = floors_tab[(floors_tab.measure == measure) & (floors_tab.family == family)]
    return str(s.sizes_b.iloc[0]) if len(s) else "none"


def floor_pairs_n(measure, family):
    s = floors_tab[(floors_tab.measure == measure) & (floors_tab.family == family)]
    return int(s.n_pairs.iloc[0]) if len(s) else 0


# ================================================================== 1. rubric calibration
print("1. rubric calibration ...")
cal_rows = []
for scope in SCOPES:
    gsc = gen_scope(scope)
    if not len(gsc):
        continue
    for (au, jshort), g in cal_rub.groupby(["author", "judge_short"], observed=True):
        ga = g[g.kind == "author"]
        gs = g[g.kind == "shuffled"]
        gg = gsc[(gsc.author == au) & (gsc.judge_short == jshort)]
        if not len(gg):
            continue
        row = {"family": scope, "author": au, "judge": jshort, "n_author_items": len(ga),
               "n_shuffled_items": len(gs), "n_gen_records": len(gg), "n_gen_runs": int(gg.run.nunique()),
               "author_mean": ga.all_mean.mean(), "shuffled_mean": gs.all_mean.mean(), "gen_mean": gg.all_mean.mean()}
        for it in ["C2", "C5"]:
            d, lo, hi = two_sample_boot_diff(ga[it], gs[it], seed=abs(hash((au, jshort, it))) % 10000)
            row[f"gap_{it}_author_minus_shuffled"] = d
            row[f"gap_{it}_lo"] = lo
            row[f"gap_{it}_hi"] = hi
        d, lo, hi = two_sample_boot_diff(ga.all_mean, gg.all_mean, seed=7)
        row["author_minus_gen"] = d
        row["author_minus_gen_lo"] = lo
        row["author_minus_gen_hi"] = hi
        # the gate has two halves, and they fail for different reasons: the shuffle separation is
        # a property of the calibration items alone (identical across families), the second half
        # asks whether the author still outscores this family's generations
        row["shuffle_separation_pass"] = bool(
            max(row["gap_C2_author_minus_shuffled"], row["gap_C5_author_minus_shuffled"]) >= 3)
        row["author_above_gen"] = bool(row["author_mean"] > row["gen_mean"])
        row["shuffle_gate_pass"] = bool(row["shuffle_separation_pass"] and row["author_above_gen"])
        cal_rows.append(row)
cal_tab = pd.DataFrame(cal_rows).sort_values(["family", "author", "judge"]).reset_index(drop=True)
write_table(cal_tab, os.path.join(OUTD, "rubric_calibration.csv"))
cal_pool = cal_tab[cal_tab.family == POOL]
n_gate_pass = int(cal_pool.shuffle_gate_pass.sum())
n_gate_rows = len(cal_pool)
n_author_below_gen = int((cal_pool.author_minus_gen < 0).sum())
# the same gate read per family: does the instrument behave the same on the second family
cal_by_fam = (cal_tab.groupby("family", observed=True)
              .agg(n_author_x_judge_cells=("shuffle_gate_pass", "size"),
                   n_authors=("author", "nunique"),
                   gate_passes=("shuffle_gate_pass", "sum"),
                   shuffle_separation_passes=("shuffle_separation_pass", "sum"),
                   author_above_gen=("author_above_gen", "sum"),
                   min_gap_C2=("gap_C2_author_minus_shuffled", "min"),
                   min_gap_C5=("gap_C5_author_minus_shuffled", "min"),
                   mean_author_minus_gen=("author_minus_gen", "mean"),
                   min_author_minus_gen=("author_minus_gen", "min"),
                   n_author_below_gen=("author_minus_gen", lambda s: int((s < 0).sum())))
              .reset_index())
write_table(cal_by_fam, os.path.join(OUTD, "rubric_calibration_by_family.csv"))
cal_min = cal_tab[cal_tab.family == "Ministral3"]
n_gate_pass_m = int(cal_min.shuffle_gate_pass.sum())
n_gate_rows_m = len(cal_min)
n_sep_pass_m = int(cal_min.shuffle_separation_pass.sum())
n_above_gen_m = int(cal_min.author_above_gen.sum())


def _gate_reason(r):
    bits = []
    if not r.shuffle_separation_pass:
        bits.append(f"shuffle gap {max(r.gap_C2_author_minus_shuffled, r.gap_C5_author_minus_shuffled):.2f} below 3")
    if not r.author_above_gen:
        bits.append(f"generations above the author by {-r.author_minus_gen:.2f}")
    return f"{r.author}/{r.judge} ({' and '.join(bits)})"


gate_fail_m = "; ".join(_gate_reason(r) for r in cal_min[~cal_min.shuffle_gate_pass].itertuples()) or "none"
cal_qwen = cal_tab[cal_tab.family == "Qwen3"]
n_gate_pass_q = int(cal_qwen.shuffle_gate_pass.sum())
n_gate_rows_q = len(cal_qwen)
n_sep_pass_q = int(cal_qwen.shuffle_separation_pass.sum())
n_above_gen_q = int(cal_qwen.author_above_gen.sum())
gate_fail_q = "; ".join(_gate_reason(r) for r in cal_qwen[~cal_qwen.shuffle_gate_pass].itertuples()) or "none"

# ================================================================== 2. inter-judge kappa
print("2. inter-judge kappa ...")
pair_key = ["run", "id", "sample", "order"]
kap_rows = []
for scope in SCOPES:
    gsc = gen_scope(scope)
    if not len(gsc):
        continue
    wide = gsc.pivot_table(index=pair_key, columns="judge_short", values=ITEMS, aggfunc="first")
    for it in ITEMS:
        sub = wide[it].dropna()
        if not len(sub):
            continue
        k, n = qwk(sub["gemini"], sub["minimax"])
        ids = np.array([i[1] for i in sub.index]) if len(sub) else np.array([])
        if len(sub) >= 20:
            pairs = np.column_stack([sub["gemini"].values, sub["minimax"].values])
            _, lo, hi = cluster_boot_stat(ids, pairs, lambda v: qwk(v[:, 0], v[:, 1])[0], n=400, seed=11)
        else:
            lo = hi = np.nan
        r = spearmanr(sub["gemini"], sub["minimax"])[0] if len(sub) >= 5 else np.nan
        kap_rows.append({"family": scope, "subscore": it, "label": ITEM_LABEL[it],
                         "block": "construction" if it in C_ITEMS else "craft",
                         "n_paired": n, "qwk_gemini_vs_minimax": k, "qwk_lo": lo, "qwk_hi": hi,
                         "spearman": float(r) if r == r else np.nan,
                         "mean_gemini": float(sub["gemini"].mean()), "mean_minimax": float(sub["minimax"].mean())})
kappa_tab = pd.DataFrame(kap_rows)
write_table(kappa_tab, os.path.join(OUTD, "rubric_interjudge_kappa.csv"))
kappa_pool = kappa_tab[kappa_tab.family == POOL].reset_index(drop=True)
kappa_fam = (kappa_tab.groupby("family", observed=True)
             .agg(n_subscores=("subscore", "size"), n_paired_min=("n_paired", "min"),
                  qwk_min=("qwk_gemini_vs_minimax", "min"), qwk_median=("qwk_gemini_vs_minimax", "median"),
                  qwk_max=("qwk_gemini_vs_minimax", "max")).reset_index())

# judge self-consistency across rubric order (same judge, fwd vs rev)
self_rows = []
for scope in SCOPES:
    gsc = gen_scope(scope)
    if not len(gsc):
        continue
    for jshort, g in gsc.groupby("judge_short", observed=True):
        w = g.pivot_table(index=["run", "id", "sample"], columns="order", values=ITEMS, aggfunc="first")
        for it in ITEMS:
            sub = w[it].dropna()
            if len(sub) < 20:
                continue
            k, n = qwk(sub["fwd"], sub["rev"])
            self_rows.append({"family": scope, "judge": jshort, "subscore": it, "label": ITEM_LABEL[it],
                              "n_paired": n, "qwk_fwd_vs_rev": k, "mean_fwd": float(sub["fwd"].mean()),
                              "mean_rev": float(sub["rev"].mean())})
self_tab = pd.DataFrame(self_rows)

# ================================================================== 3. order effect
print("3. rubric order effect ...")
ord_rows = []
for scope in SCOPES:
    gsc = gen_scope(scope)
    if not len(gsc):
        continue
    for jshort, g in gsc.groupby("judge_short", observed=True):
        w = g.pivot_table(index=["run", "id", "sample"], columns="order", values=ITEMS, aggfunc="first")
        ids = np.array([i[1] for i in w.index])
        for it in ITEMS:
            sub = w[it]
            m = sub["fwd"].notna() & sub["rev"].notna()
            f, r = sub["fwd"][m].values, sub["rev"][m].values
            if len(f) < 20:
                continue
            diff = r - f
            pt, lo, hi = cluster_boot_stat(ids[m.values], diff, np.mean, n=600, seed=3)
            try:
                p = float(wilcoxon(f, r, zero_method="zsplit").pvalue)
            except ValueError:
                p = np.nan
            ord_rows.append({"family": scope, "judge": jshort, "subscore": it, "label": ITEM_LABEL[it],
                             "n_paired": int(len(f)), "mean_fwd": float(f.mean()), "mean_rev": float(r.mean()),
                             "rev_minus_fwd": pt, "ci_low": lo, "ci_high": hi,
                             "mean_abs_shift": float(np.abs(diff).mean()),
                             "spearman_fwd_rev": float(spearmanr(f, r)[0]), "p": p})
order_tab = pd.DataFrame(ord_rows)
# BH-FDR inside each family of tests, which here means inside each scope
order_tab["q_bh"] = np.nan
for scope, g in order_tab.groupby("family", observed=True):
    order_tab.loc[g.index, "q_bh"] = bh_fdr(g.p.values)
order_tab = order_tab.merge(self_tab[["family", "judge", "subscore", "qwk_fwd_vs_rev"]],
                            on=["family", "judge", "subscore"], how="left")
write_table(order_tab, os.path.join(OUTD, "rubric_order_effect.csv"))
order_pool = order_tab[order_tab.family == POOL]
n_order_sig = int((order_pool.q_bh < 0.05).sum())
worst_order = order_pool.reindex(order_pool.rev_minus_fwd.abs().sort_values(ascending=False).index).iloc[0]
order_fam = (order_tab.groupby(["family", "judge"], observed=True)
             .agg(n_tests=("p", "size"), n_q_below_05=("q_bh", lambda s: int((s < 0.05).sum())),
                  max_abs_rev_minus_fwd=("rev_minus_fwd", lambda s: float(s.abs().max())),
                  mean_abs_shift=("mean_abs_shift", "mean")).reset_index())
write_table(order_fam, os.path.join(OUTD, "rubric_order_effect_by_family.csv"))
worst_order_m = None
_om = order_tab[order_tab.family == "Ministral3"]
if len(_om):
    worst_order_m = _om.reindex(_om.rev_minus_fwd.abs().sort_values(ascending=False).index).iloc[0]

# ================================================================== 4. factor structure
print("4. factor structure ...")
def parallel_pca(frame, seed=0, n_perm=500):
    X = frame[[f"rubric_{it}" for it in ITEMS]].dropna()
    Xs = (X - X.mean()) / X.std(ddof=1)
    corr = np.corrcoef(Xs.values, rowvar=False)
    eig = np.sort(np.linalg.eigvalsh(corr))[::-1]
    rng = np.random.default_rng(seed)
    V = Xs.values
    perm = []
    for _ in range(n_perm):
        P = np.column_stack([rng.permutation(V[:, j]) for j in range(V.shape[1])])
        perm.append(np.sort(np.linalg.eigvalsh(np.corrcoef(P, rowvar=False)))[::-1])
    thr = np.quantile(np.array(perm), 0.95, axis=0)
    nf = int((eig > thr).sum())
    sc = pd.DataFrame({"component": np.arange(1, len(eig) + 1), "eigenvalue": eig,
                       "parallel_p95": thr, "retained": eig > thr,
                       "var_explained": eig / eig.sum(), "cum_var_explained": np.cumsum(eig / eig.sum())})
    evals, evecs = np.linalg.eigh(corr)
    o = np.argsort(evals)[::-1]
    load = evecs[:, o[:max(nf, 2)]] * np.sqrt(evals[o[:max(nf, 2)]])
    ld = pd.DataFrame(load, index=ITEMS, columns=[f"PC{i+1}" for i in range(load.shape[1])])
    ld.insert(0, "label", [ITEM_LABEL[i] for i in ITEMS])
    ld = ld.reset_index().rename(columns={"index": "subscore"})
    return sc, ld, nf, int(len(X))


scree_frames, load_frames, N_FACTORS, n_pca_rows = [], [], {}, {}
for scope in SCOPES:
    fr = rc_scope(scope)
    if len(fr) < 60:
        continue
    sc, ld, nf, nrows = parallel_pca(fr)
    sc.insert(0, "family", scope)
    ld.insert(0, "family", scope)
    sc["n_passages"] = nrows
    scree_frames.append(sc)
    load_frames.append(ld)
    N_FACTORS[scope] = nf
    n_pca_rows[scope] = nrows
scree_all = pd.concat(scree_frames, ignore_index=True)
loadings = pd.concat(load_frames, ignore_index=True)
write_table(scree_all, os.path.join(OUTD, "rubric_pca_scree.csv"))
write_table(loadings, os.path.join(OUTD, "rubric_pca_loadings.csv"))
scree = scree_all[scree_all.family == POOL].reset_index(drop=True)
n_factors = N_FACTORS[POOL]

# ================================================================== 5. subscore vs mechanical measures
print("5. subscore vs mechanical measures ...")
MECH = ["per", "otd_js", "coverage", "luar_cos_source", "words"]
rows = []
for scope in SCOPES:
    fr = rc_scope(scope)
    for it in ITEMS + ["C", "S"]:
        col = f"rubric_{it}"
        for mech in MECH:
            d = fr[[col, mech, "run"]].dropna()
            if len(d) < 30:
                continue
            r_pool, p_pool = spearmanr(d[col], d[mech])
            dc = d.copy()
            dc["a"] = centre_within(dc, col, "run")
            dc["b"] = centre_within(dc, mech, "run")
            dw = dc[["a", "b"]].dropna()
            r_within = spearmanr(dw.a, dw.b)[0] if len(dw) > 30 else np.nan
            _, lo, hi = cluster_boot_stat(d.run.values, d[[col, mech]].values,
                                          lambda v: spearmanr(v[:, 0], v[:, 1])[0], n=300, seed=5)
            rows.append({"family": scope, "subscore": it, "label": ITEM_LABEL.get(it, "block mean"),
                         "measure": mech, "n": len(d), "spearman_pooled": float(r_pool), "ci_low": lo,
                         "ci_high": hi,
                         "spearman_within_run": float(r_within) if r_within == r_within else np.nan,
                         "p": float(p_pool)})
mech_tab = pd.DataFrame(rows)
mech_tab["q_bh"] = np.nan
for scope, g in mech_tab.groupby("family", observed=True):
    mech_tab.loc[g.index, "q_bh"] = bh_fdr(g.p.values)
write_table(mech_tab, os.path.join(OUTD, "rubric_vs_measures.csv"))
mech_pool = mech_tab[mech_tab.family == POOL]

# ================================================================== 6. judge vs the author's own passages
print("6. base model vs the author's own passages ...")
rc["rubric_all"] = rc[[f"rubric_{it}" for it in ITEMS]].mean(axis=1)
cal_by_author = cal_rub[cal_rub.kind == "author"].groupby("author", observed=True)
prefer_rows = []
for (au, fam, pb, kind), g in rc.groupby(["author", "family", "params_b", "kind"], observed=True):
    if au not in cal_by_author.groups:
        continue
    ca = cal_by_author.get_group(au)
    for block, gen_col, cal_col in [("S (craft)", "rubric_S", "S_mean"), ("C (construction)", "rubric_C", "C_mean"),
                                    ("all 12 subscores", "rubric_all", "all_mean")]:
        d, lo, hi = two_sample_boot_diff(g[gen_col], ca[cal_col], seed=abs(hash((au, fam, pb, kind, block))) % 9999)
        prefer_rows.append({"author": au, "family": fam, "params_b": pb, "kind": kind, "block": block,
                            "n_gen": len(g), "n_author_items": len(ca),
                            "gen_mean": float(g[gen_col].mean()), "author_item_mean": float(ca[cal_col].mean()),
                            "gen_minus_author": d, "ci_low": lo, "ci_high": hi,
                            "judge_prefers_model": bool(lo == lo and lo > 0)})
prefer_tab = pd.DataFrame(prefer_rows).sort_values(["block", "family", "author", "kind", "params_b"]).reset_index(drop=True)
write_table(prefer_tab, os.path.join(OUTD, "rubric_vs_author_items.csv"))
pref_s = prefer_tab[(prefer_tab.block == "S (craft)") & (prefer_tab.kind == "base")]
n_pref_above = int(pref_s.judge_prefers_model.sum())
n_pref_rows = len(pref_s)
pref_14 = pref_s[pref_s.params_b == 14]
n_pref14_above = int(pref_14.judge_prefers_model.sum())
n_pref14 = len(pref_14)
pref_c14 = prefer_tab[(prefer_tab.block == "C (construction)") & (prefer_tab.kind == "base") & (prefer_tab.params_b == 14)]
n_prefc14_above = int(pref_c14.judge_prefers_model.sum())
n_prefc14 = len(pref_c14)
# the closest any base run comes to the author, per block
closest = {b: g.sort_values("gen_minus_author").iloc[-1]
           for b, g in prefer_tab[prefer_tab.kind == "base"].groupby("block", observed=True)}
# the same ranking split by family: does the second family's judge layer behave the same way
prefer_by_fam = (prefer_tab[prefer_tab.kind == "base"].groupby(["block", "family"], observed=True)
                 .agg(n_cells=("judge_prefers_model", "size"), n_authors=("author", "nunique"),
                      n_model_above_author=("judge_prefers_model", "sum"),
                      mean_gen_minus_author=("gen_minus_author", "mean"),
                      max_gen_minus_author=("gen_minus_author", "max")).reset_index())
write_table(prefer_by_fam, os.path.join(OUTD, "rubric_vs_author_items_by_family.csv"))


def pref_count(block, fam, params=None):
    s = prefer_tab[(prefer_tab.block == block) & (prefer_tab.kind == "base") & (prefer_tab.family == fam)]
    if params is not None:
        s = s[s.params_b == params]
    return int(s.judge_prefers_model.sum()), len(s)


prefc14_q = pref_count("C (construction)", "Qwen3", 14)
prefc14_m = pref_count("C (construction)", "Ministral3", 14)
prefs14_q = pref_count("S (craft)", "Qwen3", 14)
prefs14_m = pref_count("S (craft)", "Ministral3", 14)

# ================================================================== 7. 2AFC rates
print("7. 2AFC rates ...")


def afc_rate_table(dat, group_cols, comparison):
    out = []
    d = dat[dat.comparison == comparison]
    for keys, g in d.groupby(group_cols, observed=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        k, n = int(g.picked_gen.sum()), int(len(g))
        p, lo, hi = wilson(k, n)
        # passage-level rate (mean over judges within a passage), bootstrapped over briefs
        pas = g.groupby(["run", "id"]).picked_gen.mean()
        pk = pas.index.get_level_values(1).values
        pt, plo, phi = cluster_boot_stat(pk, pas.values, np.mean, n=600, seed=13)
        row = dict(zip(group_cols, keys))
        row.update({"n_verdicts": n, "n_picked_gen": k, "rate": p, "wilson_low": lo, "wilson_high": hi,
                    "n_passages": len(pas), "passage_rate": pt, "cluster_low": plo, "cluster_high": phi})
        out.append(row)
    return pd.DataFrame(out)


fool_cfg = afc_rate_table(afc_ok, ["family", "params_b", "kind", "arm"], "vs_source")
fool_cfg["comparison"] = "fool_vs_source"
win_cfg = afc_rate_table(afc_ok, ["family", "params_b", "kind", "arm"], "vs_A0")
win_cfg["comparison"] = "win_vs_A0"
afc_tab = pd.concat([fool_cfg, win_cfg], ignore_index=True).sort_values(
    ["comparison", "family", "params_b", "kind", "arm"]).reset_index(drop=True)
write_table(afc_tab, os.path.join(OUTD, "afc_rates_by_config.csv"))

# the same rates split by family and judge: the two judges are not interchangeable on this task,
# and the point of the split is to show whether they behave the same way on the second family
judge_rows = []
for scope in ["all families"] + FAMS:
    sub = afc_ok if scope == "all families" else afc_ok[afc_ok.family == scope]
    miss = afc_use if scope == "all families" else afc_use[afc_use.family == scope]
    for (comp, jshort), g in sub.groupby(["comparison", "judge_short"], observed=True):
        k, n = int(g.picked_gen.sum()), int(len(g))
        p, lo, hi = wilson(k, n)
        mg = miss[(miss.comparison == comp) & (miss.judge_short == jshort)]
        judge_rows.append({"family": scope, "comparison": comp, "judge": jshort, "n_verdicts": n,
                           "n_picked_gen": k, "rate": p, "wilson_low": lo, "wilson_high": hi,
                           "n_authors": int(g.author.nunique()), "n_runs": int(g.run.nunique()),
                           "missing_rate": float(mg.picked_gen.isna().mean()) if len(mg) else np.nan})
judge_rate_tab = pd.DataFrame(judge_rows).sort_values(["comparison", "family", "judge"]).reset_index(drop=True)
write_table(judge_rate_tab, os.path.join(OUTD, "afc_rates_by_judge.csv"))


def jrate(comp, judge, fam="all families"):
    s = judge_rate_tab[(judge_rate_tab.comparison == comp) & (judge_rate_tab.judge == judge) &
                       (judge_rate_tab.family == fam)]
    return s.iloc[0] if len(s) else None


fool_gem = jrate("vs_source", "gemini")
fool_mm = jrate("vs_source", "minimax")

# the shared-author cross-family cut: arm A0, three authors run in both families, per judge,
# per size, base against adapter. This is the table the cross-family fool-rate claim comes from.
shared = afc_ok[(afc_ok.arm == "A0") & (afc_ok.comparison == "vs_source") & (afc_ok.author.isin(SHARED))]
# a rung enters the cross-family cut only if all three shared authors were run at it in that
# family; Qwen3 1.7B exists for patrick_v2 alone and is dropped here, as it is in 18_cross_family
_ok_rungs = {k for k, g in shared.groupby(["family", "params_b"], observed=True) if g.author.nunique() == len(SHARED)}
shared_dropped = sorted({f"{f} {p:g}B" for (f, p), g in shared.groupby(["family", "params_b"], observed=True)
                         if (f, p) not in _ok_rungs})
shared = shared[[(f, p) in _ok_rungs for f, p in zip(shared.family, shared.params_b)]]
srows = []
for keys, g in shared.groupby(["family", "judge_short", "params_b", "kind"], observed=True):
    k, n = int(g.picked_gen.sum()), int(len(g))
    p, lo, hi = wilson(k, n)
    pas = g.groupby(["author", "id"]).picked_gen.mean()
    pk = np.array([f"{a}|{i}" for a, i in pas.index])
    pt, plo, phi = cluster_boot_stat(pk, pas.values, np.mean, n=800, seed=41)
    srows.append({"family": keys[0], "judge": keys[1], "params_b": keys[2], "kind": keys[3],
                  "n_authors": int(g.author.nunique()), "n_verdicts": n, "n_picked_gen": k, "rate": p,
                  "wilson_low": lo, "wilson_high": hi, "n_passages": len(pas), "passage_rate": pt,
                  "cluster_low": plo, "cluster_high": phi})
shared_tab = pd.DataFrame(srows).sort_values(["family", "judge", "params_b", "kind"]).reset_index(drop=True)
write_table(shared_tab, os.path.join(OUTD, "afc_fool_shared_authors.csv"))

# adapter minus base on the same three authors, brief-paired inside an author, per family x judge x size
adiff_rows = []
for keys, g in shared.groupby(["family", "judge_short", "params_b"], observed=True):
    w = g.pivot_table(index=["author", "id"], columns="kind", values="picked_gen", aggfunc="mean")
    if "adapter" not in w.columns or "base" not in w.columns:
        continue
    w = w.dropna(subset=["adapter", "base"])
    if len(w) < 5:
        continue
    diff = (w["adapter"] - w["base"]).values
    ck = np.array([f"{a}|{i}" for a, i in w.index])
    pt, lo, hi = cluster_boot_stat(ck, diff, np.mean, n=1000, seed=43)
    fl = floor_of("fool_vs_source", keys[0])
    adiff_rows.append({"family": keys[0], "judge": keys[1], "params_b": keys[2],
                       "n_authors": int(w.index.get_level_values(0).nunique()), "n_briefs": len(w),
                       "base_rate": float(w["base"].mean()), "adapter_rate": float(w["adapter"].mean()),
                       "adapter_minus_base": pt, "ci_low": lo, "ci_high": hi, "floor": fl,
                       "within_noise": (abs(pt) < fl) if (pt == pt and fl == fl) else np.nan})
afc_adiff = pd.DataFrame(adiff_rows).sort_values(["family", "judge", "params_b"]).reset_index(drop=True)
write_table(afc_adiff, os.path.join(OUTD, "afc_fool_adapter_minus_base.csv"))


def srate(fam, judge, pb, kind):
    s = shared_tab[(shared_tab.family == fam) & (shared_tab.judge == judge) &
                   (shared_tab.params_b == pb) & (shared_tab.kind == kind)]
    return float(s.rate.iloc[0]) if len(s) else float("nan")

# authors are the unit for any claim about models: author-mean fool rate then bootstrap over authors
fool_au = afc_ok[afc_ok.comparison == "vs_source"].groupby(
    ["family", "params_b", "kind", "arm", "author"], observed=True).picked_gen.mean().reset_index()
pool_rows = []
for keys, g in fool_au.groupby(["family", "params_b", "kind", "arm"], observed=True):
    pt, lo, hi = cluster_boot_stat(g.author.values, g.picked_gen.values, np.mean, n=1000, seed=17)
    pool_rows.append({"family": keys[0], "params_b": keys[1], "kind": keys[2], "arm": keys[3],
                      "n_authors": g.author.nunique(), "fool_rate_author_mean": pt, "ci_low": lo, "ci_high": hi})
fool_pooled = pd.DataFrame(pool_rows).sort_values(["family", "arm", "kind", "params_b"]).reset_index(drop=True)
write_table(fool_pooled, os.path.join(OUTD, "afc_fool_by_author_unit.csv"))

best_fool = afc_tab[(afc_tab.comparison == "fool_vs_source") & (afc_tab.n_verdicts >= 100)].sort_values("rate").iloc[-1]
a0_fool = afc_tab[(afc_tab.comparison == "fool_vs_source") & (afc_tab.arm == "A0")]
overall_fool = wilson(int(afc_ok[afc_ok.comparison == "vs_source"].picked_gen.sum()),
                      int((afc_ok.comparison == "vs_source").sum()))
overall_win = wilson(int(afc_ok[afc_ok.comparison == "vs_A0"].picked_gen.sum()),
                     int((afc_ok.comparison == "vs_A0").sum()))

# judge agreement on 2AFC
agree_rows = []
for scope in ["all families"] + FAMS:
    sub = afc_ok if scope == "all families" else afc_ok[afc_ok.family == scope]
    for comp, g in sub.groupby("comparison", observed=True):
        w = g.pivot_table(index=["run", "id", "arm", "sample"], columns="judge_short", values="picked_gen", aggfunc="first").dropna()
        if len(w) < 20:
            continue
        agree = float((w["gemini"] == w["minimax"]).mean())
        k = float(cohen_kappa_score(w["gemini"].astype(int), w["minimax"].astype(int)))
        ids = np.array([i[1] for i in w.index])
        _, lo, hi = cluster_boot_stat(ids, (w["gemini"] == w["minimax"]).values.astype(float), np.mean, n=600, seed=19)
        agree_rows.append({"family": scope, "comparison": comp, "n_items_both_judges": len(w), "agreement": agree,
                           "agreement_lo": lo, "agreement_hi": hi, "cohens_kappa": k,
                           "gemini_rate": float(w["gemini"].mean()), "minimax_rate": float(w["minimax"].mean())})
agree_tab = pd.DataFrame(agree_rows)
agree_tab["judge_self_repeat_pairs"] = n_repeat_pairs
agree_tab["judge_self_repeat_flips"] = n_repeat_flip
write_table(agree_tab, os.path.join(OUTD, "afc_judge_agreement.csv"))
agree_pool = agree_tab[agree_tab.family == "all families"]


def agr(comp, field, fam="all families"):
    s = agree_tab[(agree_tab.comparison == comp) & (agree_tab.family == fam)]
    return float(s[field].iloc[0]) if len(s) else float("nan")

# 2AFC verdict loss per run: the credit exhaustion is not missing-at-random
loss = afc_use.groupby(["run", "family", "params_b", "kind"], observed=True).apply(
    lambda d: pd.Series({"n_requested": len(d), "n_missing": int(d.picked_gen.isna().sum()),
                         "missing_rate": float(d.picked_gen.isna().mean())}), include_groups=False).reset_index()
loss = loss.sort_values("missing_rate", ascending=False).reset_index(drop=True)
err_counts = afc_use[afc_use.picked_gen.isna()].error.astype(str).str[:60].value_counts().head(6)
write_table(loss, os.path.join(OUTD, "afc_missingness_by_run.csv"))
n_runs_total_lost = int((loss.missing_rate > 0.9).sum())
runs_total_lost = ", ".join(loss[loss.missing_rate > 0.9].run.tolist())
miss_by_judge = afc_use.groupby("judge_short", observed=True).picked_gen.apply(lambda s: float(s.isna().mean()))
miss_by_family = afc_use.groupby("family", observed=True).picked_gen.apply(lambda s: float(s.isna().mean())).to_dict()

# fool rate vs mechanical measures
a0 = main_cells(cells)
fool_link = []
for scope in ["all families"] + FAMS:
    d0 = a0[a0.fool_vs_source.notna()] if scope == "all families" else a0[a0.fool_vs_source.notna() & (a0.family == scope)]
    for mech in ["luar_cos_source", "luar_cos_ref", "per", "words", "coverage"]:
        d = d0[[mech, "fool_vs_source", "run", "author"]].dropna()
        if len(d) < 30:
            continue
        r_pool = spearmanr(d[mech], d.fool_vs_source)[0]
        dc = d.copy()
        dc["a"] = centre_within(dc, mech, "run")
        dc["b"] = centre_within(dc, "fool_vs_source", "run")
        r_within = spearmanr(dc.a, dc.b)[0]
        _, lo, hi = cluster_boot_stat(d.run.values, d[[mech, "fool_vs_source"]].values,
                                      lambda v: spearmanr(v[:, 0], v[:, 1])[0], n=300, seed=23)
        # configuration level, authors as the unit
        cfg = d0.groupby(["run", "author"], observed=True)[[mech, "fool_vs_source"]].mean().dropna().reset_index()
        r_cfg = spearmanr(cfg[mech], cfg.fool_vs_source)[0] if len(cfg) > 5 else np.nan
        fool_link.append({"family": scope, "measure": mech, "n_cells": len(d), "spearman_pooled": float(r_pool),
                          "ci_low": lo, "ci_high": hi, "spearman_within_run": float(r_within),
                          "n_configs": len(cfg), "spearman_config_level": float(r_cfg)})
fool_link_tab = pd.DataFrame(fool_link)
write_table(fool_link_tab, os.path.join(OUTD, "afc_fool_vs_measures.csv"))

# ================================================================== 8. coverage
print("8. coverage ...")
cov_rows = []
for keys, g in a0[a0.coverage.notna()].groupby(["family", "params_b", "kind"], observed=True):
    pt, lo, hi = cluster_bootstrap(g, "coverage", "id", n=1000, seed=29)
    au = g.groupby("author", observed=True).coverage.mean()
    apt, alo, ahi = cluster_boot_stat(au.index.values, au.values, np.mean, n=1000, seed=31)
    cov_rows.append({"family": keys[0], "params_b": keys[1], "kind": keys[2], "n_cells": len(g),
                     "n_authors": g.author.nunique(), "coverage_mean": pt, "brief_ci_low": lo, "brief_ci_high": hi,
                     "coverage_author_mean": apt, "author_ci_low": alo, "author_ci_high": ahi})
cov_tab = pd.DataFrame(cov_rows).sort_values(["family", "params_b", "kind"]).reset_index(drop=True)
cov_tab["floor"] = [floor_of("coverage", f) for f in cov_tab.family]
# paired adapter minus base per author x size x family, against that family's coverage floor
cov_pair_rows = []
for keys, g in a0[a0.coverage.notna()].groupby(["family", "params_b", "author"], observed=True):
    w = g.pivot_table(index="id", columns="kind", values="coverage", aggfunc="mean").dropna()
    if len(w) < 5 or "adapter" not in w or "base" not in w:
        continue
    diff = (w["adapter"] - w["base"]).values
    pt, lo, hi = cluster_boot_stat(w.index.values, diff, np.mean, n=1000, seed=37)
    fl = floor_of("coverage", keys[0])
    cov_pair_rows.append({"family": keys[0], "params_b": keys[1], "author": keys[2], "n_briefs": len(w),
                          "base_mean": float(w["base"].mean()), "adapter_mean": float(w["adapter"].mean()),
                          "adapter_minus_base": pt, "ci_low": lo, "ci_high": hi, "floor": fl,
                          "within_noise": (abs(pt) < fl) if (pt == pt and fl == fl) else np.nan})
cov_pair = pd.DataFrame(cov_pair_rows).sort_values(["family", "params_b", "author"]).reset_index(drop=True)
write_table(cov_tab, os.path.join(OUTD, "coverage_by_config.csv"))
write_table(cov_pair, os.path.join(OUTD, "coverage_adapter_minus_base.csv"))
cov_neg = int((cov_pair.ci_high < 0).sum()) if len(cov_pair) else 0
cov_pos = int((cov_pair.ci_low > 0).sum()) if len(cov_pair) else 0
cov_noise = int(cov_pair["within_noise"].fillna(False).astype(bool).sum()) if len(cov_pair) else 0

# the shared-author cross-family cut for coverage: three authors, both families, brief-paired
covs_rows = []
cova0 = a0[a0.coverage.notna() & a0.author.isin(SHARED)]
_cov_rungs = {k for k, g in cova0.groupby(["family", "params_b"], observed=True) if g.author.nunique() == len(SHARED)}
cova0 = cova0[[(f, p) in _cov_rungs for f, p in zip(cova0.family, cova0.params_b)]]
for keys, g in cova0.groupby(["family", "params_b"], observed=True):
    w = g.pivot_table(index=["author", "id"], columns="kind", values="coverage", aggfunc="mean")
    if "adapter" not in w.columns or "base" not in w.columns:
        continue
    w = w.dropna(subset=["adapter", "base"])
    if len(w) < 5:
        continue
    diff = (w["adapter"] - w["base"]).values
    ck = np.array([f"{a}|{i}" for a, i in w.index])
    pt, lo, hi = cluster_boot_stat(ck, diff, np.mean, n=1000, seed=47)
    fl = floor_of("coverage", keys[0])
    covs_rows.append({"family": keys[0], "params_b": keys[1],
                      "n_authors": int(w.index.get_level_values(0).nunique()), "n_briefs": len(w),
                      "base_mean": float(w["base"].mean()), "adapter_mean": float(w["adapter"].mean()),
                      "adapter_minus_base": pt, "ci_low": lo, "ci_high": hi, "floor": fl,
                      "within_noise": (abs(pt) < fl) if (pt == pt and fl == fl) else np.nan})
cov_shared = pd.DataFrame(covs_rows).sort_values(["family", "params_b"]).reset_index(drop=True)
write_table(cov_shared, os.path.join(OUTD, "coverage_shared_authors.csv"))


def covshared(fam, pb, field="adapter_minus_base"):
    s = cov_shared[(cov_shared.family == fam) & (cov_shared.params_b == pb)]
    return float(s[field].iloc[0]) if len(s) else float("nan")

# ================================================================== figures
print("figures ...")
FIGS = []

# fig 1: calibration ladder, with the two families' generation bars side by side
fig, ax = plt.subplots(figsize=(10, 4.6))
piv = cal_pool.groupby("author", observed=True)[["author_mean", "shuffled_mean", "gen_mean"]].mean().sort_values("author_mean")
gen_q = cal_qwen.groupby("author", observed=True).gen_mean.mean().reindex(piv.index)
gen_m = cal_min.groupby("author", observed=True).gen_mean.mean().reindex(piv.index)
xs = np.arange(len(piv))
ax.bar(xs - 0.30, piv.author_mean, 0.20, label="author's own passages", color="#2b6cb0")
ax.bar(xs - 0.10, gen_q.values, 0.20, label="Qwen3 generations (arm A0)", color="#dd8452")
ax.bar(xs + 0.10, gen_m.values, 0.20, label="Ministral 3 generations (arm A0)", color="#e5b48b")
ax.bar(xs + 0.30, piv.shuffled_mean, 0.20, label="sentence-shuffled author", color="#8c8c8c")
ax.set_xticks(xs)
ax.set_xticklabels(piv.index, rotation=30, ha="right")
ax.set_ylabel("mean of the twelve rubric subscores (0-10)")
ax.set_title("Rubric calibration: author, generations by family, shuffled author (two judges, both orders)")
ax.legend(fontsize=8)
FIGS.append(("Rubric calibration ladder", savefig(fig, os.path.join(OUTD, "fig_rubric_calibration.png"))))

# fig 2: scree with parallel analysis
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.plot(scree.component, scree.eigenvalue, "o-", label="observed eigenvalue", color="#2b6cb0")
ax.plot(scree.component, scree.parallel_p95, "s--", label="parallel analysis 95th pct", color="#8c8c8c")
ax.axvline(n_factors + 0.5, color="#dd8452", lw=1, ls=":")
ax.set_xlabel("component")
ax.set_ylabel("eigenvalue of the 12-subscore correlation matrix")
ax.set_title(f"Rubric factor structure: {n_factors} components above the parallel-analysis threshold")
ax.legend(fontsize=8)
FIGS.append(("Rubric scree and parallel analysis", savefig(fig, os.path.join(OUTD, "fig_rubric_scree.png"))))

# fig 3: inter-judge kappa per subscore, pooled and per family
fig, ax = plt.subplots(figsize=(8.4, 4.8))
kt = kappa_pool.sort_values("qwk_gemini_vs_minimax")
ys = np.arange(len(kt))
ax.barh(ys, kt.qwk_gemini_vs_minimax, 0.62,
        color=["#2b6cb0" if b == "construction" else "#dd8452" for b in kt.block], label="both families")
ax.errorbar(kt.qwk_gemini_vs_minimax, ys, xerr=[kt.qwk_gemini_vs_minimax - kt.qwk_lo, kt.qwk_hi - kt.qwk_gemini_vs_minimax],
            fmt="none", ecolor="k", lw=0.8, capsize=2)
for fam, mk in (("Qwen3", "o"), ("Ministral3", "s")):
    kf = kappa_tab[kappa_tab.family == fam].set_index("subscore").reindex(kt.subscore)
    ax.plot(kf.qwk_gemini_vs_minimax.values, ys, mk, ms=4.5, mfc="none", color="k", label=fam)
ax.set_yticks(ys)
ax.set_yticklabels([f"{r.subscore} {r.label}" for r in kt.itertuples()], fontsize=8)
ax.set_xlabel("quadratic-weighted kappa, Gemini vs MiniMax (95% brief-cluster interval)")
ax.set_title("Inter-judge agreement per rubric subscore (bars pooled; markers per family)")
ax.legend(fontsize=8, loc="lower right")
FIGS.append(("Inter-judge quadratic-weighted kappa", savefig(fig, os.path.join(OUTD, "fig_interjudge_kappa.png"))))

# fig 4: fool rate by configuration; both families now carry 2AFC verdicts
fams_judged = [f for f in FAMS if (afc_tab.family == f).any()]
fig, axes = plt.subplots(1, len(fams_judged), figsize=(6.6 * len(fams_judged), 4.6), sharey=True, squeeze=False)
for ax, fam in zip(axes[0], fams_judged):
    sub = afc_tab[(afc_tab.comparison == "fool_vs_source") & (afc_tab.family == fam) & (afc_tab.arm.isin(["A0", "A5"]))]
    for (kind, arm), g in sub.groupby(["kind", "arm"], observed=True):
        g = g.sort_values("params_b")
        ls = "-" if kind == "base" else "--"
        ax.errorbar(g.params_b, g.rate, yerr=[g.rate - g.wilson_low, g.wilson_high - g.rate],
                    marker="o", ls=ls, capsize=2, label=f"{kind} {arm}")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("parameters (B, log2)")
    ax.set_title(f"{fam}: fool rate vs the author's own passage\n(chance would be 0.50; Wilson intervals)", fontsize=10)
    ax.legend(fontsize=8, title="kind and arm", title_fontsize=8)
axes[0][0].set_ylabel("fool rate (judge picked the generation)")
FIGS.append(("2AFC fool rate by configuration", savefig(fig, os.path.join(OUTD, "fig_afc_fool.png"))))

# fig 5: coverage by configuration
fig, ax = plt.subplots(figsize=(7.2, 4.2))
for (fam, kind), g in cov_tab.groupby(["family", "kind"], observed=True):
    g = g.sort_values("params_b")
    ls = "-" if kind == "base" else "--"
    ax.errorbar(g.params_b, g.coverage_mean, yerr=[g.coverage_mean - g.brief_ci_low, g.brief_ci_high - g.coverage_mean],
                marker="o", ls=ls, capsize=2, label=f"{fam} {kind}")
ax.set_xscale("log", base=2)
ax.set_xlabel("parameters (B, log2)")
ax.set_ylabel(VARIABLES["coverage"][0])
ax.set_title("Judged brief coverage by configuration (arm A0, brief-cluster intervals)")
ax.legend(fontsize=8)
FIGS.append(("Coverage by configuration", savefig(fig, os.path.join(OUTD, "fig_coverage.png"))))

# fig 6: the cross-family cut both judges see, on the three authors run in both families
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), sharey=True, squeeze=False)
for ax, judge in zip(axes[0], ["gemini", "minimax"]):
    for fam in FAMS:
        for kind in ("base", "adapter"):
            s = shared_tab[(shared_tab.family == fam) & (shared_tab.judge == judge) &
                           (shared_tab.kind == kind)].sort_values("params_b")
            if not len(s):
                continue
            ax.errorbar(s.params_b, s.rate, yerr=[s.rate - s.wilson_low, s.wilson_high - s.rate],
                        marker="o" if fam == "Qwen3" else "s", ls="-" if kind == "base" else "--",
                        capsize=2, label=f"{fam} {kind}")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("parameters (B, log2)")
    ax.axhline(0.5, color="k", lw=0.7, ls=":")
    ax.set_title(f"{judge}: fool rate, arm A0, three shared authors", fontsize=10)
    ax.legend(fontsize=8)
axes[0][0].set_ylabel("fool rate (judge picked the generation)")
fig.suptitle("Qwen3 against Ministral 3 on chesterton, doctorow and patrick_v2, per judge", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.94])
FIGS.append(("Fool rate on the three shared authors, per judge and family",
             savefig(fig, os.path.join(OUTD, "fig_afc_fool_shared_authors.png"))))

# ================================================================== README
print("readme ...")
kap_lo = kappa_pool.sort_values("qwk_gemini_vs_minimax").iloc[0]
kap_hi = kappa_pool.sort_values("qwk_gemini_vs_minimax").iloc[-1]
mech_top = mech_pool[(mech_pool.subscore == "C") | (mech_pool.subscore == "S")].sort_values("spearman_pooled")
per_C = mech_pool[(mech_pool.subscore == "C") & (mech_pool.measure == "per")].iloc[0]
luar_C = mech_pool[(mech_pool.subscore == "C") & (mech_pool.measure == "luar_cos_source")].iloc[0]
words_C = mech_pool[(mech_pool.subscore == "C") & (mech_pool.measure == "words")].iloc[0]
cov_C = mech_pool[(mech_pool.subscore == "C") & (mech_pool.measure == "coverage")].iloc[0]
n_mech_sig = int((mech_pool.q_bh < 0.05).sum())

a0_base = afc_tab[(afc_tab.comparison == "fool_vs_source") & (afc_tab.arm == "A0") & (afc_tab.kind == "base")]
a0_adap = afc_tab[(afc_tab.comparison == "fool_vs_source") & (afc_tab.arm == "A0") & (afc_tab.kind == "adapter")]

# README-only bookkeeping (no table, figure or computation is changed by these)
n_afc_runs = int(afc_raw.run.nunique())
n_rubric_authors = int(rc.author.nunique())
_prefc14 = prefer_tab[(prefer_tab.kind == "base") & (prefer_tab.params_b == 14) &
                      (prefer_tab.block.str.startswith("C")) & (prefer_tab.judge_prefers_model)]
prefc14_authors = ", ".join(sorted(f"{r.author} {r.family}" for r in _prefc14.itertuples())) if len(_prefc14) else "none"
_covq = cov_tab[cov_tab.family == "Qwen3"]
_covm = cov_tab[cov_tab.family == "Ministral3"]
n_cov_authors_max = int(_covq.n_authors.max())
n_cov_authors_min = int(_covq[_covq.n_authors > 1].n_authors.min())
cov_authors_q_txt = f"{n_cov_authors_min} to {n_cov_authors_max}"
cov_authors_m_txt = f"{int(_covm.n_authors.min())} to {int(_covm.n_authors.max())}"

# cross-family bookkeeping, every count read back off the tables written above
SIZES_M = sorted(shared_tab[shared_tab.family == "Ministral3"].params_b.unique())
SIZES_Q = sorted(shared_tab[shared_tab.family == "Qwen3"].params_b.unique())
n_shared_authors = int(shared_tab.n_authors.max()) if len(shared_tab) else 0
n_rub_min = int(rc_fam_cells.get("Ministral3", 0))
n_rub_qwen = int(rc_fam_cells.get("Qwen3", 0))
n_afc_min = int(afc_fam_counts.get("Ministral3", 0))
n_afc_qwen = int(afc_fam_counts.get("Qwen3", 0))
n_cov_min = int(a0[a0.family == "Ministral3"].coverage.notna().sum())
n_cov_qwen = int(a0[a0.family == "Qwen3"].coverage.notna().sum())
n_runs_min_judged = int(runs[(runs.family == "Ministral3") & runs.judged_2afc.fillna(False)].shape[0])
n_runs_min = int((runs.family == "Ministral3").sum())
n_runs_min_cov = int(runs[(runs.family == "Ministral3") & runs.has_coverage.fillna(False)].shape[0])


def fool_line(fam, judge):
    """`3B base 0.06 -> adapter 0.11` style string, straight off afc_fool_shared_authors.csv."""
    s = shared_tab[(shared_tab.family == fam) & (shared_tab.judge == judge)].sort_values("params_b")
    parts = []
    for pb in sorted(s.params_b.unique()):
        b, a = srate(fam, judge, pb, "base"), srate(fam, judge, pb, "adapter")
        parts.append(f"{pb:g}B {b:.3f} base against {a:.3f} adapter")
    return "; ".join(parts) if parts else "no rows"


def cov_line(fam):
    s = cov_shared[cov_shared.family == fam].sort_values("params_b")
    return "; ".join(f"{r.params_b:g}B {r.adapter_minus_base:+.1f} [{r.ci_low:+.1f}, {r.ci_high:+.1f}]"
                     for r in s.itertuples()) if len(s) else "no rows"

what = f"""
Everything the two surviving LLM judges produced, treated as an instrument to be validated
rather than as a criterion. Three questions. (1) Does the rubric measure anything: does it
separate an author's own held-out passages from the same passages with their sentences
shuffled, do the two judges agree, does the order of the rubric items move the scores, and
how many independent dimensions do the twelve subscores actually carry. (2) What does the
rubric track: the Spearman relation of every subscore to proposition echo, opener-class
distance, judged coverage, LUAR cosine and passage length, pooled and within configuration.
(3) What the 2AFC forced choice says: how often a judge picks a generation over the author's
own passage (fool rate) and over the A0 arm (win rate), by family, size, kind and arm, how
much the two judges agree with each other and with themselves on repeats, and whether the
fool rate tracks any mechanical measure. Judged brief coverage is reported alongside.

The validity check the study cares about most is section 6: on the construction block,
{n_prefc14_above} of {n_prefc14} author x base-14B cells score the bare model strictly above
the author's own passages scored blind in the same batch ({prefc14_authors}); on the craft block
{n_pref14_above} of {n_pref14} do. That is a fact about the judges, and the reason no rubric
number in this folder is read as a level of quality: an instrument that can rank a bare model
above the author it is scoring can order two configurations, and cannot say either is good.

Both families carry a judge layer. {n_runs_min_judged} of the {n_runs_min} Ministral 3 runs have
`judged_2afc = True` and {n_runs_min_cov} have `has_coverage = True` in runs.csv. Those records
were produced on 2026-09-10 and 2026-09-11 with the same two judges (Gemini 3.1 flash-lite and
MiniMax M3), the same rubric and 2AFC prompts, the same forward and reverse item orders and the
same sample-0 protocol as the Qwen3 records, so the two families are read on one instrument
rather than two. Every table in this folder therefore carries `family` as a grouping column,
with a `both families` or `all families` row where pooling is meaningful. The rubric now covers
{n_rub_qwen} judged Qwen3 passages and {n_rub_min} judged Ministral 3 passages at arm A0, and the
2AFC layer {n_afc_qwen} Qwen3 verdicts against {n_afc_min} Ministral 3 verdicts. Ministral runs
exist for {n_shared_authors} authors ({', '.join(SHARED)}), so a Ministral row that pools over
authors pools over those {n_shared_authors} and no others, while a pooled Qwen3 row pools over
{n_rubric_authors} rubric authors. The explicit like-for-like comparison is
afc_fool_shared_authors.csv and coverage_shared_authors.csv, which restrict both families to
those {n_shared_authors} authors.
"""

how = f"""
Data. Raw rubric records from `data/eval_results/judge/*.jsonl` ({n_rub_all} records over two
judges x two rubric orders; the Mistral judge file is excluded as pre-registered).
{n_rub_fail} records ({100 * n_rub_fail / n_rub_all:.1f}%) failed to parse and carry no
subscores; they are dropped and counted. Calibration rows (the author's own passages and their
sentence-shuffled versions) live in the same files and in `data/master/rubric_calibration.csv`.
2AFC records from `data/runs/<run>/judge.jsonl` ({n_afc_raw} raw records over {n_afc_runs} run directories).
Cell-level values from `data/master/cells.parquet`.

Unit. Rubric judging ran on arm A0, sample 0 only ({n_rubric_cells_all_arms} non-null rubric
cells in cells.parquet for {n_rubric_cells_a0} judged passages at arm A0, sample 0,
non-replicate), so every cell-level rubric analysis here is restricted to that slice. The rubric
reaches {n_rubric_authors} distinct authors: all {rc_fam_authors.get('Qwen3', 0)} of them have
Qwen3 passages judged and {rc_fam_authors.get('Ministral3', 0)} of them also have Ministral 3
passages judged. 2AFC is restricted to parseable
non-replicate runs, arms A0-A5, sample 0. Repeated records for the same (run, id, arm, sample,
judge, comparison) are de-duplicated keeping the first non-missing verdict; {n_repeat_pairs}
items were judged twice by the same judge and {n_repeat_flip} of them
({100 * n_repeat_flip / max(n_repeat_pairs, 1):.0f}%) got the opposite verdict the second time,
which is this design's within-judge test-retest floor.

Family as a grouping column. Every rubric record is given the family of its run from the master
tables, not from the run name: runs.csv for the main ladder and cells_series.parquet for the
Qwen3 corpus-size adapters. {n_gen_series} of the judged generation records come from those
off-ladder corpus-size runs, and {n_gen_replicate} records from replicate base runs are dropped
before any of this, as the programme's non-replicate convention requires; those replicate runs
are the material the floors are built from instead. A row labelled `both families` or
`all families` pools everything;
a row labelled Qwen3 or Ministral 3 uses that family's main-ladder runs only, so the two
families are compared on the same design. Ministral rows pool {n_shared_authors} authors
({', '.join(SHARED)}) and say so in their n_authors column. The two shared-author tables
(afc_fool_shared_authors.csv, coverage_shared_authors.csv) keep only the size rungs at which all
{n_shared_authors} authors were run in that family, which drops {', '.join(shared_dropped) or 'no rung'};
every row in them carries all {n_shared_authors} authors.

Statistics. Proportions carry two intervals: a Wilson interval on the judge-level verdicts
(which treats the two judges' verdicts on one passage as independent, so it is the optimistic
one) and a bootstrap over briefs on the passage-level rate. Any claim about models pools author
means and bootstraps over authors. Quadratic-weighted kappa is computed on integer ratings
0-10 with a 400-replicate bootstrap over briefs. The rubric-order effect is a paired
fwd-vs-rev contrast per judge x subscore with a brief-cluster interval, a Wilcoxon p and BH-FDR
across the {len(order_pool)} tests inside each scope. Factor structure is a PCA of the
standardised twelve subscores with permutation parallel analysis (500 permutations, 95th
percentile), run once per scope. Subscore correlations are Spearman, reported pooled and again
after centring both variables within run, with BH-FDR across the {len(mech_pool)} tests inside
each scope. Rubric values are never quoted as absolute quality: every generation mean is placed
next to the author's own calibration items scored blind by the same judges in the same batch.
Judged brief coverage is an LLM-judged adherence rate on the same footing, not a measurement of
what the passage contains, and it carries no calibration items of its own.

Floors. judge_replicate_floors.csv holds the replicate floor of each judged measure per family,
computed by lib.replicate_floor over the twice-generated base runs. Coverage has
{floor_pairs_n('coverage', 'Qwen3')} Qwen3 pairs at {floor_sizes('coverage', 'Qwen3')} and
{floor_pairs_n('coverage', 'Ministral3')} Ministral 3 pairs at {floor_sizes('coverage', 'Ministral3')};
fool_vs_source has {floor_pairs_n('fool_vs_source', 'Qwen3')} Qwen3 pairs at
{floor_sizes('fool_vs_source', 'Qwen3')} and {floor_pairs_n('fool_vs_source', 'Ministral3')}
Ministral 3 pairs at {floor_sizes('fool_vs_source', 'Ministral3')}. The rubric blocks have
{floor_pairs_n('rubric_C', 'Qwen3')} Qwen3 pairs and {floor_pairs_n('rubric_C', 'Ministral3')}
Ministral 3 pairs at {floor_sizes('rubric_C', 'Ministral3')}, because no Qwen3 replicate run was
rubric-judged. Every coverage and fool-rate contrast in this folder carries the floor of its own
family, and a contrast smaller than that floor is marked within_noise whatever its interval.
"""

reading = f"""
Unit of replication. The rubric exists for {n_rubric_authors} authors across the two families,
with {n_rubric_cells_a0} judged passages ({rc_fam_authors.get('Qwen3', 0)} authors on Qwen3,
{rc_fam_authors.get('Ministral3', 0)} on Ministral 3); the calibration anchor for each author is
{cal_tab.n_author_items.min():.0f} to {cal_tab.n_author_items.max():.0f} of that author's own
passages per judge. An author-level claim on the rubric therefore rests on {n_rubric_authors}
points pooled and on {n_shared_authors} points inside the second family, and a per-author anchor
rests on a handful of passages: the author-versus-shuffled gaps below are large but their
intervals are wide, and the author-versus-generation comparison inherits that width. The 2AFC
table printed here pools verdicts within a size, which counts each author's briefs as
independent replicates of the size; `afc_fool_by_author_unit.csv` holds the same quantity with
the author as the unit and is the one to quote for any statement about a model size. The
coverage table carries both, and its author-level interval is the wider of the two. The 2AFC
rates rest on {n_afc_use} requested verdicts of which {n_afc_missing}
({100 * n_afc_missing / n_afc_use:.1f}%) never arrived, and the loss is not random.
{f'{n_runs_total_lost} runs lost more than 90 percent of their verdicts ({runs_total_lost}), and MiniMax' if n_runs_total_lost else 'No run now loses more than 90 percent of its verdicts, the worst standing at ' + f'{100 * loss.missing_rate.max():.0f}% ({loss.run.iloc[0]}), but MiniMax'}
lost {100 * miss_by_judge.get('minimax', float('nan')):.0f}% of its verdicts against Gemini's
{100 * miss_by_judge.get('gemini', float('nan')):.0f}%. The loss is also uneven across families
({100 * miss_by_family.get('Qwen3', float('nan')):.0f}% of the requested Qwen3 verdicts against
{100 * miss_by_family.get('Ministral3', float('nan')):.0f}% of the Ministral 3 ones). Any 2AFC
comparison across sizes, kinds or families is therefore over an unbalanced subset of
configurations, and the pooled rate is weighted towards the runs that survived the credit
exhaustion.

The second family on the same instrument. The shuffle gate passes on
{n_gate_pass_m} of the {n_gate_rows_m} Ministral 3 author x judge cells and
{n_gate_pass_q} of the {n_gate_rows_q} Qwen3 ones (rubric_calibration.csv,
rubric_calibration_by_family.csv). The gate has two halves and they behave differently. The
shuffle separation, an author's own passages against the same passages sentence-shuffled,
passes {n_sep_pass_m} of {n_gate_rows_m} on Ministral 3 and {n_sep_pass_q} of {n_gate_rows_q} on
Qwen3; it is computed from the calibration items alone, so the two families read it off the same
rows and it says the rubric is measuring something on both. The second half, the author still
scoring above this family's generations, holds in {n_above_gen_m} of {n_gate_rows_m} Ministral 3
cells against {n_above_gen_q} of {n_gate_rows_q} Qwen3 cells. The Ministral cells that fail are
{gate_fail_m}. The Qwen3 cells that fail are {gate_fail_q}. Inter-judge agreement is of the
same order on both
(rubric_interjudge_kappa.csv: Qwen3 kappa runs
{kappa_tab[kappa_tab.family == 'Qwen3'].qwk_gemini_vs_minimax.min():.2f} to
{kappa_tab[kappa_tab.family == 'Qwen3'].qwk_gemini_vs_minimax.max():.2f}, Ministral 3
{kappa_tab[kappa_tab.family == 'Ministral3'].qwk_gemini_vs_minimax.min():.2f} to
{kappa_tab[kappa_tab.family == 'Ministral3'].qwk_gemini_vs_minimax.max():.2f}). On the fool
comparison restricted to the {n_shared_authors} shared authors at arm A0
(afc_fool_shared_authors.csv), Gemini reads Ministral 3 at {fool_line('Ministral3', 'gemini')},
and MiniMax at {fool_line('Ministral3', 'minimax')}; the same judges read Qwen3 at
{fool_line('Qwen3', 'gemini')} and {fool_line('Qwen3', 'minimax')}. Those are relative
instrument readings on one pair of judges, not measurements of how often a human would be
fooled, and the two judges' levels differ by more than any adapter-versus-base step inside
either family.

Judged adherence across the families. On the same {n_shared_authors} authors, brief-paired,
the adapter minus base coverage difference is {cov_line('Qwen3')} on Qwen3 and
{cov_line('Ministral3')} on Ministral 3 (coverage_shared_authors.csv), against coverage floors
of {floor_of('coverage', 'Qwen3'):.2f} and {floor_of('coverage', 'Ministral3'):.2f} points from
{floor_pairs_n('coverage', 'Qwen3')} and {floor_pairs_n('coverage', 'Ministral3')} replicate
pairs. Read the floor column in that table before the interval: the Ministral floor is the
larger of the two, so a Ministral coverage step has to be bigger to mean anything.

Interval width. The overall fool rate is {overall_fool[0]:.3f} [{overall_fool[1]:.3f},
{overall_fool[2]:.3f}] on judge-level verdicts; the same quantity bootstrapped over briefs is
wider by roughly a factor of two in the per-configuration table, and that is the honest one.
The inter-judge kappas run from {kap_lo.qwk_gemini_vs_minimax:.2f} ({kap_lo.subscore}
{kap_lo.label}) to {kap_hi.qwk_gemini_vs_minimax:.2f} ({kap_hi.subscore} {kap_hi.label}); a
subscore whose interval includes 0.4 should not be used to separate two configurations on its
own.

Floor. The judge's own noise floor is set by the two repeat measurements it made of itself: the
{100 * n_repeat_flip / max(n_repeat_pairs, 1):.0f}% verdict flip rate on repeated 2AFC items and
the rubric-order shift (largest: {worst_order.subscore} {worst_order.label} on
{worst_order.judge}, rev minus fwd {worst_order.rev_minus_fwd:+.2f}
[{worst_order.ci_low:+.2f}, {worst_order.ci_high:+.2f}], mean absolute shift
{worst_order.mean_abs_shift:.2f} points on a 0-10 scale). A difference between two
configurations smaller than about one rubric point is inside the instrument's own repeat
variation. On top of that, judge_replicate_floors.csv gives the regeneration floor of each
judged measure per family from lib.replicate_floor: coverage
{floor_of('coverage', 'Qwen3'):.2f} points on Qwen3 from {floor_pairs_n('coverage', 'Qwen3')}
pairs at {floor_sizes('coverage', 'Qwen3')} and {floor_of('coverage', 'Ministral3'):.2f} on
Ministral 3 from {floor_pairs_n('coverage', 'Ministral3')} pairs at
{floor_sizes('coverage', 'Ministral3')}; fool_vs_source
{floor_of('fool_vs_source', 'Qwen3'):.3f} and {floor_of('fool_vs_source', 'Ministral3'):.3f}.
The rubric blocks carry a floor on Ministral 3 only
(rubric_C {floor_of('rubric_C', 'Ministral3'):.3f}, rubric_S {floor_of('rubric_S', 'Ministral3'):.3f},
from {floor_pairs_n('rubric_C', 'Ministral3')} pairs at {floor_sizes('rubric_C', 'Ministral3')}),
because the Qwen3 replicate runs were never rubric-judged, so a Qwen3 rubric contrast still has
no floor of its own to be read against.

The two judges are not one instrument. On the fool comparison Gemini picks the generation
{fool_gem.rate:.3f} of the time and MiniMax {fool_mm.rate:.3f} - a factor of
{fool_mm.rate / max(fool_gem.rate, 1e-9):.1f} - and their agreement on that comparison
({agr('vs_source', 'agreement'):.3f}) is almost entirely the shared base rate, since Cohen's
kappa is {agr('vs_source', 'cohens_kappa'):.3f}. The same split holds inside the second family:
on Ministral 3 the two judges agree {agr('vs_source', 'agreement', 'Ministral3'):.3f} of the
time with kappa {agr('vs_source', 'cohens_kappa', 'Ministral3'):.3f}, against
{agr('vs_source', 'agreement', 'Qwen3'):.3f} and
{agr('vs_source', 'cohens_kappa', 'Qwen3'):.3f} on Qwen3. On the win-vs-A0 comparison they agree
{agr('vs_A0', 'agreement'):.3f} of the time with kappa {agr('vs_A0', 'cohens_kappa'):.3f}, which
is close to chance for a two-alternative choice. `win_vs_A0` carries little reliable signal
about which arm a judge prefers, and its mean should not be quoted without that.

What would overturn this. A third judge family that reproduces the shuffle calibration but not
the base-above-author ranking would localise that ranking to these two judges rather than to
the rubric. Re-running the missing 2AFC verdicts would overturn any claim about the size or
kind ordering of the fool rate, because whole configurations are currently absent. A human
2AFC panel on the same passages would settle whether the fool rate measures anything a reader
would call voice. On the cross-family side, a fourth and fifth Ministral author would move the
comparison more than any additional brief could: the second family's judge rows pool
{n_shared_authors} authors.

What this does not show. Nothing here licenses a statement that one configuration writes better
prose than another. The construction block scores the bare 14B model above the author for
{n_prefc14_above} of {n_prefc14} author cells ({prefc14_q[0]} of {prefc14_q[1]} on Qwen3,
{prefc14_m[0]} of {prefc14_m[1]} on Ministral 3), which is a statement about the judges'
preferences, not about the writing. The correlations in section 5 are associations across
passages that differ in configuration, author and length at once; the within-run column is the
one that survives removing configuration-level differences, and it is usually smaller. The
cross-family judge numbers are readings from one pair of judges on {n_shared_authors} authors;
they do not establish that either family emulates authors better than the other.
"""

caveats = [
    f"Rubric records are arm A0, sample 0 only: {n_rubric_cells_all_arms} non-null rubric cells in cells.parquet for {n_rubric_cells_a0} judged passages in the A0, sample-0, non-replicate slice used here. Any analysis that groups rubric_* by arm would be counting the same judgement several times.",
    f"{n_rub_fail} of {n_rub_all} rubric records ({100 * n_rub_fail / n_rub_all:.1f}%) failed to parse, and the failures are not evenly spread across judges or orders (see rubric_order_effect.csv counts).",
    f"{n_afc_missing} of {n_afc_use} 2AFC verdicts ({100 * n_afc_missing / n_afc_use:.1f}%) are missing, dominated by OpenRouter credit exhaustion and empty completions; {n_runs_total_lost} runs lost more than 90 percent of their judging and the worst-hit run now stands at {100 * loss.missing_rate.max():.0f}% ({loss.run.iloc[0]}). The loss rate differs by family ({100 * miss_by_family.get('Qwen3', float('nan')):.0f}% Qwen3 against {100 * miss_by_family.get('Ministral3', float('nan')):.0f}% Ministral 3), so a family contrast on a pooled rate is a contrast over different denominators.",
    "Wilson intervals treat two judges' verdicts on the same passage as independent. They are reported because the plan asks for them, but the brief-cluster interval in the same table is the one to quote.",
    f"Both families are judged, but not on the same authors. The Ministral 3 judge rows cover {n_shared_authors} authors ({', '.join(SHARED)}) against {n_rubric_authors} on the rubric pooled, so a Ministral row that pools over authors pools over {n_shared_authors} of them. Quote afc_fool_shared_authors.csv and coverage_shared_authors.csv, which hold both families on the same {n_shared_authors} authors, for any cross-family statement.",
    f"The Ministral 3 judge records were produced on 2026-09-10 and 2026-09-11, after the Qwen3 ones, with the same judges, prompts, item orders and sample-0 protocol. They are the same instrument, not the same batch: a judge endpoint can drift between batches, and nothing here measures that drift.",
    f"The two judges differ by a factor of {fool_mm.rate / max(fool_gem.rate, 1e-9):.1f} on the fool rate and agree at kappa {agr('vs_A0', 'cohens_kappa'):.3f} on win-vs-A0; the pooled rate is an average of two instruments that are not measuring the same thing. That is why the cross-family fool rates are reported per judge and never averaged across judges.",
    "Coverage, fool rate and win rate are judged on sample 0 only; the handful of sample-1 records is excluded rather than mixed in.",
    "Calibration items number a handful per author per judge, so the author anchor itself is noisy; the shuffle gap is large enough to survive that, the author-versus-generation difference often is not.",
    f"Judged brief coverage is an LLM-judged adherence measure, not an accuracy. The Qwen3 runs listed under the 2026-09-09 credit outage in LOG.md carry error rows for coverage and are being rejudged, which is why the Qwen3 rows of coverage_by_config.csv rest on {cov_authors_q_txt} authors depending on the size and kind; the Ministral 3 rows rest on {cov_authors_m_txt}, which is the whole second family. Every coverage number here changes when that rerun lands, and the 2AFC rows for the same runs change with it.",
    f"The rubric blocks have a replicate floor on Ministral 3 only ({floor_pairs_n('rubric_C', 'Ministral3')} pairs at {floor_sizes('rubric_C', 'Ministral3')}) because no Qwen3 replicate run was rubric-judged. A Qwen3 rubric contrast in this folder still cannot be read against a floor.",
    "Fool rate, win rate and coverage are judged instruments with an unbalanced denominator; none of them is a measurement of whether the prose is good, and none of them is comparable to a rate from another judge pair or another batch.",
    f"The number of authors, {n_rubric_authors} on the rubric pooled and {n_shared_authors} inside the second family, is what limits every claim here. BH-FDR is applied within each family of tests and within each scope in this script, and does not buy back replication across authors.",
]

extra = f"""
### 2AFC verdict loss (the largest data problem in this script)

{md_table(loss.head(12))}

Error text on the missing verdicts, most common first:

{chr(10).join(f'- `{k}` x {v}' for k, v in err_counts.items())}
"""

write_readme(
    OUTD, "16_judges: what the LLM judges measure, and how much of it is noise",
    what, how, reading, caveats,
    tables=[("Rubric calibration per family, author and judge", cal_tab.drop(columns=[c for c in cal_tab.columns if c.endswith(("_lo", "_hi"))])),
            ("Rubric calibration rolled up per family (the shuffle gate on the second family)", cal_by_fam),
            ("Inter-judge quadratic-weighted kappa per subscore and family", kappa_tab),
            ("Rubric order effect (rev minus fwd), largest twelve pooled", order_pool.reindex(order_pool.rev_minus_fwd.abs().sort_values(ascending=False).index).head(12)),
            ("Rubric order effect rolled up per family and judge", order_fam),
            ("Factor structure: eigenvalues against parallel analysis, per family", scree_all),
            ("Block means against the mechanical measures, per family", mech_tab[mech_tab.subscore.isin(["C", "S"])]),
            ("Does the judge rank the model above the author (base runs, all three blocks)",
             prefer_tab[prefer_tab.kind == "base"].sort_values(["block", "family", "author", "params_b"])),
            ("The same ranking rolled up per family", prefer_by_fam),
            ("2AFC rates by configuration (arm A0)", afc_tab[afc_tab.arm == "A0"]),
            ("2AFC rates split by family and judge", judge_rate_tab),
            ("2AFC fool rate on the three shared authors, per family, judge, size and kind", shared_tab),
            ("2AFC fool rate, adapter minus base on the three shared authors, against the family floor", afc_adiff),
            ("2AFC judge agreement per family", agree_tab),
            ("Fool rate against the mechanical measures, per family", fool_link_tab),
            ("Coverage by configuration", cov_tab),
            ("Coverage, adapter minus base on the three shared authors, against the family floor", cov_shared),
            ("Replicate floors for the judged measures, per family", floors_tab)],
    figures=FIGS, extra=extra)

print(f"""
=== 16_judges summary ===
rubric records {n_rub_all} ({n_rub_fail} unparsed); judged passages (A0) {n_rubric_cells_a0}; authors {n_rubric_authors}
rubric passages by family: Qwen3 {n_rub_qwen} ({rc_fam_authors.get('Qwen3', 0)} authors), Ministral3 {n_rub_min} ({rc_fam_authors.get('Ministral3', 0)} authors)
shuffle gate passes {n_gate_pass}/{n_gate_rows} pooled; Qwen3 {n_gate_pass_q}/{n_gate_rows_q} (fails: {gate_fail_q}); Ministral3 {n_gate_pass_m}/{n_gate_rows_m} (fails: {gate_fail_m})
  gate halves: shuffle separation Qwen3 {n_sep_pass_q}/{n_gate_rows_q}, Ministral3 {n_sep_pass_m}/{n_gate_rows_m}; author above generations Qwen3 {n_above_gen_q}/{n_gate_rows_q}, Ministral3 {n_above_gen_m}/{n_gate_rows_m}
author scored below its own generations in {n_author_below_gen}/{n_gate_rows} pooled author x judge cells
inter-judge QWK {kap_lo.qwk_gemini_vs_minimax:.2f} ({kap_lo.subscore}) to {kap_hi.qwk_gemini_vs_minimax:.2f} ({kap_hi.subscore}) pooled
inter-judge QWK per family: {'; '.join(f"{r.family} {r.qwk_min:.2f}-{r.qwk_max:.2f}" for r in kappa_fam.itertuples())}
order effects with q<0.05: {n_order_sig}/{len(order_pool)} pooled; {'; '.join(f"{r.family}/{r.judge} {r.n_q_below_05}/{r.n_tests}" for r in order_fam.itertuples())}
factors above parallel analysis: {'; '.join(f"{k} {v}" for k, v in N_FACTORS.items())} (pooled first {n_factors} explain {scree.cum_var_explained.iloc[n_factors - 1]:.1%})
rubric_C vs per rho {per_C.spearman_pooled:+.2f} (within-run {per_C.spearman_within_run:+.2f}); vs LUAR {luar_C.spearman_pooled:+.2f}; vs words {words_C.spearman_pooled:+.2f}; vs coverage {cov_C.spearman_pooled:+.2f}
judge ranks base above author: craft {n_pref14_above}/{n_pref14} at 14B; construction {n_prefc14_above}/{n_prefc14} at 14B (Qwen3 {prefc14_q[0]}/{prefc14_q[1]}, Ministral3 {prefc14_m[0]}/{prefc14_m[1]})
closest base cell per block: {'; '.join(f"{b} {r.author} {r.family} {r.params_b:g}B {r.gen_minus_author:+.2f} [{r.ci_low:+.2f}, {r.ci_high:+.2f}]" for b, r in closest.items())}
2AFC usable {n_afc_use} requested, {n_afc_missing} missing ({100 * n_afc_missing / n_afc_use:.1f}%), {n_runs_total_lost} runs >90% lost
2AFC verdicts by family: Qwen3 {n_afc_qwen}, Ministral3 {n_afc_min}; missing {100 * miss_by_family.get('Qwen3', float('nan')):.0f}% vs {100 * miss_by_family.get('Ministral3', float('nan')):.0f}%
overall fool rate {overall_fool[0]:.3f} [{overall_fool[1]:.3f}, {overall_fool[2]:.3f}]; win vs A0 {overall_win[0]:.3f} [{overall_win[1]:.3f}, {overall_win[2]:.3f}]
per judge: gemini fool {fool_gem.rate:.3f}, minimax fool {fool_mm.rate:.3f}
shared authors ({n_shared_authors}), arm A0, gemini fool: Qwen3 {fool_line('Qwen3', 'gemini')} | Ministral3 {fool_line('Ministral3', 'gemini')}
shared authors ({n_shared_authors}), arm A0, minimax fool: Qwen3 {fool_line('Qwen3', 'minimax')} | Ministral3 {fool_line('Ministral3', 'minimax')}
A0 base fool {a0_base.rate.min():.3f}-{a0_base.rate.max():.3f}; A0 adapter fool {a0_adap.rate.min():.3f}-{a0_adap.rate.max():.3f}
judge agreement {agree_pool.agreement.min():.3f}-{agree_pool.agreement.max():.3f} (kappa {agree_pool.cohens_kappa.min():.3f}-{agree_pool.cohens_kappa.max():.3f}); self-repeat flips {n_repeat_flip}/{n_repeat_pairs}
judge layer families: {sorted(afc_tab.family.unique())}; Ministral 3 judged 2026-09-10/11 on the same judges, prompts and sample-0 protocol
coverage adapter-minus-base: {cov_neg} author x size cells below zero, {cov_pos} above, {cov_noise} inside the floor (of {len(cov_pair)})
coverage adapter-minus-base, shared authors: Qwen3 {cov_line('Qwen3')} | Ministral3 {cov_line('Ministral3')}
judged floors: {'; '.join(f"{r.measure}/{r.family} {r.floor:.3f} ({r.n_pairs} pairs at {r.sizes_b})" for r in floors_tab.itertuples())}
outputs -> {OUTD}
""")
