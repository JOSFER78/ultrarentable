#!/usr/bin/env python3
"""Final R0 certification aggregator.

This command never upgrades a source-level pass into R0_STABLE by itself.
External CI evidence must be explicitly supplied as R0_CI_GREEN=1, and the
canonical domain-boundary audit must also be clean.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARDS = [
    ROOT / "scripts/stabilization/r0_dependency_authority.py",
    ROOT / "scripts/stabilization/r0_route_inventory.py",
    ROOT / "scripts/stabilization/r0_certification_evidence.py",
    ROOT / "scripts/stabilization/r0_execution_safety.py",
    ROOT / "scripts/stabilization/r0_web_api_client.py",
    ROOT / "scripts/stabilization/r0_forbidden_literal_scan.py",
    ROOT / "scripts/stabilization/r0_domain_boundary.py",
]


def run_guard(path: Path) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"check": path.name, "status": "EXECUTION_ERROR", "returncode": completed.returncode, "stderr": completed.stderr}
    return report


def main() -> int:
    reports = [run_guard(path) for path in GUARDS if path.is_file()]
    missing = [str(path.relative_to(ROOT)) for path in GUARDS if not path.is_file()]
    blocked = [r for r in reports if r.get("status") != "PASS"]
    ci_green = os.getenv("R0_CI_GREEN", "").strip().lower() in {"1", "true", "yes"}

    evidence_failures: list[str] = []
    if missing:
        evidence_failures.append("MISSING_GUARD:" + ",".join(missing))
    if blocked:
        evidence_failures.append("BLOCKED_SOURCE_GUARD")
    if not ci_green:
        evidence_failures.append("CI_GREEN_EVIDENCE_REQUIRED")

    status = "R0_STABLE" if not evidence_failures else "R0_REWORK"
    result = {
        "check": "R0.10_FINAL_CERTIFICATION",
        "status": status,
        "guard_count": len(reports),
        "guards": reports,
        "ci_green_evidence_supplied": ci_green,
        "evidence_failures": evidence_failures,
        "rule": "R0_STABLE requires every guard PASS and explicit external CI green evidence",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if status == "R0_STABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
