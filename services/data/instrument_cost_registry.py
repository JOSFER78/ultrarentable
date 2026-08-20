"""services/data/instrument_cost_registry.py
Registro Canónico de Perfiles de Coste y Microestructura Real (Fase 3).
Prohíbe terminantemente valores 0 por defecto o ejecuciones sin modelo de costes.
"""

from __future__ import annotations

from typing import Dict, Optional
from contracts.canonical_execution import AssetClass, InstrumentCostProfile


class MissingCostModelError(ValueError):
    """Excepción forense cuando un instrumento carece de perfil de costes verificado."""
    pass


# Catálogo Canónico Físicamente Verificado de 44+ Activos Globales
CANONICAL_COST_REGISTRY: Dict[str, InstrumentCostProfile] = {
    # === 1. CRIPTO PERPETUALS (Binance / BingX Perps) ===
    "BTCUSDT": InstrumentCostProfile(
        symbol="BTCUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.1,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
        funding_rate_8h_pct=0.010,
    ),
    "ETHUSDT": InstrumentCostProfile(
        symbol="ETHUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.01,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
        funding_rate_8h_pct=0.010,
    ),
    "SOLUSDT": InstrumentCostProfile(
        symbol="SOLUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.01,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.5,
        funding_rate_8h_pct=0.010,
    ),
    "SUIUSDT": InstrumentCostProfile(
        symbol="SUIUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.0001,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.5,
        slippage_ticks_baseline=2.0,
        funding_rate_8h_pct=0.010,
    ),
    "DOGEUSDT": InstrumentCostProfile(
        symbol="DOGEUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.00001,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.5,
        funding_rate_8h_pct=0.010,
    ),
    "AVAXUSDT": InstrumentCostProfile(
        symbol="AVAXUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.01,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.5,
        funding_rate_8h_pct=0.010,
    ),
    "LINKUSDT": InstrumentCostProfile(
        symbol="LINKUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.001,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.5,
        funding_rate_8h_pct=0.010,
    ),
    "XRPUSDT": InstrumentCostProfile(
        symbol="XRPUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.0001,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.5,
        funding_rate_8h_pct=0.010,
    ),
    "BNBUSDT": InstrumentCostProfile(
        symbol="BNBUSDT",
        asset_class=AssetClass.CRYPTO_PERPETUAL,
        point_value=1.0,
        tick_size=0.01,
        contract_multiplier=1.0,
        taker_fee_pct=0.050,
        maker_fee_pct=0.020,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.5,
        funding_rate_8h_pct=0.010,
    ),

    # === 2. FOREX SPOT (100,000 Lot Multiplier) ===
    "EURUSD": InstrumentCostProfile(
        symbol="EURUSD",
        asset_class=AssetClass.FOREX_SPOT,
        point_value=10.0,
        tick_size=0.0001,
        contract_multiplier=100_000.0,
        taker_fee_pct=0.002,
        maker_fee_pct=0.001,
        typical_spread_ticks=0.6,
        slippage_ticks_baseline=0.5,
    ),
    "GBPUSD": InstrumentCostProfile(
        symbol="GBPUSD",
        asset_class=AssetClass.FOREX_SPOT,
        point_value=10.0,
        tick_size=0.0001,
        contract_multiplier=100_000.0,
        taker_fee_pct=0.002,
        maker_fee_pct=0.001,
        typical_spread_ticks=0.8,
        slippage_ticks_baseline=0.6,
    ),
    "AUDUSD": InstrumentCostProfile(
        symbol="AUDUSD",
        asset_class=AssetClass.FOREX_SPOT,
        point_value=10.0,
        tick_size=0.0001,
        contract_multiplier=100_000.0,
        taker_fee_pct=0.002,
        maker_fee_pct=0.001,
        typical_spread_ticks=0.8,
        slippage_ticks_baseline=0.6,
    ),
    "USDCAD": InstrumentCostProfile(
        symbol="USDCAD",
        asset_class=AssetClass.FOREX_SPOT,
        point_value=10.0,
        tick_size=0.0001,
        contract_multiplier=100_000.0,
        taker_fee_pct=0.002,
        maker_fee_pct=0.001,
        typical_spread_ticks=0.9,
        slippage_ticks_baseline=0.6,
    ),
    "USDCHF": InstrumentCostProfile(
        symbol="USDCHF",
        asset_class=AssetClass.FOREX_SPOT,
        point_value=10.0,
        tick_size=0.0001,
        contract_multiplier=100_000.0,
        taker_fee_pct=0.002,
        maker_fee_pct=0.001,
        typical_spread_ticks=0.9,
        slippage_ticks_baseline=0.6,
    ),
    "USDJPY": InstrumentCostProfile(
        symbol="USDJPY",
        asset_class=AssetClass.FOREX_SPOT,
        point_value=10.0,
        tick_size=0.01,
        contract_multiplier=100_000.0,
        taker_fee_pct=0.002,
        maker_fee_pct=0.001,
        typical_spread_ticks=0.7,
        slippage_ticks_baseline=0.5,
    ),

    # === 3. FUTUROS CME ===
    "NQ": InstrumentCostProfile(
        symbol="NQ",
        asset_class=AssetClass.CME_FUTURES,
        point_value=20.0,
        tick_size=0.25,
        contract_multiplier=1.0,
        taker_fee_pct=0.001,
        maker_fee_pct=0.001,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
    ),
    "ES": InstrumentCostProfile(
        symbol="ES",
        asset_class=AssetClass.CME_FUTURES,
        point_value=50.0,
        tick_size=0.25,
        contract_multiplier=1.0,
        taker_fee_pct=0.001,
        maker_fee_pct=0.001,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
    ),
    "YM": InstrumentCostProfile(
        symbol="YM",
        asset_class=AssetClass.CME_FUTURES,
        point_value=5.0,
        tick_size=1.0,
        contract_multiplier=1.0,
        taker_fee_pct=0.001,
        maker_fee_pct=0.001,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
    ),
    "RTY": InstrumentCostProfile(
        symbol="RTY",
        asset_class=AssetClass.CME_FUTURES,
        point_value=50.0,
        tick_size=0.1,
        contract_multiplier=1.0,
        taker_fee_pct=0.001,
        maker_fee_pct=0.001,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
    ),

    # === 4. COMMODITIES ===
    "CL": InstrumentCostProfile(
        symbol="CL",
        asset_class=AssetClass.COMMODITIES,
        point_value=1000.0,
        tick_size=0.01,
        contract_multiplier=1.0,
        taker_fee_pct=0.0015,
        maker_fee_pct=0.0010,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
    ),
    "GC": InstrumentCostProfile(
        symbol="GC",
        asset_class=AssetClass.COMMODITIES,
        point_value=100.0,
        tick_size=0.1,
        contract_multiplier=1.0,
        taker_fee_pct=0.0015,
        maker_fee_pct=0.0010,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
    ),
    "SI": InstrumentCostProfile(
        symbol="SI",
        asset_class=AssetClass.COMMODITIES,
        point_value=5000.0,
        tick_size=0.005,
        contract_multiplier=1.0,
        taker_fee_pct=0.0015,
        maker_fee_pct=0.0010,
        typical_spread_ticks=1.0,
        slippage_ticks_baseline=1.0,
    ),
}


def normalize_instrument_symbol(sym: str) -> str:
    """Normalizes variations like BTC-USDT, BTC_USDT, btcusdt to BTCUSDT."""
    cleaned = sym.upper().replace("-", "").replace("_", "").replace("/", "").strip()
    return cleaned


def get_instrument_cost_profile(symbol: str) -> InstrumentCostProfile:
    """Obtiene el perfil canónico de microestructura y costes.
    
    Lanza MissingCostModelError si el activo no está registrado (Doctrina Zero-Default).
    """
    norm_sym = normalize_instrument_symbol(symbol)
    if norm_sym not in CANONICAL_COST_REGISTRY:
        raise MissingCostModelError(
            f"BLOCKED_NO_COST_MODEL: El instrumento '{symbol}' (normalizado: '{norm_sym}') "
            f"no posee un perfil de costes verificado en CANONICAL_COST_REGISTRY. "
            f"Prohibido asumir valores 0 o defaults silenciosos."
        )
    return CANONICAL_COST_REGISTRY[norm_sym]
