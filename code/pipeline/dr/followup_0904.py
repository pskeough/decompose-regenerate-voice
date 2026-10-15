"""Follow-ups queued 2026-09-04 behind Patrick's corpus run.

    F1  Patrick, pair adapter on stories only (--exclude-gids 1,2,3): the
        register test for the flat result on the novel-heavy adapter. Same
        five arms, scored against patrick_base4b, judged.
    F2  Detectors in NF4 (4B observer/performer pair, both 4-bit so they fit
        beside each other) on base4b, pair_e6_4b, patrick_base4b, patrick_pair4b.
    F3  Analysis and pages for Patrick with every run; DECISIONS gets the
        numbers by hand afterwards.

Waits for patrick_night.py's analysis output before touching the GPU.

    python dr/followup_0904.py
"""
from __future__ import annotations

import datetime as dt
import glob
import os
import subprocess
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DR, LOGS, RUNS, log, read_json, write_json  # noqa: E402

PY = sys.executable
GGUF_BASE = r"C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf"
ARMS = "A0,A2,A3,A4,A5"
OUT = os.path.join(RUNS, "overnight")
STATE = os.path.join(OUT, "followup_0904_state.json")
state = read_json(STATE) if os.path.exists(STATE) else {"steps": []}


def note(**kw):
    kw["ts"] = dt.datetime.now().strftime("%H:%M")
    state["steps"].append(kw)
    write_json(STATE, state)
    log(f"[followup] {kw}")


def run(cmd, logname, background=False):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    logf = open(os.path.join(LOGS, logname), "a", encoding="utf-8")
    logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
    logf.flush()
    log(f"$ {' '.join(cmd)}  -> logs/{logname}")
    p = subprocess.Popen(cmd, cwd=DR, stdout=logf, stderr=subprocess.STDOUT, env=env)
    if background:
        return p
    rc = p.wait()
    if rc != 0:
        raise RuntimeError(f"exit {rc}: {' '.join(cmd)}")
    return rc


def step(name, fn):
    if any(s.get("name") == name and s.get("ok") for s in state["steps"]):
        log(f"skip {name}")
        return True
    t0 = time.time()
    log(f"==== {name}")
    try:
        fn()
        note(name=name, ok=True, minutes=round((time.time() - t0) / 60, 1))
        return True
    except Exception as e:
        note(name=name, ok=False, minutes=round((time.time() - t0) / 60, 1), error=repr(e)[:300],
             tb=traceback.format_exc()[-1000:])
        return False


def f1():
    tag = "patrick_pair_stories"
    adir = os.path.join(RUNS, f"train_{tag}", "adapter")
    if not os.path.exists(os.path.join(adir, "adapter_config.json")):
        run([PY, "dr/s4_train.py", "--author", "patrick", "--recipe", "pair", "--tag", tag, "--exclude-gids", "1,2,3"],
            "followup_train_stories.log")
    r = read_json(os.path.join(RUNS, f"train_{tag}", "run.json"))
    ev = [h["eval_loss"] for h in r["history"] if "eval_loss" in h]
    note(name="train stories curve", ok=bool(ev) and min(ev) < ev[0], eval_first=ev[0] if ev else None,
         eval_best=min(ev) if ev else None, probe_delta=(r.get("probe") or {}).get("delta"), steps=r["steps"],
         n_targets=r["n_targets"])
    gguf = os.path.join(RUNS, f"train_{tag}", "adapter.gguf")
    if not os.path.exists(gguf):
        snap = sorted(glob.glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--Qwen--Qwen3-4B", "snapshots", "*")))[0]
        run([PY, os.path.join(DR, "tools", "llama.cpp", "convert_lora_to_gguf.py"), "--base", snap, "--outfile", gguf, "--outtype", "f16", adir],
            "followup_convert.log")
    run_id = "patrick_stories4b"
    man = os.path.join(RUNS, run_id, f"s3_manifest_{ARMS.replace(',', '_')}.json")
    if not os.path.exists(man):
        run([PY, "dr/llamacpp.py", "start", "--model", GGUF_BASE, "--lora", gguf], "followup_server.log")
        try:
            run([PY, "dr/s3_generate.py", "--author", "patrick", "--run", run_id, "--arms", ARMS, "--backend", "llamacpp",
                 "--adapter-gguf", gguf], "followup_gen_stories.log")
        finally:
            run([PY, "dr/llamacpp.py", "stop"], "followup_server.log")
    if not os.path.exists(os.path.join(RUNS, run_id, "scores.jsonl")):
        run([PY, "dr/s5_score.py", "--run", run_id, "--author", "patrick", "--anchor-run", "patrick_base4b"], "followup_score_stories.log")
    marker = os.path.join(RUNS, run_id, "judge.started")
    if not os.path.exists(marker):
        p = run([PY, "dr/s5b_judge.py", "--run", run_id, "--author", "patrick"], "followup_judge_stories.log", background=True)
        open(marker, "w").write(f"{p.pid}\n")


def f2():
    for run_id, author, anchor in (("base4b", "wharton", "base4b"), ("pair_e6_4b", "wharton", "base4b"),
                                   ("patrick_base4b", "patrick", "patrick_base4b"), ("patrick_pair4b", "patrick", "patrick_base4b")):
        run([PY, "dr/s5_score.py", "--run", run_id, "--author", author, "--anchor-run", anchor, "--detect",
             "--observer", "Qwen/Qwen3.5-4B-Base", "--performer", "Qwen/Qwen3.5-4B", "--obs-4bit", "--perf-4bit"],
            f"followup_detect_{run_id}.log")


def f3():
    runs = [r for r in ("patrick_base4b", "patrick_base4b_frontier", "patrick_pair4b", "patrick_mix4b", "patrick_stories4b")
            if os.path.exists(os.path.join(RUNS, r, "scores.jsonl"))]
    fr = os.path.join(RUNS, "patrick_base4b_frontier")
    if os.path.exists(os.path.join(fr, "gens.jsonl")) and not os.path.exists(os.path.join(fr, "scores.jsonl")):
        run([PY, "dr/s5_score.py", "--run", "patrick_base4b_frontier", "--author", "patrick", "--anchor-run", "patrick_base4b"],
            "followup_score_frontier.log")
        runs.append("patrick_base4b_frontier")
    run([PY, "dr/s6_analysis.py", "--runs", ",".join(runs), "--out", os.path.join(OUT, "patrick")], "followup_analysis.log")
    run([PY, "dr/review_page.py", "--author", "patrick", "--runs", ",".join(runs), "--n", "3",
         "--out", os.path.join(RUNS, "review_patrick.html")], "followup_analysis.log")


def main():
    target = os.path.join(RUNS, "overnight", "patrick", "RESULTS.md")
    while not os.path.exists(target):
        time.sleep(30)
    # patrick_night relaunches overnight.py at its end; that re-run only rebuilds
    # reports, but give it a minute so the two do not fight over the review pages
    time.sleep(90)
    step("F1 patrick stories-only adapter", f1)
    step("F2 detectors NF4", f2)
    step("F3 patrick analysis + page", f3)
    log("followup complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
