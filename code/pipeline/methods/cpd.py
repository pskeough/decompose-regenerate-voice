"""S3 cadence-profile distance (CPD), from R1.

The sentence-length series carries order information no current feature uses.
Profile: lag-1..3 autocorrelation of sentence length, finite-size-corrected
burstiness A_n (Kim and Jo 2016, Phys. Rev. E 94, 032311), and the quantile
ratios q90/q50 and q50/q10. Distance is the z-normalised L1 to the source
passage's vector, with sd taken over the author's own source passages.

Corrected burstiness, as read from the arXiv HTML (1604.01125) in R1:
    r = s / m  (sd over mean of the length series, n events)
    A_n(r) = ( sqrt(n+1) r - sqrt(n-1) ) / ( (sqrt(n+1) - 2) r + sqrt(n-1) )
A_n = -1 regular, 0 random, 1 maximally bursty, independent of n. The raw
Goh-Barabasi B = (s-m)/(s+m) has a finite-size ceiling near 1 - 2/sqrt(n),
which matters at our 20-60 sentences. Re-derive against the PDF before quoting.
"""
from __future__ import annotations

import math
import os
import statistics as st
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, sent_lengths  # noqa: E402


def autocorr(x, lag):
    n = len(x)
    if n <= lag + 2:
        return 0.0
    m = st.mean(x)
    v = sum((a - m) ** 2 for a in x)
    if v == 0:
        return 0.0
    return sum((x[i] - m) * (x[i + lag] - m) for i in range(n - lag)) / v


def burstiness_an(x):
    n = len(x)
    if n < 3:
        return 0.0
    m = st.mean(x)
    s = st.pstdev(x)
    if m == 0:
        return 0.0
    r = s / m
    num = math.sqrt(n + 1) * r - math.sqrt(n - 1)
    den = (math.sqrt(n + 1) - 2) * r + math.sqrt(n - 1)
    return num / den if den != 0 else 0.0


def profile(text):
    x = sent_lengths(text)
    if len(x) < 4:
        return {"lag1": 0.0, "lag2": 0.0, "lag3": 0.0, "burst_an": 0.0, "burst_b": 0.0, "q90_q50": 1.0, "q50_q10": 1.0, "sent_cv": 0.0, "n_sent": len(x)}
    q10, q50, q90 = np.quantile(x, [0.1, 0.5, 0.9])
    m, s = st.mean(x), st.pstdev(x)
    return {
        "lag1": autocorr(x, 1), "lag2": autocorr(x, 2), "lag3": autocorr(x, 3),
        "burst_an": burstiness_an(x), "burst_b": (s - m) / (s + m) if (s + m) > 0 else 0.0,
        "q90_q50": q90 / q50 if q50 else 1.0, "q50_q10": q50 / max(q10, 1.0),
        "sent_cv": s / m if m else 0.0, "n_sent": len(x),
    }


COMPS = ["lag1", "lag2", "lag3", "burst_an", "q90_q50", "q50_q10"]


def paired(g, s, stats):
    out = {c + "_diff": g[c] - s[c] for c in COMPS}
    z = [abs(g[c] - s[c]) / stats[c][1] for c in COMPS if c in stats and stats[c][1] > 0]
    out["cpd_z"] = sum(z) / len(z) if z else float("nan")
    return out


if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "A0"
    evaluate(profile, "cpd_raw", arm=arm, quiet=True)
    evaluate(profile, "cpd", arm=arm, paired=paired, quiet=True)
    evaluate(profile, "cpd", arm=arm, paired=paired, cap=600, quiet=True)
