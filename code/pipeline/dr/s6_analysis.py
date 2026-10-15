"""S6: the pre-registered analysis (METHODS 9) -> runs/<run>/RESULTS.md

Unit is the passage: samples are averaged within passage x arm x model before
modelling. For the primary and each secondary outcome:

    per-arm mean and 95% CI (passage-level cluster bootstrap, 5,000 draws)
    contrasts vs A0 and vs A1: paired mean difference, paired Cohen's d,
        paired t p-value, and a bootstrap CI on the difference
    Holm correction across the contrasts of the PRIMARY outcome
    MixedLM outcome ~ arm + (1|passage) by REML (statsmodels), or
        outcome ~ arm * model + (1|passage) when several runs are pooled

    python dr/s6_analysis.py --runs base4b
    python dr/s6_analysis.py --runs base4b,pair4b,mix4b,raw4b --out runs/adapter_phase
"""
from __future__ import annotations

import argparse
import collections
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import RUNS, log, read_json, read_jsonl, write_json, write_text  # noqa: E402

import numpy as np  # noqa: E402

OUTCOMES = [config.PRIMARY, "geo_index", "geo_overshoot", "luar_attrib", "delta_rank", "delta_own",
            "luar_cos_ref", "luar_cos_ai", "wegmann_cos_source", "styledist_cos_source",
            "shown_dist", "memo_flag", "memo_lcs", "len_ratio"]
JUDGE_KEYS = ("vs_source", "vs_A0", "coverage")


def load(run):
    rd = os.path.join(RUNS, run)
    sc = [r for r in read_jsonl(os.path.join(rd, "scores.jsonl")) if r["group"] == "gen"]
    for r in sc:
        r["model"] = run
    jp = os.path.join(rd, "judge.jsonl")
    if os.path.exists(jp):
        jj = collections.defaultdict(list)
        for r in read_jsonl(jp):
            if "picked_gen" in r:
                jj[(r["id"], r["arm"], r["sample"], r["comparison"])].append(r["picked_gen"])
        for r in sc:
            for comp in ("vs_source", "vs_A0"):
                v = jj.get((r["id"], r["arm"], r["sample"], comp))
                r[f"judge_{comp}"] = st.mean(v) if v else None
    cp = os.path.join(rd, "coverage.jsonl")
    if os.path.exists(cp):
        cc = {(r["id"], r["arm"], r["sample"]): r["coverage"] for r in read_jsonl(cp) if r.get("coverage") is not None}
        for r in sc:
            r["judge_coverage"] = cc.get((r["id"], r["arm"], r["sample"]))
    return sc


def passage_means(rows, key):
    """{(model, arm): {id: mean over samples}}"""
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        v = r.get(key)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        acc[(r["model"], r["arm"])][r["id"]].append(float(v))
    return {k: {pid: st.mean(v) for pid, v in d.items()} for k, d in acc.items()}


def boot_ci(x, n=5000, seed=0):
    x = np.asarray(x, dtype=float)
    if len(x) < 3:
        return (float("nan"), float("nan"))
    R = np.random.default_rng(seed)
    idx = R.integers(0, len(x), size=(n, len(x)))
    m = x[idx].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def paired(a, b):
    """a, b: dicts id->value. Returns stats on a-b over shared ids."""
    ids = sorted(set(a) & set(b))
    if len(ids) < 3:
        return None
    d = np.array([a[i] - b[i] for i in ids])
    from scipy import stats
    t, p = stats.ttest_rel([a[i] for i in ids], [b[i] for i in ids])
    sd = d.std(ddof=1)
    return {"n": len(ids), "diff": float(d.mean()), "d": float(d.mean() / sd) if sd > 0 else float("nan"),
            "t": float(t), "p": float(p), "ci": boot_ci(d)}


