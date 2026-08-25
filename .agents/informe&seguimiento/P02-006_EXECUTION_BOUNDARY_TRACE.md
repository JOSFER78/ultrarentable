# EXECUTION BOUNDARY TRACE ? ORDEN AG2-P02-006
**Fase 02 ? Behavioral Runtime Proof & Universal Execution Boundary**
**Fecha:** 2026-08-25T19:15:00Z
**Estado:** AUDITED & VERIFIED

---

## 1. Cadena Can?nica de Ejecuci?n End-to-End

El flujo determinista de ejecuci?n en Ultrarentable est? estructurado en una cadena estricta de 6 etapas sin acoplamientos circulares ni p?rdida de identidad:

$$\mathbf{CanonicalStrategy} \xrightarrow{\text{1. Snapshot/Serialization}} \mathbf{StrategySnapshot} \xrightarrow{\text{2. Compile}} \mathbf{ExecutableRuntimeInstruction} \xrightarrow{\text{3. Adapter}} \mathbf{CanonicalRuntimeAdapter} \xrightarrow{\text{4. Universal Engine}} \mathbf{EventBacktestEngine} \xrightarrow{\text{5. Ledger}} \mathbf{RuntimeExecutionResult}$$

```
+-----------------------------------------------------------------------------+
| 1. CANONICAL STRATEGY (contracts/canonical_strategy.py)                     |
|    - Declarative AST: RuleTree (ConditionNode, IndicatorSpec, LogicalOp)    |
|    - ExitModel: StopLossType, TakeProfitType, trail_after_r, time_stop_bars |
|    - SizingAndRisk: SizingType, risk_value, max_open_positions              |
|    - SessionWindow: start_time_utc, end_time_utc, allowed_days, close_at_eod|
|    - SHA-256 Semantic Hash: compute_strategy_hash()                         |
+-----------------------------------------------------------------------------+
                                       ?
                                       ?
+-----------------------------------------------------------------------------+
| 2. SNAPSHOT & SERIALIZATION (contracts/snapshots/strategy_snapshot.py)      |
|    - StrategySnapshot.create_and_hash(): Congela par?metros inmutables      |
|    - Canonical JSON serialization (sort_keys=True, separators=(',', ':'))   |
|    - dataset_id_reference & dataset_sha256_reference binding                |
+-----------------------------------------------------------------------------+
                                       ?
                                       ?
+-----------------------------------------------------------------------------+
| 3. COMPILATION LAYER (contracts/canonical_strategy.py L306-354)             |
|    - CanonicalStrategy.compile_to_runtime()                                 |
|    - verify_integrity() -> StrategyIntegrityError si hash != semantic AST   |
|    - Genera ExecutableRuntimeInstruction (dataclass/pydantic frozen)        |
+-----------------------------------------------------------------------------+
                                       ?
                                       ?
+-----------------------------------------------------------------------------+
| 4. CANONICAL RUNTIME ADAPTER (services/execution/canonical_runtime_adapter) |
|    - CanonicalRuntimeAdapter(engine_version, policy_version)                |
|    - DatasetRegistry.resolve_dataset(symbol, timeframe)                     |
|    - DatasetRegistry.load_dataset_bars(verify_sha256=True)                  |
|    - Indicator evaluation (_eval_indicator): Cero fallbacks complacientes   |
|    - Trigger evaluation (evaluate_entry_trigger): AND / OR estricto         |
|    - Session check (_is_within_session): D?as y horas UTC exactas           |
+-----------------------------------------------------------------------------+
                                       ?
                                       ?
+-----------------------------------------------------------------------------+
| 5. UNIVERSAL EVENT ENGINE (services/validation/engine/event_backtest_engine)|
|    - Bar-by-bar evaluation con No-Lookahead Bias                            |
|    - Intrabar Exit Priority: LIQUIDATION -> STOP_LOSS -> TAKE_PROFIT        |
|    - Deducci?n de Comisiones (taker_fee) y Deslizamiento (slippage)         |
+-----------------------------------------------------------------------------+
                                       ?
                                       ?
+-----------------------------------------------------------------------------+
| 6. EXECUTION LEDGER & RESULT (services/execution/canonical_runtime_adapter) |
|    - EvaluatedTrade: entry/exit time ms, prices, reason, pnl_r, pnl_usd     |
|    - RuntimeExecutionResult: dataset_sha256, engine_version, policy_version |
|    - SHA-256 execution_hash derivado de todos los trades del ledger         |
+-----------------------------------------------------------------------------+
```

