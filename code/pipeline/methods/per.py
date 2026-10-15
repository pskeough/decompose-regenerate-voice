"""S6 proposition-echo rate (PER), from R2.

For each sentence take the set of unordered content-word pairs; a sentence is
an echo if more than ECHO_FRAC of its pairs appeared in an earlier sentence.
PER is the share of echoing sentences among sentences with at least two
content words. A sensitised sent_echo: pairs instead of unigrams, 0.25 instead
of 0.70, so it fires on restatement in fresh wording, not only near-duplicates.
Primary version is capped at 600 words (length confound: rho with word count
up to +0.57 uncapped on the 1.7B runs).

Grounding: Holtzman et al. 2020 (degeneration); Guan and Huang 2020 (UNION's
repetition perturbation). Unpaired: the SOURCE rows are the author's own rate.
"""
from __future__ import annotations

import itertools
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, sentences  # noqa: E402

ECHO_FRAC = 0.25
STOP = set("""
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
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]+")


def content_words(sent):
    return [w.lower() for w in _WORD.findall(sent) if len(w) > 2 and w.lower() not in STOP]


def per(text):
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


if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "A0"
    evaluate(per, "per", arm=arm, cap=600, quiet=True)
    evaluate(per, "per", arm=arm, cap=None, quiet=True)
