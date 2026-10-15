"""Scale table: per author and arm, the primary (LUAR cosine to source,
normalised) for every model tag with a scores_summary on disk, base and
adapter runs side by side, plus truncation and judge coverage/fooling where
judged. Reads runs/<author>_base<tag> and runs/<author>_<recipe>e6_<tag>.

    python dr/scale_eval.py --authors chesterton,mansfield,patrick_v2 --tags 17b,4b,8b,14b
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import RUNS, read_json, read_jsonl, write_text  # noqa: E402


def prim(rid):
    p = os.path.join(RUNS, rid, "scores_summary.json")
    if not os.path.exists(p):
        return {}
    s = read_json(p)
    return {a: v["luar_cos_source"] for a, v in s.items() if a.startswith("A") and isinstance(v, dict) and v.get("luar_cos_source") is not None}


def judge(rid):
    p = os.path.join(RUNS, rid, "judge_summary.json")
    if not os.path.exists(p):
        return {}
    out = {}
    for a, d in read_json(p).items():
        if a.startswith("A"):
            fool = [v for k, v in d.items() if k.startswith("vs_source|")]
            out[a] = (st.mean(fool) if fool else None, d.get("coverage"))
    return out


def trunc(rid):
    p = os.path.join(RUNS, rid, "gens.jsonl")
    if not os.path.exists(p):
        return None
    g = read_jsonl(p)
    return 100 * sum(1 for r in g if "truncated" in (r.get("flags") or [])) / max(len(g), 1)


def f(x, nd=3):
    return "" if x is None else f"{x:.{nd}f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--authors", required=True)
    ap.add_argument("--tags", default="17b,4b,8b,14b")
    ap.add_argument("--recipe", default="pair")
    ap.add_argument("--out", default=os.path.join(RUNS, "scale_table.md"))
    a = ap.parse_args()
    L = ["# Scale table (LUAR cosine to source, normalised; fool/cov from judges on sample 0)", ""]
    for au in [x.strip() for x in a.authors.split(",") if x.strip()]:
        L += [f"## {au}", "", "| model | run | " + " | ".join(f"{arm}" for arm in ("A0", "A1", "A2", "A3", "A4", "A5")) + " | trunc % | fool A0 | cov A0 |",
              "|---|---|" + "---:|" * 9]
        for tag in [t.strip() for t in a.tags.split(",") if t.strip()]:
            for kind, rid in (("base", f"{au}_base{tag}"), ("adapter", f"{au}_{a.recipe}e6_{tag}")):
                pr = prim(rid)
                if not pr:
                    continue
                jd = judge(rid).get("A0", (None, None))
                L.append(f"| {tag} | {kind} | " + " | ".join(f(pr.get(arm)) for arm in ("A0", "A1", "A2", "A3", "A4", "A5")) +
                         f" | {f(trunc(rid), 1)} | {f(jd[0])} | {f(jd[1], 1)} |")
        L.append("")
    write_text(a.out, "\n".join(L))
    print("\n".join(L))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
