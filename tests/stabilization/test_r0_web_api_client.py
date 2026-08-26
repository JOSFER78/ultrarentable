from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts" / "stabilization" / "r0_web_api_client.py"


def test_r0_web_api_client_surface_is_canonical() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert report["check"] == "R0.5_WEB_API_CLIENT_SURFACE"
    assert report["status"] == "PASS"
    assert report["failures"] == []
