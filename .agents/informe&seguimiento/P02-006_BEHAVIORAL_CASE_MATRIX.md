# P02-006 BEHAVIORAL CASE MATRIX ? PHASE 02 BEHAVIORAL RUNTIME PROOF
**Orden:** `AG2-P02-006`  
**Fase:** `PHASE 02 ? UNIVERSAL RUNTIME CONTRACT CLOSURE`  
**Versi?n de Motor:** `v5.4.0` (SSOT Can?nico)  
**Versi?n de Pol?tica:** `v5.4.0` (SSOT Can?nico)  
**Doctrina:** `ZERO-MOCKS ? REAL-ONLY ? DETERMINISTIC ? NO-LOOKAHEAD ? PROVENANCE-LOCKED ? FAIL-CLOSED ? ZERO-OPTIMISM`  
**Fecha UTC:** `2026-08-25T17:15:00Z`

---

## 1. Resumen y Prop?sito

El presente documento establece la matriz exhaustiva de casos de prueba f?sica de comportamiento (*Behavioral Runtime Cases*) requerida para validar la ejecuci?n universal de estrategias cuantitativas (`CanonicalStrategy`) dentro del motor `CanonicalRuntimeAdapter`.

Cada caso define las precondiciones, disparadores, ecuaciones de ejecuci?n, gesti?n de salidas y criterios de verificaci?n deterministas sin suposiciones complacientes.

---

## 2. Matriz de Casos F?sicos de Comportamiento

| ID Caso | Escenario Cuantitativo | Direcci?n | Activo / Microestructura | Condici?n de Salida | PnL R Esperado | PnL USD Esperado | Regla Fail-Closed / Criterio de Verificaci?n |
|---|---|---|---|---|---|---|---|
| **BC-01** | Long Favorable (Take Profit) | `LONG` | NQ (Point=$20, Mult=1.0) | $High_t \ge TP_{target}$ | $PnL_R = +tp\_value$ ($>0$) | $PnL_{USD} = \Delta_{TP} \times C \times 20.0 > 0$ | $ExitPrice = TP_{target}$, $ExitReason = \text{"TAKE\_PROFIT"}$. |
| **BC-02** | Long Desfavorable (Stop Loss) | `LONG` | ES (Point=$50, Mult=1.0) | $Low_t \le SL_{target}$ | $PnL_R = -1.0$ ($<0$) | $PnL_{USD} = -\Delta_{SL} \times C \times 50.0 < 0$ | $ExitPrice = SL_{target}$, $ExitReason = \text{"STOP\_LOSS"}$. |
| **BC-03** | Short Favorable (Take Profit) | `SHORT` | BTCUSDT (Point=$1, Mult=1.0) | $Low_t \le TP_{target}$ | $PnL_R = +tp\_value$ ($>0$) | $PnL_{USD} = \Delta_{TP} \times C \times 1.0 > 0$ | $ExitPrice = TP_{target}$, $ExitReason = \text{"TAKE\_PROFIT"}$. |
| **BC-04** | Short Desfavorable (Stop Loss) | `SHORT` | EURUSD (Point=$10, Mult=100k) | $High_t \ge SL_{target}$ | $PnL_R = -1.0$ ($<0$) | $PnL_{USD} = -\Delta_{SL} \times C \times 100k < 0$ | $ExitPrice = SL_{target}$, $ExitReason = \text{"STOP\_LOSS"}$. |
| **BC-05** | Bidireccional BOTH en Dataset Separado | `BOTH` | NQ & BTCUSDT | Disparo sim?trico | $PnL_R \in \mathbb{R}$ | PnL sim?trico exacto | Genera trades reales `LONG` en reg?menes alcistas y `SHORT` en reg?menes bajistas. |
| **BC-06** | Sizing Instrument-Aware | Cualquier | NQ / ES / EURUSD / CL | N/A | N/A | $Risk_{USD}$ exacto | $Contracts = \frac{Risk_{USD}}{\Delta_{SL} \times point\_value \times multiplier}$. Cero asunci?n $1pt=\$1$. |
| **BC-07** | Multi-Positioning Control | Cualquier | Cualquier | Concurrencia de triggers | N/A | N/A | $max\_open\_positions=1$: ignora entradas adicionales en posici?n. $max\_open\_positions > 1$: Fail-Closed si no soportado. |
| **BC-08** | Sesi?n Horaria Estricta | Cualquier | Cualquier | $t \notin [Start, End]$ | N/A | N/A | No permite aperturas fuera de ventana ni en d?as no autorizados (`allowed_days`). |
| **BC-09** | Sesi?n Cruzando Medianoche | Cualquier | CME Futures (18:00 a 09:00 UTC) | $t \notin [22:00, 04:00]$ | N/A | N/A | Soporta $Start > End$ v?a disyunci?n ($t \ge Start \lor t \le End$). |
| **BC-10** | Liquidaci?n Forzada EOD | Cualquier | Cualquier | Fin de sesi?n con `close_at_eod=True` | $PnL_R = \frac{\Delta_{exit}}{\Delta_{SL}}$ | PnL a precio de cierre $Close_t$ | Cierra posici?n a $Close_t$ con $ExitReason = \text{"SESSION\_EOD"}$. |
| **BC-11** | Conflicto Intrabarra SL vs TP | `LONG` / `SHORT` | Cualquier | $Low_t \le SL \land High_t \ge TP$ | $PnL_R = -1.0$ | $PnL_{USD} = -Risk_{USD}$ | Prioridad institucional pesimista: Stop Loss obligatorio (*Zero-Optimism*). |
| **BC-12** | Trailing Breakeven & Time Stop | `LONG` / `SHORT` | Cualquier | $\Delta P \ge \Delta_{SL} \cdot trail\_r \lor bars \ge N$ | $PnL_R \ge 0.0$ / Variable | PnL a $P_{entry}$ o $Close_t$ | Mueve SL a $P_{entry}$ al tocar $trail\_after\_r$ o cierra tras $time\_stop\_bars$. |

