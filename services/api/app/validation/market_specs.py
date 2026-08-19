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
}


def get_market_spec(symbol: str) -> MarketSpec:
    """Devuelve las especificaciones de mercado para un símbolo dado, con fallback inteligente."""
    clean_sym = symbol.upper().replace("-", "").replace("_", "").replace("/", "")
    
    # Búsqueda directa
    if symbol in MARKET_SPECS:
        return MARKET_SPECS[symbol]
    if clean_sym in MARKET_SPECS:
        return MARKET_SPECS[clean_sym]
    
    # Búsqueda por prefijo
    for key, spec in MARKET_SPECS.items():
        if clean_sym.startswith(key.replace("_", "")) or key.replace("_", "") in clean_sym:
            return spec
            
    # Fallback Cripto por defecto
    return MarketSpec(
        symbol=symbol,
        canonical_name=f"{symbol} Perpetuo",
        category="CRYPTO",
        exchange="Perpetual Swap",
        point_value=1.0,
        tick_size=0.01,
        fee_rate=0.0005,
        fee_fixed_usd=0.0,
        slippage_ticks=3,
        max_leverage=500.0,
        maint_margin_pct=0.5,
        default_timeframe="1h",
        typical_regime="Momentum Breakout",
        icon="⚡",
        prop_firm_eligible=False,
        prop_firm_venues="Solo Ruta ULTRA (BingX 500x)",
    )
