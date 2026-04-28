#!/usr/bin/env bash
# ============================================================
# AXIOLEV NS∞ — Founder Cockpit MAX Build Script
# Builds NSFounderCockpit.app via Swift Package Manager
# Output: dist/mac/NSFounderCockpit.app
# ============================================================
set -euo pipefail
IFS=$'\n\t'

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
log()  { echo -e "${CYAN}[BUILD]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()  { echo -e "${RED}[HALT]${NC} $*"; exit 1; }

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

log "=== NSFounderCockpit MAX Build ==="
log "Dir: $SCRIPT_DIR"
log "Swift: $(swift --version 2>/dev/null | head -1)"

# Clean prior build artifacts
log "Cleaning .build/..."
rm -rf .build/release 2>/dev/null || true

# Build release
log "Building release (swift build -c release)..."
swift build -c release 2>&1

BUILD_PRODUCT=$(find .build -name "NSFounderCockpit" -type f 2>/dev/null | grep -v "\.dSYM\|\.build/checkouts" | grep "/release/" | head -1)
[ -z "$BUILD_PRODUCT" ] && die "Build product not found under .build/"

ok "Build product: $BUILD_PRODUCT"

# Bundle into .app
BUNDLE_DIR="dist/mac/NSFounderCockpit.app"
APP_DIR="$BUNDLE_DIR/Contents"
mkdir -p "$APP_DIR/MacOS" "$APP_DIR/Resources"

cp "$BUILD_PRODUCT" "$APP_DIR/MacOS/NSFounderCockpit"
chmod +x "$APP_DIR/MacOS/NSFounderCockpit"

# Write real Info.plist with CFBundleExecutable so `open` works
cat > "$APP_DIR/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>NS∞ Founder Cockpit</string>
  <key>CFBundleDisplayName</key><string>NS∞ Founder Cockpit</string>
  <key>CFBundleIdentifier</key><string>com.axiolev.ns.founder-cockpit</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>CFBundleShortVersionString</key><string>1.0.0</string>
  <key>CFBundleExecutable</key><string>NSFounderCockpit</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleSignature</key><string>????</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
  <key>NSPrincipalClass</key><string>NSApplication</string>
</dict></plist>
PLIST
printf "APPL????" > "$APP_DIR/PkgInfo"
plutil -lint "$APP_DIR/Info.plist" > /dev/null && ok "Info.plist valid" || warn "Info.plist lint failed"

ok "App bundle: dist/mac/NSFounderCockpit.app"

echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  BUILD COMPLETE — NSFounderCockpit MAX    ${NC}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════${NC}"
echo "  Binary : $APP_DIR/MacOS/NSFounderCockpit"
echo "  App    : dist/mac/NSFounderCockpit.app"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════${NC}"
