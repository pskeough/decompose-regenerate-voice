"""Within-period attribution of adapter outputs (PLAN 2b).

For every author with a base run and an adapter run, embed the A0 outputs
of both (normalised) and every author's REF passages; report, per author:
    attribution   share of adapter outputs whose nearest REF centroid is the
                  adapter's own author (chance 1/k), and the same for base
    own shift     adapter minus base cosine to the own centroid
    period shift  mean of the same over the other period authors
    specific      own shift minus period shift  (the author-specific gain)

    python dr/cross_attribution.py
    python dr/cross_attribution.py --authors wharton,cather,chesterton,mansfield,chopin,sui_sin_far
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

# author -> (base run, adapter run); the first existing adapter run wins
RUNS_OF = {
    "wharton": ("base4b", ["pair_e6_4b", "pair4b"]),
    "cather": ("cather_base4b", ["cather_pair4b"]),
    "patrick": ("patrick_base4b", ["patrick_mix4b", "patrick_pair4b"]),
}


def unit(x):
    x = np.asarray(x, dtype=np.float32)
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-8)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--authors", default="wharton,cather,chesterton,mansfield,chopin,sui_sin_far,patrick,h_private,patrick_v2")
    ap.add_argument("--out", default=os.path.join(RUNS, "cross_attribution.md"))
    a = ap.parse_args()
    import metrics3
    authors = [x for x in a.authors.split(",") if x]
    pairs = {}
    for au in authors:
        base, cands = RUNS_OF.get(au, (f"{au}_base4b", [f"{au}_paire6_4b", f"{au}_pair4b"]))
        ad = next((c for c in cands if os.path.exists(os.path.join(RUNS, c, "gens.jsonl"))), None)
        if os.path.exists(os.path.join(RUNS, base, "gens.jsonl")) and ad:
            pairs[au] = (base, ad)
    if not pairs:
        raise SystemExit("no author has both a base and an adapter run")
    refs = {au: [normalise_punct(r["text"]) for r in read_jsonl(os.path.join(author_dir(au), "ref.jsonl"))] for au in pairs}
    cents = {au: unit(unit(metrics3.luar_embed(t).numpy()).mean(0, keepdims=True))[0] for au, t in refs.items()}
    C = np.stack([cents[au] for au in pairs])
    names = list(pairs)
    lines = ["# Within-period attribution of adapter outputs (LUAR, normalised text)", "",
             f"Authors: {', '.join(names)}; chance {1/len(names):.2f}.", "",
             "| author | adapter run | attrib base | attrib adapter | own shift | period shift | specific |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for i, au in enumerate(names):
        base, ad = pairs[au]
        Eb = unit(metrics3.luar_embed([normalise_punct(g["text"]) for g in read_jsonl(os.path.join(RUNS, base, "gens.jsonl")) if g["arm"] == "A0"]).numpy())
        Ea = unit(metrics3.luar_embed([normalise_punct(g["text"]) for g in read_jsonl(os.path.join(RUNS, ad, "gens.jsonl")) if g["arm"] == "A0"]).numpy())
        Sb, Sa = Eb @ C.T, Ea @ C.T
        att_b, att_a = float((Sb.argmax(1) == i).mean()), float((Sa.argmax(1) == i).mean())
        own = float(Sa[:, i].mean() - Sb[:, i].mean())
        others = [j for j, o in enumerate(names) if o != au and o != "patrick"] if au != "patrick" else [j for j, o in enumerate(names) if o != au]
        period = float(np.mean([Sa[:, j].mean() - Sb[:, j].mean() for j in others])) if others else float("nan")
        lines.append(f"| {au} | {ad} | {att_b:.2f} | {att_a:.2f} | {own:+.3f} | {period:+.3f} | {own - period:+.3f} |")
    write_text(a.out, "\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
