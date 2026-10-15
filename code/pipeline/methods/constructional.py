"""S5 constructional profile: signed rhetorical-figure profile distance (RFPD,
R3) and the one-sided author-relative tell index (ARTI, R5), one
implementation, on the Mimesis rule-based detectors plus four measures of
our own.

For each feature f, rate r_f(text) per 1,000 words (openers and rhythm
features per 100 sentences). Calibrate mu_f, sigma_f on the author's own
REF + TRAIN chunks (never TEST, so the paired source passage is not in the
calibration). sigma is floored at SD_FLOOR so a figure the author never uses
does not produce an infinite z on one accidental hit. Per passage:
    z_f      = (r_f - mu_f) / max(sigma_f, SD_FLOOR)
    RFPD     = mean_f |z_f|             (signed profile distance, both directions)
    ARTI     = mean_f max(0, z_f)       (excess only: the tell index)
    ARTI_hard = same over the four constructions Patrick rejected by name
               (self-explanation, unheeded reversal, "the way a X" simile,
               declarative rating; Mimesis/docs/AUTHOR_FEEDBACK.md)
The per-feature signed z (run means) is the interpretable output.

The author's own TEST passages are scored as the self-distance row. The
DETECTORS.md false-positive audit (share of the author's own calibration
pieces that a feature fires on, and the author's mean rate) is written beside
the table so a feature that is really measuring the author is visible.

Feature choice is frozen here before any table is read. Excluded on purpose:
emoji, hashtags, LinkedIn phrases, dashes (normalise_punct already folds
them), leakage (a brief-gate concern, not a style one).
"""
from __future__ import annotations

import json
import os
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, REPLICATES, RESULTS, available_runs, discover_runs, gens, refs, sentences, sources, train_texts  # noqa: E402

sys.path.insert(0, r"C:\AI Coding Projects\Online_AI\Mimesis\src")
from mimesis_voice import rhetoric, rhetoric_ext  # noqa: E402

SD_FLOOR = 0.25
CHAIN_LEN = 4
_WORD = re.compile(r"\b[\w']+\b")

PER_1K = {
    "it_is_opener": rhetoric.find_it_is_openers,
    "way_simile": rhetoric.find_way_similes,
    "declarative_rating": rhetoric.find_declarative_ratings,
    "reversal": rhetoric.find_reversals,
    "self_explanation": rhetoric.find_self_explanations,
    "triad": rhetoric.find_triads,
    "antithesis": rhetoric.find_antithesis,
    "cleft": rhetoric.find_clefts,
    "closing_flourish": rhetoric.find_closing_flourish,
    "nominalization_pickup": rhetoric.find_nominalization_pickups,
    "meta_aside": rhetoric.find_meta_asides,
    "self_rating": rhetoric.find_self_ratings,
    "absence_punch": rhetoric.find_absence_punches,
    "comma_chain": lambda t: rhetoric.find_comma_chains(t, CHAIN_LEN),
    "participial_triad": rhetoric_ext.find_participial_triads,
    "negation_template": rhetoric_ext.find_negation_templates,
    "intensifier": rhetoric_ext.find_intensifiers,
    "generator_phrase": rhetoric_ext.find_generator_phrases,
    "fragment_couplet": rhetoric_ext.find_fragment_couplets,
    "personification": rhetoric_ext.find_personifications,
    "colon_twist": rhetoric_ext.find_colon_twists,
    "tail_twist": rhetoric_ext.find_tail_twists,
    "question_fragment": rhetoric_ext.find_question_fragments,
    "then_opener": rhetoric_ext.find_then_openers,
    "pointer_verdict": rhetoric_ext.find_pointer_verdicts,
    "announcer": rhetoric_ext.find_announcers,
    "does_pair": rhetoric_ext.find_does_pairs,
    "parallel_address": rhetoric_ext.find_parallel_address,
    "conversion": rhetoric_ext.find_conversions,
}
HARD = ["self_explanation", "reversal", "way_simile", "declarative_rating"]
_COPULA = re.compile(r"\b(?:is|was|are|were|be|been|being|am)\b", re.IGNORECASE)


def own_features(text):
    """Per 100 sentences: rhetorical questions, two-word opener anaphora,
    long-then-short rhythm; per 100 words: copula density."""
    sents = [s.strip() for s in sentences(text) if s.strip()]
    n = len(sents)
    if n == 0:
        return {"rhetorical_question": 0.0, "anaphora2": 0.0, "long_short": 0.0, "copula_density": 0.0}
    q = sum(1 for s in sents if s.endswith("?"))
    firsts = [tuple(re.sub(r"^[^A-Za-z]+", "", s).lower().split()[:2]) for s in sents]
    ana = sum(1 for i in range(1, n) if len(firsts[i]) == 2 and firsts[i] == firsts[i - 1])
    lens = [len(s.split()) for s in sents]
    ls = sum(1 for i in range(1, n) if lens[i - 1] > 25 and lens[i] <= 6)
    nw = len(_WORD.findall(text))
    return {
        "rhetorical_question": 100.0 * q / n,
        "anaphora2": 100.0 * ana / max(n - 1, 1),
        "long_short": 100.0 * ls / max(n - 1, 1),
        "copula_density": 100.0 * len(_COPULA.findall(text)) / max(nw, 1),
    }


def rates(text):
    nw = len(_WORD.findall(text))
    out = {k: (1000.0 * len(fn(text)) / nw if nw else 0.0) for k, fn in PER_1K.items()}
    out.update(own_features(text))
    return out


FEATURES = list(PER_1K) + ["rhetorical_question", "anaphora2", "long_short", "copula_density"]


