#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID=""
LOG=/tmp/ultrarentable-r0-backend-clean-start.log
cleanup() {
  set +e
  [[ -n "${PID}" ]] && kill "${PID}" 2>/dev/null || true
  wait "${PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$ROOT"
export ULTRARENTABLE_AUTONOMOUS_RUNTIME=false
export GIT_COMMIT="${GITHUB_SHA:-LOCAL}"
export PYTHONUNBUFFERED=1

.venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8001 >"$LOG" 2>&1 &
PID=$!

for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8001/ >/tmp/ultrarentable-r0-root.json; then
    break
  fi
  sleep 1
done

curl -fsS http://127.0.0.1:8001/ >/tmp/ultrarentable-r0-root.json
curl -fsS http://127.0.0.1:8001/api/v1/version >/tmp/ultrarentable-r0-version.json

.venv/bin/python - <<'PY'
import json
from pathlib import Path

root = json.loads(Path('/tmp/ultrarentable-r0-root.json').read_text())
version = json.loads(Path('/tmp/ultrarentable-r0-version.json').read_text())
assert root['status'] == 'RUNNING', root
assert root['runtime_mode'] == 'LOCAL_API_ONLY', root
assert root['autonomous_runtime_enabled'] is False, root
assert version['runtime_mode'] == 'LOCAL_API_ONLY', version
assert version['autonomous_runtime_enabled'] is False, version
assert version['engine_version'], version
print(json.dumps({
    'check': 'R0.7_BACKEND_CLEAN_START',
    'status': 'PASS',
    'runtime_mode': version['runtime_mode'],
    'autonomous_runtime_enabled': version['autonomous_runtime_enabled'],
    'api_version': version['api_version'],
    'engine_version': version['engine_version'],
}, indent=2))
PY
