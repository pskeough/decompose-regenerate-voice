"""23_register_matched_pool -- a register-matched stranger pool built from the stored embeddings.

The pipeline scored every generated passage against one fixed reference pool: fourteen
period authors (austen, cather, chesterton, chopin, conrad, joyce, lovecraft, mansfield,
melville, sui_sin_far, watanna, wells, wharton, woolf, minus the run's own author when it
is one of them). Five contemporary authors and the private corpora were therefore anchored
against another century, which makes their "distance from strangers" partly a distance from
1900. This script rebuilds the anchors from the raw embedding matrices so that every author
can be positioned against a pool of its own register.

Blocks.

0. Alignment. Each run directory holds emb_luar.npy / emb_wegmann.npy / emb_styledist.npy
   whose rows are supposed to line up with scores.jsonl. They do not in most runs: s5_score
   inserts an anchor-run block of A0 generations between the run's own generations and the
   source rows, and drops that block again when it writes scores.jsonl. The script detects
   the block, repairs the index, and verifies the repair by reproducing the stored
   luar/wegmann/styledist cosine to the source and to the reference centroid from the
   embeddings themselves. It also checks that a given source passage gets a bit-identical
   embedding in every run of its author.

1. Banks. Per author, the embeddings of its own test passages (group source) and reference
   passages (group ref); plus the fourteen-author period pool from the group other:* rows.

2. The instrument. For author a and passage x, s_a(x) = mean cosine of x to a's source
   passages, excluding any passage that shares x's brief id (so a generation is never
   scored against the very passage its brief was written from). G = generations,
   H = the author's own source passages leave-one-out, P = a stranger pool measured the
   same way. Three pools: P_class (register-matched, same author class), P_13 (all twelve
   other study authors), P_period14 (the pipeline's fixed period pool, recomputed on this
   instrument so the two pools differ only in who is in them).

3. Positions, distributional fidelity, the author-region rate, and a thirteen-author
   attribution by nearest author.

Reads data/master, data/runs and analysis/15_instrument_agreement_and_fidelity only.
Writes analysis/23_register_matched_pool only.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *  # noqa: F401,F403

from scipy.stats import wasserstein_distance, binomtest, wilcoxon

T0 = time.time()
OUTD = outdir("23_register_matched_pool")
EMB = ["luar", "wegmann", "styledist"]
ARMS_USED = ["A0", "A5"]
NBOOT = 400
Z95 = 1.959963984540054

# patrick is the v1 chunking control: the same person as patrick_v2 on a different chunking,
# so it cannot sit in any stranger pool and it is not one of the thirteen study authors.
DROP_AUTHOR = "patrick"
STUDY = sorted([a for a in AUTHOR_CLASS if a != DROP_AUTHOR])
CLASS_OF = {a: AUTHOR_CLASS[a] for a in STUDY}
CLASS_MEMBERS = defaultdict(list)
for _a in STUDY:
    CLASS_MEMBERS[CLASS_OF[_a]].append(_a)

print(f"[23] {len(STUDY)} study authors; class sizes " +
      ", ".join(f"{c}={len(v)}" for c, v in sorted(CLASS_MEMBERS.items())), flush=True)


def unit(X):
    X = np.asarray(X, dtype=np.float64)
    n = np.linalg.norm(X, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return X / n


def wilson(k, n, z=Z95):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


# ---------------------------------------------------------------------------
# 0. runs to read
# ---------------------------------------------------------------------------
cells, runs_t, authors_t, briefs_t, refs_t = load_all()
gen_cells = cells[cells.arm.isin(ARMS_USED) & (~cells.replicate) & cells.author.isin(STUDY)].copy()
REPL_PAIRS = [("base4b", "base4b_r2"), ("chesterton_base4b", "chesterton_base4bc"),
              ("mansfield_base4b", "mansfield_base4b_r2"), ("chesterton_basem3b", "chesterton_basem3b_r2"),
              ("patrick_v2_basem3b", "patrick_v2_basem3b_r2")]
repl_runs = sorted({r for p in REPL_PAIRS for r in p})
run_list = sorted(set(gen_cells.run.unique()) | {r for r in repl_runs if r in set(cells.run.unique())})
print(f"[23] {len(gen_cells)} generated cells (arms {ARMS_USED}, non-replicate) over {gen_cells.run.nunique()} runs; "
      f"{len(run_list)} run directories to read (incl. replicate pairs for the floor)", flush=True)

RUNS_DIR = RUNS
SCORE_KEYS = {"luar": "luar_cos_source", "wegmann": "wegmann_cos_source", "styledist": "styledist_cos_source"}
REF_KEYS = {"luar": "luar_cos_ref", "wegmann": "wegmann_cos_ref", "styledist": "styledist_cos_ref"}

bank_src = {e: {} for e in EMB}     # author -> (ids, unit matrix)
bank_ref = {e: {} for e in EMB}
bank_oth = {e: {} for e in EMB}     # pool author -> (ids, unit matrix)
oth_union = {e: {} for e in EMB}    # pool author -> {id: unit vector}, union over runs
pool_sample_sizes = {}
identity = defaultdict(lambda: {"n_checked": 0, "n_runs": 0, "max_abs_diff": 0.0, "n_mismatch_rows": 0})

gen_store = {e: [] for e in EMB}    # list of matrices, run order
gen_index = []                      # (run, id, arm, sample) tuples aligned with the stacked matrix
align_rows = []

for run in run_list:
    rd = os.path.join(RUNS_DIR, run)
    sp, gp = os.path.join(rd, "scores.jsonl"), os.path.join(rd, "gens.jsonl")
    rec = {"run": run, "author": parse_run(run)["author"] if parse_run(run) else "", "n_scores": 0, "n_gens_file": 0,
           "n_npy": 0, "extra_anchor_rows": np.nan, "aligned": False}
    if not (os.path.exists(sp) and os.path.exists(gp)):
        rec["note"] = "scores.jsonl or gens.jsonl missing"
        align_rows.append(rec)
        continue
    with open(sp, encoding="utf-8-sig") as f:
        srows = [json.loads(l) for l in f if l.strip()]
    n_gen_file = sum(1 for l in open(gp, encoding="utf-8-sig") if l.strip())
    rec["n_scores"], rec["n_gens_file"] = len(srows), n_gen_file
    E = {}
    missing = [e for e in EMB if not os.path.exists(os.path.join(rd, f"emb_{e}.npy"))]
    if missing:
        rec["note"] = "missing npy: " + ",".join(missing)
        align_rows.append(rec)
        continue
    for e in EMB:
        E[e] = np.load(os.path.join(rd, f"emb_{e}.npy"))
    n_npy = E["luar"].shape[0]
    rec["n_npy"] = int(n_npy)
    if len({E[e].shape[0] for e in EMB}) != 1:
        rec["note"] = "the three npy files disagree on row count"
        align_rows.append(rec)
        continue
    extra = n_npy - len(srows)
    rec["extra_anchor_rows"] = int(extra)
    if extra < 0 or n_gen_file + extra > n_npy:
        rec["note"] = "npy shorter than scores.jsonl, or the anchor block does not fit"
        align_rows.append(rec)
        continue
    idx = np.concatenate([np.arange(n_gen_file), np.arange(n_gen_file + extra, n_npy)])
    if len(idx) != len(srows):
        rec["note"] = "repaired index does not match the score row count"
        align_rows.append(rec)
        continue
    U = {e: unit(E[e][idx]) for e in EMB}

    groups = np.array([r.get("group") or "" for r in srows])
    ids = np.array([r.get("id") for r in srows])
    is_gen = groups == "gen"
    src_pos = {ids[i]: i for i in np.where(groups == "source")[0]}
    ref_i = np.where(groups == "ref")[0]

    # verification: reproduce the stored cosines from the repaired index
    worst = {}
    for e in EMB:
        cen = U[e][ref_i].mean(axis=0)
        cen = cen / (np.linalg.norm(cen) or 1.0)
        err_s, err_r = [], []
        for i in np.where(is_gen)[0]:
            stored_s, stored_r = srows[i].get(SCORE_KEYS[e]), srows[i].get(REF_KEYS[e])
            j = src_pos.get(ids[i])
            if stored_s is not None and j is not None:
                err_s.append(abs(float(U[e][i] @ U[e][j]) - float(stored_s)))
            if stored_r is not None:
                err_r.append(abs(float(U[e][i] @ cen) - float(stored_r)))
        worst[e] = (max(err_s) if err_s else np.nan, max(err_r) if err_r else np.nan)
        rec[f"max_err_{e}_cos_source"] = worst[e][0]
        rec[f"max_err_{e}_cos_ref"] = worst[e][1]
    ok = all(not np.isfinite(v) or v < 1e-4 for pair in worst.values() for v in pair)
    rec["aligned"] = bool(ok)
    if not ok:
        rec["note"] = "repaired index still does not reproduce the stored cosines"
        align_rows.append(rec)
        continue

    au = parse_run(run)["author"]
    # banks + cross-run identity check. U[e] is the REPAIRED, unit-normalised matrix whose
    # rows line up with srows; indexing the raw npy here would reintroduce the anchor shift.
    other_groups = sorted({g for g in set(groups.tolist()) if g.startswith("other:")})
    for e in EMB:
        for grp_name, sel, store in (("source", np.where(groups == "source")[0], bank_src),
                                     ("ref", ref_i, bank_ref)):
            gi, gm = ids[sel], U[e][sel]
            key = au
            if key not in store[e]:
                store[e][key] = (gi, gm)
            else:
                old_ids, prev = store[e][key]
                st = identity[(e, grp_name)]
                st["n_runs"] += 1
                if list(old_ids) == list(gi):
                    st["n_checked"] += len(gi)
                    st["max_abs_diff"] = max(st["max_abs_diff"], float(np.abs(prev - gm).max()))
                    st["n_mismatch_rows"] += int((np.abs(prev - gm) > 1e-6).any(axis=1).sum())
                else:
                    st["n_mismatch_rows"] += len(gi)
        # the period pool is fixed in its authors but NOT in its passages: others.jsonl drew
        # its own sample of chunks per study author. The bank is therefore the union over
        # runs, deduplicated by id, so P_period14 does not depend on which run was read first.
        for g in other_groups:
            pool_au = g.split(":", 1)[1]
            sel = np.where(groups == g)[0]
            st = identity[(e, "other")]
            store = oth_union[e].setdefault(pool_au, {})
            for r_i, pid in zip(sel, ids[sel]):
                v = U[e][r_i]
                if pid in store:
                    st["n_checked"] += 1
                    d = float(np.abs(store[pid] - v).max())
                    st["max_abs_diff"] = max(st["max_abs_diff"], d)
                    st["n_mismatch_rows"] += int(d > 1e-6)
                else:
                    store[pid] = v
            st["n_runs"] += 1
            pool_sample_sizes[(pool_au, run)] = len(sel)

    # keep the generation rows we need
    want = set(zip(gen_cells[gen_cells.run == run].id, gen_cells[gen_cells.run == run].arm,
                   gen_cells[gen_cells.run == run]["sample"]))
    if run in repl_runs:
        want |= {(srows[i]["id"], srows[i]["arm"], srows[i]["sample"]) for i in np.where(is_gen)[0]
                 if srows[i].get("arm") == "A0"}
    keep = [i for i in np.where(is_gen)[0]
            if (srows[i]["id"], srows[i]["arm"], srows[i]["sample"]) in want]
    if keep:
        for e in EMB:
            gen_store[e].append(U[e][keep])
        gen_index += [(run, srows[i]["id"], srows[i]["arm"], int(srows[i]["sample"])) for i in keep]
    rec["n_gen_rows_kept"] = len(keep)
    align_rows.append(rec)
    del E, U

align = pd.DataFrame(align_rows)
write_table(align, os.path.join(OUTD, "alignment_check.csv"), floats=8)
n_ok = int(align.aligned.sum())
n_shifted = int((align.extra_anchor_rows.fillna(0) > 0).sum())
print(f"[23] alignment: {n_ok}/{len(align)} runs verified; {n_shifted} carried an anchor block "
      f"({time.time()-T0:.0f}s)", flush=True)

for e in EMB:
    for pool_au, store in oth_union[e].items():
        pids = sorted(store)
        bank_oth[e][pool_au] = (np.array(pids), np.vstack([store[p] for p in pids]))
del oth_union

GEN = {e: np.vstack(gen_store[e]) for e in EMB}
gidx = pd.DataFrame(gen_index, columns=["run", "id", "arm", "sample"])
del gen_store

# authors present in the banks
have = sorted(set(bank_src["luar"]) & set(STUDY))
missing_authors = [a for a in STUDY if a not in have]
POOL14 = sorted(bank_oth["luar"])
print(f"[23] banks: {len(have)} study authors, period pool has {len(POOL14)} authors "
      f"({sum(len(bank_oth['luar'][b][0]) for b in POOL14)} passages)", flush=True)

bank_rows = []
for a in have:
    bank_rows.append({"author": a, "author_class": CLASS_OF[a], "n_source": len(bank_src["luar"][a][0]),
                      "n_ref": len(bank_ref["luar"][a][0])})
bank_tab = pd.DataFrame(bank_rows)
ident_rows = [{"embedding": e, "group": g, "n_repeat_runs": v["n_runs"], "n_passages_checked": v["n_checked"],
               "n_rows_differing": v["n_mismatch_rows"], "max_abs_component_diff": v["max_abs_diff"]}
              for (e, g), v in sorted(identity.items())]
ident = pd.DataFrame(ident_rows)
ps = pd.DataFrame([{"pool_author": k[0], "run": k[1], "n_sampled": v} for k, v in pool_sample_sizes.items()])
pool_tab_counts = (ps.groupby("pool_author")
                   .agg(n_runs=("run", "nunique"), n_sampled_per_run_median=("n_sampled", "median")).reset_index())
pool_tab_counts["n_unique_passages_union"] = pool_tab_counts.pool_author.map(lambda b: len(bank_oth["luar"][b][0]))
write_table(pool_tab_counts, os.path.join(OUTD, "period_pool_composition.csv"), floats=1)
write_table(bank_tab, os.path.join(OUTD, "embedding_bank.csv"), floats=4)
write_table(ident, os.path.join(OUTD, "embedding_identity_across_runs.csv"), floats=10)


# ---------------------------------------------------------------------------
# 1. the instrument: mean cosine to an author's source set, same-brief excluded
# ---------------------------------------------------------------------------
def brief_of(pid):
    return pid


def s_to_author(Q, qids, e, a):
    """mean cosine of each row of Q to author a's source passages, excluding a source
    passage whose id equals the query's brief id."""
    aids, A = bank_src[e][a]
    sim = Q @ A.T
    if qids is not None:
        mask = np.ones_like(sim, dtype=bool)
        pos = {v: k for k, v in enumerate(aids)}
        for r, q in enumerate(qids):
            j = pos.get(q)
            if j is not None:
                mask[r, j] = False
        cnt = mask.sum(axis=1)
        return np.where(cnt > 0, (sim * mask).sum(axis=1) / np.maximum(cnt, 1), np.nan)
    return sim.mean(axis=1)


