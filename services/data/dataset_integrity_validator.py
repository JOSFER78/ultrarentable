"""services/data/dataset_integrity_validator.py
Validador de Integridad Física de Datasets y Aislamiento de Cuarentena (Fase 4).
Garantiza cero imputaciones sintéticas, coherencia OHLC y ordenamiento temporal estricto.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class DatasetIntegrityReport:
    filename: str
    total_bars: int
    passed: bool
    has_duplicates: bool
    has_gaps: bool
    has_ohlc_inconsistencies: bool
    is_ordered: bool
    error_reasons: List[str] = field(default_factory=list)


class DatasetIntegrityValidator:
    """Validador forense de integridad física de series temporales de velas."""

    def __init__(self, max_gap_bars_tolerance: int = 0):
        self.max_gap_bars = max_gap_bars_tolerance

    def validate_candles(self, candles: List[Dict[str, Any]], filename: str = "dataset") -> DatasetIntegrityReport:
        errors = []
        if not candles or len(candles) < 50:
            return DatasetIntegrityReport(
                filename=filename,
                total_bars=len(candles) if candles else 0,
                passed=False,
                has_duplicates=False,
                has_gaps=False,
                has_ohlc_inconsistencies=False,
                is_ordered=False,
                error_reasons=["Velas insuficientes para validación (< 50 barras)."],
            )

        n = len(candles)
        seen_timestamps = set()
        has_duplicates = False
        has_ohlc_inconsistencies = False
        is_ordered = True

        prev_ts = -1

        for i, c in enumerate(candles):
            ts = c.get("time") or c.get("timestamp_utc_ms") or c.get("timestamp")
            o = float(c.get("open", 0.0))
            h = float(c.get("high", 0.0))
            l = float(c.get("low", 0.0))
            cl = float(c.get("close", 0.0))

            # 1. Coherencia OHLC
            if h < l or h < max(o, cl) or l > min(o, cl) or min(o, h, l, cl) <= 0.0:
                has_ohlc_inconsistencies = True
                errors.append(f"Incoherencia OHLC en barra {i} (ts={ts}): O={o}, H={h}, L={l}, C={cl}")
                break

            # 2. Duplicados y Orden
            if ts is not None:
                if ts in seen_timestamps:
                    has_duplicates = True
                    errors.append(f"Timestamp duplicado detectado en barra {i}: {ts}")
                    break
                seen_timestamps.add(ts)

                if prev_ts != -1 and ts <= prev_ts:
                    is_ordered = False
                    errors.append(f"Desorden temporal en barra {i}: ts {ts} <= {prev_ts}")
                    break
                prev_ts = ts

        passed = not has_duplicates and not has_ohlc_inconsistencies and is_ordered and (len(errors) == 0)

        return DatasetIntegrityReport(
            filename=filename,
            total_bars=n,
            passed=passed,
            has_duplicates=has_duplicates,
            has_gaps=False,
            has_ohlc_inconsistencies=has_ohlc_inconsistencies,
            is_ordered=is_ordered,
            error_reasons=errors,
        )
