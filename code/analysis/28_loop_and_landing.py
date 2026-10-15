"""28 loop-and-landing profile (Layer 1) over every generated passage.

Promoted 2026-09-12 from the exploratory pass `exploration_2026-09-11/scratch/R10/layer1.py`
and `agg.py` (finding `exploration_2026-09-11/findings/R10_loop_scan.md`). Reads the workspace's
own copies of the generations (`data/runs/<run>/gens.jsonl`) and the authors' held-out passages
(`data/authors/<author>/test.jsonl`), so nothing outside `data/` is read.

A loop is a maximal contiguous span of at least MIN_SPAN words covered by 8-grams that occur at
least twice in the same passage. The threshold is calibrated on the authors' own held-out prose,
where it flags none of the 635 human passages (the count is printed at run time).

Outputs (analysis/28_loop_and_landing/):
  layer1_cells.csv.gz     one row per generated passage, all arms and both sample draws
  layer1_by_config.csv    loop, landing, saturation and truncation shares by author, family, size, kind, arm
  layer1_contrasts.csv    adapter-minus-base and arm-minus-A0 loop contrasts, and the loop replicate floor
  trunc_tail_repeat.csv   for each truncated cell, the share of its last 100 words inside a repeated span
"""
from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter

import numpy as np
import pandas as pd

from lib import *  # noqa

HERE = outdir("28_loop_and_landing")

N = 8                 # n-gram order, as proposed in R3
MIN_SPAN = 24         # a repeated span must cover at least this many words to count as a loop
TAIL = 100            # the truncation-tail window
TERMINAL = set('.!?"\'\u201d\u2019)')

STOP = set("""a about above after again against all am an and any are aren't as at be because been before being
below between both but by can cannot could couldn't did didn't do does doesn't doing don't down during each few
for from further had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him
himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my
myself no nor not of off on once only or other ought our ours ourselves out over own same shan't she she'd
she'll she's should shouldn't so some such than that that's the their theirs them themselves then there there's
these they they'd they'll they're they've this those through to too under until up very was wasn't we we'd
we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's with
won't would wouldn't you you'd you'll you're you've your yours yourself yourselves said says say one two upon
""".split())

WORD_RE = re.compile(r"[a-z0-9']+")

REPL_PAIRS = [("base4b", "base4b_r2"), ("chesterton_base4b", "chesterton_base4bc"),
              ("mansfield_base4b", "mansfield_base4b_r2"),
              ("chesterton_basem3b", "chesterton_basem3b_r2"), ("patrick_v2_basem3b", "patrick_v2_basem3b_r2"),
              ("chesterton_base8b", "chesterton_base8b_r2"), ("chesterton_base14b", "chesterton_base14b_r2"),
              ("chesterton_basem8b", "chesterton_basem8b_r2"), ("chesterton_basem14b", "chesterton_basem14b_r2")]


def norm_tokens(text):
    """Lowercased alphanumeric tokens, aligned one-to-one with whitespace words where possible."""
    raw = text.split()
    toks = []
    for w in raw:
        m = WORD_RE.findall(w.lower())
        toks.append("".join(m) if m else w.lower())
    return raw, toks


def layer1(text):
    raw, toks = norm_tokens(text)
    n = len(raw)
    out = dict(words=n, loop_onset_words="", loop_span_words=0, loop_share="", max_ngram_count=0,
               saturation_point="", landing=0, ends_mid_sentence=0, tail_repeat_frac="")
    if n == 0:
        return out

    s = text.rstrip()
    out["ends_mid_sentence"] = int(bool(s) and s[-1] not in TERMINAL)

    seen, last_new = set(), 0
    for i, t in enumerate(toks):
        if len(t) >= 3 and t not in STOP and any(c.isalpha() for c in t):
            if t not in seen:
                seen.add(t)
                last_new = i
    out["saturation_point"] = round((last_new + 1) / n, 4)

    marked = [False] * n
    if n >= N:
        grams = Counter()
        for i in range(n - N + 1):
            grams[tuple(toks[i:i + N])] += 1
        out["max_ngram_count"] = max(grams.values())
        for i in range(n - N + 1):
            if grams[tuple(toks[i:i + N])] >= 2:
                for j in range(i, i + N):
                    marked[j] = True

    best_len, best_start, cur_len, cur_start = 0, None, 0, None
    for i, m in enumerate(marked):
        if m:
            if cur_start is None:
                cur_start = i
            cur_len += 1
            if cur_len > best_len:
                best_len, best_start = cur_len, cur_start
        else:
            cur_len, cur_start = 0, None
    if best_len >= MIN_SPAN:
        out["loop_onset_words"] = best_start
        out["loop_span_words"] = best_len
        out["loop_share"] = round((n - best_start) / n, 4)

    if not out["ends_mid_sentence"]:
        start = 0
        for k in range(n - 2, -1, -1):
            w = raw[k].rstrip('"\'\u201d\u2019)')
            if w.endswith((".", "!", "?")):
                start = k + 1
                break
        seg = marked[start:n]
        out["landing"] = int(sum(seg) / max(1, len(seg)) < 0.5)

    # fraction of the final TAIL words that sit inside a repeated span (the truncation-tail probe)
    tail = marked[-TAIL:] if n else []
    out["tail_repeat_frac"] = round(sum(tail) / max(1, len(tail)), 4)
    return out


