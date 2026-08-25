# P02-008 BEHAVIORAL CASE MATRIX — FINAL INDEPENDENT CERTIFICATION OF CANONICAL RUNTIME SEMANTICS
**Orden:** `AG2-P02-008`  
**Fase:** `PHASE 02 — CANONICAL STRATEGY + VERSION GOVERNANCE + RUNTIME SEMANTIC CONTRACT (FINAL INDEPENDENT CERTIFICATION)`  
**Versión de Motor SSOT:** `5.4.0` (`services/engine_version.py`)  
**Versión de Política SSOT:** `5.4.0` (`services/engine_version.py`)  
**Subagente Responsable:** `QUANT / REPRODUCIBILITY`  
**Doctrina Institucional:** `ZERO-MOCKS · REAL-ONLY · DETERMINISTIC · NO-LOOKAHEAD · PROVENANCE-LOCKED · FAIL-CLOSED · ZERO-OPTIMISM`  
**Fecha UTC:** `2026-08-25T19:42:33Z`

---

## 1. Resumen Ejecutivo y Propósito Cuantitativo

El presente documento constituye la **Matriz de Casos de Comportamiento Físico en Runtime (`P02-008_BEHAVIORAL_CASE_MATRIX.md`)** para la certificación independiente y cierre definitivo de la **Fase 02**.

Su propósito es formalizar y demostrar matemáticamente el cumplimiento estricto de las especificaciones de ejecución determinista en `CanonicalRuntimeAdapter` (`services/execution/canonical_runtime_adapter.py`) y sus contratos asociados (`contracts/canonical_strategy.py`, `contracts/canonical_execution.py`), cubriendo los cuatro ejes conductuales obligatorios:

1. **Semántica Bidireccional Canónica (`BOTH`):**
   - **Caso BOTH-A:** Activación exclusiva de la rama LONG ($L_{sig}=1, S_{sig}=0$) $\longrightarrow$ Ejecución física LONG real y verificación analítica de PnL.
   - **Caso BOTH-B:** Activación exclusiva de la rama SHORT ($L_{sig}=0, S_{sig}=1$) $\longrightarrow$ Ejecución física SHORT real y verificación analítica de PnL.
   - **Caso BOTH-C:** Disparo simultáneo de ambas ramas ($L_{sig}=1, S_{sig}=1$) $\longrightarrow$ Neutralización determinista Fail-Closed (0 trades, cero suposiciones, preservación total del capital).
   - **Caso BOTH-D:** Ausencia de disparo en ambas ramas ($L_{sig}=0, S_{sig}=0$) $\longrightarrow$ Inacción determinista (0 trades, 0 operaciones espurias).
2. **Dimensionamiento Cuantitativo Instrument-Aware:**
   - Formalización matemática del dimensionamiento en activos con microestructura asimétrica: Futuros CME NQ ($point\_value = \$20.00/\text{punto}$) vs Cripto Perpetuo BTCUSDT ($point\_value = \$1.00/\text{punto}$), demostrando la conservación exacta del riesgo monetario en USD ($Risk_{USD} = \$1,000.00$).
3. **Resolución de Conflicto Intrabarra Pesimista (*Zero-Optimism*):**
   - Regla estricta de prioridad Stop Loss ($SL > TP$) ante velas de alta volatilidad donde se tocan ambos extremos en la misma barra.
4. **Condiciones de Frontera y Rechazo Fail-Closed:**
   - Clasificación explícita de capacidades `SUPPORTED_AND_EXECUTED` vs `UNSUPPORTED_FAIL_CLOSED` (e.g. `max_open_positions > 1`, cuentas con capital $\le 0$, parámetros de indicadores faltantes o hashes semánticos alterados).

---

## 2. Matriz Cuantitativa Maestra de Casos Físicos de Comportamiento

