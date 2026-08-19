"""services/validation/engines/gate_01_ingest_sanity.py
Motor 1 de Validación: Saneamiento e Integridad de Datos (Ingest Sanity).
Audita calidad del feed de datos: gaps, timestamps, OHLCV coherente, volumen no nulo y ausencia de NaNs.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np


@dataclass
class IngestSanityResult:
    passed: bool
    total_bars: int
    gap_count: int
    corrupted_bars: int
    nan_count: int
    zero_volume_bars: int
    error_reasons: List[str]


class IngestSanityEngine:
    """Motor independiente para validar la integridad física de las series temporales."""

    def __init__(self, max_allowed_gaps: int = 5, max_allowed_corrupt: int = 0) -> None:
        self.max_allowed_gaps = max_allowed_gaps
        self.max_allowed_corrupt = max_allowed_corrupt

    def evaluate(self, df: pd.DataFrame) -> IngestSanityResult:
        errors: List[str] = []
        if df is None or df.empty:
            return IngestSanityResult(
                passed=False,
                total_bars=0,
                gap_count=0,
                corrupted_bars=0,
                nan_count=0,
                zero_volume_bars=0,
                error_reasons=["Dataset vacío o nulo."],
            )

        total_bars = len(df)
        nan_count = int(df.isna().sum().sum())
        if nan_count > 0:
            errors.append(f"Se detectaron {nan_count} valores NaN en la serie de precios.")

        # Verificar integridad OHLC (High >= Low, High >= Open/Close, Low <= Open/Close)
        corrupted = 0
        if {"open", "high", "low", "close"}.issubset(set(c.lower() for c in df.columns)):
            col_map = {c.lower(): c for c in df.columns}
            h = df[col_map["high"]]
            l = df[col_map["low"]]
            o = df[col_map["open"]]
            c = df[col_map["close"]]

            invalid_high = (h < l) | (h < o) | (h < c)
            invalid_low = (l > o) | (l > c)
            corrupted = int((invalid_high | invalid_low).sum())
            if corrupted > self.max_allowed_corrupt:
                errors.append(f"Se detectaron {corrupted} barras con OHLC físicamente imposible.")

        # Gaps temporales
        gap_count = 0
        if "timestamp" in [c.lower() for c in df.columns] or isinstance(df.index, pd.DatetimeIndex):
            # Comprobar monotonicidad
            if isinstance(df.index, pd.DatetimeIndex):
                diffs = df.index.to_series().diff()
            else:
                ts_col = [c for c in df.columns if c.lower() == "timestamp"][0]
                diffs = pd.to_datetime(df[ts_col]).diff()

            median_dt = diffs.median()
            if pd.notna(median_dt):
                gaps = diffs > (median_dt * 3)
                gap_count = int(gaps.sum())
                if gap_count > self.max_allowed_gaps:
                    errors.append(f"Gaps temporales excesivos: {gap_count} discontinuidades detectadas.")

        zero_vol = 0
        if "volume" in [c.lower() for c in df.columns]:
            vol_col = [c for c in df.columns if c.lower() == "volume"][0]
            zero_vol = int((df[vol_col] <= 0).sum())

        passed = len(errors) == 0
        return IngestSanityResult(
            passed=passed,
            total_bars=total_bars,
            gap_count=gap_count,
            corrupted_bars=corrupted,
            nan_count=nan_count,
            zero_volume_bars=zero_vol,
            error_reasons=errors,
        )
