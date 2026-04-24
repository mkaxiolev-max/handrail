#!/usr/bin/env bash
# =============================================================================
# ns_download_watchdog.sh — NS∞ Model Download Status + Restart
# AXIOLEV Holdings LLC © 2026
#
# WHAT IT DOES
#   For each of the 6 target models:
#     1. Check if HF download process is alive (by PID file or ps grep)
#     2. Measure progress — disk size + mtime delta
#     3. Classify: complete | active | stalled | missing | failed
#     4. Restart stalled or missing downloads in the background
#     5. Never interrupt an actively-progressing download
#     6. Emit status table + JSON receipt
#
# SAFETY PRIMARY
#   - Uses size-delta + mtime-delta over SAMPLE_WINDOW to detect stalls
#   - NEVER kills a process that has written bytes in the last STALL_SECS
#   - NEVER removes a lock file owned by a live process
#   - Idempotent — safe to re-run every few minutes (or via launchd)
#   - Bash 3.2 compatible (macOS default shell)
#
# USAGE
#   cd ~/axiolev_runtime
#   chmod +x tools/downloads/ns_download_watchdog.sh
#   tools/downloads/ns_download_watchdog.sh
#
#   # Check-only mode (no restart, just report):
#   CHECK_ONLY=1 tools/downloads/ns_download_watchdog.sh
#
#   # Loop mode (check every N seconds, useful in a terminal tab):
#   LOOP=300 tools/downloads/ns_download_watchdog.sh
#
#   # Launchd / cron mode (one pass, JSON only, no TTY output):
#   QUIET=1 tools/downloads/ns_download_watchdog.sh
# =============================================================================

set -Eeuo pipefail
umask 0022

# ─── Config ──────────────────────────────────────────────────────────────────
REPO="${REPO:-$HOME/axiolev_runtime}"
ALEX="${ALEXANDRIA:-/Volumes/NSExternal/ALEXANDRIA}"
MODEL_ROOT="${MODEL_ROOT:-/Volumes/NSExternal/models}"
LOCAL_LIVE="$MODEL_ROOT/local_live"
WORKERS="$MODEL_ROOT/workers"
VENV="${VENV:-$HOME/ns_local_brain_env}"
HF_BIN="${HF_BIN:-$VENV/bin/hf}"
PYTHON="${PYTHON:-$VENV/bin/python}"

PID_DIR="${PID_DIR:-$HOME/.ns_downloads/pids}"
STATE_DIR="${STATE_DIR:-$HOME/.ns_downloads/state}"
LOG_DIR="${LOG_DIR:-$HOME/.ns_downloads/logs}"
RCPT_DIR="$ALEX/ledger/downloads"

STALL_SECS="${STALL_SECS:-300}"       # 5 min of no growth = stalled
SAMPLE_WINDOW="${SAMPLE_WINDOW:-8}"   # seconds between two size samples
MIN_FREE_GB="${MIN_FREE_GB:-100}"     # refuse to restart if disk below this
CHECK_ONLY="${CHECK_ONLY:-0}"
QUIET="${QUIET:-0}"
LOOP="${LOOP:-0}"                     # seconds between passes; 0 = single pass

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$PID_DIR" "$STATE_DIR" "$LOG_DIR"

# ─── Model manifest (repo_id | tier | dest_path | priority) ──────────────────
# priority controls restart order when multiple need restarting.
# Lower priority = launched first. local_live models go before workers.
MODELS="$(cat <<'EOF'
lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit|local_live|Qwen3-30B-A3B-Thinking-2507-MLX|1
Qwen/Qwen3-VL-2B-Thinking|local_live|Qwen3-VL-2B-Thinking|2
Qwen/Qwen3-VL-32B-Instruct|local_live|Qwen3-VL-32B-Instruct|3
Qwen/Qwen3-VL-30B-A3B-Thinking|worker|Qwen3-VL-30B-A3B-Thinking|4
moonshotai/Kimi-K2.6|worker|Kimi-K2.6|5
deepseek-ai/DeepSeek-V3.2|worker|DeepSeek-V3.2|6
EOF
)"

# Flat path for the in-progress 30B download (historical — not under local_live yet)
FLAT_30B="$MODEL_ROOT/Qwen3-30B-A3B-Thinking-2507-MLX"

