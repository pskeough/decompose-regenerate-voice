"""S1: content briefs with leakage gates (METHODS 3).

For every passage in a split, ask the decomposer for a brief, then test it:

    a  no word 6-gram shared with the source          hard
    b  brief 4-grams found in source  <= 0.03         hard
    c  brief words / source words     <= 0.35         hard
    d  no word from STYLE_WORDS                       hard
    f  layout present, Latin script                   hard (format, not leakage)

A failing brief is regenerated with a reminder naming the broken rule, up to
GATES.max_attempts in total; a brief that still fails is dropped and logged.
Gate e (attribution of the brief itself) needs LUAR and runs in s5.

The same script, same prompt, same model and temperature produce the TRAIN
briefs for the pair recipe, so the training conditional matches the eval one.

    python dr/s1_decompose.py --author wharton --split test --limit 10   # Gate 1
    python dr/s1_decompose.py --author wharton --split test
    python dr/s1_decompose.py --author wharton --split train
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import (Manifest, api_call, author_dir, log, ngrams, norm_words,  # noqa: E402
                     read_jsonl, upstream_hash, write_jsonl)
from dr.prompts import Prompts  # noqa: E402

_STYLE_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in config.STYLE_WORDS) + r")\b", re.I)
_NONLATIN = re.compile(r"[Ѐ-ӿ֐-ۿऀ-ॿ぀-ヿ一-鿿가-힯]")
_LAYOUT = ("SETTING", "CHARACTERS PRESENT", "NARRATIVE STANCE", "LENGTH",
           r"EVENTS,?\s+IN\s+ORDER", "WHAT THE READER LEARNS", "WHAT THE PASSAGE IS DOING")
_LENGTH_LINE = re.compile(r"^\W*LENGTH\W*:.*$", re.I | re.M)


def proper_nouns(source):
    """Lowercased words that appear capitalised somewhere other than sentence
    start in the source. Names are content the brief is told to keep, so a run
    of words that is only shared because it contains one is not a quotation."""
    out = set()
    for sent in re.split(r"(?<=[.!?])\s+", source):
        for m in re.finditer(r"\b([A-Z][a-z'’-]+)\b", sent[1:]):
            out.add(m.group(1).lower())
    return out


def brief_budget(n_words):
    return max(180, int(0.4 * n_words))


def gate(brief, source):
    """Return (passed, failures:list[(rule, reason)], stats)."""
    b, s = norm_words(brief), norm_words(source)
    pn = proper_nouns(source)
    bm = ["<N>" if w in pn else w for w in b]
    sm = ["<N>" if w in pn else w for w in s]
    n6 = config.GATES["shared_ngram"]
    shared6 = {g for g in (ngrams(bm, n6) & ngrams(sm, n6)) if any(t != "<N>" for t in g)}
    b4 = ngrams(bm, 4)
    frac4 = (len(b4 & ngrams(sm, 4)) / len(b4)) if b4 else 0.0
    ratio = len(b) / max(len(s), 1)
    style_hits = sorted({m.group(1).lower() for m in _STYLE_RE.finditer(brief)})
    fails = []
    if shared6:
        ex = " ".join(next(iter(shared6))).replace("<N>", "[name]")
        fails.append(("1", f"it reused the run of words \"{ex}\" from the passage. Quote nothing; "
                           "state the fact in different words."))
    if frac4 > config.GATES["ngram4_frac_max"]:
        fails.append(("1", f"{frac4:.0%} of its four-word runs occur in the passage. "
                           "Paraphrase every proposition in your own plain words."))
    if ratio > config.GATES["len_ratio_max"] and len(b) > config.GATES["brief_words_ok"]:
        fails.append(("2", f"it is {len(b)} words; the limit is {brief_budget(len(s))} words. "
                           "Keep every heading, cut each event to one short sentence."))
    if style_hits:
        fails.append(("3", f"it used words about the writing: {', '.join(style_hits)}. "
                           "Record only what happens and what the reader learns."))
    missing = [h.replace(r",?\s+", " ").replace(r"\s+", " ") for h in _LAYOUT
               if not re.search(h, brief, re.I)]
    if missing:
        fails.append(("layout", f"it omitted the headings: {', '.join(missing)}. Use the exact layout."))
    if _NONLATIN.search(brief):
        fails.append(("layout", "it contained non-Latin script. Write in English only."))
    stats = {"shared6": len(shared6), "frac4": round(frac4, 4), "len_ratio": round(ratio, 3),
             "style_hits": style_hits, "brief_words": len(b), "source_words": len(s),
             "proper_nouns_masked": len(pn)}
    return not fails, fails, stats


def decompose_one(P, row, model, prior=None, extra_attempts=0, recover_temperature=0.4):
    """`prior` is an earlier result for this row whose attempts are kept; the
    recovery pass adds `extra_attempts` more at a non-zero temperature, because
    at temperature 0 a model that has quoted twice tends to quote a third time
    (one dropped brief came back as the whole passage on its third try)."""
    src = row["text"]
    retry = None
    attempts = list(prior["attempts"]) if prior else []
    start = len(attempts)
    if prior and attempts and attempts[-1].get("fails"):
        rule, reason = attempts[-1]["fails"][0]
        retry = {"rule": rule, "reason": reason}
    n_total = config.GATES["max_attempts"] + extra_attempts
    for k in range(start, n_total):
        temp = recover_temperature if k >= config.GATES["max_attempts"] else 0.0
        system, user = P.brief(src, row["words"], retry=retry, max_words=brief_budget(row["words"]))
        text, meta = api_call(model, system, user, max_tokens=config.BRIEF_MAX_TOKENS,
                              temperature=temp, tag=f"brief:{row['id']}:{k}")
        if text is None:
            attempts.append({"k": k, "error": meta.get("error")})
            continue
        # The LENGTH line is read by every generation arm, so it is set here
        # from the source word count rather than trusted to the model, which
        # was seen to write a different number from the one it was given.
        length_line = f"LENGTH: about {row['words']} words."
        if _LENGTH_LINE.search(text):
            text = _LENGTH_LINE.sub(length_line, text, count=1)
        else:
            # some models drop the line; put it before the events list
            text = re.sub(r"(?im)^(\W*EVENTS,?\s+IN\s+ORDER)", length_line + "\n\\1", text, count=1)
        ok, fails, stats = gate(text, src)
        attempts.append({"k": k, "ok": ok, "fails": fails, "stats": stats,
                         "usd": meta.get("usd", 0.0), "cached": meta.get("cached", False)})
        if ok:
            return {"id": row["id"], "brief": text, "passed": True, "attempts": attempts,
                    "stats": stats, "model": meta.get("model", model), "split": row["split"],
                    "source_words": row["words"]}
        rule, reason = fails[0]
        retry = {"rule": rule, "reason": reason}
    return {"id": row["id"], "brief": None, "passed": False, "attempts": attempts,
            "stats": attempts[-1].get("stats") if attempts else None, "model": model,
            "split": row["split"], "source_words": row["words"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--split", choices=["test", "train"], default="test")
    ap.add_argument("--model", default=config.DECOMPOSER)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default="", help="override output file (dry runs)")
    ap.add_argument("--recover", type=int, default=0,
                    help="N extra attempts at --recover-temp for rows that did not pass")
    ap.add_argument("--recover-temp", type=float, default=0.4)
    a = ap.parse_args()
    d = author_dir(a.author)
    P = Prompts()
    man = Manifest(os.path.join(d, f"s1_{a.split}_manifest.json"), "s1_decompose")
    src_path = os.path.join(d, f"{a.split}.jsonl")
    man.input(a.split, src_path, expect=upstream_hash(os.path.join(d, "s0_manifest.json"), a.split))
    rows = read_jsonl(src_path)
    if a.limit:
        rows = rows[: a.limit]
    out_path = a.out or os.path.join(d, f"briefs_{a.split}{'_limit' + str(a.limit) if a.limit else ''}.jsonl")

    done, prior = {}, {}
    if os.path.exists(out_path) and not a.out:
        for r in read_jsonl(out_path):
            if r.get("passed"):
                done[r["id"]] = r
            else:
                prior[r["id"]] = r
    todo = [r for r in rows if r["id"] not in done]
    if a.recover:
        todo = [r for r in todo if r["id"] in prior]
    log(f"{a.split}: {len(rows)} passages, {len(done)} already briefed, {len(todo)} to do "
        f"with {a.model}" + (f" (recovery, +{a.recover} attempts)" if a.recover else ""))
    results = list(done.values())
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(decompose_one, P, r, a.model, prior.get(r["id"]), a.recover,
                          a.recover_temp): r["id"] for r in todo}
        for i, f in enumerate(as_completed(futs), 1):
            res = f.result()
            results.append(res)
            if i % 10 == 0 or i == len(futs):
                log(f"  {i}/{len(futs)}")
    results.sort(key=lambda r: r["id"])
    write_jsonl(out_path, results)
    man.output("briefs", out_path)

    n = len(results)
    passed = [r for r in results if r["passed"]]
    first_try = sum(1 for r in passed if len(r["attempts"]) == 1)
    fail_rules = {}
    for r in results:
        for at in r["attempts"]:
            for rule, _ in at.get("fails", []):
                fail_rules[rule] = fail_rules.get(rule, 0) + 1
    usd = sum(at.get("usd", 0.0) for r in results for at in r["attempts"])
    st = [r["stats"] for r in passed]
    summ = {"n": n, "passed": len(passed), "first_try": first_try, "dropped": n - len(passed),
            "fail_events_by_rule": fail_rules, "usd": round(usd, 4),
            "len_ratio_mean": round(sum(s["len_ratio"] for s in st) / max(len(st), 1), 3),
            "frac4_mean": round(sum(s["frac4"] for s in st) / max(len(st), 1), 4),
            "brief_words_mean": round(sum(s["brief_words"] for s in st) / max(len(st), 1), 1)}
    man.save(summary=summ, model=a.model)
    log(f"summary {summ}")
    log(f"-> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
