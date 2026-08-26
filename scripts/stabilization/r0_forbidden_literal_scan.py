#!/usr/bin/env python3
"""Fail-closed scan for known synthetic quantitative literals and generators."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [ROOT / "apps" / "web", ROOT / "services"]
EXCLUDED_PARTS = {"node_modules", ".next", "__pycache__", ".venv", "dist", "build"}

FORBIDDEN = {
    "known_synthetic_sha": re.compile(r"a3f5c9e2d1b8f4a7c0e3b6d9f2a5c8e1d4b7a0f3c6e9b2d5a8f1c4e7b0d3a6f9", re.I),
    "known_synthetic_timestamp": re.compile(r"\b(?:1672531200000|1704067200000)\b"),
    "known_synthetic_meta_strategy": re.compile(r"META-PORT-BTC-ETH-NQ-01"),
    "random_generator": re.compile(r"\bMath\.random\s*\("),
}

TEXT_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".json", ".yaml", ".yml"}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for scan_root in SCAN_ROOTS:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            files.append(path)
    return files


def main() -> int:
    hits: list[dict[str, object]] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for name, pattern in FORBIDDEN.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append({"rule": name, "file": str(path.relative_to(ROOT)), "line": line})

    result = {
        "check": "R0.8_FORBIDDEN_LITERAL_SCAN",
        "status": "PASS" if not hits else "BLOCKED",
        "hit_count": len(hits),
        "hits": hits,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
