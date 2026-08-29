# RUNTIME SEMANTIC MATRIX — ORDEN AG2-P02-005 (STEP 1)
**Fase 02 — Universal Runtime Contract Closure**
**Fecha:** 2026-08-25T17:06:00Z
**Estado:** VIGENTE & COMPLETA

---

## Matriz de Semántica de Ejecución Canónica

| Elemento Semántico | Estado de Ejecución | Regla de Validación y Fail-Closed | Archivo de Implementación |
|---|---|---|---|
| **Direction LONG** | `SUPPORTED_AND_EXECUTED` | Compra en trigger, SL por debajo, TP por encima, PnL = (exit - entry). | `services/execution/canonical_runtime_adapter.py` |
| **Direction SHORT** | `SUPPORTED_AND_EXECUTED` | Venta en trigger, SL por encima, TP por debajo, PnL = (entry - exit). | `services/execution/canonical_runtime_adapter.py` |
| **Direction BOTH** | `SUPPORTED_AND_EXECUTED` | Permite alternar entradas LONG y SHORT según la condición disparada. | `services/execution/canonical_runtime_adapter.py` |
| **LogicalOp AND** | `SUPPORTED_AND_EXECUTED` | Todas las condiciones del RuleTree deben ser verdaderas en `t`. | `services/execution/canonical_runtime_adapter.py` |
| **LogicalOp OR** | `SUPPORTED_AND_EXECUTED` | Al menos una condición del RuleTree debe ser verdadera en `t`. | `services/execution/canonical_runtime_adapter.py` |
| **Indicators (EMA, SMA, ATR, PRICE)** | `SUPPORTED_AND_EXECUTED` | Cálculo determinista sin lookahead respetando `source_field`, `params` y `shift`. | `services/execution/canonical_runtime_adapter.py` |
| **Unknown Indicator** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` de inmediato; 0% fallbacks a `close`. | `services/execution/canonical_runtime_adapter.py` |
| **Missing Indicator Param** | `UNSUPPORTED_FAIL_CLOSED` | Falta de `period` u otro parámetro obligatorio lanza `InvalidStrategyError`. | `services/execution/canonical_runtime_adapter.py` |
| **Missing ATR Data** | `UNSUPPORTED_FAIL_CLOSED` | Si el historial es menor a `period`, devuelve NaN y no genera trade; nunca inventa un valor. | `services/execution/canonical_runtime_adapter.py` |
| **SL Type: PERCENTAGE** | `SUPPORTED_AND_EXECUTED` | Distancia = `entry_price * (sl_val / 100.0)`. | `services/execution/canonical_runtime_adapter.py` |
| **SL Type: FIXED_POINTS** | `SUPPORTED_AND_EXECUTED` | Distancia = `sl_val`. | `services/execution/canonical_runtime_adapter.py` |
| **SL Type: ATR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia = `ATR(14) * sl_val`. | `services/execution/canonical_runtime_adapter.py` |
| **SL Type: BAR_LOW_HIGH** | `UNSUPPORTED_FAIL_CLOSED` | Rechazado si no está parametrizado con offset explícito. | `services/execution/canonical_runtime_adapter.py` |
| **TP Type: RR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia = `sl_distance * tp_val`. | `services/execution/canonical_runtime_adapter.py` |
| **TP Type: PERCENTAGE** | `SUPPORTED_AND_EXECUTED` | Distancia = `entry_price * (tp_val / 100.0)`. | `services/execution/canonical_runtime_adapter.py` |
| **TP Type: FIXED_POINTS** | `SUPPORTED_AND_EXECUTED` | Distancia = `tp_val`. | `services/execution/canonical_runtime_adapter.py` |
| **TP Type: ATR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia = `ATR(14) * tp_val`. | `services/execution/canonical_runtime_adapter.py` |
| **Intrabar SL/TP Conflict** | `SUPPORTED_AND_EXECUTED` | Política pesimista institucional: si una vela toca SL y TP, se ejecuta SL. | `services/execution/canonical_runtime_adapter.py` |
| **Trailing Stop (`trail_after_r`)**| `SUPPORTED_AND_EXECUTED` | Al alcanzar R múltiplos, mueve SL a Breakeven (`entry_price`). | `services/execution/canonical_runtime_adapter.py` |
| **Time Stop (`time_stop_bars`)** | `SUPPORTED_AND_EXECUTED` | Cierre forzoso a precio de cierre tras `time_stop_bars` barras. | `services/execution/canonical_runtime_adapter.py` |
| **Sizing: RISK_PCT_EQUITY** | `SUPPORTED_AND_EXECUTED` | Riesgo monetario = `capital * (risk_value / 100.0)`. | `services/execution/canonical_runtime_adapter.py` |
| **Sizing: FIXED_CONTRACTS** | `SUPPORTED_AND_EXECUTED` | Contratos fijos = `risk_value`. | `services/execution/canonical_runtime_adapter.py` |
| **Sizing: FIXED_USD** | `SUPPORTED_AND_EXECUTED` | Riesgo fijo = `risk_value` en USD. | `services/execution/canonical_runtime_adapter.py` |
| **Max Open Positions** | `SUPPORTED_AND_EXECUTED` | Bloquea nuevas entradas si posiciones abiertas >= `max_open_positions`. | `services/execution/canonical_runtime_adapter.py` |
| **Session Window (`start`/`end`)** | `SUPPORTED_AND_EXECUTED` | Filtra entradas fuera de la ventana horaria UTC declarada. | `services/execution/canonical_runtime_adapter.py` |
| **Session Allowed Days** | `SUPPORTED_AND_EXECUTED` | Filtra entradas en días no permitidos (0=Lun, 6=Dom). | `services/execution/canonical_runtime_adapter.py` |
| **Close at EOD** | `SUPPORTED_AND_EXECUTED` | Cierra posiciones abiertas al alcanzar `end_time_utc`. | `services/execution/canonical_runtime_adapter.py` |
| **Engine & Policy Version** | `SUPPORTED_AND_EXECUTED` | Exige obligatoriamente versiones explícitas desde SSOT de gobernanza. | `services/execution/canonical_runtime_adapter.py` |
| **Dataset Provenance Binding** | `SUPPORTED_AND_EXECUTED` | Resuelve dataset físico en `DatasetRegistry` con verificación SHA-256 física. | `services/execution/canonical_runtime_adapter.py` |
| **Strategy Lineage Binding** | `SUPPORTED_AND_EXECUTED` | Enlaza `strategy_hash`, `dataset_sha256`, `engine_version` en `RuntimeExecutionResult`.| `services/execution/canonical_runtime_adapter.py` |
