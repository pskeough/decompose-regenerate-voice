"""Puller for the size-series pods (2026-09-10): every --interval seconds ask each pod which
size points are finished (runs/<author>_size<n>[_s<seed>]/size_point.json with done=true and
the generations on disk), pull the run and its train directory (tar to a temp file, tarfile
extract, nothing local ever overwritten; the pull_loop routine), then score the run locally
against the author's 4B base run and judge it, one run at a time on the local card. When a
pod's sweep log says "pod sweep complete" and every point it lists is local, terminate it.

    python cloud/pull_size.py --pods logs/pods_size_0910.txt --ids logs/size_pod_ids.txt
        pods file lines: <host> <port> <name>   (written by cloud/launch_pod.sh)
        ids file lines:  <name> <pod-id>        (written by the launcher)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

DR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DR)
from dr.core import LOGS, RUNS, log  # noqa: E402
from cloud.pull_loop import pull, ssh  # noqa: E402

PY = sys.executable
LIST = r'''
import json, glob, os
os.chdir("/workspace/decompose_regenerate")
out = []
for sp in sorted(glob.glob("runs/*_size*/size_point.json")):
    st = json.load(open(sp))
    r = st.get("run"); t = st.get("train_tag")
    gens = os.path.isfile(f"runs/{r}/gens.jsonl") and bool(glob.glob(f"runs/{r}/s3_manifest*"))
    art = os.path.isfile(f"runs/train_{t}/adapter/adapter_model.safetensors") and os.path.isfile(f"runs/train_{t}/run.json")
    out.append({"run": r, "train": f"train_{t}", "author": st.get("author"), "done": bool(st.get("done")), "ready": bool(st.get("done") and gens and art)})
done = os.path.exists("logs/pod_sweep.log") and "pod sweep complete" in open("logs/pod_sweep.log").read()
print(json.dumps({"runs": out, "done": done}))
'''


def local_has(run, train):
    return os.path.isfile(os.path.join(RUNS, run, "gens.jsonl")) and os.path.isfile(os.path.join(RUNS, train, "run.json"))


def score_and_judge(run, author):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if not os.path.exists(os.path.join(RUNS, run, "scores.jsonl")):
        log(f"[size] scoring {run} against {author}_base4b")
        with open(os.path.join(LOGS, "size_local_score.log"), "a", encoding="utf-8") as f:
            subprocess.run([PY, "-u", "dr/s5_score.py", "--run", run, "--author", author, "--anchor-run", f"{author}_base4b"], cwd=DR, env=env, stdout=f, stderr=subprocess.STDOUT)
    marker = os.path.join(RUNS, run, "judge.started")
    if os.path.exists(os.path.join(RUNS, run, "scores.jsonl")) and not os.path.exists(marker):
        open(marker, "w").write("pull_size\n")
        log(f"[size] judging {run}")
        with open(os.path.join(LOGS, "size_local_judge.log"), "a", encoding="utf-8") as f:
            subprocess.run([PY, "-u", "dr/s5b_judge.py", "--run", run, "--author", author, "--only-samples", "0"], cwd=DR, env=env, stdout=f, stderr=subprocess.STDOUT)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pods", required=True)
    ap.add_argument("--ids", required=True)
    ap.add_argument("--interval", type=int, default=600)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    ids = {}
    if os.path.exists(a.ids):
        for line in open(a.ids):
            p = line.split()
            if len(p) >= 2:
                ids[p[0]] = p[1]
    finished = set()
    pulled = []
    while True:
        pods = [l.split() for l in open(a.pods) if l.strip()] if os.path.exists(a.pods) else []
        for host, port, name in [(p[0], p[1], p[2]) for p in pods if len(p) >= 3]:
            if name in finished:
                continue
            try:
                rc, out, err = ssh(host, port, f"python - <<'PY'\n{LIST}\nPY")
            except Exception as e:
                log(f"[size] {name}: ssh failed {e!r}"); continue
            if rc != 0 or not out.strip():
                log(f"[size] {name}: list failed rc={rc} {err[:120]}"); continue
            info = json.loads(out.strip().splitlines()[-1])
            owed = []
            for r in info["runs"]:
                if local_has(r["run"], r["train"]):
                    if r["run"] not in pulled:
                        pulled.append(r["run"])
                    # pulled by hand (2026-09-10 17:05, patrick_v2) or by an earlier puller that died: score and judge here
                    if not os.path.exists(os.path.join(RUNS, r["run"], "scores.jsonl")) or not os.path.exists(os.path.join(RUNS, r["run"], "judge.started")):
                        score_and_judge(r["run"], r["author"])
                    continue
                if not r["ready"]:
                    owed.append(r["run"]); continue
                log(f"[size] {name}: pulling {r['run']} + {r['train']}")
                ok = pull(host, port, [f"runs/{r['run']}", f"runs/{r['train']}", f"logs/size_{r['author']}.log", "logs/pod_sweep.log", "logs/size_pod.log"])
                if ok and local_has(r["run"], r["train"]):
                    pulled.append(r["run"])
                    score_and_judge(r["run"], r["author"])
                else:
                    owed.append(r["run"])
            if info["done"] and not owed:
                pid = ids.get(name)
                log(f"[size] {name}: sweep complete, {len([r for r in info['runs']])} points local; terminating pod {pid}")
                if pid:
                    subprocess.run([PY, "cloud/pod.py", "rest-terminate", "--id", pid], cwd=DR, timeout=180)
                finished.add(name)
            else:
                log(f"[size] {name}: done={info['done']} owed={owed}")
        # runs pulled from a pod that is no longer listed (terminated by hand): score and judge them too
        for d in sorted(os.listdir(RUNS)):
            sp = os.path.join(RUNS, d, "size_point.json")
            if "_size" in d and os.path.exists(sp) and os.path.exists(os.path.join(RUNS, d, "gens.jsonl")):
                if not os.path.exists(os.path.join(RUNS, d, "scores.jsonl")) or not os.path.exists(os.path.join(RUNS, d, "judge.started")):
                    score_and_judge(d, json.load(open(sp)).get("author"))
        if a.once or (pods and len(finished) == len(pods)):
            break
        time.sleep(a.interval)
    log(f"[size] puller finished; pulled {pulled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
