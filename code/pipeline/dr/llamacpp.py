r"""llama.cpp server client for generation (METHODS 6, DECISIONS G0 amendment).

HF `generate` decodes at 2.7 tok/s on this machine (Windows launch overhead on
a 4B); llama.cpp with CUDA graphs is the path. The prompt string is rendered by
the HF tokenizer's own chat template (thinking off) and sent raw to
`/completion`, so the tokens the server sees are the ones training saw.

Adapters: the server is started with `--lora <adapter.gguf>`; `/lora-adapters`
sets the scale at runtime, which is how the adapter-active probe works here
(scale 1 vs scale 0 on the same greedy prompt).

    python dr/llamacpp.py start --model C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf
    python dr/llamacpp.py start --model ... --lora runs/train_x/adapter.gguf
    python dr/llamacpp.py stop
    python dr/llamacpp.py bench          # 8 concurrent x 300 tokens
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import LOGS, log, write_json  # noqa: E402

SERVER_BIN = os.environ.get("DR_LLAMA_SERVER", r"C:\LocalAI\LLM\llama-b10435-bin-win-cuda-13.3-x64\llama-server.exe")   # same release tag (b10435) on every host
DEFAULT_URL = "http://127.0.0.1:8089"
PID_FILE = os.path.join(LOGS, "llama_server.json")


def _pid_file(url):
    """One pid file per port, so two lanes on one card can each stop their own server."""
    port = url.rsplit(":", 1)[1]
    return PID_FILE if port == DEFAULT_URL.rsplit(":", 1)[1] else os.path.join(LOGS, f"llama_server_{port}.json")
SLOTS = 8
CTX_PER_SLOT = 5120   # A5 prompts run ~2,700 tokens; 3,072 cut generation at ~450 (2026-09-03)


def _post(url, path, body, timeout=600):
    req = urllib.request.Request(url + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _get(url, path, timeout=30):
    with urllib.request.urlopen(url + path, timeout=timeout) as r:
        return json.loads(r.read())


def _kill_pid(pid):
    """Cross-platform: psutil where available, taskkill/kill otherwise."""
    try:
        import psutil
        psutil.Process(int(pid)).kill()
        return
    except Exception:
        pass
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    else:
        subprocess.run(["kill", "-9", str(pid)], capture_output=True)


def _kill_named(prefix):
    try:
        import psutil
        for p in psutil.process_iter(["pid", "name"]):
            if (p.info["name"] or "").lower().startswith(prefix):
                try:
                    p.kill()
                except Exception:
                    pass
    except ImportError:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/IM", prefix + ".exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "-9", "-f", prefix], capture_output=True)


def alive(url=DEFAULT_URL):
    try:
        return _get(url, "/health").get("status") == "ok"
    except Exception:
        return False


def props(url=DEFAULT_URL):
    try:
        return _get(url, "/props")
    except Exception as e:
        return {"error": repr(e)}


def start(model, lora=None, url=DEFAULT_URL, slots=SLOTS, ctx_per_slot=CTX_PER_SLOT, wait=240):
    if alive(url):
        p = props(url)
        cur_model = os.path.basename(str(p.get("model_path") or ""))
        try:
            cur_lora = [os.path.basename(str(x.get("path", ""))) for x in _get(url, "/lora-adapters")]
        except Exception:
            cur_lora = []
        want_lora = [os.path.basename(lora)] if lora else []
        if cur_model == os.path.basename(model) and cur_lora == want_lora:
            log(f"server already up with the requested model/adapter: {cur_model} {want_lora}")
            return p
        log(f"server up with {cur_model} {cur_lora}, want {os.path.basename(model)} {want_lora}: restarting")
        stop()
        time.sleep(3)
    port = url.rsplit(":", 1)[1]
    cmd = [SERVER_BIN, "-m", model, "-ngl", "99", "-c", str(slots * ctx_per_slot), "-np", str(slots),
           "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",   # q8 KV: 8 x 5,120 ctx fits beside F16 weights
           "--port", port, "--host", "127.0.0.1", "--no-webui"]
    if lora:
        cmd += ["--lora", lora]
    logf = open(os.path.join(LOGS, "llama_server.log"), "a", encoding="utf-8")
    logf.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
    logf.flush()
    proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    write_json(_pid_file(url), {"pid": proc.pid, "cmd": cmd, "url": url, "model": model, "lora": lora})
    t0 = time.time()
    while time.time() - t0 < wait:
        if alive(url):
            log(f"llama-server up in {time.time()-t0:.0f}s, pid {proc.pid}, slots {slots}, ctx {slots*ctx_per_slot}")
            return props(url)
        if proc.poll() is not None:
            raise SystemExit(f"llama-server exited with {proc.returncode}; see logs/llama_server.log")
        time.sleep(2)
    raise SystemExit("llama-server did not come up; see logs/llama_server.log")


def stop(url=DEFAULT_URL):
    pf = _pid_file(url)
    if os.path.exists(pf):
        d = json.load(open(pf))
        _kill_pid(d["pid"])
        os.remove(pf)
        log(f"stopped pid {d['pid']}")
    else:
        if url == DEFAULT_URL:
            _kill_named("llama-server")
            log("no pid file; killed any llama-server")
        else:
            log(f"no pid file for {url}; nothing killed (another lane may own a server)")


def set_lora_scale(scale, url=DEFAULT_URL):
    cur = _get(url, "/lora-adapters")
    if not cur:
        return None
    return _post(url, "/lora-adapters", [{"id": a["id"], "scale": float(scale)} for a in cur])


def complete(prompt, n_predict, seed, temperature=None, top_p=None, greedy=False, url=DEFAULT_URL):
    body = {"prompt": prompt, "n_predict": int(n_predict), "seed": int(seed),
            "temperature": 0.0 if greedy else (config.SAMPLING["temperature"] if temperature is None else temperature),
            "top_p": 1.0 if greedy else (config.SAMPLING["top_p"] if top_p is None else top_p),
            "top_k": 0, "min_p": 0.0, "repeat_penalty": config.SAMPLING["repetition_penalty"],
            "cache_prompt": True, "stop": ["<|im_end|>", "<|endoftext|>"]}
    for a in range(3):
        try:
            d = _post(url, "/completion", body)
            return {"text": d.get("content", ""), "tokens": d.get("tokens_predicted"),
                    "stop_type": d.get("stop_type") or d.get("stopped_eos"),
                    "prompt_tokens": d.get("tokens_evaluated"),
                    "tps": (d.get("timings") or {}).get("predicted_per_second")}
        except urllib.error.HTTPError as e:
            if a == 2:
                raise
            time.sleep(3)
    return None


def render_prompt(tok, system, user):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def adapter_probe(tok, url=DEFAULT_URL):
    """Greedy 40 tokens with the adapter at scale 1 and at scale 0. Identical
    outputs mean the adapter is not loaded or does nothing; refuse to run."""
    prompt = render_prompt(tok, "You write prose fiction.", "Write the opening of a scene at a dinner party.")
    cur = _get(url, "/lora-adapters")
    if not cur:
        raise SystemExit("ADAPTER PROBE: server reports no LoRA adapters loaded")
    set_lora_scale(1.0, url)
    on = complete(prompt, 40, seed=0, greedy=True, url=url)["text"]
    set_lora_scale(0.0, url)
    off = complete(prompt, 40, seed=0, greedy=True, url=url)["text"]
    set_lora_scale(1.0, url)
    res = {"adapters": cur, "greedy_on": on, "greedy_off": off, "identical": on == off}
    log(f"adapter probe: identical={on == off}")
    if on == off:
        raise SystemExit("ADAPTER PROBE FAILED: adapter changes nothing. Not deploying.")
    return res


def bench(url=DEFAULT_URL, n=8, tokens=300):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(config.BASE_MODEL)
    prompt = render_prompt(tok, "You write prose fiction.", "Write a scene of about 400 words in which two old friends meet at a railway station after twenty years and one of them has bad news.")
    t0 = time.time()
    r = complete(prompt, tokens, seed=1, url=url)
    single = r["tokens"] / (time.time() - t0)
    t0 = time.time()
    with ThreadPoolExecutor(n) as ex:
        rs = list(ex.map(lambda i: complete(prompt, tokens, seed=i, url=url), range(n)))
    dt = time.time() - t0
    agg = sum(x["tokens"] for x in rs) / dt
    log(f"single {single:.1f} tok/s; {n} concurrent {agg:.1f} tok/s aggregate ({dt:.0f}s)")
    print("---- sample ----\n" + rs[0]["text"][:600] + "\n----")
    return single, agg


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["start", "stop", "bench", "status"])
    ap.add_argument("--model", default=r"C:\LocalAI\LLM\models\Qwen3-4B-F16.gguf")
    ap.add_argument("--lora", default="")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--slots", type=int, default=SLOTS)
    a = ap.parse_args()
    if a.cmd == "start":
        p = start(a.model, a.lora or None, a.url, a.slots)
        print(json.dumps({k: p.get(k) for k in ("model_path", "total_slots", "default_generation_settings")}, indent=1)[:800])
    elif a.cmd == "stop":
        stop(a.url)
    elif a.cmd == "bench":
        bench(a.url)
    else:
        print("alive" if alive(a.url) else "down", props(a.url).get("model_path"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
