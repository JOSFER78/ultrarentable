from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts" / "stabilization" / "r0_dependency_authority.py"


def test_r0_dependency_authority_passes() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout)
    assert report["check"] == "R0.1_DEPENDENCY_AUTHORITY"
    assert report["status"] == "PASS"
    assert report["failures"] == []
