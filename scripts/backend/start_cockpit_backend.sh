#!/usr/bin/env bash
set -e
ROOT="$HOME/axiolev_runtime"
cd "$ROOT"
LOGS=".run/backend_logs"
mkdir -p "$LOGS"

start() {
    local name=$1 module=$2 port=$3 probe=${4:-/healthz}
    if curl -fsS --max-time 1 "http://127.0.0.1:$port$probe" >/dev/null 2>&1; then
        echo "  $name :$port already running"
        return
    fi
    nohup python3 -m uvicorn "$module" --host 127.0.0.1 --port "$port" \
        > "$LOGS/$name.log" 2>&1 &
    echo "$!" > "$LOGS/$name.pid"
    sleep 0.7
    if curl -fsS --max-time 2 "http://127.0.0.1:$port$probe" >/dev/null 2>&1; then
        echo "  ✓ $name :$port up (pid $(cat "$LOGS/$name.pid"))"
    else
        echo "  ✗ $name :$port failed — see $LOGS/$name.log"
    fi
}

echo "Starting NS∞ cockpit backend..."
start dwm       services.stubs.dwm_realish:app       8013  /dwm/healthz
start aletheion services.stubs.aletheion_stub:app    9000  /healthz
start handrail  services.stubs.handrail_stub:app     8011  /healthz
start ris       services.reality_ingest.api:app      8014  /ris/healthz
echo "Done. Tail logs: tail -f $LOGS/*.log"
