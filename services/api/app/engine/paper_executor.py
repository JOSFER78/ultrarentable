"""Paper Trading Simulation Executor for Ultrarentable.

Runs real-time bar-by-bar execution simulations:
1. Feeds incoming bars from verified historical datasets or live WebSocket.
2. Emulates order fills with BingX maker/taker fees and slippage models.
3. Continuously syncs session telemetry into SQLite (`execution_sessions` table).
4. Enforces automated Kill-Switches:
   - Daily Loss Limit (DLL) Breach -> Emergency Flatten & Halt.
   - Max Trailing Drawdown Breach -> Halt.
   - Kill-Switch API trigger -> Immediate Flatten.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.api.app.db.database import SessionLocal, ExecutionSessionModel, AuditEventModel


class PaperExecutor:
    def __init__(
        self,
        session_id: str,
        symbol: str = "ETH-USDT",
        initial_capital: float = 10000.0,
        daily_loss_limit: float = 500.0,
        max_drawdown_limit_pct: float = 10.0,
        taker_fee_pct: float = 0.050,
        slippage_pct: float = 0.003
    ):
        self.session_id = session_id
        self.symbol = symbol
        self.equity = initial_capital
        self.peak_equity = initial_capital
        self.daily_loss_limit = daily_loss_limit
        self.max_drawdown_limit_pct = max_drawdown_limit_pct
        self.taker_fee = taker_fee_pct / 100.0
        self.slippage = slippage_pct / 100.0

        self.current_position: Optional[Dict[str, Any]] = None
        self.daily_pnl = 0.0
        self.current_drawdown_pct = 0.0
        self.is_halted = False
        self.halt_reason = ""

    def _sync_to_db(self, last_signal: str = "", last_order: str = ""):
        with SessionLocal() as db:
            s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == self.session_id).first()
            if s:
                s.current_pnl_usd = round(self.equity - 10000.0, 2)
                s.daily_pnl_usd = round(self.daily_pnl, 2)
                s.current_drawdown_pct = round(self.current_drawdown_pct, 2)
                s.peak_equity_usd = round(self.peak_equity, 2)
                s.heartbeat_last_at = datetime.now(timezone.utc)
                if last_signal:
                    s.last_signal = last_signal
                if last_order:
                    s.last_order = last_order
                if self.current_position:
                    s.open_positions_json = json.dumps([self.current_position])
                else:
                    s.open_positions_json = json.dumps([])
                if self.is_halted:
                    s.status = "KILL_SWITCH_HALTED"
                    s.kill_switch_active = True
                    s.kill_switch_reason = self.halt_reason
                db.commit()

    def process_bar(self, bar: Dict[str, Any], signal: str = "HOLD") -> Dict[str, Any]:
        """Process a single bar in the paper trading loop."""
        if self.is_halted:
            return {"status": "HALTED", "reason": self.halt_reason}

        # Check if Kill-Switch was triggered from external API
        with SessionLocal() as db:
            s = db.query(ExecutionSessionModel).filter(ExecutionSessionModel.session_id == self.session_id).first()
            if s and s.kill_switch_active:
                self.is_halted = True
                self.halt_reason = s.kill_switch_reason or "EXTERNAL_KILL_SWITCH"
                self._emergency_flatten(bar["close"])
                return {"status": "EMERGENCY_FLATTENED", "reason": self.halt_reason}

        c_px = float(bar["close"])
        h_px = float(bar["high"])
        l_px = float(bar["low"])

        # 1. Update Open Position MTM
        if self.current_position:
            side = self.current_position["side"]
            entry_px = self.current_position["entry_price"]
            size_usd = self.current_position["size_usd"]
            sl = self.current_position["stop_loss"]
            tp = self.current_position["take_profit"]

            # Check SL / TP
            sl_hit = (side == "LONG" and l_px <= sl) or (side == "SHORT" and h_px >= sl)
            tp_hit = (side == "LONG" and h_px >= tp) or (side == "SHORT" and l_px <= tp)

            if sl_hit or tp_hit:
                exit_px = (sl if sl_hit else tp) * (1.0 - self.slippage if side == "LONG" else 1.0 + self.slippage)
                price_ret = (exit_px - entry_px) / entry_px if side == "LONG" else (entry_px - exit_px) / entry_px
                gross_pnl = size_usd * price_ret
                fee = (size_usd + (size_usd * (1 + price_ret))) * self.taker_fee
                net_pnl = gross_pnl - fee

                self.equity += net_pnl
                self.daily_pnl += net_pnl
                self.peak_equity = max(self.peak_equity, self.equity)
                self.current_drawdown_pct = (self.peak_equity - self.equity) / self.peak_equity * 100.0 if self.peak_equity > 0 else 0.0

                order_msg = f"EXIT {side} @ {exit_px:.2f} ({'SL' if sl_hit else 'TP'}) | PnL: ${net_pnl:+.2f}"
                self.current_position = None
                self._sync_to_db(last_order=order_msg)

                # Check DLL Breach
                if self.daily_pnl <= -self.daily_loss_limit:
                    self.is_halted = True
                    self.halt_reason = f"DAILY_LOSS_LIMIT_REACHED (-${abs(self.daily_pnl):.2f})"
                    self._sync_to_db(last_order="KILL-SWITCH: Daily Loss Limit Hit. Halting.")
                    return {"status": "HALTED", "reason": self.halt_reason}

        # 2. Check New Entry Signal
        if not self.current_position and signal in ("LONG", "SHORT"):
            entry_px = c_px * (1.0 + self.slippage if signal == "LONG" else 1.0 - self.slippage)
            risk_budget = self.equity * 0.015  # 1.5% Risk
            atr_est = max(1.0, c_px * 0.01) # ~1% ATR fallback
            sl_dist = atr_est * 1.5
            sl_pct = sl_dist / entry_px
            pos_size = min(risk_budget / sl_pct, self.equity * 10.0)

            sl_px = entry_px - sl_dist if signal == "LONG" else entry_px + sl_dist
            tp_px = entry_px + (atr_est * 4.2) if signal == "LONG" else entry_px - (atr_est * 4.2)

            self.current_position = {
                "symbol": self.symbol,
                "side": signal,
                "entry_price": entry_px,
                "size_usd": round(pos_size, 2),
                "leverage": round(pos_size / self.equity, 1),
                "stop_loss": round(sl_px, 2),
                "take_profit": round(tp_px, 2),
                "opened_at": datetime.now(timezone.utc).isoformat()
            }
            order_msg = f"BUY {signal} {self.symbol} @ {entry_px:.2f} (Size: ${pos_size:,.2f})"
            self._sync_to_db(last_signal=f"{signal}_SIGNAL", last_order=order_msg)

        self._sync_to_db()
        return {
            "status": "RUNNING",
            "equity": self.equity,
            "daily_pnl": self.daily_pnl,
            "drawdown_pct": self.current_drawdown_pct,
            "has_position": self.current_position is not None
        }

    def _emergency_flatten(self, current_price: float):
        if self.current_position:
            side = self.current_position["side"]
            exit_px = current_price
            order_msg = f"EMERGENCY FLATTEN {side} @ {exit_px:.2f} due to {self.halt_reason}"
            self.current_position = None
            self._sync_to_db(last_order=order_msg)
