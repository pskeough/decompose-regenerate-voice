#!/usr/bin/env bash
# One pod's work for a list of authors: 4B, 8B (train lane beside a generate
# lane), then 14B sequentially, then optional fill-in runs (existing adapters,
# missing arms). Resumable: rerun with the same args.
#   bash cloud/run_pod_sweep.sh "wharton,mansfield" [fillin_authors] [train_limit]
# Stages (2026-09-09): logs/stages.txt on the pod lists the stages this pod
# runs ("4b 8b", "14b", default all three), re-read before each stage so a
# running pod can be handed the 14B stage back if its 14B pod never appears.
set -uo pipefail
AUTHORS="$1"; FILLIN="${2:-}"; TRAIN_LIMIT="${3:-0}"   # 3rd arg (2026-09-09): cap on fit examples, 1290 = Chesterton
cd /workspace/decompose_regenerate
export DR_CLOUD=1 DR_LLAMA_SERVER=/workspace/llama.cpp/build/bin/llama-server DR_LLAMA_TOOLS=/workspace/llama.cpp PYTHONIOENCODING=utf-8
has() { local s="4b 8b 14b"; [ -f logs/stages.txt ] && s="$(tr -d '\r\n' < logs/stages.txt)"; case " $s " in *" $1 "*) return 0;; esac; return 1; }
echo "$(date +%H:%M) pod sweep start: authors=$AUTHORS fillin=$FILLIN stages=$( [ -f logs/stages.txt ] && tr -d '\r\n' < logs/stages.txt || echo '4b 8b 14b')"

if has 4b && [ -f /workspace/models/Qwen3-4B-F16.gguf ]; then
  # 4B stage (added 2026-09-09 for the contemporary-author expansion): the
  # same two-lane layout at 32 slots; the 4B F16 is 8 GB so 32 x 5120 ctx
  # fits beside the trainer. Names match the local 4B runs (author_base4b,
  # author_paire6_4b), which the bridge cell showed agree within 2 SE.
  echo "$(date +%H:%M) 4B two lanes (32 slots)"
  export DR_ALLOW_SHARED_GPU=1
  C4="--authors $AUTHORS --base Qwen/Qwen3-4B --gguf /workspace/models/Qwen3-4B-F16.gguf --model-tag 4b --slots 32 --train-limit $TRAIN_LIMIT"
  python cloud/cloud_run.py $C4 --lane train    > logs/pod_4b_train.log 2>&1 &
  T4=$!
  python cloud/cloud_run.py $C4 --lane generate > logs/pod_4b_gen.log 2>&1 &
  G4=$!
  wait $T4; wait $G4
  unset DR_ALLOW_SHARED_GPU
  python cloud/cloud_run.py $C4 --lane both >> logs/pod_4b_gen.log 2>&1
  echo "$(date +%H:%M) 4B done"
fi

if has 8b; then
  echo "$(date +%H:%M) 8B two lanes (16 slots)"
  export DR_ALLOW_SHARED_GPU=1
  C8="--authors $AUTHORS --base Qwen/Qwen3-8B --gguf /workspace/models/Qwen3-8B-F16.gguf --model-tag 8b --slots 16 --train-limit $TRAIN_LIMIT"
  python cloud/cloud_run.py $C8 --lane train    > logs/pod_8b_train.log 2>&1 &
  T=$!
  python cloud/cloud_run.py $C8 --lane generate > logs/pod_8b_gen.log 2>&1 &
  G=$!
  wait $T; wait $G
  unset DR_ALLOW_SHARED_GPU
  # a second pass catches anything a lane skipped (e.g. an adapter whose train lane died)
  python cloud/cloud_run.py $C8 --lane both >> logs/pod_8b_gen.log 2>&1
  echo "$(date +%H:%M) 8B done"
fi

if has 14b; then
  echo "$(date +%H:%M) 14B sequential (16 slots)"
  python cloud/cloud_run.py --authors $AUTHORS --base Qwen/Qwen3-14B --gguf /workspace/models/Qwen3-14B-F16.gguf --model-tag 14b --slots 16 --train-limit $TRAIN_LIMIT --lane both > logs/pod_14b.log 2>&1
  echo "$(date +%H:%M) 14B done"
fi

if [ -n "$FILLIN" ]; then
  echo "$(date +%H:%M) fill-in for $FILLIN (existing adapters, missing arms)"
  has 8b && python cloud/cloud_run.py --authors $FILLIN --base Qwen/Qwen3-8B  --gguf /workspace/models/Qwen3-8B-F16.gguf  --model-tag 8b  --slots 32 --lane both > logs/pod_fillin.log 2>&1
  has 14b && python cloud/cloud_run.py --authors $FILLIN --base Qwen/Qwen3-14B --gguf /workspace/models/Qwen3-14B-F16.gguf --model-tag 14b --slots 16 --train-limit $TRAIN_LIMIT --lane both >> logs/pod_fillin.log 2>&1
  echo "$(date +%H:%M) fill-in done"
fi
echo "$(date +%H:%M) pod sweep complete"
