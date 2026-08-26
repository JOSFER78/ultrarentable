#!/usr/bin/env python3
"""Fail-closed static execution-safety guard for R0.4."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "services" / "api" / "app" / "api" / "execution_router.py"


def function_name(node: ast.AST) -> str:
    return getattr(node, "name", "")


def is_empty_positions_assignment(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign) or not node.targets:
        return False
    target = node.targets[0]
    return (
        isinstance(target, ast.Attribute)
        and target.attr == "open_positions_json"
        and isinstance(node.value, ast.Constant)
        and node.value.value == "[]"
    )


def has_call(fn: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
        for node in ast.walk(fn)
    )


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TARGET))
    failures: list[str] = []

    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    by_name = {function_name(fn): fn for fn in functions}

    for name in ("trigger_kill_switch", "flatten_session_positions"):
        fn = by_name.get(name)
        if fn and any(is_empty_positions_assignment(node) for node in ast.walk(fn)):
            failures.append(f"{name} may not clear local positions before provider reconciliation")

    create = by_name.get("create_session")
    if create is None:
        failures.append("create_session function missing")
    elif not has_call(create, "_candidate_has_execution_evidence"):
        failures.append("create_session must enforce candidate execution evidence")

    if "PROVIDER_DISABLED" not in source:
        failures.append("create_session must reject disabled providers")
    if "provider.is_enabled is not True" not in source:
        failures.append("provider enablement must be checked explicitly")
    if source.count('"execution_confirmed": False') < 2:
        failures.append("execution API must not claim external confirmation from local session status")

    result = {
        "check": "R0.4_EXECUTION_SAFETY",
        "status": "PASS" if not failures else "BLOCKED",
        "source": str(TARGET.relative_to(ROOT)),
        "failures": failures,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
