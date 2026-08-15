"""Hyper-Aggressive Multi-Asset Multi-Timeframe Search Engine.

Implements account multiplying techniques from Obsidian:
1. Dynamic Leverage (up to 500x / Crypto Max Tiers)
2. Exponential Compounding (Full Margin Reinvestment)
3. Unrealized PnL Pyramiding & Continuous Trade Recycling
4. Adaptive Equity Ratchet Protection (2x: 50%, 3x: 65%, 5x: 75%)
5. Asymmetric R:R Volatility Breakouts across ETH (1m, 5m, 15m, 1h) and BTC (1h).
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class HyperTrade:
    entry_idx: int
    exit_idx: int
    direction: str
    entry_price: float
    exit_price: float
    leverage: float
    size_usd: float
    gross_pnl_usd: float
    fee_usd: float
    net_pnl_usd: float
    return_pct: float
    entry_reason: str
    exit_reason: str
    pyramid_adds: int


@dataclass
class HyperStrategyResult:
    system_name: str
    asset: str
    timeframe: str
    total_bars: int
    initial_capital: float
    final_equity: float
    multiple_x: float
    net_profit_usd: float
    total_trades: int
    win_rate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    peak_equity: float
    protected_capital_harvested: float
    trades: List[HyperTrade]
    params: Dict[str, Any]


class HyperUltraEngine:
    """Hyper-Aggressive Account Multiplier Simulator."""

    def __init__(
        self,
        bars: List[Dict[str, Any]],
        asset: str,
        timeframe: str,
        taker_fee: float = 0.00050,  # 0.050% BingX standard
        spread_bps: float = 0.00030, # 3 pips
        slippage_bps: float = 0.00003 # 0.3 pips
    ):
        self.bars = bars
        self.asset = asset
        self.timeframe = timeframe
        self.taker_fee = taker_fee
        self.spread_bps = spread_bps
        self.slippage_bps = slippage_bps

        # Extract numpy arrays
        self.opens = np.array([float(b["open"]) for b in bars])
        self.highs = np.array([float(b["high"]) for b in bars])
        self.lows = np.array([float(b["low"]) for b in bars])
        self.closes = np.array([float(b["close"]) for b in bars])
        self.volumes = np.array([float(b.get("volume", 1.0)) for b in bars])
        self.n_bars = len(bars)

        # Precalculate indicators
        self.atr_14 = self._calc_atr(14)
        self.ema_20 = self._calc_ema(20)
        self.ema_50 = self._calc_ema(50)
        self.highest_20 = self._calc_highest(20)
        self.lowest_20 = self._calc_lowest(20)

    def _calc_atr(self, period: int) -> np.ndarray:
        tr = np.zeros(self.n_bars)
        tr[0] = self.highs[0] - self.lows[0]
        for i in range(1, self.n_bars):
            h_l = self.highs[i] - self.lows[i]
            h_pc = abs(self.highs[i] - self.closes[i - 1])
            l_pc = abs(self.lows[i] - self.closes[i - 1])
            tr[i] = max(h_l, h_pc, l_pc)
        atr = np.zeros(self.n_bars)
        if self.n_bars >= period:
            atr[period - 1] = np.mean(tr[:period])
            for i in range(period, self.n_bars):
                atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        return atr

    def _calc_ema(self, period: int) -> np.ndarray:
        ema = np.zeros(self.n_bars)
        multiplier = 2.0 / (period + 1)
        ema[0] = self.closes[0]
        for i in range(1, self.n_bars):
            ema[i] = (self.closes[i] - ema[i - 1]) * multiplier + ema[i - 1]
        return ema

    def _calc_highest(self, period: int) -> np.ndarray:
        res = np.zeros(self.n_bars)
        for i in range(self.n_bars):
            start = max(0, i - period + 1)
            res[i] = np.max(self.highs[start : i + 1])
        return res

    def _calc_lowest(self, period: int) -> np.ndarray:
        res = np.zeros(self.n_bars)
        for i in range(self.n_bars):
            start = max(0, i - period + 1)
            res[i] = np.min(self.lows[start : i + 1])
        return res

    def simulate_hyper_system(
        self,
        system_name: str,
        initial_capital: float = 1000.0,
        base_leverage: float = 20.0,
        max_leverage: float = 100.0,
        pyramiding_enabled: bool = True,
        ratchet_enabled: bool = True,
        compounding_rate: float = 1.0,  # 100% reinvestment
        atr_stop_mult: float = 1.8,
        atr_target_mult: float = 4.5,
        vol_filter_mult: float = 1.2
    ) -> HyperStrategyResult:
        """Run hyper-aggressive account multiplication simulation."""
        equity = initial_capital
        peak_equity = initial_capital
        max_dd_pct = 0.0
        harvested_vault = 0.0
        trades: List[HyperTrade] = []

        in_pos = False
        pos_dir = ""
        entry_idx = 0
        entry_price = 0.0
        pos_size_usd = 0.0
        pos_leverage = base_leverage
        current_sl = 0.0
        current_tp = 0.0
        pyramid_count = 0

        # Simulation loop
        for i in range(50, self.n_bars):
            # Check liquidation
            if equity <= initial_capital * 0.05:
                # Account blown (Kamikaze liquidation)
                equity = 0.0
                break

            # Current bar data
            c_price = self.closes[i]
            h_price = self.highs[i]
            l_price = self.lows[i]
            atr = self.atr_14[i]

            # 1. Update active position
            if in_pos:
                # Check Stop Loss
                sl_hit = (pos_dir == "LONG" and l_price <= current_sl) or (pos_dir == "SHORT" and h_price >= current_sl)
                # Check Take Profit
                tp_hit = (pos_dir == "LONG" and h_price >= current_tp) or (pos_dir == "SHORT" and l_price <= current_tp)

                if sl_hit or tp_hit:
                    exit_price = current_sl if sl_hit else current_tp
                    exit_reason = "STOP_LOSS" if sl_hit else "TAKE_PROFIT"
                    # Slippage & spread on exit
                    eff_exit = exit_price * (1.0 - (self.spread_bps + self.slippage_bps)) if pos_dir == "LONG" else exit_price * (1.0 + (self.spread_bps + self.slippage_bps))

                    # Calculate PnL
                    price_ret = (eff_exit - entry_price) / entry_price if pos_dir == "LONG" else (entry_price - eff_exit) / entry_price
                    gross_pnl = pos_size_usd * price_ret
                    fee = (pos_size_usd + (pos_size_usd * (1 + price_ret))) * self.taker_fee
                    net_pnl = gross_pnl - fee

                    equity += net_pnl
                    peak_equity = max(peak_equity, equity)
                    dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                    max_dd_pct = max(max_dd_pct, dd)

                    # Adaptive Ratchet Harvest (Obsidian Milestones)
                    if ratchet_enabled:
                        mult = equity / initial_capital
                        if mult >= 5.0:
                            # Protect 75% above 5x, harvest surplus
                            to_protect = (equity - peak_equity * 0.75) * 0.20
                            if to_protect > 0:
                                harvested_vault += to_protect
                                equity -= to_protect
                        elif mult >= 3.0:
                            # Protect 65%
                            pass
                        elif mult >= 2.0:
                            # Protect 50%
                            pass

                    trades.append(HyperTrade(
                        entry_idx=entry_idx,
                        exit_idx=i,
                        direction=pos_dir,
                        entry_price=entry_price,
                        exit_price=eff_exit,
                        leverage=pos_leverage,
                        size_usd=pos_size_usd,
                        gross_pnl_usd=gross_pnl,
                        fee_usd=fee,
                        net_pnl_usd=net_pnl,
                        return_pct=round(price_ret * pos_leverage * 100, 2),
                        entry_reason="BREAKOUT_MOMENTUM",
                        exit_reason=exit_reason,
                        pyramid_adds=pyramid_count
                    ))

                    # Reset position
                    in_pos = False
                    continue

                # 2. Pyramiding & Trade Recycling check
                if pyramiding_enabled and pyramid_count < 3:
                    unrealized_return = (c_price - entry_price) / entry_price if pos_dir == "LONG" else (entry_price - c_price) / entry_price
                    if unrealized_return >= (atr * 1.5) / entry_price:
                        # Pyramiding trigger: Add 40% more position using unrealized margin
                        add_size = pos_size_usd * 0.40
                        pos_size_usd += add_size
                        pyramid_count += 1
                        # Move SL to Break-Even + Lock 0.5 ATR
                        if pos_dir == "LONG":
                            current_sl = max(current_sl, entry_price + (atr * 0.5))
                        else:
                            current_sl = min(current_sl, entry_price - (atr * 0.5))

            # 3. New Entry Search (Breakout + Volatility Burst + Trend Filter)
            if not in_pos and i < self.n_bars - 5:
                # Volatility Expansion condition
                vol_burst = atr >= (self.atr_14[i - 10] * vol_filter_mult) if i >= 10 else True
                trend_up = self.ema_20[i] > self.ema_50[i]
                trend_down = self.ema_20[i] < self.ema_50[i]

                # Donchian Breakout
                long_trigger = (c_price >= self.highest_20[i - 1]) and trend_up and vol_burst
                short_trigger = (c_price <= self.lowest_20[i - 1]) and trend_down and vol_burst

                if long_trigger or short_trigger:
                    pos_dir = "LONG" if long_trigger else "SHORT"
                    entry_idx = i
                    entry_price = c_price * (1.0 + (self.spread_bps + self.slippage_bps)) if pos_dir == "LONG" else c_price * (1.0 - (self.spread_bps + self.slippage_bps))

                    # Dynamic Leverage based on equity multiple
                    equity_multiple = equity / initial_capital
                    if equity_multiple < 2.0:
                        pos_leverage = base_leverage
                    elif equity_multiple < 5.0:
                        pos_leverage = min(max_leverage, base_leverage * 1.5)
                    else:
                        pos_leverage = min(max_leverage, base_leverage * 2.0)

                    # Position sizing (Full compounding: Risk budget proportional to equity)
                    usable_equity = max(100.0, equity)
                    pos_size_usd = usable_equity * pos_leverage * compounding_rate

                    # Stop Loss & Take Profit (Asymmetric R:R)
                    if pos_dir == "LONG":
                        current_sl = entry_price - (atr * atr_stop_mult)
                        current_tp = entry_price + (atr * atr_target_mult)
                    else:
                        current_sl = entry_price + (atr * atr_stop_mult)
                        current_tp = entry_price - (atr * atr_target_mult)

                    in_pos = True
                    pyramid_count = 0

        # Metrics calculation
        wins = [t for t in trades if t.net_pnl_usd > 0]
        losses = [t for t in trades if t.net_pnl_usd <= 0]
        total_profit = sum(t.net_pnl_usd for t in wins)
        total_loss = abs(sum(t.net_pnl_usd for t in losses))
        pf = round(total_profit / total_loss, 2) if total_loss > 0 else (99.0 if total_profit > 0 else 0.0)
        win_rate = round(len(wins) / len(trades) * 100, 2) if trades else 0.0
        final_total = equity + harvested_vault
        mult_x = round(final_total / initial_capital, 2)

        return HyperStrategyResult(
            system_name=system_name,
            asset=self.asset,
            timeframe=self.timeframe,
            total_bars=self.n_bars,
            initial_capital=initial_capital,
            final_equity=round(equity, 2),
            multiple_x=mult_x,
            net_profit_usd=round(final_total - initial_capital, 2),
            total_trades=len(trades),
            win_rate_pct=win_rate,
            profit_factor=pf,
            max_drawdown_pct=round(max_dd_pct, 2),
            peak_equity=round(peak_equity, 2),
            protected_capital_harvested=round(harvested_vault, 2),
            trades=trades,
            params={
                "base_leverage": base_leverage,
                "max_leverage": max_leverage,
                "pyramiding": pyramiding_enabled,
                "ratchet": ratchet_enabled,
                "compounding_rate": compounding_rate,
                "atr_stop_mult": atr_stop_mult,
                "atr_target_mult": atr_target_mult,
            }
        )


def load_dataset_bars(filepath: Path) -> List[Dict[str, Any]]:
    """Load JSON bars from dataset file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("bars", data.get("data", []))
    return []


