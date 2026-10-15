"""27 Voice-Adherence Exchange (VAX) table.

Promoted 2026-09-12 from exploration_2026-09-11/scratch/R11/vax.py, which implemented the
specification in exploration_2026-09-11/findings/R5_instrument_design.md. Every method in the
study is expressed as two numbers in replicate-floor units: V, the voice change, and A, the
brief-adherence change, with A read twice (the coverage judge and the mechanical event matcher).
A method that buys voice and pays adherence gets an exchange rate E = V / |A|, the voice bought
per floor of adherence lost.

Two defects R11 found in its own run are repaired here.

1. The specification's three regions leave the quadrant (V inside one floor, adherence inside one
   floor) unnamed and label it "frontier", where no exchange rate exists. `region` is now a
   four-region scheme that names it `inside_floor_box`, and `region_spec3` keeps the original
   three labels so earlier readings stay checkable.
2. The disagreement test between the two adherence readings fired on opposite signs alone, so two
   readings that both sat inside the floor box counted as disagreeing. `adherence_disagree` now
   requires both readings to be outside the floor box with opposite signs; the old test is kept as
   `adherence_disagree_sign_only`.

Depends on the analysis folder of script 10 (replicate floors) and on data/master.

Outputs (analysis/27_voice_adherence_exchange/):
  vax_by_author.csv             one row per method, control and author
  vax_pooled.csv                median over authors per method, with region counts
  vax_series.csv                the corpus-size series as a path through the plane
  vax_replicate_validation.csv  the replicate twins, which must land inside the unit box
  vax_plane.png                 the exchange plane
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from lib import *  # noqa

# a measure with no scored cells in one arm gives an all-NaN column; nanmean is the intended
# reading there and the row is reported with n_<measure> = 0
warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)

HERE = outdir("27_voice_adherence_exchange")

NBOOT = 2000
SEED = 11
VOICE = "luar_cos_source"
VOICE_ALT = "luar_cos_ref"
AJ = "coverage"          # judged adherence
AM = "events_present"    # mechanical adherence
MEAS = [VOICE, VOICE_ALT, AJ, AM]

floors = pd.read_csv(os.path.join(OUT, "10_inventory_integrity", "replicate_floors.csv"))
FLOOR = {(r.measure, r.family): float(r.floor_abs_mean_diff) for r in floors.itertuples()}

cells = pd.read_parquet(os.path.join(MASTER, "cells.parquet"))
series = pd.read_parquet(os.path.join(MASTER, "cells_series.parquet"))
frontier = pd.read_parquet(os.path.join(MASTER, "cells_frontier.parquet"))
MAIN = cells[~cells.replicate].copy()


def per_brief(df, measures):
    return df.groupby("id")[measures].mean()


def compare(method_df, control_df, measures, floor_family, seed=SEED):
    """Brief-paired mean difference per measure, in floor units, with a bootstrap over briefs."""
    a = per_brief(method_df, measures)
    b = per_brief(control_df, measures)
    ids = a.index.intersection(b.index)
    if len(ids) < 3:
        return None
    arr = (a.loc[ids] - b.loc[ids]).to_numpy(dtype=float)
    n = len(ids)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(NBOOT, n))
    with np.errstate(invalid="ignore"):
        point = np.nanmean(arr, axis=0)
        boots = np.nanmean(arr[idx, :], axis=1)
    out = {"n_briefs": n}
    units, bunits = {}, {}
    for j, m in enumerate(measures):
        fl = FLOOR.get((m, floor_family), np.nan)
        nz = int(np.isfinite(arr[:, j]).sum())
        bu = boots[:, j] / fl
        u = point[j] / fl if nz else np.nan
        units[m] = float(u) if u == u else np.nan
        bunits[m] = bu
        out["n_" + m] = nz
        out["raw_" + m] = float(point[j]) if nz else np.nan
        out["u_" + m] = units[m]
        out["u_" + m + "_lo"] = float(np.nanquantile(bu, 0.025)) if nz else np.nan
        out["u_" + m + "_hi"] = float(np.nanquantile(bu, 0.975)) if nz else np.nan
        out["floor_" + m] = fl
    return out, units, bunits


def region_and_E(V, Aj, Am, bV, bAj, bAm):
    """Four named regions, the specification's three, the disagreement flags and the two rates."""
    res = {}
    have_m = Am == Am
    minA = float(np.nanmin([Aj, Am])) if have_m else Aj

    # repair 1: the fourth quadrant is named rather than folded into the frontier
    if V != V or minA != minA:
        region = "undefined"
    elif V > 1 and minA > -1:
        region = "dominant"
    elif V > 1 and minA <= -1:
        region = "frontier"
    elif V <= 1 and minA <= -1:
        region = "dominated"
    else:
        region = "inside_floor_box"
    res["region"] = region
    res["region_spec3"] = {"inside_floor_box": "frontier"}.get(region, region)

    # the finer split inside the fourth region, kept from R11
    detail = region
    if region == "inside_floor_box":
        if abs(V) <= 1 and abs(minA) <= 1:
            detail = "null_inside_floor_box"
        elif V < -1 and minA > 1:
            detail = "voice_loss_adherence_gain"
        elif V < -1:
            detail = "voice_loss_no_adherence_cost"
        elif minA > 1:
            detail = "adherence_gain_no_voice_gain"
        else:
            detail = "mixed_inside_box"
    res["region_detail"] = detail

    # repair 2: disagreement requires both readings outside the floor box, not opposite signs alone
    signs_oppose = bool(have_m and ((Aj > 0 and Am < 0) or (Aj < 0 and Am > 0)))
    res["adherence_disagree_sign_only"] = signs_oppose
    res["adherence_disagree"] = bool(signs_oppose and abs(Aj) > 1 and abs(Am) > 1)
    res["both_adherence_below_m1"] = bool(have_m and Aj <= -1 and Am <= -1)
    res["adherence_readings"] = "judged+mechanical" if have_m else "judged_only"

    for tag, A, bA in (("j", Aj, bAj), ("m", Am, bAm)):
        E = lo = hi = frac = np.nan
        if A == A and A <= -1 and V == V:
            E = V / abs(A)
            ok = np.isfinite(bA) & (bA < 0)
            if ok.sum() > 50:
                r = bV[ok] / np.abs(bA[ok])
                lo = float(np.nanquantile(r, 0.025))
                hi = float(np.nanquantile(r, 0.975))
            frac = float(ok.mean())
        res["E_" + tag] = E
        res["E_" + tag + "_lo"] = lo
        res["E_" + tag + "_hi"] = hi
        res["E_" + tag + "_boot_valid_frac"] = frac
    return res


