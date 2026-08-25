"""tests/test_gate07_fail_closed_no_timestamps.py
Verificación de comportamiento fail-closed en Gate 07 cuando los trades carecen de timestamps físicos.
"""
import pytest
from services.api.app.validation.gates.gate_07_regime_coverage import Gate07RegimeCoverage

def test_gate07_fail_closed_missing_timestamps():
    gate = Gate07RegimeCoverage()
    
    # Velas válidas
    candles = [
        {"close": 100.0 + i, "high": 102.0 + i, "low": 99.0 + i, "timestamp_utc_ms": 1700000000000 + i * 3600000}
        for i in range(100)
    ]
    
    # Trades sin entry_bar_idx, bar_index ni entry_time_utc_ms
    bad_trades = [
        {"pnl": 50.0},
        {"pnl": -20.0},
        {"pnl": 30.0},
    ]
    
    res = gate.evaluate(candles=candles, trades_raw=bad_trades)
    assert res["passed"] is False
    assert "BLOCKED_MISSING_TEMPORAL_EVIDENCE" in res["verdict"] or "RECHAZADO" in res["verdict"]
    assert res["evidence"]["unmapped_trade_index"] == 0
