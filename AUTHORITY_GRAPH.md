# AUTHORITY GRAPH & REPAIR MATRIX — ULTRARENTABLE

> **Directiva:** Este documento mapea la cadena de autoridad, los puntos de bypass identificados, el estado actual de los contratos y las acciones correctivas requeridas para blindar ULTRARENTABLE como laboratorio cuantitativo con SSOT estricto.

---

## 1. MAPA DE LA CADENA DE AUTORIDAD CANÓNICA (TARGET SSOT)

```
[DATA CATALOG] (Physical CSV Manifests + SHA-256)
       │
       ▼
[HOLDOUT GATEWAY FIREWALL] (60% IS / 20% Val / 20% Blind Holdout Sealed)
       │
       ▼
[STRATEGY DISCOVERY / MUTATION] (Grammar / Novelty / Genetic)
       │
       ▼
[TRIAL REGISTRY] (Mandatory trial_id logged for every parameter variation)
       │
       ▼
[CANONICAL STRATEGY SNAPSHOT] (Frozen + Deterministic Functional SHA-256)
       │
       ▼
[CANONICAL EXECUTION CONFIG] (Instrument specifications, real tick sizes, non-zero fees, slippage, funding)
       │
       ▼
[DETERMINISTIC EVENT BACKTEST ENGINE] (Bar-by-bar execution truth)
       │
       ▼
[CANONICAL EXECUTION LEDGER] (Single Execution Truth with Sequential Merkle/Hash-Chain)
       │
       ▼
[METRICS DERIVATION ENGINE] (Lineage-aware: all metrics computed directly from ledger events)
       │
       ▼
[EVIDENCE BUNDLE & 11 GATES] (GatePipelineOrchestrator + EvidenceRecord per Gate)
       │
       ▼
[FINAL BLIND VALIDATOR] (Only authorized consumer of Blind Holdout)
       │
       ▼
[EVIDENCE GATE DECISION] (Cryptographically sealed validation outcome)
       │
       ▼
[DOMAIN API] (Read-only projection endpoints)
       │
       ▼
[FORENSIC UI] (Evidence explorer with full lineage navigation)
```

---

## 2. MATRIZ DE AUTORIDADES Y PUNTOS DE BYPASS

| Componente | Rol y Autoridad Actual | Autoridad Canónica Esperada | Riesgo / Bypass Detectado | Acción Correctiva de Inmunización | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `contracts/canonical_strategy.py` | Modelo de estrategia; `compute_sha256()` excluye `metadata`. | **SSOT Único de Estrategia**. | `metadata` podría albergar parámetros funcionales sin cambiar el hash. | Extraer cualquier parámetro funcional a campos explícitos; prohibir lógica en `metadata`. | **P0.5 LOCK** |
| `contracts/canonical_execution.py` | Configuración de costes y microestructura. | **SSOT de Ejecución**. | Defaults complacientes o sobreescritura desde requests. | Perfil estricto de instrumento; `calculate_ledger_hash()` Merkle secuencial. | **COMPLETADO (Fase 0)** |
| `contracts/backtest.py::BacktestResult` | Contenedor de métricas y trades (`profit_factor`, `sharpe`). | **Proyección / Read Model**. | Posible segunda fuente de verdad frente a `CanonicalExecutionLedger`. | Convertir en `BacktestProjection` derivada obligatoriamente del Ledger canónico. | **P0.5 LOCK** |
| `contracts/backtest.py::BacktestRequest` | Petición de backtest con campos directos de costes. | **Petición Validada**. | Posibilidad de enviar `slippage=0, fee=0` saltándose `CanonicalExecution`. | Exigir referencia a `execution_config_hash` o snapshot canónico de ejecución. | **P0.5 LOCK** |
| `contracts/backtest.py::TradeLog` | Registro de trade con `fee_usd=0, slippage_usd=0`. | **Registro Inmutable**. | Fallback silencioso a coste cero ante costes no definidos. | Eliminar defaults 0; costes obligatorios por contrato. | **P0.5 LOCK** |
| `contracts/validation_contracts.py` | `FondeoValidationResult` / `UltraValidationResult` con `passed: bool`. | **Salida de Gates**. | Posibilidad de instanciar `ValidationResult(passed=True)` manualmente. | Construcción permitida únicamente desde `EvidenceRecord` o motor determinista. | **P2 LOCK** |
| `services/validation/engine/event_backtest_engine.py` | Devuelve `EventBacktestResult`. | **Motor Determinista Oficial**. | Salida no tipada como `CanonicalExecutionLedger`. | Adaptar para producir `CanonicalExecutionLedger` con `ExecutionTruth` nativo. | **P1 LOCK** |
| `services/data/holdout_gateway.py` | Guardián de partición temporal. | **Firewall Criptográfico**. | Fuga de datos si discovery lee el tramo ciego. | Bloqueo por HMAC token y análisis de stack de llamadas. | **COMPLETADO (Fase 0)** |
| `services/discovery/strategy_search_registry.py` | Registro de hipótesis exploradas. | **Registro Global de Trials**. | Pérdida de trials para cálculo de DSR en Gate 8. | Todo experimento genera un `trial_id` persistido en SQLite. | **COMPLETADO (Fase 0)** |
| `services/portfolio/allocator.py` | Ensamblador de carteras. | **Motor de Portfolio**. | Riesgo de sumar scores escalares en vez de series de retornos. | Exigir series de retornos sincronizadas temporalmente. | **P7 LOCK** |
| `services/ultra/bala_convex_engine.py` | Lógica de subcuentas bala. | **Máquina de Estados Bala**. | Riesgo de tratar apalancamiento como convexidad sin eventos contables. | Eventos formales de apertura, piramidación, liquidación y cosecha a Bóveda. | **P6 LOCK** |
| `services/fondeo/challenge_evaluator.py` | Evaluador de exámenes. | **State Machine Fondeo**. | Tratar el fondeo como estrategia de ROI en vez de probabilidad de pase. | Reglas de Challenge vs Funded, pérdida diaria $\le \$1.000$ y sesión RTH. | **P5 LOCK** |
| `apps/web/` | Visualización en Next.js. | **Explorador Forense Read-Only**. | Riesgo de cálculos de negocio en cliente o métricas huérfanas. | La UI solo lee datos certificados; clic en métrica abre el `EvidenceRecord`. | **P10 LOCK** |
