"""S2 paragraph-shape distance (PSD), from R1.

Paragraph architecture as a distribution, not a mean: paragraph length in
words and in sentences, the coefficient of variation of paragraph length, the
1-Wasserstein distance between generation and source on log paragraph length,
and the ratio of first-sentence length to the paragraph's mean sentence length.
Raw values are reported unpaired (SOURCE rows are the author); the paired
version reports |CV diff| and W1 to the passage's own source.

para_mean is a SHOWN feature (in the A4/A5 prompts), so on those arms this is
compliance, not outcome. Paragraph CV and the shape distance are not shown.
"""
from __future__ import annotations

import math
import os
import statistics as st
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, paragraphs, sentences  # noqa: E402


def w1(a, b):
    """1-Wasserstein between two 1-D samples via quantile functions."""
    if not a or not b:
        return float("nan")
    q = np.linspace(0.0, 1.0, 101)
    return float(np.mean(np.abs(np.quantile(a, q) - np.quantile(b, q))))


def profile(text):
    paras = [p for p in paragraphs(text) if p.strip()]
    pw = [len(p.split()) for p in paras]
    ps = [len([s for s in sentences(p) if s.strip()]) for p in paras]
    n = len(pw)
    cv = st.pstdev(pw) / st.mean(pw) if n > 1 and st.mean(pw) > 0 else 0.0
    cvs = st.pstdev(ps) / st.mean(ps) if n > 1 and st.mean(ps) > 0 else 0.0
    first_ratio = []
    for p in paras:
        sl = [len(s.split()) for s in sentences(p) if s.strip()]
        if len(sl) >= 2:
            first_ratio.append(sl[0] / st.mean(sl))
    return {
        "para_n": n,
        "para_mean_words": st.mean(pw) if pw else 0.0,
        "para_mean_sents": st.mean(ps) if ps else 0.0,
        "para_cv_words": cv,
        "para_cv_sents": cvs,
        "first_sent_ratio": st.mean(first_ratio) if first_ratio else 1.0,
        "_log_para": [math.log(max(x, 1)) for x in pw],
    }


def paired(g, s, stats):
    out = {
        "abs_cv_diff": abs(g["para_cv_words"] - s["para_cv_words"]),
        "cv_diff": g["para_cv_words"] - s["para_cv_words"],
        "w1_logpara": w1(g["_log_para"], s["_log_para"]),
        "mean_sents_diff": g["para_mean_sents"] - s["para_mean_sents"],
    }
    # z-normalised L1 over the shape components, sd from the author's sources
    comps = ["para_cv_words", "para_cv_sents", "para_mean_sents", "first_sent_ratio"]
    z = [abs(g[c] - s[c]) / stats[c][1] for c in comps if c in stats and stats[c][1] > 0]
    out["psd_z"] = sum(z) / len(z) if z else float("nan")
    return out


if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "A0"
    evaluate(profile, "psd_raw", arm=arm, quiet=True)
    evaluate(profile, "psd", arm=arm, paired=paired, quiet=True)
    evaluate(profile, "psd", arm=arm, paired=paired, cap=600, quiet=True)
