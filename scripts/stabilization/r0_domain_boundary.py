#!/usr/bin/env python3
"""Fail-closed authority graph for R0.9."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "services" / "api" / "app" / "main.py"
LEGACY = ROOT / "services" / "api" / "app" / "api" / "routes.py"
COMPAT = ROOT / "services" / "api" / "app" / "api" / "legacy_compat_router.py"

ROUTER_CLASSIFICATIONS = {
    "sqx_router": "CANONICAL", "strategy_lab_router": "CANONICAL", "strategy_binding_router": "CANONICAL",
    "execution_router": "CANONICAL", "certified_summary_router": "CANONICAL", "real_data_router": "CANONICAL",
    "portfolio_router": "CANONICAL", "lineage_router": "CANONICAL", "policy_router": "CANONICAL",
    "research_lab_router": "CANONICAL", "telemetry_router": "CANONICAL", "job_queue_router": "CANONICAL",
    "forward_router": "CANONICAL", "validation_router": "CANONICAL", "legacy_routes": "LEGACY_ISOLATED",
    "audit_router": "SUPPORT", "candidates_router": "SUPPORT", "discovery_router": "RESEARCH_SURFACE",
    "firebase_sync_router": "INTEGRATION", "gates_router": "GOVERNANCE_SURFACE", "gateways_router": "INTEGRATION",
    "paper_router": "PAPER_EXECUTION_SURFACE", "providers_router": "EXECUTION_SUPPORT", "research_router": "RESEARCH_SURFACE",
    "semantic_router": "AI_SUPPORT", "system_health_router": "HEALTH_SURFACE", "ultra_router": "TRACK_SURFACE",
    "version_router": "GOVERNANCE_SURFACE",
}

def _router_names(tree: ast.AST) -> set[str]:
    return {
        node.args[0].id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "include_router" and node.args and isinstance(node.args[0], ast.Name)
    }

def main() -> int:
    main_source = MAIN.read_text(encoding="utf-8")
    mounted = sorted(_router_names(ast.parse(main_source, filename=str(MAIN))))
    nested_legacy = sorted(_router_names(ast.parse(LEGACY.read_text(encoding="utf-8"), filename=str(LEGACY))))
    failures: list[str] = []
    findings: list[dict[str, object]] = []
    for router in mounted:
        classification = ROUTER_CLASSIFICATIONS.get(router, "REVIEW_REQUIRED")
        if classification == "REVIEW_REQUIRED":
            failures.append(f"unclassified mounted router: {router}")
        findings.append({"type": "MOUNTED_ROUTER", "router": router, "classification": classification})
    canonical_nested = sorted(set(nested_legacy) & {"sqx_router"})
    compat_boundary_active = (
        COMPAT.exists()
        and "from services.api.app.api.legacy_compat_router import router as legacy_routes" in main_source
        and "_isolated_nested_canonical" in COMPAT.read_text(encoding="utf-8")
    )
    if canonical_nested and compat_boundary_active:
        findings.append({"type": "LEGACY_ISOLATION", "module": "services.api.app.api.routes", "nested_canonical_routers": canonical_nested, "classification": "LEGACY_ISOLATED", "boundary": "legacy_compat_router"})
    elif canonical_nested:
        failures.append("legacy routes.py nests canonical router(s): " + ", ".join(canonical_nested))
    result = {"check": "R0.9_CANONICAL_DOMAIN_BOUNDARY", "status": "PASS" if not failures else "BLOCKED", "authority_graph": {"UI": ["API"], "API": ["domain/evidence", "execution", "data"], "domain/evidence": ["execution", "data"], "execution": ["data"], "data": []}, "mounted_routers": mounted, "nested_legacy_routers": nested_legacy, "findings": findings, "failures": failures, "required_classifications": sorted(set(ROUTER_CLASSIFICATIONS.values()) | {"TEST_FIXTURE", "REMOVE"})}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