---

## 3. Especificaci?n Detallada de Comportamiento por Eje

### 3.1 Eje Direccional (LONG, SHORT, BOTH)

#### 1. Caso LONG (BC-01 y BC-02)
- **Precondici?n:** `RuleTree.direction == "LONG"`. Condici?n de entrada evaluada como `True` en la barra $i$.
- **Precio de Entrada:** $P_{entry} = Close_i$.
- **Nivel de Stop Loss:** $SL_{target} = P_{entry} - \Delta_{SL}$.
- **Nivel de Take Profit:** $TP_{target} = P_{entry} + \Delta_{TP}$.
- **Evaluaci?n de Barras Posteriores ($t > i$):**
  - **Favorable (TP):** Si $High_t \ge TP_{target}$ (y no toca SL previamente), salida en $P_{exit} = TP_{target}$.
    $$PnL_{R} = \frac{TP_{target} - P_{entry}}{\Delta_{SL}} = \frac{\Delta_{TP}}{\Delta_{SL}} = +tp\_value$$
    $$PnL_{USD} = (TP_{target} - P_{entry}) \times Contracts \times point\_value \times contract\_multiplier$$
  - **Desfavorable (SL):** Si $Low_t \le SL_{target}$, salida en $P_{exit} = SL_{target}$.
    $$PnL_{R} = \frac{SL_{target} - P_{entry}}{\Delta_{SL}} = \frac{-\Delta_{SL}}{\Delta_{SL}} = -1.0$$
    $$PnL_{USD} = -\Delta_{SL} \times Contracts \times point\_value \times contract\_multiplier = -Risk_{USD}$$

