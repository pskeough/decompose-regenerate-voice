"""Build the self-contained rating page for the human 2AFC study.

Reads runs/human_2afc_v1/{items.jsonl, KEY.json} and writes:
    study.html           standalone document to host anywhere (GitHub Pages,
                         Netlify Drop); download button works there
    study_artifact.html  same page as an Artifact fragment (no doctype/head);
                         the Artifact viewer blocks downloads, so raters use
                         Copy instead

The page is blind: it carries item texts in their assigned A/B order and no
condition or answer. Progress autosaves to localStorage per packet; the end
screen shows a completion code, the answers as JSON, Copy / Download, and
POSTs to WEBHOOK_URL if one is set at the top of the file.

    python dr/human_page.py --packet runs/human_2afc_v1
    python dr/human_page.py --packet runs/human_2afc_v1 --webhook https://script.google.com/... --contact "Patrick, pskeough@gmail.com"
"""
from __future__ import annotations

import argparse
import html
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import RUNS, author_dir, normalise_punct, read_json, read_jsonl, write_text  # noqa: E402
from dr.human_packet import excerpt  # noqa: E402


def practice_item(key, R, cand_words=450, ref_words=180):
    """A Wharton base-condition item on a passage not in the study."""
    used = {v["passage_id"] for v in key["items"].values()}
    d = author_dir("wharton")
    test = {r["id"]: r for r in read_jsonl(os.path.join(d, "test.jsonl"))}
    ref = read_jsonl(os.path.join(d, "ref.jsonl"))
    gens = [g for g in read_jsonl(os.path.join(RUNS, "base4b", "gens.jsonl"))
            if g["arm"] == "A0" and g["sample"] == 0 and "truncated" not in g["flags"] and g["id"] not in used]
    g = R.choice(gens)
    src = test[g["id"]]
    rf = R.choice([r for r in ref if r["work"] != src["work"]])
    real_first = R.random() < 0.5
    real_x, gen_x = excerpt(normalise_punct(src["text"]), cand_words), excerpt(normalise_punct(g["text"]), cand_words)
    return {"ref": excerpt(normalise_punct(rf["text"]), ref_words), "A": real_x if real_first else gen_x,
            "B": gen_x if real_first else real_x, "answer": "A" if real_first else "B", "passage_id": src["id"]}


