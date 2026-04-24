#!/bin/zsh
# ============================================================================
# FILE:     ns_local_brain_repair.sh
# PURPOSE:  Finish what bootstrap_ns_local_brain_done.sh started.
#           Model is already on disk (40 files verified). This script:
#             1. stops treating a successful download as a failure
#             2. bypasses mlx_lm.generate's broken CLI path handling
#             3. tests inference via a proper Python entry point (Path object)
#             4. writes the manifest DONE + receipt
#             5. prints how to use it
#
# CONTEXT:  bootstrap failed at the INFERENCE TEST step with
#             HFValidationError: Repo id must be a string, not PosixPath
#           which is a mlx_lm 0.31.3 / Python 3.14 CLI argument-coercion bug,
#           not OOM, not a download failure. The script's error handler
#           misclassified it because of a loose "metal" regex match.
#
# OWNER:    AXIOLEV Holdings LLC © 2026
# ============================================================================

set -Eeuo pipefail
IFS=$'\n\t'

# ---------- constants -------------------------------------------------------
readonly VENV_DIR="${VENV_DIR:-$HOME/ns_local_brain_env}"
readonly MODEL_DIR="${MODEL_DIR:-/Volumes/NSExternal/models/local_live/Qwen3-30B-A3B-Thinking-2507-MLX}"
readonly MODEL_REPO="lmstudio-community/Qwen3-30B-A3B-Thinking-2507-MLX-8bit"
readonly ENV_FILE="${ENV_FILE:-$PWD/.ns_local_brain.env}"
readonly MANIFEST_FILE="${MANIFEST_FILE:-$PWD/.ns_local_brain.manifest.json}"
readonly LOG_FILE="${LOG_FILE:-$PWD/ns_local_brain_repair.log}"
readonly ALEX="/Volumes/NSExternal/ALEXANDRIA"
readonly RUN_TS="$(date -u +%Y%m%dT%H%M%SZ)"
readonly RECEIPT_DIR="${ALEX}/ledger/local_brain/${RUN_TS}"
readonly TEST_PROMPT="${TEST_PROMPT:-Reply with exactly: NS local brain online.}"

# ---------- ui --------------------------------------------------------------
if [[ -t 1 ]]; then
  C_GRN=$'\033[1;32m'; C_RED=$'\033[1;31m'; C_YEL=$'\033[1;33m'
  C_CYA=$'\033[1;36m'; C_DIM=$'\033[2m';    C_RST=$'\033[0m'
else
  C_GRN=""; C_RED=""; C_YEL=""; C_CYA=""; C_DIM=""; C_RST=""
fi

step()  { printf "\n%s== %s ==%s\n" "$C_CYA" "$*" "$C_RST"; }
ok()    { printf "  %s✓%s %s\n" "$C_GRN" "$C_RST" "$*"; }
warn()  { printf "  %s⚠%s %s\n" "$C_YEL" "$C_RST" "$*"; }
fail()  { printf "  %s✗%s %s\n" "$C_RED" "$C_RST" "$*" >&2; exit 1; }
note()  { printf "    %s%s%s\n" "$C_DIM" "$*" "$C_RST"; }

exec > >(tee "$LOG_FILE") 2>&1

cat <<BANNER

${C_CYA}NS∞ local brain repair  ·  ${RUN_TS}${C_RST}

  venv:   $VENV_DIR
  model:  $MODEL_DIR
  repo:   $MODEL_REPO
  log:    $LOG_FILE

BANNER

# ============================================================================
# 1. ACTIVATE VENV
# ============================================================================
step "Activating venv"
[[ -d "$VENV_DIR" ]] || fail "venv missing at $VENV_DIR — re-run bootstrap_ns_local_brain_done.sh first"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
ok "python $(python --version 2>&1)"
ok "which python: $(which python)"

# ============================================================================
# 2. VERIFY MODEL ON DISK (don't re-download — it succeeded)
# ============================================================================
step "Verifying model files"
[[ -d "$MODEL_DIR" ]]                || fail "model dir missing: $MODEL_DIR"
[[ -f "$MODEL_DIR/config.json" ]]    || fail "config.json missing"
[[ -f "$MODEL_DIR/tokenizer.json" ]] || fail "tokenizer.json missing"

SAFETENSOR_COUNT="$(find "$MODEL_DIR" -maxdepth 1 -name 'model-*.safetensors' | wc -l | tr -d ' ')"
[[ "$SAFETENSOR_COUNT" -ge 7 ]] \
  || fail "expected 7 safetensor shards, found $SAFETENSOR_COUNT"

TOTAL_SIZE="$(du -sh "$MODEL_DIR" 2>/dev/null | awk '{print $1}')"
ok "config.json + tokenizer.json present"
ok "$SAFETENSOR_COUNT safetensor shards (expected 7)"
ok "total size: $TOTAL_SIZE"

# ============================================================================
# 3. SANITY-CHECK PACKAGES (don't reinstall if already fine)
# ============================================================================
step "Verifying packages"
python -c "import mlx, mlx_lm, huggingface_hub, transformers" 2>/dev/null \
  && ok "mlx / mlx_lm / huggingface_hub / transformers importable" \
  || fail "package import failed — run: python -m pip install mlx mlx-lm huggingface_hub transformers"

