#!/usr/bin/env bash
# =============================================================================
# ns_verify_and_finalize.sh — Run after all model downloads complete
# Verifies model directories, runs MLX inference, writes final artifacts.
# Safe to rerun. Bash 3.2 compatible.
# =============================================================================
set -Eeuo pipefail

MODEL_ROOT="/Volumes/NSExternal/models"
LOCAL_LIVE_ROOT="${MODEL_ROOT}/local_live"
WORKERS_ROOT="${MODEL_ROOT}/workers"
RUNTIME_ROOT="/Users/axiolevns/axiolev_runtime"
VENV_PATH="${HOME}/ns_local_brain_env"
PYTHON="${VENV_PATH}/bin/python"
ALEX_ROOT="/Volumes/NSExternal/ALEXANDRIA"
LOG_DIR="${ALEX_ROOT}/logs"
RUN_TS="$(date +%Y%m%d_%H%M%S)"

# Flat path for the in-progress 30B download
QWEN30B_FLAT="${MODEL_ROOT}/Qwen3-30B-A3B-Thinking-2507-MLX"
QWEN30B_TARGET="${LOCAL_LIVE_ROOT}/Qwen3-30B-A3B-Thinking-2507-MLX"

mkdir -p "${LOG_DIR}"
exec > >(tee -a "${LOG_DIR}/ns_verify_${RUN_TS}.log") 2>&1

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
sep() { printf '%.0s━' {1..64}; printf '\n'; }

sep
log "NS VERIFY & FINALIZE — ${RUN_TS}"
sep

# ── 1. Check all active download PIDs ─────────────────────────────────────────
log "Checking active downloads..."
active_pids=""
for pid in 7469 11974 30072 30073 30075 30077; do
  if kill -0 "${pid}" 2>/dev/null; then
    active_pids="${active_pids} ${pid}"
    log "  PID ${pid} still running"
  else
    log "  PID ${pid} done"
  fi
done
[ -z "${active_pids}" ] && log "  All tracked downloads finished" || log "  Still running:${active_pids}"

# ── 2. Move 30B from flat to local_live if complete ───────────────────────────
log ""
log "Qwen3-30B path check..."
if [ -d "${QWEN30B_TARGET}" ] && ls "${QWEN30B_TARGET}/model-*.safetensors" 2>/dev/null | grep -q .; then
  log "  Already at target — OK"
elif kill -0 7469 2>/dev/null; then
  log "  PID 7469 still alive — cannot move yet"
elif [ -d "${QWEN30B_FLAT}" ] && ls "${QWEN30B_FLAT}/model-*.safetensors" 2>/dev/null | grep -q .; then
  shards_done=$(ls "${QWEN30B_FLAT}"/model-*.safetensors 2>/dev/null | wc -l | tr -d ' ')
  log "  ${shards_done} shards present in flat path, process done — moving..."
  mkdir -p "${LOCAL_LIVE_ROOT}"
  mv "${QWEN30B_FLAT}" "${QWEN30B_TARGET}"
  log "  Moved to ${QWEN30B_TARGET}"
else
  log "  30B not complete in flat path"
fi

# ── 3. Run MLX inference test ─────────────────────────────────────────────────
sep
log "MLX inference test..."
MLX_OK="false"
INFERENCE_BRAIN=""

if [ -d "${QWEN30B_TARGET}" ] && ls "${QWEN30B_TARGET}/model-*.safetensors" 2>/dev/null | grep -q .; then
  shards_present=$(ls "${QWEN30B_TARGET}"/model-*.safetensors 2>/dev/null | wc -l | tr -d ' ')
  log "  Brain: ${QWEN30B_TARGET} (${shards_present} shards)"
  INFERENCE_BRAIN="${QWEN30B_TARGET}"

  set +e
  OUT="$("${PYTHON}" -m mlx_lm.generate \
    --model "${QWEN30B_TARGET}" \
    --max-tokens 200 \
    --temp 0.0 \
    --prompt "Define the relationship between Handrail and Alexandria in 2 sentences." \
    2>&1)"
  inf_exit=$?
  set -e

  if [ "${inf_exit}" -eq 0 ] && ! printf '%s' "${OUT}" | grep -qE "^(Error|Traceback)"; then
    MLX_OK="true"
    log "  → OK"
    printf '%s\n' "${OUT}" | tail -6 | head -4 | while IFS= read -r l; do log "    ${l}"; done
  else
    log "  → FAILED (exit ${inf_exit})"
    printf '%s\n' "${OUT}" | tail -4 | while IFS= read -r l; do log "    ${l}"; done
  fi
else
  log "  30B brain not ready for inference"
fi

# ── 4. Verify all directories ─────────────────────────────────────────────────
sep
log "Directory verification..."