---

## 2. Call-Sites Reales y Mapeo de Archivos

### 2.1 Definici?n Can?nica e Integridad
- **Archivo:** `contracts/canonical_strategy.py`
  - `CanonicalStrategy.create_and_hash()` (L246?297): Construye la estrategia y calcula su `strategy_hash` determinista sobre el diccionario sem?ntico ordenado.
  - `CanonicalStrategy.verify_integrity()` (L299?303): Comprueba si `self.strategy_hash == self.compute_strategy_hash(self.get_semantic_payload())`.
  - `CanonicalStrategy.compile_to_runtime()` (L306?354): Valida integridad y transforma el AST en `ExecutableRuntimeInstruction`.

### 2.2 Inmutabilidad y Congelaci?n de Snapshots
- **Archivo:** `contracts/snapshots/strategy_snapshot.py`
  - `StrategySnapshot.create_and_hash()` (L75?127): Congela la estrategia antes de someterla a validaci?n, fijando `canonical_hash` y las referencias al dataset f?sico (`dataset_id_reference`, `dataset_sha256_reference`).
  - `StrategySnapshot.verify_integrity()` (L129?150): Detecta cualquier mutaci?n no autorizada de par?metros.

### 2.3 Compilaci?n y Orquestaci?n de Runtime
- **Archivo:** `services/execution/canonical_runtime_adapter.py`
  - `CanonicalRuntimeAdapter.compile_strategy()` (L72?78): Punto de entrada oficial que invoca `strategy.verify_integrity()` antes de compilar.
  - `CanonicalRuntimeAdapter._eval_indicator()` (L80?140): Evaluaci?n determinista de `SMA`, `EMA`, `ATR` y precios. Lanza `InvalidStrategyError` ante par?metros ausentes o hist?rico insuficiente.
  - `CanonicalRuntimeAdapter.evaluate_entry_trigger()` (L183?196): Evaluaci?n de condiciones con operadores l?gicos `AND` y `OR`.
  - `CanonicalRuntimeAdapter.execute_backtest()` (L223?539): Motor universal de backtest vinculado a `DatasetRegistry`.

---

## 3. Trazabilidad de la Pol?tica de Fill / Intrabar y Prioridad de Salidas

### 3.1 Comparativa de Prioridades: Engine vs Adaptador

Se ha verificado la estricta alineaci?n sem?ntica entre el motor de eventos (`EventBacktestEngine`) y el adaptador can?nico (`CanonicalRuntimeAdapter`):

```
+---------------------------------------------------------------------------------+
| EventBacktestEngine (L375-450)             CanonicalRuntimeAdapter (L353-392)   |
+---------------------------------------------------------------------------------+
| 1. LIQUIDATION (L376-412)                   (En cuentas fondeadas/spot          |
|    if bar_low <= liq_price (LONG)            sin apalancamiento extremo el SL   |
|    -> exit_reason = "LIQUIDATION"            se sit?a siempre antes de liq)     |
|                                                                                 |
| 2. STOP LOSS (L413-449)                  1. STOP LOSS (L354-374 / L440-460)     |
|    elif bar_low <= stop_loss_price (LONG)   if hit_sl (cur_low <= sl_target)    |
|    -> exit_reason = "STOP_LOSS"              -> exit_reason = "STOP_LOSS"       |
|                                                                                 |
| 3. TAKE PROFIT (L450-460+)               2. TAKE PROFIT (L375-392 / L461-478)   |
|    elif bar_high >= take_profit_price (LONG)elif hit_tp (cur_high >= tp_target) |
|    -> exit_reason = "TAKE_PROFIT"            -> exit_reason = "TAKE_PROFIT"     |
+---------------------------------------------------------------------------------+
```

### 3.2 An?lisis Forense de C?digo: `event_backtest_engine.py` (L375?452)

En `services/validation/engine/event_backtest_engine.py`, la evaluaci?n intrabarra dentro del bucle de velas (`for i in range(n_bars):`) ejecuta la cascada de decisi?n en este orden exacto:

