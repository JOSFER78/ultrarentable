# EXECUTION BOUNDARY TRACE ? ORDEN AG2-P02-007
**Fase 02 ? Canonical Bidirectional Semantics & Real Execution Boundary Proof**
**Fecha:** 2026-08-25T21:00:00Z
**Estado:** AUDITED & VERIFIED

---

## 1. Cadena de Producci?n Can?nica End-to-End

El recorrido de ejecuci?n determinista atraviesa una secuencia unidireccional de 10 etapas estrictamente auditadas:

$$\mathbf{CanonicalStrategy} \longrightarrow \mathbf{StrategySnapshot} \longrightarrow \mathbf{compile\_to\_runtime} \longrightarrow \mathbf{CanonicalRuntimeAdapter} \longrightarrow \mathbf{EventBacktestEngine} \longrightarrow \mathbf{CrossEngineReconciler} \longrightarrow \mathbf{BlindTestValidator} \longrightarrow \mathbf{CertificationRegistry} \longrightarrow \mathbf{GatePipelineOrchestrator} \longrightarrow \mathbf{BacktestLedger / RuntimeExecutionResult}$$

```
+----------------------------------------------------------------------------------------------------+
| 1. CANONICAL STRATEGY (contracts/canonical_strategy.py)                                           |
|    - AST Declarativo Inmutable: RuleTree, ConditionNode, IndicatorSpec, ComparisonOp               |
|    - ExitModel: StopLossType, TakeProfitType, trail_after_r, time_stop_bars                        |
|    - SizingAndRisk: SizingType, risk_value, max_open_positions == 1 (SUPPORTED)                     |
|    - SessionWindow: start_time_utc, end_time_utc, allowed_days, close_at_eod                       |
|    - SHA-256 Semantic Hash: compute_strategy_hash(get_semantic_payload())                          |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 2. STRATEGY SNAPSHOT (contracts/snapshots/strategy_snapshot.py)                                   |
|    - StrategySnapshot.create_and_hash(): Congela par?metros inmutables y reglas                    |
|    - Serializaci?n can?nica JSON: sort_keys=True, separators=(',', ':')                            |
|    - dataset_id_reference & dataset_sha256_reference binding criptogr?fico                         |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 3. COMPILE TO RUNTIME (contracts/canonical_strategy.py L306-354)                                   |
|    - CanonicalStrategy.compile_to_runtime()                                                        |
|    - verify_integrity() -> StrategyIntegrityError si hash != semantic AST                          |
|    - Genera ExecutableRuntimeInstruction inmutable (pydantic frozen, extra="forbid")                |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 4. CANONICAL RUNTIME ADAPTER (services/execution/canonical_runtime_adapter.py)                     |
|    - CanonicalRuntimeAdapter(engine_version, policy_version)                                       |
|    - DatasetRegistry.resolve_dataset(symbol, timeframe) -> Carga f?sica con verify_sha256=True     |
|    - CANONICAL_COST_REGISTRY: point_value, tick_size, contract_multiplier, taker_fee               |
|    - Sem?ntica Bidireccional BOTH expl?cita (compiled_long_conditions, compiled_short_conditions)  |
|    - Evaluaci?n determinista de indicadores (_eval_indicator) y disparadores (evaluate_entry_trigger)|
|    - Filtro de sesi?n UTC y d?as permitidos (_is_within_session)                                   |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 5. EVENT BACKTEST ENGINE (services/validation/engine/event_backtest_engine.py)                      |
|    - Simulaci?n barra a barra sin Lookahead Bias (OrderEvent -> FillEvent -> TradeRecord)          |
|    - Intrabar Exit Priority: LIQUIDATION -> STOP_LOSS -> TAKE_PROFIT (Zero-Optimism)               |
|    - Deducci?n de fricci?n: taker_fee_pct, slippage_bps, funding_fee_usd                           |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 6. CROSS ENGINE RECONCILER (services/validation/legacy_revalidation_service.py L297-346)           |
|    - Reconciliaci?n cruzada trade-a-trade de m?tricas (PnL, Drawdown, PF, R-Multiple)              |
|    - Gate 11 Independent Event Cross-Validation (services/api/app/validation/gates/gate_11_*)     |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 7. BLIND TEST VALIDATOR (services/validation/legacy_revalidation_service.py L251-260)             |
|    - Particionado F?sico Cronol?gico: 60% In-Sample (IS), 20% Validaci?n (Val), 20% Blind OOS      |
|    - Aislamiento estricto: WFO evaluado sobre Pre-OOS (IS + Val), 0% fuga en Blind Holdout OOS    |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 8. CERTIFICATION REGISTRY (services/validation/certification_registry.py)                          |
|    - certify_candidate(): Validaci?n estricta 11/11 Gates obligatorios                            |
|    - Umbrales de calidad: Max Drawdown (4.5% FONDEO / 85% ULTRA), Min PF (1.15 / 1.05), Min Trades|
|    - register_certification(): Firma SHA-256 y persistencia en evidence_bundle.json               |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 9. GATE PIPELINE ORCHESTRATOR (services/api/app/validation/gates/gate_pipeline_orchestrator.py)   |
|    - Ejecuci?n modular y aislada de Gates 01 a 11 (Data Ingest -> Event Cross-Validation)         |
|    - Persistencia de EvidenceRecord por Gate con input_hash y output_hash SHA-256 en disco         |
+----------------------------------------------------------------------------------------------------+
                                                 ?
                                                 ?
+----------------------------------------------------------------------------------------------------+
| 10. BACKTEST LEDGER / RUNTIME EXECUTION RESULT (services/execution/canonical_runtime_adapter.py)  |
|     - EvaluatedTrade: entry/exit time ms, prices, reason, pnl_r, pnl_usd, size_contracts          |
|     - RuntimeExecutionResult: dataset_sha256, engine_version, policy_version, total_trades        |
|     - execution_hash determinista calculado sobre el 100% de los trades del ledger                 |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Mapeo Exhaustivo de Call-Sites, Clases, M?todos y N?meros de L?nea Exactos

### 2.1 `CanonicalStrategy`
- **Archivo:** `contracts/canonical_strategy.py`
- **Clase:** `CanonicalStrategy(BaseModel)` (L146?355)
- **M?todos Clave:**
  - `compute_strategy_hash(payload: Dict[str, Any]) -> str` (L230?235): Serializaci?n can?nica JSON (`sort_keys=True, separators=(',', ':')`) y hash SHA-256.
  - `get_semantic_payload(self) -> Dict[str, Any]` (L237?244): Extrae el 100% del ?rbol sint?ctico sin campos vol?tiles.
  - `create_and_hash(...) -> CanonicalStrategy` (L246?297): Constructor de f?brica inmutable.
  - `verify_integrity(self) -> bool` (L299?303): Comprueba si `self.strategy_hash == self.compute_strategy_hash(self.get_semantic_payload())`.
  - `compile_to_runtime(self) -> ExecutableRuntimeInstruction` (L306?354): Valida integridad y transforma el AST en la instrucci?n de runtime.

### 2.2 `StrategySnapshot`
- **Archivo:** `contracts/snapshots/strategy_snapshot.py`
- **Clase:** `StrategySnapshot(BaseModel)` (L51?151)
- **M?todos Clave:**
  - `create_and_hash(...) -> StrategySnapshot` (L75?127): Congela par?metros, fija `dataset_id_reference` y `dataset_sha256_reference`, y calcula `canonical_hash`.
  - `verify_integrity(self) -> bool` (L129?150): Detecta mutaciones en los par?metros congelados.

### 2.3 `compile_to_runtime`
- **Archivo:** `contracts/canonical_strategy.py` (L306?354) y `services/execution/canonical_runtime_adapter.py` (L77?83)
- **M?todo:** `CanonicalStrategy.compile_to_runtime(self) -> ExecutableRuntimeInstruction`
  - Invocado por `CanonicalRuntimeAdapter.compile_strategy(self, strategy: CanonicalStrategy)`.
  - Emite `ExecutableRuntimeInstruction` (L108?143) con tipos de SL/TP, dimensionamiento, sesi?n y reglas compiladas.

### 2.4 `CanonicalRuntimeAdapter`
- **Archivo:** `services/execution/canonical_runtime_adapter.py`
- **Clase:** `CanonicalRuntimeAdapter` (L68?693)
- **M?todos Clave:**
  - `__init__(self, engine_version: str, policy_version: str)` (L71?75): Exige versiones de gobierno no vac?as.
  - `_eval_indicator(self, spec: IndicatorSpec, bars, current_idx) -> float` (L85?158): C?lculo determinista de SMA, EMA, ATR y precios con cero fallbacks silenciosos.
  - `evaluate_entry_trigger(self, instruction, bars, current_idx) -> bool` (L235?243): Disparador evaluado seg?n ramas expl?citas y operador l?gico `AND` / `OR`.
  - `_is_within_session(self, timestamp_ms, session_config) -> bool` (L244?269): Validaci?n horaria UTC y d?as permitidos (`allowed_days`).
  - `execute_backtest(self, strategy, account_equity_usd, registry=None) -> RuntimeExecutionResult` (L270?539):
    - Validaci?n Fail-Closed de `account_equity_usd > 0` (L281?290).
    - Carga de microestructura desde `CANONICAL_COST_REGISTRY` (L295).
    - Validaci?n Fail-Closed de `max_open_positions == 1` (L298?304).
    - Carga y verificaci?n de hash del dataset v?a `DatasetRegistry` (L305?315).
    - Bucle principal de ejecuci?n con resoluci?n conservadora intrabarra (SL > TP) (L353?480).

### 2.5 `EventBacktestEngine`
- **Archivo:** `services/validation/engine/event_backtest_engine.py`
- **Clase:** `EventBacktestEngine` (L102?639)
- **M?todos Clave:**
  - `run_backtest(self, strategy: StrategySnapshot, candles, initial_capital_usd=1000.0, ...) -> EventBacktestResult` (L120?550): Ejecuci?n basada en eventos con comisiones taker, deslizamiento, margen din?mico y cascada de salida pesimista:
    $$\text{LIQUIDATION (L376--412)} \succ \text{STOP\_LOSS (L414--449)} \succ \text{TAKE\_PROFIT (L451--460)}$$
  - `to_canonical_ledger(self, symbol, execution_config_hash) -> CanonicalExecutionLedger` (L100).

### 2.6 `CrossEngineReconciler`
- **Archivos:** `services/validation/legacy_revalidation_service.py` (L297?346) y `services/api/app/validation/gates/gate_11_nautilus_event.py` (L14?148)
- **Mecanismo:** Reconciliaci?n cruzada de eventos orden a orden entre el motor Python determinista y los principios de ejecuci?n orientada a eventos de NautilusTrader, verificando apalancamiento m?ximo, distancia a liquidaci?n y costes de financiaci?n.

### 2.7 `BlindTestValidator`
- **Archivos:** `services/validation/legacy_revalidation_service.py` (L251?260) y `services/validation/forward_sufficiency.py` (L1?150)
- **Mecanismo:** Particionado cronol?gico estricto del dataset f?sico:
  - In-Sample (IS): Primer 60% de velas cronol?gicas.
  - Validaci?n (Val): Siguiente 20% de velas (60% al 80%).
  - Blind Holdout Out-Of-Sample (Blind OOS): ?ltimo 20% de velas (80% al 100%), completamente aislado del ajuste de par?metros.

### 2.8 `CertificationRegistry`
- **Archivo:** `services/validation/certification_registry.py`
- **Clase:** `CertificationRegistry` (L53?131)
- **M?todos Clave:**
  - `certify_candidate(self, strategy, backtest_result, gates_passed_count, scorecard_average) -> CertificationVerdict` (L58?109): Exige 11/11 Gates aprobados al 100%, Max Drawdown $\le 4.5\%$ (FONDEO) o $\le 85\%$ (ULTRA), Profit Factor $\ge 1.15$ (FONDEO) o $\ge 1.05$ (ULTRA), y muestra m?nima de trades.
  - `register_certification(self, strategy_id, engine_version, scorecard, signature_sha256, evidence_dir) -> Dict[str, Any]` (L110?131): Emisi?n y persistencia de evidencia con firma criptogr?fica.

### 2.9 `GatePipelineOrchestrator`
- **Archivo:** `services/api/app/validation/gates/gate_pipeline_orchestrator.py`
- **Clase:** `GatePipelineOrchestrator` (L47?266)
- **M?todos Clave:**
  - `__init__(self, evidence_base_dir=None)` (L48?63): Carga modular de los 11 gates cuantitativos.
  - `run_all_gates(self, candidate_info, candles, is_trades, oos_trades, pre_oos_trades, trades_raw, strategy_snapshot) -> Dict[str, Any]` (L64?266): Ejecuta cada gate en aislamiento, deriva `input_hash` y `output_hash` SHA-256 y persiste cada `EvidenceRecord` individual en `data/evidence/<strategy_id>/`.

### 2.10 `BacktestLedger / RuntimeExecutionResult`
- **Archivo:** `services/execution/canonical_runtime_adapter.py` (L39?66)
- **Clases:**
  - `EvaluatedTrade` (L39?52): Registro inmutable de cada operaci?n (`entry_time_ms`, `exit_time_ms`, `entry_price`, `exit_price`, `exit_reason`, `pnl_r`, `pnl_usd`, `size_contracts`).
  - `RuntimeExecutionResult` (L54?66): Contenedor inmutable que vincula la identidad de estrategia, dataset f?sico, versiones de motor/pol?tica, lista de trades y el `execution_hash` SHA-256 determinista:
    $$\text{execution\_hash} = \text{SHA-256}(\text{JSON}(\text{strategy\_id}, \text{strategy\_hash}, \text{dataset\_sha256}, \text{engine\_ver}, \text{policy\_ver}, [\text{trades}]))$$

---

## 3. Demostraci?n Matem?tica de la Microestructura y Resoluci?n Pesimista Intrabarra

### 3.1 Dimensionamiento por Riesgo Instrument-Aware
El c?lculo exacto de contratos en `CanonicalRuntimeAdapter` implementa:
$$\text{size\_contracts} = \frac{\text{account\_equity\_usd} \times (\text{risk\_pct} / 100.0)}{\Delta_{SL} \times \text{point\_value} \times \text{contract\_multiplier}}$$
Para CME NQ (`point_value = 20.0`, `contract_multiplier = 1.0`), un riesgo de \$1,000 con un SL de 10 puntos resulta exactamente en:
$$\text{size} = \frac{1000}{10 \times 20.0 \times 1.0} = 5.0\ \text{contratos}$$

### 3.2 Prioridad Pesimista Intrabarra (Zero-Optimism)
Ante una vela donde tanto el nivel de Stop Loss como el de Take Profit caen dentro del rango $[Low, High]$:
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
Al evaluarse `hit_sl` en primera instancia, si ambos ocurren (`hit_sl=True` y `hit_tp=True`), el motor ejecuta obligatoriamente el Stop Loss, erradicando cualquier sesgo optimista en la curva de equidad.

