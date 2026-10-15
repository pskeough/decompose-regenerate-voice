"""Assemble the overnight report (2026-09-10) from what is on disk: run inventory
and integrity, the Qwen contemporary scale table, the Qwen-versus-Ministral
overlay, adapter training probes, judge calibration lines, gate outcomes,
failures found in the logs, and the two account balances. Every section is
independent; a missing input produces a note, not a crash.

    python dr/morning_report.py --out notes/MORNING_REPORT_2026-09-10.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

DR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DR)
RUNS = os.path.join(DR, "runs")
LOGS = os.path.join(DR, "logs")
EVAL = os.path.join(os.path.dirname(DR), "eval_methodology")
PY = sys.executable

NEW_AUTHORS = ["doctorow", "watts", "link", "stross", "rucker"]
FAMILY_AUTHORS = ["chesterton", "doctorow", "patrick_v2"]
QWEN_TAGS = ["4b", "8b", "14b"]
MIN_TAGS = ["m3b", "m8b", "m14b"]
PRIVATE = {"patrick_v2", "h_private"}


def read(p):
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8-sig") if l.strip()] if os.path.exists(p) else []


def passed_briefs(author):
    return sum(1 for r in jl(os.path.join(DR, "data", author, "briefs_test.jsonl")) if r.get("passed"))


def section_inventory(authors, tags):
    L = ["| run | gens | expected | manifest | scored | judged | backup |", "|---|---:|---:|:-:|:-:|:-:|:-:|"]
    bk = os.path.join(os.path.dirname(DR), "_backup", "decompose_regenerate", "runs")
    problems = []
    for au in authors:
        n = passed_briefs(au)
        arms_base = 5 if au in PRIVATE else 6
        arms_ad = 5 if au in PRIVATE else 3
        for tag in tags:
            for kind, name, arms in (("base", f"{au}_base{tag}", arms_base), ("adapter", f"{au}_paire6_{tag}", arms_ad)):
                d = os.path.join(RUNS, name)
                if not os.path.isdir(d):
                    L.append(f"| {name} | - | {n * arms * 2} | - | - | - | - |")
                    problems.append(f"{name}: missing")
                    continue
                g = sum(1 for _ in open(os.path.join(d, "gens.jsonl"), encoding="utf-8")) if os.path.exists(os.path.join(d, "gens.jsonl")) else 0
                man = any(f.startswith("s3_manifest") for f in os.listdir(d))
                sc = os.path.exists(os.path.join(d, "scores.jsonl"))
                jd = os.path.exists(os.path.join(d, "judge_summary.json"))
                bkp = os.path.exists(os.path.join(bk, name, "gens.jsonl"))
                exp = n * arms * 2
                L.append(f"| {name} | {g} | {exp} | {'Y' if man else '-'} | {'Y' if sc else '-'} | {'Y' if jd else '-'} | {'Y' if bkp else '-'} |")
                if g != exp or not man:
                    problems.append(f"{name}: {g} of {exp} generations, manifest {man}")
                if not sc:
                    problems.append(f"{name}: not scored")
    return "\n".join(L), problems


def scale_table(authors, tags, out_name):
    out = os.path.join(RUNS, out_name)
    r = subprocess.run([PY, os.path.join(DR, "dr", "scale_eval.py"), "--authors", ",".join(authors), "--tags", ",".join(tags), "--out", out],
                       capture_output=True, text=True, cwd=DR)
    if r.returncode != 0:
        return f"(scale_eval failed: {r.stderr[-300:]})", {}
    md = read(out)
    # parse rows: | tag | base/adapter | A0 | A1 | ... | trunc | fool | cov |
    rows = {}
    author = None
    for line in md.splitlines():
        m = re.match(r"^## (\S+)", line)
        if m:
            author = m.group(1)
            continue
        m = re.match(r"^\| (\S+) \| (base|adapter) \| ([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\| ([^|]*)\|", line)
        if m and author:
            tag, kind = m.group(1), m.group(2)
            a0 = m.group(3).strip()
            trunc = m.group(9).strip()
            rows[(author, tag, kind)] = {"A0": float(a0) if a0 else None, "trunc": float(trunc) if trunc else None}
    return md, rows


def overlay(rows):
    L = ["| author | size | family | base A0 | adapter A0 | gain | adapter trunc % | probe delta | eval best |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for au in FAMILY_AUTHORS:
        for q, m in zip(QWEN_TAGS, MIN_TAGS):
            for fam, tag in (("Qwen3", q), ("Ministral 3", m)):
                b = rows.get((au, tag, "base"), {}).get("A0")
                a = rows.get((au, tag, "adapter"), {}).get("A0")
                tr = rows.get((au, tag, "adapter"), {}).get("trunc")
                rj = os.path.join(RUNS, f"train_{au}_pair_e6_{tag}", "run.json")
                pd = ev = None
                if os.path.exists(rj):
                    r = json.load(open(rj, encoding="utf-8"))
                    pd = ((r.get("probe") or {}).get("delta"))
                    hist = [h["eval_loss"] for h in r.get("history", []) if "eval_loss" in h]
                    ev = min(hist) if hist else r.get("best_eval_loss")
                f = lambda x, d=3: ("" if x is None else f"{x:.{d}f}")
                gain = "" if (a is None or b is None) else f"{a - b:+.3f}"
                L.append(f"| {au} | {q} | {fam} | {f(b)} | {f(a)} | {gain} | {f(tr, 1)} | {f(pd)} | {f(ev)} |")
    return "\n".join(L)


def judge_lines():
    md = read(os.path.join(EVAL, "results", "judge_rubric.md"))
    lines = [l for l in md.splitlines() if l.startswith("Calibration gate")]
    return "\n".join(f"- {l}" for l in lines) if lines else "(no rubric summary found)"


def gate_flags(authors, tags):
    out = []
    for p in sorted(glob.glob(os.path.join(RUNS, "cloud_state_*.json"))):
        st = json.load(open(p, encoding="utf-8"))
        name = os.path.basename(p)[len("cloud_state_"):-5]
        au = name.rsplit("_", 1)[0]
        if au not in authors:
            continue
        for s in st.get("steps", []):
            if s.get("name") in ("gate adapter generation", "gate base generation", "gate training") and not s.get("ok"):
                keys = {k: s[k] for k in ("truncated_pct", "preface_pct", "probe_delta", "eval_best") if k in s}
                out.append(f"- {name}: {s['name']} failed {keys}")
    return "\n".join(out) if out else "- no gate failures recorded in the pod state files"


def log_failures():
    out = []
    for p in sorted(glob.glob(os.path.join(LOGS, "*0909*.log"))) + sorted(glob.glob(os.path.join(LOGS, "*min*.log"))):
        txt = read(p)
        hits = [l for l in txt.splitlines() if re.search(r"FAILED|Traceback|unreachable", l)]
        if hits:
            out.append(f"- {os.path.basename(p)}: {len(hits)} lines, last: {hits[-1][:140]}")
    return "\n".join(out) if out else "- no FAILED / Traceback / unreachable lines in tonight's logs"


def balances():
    rp = subprocess.run([PY, os.path.join(DR, "cloud", "pod.py"), "balance"], capture_output=True, text=True, cwd=DR, timeout=90)
    orr = subprocess.run([PY, os.path.join(os.path.dirname(DR), "scripts", "check_credit.py")], capture_output=True, text=True, cwd=os.path.dirname(DR), timeout=90)
    pods = subprocess.run([PY, os.path.join(DR, "cloud", "pod.py"), "status"], capture_output=True, text=True, cwd=DR, timeout=90)
    return (rp.stdout.strip().splitlines() or ["?"])[-1], (orr.stdout.strip().splitlines() or ["?"])[-1], pods.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(DR, "notes", "MORNING_REPORT_2026-09-10.md"))
    a = ap.parse_args()
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    S = [f"# Overnight report, written {now}", "",
         "Everything below is read from disk by `dr/morning_report.py`. Tables are regenerated by `dr/scale_eval.py`; numbers are LUAR cosine to the source, normalised, arm A0 unless stated.", ""]

    S += ["## 1. Inventory and integrity", ""]
    inv1, prob1 = section_inventory(NEW_AUTHORS + ["cather"], QWEN_TAGS)
    S += ["### Qwen3, contemporary authors and the Cather fill-in", "", inv1, ""]
    inv2, prob2 = section_inventory(FAMILY_AUTHORS, MIN_TAGS)
    S += ["### Ministral 3, cross-family replication", "", inv2, ""]
    reps = [os.path.basename(d) for d in glob.glob(os.path.join(RUNS, "*_r2")) if "m3b" in d]
    S += [f"Replicate base runs for the family noise floor: {', '.join(reps) if reps else 'none pulled'}", ""]
    probs = prob1 + prob2
    S += ["**Problems:**", ""] + ([f"- {p}" for p in probs] if probs else ["- none"]) + [""]

    S += ["## 2. Qwen3 contemporary scale table", ""]
    md1, rows1 = scale_table(NEW_AUTHORS + ["cather"], QWEN_TAGS, "scale_table_contemporary.md")
    S += [md1.split("\n", 1)[1] if md1.startswith("#") else md1, ""]

    S += ["## 3. Cross-family overlay (Qwen3 vs Ministral 3, same briefs, same recipe)", ""]
    md2, rows2 = scale_table(FAMILY_AUTHORS, QWEN_TAGS + MIN_TAGS, "scale_table_crossfamily.md")
    S += [overlay(rows2), "",
          "Probe delta = held-out loss with the adapter on minus off (more negative = the adapter moved the model more). "
          "Ministral adapters were trained with the identical recipe and served as merged F16 weights; the Qwen-calibrated probe threshold (-0.2) was replaced for the family by 'eval improved and delta below 0' and the deltas are reported here rather than gated.", ""]
    S += ["<details><summary>Full cross-family table</summary>", "", md2.split("\n", 1)[1] if md2.startswith("#") else md2, "", "</details>", ""]

    S += ["## 4. Judges", "", "Rubric judge calibration gates (author passages vs sentence-shuffled versions, both judges):", "", judge_lines(), ""]
    S += ["## 5. Gate failures recorded on the pods", "", gate_flags(NEW_AUTHORS + ["cather"] + FAMILY_AUTHORS, QWEN_TAGS + MIN_TAGS), ""]
    S += ["## 6. Failures in tonight's logs", "", log_failures(), ""]
    try:
        rp, orr, pods = balances()
        S += ["## 7. Accounts and pods", "", f"- RunPod: {rp}", f"- OpenRouter: {orr}", f"- Pods: {pods or 'none'}", ""]
    except Exception as e:
        S += ["## 7. Accounts and pods", "", f"- balance check failed: {e!r}", ""]
    S += ["## 8. Where things are", "",
          "- Runs: `decompose_regenerate/runs/<run>/` (gens.jsonl, scores.jsonl, s3_manifest, judge files); adapters under `runs/train_<author>_pair_e6_<tag>/`.",
          "- Backups: `Voice_Style_Retune/_backup/decompose_regenerate/`.",
          "- Instrument results and gates: `eval_methodology/results/` (GATES.md, judge_rubric.md, per-measure tables).",
          "- Design notes: `notes/CROSS_FAMILY_PLAN.md`, `eval_methodology/FIDELITY_SYNTHESIS.md`; decisions in `DECISIONS.md`.", ""]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8", newline="\n").write("\n".join(S))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
