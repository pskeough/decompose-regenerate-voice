"""A10 detector-tell dissociation (DTD), from R5.

For every run that carries the stored detector columns (binoculars_4bx4b,
fastdetectgpt_4bx4b on both the author's source rows and the generations),
compute per arm:
  AUROC_det   source vs generation on the detector score (higher = more
              separable by the same-family Qwen observer pair)
  AUROC_tell  source vs generation on the winsorised author-relative tell
              index (arti_w from results/cache/constructional_<arm>.json)
  DTD         AUROC_det - AUROC_tell
with a paired passage bootstrap (B=500) for the DTD interval. AUROC is the
Mann-Whitney statistic computed by ranks; no sklearn dependency. The
direction convention: for Binoculars a LOWER score means more machine-like
in this pipeline's storage, so the AUROC is computed as P(source score >
generation score); for the tell index P(generation > source).

A reporting device, never optimised against (R5). Writes results/dtd.md.
"""
from __future__ import annotations

import json
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, RESULTS, RUNS, discover_runs, scores  # noqa: E402

DET = "binoculars_4bx4b"
B = 500


def auroc(pos, neg):
    """P(pos > neg) + 0.5 P(pos == neg), by ranks."""
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    allv = np.concatenate([pos, neg])
    order = allv.argsort(kind="mergesort")
    ranks = np.empty(len(allv))
    ranks[order] = np.arange(1, len(allv) + 1)
    # average ranks for ties
    _, inv, counts = np.unique(allv, return_inverse=True, return_counts=True)
    sums = np.zeros(len(counts))
    np.add.at(sums, inv, ranks)
    ranks = (sums / counts)[inv]
    rp = ranks[: len(pos)].sum()
    return float((rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def main(arm="A0"):
    runs_map = discover_runs()
    cache = json.load(open(os.path.join(CACHE, f"constructional_{arm}.json"), encoding="utf-8"))
    tell = {(c["run"], c["id"], int(c.get("sample", 0))): c["arti_w"] for c in cache["cells"]}
    cal = cache["calibration"]
    # source tell values: recompute cheaply from constructional on the sources
    import constructional as C
    from common import sources
    src_tell = {}
    L = ["# Detector-tell dissociation (arm " + arm + "); AUROC of source vs generation on the same-family Binoculars observer and on the winsorised tell index; DTD = det - tell with a paired passage bootstrap (95% interval)", "",
         "| run | author | size | kind | n gen | AUROC det | AUROC tell | DTD | 95% CI |", "|---|---|---|---|---:|---:|---:|---:|---|"]
    for run in sorted(runs_map):
        rows = scores(run)
        if not rows:
            continue
        gen = [r for r in rows if r.get("group") == "gen" and r.get("arm") == arm and r.get(DET) is not None]
        src = [r for r in rows if r.get("group") == "source" and r.get(DET) is not None]
        if len(gen) < 10 or len(src) < 10:
            continue
        author, size, kind = runs_map[run]
        if author not in src_tell:
            calA = cal[author]
            src_tell[author] = {i: C.summarise(C.zvec(C.rates(t), calA))["arti_w"] for i, t in sources(author).items()}
        gd = [float(r[DET]) for r in gen]
        sd = [float(r[DET]) for r in src]
        gt = [tell.get((run, r["id"], int(r.get("sample") or 0))) for r in gen]
        gt = [x for x in gt if x is not None]
        stl = list(src_tell[author].values())
        a_det = auroc(sd, gd)
        a_tell = auroc(gt, stl)
        dtd = a_det - a_tell
        R = random.Random(0)
        boots = []
        for _ in range(B):
            gi = [R.randrange(len(gd)) for _ in gd]
            si = [R.randrange(len(sd)) for _ in sd]
            ti = [R.randrange(len(gt)) for _ in gt]
            sti = [R.randrange(len(stl)) for _ in stl]
            boots.append(auroc([sd[i] for i in si], [gd[i] for i in gi]) - auroc([gt[i] for i in ti], [stl[i] for i in sti]))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        L.append(f"| {run} | {author} | {size} | {kind} | {len(gd)} | {a_det:.3f} | {a_tell:.3f} | {dtd:+.3f} | [{lo:+.3f}, {hi:+.3f}] |")
    out = os.path.join(RESULTS, "dtd.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"-> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "A0")
