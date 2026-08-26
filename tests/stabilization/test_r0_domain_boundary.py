from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts/stabilization/r0_domain_boundary.py"


def test_r0_domain_boundary_is_passed_by_explicit_legacy_isolation() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["check"] == "R0.9_CANONICAL_DOMAIN_BOUNDARY"
    assert report["status"] == "PASS"
    assert report["failures"] == []
    findings = [f for f in report["findings"] if f["type"] == "LEGACY_ISOLATION"]
    assert findings
    assert findings[0]["classification"] == "LEGACY_ISOLATED"
