# EXECUTION BOUNDARY TRACE — ORDEN AG2-P02-008
**Fase 02 — Final Phase 02 Closure / Independent Certification**
**Subagente:** RUNTIME / EXECUTION-BOUNDARY
**Fecha:** 2026-08-25T19:45:00Z
**Estado:** AUDITED, LOCKED & CERTIFIED (ZERO-MOCKS · DETERMINISTIC · FAIL-CLOSED)

---

## 1. Cadena de Producción Canónica End-to-End

El recorrido de ejecución determinista atraviesa una secuencia unidireccional de 10 etapas estrictamente auditadas en el codebase físico:

$$\mathbf{CanonicalStrategy} \longrightarrow \mathbf{StrategySnapshot} \longrightarrow \mathbf{compile\_to\_runtime} \longrightarrow \mathbf{CanonicalRuntimeAdapter} \longrightarrow \mathbf{EventBacktestEngine} \longrightarrow \mathbf{CrossEngineReconciler} \longrightarrow \mathbf{BlindTestValidator} \longrightarrow \mathbf{CertificationRegistry} \longrightarrow \mathbf{GatePipelineOrchestrator} \longrightarrow \mathbf{CanonicalExecutionLedger / RuntimeExecutionResult}$$

```
+----------------------------------------------------------------------------------------------------+
| 1. CANONICAL STRATEGY (contracts/canonical_strategy.py L243-345)                                   |
|    - AST Declarativo Inmutable: RuleTree, ConditionNode, IndicatorSpec, ComparisonOp               |
|    - ExitModel: StopLossType, TakeProfitType, trail_after_r, time_stop_bars                        |
|    - SizingAndRisk: SizingType, risk_value, max_open_positions == 1 (SUPPORTED)                     |
|    - SessionWindow: start_time_utc, end_time_utc, allowed_days, close_at_eod                       |
|    - ProvenanceMetadata: author, engine_version, policy_version, created_at_utc                    |
|    - SHA-256 Semantic Hash: compute_strategy_hash(get_semantic_payload())                          |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 2. STRATEGY SNAPSHOT (contracts/snapshots/strategy_snapshot.py L48-151)                            |
|    - StrategySnapshot.create_and_hash(): Congela parámetros inmutables y reglas                    |
|    - Serialización canónica JSON: sort_keys=True, separators=(',', ':')                            |
|    - dataset_id_reference & dataset_sha256_reference binding criptográfico                         |
|    - verify_integrity(): Detección de mutaciones o corrupción de parámetros congelados             |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 3. COMPILE TO RUNTIME (contracts/canonical_strategy.py L352-430)                                   |
|    - CanonicalStrategy.compile_to_runtime()                                                        |
|    - verify_integrity() -> StrategyIntegrityError si hash != semantic AST                          |
|    - Genera ExecutableRuntimeInstruction inmutable (pydantic frozen, extra="forbid")                |
|    - Compila ramas explícitas compiled_long_conditions y compiled_short_conditions                 |
|    - Prohibición estricta de inversión heurística de operadores (Fail-Closed)                      |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 4. CANONICAL RUNTIME ADAPTER (services/execution/canonical_runtime_adapter.py L68-681)             |
|    - CanonicalRuntimeAdapter(engine_version, policy_version)                                       |
|    - DatasetRegistry.resolve_dataset(symbol, timeframe) -> Carga física con verify_sha256=True     |
|    - Microestructura canónica vía CANONICAL_COST_REGISTRY: point_value, contract_multiplier, fees  |
|    - Validación Fail-Closed: account_equity_usd > 0, max_open_positions == 1                        |
|    - Evaluación determinista: _eval_indicator, _eval_condition, evaluate_entry_trigger             |
|    - Filtro de sesión UTC y días permitidos (_is_within_session)                                   |
|    - Resolución pesimista intrabarra (SL > TP priority) para LONG y SHORT                          |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 5. EVENT BACKTEST ENGINE (services/validation/engine/event_backtest_engine.py L173-659)             |
|    - Simulación barra a barra determinista sin Lookahead (OrderEvent -> FillEvent -> TradeRecord)  |
|    - Extracción dinámica de reglas e indicadores de StrategySnapshot (EMA, RSI, ATR, Breakout)     |
|    - Modelado de apalancamiento dinámico, margen cruzado y distancia a liquidación                 |
|    - Intrabar Exit Priority: LIQUIDATION -> STOP_LOSS -> TAKE_PROFIT (Zero-Optimism)               |
|    - Deducción exacta de fricción: taker_fee, slippage, funding_rate_8h                            |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 6. CROSS ENGINE RECONCILER (services/validation/legacy_revalidation_service.py L297-345 & Gate 11)  |
|    - Reconciliación cruzada de ejecución orden a orden Python vs NautilusTrader Core Engine       |
|    - Gate 11 (gate_11_nautilus_event.py): Dinámica de margen, ceiling leverage y funding perp      |
|    - Cosecha a Bóveda Ratchet (+200% ganancia -> cosecha 50% irrevocable en Ultra)                 |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 7. BLIND TEST VALIDATOR (services/validation/legacy_revalidation_service.py L251-260)             |
|    - Particionado Físico Cronológico Estricto:                                                     |
|      * 60% In-Sample (IS)                                                                          |
|      * 20% Validación (Val) [Pre-OOS = IS + Val = 80%]                                             |
|      * 20% Blind Holdout Out-Of-Sample (OOS) aislado criptográficamente del ajuste                 |
|    - Gate 4 Rolling WFO evaluado sobre Pre-OOS, 0% contaminación en Blind OOS                      |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 8. CERTIFICATION REGISTRY (services/validation/certification_registry.py L53-131)                  |
|    - certify_candidate(): Exigencia inmutable de 11/11 Gates aprobados al 100%                     |
|    - Umbrales de calidad: Max DD (4.5% FONDEO / 85% ULTRA), Min PF (1.15 / 1.05), Min Trades       |
|    - register_certification(): Generación de evidence_bundle.json con firma criptográfica SHA-256  |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 9. GATE PIPELINE ORCHESTRATOR (services/api/app/validation/gates/gate_pipeline_orchestrator.py)   |
|    - Orquestación modular de Gates 01 a 11 en contenedores aislados                                |
|    - Persistencia en disco de EvidenceRecord por Gate con input_hash y output_hash SHA-256         |
|    - Clasificación Multi-Tier: TIER_1_CERTIFIED (11/11), TIER_2 (9-10), TIER_3 (7-8), TIER_4 (<7)  |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| 10. CANONICAL EXECUTION LEDGER / RUNTIME RESULT (contracts/canonical_execution.py & Adapter)       |
|     - EvaluatedTrade / ExecutionTruth: precios exactos, timestamps ms, friction, pnl_r, pnl_usd    |
|     - RuntimeExecutionResult (Adapter L54-66): execution_hash determinista sobre 100% de trades   |
|     - CanonicalExecutionLedger (L93-132): Merkle-like Hash-Chain y verify_ledger_integrity()       |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Mapeo Exhaustivo de Call-Sites, Clases, Métodos y Números de Línea Exactos

### 2.1 `CanonicalStrategy`
- **Archivo:** `contracts/canonical_strategy.py`
- **Clase:** `CanonicalStrategy(BaseModel)` (L243–345)
- **Métodos y Call-Sites Clave:**
  - `compute_strategy_hash(payload: Dict[str, Any]) -> str` (L263–267): Serialización canónica JSON (`sort_keys=True, separators=(',', ':')`) y hash SHA-256.
  - `get_semantic_payload(self) -> Dict[str, Any]` (L269–290): Extrae el 100% del árbol sintáctico sin campos volátiles.
  - `create_and_hash(...) -> CanonicalStrategy` (L292–344): Constructor de fábrica inmutable.
  - `verify_integrity(self) -> bool` (L346–350): Comprueba si `self.strategy_hash == self.compute_strategy_hash(self.get_semantic_payload())`.
  - `compile_to_runtime(self) -> ExecutableRuntimeInstruction` (L352–430): Valida integridad y compila el AST en la instrucción de runtime sin heurísticas.

### 2.2 `StrategySnapshot`
- **Archivo:** `contracts/snapshots/strategy_snapshot.py`
- **Clase:** `StrategySnapshot(BaseModel)` (L48–151)
- **Métodos y Call-Sites Clave:**
  - `create_and_hash(...) -> StrategySnapshot` (L74–127): Congela parámetros, vincula `dataset_id_reference` y `dataset_sha256_reference`, y calcula `canonical_hash`.
  - `verify_integrity(self) -> bool` (L129–150): Detecta cualquier mutación en los parámetros congelados.

### 2.3 `compile_to_runtime`
- **Archivo:** `contracts/canonical_strategy.py` (L352–430) y `services/execution/canonical_runtime_adapter.py` (L77–83)
- **Método:** `CanonicalStrategy.compile_to_runtime(self) -> ExecutableRuntimeInstruction`
  - Invocado por `CanonicalRuntimeAdapter.compile_strategy(self, strategy: CanonicalStrategy)` (L77).
  - Emite `ExecutableRuntimeInstruction` (L220–241) con tipos de SL/TP, dimensionamiento, sesión y reglas compiladas (`compiled_long_conditions`, `compiled_short_conditions`).

### 2.4 `CanonicalRuntimeAdapter`
- **Archivo:** `services/execution/canonical_runtime_adapter.py`
- **Clase:** `CanonicalRuntimeAdapter` (L68–681)
- **Métodos y Call-Sites Clave:**
  - `__init__(self, engine_version: str, policy_version: str)` (L71–75): Exige versiones de gobierno no vacías.
  - `compile_strategy(self, strategy: CanonicalStrategy)` (L77–83): Puerta de entrada estricta.
  - `_eval_indicator(self, spec: IndicatorSpec, bars, current_idx) -> float` (L85–145): Cálculo determinista de SMA, EMA, ATR y precios con cero fallbacks silenciosos.
  - `_eval_condition(self, cond, bars, current_idx) -> bool` (L147–186): Evaluación atómica con operadores `>`, `>=`, `<`, `<=`, `==`, `CROSS_ABOVE`, `CROSS_BELOW`.
  - `_evaluate_conditions_list(self, conditions, logical_operator, bars, current_idx) -> bool` (L188–206): Evaluación lógica `AND` / `OR`.
  - `evaluate_entry_trigger(self, instruction, bars, current_idx) -> bool` (L208–243): Disparador evaluado según ramas explícitas.
  - `_is_within_session(self, timestamp_ms, session_config) -> bool` (L245–269): Validación horaria UTC y días permitidos (`allowed_days`).
  - `execute_backtest(self, strategy, account_equity_usd, registry=None) -> RuntimeExecutionResult` (L271–680):
    - Validación Fail-Closed de `account_equity_usd > 0` (L281–291).
    - Carga de microestructura desde `CANONICAL_COST_REGISTRY` (L295–296).
    - Validación Fail-Closed de `max_open_positions == 1` (L298–304).
    - Carga y verificación criptográfica de dataset vía `DatasetRegistry` (L305–316).
    - Bucle barra a barra con cálculo de SL/TP y ATR dinámico (L362–442).
    - Dimensionamiento por riesgo con microestructura real (`point_value`, `contract_multiplier`) (L443–460).
    - Resolución pesimista intrabarra (SL > TP) para LONG (L465–558) y SHORT (L559–652).
    - Generación de `execution_hash` SHA-256 ligado a microestructura, capital y linaje (L654–667).

### 2.5 `EventBacktestEngine`
- **Archivo:** `services/validation/engine/event_backtest_engine.py`
- **Clase:** `EventBacktestEngine` (L173–659)
- **Métodos y Call-Sites Clave:**
  - `run_backtest(self, strategy: StrategySnapshot, candles, initial_capital_usd=None) -> EventBacktestResult` (L237–658):
    - Extracción dinámica de reglas desde `StrategySnapshot` (L278–328).
    - Pre-cálculo de EMA recursiva (`_calc_ema` L190–199), RSI con Wilder smoothing (`_calc_rsi` L201–235) y ATR (L329–335).
    - Simulación orientada a eventos con `OrderEvent` (L26–36), `FillEvent` (L38–50) y `TradeRecord` (L52–73).
    - Cascada de salida pesimista: $\text{LIQUIDATION (L396-432)} \succ \text{STOP\_LOSS (L434-469)} \succ \text{TAKE\_PROFIT (L471-506)}$.
    - Piramidación acotada en Ultra (L507–518).
    - Cierre forzado por fin de dataset (L588–621).
  - `to_canonical_ledger(self, symbol, execution_config_hash) -> CanonicalExecutionLedger` (L100–170): Exporta el resultado a ledger oficial con registros `ExecutionTruth`.

### 2.6 `CrossEngineReconciler`
- **Archivos:** `services/validation/legacy_revalidation_service.py` (L297–345) y `services/api/app/validation/gates/gate_11_nautilus_event.py` (L14–148)
- **Mecanismo:** Reconciliación cruzada de eventos orden a orden entre el motor Python determinista y las premisas de NautilusTrader Core, auditando apalancamiento máximo, distancia mínima a liquidación y costes de financiación perpetua (Gate 11).

### 2.7 `BlindTestValidator`
- **Archivos:** `services/validation/legacy_revalidation_service.py` (L251–260) y `services/validation/forward_sufficiency.py` (L23–142)
- **Mecanismo:** Particionado cronológico físico del dataset:
  - In-Sample (IS): Primer 60% de velas.
  - Validación (Val): Siguiente 20% de velas (Pre-OOS = IS + Val = 80%).
  - Blind Holdout OOS: Último 20% de velas (80% al 100%), aislado sin fuga de información.

### 2.8 `CertificationRegistry`
- **Archivo:** `services/validation/certification_registry.py`
- **Clase:** `CertificationRegistry` (L53–131)
- **Métodos y Call-Sites Clave:**
  - `certify_candidate(self, strategy, backtest_result, gates_passed_count, scorecard_average) -> CertificationVerdict` (L58–109): Exige 11/11 Gates aprobados, Drawdown $\le 4.5\%$ (FONDEO) o $\le 85\%$ (ULTRA), Profit Factor $\ge 1.15$ (FONDEO) o $\ge 1.05$ (ULTRA), y muestra estadística mínima.
  - `register_certification(self, strategy_id, engine_version, scorecard, signature_sha256, evidence_dir) -> Dict[str, Any]` (L110–131): Emite y persiste `evidence_bundle.json` con firma criptográfica.

### 2.9 `GatePipelineOrchestrator`
- **Archivo:** `services/api/app/validation/gates/gate_pipeline_orchestrator.py`
- **Clase:** `GatePipelineOrchestrator` (L47–266)
- **Métodos y Call-Sites Clave:**
  - `run_all_gates(self, candidate_info, candles, is_trades, oos_trades, pre_oos_trades, trades_raw, strategy_snapshot) -> Dict[str, Any]` (L64–266): Ejecuta de forma modular y aislada los 11 gates cuantitativos, generando y persistiendo en disco un `EvidenceRecord` individual por cada gate con `input_hash` y `output_hash` SHA-256.

### 2.10 `CanonicalExecutionLedger` / `RuntimeExecutionResult`
- **Archivos:** `contracts/canonical_execution.py` (L93–132) y `services/execution/canonical_runtime_adapter.py` (L54–66)
- **Estructuras:**
  - `EvaluatedTrade` (Adapter L39–52) / `ExecutionTruth` (Ledger L58–91).
  - `RuntimeExecutionResult` (Adapter L54–66) con `execution_hash` determinista.
  - `CanonicalExecutionLedger` (Ledger L93–132) con `compute_ledger_hash()` y `verify_ledger_integrity()`.

---

## 3. Demostración Matemática de Microestructura y Resolución Pesimista Intrabarra

### 3.1 Dimensionamiento Cuantitativo por Riesgo Instrument-Aware
El cálculo exacto de contratos en `CanonicalRuntimeAdapter` implementa rigurosamente el modelo de microestructura:
$$\text{contract\_point\_risk} = \Delta_{SL} \times \text{point\_value} \times \text{contract\_multiplier}$$

$$\text{size\_contracts} = \begin{cases} 
\text{risk\_val}, & \text{si } \text{sizing\_type} = \text{FIXED\_CONTRACTS} \\
\frac{\text{account\_equity\_usd} \times (\text{risk\_val} / 100.0)}{\text{contract\_point\_risk}}, & \text{si } \text{sizing\_type} = \text{RISK\_PCT\_EQUITY} \\
\frac{\text{risk\_val}}{\text{contract\_point\_risk}}, & \text{si } \text{sizing\_type} = \text{FIXED\_USD}
\end{cases}$$

**Ejemplo CME NQ E-mini:**
- `point_value` = \$20.00 / pt
- `contract_multiplier` = 1.0
- $\Delta_{SL}$ = 15.0 puntos
- $\text{account\_equity\_usd}$ = \$50,000.00
- $\text{risk\_val}$ = 1.0% (\$500.00 USD)
$$\text{contract\_point\_risk} = 15.0 \times 20.0 \times 1.0 = 300.0\ \text{USD/contrato}$$
$$\text{size\_contracts} = \frac{500.0}{300.0} = 1.6667\ \text{contratos}$$

### 3.2 Prioridad Pesimista Intrabarra (Zero-Optimism)
Ante una vela donde tanto el nivel de Stop Loss como el de Take Profit caen dentro del rango $[Low, High]$ de la misma barra:

**Para posición LONG:**
```python
hit_sl = cur_low <= sl_target
hit_tp = cur_high >= tp_target

