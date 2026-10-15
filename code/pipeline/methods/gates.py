"""Phase 3 gates over every measure's per-cell cache (SYNTHESIS.md section 4).

For each results/cache/<measure>_<arm>.json and each numeric key in it:
  1. replicate floor: max |mean difference| over the three twice-generated
     base configurations;
  2. adapter effect: mean |adapter - base| over the (author, size) pairs that
     have both, and the effect / floor ratio;
  3. manipulation check (unpaired measures only): Cohen's d between the
     author's sources and that author's 4B base run; count of authors at
     d >= 0.2 (GEOMETRY.min_sep_sd) and d >= 0.5;
  4. length: Spearman rho with the cell's word count (from scores.jsonl);
  5. redundancy: Spearman rho with luar_cos_source, open_top_share,
     open_entropy, sent_len_cv, sent_echo over all joined cells;
  6. blind item 1: the measure recomputed on the four candidates the reader
     ruled on (D best; B lost the story; A and C regressive), Spearman with
     the reader's style order D > B > A > C and the coherence order
     D > A = C > B.
Writes results/GATES.md. Nothing under decompose_regenerate/runs is touched.
"""
from __future__ import annotations

import glob
import importlib
import json
import os
import statistics as st
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, RESULTS, REPLICATES, blind_item1, discover_runs, norm, scores  # noqa: E402

SCORE_KEYS = ["words", "luar_cos_source", "open_top_share", "open_entropy", "sent_len_cv", "sent_echo", "geo_index"]
META = {"run", "author", "size", "kind", "id", "sample", "n", "n_sent", "per_n_sent", "n_tok", "n_events", "para_n"}
# cache name -> (module, measure fn, paired fn or None)
REGISTRY = {
    "per": ("per", "per", None),
    "psd_raw": ("psd", "profile", None), "psd": ("psd", "profile", "paired"),
    "cpd_raw": ("cpd", "profile", None), "cpd": ("cpd", "profile", "paired"),
    "lexdiv": ("lexdiv", "measure", None),
    "otd_raw": ("otd", "profile", None), "otd": ("otd", "profile", "paired"),
}
STYLE_ORDER = {"D": 1, "B": 2, "A": 3, "C": 4}
COHER_ORDER = {"D": 1, "A": 2.5, "C": 2.5, "B": 4}


def _score_index():
    idx = {}
    for run in discover_runs():
        for r in scores(run):
            idx[(run, r["id"], int(r.get("sample") or 0), r.get("arm"))] = r
    return idx


def _rho(x, y):
    if len(x) < 8:
        return float("nan")
    r = spearmanr(x, y, nan_policy="omit").correlation
    return float(r) if r == r else float("nan")


