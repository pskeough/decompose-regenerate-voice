"""GPU smoke test for the generation and training paths. No API calls.

1. tokenizer + chat template with thinking disabled: show the prompt tail
2. s4.encode() on a synthetic pair view: prefix property and mask boundary
3. load the base in bf16, free the vision tower, generate 80 tokens from an
   A0-style prompt with a synthetic brief; report VRAM and speed
4. one forward/backward with a LoRA at max_len to measure training peak VRAM

    python dr/smoke.py            # steps 1-3
    python dr/smoke.py --train    # adds step 4
"""
from __future__ import annotations

import argparse
import gc
import os
import sys
import time

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import log  # noqa: E402
from dr.prompts import Prompts  # noqa: E402
from dr.s3_generate import chat_ids, clean  # noqa: E402
from dr.s4_train import encode  # noqa: E402

BRIEF = """SETTING: A drawing room in a large house in the evening, after dinner.
CHARACTERS PRESENT: Mrs. Ansell, the hostess; her nephew Gerald, recently returned from abroad.
NARRATIVE STANCE: third person, past tense, following Mrs. Ansell.
LENGTH: about 450 words.
EVENTS, IN ORDER:
1. Mrs. Ansell notices that Gerald has not touched his coffee.
2. She asks him whether the journey tired him; he says it did not.
3. She recalls the letter he sent from Florence and how little it said.
4. Gerald admits he has decided not to take the post his uncle arranged.
5. Mrs. Ansell does not answer at once and looks at the fire.
6. She tells him his uncle will need to be told before the end of the week.
7. Gerald says he will tell him himself.
WHAT THE READER LEARNS: Gerald has refused the family's plan for him. Mrs. Ansell had suspected it. The refusal will cause trouble with the uncle.
WHAT THE PASSAGE IS DOING: shows a decision being disclosed and received."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=config.BASE_MODEL)
    ap.add_argument("--train", action="store_true")
    ap.add_argument("--max-len", type=int, default=config.LORA["max_len"])
    a = ap.parse_args()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    P = Prompts()
    tok = AutoTokenizer.from_pretrained(a.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    ids = chat_ids(tok, P.gen_system(), P.gen_user("A0", BRIEF))
    log(f"prompt tokens {len(ids)}; tail: {tok.decode(ids[-24:])!r}")
    im_end = tok.convert_tokens_to_ids("<|im_end|>") if "<|im_end|>" in tok.get_vocab() else None
    log(f"im_end id {im_end}, eos id {tok.eos_token_id}, pad id {tok.pad_token_id}")

    view = {"framing": "pair", "system": P.gen_system(), "user": P.gen_user("A0", BRIEF),
            "target": "Mrs. Ansell had observed, without appearing to, that the coffee stood untouched at his elbow.\n\nIt was not like him."}
    e = encode(tok, view, a.max_len, im_end)
    full_prompt = tok.decode(e["input_ids"][: e["n_prompt"]])
    first_target = tok.decode(e["input_ids"][e["n_prompt"]: e["n_prompt"] + 10])
    log(f"encode: n_prompt {e['n_prompt']} n_target {e['n_target']}; prompt ends {full_prompt[-40:]!r}; "
        f"target starts {first_target!r}")
    assert first_target.startswith("Mrs"), "mask boundary is wrong"
    assert e["labels"][e["n_prompt"] - 1] == -100 and e["labels"][e["n_prompt"]] != -100

    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(a.base, dtype=torch.bfloat16, device_map="cuda:0")
    freed = False
    for holder in (model, getattr(model, "model", None)):
        for attr in ("visual", "vision_tower", "vision_model"):
            if holder is not None and hasattr(holder, attr) and getattr(holder, attr) is not None:
                setattr(holder, attr, None)
                freed = True
    gc.collect()
    torch.cuda.empty_cache()
    log(f"loaded {type(model).__name__} in {time.time()-t0:.0f}s; vision freed={freed}; "
        f"{torch.cuda.memory_allocated()/2**30:.2f} GB resident")
    model.eval()
    x = torch.tensor([ids]).cuda()
    torch.manual_seed(0)
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(x, max_new_tokens=80, do_sample=True, temperature=0.8, top_p=0.95,
                             pad_token_id=tok.pad_token_id)
    dt = time.time() - t0
    raw = tok.decode(out[0, x.shape[1]:], skip_special_tokens=True)
    text, flags = clean(raw)
    log(f"80 tokens in {dt:.1f}s ({80/dt:.1f} tok/s); flags {flags}")
    print("---- sample ----\n" + text + "\n----------------")

    if a.train:
        from peft import LoraConfig, get_peft_model
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
        model.config.use_cache = False
        model.train()
        model = get_peft_model(model, LoraConfig(r=config.LORA["r"], lora_alpha=config.LORA["alpha"],
                                                 lora_dropout=0.05, task_type="CAUSAL_LM",
                                                 target_modules=config.LORA["targets"],
                                                 exclude_modules=r".*(visual|vision).*"))
        model.print_trainable_parameters()
        L = a.max_len
        ids_t = torch.randint(100, 5000, (1, L)).cuda()
        torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        loss = model(input_ids=ids_t, labels=ids_t).loss
        loss.backward()
        torch.cuda.synchronize()
        log(f"train step at len {L}: {time.time()-t0:.1f}s, peak {torch.cuda.max_memory_allocated()/2**30:.2f} GB, "
            f"loss {float(loss):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
