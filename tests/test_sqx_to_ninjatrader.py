"""tests/test_sqx_to_ninjatrader.py
Unit tests for NinjaTrader 8 C# Strategy Generator and CME Presets.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from services.api.app.export.sqx_to_ninjatrader import (
    CME_INSTRUMENT_SPECS,
    generate_ninjatrader_strategy_cs,
    export_strategy_to_file,
    export_all_cme_presets,
)


def test_cme_specs_completeness():
    required_assets = ["MNQ", "MES", "NQ", "ES", "MGC", "GC", "MCL", "6E"]
    for asset in required_assets:
        assert asset in CME_INSTRUMENT_SPECS
        spec = CME_INSTRUMENT_SPECS[asset]
        assert spec["tick_size"] > 0
        assert spec["point_value"] > 0
        assert spec["tick_value_usd"] > 0
        assert spec["default_sl_ticks"] > 0
        assert spec["default_tp_ticks"] > 0
        assert spec["default_be_ticks"] > 0


def test_generate_ninjatrader_strategy_cs_mnq():
    code = generate_ninjatrader_strategy_cs(
        strategy_name="UR_Test_MNQ_Combine",
        asset="MNQ",
        default_qty=2,
        daily_loss_limit_usd=1000.0,
        max_trailing_dd_usd=2000.0,
        profit_target_ticks=100,
        stop_loss_ticks=40,
        break_even_trigger_ticks=60,
    )
    assert "public class UR_Test_MNQ_Combine : Strategy" in code
    assert "Contracts { get; set; } = 2;" in code
    assert "DailyLossLimit { get; set; } = 1000.0;" in code
    assert "MaxTrailingDrawdown { get; set; } = 2000.0;" in code
    assert "ProfitTargetTicks { get; set; } = 100;" in code
    assert "StopLossTicks { get; set; } = 40;" in code
    assert "BreakEvenTriggerTicks { get; set; } = 60;" in code
    assert "DAILY_LOSS_LIMIT" in code
    assert "TRAILING_DRAWDOWN" in code
    assert "Break-Even armed" in code
    assert "SendTelemetryWebhook" in code


def test_export_all_cme_presets():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir)
        exported = export_all_cme_presets(out_path)
        assert len(exported) == 8
        for sym, path in exported.items():
            assert path.exists()
            assert path.stat().st_size > 5000
            content = path.read_text(encoding="utf-8")
            assert f"public class UR_Prop_{sym}_TrendBreakout" in content