# H (author's own source passages, leave-one-out) and the pool distributions
Hdist = {e: {} for e in EMB}
Pset = {e: {} for e in EMB}          # (anchor author, pool name) -> pooled per-passage values
Pauth = {e: {} for e in EMB}         # (anchor author, other author) -> mean of that author's values
for e in EMB:
    for a in have:
        aids, A = bank_src[e][a]
        Hdist[e][a] = s_to_author(A, aids, e, a)
        for b in have:
            if b == a:
                continue
            bids, B = bank_src[e][b]
            Pauth[e][(a, b)] = s_to_author(B, None, e, a)
        for b in POOL14:
            if b == a:
                continue
            bids, B = bank_oth[e][b]
            Pauth[e][(a, "period14:" + b)] = s_to_author(B, None, e, a)

POOLS = ["P_class", "P_13", "P_period14"]


def pool_members(a, pool):
    if pool == "P_class":
        return [b for b in CLASS_MEMBERS[CLASS_OF[a]] if b != a and b in have]
    if pool == "P_13":
        return [b for b in have if b != a]
    return ["period14:" + b for b in POOL14 if b != a]


pool_rows = []
for e in EMB:
    for a in have:
        h = Hdist[e][a]
        pool_rows.append({"embedding": e, "anchor_author": a, "anchor_class": CLASS_OF[a], "other_author": a,
                          "other_class": CLASS_OF[a], "role": "H (own, leave-one-out)", "n_passages": len(h),
                          "mean_cosine": float(np.nanmean(h)), "sd": float(np.nanstd(h, ddof=1))})
        for b in have:
            if b == a:
                continue
            v = Pauth[e][(a, b)]
            pool_rows.append({"embedding": e, "anchor_author": a, "anchor_class": CLASS_OF[a], "other_author": b,
                              "other_class": CLASS_OF[b], "role": "study author", "n_passages": len(v),
                              "mean_cosine": float(v.mean()), "sd": float(v.std(ddof=1))})
        for b in POOL14:
            if b == a:
                continue
            v = Pauth[e][(a, "period14:" + b)]
            pool_rows.append({"embedding": e, "anchor_author": a, "anchor_class": CLASS_OF[a],
                              "other_author": b, "other_class": "period_pool", "role": "period-14 pool",
                              "n_passages": len(v), "mean_cosine": float(v.mean()), "sd": float(v.std(ddof=1))})
