# RUNTIME SEMANTIC MATRIX & BOUNDARY PROOF ? ORDEN AG2-P02-007
**Fase 02 ? Canonical Bidirectional Semantics & Real Execution Boundary Proof**  
**Fecha:** 2026-08-25T19:28:00Z  
**Subagente:** CANONICAL / AST  
**Estado:** VIGENTE & CERTIFICADA  

---

## 1. Declaraci?n de Principios de Ejecuci?n Can?nica (SSOT)

1. **Doctrina Zero-Mocks & Real-Only:** Cero heur?sticas no declaradas, cero inversiones sint?ticas de operadores l?gicos y cero valores ficticios.
2. **Fail-Closed Estricto:** Toda capacidad fuera del contrato de runtime, par?metro faltante o configuraci?n ambigua debe abortar con `InvalidStrategyError` o `ValidationError`.
3. **Sem?ntica Bidireccional Verdadera:** El modo `direction == "BOTH"` exige obligatoriamente ramas expl?citas e independientes `long_conditions` y `short_conditions`. La inversi?n heur?stica de operadores (`_invert_operator`) queda formalmente clasificada como **UNSUPPORTED_FAIL_CLOSED**.
4. **L?mite de Concurrencia de Posiciones:** El motor opera estrictamente en modo single-position (`max_open_positions == 1`). Todo intento de ejecutar con `max_open_positions > 1` queda clasificado como **UNSUPPORTED_FAIL_CLOSED**.

---

## 2. Matriz Sem?ntica Universal de Capacidades y Fronteras

