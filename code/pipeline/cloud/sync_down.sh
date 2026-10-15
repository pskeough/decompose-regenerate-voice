#!/usr/bin/env bash
# Pull finished runs back: gens + manifests, training run.json + adapter (HF
# and GGUF), cloud state and logs. Checkpoints excluded. tar over ssh.
#   bash cloud/sync_down.sh <ssh-host> <ssh-port>
set -euo pipefail
HOST="$1"; PORT="$2"
python dr/backup_runs.py          # snapshot everything before any extraction (2026-09-07 rule)
KEY="${DR_SSH_KEY:-$HOME/.ssh/dr_runpod}"
SSH="ssh -i $KEY -p $PORT -o StrictHostKeyChecking=accept-new -o BatchMode=yes root@$HOST"
$SSH "cd /workspace/decompose_regenerate && python - <<'PY'
import json, os
runs = json.load(open('runs/cloud_pull_list.json'))['runs']
print(' '.join('runs/' + r for r in runs if os.path.isdir('runs/' + r)))
PY" > /tmp/dr_pull_list.txt
LIST=$(cat /tmp/dr_pull_list.txt)
echo "pulling: $LIST"
# shellcheck disable=SC2086
$SSH "cd /workspace/decompose_regenerate && tar czf - --exclude='checkpoint-*' $LIST runs/cloud_pull_list.json runs/cloud_state_*.json logs/cloud_*.log" | tar xzf - --no-same-owner --skip-old-files   # never clobber a local file (2026-09-07: a bridge run named like a local run overwrote it)
echo "sync_down done; next: python dr/score_runs.py --from-pull-list"