CSS = """
:root{--bg:#f6f7f5;--card:#ffffff;--ink:#1d1f1e;--muted:#5f6663;--rule:#d9ddd8;--accent:#1f5c6b;--accent-ink:#ffffff;
--soft:#e8eef0;--ok:#2f7d4f;--ok-bg:#e6f2ea;--warn:#8a4b1f;--warn-bg:#f8ece2;--sel:#dbe9ec}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171a1b;--card:#1f2325;--ink:#e8e6e0;--muted:#a0a7a3;--rule:#33393b;--accent:#7fbccb;--accent-ink:#0f1a1e;
--soft:#242b2e;--ok:#8fd0a5;--ok-bg:#1c2b22;--warn:#e0a672;--warn-bg:#2d2218;--sel:#233539}}
:root[data-theme="dark"]{--bg:#171a1b;--card:#1f2325;--ink:#e8e6e0;--muted:#a0a7a3;--rule:#33393b;--accent:#7fbccb;--accent-ink:#0f1a1e;
--soft:#242b2e;--ok:#8fd0a5;--ok-bg:#1c2b22;--warn:#e0a672;--warn-bg:#2d2218;--sel:#233539}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;font-size:17px;line-height:1.5}
main{max-width:1080px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:30px;line-height:1.15;margin:0 0 8px;font-weight:600;text-wrap:balance}
h2{font-size:21px;margin:26px 0 8px;font-weight:600}
h3{font-size:16px;margin:0 0 8px;font-weight:600;letter-spacing:.02em}
p{margin:0 0 12px}
.lead{max-width:66ch}
.muted{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:18px 20px;margin:14px 0}
.prose{font-family:"Source Serif 4",Georgia,"Times New Roman",serif;font-size:17px;line-height:1.6}
.prose p{margin:0 0 .8em}
.ref .prose{border-left:3px solid var(--accent);padding-left:14px}
.cands{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:820px){.cands{grid-template-columns:1fr}}
.cand{background:var(--card);border:2px solid var(--rule);border-radius:10px;padding:16px 18px;cursor:pointer;transition:border-color .12s,background .12s}
.cand:hover{border-color:var(--accent)}
.cand.selected{border-color:var(--accent);background:var(--sel)}
.cand h3{display:flex;justify-content:space-between;align-items:center}
.pick{font-size:13px;color:var(--muted);font-weight:500}
.cand.selected .pick{color:var(--accent)}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:12px 0}
button{font:inherit;font-size:15px;border:1px solid var(--rule);background:var(--card);color:var(--ink);border-radius:8px;padding:9px 16px;cursor:pointer}
button:hover{border-color:var(--accent)}
button:focus-visible,.cand:focus-visible,select:focus-visible,textarea:focus-visible,input:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
button.primary{background:var(--accent);color:var(--accent-ink);border-color:var(--accent);font-weight:600;padding:11px 22px}
button.primary:disabled{opacity:.45;cursor:not-allowed}
button.conf{min-width:52px}
button.conf.on{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
textarea,select,input{font:inherit;border:1px solid var(--rule);border-radius:8px;padding:8px 10px;background:var(--card);color:var(--ink)}
textarea{width:100%;min-height:64px;resize:vertical}
.progress{height:8px;background:var(--soft);border-radius:4px;overflow:hidden;margin:8px 0 18px}
.progress > div{height:100%;background:var(--accent);transition:width .2s}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.tag{font-size:13px;color:var(--muted)}
.note{background:var(--soft);border-radius:8px;padding:10px 14px;font-size:15px}
.ok{background:var(--ok-bg);color:var(--ok);border-radius:8px;padding:10px 14px}
.warn{background:var(--warn-bg);color:var(--warn);border-radius:8px;padding:10px 14px}
.code{font-family:"IBM Plex Mono",Consolas,monospace;font-size:22px;letter-spacing:.06em;background:var(--soft);padding:10px 16px;border-radius:8px;display:inline-block}
pre{background:var(--soft);padding:12px;border-radius:8px;overflow:auto;max-height:260px;font-size:12px}
.hidden{display:none}
ol.steps{padding-left:22px}
ol.steps li{margin:6px 0}
.reveal{border-left:3px solid var(--ok);padding-left:14px}
kbd{font-family:"IBM Plex Mono",Consolas,monospace;font-size:12px;border:1px solid var(--rule);border-radius:4px;padding:1px 5px;background:var(--soft)}
"""

