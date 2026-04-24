#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
VENV_DIR="${VENV_DIR:-$HOME/ns_local_brain_env}"
MODEL_REPO="${MODEL_REPO:-lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit}"
MODEL_DIR="${MODEL_DIR:-/Volumes/NSExternal/models/Qwen3-30B-A3B-Thinking-2507-MLX}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.ns_local_brain.env}"
LOG_FILE="${LOG_FILE:-$PROJECT_DIR/bootstrap_ns_local_brain.log}"
MANIFEST_FILE="${MANIFEST_FILE:-$PROJECT_DIR/ns_local_brain_manifest.json}"
TEST_PROMPT="${TEST_PROMPT:-Explain NS architecture in 3 bullet points}"
MAX_RETRIES="${MAX_RETRIES:-3}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

exec > >(tee -a "$LOG_FILE") 2>&1

step() { echo; echo "== $* =="; }
warn() { echo "WARN: $*" >&2; }
die() { echo "ERROR: $*" >&2; exit 1; }
have_cmd() { command -v "$1" >/dev/null 2>&1; }

on_error() {
  local line="$1"
  warn "Script failed near line $line"
  warn "See log: $LOG_FILE"
}
trap 'on_error $LINENO' ERR

retry() {
  local attempts="$1"
  shift
  local n=1
  while true; do
    echo "RUN [$n/$attempts]: $*"
    if "$@"; then
      return 0
    fi
    if [ "$n" -ge "$attempts" ]; then
      return 1
    fi
    n=$((n + 1))
    sleep 2
  done
}

check_python() {
  step "Checking Python"
  have_cmd "$PYTHON_BIN" || die "python3 not found"
  "$PYTHON_BIN" --version
}

check_disk() {
  step "Checking target storage"
  mkdir -p "$(dirname "$MODEL_DIR")"
  df -h "$(dirname "$MODEL_DIR")" || true
}

create_or_activate_venv() {
  step "Creating or activating virtual environment"
  if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
  python --version
  which python
}

install_packages() {
  step "Installing required packages in venv"
  retry 2 python -m pip install --upgrade pip
  retry 2 python -m pip install "huggingface_hub[cli]" mlx mlx-lm
}

resolve_hf_cli() {
  step "Resolving Hugging Face CLI"
  if have_cmd hf; then
    HF_CMD="hf"
    echo "Using CLI: hf"
    return 0
  fi
  if [ -x "$VENV_DIR/bin/hf" ]; then
    HF_CMD="$VENV_DIR/bin/hf"
    echo "Using CLI: $HF_CMD"
    return 0
  fi
  die "Could not find hf CLI after install"
}

hf_login_optional() {
  step "Checking Hugging Face auth"
  set +e
  python - <<'PY'
from huggingface_hub import HfApi
try:
    HfApi().whoami()
    print("AUTH_OK")
except Exception:
    print("AUTH_MISSING")
PY
  local rc=$?
  set -e
  if grep -q "AUTH_OK" "$LOG_FILE"; then
    echo "HF auth already present"
    return 0
  fi
  warn "HF auth not detected. Public repos may still download without login."
  warn "If download fails with 401/403/gated, the script will prompt for login."
}

hf_login_if_needed() {
  step "Logging into Hugging Face"
  "$HF_CMD" auth login
}

download_model() {
  step "Downloading model"
  mkdir -p "$MODEL_DIR"

  local attempt=1
  while [ "$attempt" -le "$MAX_RETRIES" ]; do
    echo "Download attempt $attempt/$MAX_RETRIES"
    set +e
    "$HF_CMD" download "$MODEL_REPO" --local-dir "$MODEL_DIR"
    local rc=$?
    set -e

    if [ "$rc" -eq 0 ]; then
      echo "Model download complete"
      return 0
    fi

    if grep -Eqi "401|403|gated|access to model|authentication" "$LOG_FILE"; then
      warn "Auth issue detected; attempting login"
      hf_login_if_needed
    elif grep -Eqi "No space left on device" "$LOG_FILE"; then
      die "Disk full at $(dirname "$MODEL_DIR")"
    elif grep -Eqi "timed out|Temporary failure|Connection reset|network" "$LOG_FILE"; then
      warn "Network issue detected; retrying"
    else
      warn "Download failed for an unknown reason; retrying"
    fi

    attempt=$((attempt + 1))
    sleep 2
  done

  die "Model download failed after $MAX_RETRIES attempts"
}

