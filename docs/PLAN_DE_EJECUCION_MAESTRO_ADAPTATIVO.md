# Plan de Ejecución Maestro Adaptativo — Ultrarentable V2 (2026)

> **Directiva:** REAL-ONLY. Cero datos simulados, cero mocks, cero fallbacks hardcodeados. Todo cálculo se ejecuta de forma determinista sobre series de velas reales y modelos Pydantic validados.

---

## 📌 Fases de Ejecución

### [x] FASE 0: Saneamiento REAL-ONLY y Contratos de Código (COMPLETADA)
- **Objetivo:** Dejar la base de código limpia de errores de importación, rutas fijas y bugs de contratos en `services/` y `tests/`.
- **Acciones Ejecutadas:**
  1. **`services/exploitation_engines/prop_firm_engine.py`:**
     - Añadido `Optional` en `typing`.
     - Ejecutado `PropFirmRules.model_rebuild()` para compatibilidad total con Pydantic v2.
  2. **`services/strategy_core/spec.py` y `services/strategy_core/validator.py`:**
     - Definidos enums canónicos `AssetClass` y `StrategySource`.
     - Alias `RuleCondition = RuleConditionSpec` para compatibilidad de tipos.
     - Añadido validador flexible en `StrategySpec` (`_normalize_flexible_input`) y propiedades `@property symbol` y `@property close_at_session_end`.
  3. **`services/sqx_bridge/ingest_sqx_results.py`:**
     - Eliminada ruta absoluta hardcodeada `/home/ubuntu/...` sustituida por resolución dinámica `Path(__file__).resolve().parent.parent.parent`.
  4. **`tests/test_sqx_bridge.py`:**
     - Gestión limpia y robusta del estado `ONLINE` / `OFFLINE` del servidor MCP de StrategyQuant X.
  5. **Verificación de Tests:**
     - Ejecución de `pytest tests/ -v` arrojando **12 tests PASSED, 1 SKIPPED (SQX offline), 0 FAILED**.

---

### [x] FASE 1: Paquete de Contratos Canónicos e Inmutabilidad Pydantic v2 (COMPLETADA)
- **Objetivo:** Crear el paquete central `contracts/` con modelos Pydantic v2 inmutables (`frozen=True`) para unificar la interfaz entre FastEngine, StrategyQuant X y el subsistema de IA.
- **Acciones Ejecutadas:**
  1. **`contracts/canonical_strategy.py`:**
     - Modelo unificado `CanonicalStrategy` v2.0.0 (`frozen=True`).
     - AST completo de reglas técnicas (`ASTIndicatorNode`, `ASTRuleCondition`, `ASTActionNode`, `ASTEntryExitLogic`).
     - Configuración de instrumento, sesión, dimensionamiento de riesgo y comisiones.
     - Método determinista de hashing criptográfico `compute_provenance_hash()` (SHA-256 sobre la estructura canónica serializada).
  2. **`contracts/validation_contracts.py`:**
     - Criterios desacoplados: `FondeoValidationCriteria` (preservación CME, trailing DD $\le 4\%$, auto-flatten) y `UltraValidationCriteria` (convexidad, asimetría $\ge 3.0x$, ROI anualizado $\ge 100\%$).
     - Estructura de auditoría de compuertas `EvidenceGateDecision` y registro de balas `BalaExecutionRecord`.
  3. **`contracts/backtest.py`:**
     - Contratos inmutables de petición y resultado (`BacktestRequest`, `BacktestResult`, `BarData`, `DatasetSnapshot`, `TradeRecord`).
     - Enums estrictos de ejecución intrabar (`IntrabarPolicy.PESSIMISTIC`, `OPTIMISTIC`, `LOWER_TF_REPLAY`).
  4. **`contracts/portfolio.py`:**
     - Modelo de 6 estados de bala canónica (`BalaState`: `SEEDED`, `ACTIVE`, `RUNNER`, `HARVESTING`, `RECYCLE_PROFIT`, `STOPPED`).
     - Contratos de gestión de bóveda y retos de fondeo (`VaultRatchetConfig`, `PropChallengeConfig`, `IsolatedBullet`).
  5. **Verificación de Tests:**
     - Creado `tests/test_canonical_contracts.py`.
     - Ejecución de `pytest tests/ -v` arrojando **19 tests PASSED, 1 SKIPPED, 0 FAILED**.

---

### [ ] FASE 2: Ingesta Determinista y Persistencia SQLite / WAL
- Sincronización continua de candidatos evaluados hacia SQLite sin duplicidad de métricas.
- Índices de ordenación de alta velocidad por beneficio OOS y ruta.

---

### [ ] FASE 3: Interfaz de Usuario y Telemetría en Tiempo Real
- Control Center con paginación optimizada (`25 | 50 | 100` por página).
- Selector de rutas desacoplado (`ULTRA` vs `FONDEO`).
- Vista detallada de ADN con curvas de capital IS/OOS reales.