# ─── UI helpers ──────────────────────────────────────────────────────────────
_ts()  { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
_hm()  { date -u +"%H:%M:%S"; }

if [ "$QUIET" = "1" ]; then
  log()  { :; }
  ok()   { :; }
  warn() { :; }
  info() { :; }
  hdr()  { :; }
else
  log()  { printf '[%s] %s\n' "$(_hm)" "$*"; }
  ok()   { printf '\033[0;32m[OK]\033[0m %s\n' "$*"; }
  warn() { printf '\033[0;33m[!!]\033[0m %s\n' "$*"; }
  info() { printf '\033[0;34m[..]\033[0m %s\n' "$*"; }
  hdr()  { printf '\n\033[1;36m━━━ %s ━━━\033[0m\n' "$*"; }
fi
err()  { printf '\033[0;31m[XX]\033[0m %s\n' "$*" >&2; }

# ─── helpers ─────────────────────────────────────────────────────────────────

# dir_size_bytes <path>  — cumulative size in bytes (0 if missing)
dir_size_bytes() {
  local p="$1"
  [ -d "$p" ] || { echo 0; return; }
  local kb
  kb="$(du -sk "$p" 2>/dev/null | awk '{print $1}')"
  kb="${kb:-0}"
  echo $(( kb * 1024 ))
}

# dir_mtime <path>  — latest mtime as epoch seconds
dir_mtime() {
  local p="$1"
  [ -d "$p" ] || { echo 0; return; }
  local m
  m="$(find "$p" -type f -exec stat -f '%m' {} + 2>/dev/null | sort -n | tail -1)"
  echo "${m:-0}"
}

# human_size <bytes>
human_size() {
  awk -v b="$1" 'BEGIN{
    split("B KB MB GB TB",u);
    i=1; while(b>=1024 && i<5){b/=1024; i++}
    printf "%.1f%s", b, u[i]
  }'
}

# free_gb <mount> — free space on the volume containing <mount>
free_gb() {
  df -g "$1" 2>/dev/null | awk 'NR==2{print $4}'
}

# find live HF download PID for a given target dir (or empty if none)
find_live_pid() {
  local target="$1"
  ps -eo pid,args 2>/dev/null | \
    awk -v t="$target" '$0 ~ "hf download" && $0 ~ t { print $1; exit }'
}

# has_weights <dir>  — returns 0 if dir contains model weights
has_weights() {
  local d="$1"
  [ -d "$d" ] || return 1
  find "$d" -maxdepth 1 \( -name "*.safetensors" -o -name "*.npz" -o -name "*.bin" -o -name "*.gguf" \) \
    -print -quit 2>/dev/null | grep -q . && return 0
  return 1
}

# download_complete <dir>  — returns 0 if weights present AND index covered
download_complete() {
  local d="$1"
  [ -f "$d/config.json" ] || return 1
  has_weights "$d" || return 1
  # If there's a shard index, check shard coverage
  local idx="$d/model.safetensors.index.json"
  if [ -f "$idx" ] && [ -x "$PYTHON" ]; then
    local miss
    miss="$("$PYTHON" - "$d" "$idx" <<'PY' 2>/dev/null
import json, os, sys
dp, ip = sys.argv[1], sys.argv[2]
try:
    idx = json.load(open(ip))
    want = set(idx.get("weight_map", {}).values())
    have = set(os.listdir(dp))
    missing = want - have
    print(len(missing))
except Exception:
    print(-1)
PY
)"
    [ "${miss:-0}" = "0" ] || return 1
  fi
  return 0
}

# ─── resolve an HF repo_id to a downloadable directory name ──────────────────
dest_dir() {
  local tier="$1" ; local rel="$2"
  case "$tier" in
    local_live) echo "$LOCAL_LIVE/$rel" ;;
    worker)     echo "$WORKERS/$rel" ;;
    *)          echo "$MODEL_ROOT/$rel" ;;
  esac
}

# ─── restart a download in the background ────────────────────────────────────
restart_download() {
  local repo_id="$1" ; local dest="$2" ; local pidfile="$3"

  if [ "$CHECK_ONLY" = "1" ]; then
    warn "CHECK_ONLY=1 — not restarting $repo_id"
    return 0
  fi

  if [ ! -x "$HF_BIN" ]; then
    err "hf CLI missing at $HF_BIN — cannot restart"
    return 1
  fi

  # Disk space gate
  local fg
  fg="$(free_gb "$MODEL_ROOT")"
  if [ -n "$fg" ] && [ "$fg" -lt "$MIN_FREE_GB" ] 2>/dev/null; then
    err "only ${fg}G free on $MODEL_ROOT — refusing to restart $repo_id (min=${MIN_FREE_GB}G)"
    return 1
  fi

  mkdir -p "$dest"
  local logf="$LOG_DIR/$(basename "$dest").$(date -u +%Y%m%dT%H%M%SZ).log"

  info "launching: $HF_BIN download $repo_id --local-dir $dest"
  nohup "$HF_BIN" download "$repo_id" --local-dir "$dest" \
    >"$logf" 2>&1 &
  local pid=$!
  echo "$pid" > "$pidfile"
  ok "restarted $repo_id pid=$pid log=$logf"
  # Small stagger so concurrent HF clients don't all hit the API at once
  sleep 2
}

