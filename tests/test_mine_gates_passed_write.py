"""tests/test_mine_gates_passed_write.py — W4.4 (AG-C): regresión de "gates_passed=0" en el
escritor de scripts/mine.py::save_certified_candidate_to_db.

Diagnóstico (AG-C, 2026-09-01): se rastreó el flujo completo del conteo de gates superados en
los tres escritores nombrados por la tarea (scripts/mine.py, discovery_validation_pipeline.py,
legacy_revalidation_service.py) línea a línea, incluyendo el `INSERT`/`UPDATE` SQL exacto y el
binding posicional de cada valor. Los tres ya leen `gates_eval.get("gates_passed_count", 0)`
(la clave real que devuelve GatePipelineOrchestrator.run_all_gates, services/api/app/
validation/gates/gate_pipeline_orchestrator.py:256) y la vinculan correctamente a la columna
`gates_passed`. `git blame` confirma que los tres puntos de escritura fueron tocados por el
MISMO commit (31352ae86c, 2026-08-31 18:22:25, anterior a esta tarea) que ya corrigió este
bug exacto. No se encontró ninguna ruta de código viva en la que un candidato certificado
11/11 se persista con gates_passed=0.

Este test es el "test unitario sobre la función de escritura con un objeto de resultado
construido explícitamente" que pide la aceptación de W4.4 cuando no hay datos reales
disponibles (no hay velas en esta copia, ver CLAUDE.md de la tarea) -- bloquea el
comportamiento correcto como regresión: si algún cambio futuro vuelve a romper el binding,
este test falla.

No usa la base de datos real (services.api.app.config.STATE_DB_PATH, fuera del repo):
monkeypatchea scripts.mine.get_db_connection para apuntar a un SQLite temporal con el mismo
esquema que scripts/normalize_database_candidates.py define para la tabla `candidates`.
"""
from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace

import pytest

from scripts.mine import save_certified_candidate_to_db
from services.engine_version import CURRENT_ENGINE_VERSION

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


@pytest.fixture
def db_temporal(tmp_path, monkeypatch):
    """SQLite temporal con el esquema real de `candidates` (scripts/normalize_database_candidates.py),
    y scripts.mine.get_db_connection() apuntando a él en vez de a la BD canónica real."""
    import scripts.mine as mine

    db_path = tmp_path / "candidates_test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(_CREATE_CANDIDATES_TABLE)
    conn.commit()
    conn.close()

    def _get_db_connection_temporal() -> sqlite3.Connection:
        c = sqlite3.connect(str(db_path))
        c.execute("PRAGMA journal_mode=WAL;")
        return c

    monkeypatch.setattr(mine, "get_db_connection", _get_db_connection_temporal)
    return db_path


def _construir_backtest_result(*, trades: int, pf: float, dd_pct: float, net_profit: float) -> SimpleNamespace:
    """Objeto de resultado de backtest construido EXPLÍCITAMENTE con los campos que
    save_certified_candidate_to_db lee (is_bt/oos_bt) -- esto es un test de la FUNCIÓN de
    escritura, no un dato de mercado inventado: ningún valor aquí pretende ser una operación
    real, son los campos mínimos que el escritor necesita para construir la fila SQL."""
    return SimpleNamespace(
        net_profit_usd=net_profit,
        total_trades=trades,
        profit_factor=pf,
        max_drawdown_pct=dd_pct,
    )


def test_fila_certificada_11_de_11_persiste_gates_passed_igual_a_11(db_temporal):
    """Caso de aceptación W4.4: una candidata con los 11 gates superados debe reflejar
    gates_passed=11 en la fila persistida -- no 0."""
    snapshot = SimpleNamespace(strategy_id="TEST_STRAT_11_11")
    is_bt = _construir_backtest_result(trades=180, pf=1.9, dd_pct=3.1, net_profit=5200.0)
    oos_bt = _construir_backtest_result(trades=210, pf=1.55, dd_pct=3.8, net_profit=4100.0)
    scorecard_payload = {"gates_passed_count": 11, "overall_score": 97.4}

    guardado = save_certified_candidate_to_db(
        snapshot=snapshot,
        route="fondeo",
        symbol="es",
        timeframe="4h",
        dataset_id="ds_test_11_11",
        is_bt=is_bt,
        oos_bt=oos_bt,
        scorecard_payload=scorecard_payload,
        certified_at_iso="2026-09-01T00:00:00+00:00",
        gates_passed=11,
        tier="TIER_1_CERTIFIED",
    )
    assert guardado is True

    conn = sqlite3.connect(str(db_temporal))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT gates_passed, tier, status, engine_version FROM candidates WHERE candidate_id = ?",
        ("TEST_STRAT_11_11",),
    ).fetchone()
    conn.close()

    assert row is not None, "la fila no se persistió"
    assert row["gates_passed"] == 11, (
        f"gates_passed persistido = {row['gates_passed']!r}, se esperaba 11 (bug W4.4: "
        f"conteo real de gates superados no se escribe)"
    )
    assert row["tier"] == "TIER_1_CERTIFIED"
    assert row["status"] == "APPROVED_CURRENT_ENGINE"
    assert row["engine_version"] == CURRENT_ENGINE_VERSION


def test_fila_con_gates_parciales_persiste_el_numero_real_no_cero(db_temporal):
    """Regresión directa del bug descrito: un conteo parcial (p.ej. 7) debe reflejarse tal
    cual, nunca colapsar a 0."""
    snapshot = SimpleNamespace(strategy_id="TEST_STRAT_PARCIAL")
    is_bt = _construir_backtest_result(trades=120, pf=1.3, dd_pct=4.0, net_profit=900.0)
    oos_bt = _construir_backtest_result(trades=140, pf=1.15, dd_pct=4.4, net_profit=600.0)

    guardado = save_certified_candidate_to_db(
        snapshot=snapshot,
        route="fondeo",
        symbol="gc",
        timeframe="4h",
        dataset_id="ds_test_parcial",
        is_bt=is_bt,
        oos_bt=oos_bt,
        scorecard_payload={"gates_passed_count": 7},
        certified_at_iso="2026-09-01T00:00:00+00:00",
        gates_passed=7,
        tier="TIER_3_INCUBATOR",
    )
    assert guardado is True

    conn = sqlite3.connect(str(db_temporal))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT gates_passed FROM candidates WHERE candidate_id = ?",
        ("TEST_STRAT_PARCIAL",),
    ).fetchone()
    conn.close()

    assert row["gates_passed"] == 7
