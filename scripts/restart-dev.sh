#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
RUN_DIR="$ROOT_DIR/.run"

mkdir -p "$RUN_DIR"
cd "$ROOT_DIR"

stop_pid_file() {
  local name="$1"
  local pid_file="$RUN_DIR/$name.pid"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file" || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $name pid=$pid"
      kill "$pid" 2>/dev/null || true
      sleep 1
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$pid_file"
  fi
}

stop_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti "tcp:$port" 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Stopping processes on port $port: $pids"
    kill $pids 2>/dev/null || true
    sleep 1
    pids="$(lsof -ti "tcp:$port" 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

ensure_backend_env() {
  if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
    echo "Creating Python virtual environment"
    python3 -m venv "$ROOT_DIR/.venv"
  fi
  if ! "$ROOT_DIR/.venv/bin/python" -c "import fastapi, uvicorn, longbridge" >/dev/null 2>&1; then
    echo "Installing backend dependencies"
    "$ROOT_DIR/.venv/bin/python" -m pip install "$ROOT_DIR"
  fi
}

ensure_frontend_env() {
  if [[ ! -d "$ROOT_DIR/web/node_modules" ]]; then
    echo "Installing frontend dependencies"
    (cd "$ROOT_DIR/web" && npm install --cache /private/tmp/mini_smart_npm_cache)
  fi
}

start_backend() {
  echo "Starting backend on http://$BACKEND_HOST:$BACKEND_PORT"
  : > "$RUN_DIR/backend.log"
  "$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/scripts/spawn-detached.py" \
    --cwd "$ROOT_DIR" \
    --pid-file "$RUN_DIR/backend.pid" \
    --log-file "$RUN_DIR/backend.log" \
    -- "$ROOT_DIR/.venv/bin/python" -m uvicorn bankend.api:app \
      --host "$BACKEND_HOST" \
      --port "$BACKEND_PORT"
}

start_frontend() {
  echo "Starting frontend on http://$FRONTEND_HOST:$FRONTEND_PORT"
  : > "$RUN_DIR/frontend.log"
  "$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/scripts/spawn-detached.py" \
    --cwd "$ROOT_DIR/web" \
    --pid-file "$RUN_DIR/frontend.pid" \
    --log-file "$RUN_DIR/frontend.log" \
    -- npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local log_file="$3"
  for _ in {1..30}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name ready: $url"
      return 0
    fi
    sleep 1
  done
  echo "$name did not become ready. Last log lines:"
  tail -n 40 "$log_file" || true
  return 1
}

echo "Restarting mini_smart development services"
stop_pid_file "backend"
stop_pid_file "frontend"
stop_port "$BACKEND_PORT"
stop_port "$FRONTEND_PORT"
ensure_backend_env
ensure_frontend_env
start_backend
start_frontend
wait_for_url "Backend" "http://$BACKEND_HOST:$BACKEND_PORT/api/symbols" "$RUN_DIR/backend.log"
wait_for_url "Frontend" "http://$FRONTEND_HOST:$FRONTEND_PORT" "$RUN_DIR/frontend.log"

echo
echo "Done."
echo "Backend log:  $RUN_DIR/backend.log"
echo "Frontend log: $RUN_DIR/frontend.log"
