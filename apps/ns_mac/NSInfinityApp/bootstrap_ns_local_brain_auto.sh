#!/usr/bin/env bash
set -u

MODEL_REPO="${MODEL_REPO:-lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit}"
MODEL_DIR="${MODEL_DIR:-/Volumes/NSExternal/models/Qwen3-30B-A3B-Thinking-2507-MLX}"
VENV_DIR="${VENV_DIR:-$HOME/ns_local_brain_env}"
ENV_FILE="${ENV_FILE:-.ns_local_brain.env}"
LOG_FILE="${LOG_FILE:-./bootstrap_ns_local_brain.log}"
TEST_PROMPT="${TEST_PROMPT:-Explain NS architecture in 3 bullet points}"
MAX_RETRIES="${MAX_RETRIES:-3}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

exec > >(tee -a "$LOG_FILE") 2>&1

step() { echo; echo "== $* =="; }
warn() { echo "WARN: $*" >&2; }
fail() { echo "ERROR: $*" >&2; exit 1; }

have_cmd() { command -v "$1" >/dev/null 2>&1; }

run_with_retry() {
  local n=1
  local max="${2:-$MAX_RETRIES}"
  local cmd="$1"
  while true; do
    echo "RUN [$n/$max]: $cmd"
    if eval "$cmd"; then
      return 0
    fi
    if [ "$n" -ge "$max" ]; then
      return 1
    fi
    n=$((n + 1))
    sleep 2
  done
}

check_disk_space() {
  step "Checking disk space"
  local target_root
  target_root="$(dirname "$MODEL_DIR")"
  mkdir -p "$target_root" || true
  df -h "$target_root" || true
}

check_python() {
  step "Checking Python"
  have_cmd "$PYTHON_BIN" || fail "python3 not found"
  "$PYTHON_BIN" --version || fail "python3 exists but failed"
}

create_or_reuse_venv() {
  step "Creating or reusing virtual environment"
  if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR" || fail "venv creation failed"
  fi
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate" || fail "failed to activate venv"
  echo "Using venv: $VENV_DIR"
  python --version || fail "venv python failed"
}

upgrade_pip() {
  step "Upgrading pip inside venv"
  run_with_retry "python -m pip install --upgrade pip" 2 || fail "pip upgrade failed"
}

install_packages() {
  step "Installing required packages"
  run_with_retry "python -m pip install huggingface_hub mlx mlx-lm" 2 || fail "package install failed"
}

discover_hf_cli() {
  step "Resolving Hugging Face CLI"
  HF_DOWNLOAD_CMD=""

  if have_cmd huggingface-cli; then
    HF_DOWNLOAD_CMD='huggingface-cli download'
    echo "Using CLI: huggingface-cli"
    return 0
  fi

  if python -c "import shutil,sys; sys.exit(0 if shutil.which('huggingface-cli') else 1)"; then
    HF_DOWNLOAD_CMD='huggingface-cli download'
    echo "Using CLI from PATH: huggingface-cli"
    return 0
  fi

  if python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('huggingface_hub.commands.huggingface_cli') else 1)"; then
    HF_DOWNLOAD_CMD='python -m huggingface_hub.commands.huggingface_cli download'
    echo "Using module CLI: huggingface_hub.commands.huggingface_cli"
    return 0
  fi

  if [ -x "$VENV_DIR/bin/huggingface-cli" ]; then
    HF_DOWNLOAD_CMD="\"$VENV_DIR/bin/huggingface-cli\" download"
    echo "Using venv CLI binary: $VENV_DIR/bin/huggingface-cli"
    return 0
  fi

  fail "Could not resolve a working Hugging Face CLI"
}

hf_login_if_needed() {
  step "Checking Hugging Face authentication"
  set +e
  local whoami_output
  whoami_output="$(python - <<'PY'
from huggingface_hub import HfApi
try:
    HfApi().whoami()
    print("AUTH_OK")
except Exception:
    print("AUTH_MISSING")
PY
)"
  set -e

  if echo "$whoami_output" | grep -q "AUTH_OK"; then
    echo "Hugging Face auth already present"
    return 0
  fi

  warn "No Hugging Face auth detected"
  warn "If prompted, paste your Hugging Face token"

  if have_cmd huggingface-cli; then
    set +e
    huggingface-cli login
    set -e
  elif [ -x "$VENV_DIR/bin/huggingface-cli" ]; then
    set +e
    "$VENV_DIR/bin/huggingface-cli" login
    set -e
  elif python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('huggingface_hub.commands.huggingface_cli') else 1)"; then
    set +e
    python -m huggingface_hub.commands.huggingface_cli login
    set -e
  fi
}

