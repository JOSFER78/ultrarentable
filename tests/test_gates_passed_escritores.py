"""tests/test_gates_passed_escritores.py — Auditoría con tests de la deuda W4.4.

Verifica que los escritores de persistencia en base de datos:
1. `DiscoveryValidationPipeline` (services/discovery/discovery_validation_pipeline.py)
2. `LegacyRevalidationService` (services/validation/legacy_revalidation_service.py)

Escriben el conteo real de compuertas superadas (`gates_passed`) en la columna `candidates.gates_passed`,
tanto para evaluaciones 11/11 (persiste 11) como para evaluaciones parciales 7/11 (persiste 7).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.discovery.discovery_validation_pipeline import DiscoveryValidationPipeline
from services.engine_version import CURRENT_ENGINE_VERSION
from services.validation.legacy_revalidation_service import LegacyRevalidationService

_CREATE_CANDIDATES_TABLE = """
    CREATE TABLE IF NOT EXISTS candidates (
        candidate_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        route TEXT DEFAULT 'FONDEO',
        symbol TEXT DEFAULT 'BTC-USDT',
        timeframe TEXT DEFAULT '1h',
        dataset_id TEXT,
        status TEXT DEFAULT 'INVESTIGACION_BTC',
        status_reason TEXT,
        tier TEXT DEFAULT 'TIER_3_RESEARCH',
        gates_passed INTEGER DEFAULT 0,
        net_profit_is REAL DEFAULT 0.0,
        trades_is INTEGER DEFAULT 0,
        profit_factor_is REAL DEFAULT 0.0,
        max_dd_is_pct REAL DEFAULT 0.0,
        net_profit_oos REAL DEFAULT 0.0,
        trades_oos INTEGER DEFAULT 0,
        profit_factor_oos REAL DEFAULT 0.0,
        max_dd_oos_pct REAL DEFAULT 0.0,
        ratio_oos_is REAL DEFAULT 0.0,
        wfo_pass_pct REAL,
        monte_carlo_score REAL,
        duration_info TEXT,
        scorecard_json TEXT,
        margin_call INTEGER DEFAULT 0,
        engine_version TEXT DEFAULT '5.3.0',
        validation_pipeline_version TEXT DEFAULT '5.3.0',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

_CREATE_AUDIT_EVENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS audit_events (
        event_id TEXT PRIMARY KEY,
        category TEXT DEFAULT 'SYSTEM',
        route TEXT DEFAULT 'SYSTEM',
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT DEFAULT 'INFO',
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""


@pytest.fixture
def env_temporal(tmp_path: Path):
    """Crea una base de datos SQLite temporal y un directorio de datos normalizados
    aislados para probar la persistencia de los escritores."""
    db_path = tmp_path / "candidates_test.db"
    data_dir = tmp_path / "normalized"
    data_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute(_CREATE_CANDIDATES_TABLE)
    conn.execute(_CREATE_AUDIT_EVENTS_TABLE)
    conn.commit()
    conn.close()

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    base_ts = now_ms - (300 * 4 * 3600 * 1000)
    step_ms = 4 * 3600 * 1000

    candles = []
    price = 5000.0
    for i in range(250):
        ts = base_ts + i * step_ms
        price += ((i % 5) - 2) * 10.0
        candles.append({
            "time": ts,
            "timestamp": ts,
            "timestamp_ms": ts,
            "open": price - 5.0,
            "high": price + 10.0,
            "low": price - 10.0,
            "close": price + 2.0,
            "volume": 100.0,
        })

    return SimpleNamespace(
        db_path=db_path,
        data_dir=data_dir,
        candles=candles,
        base_ts=base_ts,
    )


def _crear_mock_backtest(base_ts: int) -> SimpleNamespace:
    trade = SimpleNamespace(
        return_pct=1.0,
        entry_price=5000.0,
        exit_price=5050.0,
        qty=1.0,
        side="BUY",
        net_pnl_usd=50.0,
        r_multiple=1.5,
        equity_before_usd=50000.0,
        equity_after_usd=50050.0,
        entry_bar=10,
        exit_bar=20,
        entry_time_ms=base_ts,
        exit_time_ms=base_ts + 1000,
    )
    return SimpleNamespace(
        profit_factor=1.85,
        max_drawdown_pct=2.8,
        total_trades=20,
        net_profit_usd=1000.0,
        final_equity_usd=51000.0,
        win_rate_pct=65.0,
        trades=[trade] * 20,
    )


# ==============================================================================
# 1. Escritor: DiscoveryValidationPipeline
# ==============================================================================

def test_discovery_pipeline_persiste_gates_passed_11_de_11(env_temporal):
    """W4.4: DiscoveryValidationPipeline persiste gates_passed=11 cuando 11 gates superados."""
    ds_file = env_temporal.data_dir / "dataset_fondeo_ES_4h.json"
    ds_file.write_text(json.dumps(env_temporal.candles), encoding="utf-8")

    pipeline = DiscoveryValidationPipeline(
        db_path=env_temporal.db_path,
        data_dir=env_temporal.data_dir,
    )

    mock_bt = _crear_mock_backtest(env_temporal.base_ts)
    pipeline.backtest_engine.run_backtest = lambda *a, **kw: mock_bt
    pipeline.gates_orchestrator.run_all_gates = lambda **kw: {
        "gates_passed_count": 11,
        "overall_score": 97.5,
        "gates": [{"gate_id": i, "name": f"gate_{i}", "passed": True, "score": 97.5} for i in range(1, 12)],
        "gates_evaluation": {},
    }

    res = pipeline.process_dataset(str(ds_file))
    assert res is not None
    assert res.get("status") == "APPROVED_CURRENT_ENGINE"
    assert res.get("gates_passed_count") == 11

    conn = sqlite3.connect(str(env_temporal.db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT candidate_id, gates_passed, engine_version, status FROM candidates WHERE candidate_id = ?",
        (res["strategy_id"],),
    ).fetchone()
    conn.close()

    assert row is not None, "La candidata no fue persistida en base de datos"
    assert row["gates_passed"] == 11, (
        f"gates_passed={row['gates_passed']!r}, se esperaba 11 (bug W4.4)"
    )
    assert row["engine_version"] == CURRENT_ENGINE_VERSION


def test_discovery_pipeline_persiste_gates_passed_parcial_7_de_11(env_temporal):
    """W4.4: DiscoveryValidationPipeline persiste gates_passed=7 cuando 7 gates superados."""
    ds_file = env_temporal.data_dir / "dataset_fondeo_GC_4h.json"
    ds_file.write_text(json.dumps(env_temporal.candles), encoding="utf-8")

    pipeline = DiscoveryValidationPipeline(
        db_path=env_temporal.db_path,
        data_dir=env_temporal.data_dir,
    )

    mock_bt = _crear_mock_backtest(env_temporal.base_ts)
    pipeline.backtest_engine.run_backtest = lambda *a, **kw: mock_bt
    pipeline.gates_orchestrator.run_all_gates = lambda **kw: {
        "gates_passed_count": 7,
        "overall_score": 73.0,
        "gates": [{"gate_id": i, "name": f"gate_{i}", "passed": i <= 7, "score": 73.0} for i in range(1, 12)],
        "gates_evaluation": {},
    }

    res = pipeline.process_dataset(str(ds_file))
    assert res is not None
    assert res.get("gates_passed_count") == 7

    conn = sqlite3.connect(str(env_temporal.db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT candidate_id, gates_passed, engine_version FROM candidates WHERE candidate_id = ?",
        (res["strategy_id"],),
    ).fetchone()
    conn.close()

    assert row is not None, "La candidata no fue persistida en base de datos"
    assert row["gates_passed"] == 7, (
        f"gates_passed={row['gates_passed']!r}, se esperaba 7 (bug W4.4)"
    )


# ==============================================================================
# 2. Escritor: LegacyRevalidationService
# ==============================================================================

def test_legacy_revalidation_persiste_gates_passed_11_de_11(env_temporal):
    """W4.4: LegacyRevalidationService persiste gates_passed=11 cuando 11 gates superados."""
    ds_file = env_temporal.data_dir / "dukascopy_ES_4h_2026.json"
    ds_file.write_text(json.dumps(env_temporal.candles), encoding="utf-8")

    conn = sqlite3.connect(str(env_temporal.db_path))
    conn.execute(
        "INSERT INTO candidates (candidate_id, name, symbol, timeframe, route, status, engine_version) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("TEST_REVAL_11", "TEST_REVAL_11", "ES", "4h", "FONDEO", "TIER_3_RESEARCH", "5.3.0"),
    )
    conn.commit()
    conn.close()

    service = LegacyRevalidationService(
        db_path=env_temporal.db_path,
        data_dir=env_temporal.data_dir,
    )

    mock_bt = _crear_mock_backtest(env_temporal.base_ts)
    service.backtest_engine.run_backtest = lambda *a, **kw: mock_bt
    service.gates_orchestrator.run_all_gates = lambda **kw: {
        "gates_passed_count": 11,
        "overall_score": 96.0,
        "gates": [{"gate_id": i, "name": f"gate_{i}", "passed": True, "score": 96.0} for i in range(1, 12)],
        "gates_evaluation": {},
    }

    res = service.revalidate_single_candidate("TEST_REVAL_11")
    assert res.get("gates_passed") == 11

    conn = sqlite3.connect(str(env_temporal.db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT candidate_id, gates_passed, engine_version, status FROM candidates WHERE candidate_id = ?",
        ("TEST_REVAL_11",),
    ).fetchone()
    conn.close()

    assert row is not None, "La fila no fue encontrada tras revalidar"
    assert row["gates_passed"] == 11, (
        f"gates_passed={row['gates_passed']!r}, se esperaba 11 (bug W4.4)"
    )
    assert row["engine_version"] == CURRENT_ENGINE_VERSION


def test_legacy_revalidation_persiste_gates_passed_parcial_7_de_11(env_temporal):
    """W4.4: LegacyRevalidationService persiste gates_passed=7 cuando 7 gates superados."""
    ds_file = env_temporal.data_dir / "dukascopy_GC_4h_2026.json"
    ds_file.write_text(json.dumps(env_temporal.candles), encoding="utf-8")

    conn = sqlite3.connect(str(env_temporal.db_path))
    conn.execute(
        "INSERT INTO candidates (candidate_id, name, symbol, timeframe, route, status, engine_version) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("TEST_REVAL_7", "TEST_REVAL_7", "GC", "4h", "FONDEO", "TIER_3_RESEARCH", "5.3.0"),
    )
    conn.commit()
    conn.close()

    service = LegacyRevalidationService(
        db_path=env_temporal.db_path,
        data_dir=env_temporal.data_dir,
    )

    mock_bt = _crear_mock_backtest(env_temporal.base_ts)
    service.backtest_engine.run_backtest = lambda *a, **kw: mock_bt
    service.gates_orchestrator.run_all_gates = lambda **kw: {
        "gates_passed_count": 7,
        "overall_score": 72.0,
        "gates": [{"gate_id": i, "name": f"gate_{i}", "passed": i <= 7, "score": 72.0} for i in range(1, 12)],
        "gates_evaluation": {},
    }

    res = service.revalidate_single_candidate("TEST_REVAL_7")
    assert res.get("gates_passed") == 7

    conn = sqlite3.connect(str(env_temporal.db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT candidate_id, gates_passed, engine_version FROM candidates WHERE candidate_id = ?",
        ("TEST_REVAL_7",),
    ).fetchone()
    conn.close()

    assert row is not None, "La fila no fue encontrada tras revalidar"
    assert row["gates_passed"] == 7, (
        f"gates_passed={row['gates_passed']!r}, se esperaba 7 (bug W4.4)"
    )
