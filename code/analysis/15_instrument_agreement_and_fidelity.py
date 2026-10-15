"""15_instrument_agreement_and_fidelity -- which instruments agree, and which can be calibrated.

Three blocks.

1. Agreement. Spearman correlation matrix over arm-A0 cells (pooled and per family),
   hierarchical clustering on 1 - |rho|, PCA with Horn parallel analysis, redundancy pairs
   at |rho| >= 0.8, and the LUAR / Wegmann / StyleDistance disagreement on adapter gain
   per author.

2. Calibration. For every dictionary measure the script asks whether the author's own
   passages (H) and the stranger pool (P) exist for it in references.parquet. Where they do
   it computes the mean-based position pos = (mean G - mean P) / (mean H - mean P) and the
   distributional fidelity F = 1 - W1(G, H) / W1(P, H) per configuration, with a
   brief-cluster bootstrap. Where they do not it says so and why.

3. The author region. R = the share of generated passages inside the central 90% interval
   of H on every calibrated voice instrument at once, and R@2 over the two samples.

Reads data/master only. Writes analysis/15_instrument_agreement_and_fidelity only.
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *  # noqa: F401,F403

from scipy.stats import spearmanr, wasserstein_distance
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform

T0 = time.time()
OUTD = outdir("15_instrument_agreement_and_fidelity")
RNG = 0
NBOOT_F = 400          # bootstrap resamples for F (briefs resampled within a configuration)
NBOOT = 2000
KEYS = ["author", "family", "params_b"]

print("[15] loading", flush=True)
cells, runs, authors, briefs, refs = load_all()
d = main_cells(cells).copy()                       # arm A0, non-replicate, both kinds, both samples
n_cells_a0, n_runs_a0, n_cfg = len(d), d.run.nunique(), d.groupby(KEYS + ["kind"]).ngroups

# ---------------------------------------------------------------------------
# 0. Which dictionary measures can be calibrated at all
# ---------------------------------------------------------------------------
NUMERIC = [m for m in VARIABLES
           if m in d.columns and pd.api.types.is_numeric_dtype(d[m]) or (m in d.columns and d[m].dtype == bool)]
NUMERIC = [m for m in NUMERIC if m in d.columns and d[m].dropna().nunique() > 1]

ref_src = refs[refs.group == "source"]                      # H: the author's own held-out passages
ref_pop = refs[refs.group.str.startswith("other:")]          # P: the stranger pool scored in the same run
ref_own = refs[refs.group == "ref"]                          # the author's REF chunks (the profile side)

cal_rows = []
for m in VARIABLES:
    in_cells = m in d.columns
    numeric_g = in_cells and (pd.api.types.is_numeric_dtype(d[m]) or d[m].dtype == bool)
    in_refs = m in refs.columns
    h_ok = bool(in_refs and ref_src[m].notna().any()) if in_refs else False
    p_ok = bool(in_refs and ref_pop[m].notna().any()) if in_refs else False
    src = VARIABLES[m][2]
    if not in_cells:
        why = "not in the master cell table"
    elif not numeric_g:
        why = "categorical, no distance defined"
    elif not in_refs and src.startswith("eval cache"):
        why = ("eval-cache measure computed on generations only; the cache keeps a per-author mean "
               "and sd of the author's own passages under source_stats, not per-passage values, and "
               "nothing at all for other authors, so neither H nor P exists")
    elif not in_refs and m.endswith("_cos_source"):
        why = ("defined against the brief's own source passage; for a reference passage the source "
               "is itself, so the quantity is not comparable and was not scored")
    elif not in_refs and m.startswith("memo_"):
        why = "overlap with the author's training text; only defined for a generation"
    elif not in_refs and m in ("truncated", "preface"):
        why = "a decoding flag of the generation run; a human passage has no analogue"
    elif not in_refs and src in ("coverage.jsonl", "judge.jsonl", "eval_results/judge"):
        why = "LLM-judge measure; the reference passages were never put through this judge pass"
    elif not in_refs:
        why = f"present in the generations only (source: {src}); no reference passage carries it"
    elif not h_ok:
        why = "column exists in references.parquet but is empty for the author's own passages"
    elif not p_ok:
        why = "column exists in references.parquet but is empty for the stranger pool"
    else:
        why = ""
    cal_rows.append({"measure": m, "construct": VARIABLES[m][1], "source": src,
                     "in_generations": in_cells, "numeric": bool(numeric_g),
                     "H_available": h_ok, "P_available": p_ok,
                     "calibratable": bool(numeric_g and h_ok and p_ok), "reason_if_not": why})
calibratable = pd.DataFrame(cal_rows)
write_table(calibratable, os.path.join(OUTD, "instrument_calibration_coverage.csv"))
INSTR = [r.measure for r in calibratable.itertuples() if r.calibratable]
NOT_CAL = calibratable[~calibratable.calibratable]
print(f"[15] {len(INSTR)} calibratable of {len(VARIABLES)} dictionary measures", flush=True)

# ---- integrity check on the anchors themselves ------------------------------
# The same reference passage is re-scored inside every run of its author. If the anchor is
# well defined, a passage's value must not depend on which run scored it.
stab_rows = []
for m in INSTR:
    g = ref_src.groupby(["author", "id"])[m]
    nun = g.nunique(dropna=True)
    within = g.std(ddof=0)
    across = ref_src.groupby("author")[m].std(ddof=0)
    ratio = (within.groupby("author").median() / across).replace([np.inf, -np.inf], np.nan)
    stab_rows.append({"measure": m, "construct": VARIABLES[m][1],
                      "n_reference_passages": int(len(nun)),
                      "share_run_dependent": float((nun > 1).mean()),
                      "max_distinct_values_one_passage": int(nun.max()),
                      "median_within_over_between_sd": float(np.nanmedian(ratio.values))})
anchor_stability = pd.DataFrame(stab_rows).sort_values("share_run_dependent", ascending=False)
write_table(anchor_stability, os.path.join(OUTD, "anchor_stability.csv"), floats=5)
UNSTABLE = anchor_stability[anchor_stability.share_run_dependent > 0.01].measure.tolist()

# ---------------------------------------------------------------------------
# 1. Agreement: Spearman matrix, clustering, PCA
# ---------------------------------------------------------------------------
CORR_MEAS = [m for m in NUMERIC if d[m].notna().mean() > 0.02]


def corr_matrix(frame, measures):
    x = frame[measures].astype(float)
    r = x.corr(method="spearman", min_periods=50)
    return r


corr_all = corr_matrix(d, CORR_MEAS)
write_table(corr_all.reset_index().rename(columns={"index": "measure"}), os.path.join(OUTD, "spearman_matrix_pooled.csv"))
degen_rows = []
for fam, g in d.groupby("family"):
    cm = corr_matrix(g, CORR_MEAS)
    write_table(cm.reset_index().rename(columns={"index": "measure"}),
                os.path.join(OUTD, f"spearman_matrix_{fam}.csv"))
    for m in CORR_MEAS:
        v = g[m].astype(float)
        degen_rows.append({"family": fam, "measure": m, "construct": VARIABLES[m][1],
                           "n_cells": int(len(g)), "n_non_null": int(v.notna().sum()),
                           "n_distinct": int(v.dropna().nunique()),
                           "degenerate": bool(v.notna().sum() < 50 or v.dropna().nunique() < 2)})
degen = pd.DataFrame(degen_rows)
degen_bad = degen[degen.degenerate].sort_values(["family", "construct", "measure"])
write_table(degen, os.path.join(OUTD, "family_measure_coverage.csv"))

pairs = []
mm = corr_all.values
for i in range(len(CORR_MEAS)):
    for j in range(i + 1, len(CORR_MEAS)):
        r = mm[i, j]
        if np.isfinite(r):
            pairs.append({"a": CORR_MEAS[i], "b": CORR_MEAS[j], "rho": float(r), "abs_rho": abs(float(r)),
                          "construct_a": VARIABLES[CORR_MEAS[i]][1], "construct_b": VARIABLES[CORR_MEAS[j]][1]})
pairs = pd.DataFrame(pairs).sort_values("abs_rho", ascending=False)
redundant = pairs[pairs.abs_rho >= 0.8].copy()
write_table(redundant, os.path.join(OUTD, "redundancy_pairs.csv"))
write_table(pairs.head(200), os.path.join(OUTD, "strongest_correlations.csv"))

# per-family stability of the correlation structure
famA, famB = "Qwen3", "Ministral3"
cA = corr_matrix(d[d.family == famA], CORR_MEAS).values
cB = corr_matrix(d[d.family == famB], CORR_MEAS).values
iu = np.triu_indices(len(CORR_MEAS), 1)
mfin = np.isfinite(cA[iu]) & np.isfinite(cB[iu])
fam_agree = float(spearmanr(cA[iu][mfin], cB[iu][mfin])[0])

# hierarchical clustering on 1 - |rho|
dist = 1 - np.abs(corr_all.values)
np.fill_diagonal(dist, 0.0)
dist = np.where(np.isfinite(dist), dist, 1.0)
dist = (dist + dist.T) / 2
Z = linkage(squareform(dist, checks=False), method="average")
CUT = 0.55
clusters = fcluster(Z, t=CUT, criterion="distance")
clus_tbl = pd.DataFrame({"measure": CORR_MEAS, "construct": [VARIABLES[m][1] for m in CORR_MEAS], "cluster": clusters})
clus_tbl = clus_tbl.sort_values(["cluster", "construct", "measure"])
n_clusters = int(clus_tbl.cluster.nunique())
cut_rows = []
for t in [0.3, 0.4, 0.5, CUT, 0.6, 0.7, 0.8, 0.9]:
    cl = fcluster(Z, t=t, criterion="distance")
    s = pd.Series(cl).value_counts()
    clus_tbl[f"cluster_at_{t}"] = cl
    cut_rows.append({"cut_1_minus_abs_rho": t, "n_clusters": int(s.nunique() * 0 + len(s)),
                     "n_singletons": int((s == 1).sum()), "largest_cluster": int(s.max())})
cut_tbl = pd.DataFrame(cut_rows)
write_table(cut_tbl, os.path.join(OUTD, "cluster_counts_by_cut.csv"), floats=2)
write_table(clus_tbl, os.path.join(OUTD, "instrument_clusters.csv"))

fig, ax = plt.subplots(figsize=(9, 0.19 * len(CORR_MEAS) + 2.2))
dendrogram(Z, labels=[f"{m}" for m in CORR_MEAS], orientation="right", ax=ax,
           color_threshold=CUT, leaf_font_size=7)
ax.axvline(CUT, color="red", ls="--", lw=1)
ax.set_xlabel("1 - |Spearman rho| (average linkage)")
ax.set_title(f"Instrument clustering over {n_cells_a0:,} arm-A0 cells; cut at {CUT} gives {n_clusters} clusters", fontsize=10)
fig_dend = savefig(fig, os.path.join(OUTD, "instrument_dendrogram.png"))

# PCA with Horn parallel analysis on complete-case, high-completeness measures
PCA_MEAS = [m for m in CORR_MEAS if d[m].notna().mean() >= 0.95]
X = d[PCA_MEAS].astype(float).dropna()
Xz = (X - X.mean()) / X.std(ddof=1)
Xz = Xz.loc[:, Xz.std().gt(0)]
PCA_MEAS = list(Xz.columns)
ev_obs = np.linalg.eigvalsh(np.corrcoef(Xz.values, rowvar=False))[::-1]
rng = np.random.default_rng(RNG)
sim = np.empty((200, len(PCA_MEAS)))
for i in range(200):
    Y = rng.standard_normal(Xz.shape)
    sim[i] = np.linalg.eigvalsh(np.corrcoef(Y, rowvar=False))[::-1]
ev_95 = np.quantile(sim, 0.95, axis=0)
n_factors = int(np.sum(ev_obs > ev_95))
pa = pd.DataFrame({"component": np.arange(1, len(ev_obs) + 1), "eigenvalue": ev_obs,
                   "parallel_95th": ev_95, "retained": ev_obs > ev_95,
                   "variance_share": ev_obs / ev_obs.sum(),
                   "cumulative_share": np.cumsum(ev_obs) / ev_obs.sum()})
write_table(pa, os.path.join(OUTD, "pca_parallel_analysis.csv"))

evals, evecs = np.linalg.eigh(np.corrcoef(Xz.values, rowvar=False))
order = np.argsort(evals)[::-1]
load = pd.DataFrame(evecs[:, order[:max(n_factors, 1)]] * np.sqrt(evals[order[:max(n_factors, 1)]]),
                    index=PCA_MEAS, columns=[f"PC{i + 1}" for i in range(max(n_factors, 1))])
load.insert(0, "construct", [VARIABLES[m][1] for m in PCA_MEAS])
write_table(load.reset_index().rename(columns={"index": "measure"}), os.path.join(OUTD, "pca_loadings.csv"))

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(pa.component, pa.eigenvalue, "o-", label="observed eigenvalue", color="#1f77b4")
ax.plot(pa.component, pa.parallel_95th, "s--", label="95th percentile of random data", color="#d62728", ms=4)
ax.axvline(n_factors + 0.5, color="grey", ls=":", lw=1)
ax.set_xlabel("component"); ax.set_ylabel("eigenvalue")
ax.set_title(f"Parallel analysis over {len(PCA_MEAS)} instruments, {len(Xz):,} complete cells: {n_factors} components retained", fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.3, lw=0.5)
fig_scree = savefig(fig, os.path.join(OUTD, "pca_scree_parallel.png"))

# correlation heatmap ordered by the dendrogram
ordr = dendrogram(Z, no_plot=True)["leaves"]
fig, ax = plt.subplots(figsize=(0.17 * len(CORR_MEAS) + 3, 0.17 * len(CORR_MEAS) + 3))
im = ax.imshow(corr_all.values[np.ix_(ordr, ordr)], cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(ordr))); ax.set_xticklabels([CORR_MEAS[i] for i in ordr], rotation=90, fontsize=6)
ax.set_yticks(range(len(ordr))); ax.set_yticklabels([CORR_MEAS[i] for i in ordr], fontsize=6)
fig.colorbar(im, ax=ax, shrink=0.6, label="Spearman rho")
ax.set_title("Instrument agreement, arm A0, clustered order", fontsize=10)
fig_heat = savefig(fig, os.path.join(OUTD, "spearman_heatmap.png"))

# ---------------------------------------------------------------------------
# 1b. Instrument disagreement on adapter gain: LUAR vs Wegmann vs StyleDistance
# ---------------------------------------------------------------------------
EMB = ["luar_cos_ref", "wegmann_cos_ref", "styledist_cos_ref"]
floors = {}
n_floor_pairs_qwen = n_floor_pairs_min = 0
for m in set(EMB + INSTR):
    t = replicate_floor(cells, m)
    floors[m] = float(t.abs_mean_diff.max()) if len(t) else np.nan
    if len(t):
        n_floor_pairs_qwen = max(n_floor_pairs_qwen, int((t.family == "Qwen3").sum()))
        n_floor_pairs_min = max(n_floor_pairs_min, int((t.family == "Ministral3").sum()))

bas = d[d.kind == "base"][KEYS + ["id", "sample"] + EMB]
ada = d[d.kind == "adapter"][KEYS + ["id", "sample"] + EMB]
pair = bas.merge(ada, on=KEYS + ["id", "sample"], suffixes=("_base", "_ada"))
for m in EMB:
    pair["d_" + m] = pair[m + "_ada"] - pair[m + "_base"]

rows = []
for (au, fam, pb), g in pair.groupby(KEYS):
    rec = {"author": au, "family": fam, "params_b": pb, "n_pairs": int(len(g)), "n_briefs": int(g.id.nunique())}
    for m in EMB:
        pt, lo, hi = cluster_bootstrap(g, "d_" + m, "id", n=NBOOT, seed=RNG)
        rec[f"gain_{m}"] = pt; rec[f"lo_{m}"] = lo; rec[f"hi_{m}"] = hi
        rec[f"floor_{m}"] = floors.get(m, np.nan)
        rec[f"above_floor_{m}"] = abs(pt) > floors.get(m, np.nan) if pt == pt else False
    fl = {m: floors.get(m, np.nan) for m in EMB}
    flags = []
    for i in range(len(EMB)):
        for j in range(i + 1, len(EMB)):
            a, b = EMB[i], EMB[j]
            gap = abs(rec[f"gain_{a}"] - rec[f"gain_{b}"])
            thr = 2 * max(fl[a], fl[b])
            rec[f"gap_{a.split('_')[0]}_{b.split('_')[0]}"] = gap
            if gap > thr:
                flags.append(f"{a.split('_')[0]}!={b.split('_')[0]}")
    rec["disagreement_flags"] = ",".join(flags)
    rec["n_disagreements"] = len(flags)
    rows.append(rec)
disagree = pd.DataFrame(rows).sort_values(KEYS)
write_table(disagree, os.path.join(OUTD, "embedding_disagreement.csv"), floats=5)
n_disagree_cfg = int((disagree.n_disagreements > 0).sum())

emb_rank = []
for i in range(len(EMB)):
    for j in range(i + 1, len(EMB)):
        r, lo, hi, p, n = spearman_ci(disagree[f"gain_{EMB[i]}"], disagree[f"gain_{EMB[j]}"], n=NBOOT, seed=RNG)
        emb_rank.append({"a": EMB[i], "b": EMB[j], "spearman_of_gains": r, "ci_low": lo, "ci_high": hi, "p": p, "n": n})
emb_rank = pd.DataFrame(emb_rank)
emb_rank["q_bh"] = bh_fdr(emb_rank.p.values)
write_table(emb_rank, os.path.join(OUTD, "embedding_gain_agreement.csv"), floats=5)

# ---------------------------------------------------------------------------
# 2. Calibrated positions and distributional fidelity
# ---------------------------------------------------------------------------
print(f"[15] positions and F over {len(INSTR)} instruments x {n_cfg} configurations", flush=True)


def w1(a, b):
    return float(wasserstein_distance(a, b))


cfg_keys = d.groupby(KEYS + ["kind"]).groups.keys()
rows_pos, rows_F = [], []
rng = np.random.default_rng(RNG)

for (au, fam, pb, kind) in cfg_keys:
    g = d[(d.author == au) & (d.family == fam) & (d.params_b == pb) & (d.kind == kind)]
    run = g.run.iloc[0]
    rH = ref_src[ref_src.run == run]
    rP = ref_pop[ref_pop.run == run]
    if not len(rH) or not len(rP):
        continue
    # one set of brief resamples per configuration, reused across instruments
    codes, uniq = pd.factorize(g.id.values)
    idx_by_brief = [np.where(codes == k)[0] for k in range(len(uniq))]
    boots = [np.concatenate([idx_by_brief[i] for i in rng.integers(0, len(uniq), size=len(uniq))])
             for _ in range(NBOOT_F)]
    for m in INSTR:
        G = g[m].astype(float).values
        H = rH[m].astype(float).dropna().values
        P = rP[m].astype(float).dropna().values
        okG = np.isfinite(G)
        if okG.sum() < 10 or len(H) < 5 or len(P) < 5:
            continue
        Gv = G[okG]
        mH, mP, mG = float(np.mean(H)), float(np.mean(P)), float(np.mean(Gv))
        sep = mH - mP
        pos = (mG - mP) / sep if sep != 0 else np.nan
        den = w1(P, H)
        F = 1 - w1(Gv, H) / den if den > 0 else np.nan
        fb = []
        for bidx in boots:
            gv = G[bidx]
            gv = gv[np.isfinite(gv)]
            if len(gv) < 5 or den <= 0:
                continue
            fb.append(1 - w1(gv, H) / den)
        lo, hi = (float(np.quantile(fb, 0.025)), float(np.quantile(fb, 0.975))) if fb else (np.nan, np.nan)
        rows_F.append({"author": au, "family": fam, "params_b": pb, "kind": kind, "run": run,
                       "measure": m, "construct": VARIABLES[m][1], "n_G": int(len(Gv)), "n_H": int(len(H)),
                       "n_P": int(len(P)), "F": F, "F_lo": lo, "F_hi": hi,
                       "W1_G_H": w1(Gv, H), "W1_P_H": den, "floor": floors.get(m, np.nan)})
        rows_pos.append({"author": au, "family": fam, "params_b": pb, "kind": kind, "run": run,
                         "measure": m, "construct": VARIABLES[m][1], "mean_G": mG, "mean_H": mH, "mean_P": mP,
                         "anchor_separation": sep, "abs_separation": abs(sep), "pos": pos,
                         "floor": floors.get(m, np.nan),
                         "anchor_below_floor": abs(sep) < (floors.get(m, np.nan) if floors.get(m, np.nan) == floors.get(m, np.nan) else -1)})

positions = pd.DataFrame(rows_pos)
fidelity = pd.DataFrame(rows_F)
write_table(positions, os.path.join(OUTD, "positions_by_configuration.csv"), floats=5)
write_table(fidelity, os.path.join(OUTD, "fidelity_by_configuration.csv"), floats=5)

# instruments whose anchors are too close together to calibrate a position on
anchor = (positions.groupby("measure")
          .agg(median_abs_separation=("abs_separation", "median"),
               floor=("floor", "first"),
               configs=("pos", "size"),
               share_anchor_below_floor=("anchor_below_floor", "mean"),
               median_pos=("pos", "median"),
               pos_iqr=("pos", lambda x: float(np.nanquantile(x, 0.75) - np.nanquantile(x, 0.25))))
          .reset_index())
anchor["separation_over_floor"] = anchor.median_abs_separation / anchor.floor
anchor["position_usable"] = anchor.separation_over_floor >= 2
anchor = anchor.sort_values("separation_over_floor", ascending=False)
write_table(anchor, os.path.join(OUTD, "anchor_separation.csv"), floats=5)
n_pos_usable = int(anchor.position_usable.sum())

# summary of F by instrument and kind
fid_summary = (fidelity.groupby(["measure", "construct", "kind"])
               .agg(n_configs=("F", "size"), median_F=("F", "median"),
                    mean_F=("F", "mean"), q25=("F", lambda x: float(np.nanquantile(x, 0.25))),
                    q75=("F", lambda x: float(np.nanquantile(x, 0.75))),
                    median_W1_P_H=("W1_P_H", "median"))
               .reset_index())
fid_wide = fid_summary.pivot_table(index=["measure", "construct"], columns="kind",
                                   values=["median_F", "median_W1_P_H"]).reset_index()
fid_wide.columns = ["_".join([c for c in col if c]) for col in fid_wide.columns.to_flat_index()]
fid_wide["adapter_minus_base_median_F"] = fid_wide.get("median_F_adapter") - fid_wide.get("median_F_base")
fid_wide = fid_wide.sort_values("median_F_base", ascending=False)
write_table(fid_summary, os.path.join(OUTD, "fidelity_by_instrument.csv"), floats=5)
write_table(fid_wide, os.path.join(OUTD, "fidelity_by_instrument_wide.csv"), floats=5)

# family indices: median F over the instruments of a family, with the disagreement flag
FAM_VOICE_E = [m for m in ["luar_cos_ref", "wegmann_cos_ref", "styledist_cos_ref"] if m in INSTR]
FAM_VOICE_S = [m for m in ["geo_index", "cr_pos", "open_entropy", "open_top_share", "pct_short8",
                           "sent_len_cv", "mattr", "mtld", "delta_own", "commas_per_sent"] if m in INSTR]
FAM_CONSTR = [m for m in ["sent_echo", "distinct_3", "rep_4", "max_repeat"] if m in INSTR]


def family_index(sub, members):
    x = sub[sub.measure.isin(members)]
    if not len(x):
        return np.nan, ""
    med = float(np.nanmedian(x.F))
    flags = []
    vals = x.set_index("measure").F.to_dict()
    fl = x.set_index("measure").floor.to_dict()
    ms = list(vals)
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            a, b = ms[i], ms[j]
            if abs(vals[a] - vals[b]) > 2 * max(fl.get(a, 0) or 0, fl.get(b, 0) or 0) + 0.25:
                flags.append(f"{a}!={b}")
    return med, ";".join(flags[:6])


frows = []
for (au, fam, pb, kind), g in fidelity.groupby(KEYS + ["kind"]):
    ve, fe = family_index(g, FAM_VOICE_E)
    vs, fs = family_index(g, FAM_VOICE_S)
    cc, fc = family_index(g, FAM_CONSTR)
    frows.append({"author": au, "family": fam, "params_b": pb, "kind": kind,
                  "F_VOICE_E": ve, "F_VOICE_S": vs, "F_CONSTRUCTION": cc,
                  "voiceE_disagreement": fe, "constr_disagreement": fc,
                  "dist_to_11": float(np.sqrt((1 - np.nanmedian([ve, vs])) ** 2 + (1 - cc) ** 2))})
fam_index = pd.DataFrame(frows).sort_values(KEYS + ["kind"])
write_table(fam_index, os.path.join(OUTD, "family_fidelity_index.csv"), floats=5)

# ---------------------------------------------------------------------------
# 3. Author-region rate R
# ---------------------------------------------------------------------------
print("[15] author-region rate", flush=True)
REGION_REQUESTED = ["luar_cos_ref", "wegmann_cos_ref", "otd_js", "per"]
REGION_USED = [m for m in REGION_REQUESTED if m in INSTR]
REGION_DROPPED = [m for m in REGION_REQUESTED if m not in INSTR]
REGION_EXT = [m for m in ["luar_cos_ref", "wegmann_cos_ref", "styledist_cos_ref", "geo_index"] if m in INSTR]


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, c - h), min(1.0, c + h))


rrows = []
for (au, fam, pb, kind), g in d.groupby(KEYS + ["kind"]):
    run = g.run.iloc[0]
    rH = ref_src[ref_src.run == run]
    if not len(rH):
        continue
    for label, members in [("requested_subset", REGION_USED), ("voice_extended", REGION_EXT)]:
        if not members:
            continue
        inside = np.ones(len(g), dtype=bool)
        bounds = {}
        for m in members:
            H = rH[m].astype(float).dropna().values
            lo, hi = float(np.quantile(H, 0.05)), float(np.quantile(H, 0.95))
            bounds[m] = (lo, hi)
            v = g[m].astype(float).values
            inside &= np.isfinite(v) & (v >= lo) & (v <= hi)
        gg = g.assign(_inside=inside)
        k1, n1 = int(inside.sum()), int(len(inside))
        R, R_lo, R_hi = wilson(k1, n1)
        by_brief = gg.groupby("id")._inside.max()
        k2, n2 = int(by_brief.sum()), int(len(by_brief))
        R2, R2_lo, R2_hi = wilson(k2, n2)
        # the same rule applied to the author's own passages (the ceiling) and to the
        # stranger pool (the floor), so that R has something to be read against
        rP = ref_pop[ref_pop.run == run]
        ins_H = np.ones(len(rH), dtype=bool)
        ins_P = np.ones(len(rP), dtype=bool)
        for m in members:
            lo, hi = bounds[m]
            vh = rH[m].astype(float).values
            vp = rP[m].astype(float).values
            ins_H &= np.isfinite(vh) & (vh >= lo) & (vh <= hi)
            ins_P &= np.isfinite(vp) & (vp >= lo) & (vp <= hi)
        rrows.append({"author": au, "family": fam, "params_b": pb, "kind": kind, "region": label,
                      "n_instruments": len(members), "instruments": ",".join(members),
                      "n_passages": n1, "n_inside": k1, "R": R, "R_lo": R_lo, "R_hi": R_hi,
                      "n_briefs": n2, "n_briefs_inside": k2, "R_at_2": R2, "R2_lo": R2_lo, "R2_hi": R2_hi,
                      "R_ceiling_author_own": float(ins_H.mean()), "R_floor_strangers": float(ins_P.mean()),
                      "R_scaled": (R - float(ins_P.mean())) / (float(ins_H.mean()) - float(ins_P.mean()))
                      if float(ins_H.mean()) > float(ins_P.mean()) else np.nan,
                      **{f"lo_{m}": bounds[m][0] for m in members}, **{f"hi_{m}": bounds[m][1] for m in members}})
region = pd.DataFrame(rrows).sort_values(["region"] + KEYS + ["kind"])
write_table(region, os.path.join(OUTD, "author_region_rate.csv"), floats=5)

# per-instrument region hit rate, so a zero R can be attributed
irows = []
for (au, fam, pb, kind), g in d.groupby(KEYS + ["kind"]):
    run = g.run.iloc[0]
    rH = ref_src[ref_src.run == run]
    if not len(rH):
        continue
    for m in sorted(set(REGION_USED + REGION_EXT)):
        H = rH[m].astype(float).dropna().values
        lo, hi = float(np.quantile(H, 0.05)), float(np.quantile(H, 0.95))
        v = g[m].astype(float).values
        ins = np.isfinite(v) & (v >= lo) & (v <= hi)
        p, l, h = wilson(int(ins.sum()), int(len(ins)))
        irows.append({"author": au, "family": fam, "params_b": pb, "kind": kind, "measure": m,
                      "H_lo90": lo, "H_hi90": hi, "n": int(len(ins)), "n_inside": int(ins.sum()),
                      "rate": p, "rate_lo": l, "rate_hi": h})
region_by_instr = pd.DataFrame(irows)
write_table(region_by_instr, os.path.join(OUTD, "region_rate_by_instrument.csv"), floats=5)

reg_sub = region[region.region == "requested_subset"]
reg_summary = (reg_sub.groupby(["family", "params_b", "kind"])
               .agg(n_configs=("R", "size"), mean_R=("R", "mean"), median_R=("R", "median"),
                    mean_R_at_2=("R_at_2", "mean"),
                    mean_ceiling=("R_ceiling_author_own", "mean"), mean_floor=("R_floor_strangers", "mean"),
                    mean_R_scaled=("R_scaled", "mean"), n_authors=("author", "nunique"))
               .reset_index())
write_table(reg_summary, os.path.join(OUTD, "author_region_summary.csv"), floats=5)

# ---------------------------------------------------------------------------
# figures: fidelity plane and F by instrument
# ---------------------------------------------------------------------------
print("[15] figures", flush=True)
SIZE_ORDER = [("Qwen3", 1.7), ("Qwen3", 4.0), ("Qwen3", 8.0), ("Qwen3", 14.0),
              ("Ministral3", 3.0), ("Ministral3", 8.0), ("Ministral3", 14.0)]
CLS = d[["author", "author_class"]].drop_duplicates().set_index("author").author_class.to_dict()
CLS_COLOR = {"period": "#1f77b4", "contemporary": "#d62728", "private": "#2ca02c"}

fig, axes = plt.subplots(2, 4, figsize=(19, 9.5), sharex=True, sharey=True)
for ax, (fam, pb) in zip(axes.ravel(), SIZE_ORDER):
    b = fam_index[(fam_index.family == fam) & (fam_index.params_b == pb) & (fam_index.kind == "base")].set_index("author")
    a = fam_index[(fam_index.family == fam) & (fam_index.params_b == pb) & (fam_index.kind == "adapter")].set_index("author")
    for au in sorted(set(b.index) & set(a.index)):
        col = CLS_COLOR.get(CLS.get(au), "#666")
        ax.annotate("", xy=(a.loc[au, "F_VOICE_E"], a.loc[au, "F_CONSTRUCTION"]),
                    xytext=(b.loc[au, "F_VOICE_E"], b.loc[au, "F_CONSTRUCTION"]),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.3, alpha=0.85))
        ax.scatter([b.loc[au, "F_VOICE_E"]], [b.loc[au, "F_CONSTRUCTION"]], s=16, c=col, marker="o", zorder=3)
        ax.scatter([a.loc[au, "F_VOICE_E"]], [a.loc[au, "F_CONSTRUCTION"]], s=28, c=col, marker="*", zorder=3)
        ax.annotate(au[:9], (a.loc[au, "F_VOICE_E"], a.loc[au, "F_CONSTRUCTION"]), fontsize=6,
                    xytext=(2, 2), textcoords="offset points", color=col)
    ax.scatter([1], [1], marker="P", s=70, c="k", zorder=4)
    ax.axhline(0, color="grey", lw=0.6); ax.axvline(0, color="grey", lw=0.6)
    ax.set_title(f"{fam} {pb:g}B  (n authors = {len(set(b.index) & set(a.index))})", fontsize=10)
    ax.grid(alpha=0.25, lw=0.5); ax.margins(0.10)
    ax.set_yscale("symlog", linthresh=1)
fig.supxlabel("VOICE-E fidelity F (median over LUAR, Wegmann, StyleDistance cosines to the reference set)", fontsize=10)
fig.supylabel("CONSTRUCTION fidelity F, symlog scale below -1\n(median over sentence echo, distinct-3, repeat-4, longest repeat;\nits W1(P, H) denominator is near zero, so the magnitudes are ratio artefacts)", fontsize=9)
axes.ravel()[-1].axis("off")
h = [plt.Line2D([], [], color=c, marker="o", ls="", label=k) for k, c in CLS_COLOR.items()]
h += [plt.Line2D([], [], color="k", marker="o", ls="", label="base (circle)"),
      plt.Line2D([], [], color="k", marker="*", ls="", label="adapter (star)"),
      plt.Line2D([], [], color="k", marker="P", ls="", label="the author's own passages (1, 1)")]
axes.ravel()[-1].legend(handles=h, loc="center", fontsize=9, frameon=False)
fig.suptitle("Fidelity plane: F = 1 - W1(G, H) / W1(P, H), arm A0, base -> adapter", fontsize=12)
fig_plane = savefig(fig, os.path.join(OUTD, "fidelity_plane.png"))

top = (fid_summary[fid_summary.kind == "base"].sort_values("median_F", ascending=False).measure.tolist())
fig, ax = plt.subplots(figsize=(10, 0.26 * len(top) + 2))
y = np.arange(len(top))
for kind, off, col, mk in [("base", -0.16, "#1f77b4", "o"), ("adapter", 0.16, "#d62728", "*")]:
    s = fid_summary[fid_summary.kind == kind].set_index("measure").reindex(top)
    ax.errorbar(s.median_F, y + off, xerr=[np.maximum(s.median_F - s.q25, 0), np.maximum(s.q75 - s.median_F, 0)],
                fmt=mk, ms=5, lw=1.0, color=col, label=kind)
ax.axvline(1, color="k", ls="--", lw=1); ax.axvline(0, color="grey", lw=0.8)
ax.set_xscale("symlog", linthresh=1)
ax.set_yticks(y); ax.set_yticklabels(top, fontsize=7)
ax.set_xlabel("distributional fidelity F, symlog below -1 (1 = the author's own passages, 0 = strangers)\nmedian over configurations with the IQR", fontsize=9)
ax.set_title("Fidelity by instrument, arm A0", fontsize=11)
ax.legend(fontsize=9); ax.grid(alpha=0.3, lw=0.5, axis="x")
fig_fid = savefig(fig, os.path.join(OUTD, "fidelity_by_instrument.png"))

fig, axes = plt.subplots(1, 2, figsize=(14, 0.19 * len(reg_sub) / 2 + 3), sharey=True)
order = (reg_sub[reg_sub.kind == "base"]
         .sort_values(["family", "params_b", "author"])[KEYS].reset_index(drop=True))
order["_y"] = np.arange(len(order))
for ax, lab in zip(axes, ["requested_subset", "voice_extended"]):
    s = region[region.region == lab].merge(order, on=KEYS, how="inner")
    for kind, off, col, mk in [("base", -0.18, "#1f77b4", "o"), ("adapter", 0.18, "#d62728", "*")]:
        ss = s[s.kind == kind].sort_values("_y")
        lo = np.maximum(0.0, (ss.R - ss.R_lo).values)
        hi = np.maximum(0.0, (ss.R_hi - ss.R).values)
        ax.errorbar(ss.R.values, ss._y.values + off, xerr=[lo, hi], fmt=mk, ms=4, lw=0.8,
                    color=col, alpha=0.85, label=kind)
    ax.set_xlabel("author-region rate R (Wilson 95%)", fontsize=9)
    ax.set_title(f"{lab}\n{s.instruments.iloc[0] if len(s) else ''}", fontsize=8)
    ax.legend(fontsize=8); ax.grid(alpha=0.3, lw=0.5, axis="x")
axes[0].set_yticks(order._y.values)
axes[0].set_yticklabels([f"{r.family[:4]}-{r.params_b:g}B {r.author[:10]}" for r in order.itertuples()], fontsize=6)
fig.suptitle("Share of generated passages inside the central 90% of the author's own passages, on every instrument at once", fontsize=11)
fig_region = savefig(fig, os.path.join(OUTD, "author_region_rate.png"))

# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------
red_top = redundant.head(20)[["a", "b", "rho", "construct_a", "construct_b"]]
notcal_tbl = NOT_CAL[["measure", "construct", "source", "reason_if_not"]].sort_values(["construct", "measure"])
anchor_tbl = anchor[["measure", "median_abs_separation", "floor", "separation_over_floor", "position_usable", "median_pos", "pos_iqr"]]
fid_tbl = fid_wide[["measure", "construct", "median_F_base", "median_F_adapter", "adapter_minus_base_median_F", "median_W1_P_H_base"]]
dis_tbl = disagree[KEYS + ["gain_luar_cos_ref", "gain_wegmann_cos_ref", "gain_styledist_cos_ref", "n_disagreements", "disagreement_flags"]]

# README-only bookkeeping (no table, figure or computation is changed by these)
n_region_authors = int(reg_sub.author.nunique())
n_disagree_authors = int(disagree.author.nunique())
n_qwen_ada_R = {int(pb): reg_sub[(reg_sub.family == "Qwen3") & (reg_sub.params_b == pb) & (reg_sub.kind == "adapter")].author.nunique()
                for pb in (4, 8, 14)}

R_base = reg_sub[reg_sub.kind == "base"]
R_ada = reg_sub[reg_sub.kind == "adapter"]
r_zero = int((reg_sub.R == 0).sum())
best_R = reg_sub.nlargest(5, "R")[KEYS + ["kind", "R", "R_lo", "R_hi", "R_at_2"]]
voiceE_base = fid_summary[(fid_summary.kind == "base") & (fid_summary.measure.isin(FAM_VOICE_E))]
voiceE_ada = fid_summary[(fid_summary.kind == "adapter") & (fid_summary.measure.isin(FAM_VOICE_E))]
n_flagged_voiceE = int((fam_index.voiceE_disagreement.str.len() > 0).sum())
neg_F = fid_summary[fid_summary.median_F < 0].measure.nunique()

write_readme(
    OUTD,
    "15 - Instrument agreement and calibrated fidelity",
    f"""
    Two questions. First, how many separate things do the {len(CORR_MEAS)} numeric instruments in the
    variable dictionary actually measure on these {n_cells_a0:,} arm-A0 passages, and which of them are
    redundant with each other. Second, which instruments can be put on the author-calibrated
    scale that `FIDELITY_SYNTHESIS.md` specifies - a position between the stranger pool P and
    the author's own held-out passages H, and a distributional fidelity
    F = 1 - W1(G, H) / W1(P, H) - and what those numbers say about the {n_cfg} configurations.
    The script also computes the author-region rate R: the share of generated passages that
    fall inside the central 90% interval of the author's own passages on every calibrated
    instrument at once.
    """,
    f"""
    **Data.** `data/master/cells.parquet` at arm A0, non-replicate, both samples, both kinds
    ({n_cells_a0:,} cells, {n_runs_a0} runs, {n_cfg} configurations) for G, and
    `data/master/references.parquet` for the anchors. H is the `group == "source"` rows of a
    run: the author's own held-out passages, scored inside that run against the author's
    reference profile ({int(ref_src.groupby('run').size().median())} per run at the median). P is the `group == "other:*"` rows
    of the same run ({int(ref_pop.groupby('run').size().median())} per run at the median). A given reference passage gets the same
    value in every run of its author on {len(INSTR) - len(UNSTABLE)} of the {len(INSTR)} calibratable instruments, which is the
    consistency check that the reference scoring is deterministic; the {len(UNSTABLE)} that fail it are
    named below and in `anchor_stability.csv`.

    **Which instruments could be calibrated.** `instrument_calibration_coverage.csv` lists
    every one of the {len(VARIABLES)} dictionary variables with the reason it is or is not calibratable.
    {len(INSTR)} are: all of them are `scores.jsonl` measures, because those are the only ones the
    reference passages were scored on. {len(NOT_CAL)} are not. The important exclusions are the
    {int(NOT_CAL.source.str.startswith('eval cache').sum())} eval-cache measures -
    {', '.join('`' + m + '`' for m in sorted(NOT_CAL[NOT_CAL.source.str.startswith('eval cache')].measure))} -
    which exist for generations only. The caches in
    `data/eval_results/cache/*.json` carry a `source_stats` block, but that block is a single
    mean and standard deviation of the author's own passages per author, not per-passage
    values, and it contains nothing at all for other authors. Without a per-passage H there
    is no Wasserstein distance and without any P there is no denominator, so **F and pos are
    not computed for `otd_js` or `per`**, and the author region cannot use them either.

    **Positions and F.** For each configuration and each calibratable instrument:
    pos = (mean G - mean P) / (mean H - mean P), and F = 1 - W1(G, H) / W1(P, H) using
    `scipy.stats.wasserstein_distance`. F carries a cluster bootstrap over briefs
    ({NBOOT_F} resamples; the same brief resamples are reused across instruments within a
    configuration so that instruments are compared on the same resampling). `anchor_separation.csv`
    reports |mean H - mean P| against each instrument's replicate floor: where the two anchors
    are closer together than twice the floor the position is a ratio of two noise terms and is
    marked unusable ({n_pos_usable} of {len(anchor)} instruments pass that test).

    **Agreement.** Spearman over A0 cells, pooled and per family; average-linkage clustering on
    1 - |rho| cut at {CUT}; PCA with Horn parallel analysis (200 random matrices, 95th percentile)
    on the {len(PCA_MEAS)} instruments with at least 95% completeness over {len(Xz):,} complete cells; and the
    brief-paired adapter gain of the three style embeddings per author, with the
    FIDELITY_SYNTHESIS disagreement rule (two instruments in a family disagree when their
    gains differ by more than twice the larger replicate floor).

    **Correction.** BH-FDR within each family of tests (the embedding-gain agreement table,
    the region tables). Effect sizes and intervals lead; p-values follow.

    **Floors.** Replicate floors come from `lib.replicate_floor`, which finds
    {n_floor_pairs_qwen} twice-generated Qwen3 base pairs in the master table and {n_floor_pairs_min} Ministral3 pairs. This
    script takes one floor per instrument, the largest absolute difference over every pair of
    either family, so a floor here is a pooled worst case and not a per-family noise model;
    where a family is noisier than the other its own contrasts are compared with a floor set
    partly by the quieter one. The Ministral3 pairs were scored on 2026-09-10, so any earlier
    reading of this folder saw Qwen3-only floors.
    """,
    f"""
    **Unit of replication.** The configuration (author x family x size x kind) for F and pos,
    the author for anything said about models. F intervals are cluster bootstraps over the
    {int(fidelity.n_G.median())}-odd generated passages of one configuration, grouped by brief: they answer "would
    this author's other briefs give the same F", not "would another author".

    **How wide the intervals are.** The median F interval half-width over all
    {len(fidelity):,} configuration-by-instrument rows is
    {float(np.nanmedian((fidelity.F_hi - fidelity.F_lo) / 2)):.3f}, which is the resolution at which two configurations can be
    told apart on one instrument. Differences smaller than that are not differences.

    **The denominator is the fragile part.** F is a ratio whose denominator is W1(P, H), the
    distance between strangers and the author on that instrument. Where the instrument does
    not separate strangers from the author the denominator is near zero and F swings wildly;
    `fidelity_by_instrument_wide.csv` carries `median_W1_P_H_base` next to every F for exactly
    this reason. The construction instruments are the clear case: strangers' prose is as
    coherent as the author's, so W1(P, H) on sentence echo and repeat rate is tiny and the
    construction axis of the fidelity plane is the least trustworthy number in this folder.
    `FIDELITY_SYNTHESIS.md` section 2 proposed the author's own sentence-shuffled passages as
    the construction anchor instead. Its 2026-09-10 amendment withdraws that: proposition echo
    is close to permutation-invariant, so a sentence shuffle fails the anchor's own
    manipulation check, and no shuffled floor and no F value may be quoted for `per` from any
    pool. The plane's vertical axis is therefore a placeholder with no replacement currently
    available, and it is labelled as one.

    **What would overturn it.** Per-passage reference values for `per` and `otd_js`, and a
    register-matched stranger pool. Both measures are named in the plan as members of the
    region and of the construction family, both are absent from the reference scoring, and
    adding them would change R directly rather than adjust it at the margin; `per` would enter
    only as a raw rate and as region membership, because the 2026-09-10 amendment forbids an F
    for it. Register matching is the larger change: `scripts/23_register_matched_pool.py`
    reports that it moves contemporary and private authors' positions down by more than the
    adapter gain and halves the share of usable rows, so every position and F for those two
    author classes here is provisional. The correlation and clustering results would not
    change; they rest on the generations alone.

    **What it does not show.** It does not show that any configuration writes like the author.
    F near 1 on an instrument means the generated distribution on that one statistic is as
    close to the author's as the author's own passages are to each other, which is a
    necessary condition and nowhere near a sufficient one. R is the summary to quote and it is
    small. No judge score is quoted as a level anywhere: `coverage`, `rubric_C`, `rubric_S`,
    `fool_vs_source` and `win_vs_A0` are not calibratable and appear only inside the
    correlation matrix, where the `rubric_C`/`rubric_S` pair is read as two judge instruments
    tracking each other rather than as a measure of the prose.
    """,
    caveats=[
        f"The stranger pool P is period fiction for every author: the fourteen `other:*` groups are austen, cather, chesterton, chopin, conrad, joyce, lovecraft, mansfield, melville, sui_sin_far, watanna, wells, wharton, woolf. For the five contemporary and three private authors the population anchor therefore comes from a different century and register than H, which is not the pool FIDELITY_SYNTHESIS section 1 specifies. Positions and F for those authors are on a different scale from the period authors' and the two groups should not be pooled.",
        "`per` and `otd_js` have no per-passage reference values anywhere in data/, so they enter neither F nor pos nor the author region; the region is computed on the calibratable subset and the dropped members are named in the table.",
        "The construction family's F has a near-zero denominator by construction (strangers are coherent); read it as a diagnostic, not as a fidelity.",
        f"Replicate floors rest on {n_floor_pairs_qwen} Qwen3 pairs and {n_floor_pairs_min} Ministral3 pairs and are taken as one pooled worst case per instrument, not per family, so an 'above floor' verdict on either family is read against the noisier of the two. The Ministral3 pairs were scored on 2026-09-10.",
        "Ministral3 covers three authors; Qwen3 1.7B covers one. Their rows are descriptive.",
        f"{int((degen_bad.family == 'Ministral3').sum())} measures are empty or constant across every Ministral3 arm-A0 cell ({', '.join(sorted(degen_bad[degen_bad.family == 'Ministral3'].measure))}), so `spearman_matrix_Ministral3.csv` carries NaN rows for them. The judge measures were never run on Ministral3 at all; the rest are constant. The cross-family correlation-structure agreement is computed on the pairs that exist in both.",
        f"H is 25 to 50 passages per author ({int(ref_src.groupby('run').size().min())} at the minimum, for link), so the central 90% interval of H is estimated from as few as {int(ref_src.groupby('run').size().min())} values and its tails are unstable; R inherits that.",
        "Arm A0 only. The A4/A5 arms show the model the author's own statistics, so a position on those arms would be compliance, not fidelity.",
        f"{', '.join(sorted(UNSTABLE))} are run-dependent even on the author's own passages ({float(anchor_stability[anchor_stability.measure == UNSTABLE[0]].share_run_dependent.iloc[0]) * 100:.0f}% of reference passages take more than one value across the runs of their author). All four are measured against 'generic AI prose' taken from the scoring run itself, so the anchor is not fixed and their positions, F values and region bounds are conditional on the run. Every other calibratable instrument is bit-identical across runs, which is the check that the rest of the reference scoring is deterministic.",
        f"The author-region rate has a high floor: with only {len(REGION_USED)} instruments and a 90% interval each, a stranger's passage lands inside the region {float(reg_sub.R_floor_strangers.mean()) * 100:.0f}% of the time. Quote `R_scaled` (floor to ceiling) rather than R when comparing regions of different width.",
        "Wilson intervals on R treat the passages of a configuration as independent; they are two samples per brief and are not, so the interval is optimistic. R@2 is the brief-level number and is the safer one.",
        "Generated and reference passages were not matched on length before F was computed; `words` is included as a calibratable instrument so that its own F can be read as the length-matching diagnostic.",
        "Proposition echo is close to permutation-invariant, so the sentence-shuffled construction floor that FIDELITY_SYNTHESIS section 2 prescribed fails its own manipulation check. No shuffled floor and no F value may be quoted for `per` from any pool; raw rates and region membership are the only permitted readings of it, here or anywhere in this workspace.",
        "The event-order measure has a ceiling on the authors' own passages, reported per author in the 2026-09-10 amendment to FIDELITY_SYNTHESIS.md, so a tau at or above it on a generation is not evidence of fidelity. `tau` is not calibratable here, and is listed among the exclusions for a different reason (no per-passage reference values), which does not make that ceiling irrelevant to anyone reading tau elsewhere.",
        "The per-run `emb_*.npy` files are not row-aligned with `scores.jsonl` in most runs; this script reads `references.parquet` and the stored scores only, and `scripts/23_register_matched_pool.py` holds the verified repair. Any follow-up that reads an embedding row directly must reproduce a stored cosine first.",
        "`patrick` (the v1-chunking control) is included in the configuration counts, the region tables and the embedding-disagreement table here, unlike script 14, which excludes it from author-level tests. `patrick` and `patrick_v2` are the same corpus chunked two ways, so the author counts in this folder are one higher than the study's usable author count.",
        "The Qwen3 runs listed under the 2026-09-09 credit outage in LOG.md carry error rows for coverage and are being rejudged. `coverage` is not calibratable and enters only the Spearman matrix and the degenerate-column table, both of which shift slightly when that rerun lands.",
        f"The {int(d.author.nunique())} authors in these tables, not the number of tests, are what limits every claim in this folder; BH-FDR within a table does not buy back replication, and one of those authors (`patrick`) is a chunking control on the same corpus as `patrick_v2`.",
    ],
    tables=[
        ("Instruments that could not be calibrated, and why", notcal_tbl),
        ("Anchor stability: does a reference passage get the same value in every run?",
         anchor_stability.head(8)[["measure", "construct", "n_reference_passages", "share_run_dependent",
                                   "max_distinct_values_one_passage", "median_within_over_between_sd"]]),
        ("Anchor separation: can a position be estimated on this instrument at all", anchor_tbl),
        ("Distributional fidelity by instrument, base and adapter", fid_tbl),
        ("Parallel analysis", pa.head(15)),
        ("Redundancy pairs at |rho| >= 0.8 (top 20)", red_top),
        ("Measures that are empty or constant within a family at arm A0 (their correlation row is NaN by necessity, not by error)",
         degen_bad[["family", "measure", "construct", "n_cells", "n_non_null", "n_distinct"]]),
        ("Embedding disagreement on adapter gain, per author", dis_tbl),
        ("Author-region rate summary by family, size and kind", reg_summary),
        ("The five configurations with the highest author-region rate", best_R),
    ],
    figures=[("Instrument dendrogram", fig_dend),
             ("Spearman heatmap in clustered order", fig_heat),
             ("Parallel analysis scree", fig_scree),
             ("Fidelity by instrument", fig_fid),
             ("Fidelity plane, base -> adapter", fig_plane),
             ("Author-region rate per configuration", fig_region)],
    extra=f"""
