"""Universe Market Matrix Core Definitions.

Defines the asset classes, symbols, supported timeframes (1m, 5m, 15m, 1h, 4h),
and trading archetypes for multi-market quantitative strategy generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AssetClass(str, Enum):
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    INDICES_FUTURES = "INDICES_FUTURES"


class Timeframe(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"


class StrategyArchetype(str, Enum):
    VOLATILITY_BREAKOUT = "VOLATILITY_BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    OPENING_RANGE_BREAKOUT = "OPENING_RANGE_BREAKOUT"
    TREND_MOMENTUM = "TREND_MOMENTUM"


class TargetRoute(str, Enum):
    ULTRA = "ULTRA"
    FONDEO = "FONDEO"


@dataclass(frozen=True)
class MarketCell:
    symbol: str
    asset_class: AssetClass
    timeframe: Timeframe
    target_route: TargetRoute
    primary_archetype: StrategyArchetype
    description: str
    max_dd_limit_pct: float
    min_pf_target: float


# Matriz canónica del universo de búsqueda
CANONICAL_UNIVERSE_MATRIX: List[MarketCell] = [
    # ══════════════════════════════════════════════════════════════════════════════
    # ── 1. RUTA ULTRA (BingX Crypto Perps — Convexidad Kamikaze & Pyramiding 500x) ──
    # ══════════════════════════════════════════════════════════════════════════════
    MarketCell(symbol="SOL-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M5, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="SOL High Volatility Breakout 5m", max_dd_limit_pct=15.0, min_pf_target=1.25),
    MarketCell(symbol="SOL-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="SOL Trend Momentum 15m", max_dd_limit_pct=15.0, min_pf_target=1.30),
    MarketCell(symbol="SOL-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.H1, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="SOL Trend Following 1h", max_dd_limit_pct=20.0, min_pf_target=1.35),
    
    MarketCell(symbol="BTC-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M1, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="BTC Micro Breakout 1m", max_dd_limit_pct=10.0, min_pf_target=1.20),
    MarketCell(symbol="BTC-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M5, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="BTC Momentum Intradía 5m", max_dd_limit_pct=10.0, min_pf_target=1.25),
    MarketCell(symbol="BTC-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="BTC Volatility Breakout 15m", max_dd_limit_pct=12.0, min_pf_target=1.25),
    MarketCell(symbol="BTC-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.H1, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="BTC Trend Following Swing 1h", max_dd_limit_pct=15.0, min_pf_target=1.30),

    MarketCell(symbol="ETH-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M5, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="ETH Breakout Donchian 5m", max_dd_limit_pct=10.0, min_pf_target=1.25),
    MarketCell(symbol="ETH-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="ETH SuperTrend Momentum 15m", max_dd_limit_pct=12.0, min_pf_target=1.30),
    MarketCell(symbol="ETH-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.H1, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="ETH Dual Moving Average 1h", max_dd_limit_pct=15.0, min_pf_target=1.35),

    MarketCell(symbol="DOGE-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M5, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="DOGE Explosive Volume 5m", max_dd_limit_pct=15.0, min_pf_target=1.20),
    MarketCell(symbol="DOGE-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.H1, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="DOGE Momentum Follow 1h", max_dd_limit_pct=20.0, min_pf_target=1.30),

    MarketCell(symbol="PEPE-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M5, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="PEPE Meme Squeeze 5m", max_dd_limit_pct=20.0, min_pf_target=1.25),
    MarketCell(symbol="PEPE-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="PEPE Trend Pyramiding 15m", max_dd_limit_pct=20.0, min_pf_target=1.30),

    MarketCell(symbol="AVAX-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M5, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="AVAX Volatility Squeeze 5m", max_dd_limit_pct=15.0, min_pf_target=1.25),
    MarketCell(symbol="LINK-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="LINK Oracle Momentum 15m", max_dd_limit_pct=15.0, min_pf_target=1.30),
    MarketCell(symbol="XRP-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.H1, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="XRP Breakout Trend 1h", max_dd_limit_pct=15.0, min_pf_target=1.30),
    MarketCell(symbol="BNB-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="BNB Trend Channel 15m", max_dd_limit_pct=12.0, min_pf_target=1.30),
    MarketCell(symbol="SUI-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M5, target_route=TargetRoute.ULTRA, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="SUI Hyperscale Breakout 5m", max_dd_limit_pct=20.0, min_pf_target=1.25),

    # ══════════════════════════════════════════════════════════════════════════════
    # ── 2. RUTA FONDEO (CME Prop Firms: Apex, Topstep, FTMO, TradeDay — DD <= 4%) ─
    # ══════════════════════════════════════════════════════════════════════════════
    # CME Futuros Índices
    MarketCell(symbol="NQ", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M1, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.OPENING_RANGE_BREAKOUT, description="NQ Micro Scalp 1m (NY Open)", max_dd_limit_pct=3.5, min_pf_target=1.25),
    MarketCell(symbol="NQ", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M5, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.OPENING_RANGE_BREAKOUT, description="NQ ORB 5m (NY Session)", max_dd_limit_pct=4.0, min_pf_target=1.30),
    MarketCell(symbol="NQ", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="NQ Momentum Breakout 15m", max_dd_limit_pct=4.0, min_pf_target=1.35),
    MarketCell(symbol="MNQ", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M5, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.OPENING_RANGE_BREAKOUT, description="Micro Nasdaq 5m Fondeo Sprint", max_dd_limit_pct=3.5, min_pf_target=1.30),
    
    MarketCell(symbol="ES", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M5, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.MEAN_REVERSION, description="S&P 500 Pullback Reversion 5m", max_dd_limit_pct=3.5, min_pf_target=1.25),
    MarketCell(symbol="ES", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="S&P 500 Trend Following 15m", max_dd_limit_pct=4.0, min_pf_target=1.30),
    MarketCell(symbol="MES", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.MEAN_REVERSION, description="Micro S&P 15m Preservación", max_dd_limit_pct=3.5, min_pf_target=1.25),
    
    MarketCell(symbol="YM", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="Dow Jones 15m Trend Momentum", max_dd_limit_pct=4.0, min_pf_target=1.30),
    MarketCell(symbol="RTY", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="Russell 2000 15m Small-Caps Breakout", max_dd_limit_pct=4.0, min_pf_target=1.30),

    # CME Commodities
    MarketCell(symbol="CL", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="Crude Oil WTI 15m Energy Breakout", max_dd_limit_pct=4.0, min_pf_target=1.30),
    MarketCell(symbol="GC", asset_class=AssetClass.INDICES_FUTURES, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="Gold CME Futures 15m Safe-Haven Trend", max_dd_limit_pct=3.5, min_pf_target=1.35),
    MarketCell(symbol="XAUUSD", asset_class=AssetClass.FOREX, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="Gold Spot XAUUSD 15m Prop Firm Sprint", max_dd_limit_pct=3.5, min_pf_target=1.35),

    # Forex Prop Firms (FTMO, Alpha Capital, FundedNext)
    MarketCell(symbol="EURUSD", asset_class=AssetClass.FOREX, timeframe=Timeframe.M5, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.MEAN_REVERSION, description="EURUSD RSI Extremes 5m", max_dd_limit_pct=3.5, min_pf_target=1.25),
    MarketCell(symbol="EURUSD", asset_class=AssetClass.FOREX, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.OPENING_RANGE_BREAKOUT, description="EURUSD London Open ORB 15m", max_dd_limit_pct=4.0, min_pf_target=1.30),
    MarketCell(symbol="EURUSD", asset_class=AssetClass.FOREX, timeframe=Timeframe.H1, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.MEAN_REVERSION, description="EURUSD Bollinger Mean Reversion 1h", max_dd_limit_pct=4.0, min_pf_target=1.35),
    
    MarketCell(symbol="GBPUSD", asset_class=AssetClass.FOREX, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.OPENING_RANGE_BREAKOUT, description="GBPUSD London Breakout 15m", max_dd_limit_pct=4.0, min_pf_target=1.30),
    MarketCell(symbol="GBPUSD", asset_class=AssetClass.FOREX, timeframe=Timeframe.H1, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="GBPUSD Trend Pullback 1h", max_dd_limit_pct=4.0, min_pf_target=1.35),

    MarketCell(symbol="USDJPY", asset_class=AssetClass.FOREX, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="USDJPY Tokyo & NY Trend 15m", max_dd_limit_pct=3.5, min_pf_target=1.30),
    MarketCell(symbol="AUDUSD", asset_class=AssetClass.FOREX, timeframe=Timeframe.H1, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.MEAN_REVERSION, description="AUDUSD Commodity Currency Reversion 1h", max_dd_limit_pct=4.0, min_pf_target=1.30),
    MarketCell(symbol="USDCAD", asset_class=AssetClass.FOREX, timeframe=Timeframe.H1, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="USDCAD Oil Correlation Trend 1h", max_dd_limit_pct=4.0, min_pf_target=1.30),

    # Crypto en Prop Firms (FTMO Crypto, BingX Prop)
    MarketCell(symbol="BTC-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="BTC Prop Firm Preservation 15m (DD <= 4%)", max_dd_limit_pct=3.5, min_pf_target=1.30),
    MarketCell(symbol="ETH-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.TREND_MOMENTUM, description="ETH Prop Firm Preservation 15m (DD <= 4%)", max_dd_limit_pct=3.5, min_pf_target=1.30),
    MarketCell(symbol="SOL-USDT", asset_class=AssetClass.CRYPTO, timeframe=Timeframe.M15, target_route=TargetRoute.FONDEO, primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT, description="SOL Prop Firm Preservation 15m (DD <= 4%)", max_dd_limit_pct=4.0, min_pf_target=1.30),
]


def get_matrix_by_symbol(symbol: str) -> List[MarketCell]:
    return [c for c in CANONICAL_UNIVERSE_MATRIX if c.symbol == symbol]


def get_matrix_by_timeframe(tf: Timeframe) -> List[MarketCell]:
    return [c for c in CANONICAL_UNIVERSE_MATRIX if c.timeframe == tf]


def get_matrix_by_asset_class(ac: AssetClass) -> List[MarketCell]:
    return [c for c in CANONICAL_UNIVERSE_MATRIX if c.asset_class == ac]
