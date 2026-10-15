"""S1 + S6(b): read what the pipeline already stores but does not report.

Per run and arm, from runs/<run>/scores.jsonl (no recomputation):
  luar_cos_source, wegmann_cos_source, styledist_cos_source  (three embeddings side by side)
  luar_attrib, wegmann_attrib, styledist_attrib               (nearest-centroid attribution = author)
  sent_echo, rep_4, distinct_3                                 (degeneracy, un-folded from geo_index)
  geo_index
Writes results/stored_outcomes_<arm>.md with the replicate floor and the
base -> adapter contrast per author and size, and caches per-cell values.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, REPLICATES, RESULTS, available_runs, discover_runs, scores  # noqa: E402

COS = ["luar_cos_source", "wegmann_cos_source", "styledist_cos_source"]
ATTR = ["luar_attrib", "wegmann_attrib", "styledist_attrib"]
DEGEN = ["sent_echo", "rep_4", "distinct_3", "geo_index"]


def _attrib_is_author(v, author):
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    return float(str(v) == author)


def run_arm(arm="A0"):
    runs_map = discover_runs()
    rows, cells = [], []
    for run in available_runs(runs_map):
        author, size, kind = runs_map[run]
        recs = [r for r in scores(run) if r.get("arm") == arm]
        if not recs:
            continue
        means = {}
        for k in COS + DEGEN:
            vals = [float(r[k]) for r in recs if r.get(k) is not None]
            if vals:
                means[k] = (st.mean(vals), st.pstdev(vals) if len(vals) > 1 else 0.0)
        for k in ATTR:
            vals = [_attrib_is_author(r[k], author) for r in recs if r.get(k) is not None]
            if vals:
                means[k] = (st.mean(vals), st.pstdev(vals) if len(vals) > 1 else 0.0)
        for r in recs:
            rec = {"run": run, "author": author, "size": size, "kind": kind, "id": r["id"], "sample": r.get("sample", 0)}
            for k in COS + DEGEN:
                if r.get(k) is not None:
                    rec[k] = float(r[k])
            for k in ATTR:
                if r.get(k) is not None:
                    rec[k] = _attrib_is_author(r[k], author)
            cells.append(rec)
        rows.append({"run": run, "author": author, "size": size, "kind": kind, "n": len(recs), "means": means})
    keys = COS + ATTR + DEGEN
    by_run = {r["run"]: r for r in rows}
    L = [f"# Stored outcomes, arm {arm} (read from scores.jsonl; nothing recomputed)", "",
         "Attribution columns are the share of cells whose nearest author centroid is the run's own author (chance 1/k over the reference authors).", ""]
    for k in keys:
        L += [f"## {k}", "", "| run | author | size | kind | n | mean | sd |", "|---|---|---|---|---:|---:|---:|"]
        for r in rows:
            if k in r["means"]:
                m, s = r["means"][k]
                L.append(f"| {r['run']} | {r['author']} | {r['size']} | {r['kind']} | {r['n']} | {m:.3f} | {s:.3f} |")
        L += ["", "Replicate floor:", ""]
        for a, b in REPLICATES:
            if a in by_run and b in by_run and k in by_run[a]["means"] and k in by_run[b]["means"]:
                L.append(f"- {a} vs {b}: {by_run[b]['means'][k][0] - by_run[a]['means'][k][0]:+.3f}")
        L += ["", "Base vs adapter, same author and size:", ""]
        key = {(r["author"], r["size"], r["kind"]): r["means"][k][0] for r in rows if k in r["means"]}
        for (author, size, kind), m in sorted(key.items()):
            if kind == "base" and (author, size, "adapter") in key:
                ad = key[(author, size, "adapter")]
                L.append(f"- {author} {size}: base {m:.3f} -> adapter {ad:.3f} ({ad - m:+.3f})")
        L.append("")
    # three embeddings side by side, adapter minus base
    L += ["## Adapter minus base, three embeddings side by side", "", "| author | size | LUAR | Wegmann | StyleDistance |", "|---|---|---:|---:|---:|"]
    key = {(r["author"], r["size"], r["kind"]): r["means"] for r in rows}
    for (author, size, kind), m in sorted(key.items()):
        if kind == "base" and (author, size, "adapter") in key:
            ad = key[(author, size, "adapter")]
            cells3 = []
            for k in COS:
                cells3.append(f"{ad[k][0] - m[k][0]:+.3f}" if k in m and k in ad else "-")
            L.append(f"| {author} | {size} | " + " | ".join(cells3) + " |")
    out = os.path.join(RESULTS, f"stored_outcomes_{arm}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(CACHE, f"stored_outcomes_{arm}.json"), "w", encoding="utf-8") as f:
        json.dump({"cells": cells}, f)
    print("\n".join(L[-40:]))
    print(f"-> {out}")


if __name__ == "__main__":
    for arm in (sys.argv[1:] or ["A0", "A5"]):
        run_arm(arm)