### Headline numbers

- **{len(INSTR)} of the {len(VARIABLES)} dictionary variables can be put on the author-calibrated scale.**
  Every calibratable one is a `scores.jsonl` measure. The whole eval-cache layer - PER, opener-class
  distance, hapax, cadence, paragraph shape, event order, the constructional tell index - was
  computed on generations only, and the caches keep a per-author mean and sd of the author's own
  passages rather than the values, so neither F nor a position exists for any of them.
- **Only {n_pos_usable} of {len(anchor)} calibratable instruments have anchors far enough apart to carry a
  position.** The median |mean H - mean P| over instruments is {float(anchor.median_abs_separation.median()):.4f} against a median
  replicate floor of {float(anchor.floor.median()):.4f}. Where the ratio is below 2 the position is two noise terms
  divided by each other.
- **The three style embeddings do not agree on what the adapter did.** Over
  {len(disagree)} author-by-family-by-size cells from {n_disagree_authors} authors (`patrick`, the v1-chunking control,
  among them), {n_disagree_cfg} carry at least one pairwise disagreement flag. The cells of one author are
  not independent of each other, so the rank correlations below describe the spread across
  configurations and are not an author-level estimate.
  The rank correlation between LUAR gain and Wegmann gain across cells is
  {emb_rank[(emb_rank.a == 'luar_cos_ref') & (emb_rank.b == 'wegmann_cos_ref')].spearman_of_gains.iloc[0]:+.3f}
  [{emb_rank[(emb_rank.a == 'luar_cos_ref') & (emb_rank.b == 'wegmann_cos_ref')].ci_low.iloc[0]:+.3f},
  {emb_rank[(emb_rank.a == 'luar_cos_ref') & (emb_rank.b == 'wegmann_cos_ref')].ci_high.iloc[0]:+.3f}], and between LUAR and StyleDistance
  {emb_rank[(emb_rank.a == 'luar_cos_ref') & (emb_rank.b == 'styledist_cos_ref')].spearman_of_gains.iloc[0]:+.3f}
  [{emb_rank[(emb_rank.a == 'luar_cos_ref') & (emb_rank.b == 'styledist_cos_ref')].ci_low.iloc[0]:+.3f},
  {emb_rank[(emb_rank.a == 'luar_cos_ref') & (emb_rank.b == 'styledist_cos_ref')].ci_high.iloc[0]:+.3f}].
  {n_flagged_voiceE} of {len(fam_index)} configurations carry a VOICE-E disagreement flag on F.
