# RECON REPORT ? ORDEN AG2-P02-007 (STEP 0)
**Fase 02 ? Canonical Bidirectional Semantics & Real Execution Boundary Proof**
**Fecha:** 2026-08-25T21:00:00Z
**Estado:** VERIFIED & INITIALIZED

---

## 1. Verificaci?n de Identidad de Control

Se ha validado la identidad criptogr?fica y de gobernanza para la orden activa en estricta conformidad con el protocolo de control:

- **Dispatch ID:** `AG2-DISPATCH-20260825-2100-P02-007`
- **Order ID:** `AG2-P02-007`
- **Pre-execution Remote SHA:** `e0fe9864`
- **Target Phase:** `PHASE 02 ? CANONICAL BIDIRECTIONAL SEMANTICS & REAL EXECUTION BOUNDARY PROOF`
- **Execution Surface:** `origin/main` (Workspace Real: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`)
- **Doctrina:** `REAL-ONLY ? ZERO-MOCK ? ZERO-SIMULATION ? ZERO-FORCING ? ZERO-LOOKAHEAD ? FAIL-CLOSED ? ZERO-OPTIMISM`

---

## 2. Estado Inicial y Paridad con origin/main

1. **Paridad Git:**
   - El ?rbol de trabajo remoto y local se encuentra sincronizado en el commit base `e0fe9864` tras la entrega y revisi?n de la orden precedente `AG2-P02-006`.
2. **Gobernanza SSOT:**
   - `services/engine_version.py` establece como verdad ?nica institucional:
     - `CURRENT_ENGINE_VERSION = "5.4.0"`
     - `CURRENT_POLICY_VERSION = "5.4.0"`
   - `services/version_control_manager.py` verifica la huella digital criptogr?fica del c?digo fuente (`compute_codebase_fingerprint`) bloqueando cualquier code drift o mutaci?n no autorizada.
3. **Cadena de Custodia de Datos (Fase 01):**
   - `services/data/dataset_registry.py` mantiene la resoluci?n determinista de datasets f?sicos en `data/normalized/` con validaci?n estricta de hash SHA-256 (`verify_sha256=True`) y compuerta fail-closed ante procedencia no verificada (`require_verified_provenance=True`).
4. **Estado del Adaptador y Suite de Tests:**
   - La suite de regresi?n (`tests/test_phase01_dataset_chain_of_custody.py`, `tests/test_phase02_canonical_strategy.py`, `tests/test_version_control_manager_ssot.py`) cuenta con 33/33 tests pasando al 100% en 45.09s en el entorno VPS de producci?n.

---

## 3. Subsanaci?n y Consolidaci?n de Hallazgos P02-006-R01 a R04

Para la orden `AG2-P02-007`, se auditan y consolidan formalmente los 4 ejes cr?ticos de ejecuci?n:

| Hallazgo / Requisito | Denominaci?n Can?nica | Diagn?stico Forense y Mecanismo Fail-Closed Implementado | Call-Sites en C?digo Fuente |
|---|---|---|---|
| **P02-006-R01** | **Sem?ntica Real Bidireccional (`BOTH`)** | Erradicaci?n total de la inferencia heur?stica de operadores (`_invert_condition`, `_invert_operator`). En `contracts/canonical_strategy.py`, `RuleTree` requiere expl?citamente `long_conditions` y `short_conditions` para `direction == "BOTH"`. En `CanonicalRuntimeAdapter`, el motor eval?a ambas ramas declarativas de forma independiente sin mutaciones autom?ticas. | `contracts/canonical_strategy.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **P02-006-R02** | **Cero Defaults de Capital (`account_equity_usd`)** | Eliminaci?n de valores por defecto complacientes en `execute_backtest()`. El capital de la cuenta `account_equity_usd` es un argumento posicional obligatorio (> 0). Si es `None`, $\le 0$, no num?rico o `NaN`, el motor falla cerrado lanzando de inmediato `InvalidStrategyError`. | `services/execution/canonical_runtime_adapter.py` (L270?290) |
| **P02-006-R03** | **Fallo Cerrado de Concurrencia (`max_open_positions`)** | En el runtime monohilo actual, la concurrencia permitida por estrategia es estrictamente de 1 posici?n activa simult?nea (`max_open_positions == 1: SUPPORTED_AND_EXECUTED`). Si una estrategia define `max_open_positions > 1`, el runtime lanza expl?citamente `InvalidStrategyError` (`UNSUPPORTED_FAIL_CLOSED`). | `services/execution/canonical_runtime_adapter.py` (L298?304) |
| **P02-006-R04** | **Sizing Instrument-Aware con Microestructura Real** | Vinculaci?n obligatoria con `CANONICAL_COST_REGISTRY` (`services/data/instrument_cost_registry.py`). El dimensionamiento por riesgo (`RISK_PCT_EQUITY` y `FIXED_USD`) y el PnL monetario integran la f?sica real del activo (`point_value` y `contract_multiplier`):<br>$$\text{size} = \frac{\text{equity} \times (\text{risk\_pct} / 100)}{\Delta_{SL} \times \text{point\_value} \times \text{multiplier}}$$<br>$$\text{PnL}_{\text{USD}} = \Delta_{\text{price}} \times \text{point\_value} \times \text{multiplier} \times \text{size}$$ | `services/execution/canonical_runtime_adapter.py` |

---

## 4. L?mites de Scope y Guardarra?les de la Fase 02

### 4.1 En Alcance (Phase 02):
- `contracts/canonical_strategy.py`
- `contracts/snapshots/strategy_snapshot.py`
- `contracts/canonical_execution.py`
- `services/execution/canonical_runtime_adapter.py`
- `services/validation/engine/event_backtest_engine.py`
- `services/data/instrument_cost_registry.py`
- `tests/test_phase02_canonical_strategy.py`
- `.agents/informe&seguimiento/*`

### 4.2 Expl?citamente Fuera de Alcance (`DEFERRED_TO_FUTURE_ORDER`):
- `services/discovery/*` (Fase 04 ? Discovery Factory & Blueprints)
- `services/research/*` (Fase 04 ? Quantitative Research Lab & Multi-Agent Debate)
- `services/portfolio/*` (Fase 05 ? Multi-Strategy Portfolio Allocation)
- `apps/web/*` (Frontend UI & Dashboards)

