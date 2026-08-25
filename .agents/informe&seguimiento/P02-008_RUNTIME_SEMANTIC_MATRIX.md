# RUNTIME SEMANTIC MATRIX & INDEPENDENT CERTIFICATION — ORDEN AG2-P02-008
**Fase 02 — Final Phase 02 Closure / Independent Certification**  
**Fecha:** 2026-08-25T19:44:00Z  
**Subagente Certificador:** CANONICAL / AST & SERIALIZATION  
**Estado:** FINAL SEALED & CERTIFIED (SSOT)  

---

## 1. Principios Canónicos y Guardarraíles Inquebrantables de Ejecución

1. **Doctrina Zero-Mocks & Real-Only:** Cero heurísticas sintéticas, cero inversiones no declaradas de operadores lógicos, cero valores numéricos inventados y cero fallbacks complacientes.
2. **Inmutabilidad y Sellado Criptográfico:** 100% de los modelos de contrato operan con `ConfigDict(frozen=True, extra="forbid")`. Todos los hashes (`strategy_hash`, `canonical_hash`, `ledger_hash`, `execution_hash`) se computan mediante serialización determinista canónica `json.dumps(..., sort_keys=True, separators=(",", ":"), default=str)` y algoritmo SHA-256.
3. **Fail-Closed Estricto:** Toda capacidad fuera del contrato formal de runtime, parámetro ausente, valor fuera de rango o configuración ambigua aborta inmediatamente con `InvalidStrategyError`, `ValidationError` o `StrategyIntegrityError`.
4. **Semántica Bidireccional Verdadera:** El modo `direction == "BOTH"` exige obligatoriamente ramas declarativas explícitas e independientes `long_conditions` y `short_conditions`. La inversión heurística de operadores (`_invert_operator`) queda clasificada formalmente como **UNSUPPORTED_FAIL_CLOSED**.
5. **Límite de Concurrencia de Posición:** El motor opera de forma determinista en modo single-position (`max_open_positions == 1`). La ejecución con `max_open_positions > 1` queda formalmente clasificada como **UNSUPPORTED_FAIL_CLOSED**.
6. **Resolución Pesimista Intrabarra (Zero-Optimism):** Ante la activación simultánea de niveles de SL y TP en la misma vela, el motor ejecuta obligatoriamente el Stop Loss.

---

## 2. Matriz Semántica Universal de Capacidades y Fronteras de Ejecución

