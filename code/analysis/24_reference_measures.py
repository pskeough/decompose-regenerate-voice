"""24_reference_measures -- the eval-cache measures computed on the authors' own passages.

Script 15 could not calibrate fourteen instruments because the eval caches hold per-cell
values for generations only: the caches keep one mean and one standard deviation of the
author's own passages under `source_stats` and nothing at all for other authors, so neither
the author distribution H nor a stranger pool P exists for `per`, `otd_js`, `hapax_w300`,
`cpd_z`, `arti_w` and the rest. This script computes those measures on every author's own
passages -- the held-out test passages and the reference passages -- using the pipeline's own
measure code, and then puts the generations on the same author-calibrated scale that the
embeddings got in script 23.

Blocks.

1. Measure. The pure functions of scripts/legacy/methods/{per,otd,psd,cpd,lexdiv,
   event_order,constructional}.py and scripts/legacy/dr/core.py are copied here verbatim
   (the legacy files are not modified and not imported: legacy/methods/common.py points at
   the original pipeline paths and legacy/dr/core.py creates directories on import).
   Every author passage gets: per (600-word cap) and per_uncapped, the opener-class profile,
   the paragraph-shape profile, the cadence profile, the windowed lexical-diversity triple,
   the constructional rate vector, and -- for test passages, which have briefs -- the
   event-order triple against the passage's own brief.

2. Anchor. Measures that are defined against something (otd_js, cv_diff, w1_logpara,
   burst_an_diff, cpd_z) are computed for a passage against the author's REFERENCE set,
   leaving the passage out when it is itself in that set. The constructional z scores use
   the author's REF+TRAIN calibration, with a leave-one-out mean and sd for a reference
   passage. A stranger's passage is measured against the same author's anchor, which is what
   makes P comparable with H.

3. Calibrate. H = the author's own test passages, P = the register-matched other authors'
   test passages (the same class assignment script 23 uses), G = the arm-A0 cells. Positions,
   distributional fidelity F with a brief-cluster bootstrap, and the author-region rate R on
   (per, otd_js, hapax_w300) added to the two embedding instruments of script 23.

Reads data/authors, data/master, data/eval_results and analysis/23_register_matched_pool.
Writes analysis/24_reference_measures only.
"""
from __future__ import annotations

import itertools
import json
import math
import os
import re
import statistics as st
import sys
import time
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *  # noqa: F401,F403

from scipy.stats import wasserstein_distance

T0 = time.time()
OUTD = outdir("24_reference_measures")
NBOOT = 400
Z95 = 1.959963984540054
DROP_AUTHOR = "patrick"          # v1 chunking control, same person as patrick_v2 (see script 23)
STUDY = sorted([a for a in AUTHOR_CLASS if a != DROP_AUTHOR])
CLASS_MEMBERS = defaultdict(list)
for _a in STUDY:
    CLASS_MEMBERS[AUTHOR_CLASS[_a]].append(_a)

# ===========================================================================
# 1. measure code, copied from the pipeline (legacy files untouched)
# ===========================================================================
# --- scripts/legacy/dr/core.py -------------------------------------------------------
_SENT_SPLIT = re.compile(r"(?<=[.!?])[\"'\u201d\u2019)\]]*\s+")
_CORE_WORD = re.compile(r"[A-Za-z][A-Za-z'\u2019-]*")
_DDASH = re.compile(r"\s*--+\s*")
_UNDER = re.compile(r"(?<![A-Za-z0-9])_([^_\n]{1,80})_(?![A-Za-z0-9])")


