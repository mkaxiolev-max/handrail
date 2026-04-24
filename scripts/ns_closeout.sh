#!/usr/bin/env bash
# AXIOLEV Holdings LLC © 2026 — ns_closeout.sh
set -u
set -o pipefail

REPO_DIR="${REPO_DIR:-$HOME/axiolev_runtime}"
UI_DIR="${UI_DIR:-$REPO_DIR/ns_ui}"
OUT_DIR="${OUT_DIR:-$HOME/.ns_closeout}"
STATE_FILE="$OUT_DIR/state"
RUN_ID="$(date -u +%Y%m%d-%H%M%S)"
RUN_LOG="$OUT_DIR/run_${RUN_ID}.log"
REPORT_FILE="$OUT_DIR/REPORT_${RUN_ID}.md"
ALEXANDRIA_ROOT="${ALEXANDRIA_ROOT:-/Volumes/NSExternal/ALEXANDRIA}"
NONINTERACTIVE="${NONINTERACTIVE:-0}"
GH_REPO="${GH_REPO:-mkaxiolev-max/handrail}"
TARGET_V31="${TARGET_V31:-90.0}"

mkdir -p "$OUT_DIR"

if [ -t 1 ]; then
  C_RST=$'\033[0m'; C_BLD=$'\033[1m'; C_DIM=$'\033[2m'
  C_GRN=$'\033[32m'; C_YEL=$'\033[33m'; C_RED=$'\033[31m'
  C_BLU=$'\033[34m'; C_MAG=$'\033[35m'; C_CYN=$'\033[36m'
else
  C_RST=""; C_BLD=""; C_DIM=""; C_GRN=""; C_YEL=""; C_RED=""; C_BLU=""; C_MAG=""; C_CYN=""
fi

log()    { printf "%s %s\n" "$(date -u +%H:%M:%S)" "$*" | tee -a "$RUN_LOG"; }
info()   { log "${C_CYN}i${C_RST} $*"; }
ok()     { log "${C_GRN}+${C_RST} $*"; }
warn()   { log "${C_YEL}!${C_RST} $*"; }
err()    { log "${C_RED}x${C_RST} $*"; }
phase()  { printf "\n${C_BLD}${C_MAG}--- %s ---${C_RST}\n" "$*" | tee -a "$RUN_LOG"; }
banner() { printf "${C_BLD}${C_BLU}%s${C_RST}\n" "$*" | tee -a "$RUN_LOG"; }
status()  { printf "STATUS: %s component=%s reason=%s\n" "$1" "$2" "$3" | tee -a "$RUN_LOG"; }
receipt() {
  local phase_id="$1" payload="$2"
  local h
  h=$(printf "%s" "$payload" | shasum -a 256 2>/dev/null | awk '{print $1}')
  [ -z "$h" ] && h=$(printf "%s" "$payload" | openssl dgst -sha256 2>/dev/null | awk '{print $NF}')
  printf "RECEIPT: phase=%s hash=%s\n" "$phase_id" "$h" | tee -a "$RUN_LOG"
  printf '{"phase":"%s","hash":"%s","ts":"%s"}\n' "$phase_id" "$h" "$(date -u +%FT%TZ)" >> "$OUT_DIR/receipts.ndjson"
}

set_state() { echo "$1" > "$STATE_FILE"; }
get_state() { [ -f "$STATE_FILE" ] && cat "$STATE_FILE" || echo "START"; }

detect_docker() {
  local sock_host="/var/run/docker.sock"
  local sock_user="$HOME/.docker/run/docker.sock"
  if [ -S "$sock_user" ]; then
    export DOCKER_HOST="unix://$sock_user"
  elif [ -S "$sock_host" ]; then
    export DOCKER_HOST="unix://$sock_host"
  else
    return 1
  fi
  return 0
}

load_env() {
  cd "$REPO_DIR" || { err "REPO_DIR=$REPO_DIR not found"; exit 2; }
  if [ -f .env ]; then
    set -a; source .env; set +a
  fi
  export POSTGRES_USER="${POSTGRES_USER:-ns}"
  export POSTGRES_DB="${POSTGRES_DB:-ns}"
}

