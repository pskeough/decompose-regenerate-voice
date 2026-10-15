"""One command per author: the whole pipeline with the gates on.

    python dr/run_author.py --authors chesterton,mansfield,chopin,sui_sin_far
    python dr/run_author.py --authors chesterton --recipe pair --epochs 6 --adapter-arms A0,A1,A5
    python dr/run_author.py --authors chesterton --dry

Per author, in order, each step skipped when its output exists:
    credits check (hard stop under --min-credits)
    s0 split -> s1 briefs test + train (+ recovery) -> s2 guide, quant, retrieval
    server(base) -> s3 base, six arms -> stop -> gate
    s3 frontier F0/F5 (API, background)
    s5 score base (normalised) -> gate -> judges (background)
    s4 train <recipe> <epochs> -> gate -> convert to GGUF
    server(--lora) -> probe -> s3 adapter arms -> stop -> gate
    s5 score adapter (anchor = base) -> gate -> judges (background)
    s6 analysis + review page

GPU steps are strictly serial (nothing else touches the card while a
training job runs); API steps run in the background. State per author in
runs/author_runs/<author>.json; a failed gate skips the dependent steps and
moves to the next author. Roughly 2 hours per author on the 5060 Ti.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import os
import subprocess
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import DR, LOGS, RUNS, author_dir, credits_usd, log, read_json, read_jsonl, write_json  # noqa: E402
from dr.overnight import gate_generation, gate_scoring, gate_training  # noqa: E402

PY = sys.executable
GGUF_BASE = r"C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf"
ARMS6 = "A0,A1,A2,A3,A4,A5"
STATE_DIR = os.path.join(RUNS, "author_runs")
os.makedirs(STATE_DIR, exist_ok=True)


def other_run_author():
    """PID of another live run_author, or None. A crashed Claude session does
    not kill its background chains: on 2026-09-05 the pre-crash chain kept
    going beside the resumed one, ran Mansfield's generation and a scoring
    pass on top of Chesterton's training, and step 1 took 80 minutes."""
    try:
        from dr.live import find_script
        hits = find_script("run_author.py")
    except Exception:
        return None
    return hits[0][0] if hits else None


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
        raise RuntimeError(f"exit {rc}: {' '.join(cmd)} (logs/{logname})")
    return rc


def server(model, lora=None, slots=8):
    run([PY, "dr/llamacpp.py", "start", "--model", model, "--slots", str(slots)] + (["--lora", lora] if lora else []), "author_server.log")


def server_stop():
    run([PY, "dr/llamacpp.py", "stop"], "author_server.log")


def judge_bg(run_id, author):
    marker = os.path.join(RUNS, run_id, "judge.started")
    if os.path.exists(marker):
        return
    p = run([PY, "dr/s5b_judge.py", "--run", run_id, "--author", author, "--only-samples", "0"], f"author_judge_{run_id}.log", background=True)
    open(marker, "w").write(f"{p.pid}\n")


