from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts/stabilization/r0_domain_boundary.py"


def test_r0_domain_boundary_audit_is_explicit() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["check"] == "R0.9_CANONICAL_DOMAIN_BOUNDARY"
    # Current repository intentionally remains blocked here until routes.py is
    # isolated from its nested SQX canonical router.
    assert "legacy routes.py nests canonical router(s): sqx_router" in report["failures"]
    assert report["status"] == "BLOCKED"
