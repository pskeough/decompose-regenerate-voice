"""S2: the three conditioning materials, from TRAIN only (METHODS 4).

    guide      one API call over GUIDE_N_PASSAGES train passages -> guide.md
    quant      the nine SHOWN features over all TRAIN passages -> quant.json,
               quant_block.txt (rendered through PROMPTS.md 3)
    retrieval  BM25 over TRAIN passages, query = brief, k per brief, one per
               work, cut to max_words on a paragraph boundary -> retrieval_<split>.jsonl

BM25 is implemented here (Robertson/Sparck Jones k1=1.5, b=0.75) rather than
imported, because rank_bm25 is not installed and thirty lines is not worth a
dependency. Stopwords are removed from the query and the index so that the
match is on content words.

    python dr/s2_conditioning.py --author wharton --guide --quant
    python dr/s2_conditioning.py --author wharton --retrieval --briefs briefs_test_limit10.jsonl
    python dr/s2_conditioning.py --author wharton --show <passage_id>     # one full A5 prompt
"""
from __future__ import annotations

import argparse
import collections
import math
import os
import random
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import (Manifest, api_call, author_dir, log, ngrams, norm_words,  # noqa: E402
                     paragraphs, read_json, read_jsonl, read_text, sentences,
                     upstream_hash, words, write_json, write_jsonl, write_text)
from dr.prompts import Prompts  # noqa: E402

STOP = set("""a an the and or but if while of to in on at by for with from as is are was
were be been being it its this that these those he she they them his her their you your
i me my we us our not no nor so then than there here what which who whom whose when where
why how all any both each few more most other some such only own same too very can will
just do does did done has have had having would could should may might must shall into
onto over under out up down off again further once about after before between through
during above below against because until also one two three said says say""".split())

_DASH = re.compile(r"—|–|--")
_QUOTE = re.compile(r"[\"“”]")


# ------------------------------------------------------------ SHOWN features

def shown_features(text):
    """The nine features written into the A4 prompt. Also used by s5 for the
    compliance table, so this is the single definition."""
    sents = sentences(text)
    lens = [len(words(s)) for s in sents] or [0]
    n = max(len(sents), 1)
    paras = paragraphs(text)
    openers = [words(s)[0].lower() for s in sents if words(s)]
    nw = max(len(words(text)), 1)
    return {
        "sent_mean": st.mean(lens),
        "sent_sd": st.pstdev(lens) if len(lens) > 1 else 0.0,
        "pct_short": 100.0 * sum(1 for L in lens if L < 9) / n,
        "pct_long": 100.0 * sum(1 for L in lens if L > 30) / n,
        "commas": text.count(",") / n,
        "semi_per100": 100.0 * text.count(";") / n,
        "dialogue_pct": 100.0 * sum(1 for s in sents if _QUOTE.search(s)) / n,
        "para_mean": st.mean([len(words(p)) for p in paras]),
        "open_distinct100": 100.0 * len(set(openers)) / max(len(openers), 1),
        "dash_per100w": 100.0 * len(_DASH.findall(text)) / nw,
        "_openers": openers,
    }


def quant_from_train(train_rows):
    """Corpus-level values: per-passage features averaged, openers pooled."""
    feats = [shown_features(r["text"]) for r in train_rows]
    keys = [k for k in feats[0] if not k.startswith("_")]
    q = {k: float(st.mean(f[k] for f in feats)) for k in keys}
    q["sd"] = {k: float(st.pstdev([f[k] for f in feats])) for k in keys}
    pooled = collections.Counter(o for f in feats for o in f["_openers"])
    top = [w for w, _ in pooled.most_common(5)]
    q["top_openers"] = ", ".join(f'"{w}"' for w in top)
    q["n_passages"] = len(feats)
    return q


# ---------------------------------------------------------------- BM25

class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.toks = [[w for w in norm_words(d) if w not in STOP] for d in docs]
        self.N = len(docs)
        self.avgdl = sum(len(t) for t in self.toks) / max(self.N, 1)
        self.df = collections.Counter()
        for t in self.toks:
            self.df.update(set(t))
        self.tf = [collections.Counter(t) for t in self.toks]

    def score(self, query):
        q = [w for w in norm_words(query) if w not in STOP]
        out = []
        for i in range(self.N):
            dl = len(self.toks[i])
            s = 0.0
            for w in set(q):
                if w not in self.tf[i]:
                    continue
                idf = math.log(1 + (self.N - self.df[w] + 0.5) / (self.df[w] + 0.5))
                f = self.tf[i][w]
                s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out.append(s)
        return out


