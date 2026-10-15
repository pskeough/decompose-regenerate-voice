#!/usr/bin/env bash
# Scale sweep on one pod (L40S 48 GB, 2026-09-07): 8B on patrick_v2 with two
# lanes, then 14B on chesterton and patrick_v2 sequentially (a 14B trainer
# and a 14B server do not fit beside each other on 48 GB). Every step is
# resumable: rerunning this script skips finished products.
set -uo pipefail
cd /workspace/decompose_regenerate
export DR_CLOUD=1 DR_LLAMA_SERVER=/workspace/llama.cpp/build/bin/llama-server DR_LLAMA_TOOLS=/workspace/llama.cpp
export PYTHONIOENCODING=utf-8
echo "$(date +%H:%M) scale sweep start"

echo "$(date +%H:%M) 8B patrick_v2: two lanes"
export DR_ALLOW_SHARED_GPU=1
C8="--authors patrick_v2 --base Qwen/Qwen3-8B --gguf /workspace/models/Qwen3-8B-F16.gguf --model-tag 8b --slots 16"   # 16 slots: a 32-slot 8B server (28 GB) plus a trainer OOMs a 48 GB card (2026-09-07)
python cloud/cloud_run.py $C8 --lane train    > logs/cloud_8b_train.log 2>&1 &
T=$!
python cloud/cloud_run.py $C8 --lane generate > logs/cloud_8b_gen.log 2>&1 &
G=$!
wait $T; wait $G
unset DR_ALLOW_SHARED_GPU
echo "$(date +%H:%M) 8B patrick_v2 done"

echo "$(date +%H:%M) 14B chesterton, patrick_v2: sequential (--lane both), 16 slots"
python cloud/cloud_run.py --authors chesterton,patrick_v2 --base Qwen/Qwen3-14B --gguf /workspace/models/Qwen3-14B-F16.gguf --model-tag 14b --slots 16 --lane both > logs/cloud_14b.log 2>&1
echo "$(date +%H:%M) 14B done"

python - <<'PY'
import json, os
runs = []
for r in ("patrick_v2_base8b", "patrick_v2_paire6_8b", "train_patrick_v2_pair_e6_8b",
          "chesterton_base14b", "chesterton_paire6_14b", "train_chesterton_pair_e6_14b",
          "patrick_v2_base14b", "patrick_v2_paire6_14b", "train_patrick_v2_pair_e6_14b"):
    if os.path.isdir(os.path.join("runs", r)):
        runs.append(r)
json.dump({"runs": runs}, open("runs/cloud_pull_list.json", "w"))
print("pull list:", runs)
PY
echo "$(date +%H:%M) scale sweep complete"
