#!/usr/bin/env bash
# NS∞ Founder Habitat — native macOS build & run
# Post Xcode 26.4.1 SDK install. Run from ~/axiolev_runtime.
# Canonical rule: never fake green. Every failure surfaces loudly.

set -euo pipefail

# ---------- paths ----------
REPO="${HOME}/axiolev_runtime"
APP_DIR="${REPO}/apps/ns_mac/NSInfinityApp"
PROJ="${APP_DIR}/NSInfinityApp.xcodeproj"
SCHEME="NSInfinityApp"
CONFIG="Debug"
DERIVED="${REPO}/.build/ns_mac_derived"
LOG="${REPO}/.build/ns_mac_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$(dirname "$LOG")"

banner() { printf '\n\033[1;35m== %s ==\033[0m\n' "$*"; }
ok()     { printf '\033[1;32m[ok]\033[0m %s\n' "$*"; }
fail()   { printf '\033[1;31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

# ---------- preflight ----------
banner "Preflight"
cd "$REPO" || fail "repo not found: $REPO"
[[ -d "$PROJ" ]] || fail "xcodeproj missing: $PROJ"

# Xcode selected?
XCODE_PATH="$(xcode-select -p 2>/dev/null || true)"
[[ "$XCODE_PATH" == *"Xcode.app"* ]] || {
  echo "Xcode not selected. Fix with:"
  echo "  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
  fail "xcode-select points at: $XCODE_PATH"
}
ok "xcode-select: $XCODE_PATH"

XCBUILD_VER="$(xcodebuild -version | head -1)"
ok "$XCBUILD_VER"

# License accepted?
xcodebuild -checkFirstLaunchStatus >/dev/null 2>&1 || {
  echo "First-launch tasks pending. Running:"
  echo "  sudo xcodebuild -runFirstLaunch"
  fail "accept license & install components first"
}
ok "first-launch status clean"

# macOS 26.4 SDK present?
if ! xcodebuild -showsdks 2>/dev/null | grep -qi "macosx26"; then
  fail "macOS 26.x SDK not visible to xcodebuild — check Xcode → Settings → Platforms"
fi
ok "macOS 26 SDK visible"

# Capture current objectVersion (it was 56 pre-upgrade)
OBJVER_BEFORE="$(grep -Eo 'objectVersion = [0-9]+' "$PROJ/project.pbxproj" | head -1 | awk '{print $3}')"
ok "project objectVersion (pre-build): ${OBJVER_BEFORE}"

# Git state snapshot
cd "$REPO"
if git rev-parse --git-dir >/dev/null 2>&1; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  HEAD_SHA="$(git rev-parse --short HEAD)"
  ok "git: ${BRANCH} @ ${HEAD_SHA}"
  if ! git diff --quiet "$PROJ/project.pbxproj" 2>/dev/null; then
    echo "[note] project.pbxproj has uncommitted changes (likely Xcode auto-upgrade)"
  fi
fi

# ---------- resolve packages (handles SPM deps if any) ----------
banner "Resolve Swift packages"
xcodebuild -resolvePackageDependencies \
  -project "$PROJ" \
  -scheme "$SCHEME" \
  -derivedDataPath "$DERIVED" 2>&1 | tee -a "$LOG" | tail -20 || \
  fail "package resolution failed (see $LOG)"
ok "packages resolved"

# ---------- build ----------
banner "Build ($CONFIG for my-mac)"
# my-mac destination avoids simulator/arch confusion on Apple Silicon + x86_64
set +e
xcodebuild \
  -project "$PROJ" \
  -scheme "$SCHEME" \
  -configuration "$CONFIG" \
  -destination 'platform=macOS' \
  -derivedDataPath "$DERIVED" \
  -skipMacroValidation \
  ONLY_ACTIVE_ARCH=YES \
  CODE_SIGN_IDENTITY="-" \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGNING_ALLOWED=NO \
  build 2>&1 | tee -a "$LOG" | \
    xcbeautify 2>/dev/null || cat  # pretty if xcbeautify present, else raw
BUILD_RC=${PIPESTATUS[0]}
set -e

if [[ $BUILD_RC -ne 0 ]]; then
  echo
  echo "---- last 40 lines of log ----"
  tail -40 "$LOG"
  fail "xcodebuild returned $BUILD_RC — full log: $LOG"
fi
ok "build succeeded"

# Confirm objectVersion upgrade (Xcode 26 typically bumps 56 → 77)
OBJVER_AFTER="$(grep -Eo 'objectVersion = [0-9]+' "$PROJ/project.pbxproj" | head -1 | awk '{print $3}')"
if [[ "$OBJVER_AFTER" != "$OBJVER_BEFORE" ]]; then
  echo "[note] project.pbxproj objectVersion: ${OBJVER_BEFORE} → ${OBJVER_AFTER} (Xcode 26 upgrade)"
  echo "       commit this change as part of landing the native app batch:"
  echo "         git add ${PROJ#${REPO}/}/project.pbxproj && git commit -m 'chore(ns_mac): xcode 26 project format upgrade'"
fi

# ---------- locate built .app ----------
APP_BUNDLE="$(/usr/bin/find "$DERIVED/Build/Products/${CONFIG}" -maxdepth 2 -name "${SCHEME}.app" -print -quit 2>/dev/null || true)"
[[ -n "${APP_BUNDLE:-}" && -d "$APP_BUNDLE" ]] || fail "built .app not found under $DERIVED"
ok "app: $APP_BUNDLE"

# Gatekeeper will yell on an unsigned ad-hoc build — fine for local dev
codesign --force --deep --sign - "$APP_BUNDLE" >/dev/null 2>&1 || true

# ---------- run ----------
banner "Launch"
# Kill any prior instance so we see fresh output
pkill -x "$SCHEME" 2>/dev/null || true
sleep 0.5

open -n "$APP_BUNDLE"
sleep 1.5

if pgrep -x "$SCHEME" >/dev/null; then
  ok "$SCHEME running (pid $(pgrep -x $SCHEME))"
else
  fail "app launched but process not visible — check Console.app for $SCHEME"
fi

echo
echo "Build log: $LOG"
echo "Stream app logs live:  log stream --predicate 'process == \"$SCHEME\"' --level info"
echo "Stop app:              pkill -x $SCHEME"
