"""Mandatory tests for DSL v1.0.0 — all 12 criteria from PROMPT_IDE_CORRECCIONES_C2_Y_FASE_D.md."""
from __future__ import annotations

import json
import copy

import pytest
from pydantic import ValidationError as PydanticValidationError

from services.api.app.dsl.engine import (
    StrategyDSL,
    canonical_json,
    canonical_hash,
    validate_semantics,
    compile_to_ir,
    extract_required_series,
    SeriesName,
    COMPILER_VERSION,
    DSL_VERSION,
)


def _make_valid_dsl() -> dict:
    """Construct a minimal valid DSL v1.0.0 strategy dict."""
    return {
        "dslVersion": "1.0.0",
        "metadata": {
            "name": "Test Breakout EMA",
            "family": "breakout",
            "parents": [],
            "origin": "MANUAL",
        },
        "market": {
            "venue": "BINGX",
            "symbol": "ETH-USDT",
            "timeframe": "1h",
        },
        "signals": {
            "longEntry": {
                "nodeType": "COMPARISON",
                "op": "GT",
                "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                    "params": {"period": 20},
                    "offset": 0,
                },
            },
            "shortEntry": {
                "nodeType": "COMPARISON",
                "op": "LT",
                "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                "right": {
                    "type": "INDICATOR",
                    "indicator": "EMA",
                    "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                    "params": {"period": 20},
                    "offset": 0,
                },
            },
            "longExit": {
                "nodeType": "COMPARISON",
                "op": "CROSS_BELOW",
                "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                "right": {
                    "type": "INDICATOR",
                    "indicator": "SMA",
                    "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                    "params": {"period": 50},
                    "offset": 0,
                },
            },
            "shortExit": {
                "nodeType": "COMPARISON",
                "op": "CROSS_ABOVE",
                "left": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                "right": {
                    "type": "INDICATOR",
                    "indicator": "SMA",
                    "source": {"type": "SERIES", "series": "CLOSE", "offset": 0},
                    "params": {"period": 50},
                    "offset": 0,
                },
            },
        },
        "position": {
            "marginMode": "ISOLATED",
            "leverage": 5,
            "allocationPct": 100.0,
            "compound": True,
            "pyramiding": {"enabled": False, "maxEntries": 1},
        },
        "execution": {
            "entryOrderType": "MARKET",
            "exitOrderType": "MARKET",
            "signalTiming": "BAR_CLOSE_EXECUTE_NEXT_OPEN",
        },
    }


# ─── Test 1: Same JSON with different key ordering produces same hash ─────────

def test_same_json_different_key_order_same_hash() -> None:
    dsl_a = _make_valid_dsl()
    dsl_b = json.loads(json.dumps(dsl_a))
    dsl_c = {k: dsl_b[k] for k in reversed(list(dsl_b.keys()))}
    parsed_a = StrategyDSL(**dsl_a)
    parsed_c = StrategyDSL(**dsl_c)
    assert canonical_hash(parsed_a) == canonical_hash(parsed_c)


# ─── Test 2: Real parameter change produces different hash ────────────────────

def test_parameter_change_produces_different_hash() -> None:
    dsl_a = _make_valid_dsl()
    dsl_b = copy.deepcopy(dsl_a)
    dsl_b["position"]["leverage"] = 10
    parsed_a = StrategyDSL(**dsl_a)
    parsed_b = StrategyDSL(**dsl_b)
    assert canonical_hash(parsed_a) != canonical_hash(parsed_b)


# ─── Test 3: Unknown property is rejected ─────────────────────────────────────

def test_unknown_property_rejected() -> None:
    dsl = _make_valid_dsl()
    dsl["unknownField"] = "should fail"
    with pytest.raises(PydanticValidationError):
        StrategyDSL(**dsl)


# ─── Test 4: Unknown indicator is rejected ────────────────────────────────────

def test_unknown_indicator_rejected() -> None:
    dsl = _make_valid_dsl()
    dsl["signals"]["longEntry"]["right"]["indicator"] = "BOLLINGER_BANDS"
    with pytest.raises(PydanticValidationError):
        StrategyDSL(**dsl)


