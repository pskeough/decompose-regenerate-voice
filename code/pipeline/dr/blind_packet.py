"""Blind reading packet for a gate: K passages, each with the real source and
one output per condition, conditions shuffled and unlabeled. A key file maps
letters back to conditions. Patrick reads the packet, ranks, then opens the key.

    python dr/blind_packet.py --runs base4b,pair4b,mix4b,raw4b --arm A0 --k 5 --out runs/blind_G5
    python dr/blind_packet.py --runs base4b --arms A0,A1,A5 --k 5 --out runs/blind_G3
"""
from __future__ import annotations

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import RUNS, author_dir, read_jsonl, write_json, write_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--runs", required=True, help="comma-separated run ids (each is a model)")
    ap.add_argument("--arms", default="A0", help="comma-separated arms to include from each run")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=config.SEED)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = author_dir(a.author)
    test = {r["id"]: r for r in read_jsonl(os.path.join(d, "test.jsonl"))}
    runs = [r for r in a.runs.split(",") if r]
    arms = [x for x in a.arms.split(",") if x]
    conds = [(run, arm) for run in runs for arm in arms]
    gens = {}
    for run in runs:
        for g in read_jsonl(os.path.join(RUNS, run, "gens.jsonl")):
            if g["sample"] == a.sample and g["arm"] in arms:
                gens[(g["id"], run, g["arm"])] = g["text"]
    complete = [pid for pid in sorted(test) if all((pid, run, arm) in gens for run, arm in conds)]
    R = random.Random(a.seed)
    pick = R.sample(complete, min(a.k, len(complete)))
    packet, key = [f"# Blind packet ({len(pick)} passages, {len(conds)} conditions + the real one)", "",
                   "Each passage: the brief's source is shown first as REAL. Then lettered candidates in random order. "
                   "Rank the candidates by how much they read like the REAL author. Do not open the key until done.", ""], {}
    for n, pid in enumerate(pick, 1):
        items = [(run, arm, gens[(pid, run, arm)]) for run, arm in conds]
        R.shuffle(items)
        letters = "ABCDEFGH"
        packet += [f"## Passage {n}  ({test[pid]['work']}, {test[pid]['words']} words)", "",
                   "### REAL", "", test[pid]["text"], ""]
        key[f"passage_{n}"] = {"id": pid}
        for L, (run, arm, text) in zip(letters, items):
            packet += [f"### Candidate {L}", "", text, ""]
            key[f"passage_{n}"][L] = f"{run}/{arm}"
        packet.append("---\n")
    os.makedirs(a.out, exist_ok=True)
    write_text(os.path.join(a.out, "PACKET.md"), "\n".join(packet))
    write_json(os.path.join(a.out, "KEY.json"), key)
    print(f"{len(pick)} passages x {len(conds)} conditions -> {a.out}/PACKET.md (key in KEY.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
