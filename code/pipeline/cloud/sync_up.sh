#!/usr/bin/env bash
# Push the minimal workspace to the pod: code, prompts, config, converter, and
# the prepared author data (splits, briefs, guide, quant, retrieval). No runs,
# no corpora, no models. tar over ssh (Git Bash has no rsync).
#   bash cloud/sync_up.sh <ssh-host> <ssh-port> chesterton,mansfield
set -euo pipefail
HOST="$1"; PORT="$2"; AUTHORS="${3:-}"
KEY="${DR_SSH_KEY:-$HOME/.ssh/dr_runpod}"
SSH="ssh -i $KEY -p $PORT -o StrictHostKeyChecking=accept-new -o BatchMode=yes root@$HOST"
PATHS="dr cloud PROMPTS.md tools/llama.cpp/convert_hf_to_gguf.py tools/llama.cpp/convert_lora_to_gguf.py tools/llama.cpp/gguf-py"
IFS=',' read -ra AUS <<< "$AUTHORS"
for au in "${AUS[@]}"; do [ -n "$au" ] && PATHS="$PATHS data/$au"; done
$SSH "mkdir -p /workspace/decompose_regenerate/runs /workspace/decompose_regenerate/logs"
# shellcheck disable=SC2086
tar czf - --exclude='__pycache__' --exclude='_api_cache' $PATHS | $SSH "cd /workspace/decompose_regenerate && tar xzf - --no-same-owner && cp -r cloud /workspace/ && chmod +x cloud/*.sh /workspace/cloud/*.sh"
echo "remote hashes:"; $SSH "cd /workspace/decompose_regenerate && sha256sum PROMPTS.md dr/config.py | cut -c1-12,66-"
echo "local hashes:";  sha256sum PROMPTS.md dr/config.py | cut -c1-12,66-
echo "sync_up done: the two hash pairs must match"