def sentences(text: str):                                   # dr/core.py
    return [s for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def paragraphs(text: str):                                  # dr/core.py
    ps = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return ps or [text.strip()]


def normalise_punct(text: str) -> str:                      # dr/core.py
    t = _UNDER.sub(r"\1", text)
    return _DDASH.sub("\u2014", t)


# --- scripts/legacy/methods/common.py ------------------------------------------------
_GLYPHS = {"\u2019": "'", "\u2018": "'", "\u201b": "'", "\u2032": "'",
           "\u201c": '"', "\u201d": '"', "\u201f": '"', "\u2033": '"',
           "\u2026": "...", "\u00a0": " "}


def fold_glyphs(text: str) -> str:                          # methods/common.py
    for a, b in _GLYPHS.items():
        text = text.replace(a, b)
    return text


def norm(text: str) -> str:                                 # methods/common.py (FOLD_GLYPHS on)
    return fold_glyphs(normalise_punct(text))


def truncate_words(text, n):                                # methods/common.py
    if n is None:
        return text
    out, count = [], 0
    for para in text.split("\n"):
        w = para.split()
        if count + len(w) <= n:
            out.append(para)
            count += len(w)
        else:
            out.append(" ".join(w[: n - count]))
            break
    return "\n".join(out)


def sent_lengths(text):                                     # methods/common.py
    return [len(s.split()) for s in sentences(text) if s.strip()]


# --- scripts/legacy/methods/per.py ---------------------------------------------------
ECHO_FRAC = 0.25
PER_STOP = set("""
a an the and or but nor so yet for of in on at to from by with without into onto over under
about above below between through during before after again further then once here there
when where why how all any both each few more most other some such no not only own same than
too very can will just don should now is are was were be been being have has had having do
does did doing i me my myself we our ours ourselves you your yours yourself yourselves he him
his himself she her hers herself it its itself they them their theirs themselves what which
who whom this that these those am as if because until while up down out off would could
might must shall may also one two said says say like get got go went come came see saw made
make take took thing things way still even much many back way
""".split())
_PER_WORD = re.compile(r"[A-Za-z][A-Za-z'-]+")


def content_words(sent):                                    # methods/per.py
    return [w.lower() for w in _PER_WORD.findall(sent) if len(w) > 2 and w.lower() not in PER_STOP]


def per_measure(text):                                      # methods/per.py: per()
    seen = set()
    n, echo = 0, 0
    for s in sentences(text):
        cw = sorted(set(content_words(s)))
        if len(cw) < 2:
            continue
        pairs = set(itertools.combinations(cw, 2))
        n += 1
        if len(pairs & seen) / len(pairs) > ECHO_FRAC:
            echo += 1
        seen |= pairs
    return {"per": echo / n if n else 0.0, "per_n_sent": n}


# --- scripts/legacy/methods/otd.py ---------------------------------------------------
CLASSES = ["QUOTE", "CONJ", "DISC", "SUBORD", "PP", "ADV", "PART", "PRON", "NP", "OTHER"]
OTD_DISC = set("""however then now still yet so meanwhile anyway besides instead nevertheless nonetheless
otherwise moreover indeed finally first second third next later afterwards perhaps maybe also again
thus hence therefore well today tonight yesterday tomorrow once sometimes suddenly""".split())
OTD_SUB = set("""when if although though because while as since until unless whereas whenever wherever
before after once whether even""".split())

import spacy  # noqa: E402
_NLP_TAG = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
_NLP_LEM = spacy.load("en_core_web_sm", disable=["parser", "ner"])


def _opener_class_from_doc(s, doc):                         # methods/otd.py: opener_class()
    st_ = s.strip()
    if not st_:
        return "OTHER"
    if st_[0] in "\"'\u201c\u2018":
        return "QUOTE"
    toks = [t for t in doc if not t.is_punct and not t.is_space]
    if not toks:
        return "OTHER"
    t = toks[0]
    w = t.text.lower()
    if t.pos_ == "CCONJ" or w in ("and", "but", "or", "nor", "yet", "so"):
        return "CONJ" if w != "so" or t.pos_ == "CCONJ" else "DISC"
    if w in OTD_DISC:
        return "DISC"
    if t.pos_ == "SCONJ" or w in OTD_SUB:
        return "SUBORD"
    if t.pos_ == "ADP":
        return "PP"
    if t.pos_ == "ADV":
        return "ADV"
    if t.pos_ in ("VERB", "AUX") and t.tag_ in ("VBG", "VBN"):
        return "PART"
    if t.pos_ == "PRON" or w in ("i", "you", "he", "she", "it", "we", "they", "there", "this", "that", "these", "those"):
        return "PRON"
    if t.pos_ in ("DET", "NOUN", "PROPN", "ADJ", "NUM"):
        return "NP"
    if t.pos_ in ("VERB", "AUX"):
        return "OTHER"
    return "OTHER"


def otd_profiles_batch(texts):
    """methods/otd.py: profile(), but the six-token opener stubs of every passage go through
    one nlp.pipe call instead of one _NLP call per sentence. Same tagger, same annotations."""
    stubs, owner = [], []
    sents_per = []
    for i, t in enumerate(texts):
        ss = [s for s in sentences(t) if s.strip()]
        sents_per.append(ss)
        for s in ss:
            stubs.append(" ".join(s.split()[:6]))
            owner.append(i)
    docs = list(_NLP_TAG.pipe(stubs, batch_size=512))
    counts = [Counter() for _ in texts]
    k = 0
    for i, ss in enumerate(sents_per):
        for s in ss:
            counts[i][_opener_class_from_doc(s, docs[k])] += 1
            k += 1
    out = []
    for i, c in enumerate(counts):
        n = sum(c.values())
        out.append(np.array([(c[cl] / n if n else 0.0) for cl in CLASSES], dtype=float))
    return out


def js_matrix(P, Q):
    """sqrt of the base-2 Jensen-Shannon divergence between every row of P and every row of Q
    (methods/otd.py: _js, vectorised)."""
    P = P[:, None, :]
    Q = Q[None, :, :]
    M = (P + Q) / 2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        kp = np.where(P > 0, P * np.log2(np.where(M > 0, P / np.where(M > 0, M, 1), 1)), 0.0).sum(-1)
        kq = np.where(Q > 0, Q * np.log2(np.where(M > 0, Q / np.where(M > 0, M, 1), 1)), 0.0).sum(-1)
    return np.sqrt(np.maximum(0.0, (kp + kq) / 2.0))


# --- scripts/legacy/methods/psd.py ---------------------------------------------------
_W1Q = np.linspace(0.0, 1.0, 101)


def psd_profile(text):                                      # methods/psd.py: profile()
    paras = [p for p in paragraphs(text) if p.strip()]
    pw = [len(p.split()) for p in paras]
    ps = [len([s for s in sentences(p) if s.strip()]) for p in paras]
    n = len(pw)
    cv = st.pstdev(pw) / st.mean(pw) if n > 1 and st.mean(pw) > 0 else 0.0
    cvs = st.pstdev(ps) / st.mean(ps) if n > 1 and st.mean(ps) > 0 else 0.0
    first_ratio = []
    for p in paras:
        sl = [len(s.split()) for s in sentences(p) if s.strip()]
        if len(sl) >= 2:
            first_ratio.append(sl[0] / st.mean(sl))
    logpara = [math.log(max(x, 1)) for x in pw]
    return {"para_n": n, "para_mean_words": st.mean(pw) if pw else 0.0,
            "para_mean_sents": st.mean(ps) if ps else 0.0, "para_cv_words": cv, "para_cv_sents": cvs,
            "first_sent_ratio": st.mean(first_ratio) if first_ratio else 1.0,
            "logpara_q": np.quantile(logpara, _W1Q) if logpara else np.zeros(101)}


# --- scripts/legacy/methods/cpd.py ---------------------------------------------------
def autocorr(x, lag):                                       # methods/cpd.py
    n = len(x)
    if n <= lag + 2:
        return 0.0
    m = st.mean(x)
    v = sum((a - m) ** 2 for a in x)
    if v == 0:
        return 0.0
    return sum((x[i] - m) * (x[i + lag] - m) for i in range(n - lag)) / v


def burstiness_an(x):                                       # methods/cpd.py
    n = len(x)
    if n < 3:
        return 0.0
    m, s = st.mean(x), st.pstdev(x)
    if m == 0:
        return 0.0
    r = s / m
    num = math.sqrt(n + 1) * r - math.sqrt(n - 1)
    den = (math.sqrt(n + 1) - 2) * r + math.sqrt(n - 1)
    return num / den if den != 0 else 0.0


CPD_COMPS = ["lag1", "lag2", "lag3", "burst_an", "q90_q50", "q50_q10"]


def cpd_profile(text):                                      # methods/cpd.py: profile()
    x = sent_lengths(text)
    if len(x) < 4:
        return {"lag1": 0.0, "lag2": 0.0, "lag3": 0.0, "burst_an": 0.0, "burst_b": 0.0,
                "q90_q50": 1.0, "q50_q10": 1.0, "sent_cv": 0.0, "n_sent": len(x)}
    q10, q50, q90 = np.quantile(x, [0.1, 0.5, 0.9])
    m, s = st.mean(x), st.pstdev(x)
    return {"lag1": autocorr(x, 1), "lag2": autocorr(x, 2), "lag3": autocorr(x, 3),
            "burst_an": burstiness_an(x), "burst_b": (s - m) / (s + m) if (s + m) > 0 else 0.0,
            "q90_q50": q90 / q50 if q50 else 1.0, "q50_q10": q50 / max(q10, 1.0),
            "sent_cv": s / m if m else 0.0, "n_sent": len(x)}


# --- scripts/legacy/methods/lexdiv.py ------------------------------------------------
LEX_WINDOW, LEX_MIN = 300, 200
_LEX_TOK = re.compile(r"[A-Za-z][A-Za-z'-]*")


def lex_tokens(text):                                       # methods/lexdiv.py
    return [t.lower() for t in _LEX_TOK.findall(text)]


def mattr_w(toks, w=50):                                    # methods/lexdiv.py: mattr()
    if len(toks) < w:
        return len(set(toks)) / len(toks) if toks else 0.0
    return sum(len(set(toks[i:i + w])) / w for i in range(len(toks) - w + 1)) / (len(toks) - w + 1)


def _mtld_one(toks, thr=0.72):                              # methods/lexdiv.py
    factors, types, count = 0.0, set(), 0
    for t in toks:
        types.add(t)
        count += 1
        if len(types) / count <= thr:
            factors += 1
            types, count = set(), 0
    if count > 0:
        ttr = len(types) / count
        factors += (1 - ttr) / (1 - thr) if ttr > thr else 1.0
    return len(toks) / factors if factors else float(len(toks))


def mtld_w(toks, thr=0.72):                                 # methods/lexdiv.py: mtld()
    if len(toks) < 50:
        return float("nan")
    return (_mtld_one(toks, thr) + _mtld_one(list(reversed(toks)), thr)) / 2


def lexdiv_measure(text):                                   # methods/lexdiv.py: measure()
    toks = lex_tokens(text)
    if len(toks) < LEX_MIN:
        return {}
    w = toks[:LEX_WINDOW]
    counts = Counter(w)
    v1 = sum(1 for c in counts.values() if c == 1)
    return {"hapax_w300": v1 / len(w), "ttr_w300": len(counts) / len(w),
            "mattr50_w300": mattr_w(w, 50), "mtld_w300": mtld_w(w), "n_tok": len(toks)}


# --- scripts/legacy/methods/event_order.py -------------------------------------------
EO_MIN_HIT = 2
EO_STOP = set("""a an the and or but of in on at to from by with into onto over under about
above below between through during before after then once here there when where why how
all any both each few more most other some such no not only own same than too very can will
just should now is are was were be been being have has had having do does did doing i me my
we our you your he him his she her it its they them their what which who whom this that these
those am as if because until while up down out off would could might must shall may also one
two say tell speaker listener narrator character person people reader passage describe
describes mention mentions note notes recount recounts explain explains express expresses
acknowledge acknowledges""".split())
_EO_EVENTS = re.compile(r"EVENTS, IN ORDER:\s*\n(.*?)(?:\n[A-Z][A-Z ]+:|\Z)", re.S)
_EO_NUM = re.compile(r"^\s*\d+[.)]\s*(.+)$")


def event_lines(brief):                                     # methods/event_order.py
    m = _EO_EVENTS.search(brief)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        mm = _EO_NUM.match(line)
        if mm:
            out.append(mm.group(1).strip())
    return out


def _lemset(doc):
    return set(t.lemma_.lower() for t in doc
               if t.is_alpha and not t.is_stop and len(t.lemma_) > 2 and t.lemma_.lower() not in EO_STOP)


def event_keywords(brief):                                  # methods/event_order.py
    lines = event_lines(brief)
    if not lines:
        return []
    sets = [_lemset(d) for d in _NLP_LEM.pipe(lines, batch_size=64)]
    c = Counter(l for s in sets for l in s)
    generic = {l for l, k in c.items() if k > len(sets) / 2}
    return [s - generic for s in sets]


def kendall_tau(order):                                     # methods/event_order.py
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


def eo_score(text, keysets):                                # methods/event_order.py: score()
    sents = [s for s in sentences(text) if s.strip()]
    sent_lem = [_lemset(d) for d in _NLP_LEM.pipe(sents, batch_size=64)]
    first = []
    for ks in keysets:
        need = EO_MIN_HIT if len(ks) >= 4 else max(1, (len(ks) + 1) // 2)
        pos = None
        for i, sl in enumerate(sent_lem):
            if len(ks & sl) >= need:
                pos = i
                break
        first.append(pos)
    found = [(i, p) for i, p in enumerate(first) if p is not None]
    order = [p for _, p in sorted(found)]
    return {"tau": kendall_tau(order) if len(order) >= 2 else (1.0 if order else 0.0),
            "events_present": len(found) / len(keysets) if keysets else 0.0,
            "terminal_missing": 1.0 if keysets and first[-1] is None else 0.0,
            "n_events": len(keysets)}


# --- scripts/legacy/methods/constructional.py ----------------------------------------
CONSTRUCTIONAL_OK, CONSTRUCTIONAL_WHY = True, ""
try:
    sys.path.insert(0, r"C:\AI Coding Projects\Online_AI\Mimesis\src")
    from mimesis_voice import rhetoric, rhetoric_ext  # noqa: E402
except Exception as _e:                                     # the measure is skipped, loudly
    CONSTRUCTIONAL_OK, CONSTRUCTIONAL_WHY = False, repr(_e)[:200]

SD_FLOOR, CHAIN_LEN, WINSOR = 0.25, 4, 5.0
_C_WORD = re.compile(r"\b[\w']+\b")
_COPULA = re.compile(r"\b(?:is|was|are|were|be|been|being|am)\b", re.IGNORECASE)
if CONSTRUCTIONAL_OK:
    PER_1K = {                                              # methods/constructional.py
        "it_is_opener": rhetoric.find_it_is_openers, "way_simile": rhetoric.find_way_similes,
        "declarative_rating": rhetoric.find_declarative_ratings, "reversal": rhetoric.find_reversals,
        "self_explanation": rhetoric.find_self_explanations, "triad": rhetoric.find_triads,
        "antithesis": rhetoric.find_antithesis, "cleft": rhetoric.find_clefts,
        "closing_flourish": rhetoric.find_closing_flourish,
        "nominalization_pickup": rhetoric.find_nominalization_pickups,
        "meta_aside": rhetoric.find_meta_asides, "self_rating": rhetoric.find_self_ratings,
        "absence_punch": rhetoric.find_absence_punches,
        "comma_chain": lambda t: rhetoric.find_comma_chains(t, CHAIN_LEN),
        "participial_triad": rhetoric_ext.find_participial_triads,
        "negation_template": rhetoric_ext.find_negation_templates,
        "intensifier": rhetoric_ext.find_intensifiers,
        "generator_phrase": rhetoric_ext.find_generator_phrases,
        "fragment_couplet": rhetoric_ext.find_fragment_couplets,
        "personification": rhetoric_ext.find_personifications,
        "colon_twist": rhetoric_ext.find_colon_twists, "tail_twist": rhetoric_ext.find_tail_twists,
        "question_fragment": rhetoric_ext.find_question_fragments,
        "then_opener": rhetoric_ext.find_then_openers,
        "pointer_verdict": rhetoric_ext.find_pointer_verdicts,
        "announcer": rhetoric_ext.find_announcers, "does_pair": rhetoric_ext.find_does_pairs,
        "parallel_address": rhetoric_ext.find_parallel_address,
        "conversion": rhetoric_ext.find_conversions,
    }
    HARD = ["self_explanation", "reversal", "way_simile", "declarative_rating"]
    FEATURES = list(PER_1K) + ["rhetorical_question", "anaphora2", "long_short", "copula_density"]
else:
    PER_1K, HARD, FEATURES = {}, [], []


def own_features(text):                                     # methods/constructional.py
    sents = [s.strip() for s in sentences(text) if s.strip()]
    n = len(sents)
    if n == 0:
        return {"rhetorical_question": 0.0, "anaphora2": 0.0, "long_short": 0.0, "copula_density": 0.0}
    q = sum(1 for s in sents if s.endswith("?"))
    firsts = [tuple(re.sub(r"^[^A-Za-z]+", "", s).lower().split()[:2]) for s in sents]
    ana = sum(1 for i in range(1, n) if len(firsts[i]) == 2 and firsts[i] == firsts[i - 1])
    lens = [len(s.split()) for s in sents]
    ls = sum(1 for i in range(1, n) if lens[i - 1] > 25 and lens[i] <= 6)
    nw = len(_C_WORD.findall(text))
    return {"rhetorical_question": 100.0 * q / n, "anaphora2": 100.0 * ana / max(n - 1, 1),
            "long_short": 100.0 * ls / max(n - 1, 1),
            "copula_density": 100.0 * len(_COPULA.findall(text)) / max(nw, 1)}


def rates(text):                                            # methods/constructional.py
    nw = len(_C_WORD.findall(text))
    out = {k: (1000.0 * len(fn(text)) / nw if nw else 0.0) for k, fn in PER_1K.items()}
    out.update(own_features(text))
    return out


def summarise_z(zvals, zhard):                              # methods/constructional.py: summarise()
    w = np.clip(zvals, -WINSOR, WINSOR)
    wh = np.clip(zhard, -WINSOR, WINSOR)
    return {"rfpd": float(np.abs(zvals).mean()), "arti": float(np.maximum(0.0, zvals).mean()),
            "arti_hard": float(np.maximum(0.0, zhard).mean()),
            "rfpd_w": float(np.abs(w).mean()), "arti_w": float(np.maximum(0.0, w).mean()),
            "arti_hard_w": float(np.maximum(0.0, wh).mean())}


# ===========================================================================
# 2. read the authors' own passages
# ===========================================================================
def read_jsonl(p):
    with open(p, encoding="utf-8-sig") as f:
        return [json.loads(l) for l in f if l.strip()]


print("[24] reading author corpora", flush=True)
passages = []                                   # author, id, split, text
for a in STUDY:
    d = os.path.join(AUTHORS_DIR, a)
    for split, fn in (("test", "test.jsonl"), ("ref", "ref.jsonl")):
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            continue
        for r in read_jsonl(p):
            passages.append({"author": a, "id": r["id"], "split": split, "text": norm(r["text"]),
                             "words": len(r["text"].split())})
pas = pd.DataFrame(passages)
briefs_by_author = {}
for a in STUDY:
    p = os.path.join(AUTHORS_DIR, a, "briefs_test.jsonl")
    briefs_by_author[a] = ({b["id"]: b["brief"] for b in read_jsonl(p) if b.get("passed") and b.get("brief")}
                           if os.path.exists(p) else {})
train_texts = {}
for a in STUDY:
    p = os.path.join(AUTHORS_DIR, a, "train.jsonl")
    train_texts[a] = [norm(r["text"]) for r in read_jsonl(p)] if os.path.exists(p) else []
print(f"[24] {len(pas)} author passages ({int((pas.split=='test').sum())} test, "
      f"{int((pas.split=='ref').sum())} ref) over {pas.author.nunique()} authors; "
      f"{sum(len(v) for v in train_texts.values())} train chunks for calibration "
      f"({time.time()-T0:.0f}s)", flush=True)

# ===========================================================================
# 3. per-passage profiles
# ===========================================================================
texts = pas.text.tolist()
print("[24] per / lexdiv / psd / cpd", flush=True)
rows = []
for t in texts:
    p600 = per_measure(truncate_words(t, 600))
    punc = per_measure(t)
    lx = lexdiv_measure(t)
    ps = psd_profile(t)
    cp = cpd_profile(t)
    rows.append({"per": p600["per"], "per_n_sent": p600["per_n_sent"], "per_uncapped": punc["per"],
                 "hapax_w300": lx.get("hapax_w300", np.nan), "mattr50_w300": lx.get("mattr50_w300", np.nan),
                 "mtld_w300": lx.get("mtld_w300", np.nan), "n_tok": lx.get("n_tok", np.nan),
                 "para_cv_words": ps["para_cv_words"], "para_cv_sents": ps["para_cv_sents"],
                 "para_mean_sents": ps["para_mean_sents"], "first_sent_ratio": ps["first_sent_ratio"],
                 "burst_an": cp["burst_an"], "sent_cv": cp["sent_cv"], "n_sent_cpd": cp["n_sent"],
                 **{c: cp[c] for c in CPD_COMPS}})
    rows[-1]["_logq"] = ps["logpara_q"]
prof = pd.DataFrame(rows)
LOGQ = np.vstack(prof.pop("_logq").values)
pas = pd.concat([pas.reset_index(drop=True), prof], axis=1)
print(f"[24] opener-class profiles (spaCy) ({time.time()-T0:.0f}s)", flush=True)
OPEN = np.vstack(otd_profiles_batch(texts))
for i, c in enumerate(CLASSES):
    pas["open_share_" + c] = OPEN[:, i]
print(f"[24] done ({time.time()-T0:.0f}s)", flush=True)

# constructional rates
def rate_vector(t):
    r = rates(t)                                  # one call per text, then index the features
    return [r[f] for f in FEATURES]


if CONSTRUCTIONAL_OK:
    print("[24] constructional rates", flush=True)
    RATE = np.vstack([rate_vector(t) for t in texts])
    TRAIN_RATE = {}
    for a in STUDY:
        keep = [t for t in train_texts[a] if len(_C_WORD.findall(t)) >= 200]
        TRAIN_RATE[a] = np.vstack([rate_vector(t) for t in keep]) if keep else np.zeros((0, len(FEATURES)))
        print(f"    {a}: {len(keep)} train chunks ({time.time()-T0:.0f}s)", flush=True)
    print(f"[24] done ({time.time()-T0:.0f}s)", flush=True)
else:
    RATE, TRAIN_RATE = None, None
    print(f"[24] constructional SKIPPED: {CONSTRUCTIONAL_WHY}", flush=True)

# event order, test passages only (they are the ones with briefs)
print("[24] event order on the authors' own test passages", flush=True)
eo_vals = {}
for a in STUDY:
    ks = {i: event_keywords(b) for i, b in briefs_by_author[a].items()}
    sub = pas[(pas.author == a) & (pas.split == "test")]
    for _, r in sub.iterrows():
        k = ks.get(r["id"])
        if k:
            eo_vals[(a, r["id"])] = eo_score(r["text"], k)
pas["tau"] = [eo_vals.get((r.author, r.id), {}).get("tau", np.nan) for r in pas.itertuples()]
pas["events_present"] = [eo_vals.get((r.author, r.id), {}).get("events_present", np.nan) for r in pas.itertuples()]
pas["terminal_missing"] = [eo_vals.get((r.author, r.id), {}).get("terminal_missing", np.nan) for r in pas.itertuples()]
pas["n_events"] = [eo_vals.get((r.author, r.id), {}).get("n_events", np.nan) for r in pas.itertuples()]
print(f"[24] event order on {len(eo_vals)} passages ({time.time()-T0:.0f}s)", flush=True)

# ===========================================================================
# 4. anchor-relative measures: a passage against an author's REF set
# ===========================================================================
idx_of = {(r.author, r.id): i for i, r in enumerate(pas.itertuples())}
ref_idx = {a: pas.index[(pas.author == a) & (pas.split == "ref")].to_numpy() for a in STUDY}
test_idx = {a: pas.index[(pas.author == a) & (pas.split == "test")].to_numpy() for a in STUDY}
# sd per cadence component over the author's own TEST passages (methods/common.py src_stats)
CPD_SD = {a: {c: float(np.std(pas.loc[test_idx[a], c].values, ddof=0)) for c in CPD_COMPS} for a in STUDY}

rng = np.random.default_rng(7)
anchored = []                                   # (passage row, anchor author) -> measures
CPDM = pas[CPD_COMPS].to_numpy(float)
CVW = pas["para_cv_words"].to_numpy(float)
BURST = pas["burst_an"].to_numpy(float)

for a in STUDY:
    R = ref_idx[a]
    if len(R) < 2:
        continue
    q_rows = np.unique(np.concatenate([np.concatenate([test_idx[b] for b in STUDY]), R]))
    JS = js_matrix(OPEN[q_rows], OPEN[R])                              # (nq, nref)
    W1 = np.abs(LOGQ[q_rows][:, None, :] - LOGQ[R][None, :, :]).mean(-1)
    sd = np.array([max(CPD_SD[a][c], 0.0) for c in CPD_COMPS])
    use = sd > 0
    Z = (np.abs(CPDM[q_rows][:, None, :] - CPDM[R][None, :, :])[:, :, use] / sd[use]).mean(-1)
    same = (q_rows[:, None] == R[None, :])                              # leave-one-out
    w = (~same).astype(float)
    denom = w.sum(1)
    keep = denom > 0
    pick = rng.integers(0, len(R), size=len(q_rows))                    # single-partner sensitivity
    for k, qi in enumerate(q_rows):
        if not keep[k]:
            continue
        j = pick[k]
        if R[j] == qi:
            j = (j + 1) % len(R)
        anchored.append({
            "row": int(qi), "anchor_author": a,
            "otd_js": float((JS[k] * w[k]).sum() / denom[k]), "otd_js_pair1": float(JS[k, j]),
            "w1_logpara": float((W1[k] * w[k]).sum() / denom[k]), "w1_logpara_pair1": float(W1[k, j]),
            "cpd_z": float((Z[k] * w[k]).sum() / denom[k]), "cpd_z_pair1": float(Z[k, j]),
            "cv_diff": float(CVW[qi] - (CVW[R] * w[k]).sum() / denom[k]),
            "burst_an_diff": float(BURST[qi] - (BURST[R] * w[k]).sum() / denom[k]),
        })
anch = pd.DataFrame(anchored)
print(f"[24] anchored measures: {len(anch)} passage-by-author rows ({time.time()-T0:.0f}s)", flush=True)

# constructional z, leave-one-out on the author's own REF rows
if CONSTRUCTIONAL_OK:
    con_rows = []
    hard_i = [FEATURES.index(f) for f in HARD]
    cal_words = pas.text.map(lambda t: len(_C_WORD.findall(t))).to_numpy()
    for a in STUDY:
        ref_ok = ref_idx[a][cal_words[ref_idx[a]] >= 200]
        cal = np.vstack([RATE[ref_ok], TRAIN_RATE[a]]) if len(ref_ok) else TRAIN_RATE[a]
        n = len(cal)
        if n < 2:
            continue
        S, SS = cal.sum(0), (cal ** 2).sum(0)
        mu = S / n
        sd = np.sqrt(np.maximum((SS / n) - mu ** 2, 0.0))
        sd_f = np.maximum(sd, SD_FLOOR)
        in_cal = set(int(i) for i in ref_ok)
        q_rows = np.unique(np.concatenate([np.concatenate([test_idx[b] for b in STUDY]), ref_idx[a]]))
        for qi in q_rows:
            r = RATE[qi]
            if int(qi) in in_cal and n > 2:                            # leave this passage out
                m2 = (S - r) / (n - 1)
                v2 = np.maximum((SS - r ** 2) / (n - 1) - m2 ** 2, 0.0)
                z = (r - m2) / np.maximum(np.sqrt(v2), SD_FLOOR)
            else:
                z = (r - mu) / sd_f
            s = summarise_z(z, z[hard_i])
            con_rows.append({"row": int(qi), "anchor_author": a, **s})
    con = pd.DataFrame(con_rows)
    anch = anch.merge(con, on=["row", "anchor_author"], how="outer")
    print(f"[24] constructional z done ({time.time()-T0:.0f}s)", flush=True)

anch = anch.merge(pas[["author", "id", "split"]].rename_axis("row").reset_index(), on="row", how="left")

# reference_measures.csv: one row per author passage, measured against its OWN author
own = anch[anch.anchor_author == anch.author].drop(columns=["anchor_author"])
ref_measures = pas.drop(columns=["text"]).rename_axis("row").reset_index().merge(own, on=["row", "author", "id", "split"], how="left")
ref_measures.insert(1, "author_class", ref_measures.author.map(AUTHOR_CLASS))
write_table(ref_measures.drop(columns=["row"]), os.path.join(OUTD, "reference_measures.csv"), floats=5)
write_table(anch.drop(columns=["row"]), os.path.join(OUTD, "cross_author_measures.csv"), floats=5)

# ===========================================================================
# 5. G: the arm-A0 cells, plus the three cache-only columns
# ===========================================================================
cells, runs_t, authors_t, briefs_t, refs_t = load_all()


def cache_cells(name, keys):
    d = json.load(open(os.path.join(EVAL, "cache", name + ".json"), encoding="utf-8"))
    t = pd.DataFrame(d["cells"])
    return t[["run", "id", "sample"] + keys].drop_duplicates(subset=["run", "id", "sample"])


# three measures live only in the eval cache, never in the master cell table; the merge keeps
# them on every row (replicate runs included) so lib.replicate_floor can see them too
CACHE_OK, cache_why = True, ""
try:
    cells = cells.merge(cache_cells("psd_raw_A0", ["para_cv_words"]), on=["run", "id", "sample"], how="left")
    cells = cells.merge(cache_cells("lexdiv_A0", ["mattr50_w300", "mtld_w300"]), on=["run", "id", "sample"], how="left")
except Exception as e:
    CACHE_OK, cache_why = False, repr(e)[:200]
    print("[24] cache merge failed:", cache_why, flush=True)
G = main_cells(cells).copy()
G = G[G.author.isin(STUDY)]

MEASURES = [
    ("per", "construction", "-", "absolute"),
    ("per_uncapped", "construction", "-", "absolute"),
    ("hapax_w300", "voice_structure", "0", "absolute"),
    ("mattr50_w300", "voice_structure", "0", "absolute"),
    ("mtld_w300", "voice_structure", "0", "absolute"),
    ("para_cv_words", "voice_structure", "0", "absolute"),
    ("otd_js", "voice_structure", "-", "ref-anchored"),
    ("cv_diff", "voice_structure", "0", "ref-anchored"),
    ("w1_logpara", "voice_structure", "-", "ref-anchored"),
    ("burst_an_diff", "voice_structure", "0", "ref-anchored"),
    ("cpd_z", "voice_structure", "-", "ref-anchored"),
    ("arti_w", "tell", "-", "calibration-z"),
    ("rfpd_w", "voice_structure", "-", "calibration-z"),
]
MEASURES = [m for m in MEASURES if m[0] in G.columns and (CONSTRUCTIONAL_OK or m[3] != "calibration-z")]

# H and P per author and measure
HP = {}
for a in STUDY:
    own_test = anch[(anch.author == a) & (anch.split == "test") & (anch.anchor_author == a)]
    pool = [b for b in CLASS_MEMBERS[AUTHOR_CLASS[a]] if b != a]
    other_test = anch[(anch.author.isin(pool)) & (anch.split == "test") & (anch.anchor_author == a)]
    own_abs = pas[(pas.author == a) & (pas.split == "test")]
    other_abs = pas[(pas.author.isin(pool)) & (pas.split == "test")]
    for m, construct, direction, kind in MEASURES:
        if kind == "absolute":
            h = own_abs[m].dropna().values if m in own_abs.columns else np.array([])
            p = other_abs[m].dropna().values if m in other_abs.columns else np.array([])
            pa = ([other_abs[other_abs.author == b][m].dropna().mean() for b in pool]
                  if m in other_abs.columns else [])
        else:
            h = own_test[m].dropna().values if m in own_test.columns else np.array([])
            p = other_test[m].dropna().values if m in other_test.columns else np.array([])
            pa = ([other_test[other_test.author == b][m].dropna().mean() for b in pool]
                  if m in other_test.columns else [])
        HP[(a, m)] = (h, p, float(np.mean(pa)) if len(pa) else np.nan, pool)

anchors_tab = pd.DataFrame([
    {"author": a, "author_class": AUTHOR_CLASS[a], "measure": m, "definition": kind,
     "n_H": len(HP[(a, m)][0]), "n_P": len(HP[(a, m)][1]), "n_pool_authors": len(HP[(a, m)][3]),
     "pool_authors": ",".join(HP[(a, m)][3]),
     "mean_H": float(np.mean(HP[(a, m)][0])) if len(HP[(a, m)][0]) else np.nan,
     "sd_H": float(np.std(HP[(a, m)][0], ddof=1)) if len(HP[(a, m)][0]) > 1 else np.nan,
     "P": HP[(a, m)][2],
     "separation_H_minus_P": (float(np.mean(HP[(a, m)][0])) - HP[(a, m)][2]) if len(HP[(a, m)][0]) else np.nan}
    for a in STUDY for m, c, d, kind in MEASURES])
write_table(anchors_tab, os.path.join(OUTD, "anchors_by_author_measure.csv"), floats=5)

# ---------------------------------------------------------------------------
# 5b. the coherence floor FIDELITY_SYNTHESIS section 2 asks for: the author's own passages
#     with their sentences shuffled. Strangers' prose is as coherent as the author's, so a
#     stranger pool cannot floor a CONSTRUCTION measure; a shuffled passage can.
# ---------------------------------------------------------------------------
shuf_rng = np.random.default_rng(11)


def shuffle_sentences(text):
    paras = [p for p in paragraphs(text) if p.strip()]
    per_para = [[s for s in sentences(p) if s.strip()] for p in paras]
    flat = [s for block in per_para for s in block]
    if len(flat) < 3:
        return text
    order = shuf_rng.permutation(len(flat))
    flat = [flat[i] for i in order]
    out, k = [], 0
    for block in per_para:
        out.append(" ".join(flat[k:k + len(block)]))
        k += len(block)
    return "\n\n".join(out)


shuf_rows = []
test_mask = pas.split == "test"
for i in pas.index[test_mask]:
    t = pas.at[i, "text"]
    sh = shuffle_sentences(t)
    p600 = per_measure(truncate_words(sh, 600))
    punc = per_measure(sh)
    lx = lexdiv_measure(sh)
    cp = cpd_profile(sh)
    shuf_rows.append({"author": pas.at[i, "author"], "id": pas.at[i, "id"], "per": p600["per"],
                      "per_uncapped": punc["per"], "hapax_w300": lx.get("hapax_w300", np.nan),
                      "burst_an": cp["burst_an"], "lag1": cp["lag1"]})
shuf = pd.DataFrame(shuf_rows)
write_table(shuf, os.path.join(OUTD, "shuffled_author_passages.csv"), floats=5)

SHUF_M = ["per", "per_uncapped", "hapax_w300"]
shuf_pos, shuf_check = [], []
for a in STUDY:
    own = pas[(pas.author == a) & (pas.split == "test")]
    sh_a = shuf[shuf.author == a]
    for m in SHUF_M:
        h = own[m].dropna().values
        p = sh_a[m].dropna().values
        if len(h) < 5 or len(p) < 5:
            continue
        shuf_check.append({"author": a, "author_class": AUTHOR_CLASS[a], "measure": m, "n": len(h),
                           "mean_author": float(h.mean()), "mean_shuffled": float(p.mean()),
                           "mean_shift": float(p.mean() - h.mean()),
                           "W1_shuffled_vs_author": wasserstein_distance(p, h),
                           "W1_strangers_vs_author": (wasserstein_distance(HP[(a, m)][1], h)
                                                      if (a, m) in HP and len(HP[(a, m)][1]) >= 5 else np.nan)})
shuf_check = pd.DataFrame(shuf_check)
write_table(shuf_check, os.path.join(OUTD, "shuffle_manipulation_check.csv"), floats=5)

# the event-order ceiling (H only: a stranger has no brief of this author's)
ceiling = (pas[pas.split == "test"].groupby("author")
           .agg(n=("tau", "count"), mean_tau=("tau", "mean"), sd_tau=("tau", "std"),
                mean_events_present=("events_present", "mean"),
                mean_terminal_missing=("terminal_missing", "mean"),
                mean_n_events=("n_events", "mean")).reset_index())
ceiling.insert(1, "author_class", ceiling.author.map(AUTHOR_CLASS))
gen_eo = (G.groupby(["kind"]).agg(mean_tau=("tau", "mean"), mean_events_present=("events_present", "mean"),
                                  mean_terminal_missing=("terminal_missing", "mean")).reset_index())
write_table(ceiling, os.path.join(OUTD, "event_order_ceiling.csv"), floats=4)

# ===========================================================================
# 6. floors, positions, fidelity
# ===========================================================================
floor_rows = []
for m, construct, direction, kind in MEASURES:
    t = replicate_floor(cells, m)
    for _, r in t.iterrows():
        floor_rows.append({"measure": m, **r.to_dict()})
floors = pd.DataFrame(floor_rows)
write_table(floors, os.path.join(OUTD, "replicate_floors.csv"), floats=5)
FLOOR = {m: (float(floors[floors.measure == m].abs_mean_diff.max()) if len(floors[floors.measure == m]) else np.nan)
         for m, c, d, k in MEASURES}

CFG = ["author", "family", "params_b", "kind"]
rng2 = np.random.default_rng(0)
pos_rows, fid_rows = [], []
for (a, fam, pb, kind), g in G.groupby(CFG, dropna=False):
    for m, construct, direction, mkind in MEASURES:
        h, p, P, pool = HP[(a, m)]
        gv = g[m].dropna()
        gids = g.loc[gv.index, "id"].values
        gv = gv.values.astype(float)
        if len(gv) < 5 or len(h) < 5 or len(p) < 5 or not np.isfinite(P):
            continue
        meanH = float(np.mean(h))
        uniq = pd.unique(gids)
        gidx = [np.where(gids == u)[0] for u in uniq]
        w1_gh = wasserstein_distance(gv, h)
        w1_ph = wasserstein_distance(p, h)
        bm, bw = [], []
        for _ in range(NBOOT):
            pick = rng2.integers(0, len(gidx), size=len(gidx))
            star = gv[np.concatenate([gidx[i] for i in pick])]
            bm.append(star.mean())
            bw.append(wasserstein_distance(star, h))
        bm, bw = np.array(bm), np.array(bw)
        denom = meanH - P
        pos = (gv.mean() - P) / denom if denom != 0 else np.nan
        bp = (bm - P) / denom if denom != 0 else np.full(NBOOT, np.nan)
        F = 1 - w1_gh / w1_ph if w1_ph > 0 else np.nan
        bf = 1 - bw / w1_ph if w1_ph > 0 else np.full(NBOOT, np.nan)
        base = {"author": a, "author_class": AUTHOR_CLASS[a], "family": fam, "params_b": pb, "kind": kind,
                "arm": "A0", "measure": m, "construct": construct, "direction": direction,
                "definition": mkind, "n_G": len(gv), "n_briefs": len(uniq), "n_H": len(h), "n_P": len(p),
                "n_pool_authors": len(pool), "floor": FLOOR[m],
                "separation": denom, "separation_over_floor": abs(denom) / FLOOR[m] if FLOOR[m] else np.nan}
        base["anchor_usable"] = bool(base["separation_over_floor"] >= 2) if np.isfinite(base["separation_over_floor"]) else False
        pos_rows.append({**base, "mean_G": float(gv.mean()), "mean_H": meanH, "P": P, "pos": pos,
                         "pos_lo": float(np.nanquantile(bp, 0.025)), "pos_hi": float(np.nanquantile(bp, 0.975))})
        fid_rows.append({**base, "F": F, "F_lo": float(np.nanquantile(bf, 0.025)),
                         "F_hi": float(np.nanquantile(bf, 0.975)), "W1_G_H": w1_gh, "W1_P_H": w1_ph})
positions = pd.DataFrame(pos_rows)
fidelity = pd.DataFrame(fid_rows)
write_table(positions, os.path.join(OUTD, "positions_by_configuration.csv"), floats=5)
write_table(fidelity, os.path.join(OUTD, "fidelity_by_configuration.csv"), floats=5)
print(f"[24] positions and F: {len(positions)} rows over {positions.groupby(CFG).ngroups} configurations "
      f"({time.time()-T0:.0f}s)", flush=True)

by_measure = (fidelity.groupby(["measure", "construct", "definition", "kind"])
              .agg(n=("F", "size"), n_authors=("author", "nunique"), median_F=("F", "median"),
                   median_pos=("F", "size"), share_anchor_usable=("anchor_usable", "mean"),
                   median_separation_over_floor=("separation_over_floor", "median")).reset_index())
by_measure["median_pos"] = (positions.groupby(["measure", "construct", "definition", "kind"]).pos.median()
                            .reindex(pd.MultiIndex.from_frame(by_measure[["measure", "construct", "definition", "kind"]])).values)
write_table(by_measure, os.path.join(OUTD, "fidelity_by_measure.csv"), floats=4)

# F against the shuffled-author floor, for the measures a stranger pool cannot floor
sh_rows = []
for (a, fam, pb, kind), g in G.groupby(CFG, dropna=False):
    own = pas[(pas.author == a) & (pas.split == "test")]
    sh_a = shuf[shuf.author == a]
    for m in SHUF_M:
        h = own[m].dropna().values
        p = sh_a[m].dropna().values
        gv = g[m].dropna()
        gids = g.loc[gv.index, "id"].values
        gv = gv.values.astype(float)
        if len(gv) < 5 or len(h) < 5 or len(p) < 5:
            continue
        w1_ph = wasserstein_distance(p, h)
        w1_gh = wasserstein_distance(gv, h)
        uniq = pd.unique(gids)
        gidx = [np.where(gids == u)[0] for u in uniq]
        bw = []
        for _ in range(NBOOT):
            pick = rng2.integers(0, len(gidx), size=len(gidx))
            bw.append(wasserstein_distance(gv[np.concatenate([gidx[i] for i in pick])], h))
        bw = np.array(bw)
        sh_rows.append({"author": a, "author_class": AUTHOR_CLASS[a], "family": fam, "params_b": pb,
                        "kind": kind, "measure": m, "floor_pool": "shuffled author passages",
                        "n_G": len(gv), "n_H": len(h), "n_P": len(p),
                        "F_vs_shuffled": 1 - w1_gh / w1_ph if w1_ph > 0 else np.nan,
                        "F_lo": float(np.nanquantile(1 - bw / w1_ph, 0.025)) if w1_ph > 0 else np.nan,
                        "F_hi": float(np.nanquantile(1 - bw / w1_ph, 0.975)) if w1_ph > 0 else np.nan,
                        "W1_G_H": w1_gh, "W1_shuffled_H": w1_ph})
shuffle_fid = pd.DataFrame(sh_rows)
write_table(shuffle_fid, os.path.join(OUTD, "fidelity_vs_shuffle_floor.csv"), floats=5)
shuffle_fid_summary = (shuffle_fid.groupby(["measure", "kind"])
                       .agg(n=("F_vs_shuffled", "size"), n_authors=("author", "nunique"),
                            median_F_vs_shuffled=("F_vs_shuffled", "median")).reset_index())
if len(shuffle_fid_summary):
    shuffle_fid_summary = shuffle_fid_summary.merge(
        fidelity.groupby(["measure", "kind"]).F.median().rename("median_F_vs_strangers").reset_index(),
        on=["measure", "kind"], how="left")
write_table(shuffle_fid_summary, os.path.join(OUTD, "fidelity_vs_shuffle_summary.csv"), floats=4)

# sensitivity: does the ref-set anchor definition change F for the paired measures
sens_rows = []
for m in [x[0] for x in MEASURES if x[3] == "ref-anchored" and x[0] in ("otd_js", "cpd_z", "w1_logpara")]:
    for a in STUDY:
        pool = [b for b in CLASS_MEMBERS[AUTHOR_CLASS[a]] if b != a]
        ot = anch[(anch.split == "test") & (anch.anchor_author == a)]
        h1 = ot[ot.author == a][m].dropna().values
        p1 = ot[ot.author.isin(pool)][m].dropna().values
        h2 = ot[ot.author == a][m + "_pair1"].dropna().values
        p2 = ot[ot.author.isin(pool)][m + "_pair1"].dropna().values
        if min(len(h1), len(p1), len(h2), len(p2)) < 5:
            continue
        sens_rows.append({"author": a, "author_class": AUTHOR_CLASS[a], "measure": m,
                          "mean_H_ref_set": float(h1.mean()), "sd_H_ref_set": float(h1.std(ddof=1)),
                          "mean_H_single_partner": float(h2.mean()), "sd_H_single_partner": float(h2.std(ddof=1)),
                          "sd_ratio_single_over_set": float(h2.std(ddof=1) / h1.std(ddof=1)) if h1.std(ddof=1) else np.nan,
                          "W1_P_H_ref_set": wasserstein_distance(p1, h1),
                          "W1_P_H_single_partner": wasserstein_distance(p2, h2)})
sens = pd.DataFrame(sens_rows)
write_table(sens, os.path.join(OUTD, "anchor_definition_sensitivity.csv"), floats=5)

# ===========================================================================
# 7. author-region rate: three measure instruments + the two embeddings of script 23
# ===========================================================================
REG_M = ["per", "otd_js", "hapax_w300"]
REG_M = [m for m in REG_M if m in {x[0] for x in MEASURES}]
p23 = os.path.join(OUT, "23_register_matched_pool", "generation_instrument_values.csv")
emb23 = pd.read_csv(p23) if os.path.exists(p23) else pd.DataFrame()
EMB_INST = ["luar", "wegmann"]
have23 = len(emb23) > 0
if have23:
    emb23 = emb23[emb23.arm == "A0"]
    a23 = os.path.join(OUT, "23_register_matched_pool", "pool_pairwise_cosine.csv")
    H23 = pd.read_csv(a23)

bounds = {}
for a in STUDY:
    for m in REG_M:
        h = HP[(a, m)][0]
        if len(h) >= 5:
            bounds[(a, m)] = (float(np.quantile(h, 0.05)), float(np.quantile(h, 0.95)))

if have23:
    # script 23 writes the central-90% bounds of H per author and embedding instrument into
    # its region table; reuse them rather than re-deriving the embedding anchors here
    r23 = pd.read_csv(os.path.join(OUT, "23_register_matched_pool", "author_region_rate.csv"))
    r23 = r23[r23.arm == "A0"]

reg_rows = []
for (a, fam, pb, kind), g in G.groupby(CFG, dropna=False):
    ok = np.ones(len(g), dtype=bool)
    used = []
    for m in REG_M:
        if (a, m) not in bounds or m not in g.columns:
            continue
        lo, hi = bounds[(a, m)]
        v = g[m].values.astype(float)
        ok &= np.isfinite(v) & (v >= lo) & (v <= hi)
        used.append(m)
    df = pd.DataFrame({"id": g.id.values, "sample": g["sample"].values, "in_measures": ok})
    if have23:
        e = emb23[(emb23.author == a) & (emb23.family == fam) & (np.isclose(emb23.params_b, float(pb))) &
                  (emb23.kind == kind)]
        rr = r23[(r23.author == a) & (r23.family == fam) & (np.isclose(r23.params_b, float(pb))) & (r23.kind == kind)]
        if len(e) and len(rr):
            eb = {}
            for inst in EMB_INST:
                eb[inst] = (float(rr[f"lo_{inst}"].iloc[0]) if f"lo_{inst}" in rr.columns else np.nan,
                            float(rr[f"hi_{inst}"].iloc[0]) if f"hi_{inst}" in rr.columns else np.nan)
            e = e.copy()
            inside = np.ones(len(e), dtype=bool)
            for inst in EMB_INST:
                lo, hi = eb[inst]
                v = e[f"s_own_{inst}"].values.astype(float)
                inside &= np.isfinite(v) & (v >= lo) & (v <= hi)
            e["in_emb"] = inside
            df = df.merge(e[["id", "sample", "in_emb"]], on=["id", "sample"], how="left")
        else:
            df["in_emb"] = np.nan
    else:
        df["in_emb"] = np.nan
    n = len(df)
    k = int(df.in_measures.sum())
    R_m = k / n if n else np.nan
    both = df.in_measures & df.in_emb.fillna(False).astype(bool)
    n_both = int(df.in_emb.notna().sum())
    k_both = int(both[df.in_emb.notna()].sum())
    per_brief_m = df.groupby("id").in_measures.max()
    per_brief_b = df[df.in_emb.notna()].groupby("id").apply(lambda x: bool((x.in_measures & x.in_emb).max()),
                                                            include_groups=False) if n_both else pd.Series(dtype=bool)
    reg_rows.append({"author": a, "author_class": AUTHOR_CLASS[a], "family": fam, "params_b": pb, "kind": kind,
                     "instruments_measure": ",".join(used), "n_passages": n, "n_inside_measures": k,
                     "R_measures": R_m, "n_passages_with_embeddings": n_both,
                     "n_inside_all5": k_both, "R_all5": (k_both / n_both) if n_both else np.nan,
                     "R_measures_at_2": float(per_brief_m.mean()) if len(per_brief_m) else np.nan,
                     "R_all5_at_2": float(per_brief_b.mean()) if len(per_brief_b) else np.nan})
region = pd.DataFrame(reg_rows)


def wilson(k, n, z=Z95):
    if not n:
        return (np.nan, np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


for i, r in region.iterrows():
    _, lo, hi = wilson(int(r.n_inside_measures), int(r.n_passages))
    region.loc[i, "R_measures_lo"], region.loc[i, "R_measures_hi"] = lo, hi
    if r.n_passages_with_embeddings:
        _, lo, hi = wilson(int(r.n_inside_all5), int(r.n_passages_with_embeddings))
        region.loc[i, "R_all5_lo"], region.loc[i, "R_all5_hi"] = lo, hi
write_table(region, os.path.join(OUTD, "author_region_rate.csv"), floats=4)

# the author's own passages and the register-matched strangers on the same rule, three
# measure instruments and then all five
p23v = os.path.join(OUT, "23_register_matched_pool", "author_passage_instrument_values.csv")
emb_vals = pd.read_csv(p23v) if os.path.exists(p23v) else pd.DataFrame()
own_floor = []
for a in STUDY:
    for who, sel in (("author_own_test", pas[(pas.author == a) & (pas.split == "test")]),
                     ("register_matched_strangers",
                      pas[pas.author.isin([b for b in CLASS_MEMBERS[AUTHOR_CLASS[a]] if b != a]) & (pas.split == "test")])):
        rows_i = sel.index.to_numpy()
        if not len(rows_i):
            continue
        ok = np.ones(len(rows_i), dtype=bool)
        for m in REG_M:
            if (a, m) not in bounds:
                continue
            lo, hi = bounds[(a, m)]
            if m in ("otd_js",):
                v = anch[(anch.anchor_author == a) & (anch.row.isin(rows_i))].set_index("row").reindex(rows_i)[m].values
            else:
                v = pas.loc[rows_i, m].values.astype(float)
            ok &= np.isfinite(v.astype(float)) & (v >= lo) & (v <= hi)
        rate5 = np.nan
        if len(emb_vals) and have23:
            rr = r23[r23.author == a]
            ev = emb_vals[(emb_vals.anchor_author == a) & (emb_vals.id.isin(pas.loc[rows_i, "id"]))]
            if len(rr) and len(ev):
                ev = ev.set_index("id").reindex(pas.loc[rows_i, "id"])
                in5 = ok.copy()
                for inst in EMB_INST:
                    lo, hi = float(rr[f"lo_{inst}"].iloc[0]), float(rr[f"hi_{inst}"].iloc[0])
                    v = ev["s_" + inst].values.astype(float)
                    in5 &= np.isfinite(v) & (v >= lo) & (v <= hi)
                rate5 = float(in5.mean())
        own_floor.append({"author": a, "author_class": AUTHOR_CLASS[a], "group": who, "n": len(rows_i),
                          "rate_inside_3_measures": float(ok.mean()), "rate_inside_all5": rate5})
own_floor = pd.DataFrame(own_floor)
write_table(own_floor, os.path.join(OUTD, "region_ceiling_and_floor.csv"), floats=4)
region_summary = (region.groupby(["family", "params_b", "kind"])
                  .agg(n_configs=("R_measures", "size"), n_authors=("author", "nunique"),
                       mean_R_measures=("R_measures", "mean"), median_R_measures=("R_measures", "median"),
                       mean_R_measures_at_2=("R_measures_at_2", "mean"),
                       mean_R_all5=("R_all5", "mean"), mean_R_all5_at_2=("R_all5_at_2", "mean")).reset_index())
write_table(region_summary, os.path.join(OUTD, "author_region_summary.csv"), floats=4)

# ===========================================================================
# 8. figures
# ===========================================================================
figs = []
STRUCT = [m for m, c, d, k in MEASURES if c == "voice_structure"]
CONSTR = [m for m, c, d, k in MEASURES if c in ("construction", "tell")]
for name, group, title in (("structure", STRUCT, "VOICE-S instruments"),
                           ("construction", CONSTR, "CONSTRUCTION and TELL instruments")):
    if not group:
        continue
    fig, ax = plt.subplots(figsize=(max(7.5, 2.5 + 1.4 * len(group)), 5.4))
    xs = np.arange(len(group))
    for off, kind, col in ((-0.17, "base", "#7a7a7a"), (0.17, "adapter", "#1f77b4")):
        med, lo, hi = [], [], []
        for m in group:
            v = fidelity[(fidelity.measure == m) & (fidelity.kind == kind)].groupby("author").F.mean().dropna().values
            med.append(np.median(v) if len(v) else np.nan)
            pt, l, h = bootstrap_ci(v, stat=np.median, n=2000, seed=3)
            lo.append(pt - l if np.isfinite(l) else np.nan); hi.append(h - pt if np.isfinite(h) else np.nan)
        ax.errorbar(xs + off, med, yerr=[lo, hi], fmt="o", color=col, capsize=3, label=kind)
    ax.axhline(1.0, color="k", ls=":", lw=0.8); ax.axhline(0.0, color="k", lw=0.8)
    usable = {m: bool(fidelity[fidelity.measure == m].separation_over_floor.median() >= 2) for m in group}
    ax.set_xticks(xs)
    ax.set_xticklabels([m if usable[m] else m + " *" for m in group], rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("distributional fidelity F\n1 = the author, 0 = register-matched strangers", fontsize=9)
    ax.set_title(f"F by instrument, arm A0, {title}\nauthor is the unit; bars bootstrap authors; "
                 "* = anchors closer than twice the replicate floor", fontsize=10)
    ax.legend(loc="lower left", fontsize=9)
    figs.append((f"Fidelity by instrument, {title}",
                 savefig(fig, os.path.join(OUTD, f"fidelity_{name}.png"))))

fig, ax = plt.subplots(figsize=(9, 5.6))
sub = fidelity[fidelity.measure.isin(["per", "otd_js", "hapax_w300"]) & (fidelity.family == "Qwen3")]
n_au = sub.groupby("params_b").author.nunique()
sub = sub[sub.params_b.isin(n_au[n_au >= 3].index)]        # 1.7B is one author only
for m, col in zip(["per", "otd_js", "hapax_w300"], ["#d62728", "#1f77b4", "#2ca02c"]):
    for kind, ls in (("base", "--"), ("adapter", "-")):
        s = sub[(sub.measure == m) & (sub.kind == kind)]
        if not len(s):
            continue
        gg = s.groupby("params_b").F.median()
        ax.plot(gg.index.values, gg.values, ls, marker="o", color=col, label=f"{m} {kind}")
ax.axhline(1.0, color="k", ls=":", lw=0.8); ax.axhline(0.0, color="k", lw=0.8)
sizes_q = sorted(sub.params_b.dropna().unique())
ax.set_xscale("log", base=2); ax.set_xlabel("parameters (B)")
ax.set_xticks(sizes_q); ax.set_xticklabels([f"{s:g}" for s in sizes_q])
ax.minorticks_off()
ax.set_ylabel("median F over authors")
ax.set_title(f"The three region instruments against scale, Qwen3, arm A0, "
             f"{sub.author.nunique()} authors\n"
             "solid = adapter, dashed = base; per has no usable denominator (see the README)", fontsize=10)
ax.legend(fontsize=8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
figs.append(("The three region instruments against scale",
             savefig(fig, os.path.join(OUTD, "fidelity_region_instruments_vs_scale.png"))))

# ===========================================================================
# 9. README
# ===========================================================================
tau_mean = float(ceiling.mean_tau.mean())
tau_lo, tau_hi = float(ceiling.mean_tau.min()), float(ceiling.mean_tau.max())
gen_tau = float(G.tau.mean())
skipped = "" if CONSTRUCTIONAL_OK else (
    f"\n**The constructional measures were skipped.** `constructional.py` needs "
    f"`mimesis_voice.rhetoric` and `rhetoric_ext` from the Mimesis source tree and the import "
    f"failed: `{CONSTRUCTIONAL_WHY}`. `arti_w` and `rfpd_w` therefore have no H and no P here "
    f"and remain uncalibrated.\n")

# README string helpers only; no table is recomputed here.
_MEAS_NAMES = ("per", "per_uncapped", "hapax_w300", "mattr50_w300", "mtld_w300", "para_cv_words",
               "otd_js", "cv_diff", "w1_logpara", "burst_an_diff", "cpd_z", "arti_w", "rfpd_w")
cal_names = sorted(positions.measure.unique())
uncal_names = sorted(set(c for c in pas.columns if c in _MEAS_NAMES) - set(cal_names))
n_cal = len(cal_names)
floor_fams = sorted(floors.family.unique())
class_txt = ", ".join(f"{c} {len(v)}" for c, v in sorted(CLASS_MEMBERS.items()))
own_ceiling = own_floor[own_floor.group == "author_own_test"]
own_strangers = own_floor[own_floor.group == "register_matched_strangers"]
n_region_authors = int(own_ceiling.author.nunique())
r14 = region_summary[(region_summary.family == "Qwen3") & (region_summary.params_b == 14.0)]
n_r14_authors = int(r14.n_authors.max()) if len(r14) else 0
best5 = region_summary.loc[region_summary.mean_R_all5.idxmax()] if len(region_summary) else None
trunc_flagged_used = sorted(runs_t[(runs_t.truncation_gate_ok == False) & runs_t.run.isin(G.run.unique())].run)  # noqa: E712

what = f"""
The eval caches store per-cell values for generations only, so script 15 could not put these
instruments on the author-calibrated scale at all. This script computes them on the authors'
own passages -- {int((pas.split=='test').sum())} held-out test passages and
{int((pas.split=='ref').sum())} reference passages over {pas.author.nunique()} authors --
with the pipeline's own measure code, and then calibrates the generations against them.
{n_cal} instruments end with an H, a P and calibrated rows ({', '.join(cal_names)}).
{("Measured on the author passages but left uncalibrated because the generation side is not in the master cell table: " + ", ".join(uncal_names) + ".") if uncal_names else "Every measured instrument ends calibrated."}

`reference_measures.csv` is the artefact the rest of the programme was missing: one row per
author passage with every measure on it. `cross_author_measures.csv` is the same measures
computed for each passage against every other author's anchor, which is what a stranger pool
needs. On top of them the script reports positions, distributional fidelity F, and an
author-region rate that now has structure and construction in it, not only embeddings.
{skipped}"""

how = f"""
**Measure code.** The pure functions of `scripts/legacy/methods/per.py`, `otd.py`, `psd.py`,
`cpd.py`, `lexdiv.py`, `event_order.py` and `constructional.py`, plus `sentences`,
`paragraphs` and `normalise_punct` from `scripts/legacy/dr/core.py`, are copied into this
script verbatim with a comment naming the source file on each. Nothing in `scripts/legacy`
is imported or modified: `methods/common.py` points at the original pipeline directories and
`dr/core.py` creates directories when it is imported. The one deliberate change is that the
six-token opener stubs go through a single `nlp.pipe` call instead of one `spacy` call per
sentence; the tagger and its annotations are the same. Texts are normalised exactly as the
pipeline normalises them (`normalise_punct` then the S9 glyph fold), `per` is computed on the
first 600 words and `per_uncapped` on the whole passage, `lexdiv` on the first 300 tokens.

**Anchors.** `per`, `per_uncapped`, `hapax_w300`, `mattr50_w300`, `mtld_w300` and
`para_cv_words` are properties of a passage and need no anchor. `otd_js`, `cv_diff`,
`w1_logpara`, `burst_an_diff` and `cpd_z` are distances, and the pipeline computes them
against the generation's own source passage -- which does not exist for an author's own
passage. They are therefore computed here against the author's REFERENCE set: the mean over
the author's reference passages of the paired distance, leaving the passage out of the set
when it is itself in it. A stranger's passage is measured against the same author's
reference set, so H and P are exactly comparable. The constructional z scores use the
author's REF+TRAIN calibration exactly as `constructional.py` does, with a leave-one-out
mean and standard deviation when the passage being scored is in that calibration.

**The definition gap, stated plainly.** G keeps the pipeline's definition: a single distance
to the passage's own source. H and P use a mean over the reference set. Averaging shrinks
spread, so H is narrower than a single-pair H would be, W1(G, H) is inflated and F on the
five ref-anchored measures is biased downward. `anchor_definition_sensitivity.csv` measures
the size of that: it recomputes H and P with one randomly chosen reference partner per
passage and prints the ratio of standard deviations. The absolute measures (`per`,
`hapax_w300`, the lexical triple, `para_cv_words`) have no such gap and are the ones to lean
on.

**Calibration.** H = the author's own test passages; P = the test passages of the other
authors of the same class, the register-matched pool of script 23 ({class_txt}, so a private
author's pool is one other author); G = the arm-A0, non-replicate cells of `cells.parquet`,
with `para_cv_words`, `mattr50_w300` and `mtld_w300` sought in `data/eval_results/cache/`
because they are not in the master cell table.
pos = (mean G - P) / (mean H - P) with P the author-balanced pool mean;
F = 1 - W1(G, H) / W1(P, H); {NBOOT}-resample bootstrap over brief clusters inside a
configuration, anchors held fixed. Each row carries the measure's replicate floor from
`lib.replicate_floor` and is flagged unusable when the two anchors are closer together than
twice that floor.

**Event order.** `tau`, `events_present` and `terminal_missing` need the passage's own brief,
so they exist for the author's test passages and for generations, and cannot exist for a
stranger: nobody else wrote to this author's brief. They are reported as a ceiling table
(`event_order_ceiling.csv`), not as a position.

**Region rate.** R on (`per`, `otd_js`, `hapax_w300`) is the share of generated passages
inside the central 90% interval of H on all three at once; `R_all5` adds the two
register-matched embedding instruments from script 23 and is the five-instrument rate.
`region_ceiling_and_floor.csv` gives the same rule applied to the author's own passages
(the ceiling) and to the register-matched strangers (the floor).

**A second floor for construction.** FIDELITY_SYNTHESIS section 2 says a stranger pool
cannot floor a coherence measure, because strangers' prose is as coherent as the author's.
The first half of that prediction holds: on `per` the register-matched pool sits
{float(np.abs(anchors_tab[anchors_tab.measure=='per'].separation_H_minus_P).median()):.4f} from
the author's own mean, against a within-author standard deviation of
{float(anchors_tab[anchors_tab.measure=='per'].sd_H.median()):.4f}, and the sign of the gap
is not even consistent across authors. So the script builds the floor that section names:
every author test passage with its sentences permuted inside its own paragraph structure,
seeded, remeasured. `shuffle_manipulation_check.csv` reports how far that moves each measure
and `fidelity_vs_shuffle_floor.csv` recomputes F against it. The second half of the
prediction does not hold, and the check is what shows it -- see the conservative reading.
"""

pos_med = positions.groupby("measure").pos.median()
fid_med = fidelity.groupby(["measure", "kind"]).F.median()

reading = f"""
The unit is the author. Every median in `fidelity_by_measure.csv` is taken over
configurations, and the figures resample authors, not passages; with
{fidelity.author.nunique()} authors the intervals are wide and are meant to be.

{n_cal} instruments that script 15 had to leave uncalibrated now have an H and a P, and on
several of them the anchor is the more informative number. The event-order ceiling is the
clearest case: the authors' own passages score a mean Kendall tau of {tau_mean:.2f} against
their own briefs over {len(ceiling)} authors (author means from {tau_lo:.2f} to {tau_hi:.2f}),
while the generations average {gen_tau:.2f}. A generation scoring above {tau_mean:.2f} is
following the brief's event order more closely than the prose the brief was extracted from
did, which is consistent with mechanical ordering rather than with fidelity. `tau` is
therefore reported raw and is not treated as a quantity to maximise.

Read F per instrument, never averaged across constructs: `fidelity_by_measure.csv` keeps
structure, construction and tell apart, which is the whole point of the profile in
FIDELITY_SYNTHESIS section 2.

Most F values here are below zero, and that is a statement about the instruments more than
about the models. F divides by W1(P, H), and on these measures a register-matched stranger
is very close to the author: the whole usable range is compressed, so any generation that
misses lands well below zero. The column to read first is `separation_over_floor` --
{int(round(100*float(by_measure.share_anchor_usable.mean())))} per cent of the
configuration-by-instrument rows clear the twice-the-floor rule, and the instruments marked
with an asterisk in the figures do not clear it on their median.

Any base-versus-adapter difference read off `fidelity_by_configuration.csv` or
`positions_by_configuration.csv` is compared with the measure's replicate floor in the same
row (`replicate_floors.csv` carries the floors themselves). A difference smaller than that
floor is inside the twice-generated replicate noise of the measure and is reported as within
the floor whatever else the row says.

`per` carries the largest problem of the set, and the second floor does not fix it. The
shuffled-author floor that FIDELITY_SYNTHESIS section 2 prescribes fails its own manipulation
check on this measure: taking an author's own passage and permuting its sentences moves the median
proposition-echo rate by
{float(shuf_check[shuf_check.measure=='per'].mean_shift.median()):+.4f}, and the Wasserstein
distance between the shuffled and unshuffled distributions,
{float(shuf_check[shuf_check.measure=='per'].W1_shuffled_vs_author.median()):.4f}, is
*smaller* than the distance to the register-matched strangers,
{float(shuf_check[shuf_check.measure=='per'].W1_strangers_vs_author.median()):.4f}. PER is
close to permutation-invariant by construction -- whether sentence A echoes B or B echoes A,
one of the pair is counted -- so a sentence shuffle is not a manipulation it can see.
Neither pool gives `per` a usable denominator, and its F should not be quoted from this
table at all; the raw rates in `reference_measures.csv` and the region membership are what
it can support. `hapax_w300` does move under the shuffle
({float(shuf_check[shuf_check.measure=='hapax_w300'].mean_shift.median()):+.4f}) but less far than
a different author moves it, so the stranger pool stays its floor.

For the five ref-anchored measures the direction of the bias is known and one-sided: F is too
low, because G is a single-pair distance and H is a mean over the reference set. Treat their
F values as a lower bound and quote `anchor_definition_sensitivity.csv` beside them. The
absolute measures carry no such caveat.

The region rate on three measure instruments is much harsher than the embedding rate of
script 23, and the ceiling accounts for part of it: over {n_region_authors} authors the
author's own passages clear all three simultaneously
{float(own_ceiling.rate_inside_3_measures.mean()):.2f} of the time, because each central-90%
interval throws away 10 per cent of them and the intervals are close to independent. Read R as
a fraction of that ceiling. The register-matched strangers clear the same three
{float(own_strangers.rate_inside_3_measures.mean()):.2f} of the time on average, which is how
little these three instruments separate an author from their own register. That stranger floor
is an average over very unlike rows: it runs from
{float(own_strangers.rate_inside_3_measures.min()):.2f} to
{float(own_strangers.rate_inside_3_measures.max()):.2f} by author, and the private authors'
figure rests on a pool of one other writer, so the mean is not a floor any single row can be
read against. On all five instruments the ceiling falls to
{float(own_ceiling.rate_inside_all5.mean()):.2f} and the stranger floor to
{float(own_strangers.rate_inside_all5.mean()):.2f}. The two embedding instruments inside the
five-instrument rate come from script 23 and therefore inherit its npy row-alignment repair;
without that repair every cross-author cosine feeding them would be mislabelled.

The three-measure rate moves in the opposite direction from the embedding rate. Adapters raise
the embedding region rate in script 23 and lower this one: on Qwen3 at 14B, over
{n_r14_authors} authors, the base runs clear the three-instrument region
{float(r14[r14.kind=='base'].mean_R_measures.iloc[0]):.2f} of the time and the adapter runs
{float(r14[r14.kind=='adapter'].mean_R_measures.iloc[0]):.2f}. That pattern is consistent with
FIDELITY_SYNTHESIS fact 3, voice and construction moving in opposite directions under LoRA,
measured on a rate rather than a mean; the design is observational across authors, so it is
consistency rather than a demonstration, and the number of authors behind each row is printed
in `n_authors`. The five-instrument rate, which needs both constructs at once, averages at
most {float(region_summary.mean_R_all5.max()):.2f} over any family-size-kind group, and that
best group is {best5.family} {float(best5.params_b):g}B {best5.kind} over
{int(best5.n_authors)} authors. The best single author-and-configuration cell in the whole
table reaches {float(region.R_all5.max()):.2f} against an author ceiling of
{float(own_ceiling.rate_inside_all5.mean()):.2f}.
"""

caveats = [
    "G and the ref-anchored H and P are not the same function. G is the pipeline's distance "
    "to the generation's own source passage; H and P are means over the author's reference "
    "set, because an author's own passage has no separate source. F for otd_js, cv_diff, "
    "w1_logpara, burst_an_diff and cpd_z is therefore a lower bound, not an estimate.",
    "P uses the other authors' TEST passages so that it matches H. Their reference passages "
    "are measured too and are in reference_measures.csv, but they do not enter P.",
    "The private class has two authors, so a private author's register-matched pool is a "
    "single other author. patrick (the v1 chunking control) is excluded throughout for the "
    "reason given in script 23.",
    "cpd_z uses the standard deviations of the author's own test passages per cadence "
    "component, exactly as methods/common.py's source_stats does; those sds are estimated on "
    "25 to 50 passages and are themselves noisy.",
    "The constructional calibration is REF+TRAIN, so it is not independent of the adapter's "
    "training data: an adapter trained on those chunks is being scored against a calibration "
    "built from them. That is the pipeline's own design and is kept here for comparability, "
    "but it means arti_w and rfpd_w are not clean held-out measures for adapter runs.",
    "Event-order tau, events_present and terminal_missing have a ceiling but no floor: a "
    "stranger cannot be scored against this author's brief. They are reported raw.",
    "Only arm A0 has eval-cache measures, so nothing here speaks to the prompting arms: no "
    "A1-A5 effect on per, otd_js, psd, cpd, lexdiv, event order or the constructional features "
    "can be claimed from this table or any other.",
    f"Replicate floors are now measured for {', '.join(floor_fams)} (`replicate_floors.csv`), "
    f"the two Ministral3 replicate base runs having been scored on 2026-09-10. The Ministral3 "
    f"pairs are few and their floors are smaller than the Qwen3 ones on most measures, so a "
    f"Ministral3 contrast judged above its own floor is on thinner evidence than the same "
    f"verdict on Qwen3.",
    f"Generated passages from runs that exceed the 20 per cent truncation gate are included "
    f"and flagged, not excluded. Among the runs read here that is: "
    f"{', '.join(trunc_flagged_used) if trunc_flagged_used else 'none'}.",
    "Thirteen authors, not the multiplicity correction, is what limits every pooled statement "
    "here; the BH-FDR in this folder is applied within this script's own families and has not "
    "been through the programme-wide layer in script 22.",
    "The shuffle floor moves only the measures that read order. otd_js is computed from a "
    "distribution over opener classes and burst_an from the sentence-length distribution, "
    "so a sentence shuffle leaves them where they are by construction; that is why the "
    "shuffle floor is offered for per, per_uncapped and hapax_w300 and not for the rest.",
]

tables = [
    ("Fidelity and position by instrument", by_measure.sort_values(["construct", "measure", "kind"])),
    ("Event-order ceiling: the authors' own passages against their own briefs", ceiling),
    ("The region rule applied to the authors and to the strangers (the ceiling and the floor)",
     own_floor.groupby(["group", "author_class"])[["rate_inside_3_measures", "rate_inside_all5"]].mean().reset_index()),
    ("Author-region rate by configuration", region_summary),
    ("Anchor-definition sensitivity for the ref-anchored measures",
     sens.groupby("measure")[["sd_H_ref_set", "sd_H_single_partner", "sd_ratio_single_over_set",
                              "W1_P_H_ref_set", "W1_P_H_single_partner"]].median().reset_index()),
    ("Sentence-shuffle manipulation check (author vs their own shuffled passages)",
     shuf_check.groupby("measure")[["mean_author", "mean_shuffled", "mean_shift",
                                    "W1_shuffled_vs_author", "W1_strangers_vs_author"]].median().reset_index()),
    ("F against the shuffled-author floor, beside F against the stranger pool", shuffle_fid_summary),
    (f"Replicate floors used, per measure and family ({', '.join(floor_fams)})",
     floors.groupby(["measure", "family"]).abs_mean_diff.max().reset_index()),
]

write_readme(OUTD, "24 - The eval-cache measures on the authors' own passages", what, how, reading,
             caveats=caveats, tables=tables, figures=figs,
             extra=f"Runtime {time.time()-T0:.0f}s. {len(ref_measures)} author passages measured, "
                   f"{len(anch)} passage-by-anchor rows, {len(positions)} calibrated rows over "
                   f"{positions.measure.nunique()} instruments.")
print(f"[24] done in {time.time()-T0:.0f}s -> {OUTD}", flush=True)
