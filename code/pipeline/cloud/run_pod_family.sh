#!/usr/bin/env bash
# One pod's work for a model FAMILY other than Qwen3 (2026-09-09): the same
# steps as cloud/run_pod_sweep.sh (base arms, pair-6 adapter under the same
# train limit, adapter arms), driven by a stage file instead of hard-coded
# Qwen names. Nothing about the recipe changes: cloud/cloud_run.py is called
# with the same flags the Qwen runs used, only --base, --gguf, --model-tag
# and --slots come from the stage line.
#   bash cloud/run_pod_family.sh "chesterton" cloud/family_ministral3.txt 1290
# Stage file lines: tag|hf_id|gguf|slots|mode   (mode: two-lane | sequential)
# logs/stages.txt on the pod lists the tags this pod runs (default: all).
# logs/replicate.txt (optional) holds "author tag": after that stage, the base
# arms are generated a second time as {author}_base{tag}_r2 for the replicate
# floor, exactly as base4b_r2 / mansfield_base4b_r2 were produced for Qwen.
set -uo pipefail
AUTHORS="$1"; FAMILY="${2:-cloud/family_ministral3.txt}"; TRAIN_LIMIT="${3:-0}"
cd /workspace/decompose_regenerate
export DR_CLOUD=1 DR_LLAMA_SERVER=/workspace/llama.cpp/build/bin/llama-server DR_LLAMA_TOOLS=/workspace/llama.cpp PYTHONIOENCODING=utf-8
has() { local s=""; [ -f logs/stages.txt ] && s="$(tr -d '\r\n' < logs/stages.txt)"; [ -z "$s" ] && return 0; case " $s " in *" $1 "*) return 0;; esac; return 1; }
# Ministral 3 adapters move the held-out loss far less than Qwen3 adapters (-0.07 vs -0.3 to -1.1 at 3B/4B);
# the Qwen-calibrated probe gate would reject every one. The family gate is "eval improved and probe delta below 0";
# the delta itself is recorded per adapter and reported. The Qwen sweep never writes this file.
[ -f logs/probe_delta_max.txt ] || echo 0 > logs/probe_delta_max.txt
# Adapters are served as merged F16 weights for this family (cloud_run.merge_mode): llama.cpp's LoRA converter
# does not handle Mistral3ForConditionalGeneration. Merged GGUFs are 7-29 GB, so each stage cleans up after itself.
[ -f logs/adapter_mode.txt ] || echo merge > logs/adapter_mode.txt
cleanup_stage() {  # tag hf gguf: drop the stage's HF snapshot, base GGUF and merged GGUFs once nothing on this pod needs them
  local tag="$1" hf="$2" gguf="$3" snap
  snap="$HOME/.cache/huggingface/hub/models--$(echo "$hf" | sed 's#/#--#g')"
  rm -rf "$snap" 2>/dev/null
  rm -f "$gguf" runs/train_*_"$tag"/merged.gguf 2>/dev/null
  echo "$(date +%H:%M) cleanup $tag: $(df -h /workspace | tail -n 1 | awk '{print $4}') free"
}
echo "$(date +%H:%M) family sweep start: authors=$AUTHORS family=$FAMILY train_limit=$TRAIN_LIMIT stages=$( [ -f logs/stages.txt ] && tr -d '\r\n' < logs/stages.txt || echo all)"

replicate() {  # author tag gguf slots -> {author}_base{tag}_r2 with the six base arms (five for a private author)
  local au="$1" tag="$2" gguf="$3" slots="$4" run="${1}_base${2}_r2" arms="A0,A1,A2,A3,A4,A5"
  case ",patrick_v2,h_private," in *",$au,"*) arms="A0,A2,A3,A4,A5";; esac
  [ -f "runs/$run/gens.jsonl" ] && ls runs/$run/s3_manifest* >/dev/null 2>&1 && { echo "$(date +%H:%M) replicate $run exists"; return 0; }
  echo "$(date +%H:%M) replicate $run"
  python dr/llamacpp.py start --model "$gguf" --slots "$slots" --url http://127.0.0.1:8089 || { echo "replicate: server failed"; return 1; }
  python dr/s3_generate.py --author "$au" --run "$run" --arms "$arms" --backend llamacpp --base "$5" --slots "$slots" --server http://127.0.0.1:8089 > "logs/replicate_${run}.log" 2>&1 && echo "$(date +%H:%M) replicate $run ok" || echo "$(date +%H:%M) replicate $run FAILED"
  python dr/llamacpp.py stop --url http://127.0.0.1:8089
}

grep -v '^\s*#' "$FAMILY" | grep -v '^\s*$' | tr -d '\r' | while IFS='|' read -r TAG HF GGUF SLOTS MODE; do
  has "$TAG" || { echo "$(date +%H:%M) stage $TAG not on this pod; skip"; continue; }
  [ -f "$GGUF" ] || { echo "$(date +%H:%M) stage $TAG: $GGUF missing (setup did not convert it); skip"; continue; }
  C="--authors $AUTHORS --base $HF --gguf $GGUF --model-tag $TAG --slots $SLOTS --train-limit $TRAIN_LIMIT"
  if [ "$MODE" = "two-lane" ]; then
    echo "$(date +%H:%M) $TAG two lanes ($SLOTS slots)"
    export DR_ALLOW_SHARED_GPU=1
    python cloud/cloud_run.py $C --lane train    > "logs/pod_${TAG}_train.log" 2>&1 &
    T=$!
    python cloud/cloud_run.py $C --lane generate > "logs/pod_${TAG}_gen.log" 2>&1 &
    G=$!
    wait $T; wait $G
    unset DR_ALLOW_SHARED_GPU
    python cloud/cloud_run.py $C --lane both >> "logs/pod_${TAG}_gen.log" 2>&1   # second pass catches anything a lane skipped
  else
    echo "$(date +%H:%M) $TAG sequential ($SLOTS slots)"
    python cloud/cloud_run.py $C --lane both > "logs/pod_${TAG}.log" 2>&1
  fi
  echo "$(date +%H:%M) $TAG done"
  if [ -f logs/replicate.txt ]; then
    while read -r RAU RTAG; do [ "$RTAG" = "$TAG" ] && replicate "$RAU" "$RTAG" "$GGUF" "$SLOTS" "$HF"; done < <(tr -d '\r' < logs/replicate.txt)
  fi
  cleanup_stage "$TAG" "$HF" "$GGUF"
done
echo "$(date +%H:%M) pod sweep complete"
