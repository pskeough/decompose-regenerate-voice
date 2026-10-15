"""Day 2026-09-06: the remaining GPU work for the paper, behind a smoke run.

    python dr/day_0906.py            # resumable; state in runs/day_0906/state.json
    python dr/day_0906.py --dry      # print the plan
    python dr/day_0906.py --eval-only

    D0 smoke (~35 min)  replay set for Wharton (base server), 8-target 1-epoch
                        pair+replay adapter, convert, adapter server, 2-passage
                        A0 at temperature 0.6, score vs base4b with NF4
                        detectors, judge 2 rows. Every artefact is checked;
                        a failure stops the day.
    D1 size curve       chesterton, pair-6, nested seeded subsets 25/50/100/150
                        (the 215 point is the existing chesterton_paire6_4b)   ~4.5 h
    D2 adherence        wharton pair-6: (a) temperature 0.6 arms A0,A1;
                        (b) replay 10% adapter, arms A0,A1                      ~2.5 h
    D3 seed             mansfield pair-6 seed 1, arms A0,A1,A5                  ~1 h
    D4 detectors        NF4 4B pair on chesterton/mansfield/wharton base+adapter ~4.5 h
    D5 eval             runs/day_0906/REPORT.md

GPU steps are serial; judges run in the background (sample 0). Nothing else
may touch the card while this runs; launch through logs/launch_detached.ps1.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DR, LOGS, RUNS, credits_usd, log, read_json, read_jsonl, write_json, write_text  # noqa: E402

PY = sys.executable
GGUF_BASE = r"C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf"
DETECT = ["--detect", "--observer", "Qwen/Qwen3.5-4B-Base", "--performer", "Qwen/Qwen3.5-4B", "--obs-4bit", "--perf-4bit"]
OUT = os.path.join(RUNS, "day_0906")
os.makedirs(OUT, exist_ok=True)
STATE = os.path.join(OUT, "state.json")
state = read_json(STATE) if os.path.exists(STATE) else {"steps": []}
SNAP = sorted(glob.glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--Qwen--Qwen3-4B", "snapshots", "*")))[0]


def note(**kw):
    kw["ts"] = dt.datetime.now().strftime("%m-%d %H:%M")
    state["steps"].append(kw)
    write_json(STATE, state)
    log(f"[day] {kw}")


def run(cmd, logname, background=False):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    logf = open(os.path.join(LOGS, logname), "a", encoding="utf-8")
    logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
    logf.flush()
    log(f"$ {' '.join(cmd)}  -> logs/{logname}")
    p = subprocess.Popen(cmd, cwd=DR, stdout=logf, stderr=subprocess.STDOUT, env=env)
    if background:
        return p
    if p.wait() != 0:
        raise RuntimeError(f"failed: {' '.join(cmd)} (logs/{logname})")


def step(name, fn):
    if any(s.get("name") == name and s.get("ok") for s in state["steps"]):
        log(f"skip {name}")
        return True
    t0 = time.time()
    log(f"==== {name}")
    try:
        res = fn()
        ok = res is not False
        note(name=name, ok=ok, minutes=round((time.time() - t0) / 60, 1))
        return ok
    except Exception as e:
        note(name=name, ok=False, minutes=round((time.time() - t0) / 60, 1), error=repr(e)[:300], tb=traceback.format_exc()[-800:])
        return False


def server(lora=None, logname="day_0906_server.log"):
    run([PY, "dr/llamacpp.py", "start", "--model", GGUF_BASE] + (["--lora", lora] if lora else []), logname)


def server_stop(logname="day_0906_server.log"):
    run([PY, "dr/llamacpp.py", "stop"], logname)


def convert(tag, logname):
    adir = os.path.join(RUNS, f"train_{tag}", "adapter")
    gguf = os.path.join(RUNS, f"train_{tag}", "adapter.gguf")
    if not os.path.exists(gguf):
        run([PY, os.path.join(DR, "tools", "llama.cpp", "convert_lora_to_gguf.py"), "--base", SNAP, "--outfile", gguf, "--outtype", "f16", adir], logname)
    return gguf


def adapter_arms(author, tag, run_id, arms, logname, temperature=None, limit=0):
    """train_<tag> must exist: convert, serve with the adapter, generate, stop."""
    gguf = convert(tag, logname)
    man = os.path.join(RUNS, run_id, f"s3_manifest_{arms.replace(',', '_')}.json")
    if not os.path.exists(man):
        server(gguf, logname)
        try:
            cmd = [PY, "dr/s3_generate.py", "--author", author, "--run", run_id, "--arms", arms, "--backend", "llamacpp", "--adapter-gguf", gguf]
            if temperature is not None:
                cmd += ["--temperature", str(temperature)]
            if limit:
                cmd += ["--limit", str(limit)]
            run(cmd, logname)
        finally:
            server_stop(logname)
    return gguf


def score(run_id, author, anchor, logname, detect=False):
    if not os.path.exists(os.path.join(RUNS, run_id, "scores.jsonl")) or detect:
        run([PY, "dr/s5_score.py", "--run", run_id, "--author", author, "--anchor-run", anchor] + (DETECT if detect else []), logname)


def judge_bg(run_id, author, logname, extra=()):
    marker = os.path.join(RUNS, run_id, "judge.started")
    if os.path.exists(marker):
        return
    p = run([PY, "dr/s5b_judge.py", "--run", run_id, "--author", author, "--only-samples", "0", *extra], logname, background=True)
    open(marker, "w").write(f"{p.pid}\n")


# ------------------------------------------------------------------ D0 smoke

def smoke():
    L = "day_0906_smoke.log"
    replay = os.path.join(DR, "data", "wharton", "replay_base.jsonl")
    if not os.path.exists(replay):
        server(logname=L)
        try:
            run([PY, "dr/make_replay.py", "--author", "wharton"], L)
        finally:
            server_stop(L)
    rows = read_jsonl(replay)
    assert len(rows) >= 50 and all(k in rows[0] for k in ("system", "user", "target")), f"replay set malformed: {len(rows)} rows"
    tag, rid = "smoke_0906", "smoke_0906"
    if not os.path.exists(os.path.join(RUNS, f"train_{tag}", "adapter", "adapter_config.json")):
        run([PY, "dr/s4_train.py", "--author", "wharton", "--recipe", "pair", "--epochs", "1", "--n-targets", "8", "--tag", tag,
             "--replay-file", replay, "--replay-frac", "0.5"], L)
    r = read_json(os.path.join(RUNS, f"train_{tag}", "run.json"))
    assert r["steps"] >= 1 and r.get("probe"), f"smoke training incomplete: {r.get('steps')} steps, probe {r.get('probe')}"
    assert any("replay" in k for k in r.get("framings", {})), f"replay framing absent: {r.get('framings')}"
    adapter_arms("wharton", tag, rid, "A0", L, temperature=0.6, limit=2)
    man = json.dumps(read_json(os.path.join(RUNS, rid, "s3_manifest_A0.json")))
    assert "0.6" in man, "temperature 0.6 not recorded in the manifest"
    gens = read_jsonl(os.path.join(RUNS, rid, "gens.jsonl"))
    assert gens and all((g.get("text") or "").strip() for g in gens), "empty smoke generations"
    scp = os.path.join(RUNS, rid, "scores.jsonl")
    have_detect = os.path.exists(scp) and any(k.startswith("binoculars") and v is not None for k, v in read_jsonl(scp)[0].items())
    if not have_detect:
        score(rid, "wharton", "base4b", L, detect=True)
    s = read_json(os.path.join(RUNS, rid, "scores_summary.json"))
    a0 = (s.get("A0") or {}).get("luar_cos_source")
    assert a0 is not None and 0.3 < a0 < 1.0, f"smoke A0 primary {a0}"
    sc = [x for x in read_jsonl(os.path.join(RUNS, rid, "scores.jsonl")) if x.get("group") == "gen"]
    dcols = [k for k in sc[0] if k.startswith(("binoculars", "fastdetectgpt"))]
    assert dcols and all(sc[0].get(k) is not None for k in dcols), f"detector columns missing: {list(sc[0])[:12]}"
    jcmd = [PY, "dr/s5b_judge.py", "--run", rid, "--author", "wharton", "--limit", "2", "--no-coverage", "--suffix", "_smoke"]
    run(jcmd, L)
    j = read_jsonl(os.path.join(RUNS, rid, "judge_smoke.jsonl"))
    if any(x.get("error") for x in j):
        run(jcmd, L)          # the judge retries its own error rows; MiniMax returns an empty completion now and then
        j = read_jsonl(os.path.join(RUNS, rid, "judge_smoke.jsonl"))
    # the judge appends on every run, so judge the LAST row per key; a MiniMax
    # "empty completion, finish=length" recurs on ~5% of items and is tolerated
    last = {}
    for x in j:
        last[(x.get("id"), x.get("arm"), x.get("sample"), x.get("judge"), x.get("comparison"))] = x
    ok_rows = [x for x in last.values() if not x.get("error")]
    per_judge = {x.get("judge") for x in ok_rows}
    assert last and len(ok_rows) >= 0.5 * len(last) and len(per_judge) >= 2,         f"judge smoke: {len(last)} keys, {len(last) - len(ok_rows)} errors, judges answering {sorted(per_judge)}"
    note(name="smoke checks", ok=True, replay_rows=len(rows), steps=r["steps"], a0=round(a0, 3), detect_cols=dcols, judge_rows=len(j))
    log("SMOKE OK")


# --------------------------------------------------------------- D1..D4

def size_curve():
    run([PY, "dr/size_curve.py", "--author", "chesterton", "--base-run", "chesterton_base4b", "--sizes", "25,50,100,150", "--epochs", "6"],
        "day_0906_size_curve.log")


def adherence_t06():
    L = "day_0906_adherence.log"
    adapter_arms("wharton", "wharton_pair_e6", "pair_e6_t06", "A0,A1", L, temperature=0.6)
    score("pair_e6_t06", "wharton", "base4b", L)
    judge_bg("pair_e6_t06", "wharton", "day_0906_judge_t06.log")


def adherence_replay():
    L = "day_0906_adherence.log"
    replay = os.path.join(DR, "data", "wharton", "replay_base.jsonl")
    tag = "wharton_pair_e6_replay"
    if not os.path.exists(os.path.join(RUNS, f"train_{tag}", "adapter", "adapter_config.json")):
        run([PY, "dr/s4_train.py", "--author", "wharton", "--recipe", "pair", "--epochs", "6", "--tag", tag,
             "--replay-file", replay, "--replay-frac", "0.10"], L)
    adapter_arms("wharton", tag, "pair_e6_replay", "A0,A1", L)
    score("pair_e6_replay", "wharton", "base4b", L)
    judge_bg("pair_e6_replay", "wharton", "day_0906_judge_replay.log")


def seed_mansfield():
    L = "day_0906_seed.log"
    tag, rid = "mansfield_pair_e6_s1", "mansfield_paire6s1_4b"
    if not os.path.exists(os.path.join(RUNS, f"train_{tag}", "adapter", "adapter_config.json")):
        run([PY, "dr/s4_train.py", "--author", "mansfield", "--recipe", "pair", "--epochs", "6", "--seed", "1", "--tag", tag], L)
    adapter_arms("mansfield", tag, rid, "A0,A1,A5", L)
    score(rid, "mansfield", "mansfield_base4b", L)
    judge_bg(rid, "mansfield", "day_0906_judge_seed.log")


DETECT_RUNS = [("chesterton_paire6_4b", "chesterton", "chesterton_base4b"), ("chesterton_base4b", "chesterton", "chesterton_base4b"),
               ("mansfield_paire6_4b", "mansfield", "mansfield_base4b"), ("mansfield_base4b", "mansfield", "mansfield_base4b"),
               ("pair_e6_4b", "wharton", "base4b"), ("base4b", "wharton", "base4b")]


def detectors():
    for rid, author, anchor in DETECT_RUNS:
        def one(rid=rid, author=author, anchor=anchor):
            sc = os.path.join(RUNS, rid, "scores.jsonl")
            first = read_jsonl(sc)[0] if os.path.exists(sc) else {}
            if any(k.startswith("binoculars") and first.get(k) is not None for k in first):
                log(f"{rid}: detector columns present, skip")
                return
            score(rid, author, anchor, f"day_0906_detect_{rid}.log", detect=True)
        step(f"D4 detect {rid}", one)


# ------------------------------------------------------------------ D5 eval

def auroc(pos, neg):
    """P(pos > neg) with ties at 0.5."""
    if not pos or not neg:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def prim(rid):
    p = os.path.join(RUNS, rid, "scores_summary.json")
    if not os.path.exists(p):
        return {}
    s = read_json(p)
    return {a: round(v["luar_cos_source"], 3) for a, v in s.items() if isinstance(v, dict) and v.get("luar_cos_source") is not None}


def judge(rid):
    p = os.path.join(RUNS, rid, "judge_summary.json")
    if not os.path.exists(p):
        return {}
    s = read_json(p)
    out = {}
    for a, d in s.items():
        if not a.startswith("A"):
            continue
        fool = [v for k, v in d.items() if k.startswith("vs_source|")]
        out[a] = {"fool": round(st.mean(fool), 3) if fool else None, "cov": d.get("coverage")}
    return out


def trunc(rid):
    p = os.path.join(RUNS, rid, "gens.jsonl")
    if not os.path.exists(p):
        return None
    g = read_jsonl(p)
    return round(100 * sum(1 for r in g if "truncated" in (r.get("flags") or [])) / max(len(g), 1), 1)


def fmt(x):
    return "" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def evaluate():
    L = []
    L += [f"# Day 2026-09-06 report ({dt.datetime.now():%Y-%m-%d %H:%M})", "", "| step | ok | min | note |", "|---|---|---:|---|"]
    for s in state["steps"]:
        if s.get("name"):
            L.append(f"| {s['name']} | {'yes' if s.get('ok') else 'NO'} | {s.get('minutes', '')} | {s.get('error') or ''} |")
    # size curve
    L += ["", "## Data-size curve, Chesterton, pair-6 (base A0 = {} )".format(prim("chesterton_base4b").get("A0")), "",
          "| n targets | steps | eval best | probe | A0 | A1 | trunc % | fool A0 | cov A0 |", "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for n in (25, 50, 100, 150, 215):
        tag, rid = (f"chesterton_pair_n{n}_e6", f"chesterton_size{n}") if n != 215 else ("chesterton_pair_e6", "chesterton_paire6_4b")
        rp = os.path.join(RUNS, f"train_{tag}", "run.json")
        r = read_json(rp) if os.path.exists(rp) else {}
        ev = [h["eval_loss"] for h in r.get("history", []) if "eval_loss" in h]
        pr, jd = prim(rid), judge(rid)
        L.append(f"| {n} | {r.get('steps', '')} | {fmt(min(ev)) if ev else ''} | {fmt((r.get('probe') or {}).get('delta'))} | "
                 f"{fmt(pr.get('A0'))} | {fmt(pr.get('A1'))} | {fmt(trunc(rid))} | {fmt((jd.get('A0') or {}).get('fool'))} | {fmt((jd.get('A0') or {}).get('cov'))} |")
    # adherence
    L += ["", "## Adherence fix, Wharton pair-6 (success: coverage > 70, primary within 0.01 of pair_e6_4b)", "",
          "| run | A0 | A1 | trunc % | fool A0 | cov A0 | cov A1 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for rid in ("pair_e6_4b", "pair_e6_t06", "pair_e6_replay", "base4b"):
        pr, jd = prim(rid), judge(rid)
        L.append(f"| {rid} | {fmt(pr.get('A0'))} | {fmt(pr.get('A1'))} | {fmt(trunc(rid))} | {fmt((jd.get('A0') or {}).get('fool'))} | "
                 f"{fmt((jd.get('A0') or {}).get('cov'))} | {fmt((jd.get('A1') or {}).get('cov'))} |")
    # seed
    L += ["", "## Seed replication, Mansfield pair-6", "", "| arm | seed 0 | seed 1 | diff | sd of per-cell diff |", "|---|---:|---:|---:|---:|"]
    p0 = os.path.join(RUNS, "mansfield_paire6_4b", "scores.jsonl")
    p1 = os.path.join(RUNS, "mansfield_paire6s1_4b", "scores.jsonl")
    s0 = {(r["id"], r["arm"], r.get("sample")): r.get("luar_cos_source") for r in read_jsonl(p0)} if os.path.exists(p0) else {}
    s1 = {(r["id"], r["arm"], r.get("sample")): r.get("luar_cos_source") for r in read_jsonl(p1)} if os.path.exists(p1) else {}
    for arm in ("A0", "A1", "A5"):
        d = [s1[k] - s0[k] for k in s1 if k in s0 and k[1] == arm and s1[k] is not None and s0[k] is not None]
        m0 = prim("mansfield_paire6_4b").get(arm)
        m1 = prim("mansfield_paire6s1_4b").get(arm)
        L.append(f"| {arm} | {fmt(m0)} | {fmt(m1)} | {fmt(st.mean(d)) if d else ''} | {fmt(st.pstdev(d)) if len(d) > 1 else ''} |")
    # detectors
    L += ["", "## Detectors, NF4 4B observer pair (AUROC for separating generations from source; 0.5 = chance)", "",
          "| run | arm | n | binoculars | fast-detectgpt |", "|---|---|---:|---:|---:|"]
    for rid, author, anchor in DETECT_RUNS:
        sc = os.path.join(RUNS, rid, "scores.jsonl")
        if not os.path.exists(sc):
            continue
        rows = read_jsonl(sc)
        cols = [k for k in rows[0] if k.startswith(("binoculars", "fastdetectgpt"))]
        if not cols:
            L.append(f"| {rid} | | | (no detector columns) | |")
            continue
        src = [r for r in rows if r.get("group") == "source"]
        for arm in sorted({r["arm"] for r in rows if r.get("group") == "gen"}):
            gen = [r for r in rows if r.get("group") == "gen" and r["arm"] == arm]
            vals = []
            for pref in ("binoculars", "fastdetectgpt"):
                c = next((k for k in cols if k.startswith(pref)), None)
                if not c:
                    vals.append(None)
                    continue
                g = [r[c] for r in gen if r.get(c) is not None]
                s = [r[c] for r in src if r.get(c) is not None]
                # binoculars: lower = machine; fast-detectgpt: higher = machine
                vals.append(auroc(s, g) if pref == "binoculars" else auroc(g, s))
            L.append(f"| {rid} | {arm} | {len(gen)} | {fmt(vals[0])} | {fmt(vals[1])} |")
    L += ["", f"balance at eval: USD {credits_usd()}", ""]
    out = os.path.join(OUT, "REPORT.md")
    write_text(out, "\n".join(L))
    log(f"-> {out}")
    print("\n".join(L[-40:]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--eval-only", action="store_true")
    ap.add_argument("--min-credits", type=float, default=3.0)
    a = ap.parse_args()
    if a.eval_only:
        evaluate()
        return 0
    bal = credits_usd()
    log(f"balance USD {bal}; floor {a.min_credits}")
    if a.dry:
        print(__doc__)
        return 0
    if bal is not None and bal < a.min_credits:
        raise SystemExit("balance below floor")
    if not step("D0 smoke", smoke):
        log("STOP: smoke failed; nothing else runs")
        evaluate()
        return 1
    step("D1 size curve", size_curve)
    step("D2a adherence t0.6", adherence_t06)
    step("D2b adherence replay", adherence_replay)
    step("D3 seed mansfield", seed_mansfield)
    detectors()
    step("D5 eval", evaluate)
    log(f"balance USD {credits_usd()}")
    log("day complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
