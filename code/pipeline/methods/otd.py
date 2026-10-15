"""S4 opener-class transition distance (OTD), from R1.

Replace surface first words with a fronting taxonomy (Biber 1988 dimensions
simplified to what a POS tagger labels reliably): QUOTE, CONJ (coordinator),
DISC (discourse marker), SUBORD (subordinator), PP (preposition-fronted),
ADV (other adverbial), PART (participial), PRON (pronoun subject), NP
(determiner / noun / proper / adjective / number), OTHER. The generation's
class distribution p is compared to its source's q by the Jensen-Shannon
distance sqrt(JSD(p||q)) (base 2, so 0..1). Raw class shares are also
reported unpaired with the SOURCE rows.

open_distinct100 is a SHOWN feature, so on A4/A5 this is compliance, not
outcome. Uses spaCy en_core_web_sm (tagger only) on the default interpreter.
"""
from __future__ import annotations

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, sentences  # noqa: E402

import spacy  # noqa: E402

_NLP = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
CLASSES = ["QUOTE", "CONJ", "DISC", "SUBORD", "PP", "ADV", "PART", "PRON", "NP", "OTHER"]
DISC = set("""however then now still yet so meanwhile anyway besides instead nevertheless nonetheless
otherwise moreover indeed finally first second third next later afterwards perhaps maybe also again
thus hence therefore well today tonight yesterday tomorrow once sometimes suddenly""".split())
SUB = set("""when if although though because while as since until unless whereas whenever wherever
before after once whether even""".split())


def opener_class(sent: str) -> str:
    s = sent.strip()
    if not s:
        return "OTHER"
    if s[0] in "\"'“‘":
        return "QUOTE"
    doc = _NLP(" ".join(s.split()[:6]))
    toks = [t for t in doc if not t.is_punct and not t.is_space]
    if not toks:
        return "OTHER"
    t = toks[0]
    w = t.text.lower()
    if t.pos_ == "CCONJ" or w in ("and", "but", "or", "nor", "yet", "so"):
        return "CONJ" if w != "so" or t.pos_ == "CCONJ" else "DISC"
    if w in DISC:
        return "DISC"
    if t.pos_ == "SCONJ" or w in SUB:
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


def profile(text):
    counts = {c: 0 for c in CLASSES}
    n = 0
    for s in sentences(text):
        if s.strip():
            counts[opener_class(s)] += 1
            n += 1
    out = {f"share_{c}": (counts[c] / n if n else 0.0) for c in CLASSES}
    out["n_sent"] = n
    return out


def _js(p, q):
    m = [(a + b) / 2 for a, b in zip(p, q)]

    def kl(x, y):
        return sum(a * math.log2(a / b) for a, b in zip(x, y) if a > 0 and b > 0)
    return math.sqrt(max(0.0, (kl(p, m) + kl(q, m)) / 2))


def paired(g, s, stats):
    p = [g[f"share_{c}"] for c in CLASSES]
    q = [s[f"share_{c}"] for c in CLASSES]
    return {"otd_js": _js(p, q), "np_share_diff": g["share_NP"] - s["share_NP"], "pron_share_diff": g["share_PRON"] - s["share_PRON"]}


if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "A0"
    evaluate(profile, "otd_raw", arm=arm, quiet=True)
    evaluate(profile, "otd", arm=arm, paired=paired, quiet=True)