class Author:
    def __init__(self, name, a):
        self.name, self.a = name, a
        self.d = author_dir(name)
        self.state_path = os.path.join(STATE_DIR, f"{name}.json" if a.model_tag == "4b" else f"{name}_{a.model_tag}.json")   # state per (author, base model)
        self.state = read_json(self.state_path) if os.path.exists(self.state_path) else {"steps": []}
        mt = a.model_tag
        self.base_run = f"{name}_base{mt}"
        self.tag = f"{name}_{a.recipe}_e{a.epochs}" + ("" if mt == "4b" else f"_{mt}")
        self.adapter_run = f"{name}_{a.recipe}e{a.epochs}_{mt}"
        self.frontier_run = f"{name}_base4b_frontier"   # frontier arms are model-independent; one set per author

    def note(self, **kw):
        kw["ts"] = dt.datetime.now().strftime("%m-%d %H:%M")
        self.state["steps"].append(kw)
        write_json(self.state_path, self.state)
        log(f"[{self.name}] {kw}")

    def step(self, name, fn):
        if any(s.get("name") == name and s.get("ok") for s in self.state["steps"]):
            log(f"[{self.name}] skip {name}")
            return True
        t0 = time.time()
        log(f"==== {self.name}: {name}")
        try:
            res = fn()
            ok = res is not False
            self.note(name=name, ok=ok, minutes=round((time.time() - t0) / 60, 1))
            return ok
        except Exception as e:
            self.note(name=name, ok=False, minutes=round((time.time() - t0) / 60, 1), error=repr(e)[:300],
                      tb=traceback.format_exc()[-800:])
            return False

    # ---- steps
    def prep(self):
        d, n = self.d, self.name
        if not os.path.exists(os.path.join(d, "split.json")):
            run([PY, "dr/s0_split.py", "--author", n], f"author_{n}.log")
        for split in ("test", "train"):
            if not os.path.exists(os.path.join(d, f"briefs_{split}.jsonl")):
                run([PY, "dr/s1_decompose.py", "--author", n, "--split", split, "--workers", "8"], f"author_{n}.log")
                run([PY, "dr/s1_decompose.py", "--author", n, "--split", split, "--workers", "8", "--recover", "2"], f"author_{n}.log")
        if not os.path.exists(os.path.join(d, "guide.md")):
            run([PY, "dr/s2_conditioning.py", "--author", n, "--guide", "--quant"], f"author_{n}.log")
        if not os.path.exists(os.path.join(d, "retrieval_test.jsonl")):
            run([PY, "dr/s2_conditioning.py", "--author", n, "--retrieval", "--briefs", "briefs_test.jsonl"], f"author_{n}.log")
        bt = [r for r in read_jsonl(os.path.join(d, "briefs_test.jsonl")) if r.get("passed")]
        btr = [r for r in read_jsonl(os.path.join(d, "briefs_train.jsonl")) if r.get("passed")]
        ok = len(bt) >= self.a.min_test_briefs and len(btr) >= self.a.min_train_briefs
        self.note(name="prep counts", ok=ok, test_briefs=len(bt), train_briefs=len(btr))
        return ok

    def base(self):
        arms = self.a.base_arms
        man = os.path.join(RUNS, self.base_run, f"s3_manifest_{arms.replace(',', '_')}.json")
        if not os.path.exists(man):
            server(self.a.gguf, slots=self.a.slots)
            try:
                run([PY, "dr/s3_generate.py", "--author", self.name, "--run", self.base_run, "--arms", arms, "--backend", "llamacpp", "--base", self.a.base, "--slots", str(self.a.slots)],
                    f"author_{self.name}.log")
            finally:
                server_stop()
        if not gate_generation(self.base_run):
            return False
        if not os.path.exists(os.path.join(RUNS, self.frontier_run, "gens.jsonl")):
            run([PY, "dr/s3_generate.py", "--author", self.name, "--run", self.frontier_run, "--arms", "F0,F5"],
                f"author_{self.name}_frontier.log", background=True)
        if not os.path.exists(os.path.join(RUNS, self.base_run, "scores.jsonl")):
            run([PY, "dr/s5_score.py", "--run", self.base_run, "--author", self.name], f"author_{self.name}.log")
        ok = gate_scoring(self.base_run)
        judge_bg(self.base_run, self.name)
        return ok

    def adapter(self):
        a, n = self.a, self.name
        adir = os.path.join(RUNS, f"train_{self.tag}", "adapter")
        if not os.path.exists(os.path.join(adir, "adapter_config.json")):
            run([PY, "dr/s4_train.py", "--author", n, "--recipe", a.recipe, "--epochs", str(a.epochs), "--tag", self.tag, "--base", a.base, "--bs", str(a.bs), "--accum", str(a.accum)],
                f"author_{n}_train.log")
        if not gate_training(self.tag):
            return False
        gguf = os.path.join(RUNS, f"train_{self.tag}", "adapter.gguf")
        if not os.path.exists(gguf):
            snap = sorted(glob.glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--" + a.base.replace("/", "--"), "snapshots", "*")))[0]
            run([PY, os.path.join(DR, "tools", "llama.cpp", "convert_lora_to_gguf.py"), "--base", snap, "--outfile", gguf, "--outtype", "f16", adir],
                f"author_{n}_train.log")
        man = os.path.join(RUNS, self.adapter_run, f"s3_manifest_{a.adapter_arms.replace(',', '_')}.json")
        if not os.path.exists(man):
            server(self.a.gguf, gguf, slots=self.a.slots)
            try:
                run([PY, "dr/s3_generate.py", "--author", n, "--run", self.adapter_run, "--arms", a.adapter_arms, "--backend", "llamacpp",
                     "--adapter-gguf", gguf, "--base", a.base, "--slots", str(a.slots)], f"author_{n}.log")
            finally:
                server_stop()
        if not gate_generation(self.adapter_run, expect_probe=True):
            return False
        if not os.path.exists(os.path.join(RUNS, self.adapter_run, "scores.jsonl")):
            run([PY, "dr/s5_score.py", "--run", self.adapter_run, "--author", n, "--anchor-run", self.base_run], f"author_{n}.log")
        ok = gate_scoring(self.adapter_run)
        judge_bg(self.adapter_run, n)
        return ok

    def analysis(self):
        runs = [r for r in (self.base_run, self.frontier_run, self.adapter_run)
                if os.path.exists(os.path.join(RUNS, r, "gens.jsonl"))]
        fr = self.frontier_run
        if fr in runs and not os.path.exists(os.path.join(RUNS, fr, "scores.jsonl")):
            run([PY, "dr/s5_score.py", "--run", fr, "--author", self.name, "--anchor-run", self.base_run], f"author_{self.name}.log")
        runs = [r for r in runs if os.path.exists(os.path.join(RUNS, r, "scores.jsonl"))]
        run([PY, "dr/s6_analysis.py", "--runs", ",".join(runs), "--out", os.path.join(RUNS, "author_runs", self.name)], f"author_{self.name}.log")
        run([PY, "dr/review_page.py", "--author", self.name, "--runs", ",".join(runs), "--n", "3",
             "--out", os.path.join(RUNS, f"review_{self.name}.html")], f"author_{self.name}.log")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--authors", required=True, help="comma-separated corpus slugs")
    ap.add_argument("--recipe", default="pair", choices=config.RECIPES)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--adapter-arms", default="A0,A1,A5")
    ap.add_argument("--base-arms", default=ARMS6, help="private authors drop A1 (the name means nothing to the model): A0,A2,A3,A4,A5")
    ap.add_argument("--min-credits", type=float, default=6.0, help="USD; hard stop below this before starting")
    ap.add_argument("--min-test-briefs", type=int, default=30)
    ap.add_argument("--min-train-briefs", type=int, default=60, help="lower it for a deliberate thin-data author")
    ap.add_argument("--base", default=config.BASE_MODEL, help="HF id of the base model (tokenizer, training, probe)")
    ap.add_argument("--gguf", default=GGUF_BASE, help="F16 GGUF of the same base for the llama.cpp server")
    ap.add_argument("--model-tag", default="4b", help="run-id suffix for the base model: 4b (default), 17b, 8b ...")
    ap.add_argument("--slots", type=int, default=0, help="server slots and client concurrency; 0 = 8 for 4b, 24 for smaller models (a 1.7B at 8 slots left the card half idle, 2026-09-07)")
    ap.add_argument("--bs", type=int, default=config.LORA["bs"], help="training micro-batch (recipe default 1 x accum 8)")
    ap.add_argument("--accum", type=int, default=config.LORA["accum"])
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true", help="start even if another run_author is alive")
    a = ap.parse_args()
    if not a.slots:
        a.slots = 8 if a.model_tag == "4b" else 24
    other = other_run_author()
    if other and not a.force and not a.dry:
        raise SystemExit(f"another run_author is alive (pid {other}); python dr/stop_all.py first, or --force")
    authors = [x.strip() for x in a.authors.split(",") if x.strip()]
    bal = credits_usd()
    log(f"OpenRouter balance: {bal if bal is None else f'USD {bal:.2f}'}; need ~USD 2.5 per author, floor {a.min_credits}")
    if bal is not None and bal < a.min_credits:
        raise SystemExit("balance below floor; top up first")
    if bal is None:
        log("WARNING could not read the balance; continuing on the software cap only")
    log(f"authors {authors}; recipe {a.recipe} x {a.epochs} epochs; adapter arms {a.adapter_arms}; ~2 h each")
    if a.dry:
        return 0
    summary = {}
    for name in authors:
        A = Author(name, a)
        ok = A.step("prep", A.prep)
        ok = ok and A.step("base run", A.base)
        ok = ok and A.step("adapter", A.adapter)
        A.step("analysis", A.analysis)
        summ = {}
        for run_id in (A.base_run, A.adapter_run):
            p = os.path.join(RUNS, run_id, "scores_summary.json")
            if os.path.exists(p):
                s = read_json(p)
                summ[run_id] = {k: round(v["luar_cos_source"], 3) for k, v in s.items() if k.startswith("A") and v.get("luar_cos_source") is not None}
        summary[name] = summ
        log(f"[{name}] {summ}")
    write_json(os.path.join(STATE_DIR, "summary.json"), summary)
    run([PY, "dr/backup_runs.py"], "backup.log")
    log("all authors done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