rows = []


def add(method_df, control_df, method, control, author, family, floor_family, size, extra=None):
    r = compare(method_df, control_df, MEAS, floor_family)
    if r is None:
        return
    out, units, bunits = r
    V, Aj, Am, Vr = units[VOICE], units[AJ], units[AM], units[VOICE_ALT]
    reg = region_and_E(V, Aj, Am, bunits[VOICE], bunits[AJ], bunits[AM])
    regr = region_and_E(Vr, Aj, Am, bunits[VOICE_ALT], bunits[AJ], bunits[AM])
    row = {"method": method, "control": control, "author": author, "family": family,
           "floor_family": floor_family, "size_b": size}
    row.update(out)
    row.update(reg)
    row["V"] = V
    row["A_j"] = Aj
    row["A_m"] = Am
    row["V_ref"] = Vr
    row["region_ref"] = regr["region"]
    row["region_flips_on_ref"] = bool(regr["region"] != reg["region"])
    if extra:
        row.update(extra)
    rows.append(row)


# 1. adapter A0 versus base A0, every size, both families
for (fam, tag), g in MAIN.groupby(["family", "tag"]):
    size = float(g.params_b.iloc[0])
    for au, ga in g.groupby("author"):
        ad = ga[(ga.kind == "adapter") & (ga.arm == "A0")]
        ba = ga[(ga.kind == "base") & (ga.arm == "A0")]
        if len(ad) and len(ba):
            add(ad, ba, "adapter_A0", "base_A0", au, fam, fam, size)

# 2. prompting arms on the base versus base A0
for (fam, tag), g in MAIN.groupby(["family", "tag"]):
    size = float(g.params_b.iloc[0])
    if fam == "Qwen3" and tag not in ("4b", "8b", "14b"):
        continue
    if fam == "Ministral3" and tag not in ("m3b", "m8b", "m14b"):
        continue
    for au, ga in g.groupby("author"):
        ba0 = ga[(ga.kind == "base") & (ga.arm == "A0")]
        if not len(ba0):
            continue
        for arm in ["A1", "A2", "A3", "A4", "A5"]:
            bx = ga[(ga.kind == "base") & (ga.arm == arm)]
            if len(bx):
                add(bx, ba0, "base_" + arm, "base_A0", au, fam, fam, size)