# ─── classify + act on one model ─────────────────────────────────────────────
# writes per-model state file and prints display row directly to stdout.
# caller must NOT capture output — read status back from the .state file.
classify_and_act() {
  local repo_id="$1" ; local tier="$2" ; local rel="$3"
  local dest; dest="$(dest_dir "$tier" "$rel")"
  local pidfile="$PID_DIR/$(basename "$dest").pid"

  # Special handling: 30B flat path still in use by PID 7469
  local effective_dir="$dest"
  if [ "$rel" = "Qwen3-30B-A3B-Thinking-2507-MLX" ] \
     && [ ! -d "$dest" ] && [ -d "$FLAT_30B" ]; then
    effective_dir="$FLAT_30B"
  fi

  local STATUS SIZE_BYTES LIVE_PID REASON
  SIZE_BYTES="$(dir_size_bytes "$effective_dir")"
  LIVE_PID=""
  STATUS=""
  REASON=""

  # 1. Already complete?
  if download_complete "$effective_dir"; then
    STATUS="complete"
    REASON="all shards + config present"
  else
    # 2. Find live process
    LIVE_PID="$(find_live_pid "$effective_dir")"
    if [ -z "$LIVE_PID" ] && [ -f "$pidfile" ]; then
      local stored_pid
      stored_pid="$(cat "$pidfile" 2>/dev/null || true)"
      if [ -n "$stored_pid" ] && kill -0 "$stored_pid" 2>/dev/null; then
        LIVE_PID="$stored_pid"
      fi
    fi

    # 3. If live, check progress over sample window
    if [ -n "$LIVE_PID" ]; then
      local s1 m1 s2 m2
      s1="$SIZE_BYTES"
      m1="$(dir_mtime "$effective_dir")"
      sleep "$SAMPLE_WINDOW"
      s2="$(dir_size_bytes "$effective_dir")"
      m2="$(dir_mtime "$effective_dir")"

      if [ "$s2" -gt "$s1" ] || [ "$m2" -gt "$m1" ]; then
        STATUS="active"
        REASON="bytes+$((s2 - s1)) over ${SAMPLE_WINDOW}s"
        SIZE_BYTES="$s2"
      else
        # Size/mtime didn't move — check wall time since last mtime
        local now age
        now="$(date -u +%s)"
        age=$(( now - m2 ))
        if [ "$age" -gt "$STALL_SECS" ]; then
          STATUS="stalled"
          REASON="live PID $LIVE_PID but no growth in ${age}s"
          # Only intervene past 2× threshold; kill the stalled process
          # and start fresh — safer than running two writers to the same dir.
          if [ "$age" -gt $(( STALL_SECS * 2 )) ]; then
            warn "$repo_id PID $LIVE_PID stalled ${age}s — killing and restarting"
            kill "$LIVE_PID" 2>/dev/null || true
            LIVE_PID=""
            restart_download "$repo_id" "$dest" "$pidfile"
          fi
        else
          STATUS="active"
          REASON="live PID $LIVE_PID, no growth yet but within ${STALL_SECS}s grace"
        fi
      fi
    else
      # 4. No live process — classify as paused or missing
      if [ -d "$effective_dir" ] && [ "$SIZE_BYTES" -gt 0 ]; then
        STATUS="paused"
        REASON="partial download, no active process — resuming"
      else
        STATUS="missing"
        REASON="no directory yet"
      fi
      restart_download "$repo_id" "$dest" "$pidfile"
    fi
  fi

  # Write per-model state file (persists out of subshell via disk)
  cat > "$STATE_DIR/$(basename "$(dest_dir "$tier" "$rel")").state" <<EOF
repo_id=$repo_id
tier=$tier
dest=$effective_dir
status=$STATUS
size_bytes=$SIZE_BYTES
live_pid=${LIVE_PID:-}
reason=$REASON
timestamp=$(_ts)
EOF

  # Print display row
  if [ "$QUIET" != "1" ]; then
    local short; short="$(echo "$repo_id" | awk -F'/' '{print $NF}')"
    local size_h; size_h="$(human_size "$SIZE_BYTES")"
    local color
    case "$STATUS" in
      complete) color="\033[0;32mcomplete\033[0m" ;;
      active)   color="\033[0;34mactive  \033[0m" ;;
      stalled)  color="\033[0;33mstalled \033[0m" ;;
      paused)   color="\033[0;33mpaused  \033[0m" ;;
      missing)  color="\033[0;31mmissing \033[0m" ;;
      *)        color="$STATUS" ;;
    esac
    printf "  %-50s " "$short"
    printf "$color"
    printf "  %-9s %-10s\n" "$size_h" "${LIVE_PID:---}"
    printf "    └─ %s\n" "$REASON"
  fi
}

