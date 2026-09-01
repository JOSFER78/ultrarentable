"""services/sqx_bridge/export_to_sqx.py

Convierte un dataset normalizado REAL de Ultrarentable (data/normalized/*.json,
formato {"bars": [...], "dataset_id", "symbol", "timeframe", "venue", "proxy_for", ...})
al CSV que StrategyQuant X importa via `sqcli.exe -data action=import`.

Formato de salida: "MetaTrader4 bar format" (el default documentado por
`sqcli.exe -h` para `-data action=import` cuando no se especifica `format=`):
    YYYY.MM.DD,HH:MM,Open,High,Low,Close,Volume
sin cabecera, timestamps en UTC (mismo huso que trae el dataset normalizado;
SQX interpreta el fichero con el huso que se declare en `-symbol action=add
... timezone=`, no se reconvierte aqui).

REAL-ONLY: no rellena barras, no sintetiza precios ni volumen. Si el dataset
no tiene 'bars' o esta vacio, falla con ERROR explicito (no escribe un CSV
parcial silencioso). El volumen exportado es el 'volume' real del dataset
(tick_count/volumen agregado de Dukascopy), NUNCA un valor inventado; si el
dataset no trae 'volume' para una barra se exporta 0 explicitamente (no se
inventa un numero) unicamente si la clave falta, nunca si el valor es None
para una parte del rango (eso es ERROR, dataset incompleto).

Uso:
    python services/sqx_bridge/export_to_sqx.py \
        --input data/normalized/ds_dukascopy_usa500idxusd_15m_consolidated.json \
        --output <ruta_csv_destino>

No requiere SQX corriendo: es una transformacion pura de datos.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


class ExportError(ValueError):
    pass


def load_dataset(path: Path) -> dict:
    if not path.exists():
        raise ExportError(f"NO DATA: no existe el fichero de entrada {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ExportError(f"ERROR: {path} no es un objeto JSON con 'bars' (tipo real: {type(data)})")
    bars = data.get("bars")
    if not bars:
        raise ExportError(f"NO DATA: {path} no contiene 'bars' o esta vacio")
    return data


def bar_to_mt4_row(bar: dict, *, index: int, source: str) -> str:
    """Convierte una barra real del dataset a una fila 'MetaTrader4 bar format'.

    Exige explicitamente timestamp_utc_ms/open/high/low/close; cualquier
    ausencia es un ERROR (no se rellena con 0.0 ni con la barra anterior).
    """
    required = ("timestamp_utc_ms", "open", "high", "low", "close")
    missing = [k for k in required if bar.get(k) is None]
    if missing:
        raise ExportError(
            f"ERROR: barra #{index} de {source} le faltan campos obligatorios {missing}: {bar}"
        )
    ts_ms = bar["timestamp_utc_ms"]
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    date_s = dt.strftime("%Y.%m.%d")
    time_s = dt.strftime("%H:%M")
    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    # Volumen: real si esta presente (tick_count agregado real de Dukascopy vive en
    # 'volume' del dataset normalizado); si la clave no existe en absoluto se exporta
    # 0 de forma EXPLICITA (MT4 bar format exige una columna de volumen), nunca se
    # inventa un numero distinto de 0 para rellenar un hueco.
    vol = bar.get("volume")
    if vol is None:
        vol = 0
    return f"{date_s},{time_s},{o},{h},{l},{c},{vol}"


def export_dataset(input_path: Path, output_path: Path) -> dict:
    data = load_dataset(input_path)
    bars = data["bars"]
    source = data.get("dataset_id", str(input_path))

    rows = [bar_to_mt4_row(b, index=i, source=source) for i, b in enumerate(bars)]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="ascii", newline="\r\n") as f:
        f.write("\n".join(rows))
        f.write("\n")

    first_ts = bars[0]["timestamp_utc_ms"]
    last_ts = bars[-1]["timestamp_utc_ms"]
    return {
        "input": str(input_path),
        "output": str(output_path),
        "dataset_id": data.get("dataset_id"),
        "symbol": data.get("symbol"),
        "timeframe": data.get("timeframe"),
        "venue": data.get("venue"),
        "proxy_for": data.get("proxy_for"),
        "n_bars": len(bars),
        "first_bar_utc": datetime.fromtimestamp(first_ts / 1000.0, tz=timezone.utc).isoformat(),
        "last_bar_utc": datetime.fromtimestamp(last_ts / 1000.0, tz=timezone.utc).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON normalizado (data/normalized/*.json)")
    parser.add_argument("--output", required=True, type=Path, help="Ruta del CSV de salida para sqcli -data action=import")
    args = parser.parse_args(argv)

    try:
        summary = export_dataset(args.input, args.output)
    except ExportError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
