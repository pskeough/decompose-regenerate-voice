"""Shared harness for candidate measures (Phase 3).

A measure is a function passage_text -> float or dict[str, float]. This module
loads every generation and its paired source, applies the pipeline's own text
normalisation plus a glyph fold (S9: curly apostrophes and quotes folded to
straight, so no measure reads corpus provenance), and evaluates a measure under
the contrasts the study already has: source vs base vs adapter, model size,
memorised vs private author, and the replicate-noise floor from runs that were
generated twice. Distances are PAIRED to the source passage whenever the
measure is a profile (R1's constraint): a passage is compared to its own
source, not to a human population.

Nothing here writes into decompose_regenerate/runs; results go to
eval_methodology/results/ and per-cell values to results/cache/ so the
redundancy and blind-agreement gates can be computed across measures later.
"""
from __future__ import annotations

import json
import math
import os
import re
import statistics as st
import sys

DR = r"C:\Work\Personal\Voice_Style_Retune\decompose_regenerate"
sys.path.insert(0, DR)
from dr.core import normalise_punct, paragraphs, sentences  # noqa: E402

try:
    from dr.config import AUTHOR_NAMES  # noqa: E402
except Exception:  # pragma: no cover
    AUTHOR_NAMES = ["wharton", "chesterton", "mansfield", "chopin", "sui_sin_far", "cather", "h_private", "patrick_v2"]

RUNS = os.path.join(DR, "runs")
DATA = os.path.join(DR, "data")
RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CACHE = os.path.join(RESULTS, "cache")
os.makedirs(CACHE, exist_ok=True)

# S9 glyph fold. Off with EVAL_FOLD_GLYPHS=0 for the raw-text sensitivity column.
FOLD_GLYPHS = os.environ.get("EVAL_FOLD_GLYPHS", "1") != "0"
_GLYPHS = {
    "\u2019": "'", "\u2018": "'", "\u201b": "'", "\u2032": "'",
    "\u201c": '"', "\u201d": '"', "\u201f": '"', "\u2033": '"',
    "\u2026": "...", "\u00a0": " ",
}


def fold_glyphs(text: str) -> str:
    for a, b in _GLYPHS.items():
        text = text.replace(a, b)
    return text


def norm(text: str) -> str:
    t = normalise_punct(text)
    return fold_glyphs(t) if FOLD_GLYPHS else t


# run id -> (author, size tag, kind)
SCALE_RUNS = {
    "base4b": ("wharton", "4b", "base"), "base4b_r2": ("wharton", "4b_r2", "base"), "pair_e6_4b": ("wharton", "4b", "adapter"),
    "chesterton_base4b": ("chesterton", "4b", "base"), "chesterton_base4bc": ("chesterton", "4bc", "base"),
    "chesterton_paire6_4b": ("chesterton", "4b", "adapter"), "chesterton_paire6_4bc": ("chesterton", "4bc", "adapter"),
    "chesterton_base8b": ("chesterton", "8b", "base"), "chesterton_paire6_8b": ("chesterton", "8b", "adapter"),
    "chesterton_base14b": ("chesterton", "14b", "base"), "chesterton_paire6_14b": ("chesterton", "14b", "adapter"),
    "mansfield_base4b": ("mansfield", "4b", "base"), "mansfield_base4b_r2": ("mansfield", "4b_r2", "base"), "mansfield_paire6_4b": ("mansfield", "4b", "adapter"),
    "patrick_v2_base17b": ("patrick_v2", "17b", "base"), "patrick_v2_paire6_17b": ("patrick_v2", "17b", "adapter"),
    "patrick_v2_base4b": ("patrick_v2", "4b", "base"), "patrick_v2_paire6_4b": ("patrick_v2", "4b", "adapter"),
    "patrick_v2_base8b": ("patrick_v2", "8b", "base"), "patrick_v2_paire6_8b": ("patrick_v2", "8b", "adapter"),
    "patrick_v2_base14b": ("patrick_v2", "14b", "base"), "patrick_v2_paire6_14b": ("patrick_v2", "14b", "adapter"),
    "h_private_base4b": ("h_private", "4b", "base"), "h_private_paire6_4b": ("h_private", "4b", "adapter"),
    "chopin_base4b": ("chopin", "4b", "base"), "chopin_paire6_4b": ("chopin", "4b", "adapter"),
    "sui_sin_far_base4b": ("sui_sin_far", "4b", "base"), "sui_sin_far_paire6_4b": ("sui_sin_far", "4b", "adapter"),
    "cather_base4b": ("cather", "4b", "base"), "cather_pair4b": ("cather", "4b", "adapter"),
}
PRIVATE = {"patrick_v2", "h_private"}
REPLICATES = [("base4b", "base4b_r2"), ("chesterton_base4b", "chesterton_base4bc"), ("mansfield_base4b", "mansfield_base4b_r2")]

