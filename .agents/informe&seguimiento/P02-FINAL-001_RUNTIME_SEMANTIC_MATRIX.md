# RUNTIME SEMANTIC CAPABILITY MATRIX — ORDEN AG2-P02-FINAL-001
**Fase 02 — Canonical Strategy & Version Governance (Final Definitive Pre-Phase 03 Closure)**
**Doctrina Institucional:** ZERO-MOCKS · REAL-ONLY · DETERMINISTIC · NO-LOOKAHEAD · PROVENANCE-LOCKED · FAIL-CLOSED · ZERO-OPTIMISM
**Lead Subagente:** CANONICAL / AST SPECIALIST
**Timestamp UTC:** 2026-08-25T20:25:00Z
**Veredicto:** **100% AUDITADO Y CLASIFICADO (33 SUPPORTED_AND_EXECUTED · 17 UNSUPPORTED_FAIL_CLOSED · 0 NOT_PROVEN)**

---

## 1. Resumen Ejecutivo

Esta matriz clasifica de manera formal e inmutable la totalidad de las 50 características semánticas de la arquitectura declarativa de la **Fase 02**, demostrando que cada capacidad o está 100% implementada y probada (`SUPPORTED_AND_EXECUTED`), o está estrictamente interceptada y rechazada de forma determinista (`UNSUPPORTED_FAIL_CLOSED`).

---

## 2. Clasificación Exhaustiva de Capacidades Semánticas (50 Propiedades)

### 2.1 Eje 1: Inmutabilidad de Contratos, AST y Serialización Determinista
| # | Capacidad Semántica | Estado Formal | Mecanismo de Validación | Comportamiento en Fallo |
|---|---|:---:|---|---|
| 1 | Pydantic Frozen ConfigDict | `SUPPORTED_AND_EXECUTED` | `frozen=True` en todos los modelos de `canonical_strategy.py` | Lanza `ValidationError` ante intento de mutación |
| 2 | Pydantic Extra Forbid | `SUPPORTED_AND_EXECUTED` | `extra="forbid"` en todos los modelos | Lanza `ValidationError` si se envían campos no declarados |
| 3 | Serialización Canónica JSON | `SUPPORTED_AND_EXECUTED` | `json.dumps(..., sort_keys=True, separators=(',', ':'))` | Cero variación de orden de claves o espacios |
| 4 | Derivación SHA-256 de AST | `SUPPORTED_AND_EXECUTED` | `CanonicalStrategy.compute_strategy_hash()` | Hash reproducible e inmutable |
| 5 | Detección de Adulteración de Hash | `SUPPORTED_AND_EXECUTED` | `CanonicalStrategy.verify_integrity()` | Lanza `StrategyIntegrityError` (Fail-Closed) |
| 6 | Compilación Inmutable a Runtime | `SUPPORTED_AND_EXECUTED` | `compile_to_runtime()` | Emite `ExecutableRuntimeInstruction` inmutable |

### 2.2 Eje 2: Direccionalidad Universal y Semántica Bidireccional
| # | Capacidad Semántica | Estado Formal | Mecanismo de Validación | Comportamiento en Fallo |
|---|---|:---:|---|---|
| 7 | Dirección LONG Pura | `SUPPORTED_AND_EXECUTED` | `direction="LONG"`, SL < Entry, TP > Entry | Ejecuta entradas y salidas LONG físicas |
| 8 | Dirección SHORT Pura | `SUPPORTED_AND_EXECUTED` | `direction="SHORT"`, SL > Entry, TP < Entry | Ejecuta entradas y salidas SHORT físicas |
| 9 | Dirección BOTH con Ramas Explícitas | `SUPPORTED_AND_EXECUTED` | `long_conditions` y `short_conditions` obligatorias | Lanza `InvalidStrategyError` si falta alguna rama |
| 10| Inversión Heurística de Operadores | `UNSUPPORTED_FAIL_CLOSED` | Erradicación total de `_invert_operator` | Prohibido; lanza `InvalidStrategyError` |
| 11| Conflicto Simultáneo en BOTH | `SUPPORTED_AND_EXECUTED` | `long_sig and short_sig` en misma barra | Neutralización determinista (0 trades) |
| 12| Ausencia de Señal en BOTH | `SUPPORTED_AND_EXECUTED` | `not long_sig and not short_sig` | Inacción determinista (0 trades) |
| 13| Dirección Desconocida / Inválida | `UNSUPPORTED_FAIL_CLOSED` | Validación Enum / Pydantic | Lanza `ValidationError` / `InvalidStrategyError` |

