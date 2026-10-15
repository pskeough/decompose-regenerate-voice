"""Blind sample sheet: source passage plus the candidate outputs of several
runs for the same brief, shuffled and lettered, key written separately.
Patrick reads the page and rules; the key stays in runs/<out>_KEY.json.

    python dr/blind_sheet.py --author patrick_v2 --runs patrick_v2_base4b,patrick_v2_base17b,patrick_v2_paire6_4b,patrick_v2_paire6_17b --arm A0 --n 6 --out runs/blind_patrick_v2_scale
"""
from __future__ import annotations

import argparse
import html
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import RUNS, author_dir, normalise_punct, read_jsonl, write_json, write_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", required=True)
    ap.add_argument("--runs", required=True, help="comma-separated run ids")
    ap.add_argument("--arm", default="A0")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True, help="path stem; writes <out>.html and <out>_KEY.json")
    a = ap.parse_args()
    runs = [r.strip() for r in a.runs.split(",") if r.strip()]
    test = {r["id"]: r for r in read_jsonl(os.path.join(author_dir(a.author), "test.jsonl"))}
    gens = {}
    for r in runs:
        for g in read_jsonl(os.path.join(RUNS, r, "gens.jsonl")):
            if g["arm"] == a.arm and int(g.get("sample", 0)) == a.sample:
                gens.setdefault(g["id"], {})[r] = g["raw"]
    ids = sorted(i for i, d in gens.items() if len(d) == len(runs) and i in test)
    R = random.Random(a.seed)
    R.shuffle(ids)
    ids = ids[: a.n]
    key = {"author": a.author, "arm": a.arm, "sample": a.sample, "runs": runs, "items": []}
    parts = ["<title>Blind sheet</title>",
             "<style>body{font-family:Georgia,serif;max-width:920px;margin:2em auto;line-height:1.5;color:#222}"
             ".src{background:#f6f1e7;padding:1em;border-left:4px solid #b08d57}.cand{padding:1em;border:1px solid #ddd;margin:.6em 0}"
             "h2{margin-top:2.5em}h3{margin:.2em 0 .4em;font-family:sans-serif;font-size:.95em;color:#666}p{white-space:pre-wrap}</style>",
             f"<h1>Blind sheet: {html.escape(a.author)}, arm {a.arm}</h1>",
             "<p>Each item shows the real passage, then the candidate regenerations in random order. "
             "Rank or mark the candidates; the key is in a separate file.</p>"]
    for k, i in enumerate(ids, 1):
        cands = list(runs)
        R.shuffle(cands)
        letters = "ABCDEFGH"
        key["items"].append({"n": k, "id": i, "map": {letters[j]: r for j, r in enumerate(cands)}})
        parts.append(f"<h2>Item {k}</h2><h3>Real passage</h3><div class='src'><p>{html.escape(normalise_punct(test[i]['text']))}</p></div>")
        for j, r in enumerate(cands):
            parts.append(f"<h3>Candidate {letters[j]}</h3><div class='cand'><p>{html.escape(normalise_punct(gens[i][r]))}</p></div>")
    write_text(a.out + ".html", "\n".join(parts))
    write_json(a.out + "_KEY.json", key)
    print(f"-> {a.out}.html ({len(ids)} items, {len(runs)} candidates each); key {a.out}_KEY.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