pool_tab = pd.DataFrame(pool_rows)
write_table(pool_tab, os.path.join(OUTD, "pool_pairwise_cosine.csv"), floats=5)

# per-passage instrument values for the authors' own passages and for every other author's
# passages measured against them: script 24 needs these to put the embedding instruments in
# the same region rule as the structure measures
own_rows = []
for a in have:
    for e in EMB:
        aids = bank_src[e][a][0]
        for pid, v in zip(aids, Hdist[e][a]):
            own_rows.append({"anchor_author": a, "passage_author": a, "id": pid, "role": "H",
                             "embedding": e, "value": float(v)})
        for b in have:
            if b == a:
                continue
            for pid, v in zip(bank_src[e][b][0], Pauth[e][(a, b)]):
                own_rows.append({"anchor_author": a, "passage_author": b, "id": pid, "role": "P",
                                 "embedding": e, "value": float(v)})
own_tab = pd.DataFrame(own_rows).pivot_table(index=["anchor_author", "passage_author", "id", "role"],
                                             columns="embedding", values="value").reset_index()
own_tab.columns.name = None
own_tab = own_tab.rename(columns={e: "s_" + e for e in EMB})
write_table(own_tab, os.path.join(OUTD, "author_passage_instrument_values.csv"), floats=5)

# scalar floors (author-balanced) and pooled distributions
Pscalar, Pdist = {}, {}
for e in EMB:
    for a in have:
        for pool in POOLS:
            mem = pool_members(a, pool)
            if not mem:
                continue
            per_author = [Pauth[e][(a, b)] for b in mem]
            Pscalar[(e, a, pool)] = float(np.mean([v.mean() for v in per_author]))
            Pdist[(e, a, pool)] = np.concatenate(per_author)

floor_gap = []
for e in EMB:
    for a in have:
        for pool in POOLS:
            if (e, a, pool) not in Pscalar:
                continue
            floor_gap.append({"embedding": e, "author": a, "author_class": CLASS_OF[a], "pool": pool,
                              "n_pool_authors": len(pool_members(a, pool)), "n_pool_passages": len(Pdist[(e, a, pool)]),
                              "mean_H": float(np.nanmean(Hdist[e][a])), "P": Pscalar[(e, a, pool)],
                              "separation_H_minus_P": float(np.nanmean(Hdist[e][a])) - Pscalar[(e, a, pool)]})
sep = pd.DataFrame(floor_gap)
write_table(sep, os.path.join(OUTD, "anchor_separation_by_pool.csv"), floats=5)
print(f"[23] anchors built ({time.time()-T0:.0f}s)", flush=True)

# ---------------------------------------------------------------------------
# 2. per-generation instrument values and the 13-author attribution
# ---------------------------------------------------------------------------
key = gidx.merge(cells[["run", "id", "arm", "sample", "author", "family", "params_b", "kind", "author_class", "replicate"]],
                 on=["run", "id", "arm", "sample"], how="left")
key["author"] = key.author.fillna(key.run.map(lambda r: (parse_run(r) or {}).get("author")))
for c, f in (("family", "family"), ("params_b", "params_b"), ("kind", "kind")):
    key[c] = key[c].where(key[c].notna(), key.run.map(lambda r: (parse_run(r) or {}).get(f)))
key["replicate"] = key.replicate.fillna(key.run.map(lambda r: bool((parse_run(r) or {}).get("replicate"))))

own_val = {}
attrib = {}
for e in EMB:
    Q = GEN[e]
    M = np.full((len(key), len(have)), np.nan)
    for j, b in enumerate(have):
        M[:, j] = s_to_author(Q, key.id.values, e, b)
    own = np.array([M[i, have.index(a)] if a in have else np.nan for i, a in enumerate(key.author.values)])
    own_val[e] = own
    nearest = np.array([have[j] for j in np.nanargmax(M, axis=1)])
    srt = np.sort(M, axis=1)
    attrib[e] = {"nearest": nearest, "margin": srt[:, -1] - srt[:, -2]}
    key[f"s_own_{e}"] = own
    key[f"nearest_{e}"] = nearest
    key[f"margin_{e}"] = attrib[e]["margin"]
    key[f"correct_{e}"] = (nearest == key.author.values).astype(int)
print(f"[23] generation instrument values computed ({time.time()-T0:.0f}s)", flush=True)

main = key[(~key.replicate.astype(bool)) & key.arm.isin(ARMS_USED)].copy()
write_table(main[["run", "author", "author_class", "family", "params_b", "kind", "arm", "sample", "id"] +
                 [c for c in main.columns if c.startswith(("s_own_", "nearest_", "margin_", "correct_"))]],
            os.path.join(OUTD, "generation_instrument_values.csv"), floats=5)

# replicate floor on this instrument
floor_rows = []
for e in EMB:
    for a, b in REPL_PAIRS:
        xa = key[(key.run == a) & (key.arm == "A0")][f"s_own_{e}"].dropna()
        xb = key[(key.run == b) & (key.arm == "A0")][f"s_own_{e}"].dropna()
        if len(xa) and len(xb):
            fam = "Ministral3" if "m3b" in a else "Qwen3"
            floor_rows.append({"embedding": e, "pair": f"{a} vs {b}", "family": fam,
                               "n": int(min(len(xa), len(xb))), "abs_mean_diff": float(abs(xa.mean() - xb.mean()))})
floors = pd.DataFrame(floor_rows)
write_table(floors, os.path.join(OUTD, "replicate_floors_instrument.csv"), floats=5)
FLOOR = {e: (float(floors[floors.embedding == e].abs_mean_diff.max()) if len(floors[floors.embedding == e]) else np.nan)
         for e in EMB}

