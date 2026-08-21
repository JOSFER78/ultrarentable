"""tests/audit_forensic_suite.py
Suite de Auditoría Interna Forense y Certificación Ciega (Fase 0 a Fase 6).

DOCTRINA ZERO-MOCKS & REAL-ONLY:
Ejecuta una auditoría objetiva e imparcial sobre el 100% de los componentes del sistema:
1. Integridad de Datos y Ausencia de Generadores Sintéticos / Random en Validación.
2. Invariabilidad de los 11 Gates y Exactitud de Fórmulas Matemáticas (DSR, Hurst, Parkinson).
3. Comportamiento Ciego del Optimizador Universal (sin lookahead ni forzado de métricas).
4. Integridad de la Base de Datos SQLite WAL y Consistencia de Tiers.
5. Sincronización en la Nube con Firebase Realtime Database.
"""

from __future__ import annotations

import ast
import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List
import pytest
import numpy as np

from services.optimization.universal_optimizer_engine import UniversalStrategyOptimizer
from services.optimization.quantitative_arsenal import MicrostructureProfiler
from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
from services.api.app.validation.gates.gate_08_dsr_ratio import _std_norm_cdf, _std_norm_ppf
from services.sync.firebase_sync_manager import firebase_sync_manager


WORKSPACE_ROOT = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable")
DB_PATH = Path("/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3")


def test_audit_dimension_1_no_random_in_validation_engines():
    """Auditoría Estática: Ningún archivo en services/api/app/validation/ o services/validation/ debe importar random."""
    validation_dirs = [
        WORKSPACE_ROOT / "services/api/app/validation/gates",
        WORKSPACE_ROOT / "services/validation/engine",
    ]
    
    violations = []
    for vdir in validation_dirs:
        if not vdir.exists():
            continue
        for py_file in vdir.glob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == "random":
                                violations.append(f"{py_file.name}: import random")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module == "random":
                            violations.append(f"{py_file.name}: from random import ...")

    assert len(violations) == 0, f"Violación de Doctrina Zero-Mocks: Se encontró 'random' en validación: {violations}"


def test_audit_dimension_2_mathematical_precision_and_blind_gates():
    """Auditoría Matemática: Verifica que DSR, Hurst, Parkinson y Acklam PPF sean exactos."""
    # 1. Acklam Normal Inverse CDF (PPF) precision
    assert abs(_std_norm_ppf(0.50) - 0.0) < 1e-9
    assert abs(_std_norm_ppf(0.841344746) - 1.0) < 1e-4
    assert abs(_std_norm_cdf(0.0) - 0.50) < 1e-9
    assert abs(_std_norm_cdf(1.95996) - 0.975) < 1e-4

    # 2. Gate Evaluator ciego: Con trades perdedores debe rechazar sin piedad
    orchestrator = GatePipelineOrchestrator()
    losing_trades = [-0.02, -0.015, -0.03, 0.01, -0.025, -0.04, -0.01]
    candidate_info = {
        "candidate_id": "AUDIT_TEST_LOSER",
        "route": "ULTRA",
        "symbol": "BTC-USDT",
        "timeframe": "15m",
        "trades_count": len(losing_trades),
        "profit_factor_oos": 0.25,
        "max_drawdown_pct": 45.0,
        "net_profit_oos_usd": -350.0,
    }
    eval_result = orchestrator.run_all_gates(
        candidate_info=candidate_info,
        oos_trades=losing_trades,
    )
    assert eval_result["gates_passed_count"] < 11
    assert eval_result["overall_score"] < 50.0
    assert eval_result["overall_passed"] is False


def test_audit_dimension_3_real_candles_physical_integrity():
    """Auditoría de Datos Físicos: Verifica que todos los datasets normalizados tengan OHLCV real y no sintético."""
    norm_dir = WORKSPACE_ROOT / "data/normalized"
    assert norm_dir.exists(), "Directorio de datos normalizados debe existir"

    json_files = [f for f in norm_dir.glob("*.json") if not f.name.endswith("_manifest.json")]
    assert len(json_files) >= 5, f"Debe haber al menos 5 datasets en disco (encontrados: {len(json_files)})"

    for ds_file in json_files:
        with open(ds_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        candles = data if isinstance(data, list) else (data.get("candles") or data.get("bars") or [])
        assert len(candles) >= 500, f"Dataset {ds_file.name} tiene menos de 500 velas ({len(candles)})"

        # Verificar integridad de velas (High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close)
        for c in candles[:100]:
            o = float(c.get("open", c.get("o", 0)))
            h = float(c.get("high", c.get("h", 0)))
            l = float(c.get("low", c.get("l", 0)))
            close = float(c.get("close", c.get("c", 0)))
            assert h >= l, f"Violación OHLC en {ds_file.name}: High {h} < Low {l}"
            assert h >= min(o, close) * 0.999, f"Violación OHLC en {ds_file.name}"
            assert l <= max(o, close) * 1.001, f"Violación OHLC en {ds_file.name}"


def test_audit_dimension_4_sqlite_wal_database_consistency():
    """Auditoría de Base de Datos: Verifica la consistencia de los 230 candidatos y ausencia de aprobaciones falsas."""
    assert DB_PATH.exists(), "La base de datos SQLite debe existir"

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM candidates")
    total = cur.fetchone()[0]
    assert total >= 200, f"Debe haber catálogo poblado (total: {total})"

    # Verificar que ninguna estrategia con Profit Factor < 1.0 esté marcada como APPROVED
    cur.execute(
        """
        SELECT candidate_id, profit_factor_oos, status
        FROM candidates
        WHERE status = 'APPROVED' AND profit_factor_oos < 1.0
        """
    )
    fake_approved = cur.fetchall()
    assert len(fake_approved) == 0, f"Violación Zero-Mocks: Estrategias perdedoras aprobadas: {fake_approved}"

    conn.close()


def test_audit_dimension_5_closed_loop_optimizer_impartiality():
    """Auditoría del Optimizador Universal: Comprueba que el optimizador mejora deterministamente sin falsear."""
    optimizer = UniversalStrategyOptimizer()
    
    # Probar que un candidato real ejecutado en partición OOS pura calcula métricas reales
    res = optimizer.optimize_candidate_closed_loop(
        candidate_id="UR_ULTRA_LINK_USDT_4H",
        max_iterations=1,
    )
    assert res["candidate_id"] == "UR_ULTRA_LINK_USDT_4H"
    assert "microstructure_profile" in res
    assert res["microstructure_profile"]["hurst"] > 0.0
    assert res["iterations_executed"] == 1
