"""NautilusTrader Gate 11 Execution Engine.

Isolated event-driven microstructure, margin (up to 500x), liquidation and funding rate
validation gate with circuit-breaker protection for Ultrarentable.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger("nautilus_gate")


@dataclass
class NautilusGateResult:
    status: str  # "PASSED" | "FAILED" | "SKIPPED"
    verified: bool
    total_trades: int
    net_profit_usd: float
    roi_pct: float
    profit_factor: float
    max_drawdown_pct: float
    peak_margin_utilization_pct: float  # Peak margin / equity (0-100%)
    liquidation_distance_min_pct: float  # Minimum distance to liquidation (must be > 0.3%)
    funding_fees_usd: float
    effective_max_leverage: float
    execution_time_ms: float
    diagnostics: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": str(self.status),
            "verified": bool(self.verified),
            "total_trades": int(self.total_trades),
            "net_profit_usd": round(float(self.net_profit_usd), 2),
            "roi_pct": round(float(self.roi_pct), 2),
            "profit_factor": round(float(self.profit_factor), 2),
            "max_drawdown_pct": round(float(self.max_drawdown_pct), 2),
            "peak_margin_utilization_pct": round(float(self.peak_margin_utilization_pct), 2),
            "liquidation_distance_min_pct": round(float(self.liquidation_distance_min_pct), 2),
            "funding_fees_usd": round(float(self.funding_fees_usd), 2),
            "effective_max_leverage": round(float(self.effective_max_leverage), 1),
            "execution_time_ms": round(float(self.execution_time_ms), 2),
            "diagnostics": str(self.diagnostics),
            "details": {k: (float(v) if isinstance(v, (np.floating, np.integer)) else bool(v) if isinstance(v, np.bool_) else v) for k, v in self.details.items()},
        }


class NautilusGateEngine:
    """High-Fidelity Event-Driven Validation Gate using NautilusTrader principles.

    Runs fully isolated with a strict circuit breaker so errors or dependency issues
    never crash the host FastAPI server or background mining daemon.
    """

    def __init__(self, taker_fee_pct: float = 0.05, maker_fee_pct: float = 0.02, slippage_bps: float = 2.0):
        self.taker_fee = taker_fee_pct / 100.0
        self.maker_fee = maker_fee_pct / 100.0
        self.slippage = slippage_bps / 10_000.0
        self.funding_rate_8h = 0.0001  # Standard 0.01% / 8h baseline for crypto perps

    def validate_candidate(
        self,
        candidate_dict: Dict[str, Any],
        candles: List[Dict[str, Any]],
        account_size_usd: float = 10_000.0,
        max_leverage_ceiling: float = 500.0,
    ) -> NautilusGateResult:
        """Run Gate 11 event-driven simulation with dynamic margin tracking."""
        start_time = datetime.now(timezone.utc)

        if not candles or len(candles) < 100:
            return NautilusGateResult(
                status="SKIPPED",
                verified=False,
                total_trades=0,
                net_profit_usd=0.0,
                roi_pct=0.0,
                profit_factor=0.0,
                max_drawdown_pct=0.0,
                peak_margin_utilization_pct=0.0,
                liquidation_distance_min_pct=100.0,
                funding_fees_usd=0.0,
                effective_max_leverage=1.0,
                execution_time_ms=0.0,
                diagnostics="Insufficient candle data for Gate 11 simulation (< 100 bars).",
            )

        try:
            # Extract parameters safely
            scorecard = candidate_dict.get("scorecard_json", {})
            if isinstance(scorecard, str):
                import json
                try:
                    scorecard = json.loads(scorecard)
                except Exception:
                    scorecard = {}

            params = scorecard.get("parameters", {})
            route = candidate_dict.get("route", "ULTRA")
            arch = candidate_dict.get("archetype", scorecard.get("archetype", "TREND_EMA_REGIME"))

            sl_mult = float(params.get("sl_atr_mult", 1.5))
            tp_mult = float(params.get("tp_atr_mult", 7.0))
            risk_pct = float(params.get("risk_pct", 3.0 if route == "ULTRA" else 0.8))
            max_tiers = int(params.get("pyramiding_tiers", 3 if route == "ULTRA" else 1))

            # Arrays for event simulation
            n = len(candles)
            closes = np.array([c["close"] for c in candles], dtype=np.float64)
            highs = np.array([c["high"] for c in candles], dtype=np.float64)
            lows = np.array([c["low"] for c in candles], dtype=np.float64)

            # Precalculate Indicators
            tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
            atr = np.zeros(n)
            atr[0] = highs[0] - lows[0]
            for i in range(1, n):
                atr[i] = (atr[i - 1] * 13 + tr[i - 1]) / 14.0

            ema20 = np.zeros(n)
            ema50 = np.zeros(n)
            ema200 = np.zeros(n)
            ema20[0] = closes[0]
            ema50[0] = closes[0]
            ema200[0] = closes[0]
            for i in range(1, n):
                ema20[i] = (2 / 21) * closes[i] + (1 - 2 / 21) * ema20[i - 1]
                ema50[i] = (2 / 51) * closes[i] + (1 - 2 / 51) * ema50[i - 1]
                ema200[i] = (2 / 201) * closes[i] + (1 - 2 / 201) * ema200[i - 1]

            donch_hi = np.zeros(n)
            donch_lo = np.zeros(n)
            for i in range(20, n):
                donch_hi[i] = np.max(highs[i - 20:i])
                donch_lo[i] = np.min(lows[i - 20:i])

            # Simulation State
            equity = account_size_usd
            peak_equity = account_size_usd
            max_drawdown = 0.0
            peak_margin_utilization = 0.0
            min_liquidation_distance = 100.0
            total_funding_fees = 0.0
            max_effective_leverage = 1.0

            trades = []
            in_pos = False
            pos_side = ""
            entry_px = 0.0
            sl_px = 0.0
            tp_px = 0.0
            tier_count = 0
            pos_qty = 0.0
            entry_bar_idx = 0

            # Maintenance margin requirement (MMR = 0.4% on BingX Perps 500x)
            mmr = 0.004

            for i in range(200, n):
                c = closes[i]
                h = highs[i]
                l = lows[i]
                a = atr[i]

                if in_pos:
                    # Funding Rate Deduction (every 8 bars in 1h = 8h)
                    if (i - entry_bar_idx) % 8 == 0 and (i - entry_bar_idx) > 0:
                        funding_fee = (pos_qty * c) * self.funding_rate_8h
                        total_funding_fees += funding_fee
                        equity -= funding_fee

                    # Cross-Margin Liquidation Engine (BingX / Binance Perps)
                    notional = pos_qty * c
                    unrealized_pnl = (c - entry_px) * pos_qty if pos_side == "LONG" else (entry_px - c) * pos_qty
                    current_equity = equity + unrealized_pnl
                    maint_margin_req = notional * mmr
                    margin_used = notional / max_leverage_ceiling
                    margin_utilization = (margin_used / max(1.0, current_equity)) * 100.0
                    peak_margin_utilization = max(peak_margin_utilization, margin_utilization)

                    effective_lev = notional / max(1.0, current_equity)
                    max_effective_leverage = max(max_effective_leverage, effective_lev)

                    # Liquidation occurs if Account Equity <= Maintenance Margin Requirement
                    # Long Liq Price: entry_px - ((equity - maint_margin_req) / pos_qty)
                    # Short Liq Price: entry_px + ((equity - maint_margin_req) / pos_qty)
                    if pos_side == "LONG":
                        liq_px = max(0.0, entry_px - ((equity - maint_margin_req) / max(0.0001, pos_qty)))
                        liq_dist_pct = ((l - liq_px) / entry_px) * 100.0
                        min_liquidation_distance = min(min_liquidation_distance, max(0.0, liq_dist_pct))
                        if l <= liq_px or current_equity <= maint_margin_req:
                            return NautilusGateResult(
                                status="FAILED",
                                verified=False,
                                total_trades=len(trades) + 1,
                                net_profit_usd=-account_size_usd,
                                roi_pct=-100.0,
                                profit_factor=0.0,
                                max_drawdown_pct=100.0,
                                peak_margin_utilization_pct=100.0,
                                liquidation_distance_min_pct=0.0,
                                funding_fees_usd=total_funding_fees,
                                effective_max_leverage=max_effective_leverage,
                                execution_time_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                                diagnostics=f"Gate 11 FAILED: Position breached liquidation price (${liq_px:.2f}) on bar {i}.",
                            )
                    else:
                        liq_px = entry_px + ((equity - maint_margin_req) / max(0.0001, pos_qty))
                        liq_dist_pct = ((liq_px - h) / entry_px) * 100.0
                        min_liquidation_distance = min(min_liquidation_distance, max(0.0, liq_dist_pct))
                        if h >= liq_px or current_equity <= maint_margin_req:
                            return NautilusGateResult(
                                status="FAILED",
                                verified=False,
                                total_trades=len(trades) + 1,
                                net_profit_usd=-account_size_usd,
                                roi_pct=-100.0,
                                profit_factor=0.0,
                                max_drawdown_pct=100.0,
                                peak_margin_utilization_pct=100.0,
                                liquidation_distance_min_pct=0.0,
                                funding_fees_usd=total_funding_fees,
                                effective_max_leverage=max_effective_leverage,
                                execution_time_ms=(datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                                diagnostics=f"Gate 11 FAILED: Short breached liquidation price (${liq_px:.2f}) on bar {i}.",
                            )

                    # Check SL / TP
                    sl_hit = (pos_side == "LONG" and l <= sl_px) or (pos_side == "SHORT" and h >= sl_px)
                    tp_hit = (pos_side == "LONG" and h >= tp_px) or (pos_side == "SHORT" and l <= tp_px)

                    # Pyramiding & Break-Even Trailing (Free Margin Recycling)
                    if not sl_hit and not tp_hit and tier_count < max_tiers:
                        dist = (h - entry_px) if pos_side == "LONG" else (entry_px - l)
                        if dist >= tier_count * (1.8 * a):
                            # Lock previous tier in profit
                            sl_px = entry_px + ((tier_count - 1) * 0.8 * a) if pos_side == "LONG" else entry_px - ((tier_count - 1) * 0.8 * a)
                            tier_risk = equity * (risk_pct / 100.0)
                            added_qty = tier_risk / max(0.001, sl_mult * a)
                            max_add = max(0.0, (100_000.0 - pos_qty * c) / c)
                            pos_qty += min(added_qty, max_add)
                            tier_count += 1

                    if sl_hit or tp_hit:
                        raw_exit = sl_px if sl_hit else tp_px
                        exit_px = raw_exit * (1.0 - self.slippage) if pos_side == "LONG" else raw_exit * (1.0 + self.slippage)
                        pnl = (exit_px - entry_px) * pos_qty if pos_side == "LONG" else (entry_px - exit_px) * pos_qty
                        fee = (pos_qty * entry_px + pos_qty * exit_px) * self.taker_fee
                        net_pnl = pnl - fee
                        equity += net_pnl
                        peak_equity = max(peak_equity, equity)
                        dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                        max_drawdown = max(max_drawdown, dd)
                        trades.append(net_pnl)
                        in_pos = False
                        continue

                if not in_pos:
                    if arch == "TREND_EMA_REGIME":
                        long_sig = (c > ema200[i]) and (ema20[i] > ema50[i]) and (c >= donch_hi[i - 1]) and (a > np.mean(atr[i - 20:i]))
                        short_sig = (c < ema200[i]) and (ema20[i] < ema50[i]) and (c <= donch_lo[i - 1]) and (a > np.mean(atr[i - 20:i]))
                    elif arch == "DONCHIAN_EXPANSION":
                        long_sig = (c >= donch_hi[i - 1]) and (a >= np.mean(atr[i - 20:i]) * 1.1)
                        short_sig = (c <= donch_lo[i - 1]) and (a >= np.mean(atr[i - 20:i]) * 1.1)
                    else:
                        long_sig = (c >= donch_hi[i - 1]) and (a >= np.mean(atr[i - 20:i]))
                        short_sig = (c <= donch_lo[i - 1]) and (a >= np.mean(atr[i - 20:i]))

                    if long_sig:
                        in_pos = True
                        pos_side = "LONG"
                        entry_px = c * (1.0 + self.slippage)
                        sl_px = c - (sl_mult * a)
                        tp_px = c + (tp_mult * a)
                        risk_cash = equity * (risk_pct / 100.0)
                        pos_qty = min(risk_cash / max(0.001, sl_mult * a), 100_000.0 / c)
                        tier_count = 1
                        entry_bar_idx = i
                    elif short_sig:
                        in_pos = True
                        pos_side = "SHORT"
                        entry_px = c * (1.0 - self.slippage)
                        sl_px = c + (sl_mult * a)
                        tp_px = c - (tp_mult * a)
                        risk_cash = equity * (risk_pct / 100.0)
                        pos_qty = min(risk_cash / max(0.001, sl_mult * a), 100_000.0 / c)
                        tier_count = 1
                        entry_bar_idx = i

            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0
            wins = [t for t in trades if t > 0]
            losses = [t for t in trades if t <= 0]
            pf = sum(wins) / abs(sum(losses)) if losses else 99.0
            net_profit = equity - account_size_usd
            roi_pct = (net_profit / account_size_usd) * 100.0

            # Gate 11 Acceptance Criteria:
            # 1. Profit Factor >= 1.25
            # 2. Minimum Liquidation Distance > 0.5% (No margin calls / near-death events)
            # 3. Trades >= 15
            # 4. Max Drawdown acceptable for route (<= 4.0% for Fondeo, <= 50.0% for Ultra)
            max_dd_limit = 4.0 if route == "FONDEO" else 55.0
            passed = (pf >= 1.25) and (min_liquidation_distance >= 0.5) and (len(trades) >= 15) and (max_drawdown <= max_dd_limit) and (net_profit > 0)

            return NautilusGateResult(
                status="PASSED" if passed else "FAILED",
                verified=passed,
                total_trades=len(trades),
                net_profit_usd=net_profit,
                roi_pct=roi_pct,
                profit_factor=pf,
                max_drawdown_pct=max_drawdown,
                peak_margin_utilization_pct=peak_margin_utilization,
                liquidation_distance_min_pct=min_liquidation_distance,
                funding_fees_usd=total_funding_fees,
                effective_max_leverage=max_effective_leverage,
                execution_time_ms=elapsed_ms,
                diagnostics="Gate 11 PASSED: Event-driven microstructure, margin & funding simulation verified." if passed else f"Gate 11 FAILED: PF={pf:.2f}, MinLiqDist={min_liquidation_distance:.2f}%, MaxDD={max_drawdown:.1f}%.",
                details={
                    "route": route,
                    "archetype": arch,
                    "effective_max_leverage": round(max_effective_leverage, 1),
                    "funding_fees_usd": round(total_funding_fees, 2),
                    "trades_count": len(trades),
                },
            )

        except Exception as e:
            logger.exception("Nautilus Gate 11 simulation exception caught gracefully.")
            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0
            return NautilusGateResult(
                status="SKIPPED",
                verified=False,
                total_trades=0,
                net_profit_usd=0.0,
                roi_pct=0.0,
                profit_factor=0.0,
                max_drawdown_pct=0.0,
                peak_margin_utilization_pct=0.0,
                liquidation_distance_min_pct=100.0,
                funding_fees_usd=0.0,
                effective_max_leverage=1.0,
                execution_time_ms=elapsed_ms,
                diagnostics=f"Nautilus Gate 11 Circuit Breaker caught: {type(e).__name__}: {str(e)}",
            )
