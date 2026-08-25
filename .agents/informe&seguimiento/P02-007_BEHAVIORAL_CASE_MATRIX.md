# P02-007 BEHAVIORAL CASE MATRIX ? CANONICAL BIDIRECTIONAL SEMANTICS & REAL EXECUTION BOUNDARY PROOF
**Orden:** `AG2-P02-007`  
**Fase:** `PHASE 02 ? CANONICAL BIDIRECTIONAL SEMANTICS & REAL EXECUTION BOUNDARY PROOF`  
**Versi?n de Motor SSOT:** `v5.4.0` (`services/engine_version.py`)  
**Versi?n de Pol?tica SSOT:** `v5.4.0` (`services/engine_version.py`)  
**Subagente Responsable:** `QUANT / BIDIRECTIONAL`  
**Doctrina Institucional:** `ZERO-MOCKS ? REAL-ONLY ? DETERMINISTIC ? NO-LOOKAHEAD ? PROVENANCE-LOCKED ? FAIL-CLOSED ? ZERO-OPTIMISM`  
**Fecha UTC:** `2026-08-25T19:30:00Z`

---

## 1. Resumen Ejecutivo y Prop?sito

El presente documento establece la especificaci?n cuantitativa y la matriz formal de casos f?sicos de comportamiento (*Behavioral Runtime Cases*) para la validaci?n definitiva de la **sem?ntica bidireccional can?nica (`BOTH`)** y los **l?mites f?sicos de ejecuci?n determinista** en `CanonicalRuntimeAdapter` (`services/execution/canonical_runtime_adapter.py`).

Este est?ndar formaliza:
1. **Sem?ntica de Se?ales Bidireccionales (`BOTH`):** Descomposici?n sim?trica del AST en ramas alcistas ($L_{signal}$) y bajistas ($S_{signal}$) mediante el operador de inversi?n anal?tica $\mathcal{I}(C)$.
2. **Casos F?sicos de Activaci?n y Neutralizaci?n:** Demostraci?n de ejecuci?n LONG real (BOTH-01), ejecuci?n SHORT real (BOTH-02), inacci?n por ausencia de se?al (BOTH-03) y neutralizaci?n por conflicto simult?neo / indeterminaci?n (BOTH-04).
3. **Dimensionamiento Instrument-Aware (Point Value & Sizing):** Formalizaci?n matem?tica del dimensionamiento de riesgo en futuros CME (NQ a \$20/punto) versus criptoactivos (BTCUSDT a \$1/punto), demostrando la conservaci?n exacta del riesgo monetario en USD.
4. **Condiciones de Frontera y Prioridad Pesimista:** Resoluci?n de conflicto intrabarra SL vs TP (*Zero-Optimism*) y restricciones de sesi?n horaria UTC.

---

## 2. Matriz de Casos de Comportamiento F?sico Cuantitativo

