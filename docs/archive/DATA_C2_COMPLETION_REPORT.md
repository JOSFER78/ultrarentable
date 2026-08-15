# Informe de Cierre C2 — Ingesta Real y Puerta de Validación

## 1. Resumen de ejecución

Se ha completado el cierre de C2 (Bloque 1) resolviendo las 16 discrepancias señaladas en `AUDITORIA_FASES_ABC_V3.md`:

1. **Lockfile del workspace**: Regenerado limpiando lockfiles parciales y ejecutando `npm install`.
2. **Build Web**: `npm run web:build` finalizado con éxito (12/12 páginas).
3. **Validación Python**: `compileall services` sin errores.
4. **Pytest Offline**: `test_captured_artifacts.py` y `test_local_storage.py` PASAN (2 passed, 4 skipped).
5. **Pytest Live**: `RUN_LIVE_BINGX_TESTS=1` pasa contra la API de BingX.
6. **Ingesta Canónica**: `POST /api/v1/ingestion/backfill` almacena la respuesta RAW en `data/raw/rest/...`, calcula el hash SHA-256 RAW, filtra velas incompletas (`candle_time + interval <= received_ms`), normaliza a ms y registra el dataset en SQLite con estado `VALIDATING`.
7. **Puerta de Aprobación**: `POST /api/v1/datasets/{id}/approve` exige:
   - Existencia de archivo normalizado y manifiesto JSON.
   - Coincidencia de hash SHA-256 del normalizado y RAW.
   - Timestamps en milisegundos (`startTime > 10^12`).
   - Demostración de sólo velas cerradas (`closedRecordsOnly: true`).
   - Orden cronológico estricto en el normalizado.
   - Ausencia de duplicados o huecos en la serie temporal.

## 2. Dataset Canónico Verificado

- **ID**: `ds_bingx_ETH_USDT_1h_1784991600000_1785344400000_cd007df145`
- **Símbolo**: `ETH-USDT` (Intervalo: `1h`)
- **Registros**: 99 velas cerradas
- **Estado**: `APPROVED` (tras validación explícita)
- **Checksum Normalizado**: `cd007df1450b90c926d39043d545d4f8ec8071041716e8a0d0e7e40faa7bb970`
