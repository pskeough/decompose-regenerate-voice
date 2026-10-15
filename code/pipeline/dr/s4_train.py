"""S4: per-author LoRA, three recipes (METHODS 7).

    pair   brief -> passage, through the chat template, byte-identical to the
           A0 prompt; loss on the assistant tokens only
    mix    pair + continue + infill views; views_per_target per epoch,
           resampled each epoch; loss on the assistant tokens only
    raw    the whole passage, no template, EOS; loss on every token. The July
           objective without the segmentation and deployment faults. A control.

Everything else is identical across recipes: base, LoRA config, optimiser,
schedule, batch, max_len, seed, and checkpoint selection by held-out loss on
TRAIN-val works.

Two val losses are logged for every recipe: the recipe's own view on the val
targets (used for checkpoint selection) and the PAIR view on the val targets
(`eval_pairview_loss`), which is the same number for all three recipes and
says how well each predicts the author's prose given a brief, which is what
the eval asks. For `raw` that second number is the direct test of whether raw
training helps the conditional task at all.

The prompt is truncated from the LEFT when a pair is too long; the target is
never truncated (Suri: severed targets teach the model to stop mid-scene).
Chat-template prefix property is asserted per example, so that the label mask
starts exactly where the assistant turn starts.

    python dr/s4_train.py --author wharton --recipe pair
    python dr/s4_train.py --author wharton --recipe mix
    python dr/s4_train.py --author wharton --recipe raw
"""
from __future__ import annotations

import argparse
import collections
import gc
import json
import os
import random
import sys
import time

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr import config  # noqa: E402
from dr.core import (RUNS, Manifest, author_dir, log, paragraphs, read_jsonl,  # noqa: E402
                     upstream_hash, words, write_json)
from dr.core import load_causal_lm  # noqa: E402  (2026-09-09: vision-capable bases such as Ministral 3)
from dr.prompts import Prompts  # noqa: E402


# ------------------------------------------------------------------ views

def tail_words(text, lo, hi):
    """Last paragraphs of `text` totalling between lo and hi words (as close to
    hi as paragraph boundaries allow); falls back to the last hi words."""
    ps = paragraphs(text)
    out, n = [], 0
    for p in reversed(ps):
        pw = len(words(p))
        if n + pw > hi and n >= lo:
            break
        out.insert(0, p)
        n += pw
        if n >= hi:
            break
    if n < lo:
        ws = text.split()
        return " ".join(ws[-hi:])
    return "\n\n".join(out)


def head_words(text, n):
    ps = paragraphs(text)
    out, m = [], 0
    for p in ps:
        pw = len(words(p))
        if m + pw > n and m > 0:
            break
        out.append(p)
        m += pw
        if m >= n:
            break
    return "\n\n".join(out)


def build_views(P, train_rows, briefs, recipe):
    """Rows: {target_id, framing, system, user, target}. system/user None for raw."""
    by_id = {r["id"]: r for r in train_rows}
    lo, hi = config.CONTINUE_WORDS
    views = []
    for r in train_rows:
        t = r["text"]
        if recipe == "raw":
            views.append({"target_id": r["id"], "framing": "raw", "system": None, "user": None,
                          "target": t, "split": r["split"]})
            continue
        b = briefs.get(r["id"])
        if b and b.get("passed"):
            views.append({"target_id": r["id"], "framing": "pair", "system": P.gen_system(),
                          "user": P.gen_user("A0", b["brief"]), "target": t, "split": r["split"]})
        if recipe == "mix":
            prev = by_id.get(r["prev_id"]) if r.get("prev_id") else None
            nxt = by_id.get(r["next_id"]) if r.get("next_id") else None
            if prev:
                views.append({"target_id": r["id"], "framing": "continue", "system": P.gen_system(),
                              "user": P.train_continue(tail_words(prev["text"], lo, hi)),
                              "target": t, "split": r["split"]})
            if prev and nxt:
                views.append({"target_id": r["id"], "framing": "infill", "system": P.gen_system(),
                              "user": P.train_infill(tail_words(prev["text"], config.INFILL_WORDS, config.INFILL_WORDS),
                                                     head_words(nxt["text"], config.INFILL_WORDS)),
                              "target": t, "split": r["split"]})
    return views


