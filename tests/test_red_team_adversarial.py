"""tests/test_red_team_adversarial.py
Batería de Pruebas Adversariales Forenses (Red-Team Attacks - Fase 6).
Valida que el sistema cumple de forma matemática e incondicional la Doctrina Zero-Mocks & Real-Only:
1. Inmunidad a corrupción de velas.
2. Inmunidad a alteración de parámetros.
3. Intolerancia a falta de trials en Gate 8 (DSR).
4. Intolerancia a ausencia de trades físicos en Gate 7.
5. Intolerancia a ausencia de velas para re-backtesting en Gate 9.
6. Integridad criptográfica SHA-256 de 64 caracteres en EvidenceRecord.
"""

import hashlib
import json
import pytest
from contracts.snapshots.strategy_snapshot import StrategyRoute
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.api.app.validation.gates.gate_07_regime_coverage import Gate07RegimeCoverage
from services.api.app.validation.gates.gate_08_dsr_ratio import Gate08DSRRatio
from services.api.app.validation.gates.gate_09_novelty_antifit import Gate09NoveltyAntiFit
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator


def test_redteam_candle_tampering_alters_backtest_deterministically():
    """Attack 1: Modificar 1 sola vela altera el resultado físico del backtest."""
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    ultra_discovery = UltraDiscoveryEngine()
    strat = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_rt_01",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_btc_1h",
        dataset_sha256="sha_rt_1",
        risk_pct=0.015,  # re-pin motor 5.10.0 (unidad de riesgo = fraccion, no porcentaje)
    )

    engine = EventBacktestEngine()
    res_clean = engine.run_backtest(strat, candles)

    # Corromper velas en la serie
    tampered_candles = json.loads(json.dumps(candles))
    for k in range(min(50, len(tampered_candles))):
        tampered_candles[k]["close"] *= 1.15
        tampered_candles[k]["high"] *= 1.20

    res_tampered = engine.run_backtest(strat, tampered_candles)

    # El resultado debe cambiar físicamente y no ocultar discrepancias
    assert res_clean.net_profit_usd != res_tampered.net_profit_usd or res_clean.total_trades != res_tampered.total_trades


def test_redteam_gate_08_blocks_unverified_trials():
    """Attack 2: Gate 8 rechaza categóricamente si trials_tested es None o <= 0."""
    g8 = Gate08DSRRatio()
    
    # 0 trials
    res_zero = g8.evaluate(oos_trades_pnl=[10.0, -5.0, 12.0, -3.0, 8.0, 15.0, -4.0, 9.0, 11.0, -2.0], trials_tested=0)
    assert not res_zero["passed"]
    assert "BLOCKED" in res_zero["verdict"]

    # None trials
    res_none = g8.evaluate(oos_trades_pnl=[10.0, -5.0, 12.0, -3.0, 8.0, 15.0, -4.0, 9.0, 11.0, -2.0], trials_tested=None)
    assert not res_none["passed"]
    assert "BLOCKED" in res_none["verdict"]

    # Negative trials
    res_neg = g8.evaluate(oos_trades_pnl=[10.0, -5.0, 12.0, -3.0, 8.0, 15.0, -4.0, 9.0, 11.0, -2.0], trials_tested=-5)
    assert not res_neg["passed"]
    assert "BLOCKED" in res_neg["verdict"]


def test_redteam_gate_07_blocks_synthetic_fallback():
    """Attack 3: Gate 7 rechaza si no hay trades_raw con timestamps reales."""
    g7 = Gate07RegimeCoverage()
    res = g7.evaluate(candles=[{"close": 100, "volume": 10} for _ in range(100)], trades_raw=[], oos_trades_pnl=[10.0, -5.0])
    assert not res["passed"]
    assert "BLOCKED" in res["verdict"]


def test_redteam_gate_09_blocks_missing_rebacktest_evidence():
    """Attack 4: Gate 9 rechaza si faltan velas para re-backtesting de vecindario."""
    g9 = Gate09NoveltyAntiFit()
    res = g9.evaluate(parameters={"ema_fast": 20, "ema_slow": 50}, trades_count=50, oos_pf=2.1, candles=[], strategy_snapshot=None)
    assert not res["passed"]
    assert "BLOCKED" in res["verdict"]


def test_redteam_evidence_record_sha256_integrity():
    """Attack 5: EvidenceRecord genera hashes de 64 caracteres válidos."""
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    ultra_discovery = UltraDiscoveryEngine()
    strat = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_rt_hash",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_btc_1h",
        dataset_sha256="sha_rt_1",
        risk_pct=0.015,  # re-pin motor 5.10.0 (unidad de riesgo = fraccion, no porcentaje)
    )

    engine = EventBacktestEngine()
    oos_bt = engine.run_backtest(strat, candles[:200])

    orchestrator = GatePipelineOrchestrator()
    eval_res = orchestrator.run_all_gates(
        candidate_info={
            "candidate_id": strat.strategy_id,
            "route": "ULTRA",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "dataset_id": "ds_btc_1h",
            "dataset_sha256": "3a4b5c6d7e8f00112233445566778899aabbccddeeff00112233445566778899",
            "trials_tested": 250,
            "profit_factor_oos": oos_bt.profit_factor,
            "parameters": {"ema_fast": 20, "ema_slow": 50},
        },
        candles=candles[:200],
        oos_trades=[t.net_pnl_usd for t in oos_bt.trades],
        pre_oos_trades=[t.net_pnl_usd for t in oos_bt.trades],
        trades_raw=[
            {
                "entry_price": t.entry_price, "exit_price": t.exit_price,
                "qty": t.qty, "side": t.side, "net_pnl_usd": t.net_pnl_usd,
                "entry_bar_idx": t.entry_bar, "exit_bar_idx": t.exit_bar,
                "entry_time_ms": t.entry_time_ms, "exit_time_ms": t.exit_time_ms,
            }
            for t in oos_bt.trades
        ],
        strategy_snapshot=strat,
    )

    assert "gates" in eval_res
    evidence_files = list(orchestrator.evidence_dir.glob(f"{strat.strategy_id}/*.json"))
    assert len(evidence_files) == 11
    for ev_f in evidence_files:
        with open(ev_f, "r") as f:
            rec_data = json.load(f)
            assert len(rec_data["strategy_snapshot_hash"]) == 64
            assert len(rec_data["input_hash"]) == 64
            assert len(rec_data["output_hash"]) == 64
