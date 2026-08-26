#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_PID=""
WEB_PID=""
BACKEND_LOG=/tmp/ultrarentable-r0-backend.log
WEB_LOG=/tmp/ultrarentable-r0-web.log

cleanup() {
  set +e
  [[ -n "${WEB_PID}" ]] && kill "${WEB_PID}" 2>/dev/null || true
  [[ -n "${BACKEND_PID}" ]] && kill "${BACKEND_PID}" 2>/dev/null || true
  [[ -n "${WEB_PID}" ]] && wait "${WEB_PID}" 2>/dev/null || true
  [[ -n "${BACKEND_PID}" ]] && wait "${BACKEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

fail_with_log() {
  local component="$1"
  local log_file="$2"
  local pid="${3:-}"
  echo "R0.6_WEB_E2E_BLOCKED component=${component} pid=${pid:-none}" >&2
  if [[ -f "$log_file" ]]; then
    echo "----- ${component} log: ${log_file} -----" >&2
    cat "$log_file" >&2 || true
    echo "----- end ${component} log -----" >&2
  else
    echo "No ${component} log file was created: ${log_file}" >&2
  fi
  exit 1
}

cd "$ROOT"

export ULTRARENTABLE_AUTONOMOUS_RUNTIME=false
export GIT_COMMIT="${GITHUB_SHA:-LOCAL}"
export PYTHONUNBUFFERED=1

# Backend: real FastAPI app in deterministic local mode; no worker fleet.
: > "$BACKEND_LOG"
.venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8000/api/v1/version >/tmp/ultrarentable-backend-version.json; then
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    fail_with_log "backend" "$BACKEND_LOG" "$BACKEND_PID"
  fi
  sleep 1
done

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  fail_with_log "backend" "$BACKEND_LOG" "$BACKEND_PID"
fi
curl -fsS http://127.0.0.1:8000/api/v1/version >/tmp/ultrarentable-backend-version.json || fail_with_log "backend" "$BACKEND_LOG" "$BACKEND_PID"

cd "$ROOT/apps/web"
npm run typecheck
npm run build

# Web: production server against the same real backend process.
: > "$WEB_LOG"
PORT=3000 npm run start >"$WEB_LOG" 2>&1 &
WEB_PID=$!

for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:3000/ >/tmp/ultrarentable-web-root.html; then
    break
  fi
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    fail_with_log "web" "$WEB_LOG" "$WEB_PID"
  fi
  sleep 1
done

if ! kill -0 "$WEB_PID" 2>/dev/null; then
  fail_with_log "web" "$WEB_LOG" "$WEB_PID"
fi
curl -fsS http://127.0.0.1:3000/ >/tmp/ultrarentable-web-root.html || fail_with_log "web" "$WEB_LOG" "$WEB_PID"
curl -fsS http://127.0.0.1:3000/api/v1/version >/tmp/ultrarentable-web-version.json || fail_with_log "web" "$WEB_LOG" "$WEB_PID"

cd "$ROOT"
.venv/bin/python - <<'PY'
import json
from pathlib import Path

backend = json.loads(Path('/tmp/ultrarentable-backend-version.json').read_text())
proxied = json.loads(Path('/tmp/ultrarentable-web-version.json').read_text())
assert backend['runtime_mode'] == 'LOCAL_API_ONLY', backend
assert backend['autonomous_runtime_enabled'] is False, backend
assert proxied['api_version'] == backend['api_version'], (backend, proxied)
assert proxied['engine_version'] == backend['engine_version'], (backend, proxied)
print(json.dumps({
    'check': 'R0.6_WEB_E2E',
    'status': 'PASS',
    'backend_runtime_mode': backend['runtime_mode'],
    'proxied_api_version': proxied['api_version'],
    'proxied_engine_version': proxied['engine_version'],
}, indent=2))
PY
