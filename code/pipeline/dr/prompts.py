"""Reads PROMPTS.md and assembles arm prompts.

The markdown is the source of truth; nothing here contains prompt text. A block
is the fenced code that follows `<!-- id: NAME -->`. Block text keeps its
trailing newline, so a block that ends in a blank line concatenates with one
blank line after it, which is how the user message gets its spacing.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import DR, read_text

_BLOCK = re.compile(r"<!--\s*id:\s*([a-z0-9_]+)\s*-->\s*\n```[a-z]*\n(.*?)\n```", re.S)


def load_blocks(path=None):
    text = read_text(path or os.path.join(DR, "PROMPTS.md"))
    blocks = {m.group(1): m.group(2) + "\n" for m in _BLOCK.finditer(text)}
    need = {"brief_system", "brief_user", "brief_retry_suffix", "guide_system", "guide_user",
            "quant_block", "gen_system", "gen_user", "name_block", "exemplar_block",
            "guide_block", "quant_block_wrap", "train_continue", "train_infill",
            "judge_2afc_system", "judge_2afc_user", "judge_coverage_system",
            "judge_coverage_user"}
    missing = need - set(blocks)
    if missing:
        raise SystemExit(f"PROMPTS.md is missing blocks: {sorted(missing)}")
    return blocks


class Prompts:
    def __init__(self, path=None):
        self.b = load_blocks(path)

    # ---- decomposition
    def brief(self, passage, n_words, retry=None, max_words=None):
        user = self.b["brief_user"].format(n_words=n_words, passage=passage,
                                           max_words=max_words or max(180, int(0.4 * n_words))).strip()
        if retry:
            user += self.b["brief_retry_suffix"].format(**retry).rstrip()
        return self.b["brief_system"].strip(), user

    # ---- guide
    def guide(self, passages):
        joined = "\n\n=====\n\n".join(passages)
        return self.b["guide_system"].strip(), self.b["guide_user"].format(passages=joined).strip()

    # ---- quant block rendered from a dict of the nine SHOWN features
    def quant(self, q):
        return self.b["quant_block"].format(**q).strip()

    # ---- generation
    def gen_system(self):
        return self.b["gen_system"].strip()

    def gen_user(self, arm, brief, author_name=None, exemplars=None, guide=None, quant=None):
        use_name, use_ex, use_guide, use_quant = config.ARMS[arm]
        name_block = self.b["name_block"].format(author_name=author_name) if use_name else ""
        ex_block = ""
        if use_ex:
            ex = list(exemplars or [])
            if len(ex) != 3:
                raise ValueError(f"arm {arm} needs 3 exemplars, got {len(ex)}")
            ex_block = self.b["exemplar_block"].format(ex1=ex[0], ex2=ex[1], ex3=ex[2])
        guide_block = self.b["guide_block"].format(guide=guide.strip()) if use_guide else ""
        quant_block = self.b["quant_block_wrap"].format(quant=quant.strip()) if use_quant else ""
        return self.b["gen_user"].format(name_block=name_block, exemplar_block=ex_block,
                                         guide_block=guide_block, quant_block=quant_block,
                                         brief=brief.strip()).strip()

    # ---- training views
    def train_continue(self, preceding):
        return self.b["train_continue"].format(preceding=preceding.strip()).strip()

    def train_infill(self, before, after):
        return self.b["train_infill"].format(before=before.strip(), after=after.strip()).strip()

    # ---- judges
    def judge_2afc(self, reference, cand_a, cand_b):
        return (self.b["judge_2afc_system"].strip(),
                self.b["judge_2afc_user"].format(reference=reference, cand_a=cand_a,
                                                 cand_b=cand_b).strip())

    def judge_coverage(self, brief, passage):
        return (self.b["judge_coverage_system"].strip(),
                self.b["judge_coverage_user"].format(brief=brief, passage=passage).strip())


if __name__ == "__main__":
    p = Prompts()
    print(sorted(p.b))
    print("---- A5 skeleton ----")
    print(p.gen_user("A5", "BRIEF", exemplars=["E1", "E2", "E3"], guide="GUIDE", quant="QUANT"))