1. **Prioridad 1 ? Liquidaci?n Forzada (L376?412):**
   ```python
   # Comprobar liquidaci?n real (quiebra al 100%)
   if (position_side == "LONG" and bar_low <= liq_price) or (position_side == "SHORT" and bar_high >= liq_price):
       exit_price = liq_price
       gross_pnl = (exit_price - position_entry_price) * position_qty if position_side == "LONG" else (position_entry_price - exit_price) * position_qty
       comm = exit_price * position_qty * self.taker_fee
       slip = exit_price * position_qty * self.slippage
       net_pnl = gross_pnl - comm - slip
       current_equity = max(0.0, current_equity + net_pnl)
   ```

2. **Prioridad 2 ? Stop Loss (L414?449):**
   ```python
   # Comprobar Stop Loss
   elif (position_side == "LONG" and bar_low <= stop_loss_price) or (position_side == "SHORT" and bar_high >= stop_loss_price):
       exit_price = stop_loss_price
       gross_pnl = (exit_price - position_entry_price) * position_qty if position_side == "LONG" else (position_entry_price - exit_price) * position_qty
       comm = exit_price * position_qty * self.taker_fee
       slip = exit_price * position_qty * self.slippage
       net_pnl = gross_pnl - comm - slip
       current_equity += net_pnl
   ```

3. **Prioridad 3 ? Take Profit (L451?460+):**
   ```python
   # Comprobar Take Profit
   elif (position_side == "LONG" and bar_high >= take_profit_price) or (position_side == "SHORT" and bar_low <= take_profit_price):
       exit_price = take_profit_price
       gross_pnl = (exit_price - position_entry_price) * position_qty if position_side == "LONG" else (position_entry_price - exit_price) * position_qty
       comm = exit_price * position_qty * self.taker_fee
       slip = exit_price * position_qty * self.slippage
       net_pnl = gross_pnl - comm - slip
       current_equity += net_pnl
   ```

### 3.3 Demostraci?n de la Pol?tica de Conflicto Intrabarra (Zero-Optimism)

En `services/execution/canonical_runtime_adapter.py` (L353?374 para `LONG` y L439?460 para `SHORT`):
```python
hit_sl = cur_low <= sl_target
hit_tp = cur_high >= tp_target

if hit_sl:
    # Si ambos niveles (SL y TP) son tocados en la misma vela (hit_sl=True y hit_tp=True),
    # el motor eval?a 'hit_sl' en primera instancia y ejecuta STOP_LOSS.
    exit_p = sl_target
    pnl_usd = (exit_p - entry_price) * size_contracts
    pnl_r = (exit_p - entry_price) / sl_distance
    trades.append(EvaluatedTrade(
        ...,
        exit_reason="STOP_LOSS",
        pnl_r=pnl_r,
        pnl_usd=pnl_usd,
    ))
    in_pos = False
elif hit_tp:
    exit_p = tp_target
    # Se ejecuta ?nicamente si hit_sl fue False
```

**Conclusi?n Matem?tica:**
Ambos motores aplican rigurosamente el principio de no-optimismo: ante ambig?edad intrabarra o colisi?n de niveles en la misma vela, la prioridad es deterministamente:
$$\mathbf{Liquidation} \succ \mathbf{StopLoss} \succ \mathbf{TakeProfit}$$
lo que erradica cualquier sesgo de sobreestimaci?n del rendimiento en backtest.

---

## 4. Entrada y Salida del Ledger Determinista

### 4.1 Input Bundle de Ejecuci?n:
- `strategy_hash`: Hash SHA-256 inmutable de `CanonicalStrategy`.
- `dataset_sha256`: Hash SHA-256 de las velas f?sicas cargadas por `DatasetRegistry`.
- `engine_version`: Identidad de versi?n del motor (`5.4.0`).
- `policy_version`: Identidad de pol?tica de ejecuci?n (`5.4.0`).

### 4.2 Output Ledger (`RuntimeExecutionResult`):
- Lista inmutable de `EvaluatedTrade`:
  - `entry_bar_index`, `entry_time_ms`, `entry_price`, `direction`, `size_contracts`
  - `exit_bar_index`, `exit_time_ms`, `exit_price`, `exit_reason`, `pnl_r`, `pnl_usd`
- `execution_hash`: Hash SHA-256 can?nico calculado sobre todos los trades del ledger y la identidad de ejecuci?n.

