"""S7 event-order fidelity, from R2.

The brief lists the source passage's events in order ("EVENTS, IN ORDER:"
followed by numbered lines). For each event, build a keyword set from its
content lemmas (minus stop words, minus lemmas shared by more than half the
events, e.g. "speaker"). An event's first mention is the first sentence whose
lemma set covers at least MIN_HIT keywords (or half the set for short sets).
Outputs per cell: Kendall tau between brief order and first-mention order over
events found; events_present share; terminal_missing (last event not found);
n_events. The keyword rule is frozen here before any table is read.

Unpaired: the author's own source passage is scored against its brief too, and
the SOURCE rows are the ceiling (tau near 1 by construction of the brief).
Reports for arm A0 by default; the coverage judge is the comparison.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, RESULTS, REPLICATES, available_runs, briefs, discover_runs, gens, sentences, sources  # noqa: E402

import json  # noqa: E402
import statistics as st  # noqa: E402

import spacy  # noqa: E402

_NLP = spacy.load("en_core_web_sm", disable=["parser", "ner"])
MIN_HIT = 2
STOP = set("""a an the and or but of in on at to from by with into onto over under about
above below between through during before after then once here there when where why how
all any both each few more most other some such no not only own same than too very can will
just should now is are was were be been being have has had having do does did doing i me my
we our you your he him his she her it its they them their what which who whom this that these
those am as if because until while up down out off would could might must shall may also one
two say tell speaker listener narrator character person people reader passage describe
describes mention mentions note notes recount recounts explain explains express expresses
acknowledge acknowledges""".split())
_EVENTS = re.compile(r"EVENTS, IN ORDER:\s*\n(.*?)(?:\n[A-Z][A-Z ]+:|\Z)", re.S)
_NUM = re.compile(r"^\s*\d+[.)]\s*(.+)$")


def event_lines(brief):
    m = _EVENTS.search(brief)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        mm = _NUM.match(line)
        if mm:
            out.append(mm.group(1).strip())
    return out


def lemmas(text):
    return [t.lemma_.lower() for t in _NLP(text) if t.is_alpha and not t.is_stop and len(t.lemma_) > 2 and t.lemma_.lower() not in STOP]


def event_keywords(brief):
    lines = event_lines(brief)
    sets = [set(lemmas(l)) for l in lines]
    if not sets:
        return []
    from collections import Counter
    c = Counter(l for s in sets for l in s)
    generic = {l for l, k in c.items() if k > len(sets) / 2}
    return [s - generic for s in sets]


def kendall_tau(order):
    """tau-a of a sequence of first-mention positions against 0..n-1."""
    n = len(order)
    if n < 2:
        return 1.0
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = order[j] - order[i]
            if d > 0:
                conc += 1
            elif d < 0:
                disc += 1
    return (conc - disc) / (n * (n - 1) / 2)


def score(text, keysets):
    sents = [s for s in sentences(text) if s.strip()]
    sent_lem = [set(t.lemma_.lower() for t in d if t.is_alpha and not t.is_stop and len(t.lemma_) > 2 and t.lemma_.lower() not in STOP) for d in _NLP.pipe(sents, batch_size=64)]
    first = []
    for ks in keysets:
        need = MIN_HIT if len(ks) >= 4 else max(1, (len(ks) + 1) // 2)
        pos = None
        for i, sl in enumerate(sent_lem):
            if len(ks & sl) >= need:
                pos = i
                break
        first.append(pos)
    found = [(i, p) for i, p in enumerate(first) if p is not None]
    order = [p for _, p in sorted(found)]
    return {
        "tau": kendall_tau(order) if len(order) >= 2 else (1.0 if order else 0.0),
        "events_present": len(found) / len(keysets) if keysets else 0.0,
        "terminal_missing": 1.0 if keysets and first[-1] is None else 0.0,
        "first_missing": 1.0 if keysets and first[0] is None else 0.0,
        "n_events": len(keysets),
        "_first": first,
    }


def run(arm="A0"):
    runs_map = discover_runs()
    rows, cells, keycache, src_rows = [], [], {}, []
    for run in available_runs(runs_map):
        author, size, kind = runs_map[run]
        if author not in keycache:
            b = briefs(author)
            keycache[author] = {i: event_keywords(t) for i, t in b.items()}
            # ceiling: the author's own passage against its brief
            vals = [score(t, keycache[author][i]) for i, t in sources(author).items() if keycache[author].get(i)]
            if vals:
                src_rows.append({"run": f"{author} SOURCE", "author": author, "size": "-", "kind": "source", "n": len(vals),
                                 "means": {k: (st.mean([v[k] for v in vals]), st.pstdev([v[k] for v in vals])) for k in ("tau", "events_present", "terminal_missing")}})
        vals = []
        for gid, sample, text in gens(run, arm):
            ks = keycache[author].get(gid)
            if not ks:
                continue
            v = score(text, ks)
            vals.append(v)
            cells.append({"run": run, "author": author, "size": size, "kind": kind, "id": gid, "sample": sample,
                          "tau": v["tau"], "events_present": v["events_present"], "terminal_missing": v["terminal_missing"], "n_events": v["n_events"]})
        if vals:
            rows.append({"run": run, "author": author, "size": size, "kind": kind, "n": len(vals),
                         "means": {k: (st.mean([v[k] for v in vals]), st.pstdev([v[k] for v in vals])) for k in ("tau", "events_present", "terminal_missing")}})
    by_run = {r["run"]: r for r in rows}
    L = [f"# event_order (arm {arm}); tau = Kendall tau-a between brief order and first-mention order; SOURCE rows are the author's own passage against its brief", ""]
    for k in ("tau", "events_present", "terminal_missing"):
        L += [f"## {k}", "", "| run | author | size | kind | n | mean | sd |", "|---|---|---|---|---:|---:|---:|"]
        for r in src_rows + rows:
            m, s = r["means"][k]
            L.append(f"| {r['run']} | {r['author']} | {r['size']} | {r['kind']} | {r['n']} | {m:.3f} | {s:.3f} |")
        L += ["", "Replicate floor:", ""]
        for a, b in REPLICATES:
            if a in by_run and b in by_run:
                L.append(f"- {a} vs {b}: {by_run[b]['means'][k][0] - by_run[a]['means'][k][0]:+.3f}")
        L += ["", "Base vs adapter:", ""]
        key = {(r["author"], r["size"], r["kind"]): r["means"][k][0] for r in rows}
        for (author, size, kind), m in sorted(key.items()):
            if kind == "base" and (author, size, "adapter") in key:
                ad = key[(author, size, "adapter")]
                L.append(f"- {author} {size}: base {m:.3f} -> adapter {ad:.3f} ({ad - m:+.3f})")
        L.append("")
    out = os.path.join(RESULTS, f"event_order_{arm}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(CACHE, f"event_order_{arm}.json"), "w", encoding="utf-8") as f:
        json.dump({"cells": cells}, f)
    print("\n".join(L))
    print(f"-> {out}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "A0")