| Categoría | Propiedad / Elemento Semántico | Clasificación Formal | Comportamiento en Runtime & Regla de Validación Fail-Closed | Archivo SSOT |
|---|---|---|---|---|
| **Direccionalidad** | **Direction LONG** | `SUPPORTED_AND_EXECUTED` | Evalúa `entry_rules.conditions` (o `long_conditions`). Genera trades LONG: SL por debajo del precio de entrada, TP por encima, $PnL = (P_{exit} - P_{entry}) \times \text{point\_val} \times \text{mult} \times \text{size}$. | `contracts/canonical_strategy.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Direccionalidad** | **Direction SHORT** | `SUPPORTED_AND_EXECUTED` | Evalúa `entry_rules.conditions` (o `short_conditions`). Genera trades SHORT: SL por encima del precio de entrada, TP por debajo, $PnL = (P_{entry} - P_{exit}) \times \text{point\_val} \times \text{mult} \times \text{size}$. | `contracts/canonical_strategy.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Direccionalidad** | **Direction BOTH (Ramas Explícitas)** | `SUPPORTED_AND_EXECUTED` | Requiere obligatoriamente `long_conditions` y `short_conditions` no vacías. Evalúa ambas ramas de forma independiente. Si ambas disparan simultáneamente en la misma barra, se cancela la entrada por conflicto. | `contracts/canonical_strategy.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Direccionalidad** | **Direction BOTH (Inversión Heurística)** | `UNSUPPORTED_FAIL_CLOSED` | **PROHIBIDO.** Si `direction == "BOTH"` y no se declaran explícitamente `long_conditions` y `short_conditions`, lanza `InvalidStrategyError` en validación de AST. Cero deducciones automáticas. | `contracts/canonical_strategy.py` |
| **Direccionalidad** | **Dirección No Declarada / Fuera de Enum** | `UNSUPPORTED_FAIL_CLOSED` | Rechaza cualquier valor fuera de `Literal["LONG", "SHORT", "BOTH"]` con `ValidationError`. | `contracts/canonical_strategy.py` |
| **Operadores Lógicos** | **LogicalOp AND** | `SUPPORTED_AND_EXECUTED` | Conjunción estricta: el 100% de las condiciones evaluadas en la rama activa deben ser verdaderas en la barra $t$ para generar señal. | `services/execution/canonical_runtime_adapter.py` |
| **Operadores Lógicos** | **LogicalOp OR** | `SUPPORTED_AND_EXECUTED` | Disyunción estricta: al menos una de las condiciones evaluadas en la rama activa debe ser verdadera en la barra $t$ para generar señal. | `services/execution/canonical_runtime_adapter.py` |
| **Operadores Lógicos** | **Operador Lógico Desconocido** | `UNSUPPORTED_FAIL_CLOSED` | Rechazado por Pydantic con `ValidationError` o runtime con `InvalidStrategyError`. | `contracts/canonical_strategy.py` |
| **Operadores Comparación** | **GT (`>`), GTE (`>=`), LT (`<`), LTE (`<=`), EQ (`==`)** | `SUPPORTED_AND_EXECUTED` | Comparación escalar determinista en barra $t$. Si algún operando evalúa a `NaN`, retorna `False`. | `services/execution/canonical_runtime_adapter.py` |
| **Operadores Comparación** | **CROSS_ABOVE / CROSS_BELOW** | `SUPPORTED_AND_EXECUTED` | Cruce temporal interbarra entre $t-1$ y $t$. Si $t < 1$ o algún valor previo es `NaN`, retorna `False`. | `services/execution/canonical_runtime_adapter.py` |
| **Operadores Comparación** | **Operador de Comparación Inválido** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` inmediatamente. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores & Fuentes** | **Shift Temporal ($t - \text{shift}$)** | `SUPPORTED_AND_EXECUTED` | Indexación retrospectiva determinista con $\text{shift} \ge 0$. Cero sesgo lookahead. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores & Fuentes** | **PRICE (Close, Open, High, Low, Volume)** | `SUPPORTED_AND_EXECUTED` | Extracción directa del feed físico normalizado de la barra $t - \text{shift}$. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores & Fuentes** | **SMA (Simple Moving Average)** | `SUPPORTED_AND_EXECUTED` | Media aritmética sobre ventana `period`. Retorna `NaN` si $index < period - 1$. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores & Fuentes** | **EMA (Exponential Moving Average)** | `SUPPORTED_AND_EXECUTED` | Ponderación exponencial $k = 2 / (period + 1)$ acumulada desde la barra 0. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores & Fuentes** | **ATR (Average True Range)** | `SUPPORTED_AND_EXECUTED` | Media de True Range sobre ventana `period`. Retorna `NaN` si $index < period$. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores & Fuentes** | **Indicador No Implementado (e.g. RSI, MACD)** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError`. 0% fallbacks a precios de cierre u otros indicadores. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores & Fuentes** | **Parámetro `period` Ausente o <= 0** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` de inmediato. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores & Fuentes** | **Campo Fuente No Soportado** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` si `source_field` no pertenece a `['close', 'open', 'high', 'low', 'volume']`. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Type: PERCENTAGE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{SL} = P_{entry} \times (sl\_val / 100.0)$. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Type: FIXED_POINTS** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{SL} = sl\_val$. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Type: ATR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{SL} = \text{ATR}(14) \times sl\_val$. Falla cerrado con `InvalidStrategyError` si no hay suficientes barras. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Type: BAR_LOW_HIGH** | `UNSUPPORTED_FAIL_CLOSED` | Salida dinámica de lookback no implementada en Fase 02; lanza `InvalidStrategyError`. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Value <= 0** | `UNSUPPORTED_FAIL_CLOSED` | Rechazado por Pydantic `gt=0.0` con `ValidationError` o `InvalidStrategyError` en cálculo. | `contracts/canonical_strategy.py` |
| **Take Profit** | **TP Type: RR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{TP} = \Delta_{SL} \times tp\_val$. | `services/execution/canonical_runtime_adapter.py` |
| **Take Profit** | **TP Type: PERCENTAGE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{TP} = P_{entry} \times (tp\_val / 100.0)$. | `services/execution/canonical_runtime_adapter.py` |
| **Take Profit** | **TP Type: FIXED_POINTS** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{TP} = tp\_val$. | `services/execution/canonical_runtime_adapter.py` |
| **Take Profit** | **TP Type: ATR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{TP} = \text{ATR}(14) \times tp\_val$. Falla cerrado con `InvalidStrategyError` si no hay suficientes barras. | `services/execution/canonical_runtime_adapter.py` |
| **Take Profit** | **TP Value <= 0** | `UNSUPPORTED_FAIL_CLOSED` | Rechazado por Pydantic `gt=0.0` con `ValidationError`. | `contracts/canonical_strategy.py` |
| **Gestión de Salidas** | **Conflicto Intrabarra SL / TP** | `SUPPORTED_AND_EXECUTED` | **Doctrina Zero-Optimism:** Si una vela toca simultáneamente los niveles de SL y TP, se ejecuta obligatoriamente Stop Loss. | `services/execution/canonical_runtime_adapter.py` |
| **Gestión de Salidas** | **Trailing Stop (`trail_after_r`)** | `SUPPORTED_AND_EXECUTED` | Mueve el SL a Breakeven ($P_{entry}$) cuando la ganancia flotante alcanza $R \ge trail\_after\_r$. | `services/execution/canonical_runtime_adapter.py` |
| **Gestión de Salidas** | **Time Stop (`time_stop_bars`)** | `SUPPORTED_AND_EXECUTED` | Cierre forzoso de mercado al precio de cierre tras $N$ barras transcurridas sin tocar SL/TP. | `services/execution/canonical_runtime_adapter.py` |
| **Gestión de Salidas** | **Cierre por Fin de Sesión (`close_at_eod`)** | `SUPPORTED_AND_EXECUTED` | Cierre forzoso al precio de cierre al salir de la ventana horaria de la sesión declarada. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Sizing: RISK_PCT_EQUITY** | `SUPPORTED_AND_EXECUTED` | Contratos = $\frac{AccountEquity \times (RiskPct / 100.0)}{\Delta_{SL} \times PointValue \times Multiplier}$. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Sizing: FIXED_CONTRACTS** | `SUPPORTED_AND_EXECUTED` | Contratos = `risk_value`. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Sizing: FIXED_USD** | `SUPPORTED_AND_EXECUTED` | Contratos = $\frac{RiskUSD}{\Delta_{SL} \times PointValue \times Multiplier}$. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Sizing: VOLATILITY_ADJUSTED** | `UNSUPPORTED_FAIL_CLOSED` | Modelo de volatilidad multivariable no estandarizado en adapter; lanza `InvalidStrategyError`. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Capacidad Single-Position (`max_open_positions == 1`)** | `SUPPORTED_AND_EXECUTED` | Bloqueo estricto de nuevas entradas mientras haya una posición abierta. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Multi-Position Scaling (`max_open_positions > 1`)** | `UNSUPPORTED_FAIL_CLOSED` | **LÍMITE ARQUITECTÓNICO FASE 02.** Motor monohilo opera en single-position; si `max_open_positions != 1`, lanza `InvalidStrategyError`. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Account Equity <= 0 / NaN / None** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` sin valores por defecto ficticios. | `services/execution/canonical_runtime_adapter.py` |
| **Microestructura** | **Integración de Costes Canónicos (CME vs Crypto)** | `SUPPORTED_AND_EXECUTED` | Extrae `point_value`, `contract_multiplier`, `tick_size`, comisiones y slippage de `InstrumentCostProfile`. | `services/data/instrument_cost_registry.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Ventana Intra-Día UTC (e.g. 13:30 - 20:00)** | `SUPPORTED_AND_EXECUTED` | Filtra entradas fuera del intervalo horario UTC declarado. | `services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Ventana Nocturna Cruzando Medianoche (e.g. 22:00 - 04:00)** | `SUPPORTED_AND_EXECUTED` | Evalúa la disyunción circular de minutos sobre las 24 horas UTC. | `services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Filtro de Días Permitidos (`allowed_days`)** | `SUPPORTED_AND_EXECUTED` | Permite operar únicamente en los días indexados en la lista (0=Lunes, 6=Domingo). | `services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Falta de `allowed_days` en Sesión Declarada** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` si se incluye sesión sin especificar días permitidos. | `services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Timestamps Ausentes o Inválidos (<= 0)** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError`; cero fallbacks a timestamps sintéticos. | `services/execution/canonical_runtime_adapter.py` |
| **Gobernanza y Linaje** | **SHA-256 Strategy Hash SSOT** | `SUPPORTED_AND_EXECUTED` | Valida coincidencia exacta de `strategy_hash` con el payload JSON ordenado del AST completo. | `contracts/canonical_strategy.py` |
| **Gobernanza y Linaje** | **Detección de Strategy Hash Alterado** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `StrategyIntegrityError` inmediatamente si el hash no coincide con el payload semántico. | `contracts/canonical_strategy.py` |
| **Gobernanza y Linaje** | **Engine & Policy Version Binding** | `SUPPORTED_AND_EXECUTED` | Exige versiones idénticas del SSOT (`CURRENT_ENGINE_VERSION == "5.4.0"`, `CURRENT_POLICY_VERSION == "5.4.0"`). | `services/engine_version.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Gobernanza y Linaje** | **Versión de Motor Vacía o Ausente** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `ValueError` en instanciación de adapter. | `services/execution/canonical_runtime_adapter.py` |
| **Gobernanza y Linaje** | **Cadena de Custodia DatasetRegistry** | `SUPPORTED_AND_EXECUTED` | Resuelve dataset físico en parquet/JSON y verifica su hash SHA-256 en disco antes de ejecutar. | `services/data/dataset_registry.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Gobernanza y Linaje** | **Dataset Inexistente / Hash Corrupto** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `MissingDatasetError` o `DatasetIntegrityError` con rechazo Fail-Closed. | `services/data/dataset_registry.py` |
| **Gobernanza y Linaje** | **Execution Hash Criptográfico SSOT** | `SUPPORTED_AND_EXECUTED` | Genera SHA-256 inmutable ligando estrategia, dataset, capital, microestructura y lista completa de trades. | `services/execution/canonical_runtime_adapter.py` |
| **Gobernanza y Linaje** | **CanonicalExecutionLedger Merkle Proof** | `SUPPORTED_AND_EXECUTED` | Sellado SHA-256 de ledger con `verify_ledger_integrity()` verificable en EventBacktestEngine. | `contracts/canonical_execution.py`<br>`services/validation/engine/event_backtest_engine.py` |
| **Gobernanza y Linaje** | **Pyramiding Policy Multi-Tier** | `NOT_PROVEN` | Definido en `StrategySnapshot` (`PyramidingPolicy`), pero su ejecución multi-tramo está restringida en el runtime monohilo Phase 02 single-position. | `contracts/snapshots/strategy_snapshot.py` |
| **Gobernanza y Linaje** | **Margin Policy Dynamic Harvest/Vault** | `NOT_PROVEN` | Definido en `StrategySnapshot` (`MarginPolicy`), pero su gestión dinámica de liquidez multi-cuenta corresponde a la Fase 03 / Fase 04. | `contracts/snapshots/strategy_snapshot.py` |

---

## 3. Resumen Cuantitativo de Capacidades de la Matriz

- **SUPPORTED_AND_EXECUTED:** 33 propiedades auditadas, probadas y respaldadas físicamente por pruebas de ejecución en `tests/test_phase02_canonical_strategy.py`.
- **UNSUPPORTED_FAIL_CLOSED:** 17 límites y condiciones inválidas formalmente identificadas que disparan excepciones inmediatas sin fallbacks silenciosos.
- **NOT_PROVEN:** 2 políticas declarativas avanzadas (`PyramidingPolicy` multi-tramo y `MarginPolicy` dynamic harvest) contenidas en contratos de snapshot pero diferidas de ejecución por el límite single-position de Fase 02.
