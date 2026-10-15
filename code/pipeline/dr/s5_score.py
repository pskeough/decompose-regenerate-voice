"""S5: score every generation against its source, the author, and the AI anchor
(METHODS 8). GPU stage; the API judges are s5b.

Rows scored: the run's generations, the TEST sources, the REF passages, and the
other-author chunks (centroids only). The overnight battery's family functions
are imported by path so the instrument is the validated one.

Per generation:
    luar_cos_source      PRIMARY. cosine to its own source passage
    luar_cos_ref         cosine to the author's REF centroid
    luar_cos_ai          cosine to the A0 centroid of the anchor run
    luar_attrib          1 if nearest of the 14 author centroids is the target
    wegmann_*, styledist_*   the same four for the other two embeddings
    delta_own, delta_rank    Burrows's Delta to the target author, and its rank
    surface / syntax / degeneracy features (overnight battery)
    shown_*              the nine SHOWN features, and shown_dist (compliance)
    geo_index, geo_overshoot, geo_n    position between A0 and REF on SEALED features
    memo_lcs, memo_8gram, memo_flag    reconstruction from the source
    (--detect) binoculars, fastdetectgpt

    python dr/s5_score.py --run base4b
    python dr/s5_score.py --run pair4b --anchor-run base4b
"""
from __future__ import annotations

import argparse
import collections
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import (DATA, MIMESIS_LOCAL, OVERNIGHT, RUNS, SCRIPTS, Manifest,  # noqa: E402
                     author_dir, log, ngrams, norm_words, normalise_punct, read_json, read_jsonl, words,
                     write_json, write_jsonl)
from dr.s2_conditioning import shown_features  # noqa: E402

for p in (MIMESIS_LOCAL, SCRIPTS, OVERNIGHT):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402


def _unit(x):
    x = np.asarray(x, dtype=np.float32)
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-8)


# ---------------------------------------------------------- memorisation

def lcs_words(a, b, lo=4):
    """Length of the longest shared word run, by binary search over n-gram sets."""
    if not a or not b:
        return 0
    hi = min(len(a), len(b))
    if not (ngrams(a, lo) & ngrams(b, lo)):
        return max(0, lo - 1) if not (set(a) & set(b)) else lo - 1
    best, L, H = lo, lo, hi
    while L <= H:
        m = (L + H) // 2
        if ngrams(a, m) & ngrams(b, m):
            best, L = m, m + 1
        else:
            H = m - 1
    return best


def memo(gen_text, src_text):
    g, s = norm_words(gen_text), norm_words(src_text)
    n = config.MEMO["ngram"]
    gn = ngrams(g, n)
    frac = len(gn & ngrams(s, n)) / len(gn) if gn else 0.0
    lcs = lcs_words(g, s)
    return {"memo_lcs": lcs, "memo_8gram": round(frac, 4),
            "memo_flag": int(lcs >= config.MEMO["lcs_words"])}


# ------------------------------------------------------------------ delta

def delta_features(rows, fw_profile, target):
    """Burrows's Delta: z-score function-word rates against the population of
    REF + other-author rows; author centroids are mean z-profiles; distance is
    mean absolute z difference (Burrows 2002; Evert et al. 2017 for why the
    mean-absolute form is the one to keep)."""
    prof = np.stack([fw_profile(r["text"]) for r in rows])
    pop = [i for i, r in enumerate(rows) if r["group"] in ("ref",) or r["group"].startswith("other:")]
    mu, sd = prof[pop].mean(0), prof[pop].std(0) + 1e-9
    z = (prof - mu) / sd
    cents = {}
    by_author = collections.defaultdict(list)
    for i in pop:
        r = rows[i]
        by_author[target if r["group"] == "ref" else r["group"].split(":", 1)[1]].append(i)
    for a_, idx in by_author.items():
        cents[a_] = z[idx].mean(0)
    out = []
    for i, r in enumerate(rows):
        zi = z[i]
        if r["group"] == "ref":   # leave-one-out for the author's own rows
            idx = [j for j in by_author[target] if j != i]
            c_t = z[idx].mean(0)
        else:
            c_t = cents[target]
        d_t = float(np.abs(zi - c_t).mean())
        ds = {a_: float(np.abs(zi - c).mean()) for a_, c in cents.items() if a_ != target}
        rank = 1 + sum(1 for v in ds.values() if v < d_t)
        out.append({"delta_own": d_t, "delta_rank": rank,
                    "delta_nearest": target if rank == 1 else min(ds, key=ds.get)})
    return out


