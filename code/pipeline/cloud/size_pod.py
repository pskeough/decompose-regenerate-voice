"""Within-author corpus-size series on a pod (2026-09-10).

For each size token in --sizes ("25", "50", "50s1" = 50 targets with targets-seed 1), train the
pair recipe on a seeded, nested subset of n TRAIN-fit targets for --epochs epochs (the same
recipe as dr/size_curve.py, which made the Chesterton series locally on 2026-09-06), convert the
LoRA to GGUF, and generate --arms with the adapter. No scoring and no judging on the pod: the
runs are pulled by cloud/pull_size.py and scored locally against the author's existing 4B base
run, so every point sits on the same anchor as the local series.

Run names: train_{author}_pair_n{n}_e{epochs}[_s{seed}] and {author}_size{n}[_s{seed}].
A point is skipped when its artefacts exist, so the script is resumable.

    python cloud/size_pod.py --author doctorow --sizes 25,50,100,150,215,300,525,50s1 --arms A0,A1 \
        --base Qwen/Qwen3-4B --gguf /workspace/models/Qwen3-4B-F16.gguf --slots 32
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
import traceback

DR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DR)
from dr.core import RUNS, log, read_json, write_json  # noqa: E402
from cloud.cloud_run import PY, gate_generation, gate_training, run, snapshot  # noqa: E402


def parse_token(tok):
    m = re.fullmatch(r"(\d+)(?:s(\d+))?", tok.strip())
    if not m:
        raise SystemExit(f"bad size token {tok!r}; use n or n s<seed> like 50s1")
    return int(m.group(1)), int(m.group(2) or 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", required=True)
    ap.add_argument("--sizes", required=True)
    ap.add_argument("--arms", default="A0,A1")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--base", default="Qwen/Qwen3-4B")
    ap.add_argument("--gguf", default="/workspace/models/Qwen3-4B-F16.gguf")
    ap.add_argument("--slots", type=int, default=32)
    ap.add_argument("--port", type=int, default=8089)
    a = ap.parse_args()
    url = f"http://127.0.0.1:{a.port}"
    tools = os.environ.get("DR_LLAMA_TOOLS", os.path.join(DR, "tools", "llama.cpp"))
    logname = f"size_{a.author}.log"
    results = []
    for tok in a.sizes.split(","):
        n, seed = parse_token(tok)
        suffix = f"_s{seed}" if seed else ""
        tag = f"{a.author}_pair_n{n}_e{a.epochs}{suffix}"
        run_id = f"{a.author}_size{n}{suffix}"
        tdir = os.path.join(RUNS, f"train_{tag}")
        adir = os.path.join(tdir, "adapter")
        gguf = os.path.join(tdir, "adapter.gguf")
        rdir = os.path.join(RUNS, run_id)
        os.makedirs(rdir, exist_ok=True)
        state_path = os.path.join(rdir, "size_point.json")
        state = read_json(state_path) if os.path.exists(state_path) else {}
        state.update({"author": a.author, "n_targets": n, "targets_seed": seed, "train_tag": tag, "run": run_id,
                      "arms": a.arms, "epochs": a.epochs, "base": a.base, "platform": "runpod"})
        t0 = time.time()
        log(f"==== {a.author}: n={n} seed={seed} ({tag} -> {run_id})")
        try:
            if not os.path.exists(os.path.join(adir, "adapter_config.json")):
                run([PY, "dr/s4_train.py", "--author", a.author, "--recipe", "pair", "--epochs", str(a.epochs), "--tag", tag,
                     "--n-targets", str(n), "--targets-seed", str(seed), "--base", a.base], logname)
            ok, checks = gate_training(tag)
            state["gate_training"] = {"ok": bool(ok), **checks}
            write_json(state_path, state)
            if not os.path.exists(gguf):
                run([PY, os.path.join(tools, "convert_lora_to_gguf.py"), "--base", snapshot(a.base), "--outfile", gguf, "--outtype", "f16", adir], logname)
                open(gguf + ".done", "w").write(str(os.path.getsize(gguf)))
            man = os.path.join(rdir, f"s3_manifest_{a.arms.replace(',', '_')}.json")
            if not os.path.exists(man):
                run([PY, "dr/llamacpp.py", "start", "--model", a.gguf, "--slots", str(a.slots), "--url", url, "--lora", gguf], logname)
                try:
                    run([PY, "dr/s3_generate.py", "--author", a.author, "--run", run_id, "--arms", a.arms, "--backend", "llamacpp",
                         "--adapter-gguf", gguf, "--base", a.base, "--slots", str(a.slots), "--server", url], logname)
                finally:
                    run([PY, "dr/llamacpp.py", "stop", "--url", url], logname)
            ok, checks = gate_generation(run_id, expect_probe=True)
            state["gate_generation"] = {"ok": bool(ok), **checks}
            state["done"] = True
        except Exception as e:  # keep going: the next point is independent
            state["error"] = repr(e)[:300]
            state["traceback"] = traceback.format_exc()[-1200:]
            state["done"] = False
            log(f"[size] {run_id} FAILED: {e!r}")
        state["minutes"] = round((time.time() - t0) / 60, 1)
        write_json(state_path, state)
        results.append((run_id, state.get("done"), state["minutes"]))
        log(f"[size] point {run_id} done={state.get('done')} in {state['minutes']} min")
    log("size series summary: " + "; ".join(f"{r} done={d} {m}min" for r, d, m in results))
    return 0 if all(d for _, d, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