verify_model_dir_nonempty() {
  step "Verifying model directory"
  [ -d "$MODEL_DIR" ] || die "Model directory missing"
  find "$MODEL_DIR" -maxdepth 2 | head -100
  local count
  count="$(find "$MODEL_DIR" -type f | wc -l | tr -d ' ')"
  [ "$count" -gt 0 ] || die "Model directory is empty"
  echo "Model file count: $count"
}

write_env_file() {
  step "Writing NS env file"
  cat > "$ENV_FILE" <<ENV
NS_LOCAL_TEXT_MODEL=$MODEL_DIR
NS_LOCAL_RUNTIME=mlx
NS_LOCAL_LAYER_ENABLED=true
NS_LOCAL_LAYER_DEFAULT_LOCAL_ONLY=true
NS_LOCAL_LAYER_ALLOW_WORKER_ESCALATION=false
NS_LOCAL_LAYER_MODEL_CACHE_ROOT=/Volumes/NSExternal/models
ENV
  cat "$ENV_FILE"
}

write_manifest() {
  step "Writing manifest"
  cat > "$MANIFEST_FILE" <<JSON
{
  "local_text_model": "$MODEL_REPO",
  "resolved_model_dir": "$MODEL_DIR",
  "runtime": "mlx",
  "locality": "mac_local",
  "tier": "L1",
  "status": "active_pending_test"
}
JSON
  cat "$MANIFEST_FILE"
}

test_inference() {
  step "Testing local inference"
  local attempt=1
  while [ "$attempt" -le 2 ]; do
    echo "Inference attempt $attempt/2"
    set +e
    python -m mlx_lm.generate \
      --model "$MODEL_DIR" \
      --prompt "$TEST_PROMPT"
    local rc=$?
    set -e

    if [ "$rc" -eq 0 ]; then
      echo "Inference test passed"
      return 0
    fi

    if grep -Eqi "No module named mlx_lm" "$LOG_FILE"; then
      warn "mlx-lm missing unexpectedly; reinstalling"
      install_packages
    elif grep -Eqi "out of memory|OOM|metal" "$LOG_FILE"; then
      warn "Memory or Metal issue detected"
      warn "Close other apps and retry, or switch to a smaller model"
    elif grep -Eqi "tokenizer|config|No such file|not found" "$LOG_FILE"; then
      warn "Model files may be incomplete; retrying download"
      download_model
    else
      warn "Unknown inference failure; retrying once"
    fi

    attempt=$((attempt + 1))
    sleep 2
  done

  die "Inference test failed"
}

mark_done() {
  step "Finalizing"
  python - <<PY
from pathlib import Path
p = Path("$MANIFEST_FILE")
text = p.read_text()
text = text.replace('"active_pending_test"', '"DONE"')
p.write_text(text)
print(p.read_text())
PY

  echo
  echo "DONE"
  echo "Virtual env: $VENV_DIR"
  echo "Model dir:   $MODEL_DIR"
  echo "Env file:    $ENV_FILE"
  echo "Manifest:    $MANIFEST_FILE"
  echo "Log:         $LOG_FILE"
  echo
  echo "Use later with:"
  echo "source \"$VENV_DIR/bin/activate\""
  echo "set -a; source \"$ENV_FILE\"; set +a"
}

main() {
  check_python
  check_disk
  create_or_activate_venv
  install_packages
  resolve_hf_cli
  hf_login_optional
  download_model
  verify_model_dir_nonempty
  write_env_file
  write_manifest
  test_inference
  mark_done
}

main "$@"
