from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts" / "stabilization" / "r0_execution_safety.py"


def test_r0_execution_safety_guard_passes() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert report["check"] == "R0.4_EXECUTION_SAFETY"
    assert report["status"] == "PASS"
    assert report["failures"] == []