#### 2. Caso SHORT (BC-03 y BC-04)
- **Precondici?n:** `RuleTree.direction == "SHORT"`. Condici?n de entrada evaluada como `True` en la barra $i$.
- **Precio de Entrada:** $P_{entry} = Close_i$.
- **Nivel de Stop Loss:** $SL_{target} = P_{entry} + \Delta_{SL}$.
- **Nivel de Take Profit:** $TP_{target} = P_{entry} - \Delta_{TP}$.
- **Evaluaci?n de Barras Posteriores ($t > i$):**
  - **Favorable (TP):** Si $Low_t \le TP_{target}$, salida en $P_{exit} = TP_{target}$.
    $$PnL_{R} = \frac{P_{entry} - TP_{target}}{\Delta_{SL}} = \frac{\Delta_{TP}}{\Delta_{SL}} = +tp\_value$$
    $$PnL_{USD} = (P_{entry} - TP_{target}) \times Contracts \times point\_value \times contract\_multiplier$$
  - **Desfavorable (SL):** Si $High_t \ge SL_{target}$, salida en $P_{exit} = SL_{target}$.
    $$PnL_{R} = \frac{P_{entry} - SL_{target}}{\Delta_{SL}} = \frac{-\Delta_{SL}}{\Delta_{SL}} = -1.0$$
    $$PnL_{USD} = -\Delta_{SL} \times Contracts \times point\_value \times contract\_multiplier = -Risk_{USD}$$

#### 3. Caso BOTH Bidireccional (BC-05)
- **Precondici?n:** `RuleTree.direction == "BOTH"`.
- **Comportamiento:** Permite ejecutar operaciones tanto LONG como SHORT dependiendo de la condici?n disparada o del r?gimen del mercado. En datasets alcistas produce ejecuciones LONG verificables y en datasets bajistas ejecuciones SHORT verificables, validando la simetr?a matem?tica completa del motor.

---

### 3.2 Eje de Sizing Instrument-Aware (BC-06)

El motor cuantitativo no asume que 1 punto equivale a 1 USD. Integra de manera mandatoria los par?metros de microestructura desde `CANONICAL_COST_REGISTRY`:

$$\text{Profile}(sym) = \langle point\_value, contract\_multiplier, tick\_size, taker\_fee, spread \rangle$$

#### Conversi?n de Riesgo USD a Contratos:
1. **Riesgo Total en USD ($Risk_{USD}$):**
   $$Risk_{USD} = \begin{cases} \text{account\_equity\_usd} \times \left(\frac{risk\_val}{100.0}\right) & \text{si } sizing\_type = \text{RISK\_PCT\_EQUITY} \\ risk\_val & \text{si } sizing\_type = \text{FIXED\_USD} \end{cases}$$

2. **Riesgo por Contrato ($RiskPerContract_{USD}$):**
   $$RiskPerContract_{USD} = \Delta_{SL} \times point\_value \times contract\_multiplier$$
   *Donde $\Delta_{SL} > 0$ es la distancia al Stop Loss en puntos de precio.*

3. **N?mero de Contratos ($Contracts$):**
   $$Contracts = \begin{cases} risk\_val & \text{si } sizing\_type = \text{FIXED\_CONTRACTS} \\ \frac{Risk_{USD}}{\Delta_{SL} \times point\_value \times contract\_multiplier} & \text{si } sizing\_type \in \{\text{RISK\_PCT\_EQUITY}, \text{FIXED\_USD}\} \end{cases}$$

4. **Regla Fail-Closed:**
   - Si el s?mbolo no se encuentra registrado en `CANONICAL_COST_REGISTRY`, lanza `MissingCostModelError` (Doctrina Zero-Default).
   - Si $\Delta_{SL} \le 0$, lanza `InvalidStrategyError` de inmediato.
   - Si $point\_value \le 0$ o $contract\_multiplier \le 0$, lanza `InvalidStrategyError`.

---

### 3.3 Eje de Multi-Positioning (BC-07)

1. **Soporte de 1 Posici?n ($max\_open\_positions = 1$):**
   - Si el sistema ya mantiene una posici?n abierta (`in_pos == True`), los nuevos disparadores de entrada son estrictamente ignorados hasta que la posici?n activa se cierre por SL, TP, Time Stop o EOD.