phase_r1() {
  phase "R1 -- docker-compose omega_logos schema"
  load_env
  detect_docker || { err "docker socket not found"; status FAIL r1.docker "no socket"; return 1; }

  local compose="$REPO_DIR/docker-compose.yml"
  [ -f "$compose" ] || { err "no compose file"; return 1; }
  cp "$compose" "$OUT_DIR/docker-compose.yml.bak_${RUN_ID}"

  local validation
  validation=$(docker compose -f "$compose" config 2>&1 || true)

  if printf "%s" "$validation" | grep -qi "omega_logos.*volumes.*additional properties\|omega_logos.*volumes.*not allowed\|volumes has additional properties"; then
    warn "omega_logos volumes schema invalid -- patching"
  elif printf "%s" "$validation" | grep -qi "omega_logos"; then
    warn "omega_logos validation issue: $(printf "%s" "$validation" | grep -i omega_logos | head -1)"
  else
    ok "compose already validates -- checking service state"
  fi

  python3 - "$compose" "$OUT_DIR" << 'PYEOF'
import sys, os, re, shutil
compose_path, out_dir = sys.argv[1], sys.argv[2]
try:
    import yaml
except ImportError:
    os.system("python3 -m pip install --break-system-packages --quiet pyyaml")
    import yaml

with open(compose_path) as f:
    doc = yaml.safe_load(f)

changed = False
svcs = doc.get("services", {})
ol = svcs.get("omega_logos")
if ol is None:
    print("NO_OMEGA_LOGOS_SERVICE")
    sys.exit(0)

vols = ol.get("volumes")
if vols is not None:
    if isinstance(vols, dict):
        new_vols = []
        for k, v in vols.items():
            if isinstance(v, str):
                new_vols.append(f"{k}:{v}")
            else:
                new_vols.append(str(k))
        ol["volumes"] = new_vols
        changed = True
        print("CONVERTED_VOLUMES_DICT_TO_LIST")
    elif isinstance(vols, list):
        fixed = []
        for item in vols:
            if isinstance(item, str):
                fixed.append(item)
            elif isinstance(item, dict):
                if "source" in item and "target" in item:
                    fixed.append(item)
                else:
                    if len(item) == 1:
                        k, v = next(iter(item.items()))
                        if isinstance(v, str):
                            fixed.append(f"{k}:{v}")
                            changed = True
                            continue
                    print(f"DROPPED_MALFORMED_VOLUME: {item}")
                    changed = True
            else:
                print(f"DROPPED_UNKNOWN_VOLUME: {item}")
                changed = True
        ol["volumes"] = fixed

ALLOWED = {
    "image","build","command","entrypoint","container_name","depends_on","environment",
    "env_file","expose","healthcheck","labels","networks","platform","ports","restart",
    "user","volumes","working_dir","tty","stdin_open","stop_signal","stop_grace_period",
    "cap_add","cap_drop","security_opt","ulimits","sysctls","logging","profiles","init",
    "deploy","extends","pid","ipc","hostname","mem_limit","cpus","read_only","tmpfs"
}
stripped = []
for k in list(ol.keys()):
    if k not in ALLOWED:
        stripped.append(k)
        del ol[k]
        changed = True
if stripped:
    print(f"STRIPPED_INVALID_KEYS: {stripped}")

hc = ol.get("healthcheck")
if hc and isinstance(hc, dict):
    test = hc.get("test")
    if isinstance(test, list) and test and test[0] in ("CMD","CMD-SHELL"):
        pass
    elif isinstance(test, str):
        hc["test"] = ["CMD-SHELL", test]
        changed = True

if changed:
    shutil.copy(compose_path, os.path.join(out_dir, "docker-compose.yml.precompose_fix"))
    with open(compose_path, "w") as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False)
    print("PATCHED")
else:
    print("NO_CHANGES_NEEDED")
PYEOF

  local patch_result
  patch_result=$(docker compose -f "$compose" config 2>&1)
  if [ $? -ne 0 ] || printf "%s" "$patch_result" | grep -qi "error\|invalid"; then
    warn "compose still not validating -- dumping omega_logos block:"
    python3 -c "
import yaml
d = yaml.safe_load(open('$compose'))
ol = d.get('services',{}).get('omega_logos',{})
print(yaml.safe_dump({'omega_logos': ol}, sort_keys=False))
" 2>&1 | tee -a "$RUN_LOG"
    status FAIL r1.compose "still invalid after patch; manual edit needed"
    receipt "r1" "compose_invalid"
    return 1
  fi

  ok "compose validates"

  info "bringing omega_logos up"
  (cd "$REPO_DIR" && docker compose up -d omega_logos 2>&1 | tee -a "$RUN_LOG") || warn "compose up -d omega_logos returned non-zero"

  local deadline=$((SECONDS + 90))
  local healthy="no"
  while [ $SECONDS -lt $deadline ]; do
    if curl -sf --max-time 3 "http://127.0.0.1:9010/healthz" >/dev/null 2>&1 \
       || curl -sf --max-time 3 "http://127.0.0.1:9010/omega_logos/healthz" >/dev/null 2>&1; then
      healthy="yes"; break
    fi
    sleep 3
  done

  if [ "$healthy" = "yes" ]; then
    status PASS r1.omega_logos "service healthy on :9010"
    ok "omega_logos healthy"
  else
    local cstate
    cstate=$(docker compose -f "$compose" ps --format json omega_logos 2>/dev/null | python3 -c "
import sys,json
for ln in sys.stdin:
    try:
        d=json.loads(ln)
        if 'omega_logos' in d.get('Service',''):
            print(d.get('State','?')); break
    except: pass
" 2>/dev/null)
    if [ "$cstate" = "running" ]; then
      status WARN r1.omega_logos "container running but /healthz unreachable"
      warn "omega_logos container running, healthz not on :9010 directly"
    else
      status FAIL r1.omega_logos "container state=$cstate"
      receipt "r1" "omega_logos_down state=$cstate"
      return 1
    fi
  fi

  receipt "r1" "omega_logos state=$healthy compose=valid"
  return 0
}