| Categor?a | Elemento Sem?ntico | Estado de Ejecuci?n | Regla de Validaci?n y Comportamiento Fail-Closed | Archivo SSOT |
|---|---|---|---|---|
| **Direccionalidad** | **Direction LONG** | `SUPPORTED_AND_EXECUTED` | Eval?a `entry_rules.conditions` (o `long_conditions`). Genera trades LONG: SL por debajo del precio de entrada, TP por encima, $PnL = (P_{exit} - P_{entry}) \times \text{mult}$. | `contracts/canonical_strategy.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Direccionalidad** | **Direction SHORT** | `SUPPORTED_AND_EXECUTED` | Eval?a `entry_rules.conditions` (o `short_conditions`). Genera trades SHORT: SL por encima del precio de entrada, TP por debajo, $PnL = (P_{entry} - P_{exit}) \times \text{mult}$. | `contracts/canonical_strategy.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Direccionalidad** | **Direction BOTH (Ramas Expl?citas)** | `SUPPORTED_AND_EXECUTED` | Requiere obligatoriamente `long_conditions` y `short_conditions` no vac?as. Eval?a ambas ramas independientemente. Si ambas disparan en la misma vela, omite entrada por conflicto simult?neo. | `contracts/canonical_strategy.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Direccionalidad** | **Direction BOTH (Inversi?n Heur?stica)** | `UNSUPPORTED_FAIL_CLOSED` | **PROHIBIDO TERMINANTEMENTE.** Si `direction == "BOTH"` y no se declaran `long_conditions` y `short_conditions`, lanza `InvalidStrategyError`. Cero inferencias autom?ticas. | `contracts/canonical_strategy.py` |
| **Direccionalidad** | **Direcci?n No Declarada / Inv?lida** | `UNSUPPORTED_FAIL_CLOSED` | Rechaza cualquier valor fuera de `LONG`, `SHORT`, `BOTH` con `ValidationError`. | `contracts/canonical_strategy.py` |
| **Operadores L?gicos** | **LogicalOp AND** | `SUPPORTED_AND_EXECUTED` | Conjunci?n estricta: el 100% de las condiciones de la rama activa deben ser verdaderas en la barra $t$ para disparar entrada. | `services/execution/canonical_runtime_adapter.py` |
| **Operadores L?gicos** | **LogicalOp OR** | `SUPPORTED_AND_EXECUTED` | Disyunci?n estricta: al menos 1 condici?n de la rama activa debe ser verdadera en la barra $t$ para disparar entrada. | `services/execution/canonical_runtime_adapter.py` |
| **Operadores L?gicos** | **Operador L?gico Desconocido** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `ValidationError` en construcci?n de AST o `InvalidStrategyError` en runtime. | `contracts/canonical_strategy.py` |
| **Comparaci?n** | **GT (`>`), GTE (`>=`), LT (`<`), LTE (`<=`), EQ (`==`)** | `SUPPORTED_AND_EXECUTED` | Comparaci?n escalar num?rica determinista en barra $t$. Si alg?n lado resulta `NaN`, eval?a como `False`. | `services/execution/canonical_runtime_adapter.py` |
| **Comparaci?n** | **CROSS_ABOVE / CROSS_BELOW** | `SUPPORTED_AND_EXECUTED` | Cruce temporal interbarra entre $t-1$ y $t$. Si $t < 1$ o alg?n valor previo es `NaN`, eval?a como `False`. | `services/execution/canonical_runtime_adapter.py` |
| **Comparaci?n** | **Operador de Comparaci?n Inv?lido** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` inmediatamente. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores** | **PRICE (Close, Open, High, Low, Volume)** | `SUPPORTED_AND_EXECUTED` | Extracci?n directa del feed f?sico normalizado con `shift` temporal expl?cito ($t - \text{shift}$). | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores** | **SMA (Simple Moving Average)** | `SUPPORTED_AND_EXECUTED` | Media aritm?tica exacta de la ventana `period`. Retorna `NaN` si el ?ndice es menor a `period - 1`. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores** | **EMA (Exponential Moving Average)** | `SUPPORTED_AND_EXECUTED` | Ponderaci?n exponencial $k = 2 / (\text{period} + 1)$ acumulada desde la barra 0. Retorna `NaN` si faltan datos. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores** | **ATR (Average True Range)** | `SUPPORTED_AND_EXECUTED` | Media de True Range sobre ventana `period` (m?nimo 14 barras para SL/TP din?micos). | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores** | **Indicador No Registrado** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError`. 0% fallback a `close` o valores predeterminados. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores** | **Par?metro `period` Ausente o <= 0** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` de inmediato. | `services/execution/canonical_runtime_adapter.py` |
| **Indicadores** | **Campo Fuente No Soportado** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` si `source_field` no pertenece a `['close', 'open', 'high', 'low', 'volume']`. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Type: PERCENTAGE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{SL} = P_{entry} \times (sl\_val / 100.0)$. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Type: FIXED_POINTS** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{SL} = sl\_val$. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Type: ATR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{SL} = \text{ATR}(14) \times sl\_val$. Falla cerrado si faltan barras hist?ricas. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Type: BAR_LOW_HIGH** | `UNSUPPORTED_FAIL_CLOSED` | Requiere parametrizaci?n din?mica de lookback no formalizada; lanza `InvalidStrategyError`. | `services/execution/canonical_runtime_adapter.py` |
| **Stop Loss** | **SL Value <= 0** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `ValidationError` (`gt=0.0`) en AST o `InvalidStrategyError` en c?lculo. | `contracts/canonical_strategy.py` |
| **Take Profit** | **TP Type: RR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{TP} = \Delta_{SL} \times tp\_val$. Enlaza sim?tricamente el riesgo con la recompensa. | `services/execution/canonical_runtime_adapter.py` |
| **Take Profit** | **TP Type: PERCENTAGE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{TP} = P_{entry} \times (tp\_val / 100.0)$. | `services/execution/canonical_runtime_adapter.py` |
| **Take Profit** | **TP Type: FIXED_POINTS** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{TP} = tp\_val$. | `services/execution/canonical_runtime_adapter.py` |
| **Take Profit** | **TP Type: ATR_MULTIPLE** | `SUPPORTED_AND_EXECUTED` | Distancia: $\Delta_{TP} = \text{ATR}(14) \times tp\_val$. Falla cerrado si faltan barras hist?ricas. | `services/execution/canonical_runtime_adapter.py` |
| **Take Profit** | **TP Value <= 0** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `ValidationError` (`gt=0.0`) en AST o `InvalidStrategyError` en c?lculo. | `contracts/canonical_strategy.py` |
| **Gesti?n de Salida** | **Conflicto Intrabarra SL / TP** | `SUPPORTED_AND_EXECUTED` | **Doctrina Zero-Optimism:** Si una misma vela toca simult?neamente el nivel de SL y TP, se ejecuta obligatoriamente el Stop Loss. | `services/execution/canonical_runtime_adapter.py` |
| **Gesti?n de Salida** | **Trailing Stop (`trail_after_r`)** | `SUPPORTED_AND_EXECUTED` | Mueve el SL a Breakeven ($P_{entry}$) cuando la ganancia flotante alcanza $R \ge trail\_after\_r$. | `services/execution/canonical_runtime_adapter.py` |
| **Gesti?n de Salida** | **Time Stop (`time_stop_bars`)** | `SUPPORTED_AND_EXECUTED` | Cierre forzoso de mercado al precio de cierre de la barra tras $N$ velas transcurridas. | `services/execution/canonical_runtime_adapter.py` |
| **Gesti?n de Salida** | **Cierre por Fin de Sesi?n (`close_at_eod`)** | `SUPPORTED_AND_EXECUTED` | Cierre forzoso al precio de cierre al alcanzar o superar `end_time_utc`. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Sizing: RISK_PCT_EQUITY** | `SUPPORTED_AND_EXECUTED` | Contratos = $\frac{AccountEquity \times (RiskPct / 100.0)}{\Delta_{SL} \times PointValue \times Multiplier}$. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Sizing: FIXED_CONTRACTS** | `SUPPORTED_AND_EXECUTED` | Contratos fijos = `risk_value`. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Sizing: FIXED_USD** | `SUPPORTED_AND_EXECUTED` | Contratos = $\frac{RiskUSD}{\Delta_{SL} \times PointValue \times Multiplier}$. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Sizing: VOLATILITY_ADJUSTED** | `UNSUPPORTED_FAIL_CLOSED` | Modelo de volatilidad multivariable no estandarizado en adapter; lanza `InvalidStrategyError`. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Capacidad Single-Position (`max_open_positions == 1`)** | `SUPPORTED_AND_EXECUTED` | Bloqueo estricto de nuevas entradas mientras haya una posici?n abierta. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Multi-Position Scaling (`max_open_positions > 1`)** | `UNSUPPORTED_FAIL_CLOSED` | **L?MITE ARQUITECT?NICO FASE 02.** Motor actual opera en single-position; si `max_open_positions != 1`, lanza `InvalidStrategyError`. | `services/execution/canonical_runtime_adapter.py` |
| **Dimensionamiento** | **Account Equity <= 0 / NaN / None** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError` de inmediato sin defaults ficticios. | `services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Ventana Intra-D?a UTC (e.g. 14:30 - 21:00)** | `SUPPORTED_AND_EXECUTED` | Filtra entradas fuera del intervalo horario UTC declarado. | `services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Ventana Nocturna Cruzando Medianoche (e.g. 22:00 - 04:00)** | `SUPPORTED_AND_EXECUTED` | Eval?a correctamente la disyunci?n circular de minutos sobre las 24 horas UTC. | `services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Filtro de D?as Permitidos (`allowed_days`)** | `SUPPORTED_AND_EXECUTED` | Permite operar ?nicamente en d?as indexados en la lista (0=Lunes, 6=Domingo). | `services/execution/canonical_runtime_adapter.py` |
| **Sesiones y Tiempo** | **Timestamps Ausentes o Inv?lidos (<= 0)** | `UNSUPPORTED_FAIL_CLOSED` | Lanza `InvalidStrategyError`; cero fallbacks a timestamps sint?ticos. | `services/execution/canonical_runtime_adapter.py` |
| **Gobernanza y Linaje** | **SHA-256 Strategy Hash SSOT** | `SUPPORTED_AND_EXECUTED` | Valida coincidencia exacta de `strategy_hash` con el payload JSON ordenado del AST completo. | `contracts/canonical_strategy.py` |
| **Gobernanza y Linaje** | **Engine & Policy Version Binding** | `SUPPORTED_AND_EXECUTED` | Exige versiones id?nticas del SSOT (`CURRENT_ENGINE_VERSION`, `CURRENT_POLICY_VERSION`). | `services/engine_version.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Gobernanza y Linaje** | **Cadena de Custodia DatasetRegistry** | `SUPPORTED_AND_EXECUTED` | Resuelve dataset f?sico en parquet y verifica su hash criptogr?fico SHA-256 en disco. | `services/data/dataset_registry.py`<br>`services/execution/canonical_runtime_adapter.py` |
| **Gobernanza y Linaje** | **Execution Hash Criptogr?fico** | `SUPPORTED_AND_EXECUTED` | Genera SHA-256 inmutable ligando estrategia, dataset, capital, microestructura y lista completa de trades. | `services/execution/canonical_runtime_adapter.py` |

---

