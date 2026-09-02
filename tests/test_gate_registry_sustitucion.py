"""tests/test_gate_registry_sustitucion.py
Pruebas de sustitución granular e independencia modular en el registro v1.
Demuestra que modificar o sustituir un gate (Gate 4) no altera los otros 10 gates.
"""

from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
from typing import Any, Dict

from contracts.canonical_strategy import (
    ComparisonOperator,
    ExitModel,
    IndicatorSpec,
    RuleCondition,
    RuleTree,
    SizingAndRisk,
)
from contracts.snapshots.strategy_snapshot import (
    LogicalOp,
    SizingType,
    StopLossType,
    StrategyRoute,
    StrategySnapshot,
    TakeProfitType,
)
from services.validation.registry import GATE_REGISTRY, Evidencia, RegistryPipeline
from services.validation.registry.gates.gate_04 import Gate04WalkForward


def _crear_fixture_tier2_evidencia() -> Evidencia:
    entry_rules = RuleTree(
        logic=LogicalOp.AND,
        direction="LONG",
        long_conditions=[
            RuleCondition(
                left=IndicatorSpec(name="RSI", params={"period": 14}, source_field="close", shift=0),
                op=ComparisonOperator.GT,
                right=50.0,
            )
        ],
    )
    exit_rules = ExitModel(
        sl_type=StopLossType.ATR_MULTIPLE,
        sl_value=1.5,
        tp_type=TakeProfitType.ATR_MULTIPLE,
        tp_value=3.0,
    )
    sizing = SizingAndRisk(
        sizing_type=SizingType.RISK_PCT_EQUITY,
        risk_value=0.01,
        max_open_positions=1,
        max_contracts_or_lots=2.0,
    )

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

    return Evidencia(
        candidate_info=candidate_info,
        candles=candles,
        is_trades=pnl_fractional,
        oos_trades=pnl_fractional,
        pre_oos_trades=pnl_fractional,
        trades_raw=trades_raw,
        strategy_snapshot=strat,
    )


def test_sustitucion_gate_04_umbral_0_45():
    """Demuestra sustitución aislada del Gate 4 elevando min_avg_wfe de 0.40 a 0.45."""
    class Gate04Variante(Gate04WalkForward):
        VERSION = "1.1.0-test"
        UMBRALES = {**Gate04WalkForward.UMBRALES, "min_avg_wfe": 0.45}

    ev = _crear_fixture_tier2_evidencia()

    # Ejecución canónica previa
    pipeline_canonica = RegistryPipeline()
    res_antes = pipeline_canonica.veredicto(ev)

    # Pipeline con Gate 4 sustituido
    reg_b = dict(GATE_REGISTRY)
    reg_b[4] = Gate04Variante
    pipeline_variante = RegistryPipeline(registry=reg_b)
    res_despues = pipeline_variante.veredicto(ev)

    # 1. Gate 4 antes vs después
    g4_antes = res_antes["gates"][3]
    g4_despues = res_despues["gates"][3]

    assert g4_antes["passed"] is True
    assert g4_antes["score"] == 66.7
    assert g4_antes["gate_version"] == "1.0.0"

    assert g4_despues["passed"] is False
    assert g4_despues["score"] == 22.2
    assert g4_despues["gate_version"] == "1.1.0-test"

    # 2. Los otros 10 gates permanecen idénticos
    for idx in [0, 1, 2, 4, 5, 6, 7, 8, 9, 10]:
        ga = res_antes["gates"][idx]
        gd = res_despues["gates"][idx]
        assert ga == gd, f"Gate {idx+1} se vio afectado indebidamente"
        assert gd["gate_version"] == "1.0.0"

    # 3. Veredictos agregados reflejan el cambio
    assert res_antes["gates_passed_count"] == 9
    assert res_despues["gates_passed_count"] == 8
    assert res_antes["tier"] == "TIER_2_NEAR_CERTIFIED"
    assert res_despues["tier"] == "TIER_3_INCUBATOR"


def test_variante_no_toca_otros_modulos():
    """Verifica que el registro variante conserve referencias intactas a los módulos canónicos en disco."""
    class Gate04Variante(Gate04WalkForward):
        VERSION = "1.1.0-test"

    reg_b = dict(GATE_REGISTRY)
    reg_b[4] = Gate04Variante

    for gid in range(1, 12):
        if gid != 4:
            assert reg_b[gid] is GATE_REGISTRY[gid]
        
        canon_cls = GATE_REGISTRY[gid]
        src_file = inspect.getsourcefile(canon_cls)
        assert src_file is not None
        norm_src = src_file.replace("\\", "/")
        assert norm_src.endswith(f"services/validation/registry/gates/gate_{gid:02d}.py")
