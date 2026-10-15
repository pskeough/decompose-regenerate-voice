"""Merge a PEFT adapter into the base weights and export an F16 GGUF, so the
server decodes at full speed (an unmerged --lora costs ~25% per token in
llama.cpp on this card: 15 vs 20 tok/s per slot).

This build of llama.cpp ships no llama-export-lora, so the merge is done in
HF: load base bf16 on CPU, PeftModel.merge_and_unload, save, convert with
tools/llama.cpp/convert_hf_to_gguf.py, delete the 8 GB HF copy.

Validation: the caller compares a greedy probe on the merged model against the
`greedy_on` text the unmerged run recorded; they should agree on the first
tokens up to bf16/F16 rounding.

    python dr/merge_adapter.py --adapter runs/train_wharton_pair_r16_s0/adapter
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import DR, log, load_causal_lm  # noqa: E402

CONVERT = os.path.join(os.environ.get("DR_LLAMA_TOOLS", os.path.join(DR, "tools", "llama.cpp")), "convert_hf_to_gguf.py")   # DR_LLAMA_TOOLS on the pods (2026-09-09)


def merge(adapter_dir, base=config.BASE_MODEL, out_gguf=None, device="cpu"):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    run_dir = os.path.dirname(os.path.abspath(adapter_dir))
    out_gguf = out_gguf or os.path.join(run_dir, "merged.gguf")
    if os.path.exists(out_gguf):
        log(f"merged already exists: {out_gguf}")
        return out_gguf
    hf_dir = os.path.join(run_dir, "merged_hf")
    t0 = time.time()
    log(f"loading {base} on {device}")
    # FP8 checkpoints (Ministral 3, 2026-09-09: quant_method fp8, per-tensor weight_scale_inv) must be
    # dequantised to bf16 before merging, or the saved model carries FP8 weights plus scale tensors that
    # no converter maps. First choice: transformers' own dequantize flag; fallback: manual per-tensor dequant.
    from transformers import AutoConfig
    cfg = AutoConfig.from_pretrained(base)
    qc = getattr(cfg, "quantization_config", None) or getattr(getattr(cfg, "text_config", None), "quantization_config", None)
    qm = (qc.get("quant_method") if isinstance(qc, dict) else getattr(qc, "quant_method", None)) if qc else None
    kw = dict(dtype=torch.bfloat16, device_map=device)
    manual = False
    if qm == "fp8":
        try:
            from transformers import FineGrainedFP8Config
            kw["quantization_config"] = FineGrainedFP8Config(dequantize=True)
            log("FP8 checkpoint: dequantising to bf16 on load")
        except Exception as e:
            log(f"FineGrainedFP8Config(dequantize=True) unavailable ({e!r}); manual dequant after load")
            manual = True
    model = load_causal_lm(base, **kw)
    if qm == "fp8":
        n_fp8 = 0
        for name, mod in list(model.named_modules()):
            w = getattr(mod, "weight", None)
            sc = getattr(mod, "weight_scale_inv", None)
            if w is not None and w.dtype == torch.float8_e4m3fn:
                n_fp8 += 1
                if sc is None:
                    raise SystemExit(f"FP8 weight without weight_scale_inv at {name}")
                s_ = sc.to(torch.float32)
                deq = w.to(torch.float32) * (s_ if s_.dim() == 0 or s_.numel() == 1 else s_.reshape(*s_.shape, 1, 1).repeat_interleave(w.shape[0] // s_.shape[0], 0).squeeze() if False else s_)
                mod.weight = torch.nn.Parameter(deq.to(torch.bfloat16), requires_grad=False)
                delattr(mod, "weight_scale_inv") if hasattr(mod, "weight_scale_inv") else None
        log(f"FP8 modules dequantised manually: {n_fp8}" if n_fp8 else "no FP8 weights remain after load")
        for c in (model.config, getattr(model.config, "text_config", None)):
            if c is not None and hasattr(c, "quantization_config"):
                try:
                    delattr(c, "quantization_config")
                except Exception:
                    c.quantization_config = None
    tok = AutoTokenizer.from_pretrained(base)
    model = PeftModel.from_pretrained(model, adapter_dir)
    model = model.merge_and_unload()
    log(f"merged in {time.time()-t0:.0f}s; saving HF copy")
    # 2026-09-09: with the FP8 quantizer still attached, save_pretrained re-quantised the merged
    # bf16 weights back to FP8 plus scale tensors that no converter maps. Detach it, save, verify.
    for attr in ("hf_quantizer", "quantization_method"):
        if hasattr(model, attr):
            try:
                setattr(model, attr, None)
            except Exception:
                pass
    if hasattr(model, "is_quantized"):
        model.is_quantized = False
    for c in (model.config, getattr(model.config, "text_config", None)):
        if c is not None and getattr(c, "quantization_config", None) is not None:
            c.quantization_config = None
    model.save_pretrained(hf_dir, safe_serialization=True)
    tok.save_pretrained(hf_dir)
    from safetensors import safe_open
    bad = 0
    for shard in glob.glob(os.path.join(hf_dir, "*.safetensors")):
        with safe_open(shard, "pt") as sf:
            for k in sf.keys():
                if "F8" in str(sf.get_slice(k).get_dtype()) or k.endswith("weight_scale_inv") or k.endswith("activation_scale"):
                    bad += 1
    if bad:
        log(f"save_pretrained still wrote {bad} FP8/scale tensors; rewriting the shards from the bf16 state dict")
        from safetensors.torch import save_file, _remove_duplicate_names
        for shard in glob.glob(os.path.join(hf_dir, "*.safetensors")):
            os.remove(shard)
        for fn in ("model.safetensors.index.json",):
            if os.path.exists(os.path.join(hf_dir, fn)):
                os.remove(os.path.join(hf_dir, fn))
        sd = {k: v for k, v in model.state_dict().items() if not (k.endswith("weight_scale_inv") or k.endswith("activation_scale"))}
        # tied embeddings share storage (embed_tokens / lm_head); keep one name per storage, as save_model does
        # keep the embedding name for a tied embed_tokens / lm_head pair: llama.cpp needs token_embd.weight
        # and ties output.weight to it when output.weight is absent (2026-09-09: dropping embed_tokens gave
        # "tensor 'token_embd.weight' not found")
        for kept, dups in _remove_duplicate_names(sd).items():
            group = [kept] + list(dups)
            keep = next((g for g in group if "embed_tokens" in g), kept)
            for d in group:
                if d != keep:
                    sd.pop(d, None)
        sd = {k: (v.to(torch.bfloat16) if v.is_floating_point() else v).contiguous() for k, v in sd.items()}
        save_file(sd, os.path.join(hf_dir, "model.safetensors"), metadata={"format": "pt"})
        for idx in glob.glob(os.path.join(hf_dir, "*.index.json")):
            os.remove(idx)   # a shard index left behind sends the converter to shards that no longer exist (patrick 14B, 2026-09-09)
        log(f"rewrote {len(sd)} tensors in bf16 (shared tensors deduplicated); shard index removed")
    # the converter needs the generation/chat template files the snapshot had
    # (2026-09-09: any base, not only Qwen3-4B; Ministral 3 also needs params.json, tekken.json, chat_template.jinja)
    snaps = glob.glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub",
                                   "models--" + base.replace("/", "--"), "snapshots", "*"))
    if snaps and os.path.isdir(snaps[0]):
        for fn in os.listdir(snaps[0]):
            src = os.path.join(snaps[0], fn)
            if os.path.isfile(src) and not fn.endswith((".safetensors", ".bin", ".gguf", ".pt", ".index.json")) and not os.path.exists(os.path.join(hf_dir, fn)):
                shutil.copy(src, hf_dir)   # never the snapshot's shard index: a sharded snapshot (14B) would send the converter to shards that do not exist here
    del model
    log("converting to F16 GGUF")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    rc = subprocess.run([sys.executable, CONVERT, hf_dir, "--outtype", "f16", "--outfile", out_gguf],
                        env=env, capture_output=True, text=True)
    if rc.returncode != 0 or not os.path.exists(out_gguf):
        raise SystemExit(f"convert failed: {rc.stderr[-800:]}")
    shutil.rmtree(hf_dir, ignore_errors=True)
    log(f"-> {out_gguf} ({os.path.getsize(out_gguf)/2**30:.1f} GB) in {time.time()-t0:.0f}s")
    return out_gguf


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--base", default=config.BASE_MODEL)
    ap.add_argument("--out", default="")
    ap.add_argument("--device", default="cpu")
    a = ap.parse_args()
    merge(a.adapter, a.base, a.out or None, a.device)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
