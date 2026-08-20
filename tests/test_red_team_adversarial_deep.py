"""tests/test_red_team_adversarial_deep.py
Batería de Ataques Adversariales Profundos (Red-Team) (Fase 7).
Ataca deliberadamente todas las capas del sistema.
Cualquier ataque que obtenga 'PASSED' es considerado un fallo crítico del sistema.
"""

import json
import pytest
from contracts.canonical_execution import AssetClass
from services.data.instrument_cost_registry import MissingCostModelError, get_instrument_cost_profile
from services.data.dataset_integrity_validator import DatasetIntegrityValidator
from services.data.holdout_partitioner import HoldoutPartitioner, BlindHoldoutAccessViolation
from services.api.app.validation.nautilus_gate_engine import NautilusGateEngine


def test_adversarial_attack_corrupt_empty_dataset():
    """Attack 1: Passing empty or truncated dataset to Gate 11 must return SKIPPED/FAILED, never PASS."""
    engine = NautilusGateEngine()
    res = engine.validate_candidate(
        candidate_dict={"candidate_id": "cand_attack_01"},
        candles=[],
        account_size_usd=10000.0,
    )
    assert res.status != "PASSED"
    assert res.verified is False


def test_adversarial_attack_future_timestamps():
    """Attack 2: Passing timestamps out of order or far into future must fail dataset integrity."""
    validator = DatasetIntegrityValidator()
    tampered_candles = [
        {"time": 1000, "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5},
        {"time": 500, "open": 10.5, "high": 11.5, "low": 9.5, "close": 11.0},  # Time travels backward!
    ] * 30
    rep = validator.validate_candles(tampered_candles)
    assert rep.passed is False
    assert rep.is_ordered is False


def test_adversarial_attack_hidden_zero_cost_symbol():
    """Attack 3: Executing with an unregistered asset to bypass fees must be immediately blocked."""
    with pytest.raises(MissingCostModelError):
        get_instrument_cost_profile("FAKE_ZERO_FEE_COIN")


def test_adversarial_attack_discovery_holdout_contamination():
    """Attack 4: Attempting to peek into blind holdout partition during discovery raises error."""
    with pytest.raises(BlindHoldoutAccessViolation):
        HoldoutPartitioner.assert_discovery_cannot_read_holdout(
            caller_module="services.discovery.genetic_search",
            requested_partition="blind_oos",
        )


def test_adversarial_attack_excessive_leverage_spoof():
    """Attack 5: Strategy claiming 3x leverage but exceeding ceiling must fail Gate 11."""
    engine = NautilusGateEngine()
    sample_file = "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_suiusdt_1h_1695290400000_1787086800000.json"
    with open(sample_file, "r") as f:
        candles = json.load(f)

    res = engine.validate_candidate(
        candidate_dict={
            "candidate_id": "cand_attack_05",
            "route": "FONDEO",
            "symbol": "SUIUSDT",
            "scorecard_json": {"parameters": {"risk_pct": 5.0}},
        },
        candles=candles,
        account_size_usd=10000.0,
        max_leverage_ceiling=1.0,  # Strict 1x ceiling
    )
    assert res.status == "FAILED"
    assert res.verified is False
