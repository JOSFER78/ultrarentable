from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "stabilization" / "r0_web_e2e.sh"


def test_r0_web_e2e_script_is_fail_closed() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    required = [
        "ULTRARENTABLE_AUTONOMOUS_RUNTIME=false",
        "uvicorn services.api.app.main:app",
        "curl -fsS http://127.0.0.1:8000/api/v1/version",
        "npm run typecheck",
        "npm run build",
        "npm run start",
        "curl -fsS http://127.0.0.1:3000/api/v1/version",
        "runtime_mode' == 'LOCAL_API_ONLY'",
        "autonomous_runtime_enabled' is False",
    ]
    for marker in required:
        assert marker in text, marker