def analyse(path, sidx, item1, cal_cache):
    name = os.path.basename(path)[:-5]
    base_name, _, arm = name.rpartition("_A")
    arm = "A" + arm.split("_cap")[0]
    d = json.load(open(path, encoding="utf-8"))
    cells = d["cells"]
    src_stats = d.get("source_stats", {})
    keys = sorted({k for c in cells for k, v in c.items() if k not in META and isinstance(v, (int, float))})
    out = {}
    by_run = {}
    for c in cells:
        by_run.setdefault(c["run"], []).append(c)
    runs_map = discover_runs()
    for k in keys:
        rm = {run: st.mean([c[k] for c in cs if k in c]) for run, cs in by_run.items() if any(k in c for c in cs)}
        floors = [abs(rm[b] - rm[a]) for a, b in REPLICATES if a in rm and b in rm]
        floor = max(floors) if floors else float("nan")
        pairs = {}
        for run, m in rm.items():
            if run in runs_map:
                a, s, kind = runs_map[run]
                pairs.setdefault((a, s), {})[kind] = m
        effects = [abs(v["adapter"] - v["base"]) for v in pairs.values() if "adapter" in v and "base" in v]
        effect = st.mean(effects) if effects else float("nan")
        # manipulation check
        d_ok2 = d_ok5 = d_n = 0
        dvals = {}
        if src_stats:
            for author, stt in src_stats.items():
                if k not in stt:
                    continue
                base_run = next((r for r, (a, s, kd) in runs_map.items() if a == author and s == "4b" and kd == "base" and r in rm), None)
                if not base_run:
                    continue
                bv = [c[k] for c in by_run[base_run] if k in c]
                mu_s, sd_s = stt[k]
                if len(bv) < 2:
                    continue
                sd_b = st.pstdev(bv)
                pooled = ((sd_s ** 2 + sd_b ** 2) / 2) ** 0.5
                dd = abs(mu_s - st.mean(bv)) / pooled if pooled > 0 else float("nan")
                dvals[author] = dd
                d_n += 1
                d_ok2 += dd >= 0.2
                d_ok5 += dd >= 0.5
        # length + redundancy
        xs, ys = [], {sk: [] for sk in SCORE_KEYS}
        for c in cells:
            if k not in c:
                continue
            r = sidx.get((c["run"], c["id"], int(c.get("sample", 0)), arm))
            if not r:
                continue
            ok = all(r.get(sk) is not None for sk in SCORE_KEYS)
            if not ok:
                continue
            xs.append(c[k])
            for sk in SCORE_KEYS:
                ys[sk].append(float(r[sk]))
        rhos = {sk: _rho(xs, ys[sk]) for sk in SCORE_KEYS}
        out[k] = {"floor": floor, "effect": effect, "ratio": (effect / floor if floor and floor == floor and floor > 0 else float("nan")),
                  "d_n": d_n, "d_ok2": d_ok2, "d_ok5": d_ok5, "dvals": dvals, "rhos": rhos, "n_joined": len(xs)}
    # blind item 1
    item = {}
    if item1 and base_name == "constructional":
        import constructional as C
        calA = d.get("calibration", {}).get("patrick_v2")
        if calA:
            for letter in "ABCD":
                sm = C.summarise(C.zvec(C.rates(norm(item1[letter])), calA))
                for kk, x in sm.items():
                    item.setdefault(kk, {})[letter] = float(x)
            sm = C.summarise(C.zvec(C.rates(norm(item1["source"])), calA))
            for kk, x in sm.items():
                item.setdefault(kk, {})["source"] = float(x)
    if item1 and base_name == "event_order":
        import event_order as EO
        from common import briefs
        b = briefs("patrick_v2").get("patrick_v2__116_00_0001")
        if b:
            ks = EO.event_keywords(b)
            for letter in "ABCD":
                sc = EO.score(norm(item1[letter]), ks)
                for kk in ("tau", "events_present", "terminal_missing"):
                    item.setdefault(kk, {})[letter] = float(sc[kk])
            sc = EO.score(norm(item1["source"]), ks)
            for kk in ("tau", "events_present", "terminal_missing"):
                item.setdefault(kk, {})["source"] = float(sc[kk])
    if item1 and base_name in REGISTRY:
        mod_name, fn_name, paired_name = REGISTRY[base_name]
        mod = importlib.import_module(mod_name)
        fn = getattr(mod, fn_name)
        pr = getattr(mod, paired_name) if paired_name else None
        srcv = fn(norm(item1["source"]))
        srcv = srcv if isinstance(srcv, dict) else {"value": srcv}
        stats = {kk: (0.0, 1.0) for kk in srcv}
        if src_stats.get("patrick_v2"):
            stats.update({kk: tuple(v) for kk, v in src_stats["patrick_v2"].items()})
        for letter in "ABCD":
            v = fn(norm(item1[letter]))
            v = v if isinstance(v, dict) else {"value": v}
            if pr:
                v = pr(v, srcv, stats)
                v = v if isinstance(v, dict) else {"value": v}
            for kk, x in v.items():
                if isinstance(x, (int, float)):
                    item.setdefault(kk, {})[letter] = float(x)
        if not pr:
            for kk, x in srcv.items():
                if isinstance(x, (int, float)):
                    item.setdefault(kk, {})["source"] = float(x)
    return name, out, item


def main():
    sidx = _score_index()
    item1 = blind_item1()
    L = ["# Phase 3 gates (SYNTHESIS.md section 4)", "",
         "floor = max |mean diff| over the three replicate pairs; effect = mean |adapter - base| over (author, size) pairs; ratio = effect / floor (below 1 is noise).",
         "d = Cohen's d between the author's sources and the 4B base (unpaired measures only); counts at d >= 0.2 and d >= 0.5 over authors.",
         "rho columns are Spearman over joined cells with the stored scores; |rho| >= 0.8 with an existing measure means fold, not add; |rho(words)| >= 0.4 means length-contaminated.", ""]
    files = sorted(glob.glob(os.path.join(CACHE, "*_A0*.json")))
    summary = []
    for path in files:
        name, out, item = analyse(path, sidx, item1, {})
        if not out:
            continue
        L += [f"## {name}", "", "| key | floor | effect | ratio | d>=0.2 | d>=0.5 | n authors | rho words | rho LUAR | rho open_top | rho open_entropy | rho sent_cv | rho sent_echo | n cells |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for k, g in out.items():
            r = g["rhos"]
            L.append(f"| {k} | {g['floor']:.3f} | {g['effect']:.3f} | {g['ratio']:.1f} | {g['d_ok2']} | {g['d_ok5']} | {g['d_n']} | "
                     f"{r['words']:+.2f} | {r['luar_cos_source']:+.2f} | {r['open_top_share']:+.2f} | {r['open_entropy']:+.2f} | {r['sent_len_cv']:+.2f} | {r['sent_echo']:+.2f} | {g['n_joined']} |")
            summary.append((name, k, g))
        if item:
            L += ["", "Blind item 1 (reader: D best; B lost the story; A and C regressive):", "",
                  "| key | source | A | B | C | D | rho style D>B>A>C | rho coherence D>(A,C)>B |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
            for kk, vals in item.items():
                if not all(l in vals for l in "ABCD"):
                    continue
                v = [vals[l] for l in "ABCD"]
                rs = spearmanr(v, [STYLE_ORDER[l] for l in "ABCD"]).correlation
                rc = spearmanr(v, [COHER_ORDER[l] for l in "ABCD"]).correlation
                L.append(f"| {kk} | {vals.get('source', float('nan')):.3f} | {vals['A']:.3f} | {vals['B']:.3f} | {vals['C']:.3f} | {vals['D']:.3f} | {rs:+.2f} | {rc:+.2f} |")
        L.append("")
    out = os.path.join(RESULTS, "GATES.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
