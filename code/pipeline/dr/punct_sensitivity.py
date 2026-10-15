"""Does the primary outcome survive removing transcription punctuation?

Wharton's Gutenberg text writes dashes as `--` and italics as `_word_`; no
model output does, and the 6-epoch adapter learned to emit `--` in 32% of
its outputs. If LUAR is partly reading that encoding, the adapter's gain is
partly an artefact. Re-embed every generation and its source with
`normalise_punct` applied to both and compare cosine-to-source with the raw
numbers, per arm.

    python dr/punct_sensitivity.py --runs base4b,pair4b,pair_e6_4b,base4b_frontier --author wharton
"""
from __future__ import annotations

import argparse
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import MIMESIS_LOCAL, OVERNIGHT, RUNS, SCRIPTS, author_dir, normalise_punct, read_jsonl, write_text  # noqa: E402

for p in (MIMESIS_LOCAL, SCRIPTS, OVERNIGHT):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np  # noqa: E402


def unit(x):
    x = np.asarray(x, dtype=np.float32)
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-8)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="base4b,pair4b,pair_e6_4b,base4b_frontier")
    ap.add_argument("--author", default="wharton")
    ap.add_argument("--out", default=os.path.join(RUNS, "punct_sensitivity_wharton.md"))
    a = ap.parse_args()
    import metrics3
    test = {r["id"]: r["text"] for r in read_jsonl(os.path.join(author_dir(a.author), "test.jsonl"))}
    lines = ["# Punctuation sensitivity of the primary (LUAR cosine to source)", "",
             "raw = texts as scored; norm = `--` -> em dash and `_x_` -> x applied to both generation and source.", "",
             "| run | arm | n | raw | norm | delta |", "|---|---|---:|---:|---:|---:|"]
    for run in [r for r in a.runs.split(",") if r]:
        gens = read_jsonl(os.path.join(RUNS, run, "gens.jsonl"))
        arms = sorted({g["arm"] for g in gens})
        for arm in arms:
            gs = [g for g in gens if g["arm"] == arm and g["id"] in test]
            raw_g = [g["text"] for g in gs]; raw_s = [test[g["id"]] for g in gs]
            nrm_g = [normalise_punct(t) for t in raw_g]; nrm_s = [normalise_punct(t) for t in raw_s]
            E = unit(metrics3.luar_embed(raw_g + raw_s + nrm_g + nrm_s).numpy())
            n = len(gs)
            raw = [float(E[i] @ E[n + i]) for i in range(n)]
            nrm = [float(E[2 * n + i] @ E[3 * n + i]) for i in range(n)]
            lines.append(f"| {run} | {arm} | {n} | {st.mean(raw):.3f} | {st.mean(nrm):.3f} | {st.mean(nrm) - st.mean(raw):+.3f} |")
            print(lines[-1])
    write_text(a.out, "\n".join(lines) + "\n")
    print("->", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