# ------------------------------------------------------------- embeddings

def embed_features(rows, name, E, target, anchor_ids):
    """cos to source, ref centroid, AI (A0) centroid; nearest-author attribution."""
    E = _unit(E)
    idx_by_id = {}
    for i, r in enumerate(rows):
        if r["group"] == "source":
            idx_by_id[r["id"]] = i
    ref_idx = [i for i, r in enumerate(rows) if r["group"] == "ref"]
    cents = {target: _unit(E[ref_idx].mean(0))}
    by_other = collections.defaultdict(list)
    for i, r in enumerate(rows):
        if r["group"].startswith("other:"):
            by_other[r["group"].split(":", 1)[1]].append(i)
    for a_, idx in by_other.items():
        cents[a_] = _unit(E[idx].mean(0))
    ai_idx = [i for i, r in enumerate(rows) if r["group"] == "gen" and r["arm"] == "A0"
              and (not anchor_ids or r["_key"] in anchor_ids)]
    c_ai = _unit(E[ai_idx].mean(0)) if ai_idx else None
    ref_sum = E[ref_idx].sum(0)
    out = []
    for i, r in enumerate(rows):
        e = E[i]
        f = {}
        if r["group"] == "gen" and r["id"] in idx_by_id:
            f[f"{name}_cos_source"] = float(e @ E[idx_by_id[r["id"]]])
        if r["group"] == "ref":
            c_t = _unit(ref_sum - e)
        else:
            c_t = cents[target]
        f[f"{name}_cos_ref"] = float(e @ c_t)
        if c_ai is not None:
            f[f"{name}_cos_ai"] = float(e @ c_ai)
        sims = {a_: float(e @ c) for a_, c in cents.items() if a_ != target}
        sims[target] = float(e @ c_t)
        best = max(sims, key=sims.get)
        f[f"{name}_nearest"] = best
        f[f"{name}_attrib"] = int(best == target)
        out.append(f)
    return out


# --------------------------------------------------------------- geometry

