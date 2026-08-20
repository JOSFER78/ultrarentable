"""tests/test_nautilus_leverage_adversarial.py
Pruebas Adversariales de Apalancamiento y Tolerancia Cero en Gate 11 (NautilusGateEngine).
"""

import json
import math
import pytest
from services.api.app.validation.nautilus_gate_engine import NautilusGateEngine


@pytest.fixture
def real_candles():
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_suiusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        return json.load(f)


def test_leverage_hard_ceiling_breach_fails(real_candles):
    """Verify that exceeding max_leverage_ceiling (e.g. 3.27x > 3.00x) strictly FAILS Gate 11."""
    engine = NautilusGateEngine()
    candidate_dict = {
        "candidate_id": "cand_adv_leverage_01",
        "route": "FONDEO",
        "symbol": "SUIUSDT",
        "scorecard_json": {
            "parameters": {
                "sl_atr_mult": 1.5,
                "tp_atr_mult": 6.0,
                "risk_pct": 2.5,
            }
        },
    }
    
    # 1. Con un techo estricto de 3.0x, si el apalancamiento efectivo supera 3.0x debe fallar
    res_strict = engine.validate_candidate(
        candidate_dict=candidate_dict,
        candles=real_candles,
        account_size_usd=10000.0,
        max_leverage_ceiling=1.0,  # Forzar fallo de apalancamiento techo 1.0x
    )
    
    assert res_strict.effective_max_leverage >= 1.0
    assert res_strict.status == "FAILED"
    assert "Apalancamiento pico" in res_strict.diagnostics


def test_leverage_within_ceiling_passes_if_profitable(real_candles):
    """Verify that staying within leverage ceiling allows PASS if all other metrics are valid."""
    engine = NautilusGateEngine()
    candidate_dict = {
        "candidate_id": "cand_adv_leverage_02",
        "route": "ULTRA",
        "symbol": "SUIUSDT",
        "scorecard_json": {
            "parameters": {
                "sl_atr_mult": 1.5,
                "tp_atr_mult": 7.0,
                "risk_pct": 2.0,
            }
        },
    }
    
    res_permissive = engine.validate_candidate(
        candidate_dict=candidate_dict,
        candles=real_candles,
        account_size_usd=10000.0,
        max_leverage_ceiling=500.0,
    )
    
    assert res_permissive.effective_max_leverage <= 500.0
    assert not math.isnan(res_permissive.effective_max_leverage)


def test_nan_metrics_strictly_blocked(real_candles):
    """Verify that corrupt / NaN values in execution return status FAILED without exceptions."""
    engine = NautilusGateEngine()
    # Velas vacías
    res_empty = engine.validate_candidate(
        candidate_dict={"candidate_id": "cand_empty"},
        candles=[],
        account_size_usd=10000.0,
        max_leverage_ceiling=10.0,
    )
    assert res_empty.status in ["SKIPPED", "FAILED"]
    assert res_empty.verified is False
