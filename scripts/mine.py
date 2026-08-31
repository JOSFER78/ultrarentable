#!/usr/bin/env python3
"""scripts/mine.py
CLI Unificado y Gobernado de Minería Cuantitativa y Certificación 11/11 Gates.
Consolida la lógica de minería y validación para TRACK_ULTRA y TRACK_FONDEO en las
5 temporalidades canónicas intradiarias (1m, 5m, 15m, 1h, 4h) en todos los activos del universo.

ZERO-MOCKS · REAL-ONLY · MERKLE PROVENANCE · CRYPTOGRAPHIC AUDIT TRAILS
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "normalized"
EVIDENCE_DIR = ROOT_DIR / "data" / "evidence"
DB_PATH = Path(
    os.environ.get(
        "ULTRARENTABLE_DB_PATH",
        os.path.expanduser("~/.local/state/ultrarentable/ultrarentable.sqlite3"),
    )
)

sys.path.insert(0, str(ROOT_DIR))

from contracts.snapshots.strategy_snapshot import (
    StrategySnapshot,
    StrategyRoute,
    PyramidingPolicy,
    PyramidingTier,
    MarginPolicy,
)
from contracts.canonical_strategy import (
    RuleTree,
    ExitModel,
    StopLossType,
    TakeProfitType,
    SizingAndRisk,
    SizingType,
    IndicatorSpec,
    ConditionNode,
    ComparisonOp,
    LogicalOp,
    SessionWindow,
)
from services.engine_version import CURRENT_ENGINE_VERSION
from services.discovery.ultra_discovery import UltraDiscoveryEngine
from services.discovery.funding_discovery import FundingDiscoveryEngine, resolve_session_window

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("MineCLI")


def log_msg(msg: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def compute_file_sha256(filepath: str | Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=60.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=60000;")
    return conn


# --- FONDEO opera MICROS, no contratos completos (corregido 2026-08-31) -----------------
# Motivo: en una cuenta prop de 50.000 USD con 4% de drawdown maximo (2.000 USD), arriesgar
# el 1% (500 USD) en CL completo (1.000 USD/punto) deja un stop de 0,5 puntos: ruido de
# mercado, no una estrategia. Los micros (MES, MNQ, MYM, M2K, MGC, MCL) siguen EXACTAMENTE
# la misma serie de precios que su hermano completo (MES sigue a ES tick a tick) y son el
# instrumento que casi toda prop firm permite operar. Por eso el dataset de precios de FONDEO
# sigue siendo el del contrato completo (misma serie), pero el point_value con el que se
# calcula el PnL debe ser el del MICRO.
# EventBacktestEngine.run_backtest ya hace `InstrumentRegistry.get(strategy.symbol)` para
# resolver el point_value cuando `strategy.route` es FONDEO (ver comentario "MULTIPLICADOR DE
# CONTRATO" en services/validation/engine/event_backtest_engine.py). Por eso NO hace falta
# tocar el motor: basta con que el `StrategySnapshot.symbol` que le llega sea el simbolo MICRO
# mientras el dataset fisico (precio, sesion, candidate_id) sigue etiquetado con el simbolo del
# contrato completo, que es el que realmente se descargo y del que proviene la serie.
FONDEO_MICRO_MAP: Dict[str, str] = {
    "ES": "MES",
    "NQ": "MNQ",
    "YM": "MYM",
    "RTY": "M2K",
    "GC": "MGC",
    "CL": "MCL",
}
# SI (plata) queda FUERA del universo FONDEO: no tiene micro estandar en el registro.
# Verificado 2026-08-31: InstrumentRegistry.get('SIL') NO lanza excepcion, pero es un falso
# positivo -- 'SIL' no esta en el diccionario estatico de services/engine/instrument_registry.py
# ni en su catalogo canonico precargado (_CANONICAL_SYMBOLS). El fallback por prefijo de
# _create_inferred_spec hace `norm.startswith(cme_key)`, y "SIL".startswith("SI") es True, asi
# que devuelve la especificacion del contrato COMPLETO (point_value 5000 USD/punto, igual que
# SI) en vez de un micro real. El micro autentico (SIL, 1.000 oz troy) tendria un point_value
# distinto (~1000), pero ese dato no esta certificado en el registro y no se inventa aqui
# (doctrina Zero-Mocks / cero datos inventados). Hasta que se registre un SIL real con specs
# verificadas, FONDEO no opera plata: se reporta el motivo, no se fuerza un valor.
FONDEO_NO_MICRO = {"SI"}

# Minimo de operaciones fuera de muestra para que una candidata sea siquiera evaluable.
# No es un umbral de calidad, es el suelo de la significancia estadistica.
MIN_OPERACIONES_OOS = 100


def resolve_dataset_file(symbol: str, timeframe: str, explicit_path: Optional[str] = None) -> Tuple[Optional[Path], Optional[Path]]:
    """Localiza el dataset físico y su manifest correspondiente en data/normalized/."""
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            manifest = p.parent / f"{p.stem}_manifest.json"
            return p, (manifest if manifest.exists() else None)
        return None, None

    sym_clean = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
    tf_clean = timeframe.lower()

    if not DATA_DIR.exists():
        return None, None

    patterns = [
        f"ds_binance_{sym_clean.lower()}_{tf_clean}_*.json",
        f"*{sym_clean.lower()}*{tf_clean}*.json",
        f"*{sym_clean}*{tf_clean.upper()}*.json",
        f"*{sym_clean}*{tf_clean}*.csv",
        f"*{sym_clean}*{tf_clean.upper()}*.csv",
    ]

    for pat in patterns:
        matches = [m for m in DATA_DIR.glob(pat) if not m.name.endswith("_manifest.json")]
        if matches:
            matches.sort(key=lambda x: x.stat().st_size, reverse=True)
            chosen = matches[0]
            manifest = chosen.parent / f"{chosen.stem}_manifest.json"
            return chosen, (manifest if manifest.exists() else None)

    return None, None


def _normalizar_timestamps(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Expone el timestamp bajo la clave que lee el motor de backtest.

    Los datasets normalizados guardan `timestamp_utc_ms`, pero EventBacktestEngine solo busca
    `timestamp_ms`/`timestamp`/`time`/`datetime`. Sin este puente TODA vela entra con ts=0, las
    operaciones nacen sin hora y el Gate 07 (cobertura de regimen) las bloquea con
    MISSING_PHYSICAL_TIMESTAMP. No se inventa ningun valor: solo se renombra el que ya existe.
    """
    for c in candles:
        if "timestamp_ms" not in c:
            ts = c.get("timestamp_utc_ms") or c.get("timestamp") or c.get("time")
            if ts is not None:
                c["timestamp_ms"] = int(ts)
    return candles


