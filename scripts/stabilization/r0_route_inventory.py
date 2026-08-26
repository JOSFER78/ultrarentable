#!/usr/bin/env python3
"""Static FastAPI router-registration inventory for R0.2.

The check intentionally audits source registration rather than depending on a
running server. Repeated router registrations must be explicit and remain
limited to the documented V1/V2 or alias surfaces.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "services" / "api" / "app" / "main.py"

# Reuse across API generations is intentional when the same domain contract is
# exposed under a versioned prefix. The alias is explicit and separately tagged.
ALLOWED_REPEAT_REGISTRATIONS = {
    "portfolio_router": {"/api/v1/portfolio", "/api/v2/portfolio"},
    "lineage_router": {"/api/v1", "/api/v2"},
    "policy_router": {"/api/v1", "/api/v2"},
    "research_lab_router": {"/api/v1", "/api/v2"},
    "telemetry_router": {"/api/v1/telemetry", "/api/v2/telemetry"},
    "job_queue_router": {"/api/v1/jobs", "/api/v2"},
    "forward_router": {"/api/v1/forward", "/api/v2"},
    "certified_summary_router": {"/api/v1", "/api/v2"},
    "real_data_router": {"/api/v2", "/api/v2/real"},
}


def literal_prefix(node: ast.Call) -> str:
    for keyword in node.keywords:
        if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
    return ""


def router_symbol(node: ast.Call) -> str | None:
    if not node.args:
        return None
    target = node.args[0]
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def main() -> int:
    source = MAIN.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(MAIN))

    registrations: list[dict[str, object]] = []
    by_router: dict[str, list[str]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "include_router":
            continue
        symbol = router_symbol(node)
        if not symbol:
            continue
        prefix = literal_prefix(node)
        registrations.append({"router": symbol, "prefix": prefix, "line": node.lineno})
        by_router.setdefault(symbol, []).append(prefix)

    failures: list[str] = []
    for symbol, prefixes in sorted(by_router.items()):
        if len(prefixes) <= 1:
            continue
        expected = ALLOWED_REPEAT_REGISTRATIONS.get(symbol)
        actual = set(prefixes)
        if expected != actual:
            failures.append(
                f"router {symbol!r} has repeated registrations {sorted(actual)!r}; expected explicit allowlist {sorted(expected) if expected else None!r}"
            )

    result = {
        "check": "R0.2_ROUTE_INVENTORY",
        "status": "PASS" if not failures else "BLOCKED",
        "source": str(MAIN.relative_to(ROOT)),
        "registration_count": len(registrations),
        "registrations": registrations,
        "failures": failures,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
