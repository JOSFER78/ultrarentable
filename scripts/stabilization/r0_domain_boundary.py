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

CANONICAL_ROUTERS = {
    "sqx_router": "CANONICAL",
    "strategy_lab_router": "CANONICAL",
    "strategy_binding_router": "CANONICAL",
    "execution_router": "CANONICAL",
    "certified_summary_router": "CANONICAL",
    "real_data_router": "CANONICAL",
    "portfolio_router": "CANONICAL",
    "lineage_router": "CANONICAL",
    "policy_router": "CANONICAL",
    "research_lab_router": "CANONICAL",
    "telemetry_router": "CANONICAL",
    "job_queue_router": "CANONICAL",
    "forward_router": "CANONICAL",
    "validation_router": "CANONICAL",
}

LEGACY_MODULES = {"legacy_routes": "LEGACY_ISOLATED"}


def _router_names(tree: ast.AST) -> set[str]:
    return {
        node.args[0].id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "include_router"
        and node.args
        and isinstance(node.args[0], ast.Name)
    }


def main() -> int:
    main_source = MAIN.read_text(encoding="utf-8")
    main_tree = ast.parse(main_source, filename=str(MAIN))
    legacy_tree = ast.parse(LEGACY.read_text(encoding="utf-8"), filename=str(LEGACY))

    mounted = sorted(_router_names(main_tree))
    nested_legacy = sorted(_router_names(legacy_tree))
    findings: list[dict[str, object]] = []
    failures: list[str] = []

    classifications: dict[str, str] = {}
    for router in mounted:
        classifications[router] = CANONICAL_ROUTERS.get(router, LEGACY_MODULES.get(router, "REVIEW_REQUIRED"))
        if classifications[router] == "REVIEW_REQUIRED":
            failures.append(f"unclassified mounted router: {router}")

    canonical_nested = sorted(set(nested_legacy) & set(CANONICAL_ROUTERS))
    compat_boundary_active = (
        COMPAT.exists()
        and "from services.api.app.api.legacy_compat_router import router as legacy_routes" in main_source
        and "_isolated_nested_canonical" in COMPAT.read_text(encoding="utf-8")
    )

    if canonical_nested and not compat_boundary_active:
        failures.append("legacy routes.py nests canonical router(s): " + ", ".join(canonical_nested))
        findings.append({
            "type": "LEGACY_BYPASS",
            "module": "services.api.app.api.routes",
            "nested_canonical_routers": canonical_nested,
            "classification": "REMOVE_OR_ISOLATE",
        })
    elif canonical_nested:
        findings.append({
            "type": "LEGACY_ISOLATION",
            "module": "services.api.app.api.routes",
            "nested_canonical_routers": canonical_nested,
            "classification": "LEGACY_ISOLATED",
            "boundary": "legacy_compat_router",
        })

    findings.extend(
        {"type": "MOUNTED_ROUTER", "router": router, "classification": classifications[router]}
        for router in mounted
    )

    graph = {
        "UI": ["API"],
        "API": ["domain/evidence", "execution", "data"],
        "domain/evidence": ["execution", "data"],
        "execution": ["data"],
        "data": [],
    }

    result = {
        "check": "R0.9_CANONICAL_DOMAIN_BOUNDARY",
        "status": "PASS" if not failures else "BLOCKED",
        "authority_graph": graph,
        "mounted_routers": mounted,
        "nested_legacy_routers": nested_legacy,
        "findings": findings,
        "failures": failures,
        "required_classifications": ["CANONICAL", "LEGACY_ISOLATED", "TEST_FIXTURE", "REMOVE"],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
