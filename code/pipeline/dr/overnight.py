"""Overnight controller, 2026-09-03: follow-ups after the main chain, each
gated, each non-fatal, all written to runs/overnight/MORNING_REPORT.md.

    S0  wait for the main chain (runs/adapter_phase/RESULTS.md)
    S1  quality gates on the four Wharton runs (flags, coverage, encoding)
    S2  merge the pair adapter into an F16 GGUF and validate against the
        unmerged run's greedy probe; decides merged vs --lora for the night
    S3  pair, 6 epochs           -> A0, A1            -> score, judge
    S4  pair, seed 1             -> A0, A1            -> score, judge
    S5  Cather: base run (6 arms), frontier, pair adapter -> A0, A1, A5,
        score, judge, analysis
    S6  detectors (Binoculars, Fast-DetectGPT, 9B observer) on base4b, pair4b
    S7  analysis over every Wharton run; review pages; MORNING_REPORT.md

Gates (a failing gate is reported and the dependent steps are skipped; the
next independent step runs):
    generation   truncated <= 20%, preface <= 5%, no U+FFFD, mean length
                 ratio in [0.6, 1.6], adapter probe not identical
    training     best eval loss below the first eval; probe delta < -0.2 nats
    scoring      geometry keeps >= 10 features; A0 primary in [0.6, 0.95]
    coverage     reported, not gated: a variant whose coverage falls under 40
                 is flagged in the report as "drifts from the brief"

    python dr/overnight.py            # run
    python dr/overnight.py --dry      # plan only
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import statistics as st
import subprocess
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import DR, LOGS, RUNS, author_dir, log, read_json, read_jsonl, write_json, write_text  # noqa: E402

PY = sys.executable
GGUF_BASE = r"C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf"
OUT = os.path.join(RUNS, "overnight")
os.makedirs(OUT, exist_ok=True)
REPORT = os.path.join(OUT, "MORNING_REPORT.md")
STATE = os.path.join(OUT, "state.json")
ARMS6 = "A0,A1,A2,A3,A4,A5"
state = {"steps": [], "gates": [], "decisions": {}, "started": dt.datetime.now().isoformat(timespec="seconds")}
if os.path.exists(STATE):
    state.update(read_json(STATE))


def save():
    write_json(STATE, state)


def note(kind, **kw):
    kw["ts"] = dt.datetime.now().strftime("%H:%M")
    state.setdefault(kind, []).append(kw)
    save()
    log(f"[{kind}] {kw}")


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


def wait_for(path, every=20):
    if not os.path.exists(path):
        log(f"waiting for {path}")
    while not os.path.exists(path):
        time.sleep(every)


def server_start(model, lora=None):
    cmd = [PY, "dr/llamacpp.py", "start", "--model", model]
    if lora:
        cmd += ["--lora", lora]
    run(cmd, "overnight_server.log")


def server_stop():
    run([PY, "dr/llamacpp.py", "stop"], "overnight_server.log")


def judge_bg(run_id, author):
    marker = os.path.join(RUNS, run_id, "judge.started")
    if os.path.exists(marker):
        return
    p = run([PY, "dr/s5b_judge.py", "--run", run_id, "--author", author], f"overnight_judge_{run_id}.log", background=True)
    with open(marker, "w") as f:
        f.write(f"{p.pid}\n")


# ------------------------------------------------------------------ gates

def gate_generation(run_id, expect_probe=False):
    p = os.path.join(RUNS, run_id, "gens.jsonl")
    rows = read_jsonl(p)
    n = len(rows)
    fl = collections.Counter(f for r in rows for f in r["flags"])
    bad_enc = sum(1 for r in rows if "\ufffd" in r["text"])
    ratio = st.mean(r["len_ratio"] for r in rows)
    probe_ok = True
    if expect_probe:
        mans = [f for f in os.listdir(os.path.join(RUNS, run_id)) if f.startswith("s3_manifest")]
        probe_ok = any((read_json(os.path.join(RUNS, run_id, m)).get("adapter_probe") or {}).get("identical") is False for m in mans)
    checks = {"n": n, "truncated_pct": round(100 * fl["truncated"] / max(n, 1), 1),
              "preface_pct": round(100 * fl["preface"] / max(n, 1), 1), "bad_encoding": bad_enc,
              "len_ratio_mean": round(ratio, 2), "adapter_probe_ok": probe_ok}
    ok = (checks["truncated_pct"] <= 20 and checks["preface_pct"] <= 5 and bad_enc == 0
          and 0.6 <= ratio <= 1.6 and probe_ok)
    note("gates", step="generation", run=run_id, ok=ok, **checks)
    return ok


def gate_training(tag):
    r = read_json(os.path.join(RUNS, f"train_{tag}", "run.json"))
    ev = [h["eval_loss"] for h in r["history"] if "eval_loss" in h]
    pv = [h["eval_pairview_loss"] for h in r["history"] if "eval_pairview_loss" in h]
    delta = (r.get("probe") or {}).get("delta")
    checks = {"steps": r["steps"], "eval_first": round(ev[0], 4) if ev else None, "eval_best": round(min(ev), 4) if ev else None,
              "pairview_last": round(pv[-1], 4) if pv else None, "probe_delta": round(delta, 3) if delta is not None else None,
              "wall_min": round(r["wall_s"] / 60, 1)}
    # Thin authors (< 2 x eval_every steps) get at most one eval, so "loss
    # fell" cannot be tested; the adapter-on/off probe carries the gate alone
    # (Sui Sin Far 2026-09-06: 18 steps, one eval, probe delta -0.72, failed).
    improved = (len(ev) >= 2 and min(ev) < ev[0]) or (len(ev) < 2 and delta is not None)
    ok = improved and (delta is None or delta < -0.2)
    checks["single_eval"] = len(ev) < 2
    note("gates", step="training", tag=tag, ok=ok, **checks)
    return ok


def gate_scoring(run_id):
    s = read_json(os.path.join(RUNS, run_id, "scores_summary.json"))
    g = read_json(os.path.join(RUNS, run_id, "geometry.json"))
    a0 = (s.get("A0") or {}).get("luar_cos_source")
    checks = {"geometry_kept": len(g["kept"]), "A0_primary": a0,
              "arms": {k: v.get("luar_cos_source") for k, v in s.items() if k.startswith(("A", "F"))}}
    ok = len(g["kept"]) >= 10 and (a0 is None or 0.6 <= a0 <= 0.95)
    note("gates", step="scoring", run=run_id, ok=ok, **checks)
    return ok


def coverage_of(run_id):
    p = os.path.join(RUNS, run_id, "judge_summary.json")
    if not os.path.exists(p):
        return {}
    s = read_json(p)
    return {k: v.get("coverage") for k, v in s.items() if not k.startswith("_")}


# ------------------------------------------------------------------ steps

def step(name, fn, depends=True):
    done = {s["name"] for s in state["steps"] if s.get("ok")}
    if name in done:
        log(f"skip {name} (done)")
        return True
    if not depends:
        note("steps", name=name, ok=False, skipped="dependency failed")
        return False
    t0 = time.time()
    log(f"==== {name}")
    try:
        res = fn()
        ok = res is not False
        note("steps", name=name, ok=ok, minutes=round((time.time() - t0) / 60, 1))
        return ok
    except Exception as e:
        note("steps", name=name, ok=False, minutes=round((time.time() - t0) / 60, 1),
             error=repr(e)[:300], tb=traceback.format_exc()[-1200:])
        return False


def adapter_pipeline(author, tag, train_args, run_id, arms, anchor, use_merged):
    """train -> gate -> (merge | convert) -> server -> generate -> gate -> score -> gate -> judges"""
    adir = os.path.join(RUNS, f"train_{tag}", "adapter")
    if not os.path.exists(os.path.join(adir, "adapter_config.json")):
        run([PY, "dr/s4_train.py", "--author", author, "--tag", tag] + train_args, f"overnight_train_{tag}.log")
    if not gate_training(tag):
        return False
    gguf_lora = os.path.join(RUNS, f"train_{tag}", "adapter.gguf")
    merged = os.path.join(RUNS, f"train_{tag}", "merged.gguf")
    if use_merged:
        if not os.path.exists(merged):
            run([PY, "dr/merge_adapter.py", "--adapter", adir], f"overnight_merge_{tag}.log")
        server_start(merged)
        gen_extra = []
    else:
        if not os.path.exists(gguf_lora):
            snap = sorted(__import__("glob").glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--Qwen--Qwen3-4B", "snapshots", "*")))[0]
            run([PY, os.path.join(DR, "tools", "llama.cpp", "convert_lora_to_gguf.py"), "--base", snap,
                 "--outfile", gguf_lora, "--outtype", "f16", adir], "overnight_convert.log")
        server_start(GGUF_BASE, gguf_lora)
        gen_extra = ["--adapter-gguf", gguf_lora]
    try:
        man = os.path.join(RUNS, run_id, f"s3_manifest_{arms.replace(',', '_')}.json")
        if not os.path.exists(man):
            run([PY, "dr/s3_generate.py", "--author", author, "--run", run_id, "--arms", arms, "--backend", "llamacpp"] + gen_extra,
                f"overnight_gen_{run_id}.log")
    finally:
        server_stop()
    if not gate_generation(run_id, expect_probe=not use_merged):
        return False
    if not os.path.exists(os.path.join(RUNS, run_id, "scores.jsonl")):
        run([PY, "dr/s5_score.py", "--run", run_id, "--author", author, "--anchor-run", anchor], f"overnight_score_{run_id}.log")
    ok = gate_scoring(run_id)
    judge_bg(run_id, author)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--skip-cather", action="store_true")
    ap.add_argument("--skip-detect", action="store_true")
    a = ap.parse_args()
    plan = ["S0 wait chain", "S1 gates on wharton runs", "S2 merge + validate", "S3 pair 6 epochs",
            "S4 pair seed 1", "S5 cather", "S6 detectors", "S7 analysis + report"]
    for p in plan:
        log("  " + p)
    if a.dry:
        return 0

    # S0
    step("S0 wait chain", lambda: wait_for(os.path.join(RUNS, "adapter_phase", "RESULTS.md")))

    # S1 gates
    def s1():
        ok = True
        for r in ("base4b", "pair4b", "mix4b", "raw4b"):
            if os.path.exists(os.path.join(RUNS, r, "gens.jsonl")):
                ok &= gate_generation(r, expect_probe=(r != "base4b"))
                if os.path.exists(os.path.join(RUNS, r, "scores_summary.json")):
                    gate_scoring(r)
                cov = coverage_of(r)
                if cov:
                    note("gates", step="coverage", run=r, **{k: v for k, v in cov.items() if v is not None})
        return True   # gates are reported; a failing base run would already be visible
    step("S1 gates on wharton runs", s1)

    # S2 merge + validate
    def s2():
        adir = os.path.join(RUNS, "train_wharton_pair_r16_s0", "adapter")
        merged = os.path.join(RUNS, "train_wharton_pair_r16_s0", "merged.gguf")
        if not os.path.exists(merged):
            run([PY, "dr/merge_adapter.py", "--adapter", adir], "overnight_merge_pair.log")
        # reference greedy text from the unmerged run's probe
        ref = None
        for m in os.listdir(os.path.join(RUNS, "pair4b")):
            if m.startswith("s3_manifest"):
                ref = (read_json(os.path.join(RUNS, "pair4b", m)).get("adapter_probe") or {}).get("greedy_on")
        server_start(merged)
        try:
            from transformers import AutoTokenizer
            from dr import llamacpp as L
            tok = AutoTokenizer.from_pretrained(config.BASE_MODEL)
            prompt = L.render_prompt(tok, "You write prose fiction.", "Write the opening of a scene at a dinner party.")
            got = L.complete(prompt, 40, seed=0, greedy=True)["text"]
            base_txt = None
        finally:
            server_stop()
        ra, rb = (ref or "").split(), got.split()
        overlap = sum(1 for x, y in zip(ra, rb) if x == y) / max(min(len(ra), len(rb)), 1)
        ok = overlap >= 0.6
        state["decisions"]["use_merged"] = ok
        note("gates", step="merge_validate", ok=ok, prefix_overlap=round(overlap, 2), merged=got[:120], unmerged=(ref or "")[:120])
        return True
    step("S2 merge + validate", s2)
    use_merged = state["decisions"].get("use_merged", False)

    # S3 pair 6 epochs
    step("S3 pair 6 epochs", lambda: adapter_pipeline(
        "wharton", "wharton_pair_e6", ["--recipe", "pair", "--epochs", "6"], "pair_e6_4b", "A0,A1", "base4b", use_merged))

    # S5 cather
    def s5():
        d = author_dir("cather")
        wait_for(os.path.join(d, "retrieval_test.jsonl"))
        server_start(GGUF_BASE)
        try:
            man = os.path.join(RUNS, "cather_base4b", f"s3_manifest_{ARMS6.replace(',', '_')}.json")
            if not os.path.exists(man):
                run([PY, "dr/s3_generate.py", "--author", "cather", "--run", "cather_base4b", "--arms", ARMS6, "--backend", "llamacpp"],
                    "overnight_gen_cather_base.log")
        finally:
            server_stop()
        if not gate_generation("cather_base4b"):
            return False
        run([PY, "dr/s3_generate.py", "--author", "cather", "--run", "cather_base4b_frontier", "--arms", "F0,F5"],
            "overnight_gen_cather_frontier.log", background=True)
        if not os.path.exists(os.path.join(RUNS, "cather_base4b", "scores.jsonl")):
            run([PY, "dr/s5_score.py", "--run", "cather_base4b", "--author", "cather"], "overnight_score_cather_base.log")
        gate_scoring("cather_base4b")
        judge_bg("cather_base4b", "cather")
        return adapter_pipeline("cather", "cather_pair_r16_s0", ["--recipe", "pair"], "cather_pair4b", "A0,A1,A5",
                                "cather_base4b", use_merged)
    if not a.skip_cather:
        step("S5 cather", s5)

    # S4 pair seed 1
    step("S4 pair seed 1", lambda: adapter_pipeline(
        "wharton", "wharton_pair_s1", ["--recipe", "pair", "--seed", "1"], "pair_s1_4b", "A0,A1", "base4b", use_merged))

    # S6 detectors
    def s6():
        for r in ("base4b", "pair4b"):
            run([PY, "dr/s5_score.py", "--run", r, "--author", "wharton", "--anchor-run", "base4b", "--detect"],
                f"overnight_detect_{r}.log")
        return True
    if not a.skip_detect:
        step("S6 detectors", s6)

    # S7 analysis + report
    def s7():
        wr = [r for r in ("base4b", "base4b_frontier", "pair4b", "mix4b", "raw4b", "pair_e6_4b", "pair_s1_4b")
              if os.path.exists(os.path.join(RUNS, r, "scores.jsonl"))]
        run([PY, "dr/s6_analysis.py", "--runs", ",".join(wr), "--out", os.path.join(OUT, "wharton")], "overnight_analysis.log")
        cr = [r for r in ("cather_base4b", "cather_base4b_frontier", "cather_pair4b")
              if os.path.exists(os.path.join(RUNS, r, "scores.jsonl"))]
        if "cather_base4b_frontier" in cr and not os.path.exists(os.path.join(RUNS, "cather_base4b_frontier", "scores.jsonl")):
            cr.remove("cather_base4b_frontier")
        if cr:
            for r in cr:
                if not os.path.exists(os.path.join(RUNS, r, "scores.jsonl")):
                    run([PY, "dr/s5_score.py", "--run", r, "--author", "cather", "--anchor-run", "cather_base4b"], f"overnight_score_{r}.log")
            run([PY, "dr/s6_analysis.py", "--runs", ",".join(cr), "--out", os.path.join(OUT, "cather")], "overnight_analysis.log")
        run([PY, "dr/review_page.py", "--author", "wharton", "--runs", ",".join(wr), "--n", "3", "--out", os.path.join(RUNS, "review.html")], "overnight_analysis.log")
        if cr:
            run([PY, "dr/review_page.py", "--author", "cather", "--runs", ",".join(cr), "--n", "3", "--out", os.path.join(RUNS, "review_cather.html")], "overnight_analysis.log")
        return True
    step("S7 analysis + report", s7)
    write_report()
    log("overnight complete")
    return 0


def write_report():
    lines = [f"# Morning report, overnight of 2026-09-03 (written {dt.datetime.now():%Y-%m-%d %H:%M})", ""]
    lines += ["## Steps", "", "| step | ok | minutes | note |", "|---|---|---:|---|"]
    for s in state["steps"]:
        lines.append(f"| {s['name']} | {'yes' if s.get('ok') else 'NO'} | {s.get('minutes', '')} | {s.get('error') or s.get('skipped') or ''} |")
    lines += ["", "## Gates", ""]
    for g in state.get("gates", []):
        g2 = {k: v for k, v in g.items() if k not in ("tb",)}
        lines.append(f"- {json.dumps(g2, ensure_ascii=False)}")
    lines += ["", "## Decisions", "", f"- {json.dumps(state['decisions'])}", ""]
    # primary per run
    lines += ["## Primary outcome (LUAR to source), means per run and arm", "", "| run | " + " | ".join(["A0", "A1", "A2", "A3", "A4", "A5", "F0", "F5"]) + " | coverage A0 |", "|---|" + "---:|" * 9]
    for r in sorted(os.listdir(RUNS)):
        sp = os.path.join(RUNS, r, "scores_summary.json")
        if not os.path.exists(sp):
            continue
        s = read_json(sp)
        cov = coverage_of(r).get("A0")
        cells = [f"{s[k]['luar_cos_source']:.3f}" if k in s and s[k].get("luar_cos_source") is not None else "" for k in ["A0", "A1", "A2", "A3", "A4", "A5", "F0", "F5"]]
        lines.append(f"| {r} | " + " | ".join(cells) + f" | {cov if cov is not None else ''} |")
    lines += ["", "Full tables: `runs/overnight/wharton/RESULTS.md`, `runs/overnight/cather/RESULTS.md`; pages `runs/review.html`, `runs/review_cather.html`.", ""]
    try:
        rows = read_jsonl(os.path.join(LOGS, "api_ledger.jsonl"), strict=False)
        lines.append(f"API spend to date: USD {sum((r.get('usd') or 0) for r in rows):.2f}")
    except Exception:
        pass
    write_text(REPORT, "\n".join(lines) + "\n")
    log(f"-> {REPORT}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        write_report()
