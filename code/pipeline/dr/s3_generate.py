"""S3: regenerate every TEST passage under every arm (METHODS 5, 6).

Local arms (A0-A5) run on the base model in bf16 with an optional LoRA. API
arms (F0, F5) go to the frontier comparator through the same prompt builder.
One row per (passage, arm, sample) in runs/<run_id>/gens.jsonl; the run is
resumable, and a re-run skips cells already on disk.

Before any adapter generation the ADAPTER PROBE runs: one REF passage is scored
with the adapter enabled and disabled, and forty greedy tokens are generated
both ways. Identical outputs abort the run. This is the check the July
pipeline did not have (METHODS 7.1, fault 3).

    python dr/s3_generate.py --author wharton --run base4b --arms A0,A1,A2,A3,A4,A5
    python dr/s3_generate.py --author wharton --run base4b --arms F0,F5
    python dr/s3_generate.py --author wharton --run pair4b --arms A0,A5 --adapter runs/train_pair/adapter
"""
from __future__ import annotations

import argparse
import gc
import os
import re
import sys
import time

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import (RUNS, Manifest, api_call, author_dir, log, read_json,  # noqa: E402
                     read_jsonl, read_text, sha_text, upstream_hash, words, write_jsonl)
from dr.core import load_causal_lm  # noqa: E402  (2026-09-09: vision-capable bases such as Ministral 3)
from dr.prompts import Prompts  # noqa: E402

_THINK = re.compile(r"<think>.*?</think>\s*", re.S)
_PREFACE = re.compile(r"^\s*(?:#+\s*.*|\*\*.*\*\*|here(?:'s| is) .*?:|title:.*|passage:?)\s*\n", re.I)
_TRAIL = re.compile(r"\n\s*\n\s*(?:\[|\(|note\b|---|\*\*note|word count).*\Z", re.I | re.S)


def clean(text):
    """Strip thinking, a leading title/preface line, and a trailing note.
    Returns (text, flags)."""
    flags = []
    if "<think>" in text:
        text = _THINK.sub("", text)
        flags.append("think")
    if text.count("<think>") or "</think>" in text:
        text = text.replace("<think>", "").replace("</think>", "")
    m = _PREFACE.match(text)
    if m and len(words(m.group(0))) <= 12:
        text = text[m.end():]
        flags.append("preface")
    m = _TRAIL.search(text)
    if m and len(words(m.group(0))) <= 60:
        text = text[: m.start()]
        flags.append("trailer")
    text = text.strip().strip('"').strip()
    return text, flags


def load_materials(d, briefs_file):
    briefs = {r["id"]: r for r in read_jsonl(os.path.join(d, briefs_file)) if r.get("passed")}
    tag = briefs_file.replace("briefs_", "").replace(".jsonl", "")
    rp = os.path.join(d, f"retrieval_{tag}.jsonl")
    retrieval = {r["id"]: [e["text"] for e in r["exemplars"]] for r in read_jsonl(rp)} if os.path.exists(rp) else {}
    guide = read_text(os.path.join(d, "guide.md")) if os.path.exists(os.path.join(d, "guide.md")) else None
    quant = read_text(os.path.join(d, "quant_block.txt")) if os.path.exists(os.path.join(d, "quant_block.txt")) else None
    return briefs, retrieval, guide, quant


def build_cells(P, arms, briefs, retrieval, guide, quant, author_name):
    cells = []
    for pid, b in sorted(briefs.items()):
        for arm in arms:
            use_name, use_ex, use_guide, use_quant = config.ARMS[arm]
            if use_ex and pid not in retrieval:
                raise SystemExit(f"arm {arm} needs retrieval for {pid}; run s2 --retrieval")
            if use_guide and guide is None or use_quant and quant is None:
                raise SystemExit(f"arm {arm} needs guide/quant; run s2 --guide --quant")
            user = P.gen_user(arm, b["brief"], author_name=author_name,
                              exemplars=retrieval.get(pid), guide=guide, quant=quant)
            for s in config.SAMPLE_SEEDS:
                cells.append({"id": pid, "arm": arm, "sample": s, "user": user,
                              "target_words": b["source_words"]})
    return cells


# ------------------------------------------------------------- local model

def load_model(base, adapter=None):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(base, padding_side="left")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = load_causal_lm(base, dtype=torch.bfloat16, device_map="cuda:0")
    for holder in (model, getattr(model, "model", None)):
        for attr in ("visual", "vision_tower", "vision_model"):
            if holder is not None and hasattr(holder, attr) and getattr(holder, attr) is not None:
                setattr(holder, attr, None)
    gc.collect()
    torch.cuda.empty_cache()
    model.eval()
    probe = None
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)
        model.eval()
        probe = adapter_probe(model, tok)
        model = model.merge_and_unload()
        model.eval()
    return tok, model, probe


