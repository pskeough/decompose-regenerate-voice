"""10_inventory_integrity -- what was actually generated, what is missing, and how much of a
cell's value is signal rather than sampling noise.

Outputs into analysis/10_inventory_integrity/:
    inventory.csv               cells per author x family x size x kind x arm vs expected
    inventory_runs.csv          run-level counts, gates, adapter_served, training record
    replicate_floors.csv        per measure x family: the twice-generated floor
    replicate_floor_pairs.csv   the individual replicate pairs behind those floors
    test_retest.csv             per run x measure: sample-0 vs sample-1 agreement over briefs
    test_retest_summary.csv     pooled across runs
    missingness.csv             non-null share per measure by arm, sample, kind
    authors_table.csv           corpus and brief counts per author
    integrity_flags.csv         machine-checkable integrity checks and their verdicts
    arm_broadcast_check.csv     do the eval-cache measures vary across arms within a run
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from lib import *  # noqa: F401,F403

T0 = time.time()
OUTD = outdir("10_inventory_integrity")

CORE = ["luar_cos_source", "luar_cos_ref", "wegmann_cos_source", "styledist_cos_source",
        "geo_index", "open_entropy", "pct_short8", "otd_js", "per", "hapax_w300",
        "coverage", "truncated"]
RETEST = CORE + ["words", "len_ratio", "arti_w", "template_rate", "delta_own", "mattr"]
EVAL_CACHE = [k for k, v in VARIABLES.items() if v[2].startswith("eval cache")]

cells, runs, authors, briefs, refs = load_all()
NUMERIC = [k for k in VARIABLES if k in cells.columns and cells[k].dtype.kind in "ifb"]

# ------------------------------------------------------------------ 1. inventory
nonrep = cells[~cells.replicate]
exp_briefs = authors.set_index("author").test_briefs_passed.to_dict()

inv = (nonrep.groupby(["author", "author_class", "family", "params_b", "size_key", "kind", "arm"], observed=True)
       .agg(run=("run", lambda s: sorted(set(s))[0]),
            n_cells=("id", "size"),
            n_briefs=("id", "nunique"),
            n_samples=("sample", "nunique"),
            truncated_rate=("truncated", "mean"),
            preface_rate=("preface", "mean"),
            length_flag_rate=("length_flag", "mean"),
            words_mean=("words", "mean"))
       .reset_index())
inv["expected_cells"] = inv.author.map(exp_briefs) * 2
inv["deficit"] = inv.expected_cells - inv.n_cells
inv["complete"] = inv.deficit == 0
run_meta = runs.set_index("run")
for col in ["adapter_served", "gate_generation_ok", "gate_training_ok", "scored", "judged_2afc",
            "has_coverage", "probe_delta", "eval_best", "train_steps", "train_examples", "backend"]:
    inv[col] = inv.run.map(run_meta[col])
inv = inv.sort_values(["family", "params_b", "author", "kind", "arm"])
write_table(inv, os.path.join(OUTD, "inventory.csv"))

inv_runs = (nonrep.groupby("run", observed=True)
            .agg(author=("author", "first"), family=("family", "first"), params_b=("params_b", "first"),
                 kind=("kind", "first"), n_cells=("id", "size"), n_briefs=("id", "nunique"),
                 n_arms=("arm", "nunique"), arms=("arm", lambda s: ",".join(sorted(set(s)))),
                 truncated_rate=("truncated", "mean"), preface_rate=("preface", "mean"),
                 words_mean=("words", "mean"))
            .reset_index())
for col in ["adapter_served", "gate_generation_ok", "gate_training_ok", "scored", "judged_2afc",
            "has_coverage", "truncated_pct", "probe_delta", "eval_best", "eval_first",
            "train_steps", "train_examples", "lora_rank", "epochs", "provenance_hash"]:
    inv_runs[col] = inv_runs.run.map(run_meta[col])
inv_runs["truncated_pct_matches"] = np.isclose(inv_runs.truncated_rate * 100, inv_runs.truncated_pct, atol=0.6)
inv_runs = inv_runs.sort_values(["family", "params_b", "author", "kind"])
write_table(inv_runs, os.path.join(OUTD, "inventory_runs.csv"))

runs_missing_cells = sorted(set(runs.run) - set(cells.run))
cells_missing_runs = sorted(set(cells.run) - set(runs.run))

# ------------------------------------------------------------------ 2. replicate floors
pair_rows = []
for m in NUMERIC:
    t = replicate_floor(cells, m, arm="A0")
    if len(t):
        pair_rows.append(t)
pairs = pd.concat(pair_rows, ignore_index=True) if pair_rows else pd.DataFrame()
pairs["construct"] = pairs.measure.map(lambda m: VARIABLES[m][1])
write_table(pairs, os.path.join(OUTD, "replicate_floor_pairs.csv"), floats=6)

a0_base = main_cells(cells, kinds=("base",))
sd = {m: float(a0_base[m].astype(float).std()) for m in NUMERIC}
floors = (pairs.groupby(["measure", "family"], observed=True)
          .agg(n_pairs=("pair", "nunique"), floor_abs_mean_diff=("abs_mean_diff", "max"),
               mean_abs_mean_diff=("abs_mean_diff", "mean"), min_n=("n", "min"))
          .reset_index())
floors["construct"] = floors.measure.map(lambda m: VARIABLES[m][1])
floors["sd_A0_base"] = floors.measure.map(sd)
floors["floor_over_sd"] = floors.floor_abs_mean_diff / floors.sd_A0_base.replace(0, np.nan)
floors = floors.sort_values(["family", "construct", "measure"])
write_table(floors, os.path.join(OUTD, "replicate_floors.csv"), floats=6)

fams_with_floor = sorted(floors.family.unique())
fams_in_data = sorted(cells.family.unique())
fams_without_floor = [f for f in fams_in_data if f not in fams_with_floor]

# ------------------------------------------------------------------ 3. test-retest
def icc1(wide):
    """One-way random-effects ICC with k=2 raters (here: the two samples of a brief)."""
    x = wide[["s0", "s1"]].to_numpy(float)
    x = x[np.isfinite(x).all(axis=1)]
    n = len(x)
    if n < 4:
        return np.nan
    grand = x.mean()
    msb = 2.0 * ((x.mean(axis=1) - grand) ** 2).sum() / (n - 1)
    msw = ((x - x.mean(axis=1, keepdims=True)) ** 2).sum() / n
    if not np.isfinite(msb + msw) or (msb + msw) == 0:
        return np.nan
    return float((msb - msw) / (msb + msw))


tr_rows = []
for run, g in nonrep[nonrep.arm == "A0"].groupby("run", observed=True):
    for m in RETEST:
        if m not in g.columns:
            continue
        w = (g.pivot_table(index="id", columns="sample", values=m, aggfunc="mean")
             .rename(columns={0: "s0", 1: "s1"}))
        if "s0" not in w.columns or "s1" not in w.columns:
            continue
        w = w[["s0", "s1"]].dropna()
        if len(w) < 4 or w.s0.nunique() < 2 or w.s1.nunique() < 2:
            tr_rows.append({"run": run, "measure": m, "n_briefs": int(len(w)), "rho": np.nan,
                            "p": np.nan, "icc1": np.nan, "note": "degenerate or too few briefs"})
            continue
        r, p = spearmanr(w.s0.values, w.s1.values)
        tr_rows.append({"run": run, "measure": m, "n_briefs": int(len(w)), "rho": float(r),
                        "p": float(p), "icc1": icc1(w), "note": ""})
tr = pd.DataFrame(tr_rows)
for col, src in [("author", "author"), ("family", "family"), ("params_b", "params_b"), ("kind", "kind")]:
    tr[col] = tr.run.map(run_meta[src])
tr["construct"] = tr.measure.map(lambda m: VARIABLES[m][1])
tr = tr.sort_values(["measure", "family", "params_b", "author", "kind"])
write_table(tr, os.path.join(OUTD, "test_retest.csv"))

trs_rows = []
for m, g in tr.groupby("measure", observed=True):
    ok = g.dropna(subset=["rho"])
    pt, lo, hi = bootstrap_ci(ok.rho.values, np.median, n=2000, seed=1)
    ipt, ilo, ihi = bootstrap_ci(ok.icc1.dropna().values, np.median, n=2000, seed=1)
    trs_rows.append({"measure": m, "construct": VARIABLES[m][1], "n_runs": int(len(ok)),
                     "n_runs_degenerate": int(g.rho.isna().sum()),
                     "median_rho": pt, "rho_lo": lo, "rho_hi": hi,
                     "min_rho": float(ok.rho.min()) if len(ok) else np.nan,
                     "max_rho": float(ok.rho.max()) if len(ok) else np.nan,
                     "median_icc1": ipt, "icc1_lo": ilo, "icc1_hi": ihi})
trs = pd.DataFrame(trs_rows).sort_values("median_rho", ascending=False)
write_table(trs, os.path.join(OUTD, "test_retest_summary.csv"))

# ------------------------------------------------------------------ 4. missingness
miss_rows = []
for m in [k for k in VARIABLES if k in cells.columns]:
    row = {"measure": m, "construct": VARIABLES[m][1], "source": VARIABLES[m][2],
           "nonnull_all": float(nonrep[m].notna().mean())}
    for arm in ARMS:
        sub = nonrep[nonrep.arm == arm]
        row[f"nonnull_{arm}"] = float(sub[m].notna().mean()) if len(sub) else np.nan
    for s in (0, 1):
        sub = nonrep[nonrep["sample"] == s]
        row[f"nonnull_sample{s}"] = float(sub[m].notna().mean())
    for k in ("base", "adapter"):
        sub = nonrep[nonrep.kind == k]
        row[f"nonnull_{k}"] = float(sub[m].notna().mean())
    for f in fams_in_data:
        sub = nonrep[nonrep.family == f]
        row[f"nonnull_{f}"] = float(sub[m].notna().mean())
    row["n_runs_with_any"] = int(nonrep[nonrep[m].notna()].run.nunique())
    row["n_runs_total"] = int(nonrep.run.nunique())
    miss_rows.append(row)
miss = pd.DataFrame(miss_rows).sort_values(["nonnull_all", "measure"])
write_table(miss, os.path.join(OUTD, "missingness.csv"))

# ------------------------------------------------------------------ 5. arm broadcast check
multi_arm = nonrep[nonrep.run.isin(nonrep.groupby("run").arm.nunique().pipe(lambda s: s[s > 1]).index)]
BC_COLS = [c for c in cells.columns if cells[c].dtype.kind in "if"
           and c not in ("sample", "params_b", "replicate")]
ident = np.zeros(len(BC_COLS)); both = np.zeros(len(BC_COLS)); tot = 0
for run, g in multi_arm.groupby("run", observed=True):
    a0 = g[g.arm == "A0"].set_index(["id", "sample"])[BC_COLS].astype(float)
    for arm in [a for a in ARMS if a != "A0"]:
        b = g[g.arm == arm].set_index(["id", "sample"])[BC_COLS].astype(float)
        idx = a0.index.intersection(b.index)
        if not len(idx):
            continue
        x = a0.loc[idx].to_numpy(); y = b.loc[idx].to_numpy()
        keep = np.isfinite(x) & np.isfinite(y)
        eq = keep & np.isclose(np.nan_to_num(x), np.nan_to_num(y), rtol=0, atol=1e-12)
        ident += eq.sum(axis=0); both += keep.sum(axis=0); tot += len(idx)
# columns keyed by the brief or by the author are invariant across arms by design
INVARIANT_BY_DESIGN = {"source_words", "brief_words", "n_events", "dialogue_share", "target_words",
                       "train_briefs_passed", "test_briefs_passed", "words_total", "n_works_train"}
bc = pd.DataFrame({"measure": BC_COLS,
                   "construct": [VARIABLES[m][1] if m in VARIABLES else "" for m in BC_COLS],
                   "source": [VARIABLES[m][2] if m in VARIABLES else "" for m in BC_COLS],
                   "n_pairs_compared": tot, "n_pairs_both_present": both.astype(int),
                   "share_identical_to_A0": np.where(both > 0, ident / np.maximum(both, 1), np.nan),
                   "in_dictionary": [m in VARIABLES for m in BC_COLS],
                   "eval_cache": [m in EVAL_CACHE for m in BC_COLS],
                   "invariant_by_design": [m in INVARIANT_BY_DESIGN for m in BC_COLS]})
bc = bc[bc.n_pairs_both_present > 0].sort_values("share_identical_to_A0", ascending=False)
write_table(bc, os.path.join(OUTD, "arm_broadcast_check.csv"))
BROADCAST = bc[(bc.share_identical_to_A0 > 0.999) & (~bc.invariant_by_design)].measure.tolist()
BROADCAST_DICT = [m for m in BROADCAST if m in VARIABLES]
BROADCAST_RUBRIC = [m for m in BROADCAST if m.startswith("rubric") or m == "n_rubric_records"]
BROADCAST_Z = [m for m in BROADCAST if m.startswith("z_")]

# ------------------------------------------------------------------ 6. authors
at = authors.copy()
obs = nonrep.groupby("author", observed=True).agg(n_cells=("id", "size"), n_runs=("run", "nunique"),
                                                  n_briefs_used=("id", "nunique"),
                                                  families=("family", lambda s: ",".join(sorted(set(s)))),
                                                  sizes=("params_b", lambda s: ",".join(f"{v:g}" for v in sorted(set(s)))))
at = at.merge(obs, on="author", how="left")
at["briefs_used_matches_passed"] = at.n_briefs_used == at.test_briefs_passed
write_table(at, os.path.join(OUTD, "authors_table.csv"))

# ------------------------------------------------------------------ 7. integrity flags
flags = []


def flag(name, ok, detail):
    flags.append({"check": name, "pass": bool(ok), "detail": detail})


# the builder records what it wrote in data/master/schema.json; a mismatch means a table was edited after the build
_schema = json.load(open(os.path.join(MASTER, "schema.json"), encoding="utf-8")) if os.path.exists(os.path.join(MASTER, "schema.json")) else {"tables": {}}
_sc = _schema["tables"].get("cells.parquet", {})
flag("cells row count matches the builder's schema.json", len(cells) == _sc.get("rows", -1),
     f"{len(cells)} rows x {cells.shape[1]} cols on disk; schema.json records {_sc.get('rows')} x {_sc.get('columns')}")
flag("A0 non-replicate cell count matches the builder's schema.json",
     len(main_cells(cells)) == _schema.get("a0_nonreplicate_cells", -1),
     f"{len(main_cells(cells))} A0 non-replicate cells on disk; schema.json records {_schema.get('a0_nonreplicate_cells')}")
flag("every run in runs.csv has cells", not runs_missing_cells,
     "missing from cells.parquet: " + (", ".join(runs_missing_cells) or "none"))
flag("every cell run is described in runs.csv", not cells_missing_runs,
     "missing from runs.csv: " + (", ".join(cells_missing_runs) or "none"))
flag("no duplicate (run, arm, id, sample) keys", cells.duplicated(["run", "arm", "id", "sample"]).sum() == 0,
     f"{int(cells.duplicated(['run', 'arm', 'id', 'sample']).sum())} duplicates")
flag("every configuration reaches its expected cell count", bool(inv.complete.all()),
     f"{int((~inv.complete).sum())} of {len(inv)} configuration x arm rows short of briefs x 2")
flag("replicate floors available for every family", not fams_without_floor,
     "families without a replicate pair in cells.parquet: " + (", ".join(fams_without_floor) or "none"))
flag("outcome measures vary across arms", len(BROADCAST) == 0,
     f"{len(BROADCAST)} outcome columns identical to their A0 value on every other arm "
     f"({len(BROADCAST_DICT)} of them dictionary variables, {len(BROADCAST_RUBRIC)} rubric, "
     f"{len(BROADCAST_Z)} constructional z_*): " + ", ".join(BROADCAST_DICT[:8]))
flag("runs.csv truncated_pct agrees with the cells", bool(inv_runs.truncated_pct_matches.all()),
     f"{int((~inv_runs.truncated_pct_matches).sum())} runs disagree by more than 0.6 points")
flag("brief counts per author match authors.csv", bool(at.briefs_used_matches_passed.all()),
     ", ".join(at.loc[~at.briefs_used_matches_passed, "author"].tolist()) or "all match")
over_gate = inv_runs[(inv_runs.truncated_rate > 0.20) & inv_runs.gate_generation_ok.isna()]
flag("every run over the 20% truncation gate has a gate verdict", len(over_gate) == 0,
     f"{len(over_gate)} runs exceed 20% truncation with no verdict recorded: "
     + ", ".join(f"{r.run} ({r.truncated_rate * 100:.0f}%)" for r in
                 over_gate.sort_values("truncated_rate", ascending=False).head(6).itertuples()))
flag("runs.csv carries a provenance hash for every run", bool(runs.provenance_hash.notna().all()),
     f"{int(runs.provenance_hash.notna().sum())} of {len(runs)} runs have a provenance_hash; "
     "file-level SHA-256 is in data/MANIFEST.json instead")
flag("every run records its sampling temperature", bool(runs.temperature.notna().all()),
     f"{int(runs.temperature.isna().sum())} runs have no temperature recorded; the rest are "
     + ", ".join(f"{v:g}" for v in sorted(runs.temperature.dropna().unique())))
fl = pd.DataFrame(flags)
write_table(fl, os.path.join(OUTD, "integrity_flags.csv"))

# ------------------------------------------------------------------ figures
core_fl = floors[floors.measure.isin(CORE)].copy()
fig, ax = plt.subplots(figsize=(9, 5))
order = core_fl.groupby("measure").floor_over_sd.max().sort_values().index.tolist()
for i, fam in enumerate(sorted(core_fl.family.unique())):
    sub = core_fl[core_fl.family == fam].set_index("measure").reindex(order)
    ax.barh(np.arange(len(order)) + (i - 0.5) * 0.38, sub.floor_over_sd.values, height=0.36, label=fam)
ax.set_yticks(np.arange(len(order))); ax.set_yticklabels(order)
ax.set_xlabel("replicate floor / sd of the measure across A0 base cells")
ax.set_title("Replicate floor relative to measure spread (core measures)")
ax.legend(); ax.grid(axis="x", alpha=0.3)
f1 = savefig(fig, os.path.join(OUTD, "fig_replicate_floors.png"))

fig, ax = plt.subplots(figsize=(9, 5))
sub = trs[trs.measure.isin(RETEST)].dropna(subset=["median_rho"]).sort_values("median_rho")
y = np.arange(len(sub))
ax.errorbar(sub.median_rho, y, xerr=[sub.median_rho - sub.rho_lo, sub.rho_hi - sub.median_rho],
            fmt="o", capsize=3, label="median Spearman across runs (95% CI over runs)")
ax.scatter(sub.median_icc1, y, marker="x", color="C1", label="median ICC(1)")
ax.set_yticks(y); ax.set_yticklabels(sub.measure)
ax.axvline(0, color="k", lw=0.8)
ax.set_xlabel("sample 0 vs sample 1 agreement over briefs, within a run")
ax.set_title("Test-retest: how much of a cell's value is the brief")
ax.legend(loc="lower right", fontsize=8); ax.grid(axis="x", alpha=0.3)
f2 = savefig(fig, os.path.join(OUTD, "fig_test_retest.png"))

fig, ax = plt.subplots(figsize=(9, 5))
order = (inv[["family", "params_b", "size_key"]].drop_duplicates()
         .sort_values(["family", "params_b"]).size_key.tolist())
pv = inv[inv.arm == "A0"].pivot_table(index="author", columns="size_key", values="truncated_rate")[order]
im = ax.imshow(pv.to_numpy(float), aspect="auto", cmap="Reds", vmin=0, vmax=float(np.nanmax(pv.to_numpy(float))))
ax.set_xticks(range(pv.shape[1])); ax.set_xticklabels(pv.columns, rotation=45, ha="right")
ax.set_yticks(range(pv.shape[0])); ax.set_yticklabels(pv.index)
ax.set_title("Hit the token cap (truncated), arm A0, base and adapter pooled")
fig.colorbar(im, ax=ax, label="share of cells truncated")
f3 = savefig(fig, os.path.join(OUTD, "fig_truncation.png"))

# ------------------------------------------------------------------ README
n_short = int((~inv.complete).sum())
short_rows = inv[~inv.complete].sort_values("deficit", ascending=False)
worst_trunc = inv_runs.sort_values("truncated_rate", ascending=False).head(6)[
    ["run", "family", "params_b", "kind", "truncated_rate", "gate_generation_ok"]]
floor_core = floors[floors.measure.isin(CORE)][
    ["measure", "family", "n_pairs", "floor_abs_mean_diff", "sd_A0_base", "floor_over_sd"]]
gates_fail = inv_runs[inv_runs.gate_generation_ok == False][  # noqa: E712
    ["run", "family", "params_b", "kind", "truncated_rate", "adapter_served"]]
bc_top = (bc[~bc.invariant_by_design & (bc.share_identical_to_A0 > 0.9)]
          .head(30)[["measure", "source", "n_pairs_both_present", "share_identical_to_A0", "eval_cache"]])

# ---- README-only helpers. Every number quoted in the written piece below is read back out of
# the tables this script just wrote; none of it is typed by hand.
_floor_fams = floors.pivot_table(index="measure", columns="family", values="n_pairs")
floor_one_family = sorted(_floor_fams.index[_floor_fams.isna().any(axis=1)])
floor_single_pair = sorted(floors.loc[floors.n_pairs == 1, "measure"].unique())
max_pairs_per_family = int(floors.n_pairs.max())
core_trs = trs[trs.measure.isin(CORE)].dropna(subset=["median_rho"])
cov_retest_runs = int(trs.loc[trs.measure == "coverage", "n_runs"].iloc[0]) if (trs.measure == "coverage").any() else 0
no_ministral = []
if "nonnull_Ministral3" in miss.columns and "nonnull_Qwen3" in miss.columns:
    no_ministral = sorted(miss.loc[(miss.nonnull_Ministral3 == 0) & (miss.nonnull_Qwen3 > 0), "measure"])
_cov_s0 = (nonrep[(nonrep["sample"] == 0) & (nonrep.arm == "A0") & (nonrep.family == "Qwen3")]
           .groupby("run", observed=True).coverage.apply(lambda s: float(s.notna().mean())))
cov_gap_runs = _cov_s0[_cov_s0 < 0.5].sort_values()
_dm8 = inv_runs[inv_runs.run == "doctorow_basem8b"]
_cm8 = inv_runs[inv_runs.run == "chesterton_paire6_m8b"]
over_gate_all = inv_runs[inv_runs.truncated_rate > 0.20]
n_prov = int(runs.provenance_hash.notna().sum())
n_authors_indep = int(authors.author.nunique() - int(authors.author.isin(["patrick"]).sum()))

runtime = time.time() - T0
write_readme(
    OUTD,
    "10 Inventory and integrity",
    f"""
    Counts every generated cell against what the design should have produced, records the gate
    verdicts and how each adapter was served, measures the noise floor of every numeric measure
    from the twice-generated runs, and measures how much of a cell's value is the brief rather
    than the sampling draw. It is the script the other analyses lean on for "is this contrast
    bigger than the machine's own jitter".

    It also runs a set of machine-checkable integrity checks over the master tables and writes
    their verdicts to `integrity_flags.csv`; {int(fl['pass'].sum())} of {len(fl)} pass.
    """,
    f"""
    Data: `data/master/cells.parquet` ({len(cells)} rows x {cells.shape[1]} columns),
    `runs.csv` ({len(runs)} runs), `authors.csv` ({len(authors)} rows). Non-replicate cells
    only ({len(nonrep)} of {len(cells)}); the {int(cells.replicate.sum())} replicate cells are
    used only to compute the floors. One of the {len(authors)} author rows, `patrick`, is the
    v1 chunking control over the same corpus as `patrick_v2`, so these tables cover
    {n_authors_indep} independent author corpora, not {len(authors)}.

    Unit. The inventory counts cells. The replicate floor is a difference of run means, so its
    unit is the run. Test-retest is computed within a run over briefs, so its unit is the brief.
    Nothing here is aggregated to the author, and nothing here is a claim about a model, a
    family or a size.

    Expected counts. Each (author, family, size, kind, arm) row should hold
    `test_briefs_passed` x 2 samples. `deficit` is that minus the observed count.

    Replicate floor. `lib.replicate_floor` takes the {int(pairs.pair.nunique())} twice-generated
    configurations and reports |mean(run) - mean(replicate)| per measure; the floor quoted is
    the largest of those differences within a family, over at most {max_pairs_per_family} pairs.
    `floor_over_sd` divides it by the standard deviation of the measure across all A0 base
    cells, which puts the floors of measures on different scales on one axis. Floors are
    computed on arm A0, so they bound arm-A0 contrasts; no floor here was measured on A1 to A5.
    {"Every measure with a floor has one in both families." if not floor_one_family else "These measures have a floor in one family only: " + ", ".join(floor_one_family) + "."}

    Test-retest. Within each run and arm A0, each brief has two generated passages (sample 0 and
    sample 1). The table reports the Spearman correlation between the two samples across briefs
    and a one-way ICC with k = 2. A measure with a low value is dominated by the sampling draw,
    not by the brief, so single-cell readings of it mean little. Pooled rows are the median
    across runs with a bootstrap interval over runs (2000 draws).

    Correction. This script runs no hypothesis family, so no BH-FDR is applied; the p-values in
    `test_retest.csv` are descriptive and are not the basis of any claim here.

    Runtime {runtime:.0f} s.
    """,
    f"""
    Unit of replication. Nothing in this script is an effect. The floors are the yardstick the
    effects in scripts 11 to 22 are measured against, and they rest on
    {int(pairs.pair.nunique())} replicate pairs, all at the small end of the size range
    ({", ".join(sorted(pairs['pair'].unique()))}). No family has more than
    {max_pairs_per_family} pairs behind any floor, so a floor is itself a noisy estimate; treat
    it as an order of magnitude, not a threshold with decimals. Because a floor is the largest
    observed difference over a handful of pairs, it understates the true jitter more often than
    it overstates it.

    Test-retest. Over the core measures the median within-run agreement between the two samples
    of a brief runs from {core_trs.median_rho.min():.2f} to {core_trs.median_rho.max():.2f}
    (Spearman over briefs, median over runs). That is a property of a single generated passage:
    roughly half of what one cell reports is the brief and the rest is the sampling draw. It is
    not a reliability figure for a run mean, which averages over briefs and samples and is
    correspondingly steadier.

    Interval width. The test-retest intervals are over runs, not over briefs, so they say how
    much run-to-run variation there is in the retest agreement, not how precisely any one run's
    agreement is known.

    Floors. {"No replicate pair exists for " + ", ".join(fams_without_floor) + ", so every contrast on those families elsewhere in the programme has to borrow the other family's floor, which is an assumption and not a measurement." if fams_without_floor else "Both families have a measured floor."}{"" if not floor_one_family else " Coverage is not uniform: " + ", ".join(floor_one_family) + " have a floor in one family only" + ("" if not floor_single_pair else ", and " + ", ".join(floor_single_pair) + " rest on a single replicate pair") + ", so a contrast on those measures is read against the thinnest yardstick in the set."}

    Judged measures. `coverage` is an LLM judge's reading of how much of the brief is present,
    not a mechanical count, so it carries a judge's failure modes as well as the generator's.
    It is scored on sample 0, so its test-retest row rests on the {cov_retest_runs} runs that
    happen to carry sample-1 coverage and is not the measure's reliability.{"" if not no_ministral else " The Ministral3 runs carry no judge data at all (" + ", ".join(no_ministral) + " are non-null on Qwen3 rows only), so no judged comparison in this programme spans the two families."}
    Judge-derived values are relative instruments throughout this programme and are never read
    as absolute quality.

    What would overturn this. Generating any configuration a third time, especially at 8B or
    14B, would put a measured floor where the present ones are extrapolated from 3B and 4B runs,
    and could move them in either direction. A floor that turned out to be twice the value here
    would sink several of the smaller contrasts elsewhere in the programme below noise.

    What this does not show. Nothing about whether any adaptation worked, and nothing about any
    model, family or size: the unit here is the cell, the run and the brief. A high test-retest
    correlation means a measure reads the brief consistently, not that it reads voice; a low one
    means single passages are noisy, not that the measure is wrong.
    """,
    caveats=[
        f"{n_short} of {len(inv)} configuration x arm rows are short of the expected briefs x 2 count"
        + (f" (largest deficit {int(short_rows.deficit.max())} cells in {short_rows.iloc[0]['run']} arm {short_rows.iloc[0]['arm']})" if n_short else ""),
        (f"{len(runs_missing_cells)} runs in runs.csv have no rows in cells.parquet ({', '.join(runs_missing_cells)}) because they were never scored."
         if runs_missing_cells else
         "Every run in runs.csv has cells. The two Ministral3 3B replicates were scored on 2026-09-10, after the rest of the grid and outside the usual `score_runs.py` path (which skips `_r2` ids), so the Ministral3 floors are the newest numbers in this workspace and rest on 3B pairs only; nothing here measures Ministral3 jitter at 8B or 14B."),
        (f"{len(BROADCAST)} outcome columns take the identical value on every arm of a run "
         f"(brief-level and author-level covariates excluded, since those are invariant by design): "
         f"{', '.join(BROADCAST_DICT[:12])}, {len(BROADCAST_Z)} constructional z_* columns and "
         f"{len(BROADCAST_RUBRIC)} rubric columns. Any arm-versus-arm contrast on those columns "
         f"compares A0 with itself and will return exactly zero."
         if BROADCAST else
         "No outcome column is identical across every arm of a run, so the arm-key join fault found earlier today is repaired in these tables. The eval-cache measures (per, otd_js, psd, cpd, lexdiv, event order, constructional) and the rubric subscores now carry values on arm A0 and NaN on A1 to A5, which is what they were computed on; no A1 to A5 effect can be claimed for any of them anywhere in the programme."),
        "A high `share_identical_to_A0` in `arm_broadcast_check.csv` can also mean a column is near-constant (a flag that is almost always zero) rather than broadcast across arms; read the column's spread before reading the share as a join fault.",
        f"`coverage` is an LLM-judged adherence measure scored on sample 0 ({float(nonrep[nonrep['sample'] == 1].coverage.notna().mean()) * 100:.1f}% non-null on sample 1, all of it in {nonrep[(nonrep['sample'] == 1) & nonrep.coverage.notna()].run.nunique()} runs), so its test-retest row is computed on those few runs and is not the measure's reliability.",
        f"Rubric measures are present on {float(nonrep.rubric_C.notna().mean()) * 100:.1f}% of cells and 2AFC on {float(nonrep.fool_vs_source.notna().mean()) * 100:.1f}%; every judge claim rests on that subset, not on the full grid. Judge values are relative instruments with known failures (the rubric ranks a 14B base above the private author's own prose, and the two judges are not one instrument), so none of them is a quality figure.",
        (f"{len(cov_gap_runs)} Qwen3 runs carry coverage on fewer than half their sample-0 A0 briefs "
         f"({', '.join(f'{r} at {v * 100:.0f}%' for r, v in cov_gap_runs.items())}); these are the residue of the "
         f"2026-09-09 credit outage, whose HTTP 402 responses were stored as error rows. The rerun that fills them "
         f"was still running when this was written, so the coverage and 2AFC shares in `missingness.csv` are a "
         f"lower bound on the final grid, not the final grid." if len(cov_gap_runs) else
         "The coverage and 2AFC rows lost to the 2026-09-09 credit outage have been refilled; `missingness.csv` reflects the repaired grid."),
        f"{int((runs.gate_generation_ok == False).sum())} runs fail the generation gate and {int(runs.gate_generation_ok.isna().sum())} have no gate verdict recorded at all; absence of a verdict is not a pass. "
        f"{len(over_gate)} of the unverdicted runs are over the stated 20% truncation threshold, the worst at "
        f"{float(over_gate.truncated_rate.max()) * 100:.0f}%, so any sensitivity analysis that drops gate-failed runs leaves them in.",
        (f"{len(over_gate_all)} runs exceed the 20% truncation gate and stay in every table here flagged rather than excluded"
         + (f", including the one Ministral3 base run over the gate, `doctorow_basem8b` at {float(_dm8.truncated_rate.iloc[0]) * 100:.1f}%" if len(_dm8) else "")
         + ". A truncated passage is short for a reason unrelated to voice, so any measure that moves with length is confounded in those cells."),
        (f"`chesterton_paire6_m8b` has a positive probe delta ({float(_cm8.probe_delta.iloc[0]):+.4f} in `inventory_runs.csv`), meaning the training probe found the adapter no closer to the author than the base; it is in the inventory as a run, not as evidence that an adapter was applied."
         if len(_cm8) and pd.notna(_cm8.probe_delta.iloc[0]) else
         "`probe_delta` is missing for some adapter runs in `inventory_runs.csv`; a missing probe is not a passed probe."),
        "The reference pool behind the `*_cos_ref`, attribution and Delta columns counted here is fourteen period authors for every study author, so contemporary and private authors are positioned against strangers from another century. `scripts/23_register_matched_pool.py` holds the register-matched repair; the counts in this script are unaffected but any downstream reading of those measures is.",
        "The per-run `emb_*.npy` files are not row-aligned with `scores.jsonl` in most runs (an anchor block sits between the generations and the reference rows). Nothing in this script reads them; `scripts/23_register_matched_pool.py` holds the verified repair for anything that does.",
        "`para_cv_words` is in the variable dictionary but not in cells.parquet, so it is absent from every table here.",
        f"`provenance_hash` is recorded for {n_prov} of {len(runs)} runs in runs.csv (the local pre-provenance runs carry none), so run-level provenance cannot be checked for the rest from the master tables; data/MANIFEST.json still carries a SHA-256 per copied file, which is a different guarantee (the copy is intact, not that the run is the one it claims to be).",
        f"{int(runs.temperature.isna().sum())} runs record no sampling temperature; the remaining {int(runs.temperature.notna().sum())} all ran at {', '.join(f'{v:g}' for v in sorted(runs.temperature.dropna().unique()))}, so the missing rows are probably the same but that is an assumption.",
        f"The study's limit is the {n_authors_indep} independent author corpora, not the number of tests run. No count in this script becomes evidence about a model, a family or a size without being aggregated to the author first.",
    ],
    tables=[
        ("Integrity checks", fl),
        ("Replicate floors, core measures", floor_core),
        ("Test-retest across runs (median over runs, 95% CI over runs)", trs),
        ("Runs that fail the generation gate", gates_fail),
        ("Highest truncation rates", worst_trunc),
        ("Configuration x arm rows short of the expected count", short_rows[["run", "author", "family", "params_b", "kind", "arm", "n_cells", "expected_cells", "deficit"]]),
        ("Outcome columns identical across arms within a run (covariates excluded)", bc_top),
    ],
    figures=[("Replicate floors relative to measure spread", f1),
             ("Test-retest agreement between the two samples", f2),
             ("Truncation by author and configuration", f3)],
)

print(f"[10] wrote {len(os.listdir(OUTD))} files to {OUTD} in {runtime:.1f}s")
print(fl.to_string(index=False))
