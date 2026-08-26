#!/usr/bin/env python3
"""Fail-closed guard for the canonical web API client (R0.5).

The client may transport quantitative data, but it must not invent it or
reimplement certification decisions locally. Canonical identity belongs to
backend responses and explicit request parameters.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "apps" / "web" / "lib" / "api.ts"

FORBIDDEN_PATTERNS: dict[str, str] = {
    "hardcoded_timestamp_literal": r"(?<![A-Za-z0-9_])1[0-9]{12}(?![0-9])",
    "hardcoded_sha256_literal": r"[\"'][0-9a-fA-F]{64}[\"']",
    "hardcoded_dataset_id": r"\bdataset_id\s*[:=]\s*[\"']",
    "default_initial_capital": r"\binitial_capital\s*[:=]\s*\d+(?:\.\d+)?",
    "local_certification_comparison": r"\b(?:all_gates_pass|certification_status|is_certified|gates_passed_count)\b\s*(?:===|!==|==|!=|>=|<=|>|<|&&|\|\|)",
    "synthetic_random": r"\bMath\.random\s*\(",
}

REQUIRED_CANONICAL_CALLS = {
    "getCertifiedStrategies": "/api/v2/certified/strategies",
    "getCertifiedMetaStrategies": "/api/v2/certified/meta-strategies",
}


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    failures: list[str] = []

    for name, pattern in FORBIDDEN_PATTERNS.items():
        if re.search(pattern, source):
            failures.append(name)

    for function_name, endpoint in REQUIRED_CANONICAL_CALLS.items():
        match = re.search(
            rf"export\s+async\s+function\s+{re.escape(function_name)}\b.*?return\s+fetchJson<[^>]+>\(\"{re.escape(endpoint)}\"\)",
            source,
            flags=re.DOTALL,
        )
        if not match:
            failures.append(f"non_canonical_{function_name}")

    # Certification retrieval is transport-only: no local gate/metric decision
    # may be made inside these two client helpers.
    for function_name in REQUIRED_CANONICAL_CALLS:
        block = re.search(
            rf"export\s+async\s+function\s+{re.escape(function_name)}\b(?P<body>.*?)\n(?=export\s+|$)",
            source,
            flags=re.DOTALL,
        )
        if block and re.search(r"\b(?:profit_factor|max_drawdown|gates_passed_count|all_gates_pass|is_certified)\b", block.group("body")):
            failures.append(f"local_certification_logic_{function_name}")

    result = {
        "check": "R0.5_WEB_API_CLIENT_SURFACE",
        "status": "PASS" if not failures else "BLOCKED",
        "source": str(TARGET.relative_to(ROOT)),
        "failures": failures,
        "required_policy": "no hardcoded quantitative identity; no synthetic hash/time; no local certification decisions; canonical API ids only",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