# ---------------------------------------------------------------------------
# 3. positions and distributional fidelity per configuration
# ---------------------------------------------------------------------------
CFG = ["author", "family", "params_b", "kind", "arm"]
rng = np.random.default_rng(0)
pos_rows, fid_rows = [], []
for (a, fam, pb, kind, arm), g in main.groupby(CFG, dropna=False):
    if a not in have:
        continue
    for e in EMB:
        gv = g[f"s_own_{e}"].values.astype(float)
        gids = g.id.values
        ok = np.isfinite(gv)
        gv, gids = gv[ok], gids[ok]
        if len(gv) < 5:
            continue
        H = Hdist[e][a][np.isfinite(Hdist[e][a])]
        meanH = float(H.mean())
        # brief clusters
        uniq = pd.unique(gids)
        groups_idx = [np.where(gids == u)[0] for u in uniq]
        boots_mean, boots_w1 = [], []
        for _ in range(NBOOT):
            pick = rng.integers(0, len(groups_idx), size=len(groups_idx))
            star = np.concatenate([groups_idx[i] for i in pick])
            gs = gv[star]
            boots_mean.append(gs.mean())
            boots_w1.append(wasserstein_distance(gs, H))
        boots_mean = np.array(boots_mean); boots_w1 = np.array(boots_w1)
        w1_gh = wasserstein_distance(gv, H)
        for pool in POOLS:
            if (e, a, pool) not in Pscalar:
                continue
            P = Pscalar[(e, a, pool)]
            Pv = Pdist[(e, a, pool)]
            w1_ph = wasserstein_distance(Pv, H)
            denom = meanH - P
            pos = (gv.mean() - P) / denom if denom != 0 else np.nan
            bp = (boots_mean - P) / denom if denom != 0 else np.full(NBOOT, np.nan)
            F = 1 - w1_gh / w1_ph if w1_ph > 0 else np.nan
            bf = 1 - boots_w1 / w1_ph if w1_ph > 0 else np.full(NBOOT, np.nan)
            base = {"author": a, "author_class": CLASS_OF[a], "family": fam, "params_b": pb, "kind": kind,
                    "arm": arm, "embedding": e, "pool": pool, "n_G": int(len(gv)), "n_briefs": int(len(uniq)),
                    "n_H": int(len(H)), "n_P": int(len(Pv)), "n_pool_authors": len(pool_members(a, pool))}
            pos_rows.append({**base, "mean_G": float(gv.mean()), "mean_H": meanH, "P": P,
                             "separation": denom, "pos": pos,
                             "pos_lo": float(np.nanquantile(bp, 0.025)), "pos_hi": float(np.nanquantile(bp, 0.975)),
                             "instrument_floor": FLOOR[e]})
            fid_rows.append({**base, "F": F, "F_lo": float(np.nanquantile(bf, 0.025)),
                             "F_hi": float(np.nanquantile(bf, 0.975)), "W1_G_H": w1_gh, "W1_P_H": w1_ph,
                             "separation": denom, "instrument_floor": FLOOR[e]})
positions = pd.DataFrame(pos_rows)
fidelity = pd.DataFrame(fid_rows)
# a position is a ratio of two means: where the two anchors sit closer together than twice
# the instrument's replicate floor it is a ratio of two noise terms (script 15's rule)
for t in (positions, fidelity):
    t["abs_separation"] = t.separation.abs()
    t["separation_over_floor"] = t.abs_separation / t.instrument_floor
    t["anchor_usable"] = t.separation_over_floor >= 2.0
write_table(positions, os.path.join(OUTD, "positions_register_matched.csv"), floats=5)
write_table(fidelity, os.path.join(OUTD, "fidelity_register_matched.csv"), floats=5)
print(f"[23] positions and F for {positions.groupby(CFG).ngroups} configurations ({time.time()-T0:.0f}s)", flush=True)

# ---------------------------------------------------------------------------
# 4. the author-region rate on the two register-matched embedding instruments
# ---------------------------------------------------------------------------
REG_INST = ["luar", "wegmann"]
bounds = {}
for e in REG_INST:
    for a in have:
        H = Hdist[e][a][np.isfinite(Hdist[e][a])]
        bounds[(e, a)] = (float(np.quantile(H, 0.05)), float(np.quantile(H, 0.95)))

reg_rows = []
for (a, fam, pb, kind, arm), g in main.groupby(CFG, dropna=False):
    if a not in have:
        continue
    inside = np.ones(len(g), dtype=bool)
    for e in REG_INST:
        lo, hi = bounds[(e, a)]
        v = g[f"s_own_{e}"].values.astype(float)
        inside &= np.isfinite(v) & (v >= lo) & (v <= hi)
    n, k = len(g), int(inside.sum())
    R, Rlo, Rhi = wilson(k, n)
    bydf = pd.DataFrame({"id": g.id.values, "in": inside})
    per_brief = bydf.groupby("id")["in"].max()
    n2, k2 = len(per_brief), int(per_brief.sum())
    R2, R2lo, R2hi = wilson(k2, n2)
    # the author's own passages and the register-matched strangers on the same rule
    own_in = np.ones(len(Hdist[REG_INST[0]][a]), dtype=bool)
    for e in REG_INST:
        lo, hi = bounds[(e, a)]
        v = Hdist[e][a]
        own_in &= np.isfinite(v) & (v >= lo) & (v <= hi)
    mem = pool_members(a, "P_class")
    if mem:
        str_in = np.ones(len(Pdist[(REG_INST[0], a, "P_class")]), dtype=bool)
        for e in REG_INST:
            lo, hi = bounds[(e, a)]
            v = Pdist[(e, a, "P_class")]
            str_in &= np.isfinite(v) & (v >= lo) & (v <= hi)
        stranger_rate = float(str_in.mean())
    else:
        stranger_rate = np.nan
    reg_rows.append({"author": a, "author_class": CLASS_OF[a], "family": fam, "params_b": pb, "kind": kind,
                     "arm": arm, "instruments": ",".join(REG_INST), "n_passages": n, "n_inside": k,
                     "R": R, "R_lo": Rlo, "R_hi": Rhi, "n_briefs": n2, "n_briefs_inside": k2,
                     "R_at_2": R2, "R2_lo": R2lo, "R2_hi": R2hi,
                     "R_ceiling_author_own": float(own_in.mean()),
                     "R_floor_register_matched_strangers": stranger_rate,
                     **{f"lo_{e}": bounds[(e, a)][0] for e in REG_INST},
                     **{f"hi_{e}": bounds[(e, a)][1] for e in REG_INST}})
region = pd.DataFrame(reg_rows)
write_table(region, os.path.join(OUTD, "author_region_rate.csv"), floats=5)
region_summary = (region.groupby(["family", "params_b", "kind", "arm"])
                  .agg(n_configs=("R", "size"), n_authors=("author", "nunique"), mean_R=("R", "mean"),
                       median_R=("R", "median"), mean_R_at_2=("R_at_2", "mean"),
                       mean_ceiling=("R_ceiling_author_own", "mean"),
                       mean_stranger_floor=("R_floor_register_matched_strangers", "mean")).reset_index())
write_table(region_summary, os.path.join(OUTD, "author_region_summary.csv"), floats=4)

# ---------------------------------------------------------------------------
# 5. attribution
# ---------------------------------------------------------------------------
acc_rows, conf_rows = [], []
CHANCE = 1.0 / len(have)
for (a, fam, pb, kind, arm), g in main.groupby(CFG, dropna=False):
    if a not in have:
        continue
    for e in EMB:
        n = int(g[f"correct_{e}"].notna().sum())
        k = int(g[f"correct_{e}"].sum())
        p, lo, hi = wilson(k, n)
        pv = binomtest(k, n, CHANCE, alternative="greater").pvalue if n else np.nan
        top_wrong = g[g[f"correct_{e}"] == 0][f"nearest_{e}"].value_counts()
        acc_rows.append({"author": a, "author_class": CLASS_OF[a], "family": fam, "params_b": pb, "kind": kind,
                         "arm": arm, "embedding": e, "n": n, "n_correct": k, "accuracy": p,
                         "wilson_low": lo, "wilson_high": hi, "chance": CHANCE,
                         "mean_margin": float(g[f"margin_{e}"].mean()),
                         "top_confusion": (top_wrong.index[0] if len(top_wrong) else ""),
                         "top_confusion_n": (int(top_wrong.iloc[0]) if len(top_wrong) else 0), "p": pv})