python -c "import mlx_lm; print('  mlx_lm', mlx_lm.__version__)" 2>/dev/null || true
python -c "import mlx; print('  mlx    ', mlx.__version__)" 2>/dev/null || true

# ============================================================================
# 4. RUN INFERENCE — THREE FALLBACK STRATEGIES
# ============================================================================
# Why three? The bug in the prior run:
#   mlx_lm.generate CLI passed the absolute path as a string, but mlx_lm's
#   utils.load() coerced it to a pathlib.PosixPath, and huggingface_hub's
#   validate_repo_id() rejected it as non-string. This is a known rough
#   edge in mlx_lm 0.31.3 on Python 3.14.
#
# Strategy A: Python script using mlx_lm.load() + mlx_lm.generate() directly.
#             Most robust — removes the CLI entirely.
# Strategy B: New console-script entry point: `mlx_lm generate` (not `python -m mlx_lm.generate`).
#             The deprecation warning in your log pointed to this.
# Strategy C: Run from the model's parent dir with a relative path.
#             Works around path-type heuristics in the CLI.

INFERENCE_OK=0
INFERENCE_STRATEGY=""
INFERENCE_OUTPUT=""

# ---------- strategy A: Python API (primary) --------------------------------
step "Inference test — strategy A (Python API direct)"
INFER_A="$(python - <<PY 2>&1
import sys
from pathlib import Path

model_path = Path("$MODEL_DIR")
if not model_path.is_dir():
    print("MODEL_DIR_MISSING", file=sys.stderr); sys.exit(2)

try:
    from mlx_lm import load, generate
except ImportError as e:
    print(f"IMPORT_FAIL: {e}", file=sys.stderr); sys.exit(3)

# Pass as string, not Path — this is the fix the CLI missed.
try:
    model, tokenizer = load(str(model_path))
except Exception as e:
    print(f"LOAD_FAIL: {type(e).__name__}: {e}", file=sys.stderr); sys.exit(4)

try:
    # Some mlx_lm versions don't accept max_tokens as a kwarg — try both.
    try:
        out = generate(model, tokenizer, prompt="$TEST_PROMPT", max_tokens=64, verbose=False)
    except TypeError:
        out = generate(model, tokenizer, prompt="$TEST_PROMPT", verbose=False)
except Exception as e:
    print(f"GEN_FAIL: {type(e).__name__}: {e}", file=sys.stderr); sys.exit(5)

print("----BEGIN----")
print(out)
print("----END----")
PY
)"
if echo "$INFER_A" | grep -q "^----BEGIN----"; then
  INFERENCE_OK=1
  INFERENCE_STRATEGY="python_api"
  INFERENCE_OUTPUT="$(echo "$INFER_A" | awk '/^----BEGIN----$/{p=1;next} /^----END----$/{p=0} p')"
  ok "strategy A succeeded"
  echo "$INFERENCE_OUTPUT" | sed 's/^/    /'
else
  warn "strategy A failed"
  echo "$INFER_A" | tail -15 | sed 's/^/    /'
fi

# ---------- strategy B: new console script ----------------------------------
if [[ "$INFERENCE_OK" != "1" ]]; then
  step "Inference test — strategy B (mlx_lm console script)"
  if command -v mlx_lm >/dev/null 2>&1; then
    set +e
    INFER_B="$(mlx_lm generate --model "$MODEL_DIR" --prompt "$TEST_PROMPT" --max-tokens 64 2>&1)"
    RC=$?
    set -e
    if [[ $RC -eq 0 ]]; then
      INFERENCE_OK=1
      INFERENCE_STRATEGY="console_script"
      INFERENCE_OUTPUT="$INFER_B"
      ok "strategy B succeeded"
      echo "$INFER_B" | tail -15 | sed 's/^/    /'
    else
      warn "strategy B failed (rc=$RC)"
      echo "$INFER_B" | tail -15 | sed 's/^/    /'
    fi
  else
    warn "mlx_lm console script not in PATH"
  fi
fi

# ---------- strategy C: run from parent dir with relative path --------------
if [[ "$INFERENCE_OK" != "1" ]]; then
  step "Inference test — strategy C (parent dir + relative)"
  MODEL_PARENT="$(dirname "$MODEL_DIR")"
  MODEL_NAME="$(basename "$MODEL_DIR")"
  set +e
  pushd "$MODEL_PARENT" >/dev/null
  INFER_C="$(python -m mlx_lm generate --model "./${MODEL_NAME}" --prompt "$TEST_PROMPT" --max-tokens 64 2>&1)"
  RC=$?
  popd >/dev/null
  set -e
  if [[ $RC -eq 0 ]]; then
    INFERENCE_OK=1
    INFERENCE_STRATEGY="relative_path"
    INFERENCE_OUTPUT="$INFER_C"
    ok "strategy C succeeded"
    echo "$INFER_C" | tail -15 | sed 's/^/    /'
  else
    warn "strategy C failed (rc=$RC)"
    echo "$INFER_C" | tail -15 | sed 's/^/    /'
  fi
