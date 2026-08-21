"""services/api/app/validation/gates/gate_01_data_ingest.py
Gate 1: Saneamiento, Continuidad Temporal e Integridad Criptográfica de Datos OHLCV.
Verifica que no existan huecos temporales (gaps), desorden temporal, velas corruptas o precios negativos.
Calcula el SHA-256 criptográfico real del dataset en disco.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional


TIMEFRAME_SECONDS_MAP = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "h1": 3600,
    "4h": 14400,
    "h4": 14400,
    "1d": 86400,
    "d1": 86400,
}


class Gate01DataIngest:
    GATE_ID = 1
    NAME = "DATA_INGEST"
    LABEL = "1. DATA INGEST & CONTINUITY"

    def evaluate(
        self,
        candles: List[Dict[str, Any]],
        timeframe: str = "1h",
        dataset_filepath: Optional[str] = None,
    ) -> Dict[str, Any]:
        tf_clean = str(timeframe or "1h").lower()
        min_required = 50 if tf_clean in ("1d", "d1") else (150 if tf_clean in ("4h", "h4") else (200 if tf_clean in ("1h", "h1") else 300))

        if not candles or len(candles) < min_required:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": f"RECHAZADO: Dataset insuficiente ({len(candles) if candles else 0} < {min_required} velas para timeframe {timeframe})",
                "evidence": {
                    "total_candles": len(candles) if candles else 0,
                    "min_required": min_required,
                    "corrupt_bars": 0,
                    "gaps_detected": 0,
                    "out_of_order_bars": 0,
                    "dataset_sha256": None,
                },
            }

        # 1. SHA-256 Criptográfico Real de los bytes del dataset en disco
        real_sha256 = None
        if dataset_filepath and os.path.exists(dataset_filepath):
            with open(dataset_filepath, "rb") as f:
                real_sha256 = hashlib.sha256(f.read()).hexdigest()
        else:
            # Hash determinista de la secuencia de velas
            raw_bytes = "".join(f"{c.get('timestamp')}:{c.get('close')}" for c in candles).encode("utf-8")
            real_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        expected_step = TIMEFRAME_SECONDS_MAP.get(timeframe.lower(), 3600)
        total_candles = len(candles)
        corrupt_bars = 0
        zero_vol_bars = 0
        gaps_detected = 0
        out_of_order_bars = 0
        max_gap_seconds = 0

        prev_ts = None
        for i, c in enumerate(candles):
            open_px = float(c.get("open", 0.0))
            high = float(c.get("high", 0.0))
            low = float(c.get("low", 0.0))
            close = float(c.get("close", 0.0))
            vol = float(c.get("volume", 0.0))
            ts = c.get("timestamp")

            # Validación OHLC
            if high < low or high < close or high < open_px or low > close or low > open_px or low <= 0 or open_px <= 0 or close <= 0:
                corrupt_bars += 1

            if vol <= 0:
                zero_vol_bars += 1

            # Validación de Continuidad Temporal
            if ts is not None and prev_ts is not None:
                # Normalizar timestamp a segundos si viene en milisegundos
                current_ts_sec = float(ts) / 1000.0 if float(ts) > 1e11 else float(ts)
                prev_ts_sec = float(prev_ts) / 1000.0 if float(prev_ts) > 1e11 else float(prev_ts)
                delta_sec = current_ts_sec - prev_ts_sec

                if delta_sec < 0:
                    out_of_order_bars += 1
                elif delta_sec > expected_step * 1.5:
                    gaps_detected += 1
                    if delta_sec > max_gap_seconds:
                        max_gap_seconds = int(delta_sec)

            prev_ts = ts

        # Criterios matemáticos de aprobación
        # Cero velas corruptas ni fuera de orden, y tamaño mínimo según timeframe
        passed = (corrupt_bars == 0) and (out_of_order_bars == 0) and (total_candles >= min_required) and (gaps_detected <= total_candles * 0.02)
        
        # Penalización estricta de score
        error_ratio = (corrupt_bars * 5 + out_of_order_bars * 10 + gaps_detected) / max(1, total_candles)
        score = max(0.0, min(100.0, (1.0 - error_ratio) * 100.0)) if passed else 0.0

        verdict_msg = (
            f"PASSED: Dataset verificado ({total_candles} velas, SHA256: {real_sha256[:8]}..., 0 corruptas, {gaps_detected} gaps tolerados)"
            if passed
            else f"FALLO: {corrupt_bars} corruptas, {out_of_order_bars} desordenadas, {gaps_detected} gaps excesivos"
        )

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": verdict_msg,
            "evidence": {
                "total_candles": total_candles,
                "corrupt_bars": corrupt_bars,
                "out_of_order_bars": out_of_order_bars,
                "gaps_detected": gaps_detected,
                "max_gap_seconds": max_gap_seconds,
                "expected_timeframe_step_sec": expected_step,
                "zero_volume_bars": zero_vol_bars,
                "dataset_sha256": real_sha256,
                "integrity_pct": round((1.0 - (corrupt_bars + out_of_order_bars) / max(1, total_candles)) * 100.0, 2),
            },
        }