def geometry(rows, feats, anchor_ids):
    """pos_f = (x - mu_ai) / (mu_author - mu_ai) on SEALED features; index and
    overshoot per row (METHODS 8.3)."""
    ref_i = [i for i, r in enumerate(rows) if r["group"] == "ref"]
    ai_i = [i for i, r in enumerate(rows) if r["group"] == "gen" and r["arm"] == "A0"
            and (not anchor_ids or r["_key"] in anchor_ids)]
    lo, hi = config.GEOMETRY["clip"]
    kept, dropped = {}, {}
    for f in config.SEALED_FEATURES:
        ra = [feats[i].get(f) for i in ref_i]
        aa = [feats[i].get(f) for i in ai_i]
        ra = [v for v in ra if v is not None and v == v]
        aa = [v for v in aa if v is not None and v == v]
        if len(ra) < 5 or len(aa) < 5:
            dropped[f] = "missing"
            continue
        mu_a, mu_ai = st.mean(ra), st.mean(aa)
        pooled = math.sqrt((st.pvariance(ra) + st.pvariance(aa)) / 2) + 1e-9
        if abs(mu_a - mu_ai) < config.GEOMETRY["min_sep_sd"] * pooled:
            dropped[f] = f"sep {abs(mu_a - mu_ai)/pooled:.2f} sd"
            continue
        kept[f] = (mu_a, mu_ai)
    for i, r in enumerate(rows):
        pos = []
        for f, (mu_a, mu_ai) in kept.items():
            v = feats[i].get(f)
            if v is None or v != v:
                continue
            p = (v - mu_ai) / (mu_a - mu_ai)
            pos.append(min(max(p, lo), hi))
        feats[i]["geo_index"] = st.mean(pos) if pos else None
        feats[i]["geo_overshoot"] = (sum(1 for p in pos if p > config.GEOMETRY["overshoot"]) / len(pos)) if pos else None
        feats[i]["geo_n"] = len(pos)
    return {"kept": {f: {"mu_author": a, "mu_ai": b} for f, (a, b) in kept.items()}, "dropped": dropped}


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--anchor-run", default="", help="run whose A0 defines the AI centroid (default: this run)")
    ap.add_argument("--detect", action="store_true", help="run Binoculars / Fast-DetectGPT (9B, slow)")
    ap.add_argument("--observer", default=config.DETECTOR_PAIR[0])
    ap.add_argument("--performer", default=config.DETECTOR_PAIR[1])
    ap.add_argument("--obs-4bit", action="store_true", help="NF4 observer; two bf16 4B models do not fit 16 GB")
    ap.add_argument("--perf-4bit", action="store_true")
    ap.add_argument("--no-embed", action="store_true")
    ap.add_argument("--raw", action="store_true", help="score raw text (default normalises per config.NORMALISE_TEXT)")
    a = ap.parse_args()
    d = author_dir(a.author)
    rd = os.path.join(RUNS, a.run)
    man = Manifest(os.path.join(rd, "s5_manifest.json"), "s5_score")
    gens = read_jsonl(os.path.join(rd, "gens.jsonl"))
    man.input("gens", os.path.join(rd, "gens.jsonl"))
    test = read_jsonl(os.path.join(d, "test.jsonl"))
    ref = read_jsonl(os.path.join(d, "ref.jsonl"))
    others = read_jsonl(os.path.join(d, "others.jsonl"))
    quant = read_json(os.path.join(d, "quant.json")) if os.path.exists(os.path.join(d, "quant.json")) else None
    briefs = {r["id"]: r for r in read_jsonl(os.path.join(d, "briefs_test.jsonl"))} \
        if os.path.exists(os.path.join(d, "briefs_test.jsonl")) else {}

    rows = []
    for g in gens:
        rows.append({**g, "group": "gen", "words": g["n_words"], "_key": f"{a.run}|{g['id']}|{g['sample']}",
                     "meta": {}})
    anchor_ids = set()
    if a.anchor_run and a.anchor_run != a.run:
        for g in read_jsonl(os.path.join(RUNS, a.anchor_run, "gens.jsonl")):
            if g["arm"] == "A0":
                rows.append({**g, "group": "gen", "words": g["n_words"], "arm": "A0",
                             "_key": f"{a.anchor_run}|{g['id']}|{g['sample']}", "meta": {}, "_anchor_only": True})
                anchor_ids.add(f"{a.anchor_run}|{g['id']}|{g['sample']}")
    src_by_id = {r["id"]: r for r in test}
    for r in test:
        rows.append({"id": r["id"], "group": "source", "text": r["text"], "words": r["words"], "meta": {}})
    for r in ref:
        rows.append({"id": r["id"], "group": "ref", "text": r["text"], "words": r["words"], "meta": {}})
    for r in others:
        rows.append({"id": r["id"], "group": f"other:{r['author']}", "text": r["text"], "words": r["words"], "meta": {}})
    normalise = config.NORMALISE_TEXT and not a.raw
    if normalise:
        for r in rows:
            r["text"] = normalise_punct(r["text"])
        for r in src_by_id.values():
            r["text"] = normalise_punct(r["text"])
        old = os.path.join(rd, "scores.jsonl")
        if os.path.exists(old) and not os.path.exists(os.path.join(rd, "scores_raw.jsonl")):
            import shutil
            shutil.copy(old, os.path.join(rd, "scores_raw.jsonl"))
            for f in ("scores_summary.json", "geometry.json"):
                if os.path.exists(os.path.join(rd, f)):
                    shutil.copy(os.path.join(rd, f), os.path.join(rd, f.replace(".", "_raw.", 1)))
            log("raw-text scores backed up as scores_raw.jsonl")
    log(f"{len(rows)} rows: {collections.Counter(r['group'].split(':')[0] for r in rows)}; normalised={normalise}")
    feats = [dict() for _ in rows]

    import s1_features as S1  # overnight battery, by path

    # surface / syntax / degeneracy: the validated families
    bank_rows = [r for r in rows if r["group"] == "ref" or r["group"].startswith("other:")]
    for fam, fn in (("surface", lambda: S1.family_surface(rows)),
                    ("syntax", lambda: S1.family_syntax(rows, bank_rows)),
                    ("degen", lambda: S1.family_degen(rows))):
        try:
            log(f"family {fam}")
            for i, f in enumerate(fn()):
                feats[i].update(f)
        except Exception as e:
            log(f"  family {fam} FAILED: {e!r}")
            man.note(family=fam, error=repr(e))

    # SHOWN features and compliance distance against the quant targets
    for i, r in enumerate(rows):
        sf = shown_features(r["text"])
        for k in config.SHOWN_FEATURES:
            feats[i][f"shown_{k}"] = sf[k]
        if quant:
            zs = [abs(sf[k] - quant[k]) / (quant["sd"][k] + 1e-9) for k in config.SHOWN_FEATURES]
            feats[i]["shown_dist"] = float(st.mean(zs))

    # Delta
    try:
        log("family delta")
        for i, f in enumerate(delta_features(rows, S1.fw_profile, a.author)):
            feats[i].update(f)
    except Exception as e:
        log(f"  delta FAILED: {e!r}")
        man.note(family="delta", error=repr(e))

    # embeddings
    if not a.no_embed:
        import metrics3
        texts = [r["text"] for r in rows]
        for name, fn in (("luar", lambda t: metrics3.luar_embed(t).numpy()),
                         ("wegmann", lambda t: metrics3.style_embed(t).numpy()),
                         ("styledist", S1.styledistance_embed)):
            try:
                log(f"embedding {name} on {len(texts)} texts")
                E = np.asarray(fn(texts), dtype=np.float32)
                np.save(os.path.join(rd, f"emb_{name}.npy"), E)
                for i, f in enumerate(embed_features(rows, name, E, a.author, anchor_ids)):
                    feats[i].update(f)
            except Exception as e:
                log(f"  embedding {name} FAILED: {e!r}")
                man.note(family=name, error=repr(e))
        try:
            metrics3._M.clear()
        except Exception:
            pass

    # memorisation
    for i, r in enumerate(rows):
        if r["group"] == "gen" and r["id"] in src_by_id:
            feats[i].update(memo(r["text"], src_by_id[r["id"]]["text"]))

    # geometry on SEALED features
    geo = geometry(rows, feats, anchor_ids)
    log(f"geometry kept {len(geo['kept'])} features, dropped {geo['dropped']}")

    # detectors, optional
    if a.detect:
        try:
            log(f"detectors (observer {a.observer}, performer {a.performer})")
            lm = S1.family_lm(rows, obs_name=a.observer, perf_name=a.performer,
                              obs_4bit=a.obs_4bit, perf_4bit=a.perf_4bit)
            for i, f in enumerate(lm):
                feats[i].update(f)
        except Exception as e:
            log(f"  detectors FAILED: {e!r}")
            man.note(family="lm", error=repr(e))

    out = []
    for r, f in zip(rows, feats):
        if r.get("_anchor_only"):
            continue
        row = {k: r.get(k) for k in ("id", "group", "arm", "sample", "words", "len_ratio", "flags")}
        row.update(f)
        out.append(row)
    p = os.path.join(rd, "scores.jsonl")
    write_jsonl(p, out)
    man.output("scores", p)
    write_json(os.path.join(rd, "geometry.json"), geo)

    # quick per-arm means for the log
    keys = [config.PRIMARY, "geo_index", "luar_attrib", "delta_rank", "memo_flag", "shown_dist",
            "luar_cos_ref", "wegmann_cos_source", "styledist_cos_source"]
    summ = {}
    for arm in sorted({r["arm"] for r in out if r["group"] == "gen"}):
        rs = [r for r in out if r["group"] == "gen" and r["arm"] == arm]
        summ[arm] = {k: round(st.mean([r[k] for r in rs if r.get(k) is not None]), 4)
                     for k in keys if any(r.get(k) is not None for r in rs)}
        summ[arm]["n"] = len(rs)
    for grp in ("source", "ref"):
        rs = [r for r in out if r["group"] == grp]
        summ[grp] = {k: round(st.mean([r[k] for r in rs if r.get(k) is not None]), 4)
                     for k in ("luar_cos_ref", "luar_attrib", "delta_rank", "geo_index") if any(r.get(k) is not None for r in rs)}
    write_json(os.path.join(rd, "scores_summary.json"), summ)
    man.save(summary=summ, anchor_run=a.anchor_run or a.run, detect=a.detect, normalised=normalise)
    for k, v in summ.items():
        log(f"  {k}: {v}")
    log(f"-> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
