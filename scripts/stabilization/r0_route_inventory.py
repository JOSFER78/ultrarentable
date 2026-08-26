#!/usr/bin/env python3
"""Fail-closed FastAPI route inventory for R0.2.

Audits the effective imported FastAPI application after dependency installation,
then reports duplicate (HTTP method, path) operations. This catches conflicts
that a source-only ``include_router`` audit can miss.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("ULTRARENTABLE_AUTONOMOUS_RUNTIME", "false")


def route_methods(route: object) -> list[str]:
    methods = getattr(route, "methods", None) or []
    return sorted(str(method).upper() for method in methods if str(method).upper() != "HEAD")


def main() -> int:
    from services.api.app.main import app

    operations: list[dict[str, object]] = []
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)

    for route in app.routes:
        path = getattr(route, "path", None)
        if not isinstance(path, str) or not path.startswith("/api/"):
            continue
        for method in route_methods(route):
            item = {
                "method": method,
                "path": path,
                "name": getattr(route, "name", None),
                "module": getattr(getattr(route, "endpoint", None), "__module__", None),
            }
            operations.append(item)
            grouped[(method, path)].append(item)

    duplicates = [
        {"method": method, "path": path, "registrations": entries}
        for (method, path), entries in sorted(grouped.items())
        if len(entries) > 1
    ]

    result = {
        "check": "R0.2_ROUTE_INVENTORY",
        "status": "PASS" if not duplicates else "BLOCKED",
        "source": "services.api.app.main.app",
        "operation_count": len(operations),
        "duplicate_operation_count": len(duplicates),
        "duplicate_operations": duplicates,
        "operations": sorted(operations, key=lambda item: (str(item["path"]), str(item["method"]))),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not duplicates else 1


if __name__ == "__main__":
    raise SystemExit(main())