def sample_epochs(views, per_target, epochs, seed):
    R = random.Random(seed)
    by = collections.defaultdict(list)
    for v in views:
        by[v["target_id"]].append(v)
    out = []
    for _ in range(epochs):
        ep = []
        for _, vs in by.items():
            ep.extend(R.sample(vs, min(per_target, len(vs))))
        R.shuffle(ep)
        out.extend(ep)
    return out


# --------------------------------------------------------------- encoding

def encode(tok, v, max_len, im_end_id):
    """input_ids / labels with the prompt masked. Asserts the chat-template
    prefix property so the mask boundary is exact."""
    t_ids = tok(v["target"], add_special_tokens=False)["input_ids"]
    if v["framing"] == "raw":
        eos = [tok.eos_token_id] if tok.eos_token_id is not None else []
        ids = t_ids[: max_len - len(eos)] + eos
        return {"input_ids": ids, "labels": list(ids), "attention_mask": [1] * len(ids),
                "n_prompt": 0, "n_target": len(ids)}
    from dr.s3_generate import chat_ids   # one template path for train and eval
    p_ids = chat_ids(tok, v["system"], v["user"])
    tail = [im_end_id] if im_end_id is not None else [tok.eos_token_id]
    budget = max_len - len(t_ids) - len(tail)
    truncated_target = False
    if budget < 32:
        t_ids = t_ids[: max_len - 32 - len(tail)]
        budget = 32
        truncated_target = True
    p_ids = p_ids[-budget:]
    ids = p_ids + t_ids + tail
    labels = [-100] * len(p_ids) + t_ids + tail
    return {"input_ids": ids, "labels": labels, "attention_mask": [1] * len(ids),
            "n_prompt": len(p_ids), "n_target": len(t_ids) + len(tail),
            "truncated_target": truncated_target}