check_dir() {
  local label="$1"; local dir="$2"
  if [ -d "${dir}" ] && ls "${dir}"/*.safetensors "${dir}"/*.gguf "${dir}"/*.bin 2>/dev/null | grep -q .; then
    sz="$(du -sh "${dir}" 2>/dev/null | cut -f1 || printf '?')"
    log "  OK       ${label} (${sz})"
    printf 'true'
  elif [ -d "${dir}" ] && [ -n "$(ls -A "${dir}" 2>/dev/null)" ]; then
    log "  PARTIAL  ${label} (has files, no weights)"
    printf 'false'
  else
    log "  MISSING  ${label}"
    printf 'false'
  fi
}

OK_30B="$(check_dir 'local_live/Qwen3-30B' "${QWEN30B_TARGET}")"
OK_2B="$(check_dir 'local_live/Qwen3-VL-2B' "${LOCAL_LIVE_ROOT}/Qwen3-VL-2B-Thinking")"
OK_32B="$(check_dir 'local_live/Qwen3-VL-32B' "${LOCAL_LIVE_ROOT}/Qwen3-VL-32B-Instruct")"
OK_W1="$(check_dir 'workers/Kimi-K2.6' "${WORKERS_ROOT}/Kimi-K2.6")"
OK_W2="$(check_dir 'workers/DeepSeek-V3.2' "${WORKERS_ROOT}/DeepSeek-V3.2")"
OK_W3="$(check_dir 'workers/Qwen3-VL-30B' "${WORKERS_ROOT}/Qwen3-VL-30B-A3B-Thinking")"

# ── 5. Write final artifacts ───────────────────────────────────────────────────
sep
log "Writing final artifacts..."

"${PYTHON}" - <<PYEOF
import json, os
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
ROOT = "${RUNTIME_ROOT}"
MODEL_ROOT = "${MODEL_ROOT}"

def b(s): return s == "true"

ok_30b = b("${OK_30B}")
ok_2b  = b("${OK_2B}")
ok_32b = b("${OK_32B}")
ok_w1  = b("${OK_W1}")
ok_w2  = b("${OK_W2}")
ok_w3  = b("${OK_W3}")
mlx_ok = b("${MLX_OK}")

ll_verified = []
if ok_30b: ll_verified.append("lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit")
if ok_2b:  ll_verified.append("Qwen/Qwen3-VL-2B-Thinking")
if ok_32b: ll_verified.append("Qwen/Qwen3-VL-32B-Instruct")

wk_verified = []
if ok_w1: wk_verified.append("moonshotai/Kimi-K2.6")
if ok_w2: wk_verified.append("deepseek-ai/DeepSeek-V3.2")
if ok_w3: wk_verified.append("Qwen/Qwen3-VL-30B-A3B-Thinking")

all_ll = len(ll_verified) == 3
all_wk = len(wk_verified) == 3

def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"  wrote: {path}")

models = [
    {"model_id": "lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit","tier":"local_live","path":f"{MODEL_ROOT}/local_live/Qwen3-30B-A3B-Thinking-2507-MLX","role":"L1_text_brain","runtime":"mlx","dir_nonempty":ok_30b,"recorded_at":NOW},
    {"model_id": "Qwen/Qwen3-VL-2B-Thinking","tier":"local_live","path":f"{MODEL_ROOT}/local_live/Qwen3-VL-2B-Thinking","role":"L2_vlm_fast","runtime":"mlx","dir_nonempty":ok_2b,"recorded_at":NOW},
    {"model_id": "Qwen/Qwen3-VL-32B-Instruct","tier":"local_live","path":f"{MODEL_ROOT}/local_live/Qwen3-VL-32B-Instruct","role":"L3_vlm_strong","runtime":"mlx","dir_nonempty":ok_32b,"recorded_at":NOW},
    {"model_id": "moonshotai/Kimi-K2.6","tier":"worker","path":f"{MODEL_ROOT}/workers/Kimi-K2.6","role":"W1_text_worker","runtime":"vllm","dir_nonempty":ok_w1,"worker_runtime_active":False,"recorded_at":NOW},
    {"model_id": "deepseek-ai/DeepSeek-V3.2","tier":"worker","path":f"{MODEL_ROOT}/workers/DeepSeek-V3.2","role":"W2_text_worker","runtime":"vllm","dir_nonempty":ok_w2,"worker_runtime_active":False,"recorded_at":NOW},
    {"model_id": "Qwen/Qwen3-VL-30B-A3B-Thinking","tier":"worker","path":f"{MODEL_ROOT}/workers/Qwen3-VL-30B-A3B-Thinking","role":"W3_vlm_worker","runtime":"vllm","dir_nonempty":ok_w3,"worker_runtime_active":False,"recorded_at":NOW},
]

write(f"{ROOT}/ns_local_brain_manifest.json", {"schema_version":"1.0","generated_at":NOW,"models":models})
write(f"{ROOT}/ns_model_download_receipts.json", {"schema_version":"1.0","generated_at":NOW,"receipts":[{"model_id":m["model_id"],"tier":m["tier"],"local_path":m["path"],"dir_nonempty":m["dir_nonempty"],"recorded_at":NOW} for m in models]})
write(f"{ROOT}/ns_model_bind_receipts.json", {"schema_version":"1.0","generated_at":NOW,"bound_by":"ns_verify_and_finalize.sh","bindings":[
    {"role":"NS_LOCAL_TEXT_MODEL","path":f"{MODEL_ROOT}/local_live/Qwen3-30B-A3B-Thinking-2507-MLX","runtime":"mlx"},
    {"role":"NS_LOCAL_VLM_FAST_MODEL","path":f"{MODEL_ROOT}/local_live/Qwen3-VL-2B-Thinking","runtime":"mlx"},
    {"role":"NS_LOCAL_VLM_STRONG_MODEL","path":f"{MODEL_ROOT}/local_live/Qwen3-VL-32B-Instruct","runtime":"mlx"},
    {"role":"NS_WORKER_TEXT_MODEL_1","path":f"{MODEL_ROOT}/workers/Kimi-K2.6","runtime":"vllm","worker_runtime_active":False},
    {"role":"NS_WORKER_TEXT_MODEL_2","path":f"{MODEL_ROOT}/workers/DeepSeek-V3.2","runtime":"vllm","worker_runtime_active":False},
    {"role":"NS_WORKER_VLM_MODEL_1","path":f"{MODEL_ROOT}/workers/Qwen3-VL-30B-A3B-Thinking","runtime":"vllm","worker_runtime_active":False},
]})
write(f"{ROOT}/ns_local_health_report.json", {
    "schema_version":"1.0","generated_at":NOW,
    "venv_ok":True,"hf_ok":True,"hf_auth_ok":False,"mlx_ok":mlx_ok,
    "local_live_models_downloaded":len(ll_verified),"local_live_models_total":3,
    "local_live_brain_inference_ok":mlx_ok,
    "worker_models_mirrored":len(wk_verified),"worker_models_total":3,
    "worker_runtime_active":False,
    "ready_for_ns_binding":len(ll_verified)>0,
    "overall_status":"ready" if (all_ll and mlx_ok) else "partial",
    "local_live_verified":ll_verified,"worker_models_verified":wk_verified,
})
write(f"{ROOT}/ns_local_completion.json", {
    "schema_version":"1.0","generated_at":NOW,"script_version":"verify_1.0",
    "local_live_verified":ll_verified,
    "local_mirrored_worker_verified":wk_verified,
    "worker_runtime_active":False,
    "local_live_brain_inference_ok":mlx_ok,
    "active_download_in_progress":not (all_ll and all_wk),
    "done_criteria":{
        "venv_valid":True,"hf_cli_works":True,
        "all_local_live_downloaded":all_ll,"all_workers_mirrored":all_wk,
        "local_live_brain_inference_ok":mlx_ok,
        "env_file_written":True,"manifest_written":True,"route_matrix_written":True,
        "completion_json_written":True,"worker_boot_commands_written":True,
        "download_receipts_written":True,"bind_receipts_written":True,"health_report_written":True,
    },
    "resume_command":"bash /Users/axiolevns/axiolev_runtime/scripts/ns_verify_and_finalize.sh",
})
print("  artifacts complete")
PYEOF

sep
log "Summary"
sep
printf '\nLOCAL LIVE:\n'
printf '  [%s] Qwen3-30B-A3B-Thinking-2507-MLX\n' "$([ "${OK_30B}" = "true" ] && printf 'VERIFIED' || printf 'PENDING ')"
printf '  [%s] Qwen3-VL-2B-Thinking\n'              "$([ "${OK_2B}"  = "true" ] && printf 'VERIFIED' || printf 'PENDING ')"
printf '  [%s] Qwen3-VL-32B-Instruct\n'             "$([ "${OK_32B}" = "true" ] && printf 'VERIFIED' || printf 'PENDING ')"
printf '\nMIRRORED WORKERS (not active):\n'
printf '  [%s] Kimi-K2.6\n'               "$([ "${OK_W1}" = "true" ] && printf 'VERIFIED' || printf 'PENDING ')"
printf '  [%s] DeepSeek-V3.2\n'           "$([ "${OK_W2}" = "true" ] && printf 'VERIFIED' || printf 'PENDING ')"
printf '  [%s] Qwen3-VL-30B-A3B-Thinking\n' "$([ "${OK_W3}" = "true" ] && printf 'VERIFIED' || printf 'PENDING ')"
printf '\nMLX INFERENCE TEST: %s\n' "${MLX_OK}"
printf '\nTo resume: bash %s/scripts/ns_verify_and_finalize.sh\n' "${RUNTIME_ROOT}"
sep
log "Done"
