"""Night of 2026-09-05: rescore + four authors + within-period attribution.

    N0  smoke: 5 briefs for chesterton, one normalised rescore, 10 judge calls
    N1  API prep for the four authors, in parallel (briefs, guide, retrieval)
        while the GPU rescores the fifteen existing runs on normalised text
    N2  key re-judges on normalised text (API, background, sample 0 only)
    N3  run_author for the four authors (GPU serial; judges in background)
    N4  cross_attribution over every author with an adapter
    N5  summary to runs/night_0905/REPORT.md

Balance is checked at the start and before N3. Each step is skipped when
its outputs exist. Log: logs/night_0905.log.

    python dr/night_0905.py
    python dr/night_0905.py --skip-smoke
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DR, LOGS, RUNS, author_dir, credits_usd, log, read_json, read_jsonl, write_json, write_text  # noqa: E402

PY = sys.executable
AUTHORS = ["chesterton", "mansfield", "chopin", "sui_sin_far"]
OUT = os.path.join(RUNS, "night_0905")
os.makedirs(OUT, exist_ok=True)
STATE = os.path.join(OUT, "state.json")
state = read_json(STATE) if os.path.exists(STATE) else {"steps": []}


def note(**kw):
    kw["ts"] = dt.datetime.now().strftime("%m-%d %H:%M")
    state["steps"].append(kw)
    write_json(STATE, state)
    log(f"[night] {kw}")


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


def prep_cmds(au):
    """The API-side prep for one author as a list of argv lists (no shell)."""
    d = author_dir(au)
    cmds = []
    if not os.path.exists(os.path.join(d, "split.json")):
        cmds.append([PY, "dr/s0_split.py", "--author", au])
    for split in ("test", "train"):
        if not os.path.exists(os.path.join(d, f"briefs_{split}.jsonl")):
            cmds.append([PY, "dr/s1_decompose.py", "--author", au, "--split", split, "--workers", "6"])
            cmds.append([PY, "dr/s1_decompose.py", "--author", au, "--split", split, "--workers", "6", "--recover", "2"])
    if not os.path.exists(os.path.join(d, "guide.md")):
        cmds.append([PY, "dr/s2_conditioning.py", "--author", au, "--guide", "--quant"])
    if not os.path.exists(os.path.join(d, "retrieval_test.jsonl")):
        cmds.append([PY, "dr/s2_conditioning.py", "--author", au, "--retrieval", "--briefs", "briefs_test.jsonl"])
    return cmds


def prep_author(au):
    """Run one author's prep commands in order; returns the first failing rc or 0."""
    for cmd in prep_cmds(au):
        try:
            run(cmd, f"night_0905_prep_{au}.log")
        except Exception as e:
            log(f"prep {au} failed: {e}")
            return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-smoke", action="store_true")
    ap.add_argument("--authors", default=",".join(AUTHORS))
    a = ap.parse_args()
    authors = [x for x in a.authors.split(",") if x]
    bal = credits_usd()
    log(f"balance USD {bal}")
    if bal is not None and bal < 8:
        raise SystemExit("need about USD 8 for the night; top up")

    # N0 smoke
    def smoke():
        au = authors[0]
        run([PY, "dr/s0_split.py", "--author", au], "night_0905_smoke.log")
        run([PY, "dr/s1_decompose.py", "--author", au, "--split", "test", "--limit", "5", "--workers", "5"], "night_0905_smoke.log")
        rows = read_jsonl(os.path.join(author_dir(au), "briefs_test_limit5.jsonl"))
        passed = sum(1 for r in rows if r.get("passed"))
        note(name="smoke briefs", ok=passed >= 3, passed=passed, of=len(rows))
        run([PY, "dr/s5_score.py", "--run", "pair_s1_4b", "--author", "wharton", "--anchor-run", "base4b"], "night_0905_smoke.log")
        m = read_json(os.path.join(RUNS, "pair_s1_4b", "s5_manifest.json"))
        note(name="smoke rescore", ok=m.get("normalised") is True, normalised=m.get("normalised"))
        run([PY, "dr/s5b_judge.py", "--run", "pair_s1_4b", "--author", "wharton", "--limit", "5", "--no-coverage", "--suffix", "_smoke"], "night_0905_smoke.log")
        jr = read_jsonl(os.path.join(RUNS, "pair_s1_4b", "judge_smoke.jsonl"))
        okj = sum(1 for r in jr if "picked_gen" in r)
        note(name="smoke judges", ok=okj >= 8, verdicts=okj, of=len(jr))
        return passed >= 3 and m.get("normalised") is True and okj >= 8
    if not a.skip_smoke and not step("N0 smoke", smoke):
        raise SystemExit("smoke failed; see logs/night_0905_smoke.log")

    # N1 prep (API, parallel) alongside rescore scores (GPU)
    def n1():
        from concurrent.futures import ThreadPoolExecutor
        ex = ThreadPoolExecutor(max_workers=len(authors))
        futs = {au: ex.submit(prep_author, au) for au in authors}
        run([PY, "dr/rescore_normalised.py", "--no-judge"], "night_0905_rescore.log")
        for au, f in futs.items():
            rc = f.result()
            note(name=f"prep {au}", ok=rc == 0, rc=rc)
        ex.shutdown()
        return True
    step("N1 prep + rescore scores", n1)

    # N2 key re-judges (background)
    def n2():
        run([PY, "dr/rescore_normalised.py", "--only", "base4b,pair_e6_4b,patrick_base4b,patrick_mix4b"], "night_0905_rejudge.log", background=True)
        return True
    step("N2 key re-judges (background)", n2)

    # N3 authors
    bal = credits_usd()
    log(f"balance before authors USD {bal}")
    step("N3 run_author", lambda: run([PY, "dr/run_author.py", "--authors", ",".join(authors), "--recipe", "pair", "--epochs", "6",
                                        "--adapter-arms", "A0,A1,A5", "--min-credits", "3"], "night_0905_authors.log"))

    # N4 attribution
    step("N4 cross attribution", lambda: run([PY, "dr/cross_attribution.py"], "night_0905_attrib.log"))

    # N5 report
    lines = [f"# Night 2026-09-05 report ({dt.datetime.now():%Y-%m-%d %H:%M})", "", "| step | ok | min | note |", "|---|---|---:|---|"]
    for s in state["steps"]:
        lines.append(f"| {s['name']} | {'yes' if s.get('ok') else 'NO'} | {s.get('minutes', '')} | {s.get('error') or ''} |")
    summ = os.path.join(RUNS, "author_runs", "summary.json")
    if os.path.exists(summ):
        lines += ["", "## Per-author primary (LUAR to source, normalised)", "", "```", open(summ, encoding="utf-8").read(), "```"]
    attr = os.path.join(RUNS, "cross_attribution.md")
    if os.path.exists(attr):
        lines += ["", open(attr, encoding="utf-8").read()]
    lines += ["", f"balance at end: USD {credits_usd()}"]
    write_text(os.path.join(OUT, "REPORT.md"), "\n".join(lines) + "\n")
    log("night complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