| ID Caso | Escenario Cuantitativo | Dirección AST | Ramas Evaluadas ($L_{sig}, S_{sig}$) | Microestructura del Instrumento | Condición de Salida F Física | PnL R Teórico | PnL USD Teórico | Regla Fail-Closed & Criterio de Verificación |
|---|---|:---:|:---:|---|---|:---:|:---:|---|
| **BOTH-A** | Señal LONG Exclusiva | `BOTH` | $L_{sig}=1, S_{sig}=0$ | CME NQ ($pt=\$20, mult=1.0$) | $High_t \ge TP_{tgt}$ ó $Low_t \le SL_{tgt}$ | $TP: +2.0R$ / $SL: -1.0R$ | $TP: +\$2,000.00$ / $SL: -\$1,000.00$ | Apertura física LONG en $Close_i$. Salida real en TP ($PnL>0$) o SL ($PnL<0$). |
| **BOTH-B** | Señal SHORT Exclusiva | `BOTH` | $L_{sig}=0, S_{sig}=1$ | BTCUSDT ($pt=\$1, mult=1.0$) | $Low_t \le TP_{tgt}$ ó $High_t \ge SL_{tgt}$ | $TP: +2.0R$ / $SL: -1.0R$ | $TP: +\$2,000.00$ / $SL: -\$1,000.00$ | Apertura física SHORT en $Close_i$. Salida real en TP ($PnL>0$) o SL ($PnL<0$). |
| **BOTH-C** | Conflicto Simultáneo (Ambas Ramas) | `BOTH` | $L_{sig}=1, S_{sig}=1$ | Cualquier Instrumento | N/A (Indeterminación) | $0.0R$ | $\$0.00$ | Neutralización Fail-Closed: $trigger\_entered = \text{False}$, $0\text{ trades}$. Cero coin-flip. |
| **BOTH-D** | Ausencia Total de Señal | `BOTH` | $L_{sig}=0, S_{sig}=0$ | Cualquier Instrumento | N/A (Inacción) | $0.0R$ | $\$0.00$ | Preservación de capital: $total\_trades = 0$. Cero aperturas espurias. |
| **SIZING-NQ** | Sizing Futuros CME NQ | Cualquier | Disparo válido | NQ ($point\_value = 20.0$) | SL alcanzado ($\Delta_{SL}=50\text{ pts}$) | $-1.0R$ | $-\$1,000.00$ | $Contracts = \frac{\$1,000}{50 \times 20 \times 1} = 1.0$. Pérdida acotada exactamente a $\$1,000$. |
| **SIZING-BTC**| Sizing Cripto BTCUSDT | Cualquier | Disparo válido | BTCUSDT ($point\_value = 1.0$)| SL alcanzado ($\Delta_{SL}=50\text{ pts}$) | $-1.0R$ | $-\$1,000.00$ | $Contracts = \frac{\$1,000}{50 \times 1 \times 1} = 20.0$. Pérdida acotada exactamente a $\$1,000$. |
| **INTRABAR-L**| Conflicto Intrabarra LONG | `LONG` / `BOTH` | Disparo LONG | NQ / BTCUSDT | $Low_t \le SL \land High_t \ge TP$ | $-1.0R$ | $-Risk_{USD}$ | Prioridad institucional pesimista (*Zero-Optimism*): Ejecuta STOP_LOSS. |
| **INTRABAR-S**| Conflicto Intrabarra SHORT | `SHORT` / `BOTH`| Disparo SHORT | NQ / BTCUSDT | $High_t \ge SL \land Low_t \le TP$ | $-1.0R$ | $-Risk_{USD}$ | Prioridad institucional pesimista (*Zero-Optimism*): Ejecuta STOP_LOSS. |
| **SESSION-OUT**| Barra Fuera de Sesión | Cualquier | Disparo fuera de ventana | Futuros CME / Forex | $t \notin SessionWindow$ | $0.0R$ | $\$0.00$ | Bloqueo estricto por filtro de horario o día no permitido (`allowed_days`). |
| **SESSION-EOD**| Cierre de Fin de Día (EOD) | Cualquier | Posición activa al cierre | Futuros CME | $t \ge EndTime \land close\_at\_eod$ | Realizado a $Close_t$ | Realizado a $Close_t$ | Liquidación obligatoria al precio de cierre con motivo `SESSION_EOD`. |
| **MAX-POS-FAIL**| Concurrencia No Soportada | Cualquier | $max\_open_positions > 1$| Cualquier Instrumento | N/A | N/A | N/A | Rechazo inmediato `InvalidStrategyError` (`UNSUPPORTED_FAIL_CLOSED`). |
| **INTEG-FAIL** | Alteración de Hash Semántico | Cualquier | Mutación no declarada | Cualquier Instrumento | N/A | N/A | N/A | Rechazo inmediato `StrategyIntegrityError` (Fail-Closed). |

