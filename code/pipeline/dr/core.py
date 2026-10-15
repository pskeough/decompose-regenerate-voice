"""Paths, io, hashing, manifests, and the OpenRouter client.

Named core rather than common so that it never shadows the overnight battery's
`common` module, which s5 imports by path.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request

DR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(DR)                              # Voice_Style_Retune
DATA = os.path.join(DR, "data")
RUNS = os.path.join(DR, "runs")
LOGS = os.path.join(DR, "logs")
CORPUS = os.path.join(ROOT, "data", "authors_v2")
SCRIPTS = os.path.join(ROOT, "scripts")
OVERNIGHT = os.path.join(ROOT, "overnight_0903")
MIMESIS_LOCAL = r"C:\AI Coding Projects\Local AI\Mimesis_Local"
ENV_FILE = r"C:\LocalAI\LLM\eval\.env"
API_CACHE = os.path.join(DATA, "_api_cache")
LEDGER = os.path.join(LOGS, "api_ledger.jsonl")
for d in (DATA, RUNS, LOGS, API_CACHE):
    os.makedirs(d, exist_ok=True)

# Same splitter family as the overnight battery and the project's instruments,
# so a sentence here is a sentence there.
_SENT_SPLIT = re.compile(r"(?<=[.!?])[\"'\u201d\u2019)\]]*\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'\u2019-]*")


def sentences(text: str) -> list[str]:
    return [s for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def words(text: str) -> list[str]:
    return _WORD.findall(text)


def paragraphs(text: str) -> list[str]:
    ps = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return ps or [text.strip()]


_DDASH = re.compile(r"\s*--+\s*")
_UNDER = re.compile(r"(?<![A-Za-z0-9])_([^_\n]{1,80})_(?![A-Za-z0-9])")


def normalise_punct(text: str) -> str:
    """Remove transcription conventions that give the source away: Gutenberg's
    `--` for a dash becomes an em dash with no spaces, and `_italics_` markup
    loses its underscores. Found 2026-09-05 in the pilot: 53-68% of Wharton's
    real passages carry `--` and 42-47% carry underscores, no model output
    carries either, and the pilot rater named the dash as his cue."""
    t = _UNDER.sub(r"\1", text)
    t = _DDASH.sub("—", t)
    return t


def ngrams(toks, n):
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def norm_words(text: str) -> list[str]:
    return [w.lower() for w in words(text)]


# ------------------------------------------------------------------ io

def read_jsonl(path, strict=True):
    """strict=False skips unparsable lines. The API ledger is appended by
    several processes at once and a torn line was seen on 2026-09-03; every
    data file stays strict."""
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                if strict:
                    raise
    return out


def write_jsonl(path, rows, mode="w"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = 0
    with open(path, mode, encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def append_jsonl(path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def read_text(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


_LOG_LOCK = threading.Lock()


def log(msg):
    with _LOG_LOCK:
        print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def author_dir(author):
    d = os.path.join(DATA, author)
    os.makedirs(d, exist_ok=True)
    return d


# ------------------------------------------------------------- hashing

def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_hashes():
    """Hashes of the two files that define the experiment."""
    return {"PROMPTS.md": sha_file(os.path.join(DR, "PROMPTS.md")),
            "config.py": sha_file(os.path.join(DR, "dr", "config.py"))}


# ----------------------------------------------------------- manifests

def new_run_id(tag):
    return f"{dt.datetime.now():%Y%m%d_%H%M}_{tag}"


class Manifest:
    """One per stage output. Records what went in, by hash, and refuses to
    build on inputs whose hash no longer matches what an upstream stage wrote.
    """

    def __init__(self, path, stage, argv=None):
        self.path = path
        self.d = {"stage": stage, "started": dt.datetime.now().isoformat(timespec="seconds"),
                  "argv": argv or sys.argv, "frozen": frozen_hashes(), "inputs": {},
                  "outputs": {}, "notes": []}

    def input(self, name, path, expect=None):
        h = sha_file(path)
        if expect and expect != h:
            raise SystemExit(f"upstream hash mismatch for {name}: manifest expects "
                             f"{expect[:12]}, file is {h[:12]}. Re-run the upstream "
                             f"stage or open a decision.")
        self.d["inputs"][name] = {"path": path, "sha256": h}
        return h

    def output(self, name, path):
        self.d["outputs"][name] = {"path": path, "sha256": sha_file(path)}

    def note(self, **kw):
        self.d["notes"].append(kw)

    def save(self, **extra):
        self.d.update(extra)
        self.d["finished"] = dt.datetime.now().isoformat(timespec="seconds")
        write_json(self.path, self.d)
        return self.d


def upstream_hash(manifest_path, name):
    """The hash an upstream manifest recorded for one of its outputs."""
    if not os.path.exists(manifest_path):
        return None
    m = read_json(manifest_path)
    return m.get("outputs", {}).get(name, {}).get("sha256")


# ---------------------------------------------------------- OpenRouter

def _api_key():
    if not os.path.exists(ENV_FILE):
        raise SystemExit(f"no env file at {ENV_FILE}")
    for line in open(ENV_FILE, encoding="utf-8"):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENROUTER_API_KEY not in env file")


# USD per million tokens, (prompt, completion). Estimates for the ledger only;
# the hard stop is on the estimate, so it errs high.
PRICE = {
    "deepseek/deepseek-v4-flash": (0.15, 0.60),
    "deepseek/deepseek-v4-flash-0731": (0.07, 0.18),
    "minimax/minimax-m3": (0.30, 1.20),
    "google/gemini-3.1-flash-lite-preview": (0.10, 0.40),
    "openai/gpt-5-nano": (0.05, 0.40),
}
_SPENT = {"usd": 0.0}
_SPENT_LOCK = threading.Lock()


def credits_usd():
    """Remaining OpenRouter balance (total credits minus usage), or None if
    the endpoint fails. Every unattended controller checks this first; the
    software cap in config is not a balance (DECISIONS 2026-09-04)."""
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/credits",
                                     headers={"Authorization": f"Bearer {_api_key()}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read()).get("data", {})
        return float(d.get("total_credits", 0)) - float(d.get("total_usage", 0))
    except Exception:
        return None


def spent_usd():
    """Sum of the ledger, so a budget stop survives a restart."""
    total = 0.0
    if os.path.exists(LEDGER):
        for r in read_jsonl(LEDGER, strict=False):
            total += r.get("usd", 0.0) or 0.0
    return total


def api_call(model, system, user, max_tokens=1000, temperature=0.0, retries=4,
             timeout=300, cache=True, tag="", reasoning=False):
    """One chat completion. Cached on (model, system, user, temperature, max_tokens,
    reasoning) so a re-run costs nothing and returns the same text. Returns
    (text, meta). `reasoning=False` sends OpenRouter's unified
    `reasoning: {enabled: false}` so hybrid-thinking models answer directly;
    the decomposer and the judges do not need a scratchpad and a reasoning
    budget was seen to eat the whole completion (gpt-5-nano, GLM-5.2).
    """
    from dr import config
    key = sha_text(json.dumps([model, system, user, temperature, max_tokens, reasoning]))
    cpath = os.path.join(API_CACHE, key + ".json")
    if cache and os.path.exists(cpath):
        c = read_json(cpath)
        return c["text"], {**c["meta"], "cached": True}
    if spent_usd() > config.API_BUDGET_USD:
        raise SystemExit(f"API budget {config.API_BUDGET_USD} USD exceeded; see {LEDGER}")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user})
    payload = {"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature}
    if not reasoning:
        payload["reasoning"] = {"enabled": False}
    body = json.dumps(payload).encode()
    last = None
    for a in range(retries):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {_api_key()}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://localhost/decompose_regenerate",
                     "X-Title": "decompose_regenerate"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            ch = d["choices"][0]
            usage = d.get("usage", {}) or {}
            text = (ch["message"].get("content") or "").strip()
            pin, pout = PRICE.get(model, (1.0, 3.0))
            usd = (usage.get("prompt_tokens", 0) * pin + usage.get("completion_tokens", 0) * pout) / 1e6
            meta = {"model": d.get("model", model), "finish": ch.get("finish_reason"),
                    "usage": usage, "usd": usd, "tag": tag,
                    "ts": dt.datetime.now().isoformat(timespec="seconds")}
            append_jsonl(LEDGER, {"model": model, "usd": usd, "usage": usage, "tag": tag,
                                  "ts": meta["ts"]})
            if text:
                if cache:
                    write_json(cpath, {"text": text, "meta": meta})
                return text, meta
            last = f"empty completion, finish={ch.get('finish_reason')}"
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            last = f"HTTP {e.code}: {detail}"
            if e.code not in (408, 429, 500, 502, 503, 504):
                break
        except Exception as e:  # network
            last = str(e)[:200]
        time.sleep(4 * (a + 1))
    return None, {"error": last, "model": model, "tag": tag}

def load_causal_lm(base, **kw):
    """Load a base checkpoint for training, probing or merging. Qwen3 loads through
    AutoModelForCausalLM; a vision-capable checkpoint whose config has no causal-LM
    mapping (Mistral3ForConditionalGeneration, the Ministral 3 family used for the
    2026-09-09 cross-family replication) falls back to the image-text class, whose
    text tower is what the callers train and probe (they free the vision tower and
    exclude it from LoRA targets already). Same dtype and placement either way."""
    from transformers import AutoModelForCausalLM
    if "quantization_config" not in kw:
        # FP8 releases (Ministral 3, 2026-09-09): on Ampere the quantizer dequantises on load and
        # training works; on Ada (L40S) the weights stay FP8 and the Trainer refuses to fine-tune a
        # quantised model. Dequantise everywhere so every pod trains, probes and merges the same
        # bf16 base, which is also what llama.cpp's F16 GGUF of the release contains.
        try:
            from transformers import AutoConfig
            cfg = AutoConfig.from_pretrained(base)
            qc = getattr(cfg, "quantization_config", None) or getattr(getattr(cfg, "text_config", None), "quantization_config", None)
            qm = (qc.get("quant_method") if isinstance(qc, dict) else getattr(qc, "quant_method", None)) if qc else None
            if qm == "fp8":
                from transformers import FineGrainedFP8Config
                kw["quantization_config"] = FineGrainedFP8Config(dequantize=True)
                log(f"{base}: FP8 checkpoint, dequantising to bf16 on load")
        except Exception as e:
            log(f"quantization check skipped for {base}: {e!r}")
    try:
        return AutoModelForCausalLM.from_pretrained(base, **kw)
    except (ValueError, KeyError) as e:
        if "Unrecognized configuration class" not in str(e) and not isinstance(e, KeyError):
            raise
        from transformers import AutoModelForImageTextToText
        log(f"AutoModelForCausalLM has no mapping for {base}; loading AutoModelForImageTextToText")
        return AutoModelForImageTextToText.from_pretrained(base, **kw)
