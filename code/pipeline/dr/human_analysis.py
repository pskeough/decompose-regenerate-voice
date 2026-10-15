"""Score returned answer sheets from a human 2AFC packet (dr/human_packet.py).

    python dr/human_analysis.py --packet runs/human_2afc_v1
    python dr/human_analysis.py --packet runs/human_2afc_v1 --exclude-raters 01

Reads sheets/rater_*.csv (choice A/B, confidence 1-4), joins KEY.json, writes
RESULTS.md with the pre-registered analysis in the packet README.
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import RUNS, read_json, read_jsonl, write_text  # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def binom_p(k, n):
    from scipy.stats import binomtest
    return binomtest(k, n, 0.5).pvalue


def kappa(pairs):
    """pairs: list of (a, b) binary ratings for the same item."""
    if not pairs:
        return float("nan"), float("nan")
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    pa = sum(a for a, _ in pairs) / n
    pb = sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan"), po


def holm(ps):
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    adj, run = [0.0] * m, 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * ps[i]))
        adj[i] = run
    return adj


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--packet", default=os.path.join(RUNS, "human_2afc_v1"))
    ap.add_argument("--exclude-raters", default="", help="comma-separated rater ids to drop (pilot, author)")
    a = ap.parse_args()
    key = read_json(os.path.join(a.packet, "KEY.json"))
    real_pos = {(r["rater"], r["item"]): r["real_position"] for r in key["ratings"]}
    cond_of = {i: v["condition"] for i, v in key["items"].items()}
    drop = {int(x) for x in a.exclude_raters.split(",") if x.strip()}
    rows = []
    # JSON exports from the rating page (study.html): returns/*.json, one per participant
    import json as _json
    for f in sorted(glob.glob(os.path.join(a.packet, "returns", "*.json"))):
        try:
            o = _json.load(open(f, encoding="utf-8-sig"))
        except Exception:
            continue
        k = int(o.get("packet") or 0)
        if not k or k in drop:
            continue
        for ans in o.get("answers", []):
            ch = (ans.get("choice") or "").strip().upper()[:1]
            rp = real_pos.get((k, ans.get("item")))
            if ch not in ("A", "B") or rp is None:
                continue
            rows.append({"rater": k, "item": ans["item"], "condition": cond_of[ans["item"]], "choice": ch,
                         "real_position": rp, "correct": int(ch == rp), "confidence": ans.get("confidence"),
                         "note": (ans.get("note") or "").strip(), "seconds": ans.get("seconds"),
                         "participant": o.get("participant", "")})
    for f in sorted(glob.glob(os.path.join(a.packet, "sheets", "rater_*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            if not r.get("choice"):
                continue
            k = int(r["rater"])
            if k in drop:
                continue
            ch = r["choice"].strip().upper()[:1]
            if ch not in ("A", "B"):
                continue
            rp = real_pos.get((k, r["item"]))
            if rp is None:
                continue
            conf = int(r["confidence"]) if str(r.get("confidence", "")).strip().isdigit() else None
            rows.append({"rater": k, "item": r["item"], "condition": cond_of[r["item"]], "choice": ch,
                         "real_position": rp, "correct": int(ch == rp), "confidence": conf,
                         "note": (r.get("note") or "").strip()})
    if not rows:
        raise SystemExit("no filled sheets found")
    out = [f"# Human 2AFC results ({len(rows)} ratings from {len({r['rater'] for r in rows})} raters)", ""]

    # 1. primary
    out += ["## Accuracy per condition (fooling rate = 1 - accuracy)", "",
            "| condition | n | accuracy | Wilson 95% | fooling | p vs 0.5 |", "|---|---:|---:|---|---:|---:|"]
    by_c = collections.defaultdict(list)
    for r in rows:
        by_c[r["condition"]].append(r)
    for c in key["conditions"]:
        rs = by_c.get(c, [])
        if not rs:
            continue
        k, n = sum(r["correct"] for r in rs), len(rs)
        lo, hi = wilson(k, n)
        out.append(f"| {c} | {n} | {k/n:.3f} | [{lo:.2f}, {hi:.2f}] | {1-k/n:.3f} | {binom_p(k, n):.3g} |")

    # 2. contrasts vs matching base, GEE clustered by rater
    out += ["", "## Contrasts against the matching base condition (logistic GEE, clusters = raters)", ""]
    try:
        import pandas as pd
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        df = pd.DataFrame(rows)
        pairs = [(c, "W-base") for c in ("W-e6", "W-front")] + [(c, "P-base") for c in ("P-mix",)]
        ps, lines = [], []
        for c, base in pairs:
            sub = df[df["condition"].isin([c, base])].copy()
            if sub["condition"].nunique() < 2:
                continue
            sub["x"] = (sub["condition"] == c).astype(int)
            m = smf.gee("correct ~ x", groups="rater", data=sub, family=sm.families.Binomial(),
                        cov_struct=sm.cov_struct.Exchangeable()).fit()
            p = float(m.pvalues["x"])
            ps.append(p)
            lines.append((c, base, float(m.params["x"]), p))
        adj = holm(ps) if ps else []
        out += ["| condition | vs | log-odds diff | p | Holm p |", "|---|---|---:|---:|---:|"]
        for (c, base, b, p), q in zip(lines, adj):
            out.append(f"| {c} | {base} | {b:+.2f} | {p:.3g} | {q:.3g} |")
    except Exception as e:
        out.append(f"GEE unavailable: {e!r}")

    # 3. position
    out += ["", "## Position check (accuracy when the real passage is A vs B)", "", "| condition | real=A | real=B |", "|---|---:|---:|"]
    for c in key["conditions"]:
        rs = by_c.get(c, [])
        if not rs:
            continue
        A = [r["correct"] for r in rs if r["real_position"] == "A"]
        B = [r["correct"] for r in rs if r["real_position"] == "B"]
        out.append(f"| {c} | {sum(A)/len(A):.2f} (n {len(A)}) | {sum(B)/len(B):.2f} (n {len(B)}) |" if A and B else f"| {c} | - | - |")

    # 4. reliability
    by_item = collections.defaultdict(list)
    for r in rows:
        by_item[r["item"]].append(r["correct"])
    pairs = [(v[0], v[1]) for v in by_item.values() if len(v) >= 2]
    kp, po = kappa(pairs)
    out += ["", f"## Reliability: {len(pairs)} double-rated items, Cohen's kappa {kp:.2f}, raw agreement {po:.2f}", ""]

    # 5. confidence
    conf = [r for r in rows if r["confidence"] is not None]
    if conf:
        mc = lambda ok: sum(r["confidence"] for r in conf if r["correct"] == ok) / max(1, sum(1 for r in conf if r["correct"] == ok))
        out += ["## Confidence", "", f"mean confidence when correct {mc(1):.2f}, when wrong {mc(0):.2f}", ""]
        out += ["| condition | confidence-weighted accuracy |", "|---|---:|"]
        for c in key["conditions"]:
            rs = [r for r in conf if r["condition"] == c]
            if rs:
                w = sum(r["confidence"] for r in rs)
                out.append(f"| {c} | {sum(r['confidence']*r['correct'] for r in rs)/w:.3f} |")

    # 6. LLM-judge calibration on the same items
    out += ["", "## LLM judges on the same items (fooling rate, vs_source)", "", "| condition | human | gemini | minimax |", "|---|---:|---:|---:|"]
    for c, v in key["conditions"].items():
        rs = by_c.get(c, [])
        if not rs:
            continue
        human = 1 - sum(r["correct"] for r in rs) / len(rs)
        jp = os.path.join(RUNS, v["run"], "judge.jsonl")
        items_c = {key["items"][r["item"]]["passage_id"] for r in rs}
        g = m = None
        if os.path.exists(jp):
            jr = [j for j in read_jsonl(jp) if j.get("comparison") == "vs_source" and j.get("arm") == v["arm"]
                  and j.get("sample") == 0 and j.get("id") in items_c and "picked_gen" in j]
            for name, tag in (("gemini", "gemini"), ("minimax", "minimax")):
                sel = [j["picked_gen"] for j in jr if tag in j["judge"]]
                if sel:
                    if name == "gemini":
                        g = sum(sel) / len(sel)
                    else:
                        m = sum(sel) / len(sel)
        out.append(f"| {c} | {human:.3f} | {g if g is None else f'{g:.3f}'} | {m if m is None else f'{m:.3f}'} |")

    notes = [r for r in rows if r["note"]]
    if notes:
        out += ["", f"## Free-text notes ({len(notes)})", ""]
        for r in notes:
            out.append(f"- {r['condition']} / {r['item']} / {'correct' if r['correct'] else 'fooled'} (conf {r['confidence']}): {r['note']}")
    p = os.path.join(a.packet, "RESULTS.md")
    write_text(p, "\n".join(out) + "\n")
    print("\n".join(out[:20]))
    print(f"-> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
