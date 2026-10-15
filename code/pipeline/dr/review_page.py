"""Build the review page: where the experiment stands, the Gate 2 materials,
per-condition scores, and real Wharton passages beside their brief and every
model's regeneration (base, frontier, and each adapter).

    python dr/review_page.py --runs base4b,base4b_frontier,pair4b,mix4b,raw4b --n 3 --out runs/review.html
"""
from __future__ import annotations

import argparse
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import RUNS, author_dir, read_jsonl, read_text  # noqa: E402

ARM_LABEL = {"A0": "bare: brief only", "A1": "named: brief + “as Edith Wharton”",
             "A2": "retrieval: brief + 3 of her passages", "A3": "guide: brief + written style guide",
             "A4": "numbers: brief + statistical targets", "A5": "full stack: passages + guide + numbers",
             "F0": "brief only", "F5": "full stack"}
RUN_LABEL = {"base4b": "4B base", "base4b_frontier": "frontier API model", "pair4b": "4B + pair adapter",
             "mix4b": "4B + mix adapter", "raw4b": "4B + raw adapter"}
RUN_SHORT = {"base4b": "base", "base4b_frontier": "frontier", "pair4b": "pair", "mix4b": "mix", "raw4b": "raw"}
ORDER = ["A0", "A1", "A2", "A3", "A4", "A5", "F0", "F5"]


def paras(text):
    return "".join(f"<p>{html.escape(p.strip())}</p>" for p in text.split("\n\n") if p.strip())


def brief_html(text):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if ":" in s and s.split(":")[0].isupper():
            head, _, rest = s.partition(":")
            out.append(f"<p><span class=\"bh\">{html.escape(head)}</span>{html.escape(rest)}</p>")
        else:
            out.append(f"<p>{html.escape(s)}</p>")
    return "".join(out)


