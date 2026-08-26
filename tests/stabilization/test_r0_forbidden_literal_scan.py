from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts/stabilization/r0_forbidden_literal_scan.py"


def test_r0_forbidden_literal_scan_is_clean() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert report["check"] == "R0.8_FORBIDDEN_LITERAL_SCAN"
    assert report["status"] == "PASS"
    assert report["hits"] == []
