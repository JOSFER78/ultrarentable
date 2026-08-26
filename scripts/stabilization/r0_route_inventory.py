#!/usr/bin/env python3
"""Fail-closed FastAPI route inventory for R0.2.

Audits the effective OpenAPI surface of the imported application after clean
dependency installation. OpenAPI is used instead of only app.routes so nested
routers cannot disappear from the inventory. Duplicate operation IDs are also
blocked because they make the API contract ambiguous even when HTTP paths differ.
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


def main() -> int:
    from services.api.app.main import app

    operations: list[dict[str, object]] = []
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    grouped_operation_ids: dict[str, list[dict[str, object]]] = defaultdict(list)
    openapi_paths = app.openapi().get("paths", {})

    for path, path_item in sorted(openapi_paths.items()):
        if not isinstance(path, str) or not path.startswith("/api/") or not isinstance(path_item, dict):
            continue
        for method, operation in sorted(path_item.items()):
            method_upper = str(method).upper()
            if method_upper in {"PARAMETERS", "HEAD"} or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            item = {
                "method": method_upper,
                "path": path,
                "operation_id": operation_id,
                "summary": operation.get("summary"),
                "tags": operation.get("tags", []),
            }
            operations.append(item)
            grouped[(method_upper, path)].append(item)
            if isinstance(operation_id, str) and operation_id.strip():
                grouped_operation_ids[operation_id].append(item)

    duplicates = [
        {"method": method, "path": path, "registrations": entries}
        for (method, path), entries in sorted(grouped.items())
        if len(entries) > 1
    ]
    duplicate_operation_ids = [
        {"operation_id": operation_id, "registrations": entries}
        for operation_id, entries in sorted(grouped_operation_ids.items())
        if len(entries) > 1
    ]
    failures = [
        f"duplicate effective operation: {item['method']} {item['path']}"
        for item in duplicates
    ]
    failures.extend(
        f"duplicate operation_id: {item['operation_id']}"
        for item in duplicate_operation_ids
    )

    result = {
        "check": "R0.2_ROUTE_INVENTORY",
        "status": "PASS" if not failures else "BLOCKED",
        "source": "services.api.app.main.app.openapi.paths",
        "operation_count": len(operations),
        "duplicate_operation_count": len(duplicates),
        "duplicate_operations": duplicates,
        "duplicate_operation_id_count": len(duplicate_operation_ids),
        "duplicate_operation_ids": duplicate_operation_ids,
        "failures": failures,
        "operations": operations,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
