"""Score and judge runs that were generated elsewhere (cloud/sync_down.sh),
with the same s5/s5b/s6 calls run_author.py makes locally. Anchor for every
run is the base run of the same author at the same model tag; judges run in
the background on sample 0 with the judge.started marker.

    python dr/score_runs.py --from-pull-list            # runs/cloud_pull_list.json
    python dr/score_runs.py --runs chesterton_base8b,chesterton_paire6_8b
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DR, LOGS, RUNS, log, read_json  # noqa: E402

PY = sys.executable
RX = re.compile(r"^(?P<author>[a-z_0-9]+?)_(?:base|(?P<recipe>pair|mix|raw)e\d+_)(?P<tag>[0-9a-z]+)$")


def run(cmd, logname, background=False):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    logf = open(os.path.join(LOGS, logname), "a", encoding="utf-8")
    logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
    logf.flush()
    log(f"$ {' '.join(cmd)}  -> logs/{logname}")
    p = subprocess.Popen(cmd, cwd=DR, stdout=logf, stderr=subprocess.STDOUT, env=env)
    if background:
        return p
    if p.wait() != 0:
        raise RuntimeError(f"failed: {' '.join(cmd)}")


def parse(run_id):
    m = RX.match(run_id)
    if not m:
        return None
    return m.group("author"), m.group("tag")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="")
    ap.add_argument("--from-pull-list", action="store_true")
    ap.add_argument("--no-judge", action="store_true")
    a = ap.parse_args()
    runs = [r.strip() for r in a.runs.split(",") if r.strip()]
    if a.from_pull_list:
        runs += [r for r in read_json(os.path.join(RUNS, "cloud_pull_list.json"))["runs"] if not r.startswith("train_")]
    by_author = {}
    for r in runs:
        p = parse(r)
        if not p:
            log(f"skip {r}: not a base/adapter run id")
            continue
        author, tag = p
        anchor = f"{author}_base{tag}"
        if not os.path.exists(os.path.join(RUNS, r, "gens.jsonl")):
            log(f"skip {r}: no gens.jsonl")
            continue
        if not os.path.exists(os.path.join(RUNS, r, "scores.jsonl")):
            run([PY, "dr/s5_score.py", "--run", r, "--author", author, "--anchor-run", anchor], f"score_{r}.log")
        if not a.no_judge and not os.path.exists(os.path.join(RUNS, r, "judge.started")):
            p = run([PY, "dr/s5b_judge.py", "--run", r, "--author", author, "--only-samples", "0"], f"judge_{r}.log", background=True)
            open(os.path.join(RUNS, r, "judge.started"), "w").write(f"{p.pid}\n")
        by_author.setdefault((author, tag), []).append(r)
    for (author, tag), rs in by_author.items():
        rs = sorted(set(rs + [f"{author}_base4b_frontier"] if os.path.exists(os.path.join(RUNS, f"{author}_base4b_frontier", "scores.jsonl")) else rs))
        out = os.path.join(RUNS, "author_runs", f"{author}_{tag}")
        run([PY, "dr/s6_analysis.py", "--runs", ",".join(rs), "--out", out], f"analysis_{author}_{tag}.log")
        run([PY, "dr/review_page.py", "--author", author, "--runs", ",".join(rs), "--n", "3", "--out", os.path.join(RUNS, f"review_{author}_{tag}.html")], f"analysis_{author}_{tag}.log")
        log(f"{author}/{tag}: analysed {rs} -> {out}")
    run([PY, "dr/backup_runs.py"], "backup.log")
    log("score_runs complete (judges may still be running in the background)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
