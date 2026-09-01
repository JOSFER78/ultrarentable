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


def test_gate_09_counts_effective_dof_for_new_archetype_families_5_14_0():
    """5.14.0 (F03.3): antes de esta corrección, las 4 familias EVENTO nuevas
    (reversion_atr, squeeze_breakout, session_momentum, streak_edge) colapsaban a 1 grado de
    libertad en services/discovery/effective_dof.py -- sus dimensiones viven en el dict
    anidado `archetype_params` (ver scripts/mine.py::_arquetipos_5_14_0_configs, p_set real
    de la búsqueda), fuera del conjunto `base` que solo conoce ema_fast/ema_slow/sl_atr_mult/
    tp_atr_mult/rsi_period. Un DoF=1 infla artificialmente el ratio trades/parámetro y deja
    pasar candidatos sobreajustados por el Gate 9 como si fueran robustos."""
    from services.discovery.effective_dof import count_effective_parameters

    reversion_atr_params = {
        "archetype": "REVERSION_ATR", "ema_fast": 20, "ema_slow": 50,
        "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "risk_pct": 0.05,
        "archetype_params": {"ema_ancla": 50, "banda_atr_mult": 2.0},
    }
    # +1 por risk_pct (2026-08-31): scripts/mine.py barre 4 valores de riesgo tambien para
    # estas 4 familias -- es grado de libertad real via compounding sobre PF/DD.
    assert count_effective_parameters(reversion_atr_params) == 4  # ema_ancla, banda_atr_mult, sl_atr_mult, risk_pct

    squeeze_params = {
        "archetype": "SQUEEZE_BREAKOUT", "ema_fast": 20, "ema_slow": 50,
        "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "risk_pct": 0.05,
        "archetype_params": {"squeeze_pct": 20.0, "squeeze_lookback": 50, "breakout_lookback": 20},
    }
    assert count_effective_parameters(squeeze_params) == 6  # +1 risk_pct

    session_params = {
        "archetype": "SESSION_MOMENTUM", "ema_fast": 20, "ema_slow": 50,
        "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "risk_pct": 0.05,
        "archetype_params": {"ancla_horas": 1, "ema_pull": 20, "cierre_eod": True},
    }
    assert count_effective_parameters(session_params) == 6  # cierre_eod cuenta + risk_pct

    streak_params = {
        "archetype": "STREAK_EDGE", "ema_fast": 20, "ema_slow": 50,
        "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "risk_pct": 0.05,
        "archetype_params": {"n_racha": 3, "modo": "continuacion"},
    }
    assert count_effective_parameters(streak_params) == 5  # modo cuenta + risk_pct

    # No-regresion: arquetipos anteriores a 5.14.0 no cambian de LOGICA de conteo (mismo
    # arbol generico de indicadores); risk_pct incluido porque los blueprints reales de
    # scripts/mine.py lo llevan tambien para estos arquetipos (ver cfg lineas ~311-319).
    trend_params = {
        "archetype": "TREND_FOLLOWING", "ema_fast": 20, "ema_slow": 50,
        "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "risk_pct": 0.02,
    }
    assert count_effective_parameters(trend_params) == 5  # +1 risk_pct

    momentum_breakout_params = {
        "archetype": "MOMENTUM_BREAKOUT", "ema_fast": 20, "ema_slow": 50,
        "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "rsi_period": 14,
        "rsi_threshold_long": 55.0, "rsi_threshold_short": 45.0, "risk_pct": 0.02,
    }
    assert count_effective_parameters(momentum_breakout_params) == 8  # +1 risk_pct


