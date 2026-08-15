from __future__ import annotations

from services.api.app.engine.ledger import BacktestLedger, TradeRecord


def test_final_equity_uses_closed_capital_not_stale_mark() -> None:
    ledger = BacktestLedger(10_000.0)
    ledger.record_equity(1, 15_000.0)
    ledger.record_trade(TradeRecord(
        trade_id="tr_1",
        symbol="ETH-USDT",
        side="LONG",
        entry_time=1,
        entry_price=100.0,
        exit_time=2,
        exit_price=90.0,
        quantity=100.0,
        leverage=1,
        gross_pnl=-1_000.0,
        fees=10.0,
        funding=0.0,
        net_pnl=-1_010.0,
        return_pct=-10.1,
        exit_reason="END_OF_DATA",
    ))
    metrics = ledger.compute_metrics()
    assert metrics.final_equity == 8_990.0
    assert metrics.net_return_pct == -10.1
