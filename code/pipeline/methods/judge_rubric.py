"""S10 two-block judge rubric (R2 construction C1-C5 + R3 craft S1-S7), with
the bias controls the reports converged on.

Per passage, one call per judge per rubric order. Absolute 0-10 integers per
subscore, and for any subscore below 7 a verbatim quotation of at most 20
words as evidence (auditable against the prose). The judge sees: one
reference passage BY THE SAME AUTHOR (from REF, never the paired source) as a
register target, then the candidate. No author name, no arm, no model, no
brief. Calibration items ride in every batch unlabelled: five of the author's
own TEST passages and sentence-shuffled versions of the same five. Two rubric
orders (forward, reversed) so order stability can be reported. Judges are
never Qwen (every generator is Qwen). Uses dr.core.api_call, so every call is
cached, ledgered and capped by config.API_BUDGET_USD; this script adds its
own per-invocation cap (--cap-usd) and runs calls concurrently (--workers).

Outputs: results/judge/<judge-slug>_<order>.jsonl (append, resumable), and
results/judge_rubric.md (per-run means, calibration gate per judge, order
stability, inter-judge quadratic-weighted kappa, subscore correlation matrix).

    python judge_rubric.py --dry                 # count calls, estimate cost
    python judge_rubric.py --limit 5             # smoke: 5 cells per run
    python judge_rubric.py                       # the fourteen scale runs, sample 0, arm A0
    python judge_rubric.py --summary             # rebuild the report only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import statistics as st
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DR, RESULTS, gens, read_jsonl, refs, sentences, sources  # noqa: E402

sys.path.insert(0, DR)
from dr import config  # noqa: E402
from dr.core import api_call  # noqa: E402

OUT = os.path.join(RESULTS, "judge")
os.makedirs(OUT, exist_ok=True)

DEFAULT_RUNS = [
    "patrick_v2_base17b", "patrick_v2_paire6_17b", "patrick_v2_base4b", "patrick_v2_paire6_4b",
    "patrick_v2_base8b", "patrick_v2_paire6_8b", "patrick_v2_base14b", "patrick_v2_paire6_14b",
    "chesterton_base4b", "chesterton_paire6_4b", "chesterton_base8b", "chesterton_paire6_8b",
    "chesterton_base14b", "chesterton_paire6_14b",
]
WORD_CAP = 900
N_CAL = 5

SUBSCORES = [
    ("C1", "Referent clarity", "Can you say at every point who each pronoun refers to, and is each character designated stably? 10: one designation per character throughout. 5: two or three designations, resolvable with effort. 0: the referent changes without warning, or a character appears who was never introduced."),
    ("C2", "Sentence-to-sentence advancement", "Does each sentence add a proposition rather than restate the previous one in new words? 10: each sentence is licensed by the previous one and moves. 5: occasional restatement, recognisably rhetorical. 0: the passage circles, restating the same content in fresh wording."),
    ("C3", "Event and state consistency", "Are asserted facts, states and character knowledge held? 10: nothing contradicts. 5: one minor slip. 0: a load-bearing contradiction (a character acts after being described as dead; an object is in two places)."),
    ("C4", "Scene logic and arc completion", "Does the passage form a scene with a beginning, a turn and a landing? 10: the arc completes. 5: completes but the landing is thin. 0: it does not land, it stops mid-thought or mid-clause."),
    ("C5", "Circling and stall", "Does the second half progress or revisit the first? 10: no revisitation. 5: one loop back. 0: the second half restates the first."),
    ("S1", "Opening move", "10: a blunt or inverted opener that commits. 5: a generic declarative. 0: scene-setting participial or 'The X stood' opener with nothing at stake."),
    ("S2", "Figure execution", "10: figures (similes, metaphors, parallel constructions) land where placed and do work. 5: present, some forced. 0: figures absent or mechanical."),
    ("S3", "Figure restraint", "10: no figure repeats past its effect. 5: occasional inflation. 0: escalating triads, 'not X, not Y, not Z' runs, repeated sentence openers, the same construction used until it is noise."),
    ("S4", "Register movement", "10: the register shifts and returns, tracking content. 5: unmotivated variation. 0: one register held flat for the whole passage."),
    ("S5", "Sentence-level stopping", "10: sentences stop when done. 5: occasional self-explanation. 0: sentences explain themselves after the point ('which means', 'that is the part that', a clause restating what the previous clause showed)."),
    ("S6", "Perspective control", "10: perspective held, or moved on purpose. 5: mostly stable. 0: the focaliser drifts, referents float."),
    ("S7", "Immersion", "10: a reader continues without noticing the prose. 5: readable, does not compel. 0: the reader is aware of a machine writing."),
]
KEYS = [k for k, _, _ in SUBSCORES]

SYSTEM = ("You are a careful reader of literary prose. You score passages on fixed subscores with integer scores from 0 to 10. "
          "Length is not evidence of quality. You never reward a passage for being longer or more elaborate. "
          "You answer with JSON only.")


def build_user(reference, candidate, order):
    subs = SUBSCORES if order == "fwd" else list(reversed(SUBSCORES))
    rubric = "\n".join(f"{k} {name}: {desc}" for k, name, desc in subs)
    keys = ", ".join(f'"{k}"' for k, _, _ in subs)
    return (
        "REFERENCE PASSAGE (by the same author; use it only as the register target, not as content to compare):\n\n"
        f"{reference}\n\n"
        "CANDIDATE PASSAGE (the passage you are scoring; it may end at a word cap, so score C4 on whether the writing was heading toward a landing, not on whether the last sentence is complete):\n\n"
        f"{candidate}\n\n"
        "SUBSCORES:\n" + rubric + "\n\n"
        "Return a single JSON object with integer scores for " + keys + ", and a key \"evidence\" holding an object that, "
        "for every subscore you scored below 7, maps the subscore key to one verbatim quotation of at most 20 words from the CANDIDATE that justifies the score. No other text."
    )


def cap_words(text, n=WORD_CAP):
    w = text.split()
    return text if len(w) <= n else " ".join(w[:n])


def shuffle_sentences(text, seed):
    s = [x for x in sentences(text) if x.strip()]
    R = random.Random(seed)
    R.shuffle(s)
    return " ".join(s)


def calibration_items(author):
    src = sources(author)
    ids = sorted(src)[:N_CAL]
    items = []
    for i in ids:
        items.append({"id": i, "kind": "author", "text": src[i]})
        items.append({"id": i, "kind": "shuffled", "text": shuffle_sentences(src[i], seed=int(hashlib.sha1(i.encode()).hexdigest()[:8], 16))})
    return items


def reference_for(author):
    r = refs(author)
    return cap_words(r[0], 500) if r else ""


_JSON = re.compile(r"\{.*\}", re.S)


def parse(text):
    if not text:
        return None
    m = _JSON.search(text)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except Exception:
        return None
    out = {}
    for k in KEYS:
        v = d.get(k)
        if isinstance(v, (int, float)):
            out[k] = int(max(0, min(10, round(v))))
    if len(out) < len(KEYS):
        return None
    ev = d.get("evidence")
    out["evidence"] = ev if isinstance(ev, dict) else {}
    return out


def slug(model):
    return re.sub(r"[^a-z0-9]+", "_", model.lower()).strip("_")


def load_done(path):
    if not os.path.exists(path):
        return set()
    return {(r["run"], r["id"], r["sample"], r["kind"]) for r in read_jsonl(path)}


def author_of(run):
    return run.split("_base")[0].split("_paire6")[0].split("_pair")[0].split("_size")[0].replace(" CAL", "")   # _size: within-author series runs (2026-09-10)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=",".join(DEFAULT_RUNS))
    ap.add_argument("--judges", default=",".join(config.JUDGES))
    ap.add_argument("--orders", default="fwd,rev")
    ap.add_argument("--arm", default="A0")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--cap-usd", type=float, default=4.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--no-cal", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--max-tokens", type=int, default=700, help="completion cap; MiniMax needs ~1400 (empty completions at 700)")
    ap.add_argument("--retry-failed", action="store_true", help="drop unparsed rows for the selected judges/orders, then run only those cells")
    a = ap.parse_args()
    if a.summary:
        summarise()
        return
    if a.retry_failed:
        for judge in [j for j in a.judges.split(",") if j]:
            for order in [o for o in a.orders.split(",") if o]:
                path = os.path.join(OUT, f"{slug(judge)}_{order}.jsonl")
                if not os.path.exists(path):
                    continue
                rows = read_jsonl(path)
                keep = [r for r in rows if r.get("ok")]
                with open(path, "w", encoding="utf-8") as f:
                    for r in keep:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                print(f"{judge} {order}: dropped {len(rows) - len(keep)} unparsed rows, kept {len(keep)}")
    runs = [r for r in a.runs.split(",") if r]
    judges = [j for j in a.judges.split(",") if j]
    orders = [o for o in a.orders.split(",") if o]
    work = []
    for run in runs:
        author = author_of(run)
        cells = [(gid, s, t) for gid, s, t in gens(run, a.arm) if s == a.sample]
        if a.limit:
            cells = cells[: a.limit]
        for gid, s, t in cells:
            work.append({"run": run, "author": author, "id": gid, "sample": s, "kind": "gen", "text": cap_words(t)})
    if not a.no_cal:
        for author in sorted({w["author"] for w in work}):
            for it in calibration_items(author):
                work.append({"run": f"{author} CAL", "author": author, "id": it["id"], "sample": 0, "kind": it["kind"], "text": cap_words(it["text"])})
    refcache = {au: reference_for(au) for au in {w["author"] for w in work}}
    tasks = []
    handles = {}
    for judge in judges:
        for order in orders:
            path = os.path.join(OUT, f"{slug(judge)}_{order}.jsonl")
            done = load_done(path)
            handles[(judge, order)] = path
            for w in work:
                if (w["run"], w["id"], w["sample"], w["kind"]) not in done:
                    tasks.append((judge, order, w))
    print(f"{len(work)} passages; {len(tasks)} calls to make ({len(judges)} judges x {len(orders)} orders, minus cached rows)")
    if a.dry:
        return
    lock = threading.Lock()
    spent = {"usd": 0.0, "stop": False, "ok": 0, "fail": 0}

    def one(judge, order, w):
        if spent["stop"]:
            return None
        user = build_user(refcache[w["author"]], w["text"], order)
        text, meta = api_call(judge, SYSTEM, user, max_tokens=a.max_tokens, temperature=0.0, tag="rubric")
        parsed = parse(text)
        rec = {"run": w["run"], "author": w["author"], "id": w["id"], "sample": w["sample"], "kind": w["kind"],
               "judge": judge, "order": order, "ok": parsed is not None, "raw": (text or "")[:1200],
               "usd": meta.get("usd", 0.0), "cached": bool(meta.get("cached"))}
        if parsed:
            rec.update(parsed)
        else:
            rec["error"] = meta.get("error")
        with lock:
            if not meta.get("cached"):
                spent["usd"] += float(meta.get("usd", 0.0) or 0.0)
            spent["ok" if parsed else "fail"] += 1
            with open(handles[(judge, order)], "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if spent["usd"] > a.cap_usd and not spent["stop"]:
                spent["stop"] = True
                print(f"cap USD {a.cap_usd} reached ({spent['usd']:.2f}); no new calls will start", flush=True)
            n = spent["ok"] + spent["fail"]
            if n % 100 == 0:
                print(f"  {n}/{len(tasks)} done, {spent['fail']} unparsed, USD {spent['usd']:.2f}", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(one, j, o, w) for j, o, w in tasks]
        for fu in as_completed(futs):
            fu.result()
    print(f"done: {spent['ok']} scored, {spent['fail']} unparsed, session spend USD {spent['usd']:.2f}")
    summarise()


def qwk(x, y, k=11):
    """Quadratic-weighted kappa on integer scores 0..10."""
    n = len(x)
    if n == 0:
        return float("nan")
    O = [[0] * k for _ in range(k)]
    for a_, b_ in zip(x, y):
        O[a_][b_] += 1
    hx = [sum(1 for v in x if v == i) for i in range(k)]
    hy = [sum(1 for v in y if v == i) for i in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = ((i - j) ** 2) / ((k - 1) ** 2)
            num += w * O[i][j]
            den += w * hx[i] * hy[j] / n
    return 1 - num / den if den > 0 else float("nan")


def summarise():
    import glob
    from scipy.stats import spearmanr
    recs = []
    for p in glob.glob(os.path.join(OUT, "*.jsonl")):
        recs += [r for r in read_jsonl(p) if r.get("ok")]
    if not recs:
        print("no scored records")
        return
    L = ["# Judge rubric (arm A0, sample 0); 0-10 per subscore; construction C1-C5, craft S1-S7", "",
         "Calibration rows: `author` = the author's own held-out passages, `shuffled` = the same passages with sentences shuffled (unlabelled to the judge).", ""]
    for judge in sorted({r["judge"] for r in recs}):
        L += [f"## {judge} (order fwd; mean per subscore)", "", "| run | kind | n | " + " | ".join(KEYS) + " | mean |", "|---|---|---:|" + "---:|" * (len(KEYS) + 1)]
        groups = {}
        for r in recs:
            if r["judge"] == judge and r["order"] == "fwd":
                groups.setdefault((r["run"], r["kind"]), []).append(r)
        for (run, kind), rs in sorted(groups.items()):
            means = [st.mean([r[k] for r in rs]) for k in KEYS]
            L.append(f"| {run} | {kind} | {len(rs)} | " + " | ".join(f"{m:.1f}" for m in means) + f" | {st.mean(means):.2f} |")
        for author in sorted({r["author"] for r in recs}):
            cal_a = [r for r in recs if r["judge"] == judge and r["order"] == "fwd" and r["kind"] == "author" and r["author"] == author]
            cal_s = [r for r in recs if r["judge"] == judge and r["order"] == "fwd" and r["kind"] == "shuffled" and r["author"] == author]
            gen = [r for r in recs if r["judge"] == judge and r["order"] == "fwd" and r["kind"] == "gen" and r["author"] == author]
            if cal_a and cal_s and gen:
                ma = st.mean([st.mean([r[k] for k in KEYS]) for r in cal_a])
                ms = st.mean([st.mean([r[k] for k in KEYS]) for r in cal_s])
                mg = st.mean([st.mean([r[k] for k in KEYS]) for r in gen])
                c2 = st.mean([r["C2"] for r in cal_a]) - st.mean([r["C2"] for r in cal_s])
                c5 = st.mean([r["C5"] for r in cal_a]) - st.mean([r["C5"] for r in cal_s])
                ok = ma > mg and max(c2, c5) >= 3
                L += ["", f"Calibration gate, {author}: author passages {ma:.2f}, shuffled {ms:.2f}, generations {mg:.2f}; author minus shuffled on C2 {c2:+.2f}, on C5 {c5:+.2f}; "
                      f"gate (author above generations, and real minus shuffled >= 3 on C2 or C5): {'PASS' if ok else 'FAIL'}"]
        fwd = {(r["run"], r["id"], r["kind"]): r for r in recs if r["judge"] == judge and r["order"] == "fwd"}
        rev = {(r["run"], r["id"], r["kind"]): r for r in recs if r["judge"] == judge and r["order"] == "rev"}
        common = sorted(set(fwd) & set(rev))
        if len(common) >= 8:
            L += ["", "Order stability (fwd vs rev rubric order), per subscore: Spearman rho and mean absolute shift:", ""]
            for k in KEYS:
                x = [fwd[c][k] for c in common]
                y = [rev[c][k] for c in common]
                rho = spearmanr(x, y).correlation
                L.append(f"- {k}: rho {rho:+.2f}, mean |shift| {st.mean(abs(p - q) for p, q in zip(x, y)):.2f} (n={len(common)})")
        L.append("")
    js = sorted({r["judge"] for r in recs})
    if len(js) >= 2:
        L += ["## Inter-judge agreement (order fwd), quadratic-weighted kappa per subscore", ""]
        for i in range(len(js)):
            for j in range(i + 1, len(js)):
                A = {(r["run"], r["id"], r["kind"]): r for r in recs if r["judge"] == js[i] and r["order"] == "fwd"}
                B = {(r["run"], r["id"], r["kind"]): r for r in recs if r["judge"] == js[j] and r["order"] == "fwd"}
                common = sorted(set(A) & set(B))
                if len(common) < 8:
                    continue
                L.append(f"- {js[i]} vs {js[j]} (n={len(common)}): " + ", ".join(f"{k} {qwk([A[c][k] for c in common], [B[c][k] for c in common]):.2f}" for k in KEYS))
        L.append("")
    gen = [r for r in recs if r["order"] == "fwd" and r["kind"] == "gen"]
    if len(gen) >= 20:
        L += ["## Subscore Spearman correlation matrix (generations, all judges, order fwd)", "", "| | " + " | ".join(KEYS) + " |", "|---|" + "---:|" * len(KEYS)]
        for k1 in KEYS:
            row = []
            for k2 in KEYS:
                rho = spearmanr([r[k1] for r in gen], [r[k2] for r in gen]).correlation
                row.append(f"{rho:+.2f}")
            L.append(f"| {k1} | " + " | ".join(row) + " |")
        L.append("")
    total = sum(float(r.get("usd", 0) or 0) for p in glob.glob(os.path.join(OUT, "*.jsonl")) for r in read_jsonl(p) if not r.get("cached"))
    L.append(f"Total judge spend logged in these files: USD {total:.2f}")
    out = os.path.join(RESULTS, "judge_rubric.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
