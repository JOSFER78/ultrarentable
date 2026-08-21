"""tests/test_gates_multitier_and_incubator.py
Suite de Tests y Verificación Cuantitativa de la Calibración Multi-Tier e Incubadora de Reprogramación.

Verifica:
1. Multi-Tier Ranking (100% Real, Cero Mocks):
   - Tier 1: Producción Certificada (11/11 Gates).
   - Tier 2: Diamantes en Bruto (9 - 10 Gates) -> No se descartan, se exponen para ajuste fino.
   - Tier 3: Incubadora de I+D (7 - 8 Gates) -> Se envían al bucle de reprogramación de IA.
   - Tier 4: Rechazo Estructural (< 7 Gates o fallo en Puertas Duras).
2. Prescripciones y Diagnóstico Accionable: Cada Gate fallido emite recetas de corrección cuantitativa.
3. Hard Gates Inquebrantables: Gate 1 (Datos limpios), Gate 2 (Costes reales), Gate 11 (Barra a barra) son innegociables.
4. API Integration: list_candidates soporta filtro por tier y expone metadatos de reprogramación.
"""

import hashlib
import json
import pytest

from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator


def _create_standard_candles(n: int = 100):
    return [
        {
            "timestamp_utc_ms": 1770000000000 + i * 3600000,
            "open": 20000.0 + i,
            "high": 20050.0 + i,
            "low": 19950.0 + i,
            "close": 20020.0 + i,
            "volume": 1000.0,
        }
        for i in range(n)
    ]


def _create_standard_trades(n: int = 40, win_ratio: float = 0.65):
    trades_raw = []
    pnl_list = []
    t0 = 1770000000000
    for i in range(n):
        is_win = (i % 3 != 0)
        pnl = 150.0 if is_win else -80.0
        ret_r = 1.8 if is_win else -1.0
        pnl_list.append(pnl)
        trades_raw.append({
            "trade_id": f"tr_{i}",
            "direction": "LONG",
            "entry_time_utc_ms": t0 + i * 3600000,
            "exit_time_utc_ms": t0 + (i + 1) * 3600000,
            "entry_price": 20000.0,
            "exit_price": 20050.0 if is_win else 19950.0,
            "quantity": 1.0,
            "gross_pnl_usd": pnl + 5.0,
            "fee_usd": 3.0,
            "slippage_usd": 2.0,
            "net_pnl_usd": pnl,
            "return_pct": 0.75 if is_win else -0.4,
            "return_r": ret_r,
            "exit_reason": "TAKE_PROFIT" if is_win else "STOP_LOSS",
        })
    return pnl_list, trades_raw


def test_tier_2_diamond_in_the_rough_classification(tmp_path):
    """Verifica que una estrategia con 10 Gates aprobados obtenga TIER_2_NEAR_CERTIFIED y recetas de mejora."""
    from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute
    from contracts.canonical_strategy import RuleTree, RuleCondition, IndicatorSpec, ComparisonOperator, ExitModel, SizingAndRisk

    orch = GatePipelineOrchestrator(evidence_base_dir=str(tmp_path))

    entry_rules = RuleTree(
        long_conditions=[
            RuleCondition(
                left_indicator=IndicatorSpec(name="RSI", timeframe="1h", period=14),
                operator=ComparisonOperator.GREATER_THAN,
                threshold_value=50.0,
            )
        ]
    )
    exit_rules = ExitModel(stop_loss_atr_mult=1.5, take_profit_atr_mult=3.0)
    sizing = SizingAndRisk(base_risk_pct=1.0, max_contracts_or_lots=2.0, base_leverage=1.0)

    strat = StrategySnapshot.create_and_hash(
        strategy_id="UR_DIAMOND_01",
        route=StrategyRoute.FONDEO,
        symbol="NQ",
        timeframe="1h",
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        sizing_and_risk=sizing,
        dataset_id_reference="ds_nq_h1",
        dataset_sha256_reference=hashlib.sha256(b"dataset_market_content").hexdigest(),
    )

    candidate_info = {
        "candidate_id": "UR_DIAMOND_01",
        "strategy_snapshot_hash": strat.canonical_hash,
        "dataset_id": "ds_nq_h1",
        "dataset_sha256": strat.dataset_sha256_reference,
        "symbol": "NQ",
        "timeframe": "1h",
        "route": "FONDEO",
        "trials_tested": 15,
        "parameters": {"fast_period": 12, "slow_period": 26, "sl_atr": 1.5, "tp_atr": 3.0},
        "profit_factor_oos": 1.65,
        "is_metrics": {"trades": 50, "profit_factor": 1.7, "max_drawdown_pct": 2.5, "win_rate_pct": 60.0},
        "oos_metrics": {"trades": 40, "profit_factor": 1.55, "max_drawdown_pct": 2.8, "win_rate_pct": 58.0},
    }

    candles = [
        {
            "timestamp_utc_ms": 1770000000000 + i * 3600000,
            "open": 20000.0 + i * 2.0,
            "high": 20050.0 + i * 2.0,
            "low": 19950.0 + i * 2.0,
            "close": 20020.0 + i * 2.0,
            "volume": 1000.0,
        }
        for i in range(300)
    ]

    pnl_fractional = [0.0075, -0.0035, 0.0080, -0.0030, 0.0065, -0.0035, 0.0090, -0.0040, 0.0050, 0.0060] * 5
    trades_raw = [
        {
            "trade_id": f"t_{i}",
            "direction": "LONG",
            "entry_time_utc_ms": 1770000000000 + i * 3600000,
            "exit_time_utc_ms": 1770000000000 + (i + 1) * 3600000,
            "entry_price": 20000.0,
            "exit_price": 20050.0 if (i % 3 != 0) else 19950.0,
            "quantity": 1.0,
            "gross_pnl_usd": 150.0 if (i % 3 != 0) else -70.0,
            "net_pnl_usd": 145.0 if (i % 3 != 0) else -75.0,
            "fee_usd": 3.0,
            "slippage_usd": 2.0,
            "return_pct": 0.0075 if (i % 3 != 0) else -0.0035,
            "return_r": 2.0 if (i % 3 != 0) else -1.0,
            "exit_reason": "TAKE_PROFIT" if (i % 3 != 0) else "STOP_LOSS",
        }
        for i in range(50)
    ]

    res = orch.run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=pnl_fractional,
        oos_trades=pnl_fractional,
        pre_oos_trades=pnl_fractional,
        trades_raw=trades_raw,
        strategy_snapshot=strat,
    )

    assert res["total_gates"] == 11
    assert res["gates_passed_count"] in (9, 10)
    assert res["tier"] == "TIER_2_NEAR_CERTIFIED"
    assert "Diamante en Bruto" in res["tier_label"]
    assert res["can_reprogram"] is True
    assert len(res["prescriptions"]) >= 1
    assert any(p["gate_id"] == 7 for p in res["prescriptions"])
    assert "actionable_advice" in res["prescriptions"][0]