2. **Posiciones M?ltiples ($max\_open\_positions > 1$):**
   - El motor `v5.4.0` de runtime actual opera bajo el contrato de ejecuci?n determinista de *single-ticket / single-instrument*.
   - Si una estrategia declara $max\_open\_positions > 1$ y el runtime no dispone de soporte multi-ticket activado en su contexto de compilaci?n, el sistema aplica la pol?tica institucional **Fail-Closed**:
     $$\text{if } max\_open\_positions > 1 \implies \text{Lanzar } InvalidStrategyError(\text{"MULTI\_POSITION\_UNSUPPORTED\_IN\_RUNTIME\_V540"})$$
   - Esto evita acumulaciones descontroladas de margen no respaldadas por el motor de liquidaci?n.

---

### 3.4 Eje de Sesi?n Horaria y D?as Permitidos (BC-08 a BC-10)

#### 1. Restricci?n por D?as Permitidos (`allowed_days`):
- Sea $Weekday_{UTC}(t) \in [0, 6]$ (donde $0 = \text{Lunes}$, $6 = \text{Domingo}$).
- Si $Weekday_{UTC}(t) \notin session\_config.allowed\_days$, se rechaza toda apertura de posici?n.
- Si `allowed_days` est? ausente o vac?o, falla cerrado con `InvalidStrategyError`.

#### 2. Ventana Horaria Intra-d?a y Cruce de Medianoche:
Sean $T_{cur} = Hour \times 60 + Minute$, $T_{start} = StartHour \times 60 + StartMinute$ y $T_{end} = EndHour \times 60 + EndMinute$:
$$\text{IsWithinSession}(T_{cur}) = \begin{cases} T_{start} \le T_{cur} \le T_{end} & \text{si } T_{start} \le T_{end} \text{ (Sesi?n intrad?a est?ndar)} \\ (T_{cur} \ge T_{start}) \lor (T_{cur} \le T_{end}) & \text{si } T_{start} > T_{end} \text{ (Sesi?n que cruza medianoche)} \end{cases}$$

#### 3. Liquidaci?n Forzada al Cierre de Sesi?n (`close_at_eod`):
- Si $session\_config.close\_at\_eod == True$ y la barra actual cae fuera de la sesi?n horaria permitida ($\text{IsWithinSession}(t) == False$):
  - La posici?n se liquida inmediatamente a $P_{exit} = Close_t$.
  - Motivo de salida: $ExitReason = \text{"SESSION\_EOD"}$.

---

### 3.5 Eje de Resoluci?n de Conflictos Intrabarra (BC-11)

- **Escenario:** En velas de alta volatilidad donde tanto el nivel de Stop Loss como el de Take Profit quedan contenidos dentro del rango $[Low_t, High_t]$:
  - LONG: $Low_t \le SL_{target}$ y $High_t \ge TP_{target}$.
  - SHORT: $High_t \ge SL_{target}$ y $Low_t \le TP_{target}$.
- **Pol?tica Institucional Determinista:** Prioridad obligatoria al Stop Loss (*Zero-Optimism / Pessimistic Execution*).
- **Ejecuci?n:** Se registra la salida como `STOP_LOSS` a $P_{exit} = SL_{target}$, garantizando que el backtest nunca sobreestime el rendimiento en situaciones de ambig?edad de orden de ticks.

---

### 3.6 Eje de Trailing Stop y Time Stop (BC-12)

1. **Trailing Stop / Mover a Breakeven (`trail_after_r`):**
   - LONG: Si $\max_{k \in [entry, t]}(High_k) - P_{entry} \ge \Delta_{SL} \times trail\_after\_r \implies SL_{active} = P_{entry}$.
   - SHORT: Si $P_{entry} - \min_{k \in [entry, t]}(Low_k) \ge \Delta_{SL} \times trail\_after\_r \implies SL_{active} = P_{entry}$.
2. **Time Stop (`time_stop_bars`):**
   - Si $(t - entry\_idx) \ge time\_stop\_bars$ y no se ha alcanzado ni SL ni TP, la posici?n se cierra a $P_{exit} = Close_t$ con $ExitReason = \text{"TIME\_STOP"}$.

