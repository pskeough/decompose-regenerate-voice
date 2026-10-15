#!/usr/bin/env bash
# One pod's work for a within-author corpus-size series (2026-09-10). Launched by
# cloud/launch_pod.sh through DR_SWEEP_SCRIPT with the usual three arguments:
#   bash cloud/run_pod_size.sh <author> "<sizes>|<arms>" <ignored>
# e.g. bash cloud/run_pod_size.sh doctorow "25,50,100,150,215,300,525,50s1|A0,A1" 0
# Resumable: rerun with the same arguments. Ends with "pod sweep complete" so the
# pullers know the pod is finished.
set -uo pipefail
AUTHOR="$1"; SPEC="${2:-25,50,100,150|A0,A1}"
SIZES="${SPEC%%|*}"; ARMS="${SPEC#*|}"; [ "$ARMS" = "$SPEC" ] && ARMS="A0,A1"
cd /workspace/decompose_regenerate
export DR_CLOUD=1 DR_LLAMA_SERVER=/workspace/llama.cpp/build/bin/llama-server DR_LLAMA_TOOLS=/workspace/llama.cpp PYTHONIOENCODING=utf-8
echo "$(date +%H:%M) size series start: author=$AUTHOR sizes=$SIZES arms=$ARMS"
if [ ! -f /workspace/models/Qwen3-4B-F16.gguf ]; then
  echo "$(date +%H:%M) no 4B GGUF at /workspace/models/Qwen3-4B-F16.gguf; setup incomplete"
  echo "$(date +%H:%M) pod sweep complete"
  exit 1
fi
python -u cloud/size_pod.py --author "$AUTHOR" --sizes "$SIZES" --arms "$ARMS" --base Qwen/Qwen3-4B \
  --gguf /workspace/models/Qwen3-4B-F16.gguf --slots 32 > logs/size_pod.log 2>&1
rc=$?
echo "$(date +%H:%M) size series exit $rc"
tail -n 3 logs/size_pod.log
echo "$(date +%H:%M) pod sweep complete"
