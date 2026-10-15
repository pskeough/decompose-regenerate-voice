#!/usr/bin/env bash
# 14B-only variant (2026-09-09): same as launch_pod.sh but the pod downloads only the 14B and its logs/stages.txt says 14b, so run_pod_sweep.sh skips the 4B and 8B stages.
# Bring one pod from "created" to "sweep running": wait for ssh, sync code and
# the authors' data (plus any existing adapter/gens dirs for fill-in), build
# the environment with the 8B and 14B, launch cloud/run_pod_sweep.sh detached.
#   bash cloud/launch_pod.sh <pod-id> <name> "wharton,mansfield" [fillin_authors]
set -uo pipefail
cd "/c/Work/Personal/Voice_Style_Retune/decompose_regenerate"
POD="$1"; NAME="$2"; AUTHORS="$3"; FILLIN="${4:-}"
KEY="$HOME/.ssh/dr_runpod"
for i in $(seq 1 40); do
  out=$(timeout 60 python cloud/pod.py ssh --id "$POD" 2>&1); echo "$out" | grep -q "^HOST=" && break; sleep 15
done
eval "$(echo "$out" | grep '^HOST=')"
[ -n "${HOST:-}" ] || { echo "$(date +%H:%M) [$NAME] no ssh port"; exit 1; }
echo "$HOST $PORT $NAME" >> "${DR_PODS_FILE:-logs/pods_0908.txt}"
SSH="ssh -i $KEY -p $PORT -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 root@$HOST"
for i in $(seq 1 20); do $SSH "true" 2>/dev/null && break; sleep 10; done
echo "$(date +%H:%M) [$NAME] ssh up at $HOST:$PORT; syncing $AUTHORS"
# a fill-in author needs its data directory too (briefs, guide, retrieval); on 2026-09-08 patrick_v2 was pushed without it and s3_generate exited at once
bash cloud/sync_up.sh "$HOST" "$PORT" "$AUTHORS${FILLIN:+,$FILLIN}" 2>&1 | tail -n 1
if [ -n "$FILLIN" ]; then
  IFS=',' read -ra FA <<< "$FILLIN"
  for au in "${FA[@]}"; do
    dirs=""; for d in runs/train_${au}_pair_e6_8b runs/train_${au}_pair_e6_14b runs/${au}_paire6_8b runs/${au}_paire6_14b runs/${au}_base8b runs/${au}_base14b; do [ -d "$d" ] && dirs="$dirs $d"; done
    [ -n "$dirs" ] && tar czf - --exclude='checkpoint-*' --exclude='*.npy' --exclude='scores*' --exclude='judge*' --exclude='coverage*' --exclude='geometry*' $dirs | $SSH "cd /workspace/decompose_regenerate && tar xzf - --no-same-owner"
    # the pod must not see local scores; state files are rebuilt from manifests on the pod
    $SSH "cd /workspace/decompose_regenerate && rm -f runs/cloud_state_${au}_8b.json runs/cloud_state_${au}_14b.json"
    echo "$(date +%H:%M) [$NAME] pushed fill-in inputs for $au"
  done
fi
MODELS="${DR_POD_MODELS:-Qwen/Qwen3-14B}"   # 14B-only pod (2026-09-09 split): downloads and converts the 14B alone
$SSH "mkdir -p /workspace/decompose_regenerate/logs && printf 14b > /workspace/decompose_regenerate/logs/stages.txt"
$SSH "cd /workspace && (setsid nohup bash cloud/setup.sh $MODELS > /workspace/setup.log 2>&1 < /dev/null &)"
echo "$(date +%H:%M) [$NAME] setup started"
for i in $(seq 1 90); do
  $SSH "grep -q 'setup complete' /workspace/setup.log" 2>/dev/null && break
  if $SSH "grep -qE 'Traceback|CMake Error' /workspace/setup.log && ! pgrep -f setup.sh >/dev/null" 2>/dev/null; then echo "$(date +%H:%M) [$NAME] SETUP FAILED"; $SSH "tail -n 5 /workspace/setup.log"; exit 1; fi
  sleep 30
done
$SSH "cd /workspace/decompose_regenerate && chmod +x cloud/*.sh && (setsid nohup bash cloud/run_pod_sweep.sh '$AUTHORS' '$FILLIN' '${DR_TRAIN_LIMIT:-0}' > logs/pod_sweep.log 2>&1 < /dev/null &)"
echo "$(date +%H:%M) [$NAME] sweep launched: $AUTHORS fillin=$FILLIN"