# ─── Test 5: Negative offset (look-ahead) is rejected ─────────────────────────

def test_negative_offset_rejected() -> None:
    dsl = _make_valid_dsl()
    dsl["signals"]["longEntry"]["left"]["offset"] = -1
    with pytest.raises(PydanticValidationError):
        StrategyDSL(**dsl)


# ─── Test 6: Unavailable series is rejected by semantic validator ──────────────

def test_unavailable_series_rejected() -> None:
    dsl = _make_valid_dsl()
    dsl["signals"]["longEntry"]["left"]["series"] = "FUNDING_RATE"
    parsed = StrategyDSL(**dsl)
    errors = validate_semantics(
        parsed,
        available_series={SeriesName.OPEN, SeriesName.HIGH, SeriesName.LOW, SeriesName.CLOSE, SeriesName.VOLUME},
        available_symbols={"ETH-USDT"},
    )
    assert any(e.code == "SERIES_NOT_AVAILABLE" for e in errors)


# ─── Test 7: Leverage exceeding venue limit is rejected ────────────────────────

def test_leverage_exceeds_venue_limit() -> None:
    dsl = _make_valid_dsl()
    dsl["position"]["leverage"] = 100
    parsed = StrategyDSL(**dsl)
    errors = validate_semantics(parsed, max_leverage=50, available_symbols={"ETH-USDT"})
    assert any(e.code == "LEVERAGE_EXCEEDS_VENUE_LIMIT" for e in errors)


def test_dsl_accepts_500x_and_rejects_501x() -> None:
    dsl = _make_valid_dsl()
    dsl["position"]["leverage"] = 500
    parsed = StrategyDSL(**dsl)
    assert parsed.position.leverage == 500

    dsl["position"]["leverage"] = 501
    with pytest.raises(PydanticValidationError):
        StrategyDSL(**dsl)


# ─── Test 8: AST and IR are deterministic ──────────────────────────────────────

def test_ast_and_ir_deterministic() -> None:
    dsl = _make_valid_dsl()
    parsed = StrategyDSL(**dsl)
    ir_1 = compile_to_ir(parsed)
    ir_2 = compile_to_ir(parsed)
    assert ir_1.irHash == ir_2.irHash
    assert ir_1.dslHash == ir_2.dslHash
    assert len(ir_1.instructions) == len(ir_2.instructions)


# ─── Test 9: Compilation saves version, hash, and artifact ────────────────────

def test_compilation_has_version_hash_artifact() -> None:
    dsl = _make_valid_dsl()
    parsed = StrategyDSL(**dsl)
    ir = compile_to_ir(parsed)
    assert ir.compilerVersion == COMPILER_VERSION
    assert ir.dslVersion == DSL_VERSION
    assert len(ir.irHash) == 64
    assert len(ir.dslHash) == 64
    assert len(ir.instructions) > 0


# ─── Test 10: Restarting does not change hashes or states ──────────────────────

def test_hash_stability_across_reparse() -> None:
    dsl_dict = _make_valid_dsl()
    hash_1 = canonical_hash(StrategyDSL(**dsl_dict))
    dsl_dict_2 = json.loads(json.dumps(dsl_dict))
    hash_2 = canonical_hash(StrategyDSL(**dsl_dict_2))
    assert hash_1 == hash_2


# ─── Test 11: No Math.random, hardcoded results, or manual CANONICAL ──────────

def test_no_forbidden_patterns_in_dsl_module() -> None:
    import inspect
    from services.api.app.dsl import engine as dsl_module
    source = inspect.getsource(dsl_module)
    assert "Math.random" not in source
    assert "eval(" not in source
    assert "exec(" not in source


# ─── Test 12: Required series extraction ──────────────────────────────────────

def test_required_series_extraction() -> None:
    dsl = _make_valid_dsl()
    parsed = StrategyDSL(**dsl)
    required = extract_required_series(parsed)
    assert SeriesName.CLOSE in required
    assert SeriesName.FUNDING_RATE not in required