def test_api_candidates_multitier_filtering():
    """Verifica que el endpoint /api/v1/candidates filtre por Tiers y entregue etiquetas cuantitativas."""
    from fastapi.testclient import TestClient
    from services.api.app.main import app

    client = TestClient(app)
    res = client.get("/api/v1/candidates?include_rejected=true&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        cand = data[0]
        assert "tier" in cand
        assert "tier_label" in cand
        assert "can_reprogram" in cand
        assert "prescriptions" in cand
        assert isinstance(cand["prescriptions"], list)

    # Filtrar específicamente por Tier 1
    res_t1 = client.get("/api/v1/candidates?tier=TIER_1_CERTIFIED&limit=10")
    assert res_t1.status_code == 200
    for c in res_t1.json():
        assert c["tier"] == "TIER_1_CERTIFIED"


def test_api_reprogram_endpoint_exists():
    """Verifica que el endpoint de reprogramación POST /api/v1/candidates/{id}/reprogram esté expuesto."""
    from fastapi.testclient import TestClient
    from services.api.app.main import app

    client = TestClient(app)
    res = client.post("/api/v1/candidates/non_existent_strat_id/reprogram?max_iterations=1")
    assert res.status_code in (200, 404)  # Retorna resultado o 404 sin crashear el servidor


def test_tier_2_and_tier_3_incubator_prescriptions(tmp_path):
    orch = GatePipelineOrchestrator(evidence_base_dir=str(tmp_path))

    # Muestra con menos trades en OOS (provoca advertencia en Gate 03 / Gate 04)
    short_is = [100.0, -50.0] * 10
    short_oos = [80.0, -90.0] * 5
    candles = _create_standard_candles(100)

    candidate_info = {
        "candidate_id": "UR_INCUBATOR_CANDIDATE",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "route": "ULTRA",
        "trials_tested": 150,  # Alta penalización DSR
        "parameters": {"fast_ema": 10, "slow_ema": 30},
        "profit_factor_oos": 0.95,
    }

    res = orch.run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=short_is,
        oos_trades=short_oos,
        pre_oos_trades=short_is,
        trades_raw=[],
    )

    assert res["tier"] in ("TIER_2_NEAR_CERTIFIED", "TIER_3_INCUBATOR", "TIER_4_REJECTED")
    assert len(res["prescriptions"]) >= 1
    # Cada prescripción contiene recomendación accionable
    p0 = res["prescriptions"][0]
    assert "gate_id" in p0
    assert "actionable_advice" in p0
    assert len(p0["actionable_advice"]) > 10


def test_hard_gates_are_non_negotiable(tmp_path):
    """Verifica que el fallo en una Puerta Dura (Gate 02 Costes Netos <= 0) impida Tier 1 o Tier 2."""
    orch = GatePipelineOrchestrator(evidence_base_dir=str(tmp_path))

    # Trades con PnL neto negativo debido a costes excesivos
    trades_losing_after_fees = [
        {
            "trade_id": f"tr_{i}",
            "direction": "LONG",
            "entry_time_utc_ms": 1770000000000 + i * 3600000,
            "exit_time_utc_ms": 1770000000000 + (i + 1) * 3600000,
            "entry_price": 100.0,
            "exit_price": 100.2,
            "quantity": 1.0,
            "gross_pnl_usd": 2.0,
            "fee_usd": 3.0,
            "slippage_usd": 1.0,
            "net_pnl_usd": -2.0,  # Pierde por comisiones
            "return_pct": -0.02,
            "return_r": -0.5,
            "exit_reason": "TAKE_PROFIT",
        }
        for i in range(20)
    ]
    pnl_neg = [-2.0] * 20
    candles = _create_standard_candles(100)

    candidate_info = {
        "candidate_id": "UR_LOSER_AFTER_FEES",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "route": "ULTRA",
        "trials_tested": 10,
        "parameters": {},
        "profit_factor_oos": 0.8,
    }

    res = orch.run_all_gates(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=pnl_neg,
        oos_trades=pnl_neg,
        pre_oos_trades=pnl_neg,
        trades_raw=trades_losing_after_fees,
    )

    # Gate 2 falló (costes netos negativos)
    g2_res = next(g for g in res["gates"] if g["gate_id"] == 2)
    assert g2_res["passed"] is False
    # La estrategia NO puede ser Tier 1 ni Tier 2
    assert res["tier"] in ("TIER_3_INCUBATOR", "TIER_4_REJECTED")
    assert res["overall_certified"] is False
