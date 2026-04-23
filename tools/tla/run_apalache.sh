#!/usr/bin/env bash
# tools/tla/run_apalache.sh
# NS∞ Dignity Kernel — Apalache bounded model checker runner
# AXIOLEV Holdings LLC © 2026
#
# Usage:
#   ./tools/tla/run_apalache.sh              # check all 10 invariants
#   ./tools/tla/run_apalache.sh I5_RiskTierGate  # check one invariant
#
# Outputs:  artifacts/tla/<invariant>.json  per invariant
# Returns:  0 if all checked invariants report NoError
#           0 if apalache-mc not found (WARN, specs still committed)
#           1 if any invariant reports Error or Violation

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

SPEC="${REPO_ROOT}/specs/tla/Dignity.tla"
CFG_DIR="${REPO_ROOT}/specs/tla"
ARTIFACTS="${REPO_ROOT}/artifacts/tla"

ALL_INVARIANTS=(
    I1_NonBypass
    I2_NonDestruct
    I3_PolicyQuorum
    I4_DignityGuard
    I5_RiskTierGate
    I6_Disjoint
    I7_TierRatchet
    I8_SecureGate
    I9_DenialReceipted
    I10_Receipted
)

# ── Argument handling ──────────────────────────────────────────────────
if [[ -n "${1:-}" ]]; then
    INVARIANTS=("$1")
else
    INVARIANTS=("${ALL_INVARIANTS[@]}")
fi

mkdir -p "${ARTIFACTS}"

# ── Guard: emit WARN and exit 0 if apalache-mc absent ─────────────────
if ! command -v apalache-mc &>/dev/null; then
    echo "WARN: apalache-mc not found — bounded model checks skipped" >&2
    echo "      Specs and cfgs are committed; install Apalache to run checks." >&2
    exit 0
fi

APALACHE_VERSION="$(apalache-mc version 2>/dev/null | head -1 || echo 'unknown')"
echo "==> apalache-mc: ${APALACHE_VERSION}"
echo "==> spec:        ${SPEC}"
echo ""

OVERALL_EXIT=0

for INV in "${INVARIANTS[@]}"; do
    CFG="${CFG_DIR}/${INV}.cfg"
    OUT="${ARTIFACTS}/${INV}.json"
    WORK_DIR="${ARTIFACTS}/${INV}_work"
    LOG="${ARTIFACTS}/${INV}.log"

    printf "── %-22s " "${INV}"

    mkdir -p "${WORK_DIR}"

    # Run Apalache; tee full output to log
    if apalache-mc check \
            --length=8 \
            --inv="${INV}" \
            --cinit=CInit \
            --config="${CFG}" \
            --out-dir="${WORK_DIR}" \
            "${SPEC}" \
            >"${LOG}" 2>&1; then
        STATUS="NoError"
        printf "OK   → %s\n" "${STATUS}"
    else
        RC=$?
        # Distinguish counterexample from internal/parse error
        if grep -q "COUNTEREXAMPLE\|violation\|Invariant.*violated" "${LOG}" 2>/dev/null; then
            STATUS="Violation"
        else
            STATUS="Error"
        fi
        printf "FAIL → %s (exit %d)\n" "${STATUS}" "${RC}"
        echo "       log: ${LOG}" >&2
        OVERALL_EXIT=1
    fi

    TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    cat > "${OUT}" <<JSONEOF
{
  "invariant": "${INV}",
  "status": "${STATUS}",
  "length": 8,
  "domain_cardinality": 4,
  "timestamp": "${TIMESTAMP}",
  "spec": "specs/tla/Dignity.tla",
  "cfg": "specs/tla/${INV}.cfg",
  "log": "artifacts/tla/${INV}.log"
}
JSONEOF
done

echo ""
if [[ ${OVERALL_EXIT} -eq 0 ]]; then
    echo "==> All checked invariants: NoError"
else
    printf "==> FAILED — see %s/ for logs\n" "${ARTIFACTS}" >&2
fi

exit "${OVERALL_EXIT}"