_RUN_RE = re.compile(r"^(?P<author>[a-z0-9_]+?)_(?P<kind>base|paire6|pair_e6|pair)(?P<tag>[0-9a-z_]*)$")
_SIZE_RE = re.compile(r"^(?P<author>[a-z0-9_]+?)_size(?P<n>\d+)(?:_s(?P<seed>\d+))?$")


def discover_runs() -> dict:
    """SCALE_RUNS plus any run on disk whose name parses as
    {author}_base{tag} / {author}_paire6_{tag} (cloud pulls land here)."""
    found = dict(SCALE_RUNS)
    if not os.path.isdir(RUNS):
        return found
    for name in sorted(os.listdir(RUNS)):
        if name in found or not os.path.exists(os.path.join(RUNS, name, "gens.jsonl")):
            continue
        if name.startswith("train_") or name.endswith("_frontier"):
            continue
        # within-author corpus-size series (<author>_size<n>[_s<seed>], 2026-09-06 Chesterton locally,
        # 2026-09-10 doctorow and patrick_v2 on RunPod): included only when DR_INCLUDE_SIZE_RUNS=1, so the
        # measure caches gain their rows without the scale tables and gates seeing a "size" that is not a
        # parameter count. Kind "adapter", size "size<n>[_s<seed>]".
        ms = _SIZE_RE.match(name)
        if ms:
            if os.environ.get("DR_INCLUDE_SIZE_RUNS") == "1" and ms.group("author") in AUTHOR_NAMES:
                found[name] = (ms.group("author"), "size" + ms.group("n") + ("_s" + ms.group("seed") if ms.group("seed") else ""), "adapter")
            continue
        m = _RUN_RE.match(name)
        if not m or m.group("author") not in AUTHOR_NAMES:
            continue
        tag = m.group("tag").strip("_") or "4b"
        kind = "base" if m.group("kind") == "base" else "adapter"
        found[name] = (m.group("author"), tag, kind)
    return found


def read_jsonl(path):
    with open(path, encoding="utf-8-sig") as f:
        return [json.loads(l) for l in f if l.strip()]


def sources(author):
    return {r["id"]: norm(r["text"]) for r in read_jsonl(os.path.join(DATA, author, "test.jsonl"))}


def refs(author):
    p = os.path.join(DATA, author, "ref.jsonl")
    return [norm(r["text"]) for r in read_jsonl(p)] if os.path.exists(p) else []


def train_texts(author):
    p = os.path.join(DATA, author, "train.jsonl")
    return [norm(r["text"]) for r in read_jsonl(p)] if os.path.exists(p) else []


def briefs(author):
    """{id: brief text} for briefs that passed the leakage gate."""
    p = os.path.join(DATA, author, "briefs_test.jsonl")
    if not os.path.exists(p):
        return {}
    return {b["id"]: b["brief"] for b in read_jsonl(p) if b.get("passed") and b.get("brief")}


def gens(run, arm="A0"):
    """[(id, sample, text)] for one arm of a run, normalised."""
    p = os.path.join(RUNS, run, "gens.jsonl")
    if not os.path.exists(p):
        return []
    return [(g["id"], int(g.get("sample", 0)), norm(g["raw"])) for g in read_jsonl(p) if g["arm"] == arm]


def scores(run):
    p = os.path.join(RUNS, run, "scores.jsonl")
    return read_jsonl(p) if os.path.exists(p) else []


def available_runs(runs_map=None):
    runs_map = runs_map or discover_runs()
    return [r for r in runs_map if os.path.exists(os.path.join(RUNS, r, "gens.jsonl"))]


def truncate_words(text, n):
    """First n words, on the original whitespace, keeping paragraph breaks."""
    if n is None:
        return text
    out, count = [], 0
    for para in text.split("\n"):
        w = para.split()
        if count + len(w) <= n:
            out.append(para)
            count += len(w)
        else:
            out.append(" ".join(w[: n - count]))
            break
    return "\n".join(out)


def sent_lengths(text):
    return [len(s.split()) for s in sentences(text) if s.strip()]


def para_lengths(text):
    return [len(p.split()) for p in paragraphs(text) if p.strip()]


def openers(text):
    out = []
    for s in sentences(text):
        w = re.sub(r"^[^A-Za-z]+", "", s).split(" ")[0].lower() if s.strip() else ""
        if w:
            out.append(w)
    return out


def _as_dict(v):
    return v if isinstance(v, dict) else {"value": float(v)}


def _mean_sd(vals):
    return (st.mean(vals), st.pstdev(vals) if len(vals) > 1 else 0.0)


