"""01_build_master.py: build the tidy tables every analysis reads.

    data/master/cells.parquet      one row per generated passage (run x brief x sample x arm)
                                   with every stored score, gens metadata, eval-cache measures
                                   (A0 and A5 where computed), coverage, 2AFC judge picks,
                                   rubric subscores (sample 0), and run/author keys
    data/master/references.parquet the authors' own passages as scored (group source/ref)
    data/master/runs.csv           one row per run: keys, counts, gate verdicts, training record
    data/master/authors.csv        one row per author: class, corpus and brief counts, notes
    data/master/briefs.csv         one row per test brief: source words, events, dialogue share
    analysis/00_variables.md       the variable dictionary

    python scripts/01_build_master.py
"""
from __future__ import annotations

import collections
import glob
import hashlib
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (AUTHORS_DIR, AUTHOR_CLASS, AUTHOR_NAME, EVAL, MASTER, OUT, PRIVATE, RUNS, VARIABLES, md_table, parse_run,  # noqa: E402
                 variables_table)


def jl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig") as f:
        return [json.loads(l) for l in f if l.strip()]


def jf(path):
    return json.load(open(path, encoding="utf-8-sig")) if os.path.exists(path) else {}


# ---------------------------------------------------------------- runs
def build_runs():
    rows = []
    for name in sorted(os.listdir(RUNS)):
        d = os.path.join(RUNS, name)
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "gens.jsonl")):
            continue
        meta = parse_run(name)
        if not meta:
            print("  unparsed run skipped:", name)
            continue
        gens = jl(os.path.join(d, "gens.jsonl"))
        arms = sorted({g["arm"] for g in gens})
        flags = collections.Counter(f for g in gens for f in (g.get("flags") or []))
        rec = dict(meta)
        rec.update({"n_gens": len(gens), "arms": ",".join(arms), "n_arms": len(arms), "n_briefs": len({g["id"] for g in gens}),
                    "n_samples": len({g.get("sample", 0) for g in gens}), "truncated_pct": 100 * flags["truncated"] / max(len(gens), 1),
                    "preface_pct": 100 * flags["preface"] / max(len(gens), 1), "scored": os.path.exists(os.path.join(d, "scores.jsonl")),
                    "judged_2afc": os.path.exists(os.path.join(d, "judge_summary.json")), "has_coverage": os.path.exists(os.path.join(d, "coverage.jsonl"))})
        man = sorted(glob.glob(os.path.join(d, "s3_manifest*.json")))
        if man:
            m = jf(man[0])
            rec["backend"] = m.get("backend"); rec["base_model"] = m.get("base"); rec["temperature"] = m.get("temperature")
            rec["adapter_served"] = "merged" if "--merged" in json.dumps(m.get("server", {})) or (m.get("adapter") or "").endswith("merged.gguf") else ("lora" if m.get("adapter") else "none")
            pv = m.get("provenance") if isinstance(m.get("provenance"), dict) else {}
            rec["provenance_platform"] = pv.get("platform"); rec["provenance_gpu"] = pv.get("gpu"); rec["provenance_transformers"] = pv.get("transformers")
            rec["llama_server"] = pv.get("llama_server")
            # a stable fingerprint of the generation environment (engine build, GGUF, library versions);
            # runs generated on the same stack share it. Local pre-provenance runs carry none.
            rec["provenance_hash"] = hashlib.sha256(json.dumps(pv, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16] if pv else None
        # training record
        tag = meta["tag"]
        tr = None
        # local 4B adapters are untagged (train_<author>_pair_e6); cloud and family adapters carry the tag;
        # the cather 4B adapter came from the rank-16 seed-0 recipe run; the wharton legacy run is train_wharton_pair_e6
        cands = [f"train_{meta['author']}_pair_e6_{tag}", f"train_{meta['author']}_pair_e6"]
        if name == "cather_pair4b":
            cands.insert(0, "train_cather_pair_r16_s0")
        for cand in cands:
            if os.path.exists(os.path.join(RUNS, cand, "run.json")):
                tr = os.path.join(RUNS, cand, "run.json"); break
        if meta["kind"] == "adapter":
            if tr:
                r = jf(tr)
                hist = [h["eval_loss"] for h in r.get("history", []) if "eval_loss" in h]
                rec.update({"train_run": os.path.basename(os.path.dirname(tr)), "train_examples": r.get("n_examples"), "train_targets": r.get("n_targets"),
                            "train_steps": r.get("steps"), "train_wall_min": (r.get("wall_s") or 0) / 60, "eval_first": hist[0] if hist else None,
                            "eval_best": min(hist) if hist else r.get("best_eval_loss"), "probe_delta": (r.get("probe") or {}).get("delta"),
                            "probe_loss_on": (r.get("probe") or {}).get("val0_loss_adapter_on"), "probe_loss_off": (r.get("probe") or {}).get("val0_loss_adapter_off"),
                            "lora_rank": r.get("rank"), "lora_alpha": r.get("alpha"), "lr": r.get("lr"), "epochs": r.get("epochs")})
            else:
                rec["train_run"] = None
        # gate verdicts from the pod state file
        st = jf(os.path.join(RUNS, f"cloud_state_{meta['author']}_{tag}.json"))
        for s in st.get("steps", []):
            if s.get("name") == "gate base generation" and meta["kind"] == "base":
                rec["gate_generation_ok"] = bool(s.get("ok"))
            if s.get("name") == "gate adapter generation" and meta["kind"] == "adapter":
                rec["gate_generation_ok"] = bool(s.get("ok"))
            if s.get("name") == "gate training" and meta["kind"] == "adapter":
                rec["gate_training_ok"] = bool(s.get("ok")); rec.setdefault("probe_delta", s.get("probe_delta"))
        rows.append(rec)
    df = pd.DataFrame(rows)
    df["author_class"] = df.author.map(AUTHOR_CLASS)
    if "probe_delta" in df.columns:
        df["probe_delta_positive"] = df.probe_delta > 0          # adapter changed nothing measurable (chesterton Ministral 8B)
    # a data-derived truncation verdict for every run, since 43 local runs carry no pod gate record (found 2026-09-10)
    df["truncation_gate_ok"] = df.truncated_pct <= 20.0
    if "gate_generation_ok" in df.columns:
        df["gate_generation_ok"] = df.gate_generation_ok.astype("boolean")
    return df


# ---------------------------------------------------------------- authors
def build_authors(runs):
    rows = []
    for au in sorted(os.listdir(AUTHORS_DIR)):
        d = os.path.join(AUTHORS_DIR, au)
        if not os.path.isdir(d) or au not in AUTHOR_CLASS:
            continue
        sp = jf(os.path.join(d, "split.json"))
        test = jl(os.path.join(d, "test.jsonl")); ref = jl(os.path.join(d, "ref.jsonl")); train = jl(os.path.join(d, "train.jsonl"))
        bt = jl(os.path.join(d, "briefs_test.jsonl")); btr = jl(os.path.join(d, "briefs_train.jsonl"))
        retr = jl(os.path.join(d, "retrieval_test.jsonl"))
        works = sp.get("works") or {}
        rows.append({"author": au, "name": AUTHOR_NAME.get(au, au), "author_class": AUTHOR_CLASS[au], "private": au in PRIVATE,
                     "n_test_chunks": len(test), "n_ref_chunks": len(ref), "n_train_chunks": len(train),
                     "test_briefs_passed": sum(1 for b in bt if b.get("passed")), "train_briefs_passed": sum(1 for b in btr if b.get("passed")),
                     "words_test": sum(c.get("words", 0) for c in test), "words_ref": sum(c.get("words", 0) for c in ref), "words_train": sum(c.get("words", 0) for c in train),
                     "words_total": sum(c.get("words", 0) for c in test + ref + train), "n_works_train": len(works.get("train", [])), "n_works_test": len(works.get("test", [])),
                     "n_works_ref": len(works.get("ref", [])), "chunk_words_mean": float(np.mean([c.get("words", 0) for c in test + ref + train])) if (test + ref + train) else np.nan,
                     "retrieval_fallback_rows": sum(1 for r in retr if r.get("work_fallback")), "within_work_test": au == "h_private",
                     "split_seed": sp.get("seed"), "in_qwen_sweep": au in set(runs[runs.family == "Qwen3"].author), "in_ministral_sweep": au in set(runs[runs.family == "Ministral3"].author)})
    df = pd.DataFrame(rows)
    # adapter training size actually used (from the runs table)
    if "train_examples" in runs.columns:
        used = runs[runs.kind == "adapter"].groupby("author")["train_examples"].max()
        df["train_examples_max"] = df.author.map(used)
    else:
        df["train_examples_max"] = np.nan
    return df


# ---------------------------------------------------------------- briefs
EVENT_RE = re.compile(r"EVENTS?, IN ORDER:\s*(.*?)(?:\n\s*\n|\Z)", re.S | re.I)


def build_briefs():
    rows = []
    for au in sorted(os.listdir(AUTHORS_DIR)):
        d = os.path.join(AUTHORS_DIR, au)
        if not os.path.isdir(d) or au not in AUTHOR_CLASS:
            continue
        chunks = {c["id"]: c for c in jl(os.path.join(d, "test.jsonl"))}
        for b in jl(os.path.join(d, "briefs_test.jsonl")):
            c = chunks.get(b["id"], {})
            text = c.get("text") or ""
            brief = b.get("brief") or ""      # failed briefs carry brief=None
            m = EVENT_RE.search(brief)
            events = [l for l in (m.group(1).splitlines() if m else []) if l.strip()]
            quotes = text.count('"') + text.count("“") + text.count("”")
            sents = max(1, len(re.findall(r"[.!?]+", text)))
            rows.append({"author": au, "id": b["id"], "passed": bool(b.get("passed")), "source_words": b.get("source_words") or c.get("words"),
                         "brief_words": len(brief.split()), "n_events": len(events), "dialogue_share": quotes / (2 * sents),
                         "work": c.get("work"), "work_key": c.get("work_key"), "chunk_idx": c.get("chunk_idx"), "form": c.get("form"),
                         "attempts": b.get("attempts"), "brief_model": b.get("model")})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- cells
NUMERIC_SCORE_COLS = None


def eval_cache_frames():
    """Per-cell eval measures keyed by (run, id, sample). Columns prefixed where names collide."""
    frames = {}
    spec = {"per_A0_cap600": ["per", "per_n_sent"], "per_A0": [("per", "per_uncapped")], "otd_A0": ["otd_js"],
            "psd_A0": ["abs_cv_diff", "cv_diff", "w1_logpara", "mean_sents_diff", "psd_z"],
            "cpd_A0": ["burst_an_diff", "cpd_z", "lag1_diff", "lag2_diff", "lag3_diff", "q50_q10_diff", "q90_q50_diff"],
            "lexdiv_A0": ["hapax_w300", "ttr_w300", "mattr50_w300", "mtld_w300"], "event_order_A0": ["tau", "terminal_missing", "events_present", ("n_events", "n_events_cache")],
            "constructional_A0": ["arti", "arti_w", "arti_hard", "arti_hard_w", "rfpd", "rfpd_w"]}
    for fname, cols in spec.items():
        p = os.path.join(EVAL, "cache", fname + ".json")
        if not os.path.exists(p):
            print("  cache missing:", fname); continue
        cells = jf(p).get("cells", [])
        if not cells:
            continue
        df = pd.DataFrame(cells)
        keep = ["run", "id", "sample"]
        ren = {}
        for c in cols:
            src, dst = (c if isinstance(c, tuple) else (c, c))
            if src in df.columns:
                keep.append(src); ren[src] = dst
        # constructional z features: keep every z_* column too
        if fname.startswith("constructional"):
            for c in df.columns:
                if c.startswith("z_") and c not in keep:
                    keep.append(c)
        sub = df[keep].rename(columns=ren)
        sub["sample"] = sub["sample"].fillna(0).astype(int)
        sub["arm"] = "A0"   # every eval cache was computed on arm A0 only; joining without the arm broadcast A0 values to A1-A5 (found 2026-09-10)
        frames[fname] = sub.drop_duplicates(["run", "id", "sample", "arm"])
    return frames


def build_cells(runs):
    parts = []
    refs = []
    caches = eval_cache_frames()
    rubric = load_rubric()
    for _, r in runs.iterrows():
        d = os.path.join(RUNS, r.run)
        sc = jl(os.path.join(d, "scores.jsonl"))
        if not sc:
            continue
        gens = {(g["id"], g.get("sample", 0), g["arm"]): g for g in jl(os.path.join(d, "gens.jsonl"))}
        cov = collections.defaultdict(list)
        for c in jl(os.path.join(d, "coverage.jsonl")):
            if c.get("coverage") is not None:
                cov[(c["id"], c.get("sample", 0), c["arm"])].append(c["coverage"])
        jud = collections.defaultdict(list)
        for j in jl(os.path.join(d, "judge.jsonl")):
            if "picked_gen" in j:
                jud[(j["id"], j.get("sample", 0), j["arm"], j["comparison"])].append(int(j["picked_gen"]))
        for s in sc:
            if s.get("group") != "gen":
                s2 = dict(s); s2["run"] = r.run; s2["author"] = r.author; refs.append(s2); continue
            key = (s["id"], int(s.get("sample") or 0), s["arm"])
            g = gens.get(key, {})
            flags = set(s.get("flags") or []) | set(g.get("flags") or [])
            row = {k: v for k, v in s.items() if k not in ("flags", "group")}
            row.update({"run": r.run, "author": r.author, "family": r.family, "params_b": r.params_b, "tag": r.tag, "kind": r.kind, "replicate": r.replicate,
                        "size_key": r.size_key, "author_class": AUTHOR_CLASS[r.author], "sample": key[1],
                        "truncated": "truncated" in flags, "preface": "preface" in flags, "length_flag": "length" in flags,
                        "gen_tokens": g.get("gen_tokens"), "prompt_tokens": g.get("prompt_tokens"), "target_words": g.get("target_words"), "n_words_gen": g.get("n_words"),
                        "coverage": float(np.mean(cov[key])) if cov.get(key) else np.nan,
                        "fool_vs_source": float(np.mean(jud[key + ("vs_source",)])) if jud.get(key + ("vs_source",)) else np.nan,
                        "win_vs_A0": float(np.mean(jud[key + ("vs_A0",)])) if jud.get(key + ("vs_A0",)) else np.nan,
                        "n_judges_2afc": len(jud.get(key + ("vs_source",), []))})
            parts.append(row)
    cells = pd.DataFrame(parts)
    for name, fr in caches.items():
        cells = cells.merge(fr, on=["run", "id", "sample", "arm"], how="left")
    if len(rubric):
        # the rubric judged arm A0, sample 0 only (2026-09-10: merging on run/id/sample alone
        # broadcast each judgement to every arm of its run)
        rubric = rubric.assign(arm="A0")
        cells = cells.merge(rubric, on=["run", "id", "sample", "arm"], how="left")
    cells["arm_desc"] = cells.arm.map(lambda a: a)
    refs = pd.DataFrame(refs)
    return cells, refs


def load_rubric():
    recs = []
    for p in sorted(glob.glob(os.path.join(EVAL, "judge", "*.jsonl"))):
        if "mistral" in os.path.basename(p):
            continue   # dropped judge (scores near 10 everywhere)
        for r in jl(p):
            if not r.get("ok"):
                continue
            recs.append(r)
    if not recs:
        return pd.DataFrame()
    df = pd.DataFrame(recs)
    sub = ["C1", "C2", "C3", "C4", "C5", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]
    for c in sub:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    gen = df[df.kind == "gen"].copy()
    gen["rubric_C"] = gen[["C1", "C2", "C3", "C4", "C5"]].mean(axis=1); gen["rubric_S"] = gen[["S1", "S2", "S3", "S4", "S5", "S6", "S7"]].mean(axis=1)
    agg = gen.groupby(["run", "id", "sample"])[sub + ["rubric_C", "rubric_S"]].mean().reset_index()
    agg["n_rubric_records"] = gen.groupby(["run", "id", "sample"]).size().values
    # per-judge means for the two blocks
    for j, short in (("google/gemini-3.1-flash-lite-preview", "gemini"), ("minimax/minimax-m3", "minimax")):
        g = gen[gen.judge == j].groupby(["run", "id", "sample"])[["rubric_C", "rubric_S"]].mean().rename(columns={"rubric_C": f"rubric_C_{short}", "rubric_S": f"rubric_S_{short}"})
        agg = agg.merge(g.reset_index(), on=["run", "id", "sample"], how="left")
    agg = agg.rename(columns={c: f"rubric_{c}" for c in sub})
    agg["sample"] = agg["sample"].fillna(0).astype(int)
    # calibration items to a side table
    cal = df[df.kind != "gen"]
    cal.to_csv(os.path.join(MASTER, "rubric_calibration.csv"), index=False)
    return agg


SIDE_RUNS = {   # runs the main parser skips on purpose; built into side tables, never into cells.parquet
    "base4b_frontier": ("wharton", "frontier", None), "cather_base4b_frontier": ("cather", "frontier", None),
    "sui_sin_far_base4b_frontier": ("sui_sin_far", "frontier", None),
}
_SIZE_RE = re.compile(r"^(?P<author>[a-z0-9_]+?)_size(?P<n>\d+)(?:_s(?P<seed>\d+))?$")


def size_series_runs():
    """Within-author corpus-size series on disk: <author>_size<n>[_s<seed>] (Chesterton 2026-09-06 locally;
    doctorow and patrick_v2 2026-09-10 on RunPod), trained as train_<author>_pair_n<n>_e6[_s<seed>]."""
    found = {}
    for name in sorted(os.listdir(RUNS)):
        m = _SIZE_RE.match(name)
        if m and os.path.exists(os.path.join(RUNS, name, "gens.jsonl")):
            found[name] = (m.group("author"), "series", int(m.group("n")), int(m.group("seed") or 0))
    return found


def build_side_tables():
    """cells_series.parquet: within-author size series, <author>_size<n>[_s<seed>] adapters at 4B (Chesterton A0/A1; doctorow A0/A1; patrick_v2 A0/A5).
    cells_frontier.parquet: the frontier-model arms F0 (brief only) and F5 (full conditioning) on three authors."""
    rows = []
    entries = {k: v + (0,) for k, v in SIDE_RUNS.items()}
    # frontier runs beyond the three legacy names: <author>_<label>_frontier (2026-09-11: base4b = deepseek F0/F5, luna = gpt-5.6-luna F0)
    for name in sorted(os.listdir(RUNS)):
        m = re.match(r"^(?P<author>[a-z0-9_]+?)_(?P<label>[a-z0-9]+)_frontier$", name)
        if m and name not in entries and m.group("author") in AUTHOR_CLASS and os.path.exists(os.path.join(RUNS, name, "gens.jsonl")):
            entries[name] = (m.group("author"), "frontier", None, 0)
    entries.update(size_series_runs())
    for name, (au, series, nb, seed) in entries.items():
        d = os.path.join(RUNS, name)
        if not os.path.exists(os.path.join(d, "gens.jsonl")):
            continue
        man = sorted(glob.glob(os.path.join(d, "s3_manifest*.json")))
        m = jf(man[0]) if man else {}
        tr = os.path.join(RUNS, f"train_{au}_pair_n{nb}_e6" + (f"_s{seed}" if seed else ""), "run.json") if series == "series" else None
        trj = jf(tr) if tr and os.path.exists(tr) else {}
        sp = jf(os.path.join(d, "size_point.json")) if series == "series" else {}
        rows.append({"run": name, "author": au, "tag": "4b", "kind": "adapter" if series == "series" else "frontier", "replicate": False,
                     "family": "Qwen3" if series == "series" else "frontier", "params_b": 4.0 if series == "series" else np.nan,
                     "size_key": "Qwen3-4B" if series == "series" else "frontier", "series": series, "train_briefs_n": nb, "targets_seed": seed,
                     "series_platform": sp.get("platform", "local") if series == "series" else None,
                     "frontier_model": m.get("frontier"), "frontier_label": (re.match(r"^(?:[a-z0-9_]+?_)?(?P<label>[a-z0-9]+)_frontier$", name).group("label") if series == "frontier" else None),
                     "train_examples": trj.get("n_examples"), "train_steps": trj.get("steps"),
                     "probe_delta": (trj.get("probe") or {}).get("delta"), "eval_best": trj.get("best_eval_loss")})
    side = pd.DataFrame(rows)
    if not len(side):
        return pd.DataFrame(), pd.DataFrame()
    cells, _ = build_cells(side)
    keep = ["series", "train_briefs_n", "targets_seed", "series_platform", "frontier_model", "frontier_label", "train_examples", "train_steps", "probe_delta", "eval_best"]
    cells = cells.merge(side[["run"] + keep], on="run", how="left")
    return cells[cells.series == "series"].copy(), cells[cells.series == "frontier"].copy()


def main():
    os.makedirs(MASTER, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    runs = build_runs(); print(f"runs: {len(runs)} ({(runs.kind=='base').sum()} base, {(runs.kind=='adapter').sum()} adapter; families {runs.family.value_counts().to_dict()})")
    authors = build_authors(runs); print(f"authors: {len(authors)}")
    briefs = build_briefs(); print(f"briefs: {len(briefs)} ({briefs.passed.sum()} passed)")
    cells, refs = build_cells(runs); print(f"cells: {len(cells)} rows x {cells.shape[1]} cols; references: {len(refs)}")
    cells = cells.merge(briefs[["author", "id", "source_words", "brief_words", "n_events", "dialogue_share", "work_key"]], on=["author", "id"], how="left")
    cells = cells.merge(authors[["author", "train_briefs_passed", "test_briefs_passed", "words_total", "n_works_train"]], on="author", how="left")
    runs.to_csv(os.path.join(MASTER, "runs.csv"), index=False)
    authors.to_csv(os.path.join(MASTER, "authors.csv"), index=False)
    briefs.to_csv(os.path.join(MASTER, "briefs.csv"), index=False)
    cells.to_parquet(os.path.join(MASTER, "cells.parquet"), index=False)
    cells.to_csv(os.path.join(MASTER, "cells.csv"), index=False)
    refs.to_parquet(os.path.join(MASTER, "references.parquet"), index=False)
    series, frontier = build_side_tables()
    for name, df in (("cells_series", series), ("cells_frontier", frontier)):
        if len(df):
            df = df.merge(briefs[["author", "id", "source_words", "brief_words", "n_events", "dialogue_share", "work_key"]], on=["author", "id"], how="left")
            df.to_parquet(os.path.join(MASTER, f"{name}.parquet"), index=False)
            print(f"{name}: {len(df)} rows ({df.run.nunique()} runs)")
    vt = variables_table()
    vt.to_csv(os.path.join(MASTER, "variables.csv"), index=False)
    present = [v for v in VARIABLES if v in cells.columns]
    lines = ["# Variable dictionary", "", f"Built by scripts/01_build_master.py. {len(present)} of {len(VARIABLES)} dictionary variables are present in cells.parquet; "
             f"eval-cache measures (per, otd_js, psd, cpd, lexdiv, event order, constructional) exist for arm A0 only.", "", md_table(vt, max_rows=200), "",
             "## Keys", "", "run, author, family (Qwen3 / Ministral3), params_b, tag, kind (base / adapter), replicate, arm (A0-A5), id (brief), sample (0/1).", "",
             "## Counts", "", md_table(cells.groupby(["family", "kind"]).size().reset_index(name="cells")), "", md_table(cells.groupby("arm").size().reset_index(name="cells"))]
    open(os.path.join(OUT, "00_variables.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    write_schema({"cells.parquet": (cells, "One row per generated passage.", "run, author, family, params_b, tag, kind, replicate, arm, id, sample"),
                  "references.parquet": (refs, "The authors' own passages and the period pool as scored per run.", "run, group, id"),
                  "runs.csv": (runs, "One row per run.", "run"), "authors.csv": (authors, "One row per author.", "author"),
                  "briefs.csv": (briefs, "One row per test brief.", "author, id"),
                  "cells_series.parquet": (series, "Chesterton training-size series (side table).", "run, arm, id, sample"),
                  "cells_frontier.parquet": (frontier, "Frontier-model arms F0/F5 (side table).", "run, arm, id, sample")},
                 a0_nonreplicate=len(cells[cells.arm.eq("A0") & cells.kind.isin(["base", "adapter"]) & ~cells.replicate]))
    print("-> data/master/*, data/master/schema.json, analysis/00_variables.md, analysis/00_schema.md")
    return 0


def write_schema(tables, a0_nonreplicate):
    """data/master/schema.json (row counts and columns, checked by 10_inventory_integrity) and analysis/00_schema.md."""
    rec = {"built": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"), "a0_nonreplicate_cells": int(a0_nonreplicate), "tables": {}}
    lines = ["# Master table schema (generated)", "", f"Built by scripts/01_build_master.py on {rec['built']}. "
             f"{a0_nonreplicate} A0 non-replicate base/adapter cells form the main analysis set."]
    for name, (df, desc, keys) in tables.items():
        if df is None or not len(df):
            continue
        cols = []
        for c in df.columns:
            s = df[c]
            ex = s.dropna().iloc[0] if s.notna().any() else ""
            cols.append({"column": c, "dtype": "str" if s.dtype == object else str(s.dtype), "non_null": round(float(s.notna().mean()), 3), "example": str(ex)[:60]})
        rec["tables"][name] = {"rows": int(len(df)), "columns": int(df.shape[1]), "keys": keys, "column_list": [c["column"] for c in cols]}
        lines += ["", f"## {name}", "", f"{len(df)} rows x {df.shape[1]} columns. {desc} Keys: {keys}.", "",
                  "| column | dtype | non-null | example |", "|---|---|---:|---|"]
        lines += [f"| {c['column']} | {c['dtype']} | {c['non_null']:.2f} | {c['example'].replace('|', '/')} |" for c in cols]
    json.dump(rec, open(os.path.join(MASTER, "schema.json"), "w", encoding="utf-8"), indent=1)
    open(os.path.join(OUT, "00_schema.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
