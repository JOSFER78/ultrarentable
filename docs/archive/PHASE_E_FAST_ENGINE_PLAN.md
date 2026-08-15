# Plan de Arquitectura — Fase E: FAST Engine Determinista Real

## 1. Módulo y Estructura

Se creará el paquete de motor rápido en:

```text
services/api/app/engine/
  ├── __init__.py
  ├── fast_engine.py      # Ejecutor determinista de IR compilada
  ├── indicator_calc.py   # Calculadora de series de indicadores (Numpy/Pandas)
  ├── margin_model.py     # Modelo de margen aislado/cruzado y liquidación aproximada
  └── ledger.py           # Generador de transacciones, ejecuciones y curva de equity
```

## 2. Requisitos de Ejecución Estricta

1. **Entrada**: Exclusivamente datasets con estado `APPROVED` en la base de datos y verificación previa de checksum SHA-256 en disco.
2. **Interpretación de IR**: Ejecución de las instrucciones declarativas compiladas por el módulo DSL (`LOAD_SERIES`, `COMPUTE_EMA`, `COMPARE_GT`, etc.). Sin `eval()` ni `exec()`.
3. **Ausencia de Look-Ahead**: Cálculo barra a barra ($t$). La señal generada en la barra $t$ genera una orden ejecutada en el precio de apertura de la barra $t+1$ (`BAR_CLOSE_EXECUTE_NEXT_OPEN`).
4. **Comisiones y Funding Real**:
   - `maker_fee_rate` y `taker_fee_rate` obtenidos desde el snapshot del catálogo de instrumentos (`InstrumentModel`). Si no existen datos de comisiones, lanza la excepción `MISSING_FEE_SNAPSHOT` (sin valores por defecto arbitrarios).
   - `funding_rate` obtenido de la serie histórica cuando la estrategia o posición lo requiera. Si falta la serie, devuelve `MISSING_FUNDING_SERIES`.
5. **Modelado Financiero**:
   - Apalancamiento ($1\times$ a $125\times$).
   - Asignación de capital (`allocationPct`).
   - Interés compuesto (`compound: true/false`).
   - Piramidación (`maxEntries`).
   - Liquidación mark-to-market cuando el valor del margen caiga por debajo de la tasa de mantenimiento.
6. **Resultados y Etiquetado**:
   - Tipo de motor: `FAST_APPROXIMATE` (nunca `CANONICAL`).
   - Métricas: `net_return_pct`, `max_drawdown_pct`, `win_rate`, `trades_count`, `profit_factor`, `final_equity`.
   - Códigos de fallo: `NO_TRADES`, `TOO_FEW_TRADES`, `LIQUIDATED`, `NEGATIVE_EQUITY`, `FEES_DOMINATE`, `FUNDING_DOMINATE`, `INVALID_ORDER`, `INSUFFICIENT_MARGIN`, `MISSING_SERIES`, `DATA_GAP`, `NON_REPRODUCIBLE`.
   - Artefactos: Ledger de trades en JSON y curva de equity con checksum SHA-256 en `data/artifacts/backtests/<id>/`.

## 3. Endpoints API

- `POST /api/v1/backtests/fast`
- `GET /api/v1/backtests/{id}`
- `GET /api/v1/backtests/{id}/trades`
- `GET /api/v1/backtests/{id}/equity`
- `GET /api/v1/backtests/{id}/artifacts`
- `POST /api/v1/backtests/{id}/reproduce`

## 4. Tests de Verificación

Suite en `services/api/tests/test_fast_engine.py`:
- Test sin look-ahead (verificación barra $t \to t+1$).
- Test de posiciones Long y Short.
- Test de comisiones reales y error por snapshot ausente.
- Test de compounding y piramidación.
- Test de regla de liquidación por margen.
- Test de reproducibilidad exacta con misma semilla e IR.