| ID Caso | Escenario Cuantitativo | Direcci?n AST | Rama Activa ($L_{sig}, S_{sig}$) | Activo / Microestructura | Condici?n de Salida | PnL R Te?rico | PnL USD Te?rico | Regla Fail-Closed / Criterio de Verificaci?n |
|---|---|:---:|:---:|---|---|:---:|:---:|---|
| **BOTH-01** | Se?al LONG Expl?cita | `BOTH` | $L_{sig}=1, S_{sig}=0$ | NQ ($pt=\$20$, $mult=1.0$) | $High_t \ge TP_{tgt}$ ? $Low_t \le SL_{tgt}$ | $TP: +2.0R$ / $SL: -1.0R$ | $TP: +\$2,000$ / $SL: -\$1,000$ | Entrada LONG real en $Close_i$. Salida verificada en TP ($PnL>0$) o SL ($PnL<0$). |
| **BOTH-02** | Se?al SHORT Expl?cita | `BOTH` | $L_{sig}=0, S_{sig}=1$ | BTCUSDT ($pt=\$1$, $mult=1.0$) | $Low_t \le TP_{tgt}$ ? $High_t \ge SL_{tgt}$ | $TP: +2.0R$ / $SL: -1.0R$ | $TP: +\$2,000$ / $SL: -\$1,000$ | Entrada SHORT real en $Close_i$. Salida verificada en TP ($PnL>0$) o SL ($PnL<0$). |
| **BOTH-03** | Ausencia de Se?al | `BOTH` | $L_{sig}=0, S_{sig}=0$ | Cualquier Instrumento | N/A (Sin posici?n) | $0.0R$ | $\$0.00$ | Inacci?n determinista: $total\_trades = 0$. Cero aperturas espurias. |
| **BOTH-04** | Conflicto Simult?neo | `BOTH` | $L_{sig}=1, S_{sig}=1$ | Cualquier Instrumento | N/A (Indeterminaci?n) | $0.0R$ | $\$0.00$ | Neutralizaci?n Fail-Closed: $trigger\_entered = \text{False}$, $0\text{ trades}$. Cero coin-flip. |
| **SIZING-NQ** | Sizing CME NQ | Cualquier | Disparo v?lido | NQ ($point\_value = 20.0$) | SL alcanzado ($\Delta_{SL}=50$) | $-1.0R$ | $-\$1,000.00$ | $Contracts = \frac{\$1,000}{50 \times 20 \times 1} = 1.0$. P?rdida acotada exactamente a $\$1,000$. |
| **SIZING-BTC**| Sizing Cripto BTC | Cualquier | Disparo v?lido | BTCUSDT ($point\_value = 1.0$)| SL alcanzado ($\Delta_{SL}=50$) | $-1.0R$ | $-\$1,000.00$ | $Contracts = \frac{\$1,000}{50 \times 1 \times 1} = 20.0$. P?rdida acotada exactamente a $\$1,000$. |
| **INTRABAR** | Conflicto Intrabarra | `LONG` / `SHORT`| Disparo v?lido | NQ / BTCUSDT | $Low_t \le SL \land High_t \ge TP$ | $-1.0R$ | $-Risk_{USD}$ | Prioridad institucional pesimista (*Zero-Optimism*): Ejecuta STOP_LOSS. |
| **SESSION** | Fuera de Ventana | Cualquier | Disparo fuera de ventana | Futuros CME / Forex | $t \notin SessionWindow$ | $0.0R$ | $\$0.00$ | Bloqueo estricto por filtro horario o d?a no permitido (`allowed_days`). |

---

## 3. Formalizaci?n Matem?tica de la Sem?ntica Bidireccional (`BOTH`)

### 3.1 ?lgebra del ?rbol de Reglas y Operador de Inversi?n $\mathcal{I}$

Sea una condici?n at?mica $C = \langle \text{Left}, \text{Op}, \text{Right} \rangle$ definida en el AST de la estrategia can?nica.

Definimos el operador de inversi?n sem?ntica $\mathcal{I}(C)$ como:
$$\mathcal{I}\big(\langle \text{Left}, \text{Op}, \text{Right} \rangle\big) = \langle \text{Left}, \mathcal{I}_{op}(\text{Op}), \text{Right} \rangle$$

Donde la biyecci?n de inversi?n de operadores $\mathcal{I}_{op}: \Omega \to \Omega$ sobre el espacio de operadores $\Omega = \{>, \ge, <, \le, \text{CROSS\_ABOVE}, \text{CROSS\_BELOW}, ==\}$ est? un?vocamente determinada por:
$$\mathcal{I}_{op}(\text{Op}) = \begin{cases} 
< & \text{si } \text{Op} \in \{>, \text{GT}\} \\
> & \text{si } \text{Op} \in \{<, \text{LT}\} \\
\le & \text{si } \text{Op} \in \{\ge, \text{GTE}\} \\
\ge & \text{si } \text{Op} \in \{\le, \text{LTE}\} \\
\text{CROSS\_BELOW} & \text{si } \text{Op} \in \{\text{CROSS\_ABOVE}\} \\
\text{CROSS\_ABOVE} & \text{si } \text{Op} \in \{\text{CROSS\_BELOW}\} \\
== & \text{si } \text{Op} \in \{==, \text{EQ}\} 
\end{cases}$$

### 3.2 Construcci?n de Ramas Direccionales $L_{conds}$ y $S_{conds}$

Para una estrategia con `direction == "BOTH"`, el motor compila dos ramas disjuntas de evaluaci?n a partir del conjunto de condiciones base $\mathcal{C} = \{c_1, c_2, \dots, c_k\}$:

1. **Clasificaci?n Polar de la Condici?n:**
   Una condici?n $c_j$ se define como intr?nsecamente bajista ($\text{Polarity}(c_j) = \text{BEARISH}$) si $\text{Op}(c_j) \in \{<, \le, \text{CROSS\_BELOW}\}$. De lo contrario, $\text{Polarity}(c_j) = \text{BULLISH}$.