def test_gate_09_perturbs_real_archetype_params_neighborhood_5_14_0():
    """5.14.0 (F03.3): sin este fix, el re-backtest de vecindario del Gate 9 nunca pasaba
    `archetype_params` a generate_candidate_blueprint -- los 4 deltas (±10%/±20%) generaban
    SIEMPRE el mismo blueprint por defecto (ema_ancla=50, banda_atr_mult=2.0...) para las
    familias EVENTO nuevas: el test de estabilidad de vecindario era un no-op silencioso.
    Verifica en directo que _perturb_archetype_params mueve las dimensiones reales por
    familia y dejar las categóricas/booleanas (modo, cierre_eod) fijas."""
    from services.api.app.validation.gates.gate_09_novelty_antifit import _perturb_archetype_params

    base_reversion = {"ema_ancla": 50, "banda_atr_mult": 2.0}
    pert_up = _perturb_archetype_params(base_reversion, "REVERSION_ATR", 0.20)
    pert_down = _perturb_archetype_params(base_reversion, "REVERSION_ATR", -0.20)
    assert pert_up["ema_ancla"] == 60 and pert_down["ema_ancla"] == 40
    assert pert_up["banda_atr_mult"] == 2.4 and pert_down["banda_atr_mult"] == 1.6
    assert base_reversion == {"ema_ancla": 50, "banda_atr_mult": 2.0}  # no muta el original

    base_streak = {"n_racha": 4, "modo": "reversion"}
    pert_streak = _perturb_archetype_params(base_streak, "STREAK_EDGE", 0.20)
    assert pert_streak["n_racha"] == 5  # paso minimo de 1 entero: 4 + max(1, round(4*0.2)) = 5
    assert pert_streak["modo"] == "reversion"  # categorico: no tiene vecindario multiplicativo

    base_session = {"ancla_horas": 1, "ema_pull": 20, "cierre_eod": True}
    pert_session_down = _perturb_archetype_params(base_session, "SESSION_MOMENTUM", -0.20)
    assert pert_session_down["ancla_horas"] == 1  # piso minimo (round(1*0.8)=1, floor=1)
    assert pert_session_down["ema_pull"] == 16
    assert pert_session_down["cierre_eod"] is True  # booleano: se mantiene fijo

    base_squeeze = {"squeeze_pct": 90.0, "squeeze_lookback": 50, "breakout_lookback": 20}
    pert_squeeze_up = _perturb_archetype_params(base_squeeze, "SQUEEZE_BREAKOUT", 0.20)
    assert pert_squeeze_up["squeeze_pct"] == 99.0  # acotado al techo de percentil (0,100)


def test_gate_09_perturbation_never_noop_on_real_archetype_grid_5_14_0():
    """Auditoría orquestador 2026-08-31: `_perturb_archetype_params` perturbaba enteros con
    `base_val * (1+delta) -> round()`, que se anula en valores pequeños (n_racha=3,
    delta=-0.10 -> 2.7 -> round=3 == base): el vecindario perturbado clonaba el candidato
    base y el Gate 9 medía la estabilidad del candidato contra sí mismo, inflándola. Recorre
    los valores REALES de la rejilla de scripts/mine.py::_arquetipos_5_14_0_configs
    (ema_ancla, squeeze_lookback/breakout_lookback, ancla_horas/ema_pull, n_racha) con los 4
    deltas de perturbación de Gate09NoveltyAntiFit.evaluate y exige que ninguna dimensión
    entera quede idéntica a la base tras perturbar.

    Excepción legítima documentada (no es un bug): ancla_horas=1 con floor=1 y delta
    negativo -- no existe vecindario físico por debajo del mínimo permitido, así que el
    clamp al floor coincide con la base y el test lo contempla en vez de fallar."""
    from services.api.app.validation.gates.gate_09_novelty_antifit import (
        _perturb_archetype_params,
        _ARCHETYPE_NEIGHBORHOOD_SPEC,
    )

    perturbation_deltas = [-0.20, -0.10, 0.10, 0.20]  # mismos deltas que Gate09NoveltyAntiFit.evaluate

    # Valores reales de la rejilla por familia (scripts/mine.py::_arquetipos_5_14_0_configs,
    # bloques A-D, ~lineas 222-284). Solo dimensiones enteras (las float no sufren el bug).
    real_grid_cases = {
        "REVERSION_ATR": [{"ema_ancla": v} for v in (20, 50, 100)],
        "SQUEEZE_BREAKOUT": [
            {"squeeze_lookback": lb, "breakout_lookback": bl}
            for lb in (50, 100) for bl in (10, 20)
        ],
        "SESSION_MOMENTUM": [
            {"ancla_horas": ah, "ema_pull": ep} for ah in (1, 2, 4) for ep in (20, 50)
        ],
        "STREAK_EDGE": [{"n_racha": v} for v in (3, 4, 5)],
    }

    checked = 0
    for archetype, cases in real_grid_cases.items():
        spec = _ARCHETYPE_NEIGHBORHOOD_SPEC[archetype]
        for base_case in cases:
            for delta in perturbation_deltas:
                perturbed = _perturb_archetype_params(base_case, archetype, delta)
                for key, base_val in base_case.items():
                    floor = spec[key][1]
                    checked += 1
                    if delta < 0 and base_val <= floor:
                        # Piso minimo fisico: no hay vecindario por debajo, el clamp
                        # legitimamente reproduce la base (p.ej. ancla_horas=1).
                        assert perturbed[key] == floor
                        continue
                    assert perturbed[key] != base_val, (
                        f"{archetype}.{key}={base_val} delta={delta} -> perturbado "
                        f"identico a la base (no-op de vecindario)"
                    )
    assert checked >= 44  # cobertura minima: no se vacio silenciosamente la rejilla


