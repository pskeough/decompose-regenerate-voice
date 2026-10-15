"""Re-score and re-judge every existing run on punctuation-normalised text
(DECISIONS 2026-09-05). Raw-text results are kept beside the new ones:
scores_raw.jsonl, judge_raw.jsonl, coverage_raw.jsonl, judge_summary_raw.json.

GPU for the embeddings (about 4 min per run, nothing else on the card), API
for the judges (~USD 8 for the twelve runs). Resumable.

    python dr/rescore_normalised.py            # everything
    python dr/rescore_normalised.py --no-judge # scores only
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DR, LOGS, RUNS, credits_usd, log  # noqa: E402

PY = sys.executable
# run -> (author, anchor)
RUNS_TO_DO = [
    ("base4b", "wharton", "base4b"), ("base4b_frontier", "wharton", "base4b"), ("pair4b", "wharton", "base4b"),
    ("mix4b", "wharton", "base4b"), ("raw4b", "wharton", "base4b"), ("pair_e6_4b", "wharton", "base4b"),
    ("pair_s1_4b", "wharton", "base4b"),
    ("cather_base4b", "cather", "cather_base4b"), ("cather_base4b_frontier", "cather", "cather_base4b"),
    ("cather_pair4b", "cather", "cather_base4b"),
    ("patrick_base4b", "patrick", "patrick_base4b"), ("patrick_base4b_frontier", "patrick", "patrick_base4b"),
    ("patrick_pair4b", "patrick", "patrick_base4b"), ("patrick_mix4b", "patrick", "patrick_base4b"),
    ("patrick_stories4b", "patrick", "patrick_base4b"),
]


def run(cmd, logname):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    with open(os.path.join(LOGS, logname), "a", encoding="utf-8") as logf:
        logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
        logf.flush()
        rc = subprocess.run(cmd, cwd=DR, stdout=logf, stderr=subprocess.STDOUT, env=env).returncode
    if rc != 0:
        raise RuntimeError(f"exit {rc}: {' '.join(cmd)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated run ids")
    ap.add_argument("--judge-runs", default="base4b,pair_e6_4b,patrick_base4b,patrick_mix4b", help="runs to re-judge (sample 0 only); others get scores only")
    a = ap.parse_args()
    todo = [t for t in RUNS_TO_DO if os.path.exists(os.path.join(RUNS, t[0], "gens.jsonl"))
            and (not a.only or t[0] in a.only.split(","))]
    if not a.no_judge:
        bal = credits_usd()
        log(f"balance {bal}; judges need ~USD 8")
        if bal is not None and bal < 5:
            raise SystemExit("top up before re-judging, or pass --no-judge")
    for run_id, author, anchor in todo:
        rd = os.path.join(RUNS, run_id)
        man = os.path.join(rd, "s5_manifest.json")
        done = False
        if os.path.exists(man):
            import json
            done = json.load(open(man, encoding="utf-8")).get("normalised") is True
        if not done:
            log(f"scoring {run_id} (normalised)")
            run([PY, "dr/s5_score.py", "--run", run_id, "--author", author, "--anchor-run", anchor], "rescore.log")
        if a.no_judge or run_id not in a.judge_runs.split(","):
            continue
        if os.path.exists(os.path.join(rd, "judge.jsonl")) and not os.path.exists(os.path.join(rd, "judge_raw.jsonl")):
            for f in ("judge.jsonl", "coverage.jsonl", "judge_summary.json", "judge.started"):
                if os.path.exists(os.path.join(rd, f)):
                    shutil.move(os.path.join(rd, f), os.path.join(rd, f.replace(".", "_raw.", 1)))
            log(f"{run_id}: raw judge files moved aside")
        if not os.path.exists(os.path.join(rd, "judge_summary.json")):
            log(f"judging {run_id} (normalised)")
            run([PY, "dr/s5b_judge.py", "--run", run_id, "--author", author, "--only-samples", "0"], "rescore.log")
    log("rescore complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
