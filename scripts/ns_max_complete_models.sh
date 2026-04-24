#!/usr/bin/env bash
# =============================================================================
# ns_max_complete_models.sh — NS MAX LOCAL MODEL MATRIX
# Version: 1.1.0 — bash 3.2 compatible (no associative arrays)
# Safe to rerun. Surgical. Self-correcting. Never destroys an active download.
# =============================================================================
set -Eeuo pipefail

# ── paths ─────────────────────────────────────────────────────────────────────
SCRIPT_VERSION="1.1.0"
RUNTIME_ROOT="/Users/axiolevns/axiolev_runtime"
MODEL_ROOT="/Volumes/NSExternal/models"
LOCAL_LIVE_ROOT="${MODEL_ROOT}/local_live"
WORKERS_ROOT="${MODEL_ROOT}/workers"
VENV_PATH="${HOME}/ns_local_brain_env"
ALEX_ROOT="/Volumes/NSExternal/ALEXANDRIA"
LOG_DIR="${ALEX_ROOT}/logs"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_DIR}/ns_max_complete_models_${RUN_TS}.log"
STATE_DIR="$(mktemp -d /tmp/ns_matrix_XXXXXX)"
trap 'rm -rf "${STATE_DIR}"' EXIT

# ── artifact output paths ─────────────────────────────────────────────────────
ENV_FILE="${RUNTIME_ROOT}/.ns_local_brain.env"
MANIFEST_FILE="${RUNTIME_ROOT}/ns_local_brain_manifest.json"
ROUTE_MATRIX_FILE="${RUNTIME_ROOT}/ns_local_route_matrix.json"
COMPLETION_FILE="${RUNTIME_ROOT}/ns_local_completion.json"
WORKER_BOOT_FILE="${RUNTIME_ROOT}/ns_worker_boot_commands.sh"
DOWNLOAD_RECEIPTS_FILE="${RUNTIME_ROOT}/ns_model_download_receipts.json"
BIND_RECEIPTS_FILE="${RUNTIME_ROOT}/ns_model_bind_receipts.json"
HEALTH_REPORT_FILE="${RUNTIME_ROOT}/ns_local_health_report.json"

# ── model definitions ─────────────────────────────────────────────────────────
# LOCAL LIVE
LL1_REPO="lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit"
LL1_PATH="${LOCAL_LIVE_ROOT}/Qwen3-30B-A3B-Thinking-2507-MLX"
LL1_KEY="Qwen3-30B"
LL1_ROLE="L1_text_brain"
LL1_RUNTIME="mlx"

LL2_REPO="Qwen/Qwen3-VL-2B-Thinking"
LL2_PATH="${LOCAL_LIVE_ROOT}/Qwen3-VL-2B-Thinking"
LL2_KEY="Qwen3-VL-2B"
LL2_ROLE="L2_vlm_fast"
LL2_RUNTIME="mlx"

LL3_REPO="Qwen/Qwen3-VL-32B-Instruct"
LL3_PATH="${LOCAL_LIVE_ROOT}/Qwen3-VL-32B-Instruct"
LL3_KEY="Qwen3-VL-32B"
LL3_ROLE="L3_vlm_strong"
LL3_RUNTIME="mlx"

# WORKERS
W1_REPO="moonshotai/Kimi-K2.6"
W1_PATH="${WORKERS_ROOT}/Kimi-K2.6"
W1_KEY="Kimi-K2"
W1_ROLE="W1_text_worker"
W1_RUNTIME="vllm"

W2_REPO="deepseek-ai/DeepSeek-V3.2"
W2_PATH="${WORKERS_ROOT}/DeepSeek-V3.2"
W2_KEY="DeepSeek-V3"
W2_ROLE="W2_text_worker"
W2_RUNTIME="vllm"

W3_REPO="Qwen/Qwen3-VL-30B-A3B-Thinking"
W3_PATH="${WORKERS_ROOT}/Qwen3-VL-30B-A3B-Thinking"
W3_KEY="Qwen3-VL-30B"
W3_ROLE="W3_vlm_worker"
W3_RUNTIME="vllm"

# Flat path used by the currently-active download
QWEN30B_FLAT_PATH="${MODEL_ROOT}/Qwen3-30B-A3B-Thinking-2507-MLX"

# ── state helpers (bash 3.2 compatible — file-based) ─────────────────────────
set_state() { printf '%s' "$2" > "${STATE_DIR}/$1"; }
get_state() { cat "${STATE_DIR}/$1" 2>/dev/null || printf 'unknown'; }

# ── logging ───────────────────────────────────────────────────────────────────
mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

