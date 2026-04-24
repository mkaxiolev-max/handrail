#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
VENV_DIR="${VENV_DIR:-$HOME/ns_local_brain_env}"
MODEL_ROOT="${MODEL_ROOT:-/Volumes/NSExternal/models}"
STATE_ROOT="${STATE_ROOT:-$PROJECT_DIR/.ns_max_state}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.ns_local_brain.env}"
MANIFEST_FILE="${MANIFEST_FILE:-$PROJECT_DIR/ns_local_brain_manifest.json}"
ROUTE_MATRIX_FILE="${ROUTE_MATRIX_FILE:-$PROJECT_DIR/ns_local_route_matrix.json}"
COMPLETION_FILE="${COMPLETION_FILE:-$PROJECT_DIR/ns_local_completion.json}"
LOG_FILE="${LOG_FILE:-$PROJECT_DIR/ns_max_local_matrix.log}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MAX_RETRIES="${MAX_RETRIES:-3}"

# Local matrix only
TEXT_BRAIN_REPO="${TEXT_BRAIN_REPO:-lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit}"
TEXT_BRAIN_DIR="${TEXT_BRAIN_DIR:-$MODEL_ROOT/Qwen3-30B-A3B-Thinking-2507-MLX}"

VLM_FAST_REPO="${VLM_FAST_REPO:-Qwen/Qwen3-VL-2B-Thinking}"
VLM_FAST_DIR="${VLM_FAST_DIR:-$MODEL_ROOT/Qwen3-VL-2B-Thinking}"

VLM_STRONG_REPO="${VLM_STRONG_REPO:-Qwen/Qwen3-VL-32B-Instruct}"
VLM_STRONG_DIR="${VLM_STRONG_DIR:-$MODEL_ROOT/Qwen3-VL-32B-Instruct}"

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

check_storage() {
  step "Checking storage"
  mkdir -p "$MODEL_ROOT" "$STATE_ROOT"
  df -h "$MODEL_ROOT" || true
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
  step "Installing required packages"
  retry 2 python -m pip install --upgrade pip
  retry 2 python -m pip install huggingface_hub mlx mlx-lm
}

resolve_hf_cli() {
  step "Resolving Hugging Face CLI"
  if have_cmd hf; then
    HF_CMD="hf"
  elif [ -x "$VENV_DIR/bin/hf" ]; then
    HF_CMD="$VENV_DIR/bin/hf"
  else
    die "Could not find hf CLI"
  fi
  echo "Using HF CLI: $HF_CMD"
}

hf_login_optional() {
  step "Checking Hugging Face auth"
  set +e
  AUTH_STATUS="$(python - <<'PY'
from huggingface_hub import HfApi
try:
    HfApi().whoami()
    print("AUTH_OK")
except Exception:
    print("AUTH_MISSING")
PY
)"
  set -e
  echo "$AUTH_STATUS"
  if echo "$AUTH_STATUS" | grep -q "AUTH_MISSING"; then
    warn "HF auth not detected. Public repos may still download without login."
    warn "If a download fails with 401/403/gated, run: hf auth login"
  fi
}

download_repo() {
  local repo="$1"
  local target_dir="$2"

  mkdir -p "$target_dir"

  local attempt=1
  while [ "$attempt" -le "$MAX_RETRIES" ]; do
    echo "Download attempt $attempt/$MAX_RETRIES for $repo"
    set +e
    "$HF_CMD" download "$repo" --local-dir "$target_dir"
    local rc=$?
    set -e

    if [ "$rc" -eq 0 ]; then
      echo "Download complete: $repo"
      return 0
    fi

    if grep -Eqi "401|403|gated|access to model|authentication" "$LOG_FILE"; then
      warn "Auth issue detected for $repo"
      warn "Run this manually if needed: $HF_CMD auth login"
    elif grep -Eqi "No space left on device" "$LOG_FILE"; then
      die "Disk full while downloading $repo"
    elif grep -Eqi "timed out|Temporary failure|Connection reset|network" "$LOG_FILE"; then
      warn "Network issue while downloading $repo, retrying"
    else
      warn "Unknown failure while downloading $repo, retrying"
    fi

    attempt=$((attempt + 1))
    sleep 2
  done

  die "Failed to download $repo after $MAX_RETRIES attempts"
}