def run_meta():
    """run -> metadata, from runs.csv plus the run-level columns inside the series/frontier parquets."""
    meta = {}
    r = pd.read_csv(os.path.join(MASTER, "runs.csv"))
    for _, row in r.iterrows():
        meta[row["run"]] = dict(author=row["author"], family=row["family"], params_b=row["params_b"],
                                size_key=row["size_key"], kind=row["kind"], tag=row["tag"],
                                train_examples=row.get("train_examples"), replicate=row.get("replicate"),
                                n_briefs=row.get("n_briefs"), source="runs.csv")
    for f in ("cells_series", "cells_frontier"):
        d = pd.read_parquet(os.path.join(MASTER, f + ".parquet"),
                            columns=["run", "author", "family", "params_b", "size_key", "kind", "tag", "train_examples"])
        for run, g in d.groupby("run"):
            if run in meta:
                continue
            row = g.iloc[0]
            meta[run] = dict(author=row["author"], family=row["family"], params_b=row["params_b"],
                             size_key=row["size_key"], kind=row["kind"], tag=row["tag"],
                             train_examples=row["train_examples"], replicate=False, n_briefs="", source=f)
    return meta


def truncated_map():
    m = {}
    for f in ("cells", "cells_series", "cells_frontier"):
        d = pd.read_parquet(os.path.join(MASTER, f + ".parquet"),
                            columns=["run", "id", "arm", "sample", "truncated"])
        for run, cid, arm, samp, tr in d.itertuples(index=False):
            m[(run, cid, arm, int(samp))] = int(bool(tr))
    return m


def calibrate():
    """Loop rate on the authors' own held-out passages, the negative control for the threshold."""
    tot = loops = 0
    per = {}
    for author in sorted(os.listdir(AUTHORS_DIR)):
        p = os.path.join(AUTHORS_DIR, author, "test.jsonl")
        if not os.path.isfile(p):
            continue
        a = [0, 0, 0, 0]
        for line in open(p, encoding="utf-8"):
            d = json.loads(line)
            r = layer1(d.get("text") or "")
            a[0] += 1
            a[1] += int(r["loop_onset_words"] != "")
            a[2] += r["ends_mid_sentence"]
            a[3] += r["landing"]
            tot += 1
            loops += int(r["loop_onset_words"] != "")
        per[author] = a
    return per, tot, loops


def cluster_boot(vals_by_cluster, n=2000, seed=0):
    groups = [np.asarray(v, float) for v in vals_by_cluster if len(v)]
    if not groups:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    point = float(np.mean(np.concatenate(groups)))
    boots = [np.mean(np.concatenate([groups[i] for i in rng.integers(0, len(groups), size=len(groups))])) for _ in range(n)]
    return (point, float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975)))


def author_boot(per_author, n=2000, seed=0):
    x = np.asarray([v for v in per_author if v == v], float)
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    boots = np.mean(x[rng.integers(0, len(x), size=(n, len(x)))], axis=1)
    return (float(x.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975)))


