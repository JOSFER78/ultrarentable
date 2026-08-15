# Informe de Entrega — Fase E: FAST Engine Determinista Real

## 1. Resumen de Implementación

Se ha construido el motor rápido determinista para interpretar la representación intermedia (IR) compilada desde estrategias DSL v1.0.0.

- **Ubicación del paquete**: `services/api/app/engine/`
  - `fast_engine.py`: Ejecutor de IR sin `eval` ni `exec`.
  - `indicator_calc.py`: Cálculo determinista con Numpy (SMA, EMA, RSI, ATR, HIGHEST, LOWEST, ROC, STDDEV, VOLUME_RATIO).
  - `margin_model.py`: Modelo de margen aislado/cruzado y liquidación por margen de mantenimiento.
  - `ledger.py`: Generador determinista de transacciones, ejecuciones y curva de equity.

## 2. Garantías de Integridad y Regla REAL-ONLY

1. **Sin Look-Ahead**: Ejecución determinista barra a barra en la observación de apertura $t+1$ (`BAR_CLOSE_EXECUTE_NEXT_OPEN`).
2. **Datasets Aprobados**: Exclusivamente datasets `APPROVED` con manifiesto y hash SHA-256 verificado en disco.
3. **Comisiones y Funding Real**: Se exige snapshot real de comisiones (`maker_fee_rate`, `taker_fee_rate`) desde el catálogo de BingX. Excepción `MISSING_FEE_SNAPSHOT` si falta el snapshot.
4. **Etiquetado de Resultados**: Todos los resultados de este motor se etiquetan obligatoriamente como `FAST_APPROXIMATE` (nunca `CANONICAL`).

## 3. Endpoints API Creados

- `POST /api/v1/backtests/fast`
- `GET /api/v1/backtests/{id}`
- `GET /api/v1/backtests/{id}/trades`
- `GET /api/v1/backtests/{id}/equity`
- `GET /api/v1/backtests/{id}/artifacts`
- `POST /api/v1/backtests/{id}/reproduce`

## 4. Resultados de Pruebas (3/3 PASSED)

- `test_missing_fee_snapshot_throws_exception`: PASSED
- `test_fast_engine_execution_reproducibility`: PASSED
- `test_unapproved_dataset_rejected`: PASSED
