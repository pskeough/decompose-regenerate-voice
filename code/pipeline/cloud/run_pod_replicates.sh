#!/usr/bin/env bash
# Replicate base runs on a pod (2026-09-11): for each "tag|HF id|GGUF|slots" line in the spec, generate
# {author}_base{tag}_r2 with the six base arms (five for a private author), exactly as the family
# script's replicate() does, so every size has its own twice-generated floor. No training.
# Launched by cloud/launch_pod.sh through DR_SWEEP_SCRIPT; arg2 = spec lines joined with ";".
#   bash cloud/run_pod_replicates.sh chesterton "8b|Qwen/Qwen3-8B|/workspace/models/Qwen3-8B-F16.gguf|16;14b|Qwen/Qwen3-14B|/workspace/models/Qwen3-14B-F16.gguf|16" 0
set -uo pipefail
AUTHOR="$1"; SPEC="${2:-}"
cd /workspace/decompose_regenerate
export DR_CLOUD=1 DR_LLAMA_SERVER=/workspace/llama.cpp/build/bin/llama-server DR_LLAMA_TOOLS=/workspace/llama.cpp PYTHONIOENCODING=utf-8
echo "$(date +%H:%M) replicate sweep start: author=$AUTHOR spec=$SPEC"
ARMS="A0,A1,A2,A3,A4,A5"
case "$AUTHOR" in patrick_v2|h_private) ARMS="A0,A2,A3,A4,A5";; esac
echo "$SPEC" | tr ';' '\n' | while IFS='|' read -r TAG HF GGUF SLOTS; do
  [ -n "$TAG" ] || continue
  RUN="${AUTHOR}_base${TAG}_r2"
  if [ -f "runs/$RUN/gens.jsonl" ] && ls runs/$RUN/s3_manifest* >/dev/null 2>&1; then echo "$(date +%H:%M) $RUN exists"; continue; fi
  if [ ! -f "$GGUF" ]; then echo "$(date +%H:%M) $RUN: $GGUF missing (setup did not convert it); skip"; continue; fi
  echo "$(date +%H:%M) generating $RUN ($HF, $SLOTS slots)"
  python dr/llamacpp.py start --model "$GGUF" --slots "$SLOTS" --url http://127.0.0.1:8089 || { echo "$(date +%H:%M) $RUN: server failed"; continue; }
  python dr/s3_generate.py --author "$AUTHOR" --run "$RUN" --arms "$ARMS" --backend llamacpp --base "$HF" --slots "$SLOTS" --server http://127.0.0.1:8089 \
    > "logs/replicate_${RUN}.log" 2>&1 && echo "$(date +%H:%M) $RUN done" || echo "$(date +%H:%M) $RUN FAILED (logs/replicate_${RUN}.log)"
  python dr/llamacpp.py stop --url http://127.0.0.1:8089
  rm -f "$GGUF"   # 16-28 GB each; the run is what travels
done
echo "$(date +%H:%M) pod sweep complete"