def calibrate(author):
    texts = [t for t in refs(author) + train_texts(author) if len(_WORD.findall(t)) >= 200]
    rows = [rates(t) for t in texts]
    cal = {}
    for f in FEATURES:
        v = [r[f] for r in rows]
        mu = st.mean(v) if v else 0.0
        sd = st.pstdev(v) if len(v) > 1 else 0.0
        fired = sum(1 for x in v if x > 0) / len(v) if v else 0.0
        cal[f] = {"mu": mu, "sd": max(sd, SD_FLOOR), "sd_raw": sd, "fired": fired}
    return cal, len(texts)


def zvec(r, cal):
    return {f: (r[f] - cal[f]["mu"]) / cal[f]["sd"] for f in FEATURES}


WINSOR = 5.0


def summarise(z):
    vals = list(z.values())
    hard = [z[f] for f in HARD]
    w = [max(-WINSOR, min(WINSOR, x)) for x in vals]
    wh = [max(-WINSOR, min(WINSOR, x)) for x in hard]
    return {
        "rfpd": sum(abs(x) for x in vals) / len(vals),
        "arti": sum(max(0.0, x) for x in vals) / len(vals),
        "arti_hard": sum(max(0.0, x) for x in hard) / len(hard),
        # winsorised at |z| = 5: one cell with three hits on a figure the author
        # never uses carries z of 10+ and dominates a run mean otherwise
        "rfpd_w": sum(abs(x) for x in w) / len(w),
        "arti_w": sum(max(0.0, x) for x in w) / len(w),
        "arti_hard_w": sum(max(0.0, x) for x in wh) / len(wh),
    }


def run(arm="A0"):
    runs_map = discover_runs()
    cals, ncal, rows, cells, feat_rows = {}, {}, [], [], []
    for run in available_runs(runs_map):
        author, size, kind = runs_map[run]
        if author not in cals:
            cals[author], ncal[author] = calibrate(author)
            src = [summarise(zvec(rates(t), cals[author])) | {"z": zvec(rates(t), cals[author])} for t in sources(author).values()]
            rows.append({"run": f"{author} SOURCE", "author": author, "size": "-", "kind": "source", "n": len(src),
                         "means": {k: (st.mean([s[k] for s in src]), st.pstdev([s[k] for s in src])) for k in ("rfpd", "arti", "arti_hard", "rfpd_w", "arti_w", "arti_hard_w")},
                         "z": {f: st.mean([s["z"][f] for s in src]) for f in FEATURES}})
        vals = []
        for gid, sample, text in gens(run, arm):
            z = zvec(rates(text), cals[author])
            s = summarise(z)
            vals.append(s | {"z": z})
            cells.append({"run": run, "author": author, "size": size, "kind": kind, "id": gid, "sample": sample, **s, **{"z_" + f: z[f] for f in FEATURES}})
        if vals:
            rows.append({"run": run, "author": author, "size": size, "kind": kind, "n": len(vals),
                         "means": {k: (st.mean([v[k] for v in vals]), st.pstdev([v[k] for v in vals])) for k in ("rfpd", "arti", "arti_hard", "rfpd_w", "arti_w", "arti_hard_w")},
                         "z": {f: st.mean([v["z"][f] for v in vals]) for f in FEATURES}})
    by_run = {r["run"]: r for r in rows}
    L = [f"# constructional profile (arm {arm}); z per feature against the author's REF+TRAIN (sd floor {SD_FLOOR}); RFPD = mean |z|, ARTI = mean max(0,z), ARTI_hard = the four constructions Patrick rejected by name", ""]
    for k in ("rfpd", "arti", "arti_hard", "rfpd_w", "arti_w", "arti_hard_w"):
        L += [f"## {k}", "", "| run | author | size | kind | n | mean | sd |", "|---|---|---|---|---:|---:|---:|"]
        for r in rows:
            m, s = r["means"][k]
            L.append(f"| {r['run']} | {r['author']} | {r['size']} | {r['kind']} | {r['n']} | {m:.3f} | {s:.3f} |")
        L += ["", "Replicate floor:", ""]
        for a, b in REPLICATES:
            if a in by_run and b in by_run:
                L.append(f"- {a} vs {b}: {by_run[b]['means'][k][0] - by_run[a]['means'][k][0]:+.3f}")
        L += ["", "Base vs adapter:", ""]
        key = {(r["author"], r["size"], r["kind"]): r["means"][k][0] for r in rows if r["kind"] != "source"}
        for (author, size, kind), m in sorted(key.items()):
            if kind == "base" and (author, size, "adapter") in key:
                ad = key[(author, size, "adapter")]
                L.append(f"- {author} {size}: base {m:.3f} -> adapter {ad:.3f} ({ad - m:+.3f})")
        L.append("")
    # per-feature signed z, per author block
    L += ["## Per-feature signed z (run means); + = more than the author, - = less", ""]
    for author in sorted({r["author"] for r in rows}):
        block = [r for r in rows if r["author"] == author]
        L += [f"### {author} (calibrated on {ncal.get(author, 0)} REF+TRAIN chunks)", "",
              "| feature | author mean/1k | fired share | " + " | ".join(f"{r['run']}" for r in block) + " |",
              "|---|---:|---:|" + "---:|" * len(block)]
        for f in FEATURES:
            c = cals[author][f]
            L.append(f"| {f} | {c['mu']:.2f} | {c['fired']:.2f} | " + " | ".join(f"{r['z'][f]:+.2f}" for r in block) + " |")
        L.append("")
    out = os.path.join(RESULTS, f"constructional_{arm}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(CACHE, f"constructional_{arm}.json"), "w", encoding="utf-8") as f:
        json.dump({"cells": cells, "calibration": cals}, f)
    print("\n".join(L[: L.index("## Per-feature signed z (run means); + = more than the author, - = less")]))
    print(f"-> {out}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "A0")