def chat_ids(tok, system, user):
    """Prompt token ids through the chat template with thinking off. Returns a
    plain list whatever the transformers version hands back (a list in 4.x, a
    BatchEncoding in 5.x)."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        out = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True,
                                      enable_thinking=False)
    except TypeError:
        out = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True)
    if hasattr(out, "keys") and "input_ids" in out:
        out = out["input_ids"]
    if hasattr(out, "ids"):
        out = out.ids
    if len(out) and isinstance(out[0], (list, tuple)):
        out = out[0]
    return [int(x) for x in out]


@__import__("torch").no_grad()
def adapter_probe(model, tok, probe_text=None):
    """Mean per-token log-likelihood of a probe passage and 40 greedy tokens,
    with the adapter enabled and disabled. Refuses to continue if identical."""
    import torch
    from dr.core import DATA
    if probe_text is None:
        ref = read_jsonl(os.path.join(DATA, config.AUTHOR, "ref.jsonl"))
        probe_text = ref[0]["text"]
    ids = tok(probe_text, return_tensors="pt", truncation=True, max_length=512).input_ids.cuda()
    prompt = torch.tensor([chat_ids(tok, "You write prose fiction.", "Write the opening of a scene at a dinner party.")]).cuda()

    def run():
        out = model(ids, labels=ids)
        g = model.generate(prompt, max_new_tokens=40, do_sample=False)
        return float(-out.loss), tok.decode(g[0, prompt.shape[1]:], skip_special_tokens=True)

    on_ll, on_txt = run()
    with model.disable_adapter():
        off_ll, off_txt = run()
    res = {"probe_ll_adapter_on": on_ll, "probe_ll_adapter_off": off_ll,
           "delta_ll": on_ll - off_ll, "greedy_on": on_txt, "greedy_off": off_txt,
           "identical": on_txt == off_txt and abs(on_ll - off_ll) < 1e-6}
    log(f"adapter probe: ll on {on_ll:.4f} off {off_ll:.4f} (delta {on_ll - off_ll:+.4f}); "
        f"greedy identical={on_txt == off_txt}")
    if res["identical"]:
        raise SystemExit("ADAPTER PROBE FAILED: adapter changes nothing. Not deploying.")
    return res


def generate_local(tok, model, cells, system, out_path, batch, gen_seed_base):
    import torch
    by_arm = {}
    for c in cells:
        by_arm.setdefault((c["arm"], c["sample"]), []).append(c)
    n_done = 0
    t0 = time.time()
    for (arm, s), group in sorted(by_arm.items()):
        group.sort(key=lambda c: len(c["user"]))   # similar lengths batch together
        for i in range(0, len(group), batch):
            chunk = group[i:i + batch]
            ids = [chat_ids(tok, system, c["user"]) for c in chunk]
            maxlen = max(len(x) for x in ids)
            input_ids = torch.full((len(ids), maxlen), tok.pad_token_id, dtype=torch.long)
            attn = torch.zeros((len(ids), maxlen), dtype=torch.long)
            for j, x in enumerate(ids):
                input_ids[j, maxlen - len(x):] = torch.tensor(x)
                attn[j, maxlen - len(x):] = 1
            tgt_tok = max(int(c["target_words"] * 1.35) for c in chunk)  # words->tokens, rough
            max_new = min(config.SAMPLING["max_new_cap"], int(config.SAMPLING["len_mult"] * tgt_tok))
            torch.manual_seed(gen_seed_base + s * 100003 + i)
            with torch.no_grad():
                out = model.generate(input_ids=input_ids.cuda(), attention_mask=attn.cuda(),
                                     do_sample=True, temperature=config.SAMPLING["temperature"],
                                     top_p=config.SAMPLING["top_p"],
                                     repetition_penalty=config.SAMPLING["repetition_penalty"],
                                     max_new_tokens=max_new, pad_token_id=tok.pad_token_id)
            rows = []
            for j, c in enumerate(chunk):
                raw = tok.decode(out[j, maxlen:], skip_special_tokens=True)
                text, flags = clean(raw)
                nw = len(words(text))
                ratio = nw / max(c["target_words"], 1)
                if not (config.LEN_FLAG[0] <= ratio <= config.LEN_FLAG[1]):
                    flags.append("length")
                if out[j, -1].item() != tok.pad_token_id and (out.shape[1] - maxlen) >= max_new:
                    flags.append("truncated")
                rows.append({"id": c["id"], "arm": c["arm"], "sample": c["sample"], "text": text,
                             "raw": raw, "n_words": nw, "target_words": c["target_words"],
                             "len_ratio": round(ratio, 3), "flags": flags,
                             "prompt_sha": sha_text(system + "\n" + c["user"]),
                             "prompt_tokens": len(ids[j]), "gen_tokens": int((out[j, maxlen:] != tok.pad_token_id).sum())})
            write_jsonl(out_path, rows, mode="a")
            n_done += len(rows)
            el = time.time() - t0
            log(f"  {arm} s{s}: {n_done}/{len(cells)} ({el/ n_done:.1f}s/gen)")
    return n_done


def generate_llamacpp(tok, cells, system, out_path, url, slots, seed_base, temperature=None):
    """All local arms through the llama.cpp server, `slots` requests in flight.
    Seed is a deterministic function of (passage, arm, sample), which is a
    property the batched HF path could not give."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from dr import llamacpp as L
    t0 = time.time()
    n_done = [0]
    lock = __import__("threading").Lock()

    def one(c):
        prompt = L.render_prompt(tok, system, c["user"])
        tgt_tok = int(c["target_words"] * 1.35)
        max_new = min(config.SAMPLING["max_new_cap"], int(config.SAMPLING["len_mult"] * tgt_tok))
        seed = (seed_base + c["sample"] * 100003 + (hash(c["id"] + c["arm"]) & 0xFFFF)) % (2**31 - 1)
        r = L.complete(prompt, max_new, seed=seed, url=url, temperature=temperature)
        raw = r["text"]
        text, flags = clean(raw)
        nw = len(words(text))
        ratio = nw / max(c["target_words"], 1)
        if not (config.LEN_FLAG[0] <= ratio <= config.LEN_FLAG[1]):
            flags.append("length")
        if r.get("stop_type") == "limit" or (r.get("tokens") or 0) >= max_new:
            flags.append("truncated")
        row = {"id": c["id"], "arm": c["arm"], "sample": c["sample"], "text": text, "raw": raw,
               "n_words": nw, "target_words": c["target_words"], "len_ratio": round(ratio, 3),
               "flags": flags, "prompt_sha": sha_text(system + "\n" + c["user"]),
               "prompt_tokens": r.get("prompt_tokens"), "gen_tokens": r.get("tokens"),
               "seed": seed, "tps": r.get("tps"), "backend": "llamacpp"}
        with lock:
            write_jsonl(out_path, [row], mode="a")
            n_done[0] += 1
            if n_done[0] % 10 == 0 or n_done[0] == len(cells):
                el = time.time() - t0
                log(f"  {n_done[0]}/{len(cells)} ({el/n_done[0]:.1f}s/gen, {r.get('tps', 0) or 0:.0f} tok/s/slot)")
        return row

    with ThreadPoolExecutor(max_workers=slots) as ex:
        futs = [ex.submit(one, c) for c in cells]
        for f in as_completed(futs):
            f.result()
    return n_done[0]