for (fam, pb, kind, arm), g in main.groupby(["family", "params_b", "kind", "arm"], dropna=False):
    for e in EMB:
        vc = g.groupby(["author", f"nearest_{e}"]).size().reset_index(name="n")
        for _, r in vc.iterrows():
            conf_rows.append({"family": fam, "params_b": pb, "kind": kind, "arm": arm, "embedding": e,
                              "true_author": r["author"], "predicted_author": r[f"nearest_{e}"], "n": int(r["n"])})
acc = pd.DataFrame(acc_rows)
acc["q"] = bh_fdr(acc.p.values)
# which authors the instrument reaches for regardless of who the passage was written for
attr_rows = []
for (fam, pb, kind, arm), g in main.groupby(["family", "params_b", "kind", "arm"], dropna=False):
    for e in EMB:
        n = len(g)
        vc = g[f"nearest_{e}"].value_counts()
        for b in have:
            attr_rows.append({"embedding": e, "family": fam, "params_b": pb, "kind": kind, "arm": arm,
                              "predicted_author": b, "author_class": CLASS_OF[b],
                              "n_predicted": int(vc.get(b, 0)), "share_predicted": float(vc.get(b, 0)) / n,
                              "share_expected_if_flat": 1.0 / len(have),
                              "mean_within_author_cosine_H": float(np.nanmean(Hdist[e][b])),
                              "n_bank_passages": len(bank_src[e][b][0])})
attractors = pd.DataFrame(attr_rows)
write_table(attractors, os.path.join(OUTD, "attribution_attractors.csv"), floats=4)
attractor_top = (attractors[attractors.arm == "A0"].groupby(["embedding", "predicted_author"])
                 .agg(mean_share=("share_predicted", "mean"),
                      mean_within_author_cosine_H=("mean_within_author_cosine_H", "first"),
                      n_bank_passages=("n_bank_passages", "first")).reset_index()
                 .sort_values(["embedding", "mean_share"], ascending=[True, False]))
write_table(attractor_top, os.path.join(OUTD, "attribution_attractors_summary.csv"), floats=4)
write_table(acc, os.path.join(OUTD, "attribution_accuracy.csv"), floats=5)
conf = pd.DataFrame(conf_rows)
write_table(conf, os.path.join(OUTD, "attribution_confusion.csv"), floats=0)
acc_summary = (acc.groupby(["embedding", "family", "params_b", "kind", "arm"])
               .apply(lambda x: pd.Series({"n_authors": x.author.nunique(), "n_passages": int(x.n.sum()),
                                           "pooled_accuracy": x.n_correct.sum() / max(x.n.sum(), 1),
                                           "n_authors_above_chance_q05": int(((x.q < 0.05) & (x.accuracy > CHANCE)).sum())}),
                      include_groups=False).reset_index())
for i, r in acc_summary.iterrows():
    p, lo, hi = wilson(int(round(r.pooled_accuracy * r.n_passages)), int(r.n_passages))
    acc_summary.loc[i, "wilson_low"], acc_summary.loc[i, "wilson_high"] = lo, hi
write_table(acc_summary, os.path.join(OUTD, "attribution_accuracy_summary.csv"), floats=4)

# ---------------------------------------------------------------------------
# 6. period-anchored vs register-matched, contemporary and private authors
# ---------------------------------------------------------------------------
cmp_rows = []
p15 = os.path.join(OUT, "15_instrument_agreement_and_fidelity", "positions_by_configuration.csv")
per15 = pd.read_csv(p15) if os.path.exists(p15) else pd.DataFrame()
MEAS15 = {"luar": "luar_cos_ref", "wegmann": "wegmann_cos_ref", "styledist": "styledist_cos_ref"}
wide = positions[positions.arm == "A0"].pivot_table(
    index=["author", "author_class", "family", "params_b", "kind", "embedding"], columns="pool",
    values=["pos", "P", "mean_G", "mean_H"]).reset_index()
wide.columns = ["_".join([c for c in col if c]).strip("_") for col in wide.columns.values]
for _, r in wide.iterrows():
    row = {"author": r["author"], "author_class": r["author_class"], "family": r["family"],
           "params_b": r["params_b"], "kind": r["kind"], "embedding": r["embedding"],
           "pos_P_class": r.get("pos_P_class"), "pos_P_13": r.get("pos_P_13"),
           "pos_P_period14": r.get("pos_P_period14"),
           "P_class": r.get("P_P_class"), "P_period14": r.get("P_P_period14"),
           "mean_H": r.get("mean_H_P_class"), "mean_G": r.get("mean_G_P_class")}
    row["pos_class_minus_period"] = (row["pos_P_class"] - row["pos_P_period14"]
                                     if pd.notna(row["pos_P_class"]) and pd.notna(row["pos_P_period14"]) else np.nan)
    if len(per15):
        m = per15[(per15.author == r["author"]) & (per15.family == r["family"]) &
                  (np.isclose(per15.params_b, float(r["params_b"]))) & (per15.kind == r["kind"]) &
                  (per15.measure == MEAS15[r["embedding"]])]
        row["pos_script15_period_pool"] = float(m.pos.iloc[0]) if len(m) else np.nan
        row["script15_anchor_below_floor"] = bool(m.anchor_below_floor.iloc[0]) if len(m) else None
    cmp_rows.append(row)
cmp = pd.DataFrame(cmp_rows)
write_table(cmp, os.path.join(OUTD, "pool_comparison_positions.csv"), floats=4)
cmp_nonperiod = cmp[cmp.author_class.isin(["contemporary", "private"])]
write_table(cmp_nonperiod, os.path.join(OUTD, "pool_comparison_nonperiod.csv"), floats=4)

# author-level test: does the pool change the position, per class and embedding
test_rows = []
for e in EMB:
    for cl in ["period", "contemporary", "private"]:
        sub = cmp[(cmp.embedding == e) & (cmp.author_class == cl)].dropna(subset=["pos_P_class", "pos_P_period14"])
        if not len(sub):
            continue
        byau = sub.groupby("author")[["pos_P_class", "pos_P_period14"]].mean()
        diff = (byau.pos_P_class - byau.pos_P_period14).values
        pt, lo, hi = bootstrap_ci(diff, n=2000, seed=1)
        try:
            pv = wilcoxon(byau.pos_P_class.values, byau.pos_P_period14.values).pvalue if len(byau) >= 5 else np.nan
        except Exception:
            pv = np.nan
        test_rows.append({"embedding": e, "author_class": cl, "n_authors": len(byau),
                          "mean_pos_register_matched": float(byau.pos_P_class.mean()),
                          "mean_pos_period_pool": float(byau.pos_P_period14.mean()),
                          "mean_difference": pt, "ci_low": lo, "ci_high": hi, "p": pv})
pooltest = pd.DataFrame(test_rows)
if len(pooltest):
    pooltest["q"] = bh_fdr(pooltest.p.values)
write_table(pooltest, os.path.join(OUTD, "pool_effect_tests.csv"), floats=4)

# ---------------------------------------------------------------------------
# 7. figures
# ---------------------------------------------------------------------------
figs = []
sub = positions[(positions.arm == "A0") & (positions.embedding == "luar") &
                positions.pool.isin(["P_class", "P_period14"])]
