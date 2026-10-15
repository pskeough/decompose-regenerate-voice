"""S5b: API judges (METHODS 8.4, 8.6).

For every generation, two 2AFC comparisons per judge:
    vs_source   the generation against the real passage; the judge sees a REF
                passage by the author as the reference. P(judge picks the
                generation) is the fooling rate; 0.5 means indistinguishable.
    vs_A0       the generation against the A0 output for the same brief and
                sample. P(picks the generation) is the relative gain.
Candidate order is randomised per call from a seed on (id, arm, sample, judge)
and recorded. The first judge also scores brief coverage (0-100).

Judges are instruments, not the criterion; their known lean toward machine
prose is why the fooling rate sits fourth in the outcome hierarchy.

    python dr/s5b_judge.py --run base4b
    python dr/s5b_judge.py --run base4b --limit 20      # smoke
"""
from __future__ import annotations

import argparse
import collections
import os
import random
import re
import statistics as st
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import RUNS, Manifest, api_call, author_dir, log, normalise_punct, read_jsonl, write_json, write_jsonl  # noqa: E402
from dr.prompts import Prompts  # noqa: E402

_AB = re.compile(r"\b([AB])\b")
_INT = re.compile(r"\d{1,3}")


def ask_2afc(P, judge, reference, gen_text, other_text, seed):
    R = random.Random(seed)
    gen_is_a = R.random() < 0.5
    ca, cb = (gen_text, other_text) if gen_is_a else (other_text, gen_text)
    system, user = P.judge_2afc(reference, ca, cb)
    text, meta = api_call(judge, system, user, max_tokens=5, temperature=0.0, tag="judge2afc")
    if text is None:
        return None, meta
    m = _AB.search(text.strip().upper())
    if not m:
        return None, {"error": f"unparsed: {text[:40]}"}
    picked_gen = (m.group(1) == "A") == gen_is_a
    return {"picked_gen": int(picked_gen), "gen_pos": "A" if gen_is_a else "B", "raw": text.strip()[:10],
            "usd": meta.get("usd", 0.0)}, meta