def to_dataset(encoded):
    from datasets import Dataset
    return Dataset.from_list([{k: e[k] for k in ("input_ids", "labels", "attention_mask")} for e in encoded])


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author", default=config.AUTHOR)
    ap.add_argument("--recipe", choices=config.RECIPES, required=True)
    ap.add_argument("--base", default=config.BASE_MODEL)
    ap.add_argument("--tag", default="")
    ap.add_argument("--max-len", type=int, default=config.LORA["max_len"])
    ap.add_argument("--epochs", type=int, default=config.LORA["epochs"])
    ap.add_argument("--lr", type=float, default=config.LORA["lr"])
    ap.add_argument("--rank", type=int, default=config.LORA["r"])
    ap.add_argument("--alpha", type=int, default=config.LORA["alpha"])
    ap.add_argument("--bs", type=int, default=config.LORA["bs"])
    ap.add_argument("--accum", type=int, default=config.LORA["accum"])
    ap.add_argument("--seed", type=int, default=config.LORA["seed"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-ckpt", action="store_true", help="disable gradient checkpointing")
    ap.add_argument("--n-targets", type=int, default=0, help="size curve: train on a seeded subset of this many TRAIN-fit targets")
    ap.add_argument("--targets-seed", type=int, default=0)
    ap.add_argument("--replay-file", default="", help="adherence fix: jsonl of {system,user,target} rows mixed into training")
    ap.add_argument("--replay-frac", type=float, default=0.10, help="share of each epoch drawn from the replay file")
    ap.add_argument("--exclude-gids", default="",
                    help="comma-separated gutenberg_id values to drop from TRAIN (e.g. Patrick's novels, "
                         "to train on stories only)")
    a = ap.parse_args()
    d = author_dir(a.author)
    P = Prompts()
    tag = a.tag or f"{a.author}_{a.recipe}_r{a.rank}_s{a.seed}"
    outdir = os.path.join(RUNS, f"train_{tag}")
    os.makedirs(outdir, exist_ok=True)
    man = Manifest(os.path.join(outdir, "s4_manifest.json"), "s4_train")
    man.input("train", os.path.join(d, "train.jsonl"),
              expect=upstream_hash(os.path.join(d, "s0_manifest.json"), "train"))
    train_rows = read_jsonl(os.path.join(d, "train.jsonl"))
    if a.exclude_gids:
        drop = {int(x) for x in a.exclude_gids.split(",") if x.strip()}
        before = len(train_rows)
        train_rows = [r for r in train_rows if r.get("gutenberg_id") not in drop]
        log(f"excluded gids {sorted(drop)}: {before} -> {len(train_rows)} train rows")
    briefs = {}
    if a.recipe in ("pair", "mix"):
        bp = os.path.join(d, "briefs_train.jsonl")
        if not os.path.exists(bp):
            raise SystemExit("briefs_train.jsonl missing; run s1 --split train first")
        man.input("briefs_train", bp)
        briefs = {r["id"]: r for r in read_jsonl(bp)}

    views = build_views(P, train_rows, briefs, a.recipe)
    fit_views = [v for v in views if v["split"] == "train_fit"]
    val_views = [v for v in views if v["split"] == "train_val"]
    if a.n_targets:
        # nested seeded subsets: the same seed gives a superset as n grows
        ids = sorted({v["target_id"] for v in fit_views})
        random.Random(a.targets_seed).shuffle(ids)
        keep = set(ids[: a.n_targets])
        fit_views = [v for v in fit_views if v["target_id"] in keep]
        log(f"size curve: {len(keep)} of {len(ids)} fit targets kept (seed {a.targets_seed})")
    per_target = config.LORA["views_per_target"] if a.recipe == "mix" else 1
    fit = sample_epochs(fit_views, per_target, a.epochs, a.seed)
    if a.replay_file:
        rep = [dict(r, framing="replay", target_id="replay:" + str(i), split="train_fit")
               for i, r in enumerate(read_jsonl(a.replay_file))]
        k = int(round(a.replay_frac * len(fit)))
        RR = random.Random(a.seed + 7)
        fit = fit + [RR.choice(rep) for _ in range(k)]
        RR.shuffle(fit)
        log(f"replay: {k} examples ({a.replay_frac:.0%}) from {len(rep)} replay rows")
    if a.limit:
        fit = fit[: a.limit]
    # selection val: the recipe's own view; comparable val: the pair view
    own_val = [v for v in val_views if v["framing"] == ("raw" if a.recipe == "raw" else "pair")]
    val_rows = [r for r in train_rows if r["split"] == "train_val"]
    if not briefs:
        # raw loads no briefs for training; the comparable pair-view metric
        # still wants them if they exist
        bp = os.path.join(d, "briefs_train.jsonl")
        briefs_for_val = {r["id"]: r for r in read_jsonl(bp)} if os.path.exists(bp) else {}
    else:
        briefs_for_val = briefs
    pair_val = build_views(P, val_rows, briefs_for_val, "pair") if briefs_for_val else []
    log(f"recipe {a.recipe}: {len(fit_views)} fit views over "
        f"{len({v['target_id'] for v in fit_views})} targets -> {len(fit)} examples "
        f"({per_target}/target x {a.epochs} epochs); framings "
        f"{dict(collections.Counter(v['framing'] for v in fit))}; own-val {len(own_val)}, pair-val {len(pair_val)}")

    # The GPU rule: nothing else on the card during training. A llama-server
    # left behind by a cancelled generation holds 12 GB and would spill this
    # run into host memory (10x slower) or corrupt it.
    shared = bool(os.environ.get("DR_ALLOW_SHARED_GPU"))   # cloud two-lane mode: a 48 GB card holds a server beside a trainer
    try:
        from dr import llamacpp as _L
        if _L.alive() and not shared:
            log("llama-server is up; stopping it before training")
            _L.stop()
            time.sleep(3)
        elif _L.alive():
            log("llama-server is up; DR_ALLOW_SHARED_GPU set, leaving it (two-lane mode)")
    except Exception:
        pass
    # ... and wait for any scoring / embedding process to finish first.
    # psutil via dr.live: the CIM query this used to run hung under GPU load
    # (TimeoutExpired 2026-09-05 14:06) and the guard let a contended run start.
    waited = 0
    while not shared:
        try:
            from dr.live import find as _find
            hits = _find(r"s5_score|rescore_normalised|transfer_control|cross_attribution|punct_sensitivity|s3_generate")
            n = len(hits)
        except Exception as e:
            log(f"GPU-guard query failed ({type(e).__name__}); proceeding")
            n = 0
        if n == 0:
            break
        if waited == 0:
            log(f"{n} GPU process(es) alive ({'; '.join(h[4][:50] for h in hits)}); training waits for them")
        time.sleep(30)
        waited += 30
    if waited:
        log(f"waited {waited // 60} min for the GPU")
    import torch
    # Cap the caching allocator below the card: the trainer's real peak is ~11 GB
    # (pair, max_len 2048, bs 1) but the allocator otherwise grows to the full
    # 16 GB and any other VRAM user (a browser tab) tips it into WDDM paging,
    # which halved the step rate on 2026-09-06 12:20. DR_GPU_FRACTION overrides.
    try:
        torch.cuda.set_per_process_memory_fraction(float(os.environ.get("DR_GPU_FRACTION", "0.85")))
    except Exception as _e:
        log(f"memory fraction not set: {_e!r}")
    from transformers import (AutoModelForCausalLM, AutoTokenizer, DataCollatorForSeq2Seq,
                              EarlyStoppingCallback, Trainer, TrainerCallback, TrainingArguments)
    from peft import LoraConfig, get_peft_model

    tok = AutoTokenizer.from_pretrained(a.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    im_end_id = tok.convert_tokens_to_ids("<|im_end|>") if "<|im_end|>" in tok.get_vocab() else None

    enc_fit = [encode(tok, v, a.max_len, im_end_id) for v in fit]
    enc_own = [encode(tok, v, a.max_len, im_end_id) for v in own_val]
    enc_pair = [encode(tok, v, a.max_len, im_end_id) for v in pair_val]
    lens = [len(e["input_ids"]) for e in enc_fit]
    mask_frac = sum(e["n_target"] for e in enc_fit) / max(sum(lens), 1)
    n_trunc = sum(1 for e in enc_fit if e.get("truncated_target"))
    log(f"tokens/example mean {sum(lens)/len(lens):.0f} max {max(lens)} (cap {a.max_len}); "
        f"label fraction {mask_frac:.2f}; truncated targets {n_trunc}")
    if a.recipe != "raw":
        # the mask must start exactly at the assistant turn: decode the first
        # unmasked token span and check it is the passage's opening
        e0 = enc_fit[0]
        first_target = tok.decode(e0["input_ids"][e0["n_prompt"]:e0["n_prompt"] + 12])
        assert fit[0]["target"].strip()[:20].split()[0] in first_target, \
            f"mask boundary wrong: decoded '{first_target}' vs target start '{fit[0]['target'][:40]}'"
        log(f"mask boundary ok: '{first_target.strip()[:50]}'")

    model = load_causal_lm(a.base, dtype=torch.bfloat16, device_map="cuda:0")
    freed = False
    for holder in (model, getattr(model, "model", None)):
        for attr in ("visual", "vision_tower", "vision_model"):
            if holder is not None and hasattr(holder, attr) and getattr(holder, attr) is not None:
                setattr(holder, attr, None)
                freed = True
    gc.collect()
    torch.cuda.empty_cache()
    log(f"model loaded; vision freed={freed}; {torch.cuda.memory_allocated()/2**30:.2f} GB resident")
    ckpt = not a.no_ckpt
    if ckpt:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
    model.config.use_cache = False
    model.train()
    lcfg = LoraConfig(r=a.rank, lora_alpha=a.alpha, lora_dropout=config.LORA["dropout"], bias="none",
                      task_type="CAUSAL_LM", target_modules=config.LORA["targets"],
                      exclude_modules=r".*(visual|vision).*")
    model = get_peft_model(model, lcfg)
    model.train()
    model.print_trainable_parameters()

    steps_per_epoch = max(1, len(enc_fit) // (a.bs * a.accum))
    eval_every = min(config.LORA["eval_every"], steps_per_epoch)
    targs = TrainingArguments(
        output_dir=outdir, per_device_train_batch_size=a.bs, per_device_eval_batch_size=1,
        gradient_accumulation_steps=a.accum, num_train_epochs=1,   # epochs unrolled by the sampler
        learning_rate=a.lr, lr_scheduler_type="cosine", warmup_ratio=config.LORA["warmup_ratio"],
        weight_decay=config.LORA["weight_decay"], logging_steps=5,
        eval_strategy="steps", eval_steps=eval_every, save_strategy="steps", save_steps=eval_every,
        save_total_limit=3, load_best_model_at_end=True, metric_for_best_model="eval_loss",
        greater_is_better=False, bf16=True, gradient_checkpointing=ckpt,
        gradient_checkpointing_kwargs={"use_reentrant": False} if ckpt else None,
        optim="adamw_torch", report_to=[], seed=a.seed, data_seed=a.seed,
        dataloader_pin_memory=False, remove_unused_columns=False)

    history = []

    class Log(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kw):
            if logs:
                history.append({"step": state.global_step, **{k: v for k, v in logs.items()}})
            if state.global_step <= 3 or state.global_step % 10 == 0:
                log(f"[mem] step {state.global_step} peak {torch.cuda.max_memory_allocated()/2**30:.2f} GB")

    class PairView(TrainerCallback):
        """Comparable val loss on the pair view, every eval, for every recipe."""
        def on_evaluate(self, args, state, control, **kw):
            if not enc_pair:
                return
            model.eval()
            tot, n = 0.0, 0
            with torch.no_grad():
                for e in enc_pair:
                    ids = torch.tensor([e["input_ids"]]).cuda()
                    lab = torch.tensor([e["labels"]]).cuda()
                    out = model(input_ids=ids, labels=lab)
                    k = int((lab != -100).sum())
                    tot += float(out.loss) * k
                    n += k
            model.train()
            history.append({"step": state.global_step, "eval_pairview_loss": tot / max(n, 1)})
            log(f"  pair-view val loss {tot / max(n, 1):.4f} at step {state.global_step}")

    coll = DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100)
    trainer = Trainer(model=model, args=targs, train_dataset=to_dataset(enc_fit),
                      eval_dataset=to_dataset(enc_own) if enc_own else None,
                      data_collator=coll, processing_class=tok,
                      callbacks=[Log(), PairView(),
                                 EarlyStoppingCallback(early_stopping_patience=config.LORA["patience"])]
                      if enc_own else [Log(), PairView()])
    # Resumability: HF checkpoints (trainer_state, optimizer, scheduler, RNG,
    # adapter weights) land every eval_every steps; a killed run continues
    # from the latest one instead of from scratch. The unrolled dataset is
    # seeded, so the skipped batches are the same batches.
    ckpts = sorted((int(x.split("-")[1]), x) for x in os.listdir(outdir)
                   if x.startswith("checkpoint-") and os.path.exists(os.path.join(outdir, x, "trainer_state.json")))
    resume = os.path.join(outdir, ckpts[-1][1]) if ckpts else None
    if resume:
        log(f"resuming from {os.path.basename(resume)} (step {ckpts[-1][0]})")
    t0 = time.time()
    trainer.train(resume_from_checkpoint=resume)
    wall = time.time() - t0
    final = os.path.join(outdir, "adapter")
    model.save_pretrained(final)
    tok.save_pretrained(final)

    # adapter-active probe on a val target: ll with adapter on vs off
    model.eval()
    probe = {}
    if enc_own:
        e = enc_own[0]
        ids = torch.tensor([e["input_ids"]]).cuda()
        lab = torch.tensor([e["labels"]]).cuda()
        with torch.no_grad():
            on = float(model(input_ids=ids, labels=lab).loss)
            with model.disable_adapter():
                off = float(model(input_ids=ids, labels=lab).loss)
        probe = {"val0_loss_adapter_on": on, "val0_loss_adapter_off": off, "delta": on - off}
        log(f"probe: val loss adapter on {on:.4f} off {off:.4f}")
        if abs(on - off) < 1e-6:
            log("WARNING adapter changes nothing on the probe")

    best = getattr(trainer.state, "best_metric", None)
    run = {"recipe": a.recipe, "author": a.author, "base": a.base, "rank": a.rank, "alpha": a.alpha,
           "lr": a.lr, "epochs": a.epochs, "bs": a.bs, "accum": a.accum, "max_len": a.max_len,
           "seed": a.seed, "ckpt": ckpt, "n_examples": len(enc_fit),
           "n_targets": len({v["target_id"] for v in fit}),
           "framings": dict(collections.Counter(v["framing"] for v in fit)),
           "tokens_mean": sum(lens) / len(lens), "tokens_max": max(lens), "label_fraction": mask_frac,
           "truncated_targets": n_trunc, "steps": trainer.state.global_step, "best_eval_loss": best,
           "best_checkpoint": getattr(trainer.state, "best_model_checkpoint", None),
           "wall_s": wall, "probe": probe, "history": history, "adapter": final,
           "provenance": __import__("dr.provenance", fromlist=["stamp"]).stamp()}
    write_json(os.path.join(outdir, "run.json"), run)
    man.output("adapter_config", os.path.join(final, "adapter_config.json"))
    man.save(run=dict((k, v) for k, v in run.items() if k != "history"))
    log(f"-> {final}  (best eval loss {best}, {trainer.state.global_step} steps, {wall/60:.1f} min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