2. **Asignaci?n a Conjuntos de Evaluaci?n:**
   $$L_{conds} = \bigcup_{c_j \in \mathcal{C}} \begin{cases} \{\mathcal{I}(c_j)\} & \text{si } \text{Polarity}(c_j) = \text{BEARISH} \\ \{c_j\} & \text{si } \text{Polarity}(c_j) = \text{BULLISH} \end{cases}$$
   $$S_{conds} = \bigcup_{c_j \in \mathcal{C}} \begin{cases} \{c_j\} & \text{si } \text{Polarity}(c_j) = \text{BEARISH} \\ \{\mathcal{I}(c_j)\} & \text{si } \text{Polarity}(c_j) = \text{BULLISH} \end{cases}$$

### 3.3 Evaluaci?n de Se?ales y L?gica de Disparo

En cada barra $i \ge 0$, dadas las barras hist?ricas $\mathcal{B}_{0:i}$:
$$L_{signal}(i) = \Phi(L_{conds}, \text{LogicalOp}, \mathcal{B}_{0:i})$$
$$S_{signal}(i) = \Phi(S_{conds}, \text{LogicalOp}, \mathcal{B}_{0:i})$$

Donde el evaluador l?gico compuesto $\Phi$ se define como:
$$\Phi(K, \text{op}, \mathcal{B}) = \begin{cases} 
\bigwedge_{c \in K} \text{Eval}(c, \mathcal{B}) & \text{si } \text{op} = \text{AND} \\
\bigvee_{c \in K} \text{Eval}(c, \mathcal{B}) & \text{si } \text{op} = \text{OR}
\end{cases}$$

La decisi?n de entrada en el modo bidireccional sigue la funci?n de decisi?n discreta:
$$\text{TriggerState}(i) = \begin{cases} 
\text{ENTER\_LONG} & \text{si } L_{signal}(i) = \text{True} \land S_{signal}(i) = \text{False} \\
\text{ENTER\_SHORT} & \text{si } S_{signal}(i) = \text{True} \land L_{signal}(i) = \text{False} \\
\text{NO\_ACTION} & \text{si } L_{signal}(i) = \text{False} \land S_{signal}(i) = \text{False} \quad (\text{Caso BOTH-03}) \\
\text{INDETERMINATE} \to \text{NO\_ACTION} & \text{si } L_{signal}(i) = \text{True} \land S_{signal}(i) = \text{True} \quad (\text{Caso BOTH-04})
\end{cases}$$

---

## 4. Especificaci?n Detallada de los Casos Cuantitativos

### 4.1 Caso BOTH-01: Se?al LONG Expl?cita en Modo Bidireccional

- **Objetivo Cuantitativo:** Verificar la apertura real de una posici?n `LONG` cuando se satisface exclusivamente la rama alcista en una estrategia declarada como `BOTH`, asegurando que el c?lculo de niveles de SL/TP y PnL responde a la geometr?a alcista.
- **Precondiciones F?sicas:**
  - `direction = "BOTH"`.
  - `entry_rules`: $\text{PRICE\_CLOSE} > \text{SMA}(20)$ con `LogicalOp.AND`.
  - Rama $L_{signal}$: $\text{Close}_i > \text{SMA}_{20}(i) \implies \text{True}$.
  - Rama $S_{signal}$: $\text{Close}_i < \text{SMA}_{20}(i) \implies \text{False}$.
- **Din?mica de Ejecuci?n:**
  1. **Precio de Entrada:** $P_{entry} = Close_i$.
  2. **Nivel de Stop Loss:** $SL_{target} = P_{entry} - \Delta_{SL}$ (donde $\Delta_{SL} > 0$).
  3. **Nivel de Take Profit:** $TP_{target} = P_{entry} + \Delta_{TP}$ (donde $\Delta_{TP} > 0$).
- **Evaluaci?n de Salida y PnL:**
  - **Rama Favorable (TP):** Si en barra $t > i$, $High_t \ge TP_{target}$ y $Low_t > SL_{target}$:
    $$ExitReason = \text{"TAKE\_PROFIT"}, \quad P_{exit} = TP_{target}$$
    $$PnL_R = \frac{TP_{target} - P_{entry}}{\Delta_{SL}} = \frac{\Delta_{TP}}{\Delta_{SL}} = +tp\_value > 0$$
    $$PnL_{USD} = (TP_{target} - P_{entry}) \times Contracts \times point\_value \times multiplier > 0$$
  - **Rama Desfavorable (SL):** Si en barra $t > i$, $Low_t \le SL_{target}$:
    $$ExitReason = \text{"STOP\_LOSS"}, \quad P_{exit} = SL_{target}$$
    $$PnL_R = \frac{SL_{target} - P_{entry}}{\Delta_{SL}} = \frac{-\Delta_{SL}}{\Delta_{SL}} = -1.0 < 0$$
    $$PnL_{USD} = -\Delta_{SL} \times Contracts \times point\_value \times multiplier = -Risk_{USD} < 0$$