# 3. adapter A5 versus adapter A0
for (fam, tag), g in MAIN.groupby(["family", "tag"]):
    size = float(g.params_b.iloc[0])
    for au, ga in g.groupby("author"):
        a5 = ga[(ga.kind == "adapter") & (ga.arm == "A5")]
        a0 = ga[(ga.kind == "adapter") & (ga.arm == "A0")]
        if len(a5) and len(a0):
            add(a5, a0, "adapter_A5", "adapter_A0", au, fam, fam, size)

# 4. hosted models F0 versus the author's Qwen 4B base A0 and adapter A0
FRONT_NAME = {"base4b": "flash", "luna": "luna", "pro": "pro"}
q4 = MAIN[(MAIN.family == "Qwen3") & (MAIN.tag == "4b")]
for lbl, gf in frontier[frontier.arm == "F0"].groupby("frontier_label"):
    nm = FRONT_NAME.get(lbl, lbl)
    for au, ga in gf.groupby("author"):
        if au == "patrick":       # v1 chunking control, not a study author
            continue
        ba = q4[(q4.author == au) & (q4.kind == "base") & (q4.arm == "A0")]
        ad = q4[(q4.author == au) & (q4.kind == "adapter") & (q4.arm == "A0")]
        if len(ba):
            add(ga, ba, "frontier_" + nm + "_F0", "qwen4b_base_A0", au, "frontier", "Qwen3", np.nan)
        if len(ad):
            add(ga, ad, "frontier_" + nm + "_F0", "qwen4b_adapter_A0", au, "frontier", "Qwen3", np.nan)

# 5. corpus-size series versus the author's base4b A0
for run, gs in series[series.arm == "A0"].groupby("run"):
    au = gs.author.iloc[0]
    tb = float(gs.train_briefs_n.iloc[0])
    seed_t = int(gs.targets_seed.iloc[0])
    ba = q4[(q4.author == au) & (q4.kind == "base") & (q4.arm == "A0")]
    if len(ba):
        add(gs, ba, "series_" + str(int(tb)) + ("_s1" if seed_t else ""), "base4b_A0", au,
            "Qwen3", "Qwen3", 4.0,
            extra={"train_briefs_n": tb, "targets_seed": seed_t, "series_run": run})

REN = {"u_" + VOICE + "_lo": "V_lo", "u_" + VOICE + "_hi": "V_hi",
       "u_" + AJ + "_lo": "A_j_lo", "u_" + AJ + "_hi": "A_j_hi",
       "u_" + AM + "_lo": "A_m_lo", "u_" + AM + "_hi": "A_m_hi",
       "u_" + VOICE_ALT + "_lo": "V_ref_lo", "u_" + VOICE_ALT + "_hi": "V_ref_hi"}
by_author = pd.DataFrame(rows).rename(columns=REN)
write_table(by_author, os.path.join(HERE, "vax_by_author.csv"))
print("vax_by_author.csv rows:", len(by_author))


def boot_median(vals, seed=SEED, n=NBOOT):
    v = np.asarray([x for x in vals if x == x], float)
    if len(v) == 0:
        return (np.nan, np.nan, np.nan, 0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(n, len(v)))
    b = np.median(v[idx], axis=1)
    return (float(np.median(v)), float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975)), len(v))