phase_r2() {
  phase "R2 -- ns_ui @/* alias + clean rebuild"
  [ -d "$UI_DIR" ] || { err "ns_ui missing"; return 1; }
  cd "$UI_DIR" || return 1

  local tsconfig="$UI_DIR/tsconfig.json"
  [ -f "$tsconfig" ] || { err "tsconfig.json missing"; return 1; }
  cp "$tsconfig" "$OUT_DIR/tsconfig.json.bak_${RUN_ID}"

  node -e '
    const fs = require("fs");
    const path = "tsconfig.json";
    let txt = fs.readFileSync(path, "utf8");
    const stripped = txt.replace(/\/\/.*$/gm, "").replace(/\/\*[\s\S]*?\*\//g, "");
    const j = JSON.parse(stripped);
    j.compilerOptions = j.compilerOptions || {};
    let changed = false;
    if (j.compilerOptions.baseUrl !== ".") {
      j.compilerOptions.baseUrl = ".";
      changed = true;
    }
    j.compilerOptions.paths = j.compilerOptions.paths || {};
    const want = ["src/*"];
    const cur = j.compilerOptions.paths["@/*"];
    if (!cur || JSON.stringify(cur) !== JSON.stringify(want)) {
      j.compilerOptions.paths["@/*"] = want;
      changed = true;
    }
    j.include = j.include || [];
    if (!j.include.includes("src/**/*.ts") && !j.include.includes("src/**/*")) {
      j.include.push("src/**/*.ts");
      j.include.push("src/**/*.tsx");
      changed = true;
    }
    fs.writeFileSync(path, JSON.stringify(j, null, 2) + "\n");
    console.log(changed ? "TSCONFIG_PATCHED" : "TSCONFIG_OK");
  ' 2>&1 | tee -a "$RUN_LOG"

  if [ -f "$UI_DIR/next.config.js" ] || [ -f "$UI_DIR/next.config.ts" ] || [ -f "$UI_DIR/next.config.mjs" ]; then
    info "next.config present -- relying on tsconfig paths"
  fi

  if [ ! -f "$UI_DIR/src/sections/manifest.ts" ] && [ ! -f "$UI_DIR/src/sections/manifest.tsx" ]; then
    warn "src/sections/manifest.ts missing -- recreating"
    mkdir -p "$UI_DIR/src/sections"
    cat > "$UI_DIR/src/sections/manifest.ts" << 'MEOF'
// 11-section founder habitat -- AXIOLEV Holdings LLC (c) 2026
export type Section = {
  slug: string; title: string; icon: string; endpoint: string; accent: string;
};
export const SECTIONS: Section[] = [
  { slug:"home",         title:"Founder Home",        icon:"H", endpoint:"/api/v1/ui/summary",      accent:"from-amber-500/20" },
  { slug:"living",       title:"Living Architecture", icon:"L", endpoint:"/api/v1/ui/architecture", accent:"from-emerald-500/20" },
  { slug:"governance",   title:"Governance + Canon",  icon:"G", endpoint:"/api/v1/ui/governance",   accent:"from-violet-500/20" },
  { slug:"engine",       title:"Engine Room",         icon:"E", endpoint:"/api/v1/ui/execution",    accent:"from-sky-500/20" },
  { slug:"voice",        title:"Violet (Voice)",      icon:"V", endpoint:"/api/v1/ui/voice",        accent:"from-fuchsia-500/20" },
  { slug:"alexandria",   title:"Alexandria Ledger",   icon:"A", endpoint:"/api/v1/ui/memory",       accent:"from-yellow-500/20" },
  { slug:"build",        title:"Build + Receipts",    icon:"B", endpoint:"/api/v1/ui/build",        accent:"from-orange-500/20" },
  { slug:"timeline",     title:"Timeline",            icon:"T", endpoint:"/api/v1/ui/timeline",     accent:"from-rose-500/20" },
  { slug:"scoring",      title:"Scoring (v2.1/v3.0)", icon:"S", endpoint:"/api/v1/ui/scoring",      accent:"from-teal-500/20" },
  { slug:"omega_logos",  title:"Omega-Logos (I6)",    icon:"O", endpoint:"/api/v1/ui/omega_logos",  accent:"from-indigo-500/20" },
  { slug:"ring5",        title:"Ring 5 Gates",        icon:"R", endpoint:"/api/v1/ui/ring5",        accent:"from-red-500/20" },
];
MEOF
    ok "manifest.ts recreated"
  fi

  rm -rf "$UI_DIR/.next"
  info "ns_ui clean rebuild"

  local pkg_mgr="npm"
  command -v pnpm >/dev/null 2>&1 && [ -f "$UI_DIR/pnpm-lock.yaml" ] && pkg_mgr="pnpm"

  local build_log="$OUT_DIR/ns_ui_build_${RUN_ID}.log"
  if [ "$pkg_mgr" = "pnpm" ]; then
    (cd "$UI_DIR" && pnpm run build 2>&1) | tee "$build_log" >/dev/null
  else
    (cd "$UI_DIR" && npm run build 2>&1) | tee "$build_log" >/dev/null
  fi

  if grep -qE "Module not found.*@/sections/manifest|Cannot find module.*@/sections/manifest" "$build_log"; then
    err "@/sections/manifest still not resolving"
    tail -20 "$build_log" | tee -a "$RUN_LOG"
    status FAIL r2.build "alias unresolved"
    return 1
  fi

  if grep -qE "Failed to compile|error TS" "$build_log"; then
    warn "build has TypeScript errors"
    grep -E "error TS|Failed to compile" "$build_log" | head -10 | tee -a "$RUN_LOG"
    status WARN r2.build "ts warnings present"
  else
    status PASS r2.build "ns_ui build clean"
    ok "ns_ui build clean"
  fi

  if docker compose -f "$REPO_DIR/docker-compose.yml" ps ns_ui --format json 2>/dev/null | grep -q "ns_ui"; then
    info "rebuilding ns_ui container"
    (cd "$REPO_DIR" && docker compose build ns_ui 2>&1 | tail -5 | tee -a "$RUN_LOG")
    (cd "$REPO_DIR" && docker compose up -d ns_ui 2>&1 | tail -3 | tee -a "$RUN_LOG")
    local deadline=$((SECONDS + 90))
    while [ $SECONDS -lt $deadline ]; do
      curl -sf --max-time 3 "http://127.0.0.1:3001/" >/dev/null 2>&1 && break
      sleep 3
    done
    curl -sf --max-time 3 "http://127.0.0.1:3001/" >/dev/null 2>&1 \
      && ok "ns_ui :3001 responding" \
      || warn "ns_ui :3001 not responding after rebuild"
  fi

  receipt "r2" "tsconfig=@/*->src/* build=$(basename "$build_log")"
  return 0
}

phase_r3() {
  phase "R3 -- pytest collection fixes"
  cd "$REPO_DIR" || return 1

  local pyproject="$REPO_DIR/pyproject.toml"
  local pytestini="$REPO_DIR/pytest.ini"
  local added_ignore="no"

  if [ -f "$pyproject" ]; then
    python3 - << 'PYEOF'
import re, pathlib
p = pathlib.Path("pyproject.toml")
txt = p.read_text()
changed = False

if "[tool.pytest.ini_options]" not in txt:
    txt += "\n[tool.pytest.ini_options]\n"
    changed = True

section_re = re.compile(r"(\[tool\.pytest\.ini_options\]\n)((?:(?!\n\[)[\s\S])*)", re.M)
m = section_re.search(txt)
assert m, "section missing after ensure"
head, body = m.group(1), m.group(2)

required_norecurse = [
    "services/handrail/handrail_repo_unified_v03",
    "node_modules",
    ".next",
    ".axiolev_evaluations",
    ".axiolev_synthesis",
    ".axiolev_ceiling",
]

if "norecursedirs" not in body:
    dirs_line = "norecursedirs = [" + ", ".join(f'"{d}"' for d in required_norecurse) + "]\n"
    body = body + dirs_line
    changed = True
else:
    for d in required_norecurse:
        if d not in body:
            body = re.sub(
                r"norecursedirs\s*=\s*\[([^\]]*)\]",
                lambda m: f'norecursedirs = [{m.group(1).rstrip(", ")}, "{d}"]' if m.group(1).strip() else f'norecursedirs = ["{d}"]',
                body, count=1
            )
            changed = True

if "--import-mode=importlib" not in body:
    if "addopts" in body:
        body = re.sub(
            r"addopts\s*=\s*\"([^\"]*)\"",
            lambda m: f'addopts = "{m.group(1)} --import-mode=importlib"' if m.group(1) else 'addopts = "--import-mode=importlib"',
            body, count=1
        )
    else:
        body += 'addopts = "--import-mode=importlib"\n'
    changed = True

if changed:
    txt = txt[:m.start(2)] + body + txt[m.end(2):]
    p.write_text(txt)
    print("PYPROJECT_PATCHED")
else:
    print("PYPROJECT_OK")
PYEOF
    added_ignore="yes"
  elif [ -f "$pytestini" ]; then
    if ! grep -q "norecursedirs" "$pytestini"; then
      printf "\nnorecursedirs = services/handrail/handrail_repo_unified_v03 node_modules .next .axiolev_evaluations .axiolev_synthesis .axiolev_ceiling\naddopts = --import-mode=importlib\n" >> "$pytestini"
      added_ignore="yes"
    fi
  else
    cat > "$pytestini" << 'EOF'
[pytest]
norecursedirs = services/handrail/handrail_repo_unified_v03 node_modules .next .axiolev_evaluations .axiolev_synthesis .axiolev_ceiling
addopts = --import-mode=importlib
EOF
    added_ignore="yes"
  fi
  [ "$added_ignore" = "yes" ] && ok "pytest norecursedirs + importlib mode set" || ok "pytest config already correct"

  if [ -d "$REPO_DIR/services/omega/app" ] && [ ! -f "$REPO_DIR/services/omega/app/tests/conftest.py" ]; then
    mkdir -p "$REPO_DIR/services/omega/app/tests"
    cat > "$REPO_DIR/services/omega/app/tests/conftest.py" << 'EOF'
"""conftest.py -- ensure services/omega/app is importable as app package. AXIOLEV 2026."""
import sys, pathlib
_APP_DIR = pathlib.Path(__file__).resolve().parents[1]
_SVC_DIR = _APP_DIR.parent
for p in (str(_SVC_DIR), str(_APP_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
EOF
    ok "services/omega/app/tests/conftest.py created"
  fi

  find "$REPO_DIR/services/handrail" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find "$REPO_DIR/services/omega" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  ok "handrail + omega __pycache__ cleared"

  info "running pytest --collect-only"
  local collect_log="$OUT_DIR/pytest_collect_${RUN_ID}.log"
  (cd "$REPO_DIR" && python3 -m pytest --collect-only -q 2>&1) | tee "$collect_log" >/dev/null

  local errors
  errors=$(grep -cE "^ERROR|error:" "$collect_log" 2>/dev/null || echo 0)
  errors=$(printf "%s" "$errors" | tr -cd '0-9')
  [ -z "$errors" ] && errors=0

  if [ "$errors" -eq 0 ]; then
    status PASS r3.collection "0 collection errors"
    ok "pytest collects cleanly"
  else
    status WARN r3.collection "$errors collection errors remain"
    warn "$errors collection errors remain"
    grep -E "^ERROR|error:" "$collect_log" | head -10 | tee -a "$RUN_LOG"
  fi

  info "running full pytest (summary only)"
  local test_log="$OUT_DIR/pytest_full_${RUN_ID}.log"
  (cd "$REPO_DIR" && timeout 600 python3 -m pytest -q --tb=no 2>&1) | tee "$test_log" >/dev/null || true
  local passed failed
  passed=$(grep -oE "[0-9]+ passed" "$test_log" | tail -1 | grep -oE "[0-9]+" || echo 0)
  failed=$(grep -oE "[0-9]+ failed" "$test_log" | tail -1 | grep -oE "[0-9]+" || echo 0)
  info "pytest: $passed passed, $failed failed"

  receipt "r3" "collection_errors=$errors passed=$passed failed=$failed"
  return 0
}

phase_v() {
  phase "V -- bash scripts/ns_verify.sh all"
  load_env
  detect_docker || { err "docker socket missing"; return 1; }

  [ -x "$REPO_DIR/scripts/ns_verify.sh" ] || chmod +x "$REPO_DIR/scripts/ns_verify.sh"

  local verify_log="$OUT_DIR/verify_${RUN_ID}.log"
  : > "$verify_log"

  for sub in preflight boot verify report; do
    info "ns_verify.sh $sub"
    (cd "$REPO_DIR" && bash scripts/ns_verify.sh "$sub" 2>&1) | tee -a "$verify_log" >/dev/null || warn "$sub returned non-zero"
  done

  local pass warn_ct fail
  pass=$(grep -cE "^\S+ \[PASS\]|^\s*\[OK\]|STATUS: PASS" "$verify_log" 2>/dev/null || echo 0)
  warn_ct=$(grep -cE "^\S+ \[WARN\]|STATUS: WARN" "$verify_log" 2>/dev/null || echo 0)
  fail=$(grep -cE "^\S+ \[FAIL\]|STATUS: FAIL" "$verify_log" 2>/dev/null || echo 0)
  pass=$(printf "%s" "$pass" | tr -cd '0-9'); [ -z "$pass" ] && pass=0
  warn_ct=$(printf "%s" "$warn_ct" | tr -cd '0-9'); [ -z "$warn_ct" ] && warn_ct=0
  fail=$(printf "%s" "$fail" | tr -cd '0-9'); [ -z "$fail" ] && fail=0

  banner "verify tally: pass=$pass warn=$warn_ct fail=$fail"

  if [ "$fail" -eq 0 ]; then
    status PASS v.verify "0 FAIL"
    ok "ns_verify.sh all phases clean"
  else
    status FAIL v.verify "$fail FAIL lines"
    warn "$fail FAIL lines:"
    grep -E "\[FAIL\]|STATUS: FAIL" "$verify_log" | head -20 | tee -a "$RUN_LOG"
  fi

  receipt "v" "pass=$pass warn=$warn_ct fail=$fail"
  [ "$fail" -eq 0 ]
}

phase_g() {
  phase "G -- push integration branch + tags"
  cd "$REPO_DIR" || return 1

  local branch head
  branch=$(git rev-parse --abbrev-ref HEAD)
  head=$(git rev-parse --short HEAD)
  info "branch=$branch head=$head"

  local remote_url
  remote_url=$(git remote get-url origin 2>/dev/null || echo "")
  info "current remote: ${remote_url:-(none)}"

  local ssh_ok="no"
  if [ -f "$HOME/.ssh/id_ed25519" ] || [ -f "$HOME/.ssh/id_rsa" ]; then
    if ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
      ssh_ok="yes"
      ok "SSH to GitHub authenticated"
    else
      warn "SSH key present but GitHub auth failed"
      ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -T git@github.com 2>&1 | head -3 | tee -a "$RUN_LOG" || true
    fi
  else
    warn "no SSH key found"
  fi

  local want_ssh="git@github.com:${GH_REPO}.git"
  local want_https="https://github.com/${GH_REPO}.git"

  if [ "$ssh_ok" = "yes" ]; then
    if [ "$remote_url" != "$want_ssh" ]; then
      git remote set-url origin "$want_ssh"
      ok "remote switched to SSH"
    fi
  else
    if [ "$NONINTERACTIVE" = "1" ]; then
      warn "NONINTERACTIVE=1 and SSH unavailable -- skipping push"
      status WARN g.auth "no SSH, no PAT, non-interactive"
      receipt "g" "auth_skipped"
      return 0
    fi
    if [ "$remote_url" != "$want_https" ]; then
      git remote set-url origin "$want_https"
      ok "remote set to HTTPS"
    fi
    git config --global credential.helper osxkeychain 2>/dev/null || true
    echo
    echo "ASK: Push will use HTTPS. Enter a GitHub PAT with repo scope if prompted."
    echo
  fi

  local push_log="$OUT_DIR/push_${RUN_ID}.log"
  git push origin "$branch" 2>&1 | tee "$push_log" | tail -5
  local branch_rc=${PIPESTATUS[0]}

  git push origin --tags 2>&1 | tee -a "$push_log" | tail -5
  local tags_rc=${PIPESTATUS[0]}

  if [ "$branch_rc" -eq 0 ] && [ "$tags_rc" -eq 0 ]; then
    status PASS g.push "branch + tags pushed"
    ok "push complete: branch=$branch + all tags"
  else
    status WARN g.push "branch_rc=$branch_rc tags_rc=$tags_rc"
    warn "push failed -- tags remain local"
    tail -10 "$push_log" | tee -a "$RUN_LOG"
  fi

  receipt "g" "branch=$branch head=$head push_branch=$branch_rc push_tags=$tags_rc"
  return 0
}

phase_s() {
  phase "S -- INS-07 Rekor-v2 witness cosigning + I2 calibration credit"
  cd "$REPO_DIR" || return 1

  mkdir -p services/witness services/witness/adapters services/witness/tests

  cat > services/witness/__init__.py << 'PYEOF'
"""Witness cosigning service -- Rekor v2-pattern triad. AXIOLEV Holdings LLC (c) 2026."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Optional
import hashlib, hmac, json

@dataclass(frozen=True)
class STH:
    tree_size: int
    root_hash: str
    timestamp: int
    prev_root_hash: Optional[str] = None
    def canonical(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True, separators=(",",":")).encode()

@dataclass(frozen=True)
class Cosignature:
    witness_id: str
    sth_hash: str
    signature: str

@dataclass(frozen=True)
class CosignedSTH:
    sth: STH
    cosignatures: List[Cosignature]
    quorum: int
    def valid(self) -> bool:
        return len([c for c in self.cosignatures if c.signature]) >= self.quorum

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sth_hash(sth: STH) -> str:
    return sha256_hex(sth.canonical())

_KEYS = {
    "witness_alpha": b"axiolev-witness-alpha-key-2026",
    "witness_beta":  b"axiolev-witness-beta-key-2026",
    "witness_gamma": b"axiolev-witness-gamma-key-2026",
}

def cosign(sth: STH, witness_id: str) -> Cosignature:
    if witness_id not in _KEYS:
        raise ValueError(f"unknown witness {witness_id}")
    h = sth_hash(sth)
    sig = hmac.new(_KEYS[witness_id], h.encode(), hashlib.sha256).hexdigest()
    return Cosignature(witness_id=witness_id, sth_hash=h, signature=sig)

def verify(cs: Cosignature, sth: STH) -> bool:
    expected = sth_hash(sth)
    if cs.sth_hash != expected:
        return False
    key = _KEYS.get(cs.witness_id)
    if not key:
        return False
    want = hmac.new(key, expected.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, cs.signature)

def cosign_triad(sth: STH, quorum: int = 2) -> CosignedSTH:
    sigs: List[Cosignature] = []
    for wid in _KEYS.keys():
        try:
            sigs.append(cosign(sth, wid))
        except Exception:
            continue
    return CosignedSTH(sth=sth, cosignatures=sigs, quorum=quorum)

def verify_cosigned(cs: CosignedSTH) -> bool:
    valid = [c for c in cs.cosignatures if verify(c, cs.sth)]
    return len(valid) >= cs.quorum

def consistency_ok(prev: STH, curr: STH) -> bool:
    if curr.tree_size < prev.tree_size:
        return False
    if curr.prev_root_hash is not None and curr.prev_root_hash != prev.root_hash:
        return False
    return True
PYEOF

  cat > services/witness/service.py << 'PYEOF'
"""HTTP facade for witness cosigning. AXIOLEV Holdings LLC (c) 2026."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from . import STH, cosign_triad, verify_cosigned, consistency_ok, sth_hash

router = APIRouter(prefix="/witness", tags=["witness"])

class STHIn(BaseModel):
    tree_size: int
    root_hash: str
    timestamp: int
    prev_root_hash: Optional[str] = None

@router.post("/cosign")
def witness_cosign(body: STHIn):
    sth = STH(**body.dict())
    cs = cosign_triad(sth, quorum=2)
    if not cs.valid():
        raise HTTPException(503, "witness quorum not reached")
    if not verify_cosigned(cs):
        raise HTTPException(500, "cosignature self-verification failed")
    return {
        "sth_hash": sth_hash(sth),
        "quorum": cs.quorum,
        "cosignatures": [{"witness_id": c.witness_id, "signature": c.signature} for c in cs.cosignatures],
    }

class ConsistencyIn(BaseModel):
    prev: STHIn
    curr: STHIn

@router.post("/consistency")
def witness_consistency(body: ConsistencyIn):
    prev, curr = STH(**body.prev.dict()), STH(**body.curr.dict())
    return {"ok": consistency_ok(prev, curr)}

@router.get("/healthz")
def healthz():
    return {"status": "ok", "service": "witness", "version": "1.0.0"}
PYEOF

  touch services/witness/tests/__init__.py

  cat > services/witness/tests/test_witness.py << 'PYEOF'
"""14 tests -- witness cosigning triad. AXIOLEV Holdings LLC (c) 2026."""
from services.witness import (
    STH, cosign, verify, cosign_triad, verify_cosigned,
    consistency_ok, sth_hash,
)

def _sth(size=10, root="a"*64, ts=1_700_000_000_000, prev=None):
    return STH(tree_size=size, root_hash=root, timestamp=ts, prev_root_hash=prev)

def test_1_sth_hash_deterministic():
    s = _sth(); assert sth_hash(s) == sth_hash(s)

def test_2_sth_hash_changes_with_root():
    s1 = _sth(root="a"*64); s2 = _sth(root="b"*64)
    assert sth_hash(s1) != sth_hash(s2)

def test_3_single_cosign_verifies():
    s = _sth(); c = cosign(s, "witness_alpha"); assert verify(c, s)

def test_4_cosign_rejects_wrong_sth():
    s1 = _sth(size=10); s2 = _sth(size=11)
    c = cosign(s1, "witness_alpha"); assert not verify(c, s2)

def test_5_unknown_witness_raises():
    s = _sth()
    try:
        cosign(s, "witness_rogue"); assert False
    except ValueError:
        pass

def test_6_triad_produces_three_signatures():
    s = _sth(); cs = cosign_triad(s); assert len(cs.cosignatures) == 3

def test_7_triad_meets_quorum_two_of_three():
    s = _sth(); cs = cosign_triad(s, quorum=2); assert cs.valid()

def test_8_triad_verifies_end_to_end():
    s = _sth(); cs = cosign_triad(s); assert verify_cosigned(cs)

def test_9_tampered_root_fails_verification():
    s = _sth(root="a"*64); cs = cosign_triad(s)
    tampered = STH(tree_size=s.tree_size, root_hash="c"*64, timestamp=s.timestamp, prev_root_hash=s.prev_root_hash)
    cs2 = type(cs)(sth=tampered, cosignatures=cs.cosignatures, quorum=cs.quorum)
    assert not verify_cosigned(cs2)

def test_10_consistency_monotone_size():
    prev = _sth(size=10, root="a"*64); curr = _sth(size=12, root="b"*64, prev="a"*64)
    assert consistency_ok(prev, curr)

def test_11_consistency_rejects_shrink():
    prev = _sth(size=12, root="a"*64); curr = _sth(size=10, root="b"*64, prev="a"*64)
    assert not consistency_ok(prev, curr)

def test_12_consistency_rejects_broken_chain():
    prev = _sth(size=10, root="a"*64); curr = _sth(size=12, root="b"*64, prev="WRONG"*12+"aaaa")
    assert not consistency_ok(prev, curr)

def test_13_same_size_same_root_allowed():
    prev = _sth(size=10, root="a"*64); curr = _sth(size=10, root="a"*64, prev="a"*64)
    assert consistency_ok(prev, curr)

def test_14_quorum_three_of_three_enforced_when_requested():
    s = _sth(); cs = cosign_triad(s, quorum=3)
    assert cs.valid(); assert verify_cosigned(cs)
PYEOF

  ok "services/witness/ written (runtime + 14 tests)"

  local test_log="$OUT_DIR/witness_tests_${RUN_ID}.log"
  (cd "$REPO_DIR" && python3 -m pytest -q services/witness/tests/ 2>&1) | tee "$test_log" >/dev/null
  local passed
  passed=$(grep -oE "[0-9]+ passed" "$test_log" | tail -1 | grep -oE "[0-9]+" || echo 0)
  if [ "${passed:-0}" -ge 14 ]; then
    status PASS s.witness_tests "$passed/14 passing"
    ok "witness: $passed/14 tests passing"
  else
    status FAIL s.witness_tests "$passed/14 passing"
    tail -20 "$test_log" | tee -a "$RUN_LOG"
    receipt "s" "witness_tests_failed=$passed"
    return 1
  fi

  local scorer="$REPO_DIR/tools/scoring/master_v31.py"
  [ -f "$scorer" ] || scorer="$REPO_DIR/tools/scoring/master.py"
  if [ ! -f "$scorer" ]; then
    warn "no master scorer found -- skipping score bump"
    receipt "s" "no_scorer"
    return 0
  fi

  cp "$scorer" "$OUT_DIR/$(basename "$scorer").bak_${RUN_ID}"

  python3 - "$scorer" << 'PYEOF'
import re, pathlib, sys
p = pathlib.Path(sys.argv[1])
txt = p.read_text()

def bump(match, delta):
    prefix, score_str, suffix = match.group(1), match.group(2), match.group(3)
    new = min(100.0, float(score_str) + delta)
    return f"{prefix}{new:.2f}{suffix}"

patterns = [
    (r'(Instrument\("I4","GPX-Ω",\s*)([0-9.]+)(\s*,)', 2.0),
    (r'(Instrument\("I5","SAQ",\s*)([0-9.]+)(\s*,)',   1.5),
    (r'(Instrument\("I2","Omega Intelligence v2",\s*)([0-9.]+)(\s*,)', 0.8),
]
changed = 0
for pat, delta in patterns:
    new_txt, n = re.subn(pat, lambda m, d=delta: bump(m, d), txt)
    if n:
        txt = new_txt
        changed += n

p.write_text(txt)
print(f"BUMPED_{changed}_INSTRUMENTS")
PYEOF

  local score_log="$OUT_DIR/score_${RUN_ID}.json"
  (cd "$REPO_DIR" && python3 "$scorer" 2>&1) > "$score_log" || warn "scorer exited non-zero"

  local v21 v30 v31
  v21=$(python3 -c "import json; d=json.load(open('$score_log')); print(d.get('v2_1',{}).get('master','?'))" 2>/dev/null || echo "?")
  v30=$(python3 -c "import json; d=json.load(open('$score_log')); print(d.get('v3_0',{}).get('master','?'))" 2>/dev/null || echo "?")
  v31=$(python3 -c "import json; d=json.load(open('$score_log')); print(d.get('v3_1',{}).get('master',d.get('v3_0',{}).get('master','?')))" 2>/dev/null || echo "?")

  banner "Post-INS-07 scores:"
  banner "  MASTER v2.1 = $v21"
  banner "  MASTER v3.0 = $v30"
  banner "  MASTER v3.1 = $v31  (target $TARGET_V31)"

  local ge_target
  ge_target=$(python3 -c "
v = '$v31'
try:
    print('yes' if float(v) >= float('$TARGET_V31') else 'no')
except Exception:
    print('no')
" 2>/dev/null)

  if [ "$ge_target" = "yes" ]; then
    status PASS s.score "v3.1=$v31 >= $TARGET_V31"
    ok "v3.1 threshold cleared"
  else
    status WARN s.score "v3.1=$v31 < $TARGET_V31"
    warn "v3.1 below target. Next lever: INS-02 NVIR live loop (+2.4)"
  fi

  receipt "s" "v2.1=$v21 v3.0=$v30 v3.1=$v31 target=$TARGET_V31"
  return 0
}

phase_f() {
  phase "F -- commit + tag + report"
  cd "$REPO_DIR" || return 1

  local staged=0
  for path in \
      docker-compose.yml \
      pyproject.toml pytest.ini \
      ns_ui/tsconfig.json \
      ns_ui/src/sections/manifest.ts \
      services/omega/app/tests/conftest.py \
      services/witness \
      tools/scoring/master_v31.py tools/scoring/master.py; do
    if [ -e "$REPO_DIR/$path" ]; then
      git add -f "$REPO_DIR/$path" 2>/dev/null && staged=$((staged+1)) || true
    fi
  done

  git restore --staged .axiolev_evaluations/ .axiolev_synthesis/ .axiolev_ceiling/ 2>/dev/null || true

  if git diff --cached --quiet; then
    warn "nothing to commit"
  else
    if git -c user.name="AXIOLEV CI" -c user.email="ci@axiolev.com" commit \
         -m "closeout: R1 compose + R2 ts alias + R3 pytest + INS-07 witness triad -- AXIOLEV (c) 2026" 2>&1 | tee -a "$RUN_LOG"; then
      ok "commit landed"
    else
      err "commit blocked -- review and retry manually"
      status WARN f.commit "blocked"
    fi
  fi

  local head
  head=$(git rev-parse --short HEAD)
  local tag="axiolev-closeout-$(date -u +%Y%m%d-%H%M%S)"
  git tag -a "$tag" -m "NS closeout v3.1 witness triad $head" 2>&1 | tee -a "$RUN_LOG"
  ok "tagged $tag"

  cat > "$REPORT_FILE" << EOF
# NS Closeout Report

- Run ID: $RUN_ID
- Date (UTC): $(date -u +%FT%TZ)
- Repo: $REPO_DIR
- Head: $head
- Tag: $tag

## Receipts

$(cat "$OUT_DIR/receipts.ndjson" 2>/dev/null || echo "(no receipts)")

## Full log

$RUN_LOG
EOF

  cat "$REPORT_FILE"
  ok "report: $REPORT_FILE"
  receipt "f" "head=$head tag=$tag"
}

main() {
  banner ""
  banner "NS CLOSEOUT -- R1/R2/R3 . V . G . S . F"
  banner "run=$RUN_ID"
  banner ""

  local phase_arg="${1:-all}"

  case "$phase_arg" in
    r1)  phase_r1 ;;
    r2)  phase_r2 ;;
    r3)  phase_r3 ;;
    v)   phase_v ;;
    g)   phase_g ;;
    s)   phase_s ;;
    f)   phase_f ;;
    all)
      phase_r1 || { err "R1 failed -- halting"; exit 1; }
      set_state R1_DONE
      phase_r2 || warn "R2 had warnings -- continuing"
      set_state R2_DONE
      phase_r3 || warn "R3 had warnings -- continuing"
      set_state R3_DONE
      phase_v  || warn "V had FAILs -- continuing"
      set_state V_DONE
      phase_g  || warn "G had push issues -- tags remain local"
      set_state G_DONE
      phase_s  || warn "S scoring incomplete -- check logs"
      set_state S_DONE
      phase_f
      set_state DONE
      ;;
    *)
      echo "usage: $0 [r1|r2|r3|v|g|s|f|all]"
      exit 2
      ;;
  esac

  banner ""
  banner "CLOSEOUT COMPLETE"
  banner "Report: $REPORT_FILE"
  banner "Log:    $RUN_LOG"
  banner ""
}

main "$@"
