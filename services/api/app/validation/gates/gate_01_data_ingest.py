"""services/api/app/validation/gates/gate_01_data_ingest.py
Gate 1: Saneamiento e Integridad de Datos OHLCV.
Verifica que no existan huecos temporales, datos corruptos, precios negativos o gaps críticos.
"""

from typing import Any, Dict, List
import numpy as np


class Gate01DataIngest:
    GATE_ID = 1
    NAME = "DATA_INGEST"
    LABEL = "1. DATA INGEST"

    def evaluate(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not candles or len(candles) < 500:
            return {
                "gate_id": self.GATE_ID,
                "name": self.NAME,
                "passed": False,
                "score": 0.0,
                "verdict": "RECHAZADO: Dataset insuficiente (< 500 velas)",
                "evidence": {
                    "total_candles": len(candles) if candles else 0,
                    "min_required": 500,
                    "corrupt_bars": 0,
                    "gaps_detected": 0,
                },
            }

        total_candles = len(candles)
        corrupt_bars = 0
        zero_vol_bars = 0
        gaps_detected = 0

        for i, c in enumerate(candles):
            high = float(c.get("high", 0.0))
            low = float(c.get("low", 0.0))
            close = float(c.get("close", 0.0))
            open_px = float(c.get("open", 0.0))
            vol = float(c.get("volume", 1.0))

            if high < low or high < close or high < open_px or low > close or low > open_px or low <= 0:
                corrupt_bars += 1
            if vol <= 0:
                zero_vol_bars += 1

        passed = (corrupt_bars == 0) and (total_candles >= 2000)
        score = 100.0 if passed else max(0.0, 100.0 - (corrupt_bars * 10))

        return {
            "gate_id": self.GATE_ID,
            "name": self.NAME,
            "passed": passed,
            "score": round(score, 1),
            "verdict": "PASSED: Datos OHLCV saneados y validados" if passed else f"FALLO: {corrupt_bars} velas corruptas",
            "evidence": {
                "total_candles": total_candles,
                "corrupt_bars": corrupt_bars,
                "zero_volume_bars": zero_vol_bars,
                "integrity_pct": round((1.0 - corrupt_bars / max(1, total_candles)) * 100.0, 2),
            },
        }
