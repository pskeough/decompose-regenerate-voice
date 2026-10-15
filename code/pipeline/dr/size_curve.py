"""Data-size curve on one author: how many passages before an adapter helps?

For n in --sizes, train the pair recipe on a seeded, nested subset of n
TRAIN-fit targets (same epochs for every n, as a writer with n passages would
do), generate A0 and A1, score against the base run, judge vs_source only.
Each point is skipped when its scores exist. About 6 h for Wharton on the
5060 Ti; nothing else may touch the GPU while it runs.

    python dr/size_curve.py --author wharton --sizes 25,50,75,100,169 --epochs 6
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DR, LOGS, RUNS, credits_usd, log, read_json, write_text  # noqa: E402
from dr.overnight import gate_generation, gate_training  # noqa: E402

PY = sys.executable
GGUF_BASE = r"C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf"


def run(cmd, logname, background=False):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    logf = open(os.path.join(LOGS, logname), "a", encoding="utf-8")
    logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
    logf.flush()
    p = subprocess.Popen(cmd, cwd=DR, stdout=logf, stderr=subprocess.STDOUT, env=env)
    if background:
        return p
    if p.wait() != 0:
        raise RuntimeError(f"failed: {' '.join(cmd)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default="wharton")
    ap.add_argument("--base-run", default="base4b")
    ap.add_argument("--sizes", default="25,50,75,100,169")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--targets-seed", type=int, default=0)
    ap.add_argument("--arms", default="A0,A1")
    a = ap.parse_args()
    bal = credits_usd()
    log(f"balance {bal}; judges need ~USD 0.5 per point")
    snap = sorted(glob.glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--Qwen--Qwen3-4B", "snapshots", "*")))[0]
    rows = ["| n targets | steps | eval best | probe | A0 primary | A1 primary | coverage A0 |", "|---:|---:|---:|---:|---:|---:|---:|"]
    for n in [int(x) for x in a.sizes.split(",")]:
        tag = f"{a.author}_pair_n{n}_e{a.epochs}"
        run_id = f"{a.author}_size{n}"
        adir = os.path.join(RUNS, f"train_{tag}", "adapter")
        log(f"==== n = {n}")
        if not os.path.exists(os.path.join(adir, "adapter_config.json")):
            run([PY, "dr/s4_train.py", "--author", a.author, "--recipe", "pair", "--epochs", str(a.epochs), "--tag", tag,
                 "--n-targets", str(n), "--targets-seed", str(a.targets_seed)], "size_curve.log")
        gate_training(tag)
        gguf = os.path.join(RUNS, f"train_{tag}", "adapter.gguf")
        if not os.path.exists(gguf):
            run([PY, os.path.join(DR, "tools", "llama.cpp", "convert_lora_to_gguf.py"), "--base", snap, "--outfile", gguf, "--outtype", "f16", adir], "size_curve.log")
        man = os.path.join(RUNS, run_id, f"s3_manifest_{a.arms.replace(',', '_')}.json")
        if not os.path.exists(man):
            run([PY, "dr/llamacpp.py", "start", "--model", GGUF_BASE, "--lora", gguf], "size_curve.log")
            try:
                run([PY, "dr/s3_generate.py", "--author", a.author, "--run", run_id, "--arms", a.arms, "--backend", "llamacpp", "--adapter-gguf", gguf], "size_curve.log")
            finally:
                run([PY, "dr/llamacpp.py", "stop"], "size_curve.log")
        gate_generation(run_id, expect_probe=True)
        if not os.path.exists(os.path.join(RUNS, run_id, "scores.jsonl")):
            run([PY, "dr/s5_score.py", "--run", run_id, "--author", a.author, "--anchor-run", a.base_run], "size_curve.log")
        marker = os.path.join(RUNS, run_id, "judge.started")
        if not os.path.exists(marker):
            p = run([PY, "dr/s5b_judge.py", "--run", run_id, "--author", a.author], "size_curve.log", background=True)
            open(marker, "w").write(f"{p.pid}\n")
        r = read_json(os.path.join(RUNS, f"train_{tag}", "run.json"))
        s = read_json(os.path.join(RUNS, run_id, "scores_summary.json"))
        ev = [h["eval_loss"] for h in r["history"] if "eval_loss" in h]
        rows.append(f"| {n} | {r['steps']} | {min(ev):.3f} | {(r.get('probe') or {}).get('delta', float('nan')):.2f} | "
                    f"{s.get('A0', {}).get('luar_cos_source', float('nan')):.3f} | {s.get('A1', {}).get('luar_cos_source', float('nan')):.3f} | (judging) |")
        log(rows[-1])
    out = os.path.join(RUNS, f"size_curve_{a.author}.md")
    write_text(out, f"# Data-size curve, {a.author}, pair recipe, {a.epochs} epochs (base A0 for reference: see {a.base_run})\n\n" + "\n".join(rows) + "\n")
    log(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
