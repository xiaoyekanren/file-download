#!/usr/bin/env bash
set -euo pipefail

export DOWNLOAD_FOLDER=/data/nas

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
PID_FILE="$LOG_DIR/web.pid"
TIMESTAMP="$(date +%Y%m%d)"
LOG_FILE="$LOG_DIR/web_$TIMESTAMP.log"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Ensure the log directory exists before starting the service
mkdir -p "$LOG_DIR"

if [[ -f "$PID_FILE" ]]; then
    existing_pid="$(cat "$PID_FILE")"
    if ps -p "$existing_pid" > /dev/null 2>&1; then
        echo "web.py appears to be running already (PID $existing_pid)."
        echo "Stop the running instance (kill $existing_pid) or remove $PID_FILE before starting a new one."
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

nohup "$PYTHON_BIN" "$ROOT_DIR/web.py" >> "$LOG_FILE" 2>&1 &
server_pid=$!

echo "$server_pid" > "$PID_FILE"

echo "web.py started in background (PID $server_pid)."
echo "Logs: $LOG_FILE"
echo "PID file: $PID_FILE"
