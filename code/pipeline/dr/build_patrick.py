"""Build data/authors_v2/patrick.jsonl from the August corpus (data/corpus.jsonl),
in the same row shape as the public-domain authors so s0..s6 run unchanged.

Patrick, 2026-09-03: "only short stories + book + proper fiction I've written,
pref to 2026 basilisk and the leprosy one too."

Included:
    short-story   every story except the old `leprosy` (superseded by
                  `leprosy.2026-03-version`; two versions of one story across
                  splits would leak) and `machinations-outline-notes` (notes)
    basilisk-2026 the nine hand-revised chapters (`day-*`, 31k words, the
                  voice-safe revision); one work group, forced into TRAIN
    iris, pwr     novel drafts, capped at NOVEL_CAP contiguous words each so
                  they do not outweigh the 2026 Basilisk; forced into TRAIN
Excluded: essays, letters, The Second Tree vignettes (creative nonfiction),
`idealism` (fragment).

Encoding repair: the August corpus carries U+FFFD where a curly quote or
apostrophe was lost. Repaired by context (between letters -> apostrophe;
before a word at a clause start -> opening double quote; after punctuation ->
closing double quote) and counted, so the repair is auditable.

    python dr/build_patrick.py
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import CORPUS, ROOT, log, words, write_jsonl  # noqa: E402

SRC = os.path.join(ROOT, "data", "corpus.jsonl")
NOVEL_CAP = 15000
EXCLUDE_WORKS = {"leprosy", "machinations-outline-notes", "idealism"}
GID = {"basilisk-2026": 1, "iris": 2, "pwr": 3}      # novels; stories numbered from 100


def repair(text):
    n = text.count("�")
    if not n:
        return text, 0
    t = re.sub(r"(?<=[A-Za-z])�(?=[a-z])", "’", text)          # don’t, it’s
    t = re.sub(r"(?<=[A-Za-z])�(?=\s|$|[,.;:!?])", "’", t)     # Tom’ / plural possessive
    t = re.sub(r"(?:(?<=^)|(?<=[\s(\[]))�(?=[A-Za-z‘“])", "“", t, flags=re.M)  # “Would
    t = re.sub(r"(?<=[.,!?;:A-Za-z])�(?=\s|$)", "”", t, flags=re.M)   # some.”
    t = t.replace("�", "“")
    return t, n


def main():
    rows = [json.loads(l) for l in open(SRC, encoding="utf-8-sig") if l.strip()]
    out, repaired = [], 0
    by_group = collections.defaultdict(list)
    for r in rows:
        w, k = r["work"], r["kind"]
        if w in EXCLUDE_WORKS:
            continue
        if k == "short-story":
            group = w
        elif k == "creative" and w.startswith("day-"):
            group = "basilisk-2026"
        elif k == "novel" and w in ("iris", "pwr"):
            group = w
        else:
            continue
        by_group[group].append(r)
    story_names = sorted(g for g in by_group if g not in GID)
    gid = dict(GID, **{g: 100 + i for i, g in enumerate(story_names)})
    for group, rs in by_group.items():
        # keep file order; day-* chapters sort by day number
        if group == "basilisk-2026":
            rs.sort(key=lambda r: (r["work"], r["id"]))
        budget = NOVEL_CAP if group in ("iris", "pwr") else None
        used, cidx = 0, 0
        for r in rs:
            if budget is not None and used + r["words"] > budget:
                break
            text, n = repair(r["target"])
            repaired += n
            out.append({"id": f"patrick__{gid[group]}_00_{cidx:04d}", "work": group if group in GID else r["work"],
                        "author": "patrick", "target": text, "words": len(words(text)),
                        "original_language": "English", "form": "novel" if group in GID else "short_stories",
                        "death_year": None, "gutenberg_id": gid[group], "kind": r["kind"], "src_id": r["id"]})
            used += r["words"]
            cidx += 1
    out.sort(key=lambda r: r["id"])
    p = os.path.join(CORPUS, "patrick.jsonl")
    write_jsonl(p, out)
    wc = collections.Counter()
    for r in out:
        wc[r["work"]] += r["words"]
    log(f"{len(out)} chunks, {sum(wc.values())} words, {repaired} U+FFFD repaired -> {p}")
    log(f"novels: basilisk-2026 {wc['basilisk-2026']}, iris {wc['iris']}, pwr {wc['pwr']}; "
        f"stories {sum(v for k, v in wc.items() if k not in GID)} words over {len(story_names)} works")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
