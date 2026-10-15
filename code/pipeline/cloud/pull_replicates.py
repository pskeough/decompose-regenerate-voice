"""Puller for the replicate pods (2026-09-11): pull every finished {author}_base{tag}_r2 run
(gens.jsonl and its s3 manifest on the pod), score it locally against {author}_base{tag}, judge
it (Gemini 2AFC + coverage, sample 0), and terminate each pod when its sweep log says
"pod sweep complete" and every run it produced is local. Same tar-to-file pull as pull_loop.

    python cloud/pull_replicates.py --pods logs/pods_rep_0911.txt --ids logs/rep_pod_ids.txt
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

DR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DR)
from dr.core import LOGS, RUNS, log  # noqa: E402
from cloud.pull_loop import pull, ssh  # noqa: E402

PY = sys.executable
JUDGE = "google/gemini-3.1-flash-lite-preview"
LIST = r'''
import json, glob, os
os.chdir("/workspace/decompose_regenerate")
out = []
for d in sorted(glob.glob("runs/*_base*_r2")):
    r = os.path.basename(d)
    out.append({"run": r, "ready": os.path.isfile(f"{d}/gens.jsonl") and bool(glob.glob(f"{d}/s3_manifest*"))})
done = os.path.exists("logs/pod_sweep.log") and "pod sweep complete" in open("logs/pod_sweep.log").read()
print(json.dumps({"runs": out, "done": done}))
'''
RUN_RE = re.compile(r"^(?P<author>[a-z0-9_]+?)_base(?P<tag>[0-9a-z]+)_r2$")


def local_has(run):
    return os.path.isfile(os.path.join(RUNS, run, "gens.jsonl")) and bool([f for f in os.listdir(os.path.join(RUNS, run)) if f.startswith("s3_manifest")]) if os.path.isdir(os.path.join(RUNS, run)) else False


def score_and_judge(run):
    m = RUN_RE.match(run)
    if not m:
        log(f"[rep] {run}: name not parsed, skipped"); return
    author, tag = m.group("author"), m.group("tag")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if not os.path.exists(os.path.join(RUNS, run, "scores.jsonl")):
        log(f"[rep] scoring {run} against {author}_base{tag}")
        with open(os.path.join(LOGS, "rep_local_score.log"), "a", encoding="utf-8") as f:
            subprocess.run([PY, "-u", "dr/s5_score.py", "--run", run, "--author", author, "--anchor-run", f"{author}_base{tag}"], cwd=DR, env=env, stdout=f, stderr=subprocess.STDOUT)
    marker = os.path.join(RUNS, run, "judge.started")
    if os.path.exists(os.path.join(RUNS, run, "scores.jsonl")) and not os.path.exists(marker):
        open(marker, "w").write("pull_replicates\n")
        log(f"[rep] judging {run}")
        with open(os.path.join(LOGS, "rep_local_judge.log"), "a", encoding="utf-8") as f:
            subprocess.run([PY, "-u", "dr/s5b_judge.py", "--run", run, "--author", author, "--judges", JUDGE, "--only-samples", "0"], cwd=DR, env=env, stdout=f, stderr=subprocess.STDOUT)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pods", required=True)
    ap.add_argument("--ids", required=True)
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--max-hours", type=float, default=6.0)
    a = ap.parse_args()
    ids = {}
    if os.path.exists(a.ids):
        for line in open(a.ids):
            p = line.split()
            if len(p) >= 2:
                ids[p[0]] = p[1]
    finished, t0 = set(), time.time()
    while True:
        pods = [l.split() for l in open(a.pods) if l.strip()] if os.path.exists(a.pods) else []
        for host, port, name in [(p[0], p[1], p[2]) for p in pods if len(p) >= 3]:
            if name in finished:
                continue
            try:
                rc, out, err = ssh(host, port, f"python - <<'PY'\n{LIST}\nPY")
            except Exception as e:
                log(f"[rep] {name}: ssh failed {e!r}"); continue
            if rc != 0 or not out.strip():
                log(f"[rep] {name}: list failed rc={rc} {err[:120]}"); continue
            info = json.loads(out.strip().splitlines()[-1])
            owed = []
            for r in info["runs"]:
                if local_has(r["run"]):
                    score_and_judge(r["run"]); continue
                if not r["ready"]:
                    owed.append(r["run"]); continue
                log(f"[rep] {name}: pulling {r['run']}")
                ok = pull(host, port, [f"runs/{r['run']}", "logs/pod_sweep.log", f"logs/replicate_{r['run']}.log"])
                if ok and local_has(r["run"]):
                    score_and_judge(r["run"])
                else:
                    owed.append(r["run"])
            if info["done"] and not owed:
                pid = ids.get(name)
                log(f"[rep] {name}: sweep complete, all local; terminating pod {pid}")
                if pid:
                    subprocess.run([PY, "cloud/pod.py", "rest-terminate", "--id", pid], cwd=DR, timeout=180)
                finished.add(name)
            else:
                log(f"[rep] {name}: done={info['done']} owed={owed}")
        if pods and len(finished) == len(pods):
            break
        if time.time() - t0 > a.max_hours * 3600:
            log(f"[rep] {a.max_hours} h elapsed; terminating every listed pod and stopping")
            for name, pid in ids.items():
                subprocess.run([PY, "cloud/pod.py", "rest-terminate", "--id", pid], cwd=DR, timeout=180)
            break
        time.sleep(a.interval)
    log("[rep] puller finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