verify_nonempty_dir() {
  local dir="$1"
  [ -d "$dir" ] || die "Missing directory: $dir"
  local count
  count="$(find "$dir" -type f | wc -l | tr -d ' ')"
  [ "$count" -gt 0 ] || die "Directory is empty: $dir"
  echo "Verified $dir ($count files)"
}

download_local_matrix() {
  step "Downloading local matrix"
  download_repo "$TEXT_BRAIN_REPO" "$TEXT_BRAIN_DIR"
  download_repo "$VLM_FAST_REPO" "$VLM_FAST_DIR"
  download_repo "$VLM_STRONG_REPO" "$VLM_STRONG_DIR"

  verify_nonempty_dir "$TEXT_BRAIN_DIR"
  verify_nonempty_dir "$VLM_FAST_DIR"
  verify_nonempty_dir "$VLM_STRONG_DIR"
}

write_env_file() {
  step "Writing env file"
  cat > "$ENV_FILE" <<ENV
NS_LOCAL_TEXT_MODEL=$TEXT_BRAIN_DIR
NS_LOCAL_VLM_FAST_MODEL=$VLM_FAST_DIR
NS_LOCAL_VLM_STRONG_MODEL=$VLM_STRONG_DIR
NS_LOCAL_RUNTIME=mlx
NS_LOCAL_LAYER_ENABLED=true
NS_LOCAL_LAYER_DEFAULT_LOCAL_ONLY=true
NS_LOCAL_LAYER_ALLOW_WORKER_ESCALATION=false
NS_LOCAL_LAYER_MODEL_CACHE_ROOT=$MODEL_ROOT
NS_MAX_CONTEXT=262144
NS_ADJUDICATION_REQUIRED=true
NS_RECEIPT_LOGGING=full_trace
ENV
  cat "$ENV_FILE"
}

write_manifest() {
  step "Writing local manifest"
  cat > "$MANIFEST_FILE" <<JSON
{
  "system_id": "NS-INFINITY-V21",
  "sovereignty_tier": "ULTRA",
  "active_models": {
    "text_reasoner": {
      "repo": "$TEXT_BRAIN_REPO",
      "path": "$TEXT_BRAIN_DIR",
      "runtime": "MLX-LM",
      "tier": "L1",
      "role": "brain",
      "status": "active"
    },
    "vlm_fast": {
      "repo": "$VLM_FAST_REPO",
      "path": "$VLM_FAST_DIR",
      "runtime": "registry_downloaded",
      "tier": "L2",
      "role": "fast_eye",
      "status": "active"
    },
    "vlm_strong": {
      "repo": "$VLM_STRONG_REPO",
      "path": "$VLM_STRONG_DIR",
      "runtime": "registry_downloaded",
      "tier": "L3",
      "role": "strong_eye",
      "status": "active"
    }
  },
  "runtimes": {
    "local": "MLX-LM",
    "worker": "vLLM-CUDA"
  },
  "governance": {
    "routing": "capability_weighted",
    "receipt_logging": "full_trace",
    "handrail_policy": "adjudicated_execution"
  }
}
JSON
  cat "$MANIFEST_FILE"
}

write_route_matrix() {
  step "Writing route matrix"
  cat > "$ROUTE_MATRIX_FILE" <<JSON
{
  "tiers": {
    "L0": "optional_local_utility",
    "L1": "$TEXT_BRAIN_REPO",
    "L2": "$VLM_FAST_REPO",
    "L3": "$VLM_STRONG_REPO",
    "W1": ["moonshotai/Kimi-K2.6", "deepseek-ai/DeepSeek-V3.2", "Qwen/Qwen3-VL-30B-A3B-Thinking"]
  },
  "routing": [
    {
      "when": "text && complexity >= 0.4 && sensitivity in [private,restricted]",
      "route": "L1"
    },
    {
      "when": "visual && quick_triage == true",
      "route": "L2"
    },
    {
      "when": "visual && complexity >= 0.5",
      "route": "L3"
    },
    {
      "when": "batch || very_large_context || heavy_codebase_transform",
      "route": "W1"
    }
  ]
}
JSON
  cat "$ROUTE_MATRIX_FILE"
}