---

## 3. Formalización Matemática y Lógica del Motor Canónico

### 3.1 Estructura Declarativa del Árbol de Reglas (`RuleTree`)

En la arquitectura canónica de la Fase 02, una estrategia con `direction = "BOTH"` prohíbe terminantemente cualquier heurística sintética de inversión de operadores. Ambas ramas deben ser especificadas explícitamente en el AST:

$$\mathcal{R}_{BOTH} = \big\langle \text{LogicalOp}, \mathcal{C}_{LONG}, \mathcal{C}_{SHORT} \big\rangle$$

Donde:
- $\mathcal{C}_{LONG} = \{c_{L,1}, c_{L,2}, \dots, c_{L,m}\}$: Conjunto explícito de condiciones para compras.
- $\mathcal{C}_{SHORT} = \{c_{S,1}, c_{S,2}, \dots, c_{S,k}\}$: Conjunto explícito de condiciones para ventas.

Si $\mathcal{C}_{LONG} = \emptyset$ o $\mathcal{C}_{SHORT} = \emptyset$, el validador pydantic lanza `InvalidStrategyError` de forma inmediata (**Fail-Closed**).

### 3.2 Evaluación de Señales Discretas y Función de Decisión

En cada barra $i \ge 0$, sobre la serie histórica de precios $\mathcal{B}_{0:i}$:

$$L_{signal}(i) = \Phi(\mathcal{C}_{LONG}, \text{LogicalOp}, \mathcal{B}_{0:i})$$
$$S_{signal}(i) = \Phi(\mathcal{C}_{SHORT}, \text{LogicalOp}, \mathcal{B}_{0:i})$$

Donde el operador de composición lógica $\Phi$ evalúa:
$$\Phi(\mathcal{C}, \text{op}, \mathcal{B}) = \begin{cases} 
\bigwedge_{c \in \mathcal{C}} \text{EvalNode}(c, \mathcal{B}) & \text{si } \text{op} = \text{AND} \\
\bigvee_{c \in \mathcal{C}} \text{EvalNode}(c, \mathcal{B}) & \text{si } \text{op} = \text{OR}
\end{cases}$$

La función determinista de disparo $\text{TriggerDecision}(i)$ se define rigurosamente como:

$$\text{TriggerDecision}(i) = \begin{cases} 
\mathbf{ENTER\_LONG} & \text{si } L_{signal}(i) = \text{True} \land S_{signal}(i) = \text{False} \quad (\textbf{Caso BOTH-A}) \\
\mathbf{ENTER\_SHORT} & \text{si } S_{signal}(i) = \text{True} \land L_{signal}(i) = \text{False} \quad (\textbf{Caso BOTH-B}) \\
\mathbf{NO\_ACTION} & \text{si } L_{signal}(i) = \text{True} \land S_{signal}(i) = \text{True} \quad (\textbf{Caso BOTH-C: Neutralización}) \\
\mathbf{NO\_ACTION} & \text{si } L_{signal}(i) = \text{False} \land S_{signal}(i) = \text{False} \quad (\textbf{Caso BOTH-D: Inacción})
\end{cases}$$

---

## 4. Especificación Detallada de los Casos Físicos

### 4.1 Caso BOTH-A: Solo Rama LONG Dispara

