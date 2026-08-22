# -*- coding: utf-8 -*-
"""tests/test_zero_mocks.py — Guardia ZERO-MOCKS.

Ejecución: python3 tests/test_zero_mocks.py  (exit 0 = limpio, exit 1 = violaciones)

Demuestra la ausencia de datos falsos conocidos en el código fuente:
 - Literales de métricas/contadores que fueron eliminados en FASE 1 (regresión).
 - Patrones de fallback inventado en métricas (|| 1.35, ?? 1.34, min(4.0, ...)).
 - Telemetría decorativa de gates (valores declarados a mano).
 - Vela sintética del adaptador de backtest.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_DIRS = [
    ROOT / "apps" / "web" / "app",
    ROOT / "apps" / "web" / "components",
    ROOT / "apps" / "web" / "lib",
    ROOT / "services",
    ROOT / "contracts",
]

# Literales de datos falsos eliminados en FASE 1 (regresión si reaparecen)
BANNED_SUBSTRINGS = [
    "78813", "610531", "255906", "109674", "48744", "21325", "609305",
    "1.103.251", "9.882", "14210", "78.813",
]

# Patrones regex de fabricación de métricas
BANNED_PATTERNS = [
    (re.compile(r"sharpe_ratio\s*=\s*2\.1\b"), "sharpe literal 2.1"),
    (re.compile(r"min\(4\.0\s*,\s*\w+\)"), "recorte de DD a 4%"),
    (re.compile(r"\|\|\s*1\.35\b"), "fallback PF 1.35"),
    (re.compile(r"\?\?\s*1\.34\b"), "fallback PF OOS 1.34"),
    (re.compile(r"\?\?\s*48\.5\b"), "fallback winrate 48.5"),
    (re.compile(r"\|\|\s*4\.2\b"), "fallback DD 4.2"),
    (re.compile(r"\|\|\s*40\.0\b"), "fallback winrate 40"),
    (re.compile(r"\|\|\s*35\.0\b"), "fallback ROI 35"),
    (re.compile(r"pass_rate_pct.{0,40}80\.0"), "pass_rate inventado 80%"),
    (re.compile(r"days_taken.{0,30}\?\?\s*8\.0|oos_months\s*\?\?\s*8\.0"), "oos_months inventado 8.0"),
    (re.compile(r"\|\|\s*230\b"), "contador hardcodeado 230"),
    (re.compile(r'\|\|\s*1420\b'), "tasksCompleted inventado 1420"),
    (re.compile(r"99\.0 if tot_p > 0"), "profit factor acuñado 99.0"),
    (re.compile(r'\{"time": "2026-01-01", "open": 100\.0'), "vela sintética del adaptador"),
    (re.compile(r"datasets_audited\"?:\s*\d+"), "telemetría de gate declarada a mano"),
    (re.compile(r'"status":\s*"ONLINE · MONITORIZANDO"'), "estado de gate decorativo"),
]

EXCLUDE_PARTS = {"node_modules", ".git", "__pycache__", "tests"}
EXCLUDE_FILES = {Path(__file__).name}


def iter_source_files():
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.suffix not in {".ts", ".tsx", ".py"} or not p.is_file():
                continue
            if p.name in EXCLUDE_FILES or EXCLUDE_PARTS & set(p.parts):
                continue
            yield p


def main() -> int:
    violations: list[str] = []
    for p in iter_source_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = p.relative_to(ROOT)
        for lit in BANNED_SUBSTRINGS:
            if lit in text:
                violations.append(f"{rel}: literal prohibido '{lit}'")
        for rx, desc in BANNED_PATTERNS:
            m = rx.search(text)
            if m:
                line = text.count("\n", 0, m.start()) + 1
                violations.append(f"{rel}:{line}: patrón prohibido ({desc})")

    if violations:
        print(f"ZERO-MOCKS: {len(violations)} VIOLACIONES:")
        for v in violations:
            print(f"  ✗ {v}")
        return 1
    print("ZERO-MOCKS: OK — sin literales ni patrones de datos falsos conocidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