YLO, YHI = -3.0, 2.0
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
for ax, kind in zip(axes, ["base", "adapter"]):
    s = sub[sub.kind == kind]
    order = [a for cl in ["period", "contemporary", "private"] for a in sorted(CLASS_MEMBERS[cl]) if a in have]
    x = np.arange(len(order))
    for pool, off, mk, col in (("P_period14", -0.14, "o", "#7a7a7a"), ("P_class", 0.14, "s", "#1f77b4")):
        m = s[s.pool == pool].groupby("author").pos.mean().reindex(order)
        v = m.values.astype(float)
        out = np.isfinite(v) & ((v < YLO) | (v > YHI))
        ax.plot(x[~out] + off, np.clip(v[~out], YLO, YHI), mk, color=col,
                label=("period-14 pool" if pool == "P_period14" else "register-matched pool"))
        ax.plot(x[out] + off, np.clip(v[out], YLO + 0.08, YHI - 0.08), "v", color=col, ms=7, mfc="none")
    ax.set_ylim(YLO, YHI)
    ax.axhline(1.0, color="k", lw=0.8, ls=":")
    ax.axhline(0.0, color="k", lw=0.8, ls="-")
    b = 0
    for cl in ["period", "contemporary", "private"]:
        b += len([a for a in sorted(CLASS_MEMBERS[cl]) if a in have])
        if b < len(order):
            ax.axvline(b - 0.5, color="0.85", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=60, ha="right", fontsize=8)
    ax.set_title(f"{kind}, arm A0")
    ax.set_xlabel("author (period | contemporary | private)")
axes[0].set_ylabel("position on LUAR mean cosine to the author's own passages\n(0 = stranger pool, 1 = author's held-out prose)")
axes[0].legend(fontsize=8, loc="lower left")
fig.suptitle("Positions under the pipeline's period pool and a register-matched pool (LUAR).\n"
             "Open triangles are clipped to the axis: the two anchors are too close to divide by.", fontsize=11)
figs.append(("Positions by author class under the two pools",
             savefig(fig, os.path.join(OUTD, "positions_by_class_pools.png"))))

fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
for ax, e in zip(axes, EMB):
    s = positions[(positions.arm == "A0") & (positions.embedding == e) & positions.pool.isin(["P_class", "P_period14"])]
    data, labs = [], []
    for cl in ["period", "contemporary", "private"]:
        for pool in ["P_period14", "P_class"]:
            v = s[(s.author_class == cl) & (s.pool == pool)].groupby("author").pos.mean().dropna().values
            data.append(v); labs.append(f"{cl[:4]}\n{'per14' if pool=='P_period14' else 'match'}")
    ax.boxplot([np.clip(v, -3.0, 2.0) for v in data], tick_labels=labs, showmeans=True)
    ax.set_ylim(-3.2, 2.2)
    ax.axhline(1.0, color="k", lw=0.8, ls=":"); ax.axhline(0.0, color="k", lw=0.8)
    ax.set_title(e)
    ax.tick_params(axis="x", labelsize=7)
axes[0].set_ylabel("position (author is the unit)")
fig.suptitle("Position by author class and stranger pool, arm A0, all configurations.\n"
             "Values are clipped to [-3, 2]; per14 = the pipeline's period pool, match = register-matched.",
             fontsize=11)
figs.append(("Position by class and pool, three embeddings",
             savefig(fig, os.path.join(OUTD, "positions_by_class_boxplot.png"))))

for fam in sorted(main.family.dropna().unique()):
    sizes = sorted(main[main.family == fam].params_b.dropna().unique())
    pb = sizes[-1]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
    for ax, kind in zip(axes, ["base", "adapter"]):
        c = conf[(conf.family == fam) & (np.isclose(conf.params_b, pb)) & (conf.kind == kind) &
                 (conf.arm == "A0") & (conf.embedding == "luar")]
        rows_ = sorted(c.true_author.unique())
        cols_ = have
        M = np.zeros((len(rows_), len(cols_)))
        for _, r in c.iterrows():
            M[rows_.index(r.true_author), cols_.index(r.predicted_author)] = r.n
        Mn = M / np.maximum(M.sum(axis=1, keepdims=True), 1)
        im = ax.imshow(Mn, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(len(cols_))); ax.set_xticklabels(cols_, rotation=70, ha="right", fontsize=7)
        ax.set_yticks(range(len(rows_))); ax.set_yticklabels(rows_, fontsize=7)
        ax.set_title(f"{fam} {pb:g}B {kind}, arm A0, LUAR")
        ax.set_xlabel("nearest of the 13 study authors")
        for i in range(len(rows_)):
            for j in range(len(cols_)):
                if Mn[i, j] >= 0.10:
                    ax.text(j, i, f"{Mn[i, j]:.2f}", ha="center", va="center", fontsize=6,
                            color="white" if Mn[i, j] > 0.55 else "black")
    axes[0].set_ylabel("author the passage was written for")
    fig.colorbar(im, ax=axes, shrink=0.8, label="share of the row")
    figs.append((f"Confusion matrix, {fam} {pb:g}B, arm A0",
                 savefig(fig, os.path.join(OUTD, f"confusion_{fam}.png"))))

# ---------------------------------------------------------------------------
# 8. README
# ---------------------------------------------------------------------------
n_runs_read = int(align.aligned.sum())
n_gen_used = int(len(main))
ident_bad = int(ident.n_rows_differing.sum()) if len(ident) else 0
ident_checked = int(ident.n_passages_checked.sum()) if len(ident) else 0

pooled_shift = pooltest.set_index(["embedding", "author_class"]) if len(pooltest) else pd.DataFrame()
head_tab = positions[(positions.arm == "A0") & (positions.kind == "adapter") & (positions.embedding == "luar")]
by_class_pool = (positions[positions.arm == "A0"].groupby(["embedding", "pool", "author_class", "kind"])
                 .agg(n=("pos", "size"), share_anchor_usable=("anchor_usable", "mean"),
                      median_separation_over_floor=("separation_over_floor", "median"),
                      median_pos=("pos", "median"),
                      median_pos_usable_only=("pos", lambda s: np.nan)).reset_index())
usable_med = (positions[(positions.arm == "A0") & positions.anchor_usable]
              .groupby(["embedding", "pool", "author_class", "kind"]).pos.median()
              .rename("median_pos_usable_only").reset_index())
by_class_pool = by_class_pool.drop(columns=["median_pos_usable_only"]).merge(
    usable_med, on=["embedding", "pool", "author_class", "kind"], how="left")
write_table(by_class_pool, os.path.join(OUTD, "median_position_by_class_pool.csv"), floats=4)
fid_class_pool = (fidelity[fidelity.arm == "A0"].groupby(["embedding", "pool", "author_class", "kind"])
                  .agg(n=("F", "size"), share_anchor_usable=("anchor_usable", "mean"),
                       median_F=("F", "median")).reset_index())
fid_usable = (fidelity[(fidelity.arm == "A0") & fidelity.anchor_usable]
              .groupby(["embedding", "pool", "author_class", "kind"]).F.median()
              .rename("median_F_usable_only").reset_index())
fid_class_pool = fid_class_pool.merge(fid_usable, on=["embedding", "pool", "author_class", "kind"], how="left")
write_table(fid_class_pool, os.path.join(OUTD, "median_fidelity_by_class_pool.csv"), floats=4)

reg_top = region_summary.sort_values("mean_R", ascending=False)
acc_top = acc_summary.sort_values("pooled_accuracy", ascending=False)

usable_class = float(positions[positions.pool == "P_class"].anchor_usable.mean())
usable_period = float(positions[positions.pool == "P_period14"].anchor_usable.mean())
nonper = cmp_nonperiod.dropna(subset=["pos_P_class", "pos_P_period14"])
shift_med = float((nonper.pos_P_class - nonper.pos_P_period14).median()) if len(nonper) else float("nan")
per_only = cmp[(cmp.author_class == "period")].dropna(subset=["pos_P_class", "pos_P_period14"])
shift_med_per = float((per_only.pos_P_class - per_only.pos_P_period14).median()) if len(per_only) else float("nan")

