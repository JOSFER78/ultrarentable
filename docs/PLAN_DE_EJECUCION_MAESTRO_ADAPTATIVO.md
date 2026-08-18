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

### [x] FASE 2: Desacoplamiento Modular & Clean Architecture (COMPLETADA)
- **Objetivo:** Desacoplar el acceso a datos monolítico estructurando los microservicios bajo Clean Architecture (`services/data`, `services/backtest`, `services/validation`, `services/evidence`, `services/semantic_ai`, `services/portfolio`, `services/fondeo`, `services/paper`, `services/execution`, `services/monitoring`) e integrando un `AsyncEventBus` tipado e inmutable.
- **Acciones Ejecutadas:**
  1. **`services/core/event_bus.py`:**
     - `AsyncEventBus` tipado y no bloqueante en memoria.
     - Eventos canónicos inmutables (`StrategyGeneratedEvent`, `BacktestRequestedEvent`, `BacktestCompletedEvent`, `ValidationCompletedEvent`, `CandidatePromotedEvent`, `BulletStateChangedEvent`, `VaultHarvestExecutedEvent`, `PortfolioRebalancedEvent`).
  2. **Microservicios de Dominio Aislados:**
     - `services/data`: `DatasetRepository` para snapshots deterministas de velas reales.
     - `services/backtest`: `BacktestEnginePort` y `FastEngineAdapter`.
     - `services/validation`: `GateEvaluator` con compuertas desacopladas para Fondeo y Ultra.
     - `services/evidence`: `EvidenceVault` para paquetes inmutables indexados por SHA-256.
     - `services/semantic_ai`: `SemanticMutationEngine` para generación de estrategias canónicas.
     - `services/portfolio`: `PortfolioAllocator` y `BulletLifecycleManager` (6 estados de bala).
     - `services/fondeo`: `PropChallengeEvaluator` para auditoría de reglas de evaluación CME.
     - `services/paper`: `PaperBrokerSimulator` con slippage y costes.
     - `services/execution`: `OrderRouter` para derivación a BingX o Tradovate.
     - `services/monitoring`: `HealthMonitor` y `SystemHealthTelemetry`.
  3. **Verificación de Tests:**
     - Creado `tests/test_event_bus_and_isolation.py`.
     - Pipeline E2E validado: Generación $\to$ Backtest $\to$ Validación $\to$ Bóveda de Evidencia.
     - Ejecución de `pytest tests/ -v` arrojando **23 tests PASSED, 1 SKIPPED, 0 FAILED**.

---

### [x] FASE 4: Quant Validation Fabric Bifurcado & Evidence Gate (COMPLETADA)
- **Objetivo:** Implementar el motor de validación cuantitativa `QuantValidationFabric` con compuertas desacopladas (`FondeoEvidenceGate` y `UltraEvidenceGate`), Máquina de Estados Finitos `CandidateRegistry` (10 estados discretos) y arnés de Golden Tests deterministas.
- **Acciones Ejecutadas:**
  1. **`services/validation/metrics_calculator.py`:**
     - Deflated Sharpe Ratio (DSR) ajustado por sesgo de selección y no-normalidad (Bailey & López de Prado).
     - Dependencia de outliers (Top-2 trades sobre ganancia total).
     - Tail Gain Ratio (ganancias en cola derecha $\ge 3.0R$).
     - Monte Carlo de ráfagas de 20 balas para probabilidad de supervivencia de la bóveda nodriza.
     - Test de estrés por fricción piramidal y spread/slippage aumentado.
  2. **`services/validation/fondeo_gate.py`:**
     - `FondeoEvidenceGate`: Criterios institucionales CME Prop Firms (Sharpe, DSR, Max DD $< 4.5\%$, Outliers $< 15\%$, single trade share $< 30\%$).
  3. **`services/validation/ultra_gate.py`:**
     - `UltraEvidenceGate`: Criterios de asimetría BingX Crypto (Payoff Ratio $\ge 3.0$, Tail Gain $\ge 60\%$, $E(Bala) \ge 0.20R$, fricción y supervivencia de ráfagas).
  4. **`services/validation/quant_fabric.py`:**
     - `QuantValidationFabric`: Orquestador de validación que bifurca según `target_track` y genera `EvidenceGateDecision` con hash criptográfico SHA-256 de procedencia.
  5. **`services/validation/candidate_registry.py`:**
     - `CandidateRegistry`: FSM estricta sobre los 10 estados discretos de `StrategyLifecycleStatus` con validación de grafo de transición y trazabilidad inmutable.
  6. **Verificación de Tests:**
     - Creado `tests/test_quant_validation_fabric.py` con Golden Tests bit a bit.
     - Ejecución de `pytest tests/ -v` arrojando **28 tests PASSED, 1 SKIPPED, 0 FAILED**.

---

