"""Patrick's own corpus, run tonight ahead of the remaining overnight steps.

Waits for the overnight controller's S3 (6-epoch pair) to finish, stops the
controller, runs the full pipeline on `patrick` (no A1 arm: the model has
never seen him, so the name carries nothing), then relaunches the controller,
which resumes at the first step it has not completed.

    base   A0, A2, A3, A4, A5      frontier F0, F5
    train  pair, mix               adapters x the same five arms
    score  anchor = patrick_base4b; judges; analysis; review page

    python dr/patrick_night.py
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import subprocess
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DR, LOGS, RUNS, author_dir, log, read_json, read_jsonl, write_json, write_text  # noqa: E402

PY = sys.executable
GGUF_BASE = r"C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf"
ARMS = "A0,A2,A3,A4,A5"
AUTHOR = "patrick"
OUT = os.path.join(RUNS, "overnight")
STATE = os.path.join(OUT, "patrick_state.json")
state = read_json(STATE) if os.path.exists(STATE) else {"steps": []}


def note(**kw):
    kw["ts"] = dt.datetime.now().strftime("%H:%M")
    state["steps"].append(kw)
    write_json(STATE, state)
    log(f"[patrick] {kw}")


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


def server(model, lora=None):
    cmd = [PY, "dr/llamacpp.py", "start", "--model", model] + (["--lora", lora] if lora else [])
    run(cmd, "patrick_server.log")


def server_stop():
    run([PY, "dr/llamacpp.py", "stop"], "patrick_server.log")


def stop_overnight():
    ps = subprocess.run(["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'overnight\\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $_.ProcessId }"],
                        capture_output=True, text=True)
    log(f"stopped overnight.py pids: {ps.stdout.strip() or 'none'}")
    subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"], capture_output=True)


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


def judge_bg(run_id):
    marker = os.path.join(RUNS, run_id, "judge.started")
    if os.path.exists(marker):
        return
    p = run([PY, "dr/s5b_judge.py", "--run", run_id, "--author", AUTHOR], f"patrick_judge_{run_id}.log", background=True)
    open(marker, "w").write(f"{p.pid}\n")


def adapter(recipe):
    tag = f"{AUTHOR}_{recipe}_r16_s0"
    adir = os.path.join(RUNS, f"train_{tag}", "adapter")
    if not os.path.exists(os.path.join(adir, "adapter_config.json")):
        run([PY, "dr/s4_train.py", "--author", AUTHOR, "--recipe", recipe, "--tag", tag], f"patrick_train_{recipe}.log")
    r = read_json(os.path.join(RUNS, f"train_{tag}", "run.json"))
    ev = [h["eval_loss"] for h in r["history"] if "eval_loss" in h]
    delta = (r.get("probe") or {}).get("delta")
    note(name=f"train {recipe} curve", ok=bool(ev) and min(ev) < ev[0], eval_first=ev[0] if ev else None,
         eval_best=min(ev) if ev else None, probe_delta=delta, steps=r["steps"])
    gguf = os.path.join(RUNS, f"train_{tag}", "adapter.gguf")
    if not os.path.exists(gguf):
        snap = sorted(glob.glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--Qwen--Qwen3-4B", "snapshots", "*")))[0]
        run([PY, os.path.join(DR, "tools", "llama.cpp", "convert_lora_to_gguf.py"), "--base", snap, "--outfile", gguf, "--outtype", "f16", adir],
            "patrick_convert.log")
    run_id = f"patrick_{recipe}4b"
    man = os.path.join(RUNS, run_id, f"s3_manifest_{ARMS.replace(',', '_')}.json")
    if not os.path.exists(man):
        server(GGUF_BASE, gguf)
        try:
            run([PY, "dr/s3_generate.py", "--author", AUTHOR, "--run", run_id, "--arms", ARMS, "--backend", "llamacpp",
                 "--adapter-gguf", gguf], f"patrick_gen_{recipe}.log")
        finally:
            server_stop()
    if not os.path.exists(os.path.join(RUNS, run_id, "scores.jsonl")):
        run([PY, "dr/s5_score.py", "--run", run_id, "--author", AUTHOR, "--anchor-run", "patrick_base4b"], f"patrick_score_{recipe}.log")
    judge_bg(run_id)


def main():
    d = author_dir(AUTHOR)
    # prerequisites built outside: briefs, guide, quant, retrieval
    for f in ("briefs_test.jsonl", "briefs_train.jsonl", "guide.md", "quant_block.txt", "retrieval_test.jsonl"):
        while not os.path.exists(os.path.join(d, f)):
            log(f"waiting for data/{AUTHOR}/{f}")
            time.sleep(30)
    # wait for overnight S3 to land, then take the GPU
    while not os.path.exists(os.path.join(RUNS, "pair_e6_4b", "scores.jsonl")):
        time.sleep(30)
    step("stop overnight", stop_overnight)

    def base():
        man = os.path.join(RUNS, "patrick_base4b", f"s3_manifest_{ARMS.replace(',', '_')}.json")
        if not os.path.exists(man):
            server(GGUF_BASE)
            try:
                run([PY, "dr/s3_generate.py", "--author", AUTHOR, "--run", "patrick_base4b", "--arms", ARMS, "--backend", "llamacpp"],
                    "patrick_gen_base.log")
            finally:
                server_stop()
        run([PY, "dr/s3_generate.py", "--author", AUTHOR, "--run", "patrick_base4b_frontier", "--arms", "F0,F5"],
            "patrick_gen_frontier.log", background=True)
        if not os.path.exists(os.path.join(RUNS, "patrick_base4b", "scores.jsonl")):
            run([PY, "dr/s5_score.py", "--run", "patrick_base4b", "--author", AUTHOR], "patrick_score_base.log")
        judge_bg("patrick_base4b")
    step("base", base)
    step("adapter pair", lambda: adapter("pair"))
    step("adapter mix", lambda: adapter("mix"))

    def analysis():
        fr = os.path.join(RUNS, "patrick_base4b_frontier")
        if os.path.exists(os.path.join(fr, "gens.jsonl")) and not os.path.exists(os.path.join(fr, "scores.jsonl")):
            run([PY, "dr/s5_score.py", "--run", "patrick_base4b_frontier", "--author", AUTHOR, "--anchor-run", "patrick_base4b"],
                "patrick_score_frontier.log")
        runs = [r for r in ("patrick_base4b", "patrick_base4b_frontier", "patrick_pair4b", "patrick_mix4b")
                if os.path.exists(os.path.join(RUNS, r, "scores.jsonl"))]
        run([PY, "dr/s6_analysis.py", "--runs", ",".join(runs), "--out", os.path.join(OUT, "patrick")], "patrick_analysis.log")
        run([PY, "dr/review_page.py", "--author", AUTHOR, "--runs", ",".join(runs), "--n", "3",
             "--out", os.path.join(RUNS, "review_patrick.html")], "patrick_analysis.log")
    step("analysis", analysis)

    # hand the GPU back to the overnight controller, which resumes where it stopped
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    logf = open(os.path.join(LOGS, "overnight.log"), "a", encoding="utf-8")
    subprocess.Popen([PY, "dr/overnight.py"], cwd=DR, stdout=logf, stderr=subprocess.STDOUT, env=env)
    note(name="relaunch overnight", ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