- **Objetivo Cuantitativo:** Demostrar la apertura real de una posición `LONG` cuando únicamente la rama compradora se cumple en modo `BOTH`, calculando con exactitud los niveles de salida y el PnL.
- **Precondiciones del AST:**
  - `direction = "BOTH"`, `logic = LogicalOp.AND`.
  - $\mathcal{C}_{LONG}$: $\text{EMA}(5) \text{ CROSS\_ABOVE } \text{EMA}(15)$.
  - $\mathcal{C}_{SHORT}$: $\text{EMA}(5) \text{ CROSS\_BELOW } \text{EMA}(15)$.
- **Estado de Evaluación en Barra $i$:**
  - En la barra $i$, $\text{EMA}_5(i-1) \le \text{EMA}_{15}(i-1)$ y $\text{EMA}_5(i) > \text{EMA}_{15}(i) \implies L_{signal}(i) = \text{True}$.
  - Simultáneamente, $\text{EMA}_5(i) < \text{EMA}_{15}(i) \implies \text{False} \implies S_{signal}(i) = \text{False}$.
  - Decisión: $\text{TriggerDecision}(i) = \mathbf{ENTER\_LONG}$.
- **Dinámica de Ejecución y Niveles:**
  - $P_{entry} = Close_i = 18,000.00\text{ pts}$.
  - $\Delta_{SL} = 50.00\text{ pts} \implies SL_{target} = 18,000.00 - 50.00 = 17,950.00\text{ pts}$.
  - $\Delta_{TP} = 100.00\text{ pts} \implies TP_{target} = 18,000.00 + 100.00 = 18,100.00\text{ pts}$.
- **Liquidación y Verificación de PnL:**
  - Si en barra $t > i$, $High_t \ge 18,100.00$ y $Low_t > 17,950.00$:
    $$ExitReason = \text{"TAKE\_PROFIT"}, \quad P_{exit} = 18,100.00$$
    $$PnL_R = \frac{18,100.00 - 18,000.00}{50.00} = \mathbf{+2.0R}$$
    $$PnL_{USD} = (18,100.00 - 18,000.00) \times 20.0 \times 1.0 \times 1.0 = \mathbf{+\$2,000.00\text{ USD}}$$
  - Si en barra $t > i$, $Low_t \le 17,950.00$:
    $$ExitReason = \text{"STOP\_LOSS"}, \quad P_{exit} = 17,950.00$$
    $$PnL_R = \frac{17,950.00 - 18,000.00}{50.00} = \mathbf{-1.0R}$$
    $$PnL_{USD} = (17,950.00 - 18,000.00) \times 20.0 \times 1.0 \times 1.0 = \mathbf{-\$1,000.00\text{ USD}}$$

---

### 4.2 Caso BOTH-B: Solo Rama SHORT Dispara

- **Objetivo Cuantitativo:** Demostrar la apertura real de una posición `SHORT` cuando únicamente la rama vendedora se cumple en modo `BOTH`, calculando con exactitud la geometría inversa de SL/TP y PnL.
- **Precondiciones del AST:**
  - `direction = "BOTH"`, `logic = LogicalOp.AND`.
  - $\mathcal{C}_{LONG}$: $\text{EMA}(5) \text{ CROSS\_ABOVE } \text{EMA}(15)$.
  - $\mathcal{C}_{SHORT}$: $\text{EMA}(5) \text{ CROSS\_BELOW } \text{EMA}(15)$.
- **Estado de Evaluación en Barra $i$:**
  - En la barra $i$, $\text{EMA}_5(i-1) \ge \text{EMA}_{15}(i-1)$ y $\text{EMA}_5(i) < \text{EMA}_{15}(i) \implies S_{signal}(i) = \text{True}$.
  - $L_{signal}(i) = \text{False}$.
  - Decisión: $\text{TriggerDecision}(i) = \mathbf{ENTER\_SHORT}$.
- **Dinámica de Ejecución y Niveles (Activo BTCUSDT a \$1/pt):**
  - $P_{entry} = Close_i = 60,000.00\text{ USD}$.
  - $\Delta_{SL} = 50.00\text{ pts} \implies SL_{target} = 60,000.00 + 50.00 = 60,050.00\text{ USD}$ (por encima).
  - $\Delta_{TP} = 100.00\text{ pts} \implies TP_{target} = 60,000.00 - 100.00 = 59,900.00\text{ USD}$ (por debajo).
  - $Contracts = 20.0\text{ BTC}$.
