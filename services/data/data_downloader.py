"""services/data/data_downloader.py
Descargador de datos históricos de alta velocidad y fidelidad cuantitativa.
Obtiene velas OHLCV reales desde Binance Futures y otras fuentes públicas,
las audita contra gaps/duplicados y las exporta tanto en formato normalizado JSON
como en CSV compatible 100% con StrategyQuant X Data Manager.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import math
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import urllib.parse
import urllib.request

from contracts.backtest import BarData
from services.data.market_ingestor import MarketDataAuditor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] DataDownloader: %(message)s",
)
logger = logging.getLogger("DataDownloader")


class BinanceFuturesDownloader:
    """Descargador de velas reales desde Binance USDT-M Futures REST API."""

    BASE_URL = "https://fapi.binance.com/fapi/v1/klines"
    MAX_LIMIT = 1500

    INTERVAL_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
    }

    INTERVAL_MS = {
        "1m": 60_000,
        "5m": 300_000,
        "15m": 900_000,
        "30m": 1_800_000,
        "1h": 3_600_000,
        "4h": 14_400_000,
        "1d": 86_400_000,
    }

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.root_dir = data_dir or Path(__file__).resolve().parent.parent.parent / "data"
        self.normalized_dir = self.root_dir / "normalized"
        self.sqx_imports_dir = self.root_dir / "sqx_imports"
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        self.sqx_imports_dir.mkdir(parents=True, exist_ok=True)

    def fetch_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
        limit: int = 1500,
    ) -> List[List[Any]]:
        """Descarga un bloque de hasta 1500 velas desde Binance Futures."""
        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "interval": self.INTERVAL_MAP.get(interval, "1h"),
            "limit": limit,
        }
        if start_time_ms is not None:
            params["startTime"] = start_time_ms
        if end_time_ms is not None:
            params["endTime"] = end_time_ms

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Ultrarentable/2.0",
                "Accept": "application/json",
            },
        )

        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        return json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                logger.warning(f"Error en intento {attempt+1}/3 para {symbol} {interval}: {e}")
                time.sleep(1.0 + attempt * 2)

        return []

    def download_history(
        self,
        symbol: str,
        interval: str = "1h",
        total_bars_target: int = 10_000,
        start_date_str: Optional[str] = None,
    ) -> List[BarData]:
        """Descarga histórico paginado continuo hacia atrás en el tiempo."""
        binance_symbol = symbol.replace("-", "").replace("/", "").upper()
        logger.info(f"Iniciando descarga histórica de {binance_symbol} ({interval}) — Objetivo: {total_bars_target} barras...")

        now_ms = int(time.time() * 1000)
        end_ts = now_ms
        all_raw_klines: List[List[Any]] = []

        if start_date_str:
            # Descarga hacia adelante desde start_date
            dt = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
            start_ts = int(dt.timestamp() * 1000)
            curr_start = start_ts

            while curr_start < now_ms and len(all_raw_klines) < total_bars_target:
                klines = self.fetch_klines(binance_symbol, interval, start_time_ms=curr_start, limit=self.MAX_LIMIT)
                if not klines:
                    break
                all_raw_klines.extend(klines)
                last_ts = klines[-1][0]
                if last_ts <= curr_start:
                    break
                curr_start = last_ts + self.INTERVAL_MS.get(interval, 3_600_000)
                time.sleep(0.08)  # Rate limit seguro
        else:
            # Descarga hacia atrás desde el presente
            curr_end = end_ts
            while len(all_raw_klines) < total_bars_target:
                klines = self.fetch_klines(binance_symbol, interval, end_time_ms=curr_end, limit=self.MAX_LIMIT)
                if not klines:
                    break
                
                # Insertar al principio para mantener orden cronológico
                all_raw_klines = klines + all_raw_klines
                first_ts = klines[0][0]
                if first_ts >= curr_end:
                    break
                curr_end = first_ts - 1
                time.sleep(0.08)  # Rate limit seguro

                if len(klines) < self.MAX_LIMIT:
                    # Llegamos al inicio del histórico disponible en Binance
                    break

        if not all_raw_klines:
            logger.error(f"No se obtuvieron datos para {binance_symbol} {interval}")
            return []

        # Convertir a BarData
        bars: List[BarData] = []
        for k in all_raw_klines:
            # Binance kline format: [open_time, open, high, low, close, volume, close_time, ...]
            bars.append(
                BarData(
                    timestamp_utc_ms=int(k[0]),
                    open=float(k[1]),
                    high=float(k[2]),
                    low=float(k[3]),
                    close=float(k[4]),
                    volume=float(k[5]),
                )
            )

        # Auditar y desduplicar
        audited_bars, audit_report = MarketDataAuditor.audit(
            bars=bars,
            venue="BINANCE",
            symbol=symbol,
            interval=interval,
        )

        logger.info(
            f"✓ {symbol} ({interval}): {len(audited_bars)} barras verificadas. "
            f"Cobertura: {audit_report.coverage_pct}%. Gaps: {audit_report.gap_count}."
        )

        # Exportar a JSON normalizado y CSV compatible SQX
        self._export_normalized_json(symbol, interval, audited_bars, audit_report)
        self._export_sqx_csv(symbol, interval, audited_bars)

        return audited_bars

    def _export_normalized_json(
        self,
        symbol: str,
        interval: str,
        bars: List[BarData],
        audit_report: Any,
    ) -> Path:
        """Guarda en data/normalized/ el JSON con manifest auditado."""
        formatted_sym = symbol.replace("-", "_").replace("/", "_")
        filename = f"ds_binance_{formatted_sym.lower()}_{interval}_{bars[0].timestamp_utc_ms}_{bars[-1].timestamp_utc_ms}.json"
        manifest_filename = f"ds_binance_{formatted_sym.lower()}_{interval}_{bars[0].timestamp_utc_ms}_{bars[-1].timestamp_utc_ms}_manifest.json"

        data_path = self.normalized_dir / filename
        manifest_path = self.normalized_dir / manifest_filename

        with open(data_path, "w", encoding="utf-8") as f:
            json.dump([b.model_dump() for b in bars], f)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(audit_report.model_dump(), f, indent=2)

        return data_path

    def _export_sqx_csv(self, symbol: str, interval: str, bars: List[BarData]) -> Path:
        """Exporta en formato CSV universal de StrategyQuant X:
        Date,Time,Open,High,Low,Close,Volume (formato: YYYY.MM.DD,HH:mm:ss)
        """
        sqx_sym = symbol.replace("-", "").replace("/", "").upper()
        filename = f"{sqx_sym}_{interval.upper()}.csv"
        csv_path = self.sqx_imports_dir / filename

        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("<TICKER>,<DTYYYYMMDD>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>\n")
            for b in bars:
                dt = datetime.datetime.fromtimestamp(b.timestamp_utc_ms / 1000.0, tz=datetime.timezone.utc)
                date_str = dt.strftime("%Y.%m.%d")
                time_str = dt.strftime("%H:%M:%S")
                f.write(f"{sqx_sym},{date_str},{time_str},{b.open:.6f},{b.high:.6f},{b.low:.6f},{b.close:.6f},{b.volume:.4f}\n")

        logger.info(f"  -> Exportado archivo SQX CSV: {csv_path} ({len(bars):,} barras)")
        return csv_path


class YahooFinanceDownloader:
    """Descargador de datos históricos de Forex, Commodities e Índices vía yfinance."""

    YAHOO_SYMBOL_MAP = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "JPY=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "CAD=X",
        "USDCHF": "CHF=X",
        "NQ": "NQ=F",
        "MNQ": "NQ=F",
        "ES": "ES=F",
        "MES": "ES=F",
        "YM": "YM=F",
        "MYM": "YM=F",
        "RTY": "RTY=F",
        "DAX": "^GDAXI",
        "GC": "GC=F",
        "MGC": "GC=F",
        "SI": "SI=F",
        "CL": "CL=F",
        "MCL": "CL=F",
    }

    INTERVAL_PARAMS = {
        "1m": ("1m", "7d"),
        "5m": ("5m", "60d"),
        "15m": ("15m", "60d"),
        "1h": ("1h", "730d"),
        "4h": ("1h", "730d"),  # Descarga 1h y re-muestrea a 4h
        "1d": ("1d", "10y"),
    }

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.root_dir = data_dir or Path(__file__).resolve().parent.parent.parent / "data"
        self.normalized_dir = self.root_dir / "normalized"
        self.sqx_imports_dir = self.root_dir / "sqx_imports"
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        self.sqx_imports_dir.mkdir(parents=True, exist_ok=True)

    def download_history(
        self,
        symbol: str,
        interval: str = "1h",
    ) -> List[BarData]:
        """Descarga velas reales de Forex, Commodities o Índices con yfinance."""
        import yfinance as yf

        clean_sym = symbol.replace("-", "").replace("/", "").upper()
        yahoo_sym = self.YAHOO_SYMBOL_MAP.get(clean_sym, f"{clean_sym}=X")
        yf_interval, yf_period = self.INTERVAL_PARAMS.get(interval, ("1h", "730d"))

        logger.info(f"Descargando {clean_sym} ({interval}) vía yfinance ({yahoo_sym}, period {yf_period})...")

        ticker = yf.Ticker(yahoo_sym)
        try:
            df = ticker.history(period=yf_period, interval=yf_interval, auto_adjust=False)
        except Exception as e:
            logger.error(f"Error descargando {clean_sym} desde yfinance: {e}")
            return []

        if df.empty:
            logger.error(f"No se obtuvieron datos para {clean_sym} ({yahoo_sym})")
            return []

        # Si el intervalo es 4h, remuestrear desde 1h
        if interval == "4h":
            df_resampled = df.resample("4h").agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }).dropna()
            df = df_resampled

        bars: List[BarData] = []
        for idx, row in df.iterrows():
            # Obtener timestamp en milisegundos UTC
            ts = int(idx.timestamp() * 1000)
            o = float(row["Open"])
            h = float(row["High"])
            l = float(row["Low"])
            c = float(row["Close"])
            v = float(row.get("Volume", 100.0)) or 100.0

            if math.isnan(o) or math.isnan(h) or math.isnan(l) or math.isnan(c):
                continue

            bars.append(
                BarData(
                    timestamp_utc_ms=ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=v,
                )
            )

        if not bars:
            logger.error(f"No se obtuvieron velas válidas para {clean_sym}")
            return []

        # Auditar calidad de datos
        venue = "YAHOO_CME" if "=F" in yahoo_sym or "^" in yahoo_sym else "YAHOO_FOREX"
        audited_bars, audit_report = MarketDataAuditor.audit(
            bars=bars,
            venue=venue,
            symbol=clean_sym,
            interval=interval,
        )

        logger.info(
            f"✓ {clean_sym} ({interval}): {len(audited_bars):,} barras verificadas. "
            f"Cobertura: {audit_report.coverage_pct}%."
        )

        # Exportar
        self._export_normalized_json(clean_sym, interval, audited_bars, audit_report)
        self._export_sqx_csv(clean_sym, interval, audited_bars)

        return audited_bars

    def _export_normalized_json(
        self,
        symbol: str,
        interval: str,
        bars: List[BarData],
        audit_report: Any,
    ) -> Path:
        filename = f"ds_trad_{symbol.lower()}_{interval}_{bars[0].timestamp_utc_ms}_{bars[-1].timestamp_utc_ms}.json"
        manifest_filename = f"ds_trad_{symbol.lower()}_{interval}_{bars[0].timestamp_utc_ms}_{bars[-1].timestamp_utc_ms}_manifest.json"

        data_path = self.normalized_dir / filename
        manifest_path = self.normalized_dir / manifest_filename

        with open(data_path, "w", encoding="utf-8") as f:
            json.dump([b.model_dump() for b in bars], f)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(audit_report.model_dump(), f, indent=2)

        return data_path

    def _export_sqx_csv(self, symbol: str, interval: str, bars: List[BarData]) -> Path:
        filename = f"{symbol.upper()}_{interval.upper()}.csv"
        csv_path = self.sqx_imports_dir / filename

        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("<TICKER>,<DTYYYYMMDD>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>\n")
            for b in bars:
                dt = datetime.datetime.fromtimestamp(b.timestamp_utc_ms / 1000.0, tz=datetime.timezone.utc)
                date_str = dt.strftime("%Y.%m.%d")
                time_str = dt.strftime("%H:%M:%S")
                f.write(f"{symbol.upper()},{date_str},{time_str},{b.open:.6f},{b.high:.6f},{b.low:.6f},{b.close:.6f},{b.volume:.4f}\n")

        logger.info(f"  -> Exportado archivo SQX CSV: {csv_path} ({len(bars):,} barras)")
        return csv_path


def run_full_download(
    symbols: Optional[List[str]] = None,
    timeframes: Optional[List[str]] = None,
    total_bars: int = 15_000,
) -> Dict[str, Any]:
    """Descarga el universo canónico completo de mercados y temporalidades."""
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "EURUSD", "GBPUSD", "NQ", "ES", "GC"]
    if timeframes is None:
        timeframes = ["5m", "15m", "1h", "4h"]

    binance_downloader = BinanceFuturesDownloader()
    yahoo_downloader = YahooFinanceDownloader()
    results = {}

    crypto_symbols = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "XRPUSDT", "BNBUSDT", "SUIUSDT"}

    for sym in symbols:
        clean = sym.replace("-", "").replace("/", "").upper()
        for tf in timeframes:
            try:
                if clean in crypto_symbols or "USDT" in clean:
                    bars_target = total_bars
                    if tf == "1h":
                        bars_target = 25_000
                    elif tf == "4h":
                        bars_target = 10_000
                    elif tf == "1m":
                        bars_target = 10_000
                    bars = binance_downloader.download_history(symbol=clean, interval=tf, total_bars_target=bars_target)
                else:
                    bars = yahoo_downloader.download_history(symbol=clean, interval=tf)
                results[f"{clean}_{tf}"] = len(bars)
            except Exception as e:
                logger.error(f"Error descargando {clean} {tf}: {e}")
                results[f"{clean}_{tf}"] = 0

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descargador de datos históricos para SQX y Ultrarentable")
    parser.add_argument("--symbols", type=str, default="BTCUSDT,ETHUSDT,SOLUSDT", help="Símbolos separados por coma")
    parser.add_argument("--timeframes", type=str, default="1m,5m,15m,1h,4h", help="Timeframes separados por coma")
    parser.add_argument("--bars", type=int, default=10000, help="Total de barras objetivo")

    args = parser.parse_args()
    sym_list = [s.strip() for s in args.symbols.split(",") if s.strip()]
    tf_list = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    print(f"Iniciando descarga para símbolos: {sym_list}, temporalidades: {tf_list}")
    res = run_full_download(symbols=sym_list, timeframes=tf_list, total_bars=args.bars)
    print("\nResumen de Descarga:")
    print(json.dumps(res, indent=2))
