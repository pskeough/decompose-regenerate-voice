"""Add-only merge of fill-in generations fetched from a pod.

    python cloud/merge_fillin.py --run patrick_v2_paire6_8b --src gens_fillin_podA.jsonl

Reads runs/<run>/<src> (a full gens.jsonl copied from the pod under a new
name), appends to runs/<run>/gens.jsonl every row whose (id, arm, sample) is
not already present, and never rewrites or reorders existing rows. Runs
dr/backup_runs.py first so the pre-merge file is versioned. Prints the arm
counts before and after. Refuses to run if the source file is missing or
contains no new rows.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys

DR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DR)
from dr.core import RUNS, log  # noqa: E402


def counts(rows):
    return dict(sorted(collections.Counter(r["arm"] for r in rows).items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--src", required=True, help="file name inside the run dir, e.g. gens_fillin_podA.jsonl")
    a = ap.parse_args()
    rd = os.path.join(RUNS, a.run)
    dst = os.path.join(rd, "gens.jsonl")
    src = os.path.join(rd, a.src)
    if not os.path.exists(src):
        raise SystemExit(f"missing {src}")
    with open(dst, encoding="utf-8-sig") as f:
        local = [json.loads(l) for l in f if l.strip()]
    with open(src, encoding="utf-8-sig") as f:
        pod = [json.loads(l) for l in f if l.strip()]
    have = {(r["id"], r["arm"], int(r.get("sample", 0))) for r in local}
    new = [r for r in pod if (r["id"], r["arm"], int(r.get("sample", 0))) not in have]
    log(f"{a.run}: local {len(local)} rows {counts(local)}; pod {len(pod)} rows {counts(pod)}; new {len(new)} {counts(new)}")
    if not new:
        raise SystemExit("nothing new to merge")
    subprocess.run([sys.executable, "dr/backup_runs.py"], cwd=DR, capture_output=True)
    with open(dst, "a", encoding="utf-8", newline="\n") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(dst, encoding="utf-8-sig") as f:
        after = [json.loads(l) for l in f if l.strip()]
    log(f"{a.run}: after merge {len(after)} rows {counts(after)}")
    with open(os.path.join(rd, "merge_fillin.json"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"src": a.src, "added": len(new), "arms": counts(new)}) + "\n")


if __name__ == "__main__":
    main()
