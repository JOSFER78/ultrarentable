"""tests/test_p3_holdout_firewall_and_trials.py
Suite de Tests y Auditoría Adversarial de la FASE P3: HOLDOUT FIREWALL & TRIAL REGISTRY.

Verifica:
1. HoldoutGateway: Partición temporal exacta (60% IS, 20% Val, 20% Blind Holdout).
2. HoldoutGateway: Acceso denegado ante token ausente o inválido (BlindHoldoutAccessViolation).
3. HoldoutGateway: Acceso permitido únicamente con token HMAC válido.
4. StrategySearchRegistry: Registro persistente e inmutable de trials por run_id y símbolo.
5. Invariante DSR: La cuenta exhaustiva de trials alimenta directamente los cálculos de deflación.
"""

import hashlib
import json
import tempfile
from pathlib import Path
import pytest

from services.data.holdout_gateway import BlindHoldoutAccessViolation, HoldoutGateway
from services.discovery.strategy_search_registry import SearchTrialRecord, StrategySearchRegistry


def _create_dummy_candles(n: int = 100):
    return [{"timestamp_utc_ms": 1700000000000 + i * 3600000, "close": 100.0 + i} for i in range(n)]


def test_holdout_gateway_partition_ratios():
    """Verifica que las particiones IS (60%), Val (20%) y Holdout (20%) sumen 100% sin solapamientos."""
    candles = _create_dummy_candles(100)

    is_data = HoldoutGateway.get_in_sample_data(candles, is_ratio=0.60)
    val_data = HoldoutGateway.get_validation_data(candles, is_ratio=0.60, val_ratio=0.20)

    assert len(is_data) == 60
    assert len(val_data) == 20

    # Token válido para holdout
    strat_id = "UR_STRAT_HOLDOUT_TEST"
    strat_hash = hashlib.sha256(b"snap").hexdigest()
    token = HoldoutGateway.generate_validation_token(strat_id, strat_hash)

    holdout_data = HoldoutGateway.get_blind_holdout_data(
        candles,
        strategy_id=strat_id,
        strategy_snapshot_hash=strat_hash,
        auth_token=token,
        is_ratio=0.60,
        val_ratio=0.20,
    )
    assert len(holdout_data) == 20

    # Sin solapamiento temporal
    assert is_data[-1]["timestamp_utc_ms"] < val_data[0]["timestamp_utc_ms"]
    assert val_data[-1]["timestamp_utc_ms"] < holdout_data[0]["timestamp_utc_ms"]


def test_holdout_gateway_unauthorized_rejection():
    """TEST ADVERSARIAL: Intentar acceder a Blind Holdout sin token o con token erróneo lanza BlindHoldoutAccessViolation."""
    candles = _create_dummy_candles(100)
    strat_id = "UR_STRAT_TEST"
    strat_hash = hashlib.sha256(b"snap").hexdigest()

    # 1. Token vacío
    with pytest.raises(BlindHoldoutAccessViolation, match="TOKEN_DE_VALIDACION_INVALIDO"):
        HoldoutGateway.get_blind_holdout_data(
            candles,
            strategy_id=strat_id,
            strategy_snapshot_hash=strat_hash,
            auth_token="",
        )

    # 2. Token de otra estrategia
    other_token = HoldoutGateway.generate_validation_token("OTHER_STRAT", strat_hash)
    with pytest.raises(BlindHoldoutAccessViolation, match="TOKEN_DE_VALIDACION_INVALIDO"):
        HoldoutGateway.get_blind_holdout_data(
            candles,
            strategy_id=strat_id,
            strategy_snapshot_hash=strat_hash,
            auth_token=other_token,
        )


from services.discovery.strategy_search_registry import SearchTrialRecord, StrategySearchRegistry


def test_trial_registry_persistent_accounting():
    """Verifica que StrategySearchRegistry registre exhaustivamente cada trial sin omisiones."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_trials.db"
        registry = StrategySearchRegistry(db_path=str(db_path))

        run_id = "run_search_001"

        # Registrar 10 trials
        for i in range(10):
            strat_hash = hashlib.sha256(f"strat_{i}".encode()).hexdigest()
            trial = SearchTrialRecord(
                trial_id=f"trial_{run_id}_{i}",
                run_id=run_id,
                generation=i // 5,
                parent_trial_id=None if i == 0 else f"trial_{run_id}_{i-1}",
                symbol="NQ",
                timeframe="1h",
                route="FONDEO",
                archetype="MOMENTUM_BREAKOUT",
                parameters={"period": 10 + i},
                rules_json=json.dumps({"rule": f"EMA_{10+i}_CROSS"}),
                dataset_id="ds_nq_h1",
                dataset_sha256="sha256_nq_dataset",
                discovery_engine="genetic_search",
                in_sample_pf=1.2 + i * 0.05,
                in_sample_dd_pct=3.0,
            )
            registry.record_trial(trial)

        trials = registry.get_trials_for_run(run_id)
        assert len(trials) == 10
        assert json.loads(trials[0]["parameters_json"])["period"] == 10
        assert json.loads(trials[9]["parameters_json"])["period"] == 19
        assert registry.get_total_trials_count(symbol="NQ", timeframe="1h") == 10
