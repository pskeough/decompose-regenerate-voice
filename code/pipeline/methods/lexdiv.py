"""S8 windowed lexical-diversity triple, from R4.

Hapax proportion (V1/N), MATTR-50 and MTLD (threshold 0.72, bidirectional)
on a fixed WINDOW-token window taken from the start of the text, so texts of
unequal length are comparable (McCarthy and Jarvis 2010: MTLD and MATTR are
length-stable, raw TTR and hapax are not). Unpaired: SOURCE rows are the
author's own values; the interesting number is the signed distance of each
run's mean from its author's source mean, printed in the table.
Texts shorter than MIN_TOKENS are skipped.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate  # noqa: E402

WINDOW = 300
MIN_TOKENS = 200
_TOK = re.compile(r"[A-Za-z][A-Za-z'-]*")


def tokens(text):
    return [t.lower() for t in _TOK.findall(text)]


def mattr(toks, w=50):
    if len(toks) < w:
        return len(set(toks)) / len(toks) if toks else 0.0
    return sum(len(set(toks[i:i + w])) / w for i in range(len(toks) - w + 1)) / (len(toks) - w + 1)


def _mtld_one(toks, thr=0.72):
    factors, types, count = 0.0, set(), 0
    for t in toks:
        types.add(t)
        count += 1
        if len(types) / count <= thr:
            factors += 1
            types, count = set(), 0
    if count > 0:
        ttr = len(types) / count
        factors += (1 - ttr) / (1 - thr) if ttr > thr else 1.0
    return len(toks) / factors if factors else float(len(toks))


def mtld(toks, thr=0.72):
    if len(toks) < 50:
        return float("nan")
    return (_mtld_one(toks, thr) + _mtld_one(list(reversed(toks)), thr)) / 2


def measure(text):
    toks = tokens(text)
    if len(toks) < MIN_TOKENS:
        return {}
    w = toks[:WINDOW]
    counts = {}
    for t in w:
        counts[t] = counts.get(t, 0) + 1
    v1 = sum(1 for c in counts.values() if c == 1)
    return {
        "hapax_w300": v1 / len(w),
        "ttr_w300": len(counts) / len(w),
        "mattr50_w300": mattr(w, 50),
        "mtld_w300": mtld(w),
        "n_tok": len(toks),
    }


if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "A0"
    evaluate(measure, "lexdiv", arm=arm, quiet=True)