NAN1 = np.array([np.nan])
REGIONS = ("dominant", "frontier", "dominated", "inside_floor_box")
pool_rows = []
is_series = by_author.method.str.startswith("series_")
for (meth, ctrl, fam, size), g in by_author[~is_series].groupby(
        ["method", "control", "family", "size_b"], dropna=False):
    rec = {"method": meth, "control": ctrl, "family": fam, "size_b": size, "k_authors": len(g)}
    for nm in ("V", "A_j", "A_m", "V_ref", "E_j", "E_m"):
        p, lo, hi, k = boot_median(g[nm].values)
        rec["med_" + nm] = p
        rec["med_" + nm + "_lo"] = lo
        rec["med_" + nm + "_hi"] = hi
        rec["k_" + nm] = k
    r = region_and_E(rec["med_V"], rec["med_A_j"], rec["med_A_m"], NAN1, NAN1, NAN1)
    rec["region_pooled"] = r["region"]
    rec["region_spec3_pooled"] = r["region_spec3"]
    rec["region_detail_pooled"] = r["region_detail"]
    rec["adherence_readings"] = r["adherence_readings"]
    for lab in REGIONS:
        rec["n_" + lab] = int((g.region == lab).sum())
    rec["n_adherence_disagree"] = int(g.adherence_disagree.sum())
    rec["n_adherence_disagree_sign_only"] = int(g.adherence_disagree_sign_only.sum())
    rec["n_flip_on_luar_ref"] = int(g.region_flips_on_ref.sum())
    rec["V_interval_excludes_1"] = bool(rec["med_V_lo"] > 1 or rec["med_V_hi"] < 1)
    rec["Aj_interval_excludes_m1"] = bool(rec["med_A_j_lo"] > -1 or rec["med_A_j_hi"] < -1)
    rec["Am_interval_excludes_m1"] = bool(
        rec["med_A_m"] == rec["med_A_m"] and (rec["med_A_m_lo"] > -1 or rec["med_A_m_hi"] < -1))
    pool_rows.append(rec)

pooled = pd.DataFrame(pool_rows).sort_values(["family", "method", "size_b"])
write_table(pooled, os.path.join(HERE, "vax_pooled.csv"))
print("vax_pooled.csv rows:", len(pooled))

# the full-corpus 4B adapter is the terminal point of each series (chesterton 235, doctorow 525,
# patrick_v2 107 training briefs; cells.parquet column train_briefs_passed)
TB_FULL = MAIN[(MAIN.tag == "4b") & (MAIN.kind == "adapter")].groupby("author").train_briefs_passed.first()
full = by_author[(by_author.method == "adapter_A0") & (by_author.control == "base_A0")
                 & (by_author.family == "Qwen3") & (by_author.size_b == 4.0)
                 & (by_author.author.isin(["chesterton", "doctorow", "patrick_v2"]))].copy()
full["train_briefs_n"] = full.author.map(TB_FULL).astype(float)
full["targets_seed"] = 0.0
full["series_run"] = full.author + "_paire6_4b (full corpus)"
full["series_point_source"] = "cells.parquet adapter_A0"
ser = by_author[is_series].copy()
ser["series_point_source"] = "cells_series.parquet"
ser = pd.concat([ser, full], ignore_index=True).sort_values(["author", "train_briefs_n", "targets_seed"])
scols = ["author", "series_run", "series_point_source", "train_briefs_n", "targets_seed", "n_briefs",
         "V", "V_lo", "V_hi", "A_j", "A_j_lo", "A_j_hi", "A_m", "A_m_lo", "A_m_hi",
         "region", "region_spec3", "region_detail", "E_j", "E_j_lo", "E_j_hi", "E_m", "E_m_lo",
         "E_m_hi", "V_ref", "region_ref", "region_flips_on_ref"]
write_table(ser[[c for c in scols if c in ser.columns]], os.path.join(HERE, "vax_series.csv"))
print("vax_series.csv rows:", len(ser))

# ---------------------------------------------------------------- validation: replicate twins
PAIRS = [("base4b", "base4b_r2"), ("chesterton_base4b", "chesterton_base4bc"),
         ("mansfield_base4b", "mansfield_base4b_r2"),
         ("chesterton_basem3b", "chesterton_basem3b_r2"),
         ("patrick_v2_basem3b", "patrick_v2_basem3b_r2"),
         ("chesterton_base8b", "chesterton_base8b_r2"),
         ("chesterton_base14b", "chesterton_base14b_r2"),
         ("chesterton_basem8b", "chesterton_basem8b_r2"),
         ("chesterton_basem14b", "chesterton_basem14b_r2")]
vrows = []
for a, b in PAIRS:
    x = cells[(cells.run == a) & (cells.arm == "A0")]
    y = cells[(cells.run == b) & (cells.arm == "A0")]
    if not len(x) or not len(y):
        vrows.append({"pair": a + " vs " + b, "status": "missing"})
        continue
    fam = str(x.family.iloc[0])
    out, units, bunits = compare(y, x, MEAS, fam)
    V, Aj, Am = units[VOICE], units[AJ], units[AM]
    reg = region_and_E(V, Aj, Am, bunits[VOICE], bunits[AJ], bunits[AM])
    vrows.append({"pair": a + " vs " + b, "family": fam, "n_briefs": out["n_briefs"],
                  "V": V, "A_j": Aj, "A_m": Am, "region": reg["region"],
                  "inside_unit_box": bool(abs(V) <= 1 + 1e-4 and (Aj != Aj or abs(Aj) <= 1 + 1e-4)
                                          and (Am != Am or abs(Am) <= 1 + 1e-4)),
                  "inside_unit_box_strict": bool(abs(V) <= 1 and (Aj != Aj or abs(Aj) <= 1)
                                                 and (Am != Am or abs(Am) <= 1)),
                  "max_abs_unit": float(np.nanmax(np.abs([V, Aj, Am]))),
                  "n_coverage": out["n_" + AJ]})