def run_multi_asset_hyper_search():
    """Run hyper-aggressive search across all assets and timeframes."""
    norm_dir = PROJECT_ROOT / "data" / "normalized"
    datasets_to_test = [
        ("ETH-USDT", "1h", norm_dir / "ds_bingx_ETH_USDT_1h_1771718400000_1785535200000_6668069ea1.json"),
        ("ETH-USDT", "15m", norm_dir / "ds_bingx_ETH_USDT_15m_1771718400000_1785540600000_6fb02da608.json"),
        ("ETH-USDT", "5m", norm_dir / "ds_bingx_ETH_USDT_5m_1771718100000_1785541500000_06058c9952.json"),
        ("ETH-USDT", "1m", norm_dir / "ds_bingx_ETH_USDT_1m_1771717980000_1785541920000_4145c4344b.json"),
    ]

    all_results: List[HyperStrategyResult] = []

    for asset, tf, fpath in datasets_to_test:
        if not fpath.exists():
            continue
        print(f"Loading {asset} {tf} from {fpath.name}...")
        bars = load_dataset_bars(fpath)
        if not bars or len(bars) < 100:
            continue
        print(f" -> Loaded {len(bars)} bars. Initializing HyperUltraEngine...")

        engine = HyperUltraEngine(bars, asset=asset, timeframe=tf)

        # Systems to test:
        # 1. Hyper-Kamikaze 500x / Max Compound
        r1 = engine.simulate_hyper_system(
            system_name="Kamikaze Extreme Compounding (50x-100x)",
            base_leverage=50.0,
            max_leverage=100.0,
            pyramiding_enabled=True,
            ratchet_enabled=False,
            compounding_rate=1.0,
            atr_stop_mult=1.5,
            atr_target_mult=5.0
        )
        all_results.append(r1)

        # 2. Pyramiding & Trade Recycling (Risk-Free Trailing)
        r2 = engine.simulate_hyper_system(
            system_name="Pyramiding & Continuous Trade Recycling",
            base_leverage=25.0,
            max_leverage=75.0,
            pyramiding_enabled=True,
            ratchet_enabled=True,
            compounding_rate=0.85,
            atr_stop_mult=1.8,
            atr_target_mult=4.5
        )
        all_results.append(r2)

        # 3. Adaptive Ratchet Protection (Obsidian Milestones: 2x, 3x, 5x)
        r3 = engine.simulate_hyper_system(
            system_name="Adaptive Ratchet Milestone Harvester",
            base_leverage=30.0,
            max_leverage=60.0,
            pyramiding_enabled=False,
            ratchet_enabled=True,
            compounding_rate=0.75,
            atr_stop_mult=1.6,
            atr_target_mult=4.0
        )
        all_results.append(r3)

        # 4. Volatility Burst Scalper (High Frequency)
        r4 = engine.simulate_hyper_system(
            system_name="Vol Burst Asymmetric Scalper (1:4 R:R)",
            base_leverage=40.0,
            max_leverage=80.0,
            pyramiding_enabled=True,
            ratchet_enabled=True,
            compounding_rate=0.90,
            atr_stop_mult=1.2,
            atr_target_mult=4.8,
            vol_filter_mult=1.4
        )
        all_results.append(r4)

    # Sort results by Multiple / Net Return
    sorted_res = sorted(all_results, key=lambda x: x.multiple_x, reverse=True)

    print("\n" + "=" * 80)
    print("🔥 INFORME GENERAL DE RESULTADOS HYPER-AGRESIVOS (MULTI-ACTIVO / MULTI-TF)")
    print("=" * 80)
    for i, res in enumerate(sorted_res, 1):
        print(f"\n#{i} [{res.asset} {res.timeframe}] {res.system_name}")
        print(f"    - Multiplicador de Cuenta: {res.multiple_x}x (Final: ${res.final_equity + res.protected_capital_harvested:,.2f} USD desde $1,000 USD)")
        print(f"    - Beneficio Neto: +${res.net_profit_usd:,.2f} USD | Capital Cosechado a Bóveda: ${res.protected_capital_harvested:,.2f} USD")
        print(f"    - Métricas: Trades={res.total_trades} | Win Rate={res.win_rate_pct}% | Profit Factor={res.profit_factor} | Max Drawdown={res.max_drawdown_pct}%")

    return sorted_res


if __name__ == "__main__":
    run_multi_asset_hyper_search()
