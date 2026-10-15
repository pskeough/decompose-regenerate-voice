"""S11 calibrated anchors for the embedding outcomes (R6 gap 1; Sawant 2026
and PersonalBench make calibrated baselines the standard).

Every run's emb_<name>.npy holds one row per scores.jsonl row, in order:
generations, the author's 50 source passages, the author's REF chunks, and
about 1,300 chunks from the other reference authors. So the anchors need no
GPU. Per author and embedding (LUAR, Wegmann, StyleDistance), all as
passage-to-passage cosines on the same scale as the primary cos_source:

  ceiling_same   mean cos(source_i, ref_j) over same-author pairs
                 (what a real second passage by the author scores)
  ceiling_self   mean cos(source_i, source_k), i != k (same, within TEST)
  floor_other    mean cos(source_i, other-author chunk) over all other authors
  floor_nearest  the same, for the single other author with the highest mean
                 (the hardest confusable, e.g. a period neighbour)

Then every run's arm mean cos_source is reported as a position
    pos = (mean - floor_other) / (ceiling_same - floor_other)
so 0 is "as far as another author" and 1 is "as close as the author's own
next passage". Positions above 1 are possible (the same brief shares content
with the source; a real second passage does not) and are reported as such.
Writes results/anchors.md and results/cache/anchors.json.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, RESULTS, RUNS, available_runs, discover_runs, read_jsonl  # noqa: E402

EMB = ["luar", "wegmann", "styledist"]


def load(run):
    rows = read_jsonl(os.path.join(RUNS, run, "scores.jsonl"))
    embs = {}
    for name in EMB:
        p = os.path.join(RUNS, run, f"emb_{name}.npy")
        if os.path.exists(p):
            E = np.load(p)
            if E.shape[0] == len(rows):
                E = E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-9)
                embs[name] = E
    return rows, embs


def anchors_for(rows, E):
    g = [r.get("group") for r in rows]
    src = np.array([i for i, x in enumerate(g) if x == "source"])
    ref = np.array([i for i, x in enumerate(g) if x == "ref"])
    others = sorted({x for x in g if x and x.startswith("other:")})
    if len(src) < 2 or len(ref) < 1:
        return None
    S, R = E[src], E[ref]
    ceiling_same = float((S @ R.T).mean())
    ss = S @ S.T
    ceiling_self = float((ss.sum() - np.trace(ss)) / (len(src) * (len(src) - 1)))
    per_other = {}
    for o in others:
        idx = np.array([i for i, x in enumerate(g) if x == o])
        per_other[o[6:]] = float((S @ E[idx].T).mean())
    floor_other = float(st.mean(per_other.values())) if per_other else float("nan")
    nearest = max(per_other, key=per_other.get) if per_other else None
    return {"ceiling_same": ceiling_same, "ceiling_self": ceiling_self, "floor_other": floor_other,
            "floor_nearest": per_other.get(nearest, float("nan")), "nearest": nearest, "n_src": int(len(src)), "n_ref": int(len(ref)),
            "per_other": per_other}


def main():
    runs_map = discover_runs()
    runs = available_runs(runs_map)
    by_author = {}
    for run in runs:
        by_author.setdefault(runs_map[run][0], []).append(run)
    anchors, table = {}, []
    for author, aruns in sorted(by_author.items()):
        scored = [r for r in aruns if os.path.exists(os.path.join(RUNS, r, "scores.jsonl"))]
        if not scored:
            continue
        base = next((r for r in scored if runs_map[r] == (author, "4b", "base")), scored[0])
        rows, embs = load(base)
        anchors[author] = {}
        for name, E in embs.items():
            a = anchors_for(rows, E)
            if a:
                anchors[author][name] = a
        for run in aruns:
            sp = os.path.join(RUNS, run, "scores.jsonl")
            if not os.path.exists(sp):
                continue
            rws = read_jsonl(sp)
            if not rws:
                continue
            for arm in ("A0", "A5"):
                cells = [r for r in rws if r.get("group") == "gen" and r.get("arm") == arm]
                if not cells:
                    continue
                rec = {"author": author, "run": run, "size": runs_map[run][1], "kind": runs_map[run][2], "arm": arm, "n": len(cells)}
                for name in EMB:
                    vals = [float(r[f"{name}_cos_source"]) for r in cells if r.get(f"{name}_cos_source") is not None]
                    a = anchors[author].get(name)
                    if vals and a:
                        m = st.mean(vals)
                        rec[name] = m
                        rec[name + "_pos"] = (m - a["floor_other"]) / (a["ceiling_same"] - a["floor_other"]) if a["ceiling_same"] != a["floor_other"] else float("nan")
                table.append(rec)
    L = ["# Calibrated anchors (passage-to-passage cosines from the stored embeddings; no recomputation)", "",
         "ceiling_same = mean cos(source, another passage by the author); ceiling_self = within-TEST pairs; floor_other = mean cos(source, other reference authors' chunks); floor_nearest = the single most confusable other author. pos = (arm mean - floor_other) / (ceiling_same - floor_other).", ""]
    for name in EMB:
        L += [f"## {name}: anchors per author", "", "| author | n src | n ref | ceiling_same | ceiling_self | floor_other | floor_nearest | nearest other |", "|---|---:|---:|---:|---:|---:|---:|---|"]
        for author, d in sorted(anchors.items()):
            a = d.get(name)
            if a:
                L.append(f"| {author} | {a['n_src']} | {a['n_ref']} | {a['ceiling_same']:.3f} | {a['ceiling_self']:.3f} | {a['floor_other']:.3f} | {a['floor_nearest']:.3f} | {a['nearest']} |")
        L += ["", f"## {name}: arm means as positions between floor and ceiling", "", "| author | run | size | kind | arm | n | mean cos_source | position |", "|---|---|---|---|---|---:|---:|---:|"]
        for rec in table:
            if name in rec:
                L.append(f"| {rec['author']} | {rec['run']} | {rec['size']} | {rec['kind']} | {rec['arm']} | {rec['n']} | {rec[name]:.3f} | {rec[name + '_pos']:.2f} |")
        L.append("")
    out = os.path.join(RESULTS, "anchors.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(CACHE, "anchors.json"), "w", encoding="utf-8") as f:
        json.dump({"anchors": anchors, "table": table}, f, indent=1)
    print("\n".join(L))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
