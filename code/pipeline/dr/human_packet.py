"""Human 2AFC packet: can a reader tell the author's real passage from the
model's regeneration of the same brief?

Design (eval-methodology-playbook conventions):
  * item = REFERENCE excerpt by the author (REF split, different work) +
    candidate A + candidate B on the same events; one is the real TEST
    passage, the other the model's sample-0 regeneration under a condition
  * every item is rated TWICE by different raters with the real passage in
    opposite positions: position bias is controlled by design and the two
    ratings give Cohen's kappa
  * a rater never sees the same passage twice, across conditions
  * response = choice A/B, confidence 1-4 (a continuous read, not a binary
    verdict), optional note on what gave it away
  * item set is hash-locked (eval_set.sha256); KEY.json stays with Patrick
  * outputs with the `truncated` flag (cut by the token cap mid-sentence)
    are excluded and the exclusion is reported; nothing else is filtered

    python dr/human_packet.py --out runs/human_2afc_v1
    python dr/human_packet.py --out runs/human_2afc_v1 --raters 16 --per-rater 12 --per-condition 19
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import RUNS, author_dir, normalise_punct, paragraphs, read_jsonl, words, write_json, write_jsonl, write_text  # noqa: E402

# condition code -> (author, run, arm, label for the key only)
CONDITIONS = {
    "W-base": ("wharton", "base4b", "A0", "Wharton, 4B base, brief only"),
    "W-e6": ("wharton", "pair_e6_4b", "A0", "Wharton, 4B + pair adapter 6 epochs, brief only"),
    "W-front": ("wharton", "base4b_frontier", "F5", "Wharton, frontier API model, full stack"),
    "P-base": ("patrick", "patrick_base4b", "A0", "Patrick, 4B base, brief only"),
    "P-mix": ("patrick", "patrick_mix4b", "A2", "Patrick, 4B + mix adapter, brief + retrieval"),
}
AUTHOR_LABEL = {"wharton": "the author", "patrick": "the author"}   # never named in the packet


def excerpt(text, n_words):
    out, m = [], 0
    for p in paragraphs(text):
        pw = len(words(p))
        if m + pw > n_words and out:
            break
        out.append(p)
        m += pw
        if m >= n_words:
            break
    t = "\n\n".join(out)
    if len(words(t)) > n_words * 1.4:      # one very long paragraph: cut at a sentence
        from dr.core import sentences
        keep, k = [], 0
        for s in sentences(t):
            if k + len(words(s)) > n_words:
                break
            keep.append(s)
            k += len(words(s))
        t = " ".join(keep)
    return t


def build_items(R, per_condition, max_words, ref_words, cand_words):
    """Candidates are the opening `cand_words` of the real passage and of the
    regeneration, cut on a paragraph boundary, so every item is a similar read
    (Wharton's test passages run 400-800 words and would otherwise make her
    items twice the length of Patrick's). A fixed-length opening is the
    standard authorship-2AFC excerpt; the rater judges voice, not plot
    completeness, and the two candidates still cover the same early events."""
    items, excluded = [], collections.Counter()
    for code, (author, run, arm, label) in CONDITIONS.items():
        d = author_dir(author)
        test = {r["id"]: r for r in read_jsonl(os.path.join(d, "test.jsonl"))}
        ref = read_jsonl(os.path.join(d, "ref.jsonl"))
        gens = [g for g in read_jsonl(os.path.join(RUNS, run, "gens.jsonl")) if g["arm"] == arm and g["sample"] == 0]
        pool = []
        for g in gens:
            src = test.get(g["id"])
            if not src or src["words"] > max_words:
                continue
            if "truncated" in g["flags"]:
                excluded[code] += 1
                continue
            pool.append((src, g))
        R.shuffle(pool)
        if len(pool) < per_condition:
            print(f"  {code}: only {len(pool)} eligible passages (<= {max_words} words); using all")
        for src, g in pool[:per_condition]:
            ref_choices = [r for r in ref if r["work"] != src["work"]]
            rf = R.choice(ref_choices)
            real_x, gen_x = excerpt(normalise_punct(src["text"]), cand_words), excerpt(normalise_punct(g["text"]), cand_words)
            items.append({"item": None, "condition": code, "author": author, "run": run, "arm": arm,
                          "passage_id": src["id"], "work": src["work"], "ref_id": rf["id"],
                          "reference": excerpt(normalise_punct(rf["text"]), ref_words), "real": real_x, "gen": gen_x,
                          "real_words": len(words(real_x)), "gen_words": len(words(gen_x)),
                          "real_full_words": src["words"], "gen_full_words": g["n_words"]})
    R.shuffle(items)
    for i, it in enumerate(items, 1):
        it["item"] = f"h{i:03d}"
    return items, excluded


def assign(R, items, raters, per_rater, tries=2000):
    """Two ratings per item in opposite positions; no rater sees a passage
    twice; conditions balanced across raters as far as the counts allow."""
    slots = []
    for it in items:
        slots.append((it["item"], "A"))   # real in position A
        slots.append((it["item"], "B"))   # real in position B
    by_item = {it["item"]: it for it in items}
    need = raters * per_rater
    if len(slots) > need:
        raise SystemExit(f"{len(slots)} ratings needed but {raters} x {per_rater} = {need} slots; "
                         f"raise --raters or --per-rater, or lower --per-condition")
    for _ in range(tries):
        R.shuffle(slots)
        packs = [[] for _ in range(raters)]
        ok = True
        for slot in slots:
            it = by_item[slot[0]]
            # candidate raters: fewest items first, must not hold this item or this passage
            order = sorted(range(raters), key=lambda k: (len(packs[k]), R.random()))
            placed = False
            for k in order:
                if len(packs[k]) >= per_rater:
                    continue
                held = {s[0] for s in packs[k]}
                held_pass = {by_item[s[0]]["passage_id"] for s in packs[k]}
                if slot[0] in held or it["passage_id"] in held_pass:
                    continue
                packs[k].append(slot)
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            for p in packs:
                R.shuffle(p)
            return packs
    raise SystemExit("could not build a valid assignment; loosen the constraints")


def rater_packet(k, pack, by_item):
    lines = [f"# Reading packet, rater {k:02d}", "",
             "Twelve items, about 45 minutes. Each item shows a short REFERENCE excerpt by a "
             "writer, then two candidate passages, A and B, that tell the same events. Exactly one "
             "candidate is by the same writer as the reference. The other was produced by a "
             "computer program from a plot summary of that passage.",
             "",
             "For each item, on the answer sheet: which candidate is by the writer (A or B); how "
             "confident you are, 1 (a guess) to 4 (certain); and, if you like, a few words on what "
             "decided it. Read at your normal pace. Do not look anything up, and do not go back to "
             "change an earlier answer after seeing later items.",
             "", "---", ""]
    for n, (item_id, real_pos) in enumerate(pack, 1):
        it = by_item[item_id]
        a, b = (it["real"], it["gen"]) if real_pos == "A" else (it["gen"], it["real"])
        lines += [f"## Item {n} of {len(pack)}   (id {item_id})", "",
                  "### Reference, by the writer", "", it["reference"], "",
                  "### Candidate A", "", a, "",
                  "### Candidate B", "", b, "", "---", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(RUNS, "human_2afc_v1"))
    ap.add_argument("--raters", type=int, default=16)
    ap.add_argument("--per-rater", type=int, default=12)
    ap.add_argument("--per-condition", type=int, default=19)
    ap.add_argument("--max-words", type=int, default=800, help="longest source passage admitted")
    ap.add_argument("--cand-words", type=int, default=450, help="opening words shown of each candidate")
    ap.add_argument("--ref-words", type=int, default=180)
    ap.add_argument("--seed", type=int, default=config.SEED)
    a = ap.parse_args()
    R = random.Random(a.seed)
    items, excluded = build_items(R, a.per_condition, a.max_words, a.ref_words, a.cand_words)
    packs = assign(R, items, a.raters, a.per_rater)
    by_item = {it["item"]: it for it in items}
    os.makedirs(os.path.join(a.out, "packets"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "sheets"), exist_ok=True)
    for k, pack in enumerate(packs, 1):
        write_text(os.path.join(a.out, "packets", f"rater_{k:02d}.md"), rater_packet(k, pack, by_item))
        rows = ["rater,item,choice,confidence,note"] + [f"{k:02d},{iid},,," for iid, _ in pack]
        write_text(os.path.join(a.out, "sheets", f"rater_{k:02d}.csv"), "\n".join(rows) + "\n")
    key = {"seed": a.seed, "conditions": {c: {"author": v[0], "run": v[1], "arm": v[2], "label": v[3]} for c, v in CONDITIONS.items()},
           "items": {it["item"]: {k: it[k] for k in ("condition", "author", "run", "arm", "passage_id", "work", "ref_id", "real_words", "gen_words")} for it in items},
           "ratings": [{"rater": k, "item": iid, "real_position": pos} for k, pack in enumerate(packs, 1) for iid, pos in pack],
           "excluded_truncated": dict(excluded)}
    write_json(os.path.join(a.out, "KEY.json"), key)
    write_jsonl(os.path.join(a.out, "items.jsonl"), items)
    h = hashlib.sha256(open(os.path.join(a.out, "items.jsonl"), "rb").read()).hexdigest()
    write_text(os.path.join(a.out, "eval_set.sha256"), h + "  items.jsonl\n")
    per_cond = collections.Counter(it["condition"] for it in items)
    pass_reads = collections.Counter(it["real_words"] + it["gen_words"] + a.ref_words for it in items)
    mean_words = sum(it["real_words"] + it["gen_words"] + a.ref_words for it in items) / len(items)
    readme = [f"# Human 2AFC, v1 (built {__import__('datetime').date.today()})", "",
              f"{len(items)} items over {len(per_cond)} conditions, each rated twice in opposite positions "
              f"= {2*len(items)} judgements; {a.raters} raters x {a.per_rater} items. Mean words per item "
              f"{mean_words:.0f} (reference {a.ref_words} + two candidates, each the opening ~{a.cand_words} "
              f"words of the real passage and of the regeneration, cut on a paragraph boundary).", "",
              "| condition | items | judgements | excluded (truncated) |", "|---|---:|---:|---:|"]
    for c in CONDITIONS:
        readme.append(f"| {c}: {CONDITIONS[c][3]} | {per_cond[c]} | {2*per_cond[c]} | {excluded.get(c, 0)} |")
    readme += ["", "## Files", "", "* `packets/rater_NN.md`: what each rater reads. Blind: no condition, author or model named.",
               "* `sheets/rater_NN.csv`: the answer sheet, prefilled with rater and item ids. Rater fills choice (A/B), confidence (1-4), note.",
               "* `KEY.json`: condition and real position per rating. Keep it away from raters.",
               "* `items.jsonl` + `eval_set.sha256`: the locked item set.",
               "", "## Pre-registered analysis (`dr/human_analysis.py`)", "",
               "1. Primary: accuracy per condition (share of ratings that pick the real passage), exact binomial test against 0.5, Wilson 95% CI. Fooling rate = 1 - accuracy.",
               "2. Condition contrasts: logistic GEE clustered by rater (exchangeable), Holm across the four contrasts against the matching base condition.",
               "3. Position check: accuracy when the real passage is A vs B, per condition.",
               "4. Reliability: Cohen's kappa and raw agreement over the double-rated items.",
               "5. Confidence: mean confidence on correct vs incorrect ratings; confidence-weighted accuracy.",
               "6. Calibration of the LLM judges: per condition, human fooling rate beside the Gemini and MiniMax fooling rates on the same items.",
               "", "## Rater rules", "",
               "* Patrick does not rate items from his own corpus (he wrote the real passages) and is excluded from the Wharton analysis too, since he has read the model outputs; he may run the pilot to check the instructions.",
               "* One rater = one packet. Raters are not told which condition an item belongs to, how many are real, or that any two items share a passage.",
               "* Recruit readers of literary fiction; a screener question on reading habit is enough. Prolific at ~45 minutes per packet is the scalable route; a personal pool of three covers a pilot, not a study.",
               ""]
    write_text(os.path.join(a.out, "README.md"), "\n".join(readme))
    print(f"{len(items)} items, {2*len(items)} judgements, {a.raters} raters x {a.per_rater}; per condition {dict(per_cond)}; "
          f"excluded truncated {dict(excluded)}; mean words/item {mean_words:.0f} -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