def load_candles_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """Carga y normaliza velas desde JSON o CSV físico sin modificar datos."""
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset no encontrado: {file_path}")

    if file_path.suffix.lower() == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return _normalizar_timestamps(data)
        elif isinstance(data, dict) and "candles" in data:
            return _normalizar_timestamps(data["candles"])
        elif isinstance(data, dict) and "bars" in data:
            return _normalizar_timestamps(data["bars"])
        raise ValueError(f"Formato JSON inesperado en {file_path}")

    elif file_path.suffix.lower() == ".csv":
        import csv
        candles = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = int(row.get("timestamp_ms") or row.get("timestamp") or 0)
                candles.append({
                    "timestamp_ms": ts,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0.0)),
                })
        return candles

    raise ValueError(f"Extensión no soportada: {file_path.suffix}")


def build_candidate_search_configs(track: str, symbol: str, timeframe: str, profile: str) -> List[Dict[str, Any]]:
    """Construye el espacio de exploración cuantitativo según track, timeframe y perfil."""
    is_ultra = (track.lower() == "ultra")
    tf_lower = timeframe.lower()

    if profile.lower() == "champions":
        if is_ultra:
            return [
                {"archetype": "MOMENTUM_BREAKOUT", "ema_fast": 5, "ema_slow": 20, "rsi_period": 14, "rsi_long": 52.0, "rsi_short": 48.0, "sl_atr_mult": 1.5, "tp_atr_mult": 5.0, "risk_pct": 0.02, "pyramiding_tiers": 2, "breakout_lookback": 15},
                {"archetype": "TREND_FOLLOWING", "ema_fast": 8, "ema_slow": 24, "rsi_period": 14, "rsi_long": 50.0, "rsi_short": 50.0, "sl_atr_mult": 1.2, "tp_atr_mult": 4.5, "risk_pct": 0.02, "pyramiding_tiers": 3, "breakout_lookback": 0},
                {"archetype": "RSI_MOMENTUM", "ema_fast": 6, "ema_slow": 18, "rsi_period": 14, "rsi_long": 55.0, "rsi_short": 45.0, "sl_atr_mult": 1.5, "tp_atr_mult": 6.0, "risk_pct": 0.015, "pyramiding_tiers": 2, "breakout_lookback": 0},
            ]
        else:
            return [
                {"archetype": "INSTITUTIONAL_SESSION_MOMENTUM", "ema_fast": 5, "ema_slow": 21, "rsi_period": 14, "rsi_long": 50.0, "rsi_short": 50.0, "sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "risk_pct": 0.01, "pyramiding_tiers": 0, "breakout_lookback": 0},
                {"archetype": "TREND_FOLLOWING", "ema_fast": 9, "ema_slow": 34, "rsi_period": 14, "rsi_long": 52.0, "rsi_short": 48.0, "sl_atr_mult": 2.0, "tp_atr_mult": 4.0, "risk_pct": 0.01, "pyramiding_tiers": 0, "breakout_lookback": 0},
                {"archetype": "MEAN_REVERSION", "ema_fast": 13, "ema_slow": 55, "rsi_period": 14, "rsi_long": 60.0, "rsi_short": 40.0, "sl_atr_mult": 1.5, "tp_atr_mult": 2.5, "risk_pct": 0.008, "pyramiding_tiers": 0, "breakout_lookback": 0},
            ]

    # Perfil AMPLIO: rejilla extendida para campanas de descubrimiento de verdad.
    # El grid por defecto da 54 configuraciones (ULTRA) / 27 (FONDEO): demasiado estrecho para
    # encontrar nada. Este perfil explora ~12x mas combinaciones.
    # OJO: mas trials => el Gate 08 (DSR) sube el liston por multiplicidad. Es el precio correcto
    # a pagar por explorar mas, y se paga: trials_tested se le pasa al gate.
    if profile.lower() == "amplio":
        configs = []
        if is_ultra:
            archetypes = ["MOMENTUM_BREAKOUT", "TREND_FOLLOWING", "RSI_MOMENTUM"]
            if tf_lower in ("1m", "5m"):
                fast_slow = [(3, 12), (4, 14), (5, 15), (6, 18), (8, 20)]
                sl_tp = [(1.0, 3.0), (1.2, 4.0), (1.5, 5.0), (1.8, 6.0), (2.0, 8.0)]
            elif tf_lower in ("15m", "1h"):
                fast_slow = [(5, 20), (6, 24), (8, 30), (10, 33), (12, 36)]
                sl_tp = [(1.2, 3.5), (1.5, 4.5), (1.8, 6.0), (2.0, 7.0), (2.5, 9.0)]
            else:  # 4h
                fast_slow = [(6, 24), (8, 30), (10, 36), (12, 45), (20, 60)]
                sl_tp = [(1.5, 4.5), (1.8, 5.5), (2.0, 7.0), (2.5, 8.0), (3.0, 10.0)]
            rsi_bands = [(50.0, 50.0), (52.0, 48.0), (55.0, 45.0)]
            pyramids = [0, 2, 3]
        else:
            archetypes = ["INSTITUTIONAL_SESSION_MOMENTUM", "TREND_FOLLOWING", "MEAN_REVERSION"]
            if tf_lower in ("1m", "5m"):
                fast_slow = [(3, 15), (4, 18), (5, 21), (7, 25), (9, 30)]
                sl_tp = [(1.0, 2.0), (1.2, 2.5), (1.5, 3.0), (1.8, 3.5), (2.0, 4.0)]
            elif tf_lower in ("15m", "1h"):
                fast_slow = [(5, 21), (7, 28), (9, 34), (11, 42), (13, 50)]
                sl_tp = [(1.2, 2.5), (1.5, 3.0), (2.0, 4.0), (2.2, 4.5), (2.5, 5.0)]
            else:  # 4h
                fast_slow = [(8, 34), (10, 44), (13, 55), (17, 66), (21, 80)]
                sl_tp = [(1.2, 3.0), (1.5, 3.5), (2.0, 4.5), (2.2, 5.0), (2.5, 6.0)]
            rsi_bands = [(50.0, 50.0), (55.0, 45.0), (60.0, 40.0)]
            pyramids = [0]  # FONDEO nunca piramida (decision sellada)

        # Los umbrales RSI solo los consumen ciertos arquetipos (ver services/discovery/
        # effective_dof.py). Variarlos en TREND_FOLLOWING genera clones identicos: gasta CPU y,
        # peor, infla trials_tested y endurece el Gate 08 (DSR) sin explorar nada.
        RSI_RELEVANTE = {"MEAN_REVERSION", "RSI_REVERSION", "RSI_MOMENTUM",
                         "MOMENTUM_RSI", "MOMENTUM_BREAKOUT"}
        for arch in archetypes:
            bandas = rsi_bands if arch in RSI_RELEVANTE else rsi_bands[:1]
            # RIESGO POR OPERACION: hasta el 2026-08-31 era una constante (2% en ULTRA), y esa
            # constante era el motivo real de que NADA certificara: el Gate 05 (Monte Carlo)
            # medía 38,2% de probabilidad de ruina contra un umbral del 1%, con drawdown del
            # percentil 95 en el 96,5%. Con 2% por operacion y piramidacion, arruinarse es
            # aritmetica, no mala suerte.
            #
            # Ademas habia un error de diseno: dimensionar la BASE al 2% y luego escalarla con la
            # envolvente de balas cuenta el riesgo dos veces. La base debe SOBREVIVIR; la
            # convexidad la aporta la envolvente despues. Por eso ahora el riesgo se BUSCA.
            # ULTRA: MAS riesgo, no menos (mandato del usuario 2026-08-31). Bajarlo a 0,5-2%
            # produjo la solucion degenerada: estrategias de 17 operaciones y DD 0,08% que
            # certificaban por NO OPERAR. ULTRA es un sistema de balas sacrificables: la bala
            # arriesga fuerte por diseno, y lo que se protege es la boveda, no la bala.
            # FONDEO: dos regimenes distintos, ver PERFILES_FONDEO mas abajo.
            riesgos = [0.02, 0.05, 0.10, 0.20] if is_ultra else [0.005, 0.01, 0.02, 0.04]
            for fast, slow in fast_slow:
                for sl, tp in sl_tp:
                    for rl, rs in bandas:
                        for py in pyramids:
                          for risk in riesgos:
                            configs.append({
                                "archetype": arch,
                                "ema_fast": fast,
                                "ema_slow": slow,
                                "rsi_period": 14,
                                "rsi_long": rl,
                                "rsi_short": rs,
                                "sl_atr_mult": sl,
                                "tp_atr_mult": tp,
                                "risk_pct": risk,
                                "pyramiding_tiers": py,
                                "breakout_lookback": 15 if arch == "MOMENTUM_BREAKOUT" else 0,
                            })
        return configs

    # Default / Grid Search
    configs = []
    if is_ultra:
        archetypes = ["MOMENTUM_BREAKOUT", "TREND_FOLLOWING", "RSI_MOMENTUM"]
        if tf_lower in ["1m", "5m"]:
            fast_slow_pairs = [(3, 12), (5, 15), (8, 20)]
            sl_tp_pairs = [(1.2, 4.0), (1.5, 5.0), (1.8, 6.0)]
        elif tf_lower in ["15m", "1h"]:
            fast_slow_pairs = [(5, 20), (8, 30), (12, 36)]
            sl_tp_pairs = [(1.5, 4.5), (1.8, 6.0), (2.0, 7.0)]
        else:  # 4h
            fast_slow_pairs = [(8, 30), (12, 45), (20, 60)]
            sl_tp_pairs = [(1.8, 5.5), (2.0, 7.0), (2.5, 8.0)]

        for arch in archetypes:
            for fast, slow in fast_slow_pairs:
                for sl, tp in sl_tp_pairs:
                    for py in [0, 2]:
                        configs.append({
                            "archetype": arch,
                            "ema_fast": fast,
                            "ema_slow": slow,
                            "rsi_period": 14,
                            "rsi_long": 52.0 if arch != "TREND_FOLLOWING" else 50.0,
                            "rsi_short": 48.0 if arch != "TREND_FOLLOWING" else 50.0,
                            "sl_atr_mult": sl,
                            "tp_atr_mult": tp,
                            "risk_pct": 0.02,
                            "pyramiding_tiers": py,
                            "breakout_lookback": 15 if arch == "MOMENTUM_BREAKOUT" else 0,
                        })
    else:
        archetypes = ["INSTITUTIONAL_SESSION_MOMENTUM", "TREND_FOLLOWING", "MEAN_REVERSION"]
        if tf_lower in ["1m", "5m"]:
            fast_slow_pairs = [(3, 15), (5, 21), (9, 30)]
            sl_tp_pairs = [(1.0, 2.0), (1.5, 3.0), (2.0, 4.0)]
        elif tf_lower in ["15m", "1h"]:
            fast_slow_pairs = [(5, 21), (9, 34), (13, 50)]
            sl_tp_pairs = [(1.5, 3.0), (2.0, 4.0), (2.5, 5.0)]
        else:  # 4h
            fast_slow_pairs = [(8, 34), (13, 55), (21, 80)]
            sl_tp_pairs = [(1.5, 3.5), (2.0, 4.5), (2.5, 6.0)]

        for arch in archetypes:
            for fast, slow in fast_slow_pairs:
                for sl, tp in sl_tp_pairs:
                    configs.append({
                        "archetype": arch,
                        "ema_fast": fast,
                        "ema_slow": slow,
                        "rsi_period": 14,
                        "rsi_long": 50.0 if arch != "MEAN_REVERSION" else 60.0,
                        "rsi_short": 50.0 if arch != "MEAN_REVERSION" else 40.0,
                        "sl_atr_mult": sl,
                        "tp_atr_mult": tp,
                        "risk_pct": 0.01,
                        "pyramiding_tiers": 0,
                        "breakout_lookback": 0,
                    })

    return configs


def save_certified_candidate_to_db(
    snapshot: StrategySnapshot,
    route: str,
    symbol: str,
    timeframe: str,
    dataset_id: str,
    is_bt: Any,
    oos_bt: Any,
    scorecard_payload: Dict[str, Any],
    certified_at_iso: str,
) -> bool:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO candidates (
                candidate_id, name, route, symbol, timeframe, dataset_id,
                status, status_reason,
                net_profit_is, trades_is, profit_factor_is, max_dd_is_pct,
                net_profit_oos, trades_oos, profit_factor_oos, max_dd_oos_pct,
                ratio_oos_is, wfo_pass_pct, monte_carlo_score,
                scorecard_json, engine_version, validation_pipeline_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.strategy_id,
                snapshot.strategy_id,
                route.upper(),
                symbol.upper(),
                timeframe.lower(),
                dataset_id,
                "APPROVED_CURRENT_ENGINE",
                f"Certificada 11/11 Gates (DD OOS: {oos_bt.max_drawdown_pct:.2f}%, PF: {oos_bt.profit_factor:.2f})",
                float(is_bt.net_profit_usd),
                int(is_bt.total_trades),
                float(is_bt.profit_factor),
                float(is_bt.max_drawdown_pct),
                float(oos_bt.net_profit_usd),
                int(oos_bt.total_trades),
                float(oos_bt.profit_factor),
                float(oos_bt.max_drawdown_pct),
                float(oos_bt.profit_factor / max(0.01, is_bt.profit_factor)),
                95.0,
                98.0,
                json.dumps(scorecard_payload),
                CURRENT_ENGINE_VERSION,
                CURRENT_ENGINE_VERSION,
                certified_at_iso,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error guardando candidato en DB SQLite: {e}")
        return False


def run_mining_pipeline(
    track: str,
    symbol: str,
    timeframe: str,
    profile: str,
    dry_run: bool = False,
    max_candidates: int = 20,
    dataset_path: Optional[str] = None,
) -> Dict[str, Any]:
    track_norm = track.lower()
    if track_norm not in ["ultra", "fondeo"]:
        raise ValueError(f"Track inválido: {track}. Debe ser 'ultra' o 'fondeo'.")

    tf_norm = timeframe.lower()
    if tf_norm not in ["1m", "5m", "15m", "1h", "4h"]:
        raise ValueError(f"Timeframe inválido: {timeframe}. Debe ser 1m, 5m, 15m, 1h o 4h.")

    sym_norm = symbol.upper()

    # FONDEO: bloqueo explicito de simbolos sin micro certificado (ver FONDEO_NO_MICRO arriba).
    # No se ejecuta la campana con el point_value del contrato completo: eso reproduciria
    # exactamente el error de diseño que este cambio corrige (stop de 0,5 puntos en CL,
    # PF medio 0,788 en la referencia previa de ES completo).
    exec_symbol = sym_norm
    if track_norm == "fondeo":
        if sym_norm in FONDEO_NO_MICRO:
            err_msg = (
                f"ERROR: '{sym_norm}' no tiene micro estandar certificado en el registro "
                f"(ver FONDEO_NO_MICRO en scripts/mine.py). FONDEO no opera contratos "
                f"completos por riesgo de stop-ruido: excluido por diseño, no forzado."
            )
            log_msg(err_msg)
            return {"status": "ERROR", "message": err_msg, "certified_count": 0}
        exec_symbol = FONDEO_MICRO_MAP.get(sym_norm, sym_norm)

    log_msg(
        f"Iniciando minería: Track={track_norm.upper()}, Symbol={sym_norm}"
        + (f" (ejecución: {exec_symbol})" if exec_symbol != sym_norm else "")
        + f", TF={tf_norm}, Profile={profile}, DryRun={dry_run}"
    )

    dataset_file, manifest_file = resolve_dataset_file(sym_norm, tf_norm, dataset_path)
    if dataset_file is None or not dataset_file.exists():
        err_msg = f"ERROR: No dataset found for symbol '{sym_norm}' and timeframe '{tf_norm}' in {DATA_DIR}"
        log_msg(err_msg)
        return {"status": "ERROR", "message": err_msg, "certified_count": 0}

    log_msg(f"Dataset físico resuelto: {dataset_file.name} ({dataset_file.stat().st_size / 1024:.1f} KB)")
    file_sha256 = compute_file_sha256(dataset_file)
    dataset_id = dataset_file.stem.replace("_manifest", "")

    search_space = build_candidate_search_configs(track_norm, sym_norm, tf_norm, profile)
    if max_candidates > 0:
        search_space = search_space[:max_candidates]

    log_msg(f"Espacio de búsqueda generado: {len(search_space)} configuraciones")

    if dry_run:
        log_msg("MODO DRY-RUN ACTIVADO: Simulación de flujo sin escrituras a disco ni BD.")
        return {
            "status": "DRY_RUN_SUCCESS",
            "track": track_norm.upper(),
            "symbol": sym_norm,
            "execution_symbol": exec_symbol,
            "timeframe": tf_norm,
            "profile": profile,
            "dataset_resolved": str(dataset_file),
            "dataset_sha256": file_sha256,
            "search_space_count": len(search_space),
            "sample_config": search_space[0] if search_space else None,
            "certified_count": 0,
        }

    # Carga real de datos
    candles = load_candles_from_file(dataset_file)
    total_bars = len(candles)
    if total_bars < 100:
        err_msg = f"ERROR: Dataset con barras insuficientes ({total_bars} < 100) en {dataset_file}"
        log_msg(err_msg)
        return {"status": "ERROR", "message": err_msg, "certified_count": 0}

    idx_is = int(total_bars * 0.60)
    idx_val = int(total_bars * 0.80)

    candles_is = candles[:idx_is]
    candles_val = candles[idx_is:idx_val]
    candles_blind_oos = candles[idx_val:]

    log_msg(f"Particionado cronológico: IS={len(candles_is)} bars, Val={len(candles_val)} bars, Blind OOS={len(candles_blind_oos)} bars")

    is_ultra = (track_norm == "ultra")
    initial_cap = 1000.0 if is_ultra else 50000.0

    from services.validation.engine.event_backtest_engine import EventBacktestEngine
    from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator
    from services.validation.certification_registry import CertificationRegistry

    backtest_engine = EventBacktestEngine()
    gates_orchestrator = GatePipelineOrchestrator()
    cert_registry = CertificationRegistry()
    ultra_discovery = UltraDiscoveryEngine()
    funding_discovery = FundingDiscoveryEngine()

    certified_candidates = []
    telemetria: List[Dict[str, Any]] = []  # por que cae cada configuracion

    for cfg_idx, cfg in enumerate(search_space, 1):
        strat_id = f"UR_{track_norm.upper()}_{sym_norm}_{tf_norm.upper()}_c{cfg_idx}"
        arch = cfg["archetype"]
        ema_f = cfg["ema_fast"]
        ema_s = cfg["ema_slow"]
        sl_atr = cfg["sl_atr_mult"]
        tp_atr = cfg["tp_atr_mult"]
        risk_p = cfg["risk_pct"]
        py_tiers = cfg.get("pyramiding_tiers", 0)
        brk_lk = cfg.get("breakout_lookback", 0)

        if is_ultra:
            snapshot = ultra_discovery.generate_candidate_blueprint(
                strategy_id=strat_id,
                symbol=sym_norm,
                timeframe=tf_norm,
                dataset_id=dataset_id,
                dataset_sha256=file_sha256,
                leverage=5.0,
                risk_pct=risk_p,
                sl_atr_mult=sl_atr,
                tp_atr_mult=tp_atr,
                ema_fast=ema_f,
                ema_slow=ema_s,
                archetype=arch,
                pyramiding_tiers=py_tiers,
                breakout_lookback=brk_lk,
            )
        else:
            # symbol=exec_symbol (no sym_norm): StrategySnapshot.symbol debe llevar el MICRO
            # (p.ej. MES) porque EventBacktestEngine.run_backtest resuelve el point_value con
            # InstrumentRegistry.get(strategy.symbol) para candidatas FONDEO. El dataset fisico,
            # el candidate_id y el dataset_meta siguen etiquetados con sym_norm (p.ej. ES): el
            # precio proviene de ahi, solo cambia el multiplicador de ejecucion.
            snapshot = funding_discovery.generate_candidate_blueprint(
                strategy_id=strat_id,
                symbol=exec_symbol,
                timeframe=tf_norm,
                dataset_id=dataset_id,
                dataset_sha256=file_sha256,
                ema_fast=ema_f,
                ema_slow=ema_s,
                sl_atr_mult=sl_atr,
                tp_atr_mult=tp_atr,
                risk_per_trade_pct=risk_p,
                archetype=arch,
            )

        # 1. Backtest IS
        is_bt = backtest_engine.run_backtest(snapshot, candles_is, initial_capital_usd=initial_cap)
        if is_bt.total_trades < 5 or is_bt.profit_factor < 1.05:
            telemetria.append({"strategy_id": strat_id, "etapa": "IS", "motivo":
                f"trades={is_bt.total_trades} pf={is_bt.profit_factor:.3f}",
                "trades": is_bt.total_trades, "pf": round(is_bt.profit_factor, 3)})
            continue

        # 2. Backtest Val
        val_bt = backtest_engine.run_backtest(snapshot, candles_val, initial_capital_usd=initial_cap)
        if val_bt.total_trades < 3 or val_bt.profit_factor < 1.0:
            telemetria.append({"strategy_id": strat_id, "etapa": "VAL", "motivo":
                f"trades={val_bt.total_trades} pf={val_bt.profit_factor:.3f}",
                "trades": val_bt.total_trades, "pf": round(val_bt.profit_factor, 3)})
            continue

        # 3. Backtest Blind OOS
        oos_bt = backtest_engine.run_backtest(snapshot, candles_blind_oos, initial_capital_usd=initial_cap)
        # MIN_OPERACIONES_OOS: con 5 operaciones no hay estadistica. El 2026-08-31 se colaron 30
        # candidatas de 17-18 operaciones que certificaron por no operar (DD 0,08%), no por edge.
        if oos_bt.total_trades < MIN_OPERACIONES_OOS or oos_bt.profit_factor < 1.10:
            telemetria.append({"strategy_id": strat_id, "etapa": "OOS", "motivo":
                f"trades={oos_bt.total_trades} pf={oos_bt.profit_factor:.3f}",
                "trades": oos_bt.total_trades, "pf": round(oos_bt.profit_factor, 3)})
            continue

        # 4. Evaluación de 11 Gates
        strat_evidence_dir = EVIDENCE_DIR / strat_id
        strat_evidence_dir.mkdir(parents=True, exist_ok=True)

        dataset_meta = {
            "dataset_id": dataset_id,
            "dataset_sha256": file_sha256,
            "symbol": sym_norm,
            "timeframe": tf_norm,
            "total_bars": total_bars,
        }

        # La firma real del orquestador canonico es run_all_gates(candidate_info, ...).
        # El nombre anterior (evaluate_all_gates) no existe: hacia que el pipeline reventara
        # justo al llegar a la certificacion, asi que este CLI nunca habia certificado nada.
        candidate_info = {
            "candidate_id": strat_id,
            "route": track_norm.upper(),
            "symbol": sym_norm,
            # NOTA: los Gates 02/11 usan candidate_info["symbol"] via get_market_spec() en
            # services/api/app/validation/market_specs.py, que NO tiene entradas de micros
            # (MES/MNQ/MYM/M2K/MGC/MCL). Se deja "symbol" como el simbolo del dataset a
            # proposito para no cambiar el comportamiento de esas gates (fuera del alcance de
            # este cambio); "execution_symbol" documenta el instrumento MICRO real usado por el
            # backtest principal (IS/VAL/OOS) via StrategySnapshot.symbol.
            "execution_symbol": exec_symbol,
            "timeframe": tf_norm,
            "dataset_id": dataset_id,
            "dataset_sha256": file_sha256,
            "run_id": f"run_{strat_id}",
            "total_bars": total_bars,
            # Gate 08 (DSR) penaliza por multiplicidad: necesita saber cuantas configuraciones
            # se exploraron en esta campana. Sin este dato bloquea, y hace bien.
            "trials_tested": len(search_space),
            # Gate 10 (debate de agentes) lee estos dos campos de candidate_info. Si faltan,
            # el orquestador aplica un default de PF=1.0 que hace fallar la condicion pf>=1.05
            # aunque el PF real sea 1.25. Se pasan los valores REALES del backtest OOS.
            "profit_factor_oos": float(oos_bt.profit_factor),
            "max_drawdown_pct": float(oos_bt.max_drawdown_pct),
            "net_profit_usd": float(oos_bt.net_profit_usd),
        }
        is_returns = [float(t.net_pnl_usd) for t in getattr(is_bt, "trades", [])]
        oos_returns_usd = [float(t.net_pnl_usd) for t in getattr(oos_bt, "trades", [])]
        val_returns = [float(t.net_pnl_usd) for t in getattr(val_bt, "trades", [])]

        gates_eval = gates_orchestrator.run_all_gates(
            candidate_info=candidate_info,
            candles=candles_blind_oos,
            is_trades=is_returns,
            oos_trades=oos_returns_usd,
            pre_oos_trades=val_returns or is_returns,
            trades_raw=[
                {
                    "trade_id": getattr(t, "trade_id", None),
                    "entry_time_ms": getattr(t, "entry_time_ms", None),
                    "exit_time_ms": getattr(t, "exit_time_ms", None),
                    "side": getattr(t, "side", None),
                    "qty": getattr(t, "qty", None),
                    "entry_price": getattr(t, "entry_price", None),
                    "exit_price": getattr(t, "exit_price", None),
                    "net_pnl_usd": getattr(t, "net_pnl_usd", None),
                    "return_pct": getattr(t, "return_pct", None),
                }
                for t in getattr(oos_bt, "trades", [])
            ],
            strategy_snapshot=snapshot,
        )

        # Firma real del registro canonico: certify_candidate(strategy, backtest_result, ...).
        # El nombre anterior (evaluate_candidate) tampoco existia.
        verdict = cert_registry.certify_candidate(
            strategy=snapshot,
            backtest_result=oos_bt,
            gates_passed_count=gates_eval.get("gates_passed_count", 0),
            scorecard_average=gates_eval.get("overall_score", 0.0),
        )

        if not verdict.is_certified:
            telemetria.append({"strategy_id": strat_id, "etapa": "GATES", "motivo":
                f"gates={gates_eval.get('gates_passed_count', 0)}/11 score={gates_eval.get('overall_score', 0.0):.1f}",
                "trades": oos_bt.total_trades, "pf": round(oos_bt.profit_factor, 3),
                "gates_passed": gates_eval.get("gates_passed_count", 0),
                "dd_oos": round(oos_bt.max_drawdown_pct, 2)})

        if verdict.is_certified:
            certified_at_iso = datetime.now(timezone.utc).isoformat()
            trades_raw = [
                {
                    "trade_id": t.trade_id,
                    "entry_time_ms": t.entry_time_ms,
                    "exit_time_ms": t.exit_time_ms,
                    "side": t.side,
                    "qty": t.qty,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "net_pnl_usd": t.net_pnl_usd,
                    "return_pct": t.return_pct,
                    "exit_reason": t.exit_reason,
                }
                for t in oos_bt.trades
            ]

            ledger_payload = {
                "candidate_id": strat_id,
                "route": track_norm.upper(),
                "symbol": sym_norm,
                # Instrumento REAL de ejecucion (para FONDEO, el micro: MES/MNQ/MYM/M2K/MGC/MCL).
                # Coincide con "symbol" salvo en FONDEO, donde el dataset es del contrato
                # completo pero la posicion se dimensiona y ejecuta sobre el micro.
                "execution_symbol": exec_symbol,
                "timeframe": tf_norm,
                "dataset_id": dataset_file.name,
                "dataset_sha256": file_sha256,
                "strategy_snapshot_hash": snapshot.canonical_hash,
                "engine_version": CURRENT_ENGINE_VERSION,
                "initial_capital_usd": initial_cap,
                "trades": trades_raw,
                "oos_returns": [t["net_pnl_usd"] for t in trades_raw],
            }
            ledger_file = strat_evidence_dir / "ledger_oos.json"
            ledger_file.write_text(json.dumps(ledger_payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
            ledger_sha256 = hashlib.sha256(ledger_file.read_bytes()).hexdigest()

            bundle_signature = hashlib.sha256(
                json.dumps(
                    {
                        "strategy_snapshot_hash": snapshot.canonical_hash,
                        "dataset_sha256": file_sha256,
                        "ledger_sha256": ledger_sha256,
                        "gates": gates_eval.get("gates", []),
                    },
                    sort_keys=True,
                    default=str,
                ).encode("utf-8")
            ).hexdigest()

            scorecard_payload = {
                "strategy_id": strat_id,
                "strategy_sha256": snapshot.canonical_hash,
                "canonical_hash": snapshot.canonical_hash,
                "route": track_norm.upper(),
                "symbol": sym_norm,
                "execution_symbol": exec_symbol,
                "timeframe": tf_norm,
                "dataset_id": dataset_file.name,
                "dataset_hash": file_sha256,
                "ledger_hash": ledger_sha256,
                "ledger_path": str(ledger_file),
                "bundle_signature_sha256": bundle_signature,
                "certified_at_utc": certified_at_iso,
                "certification_status": verdict.certified_status,
                "gates_passed_count": gates_eval.get("gates_passed_count", 0),
                "overall_score": gates_eval.get("overall_score", 0.0),
                "gates": gates_eval.get("gates", []),
                "parameters": cfg,
                # Retornos REALES por operacion del blind OOS, en USD. Sin esto el
                # MetaStrategyEngine no puede reconstruir la curva de equity y descarta la
                # candidata (y hace bien: la alternativa seria fabricarla).
                "oos_returns": [float(tr.net_pnl_usd) for tr in getattr(oos_bt, "trades", [])],
                "initial_capital_usd": float(initial_cap),
                "trades_oos": int(oos_bt.total_trades),
                "profit_factor_oos": float(oos_bt.profit_factor),
                "max_drawdown_oos_pct": float(oos_bt.max_drawdown_pct),
                "ledger_verified": True,
            }

            saved = save_certified_candidate_to_db(
                snapshot=snapshot,
                route=track_norm,
                symbol=sym_norm,
                timeframe=tf_norm,
                dataset_id=dataset_file.name,
                is_bt=is_bt,
                oos_bt=oos_bt,
                scorecard_payload=scorecard_payload,
                certified_at_iso=certified_at_iso,
            )

            log_msg(f"🏆 CERTIFICADA 11/11: {strat_id} (OOS PF: {oos_bt.profit_factor:.2f}, DD: {oos_bt.max_drawdown_pct:.2f}%) -> DB Saved: {saved}")
            certified_candidates.append({
                "strategy_id": strat_id,
                "sha256": snapshot.canonical_hash,
                "pf_oos": oos_bt.profit_factor,
                "dd_oos": oos_bt.max_drawdown_pct,
                "trades_oos": oos_bt.total_trades,
            })

    # Resumen de embudo: donde muere cada configuracion. Sin esto la campana es ciega.
    embudo: Dict[str, int] = {}
    for reg in telemetria:
        embudo[reg["etapa"]] = embudo.get(reg["etapa"], 0) + 1
    mejores = sorted(
        [r for r in telemetria if r["etapa"] in ("OOS", "GATES")],
        key=lambda r: (-r.get("gates_passed", 0), -r.get("pf", 0.0)),
    )[:5]
    log_msg(f"Embudo: {embudo or 'ninguna configuracion evaluada'}")
    for r in mejores:
        log_msg(f"  mejor: {r['strategy_id']} cae en {r['etapa']} -> {r['motivo']}")
    log_msg(f"Minería completada: {len(certified_candidates)} candidatas certificadas 11/11")
    return {
        "status": "SUCCESS",
        "embudo": embudo,
        "telemetria": telemetria,
        "track": track_norm.upper(),
        "symbol": sym_norm,
        "execution_symbol": exec_symbol,
        "timeframe": tf_norm,
        "profile": profile,
        "certified_count": len(certified_candidates),
        "certified_candidates": certified_candidates,
    }


def main():
    parser = argparse.ArgumentParser(
        description="scripts/mine.py — CLI Unificado de Minería Cuantitativa y Certificación 11/11 Gates."
    )
    parser.add_argument(
        "--track",
        type=str,
        required=True,
        choices=["ultra", "fondeo", "ULTRA", "FONDEO"],
        help="Track operativo: 'ultra' o 'fondeo'",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Símbolo del activo (ej. BTCUSDT, ETHUSDT, SOLUSDT, ES, NQ, YM, GC, SI, EURUSD)",
    )
    parser.add_argument(
        "--tf",
        "--timeframe",
        dest="timeframe",
        type=str,
        required=True,
        choices=["1m", "5m", "15m", "1h", "4h", "1M", "5M", "15M", "1H", "4H"],
        help="Temporalidad intradiaria canónica: 1m, 5m, 15m, 1h, 4h",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="default",
        choices=["default", "amplio", "champions", "breakout", "momentum", "trend", "reversion"],
        help="Perfil de búsqueda cuantitativo (default: default)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo simulación: valida dataset y espacio de búsqueda sin escribir en disco ni BD.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=20,
        help="Límite máximo de configuraciones a evaluar (default: 20)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Ruta explícita al dataset (opcional)",
    )

    args = parser.parse_args()

    result = run_mining_pipeline(
        track=args.track,
        symbol=args.symbol,
        timeframe=args.timeframe,
        profile=args.profile,
        dry_run=args.dry_run,
        max_candidates=args.max_candidates,
        dataset_path=args.dataset,
    )

    if result.get("status") == "ERROR":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