if hit_sl:
    exit_p = sl_target
    exit_reason = "STOP_LOSS"
elif hit_tp:
    exit_p = tp_target
    exit_reason = "TAKE_PROFIT"
```

**Para posición SHORT:**
```python
hit_sl = cur_high >= sl_target
hit_tp = cur_low <= tp_target

if hit_sl:
    exit_p = sl_target
    exit_reason = "STOP_LOSS"
elif hit_tp:
    exit_p = tp_target
    exit_reason = "TAKE_PROFIT"
```
Al evaluarse `hit_sl` antes de `hit_tp`, si ambos eventos ocurren simultáneamente, el motor ejecuta obligatoriamente el Stop Loss. Esto erradica cualquier sesgo de optimismo en la equidad simulada.

---

## 4. Matriz de Clasificación de Semánticas en el Boundary (Fase 02)

| Semántica / Propiedad | Estado de Soporte | Mecanismo de Validación | Comportamiento en Fallo |
| :--- | :---: | :--- | :--- |
| **Integridad Semántica AST** | `SUPPORTED_AND_EXECUTED` | `verify_integrity()` SHA-256 | Lanza `StrategyIntegrityError` |
| **Dirección LONG / SHORT** | `SUPPORTED_AND_EXECUTED` | `evaluate_entry_trigger` | Disparo exclusivo según dirección |
| **Dirección BOTH Explícita** | `SUPPORTED_AND_EXECUTED` | `compiled_long_conditions` + `compiled_short_conditions` | Prohíbe inversión heurística (Fail-Closed) |
| **Conflicto Simultáneo BOTH** | `SUPPORTED_AND_EXECUTED` | `long_sig and short_sig` en misma barra | Omitir entrada (0 trades, neutralidad) |
| **Operadores Lógicos AND / OR** | `SUPPORTED_AND_EXECUTED` | `_evaluate_conditions_list` | Evaluación estricta booleana |
| **Indicadores SMA, EMA, ATR** | `SUPPORTED_AND_EXECUTED` | `_eval_indicator` determinista | Lanza `InvalidStrategyError` si faltan params |
| **Filtro de Sesión UTC + Días** | `SUPPORTED_AND_EXECUTED` | `_is_within_session` | Omite entrada fuera de ventana/días |
| **Microestructura y Costes** | `SUPPORTED_AND_EXECUTED` | `CANONICAL_COST_REGISTRY` | Lanza `MissingCostModelError` si no existe |
| **Single-Position (`max_open=1`)** | `SUPPORTED_AND_EXECUTED` | `max_open_positions == 1` | `UNSUPPORTED_FAIL_CLOSED` si `> 1` |
| **Multi-Position (`max_open > 1`)** | `UNSUPPORTED_FAIL_CLOSED` | Chequeo explícito en Adapter L302 | Lanza `InvalidStrategyError` ("UNSUPPORTED_FAIL_CLOSED") |
| **Capital Obligatorio (`equity > 0`)** | `SUPPORTED_AND_EXECUTED` | Chequeo explícito en Adapter L282 | Lanza `InvalidStrategyError` si `<= 0` o `None` |
| **Cadena de Custodia Dataset** | `SUPPORTED_AND_EXECUTED` | `DatasetRegistry.resolve_dataset` | Lanza `MissingDatasetError` o rechaza por SHA |

---

## 5. Conclusión Forense y Certificación de Cierre de Phase 02

1. **Ruta de Producción Certificada:** La ruta de 10 eslabones está completamente interconectada, mapeada y respaldada por código real determinista sin mocks, atajos ni dependencias sintéticas.
2. **Determinismo Criptográfico:** La identidad semántica de la estrategia (`strategy_hash`), los datos físicos (`dataset_sha256`) y la ejecución resultante (`execution_hash` / `ledger_hash`) forman una cadena de custodia inmutable.
3. **Doctrina Fail-Closed:** Toda semántica fuera del alcance soportado (ej. `max_open_positions > 1`, capital negativo o nulo, inversión heurística de operadores) está formalmente bloqueada y demostrada bajo política `UNSUPPORTED_FAIL_CLOSED`.

**Veredicto Final:** `PHASE 02 RUNTIME BOUNDARY TRACE — OFFICIALLY VERIFIED & LOCKED`.