def cut_words(text, max_words):
    """First paragraphs up to max_words, never cutting inside a paragraph unless
    the first paragraph alone is over the cap, in which case cut at a sentence."""
    out, n = [], 0
    for p in paragraphs(text):
        pw = len(words(p))
        if n + pw > max_words:
            if not out:
                keep, m = [], 0
                for s in sentences(p):
                    if m + len(words(s)) > max_words:
                        break
                    keep.append(s)
                    m += len(words(s))
                out.append(" ".join(keep))
            break
        out.append(p)
        n += pw
    return "\n\n".join(out)


def retrieve(briefs, train_rows, k, max_words):
    bm = BM25([r["text"] for r in train_rows])
    out = []
    for b in briefs:
        if not b.get("passed"):
            continue
        scores = bm.score(b["brief"])
        order = sorted(range(len(train_rows)), key=lambda i: -scores[i])
        picked, seen_works = [], set()
        for i in order:
            r = train_rows[i]
            if r["work_key"] in seen_works:
                continue
            seen_works.add(r["work_key"])
            picked.append({"id": r["id"], "work": r["work"], "score": round(scores[i], 3),
                           "text": cut_words(r["text"], max_words)})
            if len(picked) == k:
                break
        fallback = 0
        if len(picked) < k:
            # 2026-09-09: an author whose train split holds fewer than k works
            # (Watts: two) fills the remaining slots with the next-best chunks
            # regardless of work; one-per-work is kept for the first pass so
            # every work is still represented. Recorded per row.
            have = {e["id"] for e in picked}
            for i in order:
                r = train_rows[i]
                if r["id"] in have:
                    continue
                have.add(r["id"])
                picked.append({"id": r["id"], "work": r["work"], "score": round(scores[i], 3),
                               "text": cut_words(r["text"], max_words)})
                fallback += 1
                if len(picked) == k:
                    break
        row = {"id": b["id"], "exemplars": picked}
        if fallback:
            row["work_fallback"] = fallback
        out.append(row)
    return out


# ---------------------------------------------------------------- guide

def make_guide(P, train_rows, model, seed):
    R = random.Random(seed)
    by_work = collections.defaultdict(list)
    for r in train_rows:
        if r["split"] == "train_fit" and 450 <= r["words"] <= 800:
            by_work[r["work_key"]].append(r)
    works = sorted(by_work)
    R.shuffle(works)
    chosen = [R.choice(by_work[w]) for w in works[: config.GUIDE_N_PASSAGES]]
    if len(chosen) < config.GUIDE_N_PASSAGES:
        pool = [r for r in train_rows if r["split"] == "train_fit" and r["id"] not in {c["id"] for c in chosen}]
        R.shuffle(pool)
        chosen += pool[: config.GUIDE_N_PASSAGES - len(chosen)]
    system, user0 = P.guide([c["text"] for c in chosen])
    name = config.AUTHOR_NAMES[train_rows[0]["author"]]
    src4 = set()
    for c in chosen:
        src4 |= ngrams(norm_words(c["text"]), 4)
    # Hard gate: at most GUIDE_MAX_SHARED_4GRAMS word 4-grams shared with the
    # twelve inputs, and no author name. The first guide written for Wharton
    # quoted whole clauses (41 shared 4-grams, runs of eight words); a guide
    # that quotes is an exemplar arm in disguise, so it is regenerated with
    # the offending runs named, up to three attempts.
    user, attempts = user0, []
    for k in range(3):
        text, meta = api_call(model, system, user, max_tokens=1400,
                              temperature=config.GUIDE_TEMPERATURE, tag=f"guide:{k}")
        if text is None:
            raise SystemExit(f"guide call failed: {meta}")
        leaks = [p for p in name.split() if len(p) > 2 and re.search(rf"\b{re.escape(p)}\b", text)]
        shared = sorted(" ".join(g) for g in (ngrams(norm_words(text), 4) & src4))
        attempts.append({"k": k, "shared": len(shared), "name_leak": leaks, "usd": meta.get("usd")})
        if len(shared) <= config.GUIDE_MAX_SHARED_4GRAMS and not leaks:
            break
        user = (user0 + "\n\nYour previous guide broke rule 3 by reusing these runs of words from the "
                "passages: " + "; ".join(f'"{s}"' for s in shared[:12]) +
                ". Describe the habit instead of quoting it. Never reuse four or more consecutive "
                "words from any passage." + (" It also broke rule 4 by naming the author." if leaks else ""))
    return text, {"model": meta.get("model", model), "usd": sum(a_["usd"] or 0 for a_ in attempts),
                  "attempts": attempts, "input_ids": [c["id"] for c in chosen],
                  "input_words": sum(c["words"] for c in chosen),
                  "guide_words": len(words(text)), "name_leak": leaks,
                  "shared_4grams_with_inputs": shared, "passed": len(shared) <= config.GUIDE_MAX_SHARED_4GRAMS and not leaks}