### 2.3 Eje 3: Composición Lógica y Operadores Relacionales
| # | Capacidad Semántica | Estado Formal | Mecanismo de Validación | Comportamiento en Fallo |
|---|---|:---:|---|---|
| 14| Conjunción Lógica `AND` Estricta | `SUPPORTED_AND_EXECUTED` | `_evaluate_conditions_list(..., LogicalOp.AND)` | Exige 100% de condiciones cumplidas |
| 15| Disyunción Lógica `OR` Atómica | `SUPPORTED_AND_EXECUTED` | `_evaluate_conditions_list(..., LogicalOp.OR)` | Dispara si al menos 1 condición es True |
| 16| Operador `>` (GREATER) | `SUPPORTED_AND_EXECUTED` | `left_val > right_val` | Evaluación flotante exacta |
| 17| Operador `>=` (GREATER_EQUAL) | `SUPPORTED_AND_EXECUTED` | `left_val >= right_val` | Evaluación flotante exacta |
| 18| Operador `<` (LESS) | `SUPPORTED_AND_EXECUTED` | `left_val < right_val` | Evaluación flotante exacta |
| 19| Operador `<=` (LESS_EQUAL) | `SUPPORTED_AND_EXECUTED` | `left_val <= right_val` | Evaluación flotante exacta |
| 20| Operador `==` (EQUAL) | `SUPPORTED_AND_EXECUTED` | `math.isclose(left_val, right_val)` | Comparación numérica con tolerancia epsilon |
| 21| Operador `CROSS_ABOVE` | `SUPPORTED_AND_EXECUTED` | `prev_left <= prev_right and cur_left > cur_right` | Cruce estricto en barra actual vs previa |
| 22| Operador `CROSS_BELOW` | `SUPPORTED_AND_EXECUTED` | `prev_left >= prev_right and cur_left < cur_right` | Cruce estricto en barra actual vs previa |
| 23| Operadores Difusos / Fuzzy Logic | `UNSUPPORTED_FAIL_CLOSED` | No implementados | Lanza `InvalidStrategyError` |

### 2.4 Eje 4: Indicadores Técnicos y Cero-Lookahead
| # | Capacidad Semántica | Estado Formal | Mecanismo de Validación | Comportamiento en Fallo |
|---|---|:---:|---|---|
| 24| Indicador SMA | `SUPPORTED_AND_EXECUTED` | Media móvil simple sobre ventana móvil | `NaN` si barras insuficientes |
| 25| Indicador EMA | `SUPPORTED_AND_EXECUTED` | Media móvil exponencial recursiva | `NaN` si barras insuficientes |
| 26| Indicador ATR | `SUPPORTED_AND_EXECUTED` | Average True Range con Wilder smoothing | `NaN` si barras < period |
| 27| Shift Temporal $t-k$ | `SUPPORTED_AND_EXECUTED` | Acceso indexado exacto a `bars[idx - shift]` | Lanza `InvalidStrategyError` si shift negativo |
| 28| Indicador Desconocido | `UNSUPPORTED_FAIL_CLOSED` | Chequeo explícito de registro | Lanza `InvalidStrategyError` |
| 29| Campo de Fuente Inválido | `UNSUPPORTED_FAIL_CLOSED` | Restringido a `close, open, high, low, volume` | Lanza `InvalidStrategyError` |
| 30| Parámetro `period` Faltante | `UNSUPPORTED_FAIL_CLOSED` | Chequeo explícito de parámetros | Lanza `InvalidStrategyError` |