def test_gate_09_evaluates_new_archetype_family_end_to_end_with_real_data():
    """5.14.0 (F03.3): integracion real (zero-mocks) -- construye un blueprint REVERSION_ATR
    con UltraDiscoveryEngine y vuelve a evaluarlo con el Gate 9 físico sobre velas reales de
    BTCUSDT 1h. Antes de este fix esto se colaba con DoF=1 (ver test de arriba) y con un
    vecindario perturbado que era un clon exacto del candidato base en las 4 iteraciones."""
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_btcusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)
    candles = candles[:3000]

    ultra_discovery = UltraDiscoveryEngine()
    strat = ultra_discovery.generate_candidate_blueprint(
        strategy_id="strat_rt_reversion_atr",
        symbol="BTCUSDT",
        timeframe="1h",
        dataset_id="ds_btc_1h",
        dataset_sha256="sha_rt_arch",
        risk_pct=0.05,
        sl_atr_mult=2.0,
        tp_atr_mult=6.0,
        archetype="REVERSION_ATR",
        archetype_params={"ema_ancla": 50, "banda_atr_mult": 2.0},
    )
    assert strat.archetype_params == {"ema_ancla": 50, "banda_atr_mult": 2.0}

    g9 = Gate09NoveltyAntiFit()
    res = g9.evaluate(
        parameters={
            "archetype": "REVERSION_ATR", "ema_fast": 20, "ema_slow": 50,
            "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "risk_pct": 0.05,
            "archetype_params": {"ema_ancla": 50, "banda_atr_mult": 2.0},
        },
        trades_count=50,
        oos_pf=1.5,
        candles=candles,
        strategy_snapshot=strat,
        is_ultra=True,
    )

    assert res["evidence"]["rebacktest_performed"] is True
    assert res["evidence"]["parameters_count"] == 4  # ema_ancla, banda_atr_mult, sl_atr_mult, risk_pct
    assert len(res["evidence"]["perturbed_neighborhood_pfs"]) == 4


def test_gate_09_counts_effective_dof_for_new_archetype_families_5_17_0():
    """5.17.0 (F03.3 cont., CUELLO 6): opening_range_breakout y vwap_reversion son familias
    EVENTO nuevas para futuros intradía de índice (misma arquitectura que las 4 de 5.14.0:
    dimensiones reales en `archetype_params`, fuera del `base` genérico). Sin registrar sus
    claves exactas en services/discovery/effective_dof.py, colapsarían a DoF=1 igual que el
    bug original de 5.14.0 -- error más peligroso posible aquí: infla el DoF ratio del Gate 9
    y deja pasar sobreajuste."""
    from services.discovery.effective_dof import count_effective_parameters

    orb_params = {
        "archetype": "OPENING_RANGE_BREAKOUT", "ema_fast": 20, "ema_slow": 50,
        "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "risk_pct": 0.02,
        "archetype_params": {"or_minutes": 30},
    }
    assert count_effective_parameters(orb_params) == 4  # or_minutes, sl_atr_mult, tp_atr_mult, risk_pct

    vwap_params = {
        "archetype": "VWAP_REVERSION", "ema_fast": 20, "ema_slow": 50,
        "sl_atr_mult": 2.0, "tp_atr_mult": 6.0, "risk_pct": 0.02,
        "archetype_params": {"vwap_dev_atr_mult": 1.5},
    }
    # tp_atr_mult NO cuenta: es placeholder inerte (TP dinamico = VWAP vivo, ver
    # event_backtest_engine.py rama VWAP_REVERSION del bloque "TP DINAMICO").
    assert count_effective_parameters(vwap_params) == 3  # vwap_dev_atr_mult, sl_atr_mult, risk_pct


def test_gate_09_perturbation_never_noop_on_real_archetype_grid_5_17_0():
    """Mismo ataque adversarial que test_gate_09_perturbation_never_noop_on_real_archetype_grid_
    5_14_0, aplicado a la rejilla REAL de opening_range_breakout/vwap_reversion
    (scripts/mine.py::_arquetipos_5_17_0_configs): recorre cada valor del grid x los 4 deltas
    de Gate09NoveltyAntiFit.evaluate (±10%/±20%) y exige que la dimension perturbada difiera
    de la base -- si no, el test de estabilidad de vecindario del Gate 9 seria un no-op
    silencioso para estos 2 arquetipos nuevos."""
    from services.api.app.validation.gates.gate_09_novelty_antifit import (
        _perturb_archetype_params,
        _ARCHETYPE_NEIGHBORHOOD_SPEC,
    )

    perturbation_deltas = [-0.20, -0.10, 0.10, 0.20]

    real_grid_cases = {
        "OPENING_RANGE_BREAKOUT": [{"or_minutes": v} for v in (15, 30, 60)],
        "VWAP_REVERSION": [{"vwap_dev_atr_mult": v} for v in (1.0, 1.5, 2.0)],
    }

    checked = 0
    for archetype, cases in real_grid_cases.items():
        spec = _ARCHETYPE_NEIGHBORHOOD_SPEC[archetype]
        for base_case in cases:
            for delta in perturbation_deltas:
                perturbed = _perturb_archetype_params(base_case, archetype, delta)
                for key, base_val in base_case.items():
                    floor = spec[key][1]
                    checked += 1
                    if delta < 0 and base_val <= floor:
                        assert perturbed[key] == floor
                        continue
                    assert perturbed[key] != base_val, (
                        f"{archetype}.{key}={base_val} delta={delta} -> perturbado "
                        f"identico a la base (no-op de vecindario)"
                    )
    assert checked == 24  # 3 valores x 4 deltas x 2 arquetipos: cobertura completa del grid real