# ─── main single-pass ────────────────────────────────────────────────────────
single_pass() {
  hdr "NS∞ Download Watchdog — pass $RUN_ID"

  if [ ! -d "$MODEL_ROOT" ]; then
    err "MODEL_ROOT $MODEL_ROOT not mounted"
    return 1
  fi

  local fg; fg="$(free_gb "$MODEL_ROOT")"
  info "disk free on $MODEL_ROOT: ${fg:-?} GB (min=$MIN_FREE_GB)"

  if [ "$QUIET" != "1" ]; then
    printf "\n  %-50s %-11s %-9s %-10s\n" "model" "status" "size" "live_pid"
    printf "  %-50s %-11s %-9s %-10s\n" "──────" "──────" "────" "────────"
  fi

  local n_complete=0 n_active=0 n_stalled=0 n_restarted=0

  # Sort by priority; use process substitution to avoid subshell scoping
  local BUF
  BUF="$(echo "$MODELS" | awk -F'|' 'NF==4{printf "%s|%s|%s|%s\n", $4, $1, $2, $3}' \
         | sort -n | awk -F'|' '{printf "%s|%s|%s\n", $2, $3, $4}')"

  while IFS='|' read -r repo_id tier rel; do
    [ -z "$repo_id" ] && continue
    classify_and_act "$repo_id" "$tier" "$rel"
    # Read status back from the state file written by classify_and_act
    local sf="$STATE_DIR/$(basename "$(dest_dir "$tier" "$rel")").state"
    local st=""
    [ -f "$sf" ] && st="$(awk -F= '/^status/{print $2}' "$sf")"
    case "$st" in
      complete) (( n_complete++ )) || true ;;
      active)   (( n_active++   )) || true ;;
      stalled)  (( n_stalled++  )) || true ;;
      paused|missing) (( n_restarted++ )) || true ;;
    esac
  done < <(echo "$BUF")

  if [ "$QUIET" != "1" ]; then
    printf "\n  summary: complete=%d active=%d stalled=%d restarted=%d\n" \
      "$n_complete" "$n_active" "$n_stalled" "$n_restarted"
  fi

  # Emit aggregate receipt
  local day; day="$(date -u +%Y-%m-%d)"
  if mkdir -p "$RCPT_DIR/$day" 2>/dev/null; then
    local rcpt="$RCPT_DIR/$day/watchdog-$RUN_ID.json"
    {
      printf '{\n'
      printf '  "lineage_fabric_version": "1.1",\n'
      printf '  "receipt_type": "download_watchdog",\n'
      printf '  "run_id": "%s",\n' "$RUN_ID"
      printf '  "model_root": "%s",\n' "$MODEL_ROOT"
      printf '  "free_gb": %s,\n' "${fg:-0}"
      printf '  "summary": {"complete":%d,"active":%d,"stalled":%d,"restarted":%d},\n' \
        "$n_complete" "$n_active" "$n_stalled" "$n_restarted"
      printf '  "models": [\n'
      local first=1
      for s in "$STATE_DIR"/*.state; do
        [ -f "$s" ] || continue
        [ "$first" = "1" ] && first=0 || printf ',\n'
        local d; d="$(basename "$s" .state)"
        printf '    {\n'
        printf '      "name": "%s",\n' "$d"
        awk -F= '
          NR>1 { printf ",\n" }
          { printf "      \"%s\": \"%s\"", $1, $2 }
        ' "$s"
        printf '\n    }'
      done
      printf '\n  ],\n'
      printf '  "generated_at": "%s"\n' "$(_ts)"
      printf '}\n'
    } > "$rcpt"
    if [ "$QUIET" != "1" ]; then
      echo
      ok "receipt: $rcpt"
    fi
  elif [ "$QUIET" != "1" ]; then
    warn "Alexandria unmounted — receipt deferred"
  fi
}

# ─── main entry ──────────────────────────────────────────────────────────────
main() {
  if [ "$LOOP" = "0" ]; then
    single_pass
    exit 0
  fi

  if ! [ "$LOOP" -gt 0 ] 2>/dev/null; then
    err "LOOP must be a positive integer seconds"
    exit 1
  fi

  info "LOOP mode — pass every ${LOOP}s. Ctrl-C to stop."
  trap 'echo; info "loop interrupted — last state in $STATE_DIR"; exit 0' INT TERM
  while true; do
    RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
    single_pass
    [ "$QUIET" != "1" ] && info "next pass in ${LOOP}s"
    sleep "$LOOP"
  done
}

main "$@"