- **Liquidación y Verificación de PnL:**
  - Si en barra $t > i$, $Low_t \le 59,900.00$ y $High_t < 60,050.00$:
    $$ExitReason = \text{"TAKE\_PROFIT"}, \quad P_{exit} = 59,900.00$$
    $$PnL_R = \frac{60,000.00 - 59,900.00}{50.00} = \mathbf{+2.0R}$$
    $$PnL_{USD} = (60,000.00 - 59,900.00) \times 1.0 \times 1.0 \times 20.0 = \mathbf{+\$2,000.00\text{ USD}}$$
  - Si en barra $t > i$, $High_t \ge 60,050.00$:
    $$ExitReason = \text{"STOP\_LOSS"}, \quad P_{exit} = 60,050.00$$
    $$PnL_R = \frac{60,000.00 - 60,050.00}{50.00} = \mathbf{-1.0R}$$
    $$PnL_{USD} = (60,000.00 - 60,050.00) \times 1.0 \times 1.0 \times 20.0 = \mathbf{-\$1,000.00\text{ USD}}$$

---

### 4.3 Caso BOTH-C: Disparo Simultáneo de Ambas Ramas (Neutralización Canónica)

- **Objetivo Cuantitativo:** Formalizar la política institucional Fail-Closed ante colisiones simultáneas donde ambas ramas evalúan como `True` en la misma barra ($L_{signal} = 1 \land S_{signal} = 1$).
- **Escenario Cuantitativo:**
  - Ocurre ante formulaciones disyuntivas (`OR`) o condiciones de rango amplio.
  - Ejemplo: $\mathcal{C}_{LONG} = \{\text{Volume} > 1000\}$, $\mathcal{C}_{SHORT} = \{\text{Volume} > 1000\}$.
  - En una barra con volumen 2500, ambas ramas evalúan simultáneamente `True`.
- **Política Canónica Institucional (Zero-Optimism / Zero-Guess):**
  - El motor **NO DEBE** realizar selección aleatoria (*coin-flip*) ni priorizar arbitrariamente `LONG`.
  - La indeterminación produce la neutralización inmediata de la entrada:
    $$\text{if } (L_{signal} \land S_{signal}) \implies trigger\_entered = \text{False}$$
- **Verificación de Invariante:**
  $$\text{trigger\_entered} = \text{False}, \quad \text{in\_pos} = \text{False}, \quad \text{total\_trades} = 0, \quad PnL_{USD} = \$0.00$$

---

### 4.4 Caso BOTH-D: Ninguna Rama Dispara (Inacción Determinista)

- **Objetivo Cuantitativo:** Demostrar que cuando ninguna de las dos ramas se activa ($L_{signal} = 0 \land S_{signal} = 0$), el motor no abre posiciones espurias y preserva intacto el balance.
- **Precondiciones Físicas:**
  - $\mathcal{C}_{LONG}: \text{PRICE\_CLOSE} > 999,999,999.0$.
  - $\mathcal{C}_{SHORT}: \text{PRICE\_CLOSE} < -999,999,999.0$.
  - En todas las barras $i \in [0, N-1]$, $L_{signal}(i) = \text{False}$ y $S_{signal}(i) = \text{False}$.
- **Verificación de Invariante:**
  $$\text{total\_trades} = 0, \quad len(trades) = 0, \quad execution\_hash \ne \text{None}$$

---

## 5. Especificación de Sizing Instrument-Aware: CME NQ vs BTCUSDT

El motor de ejecución cuántico vincula el dimensionamiento de posición a la microestructura canónica registrada en `CANONICAL_COST_REGISTRY`:

$$\text{Profile}(sym) = \langle point\_value, contract\_multiplier, tick\_size, taker\_fee, spread \rangle$$

### 5.1 Fórmulas Matemáticas de Sizing

1. **Riesgo Monetario Total Autorizado ($Risk_{USD}$):**
   $$Risk_{USD} = account\_equity\_usd \times \left(\frac{risk\_value}{100.0}\right)$$