---

### 4.2 Caso BOTH-02: Se?al SHORT Expl?cita en Modo Bidireccional

- **Objetivo Cuantitativo:** Verificar la apertura real de una posici?n `SHORT` cuando se satisface exclusivamente la rama bajista en una estrategia declarada como `BOTH`, asegurando que el c?lculo de niveles de SL/TP y PnL responde a la geometr?a bajista.
- **Precondiciones F?sicas:**
  - `direction = "BOTH"`.
  - `entry_rules`: $\text{PRICE\_CLOSE} > \text{SMA}(20)$ con `LogicalOp.AND`.
  - Rama $L_{signal}$: $\text{Close}_i > \text{SMA}_{20}(i) \implies \text{False}$.
  - Rama $S_{signal}$: $\text{Close}_i < \text{SMA}_{20}(i) \implies \text{True}$.
- **Din?mica de Ejecuci?n:**
  1. **Precio de Entrada:** $P_{entry} = Close_i$.
  2. **Nivel de Stop Loss:** $SL_{target} = P_{entry} + \Delta_{SL}$ (sobre el precio de entrada).
  3. **Nivel de Take Profit:** $TP_{target} = P_{entry} - \Delta_{TP}$ (bajo el precio de entrada).
- **Evaluaci?n de Salida y PnL:**
  - **Rama Favorable (TP):** Si en barra $t > i$, $Low_t \le TP_{target}$ y $High_t < SL_{target}$:
    $$ExitReason = \text{"TAKE\_PROFIT"}, \quad P_{exit} = TP_{target}$$
    $$PnL_R = \frac{P_{entry} - TP_{target}}{\Delta_{SL}} = \frac{\Delta_{TP}}{\Delta_{SL}} = +tp\_value > 0$$
    $$PnL_{USD} = (P_{entry} - TP_{target}) \times Contracts \times point\_value \times multiplier > 0$$
  - **Rama Desfavorable (SL):** Si en barra $t > i$, $High_t \ge SL_{target}$:
    $$ExitReason = \text{"STOP\_LOSS"}, \quad P_{exit} = SL_{target}$$
    $$PnL_R = \frac{P_{entry} - SL_{target}}{\Delta_{SL}} = \frac{-\Delta_{SL}}{\Delta_{SL}} = -1.0 < 0$$
    $$PnL_{USD} = -\Delta_{SL} \times Contracts \times point\_value \times multiplier = -Risk_{USD} < 0$$

---

### 4.3 Caso BOTH-03: Ausencia de Se?al (Preservaci?n de Capital)

- **Objetivo Cuantitativo:** Demostrar que cuando ninguna de las ramas evaluadas es verdadera ($L_{signal} = \text{False} \land S_{signal} = \text{False}$), el motor no abre posiciones espurias.
- **Precondiciones F?sicas:**
  - `direction = "BOTH"`.
  - Condici?n de ejemplo: $\text{EMA}(9) \text{ CROSS\_ABOVE } \text{EMA}(21)$.
  - En una barra de consolidaci?n horizontal donde no ocurre cruce alcista ni cruce bajista:
    $$L_{signal} = \text{False}, \quad S_{signal} = \text{False}$$
- **Din?mica y Verificaci?n:**
  $$\text{trigger\_entered} = \text{False}, \quad \text{in\_pos} = \text{False}$$
  $$\text{total\_trades} = 0, \quad \text{len(trades)} = 0, \quad PnL_{USD} = \$0.00$$
- **Criterio Fail-Closed:** Se proh?be terminantemente la existencia de operaciones forzadas o ejecuci?n por defecto.

---

### 4.4 Caso BOTH-04: Conflicto Simult?neo e Indeterminaci?n de Se?al

