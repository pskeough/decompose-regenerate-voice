#!/usr/bin/env bash
# One-time (per pod) environment build for the decompose-regenerate GPU stages.
# Idempotent: every step skips when its product exists. Run from /workspace.
#
#   bash cloud/setup.sh Qwen/Qwen3-8B [Qwen/Qwen3-14B ...]
#
# Products: /workspace/llama.cpp/build/bin/llama-server (tag b10435, CUDA),
#           /workspace/models/<Model>-F16.gguf per base, pinned python deps.
set -euo pipefail
cd /workspace
export DR_CLOUD=1
LLAMA_TAG="${LLAMA_TAG:-b10435}"          # the same release the local runs used
TORCH_VER="${TORCH_VER:-2.11.0}"

echo "== python deps"
python -c "import torch, sys; v=torch.__version__; print('torch', v); sys.exit(0 if v.startswith('${TORCH_VER}') else 1)" \
  || { pip install --quiet "torch==${TORCH_VER}" --index-url https://download.pytorch.org/whl/cu128; pip uninstall -y -q torchvision torchaudio || true; }
# a torchvision built for the template's torch breaks transformers' import chain after the torch pin (seen 2026-09-07)
python -c "import torchvision" 2>/dev/null && python -c "import torchvision, torch; torchvision.ops.nms" 2>/dev/null || pip uninstall -y -q torchvision torchaudio || true
pip install --quiet -r cloud/requirements.txt
python - <<'PY'
import torch, transformers, peft, numpy
assert torch.cuda.is_available(), "no CUDA device visible"
print("torch", torch.__version__, "cuda", torch.version.cuda, "gpu", torch.cuda.get_device_name(0))
print("transformers", transformers.__version__, "peft", peft.__version__, "numpy", numpy.__version__)
PY

echo "== llama.cpp ${LLAMA_TAG} (CUDA build)"
if [ ! -x llama.cpp/build/bin/llama-server ]; then
  command -v cmake >/dev/null || { apt-get update -qq && apt-get install -y -qq cmake build-essential git rsync >/dev/null; }
  [ -d llama.cpp ] || git clone --quiet --branch "${LLAMA_TAG}" --depth 1 https://github.com/ggml-org/llama.cpp llama.cpp
  export PATH=/usr/local/cuda/bin:$PATH          # nvcc is not on PATH in the RunPod devel template
  cmake -S llama.cpp -B llama.cpp/build -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc -DCMAKE_CUDA_ARCHITECTURES="${CUDA_ARCHS:-86;89;90}" >/dev/null   # A6000/A40, L40S/4090, H100
  cmake --build llama.cpp/build --config Release -j "$(nproc)" --target llama-server >/dev/null
fi
llama.cpp/build/bin/llama-server --version 2>&1 | head -n 2 || true
export DR_LLAMA_SERVER=/workspace/llama.cpp/build/bin/llama-server

echo "== base models -> F16 GGUF"
mkdir -p models
for BASE in "$@"; do
  NAME="${BASE##*/}"
  OUT="models/${NAME}-F16.gguf"
  if [ ! -f "$OUT" ]; then
    hf download "$BASE" >/dev/null 2>&1 || huggingface-cli download "$BASE" >/dev/null
    SNAP=$(python -c "import glob,os;print(sorted(glob.glob(os.path.expanduser('~/.cache/huggingface/hub/models--${BASE//\//--}/snapshots/*')))[0])")
    python llama.cpp/convert_hf_to_gguf.py "$SNAP" --outfile "$OUT" --outtype f16 >/dev/null   # the tag-b10435 clone carries its own gguf-py and conversion package
  fi
  ls -la "$OUT"
done
echo "== setup complete"
