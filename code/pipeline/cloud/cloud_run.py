"""GPU stages of the author pipeline on a cloud box: base arms, LoRA training,
GGUF conversion, adapter arms. Scoring and judging stay local (dr/score_runs.py
after cloud/sync_down.sh). The stage commands are the ones run_author.py
issues locally, argument for argument, so a cloud run and a local run differ
only in hardware, and dr/provenance.py stamps that into every manifest.

    cd /workspace/decompose_regenerate
    DR_CLOUD=1 DR_LLAMA_SERVER=/workspace/llama.cpp/build/bin/llama-server \\
    python cloud/cloud_run.py --authors chesterton,mansfield --base Qwen/Qwen3-8B \\
        --gguf /workspace/models/Qwen3-8B-F16.gguf --model-tag 8b --slots 16

    --bridge         also run the 4B on the first author (needs its GGUF) so the
                     local 4B result is replicated on the cloud card
    --lane train|generate   two processes on one 48 GB card: the train lane
                     trains every adapter in order; the generate lane does all
                     base arms, then adapter arms as adapters appear. Both set
                     DR_ALLOW_SHARED_GPU=1 so s4_train leaves the server alone.
    --private A,B    authors whose arms drop A1 (the name means nothing to the model)

State per (author, tag) in runs/cloud_state_<author>_<tag>.json; every step
skips when its product exists, so a preempted pod resumes with the same command.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import statistics as st
import subprocess
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
DR = os.path.dirname(HERE)
sys.path.insert(0, DR)
from dr.core import LOGS, RUNS, log, read_json, read_jsonl, write_json  # noqa: E402

PY = sys.executable
ARMS6 = "A0,A1,A2,A3,A4,A5"
ARMS5 = "A0,A2,A3,A4,A5"


def run(cmd, logname):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", DR_CLOUD="1")
    with open(os.path.join(LOGS, logname), "a", encoding="utf-8") as logf:
        logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
        logf.flush()
        log(f"$ {' '.join(cmd)}  -> logs/{logname}")
        p = subprocess.Popen(cmd, cwd=DR, stdout=logf, stderr=subprocess.STDOUT, env=env)
        rc = p.wait()
    if rc != 0:
        raise RuntimeError(f"exit {rc}: {' '.join(cmd)} (logs/{logname})")


def snapshot(base):
    pat = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--" + base.replace("/", "--"), "snapshots", "*")
    snaps = sorted(glob.glob(pat))
    if not snaps:
        raise SystemExit(f"no HF snapshot for {base}; run cloud/setup.sh {base}")
    return snaps[0]


# --- the two gates run_author uses, copied so this file imports nothing Windows-specific

def gate_generation(run_id, expect_probe=False):
    rows = read_jsonl(os.path.join(RUNS, run_id, "gens.jsonl"))
    n = len(rows)
    trunc = sum(1 for r in rows if "truncated" in (r.get("flags") or []))
    pref = sum(1 for r in rows if "preface" in (r.get("flags") or []))
    ratio = st.mean(r["len_ratio"] for r in rows) if rows else 0
    probe_ok = True
    if expect_probe:
        mans = [m for m in os.listdir(os.path.join(RUNS, run_id)) if m.startswith("s3_manifest")]
        probe_ok = any((read_json(os.path.join(RUNS, run_id, m)).get("adapter_probe") or {}).get("identical") is False for m in mans)
    checks = {"n": n, "truncated_pct": round(100 * trunc / max(n, 1), 1), "preface_pct": round(100 * pref / max(n, 1), 1),
              "len_ratio_mean": round(ratio, 2), "adapter_probe_ok": probe_ok}
    ok = checks["truncated_pct"] <= 20 and checks["preface_pct"] <= 5 and probe_ok and n > 0
    log(f"[gates] generation {run_id} ok={ok} {checks}")
    return ok, checks


def gate_training(tag):
    r = read_json(os.path.join(RUNS, f"train_{tag}", "run.json"))
    ev = [h["eval_loss"] for h in r["history"] if "eval_loss" in h]
    delta = (r.get("probe") or {}).get("delta")
    # "improved" used to require min(eval) strictly below the first eval. On a
    # 33-brief author at 14B the two evals land one step apart with identical
    # loss (cather, 2026-09-08: 2.525 and 2.525) and the adapter was ruled a
    # failure although its probe delta was -0.387. A flat eval history with a
    # passing probe is a short run, not a failed one.
    improved = (len(ev) >= 2 and min(ev) <= ev[0]) or (len(ev) < 2 and delta is not None)
    # The probe-delta threshold (-0.2) was calibrated on Qwen3, where adapters move the
    # held-out loss by -0.3 to -1.1. Ministral 3 3B (2026-09-09) improved its eval loss and
    # moved the probe by -0.074, and the Qwen threshold ruled it a failure. A family may
    # set its own threshold in logs/probe_delta_max.txt on the pod (or DR_PROBE_DELTA_MAX);
    # absent, the Qwen value stands, so no Qwen run changes. The delta is always recorded.
    delta_max = -0.2
    src = os.path.join(LOGS, "probe_delta_max.txt")
    if os.environ.get("DR_PROBE_DELTA_MAX"):
        delta_max = float(os.environ["DR_PROBE_DELTA_MAX"])
    elif os.path.exists(src):
        delta_max = float(open(src).read().strip() or -0.2)
    ok = improved and (delta is None or delta < delta_max)
    checks = {"steps": r["steps"], "eval_best": round(min(ev), 4) if ev else None, "probe_delta": round(delta, 3) if delta is not None else None,
              "probe_delta_max": delta_max, "wall_min": round(r["wall_s"] / 60, 1), "single_eval": len(ev) < 2}
    log(f"[gates] training {tag} ok={ok} {checks}")
    return ok, checks


class Job:
    def __init__(self, author, a, base, gguf, tag):
        self.author, self.a, self.base_model, self.gguf, self.tag = author, a, base, gguf, tag   # base_model: the method base() must not be shadowed
        self.base_run = f"{author}_base{tag}"
        self.train_tag = f"{author}_{a.recipe}_e{a.epochs}_{tag}"   # always tagged on the cloud; the untagged name is the local 4B run
        self.adapter_run = f"{author}_{a.recipe}e{a.epochs}_{tag}"
        private = author in {x.strip() for x in a.private.split(",") if x.strip()}
        self.base_arms = ARMS5 if private else a.base_arms
        self.adapter_arms = ARMS5 if private else a.adapter_arms   # private authors: the same five arms locally (patrick_v2_paire6_4b), not A0,A5
        self.state_path = os.path.join(RUNS, f"cloud_state_{author}_{tag}.json")
        self.state = read_json(self.state_path) if os.path.exists(self.state_path) else {"steps": []}
        self.log = f"cloud_{author}_{tag}.log"

    def note(self, **kw):
        kw["ts"] = dt.datetime.now().strftime("%m-%d %H:%M")
        self.state["steps"].append(kw)
        write_json(self.state_path, self.state)
        log(f"[{self.author}/{self.tag}] {kw}")

    def step(self, name, fn):
        if any(s.get("name") == name and s.get("ok") for s in self.state["steps"]):
            log(f"[{self.author}/{self.tag}] skip {name}")
            return True
        t0 = time.time()
        log(f"==== {self.author}/{self.tag}: {name}")
        try:
            res = fn()
            ok = res is not False
            self.note(name=name, ok=ok, minutes=round((time.time() - t0) / 60, 1))
            return ok
        except Exception as e:
            self.note(name=name, ok=False, minutes=round((time.time() - t0) / 60, 1), error=repr(e)[:300], tb=traceback.format_exc()[-800:])
            return False

    @property
    def url(self):
        return f"http://127.0.0.1:{self.a.port}"

    def server(self, lora=None, model=None):
        run([PY, "dr/llamacpp.py", "start", "--model", model or self.gguf, "--slots", str(self.a.slots), "--url", self.url] + (["--lora", lora] if lora else []), self.log)

    @staticmethod
    def merge_mode():
        """Adapter served as merged weights (2026-09-09): llama.cpp's LoRA converter wrote full-model
        tensors for Ministral 3 (Mistral3ForConditionalGeneration) and the server refused the file, so
        for that family the adapter is merged into the base with peft and the merged model is converted
        to F16 GGUF, the same forward pass as runtime LoRA application in F16. Switched on per pod by
        logs/adapter_mode.txt containing "merge" (or DR_ADAPTER_MODE=merge); the Qwen runs never set it."""
        mode = os.environ.get("DR_ADAPTER_MODE", "")
        src = os.path.join(LOGS, "adapter_mode.txt")
        if not mode and os.path.exists(src):
            mode = open(src).read().strip()
        return mode == "merge"

    def adapter_artifact(self):
        d = os.path.join(RUNS, f"train_{self.train_tag}")
        return os.path.join(d, "merged.gguf" if self.merge_mode() else "adapter.gguf")

    def server_stop(self):
        run([PY, "dr/llamacpp.py", "stop", "--url", self.url], self.log)

    def base(self):
        man = os.path.join(RUNS, self.base_run, f"s3_manifest_{self.base_arms.replace(',', '_')}.json")
        if not os.path.exists(man):
            self.server()
            try:
                run([PY, "dr/s3_generate.py", "--author", self.author, "--run", self.base_run, "--arms", self.base_arms,
                     "--backend", "llamacpp", "--base", self.base_model, "--slots", str(self.a.slots), "--server", self.url], self.log)
            finally:
                self.server_stop()
        ok, checks = gate_generation(self.base_run)
        self.note(name="gate base generation", ok=ok, **checks)
        return ok

    def train(self):
        adir = os.path.join(RUNS, f"train_{self.train_tag}", "adapter")
        if not os.path.exists(os.path.join(adir, "adapter_config.json")):
            cmd = [PY, "dr/s4_train.py", "--author", self.author, "--recipe", self.a.recipe, "--epochs", str(self.a.epochs),
                   "--tag", self.train_tag, "--base", self.base_model, "--bs", str(self.a.bs), "--accum", str(self.a.accum)]
            if self.a.train_limit:
                cmd += ["--limit", str(self.a.train_limit)]   # cap fit examples (2026-09-09: 1290 = Chesterton's 215 targets x 6) so data size is constant across authors
            run(cmd, self.log)
        ok, checks = gate_training(self.train_tag)
        self.note(name="gate training", ok=ok, **checks)
        if not ok:
            return False
        gguf = self.adapter_artifact()
        if not os.path.exists(gguf):
            if self.merge_mode():
                run([PY, "dr/merge_adapter.py", "--adapter", adir, "--base", self.base_model, "--out", gguf, "--device", os.environ.get("DR_MERGE_DEVICE", "cpu")], self.log)
                open(gguf + ".done", "w").write(str(os.path.getsize(gguf)))   # completion marker for the generate lane (2026-09-09 race)
            else:
                run([PY, os.path.join(os.environ.get("DR_LLAMA_TOOLS", os.path.join(DR, "tools", "llama.cpp")), "convert_lora_to_gguf.py"), "--base", snapshot(self.base_model),
                     "--outfile", gguf, "--outtype", "f16", adir], self.log)
        return True

    def adapter(self):
        """Adapter arms; in the generate lane, waits for the train lane's adapter.gguf."""
        gguf = self.adapter_artifact()
        adir = os.path.join(RUNS, f"train_{self.train_tag}", "adapter")
        if self.a.lane == "generate":
            t0 = time.time()
            while not os.path.exists(gguf):
                if time.time() - t0 > 6 * 3600:
                    raise RuntimeError("waited 6 h for the adapter from the train lane")
                time.sleep(60)
            # 2026-09-09: the converter creates the GGUF before it finishes writing it; the
            # generate lane once launched the server on a half-written file. Wait for the
            # train lane's .done marker, or failing that for the size to hold still for 90 s.
            t1 = time.time()
            while not os.path.exists(gguf + ".done"):
                sz = os.path.getsize(gguf); time.sleep(90)
                if os.path.getsize(gguf) == sz and sz > 0:
                    break
                if time.time() - t1 > 2 * 3600:
                    raise RuntimeError("adapter artifact never stabilised")
        elif not os.path.exists(gguf):
            if not self.train():
                return False
        if not os.path.exists(gguf):
            raise RuntimeError(f"no adapter gguf at {gguf}")
        man = os.path.join(RUNS, self.adapter_run, f"s3_manifest_{self.adapter_arms.replace(',', '_')}.json")
        if not os.path.exists(man):
            merged = self.merge_mode()
            if merged:
                self.server(model=gguf)          # merged weights: no runtime LoRA
            else:
                self.server(gguf)
            try:
                run([PY, "dr/s3_generate.py", "--author", self.author, "--run", self.adapter_run, "--arms", self.adapter_arms,
                     "--backend", "llamacpp", "--adapter-gguf", gguf, "--base", self.base_model, "--slots", str(self.a.slots), "--server", self.url]
                    + (["--merged"] if merged else []), self.log)
            finally:
                self.server_stop()
        ok, checks = gate_generation(self.adapter_run, expect_probe=True)
        self.note(name="gate adapter generation", ok=ok, **checks)
        return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--authors", required=True)
    ap.add_argument("--base", required=True, help="HF id, e.g. Qwen/Qwen3-8B")
    ap.add_argument("--gguf", required=True, help="F16 GGUF of --base")
    ap.add_argument("--model-tag", required=True, help="8b, 14b ...")
    ap.add_argument("--recipe", default="pair")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--train-limit", type=int, default=0, help="cap on fit examples passed to s4_train --limit (0 = all); 1290 matches Chesterton's adapter")
    ap.add_argument("--bs", type=int, default=1)
    ap.add_argument("--accum", type=int, default=8)
    ap.add_argument("--port", type=int, default=8089, help="llama-server port; give each generate lane its own")
    ap.add_argument("--slots", type=int, default=32, help="server slots; 48 GB holds 32 x 5120 ctx beside an 8B in F16")
    ap.add_argument("--lane", default="both", choices=["both", "train", "generate"], help="two-lane mode: run one process per lane on the same card with DR_ALLOW_SHARED_GPU=1")
    ap.add_argument("--base-arms", default=ARMS6)
    ap.add_argument("--adapter-arms", default="A0,A1,A5")
    ap.add_argument("--private", default="patrick_v2,h_private", help="authors that drop A1")
    ap.add_argument("--bridge", default="", help="HF id:GGUF of the 4B to replicate on this card for the first author, e.g. Qwen/Qwen3-4B:/workspace/models/Qwen3-4B-F16.gguf")
    a = ap.parse_args()
    if not os.environ.get("DR_LLAMA_SERVER"):
        raise SystemExit("set DR_LLAMA_SERVER to the llama-server binary built by cloud/setup.sh")
    authors = [x.strip() for x in a.authors.split(",") if x.strip()]
    jobs = []
    if a.bridge:
        b, g = a.bridge.split(":", 1)
        jobs.append(Job(authors[0], a, b, g, "4bc"))   # 4B on the cloud card: its own tag, never the local run's name
    jobs += [Job(au, a, a.base, a.gguf, a.model_tag) for au in authors]
    log(f"cloud run: {[j.base_run for j in jobs]}; slots {a.slots}; bs {a.bs} x accum {a.accum}")
    pull = []
    if a.lane == "train":
        os.environ["DR_ALLOW_SHARED_GPU"] = "1"
        for j in jobs:
            j.step("train", j.train)
    else:
        if a.lane == "generate":
            os.environ["DR_ALLOW_SHARED_GPU"] = "1"
        for j in jobs:                       # base arms for every author first (no adapter dependency)
            j.step("base run", j.base)
        for j in jobs:
            # 2026-09-09: base arms on disk are enough for the adapter step; a failed base gate
            # (truncation above the Qwen-calibrated 20%, a Ministral family property) is a
            # recorded flag, not a blocker. base() already skips generation once the manifest exists.
            base_man = os.path.join(RUNS, j.base_run, f"s3_manifest_{j.base_arms.replace(',', '_')}.json")
            if any(s.get("name") == "base run" and s.get("ok") for s in j.state["steps"]) or os.path.exists(base_man):
                j.step("adapter", j.adapter)
    for j in jobs:
        pull += [j.base_run, j.adapter_run, f"train_{j.train_tag}"]
    write_json(os.path.join(RUNS, "cloud_pull_list.json"), {"runs": pull, "ts": dt.datetime.now().isoformat(timespec="seconds")})
    log(f"pull list -> runs/cloud_pull_list.json ({len(pull)} entries)")
    log("cloud run complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
