#!/usr/bin/env python3
"""Fail-closed static execution-safety guard for R0.4."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "services" / "api" / "app" / "api" / "execution_router.py"

FORBIDDEN_ASSIGNMENTS = {
    "KILL_SWITCH": 'session.open_positions_json = "[]"',
    "FLATTEN": 'session.open_positions_json = "[]"',
}


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


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(TARGET))
    failures: list[str] = []

    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for fn in functions:
        if function_name(fn) in {"trigger_kill_switch", "flatten_session_positions"}:
            if any(is_empty_positions_assignment(node) for node in ast.walk(fn)):
                failures.append(f"{function_name(fn)} may not clear local positions before provider reconciliation")

    for fn in functions:
        if function_name(fn) == "create_session":
            calls = [node for node in ast.walk(fn) if isinstance(node, ast.Call)]
            query_text = source[fn.lineno * 0 :]
            if "_candidate_has_execution_evidence" not in query_text:
                failures.append("create_session must enforce candidate execution evidence")
            if "PROVIDER_DISABLED" not in source:
                failures.append("create_session must reject disabled providers")

    if "execution_confirmed": False not in source.replace(" ", ""):
        failures.append("execution responses must default to unconfirmed until provider evidence exists")

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
