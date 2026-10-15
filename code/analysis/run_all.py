"""run_all.py: rebuild the master tables and run every numbered analysis script in order.

    python scripts/run_all.py            # 01 then 10..99
    python scripts/run_all.py --from 14  # skip the rebuild, start at script 14
    python scripts/run_all.py --only 15,18
    python scripts/run_all.py --from 10 --jobs 4   # independent scripts in parallel; 22-25 wait for their inputs

Writes analysis/RUN_LOG.md with runtime and exit status per script. A failing script is
reported and the run continues, so one broken analysis never hides the others.
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "code", "analysis")
PY = sys.executable


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--jobs", type=int, default=1, help="scripts to run concurrently (each reads data/master, writes its own folder)")
    a = ap.parse_args()
    only = {int(x) for x in a.only.split(",") if x.strip()}
    scripts = []
    for p in sorted(glob.glob(os.path.join(SCRIPTS, "[0-9][0-9]_*.py"))):
        n = int(os.path.basename(p)[:2])
        if n == 0:
            continue
        if only and n not in only:
            continue
        if not only and n < a.start:
            continue
        if n == 1 and (a.start > 1):
            continue
        scripts.append((n, p))
    rows = []
    env = dict(os.environ, PYTHONIOENCODING="utf-8", MPLBACKEND="Agg")
    # scripts that read another script's folder run after it (22 harvests 14's tests, 23 reads 15, 24 reads 23)
    AFTER = {22: {14}, 23: {15}, 24: {23}, 26: {10, 11, 12, 18, 25}, 27: {10}, 29: {10, 20, 28}, 30: {24}}

    def run_one(n, p):
        t0 = time.time()
        r = subprocess.run([PY, p], cwd=ROOT, env=env, capture_output=True, text=True)
        dt = time.time() - t0
        ok = r.returncode == 0
        tail = (r.stderr or r.stdout).strip().splitlines()[-3:]
        print(f"{'ok ' if ok else 'FAIL'} {os.path.basename(p):48} {dt:7.0f}s", flush=True)
        if not ok:
            print("   ", "\n    ".join(tail), flush=True)
        return (n, os.path.basename(p), ok, dt, " | ".join(tail)[:300])

    if a.jobs <= 1:
        for n, p in scripts:
            rows.append(run_one(n, p)[1:])
    else:
        from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
        pending = dict(scripts)
        done, running = set(), {}
        results = {}
        with ThreadPoolExecutor(max_workers=a.jobs) as ex:
            while pending or running:
                for n in sorted(pending):
                    if len(running) >= a.jobs:
                        break
                    deps = AFTER.get(n, set()) & set(dict(scripts))
                    if deps <= done:
                        running[ex.submit(run_one, n, pending.pop(n))] = n
                if not running:
                    break
                fin, _ = wait(list(running), return_when=FIRST_COMPLETED)
                for f in fin:
                    n = running.pop(f)
                    results[n] = f.result()
                    done.add(n)
        rows = [results[n][1:] for n in sorted(results)]
    lines = [f"# Run log {time.strftime('%Y-%m-%d %H:%M')}", "", "| script | status | seconds | last lines |", "|---|---|---:|---|"]
    for name, ok, dt, tail in rows:
        lines.append(f"| {name} | {'ok' if ok else 'FAILED'} | {dt:.0f} | {tail.replace('|', '/')} |")
    open(os.path.join(ROOT, "results", "RUN_LOG.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    return 0 if all(ok for _, ok, _, _ in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
