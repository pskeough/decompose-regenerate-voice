"""Sentence-opener monotony, the thing Patrick saw blind on 2026-09-07 ("every
sentence is a The or They, it just repeats"): per run and arm, over all
cells, the share of sentences that start with the most common opener, the
share starting with a function word or pronoun (the, a, an, he, she, they,
it, i, we, there), and the rate of consecutive sentences sharing an opener.
Source and reference passages give the author's own baseline.

    python dr/opener_stats.py                         # every run with gens.jsonl
    python dr/opener_stats.py --runs a,b --arm A0
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DATA, RUNS, normalise_punct, read_jsonl, sentences, write_text  # noqa: E402

FUNC = {"the", "a", "an", "he", "she", "they", "it", "i", "we", "there"}


def stats(text):
    ss = [s for s in sentences(normalise_punct(text)) if s.strip()]
    if len(ss) < 3:
        return None
    first = [re.sub(r"^[^A-Za-z]+", "", s).split(" ")[0].lower() for s in ss]
    c = collections.Counter(first)
    return {"top": c.most_common(1)[0][1] / len(ss),
            "func": sum(1 for w in first if w in FUNC) / len(ss),
            "rep": sum(1 for a, b in zip(first, first[1:]) if a == b) / (len(ss) - 1),
            "n": len(ss)}


def agg(texts):
    vals = [v for v in (stats(t) for t in texts) if v]
    if not vals:
        return None
    return {k: st.mean(v[k] for v in vals) for k in ("top", "func", "rep")} | {"cells": len(vals)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="", help="comma-separated; default every run dir with gens.jsonl")
    ap.add_argument("--arm", default="A0")
    ap.add_argument("--out", default=os.path.join(RUNS, "opener_stats.md"))
    a = ap.parse_args()
    runs = [r for r in a.runs.split(",") if r] or sorted(d for d in os.listdir(RUNS) if os.path.exists(os.path.join(RUNS, d, "gens.jsonl")))
    L = ["# Sentence-opener monotony (arm %s; top = share on the most common opener, func = function-word/pronoun openers, rep = consecutive repeats)" % a.arm,
         "", "| run | cells | top | func | rep |", "|---|---:|---:|---:|---:|"]
    seen_authors = set()
    for r in runs:
        rows = [x for x in read_jsonl(os.path.join(RUNS, r, "gens.jsonl")) if x.get("arm") == a.arm]
        if not rows:
            continue
        g = agg([x["raw"] for x in rows])
        L.append(f"| {r} | {g['cells']} | {g['top']:.2f} | {g['func']:.2f} | {g['rep']:.2f} |")
        author = rows[0]["id"].split("__")[0]
        if author not in seen_authors and os.path.exists(os.path.join(DATA, author, "test.jsonl")):
            seen_authors.add(author)
            s = agg([x["text"] for x in read_jsonl(os.path.join(DATA, author, "test.jsonl"))])
            L.append(f"| {author} SOURCE (test) | {s['cells']} | {s['top']:.2f} | {s['func']:.2f} | {s['rep']:.2f} |")
    write_text(a.out, "\n".join(L) + "\n")
    print("\n".join(L))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