# ----------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--guide", action="store_true")
    ap.add_argument("--quant", action="store_true")
    ap.add_argument("--retrieval", action="store_true")
    ap.add_argument("--briefs", default="briefs_test.jsonl", help="file in data/<author>/")
    ap.add_argument("--guide-model", default=config.GUIDE_MODEL)
    ap.add_argument("--show", default="", help="print the full A5 prompt for one passage id")
    a = ap.parse_args()
    d = author_dir(a.author)
    P = Prompts()
    train = read_jsonl(os.path.join(d, "train.jsonl"))

    if a.guide:
        man = Manifest(os.path.join(d, "s2_guide_manifest.json"), "s2_guide")
        man.input("train", os.path.join(d, "train.jsonl"),
                  expect=upstream_hash(os.path.join(d, "s0_manifest.json"), "train"))
        text, meta = make_guide(P, train, a.guide_model, config.SEED)
        p = os.path.join(d, "guide.md")
        write_text(p, text.strip() + "\n")
        man.output("guide", p)
        man.save(**meta)
        log(f"guide: {meta['guide_words']} words, name_leak={meta['name_leak']}, "
            f"shared 4-grams={len(meta['shared_4grams_with_inputs'])} -> {p}")

    if a.quant:
        man = Manifest(os.path.join(d, "s2_quant_manifest.json"), "s2_quant")
        man.input("train", os.path.join(d, "train.jsonl"),
                  expect=upstream_hash(os.path.join(d, "s0_manifest.json"), "train"))
        q = quant_from_train(train)
        block = P.quant(q)
        write_json(os.path.join(d, "quant.json"), q)
        write_text(os.path.join(d, "quant_block.txt"), block + "\n")
        man.output("quant", os.path.join(d, "quant.json"))
        man.output("quant_block", os.path.join(d, "quant_block.txt"))
        man.save(n_passages=q["n_passages"])
        log("quant block:\n" + block)

    if a.retrieval:
        bpath = os.path.join(d, a.briefs)
        man = Manifest(os.path.join(d, f"s2_retrieval_manifest.json"), "s2_retrieval")
        man.input("briefs", bpath)
        man.input("train", os.path.join(d, "train.jsonl"),
                  expect=upstream_hash(os.path.join(d, "s0_manifest.json"), "train"))
        briefs = read_jsonl(bpath)
        rows = retrieve(briefs, train, config.RETRIEVAL["k"], config.RETRIEVAL["max_words"])
        tag = os.path.basename(bpath).replace("briefs_", "").replace(".jsonl", "")
        p = os.path.join(d, f"retrieval_{tag}.jsonl")
        write_jsonl(p, rows)
        man.output("retrieval", p)
        # sanity: no exemplar id in test or ref
        forbidden = {r["id"] for r in read_jsonl(os.path.join(d, "test.jsonl"))} | \
                    {r["id"] for r in read_jsonl(os.path.join(d, "ref.jsonl"))}
        bad = [e["id"] for r in rows for e in r["exemplars"] if e["id"] in forbidden]
        assert not bad, f"retrieval leaked from TEST/REF: {bad}"
        man.save(n=len(rows), k=config.RETRIEVAL["k"], leak_check="ok")
        log(f"retrieval: {len(rows)} briefs x {config.RETRIEVAL['k']} exemplars -> {p}")

    if a.show:
        briefs = {r["id"]: r for r in read_jsonl(os.path.join(d, a.briefs))}
        tag = a.briefs.replace("briefs_", "").replace(".jsonl", "")
        ret = {r["id"]: r for r in read_jsonl(os.path.join(d, f"retrieval_{tag}.jsonl"))}
        b = briefs[a.show]
        ex = [e["text"] for e in ret[a.show]["exemplars"]]
        guide = read_text(os.path.join(d, "guide.md"))
        quant = read_text(os.path.join(d, "quant_block.txt"))
        print("=== SYSTEM ===\n" + P.gen_system())
        print("\n=== USER (A5) ===\n" + P.gen_user("A5", b["brief"], exemplars=ex, guide=guide, quant=quant))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
