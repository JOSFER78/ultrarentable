# RECON REPORT ? ORDEN AG2-P02-006 (STEP 0)
**Fase 02 ? Phase 02 Behavioral Runtime Proof**
**Fecha:** 2026-08-25T19:15:00Z
**Estado:** VERIFIED & INITIALIZED

---

## 1. Verificaci?n de Identidad de Control

Se ha validado la identidad criptogr?fica y de gobernanza para la orden activa:

- **Dispatch ID:** `AG2-DISPATCH-20260825-2030-P02-006`
- **Order ID:** `AG2-P02-006`
- **Pre-execution Remote SHA:** `598a7d26`
- **Target Phase:** `PHASE 02 ? BEHAVIORAL RUNTIME PROOF & RUNTIME CONTRACT FINAL CLOSURE`
- **Execution Surface:** `origin/main` (Workspace Real: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`)
- **Doctrina:** `REAL-ONLY ? ZERO-MOCK ? ZERO-SIMULATION ? ZERO-FORCING ? ZERO-LOOKAHEAD ? FAIL-CLOSED`

---

## 2. Estado Inicial y Paridad con origin/main

1. **Paridad Git:** El ?rbol de trabajo local y remoto se encuentra sincronizado en el commit base `598a7d26`.
2. **Gobernanza SSOT:** 
   - `services/engine_version.py` establece `CURRENT_ENGINE_VERSION = "5.4.0"` y `CURRENT_POLICY_VERSION = "5.4.0"`.
   - `services/version_control_manager.py` verifica la huella digital del c?digo fuente (`compute_codebase_fingerprint`) y previene cualquier code drift no autorizado.
3. **Cadena de Custodia:**
   - `services/data/dataset_registry.py` (completado en P01) proporciona resoluci?n determinista de datasets f?sicos en `data/normalized/` mediante verificaci?n estricta de hash SHA-256 (`verify_sha256=True`) y compuerta de procedencia verificada (`require_verified_provenance=True`).
4. **Adaptador de Ejecuci?n Can?nica:**
   - `services/execution/canonical_runtime_adapter.py` implementa el motor determinista de ejecuci?n en runtime consumiendo `CanonicalStrategy` y emitiendo `RuntimeExecutionResult` con `execution_hash`.
5. **Suite de Pruebas de Fase 02:**
   - `tests/test_phase02_canonical_strategy.py` contiene los tests unitarios y de integraci?n de la matriz sem?ntica universal.

---

## 3. Requisitos Sem?nticos y de Ejecuci?n (R01 a R09)

Para alcanzar el cierre formal y demostrable de la orden `AG2-P02-006`, se auditan y garantizan los siguientes 9 ejes de requisitos:

| Requisito | Denominaci?n | Definici?n y Mecanismo Fail-Closed | Archivos Involucrados |
|---|---|---|---|
| **R01** | **Exact Semantic Identity & Strategy AST Integrity** | `CanonicalStrategy` es inmutable (`frozen=True`, `extra="forbid"`). Su `strategy_hash` SHA-256 cubre el 100% de la identidad sem?ntica. `verify_integrity()` valida el hash antes de compilar; cualquier discrepancia o manipulaci?n lanza `StrategyIntegrityError`. | `contracts/canonical_strategy.py` |
| **R02** | **Universal Directional Semantics (LONG, SHORT, BOTH)** | Evaluaci?n sim?trica de triggers y salidas para posiciones `LONG`, `SHORT` y modo `BOTH`. C?lculo exacto de distancias SL/TP y PnL en R y USD seg?n el lado operativo. | `services/execution/canonical_runtime_adapter.py` |
| **R03** | **Zero-Complacent Parameter & Indicator Fallbacks** | Prohibici?n absoluta de defaults silenciosos. Si un indicador carece de `period`, es desconocido, referencia una fuente inexistente o el ATR carece de barras suficientes, el motor lanza `InvalidStrategyError` de inmediato (0% fallback a `close` o `0.01 * price`). | `services/execution/canonical_runtime_adapter.py` |
| **R04** | **Deterministic Intrabar Conflict Policy (Zero-Optimism)** | Si en una misma barra concurren niveles de Stop Loss y Take Profit (`Low <= SL` y `High >= TP` para LONG), el motor ejecuta obligatoriamente el Stop Loss bajo pol?tica pesimista institucional para evitar sesgos optimistas. | `services/execution/canonical_runtime_adapter.py`, `services/validation/engine/event_backtest_engine.py` |
| **R05** | **Quantitative Sizing & Risk Limits** | Soporte estricto para `RISK_PCT_EQUITY`, `FIXED_CONTRACTS`, `FIXED_USD`. Exigencia de `sl_distance > 0` para sizing por riesgo monetario. Respeto estricto del l?mite `max_open_positions`. | `contracts/canonical_strategy.py`, `services/execution/canonical_runtime_adapter.py` |
| **R06** | **Session Filtering & Mandatory Allowed Days** | Filtrado horario UTC (`start_time_utc`, `end_time_utc`), verificaci?n estricta de `allowed_days` (obligatorio, no vac?o) y liquidaci?n forzada en fin de sesi?n diaria (`close_at_eod=True`). | `contracts/canonical_strategy.py`, `services/execution/canonical_runtime_adapter.py` |
| **R07** | **Physical Dataset Binding & SHA-256 Custody** | Prohibici?n de inyectar datos artificiales. `execute_backtest()` resuelve el dataset mediante `DatasetRegistry.resolve_dataset()`, carga datos reales desde disco y valida el SHA-256 f?sico de la partici?n. | `services/data/dataset_registry.py`, `services/execution/canonical_runtime_adapter.py` |
| **R08** | **Deterministic Ledger Output & Execution Hash** | Cada trade genera un `EvaluatedTrade` inmutable con timestamps UTC en ms, precios de entrada/salida, raz?n de salida (`STOP_LOSS`, `TAKE_PROFIT`, `TIME_STOP`, `SESSION_EOD`, `LIQUIDATION`) y PnL. El resultado genera un `execution_hash` SHA-256 determinista reproducible bit a bit. | `services/execution/canonical_runtime_adapter.py` |
| **R09** | **Version Governance & Code Drift Defense** | Vinculaci?n obligatoria de `engine_version` y `policy_version` procedentes del SSOT (`services/engine_version.py`). Ausencia de versiones lanza excepci?n inmediata. Detecci?n de drift mediante fingerprinting SHA-256 del codebase. | `services/engine_version.py`, `services/version_control_manager.py`, `services/execution/canonical_runtime_adapter.py` |

---

## 4. L?mites de Scope y Guardarra?les

### 4.1 En Alcance (Phase 02):
- `contracts/canonical_strategy.py`
- `contracts/snapshots/strategy_snapshot.py`
- `services/execution/canonical_runtime_adapter.py`
- `services/validation/engine/event_backtest_engine.py`
- `tests/test_phase02_canonical_strategy.py`
- `.agents/informe&seguimiento/*`

### 4.2 Expl?citamente Fuera de Alcance (`DEFERRED_TO_FUTURE_ORDER`):
- `services/discovery/*` (Phase 04 - Discovery Factory)
- `services/optimization/*` (Phase 04 - Optimization & Mutation)
- `services/portfolio/*` (Phase 05 - Portfolio & Allocation)
- `apps/web/*` (UI / Gate views no relacionadas con el runtime de Fase 02)

