"""S0: work-level split of one author into TEST / REF / TRAIN(fit,val).

The unit is the WORK, which the corpus already defines as the leakage
boundary: a novel is one work (chapters are never split apart), and each story
in a collection is its own work (CORPUS_REPORT 2). Assigning whole works keeps
a novel's characters and invented vocabulary on one side of every boundary. A
first version assigned whole volumes; on an eleven-volume author one story
collection swallowed the training split, and a volume is not the unit the
corpus was built around anyway.

TEST works are drawn first, in seeded order, until they hold at least N_TEST
chunks in the 400-800 word band; exactly N_TEST of those are sampled and the
remaining chunks of the TEST works are discarded rather than recycled. REF
works come next until N_REF_MIN chunks; everything else is TRAIN, which is
split again by work into fit and val for checkpoint selection. Because a work
is capped at 5,000 words (about seven chunks), the overshoot at each boundary
is at most one work.

Also writes others.jsonl: up to OTHERS_CAP chunks from each of the other
manifest authors, for centroids and Delta. Nothing generates from them.

    python dr/s0_split.py --author wharton
"""
from __future__ import annotations

import argparse
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import (CORPUS, Manifest, author_dir, log, read_jsonl,  # noqa: E402
                     write_json, write_jsonl)


def load_author(slug):
    rows = read_jsonl(os.path.join(CORPUS, f"{slug}.jsonl"))
    for r in rows:
        r["text"] = r.pop("target")
        # id: <author>__<gid>_<work_idx>_<chunk_idx>
        tail = r["id"].split("__", 1)[1]
        gid, widx, cidx = tail.rsplit("_", 2)
        r["work_key"] = f"{gid}_{widx}"
        r["chunk_idx"] = int(cidx)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--seed", type=int, default=config.SEED)
    ap.add_argument("--n-test", type=int, default=config.N_TEST, help="small authors: fewer test chunks")
    ap.add_argument("--n-ref", type=int, default=config.N_REF_MIN)
    ap.add_argument("--min-train-works", type=int, default=3,
                    help="works that must remain for TRAIN; 2 for a four-novel author (watts, 2026-09-09), each novel staying whole")
    ap.add_argument("--force-train-gids", default="",
                    help="comma-separated gutenberg_id values whose works go to TRAIN before the draw "
                         "(Patrick's novels: the test is stories, the adapter learns from the books too)")
    a = ap.parse_args()
    force_train = {int(x) for x in a.force_train_gids.split(",") if x.strip()}
    R = random.Random(a.seed)
    out = author_dir(a.author)
    man = Manifest(os.path.join(out, "s0_manifest.json"), "s0_split")
    src = os.path.join(CORPUS, f"{a.author}.jsonl")
    man.input("corpus", src)

    rows = load_author(a.author)
    lo, hi = config.TEST_WORDS
    by_work = collections.defaultdict(list)
    for r in rows:
        by_work[r["work_key"]].append(r)
    units = sorted(by_work)
    R.shuffle(units)
    n_vols = len({r["gutenberg_id"] for r in rows})
    log(f"{a.author}: {len(rows)} chunks over {len(units)} works in {n_vols} volumes")

    forced = [u for u in units if by_work[u][0]["gutenberg_id"] in force_train]
    units = [u for u in units if u not in forced]
    if forced:
        log(f"forced into TRAIN: {forced}")
    test_vols, ref_vols, train_vols = [], [], []       # lists of work keys
    n_elig = 0
    it = iter(units)
    for v in it:
        test_vols.append(v)
        n_elig += sum(1 for r in by_work[v] if lo <= r["words"] <= hi)
        if n_elig >= a.n_test:
            break
    n_ref = 0
    for v in it:
        ref_vols.append(v)
        n_ref += len(by_work[v])
        if n_ref >= a.n_ref:
            break
    train_vols = list(it) + forced
    if len(train_vols) < a.min_train_works:
        raise SystemExit(f"fewer than {a.min_train_works} works left for TRAIN; author too small for this split")
    if n_elig < a.n_test:
        raise SystemExit(f"only {n_elig} eligible TEST chunks; author too small")

    elig = [r for v in test_vols for r in by_work[v] if lo <= r["words"] <= hi]
    R.shuffle(elig)
    test = sorted(elig[: a.n_test], key=lambda r: r["id"])
    ref = sorted([r for v in ref_vols for r in by_work[v]], key=lambda r: r["id"])
    train = sorted([r for v in train_vols for r in by_work[v]], key=lambda r: r["id"])
    by_vol = by_work   # naming kept for the title listings below

    # TRAIN fit/val by work
    works = sorted({r["work_key"] for r in train})
    R.shuffle(works)
    n_val = max(1, round(config.VAL_WORK_FRAC * len(works)))
    val_works = set(works[:n_val])
    for r in train:
        r["split"] = "train_val" if r["work_key"] in val_works else "train_fit"
    for r in test:
        r["split"] = "test"
    for r in ref:
        r["split"] = "ref"

    # neighbours for the continue / infill views: same work, adjacent chunk idx,
    # and both on the TRAIN side (the split is by volume so that is automatic,
    # but it is asserted rather than assumed)
    by_key = {(r["work_key"], r["chunk_idx"]): r for r in train}
    for r in train:
        prev = by_key.get((r["work_key"], r["chunk_idx"] - 1))
        nxt = by_key.get((r["work_key"], r["chunk_idx"] + 1))
        r["prev_id"] = prev["id"] if prev else None
        r["next_id"] = nxt["id"] if nxt else None

    ids = [set(r["id"] for r in s) for s in (test, ref, train)]
    assert not (ids[0] & ids[1]) and not (ids[0] & ids[2]) and not (ids[1] & ids[2])
    assert not (set(test_vols) & set(ref_vols)) and not (set(test_vols) & set(train_vols))

    # other authors, capped, for centroids
    others = []
    for slug in config.MANIFEST_AUTHORS:
        if slug == a.author:
            continue
        o = load_author(slug)
        R.shuffle(o)
        for r in o[: config.OTHERS_CAP]:
            others.append({"id": r["id"], "author": slug, "text": r["text"], "words": r["words"],
                           "work": r["work"], "split": "other"})
    others.sort(key=lambda r: r["id"])

    keep = ("id", "author", "work", "work_key", "chunk_idx", "gutenberg_id", "form",
            "words", "text", "split", "prev_id", "next_id")
    slim = lambda r: {k: r.get(k) for k in keep}
    for name, rs in (("test", test), ("ref", ref), ("train", train)):
        p = os.path.join(out, f"{name}.jsonl")
        write_jsonl(p, [slim(r) for r in rs])
        man.output(name, p)
    p = os.path.join(out, "others.jsonl")
    write_jsonl(p, others)
    man.output("others", p)

    split = {"author": a.author, "seed": a.seed, "unit": "work", "n_test": a.n_test, "n_ref": a.n_ref,
             "works": {"test": test_vols, "ref": ref_vols, "train": train_vols},
             "counts": {"test": len(test), "ref": len(ref),
                        "train_fit": sum(r["split"] == "train_fit" for r in train),
                        "train_val": sum(r["split"] == "train_val" for r in train),
                        "train_with_prev": sum(1 for r in train if r["prev_id"]),
                        "train_with_both": sum(1 for r in train if r["prev_id"] and r["next_id"]),
                        "others": len(others)},
             "words": {"test": sum(r["words"] for r in test), "ref": sum(r["words"] for r in ref),
                       "train": sum(r["words"] for r in train)},
             "val_works": sorted(val_works),
             "test_volume_titles": sorted({r["work"] for v in test_vols for r in by_vol[v]}),
             "ref_volume_titles": sorted({r["work"] for v in ref_vols for r in by_vol[v]})}
    p = os.path.join(out, "split.json")
    write_json(p, split)
    man.output("split", p)
    man.save(summary=split["counts"])
    log(f"counts {split['counts']}")
    log(f"words {split['words']}")
    log(f"TEST volumes: {split['test_volume_titles']}")
    log(f"REF volumes: {split['ref_volume_titles']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