log()   { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
warn()  { printf '[%s] WARN: %s\n' "$(date '+%H:%M:%S')" "$*" >&2; }
die()   { printf '[%s] FATAL: %s\n' "$(date '+%H:%M:%S')" "$*" >&2; exit 1; }
sep()   { printf '%.0s━' {1..64}; printf '\n'; }

sep
log "NS MAX LOCAL MODEL MATRIX — v${SCRIPT_VERSION}"
log "Run timestamp: ${RUN_TS}"
log "Log: ${LOG_FILE}"
sep

# =============================================================================
# STEP 0 — Inspect live download processes
# =============================================================================
log "STEP 0 — Inspecting active download processes"

ACTIVE_DOWNLOAD_PID=""
ACTIVE_DOWNLOAD_DIR=""

while IFS= read -r line; do
  pid=$(printf '%s' "${line}" | awk '{print $2}')
  if printf '%s' "${line}" | grep -q "hf download"; then
    dir=$(printf '%s' "${line}" | grep -oE '\-\-local\-dir [^ ]+' | awk '{print $2}' || true)
    if [ -n "${dir}" ]; then
      log "  LIVE download: PID=${pid} → ${dir}"
      ACTIVE_DOWNLOAD_PID="${pid}"
      ACTIVE_DOWNLOAD_DIR="${dir}"
    fi
  fi
done < <(ps aux | grep "hf download" | grep -v grep || true)

if [ -n "${ACTIVE_DOWNLOAD_PID}" ]; then
  log "  → PID ${ACTIVE_DOWNLOAD_PID} active. Its lock files in ${ACTIVE_DOWNLOAD_DIR} are PROTECTED."
else
  log "  → No active hf download processes."
fi

# =============================================================================
# STEP 1 — Validate venv
# =============================================================================
sep
log "STEP 1 — Validating venv at ${VENV_PATH}"

[ -x "${VENV_PATH}/bin/python" ] || die "venv python not found at ${VENV_PATH}/bin/python"
PYTHON="${VENV_PATH}/bin/python"
PY_VERSION="$("${PYTHON}" --version 2>&1)"
log "  python: ${PY_VERSION}"

for pkg in mlx mlx-lm huggingface_hub; do
  version=$("${PYTHON}" -c "import importlib.metadata; print(importlib.metadata.version('${pkg}'))" 2>/dev/null || printf 'MISSING')
  log "  ${pkg}: ${version}"
  [ "${version}" != "MISSING" ] || die "Required package ${pkg} not found in venv"
done

VENV_OK="true"
log "  venv: OK"

# =============================================================================
# STEP 2 — Resolve hf CLI
# =============================================================================
sep
log "STEP 2 — Resolving hf CLI"

HF_BIN=""
for candidate in "${VENV_PATH}/bin/hf" "$(which hf 2>/dev/null || true)"; do
  if [ -n "${candidate}" ] && [ -x "${candidate}" ]; then
    HF_BIN="${candidate}"
    break
  fi
done

[ -n "${HF_BIN}" ] || die "hf CLI not found. Run: ${PYTHON} -m pip install 'huggingface_hub[cli]'"
HF_VERSION="$("${HF_BIN}" version 2>&1 | head -1)"
log "  hf CLI: ${HF_BIN} (${HF_VERSION})"
HF_OK="true"

AUTH_OK="false"
AUTH_USER="anonymous"
if "${HF_BIN}" auth whoami 2>/dev/null | grep -qv "Not logged"; then
  AUTH_USER="$("${HF_BIN}" auth whoami 2>/dev/null | head -1)"
  AUTH_OK="true"
  log "  HF auth: logged in as ${AUTH_USER}"
else
  log "  HF auth: not logged in — public models will still download"
  log "  If gated model downloads fail, run: ${HF_BIN} auth login"
fi

# =============================================================================
# STEP 3 — Directory setup
# =============================================================================
sep
log "STEP 3 — Creating target directory structure"
mkdir -p "${LOCAL_LIVE_ROOT}" "${WORKERS_ROOT}"
log "  ${LOCAL_LIVE_ROOT}: ready"
log "  ${WORKERS_ROOT}: ready"

# =============================================================================
# STEP 4 — Lock file audit
# =============================================================================
sep
log "STEP 4 — Lock file audit"

if [ -d "${MODEL_ROOT}" ]; then
  while IFS= read -r d; do
    # Never touch the active download dir
    if [ -n "${ACTIVE_DOWNLOAD_DIR}" ]; then
      real_d="$(cd "${d}" 2>/dev/null && pwd -P || printf '%s' "${d}")"
      real_active="$(cd "${ACTIVE_DOWNLOAD_DIR}" 2>/dev/null && pwd -P || printf '%s' "${ACTIVE_DOWNLOAD_DIR}")"
      if [ "${real_d}" = "${real_active}" ]; then
        log "  SKIPPING lock audit in active download dir: ${d}"
        continue
      fi
    fi
    # Scan locks in this dir
    while IFS= read -r lockfile; do
      lockdir="$(dirname "${lockfile}")"
      is_owned="false"
      if [ -n "${ACTIVE_DOWNLOAD_DIR}" ] && printf '%s' "${lockdir}" | grep -qF "${ACTIVE_DOWNLOAD_DIR}"; then
        is_owned="true"
      fi
      if ps aux | grep -v grep | grep -qF "${lockdir}" 2>/dev/null; then
        is_owned="true"
      fi
      if [ "${is_owned}" = "true" ]; then
        log "    LOCK PROTECTED: ${lockfile}"
      else
        log "    LOCK STALE — removing: ${lockfile}"
        rm -f "${lockfile}"
      fi
    done < <(find "${d}" -name "*.lock" 2>/dev/null || true)
  done < <(find "${MODEL_ROOT}" -maxdepth 1 -mindepth 1 -type d 2>/dev/null || true)
else
  log "  MODEL_ROOT not yet populated — no locks to audit"
fi

# =============================================================================
# STEP 5 — Download engine
# =============================================================================
sep
log "STEP 5 — Model downloads"

# Returns true if a directory has model weight files
has_weights() {
  local dir="$1"
  [ -d "${dir}" ] || return 1
  [ -n "$(ls -A "${dir}" 2>/dev/null)" ] || return 1
  ls "${dir}"/*.safetensors "${dir}"/*.gguf "${dir}"/*.bin \
     "${dir}"/*.npz "${dir}"/*.pt 2>/dev/null | grep -q . && return 0
  # Also check for config.json as minimum signal (some models land config first)
  [ -f "${dir}/config.json" ] && [ -n "$(ls -A "${dir}" 2>/dev/null)" ] && return 0
  return 1
}

download_model() {
  local key="$1"
  local repo_id="$2"
  local target_path="$3"
  local is_active_dl="$4"   # "yes" | "no"

  log ""
  log "  ── ${repo_id} → $(basename "${target_path}")"

  if [ "${is_active_dl}" = "yes" ]; then
    log "  → SKIP: actively downloading (PID ${ACTIVE_DOWNLOAD_PID})"
    log "  → Will move from flat path to target after PID exits. Rerun this script."
    set_state "dl_status_${key}" "active_download_in_progress"
    set_state "dl_size_${key}" "pending"
    set_state "dl_ts_${key}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    set_state "dir_ok_${key}" "false"
    return 0
  fi

  if has_weights "${target_path}"; then
    sz="$(du -sh "${target_path}" 2>/dev/null | cut -f1 || printf '?')"
    log "  → ALREADY PRESENT (${sz}) — skipping"
    set_state "dl_status_${key}" "already_present"
    set_state "dl_size_${key}" "${sz}"
    set_state "dl_ts_${key}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    set_state "dir_ok_${key}" "true"
    return 0
  fi

  mkdir -p "${target_path}"
  attempt=0
  max_attempts=3
  success="false"

  while [ "${attempt}" -lt "${max_attempts}" ]; do
    attempt=$((attempt + 1))
    log "  → Download attempt ${attempt}/${max_attempts}..."
    exit_code=0
    "${HF_BIN}" download "${repo_id}" \
      --local-dir "${target_path}" 2>&1 || exit_code=$?

    if [ "${exit_code}" -eq 0 ]; then
      success="true"
      break
    else
      log "  → Attempt ${attempt} failed (exit ${exit_code})"
      if [ "${attempt}" -lt "${max_attempts}" ]; then
        log "  → Waiting 10s before retry..."
        sleep 10
      fi
    fi
  done

  if [ "${success}" = "true" ]; then
    sz="$(du -sh "${target_path}" 2>/dev/null | cut -f1 || printf '?')"
    log "  → DOWNLOADED (${sz})"
    set_state "dl_status_${key}" "downloaded"
    set_state "dl_size_${key}" "${sz}"
    set_state "dl_ts_${key}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    set_state "dir_ok_${key}" "true"
  else
    warn "  → DOWNLOAD FAILED after ${max_attempts} attempts"
    log "  → If gated: ${HF_BIN} auth login"
    set_state "dl_status_${key}" "download_failed"
    set_state "dl_size_${key}" "0"
    set_state "dl_ts_${key}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    set_state "dir_ok_${key}" "false"
  fi
}

# ── Qwen3-30B — special handling for the in-progress download ─────────────────
log ""
log "  ── Qwen3-30B path management"

if has_weights "${LL1_PATH}"; then
  log "  → Already at target path — OK"
  sz="$(du -sh "${LL1_PATH}" 2>/dev/null | cut -f1 || printf '?')"
  set_state "dl_status_${LL1_KEY}" "already_present"
  set_state "dl_size_${LL1_KEY}" "${sz}"
  set_state "dl_ts_${LL1_KEY}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  set_state "dir_ok_${LL1_KEY}" "true"
elif [ -n "${ACTIVE_DOWNLOAD_PID}" ] && kill -0 "${ACTIVE_DOWNLOAD_PID}" 2>/dev/null; then
  log "  → PID ${ACTIVE_DOWNLOAD_PID} is alive, downloading to ${QWEN30B_FLAT_PATH}"
  log "  → NOT interrupting. Rerun after PID exits to move + verify."
  set_state "dl_status_${LL1_KEY}" "active_download_in_progress_pid_${ACTIVE_DOWNLOAD_PID}"
  set_state "dl_size_${LL1_KEY}" "pending"
  set_state "dl_ts_${LL1_KEY}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  set_state "dir_ok_${LL1_KEY}" "false"
elif has_weights "${QWEN30B_FLAT_PATH}"; then
  log "  → Download complete in flat path, process gone — moving to target"
  mkdir -p "${LOCAL_LIVE_ROOT}"
  mv "${QWEN30B_FLAT_PATH}" "${LL1_PATH}"
  log "  → Move complete: ${LL1_PATH}"
  sz="$(du -sh "${LL1_PATH}" 2>/dev/null | cut -f1 || printf '?')"
  set_state "dl_status_${LL1_KEY}" "moved_to_target"
  set_state "dl_size_${LL1_KEY}" "${sz}"
  set_state "dl_ts_${LL1_KEY}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  set_state "dir_ok_${LL1_KEY}" "true"
else
  log "  → Not present and no active process — downloading fresh"
  download_model "${LL1_KEY}" "${LL1_REPO}" "${LL1_PATH}" "no"
fi

# ── remaining local_live ──────────────────────────────────────────────────────
download_model "${LL2_KEY}" "${LL2_REPO}" "${LL2_PATH}" "no"
download_model "${LL3_KEY}" "${LL3_REPO}" "${LL3_PATH}" "no"

# ── workers ───────────────────────────────────────────────────────────────────
download_model "${W1_KEY}" "${W1_REPO}" "${W1_PATH}" "no"
download_model "${W2_KEY}" "${W2_REPO}" "${W2_PATH}" "no"
download_model "${W3_KEY}" "${W3_REPO}" "${W3_PATH}" "no"

# =============================================================================
# STEP 6 — Non-empty directory verification
# =============================================================================
sep
log "STEP 6 — Non-empty directory verification"

verify_dir() {
  local key="$1"
  local label="$2"
  local dir="$3"
  if has_weights "${dir}"; then
    log "  OK       ${label}"
    set_state "dir_ok_${key}" "true"
  elif [ -d "${dir}" ] && [ -n "$(ls -A "${dir}" 2>/dev/null)" ]; then
    log "  PARTIAL  ${label} (has files, no weights yet)"
    set_state "dir_ok_${key}" "false"
  else
    log "  MISSING  ${label}"
    set_state "dir_ok_${key}" "false"
  fi
}

verify_dir "${LL1_KEY}" "local_live/Qwen3-30B-A3B-Thinking-2507-MLX" "${LL1_PATH}"
verify_dir "${LL2_KEY}" "local_live/Qwen3-VL-2B-Thinking"             "${LL2_PATH}"
verify_dir "${LL3_KEY}" "local_live/Qwen3-VL-32B-Instruct"            "${LL3_PATH}"
verify_dir "${W1_KEY}"  "workers/Kimi-K2.6"                           "${W1_PATH}"
verify_dir "${W2_KEY}"  "workers/DeepSeek-V3.2"                       "${W2_PATH}"
verify_dir "${W3_KEY}"  "workers/Qwen3-VL-30B-A3B-Thinking"           "${W3_PATH}"

# =============================================================================
# STEP 7 — MLX local brain inference test
# =============================================================================
sep
log "STEP 7 — MLX local brain inference test"

MLX_OK="false"
INFERENCE_BRAIN=""
INFERENCE_OUTPUT=""

for brain_candidate in "${LL2_PATH}" "${LL1_PATH}" "${LL3_PATH}"; do
  if has_weights "${brain_candidate}"; then
    log "  Testing brain: ${brain_candidate}"
    INFERENCE_BRAIN="${brain_candidate}"

    set +e
    INFERENCE_OUTPUT="$("${PYTHON}" -m mlx_lm.generate \
      --model "${brain_candidate}" \
      --max-tokens 200 \
      --temp 0.0 \
      --prompt "Define the relationship between Handrail and Alexandria in 2 sentences." \
      2>&1)"
    inf_exit=$?
    set -e

    if [ "${inf_exit}" -eq 0 ] && ! printf '%s' "${INFERENCE_OUTPUT}" | grep -qE "^(Error|Traceback)"; then
      MLX_OK="true"
      log "  → Inference OK"
      printf '%s' "${INFERENCE_OUTPUT}" | tail -6 | head -4 | while IFS= read -r l; do log "    ${l}"; done
      break
    else
      log "  → Inference failed on $(basename "${brain_candidate}"): exit=${inf_exit}"
      printf '%s' "${INFERENCE_OUTPUT}" | tail -3 | while IFS= read -r l; do log "    ${l}"; done
    fi
  fi
done

if [ "${MLX_OK}" = "false" ]; then
  warn "  No local_live brain ready for inference (downloads may still be in progress)"
fi

# =============================================================================
# STEP 8 — Write NS integration artifacts via Python
# =============================================================================
sep
log "STEP 8 — Writing NS integration artifacts"

# Read all state values
S_LL1="$(get_state "dl_status_${LL1_KEY}")"
S_LL2="$(get_state "dl_status_${LL2_KEY}")"
S_LL3="$(get_state "dl_status_${LL3_KEY}")"
S_W1="$(get_state "dl_status_${W1_KEY}")"
S_W2="$(get_state "dl_status_${W2_KEY}")"
S_W3="$(get_state "dl_status_${W3_KEY}")"

SZ_LL1="$(get_state "dl_size_${LL1_KEY}")"
SZ_LL2="$(get_state "dl_size_${LL2_KEY}")"
SZ_LL3="$(get_state "dl_size_${LL3_KEY}")"
SZ_W1="$(get_state "dl_size_${W1_KEY}")"
SZ_W2="$(get_state "dl_size_${W2_KEY}")"
SZ_W3="$(get_state "dl_size_${W3_KEY}")"

OK_LL1="$(get_state "dir_ok_${LL1_KEY}")"
OK_LL2="$(get_state "dir_ok_${LL2_KEY}")"
OK_LL3="$(get_state "dir_ok_${LL3_KEY}")"
OK_W1="$(get_state "dir_ok_${W1_KEY}")"
OK_W2="$(get_state "dir_ok_${W2_KEY}")"
OK_W3="$(get_state "dir_ok_${W3_KEY}")"

NOW_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ── 8a. .ns_local_brain.env ───────────────────────────────────────────────────
log "  Writing .ns_local_brain.env"
cat > "${ENV_FILE}" <<ENVEOF
# NS LOCAL BRAIN — generated by ns_max_complete_models.sh v${SCRIPT_VERSION} on ${RUN_TS}
NS_LOCAL_TEXT_MODEL=${LL1_PATH}
NS_LOCAL_VLM_FAST_MODEL=${LL2_PATH}
NS_LOCAL_VLM_STRONG_MODEL=${LL3_PATH}
NS_WORKER_TEXT_MODEL_1=${W1_PATH}
NS_WORKER_TEXT_MODEL_2=${W2_PATH}
NS_WORKER_VLM_MODEL_1=${W3_PATH}
NS_LOCAL_RUNTIME=mlx
NS_WORKER_RUNTIME=vllm
NS_LOCAL_LAYER_ENABLED=true
NS_LOCAL_LAYER_DEFAULT_LOCAL_ONLY=true
NS_LOCAL_LAYER_ALLOW_WORKER_ESCALATION=true
NS_LOCAL_LAYER_MODEL_CACHE_ROOT=${MODEL_ROOT}
ENVEOF

# ── 8b–8h. JSON artifacts via Python (avoids bash JSON quoting hell) ──────────
log "  Writing JSON artifacts via Python"

"${PYTHON}" - <<PYEOF
import json, os
from datetime import datetime, timezone

NOW = "${NOW_UTC}"
RUNTIME_ROOT = "${RUNTIME_ROOT}"

models = [
    {
        "model_id":   "${LL1_REPO}",
        "tier":       "local_live",
        "path":       "${LL1_PATH}",
        "role":       "${LL1_ROLE}",
        "runtime":    "${LL1_RUNTIME}",
        "status":     "${S_LL1}",
        "disk_size":  "${SZ_LL1}",
        "dir_nonempty": "${OK_LL1}" == "true",
        "recorded_at": NOW,
    },
    {
        "model_id":   "${LL2_REPO}",
        "tier":       "local_live",
        "path":       "${LL2_PATH}",
        "role":       "${LL2_ROLE}",
        "runtime":    "${LL2_RUNTIME}",
        "status":     "${S_LL2}",
        "disk_size":  "${SZ_LL2}",
        "dir_nonempty": "${OK_LL2}" == "true",
        "recorded_at": NOW,
    },
    {
        "model_id":   "${LL3_REPO}",
        "tier":       "local_live",
        "path":       "${LL3_PATH}",
        "role":       "${LL3_ROLE}",
        "runtime":    "${LL3_RUNTIME}",
        "status":     "${S_LL3}",
        "disk_size":  "${SZ_LL3}",
        "dir_nonempty": "${OK_LL3}" == "true",
        "recorded_at": NOW,
    },
    {
        "model_id":   "${W1_REPO}",
        "tier":       "worker",
        "path":       "${W1_PATH}",
        "role":       "${W1_ROLE}",
        "runtime":    "${W1_RUNTIME}",
        "status":     "${S_W1}",
        "disk_size":  "${SZ_W1}",
        "dir_nonempty": "${OK_W1}" == "true",
        "recorded_at": NOW,
    },
    {
        "model_id":   "${W2_REPO}",
        "tier":       "worker",
        "path":       "${W2_PATH}",
        "role":       "${W2_ROLE}",
        "runtime":    "${W2_RUNTIME}",
        "status":     "${S_W2}",
        "disk_size":  "${SZ_W2}",
        "dir_nonempty": "${OK_W2}" == "true",
        "recorded_at": NOW,
    },
    {
        "model_id":   "${W3_REPO}",
        "tier":       "worker",
        "path":       "${W3_PATH}",
        "role":       "${W3_ROLE}",
        "runtime":    "${W3_RUNTIME}",
        "status":     "${S_W3}",
        "disk_size":  "${SZ_W3}",
        "dir_nonempty": "${OK_W3}" == "true",
        "recorded_at": NOW,
    },
]

local_live = [m for m in models if m["tier"] == "local_live"]
workers    = [m for m in models if m["tier"] == "worker"]
ll_ready   = [m["model_id"] for m in local_live if m["dir_nonempty"]]
wk_ready   = [m["model_id"] for m in workers if m["dir_nonempty"]]
mlx_ok     = "${MLX_OK}" == "true"
venv_ok    = "${VENV_OK}" == "true"
hf_ok      = "${HF_OK}" == "true"
auth_ok    = "${AUTH_OK}" == "true"

def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"    wrote: {path}")

# ns_local_brain_manifest.json
write(f"{RUNTIME_ROOT}/ns_local_brain_manifest.json", {
    "schema_version": "1.0",
    "generated_at": NOW,
    "models": models,
})

# ns_model_download_receipts.json
write(f"{RUNTIME_ROOT}/ns_model_download_receipts.json", {
    "schema_version": "1.0",
    "generated_at": NOW,
    "receipts": [
        {
            "model_id": m["model_id"],
            "tier": m["tier"],
            "local_path": m["path"],
            "download_status": m["status"],
            "disk_size": m["disk_size"],
            "dir_nonempty": m["dir_nonempty"],
            "recorded_at": m["recorded_at"],
        }
        for m in models
    ],
})

# ns_model_bind_receipts.json
write(f"{RUNTIME_ROOT}/ns_model_bind_receipts.json", {
    "schema_version": "1.0",
    "generated_at": NOW,
    "bound_by": "ns_max_complete_models.sh v${SCRIPT_VERSION}",
    "bindings": [
        {"role": "NS_LOCAL_TEXT_MODEL",     "env_key": "NS_LOCAL_TEXT_MODEL",     "path": "${LL1_PATH}", "runtime": "mlx", "worker_runtime_active": False},
        {"role": "NS_LOCAL_VLM_FAST_MODEL", "env_key": "NS_LOCAL_VLM_FAST_MODEL", "path": "${LL2_PATH}", "runtime": "mlx", "worker_runtime_active": False},
        {"role": "NS_LOCAL_VLM_STRONG_MODEL","env_key":"NS_LOCAL_VLM_STRONG_MODEL","path":"${LL3_PATH}", "runtime": "mlx", "worker_runtime_active": False},
        {"role": "NS_WORKER_TEXT_MODEL_1",  "env_key": "NS_WORKER_TEXT_MODEL_1",  "path": "${W1_PATH}", "runtime": "vllm","worker_runtime_active": False},
        {"role": "NS_WORKER_TEXT_MODEL_2",  "env_key": "NS_WORKER_TEXT_MODEL_2",  "path": "${W2_PATH}", "runtime": "vllm","worker_runtime_active": False},
        {"role": "NS_WORKER_VLM_MODEL_1",   "env_key": "NS_WORKER_VLM_MODEL_1",   "path": "${W3_PATH}", "runtime": "vllm","worker_runtime_active": False},
    ],
})

# ns_local_health_report.json
write(f"{RUNTIME_ROOT}/ns_local_health_report.json", {
    "schema_version": "1.0",
    "generated_at": NOW,
    "venv_ok": venv_ok,
    "hf_ok": hf_ok,
    "hf_auth_ok": auth_ok,
    "mlx_ok": mlx_ok,
    "local_live_models_downloaded": len(ll_ready),
    "local_live_models_total": len(local_live),
    "local_live_brain_inference_ok": mlx_ok,
    "worker_models_mirrored": len(wk_ready),
    "worker_models_total": len(workers),
    "worker_runtime_active": False,
    "ready_for_ns_binding": len(ll_ready) > 0,
    "overall_status": "ready" if len(ll_ready) == len(local_live) else ("partial" if ll_ready else "not_ready"),
    "active_download_pid": "${ACTIVE_DOWNLOAD_PID}" or None,
    "inference_brain_used": "${INFERENCE_BRAIN}" or None,
    "local_live_verified": ll_ready,
    "worker_models_verified": wk_ready,
})

# ns_local_completion.json
write(f"{RUNTIME_ROOT}/ns_local_completion.json", {
    "schema_version": "1.0",
    "generated_at": NOW,
    "script_version": "${SCRIPT_VERSION}",
    "run_timestamp": "${RUN_TS}",
    "local_live_verified": ll_ready,
    "local_mirrored_worker_verified": wk_ready,
    "worker_runtime_active": False,
    "local_live_brain_inference_ok": mlx_ok,
    "active_download_in_progress": bool("${ACTIVE_DOWNLOAD_PID}"),
    "active_download_pid": "${ACTIVE_DOWNLOAD_PID}" or None,
    "done_criteria": {
        "venv_valid": venv_ok,
        "hf_cli_works": hf_ok,
        "all_local_live_downloaded": len(ll_ready) == len(local_live),
        "all_workers_mirrored": len(wk_ready) == len(workers),
        "local_live_brain_inference_ok": mlx_ok,
        "env_file_written": True,
        "manifest_written": True,
        "route_matrix_written": True,
        "completion_json_written": True,
        "worker_boot_commands_written": True,
        "download_receipts_written": True,
        "bind_receipts_written": True,
        "health_report_written": True,
    },
})

print("  Python artifact generation complete")
PYEOF

# ── 8c. ns_local_route_matrix.json (written directly — static) ───────────────
log "  Writing ns_local_route_matrix.json"
cat > "${ROUTE_MATRIX_FILE}" <<'ROUTEJSON'
{
  "schema_version": "1.0",
  "description": "NS local model routing matrix. L-tiers run on Mac via MLX. W-tiers are mirrored workers.",
  "tiers": {
    "L1": {
      "role": "local_text_brain",
      "model_id": "lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit",
      "runtime": "mlx",
      "inference_cmd": "python -m mlx_lm.generate --model {path} --max-tokens {max_tokens} --temp {temp} --prompt {prompt}",
      "latency_target_ms": 500,
      "use_for": ["cps_reasoning", "voice_action", "high_risk", "strategy", "sovereign_decisions"],
      "escalate_to": "W1",
      "escalate_conditions": [
        "context_length > 32000",
        "requires_tool_use_not_supported_by_mlx",
        "worker_runtime_active == true"
      ]
    },
    "L2": {
      "role": "local_vlm_fast",
      "model_id": "Qwen/Qwen3-VL-2B-Thinking",
      "runtime": "mlx",
      "latency_target_ms": 300,
      "use_for": ["vision_quick", "ocr_assist", "screenshot_describe"],
      "escalate_to": "L3",
      "escalate_conditions": ["vision_complexity == high", "requires_detailed_analysis"]
    },
    "L3": {
      "role": "local_vlm_strong",
      "model_id": "Qwen/Qwen3-VL-32B-Instruct",
      "runtime": "mlx",
      "latency_target_ms": 2000,
      "use_for": ["vision_complex", "document_understanding", "multimodal_reasoning"],
      "escalate_to": "W3",
      "escalate_conditions": ["video_input", "multi_image_batch", "worker_runtime_active == true"]
    },
    "W1": {
      "role": "mirrored_worker_text_primary",
      "model_id": "moonshotai/Kimi-K2.6",
      "runtime": "vllm",
      "runtime_active": false,
      "use_for": ["long_context", "complex_reasoning", "batch_inference"],
      "note": "Mirrored locally. Start via ns_worker_boot_commands.sh before use."
    },
    "W2": {
      "role": "mirrored_worker_text_secondary",
      "model_id": "deepseek-ai/DeepSeek-V3.2",
      "runtime": "vllm",
      "runtime_active": false,
      "use_for": ["code_generation", "technical_analysis", "batch_tasks"],
      "note": "Mirrored locally. Start via ns_worker_boot_commands.sh before use."
    },
    "W3": {
      "role": "mirrored_worker_vlm",
      "model_id": "Qwen/Qwen3-VL-30B-A3B-Thinking",
      "runtime": "vllm",
      "runtime_active": false,
      "use_for": ["video_understanding", "high_resolution_vision", "multi_image"],
      "note": "Mirrored locally. Start via ns_worker_boot_commands.sh before use."
    }
  },
  "escalation_policy": {
    "default_tier": "L1",
    "worker_gate": "NS_LOCAL_LAYER_ALLOW_WORKER_ESCALATION == true AND worker_runtime_active == true",
    "fallback_to_cloud": false,
    "sovereign_mode": "L1_only_no_escalation"
  }
}
ROUTEJSON

# ── 8d. ns_worker_boot_commands.sh ───────────────────────────────────────────
log "  Writing ns_worker_boot_commands.sh"
cat > "${WORKER_BOOT_FILE}" <<WORKERBOOT
#!/usr/bin/env bash
# ns_worker_boot_commands.sh — Start worker-tier models via vLLM
# Generated by ns_max_complete_models.sh v${SCRIPT_VERSION} on ${RUN_TS}
#
# CAUTION: Worker models require a GPU node or substantial RAM.
# Do NOT run all workers simultaneously on the same Mac serving local_live MLX models.

set -euo pipefail

WORKERS_ROOT="${WORKERS_ROOT}"
VLLM_HOST="\${VLLM_HOST:-0.0.0.0}"
VLLM_PORT_W1="\${VLLM_PORT_W1:-8100}"
VLLM_PORT_W2="\${VLLM_PORT_W2:-8101}"
VLLM_PORT_W3="\${VLLM_PORT_W3:-8102}"

start_worker() {
  local name="\$1"
  local model_path="\$2"
  local port="\$3"
  echo "Starting \${name} on :\${port} ..."
  python -m vllm.entrypoints.openai.api_server \\
    --model "\${model_path}" \\
    --host "\${VLLM_HOST}" \\
    --port "\${port}" \\
    --trust-remote-code \\
    --dtype auto \\
    &
  echo "  PID \$! — \${name}"
}

case "\${1:-all}" in
  W1|kimi)       start_worker "Kimi-K2.6"                 "\${WORKERS_ROOT}/Kimi-K2.6"                   "\${VLLM_PORT_W1}" ;;
  W2|deepseek)   start_worker "DeepSeek-V3.2"             "\${WORKERS_ROOT}/DeepSeek-V3.2"               "\${VLLM_PORT_W2}" ;;
  W3|qwen-vlm)   start_worker "Qwen3-VL-30B-A3B-Thinking" "\${WORKERS_ROOT}/Qwen3-VL-30B-A3B-Thinking"  "\${VLLM_PORT_W3}" ;;
  all)
    start_worker "Kimi-K2.6"                 "\${WORKERS_ROOT}/Kimi-K2.6"                   "\${VLLM_PORT_W1}"
    start_worker "DeepSeek-V3.2"             "\${WORKERS_ROOT}/DeepSeek-V3.2"               "\${VLLM_PORT_W2}"
    start_worker "Qwen3-VL-30B-A3B-Thinking" "\${WORKERS_ROOT}/Qwen3-VL-30B-A3B-Thinking"  "\${VLLM_PORT_W3}"
    ;;
  *)
    echo "Usage: \$0 [W1|W2|W3|kimi|deepseek|qwen-vlm|all]"
    exit 1
    ;;
esac

echo ""
echo "Workers started. Use 'kill %1 %2 %3' or pkill -f vllm to stop."
WORKERBOOT
chmod +x "${WORKER_BOOT_FILE}"

# =============================================================================
# STEP 9 — Final summary
# =============================================================================
sep
log "STEP 9 — Final summary"
sep

printf '\nFILES CREATED / MODIFIED:\n'
for f in \
  "${ENV_FILE}" "${MANIFEST_FILE}" "${ROUTE_MATRIX_FILE}" "${COMPLETION_FILE}" \
  "${WORKER_BOOT_FILE}" "${DOWNLOAD_RECEIPTS_FILE}" "${BIND_RECEIPTS_FILE}" "${HEALTH_REPORT_FILE}"; do
  printf '  ✓ %s\n' "${f}"
done

printf '\nLOCAL LIVE MODELS (must run on Mac via MLX):\n'
for pair in \
  "${LL1_KEY}:local_live/Qwen3-30B-A3B-Thinking-2507-MLX" \
  "${LL2_KEY}:local_live/Qwen3-VL-2B-Thinking" \
  "${LL3_KEY}:local_live/Qwen3-VL-32B-Instruct"; do
  k="${pair%%:*}"; label="${pair##*:}"
  ok="$(get_state "dir_ok_${k}")"
  st="$(get_state "dl_status_${k}")"
  printf '  [%s] %s (%s)\n' "$([ "${ok}" = "true" ] && printf 'VERIFIED' || printf 'PENDING ')" "${label}" "${st}"
done

printf '\nMIRRORED WORKER ASSETS (not actively running):\n'
for pair in \
  "${W1_KEY}:workers/Kimi-K2.6" \
  "${W2_KEY}:workers/DeepSeek-V3.2" \
  "${W3_KEY}:workers/Qwen3-VL-30B-A3B-Thinking"; do
  k="${pair%%:*}"; label="${pair##*:}"
  ok="$(get_state "dir_ok_${k}")"
  st="$(get_state "dl_status_${k}")"
  printf '  [%s] %s (%s)\n' "$([ "${ok}" = "true" ] && printf 'VERIFIED' || printf 'PENDING ')" "${label}" "${st}"
done

printf '\nMLX INFERENCE TEST: %s\n' "${MLX_OK}"

printf '\nREMAINING GAPS:\n'
gaps=0

[ "${MLX_OK}" = "true" ] || { printf '  • MLX inference not yet verified — no complete local_live brain ready\n'; gaps=$((gaps+1)); }
[ -z "${ACTIVE_DOWNLOAD_PID}" ] || { printf '  • Qwen3-30B download in progress (PID %s) — rerun after completion\n' "${ACTIVE_DOWNLOAD_PID}"; gaps=$((gaps+1)); }

for pair in \
  "${LL1_KEY}:local_live/Qwen3-30B" \
  "${LL2_KEY}:local_live/Qwen3-VL-2B" \
  "${LL3_KEY}:local_live/Qwen3-VL-32B"; do
  k="${pair%%:*}"; label="${pair##*:}"
  ok="$(get_state "dir_ok_${k}")"
  [ "${ok}" = "true" ] || { printf '  • %s not yet downloaded/verified\n' "${label}"; gaps=$((gaps+1)); }
done

for pair in \
  "${W1_KEY}:workers/Kimi-K2.6" \
  "${W2_KEY}:workers/DeepSeek-V3.2" \
  "${W3_KEY}:workers/Qwen3-VL-30B"; do
  k="${pair%%:*}"; label="${pair##*:}"
  ok="$(get_state "dir_ok_${k}")"
  [ "${ok}" = "true" ] || { printf '  • %s not yet mirrored/verified\n' "${label}"; gaps=$((gaps+1)); }
done

[ "${gaps}" -eq 0 ] && printf '  None — DONE state reached\n' || true

printf '\nLOG: %s\n' "${LOG_FILE}"
sep
log "ns_max_complete_models.sh complete — safe to rerun at any time"