n_pool_min = int(pool_tab_counts.n_sampled_per_run_median.min())
n_pool_max = int(pool_tab_counts.n_sampled_per_run_median.max())
n_union_min = int(pool_tab_counts.n_unique_passages_union.min())
n_union_max = int(pool_tab_counts.n_unique_passages_union.max())
n_src_min, n_src_max = int(bank_tab.n_source.min()), int(bank_tab.n_source.max())
n_ref_min, n_ref_max = int(bank_tab.n_ref.min()), int(bank_tab.n_ref.max())
thin_author = bank_tab.sort_values("n_source").iloc[0]
usable_by_class = positions[positions.pool == "P_class"].groupby("author_class").anchor_usable.mean()
usable_class_txt = "; ".join(f"{c} {100*float(v):.0f} per cent usable" for c, v in usable_by_class.sort_values().items())
shift_by_class = {c: float(g.pos_P_class.sub(g.pos_P_period14).median())
                  for c, g in nonper.groupby("author_class")}
shift_class_txt = "; ".join(f"{c} {v:+.3f}" for c, v in sorted(shift_by_class.items()))
trunc_flagged_used = sorted(runs_t[(runs_t.truncation_gate_ok == False) & runs_t.run.isin(main.run.unique())].run)  # noqa: E712

what = f"""
The study's stranger pool was fixed: {len(POOL14)} period authors, the same pool for a Cory
Doctorow generation as for a Wharton one. Any position or fidelity number computed against
it mixes "not this author" with "not of this century" for the
{len(CLASS_MEMBERS['contemporary'])} contemporary and the {len(CLASS_MEMBERS['private'])}
private corpora. This script rebuilds the pool from the stored embedding matrices so that
each author can be anchored against authors of its own register, and reports what changes.

It covers {n_gen_used} generated passages (arms {', '.join(ARMS_USED)}, non-replicate) over
{main.run.nunique()} runs and {len(have)} study authors, on all three style embeddings.
`patrick` (the v1 chunking control) is excluded: it is the same person as `patrick_v2` on a
different chunking, so it cannot be a stranger to anyone and it is not one of the thirteen.
The private class therefore contains two authors, `patrick_v2` and `h_private`, and a
register-matched pool for one of them is the single other one; that is the weakest pool in
the table and every private row should be read with it in mind.
"""

how = f"""
**Alignment (the first thing that had to be fixed).** `emb_*.npy` is *not* row-aligned with
`scores.jsonl` in most runs. `dr/s5_score.py` appends the anchor run's A0 generations to the
row list before the source, ref and other-author rows, embeds all of them, and then drops
the anchor rows when it writes `scores.jsonl`. The npy therefore carries an extra block of
`len(npy) - len(scores)` rows sitting between the run's own generations and its source rows.
{n_shifted} of the {len(align)} run directories read here carry such a block. The repair is
to take npy rows `[0, n_gens)` and `[n_gens + extra, end)`, where `n_gens` is the line count
of `gens.jsonl`. The repair is verified per run by recomputing the stored
`luar/wegmann/styledist_cos_source` (cosine to the passage's own source row) and `*_cos_ref`
(cosine to the unit-normalised mean of the unit reference vectors) from the embeddings:
{n_ok} of {len(align)} runs reproduce every stored value to better than 1e-4
(`alignment_check.csv`). Without the repair the reference and other-author rows are
mislabelled in those runs and every cross-author cosine is wrong.

**Embedding identity across runs.** After the repair, a given passage's embedding is
bit-identical in every run that scored it: {ident_bad} of {ident_checked} repeated passage
embeddings differ by more than 1e-6 on any component, across source, ref and other-author
rows and all three embeddings (`embedding_identity_across_runs.csv`). That is what makes one
bank per author legitimate. Running the same check against the unrepaired index is how the
anchor block was found: in a run that carries a block, row-for-row indexing hands every
source, ref and other-author row the vector of a different passage, and the same passage
then appears to have a different embedding in different runs.

**Banks.** Per author, the group `source` rows (its held-out test passages) and the group
`ref` rows (`embedding_bank.csv`); plus the {len(POOL14)}-author period pool from the
`other:*` rows. That pool is fixed in its *authors* but not in its *passages*:
`others.jsonl` drew its own sample for each study author, with a per-run median of
{n_pool_min} to {n_pool_max} chunks per pool author, while the union over every run runs from
{n_union_min} to {n_union_max} chunks for the same authors (`period_pool_composition.csv`).
A union that much larger than any single run's sample is what says the pool passages differ
from run to run. The bank here is that union, deduplicated by id:
{sum(len(bank_oth['luar'][b][0]) for b in POOL14)} passages over {len(POOL14)} pool authors,
so P_period14 does not depend on which run happened to be read first.

**The instrument.** For author *a* and passage *x*, s_a(x) = the mean cosine of *x* to *a*'s
source passages, excluding any source passage whose id equals *x*'s brief id. For a
generation that removes the one passage its brief was written from, which is the content
inflation `FIDELITY_SYNTHESIS` fact 5 names; for one of *a*'s own passages it is
leave-one-out. This is a mean cosine, not a cosine to a centroid, so it differs by
construction from the pipeline's `*_cos_ref` column.

- **G** = the configuration's generations, **H** = *a*'s own source passages leave-one-out.
- **P_class** = the same-class study authors' source passages ({', '.join(f'{c}: {len(v)} authors' for c, v in sorted(CLASS_MEMBERS.items()))}).
- **P_13** = all {len(have) - 1} other study authors.
- **P_period14** = the pipeline's fixed period pool, recomputed on this same instrument, so
  the register-matched and period-anchored numbers differ only in who is in the pool.

The scalar floor P is the mean over the pool's authors of each author's mean (so authors are
weighted equally); the distribution used for W1 is the pooled per-passage values.

**Positions and fidelity.** pos = (mean G - P) / (mean H - P);
F = 1 - W1(G, H) / W1(P, H) with `scipy.stats.wasserstein_distance`. Intervals are a
{NBOOT}-resample bootstrap over brief clusters within the configuration; the anchors H and P
are held fixed, so the intervals describe the generation sample, not the anchors.

**Floors.** `replicate_floors_instrument.csv` recomputes the replicate floor for this
instrument on the twice-generated base pairs: {', '.join(f'{e} {FLOOR[e]:.4f}' for e in EMB)}
(largest absolute mean difference over the pairs, both families pooled).

**Region rate.** R is the share of generated passages inside the central 90% interval of H
on *both* register-matched embedding instruments at once (LUAR and Wegmann); R@2 is the share
of briefs with at least one of the two samples inside. The author's own passages give the
ceiling (0.90 on one instrument, less on two) and the register-matched strangers give the
floor, both in the same table.

**Attribution.** The predicted author is the argmax over the {len(have)} study authors of
s_b(g), with the same-brief exclusion applied to the true author's bank so the content of the
brief cannot carry the attribution. Chance is 1/{len(have)} = {CHANCE:.3f}. Wilson intervals
on the rate; one-sided binomial against chance, BH-FDR across the
{len(acc)} configuration-by-embedding tests in `attribution_accuracy.csv`.

**Correction.** BH-FDR is applied within each family of tests separately and each README
number says which family it belongs to: {len(acc)} attribution tests in
`attribution_accuracy.csv`, and {len(pooltest)} pool-effect tests in `pool_effect_tests.csv`.
A q below 0.05 means survival inside that one family. The programme-wide correction in script
22 is a second and stricter layer, and nothing in this folder has been through it.
"""