- **The instruments measure fewer things than there are instruments, but not far fewer.**
  Horn's parallel analysis retains **{n_factors} components** of {len(PCA_MEAS)}, carrying
  {float(pa.cumulative_share.iloc[n_factors - 1]) * 100:.1f}% of the variance; the first component alone carries
  {float(pa.variance_share.iloc[0]) * 100:.1f}% and the first five {float(pa.cumulative_share.iloc[4]) * 100:.1f}%. It takes
  {int((pa.cumulative_share < 0.8).sum()) + 1} components to reach 80%. Horn's test is liberal at
  {len(Xz):,} rows - the 95th-percentile random eigenvalue is only {float(pa.parallel_95th.iloc[0]):.2f} - so read
  "{n_factors} components" as an upper bound on the number of separable things, not a factor solution.
  Average-linkage clustering at 1 - |rho| = {CUT} gives {n_clusters} clusters
  ({int(cut_tbl[cut_tbl.cut_1_minus_abs_rho == CUT].n_singletons.iloc[0])} of them singletons; see `cluster_counts_by_cut.csv` for other cuts), and
  {len(redundant)} instrument pairs sit at |rho| >= 0.8 - `mattr`/`mtld` at {redundant.iloc[0].rho:+.3f},
  `distinct_3`/`rep_4` at {float(redundant[(redundant.a == 'distinct_3') & (redundant.b == 'rep_4')].rho.iloc[0]) if len(redundant[(redundant.a == 'distinct_3') & (redundant.b == 'rep_4')]) else float('nan'):+.3f}, and `rubric_C`/`rubric_S` at
  {float(redundant[(redundant.a == 'rubric_C') & (redundant.b == 'rubric_S')].rho.iloc[0]) if len(redundant[(redundant.a == 'rubric_C') & (redundant.b == 'rubric_S')]) else float('nan'):+.3f}, which is the judge's construction block and its craft block measuring one thing.
  The correlation structure is stable across model families: Spearman between the Qwen3 and
  Ministral3 off-diagonal correlations is {fam_agree:+.3f}.
