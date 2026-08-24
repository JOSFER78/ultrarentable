"""tests/test_candidates_and_real_data_routers_audit.py
Test suite verificando la erradicación estricta de fallbacks cuantitativos,
cálculos exactos de Retorno Acumulado / CAGR geométrica, deduplicación y normalización de timeframes.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_repo_root = str(Path(__file__).absolute().parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from services.api.app.api.candidates_router import (
    candidates_router,
    normalize_timeframe,
    compute_financial_metrics,
    resolve_strategy_sha256,
)
from services.api.app.api.real_data_router import router as real_data_router
from services.api.app.db.database import get_db, SessionLocal, CandidateModel, StrategyModel


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    app_test = FastAPI()
    app_test.include_router(candidates_router, prefix="/api/v1")
    app_test.include_router(real_data_router, prefix="/api/v2")
    return TestClient(app_test, raise_server_exceptions=True)


def test_normalize_timeframe():
    assert normalize_timeframe("1H") == "1h"
    assert normalize_timeframe("H1") == "1h"
    assert normalize_timeframe("4H") == "4h"
    assert normalize_timeframe("H4") == "4h"
    assert normalize_timeframe("15M") == "15m"
    assert normalize_timeframe("M15") == "15m"
    assert normalize_timeframe("5m") == "5m"
    assert normalize_timeframe("1m") == "1m"
    assert normalize_timeframe("1D") == "1d"
    assert normalize_timeframe("60m") == "1h"
    assert normalize_timeframe(None) == "1h"


def test_financial_metrics_exact_formulas():
    # Caso estándar: base 1000 USD, net_profit_oos 500 USD, oos_months 6.0
    # final_equity = 1500 USD
    # cumulative_return_pct = (1500 - 1000) / 1000 * 100 = 50.0%
    # growth_factor = 1.5
    # CAGR = (1.5 ** (12 / 6.0) - 1.0) * 100 = (2.25 - 1.0) * 100 = 125.0%
    fin = compute_financial_metrics(
        net_profit_oos=500.0,
        initial_capital=1000.0,
        oos_months=6.0,
    )
    assert fin["base_capital_usd"] == 1000.0
    assert fin["final_equity_usd"] == 1500.0
    assert fin["cumulative_return_pct"] == 50.0
    assert fin["annualized_cagr_pct"] == 125.0
    assert fin["is_anomalous"] is False


def test_financial_metrics_anomaly_detection():
    # Caso anómalo: retorno > 5000%
    fin = compute_financial_metrics(
        net_profit_oos=60000.0,
        initial_capital=1000.0,
        oos_months=1.0,
    )
    assert fin["cumulative_return_pct"] == 6000.0
    assert fin["is_anomalous"] is True


def test_resolve_strategy_sha256_length_and_format():
    # Sin scorecard: cálculo determinista de 64 caracteres hex
    sha = resolve_strategy_sha256("CAND_001", "Strat A", "BTC-USDT", "1h", "ULTRA")
    assert len(sha) == 64
    assert all(c in "0123456789abcdef" for c in sha)
    assert not sha.startswith("hash_")
    assert not sha.startswith("sha256_")

    # Con scorecard real
    real_sig = "a" * 64
    sha_sc = resolve_strategy_sha256("CAND_002", sc={"bundle_signature_sha256": real_sig})
    assert sha_sc == real_sig


def test_candidates_endpoints_no_fallbacks(client, db_session: Session):
    # Insertar candidato de prueba sin métricas de robustez para validar que devuelve None
    test_id = "TEST_CANDIDATE_NO_FALLBACKS"
    db_session.query(CandidateModel).filter(CandidateModel.candidate_id == test_id).delete()
    
    cand = CandidateModel(
        candidate_id=test_id,
        name="Test No Fallbacks",
        route="ULTRA",
        symbol="ETH-USDT",
        timeframe="15m",
        net_profit_is=200.0,
        net_profit_oos=300.0,
        trades_is=20,
        trades_oos=30,
        profit_factor_is=1.8,
        profit_factor_oos=1.9,
        max_dd_is_pct=5.0,
        max_dd_oos_pct=6.0,
        wfo_pass_pct=None,      # Debe retornar None, nunca 80.0
        monte_carlo_score=None, # Debe retornar None, nunca 85.0
        scorecard_json=json.dumps({
            "is_certified": True,
            "gates_passed_count": 11,
            "initial_capital_usd": 1000.0,
            "duration_info": {"oos_months": 3.0, "total_bars": 8640},
            # max_dd_realized_pct NO presente -> debe retornar None, nunca 6.0 * 0.85
        }),
    )
    cand.status = "APPROVED"
    db_session.add(cand)
    db_session.commit()

    # 1. Probar GET /api/v1/candidates/{test_id}
    res = client.get(f"/api/v1/candidates/{test_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == test_id
    assert data["timeframe"] == "15m"
    assert data["max_dd_realized_pct"] is None  # Erradicado fallback 0.85
    assert data["metrics"]["out_of_sample"]["max_dd_realized_pct"] is None
    assert data["metrics"]["anti_overfit"]["wfo_pass_pct"] is None
    assert data["metrics"]["anti_overfit"]["monte_carlo_score"] is None
    assert len(data["strategy_sha256"]) == 64

    # 2. Probar GET /api/v2/candidates/approved
    res_app = client.get("/api/v2/candidates/approved?symbol=ETH-USDT")
    assert res_app.status_code == 200
    app_data = res_app.json()
    matching = [c for c in app_data["candidates"] if c["candidate_id"] == test_id]
    assert len(matching) == 1
    c_out = matching[0]
    assert c_out["wfe_pct"] is None             # Erradicado fallback 80.0
    assert c_out["mc_robustness_score"] is None # Erradicado fallback 85.0
    assert c_out["max_dd_realized_pct"] is None # Erradicado fallback 0.85
    assert len(c_out["sha256"]) == 64
    assert not c_out["sha256"].startswith("hash_")

    # Limpieza
    db_session.query(CandidateModel).filter(CandidateModel.candidate_id == test_id).delete()
    db_session.commit()


def test_anomalous_candidate_gets_anomaly_review(client, db_session: Session):
    # Insertar candidato con rentabilidad extrema (> 5000%)
    test_id = "TEST_CANDIDATE_ANOMALOUS"
    db_session.query(CandidateModel).filter(CandidateModel.candidate_id == test_id).delete()
    
    cand = CandidateModel(
        candidate_id=test_id,
        name="Test Anomalous Strat",
        route="FONDEO",
        symbol="NQ",
        timeframe="1h",
        net_profit_oos=5000000.0, # 5M USD en 50K -> 10000% retorno
        trades_oos=10,
        scorecard_json=json.dumps({
            "is_certified": True,
            "gates_passed_count": 11,
            "initial_capital_usd": 50000.0,
            "duration_info": {"oos_months": 1.0, "total_bars": 720},
        }),
    )
    cand.status = "APPROVED"
    db_session.add(cand)
    db_session.commit()

    res = client.get(f"/api/v1/candidates/{test_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ANOMALY_REVIEW"  # Asignado estado de revisión por anomalía

    # Limpieza
    db_session.query(CandidateModel).filter(CandidateModel.candidate_id == test_id).delete()
    db_session.commit()


if __name__ == "__main__":
    db = SessionLocal()
    app_t = FastAPI()
    app_t.include_router(candidates_router, prefix="/api/v1")
    app_t.include_router(real_data_router, prefix="/api/v2")
    c = TestClient(app_t, raise_server_exceptions=True)

    print("Running test_normalize_timeframe...")
    test_normalize_timeframe()
    print("PASS: test_normalize_timeframe")

    print("Running test_financial_metrics_exact_formulas...")
    test_financial_metrics_exact_formulas()
    print("PASS: test_financial_metrics_exact_formulas")

    print("Running test_financial_metrics_anomaly_detection...")
    test_financial_metrics_anomaly_detection()
    print("PASS: test_financial_metrics_anomaly_detection")

    print("Running test_resolve_strategy_sha256_length_and_format...")
    test_resolve_strategy_sha256_length_and_format()
    print("PASS: test_resolve_strategy_sha256_length_and_format")

    print("Running test_candidates_endpoints_no_fallbacks...")
    test_candidates_endpoints_no_fallbacks(c, db)
    print("PASS: test_candidates_endpoints_no_fallbacks")

    print("Running test_anomalous_candidate_gets_anomaly_review...")
    test_anomalous_candidate_gets_anomaly_review(c, db)
    print("PASS: test_anomalous_candidate_gets_anomaly_review")

    db.close()
    print("\n>>> ALL TESTS IN AUDIT SUITE PASSED PERFECTLY! <<<")