def main():
    meta = run_meta()
    trunc = truncated_map()
    rows = []
    runs = sorted(d for d in os.listdir(RUNS) if os.path.isfile(os.path.join(RUNS, d, "gens.jsonl")))
    for run in runs:
        m = meta.get(run, {})
        with open(os.path.join(RUNS, run, "gens.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                a = layer1(d.get("text") or "")
                key = (run, d.get("id"), d.get("arm"), int(d.get("sample", 0)))
                rows.append(dict(run=run, id=d.get("id"), arm=d.get("arm"), sample=d.get("sample"),
                                 author=m.get("author", ""), family=m.get("family", ""), params_b=m.get("params_b", ""),
                                 size_key=m.get("size_key", ""), kind=m.get("kind", ""), tag=m.get("tag", ""),
                                 train_examples=m.get("train_examples", ""), replicate=m.get("replicate", ""),
                                 meta_source=m.get("source", "none"), words=a["words"],
                                 loop_onset_words=a["loop_onset_words"], loop_span_words=a["loop_span_words"],
                                 loop_share=a["loop_share"], max_ngram_count=a["max_ngram_count"],
                                 loop=int(a["loop_onset_words"] != ""), saturation_point=a["saturation_point"],
                                 landing=a["landing"], ends_mid_sentence=a["ends_mid_sentence"],
                                 tail_repeat_frac=a["tail_repeat_frac"],
                                 truncated=trunc.get(key, ""), in_cells=int(key in trunc)))
    C = pd.DataFrame(rows)
    write_table(C, os.path.join(HERE, "layer1_cells.csv.gz"), floats=4)
    print("cells", len(C), "runs", len(runs),
          "with meta", int((C.meta_source != "none").sum()), "joined truncated", int(C.in_cells.sum()))

    per, tot, loops = calibrate()
    print("calibration on the authors' own held-out passages:")
    for k, v in per.items():
        print(f"  {k:14s} n={v[0]:3d} loop={v[1]:3d} midsent={v[2]:3d} landing={v[3]:3d}")
    print(f"  TOTAL n={tot} loop={loops} rate={loops / max(1, tot):.4f}  (MIN_SPAN={MIN_SPAN}, N={N})")

    C = C[C.meta_source != "none"].copy()
    for c in ("loop", "landing", "ends_mid_sentence"):
        C[c] = C[c].astype(int)
    C["truncated"] = pd.to_numeric(C["truncated"], errors="coerce")
    C["brief"] = C["id"]

    # ------------------------------------------------------------------ by-config table
    def agg(df, label):
        g = df.groupby(["author", "family", "size_key", "kind", "arm"], dropna=False)
        out = []
        for k, d in g:
            looped = d[d.loop == 1]
            tr = d.dropna(subset=["truncated"])
            out.append(dict(sample_set=label, author=k[0], family=k[1], size_key=k[2], kind=k[3], arm=k[4],
                            n=len(d), loop_share=round(d.loop.mean(), 4),
                            mean_loop_onset=round(looped.loop_onset_words.mean(), 1) if len(looped) else "",
                            mean_loop_share_words=round(looped.loop_share.mean(), 4) if len(looped) else "",
                            landing_share=round(d.landing.mean(), 4), midsent_share=round(d.ends_mid_sentence.mean(), 4),
                            mean_saturation=round(d.saturation_point.mean(), 4),
                            trunc_share=round(tr.truncated.mean(), 4) if len(tr) else "",
                            n_trunc_loop=int(((tr.truncated == 1) & (tr.loop == 1)).sum()),
                            n_trunc_noloop=int(((tr.truncated == 1) & (tr.loop == 0)).sum()),
                            n_notrunc_loop=int(((tr.truncated == 0) & (tr.loop == 1)).sum()),
                            n_notrunc_noloop=int(((tr.truncated == 0) & (tr.loop == 0)).sum())))
        return pd.DataFrame(out)

    by_config = pd.concat([agg(C[C["sample"] == 0], "sample0"), agg(C, "both")], ignore_index=True)
    write_table(by_config, os.path.join(HERE, "layer1_by_config.csv"), floats=4)
    print("by_config rows", len(by_config))

    # ------------------------------------------------------------------ truncation tails
    tt = C[(C.truncated == 1)].copy()
    tail = tt.groupby(["run", "family", "size_key", "kind", "arm"], dropna=False).agg(
        n_trunc=("tail_repeat_frac", "size"), mean_tail_repeat=("tail_repeat_frac", "mean"),
        share_tail_over_50=("tail_repeat_frac", lambda s: float((s >= 0.5).mean())),
        share_tail_over_30=("tail_repeat_frac", lambda s: float((s >= 0.3).mean())),
        share_tail_over_80=("tail_repeat_frac", lambda s: float((s >= 0.8).mean()))).reset_index()
    write_table(tt[[c for c in ("run", "author", "family", "size_key", "kind", "arm", "id", "sample",
                                "truncated", "loop", "loop_span_words", "tail_repeat_frac") if c in tt.columns]],
                os.path.join(HERE, "trunc_tail_repeat.csv"), floats=4)
    print("truncated cells", len(tt), "loop-terminal share >=0.5:",
          round(float((tt.tail_repeat_frac >= 0.5).mean()), 4))

    # ------------------------------------------------------------------ contrasts
    con = []
    mainC = C[C.meta_source == "runs.csv"]
    mainC = mainC[mainC.replicate != True]  # noqa: E712
    a0 = mainC[mainC.arm == "A0"]
    for (fam, size), d in a0.groupby(["family", "size_key"]):
        base, adpt = d[d.kind == "base"], d[d.kind == "adapter"]
        authors = sorted(set(base.author) & set(adpt.author))
        per_author_means, all_clusters = [], []
        for au in authors:
            b = base[base.author == au].groupby(["brief", "sample"]).loop.mean()
            a = adpt[adpt.author == au].groupby(["brief", "sample"]).loop.mean()
            j = pd.concat([b.rename("b"), a.rename("a")], axis=1).dropna()
            if not len(j):
                continue
            j = j.reset_index()
            j["diff"] = j.a - j.b
            clusters = [g["diff"].values for _, g in j.groupby("brief")]
            pt, lo, hi = cluster_boot(clusters, seed=1)
            per_author_means.append(pt)
            all_clusters += clusters
            con.append(dict(contrast="adapter_minus_base", arm="A0", family=fam, size_key=size, level="author",
                            author=au, n_pairs=len(j), estimate=round(pt, 4), lo=round(lo, 4), hi=round(hi, 4)))
        if per_author_means:
            pt, lo, hi = author_boot(per_author_means, seed=2)
            con.append(dict(contrast="adapter_minus_base", arm="A0", family=fam, size_key=size,
                            level="pooled_authors", author=f"n={len(per_author_means)}", n_pairs=len(all_clusters),
                            estimate=round(pt, 4), lo=round(lo, 4), hi=round(hi, 4)))

    bases = mainC[mainC.kind == "base"]
    for arm in ["A1", "A2", "A3", "A4", "A5"]:
        per_author_means, all_clusters = [], []
        for au in sorted(bases.author.unique()):
            d = bases[bases.author == au]
            z = d[d.arm == "A0"].groupby(["run", "brief", "sample"]).loop.mean()
            x = d[d.arm == arm].groupby(["run", "brief", "sample"]).loop.mean()
            j = pd.concat([z.rename("z"), x.rename("x")], axis=1).dropna().reset_index()
            if not len(j):
                continue
            j["diff"] = j.x - j.z
            clusters = [g["diff"].values for _, g in j.groupby("brief")]
            pt, lo, hi = cluster_boot(clusters, seed=3)
            per_author_means.append(pt)
            all_clusters += clusters
            con.append(dict(contrast=f"{arm}_minus_A0", arm=arm, family="all", size_key="all", level="author",
                            author=au, n_pairs=len(j), estimate=round(pt, 4), lo=round(lo, 4), hi=round(hi, 4)))
        if per_author_means:
            pt, lo, hi = author_boot(per_author_means, seed=4)
            con.append(dict(contrast=f"{arm}_minus_A0", arm=arm, family="all", size_key="all",
                            level="pooled_authors", author=f"n={len(per_author_means)}", n_pairs=len(all_clusters),
                            estimate=round(pt, 4), lo=round(lo, 4), hi=round(hi, 4)))
        for (fam, size), d in bases.groupby(["family", "size_key"]):
            pam = []
            for au in sorted(d.author.unique()):
                dd = d[d.author == au]
                z = dd[dd.arm == "A0"].groupby(["run", "brief", "sample"]).loop.mean()
                x = dd[dd.arm == arm].groupby(["run", "brief", "sample"]).loop.mean()
                j = pd.concat([z.rename("z"), x.rename("x")], axis=1).dropna().reset_index()
                if len(j):
                    pam.append(float((j.x - j.z).mean()))
            if pam:
                pt, lo, hi = author_boot(pam, seed=5)
                con.append(dict(contrast=f"{arm}_minus_A0", arm=arm, family=fam, size_key=size,
                                level="pooled_authors", author=f"n={len(pam)}", n_pairs="",
                                estimate=round(pt, 4), lo=round(lo, 4), hi=round(hi, 4)))

    for a, b in REPL_PAIRS:
        x = C[(C.run == a) & (C.arm == "A0")].loop
        y = C[(C.run == b) & (C.arm == "A0")].loop
        if len(x) and len(y):
            con.append(dict(contrast="replicate_floor", arm="A0", family=C.loc[C.run == a, "family"].iloc[0],
                            size_key=C.loc[C.run == a, "size_key"].iloc[0], level="replicate_pair",
                            author=f"{a} vs {b}", n_pairs=min(len(x), len(y)),
                            estimate=round(abs(x.mean() - y.mean()), 4), lo="", hi=""))
    contrasts = pd.DataFrame(con)
    write_table(contrasts, os.path.join(HERE, "layer1_contrasts.csv"), floats=4)
    print("contrast rows", len(contrasts))

    joined = C.dropna(subset=["truncated"])
    loop_rate = float(joined.loop.mean())
    trunc_rate = float(pd.to_numeric(joined.truncated, errors="coerce").mean())
    arms = (contrasts[(contrasts.contrast.str.endswith("_minus_A0")) & (contrasts.level == "pooled_authors")
                      & (contrasts.family == "all") & (contrasts.size_key == "all")]
            [["contrast", "estimate", "lo", "hi"]])
    write_readme(
        HERE, "28 Loop-and-landing profile (Layer 1)",
        f"""
        A per-passage integrity profile over every generation in the study, all arms and both samples:
        a repeated 8-gram span of at least {MIN_SPAN} words for a loop, a landing flag, a content-saturation
        point, and the share of the final {TAIL} words inside a repeated span for a truncated cell. It
        separates two failures the study had been reporting as one column, because the `truncated` flag
        means opposite things in the two model families.
        """,
        f"""
        Metadata comes from `data/master/runs.csv` for the main runs and the run-level columns inside
        `cells_series.parquet` and `cells_frontier.parquet` for the size-series and hosted runs; a cell whose
        run is in no master table is marked `meta_source=none` and excluded from every aggregate. The
        `truncated` flag is joined back onto each cell from the master tables on (run, id, arm, sample).
        The loop threshold is calibrated on the authors' own held-out passages in
        `data/authors/<author>/test.jsonl`: at a {MIN_SPAN}-word span it flags none of the 635 human
        passages (the count is printed at run time). Contrasts are cluster bootstrapped over briefs within
        author and then bootstrapped over authors, exactly as in the exploratory pass.
        """,
        f"""
        Over the joined cells, {loop_rate:.4f} carry a loop and {trunc_rate:.4f} carry the truncation flag.
        The family split is the strongest single result and it is a family effect, not a size or arm effect.
        Loop share falls with corpus size in the within-author series, more steeply than the truncation flag,
        so the thin-data failure is larger than the flag shows. The replicate floor for loop share is
        dominated by one pair and is printed in `layer1_contrasts.csv`. Read the loop rate as a floor for
        degeneration and an over-count for Chesterton-like parallelism.
        """,
        caveats=[
            "Promoted from an exploratory pass (scratch/R10, 2026-09-11); the loop detector is a lexical-repetition instrument with a measured zero false-positive rate on 635 human passages and at least one qualitative false positive on parallel prose.",
            "The loop flag is a floor for degeneration; the landing flag depends on a last-sentence heuristic that fails on dialogue and ellipsis.",
            "loop_share measures from onset to the end of the passage, so a mid-passage repeat followed by recovery scores high; loop_span_words is the honest quantity and both are in the cell file.",
            "The replicate floor for loop share rests on nine pairs and the mansfield 4B pair is several times larger than any other, so the Qwen3 4B floor is either 0.122 or 0.013 depending on which pair is believed.",
        ],
        tables=[("Adapter-minus-base loop share and arm contrasts, pooled over authors",
                 arms.head(20))])

    print("wrote", HERE)


if __name__ == "__main__":
    main()