def evaluate(measure, name, arm="A0", paired=None, runs=None, cap=None, runs_map=None, quiet=False):
    """Score every cell. `measure(text) -> float | dict`. When `paired` is given
    it is `paired(gen_value, source_value, author_stats) -> float | dict` and
    the tables report the paired distance; `author_stats` is
    {key: (mean, sd)} over that author's source passages. `cap` truncates
    both generation and source to the first `cap` words (the length null).
    Writes results/<name>[_cap].md and per-cell values to results/cache/."""
    runs_map = runs_map or discover_runs()
    runs = runs or available_runs(runs_map)
    tag = f"{name}_{arm}" + (f"_cap{cap}" if cap else "")
    rows, cells, src_cache, src_stats = [], [], {}, {}
    for run in runs:
        author, size, kind = runs_map[run]
        if author not in src_cache:
            src_cache[author] = {i: _as_dict(measure(truncate_words(t, cap))) for i, t in sources(author).items()}
            keys = sorted({k for d in src_cache[author].values() for k, x in d.items() if _num(x)})
            src_stats[author] = {k: _mean_sd([d[k] for d in src_cache[author].values() if k in d and _num(d[k])]) for k in keys}
        per_key = {}
        for gid, sample, text in gens(run, arm):
            v = _as_dict(measure(truncate_words(text, cap)))
            if paired is not None:
                sv = src_cache[author].get(gid)
                if sv is None:
                    continue
                v = _as_dict(paired(v, sv, src_stats[author]))
            rec = {"run": run, "author": author, "size": size, "kind": kind, "id": gid, "sample": sample}
            for k, x in v.items():
                if _num(x):
                    per_key.setdefault(k, []).append(float(x))
                    rec[k] = float(x)
            cells.append(rec)
        if not per_key:
            continue
        rows.append({"run": run, "author": author, "size": size, "kind": kind,
                     "n": max(len(x) for x in per_key.values()),
                     "means": {k: _mean_sd(x) for k, x in per_key.items()}})
    keys = sorted({k for r in rows for k in r["means"]})
    src_rows = []
    if paired is None:
        for author, d in src_cache.items():
            src_rows.append({"run": f"{author} SOURCE", "author": author, "size": "-", "kind": "source", "n": len(d),
                             "means": {k: src_stats[author][k] for k in keys if k in src_stats[author]}})
    by_run = {r["run"]: r for r in rows}
    L = [f"# {name} (arm {arm}{', first ' + str(cap) + ' words' if cap else ''}; "
         f"{'paired distance to the source passage' if paired else 'raw value; SOURCE rows are the author'}; "
         f"glyph fold {'on' if FOLD_GLYPHS else 'off'})", ""]
    floors = {}
    for k in keys:
        L += [f"## {k}", "", "| run | author | size | kind | n | mean | sd |", "|---|---|---|---|---:|---:|---:|"]
        for r in src_rows + rows:
            if k in r["means"]:
                m, s = r["means"][k]
                L.append(f"| {r['run']} | {r['author']} | {r['size']} | {r['kind']} | {r['n']} | {m:.3f} | {s:.3f} |")
        L += ["", "Replicate floor (same configuration generated twice; a contrast smaller than this is not a finding):", ""]
        for a, b in REPLICATES:
            if a in by_run and b in by_run and k in by_run[a]["means"] and k in by_run[b]["means"]:
                d = by_run[b]["means"][k][0] - by_run[a]["means"][k][0]
                floors.setdefault(k, []).append((a, b, d))
                L.append(f"- {a} vs {b}: {d:+.3f}")
        L += ["", "Base vs adapter, same author and size:", ""]
        key = {(r["author"], r["size"], r["kind"]): r["means"][k][0] for r in rows if k in r["means"]}
        for (author, size, kind), m in sorted(key.items()):
            if kind == "base" and (author, size, "adapter") in key:
                ad = key[(author, size, "adapter")]
                L.append(f"- {author} {size}: base {m:.3f} -> adapter {ad:.3f} ({ad - m:+.3f})")
        L.append("")
    out = os.path.join(RESULTS, f"{tag}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(CACHE, f"{tag}.json"), "w", encoding="utf-8") as f:
        json.dump({"cells": cells, "source_stats": {a: {k: list(v) for k, v in d.items()} for a, d in src_stats.items()}}, f)
    if not quiet:
        print("\n".join(L))
    print(f"-> {out}")
    return rows, floors, cells


def _num(x):
    return isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x))


def extremes(measure, run, arm="A0", k=2, key=None, cap=None):
    """Top-k and bottom-k cells by the measure (or by `key` of a dict
    measure), for reading (Phase 4)."""
    cells = []
    for gid, s, t in gens(run, arm):
        v = _as_dict(measure(truncate_words(t, cap)))
        x = v[key] if key else next(iter(v.values()))
        cells.append((x, gid, s, t))
    cells.sort(key=lambda x: x[0])
    return cells[:k], cells[-k:]


def blind_item1():
    """The four candidates of blind item 1 with Patrick's ruling, if the
    key file exists: [(letter, text, run)]."""
    p = os.path.join(RUNS, "blind_patrick_v2_scale_item1.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)