reading = f"""
The unit for any claim about a pool is the author: `pool_effect_tests.csv` aggregates each
author to one number before testing, and with {len(CLASS_MEMBERS['contemporary'])}
contemporary and {len(CLASS_MEMBERS['private'])} private authors those intervals are wide by
construction. Nothing here is a claim about a model.

What the pool change does is arithmetic. Where a register-matched pool sits closer to the
author than a pool from another century, the denominator (mean H - P) shrinks and the same
generation moves further from 1. The median position shift from the period pool to the
register-matched pool is {shift_med:+.3f} over the contemporary and private rows together and
{shift_med_per:+.3f} over the period rows. The direction is not uniform, and the class-by-
embedding medians are the ones to read rather than the pooled figure: {shift_class_txt} (over
all three embeddings; `pool_comparison_nonperiod.csv` carries every row). Where the shift is
negative, a position that looked close to the author's own prose against period strangers is
consistent with register rather than with voice, and the size of that share is the difference
between the two position columns of that table. Where it is positive the period pool was the
harsher anchor, and the register-matched number is the smaller claim.

Matching the register costs anchor separation, which is the reason to read the separation
column before the position column. Moving the pool closer to the author shrinks the gap
between the two anchors, and a position is a ratio with that gap in the denominator. On the
usability rule script 15 used (the anchors must be at least twice the instrument's replicate
floor apart), {100*(1-usable_class):.0f} per cent of the register-matched rows fail against
{100*(1-usable_period):.0f} per cent of the period-pool rows. The failures are not confined to
one class: over all three embeddings the register-matched usable share is
{usable_class_txt}. The period same-class pool is {len(CLASS_MEMBERS['period'])} writers and
the contemporary one {len(CLASS_MEMBERS['contemporary'])}, and both are small enough to sit
close to the author on these instruments. `median_position_by_class_pool.csv` therefore
carries the median over all rows and over the usable rows separately, and a large negative
median under P_class, such as the LUAR period base row at
{float(by_class_pool[(by_class_pool.embedding=='luar') & (by_class_pool.pool=='P_class') & (by_class_pool.author_class=='period') & (by_class_pool.kind=='base')].median_pos.iloc[0]):.2f},
is a small numerator over a smaller denominator rather than a measurement of how far the base
model is from that author.

Read F rather than pos wherever the two disagree. pos is a ratio of two means and blows up
whenever the anchors are close together (`anchor_separation_by_pool.csv` carries the
separation for every row); F compares whole distributions and is bounded above by 1. On these
data the two agree closely, which is itself informative: it means G, P and H are almost
collinear on each embedding, so W1(G, H) is nearly |mean G - mean H| and F carries little
information the mean did not already carry.

The region rate is the number that assumes least. It cannot be inflated by collapse, it is
zero for a generator that is right on one instrument and wrong on the other, and it comes with
its own ceiling: the author's own held-out passages score
{region.R_ceiling_author_own.mean():.2f} on the same two-instrument rule, so R is read as a
fraction of that and not as a fraction of 1. Every region and position row names its
`n_authors`, and rows built on one or three authors carry no claim about a model or a family.

Read every difference against the instrument's replicate floor in
`replicate_floors_instrument.csv` ({', '.join(f'{e} {FLOOR[e]:.4f}' for e in EMB)}), which is
also the `instrument_floor` column of `positions_register_matched.csv`. A difference between
two configurations, or between two pools, that is smaller than that floor is inside the
twice-generated replicate noise of the instrument and is reported as within the floor. The
class-level pool shifts above are larger than these floors; many of the configuration-to-
configuration differences in the same tables are not.

Attribution here is stricter than the pipeline's `*_attrib` column: it removes the passage
the brief came from, so a correct attribution cannot be bought with content. Read the
confusion matrix by row. Off-diagonal mass that lands consistently on authors of a different
class is consistent with the generation carrying register rather than the individual writer,
and `attribution_attractors_summary.csv` is the check on that reading, since a tight bank
attracts predictions on its own.
"""

caveats = [
    "The instrument is a mean cosine to the author's held-out *test* passages, not the "
    "pipeline's cosine to the reference centroid; the two are correlated but not the same "
    "number, so a position here is not directly comparable with a position in script 15 "
    "even when the pool is the same. The like-for-like contrast is P_class against "
    "P_period14 inside this script, both computed on this instrument.",
    f"The private class has two authors. A register-matched pool for `patrick_v2` is "
    f"`h_private` alone and the reverse; those rows are a single-author floor and are "
    f"reported as such. `patrick` is excluded entirely as the v1 chunking control of the "
    f"same person.",
    "The period-14 pool passages come from `others.jsonl`, which excludes the run's own "
    "author when that author is in the pool. A period study author is therefore anchored "
    "against thirteen period authors and a contemporary or private author against fourteen; "
    "the per-author means in `pool_pairwise_cosine.csv` show the difference is small next to "
    "the class difference, but it is not zero.",
    "P_period14 here uses the union of every chunk any run drew from each pool author, "
    "which is a larger sample than the roughly 100 chunks the pipeline actually scored any "
    "one author against. It estimates the same population more precisely; it does not "
    "reproduce a particular run's pool passage for passage.",
    "A mean cosine to a set favours authors whose own passages sit close together: the "
    "tighter the bank, the easier it is for anything to be nearest to it. "
    "`attribution_attractors_summary.csv` prints, beside each author's share of all "
    "predictions, the mean within-author cosine of its own bank and the bank's size, so a "
    "column of the confusion matrix that fills up can be checked against the geometry of "
    "that author's cloud rather than read as a claim about the generations.",
    f"Bank sizes are uneven, so anchor precision is not constant down the table: source banks "
    f"run from {n_src_min} to {n_src_max} passages and reference banks from {n_ref_min} to "
    f"{n_ref_max} (`embedding_bank.csv`), with `{thin_author.author}` the thinnest source bank "
    f"at {int(thin_author.n_source)}.",
    f"Bootstrap intervals resample briefs within a configuration and hold the anchors fixed. "
    f"Anchor uncertainty (H has {n_src_min} to {n_src_max} passages per author) is not in the "
    f"intervals.",
    f"Generated passages from runs that exceed the 20 per cent truncation gate are included "
    f"and flagged, not excluded. Among the runs read here that is: "
    f"{', '.join(trunc_flagged_used) if trunc_flagged_used else 'none'}. A truncated passage "
    f"is shorter than the author's own, and these instruments are not length-invariant.",
    "The pool-effect tests correct within their own family in `pool_effect_tests.csv` and the "
    "attribution tests within theirs; neither has been through the programme-wide correction "
    "in script 22, which is a second and stricter layer.",
    "Arm A5 shows the model the author's own statistics, so its structure numbers are "
    "compliance rather than fidelity (FIDELITY_SYNTHESIS section 4). The embedding "
    "instruments used here are not shown to the model, but A5 rows should still be read as a "
    "different question from A0 rows.",
    "The alignment repair is inferred from the s5_score row order and verified by "
    "reproducing stored cosines; it is not a documented format. Any run whose stored "
    "cosines could not be reproduced was dropped rather than guessed at, and is listed in "
    "alignment_check.csv with the reason.",
]

tables = [
    ("Alignment repair, by run (first rows; full table in alignment_check.csv)",
     align[["run", "n_scores", "n_gens_file", "n_npy", "extra_anchor_rows", "aligned"]].head(12)),
    ("Median position by author class and pool, arm A0",
     by_class_pool[(by_class_pool.embedding == "luar")].sort_values(["kind", "author_class", "pool"])),
    ("Median distributional fidelity F by author class and pool, arm A0",
     fid_class_pool[(fid_class_pool.embedding == "luar")].sort_values(["kind", "author_class", "pool"])),
    ("Does the pool change the position (author is the unit)", pooltest),
    ("Author-region rate on the two register-matched instruments", reg_top),
    ("Thirteen-author attribution, pooled over authors", acc_top),
    ("Which authors the LUAR instrument reaches for, arm A0 (flat would be 0.077)",
     attractor_top[attractor_top.embedding == "luar"]),
]

write_readme(OUTD, "23 - A register-matched stranger pool", what, how, reading,
             caveats=caveats, tables=tables, figures=figs,
             extra=f"Runtime {time.time()-T0:.0f}s. "
                   f"{len(positions)} position rows, {len(fidelity)} fidelity rows, "
                   f"{len(region)} region rows, {len(acc)} attribution rows.")
print(f"[23] done in {time.time()-T0:.0f}s -> {OUTD}", flush=True)