val = pd.DataFrame(vrows)
write_table(val, os.path.join(HERE, "vax_replicate_validation.csv"))
n_inside = int(val.get("inside_unit_box", pd.Series(dtype=bool)).sum())
print("replicate pairs inside the unit box:", n_inside, "of", len(val))

# ---------------------------------------------------------------- figure
GROUPS = [("adapter_A0", "base_A0", "Qwen3", "o", "#1f4e79", "adapter A0 vs base A0 (Qwen3)"),
          ("adapter_A0", "base_A0", "Ministral3", "s", "#8856a7", "adapter A0 vs base A0 (Ministral3)"),
          ("base_A1", "base_A0", None, "^", "#2e8b57", "base A1 vs A0"),
          ("base_A2", "base_A0", None, "v", "#66a61e", "base A2 vs A0"),
          ("base_A3", "base_A0", None, "<", "#e6ab02", "base A3 vs A0"),
          ("base_A4", "base_A0", None, ">", "#d95f02", "base A4 vs A0"),
          ("base_A5", "base_A0", None, "P", "#7570b3", "base A5 vs A0"),
          ("adapter_A5", "adapter_A0", None, "X", "#8c564b", "adapter A5 vs adapter A0"),
          ("frontier_flash_F0", "qwen4b_base_A0", None, "*", "#c00000", "flash F0 vs 4B base"),
          ("frontier_luna_F0", "qwen4b_base_A0", None, "*", "#ff7f0e", "luna F0 vs 4B base"),
          ("frontier_pro_F0", "qwen4b_base_A0", None, "*", "#17becf", "pro F0 vs 4B base"),
          ("frontier_flash_F0", "qwen4b_adapter_A0", None, "D", "#c00000", "flash F0 vs 4B adapter"),
          ("frontier_luna_F0", "qwen4b_adapter_A0", None, "D", "#ff7f0e", "luna F0 vs 4B adapter"),
          ("frontier_pro_F0", "qwen4b_adapter_A0", None, "D", "#17becf", "pro F0 vs 4B adapter")]
SER_COL = {"chesterton": "#000000", "doctorow": "#0055aa", "patrick_v2": "#aa0055"}


def draw(ax, xlim, ylim, label_series=True, ms=30):
    XL, XH = xlim
    YL, YH = ylim
    ax.add_patch(plt.Rectangle((-1, 1), XH + 1, YH - 1, color="#a8d5a2", alpha=0.40, lw=0, zorder=0))
    ax.add_patch(plt.Rectangle((XL, 1), -1 - XL, YH - 1, color="#f2dca7", alpha=0.55, lw=0, zorder=0))
    ax.add_patch(plt.Rectangle((XL, YL), -1 - XL, 1 - YL, color="#e8a89c", alpha=0.50, lw=0, zorder=0))
    ax.add_patch(plt.Rectangle((-1, YL), XH + 1, 1 - YL, color="#d9d9d9", alpha=0.55, lw=0, zorder=0))
    ax.axhline(1, color="k", lw=1.0, ls="--")
    ax.axvline(-1, color="k", lw=1.0, ls="--")
    ax.axhline(0, color="k", lw=0.5, alpha=0.4)
    ax.axvline(0, color="k", lw=0.5, alpha=0.4)
    for meth, ctrl, fam, mk, col, lab in GROUPS:
        d = by_author[(by_author.method == meth) & (by_author.control == ctrl)]
        if fam:
            d = d[d.family == fam]
        if not len(d):
            continue
        ax.scatter(d.A_j, d.V, marker=mk, s=ms, c=col, alpha=0.75, edgecolors="none", label=lab, zorder=3)
    for au, d in ser.groupby("author"):
        d = d[d.targets_seed == 0].sort_values("train_briefs_n")
        ax.plot(d.A_j, d.V, "-o", color=SER_COL.get(au, "#333333"), lw=1.8, ms=5, zorder=4,
                label="series " + au + " (25 to " + str(int(d.train_briefs_n.max())) + " briefs)")
        if label_series:
            for _, r in d.iterrows():
                ax.annotate(str(int(r.train_briefs_n)), (r.A_j, r.V), fontsize=7,
                            xytext=(3, 3), textcoords="offset points", color=SER_COL.get(au, "#333333"))
    ax.set_xlim(XL, XH)
    ax.set_ylim(YL, YH)
    ax.set_xlabel("A: judged adherence change (coverage), replicate-floor units")