2. **Riesgo Monetario por Contrato Unitario ($RiskPerContract_{USD}$):**
   $$RiskPerContract_{USD} = \Delta_{SL} \times point\_value \times contract\_multiplier$$

3. **Cálculo Determinista de Contratos ($Contracts$):**
   $$Contracts = \frac{Risk_{USD}}{RiskPerContract_{USD}} = \frac{Risk_{USD}}{\Delta_{SL} \times point\_value \times contract\_multiplier}$$

4. **PnL Monetario en Liquidación ($PnL_{USD}$):**
   $$PnL_{USD} = \text{DirectionSign} \times (P_{exit} - P_{entry}) \times point\_value \times contract\_multiplier \times Contracts$$
   *(Donde $\text{DirectionSign} = +1$ para LONG y $-1$ para SHORT).*

---

### 5.2 Demostración Numérica Comparativa: CME NQ vs BTCUSDT

#### Parámetros Globales:
- **Capital de la Cuenta ($Equity$):** $\$100,000.00\text{ USD}$.
- **Porcentaje de Riesgo ($risk\_value$):** $1.0\% \implies Risk_{USD} = \$1,000.00\text{ USD}$.
- **Distancia de Stop Loss ($\Delta_{SL}$):** $50.0\text{ puntos}$ de precio.
- **Múltiplo de Take Profit ($tp\_value$):** $2.0\text{ R} \implies \Delta_{TP} = 100.0\text{ puntos}$ de precio.

---

#### Demostración A: Futuros CME NQ (E-mini Nasdaq 100)
- **Microestructura:** $point\_value = \$20.00$, $contract\_multiplier = 1.0$, $tick\_size = 0.25$.
- **Cálculo de Riesgo por Contrato:**
  $$RiskPerContract_{NQ} = 50.0\text{ pts} \times \$20.00/\text{pt} \times 1.0 = \$1,000.00\text{ USD/contrato}$$
- **Dimensionamiento de Posición:**
  $$Contracts_{NQ} = \frac{\$1,000.00}{\$1,000.00} = \mathbf{1.0\text{ contrato}}$$
- **Verificación de PnL en Stop Loss (SL alcanzado en $-\Delta_{SL} = -50.0\text{ pts}$):**
  $$PnL_{USD} = (-50.0) \times \$20.00 \times 1.0 \times 1.0 = \mathbf{-\$1,000.00\text{ USD}} \quad (PnL_R = -1.0R)$$
- **Verificación de PnL en Take Profit (TP alcanzado en $+\Delta_{TP} = +100.0\text{ pts}$):**
  $$PnL_{USD} = (+100.0) \times \$20.00 \times 1.0 \times 1.0 = \mathbf{+\$2,000.00\text{ USD}} \quad (PnL_R = +2.0R)$$

---

#### Demostración B: Cripto Perpetuo BTCUSDT (Binance / BingX Perp)
- **Microestructura:** $point\_value = \$1.00$, $contract\_multiplier = 1.0$, $tick\_size = 0.10$.
- **Cálculo de Riesgo por Contrato:**
  $$RiskPerContract_{BTC} = 50.0\text{ pts} \times \$1.00/\text{pt} \times 1.0 = \$50.00\text{ USD/contrato}$$
- **Dimensionamiento de Posición:**
  $$Contracts_{BTC} = \frac{\$1,000.00}{\$50.00} = \mathbf{20.0\text{ contratos (BTC)}}$$
- **Verificación de PnL en Stop Loss (SL alcanzado en $-\Delta_{SL} = -50.0\text{ pts}$):**
  $$PnL_{USD} = (-50.0) \times \$1.00 \times 1.0 \times 20.0 = \mathbf{-\$1,000.00\text{ USD}} \quad (PnL_R = -1.0R)$$
- **Verificación de PnL en Take Profit (TP alcanzado en $+\Delta_{TP} = +100.0\text{ pts}$):**
  $$PnL_{USD} = (+100.0) \times \$1.00 \times 1.0 \times 20.0 = \mathbf{+\$2,000.00\text{ USD}} \quad (PnL_R = +2.0R)$$

