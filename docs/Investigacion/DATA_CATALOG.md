# Catálogo de datos

## Dataset mínimo

- OHLCV 5m y 15m.
- Funding histórico.
- Especificaciones del instrumento por vigencia.
- Calendario de cambios de fees cuando sea posible.

## Particionado

```text
data/catalog/{exchange}/{instrument}/{timeframe}/year=YYYY/month=MM/*.parquet
```

## Manifest obligatorio

```yaml
exchange: binance_usdm
instrument: ETHUSDT-PERP
timeframe: 5m
start: 2023-01-01T00:00:00Z
end: 2026-01-01T00:00:00Z
rows: 315360
checksum: sha256:...
source_version: v1
schema_version: 1
quality:
  gaps: 0
  duplicates: 0
  repaired_rows: 0
```

## Ventanas

Cada ventana se deriva de:

```text
window_id = hash(dataset_version, start, end, seed, warmup)
```

No se generan ventanas sobre la marcha sin persistir su definición.