- **Four anchors are not anchors.** `anchor_stability.csv` runs the check that a reference
  passage must get the same value in every run of its author. {len(INSTR) - len(UNSTABLE)} of the {len(INSTR)} calibratable
  instruments pass bit-exactly. **{', '.join('`' + m + '`' for m in sorted(UNSTABLE))} do not**:
  {float(anchor_stability[anchor_stability.measure == UNSTABLE[0]].share_run_dependent.iloc[0]) * 100:.1f}% of the author's own reference passages take a different value depending
  on which run scored them, up to {int(anchor_stability[anchor_stability.measure == UNSTABLE[0]].max_distinct_values_one_passage.iloc[0])} distinct values for one passage. All four depend on the
  "generic AI prose" side of the comparison, which is drawn from the scoring run's own output,
  so the anchor moves with the thing being measured. `geo_index`, whose within-passage spread
  is {float(anchor_stability[anchor_stability.measure == 'geo_index'].median_within_over_between_sd.iloc[0]):.2f} of its between-passage spread, is the one of the four that the plan uses as a
  voice-structure instrument; its position, F and region bound are conditional on the run and
  should not be compared across runs.
- **Fidelity on voice is well below the author and the three cosines disagree about where it
  sits.** Median F over configurations on the three cosines to the reference set: base
  {float(voiceE_base.median_F.median()):+.3f}, adapter {float(voiceE_ada.median_F.median()):+.3f}. That pair of numbers is a median over three instruments whose
  own medians run from {float(voiceE_base.median_F.min()):+.3f} to {float(voiceE_base.median_F.max()):+.3f} at base and {float(voiceE_ada.median_F.min()):+.3f} to {float(voiceE_ada.median_F.max()):+.3f} under the adapter, it is
  not a brief-paired contrast, and no floor applies to a ratio of Wasserstein distances, so it
  supports a direction and not a size. {neg_F} instruments have a negative median F, meaning the generated
  distribution sits further from the author than the stranger pool does.