### [x] FASE 5: Semantic AI Engine & Memoria de Fallos FailureKnowledge (COMPLETADA)
- **Objetivo:** Implementar el motor `SemanticQuantEngine` con orquestación de agentes especializados (`Interpreter`, `Critic`, `Improver`, `RegimeAnalyst`, `AdversarialResearcher`), la base de datos de aprendizaje de fallos (`FailureKnowledgeDB`) y el pipeline de mutación/cruce de estrategias canónicas bajo la regla de gobernanza: "La IA propone candidatos, el Evidence Gate aprueba o rechaza".
- **Acciones Ejecutadas:**
  1. **`services/semantic_ai/failure_knowledge.py`:**
     - `FailureKnowledgeDB`: Catálogo estructurado de firmas de fallos (`FailureType`: `OVERFITTING_OOS`, `OUTLIER_DEPENDENCY`, `MAX_DRAWDOWN_EXCEEDED`, `FRICTION_SENSITIVITY`, `BURST_RUIN_RISK`, `INSUFFICIENT_PAYOFF`).
     - Cálculo de firmas canónicas de indicadores (`indicator_fingerprint`) y penalización progresiva para guiar la búsqueda estocástica.
     - Registro directo desde decisiones de compuerta (`record_from_gate_decision`).
  2. **`services/semantic_ai/semantic_engine.py`:**
     - `SemanticQuantEngine`: Orquestación modular de roles:
       - `Interpreter`: Traducción semántica del AST a lenguaje económico y técnico comprensible.
       - `Critic`: Auditoría previa contra la memoria de fallos y validación de reglas de fondeo / ultra.
       - `Improver`: Mutación de parámetros y cruce (`crossover`) genético-semántico de estrategias padre.
       - `RegimeAnalyst`: Clasificación de regímenes de mercado (`BULL_TRENDING`, `BEAR_TRENDING`, `CHOPPY_RANGING`, `HIGH_VOLATILITY_EXPANSION`).
       - `AdversarialResearcher`: Generación de parámetros y multiplicadores de estrés para robustez extrema.
  3. **Verificación de Tests:**
     - Creado `tests/test_semantic_ai_and_failure_db.py`.
     - Verificada la regla de gobernanza ("La IA propone, el Gate decide").
     - Ejecución de `pytest tests/ -v` arrojando **34 tests PASSED, 1 SKIPPED, 0 FAILED**.

---

### [x] FASE 6: Portfolio Multi-Activo & UltraExploitationEngine (COMPLETADA)
- **Objetivo:** Implementar el motor de optimización de carteras `PortfolioEngine` con alineación temporal estricta de trades (NQ, ES, BTC, ETH) y el `UltraExploitationEngine` con la Máquina de Estados de la Bala (6 estados: `INICIO`, `CONFIRMACION`, `CRECIMIENTO_RECYCLING`, `COSECHA_VAULT`, `PROTECCION`, `CIERRE`), piramidación financiada por House Money ($40\%$) y Bóveda de Cosecha Ratchet inmutable.
- **Acciones Ejecutadas:**
  1. **`services/portfolio/portfolio_engine.py`:**
     - Alineación sincrónica de series de retornos por timestamps UTC exactos en matriz $T \times N$.
     - Cálculo de matriz de covarianza real $\Sigma$ y ratios de diversificación.
     - Métodos de asignación: `EQUAL_WEIGHT`, `INVERSE_VOLATILITY`, `RISK_PARITY_ERC` (Equal Risk Contribution) y `HIERARCHICAL_RISK_PARITY` (HRP).
     - Generación del contrato inmutable `PortfolioAllocation` con firma criptográfica SHA-256.
  2. **`services/exploitation_engines/ultra_engine.py`:**
     - `UltraExploitationEngine`:
       - Ciclo de vida FSM de la Bala (6 estados discretos).
       - Piramidación Free-Risk: adición de capas financiada al $40\%$ por beneficio no realizado (House Money) con ajuste de SL para garantizar beneficio neto.
       - Milestones Ratchet de cosecha hacia la Bóveda Nodriza ($2x \to 50\%$, $3x \to 65\%$, $5x \to 75\%$, $10x \to 85\%$).
       - Registro consolidado `BalaExecutionRecord` y eventos `BalaHarvestEvent`.
  3. **Verificación de Tests:**
     - Creado `tests/test_portfolio_and_ultra_engine.py`.
     - Validada la optimización de pesos y la piramidación con cosecha Ratchet a la Bóveda.
     - Ejecución de `pytest tests/ -v` arrojando **36 tests PASSED, 1 SKIPPED, 0 FAILED**.

---

### [x] FASE 7: Sandbox de Paper Trading en Tiempo Real - 14 Días (COMPLETADA)
- **Objetivo:** Implementar el motor de incubación en tiempo real (`PaperSandboxEngine`) que ejecuta estrategias aprobadas en modo `INCUBATION_PAPER` durante un periodo de observación de 14 días contra datos en vivo, con métricas de degradación OOS y aborto automático.
- **Acciones Ejecutadas:**
  1. **`services/paper/paper_sandbox_engine.py`:**
     - `PaperSandboxEngine`: Simulación mark-to-market de fills en tiempo real con modelado de slippage dinámico, comisiones y latencia de red (50ms).
     - Seguimiento de equidad, trades realizados, fees acumulados y métricas operacionales continuas (`PaperMetrics`).
  2. **`services/paper/incubation_evaluator.py`:**
     - `IncubationEvaluator`: Chequeo continuo contra la línea base de backtest (`IncubationBaseline`):
       - Estado `OBSERVING` durante los primeros 14 días.
       - Aborto inmediato si el Drawdown supera $1.2 \times \text{Max DD}_{\text{backtest}}$.
       - Tras 14 días: verificación de degradación de Sharpe ($\le 30\%$) y suficiencia de trades.
       - Transición automatizada en la FSM de `CandidateRegistry`: `INCUBATION_PAPER` $\to$ `LIVE_ACTIVE` (si aprueba) o $\to$ `REJECTED` (si degrada).
  3. **Verificación de Tests:**
     - Creado `tests/test_paper_sandbox.py`.
     - Validada la simulación de ejecución, cálculo de slippage, reglas de aborto por drawdown y promoción a `LIVE_ACTIVE`.
     - Ejecución de `pytest tests/ -v` arrojando **39 tests PASSED, 1 SKIPPED, 0 FAILED**.

---

### [ ] FASE 3: Interfaz de Usuario y Telemetría en Tiempo Real
- Control Center con paginación optimizada (`25 | 50 | 100` por página).
- Selector de rutas desacoplado (`ULTRA` vs `FONDEO`).
- Vista detallada de ADN con curvas de capital IS/OOS reales.