fig, axes = plt.subplots(1, 2, figsize=(15, 7.2))
draw(axes[0], (-34, 28), (-7, 8), label_series=True, ms=26)
draw(axes[1], (-17, 4), (-2.5, 6.5), label_series=True, ms=44)
axes[0].set_ylabel("V: voice change (LUAR cosine to source), replicate-floor units")
axes[0].set_title("all comparisons, full range")
axes[1].set_title("zoom on the adapter and prompting cloud")
axes[0].add_patch(plt.Rectangle((-17, -2.5), 21, 9, fill=False, ec="k", lw=1.0, ls=":", zorder=5))
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, fontsize=8, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.suptitle("Voice-Adherence Exchange plane\n"
             "green dominant (V above 1 floor, A above minus 1 floor), yellow frontier, "
             "red dominated, grey inside the floor box; one point per author per method", fontsize=11)
fig.tight_layout(rect=(0, 0.07, 1, 0.93))
figpath = savefig(fig, os.path.join(HERE, "vax_plane.png"))

head = pooled[pooled.method.isin(["adapter_A0", "frontier_flash_F0", "frontier_luna_F0", "frontier_pro_F0"])][
    ["method", "control", "family", "size_b", "k_authors", "med_V", "med_A_j", "med_A_m",
     "med_E_j", "med_E_m", "region_pooled"]]
write_readme(
    HERE, "27 Voice-Adherence Exchange",
    """
    Each method in the study placed on one plane: V is its voice change and A its brief-adherence
    change, both as brief-paired mean differences divided by the replicate floor of the measure on
    that model family. Adherence is read twice, once by the coverage judge and once by the
    mechanical event matcher, because the two readings price the same method differently. Where a
    method buys voice above one floor and pays adherence below minus one floor, the exchange rate
    E = V / |A| says how much voice a floor of adherence bought.

    Methods covered: the adapter at every size on both families, the five prompting arms on the
    base, full conditioning on top of the adapter, three hosted models against both the local base
    and the local adapter, and the corpus-size series as a path through the plane.
    """,
    """
    Floors come from script 10 and are taken on the row's own family; hosted rows use the Qwen3
    floor because no hosted replicate pair exists. Bootstrap is over briefs within an author (2,000
    draws) and over authors for the pooled medians. Two defects in the 2026-09-11 exploratory run
    are repaired: the fourth quadrant is named inside_floor_box instead of being folded into the
    frontier (region_spec3 keeps the old three labels), and the disagreement flag between the two
    adherence readings now requires both readings to sit outside the floor box with opposite signs
    rather than firing on sign alone. The replicate twins are run through the same machinery as a
    null: a pair of identical configurations must land inside the unit box.
    """,
    """
    E is defined only in the frontier region, and it is a ratio of two noisy quantities, so read the
    bootstrap interval and the valid-draw fraction before quoting one. The two adherence readings
    disagree by about a factor of three on the adapter, and that factor appears nowhere else in the
    study, so no single price for the adapter should be quoted without naming the reading. A point
    inside the floor box is unresolved, not equal. Region membership can flip when voice is read
    against the author's reference set instead of the source passage; region_flips_on_ref counts it.
    """,
    caveats=[
        "Promoted from an exploratory pass (scratch/R11, 2026-09-11) implementing the R5 specification.",
        "The mechanical adherence reading exists for cells scored by the event matcher; rows without it are marked judged_only.",
        "Hosted-model rows have no replicate pair of their own, so their floor is borrowed from Qwen3.",
        "The series path is a single seed per size except where targets_seed marks a second draw.",
        f"Replicate twins inside the unit box: {n_inside} of {len(val)}.",
    ],
    tables=[("Adapter and hosted models, pooled over authors", head)],
    figures=[("Exchange plane", figpath)],
)
print(head.to_string(index=False))