- **The author-region rate is higher under the adapter than under the base, and it has to be
  read against its own ceiling.** These are means over configurations from {n_region_authors} authors
  (`patrick`, the v1-chunking control, among them), unpaired and untested, with several
  configurations per author. On {', '.join(REGION_USED)} (the calibratable members of the requested set;
  {', '.join(REGION_DROPPED) if REGION_DROPPED else 'none'} had to be dropped for want of reference values), mean R is
  {float(R_base.R.mean()):.3f} for base configurations and {float(R_ada.R.mean()):.3f} for adapters, with R@2
  {float(R_base.R_at_2.mean()):.3f} and {float(R_ada.R_at_2.mean()):.3f}. The same rule applied to the author's own passages puts
  the ceiling at {float(reg_sub.R_ceiling_author_own.mean()):.3f} and applied to the stranger pool puts the floor at
  {float(reg_sub.R_floor_strangers.mean()):.3f}. The floor is that high because {len(REGION_USED)} instruments with a 90% interval each is a
  wide region - a stranger's passage lands inside it {float(reg_sub.R_floor_strangers.mean()) * 100:.0f}% of the time - which is the price of
  dropping `per` and `otd_js` from it. On the floor-to-ceiling scale the base sits at
  {float(R_base.R_scaled.median()):.3f} (median; mean {float(R_base.R_scaled.mean()):.3f}) and the adapter at {float(R_ada.R_scaled.median()):.3f}
  (median; mean {float(R_ada.R_scaled.mean()):.3f}). {int((R_base.R < R_base.R_floor_strangers).sum())} of {len(R_base)} base configurations sit **below** their own stranger
  floor - their passages land in the author's region less often than a random other author's
  passages do - against {int((R_ada.R < R_ada.R_floor_strangers).sum())} of {len(R_ada)} adapter configurations. The adapter's contribution on
  this measure is to move the generator from at or below the stranger floor to part of the way
  towards the author. {r_zero} of {len(reg_sub)} configurations have R exactly 0.
  On the four-instrument extended voice region the region is tighter (floor
  {float(region[region.region == 'voice_extended'].R_floor_strangers.mean()):.3f}, ceiling {float(region[region.region == 'voice_extended'].R_ceiling_author_own.mean()):.3f}) and mean R is
  {float(region[(region.region == 'voice_extended') & (region.kind == 'base')].R.mean()):.3f} (base) and
  {float(region[(region.region == 'voice_extended') & (region.kind == 'adapter')].R.mean()):.3f} (adapter).
  Within Qwen3 the adapter's mean R is flat across parameter count
  ({float(reg_sub[(reg_sub.family == 'Qwen3') & (reg_sub.params_b == 4) & (reg_sub.kind == 'adapter')].R.mean()):.3f} at 4B on {n_qwen_ada_R[4]} authors,
  {float(reg_sub[(reg_sub.family == 'Qwen3') & (reg_sub.params_b == 8) & (reg_sub.kind == 'adapter')].R.mean()):.3f} at 8B on {n_qwen_ada_R[8]},
  {float(reg_sub[(reg_sub.family == 'Qwen3') & (reg_sub.params_b == 14) & (reg_sub.kind == 'adapter')].R.mean()):.3f} at 14B on {n_qwen_ada_R[14]}). No test of that flatness is run here, and three means over
  thirteen or fourteen authors cannot rule out a change smaller than they can resolve.
""",
)

print(f"[15] done in {time.time() - T0:.1f}s -> {OUTD}", flush=True)