test_text_brain() {
  step "Testing sovereign brain"
  local attempt=1
  while [ "$attempt" -le 2 ]; do
    echo "Inference attempt $attempt/2"
    set +e
    python -m mlx_lm.generate \
      --model "$TEXT_BRAIN_DIR" \
      --max-tokens 250 \
      --temp 0.0 \
      --prompt "You are the NS Sovereign Brain. Define the relationship between Handrail and Alexandria in 2 sentences."
    local rc=$?
    set -e

    if [ "$rc" -eq 0 ]; then
      echo "Text brain inference passed"
      return 0
    fi

    if grep -Eqi "No module named mlx_lm" "$LOG_FILE"; then
      warn "mlx-lm missing unexpectedly; reinstalling"
      install_packages
    elif grep -Eqi "out of memory|OOM|metal" "$LOG_FILE"; then
      warn "Memory or Metal issue detected"
      warn "Close other apps or use a smaller MLX build if this persists"
    elif grep -Eqi "tokenizer|config|No such file|not found" "$LOG_FILE"; then
      warn "Model files may be incomplete; re-downloading brain"
      download_repo "$TEXT_BRAIN_REPO" "$TEXT_BRAIN_DIR"
    else
      warn "Unknown inference failure; retrying once"
    fi

    attempt=$((attempt + 1))
    sleep 2
  done

  die "Text brain inference failed"
}

write_completion() {
  step "Writing completion state"
  cat > "$COMPLETION_FILE" <<JSON
{
  "status": "DONE",
  "local_brain_online": true,
  "local_matrix_downloaded": true,
  "models": {
    "text_reasoner": "$TEXT_BRAIN_REPO",
    "vlm_fast": "$VLM_FAST_REPO",
    "vlm_strong": "$VLM_STRONG_REPO"
  },
  "paths": {
    "text_reasoner": "$TEXT_BRAIN_DIR",
    "vlm_fast": "$VLM_FAST_DIR",
    "vlm_strong": "$VLM_STRONG_DIR"
  },
  "runtime": "MLX-LM",
  "env_written": true,
  "manifest_written": true,
  "route_matrix_written": true,
  "text_inference_verified": true,
  "worker_models_downloaded": false,
  "next_required": [
    "bind manifest into Alexandria",
    "register L1/L2/L3 in model_router",
    "emit model_download_receipt/model_bind_receipt/model_exec_receipt",
    "add /local_layer/health endpoint",
    "bootstrap worker tier separately via vLLM"
  ]
}
JSON
  cat "$COMPLETION_FILE"
}

print_summary() {
  step "NS-MAX CORE ONLINE"
  echo "DONE"
  echo "Venv:        $VENV_DIR"
  echo "Model root:  $MODEL_ROOT"
  echo "Env file:    $ENV_FILE"
  echo "Manifest:    $MANIFEST_FILE"
  echo "Routes:      $ROUTE_MATRIX_FILE"
  echo "Completion:  $COMPLETION_FILE"
  echo "Log:         $LOG_FILE"
  echo
  echo "Later use:"
  echo "source \"$VENV_DIR/bin/activate\""
  echo "set -a; source \"$ENV_FILE\"; set +a"
}

main() {
  check_python
  check_storage
  create_or_activate_venv
  install_packages
  resolve_hf_cli
  hf_login_optional
  download_local_matrix
  write_env_file
  write_manifest
  write_route_matrix
  test_text_brain
  write_completion
  print_summary
}

main "$@"
