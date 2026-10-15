"""Overnight puller: every few minutes, ask each pod which runs have passed a
generation gate, pull any run not yet complete locally (tar over ssh, never
overwriting), back up, and queue it for local scoring. A pod that dies takes
nothing finished with it. Ends when every pod reports "pod sweep complete"
and everything is pulled, or on --once.

    python cloud/pull_loop.py --pods logs/pods_0908.txt        # lines: <host> <port> <name>
    python cloud/pull_loop.py --pods logs/pods_0908.txt --once

Queue: logs/score_queue.txt (one run id per line); cloud/score_worker.sh
consumes it on the local card.
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

KEY = os.path.expanduser("~/.ssh/dr_runpod")
QUEUE = os.path.join(LOGS, "score_queue.txt")
REMOTE = "/workspace/decompose_regenerate"

LIST_SCRIPT = r'''
import json, glob, os
os.chdir("/workspace/decompose_regenerate")
out = []
def ready(run, train=None):
    d = f"runs/{run}"
    if not (os.path.isfile(f"{d}/gens.jsonl") and glob.glob(f"{d}/s3_manifest*")):
        return False
    if train:
        # runtime-LoRA runs carry adapter.gguf; merged-weights runs delete their 7-29 GB merged.gguf
        # after generating (2026-09-10), so the peft adapter plus run.json is the artefact that counts
        art = os.path.isfile(f"runs/{train}/adapter.gguf") or os.path.isfile(f"runs/{train}/merged.gguf") or os.path.isfile(f"runs/{train}/adapter/adapter_model.safetensors")
        if not (art and os.path.isfile(f"runs/{train}/run.json")):
            return False
    return True
for sp in glob.glob("runs/cloud_state_*.json"):
    st = json.load(open(sp))
    tag = sp.rsplit("_", 1)[1][:-5]
    author = os.path.basename(sp)[len("cloud_state_"):-len("_" + tag + ".json")]
    names = {s.get("name") for s in st["steps"]}
    ok = {s.get("name") for s in st["steps"] if s.get("ok")}
    # pull every finished run, gate-passed or not: a failed gate is a result
    # to keep (the 25-brief adapters fail truncation by design), and a pod that
    # dies takes anything unpulled with it. The gate verdict travels in the
    # cloud_state file, pulled on every pass.
    # ready (2026-09-09 15:25): a run is pulled only once its s3 manifest exists
    # on the pod (and, for an adapter run, the trained adapter.gguf + run.json).
    # A step recorded as failed and then rerun (Watts) is otherwise listed while
    # it regenerates, and a partial gens.jsonl pulled mid-run can never be
    # refreshed because nothing local is overwritten.
    if "base run" in names:
        r = f"{author}_base{tag}"
        out.append({"run": r, "train": None, "gate_ok": "base run" in ok, "ready": ready(r)})
    if "adapter" in names:
        r, t = f"{author}_paire6_{tag}", f"train_{author}_pair_e6_{tag}"
        out.append({"run": r, "train": t, "gate_ok": "adapter" in ok, "ready": ready(r, t)})
# replicate base runs ({author}_base{tag}_r2, 2026-09-09 cross-family) have no cloud_state; list them when final
for d in glob.glob("runs/*_base*_r2"):
    r = os.path.basename(d)
    if ready(r):
        out.append({"run": r, "train": None, "gate_ok": True, "ready": True})
done = os.path.exists("logs/pod_sweep.log") and "pod sweep complete" in open("logs/pod_sweep.log").read()
print(json.dumps({"runs": out, "done": done}))
'''


def ssh(host, port, cmd, timeout=120):
    r = subprocess.run(["ssh", "-i", KEY, "-p", str(port), "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
                        "-o", "StrictHostKeyChecking=accept-new", f"root@{host}", cmd],
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def pull(host, port, paths, overwrite=False):
    """Download a tar.gz of `paths` to a temp file (ssh exit code checked),
    then extract with Python's tarfile, skipping any member that already
    exists locally. No shell tar, no pipe: a reader that exits early cannot
    leave the ssh writer blocked (the 2026-09-09 hang), and nothing local is
    ever overwritten, except with overwrite=True, used only for the pod's
    small cloud_state status files so local gate verdicts stay current."""
    import tarfile, tempfile
    # --ignore-failed-read: a listed path that is missing on the pod must not
    # fail the whole archive (2026-09-09 10:52: one absent log file cost the
    # cather 14B generation, because the caller then terminated the pod)
    tar_cmd = f"cd {REMOTE} && tar czf - --ignore-failed-read --exclude='checkpoint-*' --exclude='merged*' " + " ".join(paths)   # merged GGUFs (7-29 GB) stay on the pod; the LoRA safetensors travel
    fd, tmp = tempfile.mkstemp(suffix=".tgz", dir=LOGS)
    os.close(fd)
    try:
        with open(tmp, "wb") as f:
            r = subprocess.run(["ssh", "-i", KEY, "-p", str(port), "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
                                "-o", "StrictHostKeyChecking=accept-new", f"root@{host}", tar_cmd],
                               stdout=f, stderr=subprocess.PIPE, timeout=1800)
        if r.returncode != 0 or os.path.getsize(tmp) == 0:
            log(f"ssh tar failed rc={r.returncode}: {r.stderr.decode('utf-8', 'replace')[:120]}")
            return False
        n_new = n_skip = 0
        with tarfile.open(tmp, "r:gz") as tf:
            for m in tf:
                dest = os.path.join(DR, m.name)
                if m.isdir():
                    os.makedirs(dest, exist_ok=True)
                    continue
                if os.path.exists(dest) and not overwrite:
                    n_skip += 1
                    continue
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                src = tf.extractfile(m)
                if src is None:
                    continue
                with open(dest, "wb") as out:
                    while True:
                        chunk = src.read(1 << 20)
                        if not chunk:
                            break
                        out.write(chunk)
                n_new += 1
        log(f"extracted {n_new} files ({n_skip} already present) from {' '.join(paths)}")
        return True
    except Exception as e:
        log(f"pull error: {str(e)[:160]}")
        return False
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def complete_locally(run, train):
    ok = os.path.exists(os.path.join(RUNS, run, "gens.jsonl")) and any(f.startswith("s3_manifest") for f in os.listdir(os.path.join(RUNS, run)) if os.path.isdir(os.path.join(RUNS, run)))
    if train:
        # runtime-LoRA runs carry adapter.gguf; merged-weights runs (2026-09-09) carry the peft adapter only
        art = os.path.exists(os.path.join(RUNS, train, "adapter.gguf")) or os.path.exists(os.path.join(RUNS, train, "adapter", "adapter_model.safetensors"))
        ok = ok and art and os.path.exists(os.path.join(RUNS, train, "run.json"))
    return ok


def enqueue(run):
    seen = set()
    if os.path.exists(QUEUE):
        seen = {l.strip() for l in open(QUEUE) if l.strip()}
    if run not in seen:
        with open(QUEUE, "a") as f:
            f.write(run + "\n")
        log(f"queued for scoring: {run}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pods", required=True)
    ap.add_argument("--interval", type=int, default=600)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    pods = [l.split() for l in open(a.pods) if l.strip() and not l.startswith("#")]
    finished = set()
    while True:
        for host, port, name in pods:
            if name in finished:
                continue
            rc, out, err = ssh(host, port, f"python - <<'PY'\n{LIST_SCRIPT}\nPY")
            if rc != 0 or not out.strip():
                log(f"[{name}] unreachable ({err.strip()[:80]})")
                continue
            info = json.loads(out.strip().splitlines()[-1])
            pull(host, port, ["runs/cloud_state_*.json", "runs/cloud_pull_list.json"], overwrite=True)
            pending = [r for r in info["runs"] if not complete_locally(r["run"], r["train"])]
            for r in pending:
                if not r.get("ready", True):
                    continue   # still generating or training on the pod; pulled once final
                paths = [f"runs/{r['run']}"] + ([f"runs/{r['train']}"] if r["train"] else [])
                if pull(host, port, paths) and complete_locally(r["run"], r["train"]):
                    log(f"[{name}] pulled {r['run']}" + ("" if r.get("gate_ok", True) else " (GATE FAILED on the pod; kept, scored, flagged in cloud_state)"))
                    subprocess.run([sys.executable, "dr/backup_runs.py"], cwd=DR, capture_output=True)
                    enqueue(r["run"])
                else:
                    log(f"[{name}] pull failed for {r['run']}")
            if info["done"] and not pending:
                pull(host, port, ["runs/cloud_state_*.json", "logs/pod_*.log", "logs/cloud_*.log"])
                finished.add(name)
                log(f"[{name}] sweep complete and fully pulled")
        if a.once or len(finished) == len(pods):
            break
        time.sleep(a.interval)
    log("pull loop done" if len(finished) == len(pods) else "pull loop pass done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