def cell(v, nd=3):
    return "–" if v is None else f"{v:.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--runs", default="base4b,base4b_frontier,pair4b,mix4b,raw4b")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--out", default=os.path.join(RUNS, "review.html"))
    a = ap.parse_args()
    d = author_dir(a.author)
    test = {r["id"]: r for r in read_jsonl(os.path.join(d, "test.jsonl"))}
    briefs = {r["id"]: r for r in read_jsonl(os.path.join(d, "briefs_test.jsonl")) if r.get("passed")}
    split = json.load(open(os.path.join(d, "split.json"), encoding="utf-8"))
    guide = read_text(os.path.join(d, "guide.md"))
    quant = read_text(os.path.join(d, "quant_block.txt"))
    runs = [r for r in a.runs.split(",") if r and os.path.exists(os.path.join(RUNS, r, "gens.jsonl"))]
    gens, scores, summary = {}, {}, {}
    for run in runs:
        for g in read_jsonl(os.path.join(RUNS, run, "gens.jsonl")):
            if g["sample"] == 0:
                gens.setdefault(g["id"], {})[(run, g["arm"])] = g
        sp = os.path.join(RUNS, run, "scores.jsonl")
        if os.path.exists(sp):
            for s in read_jsonl(sp):
                if s["group"] == "gen":
                    scores[(run, s["id"], s["arm"], s["sample"])] = s
        sm = os.path.join(RUNS, run, "scores_summary.json")
        if os.path.exists(sm):
            for k, v in json.load(open(sm, encoding="utf-8")).items():
                if k in ARM_LABEL:
                    summary[(run, k)] = dict(v)
                elif k in ("source", "ref") and ("_", k) not in summary:
                    summary[("_", k)] = v
        jm = os.path.join(RUNS, run, "judge_summary.json")
        if os.path.exists(jm):
            for k, v in json.load(open(jm, encoding="utf-8")).items():
                if k in ARM_LABEL and (run, k) in summary:
                    summary[(run, k)]["coverage"] = v.get("coverage")
                    fools = [val for kk, val in v.items() if kk.startswith("vs_source|")]
                    summary[(run, k)]["fool"] = max(fools) if fools else None
    ranked = sorted(gens, key=lambda pid: (-len(gens[pid]), pid))
    chosen = [pid for pid in ranked if pid in briefs][: a.n]
    n_gen = sum(len(v) for v in gens.values())
    counts = split["counts"]
    have_adapters = any(r in runs for r in ("pair4b", "mix4b", "raw4b"))

    css = """
:root{--bg:#f4f5f2;--ink:#1c1f1e;--muted:#5c6360;--rule:#d6d9d3;--card:#fbfbf9;--real:#7a2e2e;--real-bg:#f6ecea;
--model:#33414a;--model-bg:#eef1f2;--chip:#e6e9e4;--now:#1f5f3f;--now-bg:#e3efe7;--link:#2b4c7e;--adapt:#3f5a86}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15181a;--ink:#e6e4de;--muted:#9aa19c;--rule:#2c3235;--card:#1c2023;
--real:#d08a82;--real-bg:#2a1d1c;--model:#b9c4cc;--model-bg:#1e262b;--chip:#262c30;--now:#8fcf9f;--now-bg:#1a2b21;--link:#8fb3e8;--adapt:#9db4de}}
:root[data-theme="dark"]{--bg:#15181a;--ink:#e6e4de;--muted:#9aa19c;--rule:#2c3235;--card:#1c2023;
--real:#d08a82;--real-bg:#2a1d1c;--model:#b9c4cc;--model-bg:#1e262b;--chip:#262c30;--now:#8fcf9f;--now-bg:#1a2b21;--link:#8fb3e8;--adapt:#9db4de}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Source Serif 4",Georgia,"Times New Roman",serif;font-size:17px;line-height:1.55}
main{max-width:1180px;margin:0 auto;padding:32px 24px 80px}
h1{font-size:34px;line-height:1.15;margin:0 0 6px;font-weight:600;text-wrap:balance}
h2{font-size:22px;margin:40px 0 12px;font-weight:600;text-wrap:balance}
h3{font-size:18px;margin:0;font-weight:600}
.mono{font-family:"IBM Plex Mono",Consolas,monospace;font-size:13px;letter-spacing:.02em}
.sub{color:var(--muted);margin:0 0 24px}
.stages{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:12px 0 18px}
.stage{border:1px solid var(--rule);border-radius:6px;padding:10px 12px;background:var(--card)}
.stage .k{font-family:"IBM Plex Mono",Consolas,monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.stage.now{border-color:var(--now);background:var(--now-bg)}
.stage.now .k{color:var(--now)}
.stage p{margin:4px 0 0;font-size:15px;line-height:1.4}
.plain{max-width:72ch}
.plain p{margin:0 0 12px}
details{border:1px solid var(--rule);border-radius:6px;background:var(--card);padding:10px 16px;margin:10px 0}
summary{cursor:pointer;font-weight:600}
details .body{max-width:72ch;padding:8px 0 4px}
details .body p{margin:0 0 10px}
.passage{border:1px solid var(--rule);border-radius:8px;background:var(--card);margin:26px 0;overflow:hidden}
.phead{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 18px;padding:14px 18px;border-bottom:1px solid var(--rule)}
.phead .meta{color:var(--muted);font-size:14px}
.cols{display:grid;grid-template-columns:minmax(260px,320px) 1fr 1fr;gap:0}
.col{padding:16px 18px;min-width:0}
.col+.col{border-left:1px solid var(--rule)}
.label{font-family:"IBM Plex Mono",Consolas,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;margin:0 0 10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.label.real{color:var(--real)}
.label.model{color:var(--model)}
.brief p{font-size:14.5px;line-height:1.45;margin:0 0 6px;color:var(--ink)}
.bh{font-family:"IBM Plex Mono",Consolas,monospace;font-size:11.5px;letter-spacing:.06em;color:var(--muted);margin-right:6px}
.prose p{margin:0 0 .85em;font-size:16px;line-height:1.55}
.real .prose{border-left:3px solid var(--real);padding-left:14px}
.tabgroup{margin:0 0 8px}
.tabgroup .g{font-family:"IBM Plex Mono",Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:6px 0 4px}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 4px}
.tab{font-family:"IBM Plex Mono",Consolas,monospace;font-size:12px;letter-spacing:.03em;border:1px solid var(--rule);background:var(--chip);color:var(--ink);border-radius:4px;padding:5px 9px;cursor:pointer}
.tab[aria-selected="true"]{background:var(--model);color:var(--bg);border-color:var(--model)}
.tab.adapt[aria-selected="true"]{background:var(--adapt);border-color:var(--adapt)}
.tab:focus-visible{outline:2px solid var(--link);outline-offset:2px}
.panel[hidden]{display:none}
.stat{font-family:"IBM Plex Mono",Consolas,monospace;font-size:12px;color:var(--muted);margin:0 0 10px}
.flag{background:var(--real-bg);color:var(--real);padding:1px 6px;border-radius:3px}
table{border-collapse:collapse;font-size:15px}
td,th{padding:6px 12px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top;font-variant-numeric:tabular-nums}
th{font-family:"IBM Plex Mono",Consolas,monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500}
tr.hdr td{font-family:"IBM Plex Mono",Consolas,monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding-top:14px}
.scroll{overflow-x:auto}
@media (max-width:900px){.cols{grid-template-columns:1fr}.col+.col{border-left:0;border-top:1px solid var(--rule)}}
@media (prefers-reduced-motion:no-preference){.tab{transition:background .12s}}
"""
    stages = [
        ("Gate 0", "done", "Design agreed", "Wharton first. Qwen3-4B on llama.cpp. Six ways of prompting, three ways of training."),
        ("Gate 1", "done", "Briefs", "An API model rewrote each test passage as plot only. 44 of 50 passed the leakage checks."),
        ("Gate 2", "done", "Her materials", "Three example passages, a written style guide, and a block of numbers about her sentences. Below."),
        ("Gate 3", "done", "Base run", "The 4B model rewrote each brief six ways; a frontier API model did the same. Scored and judged."),
        ("Gate 4", "done" if have_adapters else "now", "Train adapters", "Three LoRA recipes on her 169 training passages: pair, mix, raw."),
        ("Gate 5", "now" if have_adapters else "next", "Adapters vs prompts", f"Same six prompts with each adapter. {n_gen} first-sample outputs on this page."),
        ("Gate 6", "later", "More authors", "Cather next, then your own writing."),
    ]
    st_html = "".join(
        f"<div class=\"stage {cls}\"><div class=\"k\">{k} · {cls}</div>"
        f"<h3>{html.escape(t)}</h3><p>{html.escape(p)}</p></div>" for k, cls, t, p in stages)

    plain = f"""
<p>The question, in one line: give a small local model the <em>plot</em> of a passage and nothing else, then tell it about the author in different ways, and measure how close each way gets to what she actually wrote. Then train a small adapter on her books and ask the same question again.</p>
<p>Wharton's books were cut into three piles: <strong>{counts['test']} test passages</strong> (the ones we try to recreate), <strong>{counts['ref']} reference passages</strong> (her prose to compare against, never shown to any model), and <strong>{counts['train_fit'] + counts['train_val']} training passages</strong> (what the adapters learned from, and where the example passages and the style guide come from). Nothing crosses between piles.</p>
<p>Each test passage was turned into a <strong>brief</strong>: setting, who is present, point of view, length, the events in order, what the reader learns. No sentences from the original, no words about how it is written. That is what every model is handed.</p>
<p>The conditions: the 4B model with six prompts (nothing, her name, three of her passages, a written guide, a block of numbers, all three), a frontier API model with two of those prompts, and the 4B model with each of three adapters under the same six prompts. Two samples per condition. Every output is scored against the real passage.</p>
"""

    # ---- scores table grouped by model
    score_section = ""
    if summary:
        rows_html = []
        for run in runs:
            arms_in = [x for x in ORDER if (run, x) in summary]
            if not arms_in:
                continue
            rows_html.append(f"<tr class=\"hdr\"><td colspan=\"9\">{html.escape(RUN_LABEL.get(run, run))}</td></tr>")
            for arm in arms_in:
                s = summary[(run, arm)]
                rows_html.append(f"<tr><td class=\"mono\">{arm}</td><td>{html.escape(ARM_LABEL[arm])}</td>"
                                 f"<td>{s.get('n', '')}</td><td>{cell(s.get('luar_cos_source'))}</td>"
                                 f"<td>{cell(s.get('geo_index'), 2)}</td><td>{cell(s.get('luar_attrib'), 2)}</td>"
                                 f"<td>{cell(s.get('coverage'), 0)}</td><td>{cell(s.get('fool'), 2)}</td>"
                                 f"<td>{cell(s.get('shown_dist'), 2)}</td><td>{cell(s.get('memo_flag'), 2)}</td></tr>")
        rows_html.append("<tr class=\"hdr\"><td colspan=\"10\">The author herself</td></tr>")
        for k, name in (("source", "her test passages, scored the same way"), ("ref", "her reference passages (leave-one-out)")):
            if ("_", k) in summary:
                s = summary[("_", k)]
                rows_html.append(f"<tr><td class=\"mono\">{k}</td><td>{name}</td><td></td><td>–</td>"
                                 f"<td>{cell(s.get('geo_index'), 2)}</td><td>{cell(s.get('luar_attrib'), 2)}</td>"
                                 f"<td></td><td></td><td></td><td></td></tr>")
        score_section = f"""
<h2>Scores per condition</h2>
<p class="plain">Means over every generation scored. <strong>LUAR to source</strong> is the primary outcome: cosine between the rewrite and the real passage on an authorship embedding; higher is closer to her. <strong>Geometry</strong> is where the rewrite sits between the bare 4B (0) and her reference prose (1) on twelve style features no model was shown. <strong>Attrib</strong> is how often the nearest of fourteen authors' centroids is her. <strong>Coverage</strong> is an API judge's 0–100 score for how many of the brief's events the rewrite contains, in order: the cost side, since a rewrite that tells a different story is not a regeneration. <strong>Fooled</strong> is the higher of two judges' rates of picking the rewrite over her real passage; 0.5 would mean indistinguishable. <strong>Compliance</strong> is distance from the numbers block in standard deviations. Paired tests and CIs are in <code>RESULTS.md</code> per run.</p>
<div class="scroll"><table><tr><th>arm</th><th>condition</th><th>n</th><th>LUAR to source</th><th>geometry</th><th>attrib</th><th>coverage</th><th>fooled</th><th>compliance</th><th>memorised</th></tr>{''.join(rows_html)}</table></div>
"""

    # ---- passages
    passages_html = []
    for pid in chosen:
        src = test[pid]
        b = briefs[pid]
        g = gens.get(pid, {})
        groups_html, panels = [], []
        first = True
        for run in runs:
            arms_in = [x for x in ORDER if (run, x) in g]
            if not arms_in:
                continue
            tabs = []
            for arm in arms_in:
                row = g[(run, arm)]
                tid = f"{pid}-{RUN_SHORT.get(run, run)}-{arm}"
                flags = " ".join(f"<span class=\"flag\">{html.escape(f)}</span>" for f in row.get("flags", []))
                sc = scores.get((run, pid, arm, 0))
                sc_html = ""
                if sc:
                    bits = []
                    if sc.get("luar_cos_source") is not None:
                        bits.append(f"LUAR to source {sc['luar_cos_source']:.3f}")
                    if sc.get("geo_index") is not None:
                        bits.append(f"geometry {sc['geo_index']:.2f}")
                    if sc.get("memo_flag"):
                        bits.append("<span class=\"flag\">memorised</span>")
                    sc_html = " · " + " · ".join(bits)
                cls = "tab adapt" if run in ("pair4b", "mix4b", "raw4b") else "tab"
                tabs.append(f"<button class=\"{cls}\" role=\"tab\" aria-selected=\"{'true' if first else 'false'}\" data-t=\"{tid}\">{RUN_SHORT.get(run, run)}·{arm}</button>")
                panels.append(f"<div class=\"panel\" id=\"{tid}\" role=\"tabpanel\"{'' if first else ' hidden'}>"
                              f"<p class=\"label model\">{html.escape(RUN_LABEL.get(run, run))} · {arm} · {html.escape(ARM_LABEL[arm])}</p>"
                              f"<p class=\"stat\">{row['n_words']} words · {row['len_ratio']:.2f} of target{sc_html} {flags}</p>"
                              f"<div class=\"prose\">{paras(row['text'])}</div></div>")
                first = False
            groups_html.append(f"<div class=\"tabgroup\"><div class=\"g\">{html.escape(RUN_LABEL.get(run, run))}</div><div class=\"tabs\" role=\"tablist\">{''.join(tabs)}</div></div>")
        passages_html.append(f"""
<section class="passage">
  <div class="phead"><h3>{html.escape(src['work'])}</h3><span class="meta mono">{html.escape(pid)} · {src['words']} words · brief {b['stats']['brief_words']} words ({b['stats']['len_ratio']:.2f} of source) · {len(g)} conditions in</span></div>
  <div class="cols">
    <div class="col brief"><p class="label">The brief every model was given</p>{brief_html(b['brief'])}</div>
    <div class="col real"><p class="label real">Wharton · the real passage</p><div class="prose">{paras(src['text'])}</div></div>
    <div class="col tabcol">{''.join(groups_html)}{''.join(panels)}</div>
  </div>
</section>""")

    arms_table = "".join(f"<tr><td class=\"mono\">{k}</td><td>{html.escape(v)}</td></tr>" for k, v in ARM_LABEL.items() if k.startswith("A"))
    page = f"""<title>Wharton Regeneration Review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}</style>
<main>
<h1>Where the Wharton experiment stands</h1>
<p class="sub">Test run, 2026-09-03. One author, one 4B model, six prompts, a frontier comparator, three adapters. Reload as runs fill in.</p>
<div class="stages">{st_html}</div>
<div class="plain">{plain}</div>
{score_section}
<h2>What the model is given (Gate 2)</h2>
<details><summary>The style guide the model is given in arms A3 and A5 (written by an API model from twelve training passages, never naming her)</summary><div class="body">{paras(guide)}</div></details>
<details><summary>The numbers block the model is given in arms A4 and A5 (computed from the training passages)</summary><div class="body">{paras(quant)}</div></details>
<details><summary>The six prompt arms</summary><div class="body scroll"><table><tr><th>arm</th><th>what the model gets besides the brief</th></tr>{arms_table}</table></div></details>

<h2>Real passage, brief, and what each model wrote</h2>
<p class="plain">Left: the brief. Middle: Wharton. Right: first sample under each condition, grouped by model; click a tab to switch. Adapter tabs are blue. Nothing here has been selected or edited.</p>
{''.join(passages_html)}
</main>
<script>
document.querySelectorAll('.tabcol').forEach(function(col){{
  col.addEventListener('click',function(e){{
    var b=e.target.closest('.tab'); if(!b) return;
    col.querySelectorAll('.tab').forEach(function(x){{x.setAttribute('aria-selected','false')}});
    b.setAttribute('aria-selected','true');
    col.querySelectorAll('.panel').forEach(function(p){{p.hidden=(p.id!==b.dataset.t)}});
  }});
}});
</script>
"""
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {a.out}: runs {runs}, {len(chosen)} passages, {n_gen} first-sample generations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