def test_gate_09_evaluates_opening_range_breakout_and_vwap_reversion_end_to_end_with_real_data():
    """5.17.0 (F03.3 cont., CUELLO 6): integracion real (zero-mocks) -- construye blueprints
    OPENING_RANGE_BREAKOUT y VWAP_REVERSION con FundingDiscoveryEngine (ruta FONDEO, la unica
    que los genera: is_ultra=True devuelve archetype_params=None y estos arquetipos son
    inertes fuera de FONDEO) y los evalua con el Gate 9 fisico sobre velas reales de
    USA500IDXUSD (proxy Dukascopy de ES) 5m, ~63 dias de sesion. Confirma que ambos arquetipos
    generan operaciones reales (no solo eventos contados) y que el vecindario perturbado del
    Gate 9 se re-ejecuta con archetype_params correctos, no con el default silencioso."""
    from services.discovery.funding_discovery import FundingDiscoveryEngine

    sample_file = (
        "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/"
        "ds_dukascopy_usa500idxusd_5m_1704150000000_1711929300000.json"
    )
    with open(sample_file, "r", encoding="utf-8") as f:
        raw = json.load(f)
    candles = raw["bars"]
    # El motor solo lee `timestamp_ms`/`timestamp`/`time`/`datetime`; el dataset normalizado
    # guarda `timestamp_utc_ms` -- mismo puente que scripts/mine.py::_normalizar_timestamps y
    # tests/test_engine_prop_firm_floating_equity.py::_load_candles_con_timestamp_real. Critico
    # para estos 2 arquetipos: sin `timestamp_ms` correcto, _is_in_session_window no puede
    # resolver el dia/hora UTC y el rango de apertura / VWAP de sesion no se ancla a nada.
    for c in candles:
        if "timestamp_ms" not in c and "timestamp_utc_ms" in c:
            c["timestamp_ms"] = int(c["timestamp_utc_ms"])

    disc_f = FundingDiscoveryEngine()
    g9 = Gate09NoveltyAntiFit()

    casos = [
        ("OPENING_RANGE_BREAKOUT", {"or_minutes": 15}, 1.5, 4.0, 4),
        ("VWAP_REVERSION", {"vwap_dev_atr_mult": 1.0}, 1.5, 4.5, 3),
    ]
    for archetype, archetype_params, sl, tp, expected_dof in casos:
        strat = disc_f.generate_candidate_blueprint(
            strategy_id=f"strat_rt_{archetype.lower()}",
            symbol="MES",
            timeframe="5m",
            dataset_id="ds_dukascopy_usa500idxusd_5m",
            dataset_sha256="sha_rt_arch_5_17_0",
            sl_atr_mult=sl,
            tp_atr_mult=tp,
            risk_per_trade_pct=0.005,
            archetype=archetype,
            archetype_params=archetype_params,
        )
        assert strat.archetype_params == archetype_params

        res = g9.evaluate(
            parameters={
                "archetype": archetype, "ema_fast": 20, "ema_slow": 50,
                "sl_atr_mult": sl, "tp_atr_mult": tp, "risk_pct": 0.005,
                "archetype_params": archetype_params,
            },
            trades_count=100,
            oos_pf=1.2,
            candles=candles,
            strategy_snapshot=strat,
            is_ultra=False,
        )
        assert res["evidence"]["rebacktest_performed"] is True
        assert res["evidence"]["parameters_count"] == expected_dof
        assert len(res["evidence"]["perturbed_neighborhood_pfs"]) == 4

        # Backtest directo (fuera del Gate 9) para confirmar volumen real de operaciones sobre
        # el mismo tramo de 63 dias de sesion usado en el diseno (ver
        # orchestration/reviews/diseno_arquetipos_5_17_0.md): >=50 operaciones en ~63 dias
        # confirma que el mecanismo dispara con la frecuencia proyectada, no solo que compila.
        bt_engine = EventBacktestEngine()
        bt = bt_engine.run_backtest(strat, candles, initial_capital_usd=50000.0)
        assert bt.total_trades >= 50, (
            f"{archetype}: solo {bt.total_trades} operaciones en 63 dias de sesion -- muy por "
            f"debajo del volumen proyectado en el diseno, revisar el anclaje de sesion"
        )
