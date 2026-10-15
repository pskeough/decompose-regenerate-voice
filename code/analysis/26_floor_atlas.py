"""26 floor-normalised effect atlas.

Promoted 2026-09-12 from exploration_2026-09-11/scratch/R12/atlas.py, which was written and
checked as an exploratory pass on 2026-09-11. No numbers are recomputed from cells.parquet:
every contrast already published by scripts 11, 12, 18 and 25 is re-expressed in units of its
own measure's replicate floor from script 10, so one table says how large each reported effect
is against the smallest difference that measure can resolve on that model family.

Depends on the analysis folders of scripts 10, 11, 12, 18 and 25.

Outputs (analysis/26_floor_atlas/):
  effect_atlas.csv              one row per (source table, contrast, author-or-pooled, family, size, measure)
  atlas_summary.csv             share of contrasts under 1 floor / 1-2 / >2 / >5, by construct and contrast family
  instrument_noise_ranking.csv  floor-over-spread ranking within each family
  atlas.png                     dot-and-interval plot, 4B adapter-vs-base and 14B arm contrasts
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from lib import *  # noqa

HERE = outdir("26_floor_atlas")

# ---------------------------------------------------------------- floors
floors = pd.read_csv(os.path.join(OUT, "10_inventory_integrity", "replicate_floors.csv"))
# construct -> the five-label scheme the atlas reports in
FIVE = {"voice_embed": "voice", "voice_structure": "voice", "construction": "construction",
        "adherence": "adherence", "length": "length", "tell": "other", "attribution": "other",
        "judge": "other"}
floors["construct5"] = floors["construct"].map(FIVE).fillna("other")
# a floor of exactly 0 (memo_flag, preface) carries no information; treat as missing
floors.loc[floors["floor_abs_mean_diff"] <= 0, "floor_abs_mean_diff"] = np.nan

floor_map = {(m, f): v for m, f, v in zip(floors["measure"], floors["family"], floors["floor_abs_mean_diff"])}
construct_raw = dict(zip(floors["measure"], floors["construct"]))
construct5 = dict(zip(floors["measure"], floors["construct5"]))
fos_map = {(m, f): v for m, f, v in zip(floors["measure"], floors["family"], floors["floor_over_sd"])}


def base_measure(m):
    """d_open_entropy and friends are distances built from a base measure; use its construct."""
    return m[2:] if m.startswith("d_") and m[2:] in construct_raw else m


def add_construct(df):
    bm = df["measure"].map(base_measure)
    df["construct_raw"] = bm.map(construct_raw).fillna("unlabelled")
    df["construct"] = bm.map(construct5).fillna("other")
    return df


def attach_floor(df):
    keys = list(zip(df["measure"], df["family"]))
    df["floor"] = [floor_map.get(k, np.nan) for k in keys]
    df["floor_over_sd"] = [fos_map.get(k, np.nan) for k in keys]
    df["has_floor"] = df["floor"].notna()
    df["effect_in_floors"] = df["delta"] / df["floor"]
    df["ci_low_floors"] = df["ci_low"] / df["floor"]
    df["ci_high_floors"] = df["ci_high"] / df["floor"]
    df["above_floor"] = (df["delta"].abs() > df["floor"]).astype(object)
    df["ci_clear_of_floor"] = ((df["ci_low"] > df["floor"]) | (df["ci_high"] < -df["floor"])).astype(object)
    df.loc[~df["has_floor"], ["above_floor", "ci_clear_of_floor"]] = np.nan
    df["flag"] = np.where(df["has_floor"], "", "no_measured_floor_for_this_measure_and_family")
    return df


COLS = ["source_table", "contrast_family", "contrast", "author", "family", "size", "measure",
        "construct", "construct_raw", "delta", "ci_low", "ci_high", "floor", "floor_over_sd",
        "has_floor", "effect_in_floors", "ci_low_floors", "ci_high_floors", "above_floor",
        "ci_clear_of_floor", "flag", "note"]


def pack(df, source, cfam, contrast, author, family, size, note=""):
    out = pd.DataFrame({"source_table": source, "contrast_family": cfam, "contrast": contrast,
                        "author": author, "family": family, "size": size,
                        "measure": df["measure"].values, "delta": df["delta"].values,
                        "ci_low": df["ci_low"].values, "ci_high": df["ci_high"].values, "note": note})
    return attach_floor(add_construct(out))[COLS]


blocks = []

# ---------------------------------------------------------------- 11 scale curves
g = pd.read_csv(os.path.join(OUT, "11_scale_curves", "gain.csv")).rename(columns={"gain": "delta"})
blocks.append(pack(g, "analysis/11_scale_curves/gain.csv", "adapter_vs_base",
                   "adapter minus base (A0, per author)", g["author"], g["family"], g["params_b"],
                   note="brief-paired within author"))

# ---------------------------------------------------------------- 12 arm effects
ap = pd.read_csv(os.path.join(OUT, "12_arm_effects", "arm_contrasts_pooled.csv")).rename(columns={"mean_diff": "delta"})
blocks.append(pack(ap, "analysis/12_arm_effects/arm_contrasts_pooled.csv", "arm_vs_A0",
                   ap["arm"] + " vs A0 (base runs)", "pooled", ap["family"], ap["params_b"],
                   note="pooled over authors, bootstrap over authors"))

aa = pd.read_csv(os.path.join(OUT, "12_arm_effects", "adapter_arm_contrasts_pooled.csv")).rename(columns={"mean_diff": "delta"})
blocks.append(pack(aa, "analysis/12_arm_effects/adapter_arm_contrasts_pooled.csv", "arm_vs_A0",
                   aa["arm"] + " vs A0 (adapter runs)", "pooled", aa["family"], aa["params_b"],
                   note="conditioning on top of the adapter"))

ab = pd.read_csv(os.path.join(OUT, "12_arm_effects", "arm_contrasts_by_author.csv")).rename(columns={"mean_diff": "delta"})
blocks.append(pack(ab, "analysis/12_arm_effects/arm_contrasts_by_author.csv", "arm_vs_A0",
                   ab["arm"] + " vs A0 (base runs)", ab["author"], ab["family"], ab["params_b"],
                   note="per author, cluster bootstrap over briefs"))

# ---------------------------------------------------------------- 18 cross family
cf = pd.read_csv(os.path.join(OUT, "18_cross_family", "adapter_gain_paired.csv")).rename(columns={"gain": "delta"})
blocks.append(pack(cf, "analysis/18_cross_family/adapter_gain_paired.csv", "adapter_vs_base",
                   "adapter minus base (A0, rung " + cf["rung_name"] + ")", cf["author"], cf["family"],
                   cf["params_b"], note="three authors on both families"))

# ---------------------------------------------------------------- 25 frontier and series
fr = pd.read_csv(os.path.join(OUT, "25_series_and_frontier", "frontier_contrasts.csv"))
CMAP = {"F0 vs base A0": "hosted_vs_base", "F5 vs base A5": "hosted_vs_base",
        "F0 vs adapter A0": "hosted_vs_adapter", "F5 vs adapter A0": "hosted_vs_adapter",
        "F5 vs F0": "hosted_arm_F5_vs_F0"}
blocks.append(pack(fr, "analysis/25_series_and_frontier/frontier_contrasts.csv",
                   fr["contrast"].map(CMAP), fr["frontier_label"] + ": " + fr["contrast"],
                   fr["author"], "Qwen3", 4.0,
                   note=np.where(fr["is_control"], "is_control (patrick v1 chunking control)",
                                 "local side is Qwen3 4B")))

fm = pd.read_csv(os.path.join(OUT, "25_series_and_frontier", "frontier_model_contrast.csv"))
blocks.append(pack(fm, "analysis/25_series_and_frontier/frontier_model_contrast.csv", "hosted_vs_hosted",
                   fm["contrast"], fm["author"], "Qwen3", np.nan,
                   note=np.where(fm["is_control"], "is_control (patrick v1 chunking control)",
                                 "hosted model against hosted model at F0; floor is the Qwen3 floor")))

ss = pd.read_csv(os.path.join(OUT, "25_series_and_frontier", "size_series.csv"))
blocks.append(pack(ss, "analysis/25_series_and_frontier/size_series.csv", "series_point",
                   "size-series adapter minus base (" + ss["train_briefs"].astype(str) + " briefs, arm "
                   + ss["arm"] + ")", ss["author"], "Qwen3", 4.0,
                   note="point_kind=" + ss["point_kind"] + "; seed=" + ss["targets_seed"].astype(str)))

atlas = pd.concat(blocks, ignore_index=True)
write_table(atlas, os.path.join(HERE, "effect_atlas.csv"))


# ---------------------------------------------------------------- summaries
def bands(df):
    a = df["effect_in_floors"].abs()
    n = len(df)
    return pd.Series({"n_contrasts": n, "n_with_floor": int(df["has_floor"].sum()),
                      "share_under_1_floor": float((a < 1).mean()),
                      "share_1_to_2_floors": float(((a >= 1) & (a < 2)).mean()),
                      "share_above_2_floors": float((a >= 2).mean()),
                      "share_above_5_floors": float((a >= 5).mean()),
                      "share_ci_clear_of_floor": float(df["ci_clear_of_floor"].fillna(False).mean()),
                      "median_abs_effect_in_floors": float(a.median()),
                      "max_abs_effect_in_floors": float(a.max()) if n else np.nan})


w = atlas[atlas["has_floor"] & atlas["note"].ne("is_control (patrick v1 chunking control)")].copy()
w = w[np.isfinite(w["effect_in_floors"])]

rows = []
for (cfam, cons), d in w.groupby(["contrast_family", "construct"]):
    r = bands(d); r["block"] = "construct_x_contrast_family"; r["contrast_family"] = cfam
    r["construct"] = cons; r["family"] = "all"; r["size"] = "all"; rows.append(r)
for (cfam, fam, size, cons), d in w.groupby(["contrast_family", "family", "size", "construct"]):
    r = bands(d); r["block"] = "construct_x_contrast_family_x_family_x_size"; r["contrast_family"] = cfam
    r["construct"] = cons; r["family"] = fam; r["size"] = size; rows.append(r)
for (cfam, src), d in w.groupby(["contrast_family", "source_table"]):
    r = bands(d); r["block"] = "contrast_family_x_source_table"; r["contrast_family"] = cfam
    r["construct"] = "all"; r["family"] = src; r["size"] = "all"; rows.append(r)
for cfam, d in w.groupby("contrast_family"):
    r = bands(d); r["block"] = "contrast_family_all_constructs"; r["contrast_family"] = cfam
    r["construct"] = "all"; r["family"] = "all"; r["size"] = "all"; rows.append(r)

summ = pd.DataFrame(rows)[["block", "contrast_family", "construct", "family", "size", "n_contrasts",
                           "n_with_floor", "share_under_1_floor", "share_1_to_2_floors",
                           "share_above_2_floors", "share_above_5_floors", "share_ci_clear_of_floor",
                           "median_abs_effect_in_floors", "max_abs_effect_in_floors"]]
write_table(summ, os.path.join(HERE, "atlas_summary.csv"))

# quiet-versus-noisy instrument ranking from the floors file itself
rank = floors[["measure", "family", "n_pairs", "floor_abs_mean_diff", "sd_A0_base", "floor_over_sd",
               "construct", "construct5"]].copy()
rank = rank.sort_values(["family", "floor_over_sd"], ascending=[True, False])
rank["rank_within_family"] = rank.groupby("family")["floor_over_sd"].rank(ascending=False, method="min")
write_table(rank, os.path.join(HERE, "instrument_noise_ranking.csv"))

# ---------------------------------------------------------------- figure
CORD = ["voice", "construction", "adherence", "length", "other"]
CCOL = {"voice": "#1f4e79", "construction": "#a33b20", "adherence": "#2e7d32",
        "length": "#7b5aa6", "other": "#666666"}

panel_a = w[(w.contrast_family == "adapter_vs_base") & (w.family == "Qwen3") & (w["size"] == 4.0)
            & (w.source_table == "analysis/11_scale_curves/gain.csv")]
pa = (panel_a.groupby(["measure", "construct"])
      .agg(effect_in_floors=("effect_in_floors", "mean"), ci_low_floors=("ci_low_floors", "mean"),
           ci_high_floors=("ci_high_floors", "mean"), n=("effect_in_floors", "size")).reset_index())

panel_b = w[(w.contrast_family == "arm_vs_A0") & (w.family == "Qwen3") & (w["size"] == 14.0)
            & (w.source_table == "analysis/12_arm_effects/arm_contrasts_pooled.csv")]
pb = panel_b.copy()
pb["label"] = pb["measure"] + "  " + pb["contrast"].str.slice(0, 2)

fig, axes = plt.subplots(1, 2, figsize=(16.5, 12.5))


def draw(ax, d, labelcol, title, fs=8):
    d = d.copy()
    d["cord"] = d["construct"].map({c: i for i, c in enumerate(CORD)})
    d = d.sort_values(["cord", "effect_in_floors"])
    y = np.arange(len(d))
    for yi, (_, r) in zip(y, d.iterrows()):
        c = CCOL.get(r["construct"], "#666666")
        ax.plot([r["ci_low_floors"], r["ci_high_floors"]], [yi, yi], color=c, lw=1.6, alpha=0.85, zorder=2)
        ax.plot([r["effect_in_floors"]], [yi], "o", color=c, ms=5.5, zorder=3)
    ax.axvline(0, color="#222222", lw=1.0, zorder=1)
    for v in (-1, 1):
        ax.axvline(v, color="#b00020", lw=1.1, ls="--", zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels(d[labelcol], fontsize=fs)
    ax.set_ylim(-1, len(d))
    ax.set_xlabel("effect in replicate-floor units (delta / floor)")
    ax.set_title(title, fontsize=10)
    ax.grid(axis="x", alpha=0.25)


draw(axes[0], pa, "measure",
     "Qwen3 4B adapter minus base, A0, averaged over authors\n"
     "(analysis/11_scale_curves/gain.csv; dashed lines at +/- 1 floor)", fs=10)
draw(axes[1], pb, "label",
     "Qwen3 14B prompting arms vs A0, pooled over authors\n"
     "(analysis/12_arm_effects/arm_contrasts_pooled.csv; dashed lines at +/- 1 floor)", fs=5.5)
axes[1].set_xlim(-6, 12)
handles = [plt.Line2D([], [], color=CCOL[c], marker="o", ls="-", label=c) for c in CORD]
axes[0].legend(handles=handles, fontsize=8, loc="lower right", title="construct")
fig.suptitle("Floor-normalised effect atlas", fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.96))
figpath = savefig(fig, os.path.join(HERE, "atlas.png"))

allc = summ[summ.block == "contrast_family_all_constructs"]
write_readme(
    HERE, "26 Floor-normalised effect atlas",
    """
    Every brief-paired contrast already reported by scripts 11, 12, 18 and 25, divided by the
    replicate floor of its own measure on its own model family (script 10). The atlas answers one
    question for the whole study at once: which reported effects are larger than the difference the
    instrument can resolve when nothing changes but the sampling seed.

    Nothing is recomputed from cells.parquet. A contrast whose measure and family have no measured
    replicate pair carries no floor and is flagged rather than dropped.
    """,
    """
    effect_in_floors is delta divided by the floor, with the confidence interval divided by the same
    floor. above_floor compares the absolute delta against one floor; ci_clear_of_floor is the
    stricter test that the whole interval sits outside the floor band. Floors of exactly zero
    (memo_flag, preface) are treated as missing. The summary counts contrasts in four bands (under
    one floor, one to two, above two, above five) by construct and by contrast family, excluding the
    patrick v1 chunking control rows. instrument_noise_ranking.csv ranks measures within each family
    by floor over the A0 base spread, the ratio that says how much of a measure's range is noise.
    """,
    """
    A floor is a noise bound, not a smallest meaningful effect: a contrast above one floor is
    resolvable, and that is all it is. The bands are shares of contrasts, not of authors or of
    briefs, and the source tables contribute unequal numbers of rows, so read each contrast family
    against its own source table rather than pooling them into one headline. Floors are measured on
    the family named in the row, and the ranking of quiet and noisy instruments differs between
    Qwen3 and Ministral3, so no measure should be called noisy without naming the generator.
    """,
    caveats=[
        "Promoted from an exploratory pass (scratch/R12, 2026-09-11); the inputs are frozen tables and the re-expression is arithmetic.",
        "Pooled arm rows bootstrap over authors and per-author rows over briefs, so their interval widths are not comparable.",
        "Hosted-model rows are divided by the Qwen3 floor because no hosted replicate pair exists.",
        "Floors at 8B, 14B and the two Ministral rungs come from single chesterton replicate pairs.",
    ],
    tables=[("Contrast families, all constructs", allc.drop(columns=["block", "construct", "family", "size"]))],
    figures=[("Atlas", figpath)],
)

print("atlas rows", len(atlas), "with floor", int(atlas["has_floor"].sum()))
print("summary rows", len(summ))
print(allc.to_string(index=False))