BODY = r"""
<main id="app"></main>
<script>
const DATA = __DATA__;
const CFG = __CFG__;
const $ = s => document.querySelector(s);
const params = new URLSearchParams(location.search);
let packet = parseInt(params.get("p") || "0", 10);
const PROLIFIC = { pid: params.get("PROLIFIC_PID") || "", study: params.get("STUDY_ID") || "", session: params.get("SESSION_ID") || "" };
let state = null;
const KEY = () => `${CFG.study}_p${packet}`;
function load(){ try { const s = localStorage.getItem(KEY()); state = s ? JSON.parse(s) : null; } catch(e){ state = null; } }
function save(){ try { localStorage.setItem(KEY(), JSON.stringify(state)); } catch(e){} }
function esc(t){ return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function paras(t){ return t.split(/\n\s*\n/).filter(x=>x.trim()).map(p=>`<p>${esc(p.trim())}</p>`).join(""); }
function newState(){ return { study: CFG.study, packet, participant: "", startedAt: new Date().toISOString(), screen: "intro",
  practiceDone: false, idx: 0, answers: [], itemStart: null, finishedAt: null, reading: "", prolific: PROLIFIC }; }

function render(){
  const app = $("#app");
  if(!state){ state = newState(); }
  if(state.screen === "intro") return renderIntro(app);
  if(state.screen === "practice") return renderPractice(app);
  if(state.screen === "items") return renderItem(app);
  if(state.screen === "done") return renderDone(app);
}

function renderIntro(app){
  const opts = Object.keys(DATA.packets).map(k => `<option value="${k}" ${parseInt(k)===packet?"selected":""}>Packet ${k}</option>`).join("");
  const resume = state.answers.length > 0;
  app.innerHTML = `
  <h1>A short reading study</h1>
  <p class="lead">Thank you for helping. This takes about <strong>45 minutes</strong> and you can stop and come back; your progress is saved in this browser.</p>
  <div class="card">
    <h2 style="margin-top:0">What you'll do</h2>
    <p class="lead">You'll read <strong>12 sets</strong>. Each set has three parts: a short <strong>voice sample</strong> by a writer, taken from a <em>different</em> story of theirs, and then two longer passages, <strong>A</strong> and <strong>B</strong>, which tell the same scene as each other (not the scene in the voice sample).</p>
    <p class="lead">One of A and B is the writer's own passage. The other was written by a computer program from a plot summary of that passage. The voice sample is there only to show you how the writer sounds.</p>
    <p class="lead">For each set, say which one you think is the writer's, and how sure you are (1 = a guess, 4 = certain). You can add a few words on what decided it, but you don't have to.</p>
    <h2>Ground rules</h2>
    <ol class="steps">
      <li>There are no trick questions. Read both, then go with your sense of the writer.</li>
      <li>A and B tell the same scene, and neither is the scene in the voice sample, so plot won't help; it's about how the writing sounds. The computer's version sometimes wanders from the plot; that's allowed and not a giveaway either way.</li>
      <li>Please don't look anything up, and don't go back to change an answer once you've moved on.</li>
      <li>Your answers are anonymous and used only for research on how well computers imitate writers. Close the page at any time if you'd rather not continue.</li>
    </ol>
    <h2>Before you start</h2>
    <div class="row">
      <label for="pk">Packet number (from the person who sent you this)</label>
      <select id="pk">${opts}</select>
    </div>
    <div class="row">
      <label for="who">A nickname or code, so we can match your answers if you get in touch (optional)</label>
      <input id="who" value="${esc(state.participant||"")}" maxlength="40">
    </div>
    <div class="row">
      <label for="rd">How often do you read fiction? (not a test, just context)</label>
      <select id="rd"><option value="">choose one</option><option value="rarely">Rarely</option><option value="monthly">A few times a month</option><option value="weekly">Weekly</option><option value="daily">Most days</option></select>
    </div>
    ${resume ? `<div class="ok">Welcome back. You've answered ${state.answers.length} of ${DATA.packets[packet].length}; you'll continue from where you left off.</div>` : ""}
    <div class="row" style="margin-top:16px">
      <button class="primary" id="start" ${packet ? "" : "disabled"}>${resume ? "Continue" : "Try a practice set first"}</button>
      ${packet ? "" : `<span class="warn">Pick your packet number first.</span>`}
    </div>
    ${CFG.contact ? `<p class="muted" style="margin-top:14px">Questions: ${esc(CFG.contact)}</p>` : ""}
  </div>`;
  $("#pk").addEventListener("change", e => { packet = parseInt(e.target.value,10); load(); if(!state) state = newState(); render(); });
  $("#who").addEventListener("input", e => { state.participant = e.target.value; save(); });
  $("#rd").value = state.reading || ""; $("#rd").addEventListener("change", e => { state.reading = e.target.value; save(); });
  $("#start").addEventListener("click", () => { state.screen = state.practiceDone ? "items" : "practice"; if(state.screen==="items" && !state.itemStart) state.itemStart = Date.now(); save(); render(); window.scrollTo(0,0); });
}

function candBlock(letter, text, selected, onpick){
  const d = document.createElement("div");
  d.className = "cand" + (selected ? " selected" : "");
  d.tabIndex = 0; d.setAttribute("role","radio"); d.setAttribute("aria-checked", selected ? "true" : "false");
  d.innerHTML = `<h3>Candidate ${letter} <span class="pick">${selected ? "your pick" : "click to pick"}</span></h3><div class="prose">${paras(text)}</div>`;
  d.addEventListener("click", onpick); d.addEventListener("keydown", e => { if(e.key===" "||e.key==="Enter"){ e.preventDefault(); onpick(); } });
  return d;
}

function renderPractice(app){
  const it = DATA.practice;
  let pick = null, revealed = false;
  const draw = () => {
    app.innerHTML = `
    <div class="top"><h1>Practice set</h1><span class="tag">not counted</span></div>
    <p class="lead">Read the voice sample, then the two candidates. Pick the one you think the same writer wrote, then reveal the answer. Remember: the sample is from a different story; A and B tell one scene between them.</p>
    <div class="card ref"><h3>Voice sample from the writer <span class="pick">a different story, for the sound of their writing</span></h3><div class="prose">${paras(it.ref)}</div></div>
    <p class="muted">Which of these two is by the same writer? Both tell the same scene.</p>
    <div class="cands" id="cands"></div>
    <div class="row" style="margin-top:14px">
      <button class="primary" id="reveal" ${pick?"":"disabled"}>Reveal the answer</button>
      <button id="skip">Skip practice</button>
    </div>
    <div id="answer"></div>`;
    const c = $("#cands");
    c.appendChild(candBlock("A", it.A, pick==="A", () => { if(!revealed){ pick="A"; draw(); } }));
    c.appendChild(candBlock("B", it.B, pick==="B", () => { if(!revealed){ pick="B"; draw(); } }));
    $("#reveal").addEventListener("click", () => {
      revealed = true;
      const right = pick === it.answer;
      $("#answer").innerHTML = `<div class="card reveal">
        <h3>The writer's passage was <strong>${it.answer}</strong>. ${right ? "You picked it." : "You picked the other one, which is fine; telling them apart is the whole question this study asks."}</h3>
        <p>Both candidates tell the same scene, so what separates them is the writing itself: the length and shape of sentences, the words chosen, how dialogue is handled, what the narrator lingers on. The computer's version may also drift from the plot or add things; treat that as part of how it writes rather than a trick. Go with your reading; a guess is a valid answer, just mark it as 1 on confidence.</p>
        <div class="row"><button class="primary" id="go">Start the 12 sets</button></div></div>`;
      $("#go").addEventListener("click", () => { state.practiceDone = true; state.screen = "items"; state.itemStart = Date.now(); save(); render(); window.scrollTo(0,0); });
      $("#reveal").disabled = true;
    });
    $("#skip").addEventListener("click", () => { state.practiceDone = true; state.screen = "items"; state.itemStart = Date.now(); save(); render(); window.scrollTo(0,0); });
  };
  draw();
}

function renderItem(app){
  const items = DATA.packets[packet];
  if(state.idx >= items.length){ state.screen = "done"; state.finishedAt = state.finishedAt || new Date().toISOString(); save(); return render(); }
  const it = items[state.idx];
  const cur = state.answers[state.idx] || { item: it.item, choice: null, confidence: null, note: "" };
  state.answers[state.idx] = cur;
  if(!state.itemStart) state.itemStart = Date.now();
  const n = state.idx + 1, N = items.length;
  app.innerHTML = `
  <div class="top"><h1>Set ${n} of ${N}</h1><span class="tag">${state.participant ? esc(state.participant) + " · " : ""}packet ${packet}</span></div>
  <div class="progress"><div style="width:${Math.round(100*state.idx/N)}%"></div></div>
  <div class="card ref"><h3>Voice sample from the writer <span class="pick">a different story, for the sound of their writing</span></h3><div class="prose">${paras(it.ref)}</div></div>
  <p class="muted">Which of these two is by the same writer? Both tell the same scene.</p>
  <div class="cands" id="cands"></div>
  <div class="card">
    <div class="row"><strong>How sure are you?</strong>
      <button class="conf ${cur.confidence===1?"on":""}" data-c="1">1 · a guess</button>
      <button class="conf ${cur.confidence===2?"on":""}" data-c="2">2</button>
      <button class="conf ${cur.confidence===3?"on":""}" data-c="3">3</button>
      <button class="conf ${cur.confidence===4?"on":""}" data-c="4">4 · certain</button>
    </div>
    <label for="note">What decided it, if anything? (optional)</label>
    <textarea id="note" placeholder="a few words is plenty">${esc(cur.note||"")}</textarea>
    <div class="row" style="margin-top:12px">
      <button class="primary" id="next" ${cur.choice && cur.confidence ? "" : "disabled"}>${n===N ? "Finish" : "Next set"}</button>
      <span class="muted">Your answer is saved as you go. Keys: <kbd>A</kbd> <kbd>B</kbd> <kbd>1</kbd>–<kbd>4</kbd></span>
    </div>
  </div>`;
  const c = $("#cands");
  const pick = L => { cur.choice = L; save(); renderItem(app); };
  c.appendChild(candBlock("A", it.A, cur.choice==="A", () => pick("A")));
  c.appendChild(candBlock("B", it.B, cur.choice==="B", () => pick("B")));
  document.querySelectorAll(".conf").forEach(b => b.addEventListener("click", () => { cur.confidence = parseInt(b.dataset.c,10); save(); renderItem(app); }));
  $("#note").addEventListener("input", e => { cur.note = e.target.value; save(); });
  $("#next").addEventListener("click", () => {
    cur.seconds = Math.round((Date.now() - state.itemStart)/1000);
    cur.answeredAt = new Date().toISOString();
    state.idx += 1; state.itemStart = Date.now(); save(); render(); window.scrollTo(0,0);
  });
  document.onkeydown = e => {
    if(e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
    const k = e.key.toUpperCase();
    if(k==="A"||k==="B") pick(k);
    else if("1234".includes(k) && k) { cur.confidence = parseInt(k,10); save(); renderItem(app); }
  };
}

function hash(s){ let h = 2166136261; for(let i=0;i<s.length;i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h>>>0).toString(16).padStart(8,"0").slice(0,6).toUpperCase(); }

function exportObj(){
  return { study: CFG.study, packet, participant: state.participant||"", reading: state.reading||"", prolific: state.prolific||PROLIFIC, startedAt: state.startedAt, finishedAt: state.finishedAt,
    userAgent: navigator.userAgent, answers: state.answers.map(a => ({ item:a.item, choice:a.choice, confidence:a.confidence, note:a.note||"", seconds:a.seconds||null })) };
}

function renderDone(app){
  document.onkeydown = null;
  const obj = exportObj();
  const json = JSON.stringify(obj, null, 1);
  const code = `H2-${String(packet).padStart(2,"0")}-${hash(JSON.stringify(obj.answers))}`;
  app.innerHTML = `
  <h1>Done. Thank you.</h1>
  <p class="lead">Your completion code is</p>
  <p><span class="code" id="code">${code}</span>${CFG.prolific_code ? ` &nbsp; <span class="muted">Prolific completion code:</span> <span class="code">${esc(CFG.prolific_code)}</span>` : ""}</p>
  <div id="sent"></div>
  <div class="card">
    <h3>Send your answers</h3>
    <p class="lead">${CFG.webhook ? "They are being sent automatically. If the line below doesn't turn green, use one of the buttons." : "Use one of the buttons, then send the file or the copied text to the person who gave you this page."}</p>
    <div class="row">
      <button class="primary" id="copy">Copy answers</button>
      <button id="dl">Download answers file</button>
      <span id="msg" class="muted"></span>
    </div>
    <details style="margin-top:10px"><summary>What gets sent</summary><pre>${esc(json)}</pre></details>
  </div>
  ${CFG.contact ? `<p class="muted">Questions or to get in touch: ${esc(CFG.contact)}</p>` : ""}`;
  $("#copy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(json); $("#msg").textContent = "Copied. Paste it into a message to the researcher."; }
    catch(e){ const ta = document.createElement("textarea"); ta.value = json; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove(); $("#msg").textContent = "Copied."; }
  });
  $("#dl").addEventListener("click", () => {
    const blob = new Blob([json], {type:"application/json"}); const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = `${CFG.study}_packet${String(packet).padStart(2,"0")}_${code}.json`; document.body.appendChild(a); a.click(); a.remove();
    $("#msg").textContent = "If nothing downloaded, use Copy instead.";
  });
  if(CFG.webhook && !state.sent){
    fetch(CFG.webhook, { method:"POST", mode:"no-cors", headers:{"Content-Type":"text/plain"}, body: json })
      .then(() => { state.sent = true; save(); $("#sent").innerHTML = `<div class="ok">Sent. You're finished; you can close this page.</div>`; })
      .catch(() => { $("#sent").innerHTML = `<div class="warn">Automatic send didn't work. Please use Copy or Download below.</div>`; });
  } else if(state.sent){ $("#sent").innerHTML = `<div class="ok">Already sent. You're finished.</div>`; }
}

load();
if(!packet && state) packet = state.packet;
render();
</script>
"""


