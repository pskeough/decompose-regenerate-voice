"""Gates for the judge rubric rows (run after judge_rubric.py).

Joins each judge's forward-order subscores per cell with the automated
measures (PER capped, opener-class distance, paragraph CV difference,
Wegmann/LUAR cosines, word count) and reports:
  1. Spearman of every subscore with each measure over the joined cells
     (redundancy and length gates);
  2. per-run means of the construction and craft block totals with the
     replicate floor where available (only 4B chesterton has a replicate
     among the judged runs, so the floor is reported as n/a otherwise);
  3. the four blind item-1 candidates (runs base17b / paire6_17b / base4b /
     paire6_4b, id patrick_v2__116_00_0001, sample 0) with the reader's
     ruling, per judge.
Writes results/judge_gates.md.
"""
from __future__ import annotations

import glob
import json
import os
import statistics as st
import sys

from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, RESULTS, discover_runs, read_jsonl, scores  # noqa: E402

KEYS = ["C1", "C2", "C3", "C4", "C5", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]
ITEM1 = {"A": "patrick_v2_base17b", "B": "patrick_v2_paire6_17b", "C": "patrick_v2_base4b", "D": "patrick_v2_paire6_4b"}
ITEM1_ID = "patrick_v2__116_00_0001"


def load_cache(name, key):
    p = os.path.join(CACHE, name + ".json")
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding="utf-8"))
    return {(c["run"], c["id"], int(c.get("sample", 0))): c[key] for c in d["cells"] if key in c}


def main():
    recs = []
    for p in glob.glob(os.path.join(RESULTS, "judge", "*.jsonl")):
        recs += [r for r in read_jsonl(p) if r.get("ok") and r.get("kind") == "gen" and r.get("order") == "fwd"]
    if not recs:
        print("no judge records")
        return
    measures = {
        "per_cap600": load_cache("per_A0_cap600", "per"),
        "otd_js": load_cache("otd_A0", "otd_js"),
        "para_cv_diff": load_cache("psd_A0", "cv_diff"),
        "arti_w": load_cache("constructional_A0", "arti_w"),
        "terminal_missing": load_cache("event_order_A0", "terminal_missing"),
    }
    sidx = {}
    for run in {r["run"] for r in recs}:
        for r in scores(run):
            if r.get("group") == "gen":
                sidx[(run, r["id"], int(r.get("sample") or 0), r.get("arm"))] = r
    L = ["# Judge rubric gates (forward order, generations only)", ""]
    for judge in sorted({r["judge"] for r in recs}):
        J = [r for r in recs if r["judge"] == judge]
        L += [f"## {judge} (n={len(J)})", "", "Spearman rho of each subscore with the automated measures and the stored scores:", "",
              "| subscore | per_cap600 | otd_js | para_cv_diff | arti_w | terminal_missing | luar_cos_source | wegmann_cos_source | words |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for k in KEYS:
            row = []
            for mname, m in measures.items():
                xs, ys = [], []
                for r in J:
                    v = m.get((r["run"], r["id"], int(r["sample"])))
                    if v is not None:
                        xs.append(r[k]); ys.append(v)
                row.append(f"{spearmanr(xs, ys).correlation:+.2f}" if len(xs) >= 10 else "n/a")
            for sk in ("luar_cos_source", "wegmann_cos_source", "words"):
                xs, ys = [], []
                for r in J:
                    s = sidx.get((r["run"], r["id"], int(r["sample"]), "A0"))
                    if s and s.get(sk) is not None:
                        xs.append(r[k]); ys.append(float(s[sk]))
                row.append(f"{spearmanr(xs, ys).correlation:+.2f}" if len(xs) >= 10 else "n/a")
            L.append(f"| {k} | " + " | ".join(row) + " |")
        # block totals per run
        L += ["", "| run | n | construction C1-C5 mean | craft S1-S7 mean | all |", "|---|---:|---:|---:|---:|"]
        by = {}
        for r in J:
            by.setdefault(r["run"], []).append(r)
        for run, rs in sorted(by.items()):
            c = st.mean(st.mean(r[k] for k in KEYS[:5]) for r in rs)
            s = st.mean(st.mean(r[k] for k in KEYS[5:]) for r in rs)
            L.append(f"| {run} | {len(rs)} | {c:.2f} | {s:.2f} | {(c * 5 + s * 7) / 12:.2f} |")
        # item 1
        L += ["", "Blind item 1 (reader: D best; B lost the story; A and C regressive):", "", "| letter | run | " + " | ".join(KEYS) + " | C mean | S mean |", "|---|---|" + "---:|" * (len(KEYS) + 2)]
        for letter, run in ITEM1.items():
            r = next((x for x in J if x["run"] == run and x["id"] == ITEM1_ID and int(x["sample"]) == 0), None)
            if r:
                L.append(f"| {letter} | {run} | " + " | ".join(str(r[k]) for k in KEYS) + f" | {st.mean(r[k] for k in KEYS[:5]):.1f} | {st.mean(r[k] for k in KEYS[5:]):.1f} |")
        L.append("")
    out = os.path.join(RESULTS, "judge_gates.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