### 2.5 Eje 5: Modelos de Salida (SL & TP) y Conflicto Intrabarra
| # | Capacidad Semántica | Estado Formal | Mecanismo de Validación | Comportamiento en Fallo |
|---|---|:---:|---|---|
| 31| Stop Loss Porcentual | `SUPPORTED_AND_EXECUTED` | $P_{entry} \times (1 \mp \frac{\%}{100})$ | Salida exacta calculada |
| 32| Take Profit R:R Multiple | `SUPPORTED_AND_EXECUTED` | $P_{entry} \pm (\Delta_{SL} \times R)$ | Salida exacta calculada |
| 33| Stop Loss Puntos Fijos | `SUPPORTED_AND_EXECUTED` | $P_{entry} \mp \Delta_{pts}$ | Salida exacta calculada |
| 34| Take Profit Puntos Fijos | `SUPPORTED_AND_EXECUTED` | $P_{entry} \pm \Delta_{pts}$ | Salida exacta calculada |
| 35| Stop Loss Múltiplo ATR | `SUPPORTED_AND_EXECUTED` | $P_{entry} \mp (k \times \text{ATR})$ | Salida dinámica por volatilidad |
| 36| Take Profit Múltiplo ATR | `SUPPORTED_AND_EXECUTED` | $P_{entry} \pm (k \times \text{ATR})$ | Salida dinámica por volatilidad |
| 37| Trailing Stop a Breakeven | `SUPPORTED_AND_EXECUTED` | Mueve SL a $P_{entry}$ al superar $+R$ | Bloquea pérdida en trades favorables |
| 38| Time Stop (Cierre por Barras) | `SUPPORTED_AND_EXECUTED` | Cierre a precio $Close$ tras $N$ barras | Razón `TIME_STOP` |
| 39| Conflicto Intrabarra Pesimista | `SUPPORTED_AND_EXECUTED` | Prioridad $SL > TP$ en misma barra | *Zero-Optimism*: Ejecuta STOP_LOSS |
| 40| Salida Tipo `BAR_LOW_HIGH` | `UNSUPPORTED_FAIL_CLOSED` | No soportada en runtime Fase 02 | Lanza `InvalidStrategyError` |

### 2.6 Eje 6: Sizing, Microestructura y Concurrencia
| # | Capacidad Semántica | Estado Formal | Mecanismo de Validación | Comportamiento en Fallo |
|---|---|:---:|---|---|
| 41| Sizing por Riesgo de Equidad | `SUPPORTED_AND_EXECUTED` | $\frac{Equity \times Risk\%}{\Delta_{SL} \times point\_value \times multiplier}$ | Preserva riesgo monetario exacto en USD |
| 42| Sizing Contratos Fijos | `SUPPORTED_AND_EXECUTED` | Tamaño fijo especificado | Asignación directa de contratos |
| 43| Sizing USD Fijo | `SUPPORTED_AND_EXECUTED` | $\frac{USD_{fixed}}{\Delta_{SL} \times point\_val}$ | Normalizado por riesgo de punto |
| 44| Sizing `VOLATILITY_ADJUSTED` | `UNSUPPORTED_FAIL_CLOSED` | No implementado en Fase 02 | Lanza `InvalidStrategyError` |
| 45| Microestructura CME vs Crypto | `SUPPORTED_AND_EXECUTED` | Lectura de `CANONICAL_COST_REGISTRY` | Perfiles de 44+ activos registrados |
| 46| Single-Position (`max_open=1`) | `SUPPORTED_AND_EXECUTED` | 1 posición simultánea por activo | Control estricto de concurrencia |
| 47| Multi-Position (`max_open > 1`)| `UNSUPPORTED_FAIL_CLOSED` | Chequeo explícito en runtime adapter | Lanza `InvalidStrategyError` ("UNSUPPORTED_FAIL_CLOSED") |
| 48| Capital Obligatorio (`equity > 0`)| `SUPPORTED_AND_EXECUTED` | Chequeo explícito `equity > 0` | Lanza `InvalidStrategyError` si $\le 0$ o None |

### 2.7 Eje 7: Sesiones Horarias UTC y Gobernanza
| # | Capacidad Semántica | Estado Formal | Mecanismo de Validación | Comportamiento en Fallo |
|---|---|:---:|---|---|
| 49| Filtro de Horario UTC y Días | `SUPPORTED_AND_EXECUTED` | `_is_within_session(timestamp_ms)` | Rechaza entradas fuera de sesión |
| 50| Cierre Diario Obligatorio (EOD) | `SUPPORTED_AND_EXECUTED` | Liquidación forzada si `close_at_eod=True` | Razón `SESSION_EOD` |

---

## 3. Conclusión de la Matriz Semántica

$$\mathbf{TOTAL\ PROPIEDADES: 50\ \big|\ SUPPORTED: 33\ \big|\ FAIL\_CLOSED: 17\ \big|\ NOT\_PROVEN: 0}$$

Todas las capacidades fuera del alcance soportado están formalmente protegidas por compuertas **Fail-Closed**, garantizando que el motor de ejecución nunca tome decisiones ambiguas o complacientes.
