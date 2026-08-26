from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts/stabilization/r0_final_certification.py"


def test_r0_final_certification_refuses_unproven_green() -> None:
    env = os.environ.copy()
    env.pop("R0_CI_GREEN", None)
    completed = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert report["check"] == "R0.10_FINAL_CERTIFICATION"
    assert report["status"] == "R0_REWORK"
    assert report["ci_green_evidence_supplied"] is False
    assert "CI_GREEN_EVIDENCE_REQUIRED" in report["evidence_failures"]
