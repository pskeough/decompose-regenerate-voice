"""Replay set for the adherence fix: the base model's own outputs on the
TRAIN briefs, so the adapter rehearses "follow the brief" while it learns
the author's prose. No external instruction data, everything local.

Writes data/<author>/replay_base.jsonl with rows {system, user, target}
consumed by `s4_train.py --replay-file ... --replay-frac 0.10`. Needs the
base server up (dr/llamacpp.py start --model <F16 GGUF>).

    python dr/make_replay.py --author wharton
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import author_dir, log, read_jsonl, write_jsonl  # noqa: E402
from dr.prompts import Prompts  # noqa: E402
from dr.s3_generate import clean  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--server", default="http://127.0.0.1:8089")
    ap.add_argument("--slots", type=int, default=8)
    a = ap.parse_args()
    from transformers import AutoTokenizer
    from dr import llamacpp as L
    if not L.alive(a.server):
        raise SystemExit("start the base server first: python dr/llamacpp.py start --model <F16 GGUF>")
    d = author_dir(a.author)
    P = Prompts()
    tok = AutoTokenizer.from_pretrained(config.BASE_MODEL)
    briefs = [b for b in read_jsonl(os.path.join(d, "briefs_train.jsonl")) if b.get("passed")]
    system = P.gen_system()
    out_path = os.path.join(d, "replay_base.jsonl")
    done = {r["id"] for r in read_jsonl(out_path)} if os.path.exists(out_path) else set()
    todo = [b for b in briefs if b["id"] not in done]
    log(f"{len(briefs)} train briefs, {len(done)} done, {len(todo)} to generate")

    def one(b):
        user = P.gen_user("A0", b["brief"])
        prompt = L.render_prompt(tok, system, user)
        max_new = min(config.SAMPLING["max_new_cap"], int(config.SAMPLING["len_mult"] * b["source_words"] * 1.35))
        r = L.complete(prompt, max_new, seed=config.SEED + 11, url=a.server)
        text, flags = clean(r["text"])
        return {"id": b["id"], "system": system, "user": user, "target": text, "flags": flags, "words": len(text.split())}

    rows = []
    with ThreadPoolExecutor(a.slots) as ex:
        for f in as_completed([ex.submit(one, b) for b in todo]):
            rows.append(f.result())
            if len(rows) % 20 == 0:
                log(f"  {len(rows)}/{len(todo)}")
    kept = [r for r in rows if "truncated" not in r["flags"] and r["words"] >= 150]
    write_jsonl(out_path, kept, mode="a")
    log(f"{len(kept)} replay rows appended -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
