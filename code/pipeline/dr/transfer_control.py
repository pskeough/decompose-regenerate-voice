"""Cross-author transfer control: does an adapter move outputs toward ITS
author, or toward the period?

For each (author, base run, adapter run): embed the base outputs and the
adapter outputs (arm A0, both samples), the author's REF passages and the
OTHER author's REF passages, all normalised. Report, per embedding, the shift
adapter minus base in cosine to the own centroid and to the other centroid,
and the ratio own/other. A ratio near 1 means the adapter learned "old
literary register"; a ratio well above 1 means it learned the author.

    python dr/transfer_control.py
    python dr/transfer_control.py --pairs wharton:base4b:pair_e6_4b,cather:cather_base4b:cather_pair4b
"""
from __future__ import annotations

import argparse
import os
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
    ap.add_argument("--pairs", default="wharton:base4b:pair_e6_4b,cather:cather_base4b:cather_pair4b,patrick:patrick_base4b:patrick_mix4b")
    ap.add_argument("--others", default="wharton,cather,patrick")
    ap.add_argument("--out", default=os.path.join(RUNS, "transfer_control.md"))
    a = ap.parse_args()
    import metrics3
    import s1_features as S1
    embedders = {"luar": lambda t: metrics3.luar_embed(t).numpy(), "wegmann": lambda t: metrics3.style_embed(t).numpy()}
    refs = {au: [normalise_punct(r["text"]) for r in read_jsonl(os.path.join(author_dir(au), "ref.jsonl"))] for au in a.others.split(",")}
    lines = ["# Cross-author transfer control", "",
             "Shift (adapter minus base, arm A0) in cosine to the author's own REF centroid and to each other author's centroid. "
             "ratio = own shift / mean other shift.", ""]
    for spec in a.pairs.split(","):
        au, base_run, ad_run = spec.split(":")
        base = [normalise_punct(g["text"]) for g in read_jsonl(os.path.join(RUNS, base_run, "gens.jsonl")) if g["arm"] == "A0"]
        adap = [normalise_punct(g["text"]) for g in read_jsonl(os.path.join(RUNS, ad_run, "gens.jsonl")) if g["arm"] == "A0"]
        lines += [f"## {au}: {base_run} -> {ad_run}", "", "| embedding | target | base cos | adapter cos | shift |", "|---|---|---:|---:|---:|"]
        for name, fn in embedders.items():
            texts = base + adap
            cents = {}
            for o, rt in refs.items():
                cents[o] = unit(fn(rt)).mean(0)
                cents[o] = cents[o] / np.linalg.norm(cents[o])
            E = unit(fn(texts))
            Eb, Ea = E[: len(base)], E[len(base):]
            shifts = {}
            for o, c in cents.items():
                b, ad = float((Eb @ c).mean()), float((Ea @ c).mean())
                shifts[o] = ad - b
                lines.append(f"| {name} | {o}{' (own)' if o == au else ''} | {b:.3f} | {ad:.3f} | {ad - b:+.3f} |")
            others = [v for o, v in shifts.items() if o != au]
            ratio = shifts[au] / (sum(others) / len(others)) if others and sum(others) != 0 else float("nan")
            lines.append(f"| {name} | ratio own/other | | | {ratio:.2f} |")
        lines.append("")
    write_text(a.out, "\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