- **Objetivo Cuantitativo:** Formalizar la pol?tica institucional Fail-Closed ante colisiones simult?neas donde ambas ramas se eval?an como `True` en la misma barra ($L_{signal} = \text{True} \land S_{signal} = \text{True}$).
- **Escenario Cuantitativo:**
  - Puede ocurrir en ?rboles con operadores `OR` complejos o indicadores multitemporales contradictorios.
  - Ejemplo: $\text{Cond}_1 = (\text{RSI} < 30 \lor \text{RSI} > 70)$. En r?gimen de sobrecompra $\text{RSI} = 75$, tanto la condici?n original como su inversi?n invertida pueden evaluar positivo en subramas disyuntivas mal formuladas.
- **Pol?tica Institucional Determinista (Zero-Guess / Zero-Optimism):**
  - Ante ambig?edad direccional, el motor **NO DEBE** elegir aleatoriamente ni favorecer a `LONG`.
  - La indeterminaci?n produce la anulaci?n inmediata de la entrada:
    $$\text{if } (L_{signal} \land S_{signal}) \implies \text{trigger\_entered} = \text{False}$$
- **Verificaci?n:**
  $$\text{total\_trades} = 0, \quad \text{trades} = []$$

---

## 5. Especificaci?n de Sizing Instrument-Aware: CME NQ vs BTCUSDT

El motor de ejecuci?n cu?ntico implementa el dimensionamiento exacto de contratos vinculado a la microestructura can?nica registrada en `CANONICAL_COST_REGISTRY`:

$$\text{Profile}(sym) = \langle point\_value, contract\_multiplier, tick\_size, taker\_fee, spread \rangle$$

### 5.1 F?rmulas Matem?ticas de Sizing

1. **Riesgo Monetario Total Autorizado ($Risk_{USD}$):**
   $$Risk_{USD} = \begin{cases} 
   \text{account\_equity\_usd} \times \left(\frac{\text{risk\_val}}{100.0}\right) & \text{si } sizing\_type = \text{RISK\_PCT\_EQUITY} \\
   \text{risk\_val} & \text{si } sizing\_type = \text{FIXED\_USD}
   \end{cases}$$

2. **Riesgo Monetario por Contrato Unitario ($RiskPerContract_{USD}$):**
   $$RiskPerContract_{USD} = \Delta_{SL} \times point\_value \times contract\_multiplier$$

3. **C?lculo Determinista de Contratos ($Contracts$):**
   $$Contracts = \frac{Risk_{USD}}{RiskPerContract_{USD}} = \frac{Risk_{USD}}{\Delta_{SL} \times point\_value \times contract\_multiplier}$$

4. **PnL Monetario en Liquidaci?n ($PnL_{USD}$):**
   $$PnL_{USD} = \text{DirectionSign} \times (P_{exit} - P_{entry}) \times point\_value \times contract\_multiplier \times Contracts$$
   *Donde $\text{DirectionSign} = +1$ para LONG y $-1$ para SHORT.*

---

### 5.2 Demostraci?n Num?rica Comparativa: Futuros CME NQ vs Cripto BTCUSDT

#### Par?metros del Entorno de Prueba:
- **Capital de la Cuenta ($Equity$):** $\$100,000.00\text{ USD}$.
- **Porcentaje de Riesgo ($risk\_val$):** $1.0\% \implies Risk_{USD} = \$1,000.00\text{ USD}$.
- **Distancia de Stop Loss ($\Delta_{SL}$):** $50.0\text{ puntos}$ de precio.
- **M?ltiplo de Take Profit ($tp\_value$):** $2.0\text{ R} \implies \Delta_{TP} = 100.0\text{ puntos}$ de precio.

---

#### Demostraci?n A: Futuros CME NQ (E-mini Nasdaq 100)
- **Microestructura:** $point\_value = \$20.00$, $contract\_multiplier = 1.0$, $tick\_size = 0.25$.
- **C?lculo de Riesgo por Contrato:**
  $$RiskPerContract_{NQ} = 50.0\text{ pts} \times \$20.00/\text{pt} \times 1.0 = \$1,000.00\text{ USD/contrato}$$
- **Dimensionamiento de Posici?n:**
  $$Contracts_{NQ} = \frac{\$1,000.00}{\$1,000.00} = \mathbf{1.0\text{ contrato}}$$
- **Verificaci?n de PnL en Stop Loss (SL alcanzado en $-\Delta_{SL} = -50.0\text{ pts}$):**
  $$PnL_{USD} = (-50.0) \times \$20.00 \times 1.0 \times 1.0 = \mathbf{-\$1,000.00\text{ USD}} \quad (PnL_R = -1.0R)$$
