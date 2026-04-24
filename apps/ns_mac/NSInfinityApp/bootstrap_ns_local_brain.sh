#!/usr/bin/env bash
set -euo pipefail

echo "== NS local brain bootstrap =="

MODEL_REPO="lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit"
MODEL_DIR="/Volumes/NSExternal/models/Qwen3-30B-A3B-Thinking-2507-MLX"
VENV_DIR="${HOME}/ns_local_brain_env"

echo
echo "1) Checking Python..."
python3 --version

echo
echo "2) Creating virtual environment at: ${VENV_DIR}"
python3 -m venv "${VENV_DIR}"

echo
echo "3) Activating virtual environment"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo
echo "4) Upgrading pip"
python -m pip install --upgrade pip

echo
echo "5) Installing required packages"
python -m pip install huggingface_hub mlx mlx-lm

echo
echo "6) Ensuring model directory exists"
mkdir -p "${MODEL_DIR}"

echo
echo "7) Downloading model from Hugging Face"
python -m huggingface_hub download "${MODEL_REPO}" \
  --local-dir "${MODEL_DIR}"

echo
echo "8) Writing NS env file"
cat > .ns_local_brain.env <<ENVVARS
NS_LOCAL_TEXT_MODEL=${MODEL_DIR}
NS_LOCAL_RUNTIME=mlx
NS_LOCAL_LAYER_ENABLED=true
NS_LOCAL_LAYER_DEFAULT_LOCAL_ONLY=true
NS_LOCAL_LAYER_ALLOW_WORKER_ESCALATION=false
NS_LOCAL_LAYER_MODEL_CACHE_ROOT=/Volumes/NSExternal/models
ENVVARS

echo
echo "9) Testing model locally"
python -m mlx_lm.generate \
  --model "${MODEL_DIR}" \
  --prompt "Explain NS architecture in 3 bullet points"

echo
echo "10) Done"
echo "Virtual env: ${VENV_DIR}"
echo "Model dir:    ${MODEL_DIR}"
echo "Env file:     .ns_local_brain.env"
echo
echo "To use later in a new shell:"
echo "source \"${VENV_DIR}/bin/activate\""
echo "set -a; source .ns_local_brain.env; set +a"
