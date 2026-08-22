"""services/engine/instrument_registry.py
Global Registry of Universal Instrument Specifications (v3.0.0).

DOCTRINA ZERO-HARDCODED ASSETS:
- Pre-registers accurate microstructural specs for 100% of global markets (Crypto Perpetuals, CME Futures, Forex).
- Allows dynamic lookup by symbol or custom specification registration.
"""

from __future__ import annotations

from typing import Dict, Optional
from contracts.instrument_specification import (
    AssetClass,
    CommissionType,
    InstrumentSpecification,
    MaintenanceTier,
)


class InstrumentRegistry:
    """Registro maestro de especificaciones de microestructura de instrumentos."""

    _registry: Dict[str, InstrumentSpecification] = {}

    @classmethod
    def register(cls, spec: InstrumentSpecification) -> None:
        key = cls.normalize_symbol(spec.symbol)
        cls._registry[key] = spec

    @classmethod
    def normalize_symbol(cls, symbol: str) -> str:
        return symbol.upper().replace("-", "").replace("/", "").replace("_", "").strip()

    @classmethod
    def get(cls, symbol: str) -> InstrumentSpecification:
        """Obtiene la especificación exacta de un activo o genera una basada en su clase."""
        key = cls.normalize_symbol(symbol)
        if key in cls._registry:
            return cls._registry[key]

        # Inferencia forense si no está explícitamente en el diccionario estático
        return cls._create_inferred_spec(symbol)

    @classmethod
    def _create_inferred_spec(cls, symbol: str) -> InstrumentSpecification:
        norm = cls.normalize_symbol(symbol)
        
        # 1. Cripto Perpetuos (e.g. BTCUSDT, ETHUSDT, SOLUSDT, etc.)
        if "USDT" in norm or "USD" in norm and len(norm) > 6:
            base = norm.replace("USDT", "").replace("USD", "")
            return InstrumentSpecification(
                symbol=f"{base}-USDT",
                raw_symbol=norm,
                asset_class=AssetClass.CRYPTO_PERPETUAL,
                exchange_or_venue="BINGX",
                base_currency=base,
                quote_currency="USDT",
                tick_size=0.1 if "BTC" in norm else (0.01 if "ETH" in norm or "SOL" in norm else 0.0001),
                point_value=1.0,
                contract_size=1.0,
                min_quantity=0.001 if "BTC" in norm else (0.01 if "ETH" in norm else 0.1),
                quantity_step=0.001 if "BTC" in norm else 0.01,
                price_precision=2 if "BTC" in norm or "ETH" in norm or "SOL" in norm else 4,
                quantity_precision=3 if "BTC" in norm else 2,
                commission_type=CommissionType.PERCENTAGE_OF_NOTIONAL,
                taker_fee_rate=0.0005,  # 0.05%
                maker_fee_rate=0.0002,  # 0.02%
                max_allowed_leverage=100.0,
                initial_margin_rate=0.01,
                maintenance_margin_rate=0.005,
                is_perpetual=True,
                default_funding_rate=0.0001,
            )

        # 2. Futuros CME & Materias Primas (NQ, ES, GC, SI, CL, YM, RTY, NG, FDAX, etc.)
        cme_specs = {
            "NQ": {"tick_size": 0.25, "point_value": 20.0, "cme_fee": 2.50, "prec": 2, "name": "Nasdaq 100 E-mini"},
            "MNQ": {"tick_size": 0.25, "point_value": 2.0, "cme_fee": 0.60, "prec": 2, "name": "Micro Nasdaq 100"},
            "ES": {"tick_size": 0.25, "point_value": 50.0, "cme_fee": 2.50, "prec": 2, "name": "S&P 500 E-mini"},
            "MES": {"tick_size": 0.25, "point_value": 5.0, "cme_fee": 0.60, "prec": 2, "name": "Micro S&P 500"},
            "GC": {"tick_size": 0.10, "point_value": 100.0, "cme_fee": 2.50, "prec": 1, "name": "Gold Futures"},
            "MGC": {"tick_size": 0.10, "point_value": 10.0, "cme_fee": 0.60, "prec": 1, "name": "Micro Gold"},
            "SI": {"tick_size": 0.005, "point_value": 5000.0, "cme_fee": 2.50, "prec": 3, "name": "Silver Futures"},
            "CL": {"tick_size": 0.01, "point_value": 1000.0, "cme_fee": 2.50, "prec": 2, "name": "Crude Oil Futures"},
            "MCL": {"tick_size": 0.01, "point_value": 100.0, "cme_fee": 0.60, "prec": 2, "name": "Micro Crude Oil"},
            "YM": {"tick_size": 1.0, "point_value": 5.0, "cme_fee": 2.50, "prec": 0, "name": "Dow Jones E-mini"},
            "MYM": {"tick_size": 1.0, "point_value": 0.5, "cme_fee": 0.60, "prec": 0, "name": "Micro Dow Jones"},
            "RTY": {"tick_size": 0.10, "point_value": 50.0, "cme_fee": 2.50, "prec": 1, "name": "Russell 2000 E-mini"},
            "M2K": {"tick_size": 0.10, "point_value": 5.0, "cme_fee": 0.60, "prec": 1, "name": "Micro Russell 2000"},
            "NG": {"tick_size": 0.001, "point_value": 10000.0, "cme_fee": 2.50, "prec": 3, "name": "Natural Gas Futures"},
            "FDAX": {"tick_size": 0.50, "point_value": 25.0, "cme_fee": 2.50, "prec": 1, "name": "DAX Futures"},
            "FTSE": {"tick_size": 0.50, "point_value": 10.0, "cme_fee": 2.50, "prec": 1, "name": "FTSE 100 Futures"},
            "NK225": {"tick_size": 5.0, "point_value": 5.0, "cme_fee": 2.50, "prec": 0, "name": "Nikkei 225 Futures"},
        }

        for cme_key, info in cme_specs.items():
            if norm.startswith(cme_key):
                return InstrumentSpecification(
                    symbol=cme_key,
                    raw_symbol=symbol,
                    asset_class=AssetClass.CME_FUTURES,
                    exchange_or_venue="CME",
                    base_currency=cme_key,
                    quote_currency="USD",
                    tick_size=info["tick_size"],
                    point_value=info["point_value"],
                    contract_size=1.0,
                    min_quantity=1.0,
                    quantity_step=1.0,
                    price_precision=info["prec"],
                    quantity_precision=0,
                    commission_type=CommissionType.FIXED_PER_CONTRACT,
                    cme_exchange_fee_per_contract=info["cme_fee"],
                    max_allowed_leverage=1.0,  # 1 contrato nominal
                    initial_margin_rate=0.10,
                    maintenance_margin_rate=0.08,
                    is_perpetual=False,
                )

        # 3. Forex Majors & Cruces (EURUSD, GBPUSD, USDJPY, USDCAD, USDCHF, AUDUSD, NZDUSD, EURJPY, GBPJPY, EURGBP, CADJPY)
        forex_pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "USDCHF", "AUDUSD", "NZDUSD",
            "EURJPY", "GBPJPY", "EURGBP", "CADJPY", "AUDJPY", "NZDJPY", "CHFJPY",
        ]
        for fx in forex_pairs:
            if norm.startswith(fx):
                is_jpy = "JPY" in fx
                return InstrumentSpecification(
                    symbol=fx,
                    raw_symbol=symbol,
                    asset_class=AssetClass.FOREX_MAJOR if ("EUR" in fx or "GBP" in fx or "JPY" in fx) else AssetClass.FOREX_CROSS,
                    exchange_or_venue="INTERBANK",
                    base_currency=fx[:3],
                    quote_currency=fx[3:],
                    tick_size=0.001 if is_jpy else 0.00001,
                    point_value=10.0,  # $10 per pip on 1 standard lot
                    contract_size=100000.0,
                    min_quantity=0.01,
                    quantity_step=0.01,
                    price_precision=3 if is_jpy else 5,
                    quantity_precision=2,
                    commission_type=CommissionType.PER_LOT,
                    taker_fee_rate=0.00005,
                    max_allowed_leverage=30.0,
                    initial_margin_rate=0.033,
                    maintenance_margin_rate=0.02,
                    is_perpetual=False,
                )

        # Default Generic Instrument
        return InstrumentSpecification(
            symbol=symbol,
            raw_symbol=symbol,
            asset_class=AssetClass.COMMODITY,
            exchange_or_venue="GENERIC",
            base_currency=symbol,
            quote_currency="USD",
            tick_size=0.01,
            point_value=1.0,
            contract_size=1.0,
            min_quantity=1.0,
            quantity_step=1.0,
            price_precision=2,
            quantity_precision=2,
            commission_type=CommissionType.PERCENTAGE_OF_NOTIONAL,
            taker_fee_rate=0.0005,
            max_allowed_leverage=10.0,
            initial_margin_rate=0.10,
            maintenance_margin_rate=0.05,
        )


# Pre-cargar catálogo canónico al importar
_CANONICAL_SYMBOLS = [
    # 1. Cripto Perpetuos (Ruta ULTRA 100% de activos)
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "SUI-USDT", "DOGE-USDT", "AVAX-USDT", "BNB-USDT", "LINK-USDT", "XRP-USDT",
    "ADA-USDT", "DOT-USDT", "NEAR-USDT", "APT-USDT", "MATIC-USDT", "PEPE-USDT", "SHIB-USDT", "ARB-USDT", "OP-USDT", "TIA-USDT",
    # 2. Futuros CME & Materias Primas (Ruta FONDEO y ULTRA)
    "NQ", "MNQ", "ES", "MES", "YM", "MYM", "RTY", "M2K", "GC", "MGC", "SI", "CL", "MCL", "NG", "FDAX", "FTSE", "NK225",
    # 3. Forex Majors & Cruces (Ruta FONDEO y ULTRA)
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "USDCHF", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "CADJPY",
]

for sym in _CANONICAL_SYMBOLS:
    InstrumentRegistry.register(InstrumentRegistry._create_inferred_spec(sym))