def holm(pvals):
    """Holm step-down; returns adjusted p in input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        v = min(1.0, (m - rank) * pvals[i])
        running = max(running, v)
        adj[i] = running
    return adj


def mixed(rows, key, multi_model):
    try:
        import pandas as pd
        import statsmodels.formula.api as smf
    except Exception as e:
        return f"statsmodels unavailable: {e!r}"
    pm = passage_means(rows, key)
    rec = [{"model": m, "arm": arm, "id": pid, "y": v} for (m, arm), d in pm.items() for pid, v in d.items()]
    if not rec:
        return "no data"
    df = pd.DataFrame(rec)
    models = sorted(df["model"].unique())
    # arm x model is only a crossed design when every model has every arm;
    # the frontier comparator (F0/F5) does not cross the base arms, so those
    # are fitted per model rather than in one rank-deficient interaction model
    cells = set(zip(df["model"], df["arm"]))
    arms_all = sorted(df["arm"].unique())
    crossed = all((m, a_) in cells for m in models for a_ in arms_all)
    groups = [df] if (crossed or len(models) == 1) else [df[df["model"] == m] for m in models]
    out = []
    for g in groups:
        g = g.copy()
        arms = sorted(g["arm"].unique())
        base = "A0" if "A0" in arms else arms[0]
        g["arm"] = pd.Categorical(g["arm"], categories=[base] + [x for x in arms if x != base])
        formula = "y ~ arm * C(model)" if (multi_model and g["model"].nunique() > 1) else "y ~ arm"
        try:
            md = smf.mixedlm(formula, g, groups=g["id"]).fit(reml=True)
            lines = [f"MixedLM {formula}, model(s)={sorted(g['model'].unique())}, groups=passage, n={len(g)}"]
            for name, coef, se, p in zip(md.params.index, md.params.values, md.bse.values, md.pvalues.values):
                if name == "Group Var":
                    continue
                lines.append(f"  {name:32s} {coef:+.4f} (se {se:.4f}, p={p:.3g})")
            out.append("\n".join(lines))
        except Exception as e:
            out.append(f"MixedLM failed for {sorted(g['model'].unique())}: {e!r}")
    return "\n\n".join(out)


def fmt(v, nd=3):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    return f"{v:.{nd}f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", required=True, help="comma-separated run ids; first is the base")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    runs = [r.strip() for r in a.runs.split(",") if r.strip()]
    rows = []
    for r in runs:
        rows += load(r)
    outdir = a.out or os.path.join(RUNS, runs[0])
    os.makedirs(outdir, exist_ok=True)
    multi = len(runs) > 1
    models = runs
    arms = sorted({r["arm"] for r in rows})
    log(f"{len(rows)} generation rows, models {models}, arms {arms}")

    md = [f"# Results: {', '.join(runs)}", "",
          f"Generated by `dr/s6_analysis.py`. Unit is the passage (samples averaged). "
          f"Primary outcome: `{config.PRIMARY}`. CIs are passage-level cluster bootstraps (5,000).", ""]
    outcomes = OUTCOMES + [f"judge_{k}" for k in JUDGE_KEYS]
    tables = {}
    for key in outcomes:
        pm = passage_means(rows, key)
        if not pm:
            continue
        md.append(f"## {key}" + ("  (PRIMARY)" if key == config.PRIMARY else ""))
        md.append("")
        md.append("| model | arm | n | mean | 95% CI | vs A0 diff | d | p | vs A1 diff | d | p |")
        md.append("|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|")
        prim_p, prim_rows = [], []
        for m in models:
            for arm in arms:
                d = pm.get((m, arm))
                if not d:
                    continue
                vals = list(d.values())
                lo, hi = boot_ci(vals)
                c0 = paired(d, pm.get((m, "A0"), {})) if arm != "A0" else None
                c1 = paired(d, pm.get((m, "A1"), {})) if arm != "A1" and (m, "A1") in pm else None
                line = (f"| {m} | {arm} | {len(vals)} | {fmt(st.mean(vals))} | [{fmt(lo)}, {fmt(hi)}] | "
                        f"{fmt(c0['diff']) if c0 else '-'} | {fmt(c0['d'], 2) if c0 else '-'} | {fmt(c0['p'], 3) if c0 else '-'} | "
                        f"{fmt(c1['diff']) if c1 else '-'} | {fmt(c1['d'], 2) if c1 else '-'} | {fmt(c1['p'], 3) if c1 else '-'} |")
                md.append(line)
                if key == config.PRIMARY and c0 and arm not in ("A0",):
                    prim_p.append(c0["p"])
                    prim_rows.append((m, arm))
                tables.setdefault(key, {})[f"{m}|{arm}"] = {"n": len(vals), "mean": st.mean(vals), "ci": [lo, hi],
                                                          "vs_A0": c0, "vs_A1": c1}
        if key == config.PRIMARY and prim_p:
            adj = holm(prim_p)
            md.append("")
            md.append("Holm-adjusted p for the vs-A0 contrasts of the primary: " +
                      ", ".join(f"{m}/{arm} {fmt(p, 3)}" for (m, arm), p in zip(prim_rows, adj)))
            for (m, arm), p in zip(prim_rows, adj):
                tables[key][f"{m}|{arm}"]["vs_A0_holm_p"] = p
        md.append("")
        md.append("```")
        md.append(mixed(rows, key, multi))
        md.append("```")
        md.append("")

    # flags per arm
    md.append("## Instruction-following and flags per arm")
    md.append("")
    md.append("| model | arm | n | preface | trailer | think | length | truncated | memo_flag |")
    md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for m in models:
        for arm in arms:
            rs = [r for r in rows if r["model"] == m and r["arm"] == arm]
            if not rs:
                continue
            fl = collections.Counter(f for r in rs for f in (r.get("flags") or []))
            memo_rate = st.mean([r.get("memo_flag") or 0 for r in rs])
            md.append(f"| {m} | {arm} | {len(rs)} | {fl['preface']} | {fl['trailer']} | {fl['think']} | "
                      f"{fl['length']} | {fl['truncated']} | {memo_rate:.2f} |")
    md.append("")

    # geometry bookkeeping
    gp = os.path.join(RUNS, runs[0], "geometry.json")
    if os.path.exists(gp):
        g = read_json(gp)
        md.append("## Geometry index: SEALED features retained")
        md.append("")
        md.append("| feature | mu_author (REF) | mu_ai (A0) |")
        md.append("|---|---:|---:|")
        for f, v in g["kept"].items():
            md.append(f"| {f} | {v['mu_author']:.4f} | {v['mu_ai']:.4f} |")
        if g["dropped"]:
            md.append("")
            md.append("Dropped (no separation): " + ", ".join(f"{k} ({v})" for k, v in g["dropped"].items()))
        md.append("")

    p = os.path.join(outdir, "RESULTS.md")
    write_text(p, "\n".join(md) + "\n")
    write_json(os.path.join(outdir, "results_tables.json"), tables)
    log(f"-> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
