"""services/api/app/validation/market_specs.py
Especificaciones cuantitativas institucionales para el universo multiactivo 24/7:
- Criptoactivos (Perpetuos USDT)
- Índices Globales y Futuros CME (NQ, ES, YM, RTY, FDAX, FTSE, NK225, HSI, STOXX50)
- Forex Majors & Crosses (EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD, EURJPY, GBPJPY, EURGBP)
- Commodities: Metales & Energías (XAUUSD/GC, XAGUSD/SI, WTI/CL, BRENT, NATGAS/NG, COPPER/HG, PLATINUM/PL)

Incluye elegibilidad real para Empresas de Fondeo (FTMO, Apex, Topstep, FundedNext, Alpha Capital) vs Ruta Ultra.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MarketSpec:
    symbol: str
    canonical_name: str
    category: str  # "CRYPTO" | "INDICES" | "FOREX" | "COMMODITIES"
    exchange: str
    point_value: float  # USD por punto entero
    tick_size: float  # Tamaño mínimo de tick
    fee_rate: float  # Tasa de comisión porcentual (si aplica, ej 0.0005)
    fee_fixed_usd: float  # Comisión fija por contrato/lote (ej $2.50)
    slippage_ticks: int  # Ticks estándar de deslizamiento institucional
    max_leverage: float  # Techo de apalancamiento
    maint_margin_pct: float  # Margen de mantenimiento requerido (%)
    default_timeframe: str
    typical_regime: str
    icon: str
    prop_firm_eligible: bool  # True si está permitido en prop firms reguladas
    prop_firm_venues: str  # Empresas que lo aceptan


MARKET_SPECS: Dict[str, MarketSpec] = {
    # =========================================================================
    # 1. CRIPTO (18 ACTIVOS) — RUTA ULTRA (TODOS) vs RUTA FONDEO (SOLO TOP MAJORS)
    # =========================================================================
    "BTCUSDT": MarketSpec(
        symbol="BTCUSDT", canonical_name="Bitcoin Perpetuo", category="CRYPTO",
        exchange="Binance / BingX / FTMO", point_value=1.0, tick_size=0.1, fee_rate=0.0004,
        fee_fixed_usd=0.0, slippage_ticks=2, max_leverage=500.0, maint_margin_pct=0.4,
        default_timeframe="1h", typical_regime="Vol Expansion", icon="₿",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext / Alpha Capital / BingX Prop"
    ),
    "ETHUSDT": MarketSpec(
        symbol="ETHUSDT", canonical_name="Ethereum Perpetuo", category="CRYPTO",
        exchange="Binance / BingX / FTMO", point_value=1.0, tick_size=0.01, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=2, max_leverage=500.0, maint_margin_pct=0.4,
        default_timeframe="1h", typical_regime="Donchian Trend", icon="⟠",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext / Alpha Capital / BingX Prop"
    ),
    "SOLUSDT": MarketSpec(
        symbol="SOLUSDT", canonical_name="Solana Perpetuo", category="CRYPTO",
        exchange="Binance / BingX / FTMO", point_value=1.0, tick_size=0.01, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=2, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="EMA Pullback", icon="☀️",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext / Alpha Capital"
    ),
    "XRPUSDT": MarketSpec(
        symbol="XRPUSDT", canonical_name="XRP Perpetuo", category="CRYPTO",
        exchange="Binance / FTMO / BingX", point_value=1.0, tick_size=0.0001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Breakout Flow", icon="✕",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext"
    ),
    "ADAUSDT": MarketSpec(
        symbol="ADAUSDT", canonical_name="Cardano Perpetuo", category="CRYPTO",
        exchange="Binance / FTMO / BingX", point_value=1.0, tick_size=0.0001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Low Vol Chop", icon="🔷",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext"
    ),
    "BNBUSDT": MarketSpec(
        symbol="BNBUSDT", canonical_name="BNB Chain Perpetuo", category="CRYPTO",
        exchange="Binance / FTMO Perps", point_value=1.0, tick_size=0.01, fee_rate=0.0004,
        fee_fixed_usd=0.0, slippage_ticks=2, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Mean Reversion", icon="🟡",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext"
    ),
    "DOGEUSDT": MarketSpec(
        symbol="DOGEUSDT", canonical_name="Dogecoin Perpetuo", category="CRYPTO",
        exchange="Binance / FTMO Perps", point_value=1.0, tick_size=0.00001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Chop Market", icon="🐕",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext"
    ),
    "LINKUSDT": MarketSpec(
        symbol="LINKUSDT", canonical_name="Chainlink Perpetuo", category="CRYPTO",
        exchange="Binance / FTMO Perps", point_value=1.0, tick_size=0.001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Momentum Breakout", icon="🔗",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext"
    ),
    "AVAXUSDT": MarketSpec(
        symbol="AVAXUSDT", canonical_name="Avalanche Perpetuo", category="CRYPTO",
        exchange="Binance / FTMO Perps", point_value=1.0, tick_size=0.01, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Breakout Range", icon="🔺",
        prop_firm_eligible=True, prop_firm_venues="FTMO / FundedNext"
    ),

    # ── Criptos Exclusivos de RUTA ULTRA (No aceptados en prop firms clásicas por baja liquidez / alta volatilidad) ──
    "SUIUSDT": MarketSpec(
        symbol="SUIUSDT", canonical_name="Sui Network Perpetuo", category="CRYPTO",
        exchange="BingX / Binance Perps", point_value=1.0, tick_size=0.0001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Trend Expansion", icon="💧",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),
    "NEARUSDT": MarketSpec(
        symbol="NEARUSDT", canonical_name="Near Protocol Perpetuo", category="CRYPTO",
        exchange="BingX Perps", point_value=1.0, tick_size=0.001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Volatility Breakout", icon="🌐",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),
    "APTUSDT": MarketSpec(
        symbol="APTUSDT", canonical_name="Aptos Perpetuo", category="CRYPTO",
        exchange="BingX Perps", point_value=1.0, tick_size=0.001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Trend Momentum", icon="⚡",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),
    "INJUSDT": MarketSpec(
        symbol="INJUSDT", canonical_name="Injective Perpetuo", category="CRYPTO",
        exchange="BingX Perps", point_value=1.0, tick_size=0.001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Momentum Expansion", icon="🎯",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),
    "RENDERUSDT": MarketSpec(
        symbol="RENDERUSDT", canonical_name="Render Perpetuo", category="CRYPTO",
        exchange="BingX Perps", point_value=1.0, tick_size=0.001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="AI Narrative Break", icon="🎨",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),
    "ARBUSDT": MarketSpec(
        symbol="ARBUSDT", canonical_name="Arbitrum Perpetuo", category="CRYPTO",
        exchange="BingX Perps", point_value=1.0, tick_size=0.0001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Compression Break", icon="🔵",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),
    "OPUSDT": MarketSpec(
        symbol="OPUSDT", canonical_name="Optimism Perpetuo", category="CRYPTO",
        exchange="BingX Perps", point_value=1.0, tick_size=0.0001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Pullback Trend", icon="🔴",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),
    "TIAUSDT": MarketSpec(
        symbol="TIAUSDT", canonical_name="Celestia Perpetuo", category="CRYPTO",
        exchange="BingX Perps", point_value=1.0, tick_size=0.001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="High Beta Trend", icon="🟣",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),
    "FETUSDT": MarketSpec(
        symbol="FETUSDT", canonical_name="Fetch.ai Perpetuo", category="CRYPTO",
        exchange="BingX Perps", point_value=1.0, tick_size=0.0001, fee_rate=0.0005,
        fee_fixed_usd=0.0, slippage_ticks=3, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Channel Breakout", icon="🤖",
        prop_firm_eligible=False, prop_firm_venues="Solo Ruta ULTRA (BingX 500x)"
    ),

    # =========================================================================
    # 2. ÍNDICES GLOBALES Y CME FUTURES (9 ACTIVOS) — PERMITIDOS EN FONDEO & ULTRA
    # =========================================================================
    "NQ": MarketSpec(
        symbol="NQ", canonical_name="E-mini Nasdaq 100", category="INDICES",
        exchange="CME Globex", point_value=20.0, tick_size=0.25, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="Opening Range Breakout", icon="📈",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox / FTMO"
    ),
    "ES": MarketSpec(
        symbol="ES", canonical_name="E-mini S&P 500", category="INDICES",
        exchange="CME Globex", point_value=50.0, tick_size=0.25, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="NY Session Trend", icon="🏛️",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox / FTMO"
    ),
    "YM": MarketSpec(
        symbol="YM", canonical_name="E-mini Dow Jones ($5)", category="INDICES",
        exchange="CBOT Globex", point_value=5.0, tick_size=1.0, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="Value Rotation Trend", icon="🏭",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox"
    ),
    "RTY": MarketSpec(
        symbol="RTY", canonical_name="E-mini Russell 2000", category="INDICES",
        exchange="CME Globex", point_value=50.0, tick_size=0.1, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="Small-Cap Expansion", icon="🏢",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox"
    ),
    "FDAX": MarketSpec(
        symbol="FDAX", canonical_name="DAX 40 Futures", category="INDICES",
        exchange="Eurex / FTMO", point_value=25.0, tick_size=1.0, fee_rate=0.0,
        fee_fixed_usd=2.00, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="Frankfurt Open Trend", icon="🇩🇪",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / Apex Eurex"
    ),
    "FTSE": MarketSpec(
        symbol="FTSE", canonical_name="FTSE 100 Index Futures", category="INDICES",
        exchange="ICE / FTMO", point_value=10.0, tick_size=0.5, fee_rate=0.0,
        fee_fixed_usd=2.00, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="1h", typical_regime="London Open Momentum", icon="🇬🇧",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers"
    ),
    "NK225": MarketSpec(
        symbol="NK225", canonical_name="Nikkei 225 Futures", category="INDICES",
        exchange="OSE / CME", point_value=5.0, tick_size=5.0, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="Tokyo Breakout Flow", icon="🇯🇵",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / FTMO"
    ),
    "HSI": MarketSpec(
        symbol="HSI", canonical_name="Hang Seng Futures", category="INDICES",
        exchange="HKEX / FTMO", point_value=50.0, tick_size=1.0, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=2, max_leverage=100.0, maint_margin_pct=1.5,
        default_timeframe="15m", typical_regime="High Vol Open Gap", icon="🇭🇰",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers"
    ),
    "STOXX50": MarketSpec(
        symbol="STOXX50", canonical_name="Euro Stoxx 50 Futures", category="INDICES",
        exchange="Eurex / FTMO", point_value=10.0, tick_size=1.0, fee_rate=0.0,
        fee_fixed_usd=1.80, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="1h", typical_regime="European Bluechip Trend", icon="🇪🇺",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers"
    ),

    # =========================================================================
    # 3. FOREX MAJORS & CROSSES (10 ACTIVOS) — PERMITIDOS EN FONDEO & ULTRA
    # =========================================================================
    "EURUSD": MarketSpec(
        symbol="EURUSD", canonical_name="Euro / US Dollar", category="FOREX",
        exchange="Interbank / FTMO", point_value=100000.0, tick_size=0.00001, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=5, max_leverage=500.0, maint_margin_pct=0.2,
        default_timeframe="1h", typical_regime="London-NY Overlap", icon="💶",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "USDJPY": MarketSpec(
        symbol="USDJPY", canonical_name="US Dollar / Yen Japonés", category="FOREX",
        exchange="Interbank / FTMO", point_value=1000.0, tick_size=0.001, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=5, max_leverage=500.0, maint_margin_pct=0.2,
        default_timeframe="1h", typical_regime="Yield Divergence Trend", icon="💴",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "GBPJPY": MarketSpec(
        symbol="GBPJPY", canonical_name="British Pound / Yen", category="FOREX",
        exchange="Interbank / FTMO", point_value=1000.0, tick_size=0.001, fee_rate=0.0,
        fee_fixed_usd=3.50, slippage_ticks=8, max_leverage=500.0, maint_margin_pct=0.3,
        default_timeframe="1h", typical_regime="Guppy High Beta Trend", icon="🐉",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "GBPUSD": MarketSpec(
        symbol="GBPUSD", canonical_name="British Pound / USD", category="FOREX",
        exchange="Interbank / FTMO", point_value=100000.0, tick_size=0.00001, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=6, max_leverage=500.0, maint_margin_pct=0.25,
        default_timeframe="1h", typical_regime="Cable London Breakout", icon="💷",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "EURJPY": MarketSpec(
        symbol="EURJPY", canonical_name="Euro / Japanese Yen", category="FOREX",
        exchange="Interbank / FTMO", point_value=1000.0, tick_size=0.001, fee_rate=0.0,
        fee_fixed_usd=3.20, slippage_ticks=6, max_leverage=500.0, maint_margin_pct=0.25,
        default_timeframe="1h", typical_regime="Cross Carry Momentum", icon="🗼",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "USDCAD": MarketSpec(
        symbol="USDCAD", canonical_name="US Dollar / Canadian Dollar", category="FOREX",
        exchange="Interbank / FTMO", point_value=100000.0, tick_size=0.00001, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=6, max_leverage=500.0, maint_margin_pct=0.25,
        default_timeframe="1h", typical_regime="Oil Correlation Flow", icon="🍁",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "AUDUSD": MarketSpec(
        symbol="AUDUSD", canonical_name="Australian Dollar / USD", category="FOREX",
        exchange="Interbank / FTMO", point_value=100000.0, tick_size=0.00001, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=6, max_leverage=500.0, maint_margin_pct=0.25,
        default_timeframe="1h", typical_regime="Commodity Flow Trend", icon="🦘",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "USDCHF": MarketSpec(
        symbol="USDCHF", canonical_name="US Dollar / Franco Suizo", category="FOREX",
        exchange="Interbank / FTMO", point_value=100000.0, tick_size=0.00001, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=6, max_leverage=500.0, maint_margin_pct=0.25,
        default_timeframe="1h", typical_regime="Safe Haven Reversion", icon="🇨🇭",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "NZDUSD": MarketSpec(
        symbol="NZDUSD", canonical_name="New Zealand Dollar / USD", category="FOREX",
        exchange="Interbank / FTMO", point_value=100000.0, tick_size=0.00001, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=7, max_leverage=500.0, maint_margin_pct=0.25,
        default_timeframe="1h", typical_regime="Pacific Session Flow", icon="🥝",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "EURGBP": MarketSpec(
        symbol="EURGBP", canonical_name="Euro / British Pound", category="FOREX",
        exchange="Interbank / FTMO", point_value=100000.0, tick_size=0.00001, fee_rate=0.0,
        fee_fixed_usd=3.00, slippage_ticks=5, max_leverage=500.0, maint_margin_pct=0.2,
        default_timeframe="1h", typical_regime="Tight Range Chop", icon="⚖️",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),

    # =========================================================================
    # 4. COMMODITIES (7 ACTIVOS) — PERMITIDOS EN FONDEO & ULTRA
    # =========================================================================
    "GC": MarketSpec(
        symbol="GC", canonical_name="Oro COMEX Gold Futures", category="COMMODITIES",
        exchange="COMEX Globex", point_value=100.0, tick_size=0.10, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="1h", typical_regime="Macro Safe Haven Trend", icon="🥇",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox"
    ),
    "XAUUSD": MarketSpec(
        symbol="XAUUSD", canonical_name="Oro Spot / Gold Futures", category="COMMODITIES",
        exchange="COMEX / Spot FX", point_value=100.0, tick_size=0.01, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=5, max_leverage=500.0, maint_margin_pct=0.5,
        default_timeframe="1h", typical_regime="Macro Safe Haven Trend", icon="🥇",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / FundedNext / Alpha Capital"
    ),
    "CL": MarketSpec(
        symbol="CL", canonical_name="Petróleo Crudo WTI", category="COMMODITIES",
        exchange="NYMEX Globex", point_value=1000.0, tick_size=0.01, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=2, max_leverage=100.0, maint_margin_pct=1.5,
        default_timeframe="1h", typical_regime="OPEC Trend Expansion", icon="🛢️",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / FTMO"
    ),
    "SI": MarketSpec(
        symbol="SI", canonical_name="Plata COMEX Silver Futures", category="COMMODITIES",
        exchange="COMEX Globex", point_value=5000.0, tick_size=0.005, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=2, max_leverage=100.0, maint_margin_pct=1.5,
        default_timeframe="1h", typical_regime="High Beta Silver Breakout", icon="🥈",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / FTMO"
    ),
    "BRENT": MarketSpec(
        symbol="BRENT", canonical_name="Petróleo Brent Mar del Norte", category="COMMODITIES",
        exchange="ICE Futures / FTMO", point_value=1000.0, tick_size=0.01, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=2, max_leverage=100.0, maint_margin_pct=1.5,
        default_timeframe="1h", typical_regime="Geopolitical Flow Trend", icon="⛽",
        prop_firm_eligible=True, prop_firm_venues="FTMO / The5ers / Apex"
    ),
    "NG": MarketSpec(
        symbol="NG", canonical_name="Gas Natural Henry Hub", category="COMMODITIES",
        exchange="NYMEX Globex", point_value=10000.0, tick_size=0.001, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=2, max_leverage=100.0, maint_margin_pct=2.0,
        default_timeframe="1h", typical_regime="Extreme Volatility Shock", icon="🔥",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / FTMO"
    ),
    "HG": MarketSpec(
        symbol="HG", canonical_name="Cobre COMEX High Grade", category="COMMODITIES",
        exchange="COMEX Globex", point_value=25000.0, tick_size=0.0005, fee_rate=0.0,
        fee_fixed_usd=2.50, slippage_ticks=2, max_leverage=100.0, maint_margin_pct=1.5,
        default_timeframe="1h", typical_regime="Dr. Copper Macro Cycle", icon="🥉",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / FTMO"
    ),

    # =========================================================================
    # 5. FUTUROS MICRO CME (6 ACTIVOS) — RUTA FONDEO (mapeo real en scripts/mine.py
    # FONDEO_MICRO_MAP). tick_size y point_value verificados contra las specs oficiales
    # CME/CBOT/COMEX/NYMEX de los contratos Micro E-mini / Micro Gold / Micro WTI, e
    # idénticos a los ya usados en services/engine/instrument_registry.py::cme_specs
    # (mismo repo, misma fecha de verificación 2026-08-31).
    # fee_fixed_usd = 0.60 USD/contrato: tomado tal cual de esa misma tabla
    # (instrument_registry.py, campo "cme_fee" de MES/MNQ/MYM/M2K/MGC/MCL), NO inventado
    # aquí. Es la comisión de cambio (exchange fee) del contrato micro; no se ha
    # verificado por separado la comisión de bróker/prop-firm específica de cada firma
    # de fondeo (Apex/Topstep/TradeDay/Bulenox) — pendiente si se necesita ese desglose.
    # slippage_ticks, max_leverage y maint_margin_pct se heredan del contrato completo
    # homólogo (mismo book/tick de precio, solo cambia el multiplicador): no hay dato
    # verificado de que difieran para el micro.
    # =========================================================================
    "MES": MarketSpec(
        symbol="MES", canonical_name="Micro E-mini S&P 500", category="INDICES",
        exchange="CME Globex", point_value=5.0, tick_size=0.25, fee_rate=0.0,
        fee_fixed_usd=0.60, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="NY Session Trend (Micro)", icon="🏛️",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox / FTMO"
    ),
    "MNQ": MarketSpec(
        symbol="MNQ", canonical_name="Micro E-mini Nasdaq 100", category="INDICES",
        exchange="CME Globex", point_value=2.0, tick_size=0.25, fee_rate=0.0,
        fee_fixed_usd=0.60, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="Opening Range Breakout (Micro)", icon="📈",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox / FTMO"
    ),
    "MYM": MarketSpec(
        symbol="MYM", canonical_name="Micro E-mini Dow Jones ($0.50)", category="INDICES",
        exchange="CBOT Globex", point_value=0.5, tick_size=1.0, fee_rate=0.0,
        fee_fixed_usd=0.60, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="Value Rotation Trend (Micro)", icon="🏭",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox"
    ),
    "M2K": MarketSpec(
        symbol="M2K", canonical_name="Micro E-mini Russell 2000", category="INDICES",
        exchange="CME Globex", point_value=5.0, tick_size=0.10, fee_rate=0.0,
        fee_fixed_usd=0.60, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="15m", typical_regime="Small-Cap Expansion (Micro)", icon="🏢",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox"
    ),
    "MGC": MarketSpec(
        symbol="MGC", canonical_name="Micro Oro COMEX Gold Futures", category="COMMODITIES",
        exchange="COMEX Globex", point_value=10.0, tick_size=0.10, fee_rate=0.0,
        fee_fixed_usd=0.60, slippage_ticks=1, max_leverage=100.0, maint_margin_pct=1.0,
        default_timeframe="1h", typical_regime="Macro Safe Haven Trend (Micro)", icon="🥇",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / Bulenox"
    ),
    "MCL": MarketSpec(
        symbol="MCL", canonical_name="Micro Petróleo Crudo WTI", category="COMMODITIES",
        exchange="NYMEX Globex", point_value=100.0, tick_size=0.01, fee_rate=0.0,
        fee_fixed_usd=0.60, slippage_ticks=2, max_leverage=100.0, maint_margin_pct=1.5,
        default_timeframe="1h", typical_regime="OPEC Trend Expansion (Micro)", icon="🛢️",
        prop_firm_eligible=True, prop_firm_venues="Apex / Topstep / TradeDay / FTMO"
    ),
}


class UnknownMarketSpecError(ValueError):
    """Símbolo sin especificación verificada en MARKET_SPECS.

    Antes, get_market_spec() devolvía un fallback silencioso (spec CRYPTO genérica point_value=1.0,
    o incluso la spec de OTRO símbolo si este era substring de una key existente, p.ej. "GC" dentro
    de "MGC" o "ES" dentro de "MES") para cualquier símbolo no reconocido. Eso es exactamente el
    fallback complaciente que causó el bug de InstrumentRegistry con "GCFOO" heredando la spec de
    "GC" sin avisar (ver services/engine/instrument_registry.py, corregido 2026-08-31): un símbolo
    mal escrito o sin dar de alta terminaba calculando costes/PnL con el multiplicador de OTRO
    contrato, en silencio. Aquí se aplica la misma doctrina: si el símbolo no está verificado,
    se falla explícito en vez de adivinar.
    """


_MESES_CME_VALIDOS = set("FGHJKMNQUVXZ")


def _es_sufijo_vencimiento_cme(resto: str) -> bool:
    """True si `resto` es un código de vencimiento CME válido (letra de mes + 1-2 dígitos de año)."""
    if not resto:
        return True  # símbolo desnudo, p.ej. "ES", "MES"
    if len(resto) not in (2, 3):
        return False
    return resto[0] in _MESES_CME_VALIDOS and resto[1:].isdigit()


def get_market_spec(symbol: str) -> MarketSpec:
    """Devuelve las especificaciones de mercado verificadas para un símbolo dado.

    Búsqueda en 3 pasos, todos exactos o acotados (sin matching por substring difuso):
    1. Coincidencia exacta del símbolo tal cual llega.
    2. Coincidencia exacta tras normalizar separadores ("-", "_", "/").
    3. Prefijo exacto + código de vencimiento CME válido (p.ej. "ESU25", "MESZ6"), evaluando
       las keys más largas primero para evitar que una key corta absorba una más específica.

    Si ninguna coincide, lanza UnknownMarketSpecError: NO hay fallback silencioso. Quien reciba
    este error debe dar de alta el símbolo en MARKET_SPECS con datos reales verificados, no
    capturarlo para sustituirlo por un valor inventado.
    """
    if not symbol:
        raise UnknownMarketSpecError("get_market_spec(): symbol vacío o None, no se puede resolver.")

    clean_sym = symbol.upper().replace("-", "").replace("_", "").replace("/", "").strip()

    # 1. Búsqueda directa (símbolo tal cual)
    if symbol in MARKET_SPECS:
        return MARKET_SPECS[symbol]
    # 2. Búsqueda por símbolo normalizado
    if clean_sym in MARKET_SPECS:
        return MARKET_SPECS[clean_sym]

    # 3. Prefijo acotado a vencimiento CME válido (keys más largas primero: "STOXX50" antes que
    #    cualquier substring corta que pudiera coincidir por accidente).
    for key in sorted(MARKET_SPECS.keys(), key=len, reverse=True):
        if clean_sym.startswith(key) and _es_sufijo_vencimiento_cme(clean_sym[len(key):]):
            return MARKET_SPECS[key]

    raise UnknownMarketSpecError(
        f"get_market_spec(): símbolo '{symbol}' (normalizado '{clean_sym}') no tiene "
        f"especificación verificada en MARKET_SPECS ({len(MARKET_SPECS)} símbolos dados de alta). "
        f"No se aplica ningún valor por defecto: añade el símbolo a MARKET_SPECS en "
        f"services/api/app/validation/market_specs.py con datos reales verificados antes de usarlo "
        f"en los gates de validación."
    )
