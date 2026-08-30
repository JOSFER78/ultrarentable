"""Universe Market Matrix Core Definitions.

Defines the asset classes, symbols, supported timeframes (1m, 5m, 15m, 1h, 4h),
and trading archetypes for multi-market quantitative strategy generation across:
- RUTA ULTRA: 44 Activos (Convexidad 500x, Pyramiding agresivo, todo el universo cripto, índices, forex y commodities).
- RUTA FONDEO: Solo Activos Aprobados por Empresas de Fondeo Reguladas (FTMO, Apex, Topstep, FundedNext, Alpha Capital).
  En Cripto Fondeo: Se limita estrictamente a los 9 activos mayores (BTC, ETH, SOL, XRP, ADA, BNB, DOGE, LINK, AVAX).
  Excluye altcoins de baja liquidez que no se permiten en prop firms.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List
from services.api.app.validation.market_specs import get_market_spec


class AssetClass(str, Enum):
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    INDICES_FUTURES = "INDICES_FUTURES"
    COMMODITIES = "COMMODITIES"


class Timeframe(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


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


# Universo Canónico Completo de 44 Activos
ALL_SYMBOLS_SPECS = [
    # ── 1. CRIPTO PERPETUOS (18 ACTIVOS) ──
    ("BTC-USDT", AssetClass.CRYPTO, "Bitcoin Perpetuo"),
    ("ETH-USDT", AssetClass.CRYPTO, "Ethereum Perpetuo"),
    ("SOL-USDT", AssetClass.CRYPTO, "Solana Perpetuo"),
    ("SUI-USDT", AssetClass.CRYPTO, "Sui Network Perpetuo"),
    ("LINK-USDT", AssetClass.CRYPTO, "Chainlink Perpetuo"),
    ("AVAX-USDT", AssetClass.CRYPTO, "Avalanche Perpetuo"),
    ("BNB-USDT", AssetClass.CRYPTO, "BNB Chain Perpetuo"),
    ("NEAR-USDT", AssetClass.CRYPTO, "Near Protocol Perpetuo"),
    ("APT-USDT", AssetClass.CRYPTO, "Aptos Perpetuo"),
    ("INJ-USDT", AssetClass.CRYPTO, "Injective Perpetuo"),
    ("RENDER-USDT", AssetClass.CRYPTO, "Render Perpetuo"),
    ("ARB-USDT", AssetClass.CRYPTO, "Arbitrum Perpetuo"),
    ("OP-USDT", AssetClass.CRYPTO, "Optimism Perpetuo"),
    ("TIA-USDT", AssetClass.CRYPTO, "Celestia Perpetuo"),
    ("FET-USDT", AssetClass.CRYPTO, "Fetch.ai Perpetuo"),
    ("DOGE-USDT", AssetClass.CRYPTO, "Dogecoin Perpetuo"),
    ("XRP-USDT", AssetClass.CRYPTO, "XRP Perpetuo"),
    ("ADA-USDT", AssetClass.CRYPTO, "Cardano Perpetuo"),

    # ── 2. ÍNDICES CME & GLOBALES (9 ACTIVOS) ──
    ("NQ", AssetClass.INDICES_FUTURES, "E-mini Nasdaq 100"),
    ("ES", AssetClass.INDICES_FUTURES, "E-mini S&P 500"),
    ("YM", AssetClass.INDICES_FUTURES, "E-mini Dow Jones"),
    ("RTY", AssetClass.INDICES_FUTURES, "E-mini Russell 2000"),
    ("FDAX", AssetClass.INDICES_FUTURES, "DAX 40 Futures"),
    ("FTSE", AssetClass.INDICES_FUTURES, "FTSE 100 Index Futures"),
    ("NK225", AssetClass.INDICES_FUTURES, "Nikkei 225 Futures"),
    ("HSI", AssetClass.INDICES_FUTURES, "Hang Seng Futures"),
    ("STOXX50", AssetClass.INDICES_FUTURES, "Euro Stoxx 50"),

    # ── 3. FOREX MAJORS & CRUCES (10 ACTIVOS) ──
    ("EURUSD", AssetClass.FOREX, "Euro / US Dollar"),
    ("USDJPY", AssetClass.FOREX, "US Dollar / Japanese Yen"),
    ("GBPJPY", AssetClass.FOREX, "British Pound / Yen"),
    ("GBPUSD", AssetClass.FOREX, "British Pound / USD"),
    ("EURJPY", AssetClass.FOREX, "Euro / Japanese Yen"),
    ("USDCAD", AssetClass.FOREX, "US Dollar / Canadian Dollar"),
    ("AUDUSD", AssetClass.FOREX, "Australian Dollar / USD"),
    ("USDCHF", AssetClass.FOREX, "US Dollar / Swiss Franc"),
    ("NZDUSD", AssetClass.FOREX, "New Zealand Dollar / USD"),
    ("EURGBP", AssetClass.FOREX, "Euro / British Pound"),

    # ── 4. COMMODITIES (7 ACTIVOS) ──
    ("GC", AssetClass.COMMODITIES, "Oro COMEX Gold Futures"),
    ("XAUUSD", AssetClass.COMMODITIES, "Oro Spot / Gold FX"),
    ("SI", AssetClass.COMMODITIES, "Plata COMEX Silver Futures"),
    ("CL", AssetClass.COMMODITIES, "Petróleo Crudo WTI"),
    ("BRENT", AssetClass.COMMODITIES, "Petróleo Brent"),
    ("NG", AssetClass.COMMODITIES, "Gas Natural Henry Hub"),
    ("HG", AssetClass.COMMODITIES, "Cobre High Grade"),
]

INTRADAY_TIMEFRAMES: List[Timeframe] = [
    Timeframe.M1,
    Timeframe.M5,
    Timeframe.M15,
    Timeframe.H1,
    Timeframe.H4,
]

CANONICAL_UNIVERSE_MATRIX: List[MarketCell] = []

for sym, aclass, name in ALL_SYMBOLS_SPECS:
    spec = get_market_spec(sym)
    
    # 1. RUTA ULTRA: DISPONIBLE PARA TODOS LOS 44 ACTIVOS EN TODAS LAS TEMPORALIDADES INTRADÍA (1m, 5m, 15m, 1h, 4h)
    for tf in INTRADAY_TIMEFRAMES:
        CANONICAL_UNIVERSE_MATRIX.append(
            MarketCell(
                symbol=sym,
                asset_class=aclass,
                timeframe=tf,
                target_route=TargetRoute.ULTRA,
                primary_archetype=StrategyArchetype.VOLATILITY_BREAKOUT if aclass != AssetClass.FOREX else StrategyArchetype.TREND_MOMENTUM,
                description=f"{sym} [{tf.value}] ULTRA Convexidad Intradía ({name})",
                max_dd_limit_pct=75.0,
                min_pf_target=1.20,
            )
        )
    
    # 2. RUTA FONDEO: DISPONIBLE PARA ACTIVOS ADMITIDOS EN PROP FIRMS EN TODAS LAS TEMPORALIDADES INTRADÍA (1m, 5m, 15m, 1h, 4h)
    if spec.prop_firm_eligible:
        for tf in INTRADAY_TIMEFRAMES:
            CANONICAL_UNIVERSE_MATRIX.append(
                MarketCell(
                    symbol=sym,
                    asset_class=aclass,
                    timeframe=tf,
                    target_route=TargetRoute.FONDEO,
                    primary_archetype=StrategyArchetype.TREND_MOMENTUM if aclass == AssetClass.INDICES_FUTURES else StrategyArchetype.OPENING_RANGE_BREAKOUT,
                    description=f"{sym} [{tf.value}] FONDEO Prop Firm [{spec.prop_firm_venues}] Intradía ({name})",
                    max_dd_limit_pct=4.0,
                    min_pf_target=1.25,
                )
            )


def get_matrix_by_symbol(symbol: str) -> List[MarketCell]:
    return [c for c in CANONICAL_UNIVERSE_MATRIX if c.symbol == symbol]


def get_matrix_by_timeframe(tf: Timeframe) -> List[MarketCell]:
    return [c for c in CANONICAL_UNIVERSE_MATRIX if c.timeframe == tf]


def get_matrix_by_asset_class(ac: AssetClass) -> List[MarketCell]:
    return [c for c in CANONICAL_UNIVERSE_MATRIX if c.asset_class == ac]
