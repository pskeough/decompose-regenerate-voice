"""Overnight chain: base run -> adapters -> adapter runs -> scoring -> analysis.

Every step is skipped when its output already exists, so the chain can be
re-run after an interruption and continues from where it stopped. Steps that
need the GPU alone (training) stop the llama.cpp server first; steps that only
need the API (judges, frontier arms) run concurrently with GPU steps.

    python dr/chain.py --author wharton            # full chain
    python dr/chain.py --author wharton --until train   # stop after the adapters
    python dr/chain.py --author wharton --dry      # print the plan only
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import DR, LOGS, RUNS, author_dir, log  # noqa: E402

PY = sys.executable
GGUF_BASE = r"C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf"
HF_SNAPSHOT = glob.glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub",
                                     "models--Qwen--Qwen3-4B", "snapshots", "*"))
CONVERT_LORA = os.path.join(DR, "tools", "llama.cpp", "convert_lora_to_gguf.py")
ARMS = "A0,A1,A2,A3,A4,A5"


def run(cmd, logname, cwd=DR, env_extra=None, background=False):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", **(env_extra or {}))
    logf = open(os.path.join(LOGS, logname), "a", encoding="utf-8")
    logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
    logf.flush()
    log(f"$ {' '.join(cmd)}  -> logs/{logname}")
    p = subprocess.Popen(cmd, cwd=cwd, stdout=logf, stderr=subprocess.STDOUT, env=env)
    if background:
        return p
    rc = p.wait()
    if rc != 0:
        raise SystemExit(f"step failed ({rc}): {' '.join(cmd)}; see logs/{logname}")
    return rc


def judge_once(run_id, author, logname):
    """Launch the judges for a run in the background unless a marker says a
    judge process was already started for it (the chain is re-run after
    failures and must not double-judge)."""
    marker = os.path.join(RUNS, run_id, "judge.started")
    if os.path.exists(marker) or os.path.exists(os.path.join(RUNS, run_id, "judge_summary.json")):
        log(f"judges already started for {run_id}; skipping")
        return None
    p = run([PY, "dr/s5b_judge.py", "--run", run_id, "--author", author], logname, background=True)
    with open(marker, "w") as f:
        f.write(f"{p.pid} {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    return p


def wait_for(path, every=15, what=""):
    if not os.path.exists(path):
        log(f"waiting for {what or path}")
    while not os.path.exists(path):
        time.sleep(every)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--base-run", default="base4b")
    ap.add_argument("--recipes", default=",".join(config.RECIPES))
    ap.add_argument("--until", choices=["base", "train", "adapters", "score", "all"], default="all")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--no-judge", action="store_true")
    a = ap.parse_args()
    d = author_dir(a.author)
    recipes = [r for r in a.recipes.split(",") if r]
    base_dir = os.path.join(RUNS, a.base_run)
    base_manifest = os.path.join(base_dir, f"s3_manifest_{ARMS.replace(',', '_')}.json")
    steps = []

    # ---- 1. base run complete (started outside the chain), then top-up for recovered briefs
    steps.append(("wait base run", lambda: wait_for(base_manifest, what="base run manifest")))
    steps.append(("base top-up (recovered briefs)", lambda: run(
        [PY, "dr/s3_generate.py", "--author", a.author, "--run", a.base_run, "--arms", ARMS,
         "--backend", "llamacpp"], "chain_base_topup.log")))
    if not a.no_judge:
        steps.append(("judges on base (background, API)", lambda: judge_once(a.base_run, a.author, "chain_judge_base.log")))
        steps.append(("judges on frontier (background, API)", lambda: judge_once(a.base_run + "_frontier", a.author, "chain_judge_frontier.log")))
    if a.until == "base":
        steps.append(("stop", lambda: None))

    # ---- 2. server down, score base (embeddings need the GPU), train adapters
    steps.append(("stop server", lambda: run([PY, "dr/llamacpp.py", "stop"], "chain_server.log")))
    steps.append(("score base", lambda: os.path.exists(os.path.join(base_dir, "scores.jsonl")) or run(
        [PY, "dr/s5_score.py", "--run", a.base_run, "--author", a.author], "chain_score_base.log")))
    steps.append(("wait train briefs", lambda: wait_for(os.path.join(d, "briefs_train.jsonl"), what="train briefs")))
    steps.append(("recover train briefs", lambda: run(
        [PY, "dr/s1_decompose.py", "--author", a.author, "--split", "train", "--recover", "2"],
        "chain_s1_train_recover.log")))
    for rc in recipes:
        tag = f"{a.author}_{rc}_r{config.LORA['r']}_s{config.LORA['seed']}"
        adir = os.path.join(RUNS, f"train_{tag}", "adapter")
        steps.append((f"train {rc}", lambda rc=rc, adir=adir: os.path.exists(os.path.join(adir, "adapter_config.json")) or run(
            [PY, "dr/s4_train.py", "--author", a.author, "--recipe", rc], f"chain_train_{rc}.log")))
        gg = os.path.join(RUNS, f"train_{tag}", "adapter.gguf")
        steps.append((f"convert {rc} to gguf", lambda adir=adir, gg=gg: os.path.exists(gg) or run(
            [PY, CONVERT_LORA, "--base", HF_SNAPSHOT[0], "--outfile", gg, "--outtype", "f16", adir],
            "chain_convert.log")))
    if a.until == "train":
        steps.append(("stop", lambda: None))

    # ---- 3. adapter x arms runs, one server per adapter
    for rc in recipes:
        tag = f"{a.author}_{rc}_r{config.LORA['r']}_s{config.LORA['seed']}"
        gg = os.path.join(RUNS, f"train_{tag}", "adapter.gguf")
        run_id = f"{rc}4b"
        man = os.path.join(RUNS, run_id, f"s3_manifest_{ARMS.replace(',', '_')}.json")

        def adapter_run(rc=rc, gg=gg, run_id=run_id, man=man):
            if os.path.exists(man):
                return
            run([PY, "dr/llamacpp.py", "start", "--model", GGUF_BASE, "--lora", gg], "chain_server.log")
            try:
                run([PY, "dr/s3_generate.py", "--author", a.author, "--run", run_id, "--arms", ARMS,
                     "--backend", "llamacpp", "--adapter-gguf", gg], f"chain_gen_{rc}.log")
            finally:
                run([PY, "dr/llamacpp.py", "stop"], "chain_server.log")
            if not a.no_judge:
                judge_once(run_id, a.author, f"chain_judge_{rc}.log")
        steps.append((f"generate with {rc} adapter", adapter_run))
    if a.until == "adapters":
        steps.append(("stop", lambda: None))

    # ---- 4. scoring and analysis
    for rc in recipes:
        run_id = f"{rc}4b"
        steps.append((f"score {rc}", lambda run_id=run_id: os.path.exists(os.path.join(RUNS, run_id, "scores.jsonl")) or run(
            [PY, "dr/s5_score.py", "--run", run_id, "--author", a.author, "--anchor-run", a.base_run],
            f"chain_score_{run_id}.log")))
    steps.append(("score frontier", lambda: os.path.exists(os.path.join(RUNS, a.base_run + "_frontier", "scores.jsonl")) or run(
        [PY, "dr/s5_score.py", "--run", a.base_run + "_frontier", "--author", a.author, "--anchor-run", a.base_run],
        "chain_score_frontier.log")))
    steps.append(("analysis base", lambda: run(
        [PY, "dr/s6_analysis.py", "--runs", f"{a.base_run},{a.base_run}_frontier"], "chain_analysis.log")))
    steps.append(("analysis base + adapters", lambda: run(
        [PY, "dr/s6_analysis.py", "--runs", ",".join([a.base_run] + [f"{rc}4b" for rc in recipes]),
         "--out", os.path.join(RUNS, "adapter_phase")], "chain_analysis.log")))

    log(f"chain: {len(steps)} steps")
    for i, (name, _) in enumerate(steps, 1):
        log(f"  {i:2d}. {name}")
    if a.dry:
        return 0
    for i, (name, fn) in enumerate(steps, 1):
        if name == "stop":
            log("stopping at --until")
            return 0
        t0 = time.time()
        log(f"[{i}/{len(steps)}] {name}")
        fn()
        log(f"[{i}/{len(steps)}] {name} done in {(time.time()-t0)/60:.1f} min")
    log("chain complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
