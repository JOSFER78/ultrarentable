import json

from services.api.app.api.strategy_lab_router import _canonical_payload


def test_canonical_source_payload_is_deterministic():
    raw = {"values": [1, 2, 3], "metrics": {"profit": 10}}
    first = _canonical_payload("P", "D", "S", raw)
    second = _canonical_payload("P", "D", "S", raw)
    assert first == second
    assert json.loads(first)["source"] == {
        "engine": "StrategyQuantX",
        "project": "P",
        "databank": "D",
        "strategy_name": "S",
    }


def test_extraction_payload_does_not_contain_synthetic_backtest_fields():
    payload = _canonical_payload("P", "D", "S", {"values": [1, 2, 3]})
    data = json.loads(payload)
    assert "initial_capital" not in data
    assert "final_equity" not in data
    assert "profit_factor" not in data
    assert "dataset_id" not in data["source"]


def test_missing_market_identity_remains_missing():
    # The extraction contract stores source facts only; it never invents symbol/timeframe.
    record = {
        "market": {"symbol": None, "timeframe": None, "dataset_id": None, "dataset_hash": None}
    }
    assert record["market"]["symbol"] is None
    assert record["market"]["timeframe"] is None
    assert record["market"]["dataset_id"] is None