download_model_once() {
  mkdir -p "$MODEL_DIR" || fail "Failed to create model directory: $MODEL_DIR"
  local cmd="$HF_DOWNLOAD_CMD \"$MODEL_REPO\" --local-dir \"$MODEL_DIR\""
  echo "Download command: $cmd"
  set +e
  eval "$cmd"
  local rc=$?
  set -e
  return $rc
}

repair_after_download_failure() {
  step "Analyzing download failure"
  if grep -qi "401\|403\|gated\|access to model" "$LOG_FILE"; then
    warn "Auth or gated model issue detected"
    hf_login_if_needed
    return 0
  fi

  if grep -qi "No space left on device" "$LOG_FILE"; then
    fail "Disk full. Free space on /Volumes/NSExternal and rerun."
  fi

  if grep -qi "Temporary failure\|timed out\|Connection reset\|network" "$LOG_FILE"; then
    warn "Network issue detected, retrying"
    return 0
  fi

  if grep -qi "No module named huggingface_hub.__main__" "$LOG_FILE"; then
    warn "Bad Hugging Face module invocation detected earlier, correcting"
    discover_hf_cli
    return 0
  fi

  warn "Unknown download failure, retrying"
  return 0
}

download_model() {
  step "Downloading model"
  local attempt=1
  while [ "$attempt" -le "$MAX_RETRIES" ]; do
    echo "Download attempt $attempt/$MAX_RETRIES"
    if download_model_once; then
      echo "Model download complete"
      return 0
    fi
    repair_after_download_failure
    attempt=$((attempt + 1))
    sleep 2
  done
  fail "Model download failed after $MAX_RETRIES attempts"
}

write_env_file() {
  step "Writing NS env file"
  cat > "$ENV_FILE" <<EOF2
NS_LOCAL_TEXT_MODEL=$MODEL_DIR
NS_LOCAL_RUNTIME=mlx
NS_LOCAL_LAYER_ENABLED=true
NS_LOCAL_LAYER_DEFAULT_LOCAL_ONLY=true
NS_LOCAL_LAYER_ALLOW_WORKER_ESCALATION=false
NS_LOCAL_LAYER_MODEL_CACHE_ROOT=/Volumes/NSExternal/models
EOF2
  echo "Wrote $ENV_FILE"
}

verify_model_files() {
  step "Verifying model files"
  ls -lah "$MODEL_DIR" || fail "Model directory missing"
}

test_inference_once() {
  python -m mlx_lm.generate \
    --model "$MODEL_DIR" \
    --prompt "$TEST_PROMPT"
}

repair_after_test_failure() {
  step "Analyzing test failure"
  if grep -qi "No module named mlx_lm" "$LOG_FILE"; then
    warn "mlx-lm missing, reinstalling"
    install_packages
    return 0
  fi

  if grep -qi "out of memory\|OOM\|metal" "$LOG_FILE"; then
    warn "Possible memory or Metal issue"
    return 0
  fi

  if grep -qi "tokenizer\|config" "$LOG_FILE"; then
    warn "Possible incomplete model download, retrying"
    download_model
    return 0
  fi

  warn "Unknown inference failure, retrying"
  return 0
}

test_inference() {
  step "Testing local inference"
  local attempt=1
  while [ "$attempt" -le 2 ]; do
    echo "Inference test attempt $attempt/2"
    if test_inference_once; then
      echo "Inference test passed"
      return 0
    fi
    repair_after_test_failure
    attempt=$((attempt + 1))
    sleep 2
  done
  fail "Inference test failed"
}

print_next_steps() {
  step "Done"
  echo "Virtual env: $VENV_DIR"
  echo "Model dir:    $MODEL_DIR"
  echo "Env file:     $ENV_FILE"
  echo
  echo "Later:"
  echo "source \"$VENV_DIR/bin/activate\""
  echo "set -a; source \"$ENV_FILE\"; set +a"
}

main() {
  check_python
  check_disk_space
  create_or_reuse_venv
  upgrade_pip
  install_packages
  discover_hf_cli
  download_model
  write_env_file
  verify_model_files
  test_inference
  print_next_steps
}

main "$@"
