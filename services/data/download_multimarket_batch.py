"""services/data/download_multimarket_batch.py
Descargador universal multi-mercado para Ultrarentable y StrategyQuant X.
Descarga Forex, Commodities, Índices y Cripto en todas las temporalidades (5m, 15m, 1h, 4h).
"""

from __future__ import annotations

import time
import logging
from pathlib import Path
from services.data.data_downloader import BinanceFuturesDownloader, YahooFinanceDownloader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MultiMarketDownloader")

def run():
    yahoo = YahooFinanceDownloader()
    binance = BinanceFuturesDownloader()

    # 1. FOREX
    forex_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
    forex_tfs = ["5m", "15m", "1h", "4h"]
    
    logger.info("=== 1. DESCARGANDO FOREX ===")
    for sym in forex_symbols:
        for tf in forex_tfs:
            try:
                bars = yahoo.download_history(sym, tf)
                logger.info(f"✓ Forex {sym} {tf}: {len(bars):,} barras")
            except Exception as e:
                logger.error(f"✗ Error Forex {sym} {tf}: {e}")
            time.sleep(0.5)

    # 2. COMMODITIES
    comm_symbols = ["GC", "SI", "CL"]
    comm_tfs = ["5m", "15m", "1h", "4h"]
    logger.info("=== 2. DESCARGANDO COMMODITIES (ORO, PLATA, PETRÓLEO) ===")
    for sym in comm_symbols:
        for tf in comm_tfs:
            try:
                bars = yahoo.download_history(sym, tf)
                logger.info(f"✓ Commodity {sym} {tf}: {len(bars):,} barras")
            except Exception as e:
                logger.error(f"✗ Error Commodity {sym} {tf}: {e}")
            time.sleep(0.5)

    # 3. ÍNDICES (CME / GLOBEX)
    idx_symbols = ["NQ", "ES", "YM", "RTY"]
    idx_tfs = ["5m", "15m", "1h", "4h"]
    logger.info("=== 3. DESCARGANDO ÍNDICES (NASDAQ, S&P 500, DOW JONES, RUSSELL) ===")
    for sym in idx_symbols:
        for tf in idx_tfs:
            try:
                bars = yahoo.download_history(sym, tf)
                logger.info(f"✓ Índice {sym} {tf}: {len(bars):,} barras")
            except Exception as e:
                logger.error(f"✗ Error Índice {sym} {tf}: {e}")
            time.sleep(0.5)

    # 4. CRIPTO (BINANCE FUTURES)
    crypto_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "XRPUSDT", "BNBUSDT", "SUIUSDT"]
    crypto_tfs = ["1m", "5m", "15m", "1h", "4h"]
    logger.info("=== 4. VERIFICANDO / DESCARGANDO CRIPTO ===")
    for sym in crypto_symbols:
        for tf in crypto_tfs:
            try:
                # Comprobar si ya existe el CSV
                csv_file = Path(f"/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/{sym}_{tf.upper()}.csv")
                if csv_file.exists() and csv_file.stat().st_size > 10_000:
                    logger.info(f"✓ Cripto {sym} {tf} ya existe ({csv_file.stat().st_size // 1024} KB)")
                    continue
                bars_target = 10_000 if tf in ["1m", "4h"] else 20_000
                bars = binance.download_history(sym, tf, total_bars_target=bars_target)
                logger.info(f"✓ Cripto {sym} {tf}: {len(bars):,} barras")
            except Exception as e:
                logger.error(f"✗ Error Cripto {sym} {tf}: {e}")
            time.sleep(0.2)

    logger.info("=== DESCARGA MULTIACTIVO COMPLETA ===")

if __name__ == "__main__":
    run()