- **Verificaci?n de PnL en Take Profit (TP alcanzado en $+\Delta_{TP} = +100.0\text{ pts}$):**
  $$PnL_{USD} = (+100.0) \times \$20.00 \times 1.0 \times 1.0 = \mathbf{+\$2,000.00\text{ USD}} \quad (PnL_R = +2.0R)$$

---

#### Demostraci?n B: Cripto Perpetuo BTCUSDT (Binance / BingX Perp)
- **Microestructura:** $point\_value = \$1.00$, $contract\_multiplier = 1.0$, $tick\_size = 0.10$.
- **C?lculo de Riesgo por Contrato:**
  $$RiskPerContract_{BTC} = 50.0\text{ pts} \times \$1.00/\text{pt} \times 1.0 = \$50.00\text{ USD/contrato}$$
- **Dimensionamiento de Posici?n:**
  $$Contracts_{BTC} = \frac{\$1,000.00}{\$50.00} = \mathbf{20.0\text{ contratos (BTC)}}$$
- **Verificaci?n de PnL en Stop Loss (SL alcanzado en $-\Delta_{SL} = -50.0\text{ pts}$):**
  $$PnL_{USD} = (-50.0) \times \$1.00 \times 1.0 \times 20.0 = \mathbf{-\$1,000.00\text{ USD}} \quad (PnL_R = -1.0R)$$
- **Verificaci?n de PnL en Take Profit (TP alcanzado en $+\Delta_{TP} = +100.0\text{ pts}$):**
  $$PnL_{USD} = (+100.0) \times \$1.00 \times 1.0 \times 20.0 = \mathbf{+\$2,000.00\text{ USD}} \quad (PnL_R = +2.0R)$$

---

#### Conclusi?n Cuantitativa del Eje de Sizing:
$$\mathbf{Risk_{USD}(NQ) \equiv Risk_{USD}(BTCUSDT) = \$1,000.00\text{ USD}}$$
$$\mathbf{PnL_{TP}(NQ) \equiv PnL_{TP}(BTCUSDT) = +\$2,000.00\text{ USD}}$$

Queda formalmente demostrado que el motor normaliza matem?ticamente el riesgo monetario real en funci?n de la microestructura del activo, erradicando por completo el fallo cr?tico de suponer $1\text{ punto} \equiv \$1\text{ USD}$.

---

## 6. Condiciones de Frontera Adicionales

### 6.1 Conflicto Intrabarra SL vs TP (Zero-Optimism)
- Si en una vela de alta volatilidad se satisface simult?neamente:
  - LONG: $Low_t \le SL_{target} \land High_t \ge TP_{target}$
  - SHORT: $High_t \ge SL_{target} \land Low_t \le TP_{target}$
- **Pol?tica Institucional:** Prioridad pesimista a Stop Loss.
  $$ExitReason = \text{"STOP\_LOSS"}, \quad PnL_R = -1.0R, \quad PnL_{USD} = -Risk_{USD}$$

### 6.2 L?mites de Sesi?n y Cierre EOD
- Si una barra $t$ se encuentra fuera de `SessionWindow.allowed_days` o del rango horario $[StartUTC, EndUTC]$:
  - Prohibida toda apertura de posici?n ($trigger\_entered = \text{False}$).
  - Si `close_at_eod == True` y la posici?n contin?a abierta, se fuerza el cierre en $P_{exit} = Close_t$ con $ExitReason = \text{"SESSION\_EOD"}$.

---

## 7. Invariantes y Criterios de Aceptaci?n para la Suite de Tests

Toda implementaci?n en `test_phase02_canonical_strategy.py` debe satisfacer estrictamente las siguientes aserciones invariantes:

1. **`assert t.direction in ["LONG", "SHORT"]`**: Toda operaci?n en modo `BOTH` debe registrar un?vocamente la direcci?n f?sica adoptada.
2. **`assert (t.exit_reason == "TAKE_PROFIT" and t.pnl_usd > 0) or (t.exit_reason == "STOP_LOSS" and t.pnl_usd < 0)`**: Consistencia de signo entre motivo de salida y PnL monetario.
3. **`assert abs(t.pnl_usd + Risk_USD) < 1e-6` para Stop Loss**: P?rdida acotada exactamente al riesgo programado sin desv?os por microestructura.
4. **`assert res_both03.total_trades == 0`**: Inacci?n determinista verificada ante ausencia de se?al.
5. **`assert res_both04.total_trades == 0`**: Neutralizaci?n verificada ante ambig?edad simult?nea.