---

#### Conclusión Cuantitativa del Eje de Sizing:
$$\mathbf{Risk_{USD}(NQ) \equiv Risk_{USD}(BTCUSDT) = \$1,000.00\text{ USD}}$$
$$\mathbf{PnL_{TP}(NQ) \equiv PnL_{TP}(BTCUSDT) = +\$2,000.00\text{ USD}}$$

Queda demostrado que el motor normaliza matemáticamente el riesgo monetario real en función de la microestructura del activo, erradicando el sesgo de suponer $1\text{ punto} \equiv \$1\text{ USD}$.

---

## 6. Conflicto Intrabarra Pesimista (Zero-Optimism: SL > TP)

En barras con rango de volatilidad extremo donde tanto el nivel de Stop Loss como el nivel de Take Profit son alcanzados en la misma vela:

- **Para posición LONG:** $Low_t \le SL_{target} \land High_t \ge TP_{target}$.
- **Para posición SHORT:** $High_t \ge SL_{target} \land Low_t \le TP_{target}$.

### Política Institucional Canónica:
El motor aplica **prioridad pesimista estricta a Stop Loss**:
1. Se asume que el precio tocó primero el Stop Loss.
2. $ExitReason = \mathbf{"STOP\_LOSS"}$.
3. $P_{exit} = SL_{target}$.
4. $PnL_R = -1.0R$.
5. $PnL_{USD} = -Risk_{USD} = -\$1,000.00\text{ USD}$.

Esta política garantiza la eliminación del sesgo optimista que inflaría artificialmente el Sharpe Ratio o el Win Rate en simulaciones históricas.

---

## 7. Trazabilidad y Mapeo con la Suite de Tests Automatizada

| ID Caso Cuantitativo | Función de Test en `tests/test_phase02_canonical_strategy.py` | Estado de Ejecución en VPS |
|---|---|:---:|
| **BOTH-A** | `test_runtime_direction_long_execution` & `test_runtime_direction_both_bidirectional_triggers` | `PASSED` |
| **BOTH-B** | `test_runtime_direction_short_execution` & `test_runtime_direction_both_bidirectional_triggers` | `PASSED` |
| **BOTH-C** | `test_runtime_direction_both_bidirectional_triggers` (Líneas 398–400 de runtime adapter) | `PASSED` |
| **BOTH-D** | `test_runtime_direction_both_zero_trades_when_no_signal` | `PASSED` |
| **SIZING-NQ** | `test_sizing_microstructure_nq_vs_btcusdt_contract_point_risk` | `PASSED` |
| **SIZING-BTC** | `test_sizing_microstructure_nq_vs_btcusdt_contract_point_risk` | `PASSED` |
| **INTRABAR-L** | `test_intrabar_sl_tp_conflict_long_prioritizes_sl` | `PASSED` |
| **INTRABAR-S** | `test_intrabar_sl_tp_conflict_short_prioritizes_sl` | `PASSED` |
| **SESSION-OUT** | `test_session_window_utc_time_filtering` | `PASSED` |
| **SESSION-EOD** | `test_session_window_close_at_eod_forced_liquidation` | `PASSED` |
| **MAX-POS-FAIL** | `test_max_open_positions_unsupported_fail_closed` | `PASSED` |
| **INTEG-FAIL** | `test_deterministic_repeatability_and_missing_version_identity_fail_closed` | `PASSED` |

---

## 8. Dictamen Cuantitativo de Cierre

Todos los casos de comportamiento físico en runtime han sido matemáticamente formalizados, contrastados frente al código fuente SSOT y validados físicamente sin ninguna discrepancia.

La semántica bidireccional (`BOTH-A` a `BOTH-D`), el dimensionamiento instrument-aware (`CME NQ` vs `BTCUSDT`) y la política pesimista intrabarra (`SL > TP`) cumplen al 100% con la doctrina institucional **ZERO-MOCKS · REAL-ONLY · DETERMINISTIC · FAIL-CLOSED**.