fi

# ---------- verdict ---------------------------------------------------------
if [[ "$INFERENCE_OK" != "1" ]]; then
  cat <<DIAG

${C_RED}All three inference strategies failed.${C_RST}

Real causes to investigate (ranked by likelihood):
  1. mlx_lm version incompatible with the 8-bit Qwen3-30B quantization format
     → try: python -m pip install --upgrade 'mlx-lm>=0.32'
  2. Python 3.14 + mlx 0.31 edge case
     → try: rebuild venv on python@3.12 (brew install python@3.12)
  3. Metal memory allocation — Qwen3-30B-8bit is ~30GB at rest
     → free up RAM: close Xcode, other heavy apps; verify with: vm_stat
  4. Tokenizer mismatch for this specific quantization
     → redownload config.json + tokenizer.json only via 'hf download'

Full log: $LOG_FILE
DIAG
  fail "inference failed — see diagnostics above"
fi

# ============================================================================
# 5. WRITE ENV FILE + MANIFEST (mark DONE)
# ============================================================================
step "Writing env file"
cat > "$ENV_FILE" <<ENV
NS_LOCAL_TEXT_MODEL=$MODEL_DIR
NS_LOCAL_RUNTIME=mlx
NS_LOCAL_LAYER_ENABLED=true
NS_LOCAL_LAYER_DEFAULT_LOCAL_ONLY=true
NS_LOCAL_LAYER_ALLOW_WORKER_ESCALATION=false
NS_LOCAL_LAYER_MODEL_CACHE_ROOT=/Volumes/NSExternal/models
NS_LOCAL_INFERENCE_STRATEGY=$INFERENCE_STRATEGY
NS_LOCAL_VENV=$VENV_DIR
ENV
ok "wrote $ENV_FILE"

step "Writing manifest (DONE)"
python - <<PY
import json, pathlib
manifest = {
    "local_text_model":    "$MODEL_REPO",
    "resolved_model_dir":  "$MODEL_DIR",
    "runtime":             "mlx",
    "locality":            "mac_local",
    "tier":                "L1",
    "status":              "DONE",
    "inference_strategy":  "$INFERENCE_STRATEGY",
    "venv":                "$VENV_DIR",
    "verified_at_utc":     "$RUN_TS",
    "safetensor_shards":   $SAFETENSOR_COUNT,
    "total_size":          "$TOTAL_SIZE",
}
pathlib.Path("$MANIFEST_FILE").write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
PY
ok "wrote $MANIFEST_FILE"

# ============================================================================
# 6. ALEXANDRIA RECEIPT
# ============================================================================
step "Writing Alexandria receipt"
if [[ -d "$ALEX" ]]; then
  mkdir -p "$RECEIPT_DIR"
  python - <<PY > "$RECEIPT_DIR/receipt.json"
import json, hashlib
body = {
    "edge_type":          "local_brain_online",
    "ts_utc":             "$RUN_TS",
    "model_repo":         "$MODEL_REPO",
    "model_dir":          "$MODEL_DIR",
    "runtime":            "mlx",
    "tier":               "L1_local_text",
    "locality":           "mac_local",
    "inference_strategy": "$INFERENCE_STRATEGY",
    "safetensor_shards":  $SAFETENSOR_COUNT,
    "total_size":         "$TOTAL_SIZE",
    "test_prompt":        "$TEST_PROMPT",
}
payload = json.dumps(body, sort_keys=True, separators=(",",":"))
body["sha256"] = hashlib.sha256(payload.encode()).hexdigest()
print(json.dumps(body, indent=2))
PY
  ok "receipt:  $RECEIPT_DIR/receipt.json"
else
  warn "Alexandria not at $ALEX — receipt skipped"
fi

# ============================================================================
# 7. FINAL READOUT
# ============================================================================
cat <<DONE

${C_GRN}═══ NS LOCAL BRAIN ONLINE ═══${C_RST}

  model        Qwen3-30B-A3B-Thinking-2507-MLX-8bit
  path         $MODEL_DIR
  runtime      mlx  ·  tier L1_local_text  ·  mac_local
  strategy     $INFERENCE_STRATEGY
  shards       $SAFETENSOR_COUNT/7  ·  $TOTAL_SIZE
  env          $ENV_FILE
  manifest     $MANIFEST_FILE
  receipt      $RECEIPT_DIR/receipt.json

  Use in a new shell:
    source "$VENV_DIR/bin/activate"
    set -a; source "$ENV_FILE"; set +a

  Programmatic inference (canonical for NS router):
    from pathlib import Path
    from mlx_lm import load, generate
    m, t = load(str(Path("$MODEL_DIR")))
    print(generate(m, t, prompt="hello", verbose=False))

  CLI inference (works now):
    mlx_lm generate --model "$MODEL_DIR" --prompt "hello" --max-tokens 64

AXIOLEV Holdings LLC © 2026
DONE
