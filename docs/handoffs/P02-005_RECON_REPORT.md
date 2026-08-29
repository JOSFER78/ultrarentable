# RECON REPORT — ORDEN AG2-P02-005 (STEP 0)
**Fase 02 — Universal Runtime Contract Closure**
**Fecha:** 2026-08-25T17:05:00Z
**Estado:** COMPLETED

---

## 1. Call Sites Reales de Producción
Se han mapeado los call sites de ejecución determinista en el repositorio:

1. **Cadena Canónica SSOT:**
   $$\mathbf{CanonicalStrategy} \xrightarrow{\text{compile\_to\_runtime()}} \mathbf{ExecutableRuntimeInstruction} \xrightarrow{\text{execute\_backtest()}} \mathbf{CanonicalRuntimeAdapter} \xrightarrow{\text{evaluates on physical bars}} \mathbf{RuntimeExecutionResult}$$
2. **Cadena Universal Engine:**
   $$\mathbf{CanonicalStrategy} \xrightarrow{\text{CanonicalCompiler.compile()}} \mathbf{StrategySpecification} \xrightarrow{\text{UniversalDeterministicBacktestEngine.run()}} \mathbf{UniversalBacktestResult} \xrightarrow{} \mathbf{UniversalLedger}$$

---

## 2. Boundary de Ejecución y Ledger
- **Motor Canónico:** `services/execution/canonical_runtime_adapter.py` y `services/engine/universal_backtest_engine.py`.
- **Salida de Ledger:** Cada trade genera `EvaluatedTrade` con timestamps UTC en milisegundos, precio de entrada, precio de salida, razón de salida (`STOP_LOSS`, `TAKE_PROFIT`, `TIME_STOP`, `SESSION_END`), PnL en R y USD, y un `execution_hash` SHA-256 inmutable derivado de los registros del ledger.

---

## 3. Consumidores de CanonicalStrategy
- `services/execution/canonical_runtime_adapter.py` (Ejecutor SSOT)
- `services/strategy_core/canonical_compiler.py` (Compilador universal)
- `contracts/snapshots/strategy_snapshot.py` (Snapshots inmutables con hash)
- `services/version_control_manager.py` (Linaje y gobernanza)

---

## 4. Modelos Legacy y Directiva de No-Autoridad
- Cualquier modelo de estrategia anterior (e.g. en `contracts/backtest.py` o `services/strategy_core/spec.py`) queda catalogado como **ADAPTADOR NO-AUTORITATIVO DE LECTURA**.
- `CanonicalStrategy` es la única autoridad (SSOT).

---

## 5. Gaps Semánticos a Subsanar en AG2-P02-005
1. **Direccionalidad Completa:** Implementar y probar evaluación determinista para `LONG`, `SHORT` y `BOTH`.
2. **Erradicación de Fallbacks:** Fail-Closed inmediato si ATR no tiene datos suficientes, indicador desconocido, o parámetros ausentes (cero fallbacks complacientes a `close` o `0.01 * price`).
3. **Semántica de Salidas:** Distancias exactas para `PERCENTAGE`, `FIXED_POINTS`, `ATR_MULTIPLE` y `RR_MULTIPLE`.
4. **Política de Conflicto Intrabarra:** Si el mismo bar toca SL y TP, política pesimista institucional (prioridad SL para evitar sesgos optimistas).
5. **Sizing y Riesgo:** Aplicación de `RISK_PCT_EQUITY`, `FIXED_CONTRACTS`, `FIXED_USD` y límite de `max_open_positions`.
6. **Filtro de Sesión:** `start_time_utc`, `end_time_utc`, `allowed_days`, `close_at_eod`.
7. **Binding con DatasetRegistry:** Resolución obligatoria y verificación física de SHA-256.

---

## 6. Alcance de Archivos

### Archivos Permitidos para Modificación:
- `contracts/canonical_strategy.py`
- `services/execution/canonical_runtime_adapter.py`
- `tests/test_phase02_canonical_strategy.py`
- `.agents/informe&seguimiento/*`

### Archivos Explícitamente Fuera de Alcance (`DEFERRED_TO_FUTURE_ORDER`):
- `services/discovery/*` (Phase 04)
- `services/optimization/*` (Phase 04)
- `services/portfolio/*` (Phase 05)
- `apps/web/*` (UI / Gate views no relacionadas con Fase 02)