def generate_api(cells, system, out_path, model, workers=8):
    """Frontier arms through OpenRouter, `workers` calls in flight. Uncached,
    because two samples of one prompt must be two draws."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    lock = threading.Lock()
    n_done = [0]

    def one(c):
        text, meta = api_call(model, system, c["user"], max_tokens=config.SAMPLING["max_new_cap"],
                              temperature=config.SAMPLING["temperature"], cache=False,
                              tag=f"gen:{c['arm']}:{c['id']}:{c['sample']}")
        if text is None:
            log(f"  API failure {c['arm']} {c['id']} {c['sample']}: {meta.get('error')}")
            return None
        clean_text, flags = clean(text)
        nw = len(words(clean_text))
        ratio = nw / max(c["target_words"], 1)
        if not (config.LEN_FLAG[0] <= ratio <= config.LEN_FLAG[1]):
            flags.append("length")
        row = {"id": c["id"], "arm": c["arm"], "sample": c["sample"], "text": clean_text,
               "raw": text, "n_words": nw, "target_words": c["target_words"],
               "len_ratio": round(ratio, 3), "flags": flags,
               "prompt_sha": sha_text(system + "\n" + c["user"]),
               "api_model": meta.get("model"), "usd": meta.get("usd"), "backend": "api"}
        with lock:
            write_jsonl(out_path, [row], mode="a")
            n_done[0] += 1
            if n_done[0] % 20 == 0 or n_done[0] == len(cells):
                log(f"  api {n_done[0]}/{len(cells)}")
        return row

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for f in as_completed([ex.submit(one, c) for c in cells]):
            f.result()
    return n_done[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--run", required=True, help="run id under runs/")
    ap.add_argument("--arms", default="A0,A1,A2,A3,A4,A5")
    ap.add_argument("--briefs", default="briefs_test.jsonl")
    ap.add_argument("--base", default=config.BASE_MODEL)
    ap.add_argument("--adapter", default="")
    ap.add_argument("--frontier", default=config.FRONTIER)
    ap.add_argument("--batch", type=int, default=config.GEN_BATCH)
    ap.add_argument("--limit", type=int, default=0, help="first N passages only")
    ap.add_argument("--backend", choices=["llamacpp", "hf"], default="llamacpp")
    ap.add_argument("--server", default="http://127.0.0.1:8089", help="llama.cpp server url")
    ap.add_argument("--slots", type=int, default=8)
    ap.add_argument("--adapter-gguf", default="", help="llamacpp: adapter the server was started with (recorded + probed)")
    ap.add_argument("--merged", action="store_true", help="llamacpp: the server holds the adapter MERGED into the base weights (no runtime LoRA), so the on/off probe is impossible; the training probe in the adapter's run.json is recorded as the evidence (2026-09-09, Ministral 3)")
    ap.add_argument("--temperature", type=float, default=None, help="override config.SAMPLING temperature (recorded in the manifest)")
    a = ap.parse_args()
    d = author_dir(a.author)
    P = Prompts()
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    rd = os.path.join(RUNS, a.run)
    os.makedirs(rd, exist_ok=True)
    out_path = os.path.join(rd, "gens.jsonl")
    man = Manifest(os.path.join(rd, f"s3_manifest_{'_'.join(arms)}.json"), "s3_generate")
    man.input("briefs", os.path.join(d, a.briefs))
    for name in ("guide.md", "quant_block.txt"):
        if os.path.exists(os.path.join(d, name)):
            man.input(name, os.path.join(d, name))

    briefs, retrieval, guide, quant = load_materials(d, a.briefs)
    if a.limit:
        briefs = dict(sorted(briefs.items())[: a.limit])
    cells = build_cells(P, arms, briefs, retrieval, guide, quant, config.AUTHOR_NAMES[a.author])
    done = set()
    if os.path.exists(out_path):
        done = {(r["id"], r["arm"], r["sample"]) for r in read_jsonl(out_path)}
    cells = [c for c in cells if (c["id"], c["arm"], c["sample"]) not in done]
    log(f"{len(briefs)} passages x {arms} x {len(config.SAMPLE_SEEDS)} samples; "
        f"{len(done)} already on disk; {len(cells)} to generate")
    system = P.gen_system()

    api_cells = [c for c in cells if c["arm"] in config.API_ARMS]
    local_cells = [c for c in cells if c["arm"] not in config.API_ARMS]
    n = 0
    probe = None
    server_props = None
    if local_cells and a.backend == "llamacpp":
        from transformers import AutoTokenizer
        from dr import llamacpp as L
        if not L.alive(a.server):
            raise SystemExit(f"no llama.cpp server at {a.server}; start it with dr/llamacpp.py start")
        server_props = L.props(a.server)
        tok = AutoTokenizer.from_pretrained(a.base)
        loaded_lora = L._get(a.server, "/lora-adapters")
        if a.merged:
            rj = os.path.join(os.path.dirname(a.adapter_gguf), "run.json") if a.adapter_gguf else ""
            tp = (read_json(rj).get("probe") or {}) if rj and os.path.exists(rj) else {}
            delta = tp.get("delta")
            probe = {"mode": "merged", "adapters": [], "train_probe": tp, "identical": not (delta is not None and abs(delta) > 0.0),
                     "note": "adapter merged into the base weights before GGUF conversion; identical=False iff the training probe (held-out loss with the adapter on vs off) moved"}
            log(f"merged-weights server; training probe delta {delta}")
            if probe["identical"]:
                raise SystemExit("MERGED ADAPTER PROBE FAILED: the training probe recorded no change")
        elif a.adapter_gguf or loaded_lora:
            probe = L.adapter_probe(tok, a.server)
        log(f"server model {server_props.get('model_path')}; adapters {loaded_lora}")
        n += generate_llamacpp(tok, local_cells, system, out_path, a.server, a.slots, config.SEED, a.temperature)
    elif local_cells:
        tok, model, probe = load_model(a.base, a.adapter or None)
        n += generate_local(tok, model, local_cells, system, out_path, a.batch, config.SEED)
        del model
        gc.collect()
    if api_cells:
        n += generate_api(api_cells, system, out_path, a.frontier)
    man.output("gens", out_path)
    adapter_dir = a.adapter or (os.path.dirname(a.adapter_gguf) if a.adapter_gguf else "")
    run_json = os.path.join(adapter_dir, "run.json") if adapter_dir else ""
    from dr.provenance import stamp as _stamp
    man.save(provenance=_stamp(), base=a.base, backend=a.backend, server=server_props, adapter=a.adapter or a.adapter_gguf or None,
             adapter_probe=probe, frontier=a.frontier, sampling=config.SAMPLING, seeds=config.SAMPLE_SEEDS,
             arms=arms, n_generated=n, temperature=a.temperature if a.temperature is not None else config.SAMPLING['temperature'],
             adapter_run_json=read_json(run_json) if run_json and os.path.exists(run_json) else None)
    log(f"-> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
