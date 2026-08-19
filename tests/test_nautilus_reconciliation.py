"""tests/test_nautilus_reconciliation.py
Verificación de reconciliación cross-engine (Fase 13: EventBacktestEngine vs NautilusGateEngine).
"""

import json
import pytest
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.cross_engine_reconciler import CrossEngineReconciler


def test_cross_engine_reconciliation_on_real_candles():
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_suiusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    ultra_discovery = UltraDiscoveryEngine()
    strategy = ultra_discovery.generate_candidate_blueprint(
        strategy_id="cand_reconcile_sui_01",
        symbol="SUIUSDT",
        timeframe="1h",
        dataset_id="ds_binance_suiusdt_1h",
        dataset_sha256="sui_hash_123456",
        leverage=50.0,
        sl_atr_mult=1.5,
        tp_atr_mult=7.0,
    )

    reconciler = CrossEngineReconciler()
    report = reconciler.reconcile(strategy, candles, account_size_usd=10000.0)

    assert report.strategy_id == "cand_reconcile_sui_01"
    assert report.internal_engine_trades > 0
    assert report.nautilus_engine_trades > 0
    assert report.verdict in ["RECONCILIADO_EXITOSAMENTE", "RECONCILIACION_CON_DISCREPANCIAS"]
    assert isinstance(report.profit_factor_delta, float)