def ask_coverage(P, judge, brief, passage):
    system, user = P.judge_coverage(brief, passage)
    text, meta = api_call(judge, system, user, max_tokens=8, temperature=0.0, tag="coverage")
    if text is None:
        return None
    m = _INT.search(text)
    return int(m.group(0)) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--judges", default=",".join(config.JUDGES))
    ap.add_argument("--limit", type=int, default=0, help="first N generations")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--no-coverage", action="store_true")
    ap.add_argument("--coverage-only", action="store_true", help="skip the 2AFC calls")
    ap.add_argument("--coverage-judge", default="", help="override the coverage judge (default judges[0])")
    ap.add_argument("--only-arms", default="", help="comma-separated arms to judge")
    ap.add_argument("--only-samples", default="", help="comma-separated sample indices to judge (e.g. 0 halves the bill)")
    ap.add_argument("--suffix", default="", help="write to judge<suffix>.jsonl / coverage<suffix>.jsonl")
    ap.add_argument("--normalise", action="store_true", help="apply normalise_punct (default per config.NORMALISE_TEXT)")
    ap.add_argument("--raw", action="store_true", help="judge raw text")
    a = ap.parse_args()
    d = author_dir(a.author)
    rd = os.path.join(RUNS, a.run)
    P = Prompts()
    judges = [j.strip() for j in a.judges.split(",") if j.strip()]
    man = Manifest(os.path.join(rd, "s5b_manifest.json"), "s5b_judge")
    gens = read_jsonl(os.path.join(rd, "gens.jsonl"))
    man.input("gens", os.path.join(rd, "gens.jsonl"))
    test = {r["id"]: r for r in read_jsonl(os.path.join(d, "test.jsonl"))}
    ref = read_jsonl(os.path.join(d, "ref.jsonl"))
    if (a.normalise or config.NORMALISE_TEXT) and not a.raw:
        for g in gens:
            g["text"] = normalise_punct(g["text"])
        for r in test.values():
            r["text"] = normalise_punct(r["text"])
        for r in ref:
            r["text"] = normalise_punct(r["text"])
    briefs = {r["id"]: r for r in read_jsonl(os.path.join(d, "briefs_test.jsonl"))}
    a0 = {(g["id"], g["sample"]): g for g in gens if g["arm"] == "A0"}
    if a.only_arms:
        keep = {x.strip() for x in a.only_arms.split(",")}
        gens = [g for g in gens if g["arm"] in keep]
    if a.only_samples:
        ks = {int(x) for x in a.only_samples.split(",") if x.strip()}
        gens = [g for g in gens if g["sample"] in ks]
    if a.limit:
        gens = gens[: a.limit]
    if a.coverage_only:
        judges = judges[:0]   # no 2AFC jobs; coverage still runs below
    cov_judge = a.coverage_judge or (judges[0] if judges else config.JUDGES[0])
    out_path = os.path.join(rd, f"judge{a.suffix}.jsonl")
    done = set()
    if os.path.exists(out_path):
        # only successful verdicts count as done; error rows (API outage,
        # exhausted credits on 2026-09-04) are retried on the next run
        done = {(r["id"], r["arm"], r["sample"], r["judge"], r["comparison"])
                for r in read_jsonl(out_path) if "picked_gen" in r}

    jobs = []
    for g in gens:
        R = random.Random(f"{config.SEED}|{g['id']}|{g['arm']}|{g['sample']}")
        reference = R.choice(ref)["text"]
        for j in judges:
            for comp in ("vs_source", "vs_A0"):
                if (g["id"], g["arm"], g["sample"], j, comp) in done:
                    continue
                if comp == "vs_source":
                    other = test[g["id"]]["text"]
                else:
                    if g["arm"] == "A0":
                        continue
                    o = a0.get((g["id"], g["sample"]))
                    if not o:
                        continue
                    other = o["text"]
                seed = f"{config.SEED}|{g['id']}|{g['arm']}|{g['sample']}|{j}|{comp}"
                jobs.append((g, j, comp, reference, other, seed))
    log(f"{len(jobs)} judge calls to make ({len(done)} on disk)")

    def run(job):
        g, j, comp, reference, other, seed = job
        res, meta = ask_2afc(P, j, reference, g["text"], other, seed)
        row = {"id": g["id"], "arm": g["arm"], "sample": g["sample"], "judge": j, "comparison": comp}
        if res is None:
            row["error"] = meta.get("error")
        else:
            row.update(res)
        return row

    rows = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(run, jb) for jb in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            rows.append(f.result())
            if i % 50 == 0 or i == len(futs):
                log(f"  {i}/{len(futs)}")
    if rows:
        write_jsonl(out_path, rows, mode="a")

    cov_path = os.path.join(rd, f"coverage{a.suffix}.jsonl")
    if not a.no_coverage:
        cdone = set()
        if os.path.exists(cov_path):
            cdone = {(r["id"], r["arm"], r["sample"]) for r in read_jsonl(cov_path) if r.get("coverage") is not None}
        cjobs = [g for g in gens if (g["id"], g["arm"], g["sample"]) not in cdone and g["id"] in briefs]
        log(f"{len(cjobs)} coverage calls with {cov_judge}")

        def runc(g):
            return {"id": g["id"], "arm": g["arm"], "sample": g["sample"], "judge": cov_judge,
                    "coverage": ask_coverage(P, cov_judge, briefs[g["id"]]["brief"], g["text"])}

        crows = []
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for f in as_completed([ex.submit(runc, g) for g in cjobs]):
                crows.append(f.result())
        write_jsonl(cov_path, crows, mode="a")

    # summary
    allrows = read_jsonl(out_path) if os.path.exists(out_path) else []
    summ = collections.defaultdict(dict)
    for j in judges:
        for comp in ("vs_source", "vs_A0"):
            by_arm = collections.defaultdict(list)
            for r in allrows:
                if r["judge"] == j and r["comparison"] == comp and "picked_gen" in r:
                    by_arm[r["arm"]].append(r["picked_gen"])
            for arm, v in by_arm.items():
                summ[arm][f"{comp}|{j.split('/')[-1]}"] = round(st.mean(v), 3)
    if len(judges) == 2:
        pairs = collections.defaultdict(dict)
        for r in allrows:
            if "picked_gen" in r:
                pairs[(r["id"], r["arm"], r["sample"], r["comparison"])][r["judge"]] = r["picked_gen"]
        both = [p for p in pairs.values() if len(p) == 2]
        agree = st.mean([int(list(p.values())[0] == list(p.values())[1]) for p in both]) if both else None
        summ["_agreement"] = {"n": len(both), "agree": round(agree, 3) if agree is not None else None}
    if os.path.exists(cov_path):
        by_arm = collections.defaultdict(list)
        for r in read_jsonl(cov_path):
            if r.get("coverage") is not None:
                by_arm[r["arm"]].append(r["coverage"])
        for arm, v in by_arm.items():
            summ[arm]["coverage"] = round(st.mean(v), 1)
    write_json(os.path.join(rd, f"judge_summary{a.suffix}.json"), dict(summ))
    if os.path.exists(out_path):
        man.output("judge", out_path)
    man.save(summary=dict(summ), judges=judges)
    for k, v in summ.items():
        log(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