def build(packet_dir, webhook, contact, seed, prolific_code=""):
    key = read_json(os.path.join(packet_dir, "KEY.json"))
    items = {it["item"]: it for it in read_jsonl(os.path.join(packet_dir, "items.jsonl"))}
    packets = {}
    for r in key["ratings"]:
        it = items[r["item"]]
        a, b = (it["real"], it["gen"]) if r["real_position"] == "A" else (it["gen"], it["real"])
        packets.setdefault(str(r["rater"]), []).append({"item": r["item"], "ref": it["reference"], "A": a, "B": b})
    R = random.Random(seed)
    data = {"packets": packets, "practice": practice_item(key, R)}
    cfg = {"study": "h2afc_v1", "webhook": webhook or "", "contact": contact or "", "prolific_code": prolific_code or ""}
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    body = BODY.replace("__DATA__", js(data)).replace("__CFG__", js(cfg))
    head_common = ('<title>Reading Study</title>\n'
                   '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono&display=swap">\n'
                   f'<style>{CSS}</style>\n')
    standalone = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                  '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + head_common +
                  '</head>\n<body>\n' + body + '\n</body>\n</html>\n')
    fragment = head_common + body
    write_text(os.path.join(packet_dir, "study.html"), standalone)
    write_text(os.path.join(packet_dir, "study_artifact.html"), fragment)
    n_items = sum(len(v) for v in packets.values())
    print(f"study.html: {len(packets)} packets, {n_items} rated items, practice on {data['practice']['passage_id']}, "
          f"{os.path.getsize(os.path.join(packet_dir, 'study.html'))/1024:.0f} KB, webhook {'set' if webhook else 'off'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--packet", default=os.path.join(RUNS, "human_2afc_v1"))
    ap.add_argument("--webhook", default="")
    ap.add_argument("--contact", default="")
    ap.add_argument("--prolific-code", default="", help="fixed completion code shown at the end for Prolific")
    ap.add_argument("--seed", type=int, default=config.SEED + 1)
    a = ap.parse_args()
    build(a.packet, a.webhook, a.contact, a.seed, a.prolific_code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
