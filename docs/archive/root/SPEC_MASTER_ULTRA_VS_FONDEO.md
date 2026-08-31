> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: especificación de bifurcación dual sustituida; la definición vigente de TRACK_ULTRA/TRACK_FONDEO vive en docs/00_MASTER_IDEAS_Y_PLAN.md §1. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

# 🏛️ ESPECIFICACIÓN MAESTRA DE BIFURCACIÓN CUANTITATIVA: TRACK_FONDEO VS TRACK_ULTRA
### *Ultrarentable V2 (Canónico 2026) — Arquitectura Dual de Minería Genética, Ejecución y Meta-Portafolios*

---

> [!IMPORTANT]
> **DOCUMENTO MAESTRO DE ESPECIFICACIÓN CUANTITATIVA DUAL:**
> Este documento establece la formulación matemática exacta, los contratos de datos inmutables y la lógica de ejecución para la bifurcación dual entre **TRACK_FONDEO** y **TRACK_ULTRA**.
> Queda prohibido mezclar las justificaciones o parámetros de una ruta con la otra.

---

## 🎯 1. DIVERGENCIA ESTRUCTURAL Y FILOSOFÍA MATEMÁTICA

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │      MERCADOS GLOBALES (22 DATASETS EN DISCO)          │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                                            ┌─────────────────┴─────────────────┐
                                            ▼                                   ▼
                         ┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐
                         │      TRACK_FONDEO (Institucional)   │ │       TRACK_ULTRA (Convexidad)      │
                         ├─────────────────────────────────────┤ ├─────────────────────────────────────┤
                         │ • Objetivo: Max Retiros Prop Firms  │ │ • Objetivo: Hiperescalado Asimétrico │
                         │ • Drawdown Realizado: <= 4.0%-4.5%  │ │ • Drawdown Realizado: Hasta 75.0%   │
                         │ • Compounding: 0% (Contratos Fijos) │ │ • Compounding: Piramidación Convexa │
                         │ • Posición: 1R Cerrado Intradía     │ │ • Posición: Balas Aisladas ($100-$1k)│
                         │ • Distribución: Gaussiana Estable   │ │ • Distribución: Fat-Tail Right Skew │
                         │ • Cero Margin Calls Toleradas       │ │ • Bóveda Ratchet Inviolable (50-85%)│
                         └─────────────────────────────────────┘ └─────────────────────────────────────┘
```

---

## 🏛️ 2. ESPECIFICACIÓN DE `TRACK_FONDEO` (PRESERVACIÓN INSTITUCIONAL & PROP FIRMS)

### 2.1. Tesis Operativa, Mercados y Activos Aceptados
- **Activos Operados:**
  - **Futuros y Micro Futuros CME:** MES, MNQ, MYM, M2K, GC, MGC, CL, MCL.
  - **Forex Majors:** EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF.
  - **Criptoactivos Institucionales (Majors):** Micro Bitcoin (`MBT`), Micro Ether (`MET`) en CME Globex (Topstep, Apex), y pares CFD/Crypto (`BTCUSD`, `ETHUSD`) en firmas reguladas (FTMO, The5ers, FundedNext, E8, Funding Pips con apalancamiento 1:2 a 1:5).
- **Modelo de Optimización Canónico:** Asignación de riesgo fijo acotado a $\le 0.3\% - 0.5\%$ del balance por operación ($R:R \ge 1:2.0$).
- **Objetivo Financiero:** Maximizar la **Economía Real Neta**:
  $$\text{Retornos Netos} = \sum \text{Retiros Fondeados} - \left( \sum \text{Coste Exámenes} + \sum \text{Cuotas Activación} + \sum \text{Resets} + \sum \text{Data/Licencias} \right)$$

### 2.2. Restricciones Contractuales Auditadas
1. **Trailing Drawdown Estricto:** $\text{Max DD} \le 4.00\% - 4.50\%$ en todo el historial.
2. **Cumplimiento Estricto del Daily Loss Limit (DLL):** $0$ violaciones (pérdida máxima en un solo día $\le \$1,000$ en cuenta base \$50k).
3. **Consistency Rule:** Ningún día o trade individual puede representar $> 30\%$ del beneficio total.
4. **Cierre Obligatorio Intradía / Fin de Semana:** Cierre automático a las **16:59 EST** para CME/FX (cero riesgo *overnight* de fin de semana).
5. **Cero Riesgo de Quiebra:** Probabilidad de ruina Monte Carlo $P(\text{Ruin}) = 0.00\%$ en 10,000 iteraciones.

---

## ⚡ 3. ESPECIFICACIÓN DE `TRACK_ULTRA` (CONVEXIDAD ASIMÉTRICA TALEB MULTI-ACTIVO)

### 3.1. Tesis Operativa y Mecánica de Balas
- **Activos Operados:** 100% del Universo Global de Activos (Cripto Perpetuos BingX, Futuros CME, Forex Majors y Commodities) bajo régimen de Margen Aislado por Subcuenta. **NUNCA es solo cripto**.
- **Temporalidades Operadas:** **1min (1m), 5min (5m), 15min (15m), 1h (1h) y 4h (4h)** — **SOLO INTRADIA** en todos los activos (cero riesgo overnight destructivo, sin depender de swing multi-día).
- **Doctrina de Opción Sintética:** Riesgo estrictamente acotado a $1R$ ($M_0 \approx \$100\text{--}\$1,000$) por bala aislada, con beneficio ilimitado ($\text{Gamma Positiva } \frac{d^2 \Pi}{dP^2} > 0$).

### 3.2. Los 6 Estados Discretos de una Bala (`IsolatedBullet` / `ultra_engine.py`)

```
[ Estado 0: INICIO ] ──► SL = -1.0R, Margen Aislado 1R ($100-$1,000 nominales)
        │
        ▼ (Si Retorno Flotante >= +1.0R a +1.5R)
[ Estado 1: CONFIRMACIÓN ] ──► SL a BREAK-EVEN REAL (+0.1R / Comisión Cubierta)
        │
        ▼ (Si Retorno Flotante >= +2.0R a +3.0R)
[ Estado 2: CRECIMIENTO / RECYCLING ] ──► Piramidación Nivel 2 (+40% House Money)
        │                                  SL Free-Risk calculado: Garantiza >= +0.5R
        ▼ (Si Retorno Flotante >= +3.0R)
[ Estado 3: COSECHA / VAULT ] ──► Obsidian Milestones a Bóveda Ratchet (Spot USDT)
        │                         - 2x (+100%): Bloquea 50%
        │                         - 3x (+200%): Bloquea 65%
        │                         - 5x (+400%): Bloquea 75%
        │                         - >=10x (+900%): Bloquea 85%
        ▼
[ Estado 4: PROTECCIÓN ] ──► Chandelier Trailing ATR dinámico
        │
        ▼ (Al tocar SL en ganancia o Take Profit Terminal)
[ Estado 5: CIERRE ] ──► Liquidación total y reciclaje de capital al cargador
```

### 3.3. Deducción Matemática del Stop Loss Free-Risk en Piramidación
Cuando se añade una capa $k$ con capital financiado por la ganancia flotante $\Delta P_{\text{flotante}} \times 0.40$:
$$\text{Nueva Cantidad Total: } Q_{\text{total}} = \sum_{i=0}^k Q_i$$
$$\text{Precio Medio Ponderado: } \overline{P}_{\text{entry}} = \frac{\sum Q_i \cdot P_i}{Q_{\text{total}}}$$
$$\text{Stop Loss Free-Risk: } SL_{\text{FreeRisk}} = \overline{P}_{\text{entry}} \pm \frac{0.5 \times \text{Margen}_0}{Q_{\text{total}}}$$
Garantiza que incluso ante un gap o reversión instantánea al nuevo SL, el beneficio neto consolidado sea siempre $\ge +0.5\text{R}$.

### 3.4. Matriz de Amortización y Asimetría
- 10 Balas fallidas a $1R$: $10 \times (-1.0R) = -10.0R$.
- 1 Bala ganadora en mega-tendencia (3 capas piramidadas): $+18.5R$.
- **PnL Neto de Campaña:** $-10.0R + 18.5R = \mathbf{+8.5R}$ ($+77.27\%$ ROI). La Bóveda retiene $50\%$ ($+4.25R$) de forma física en Spot USDT.

---

## 📊 4. COMPARATIVA CUANTITATIVA FONDEO VS ULTRA

| Dimensión Cuantitativa | TRACK_FONDEO (CME / Prop Firms) | TRACK_ULTRA (BingX Cripto Perps) | Justificación Matemática & Operativa |
| :--- | :--- | :--- | :--- |
| **Max Realized Drawdown** | **$\le 4.00\% - 4.50\%$** | **$\le 75.00\%$** | En Fondeo un DD > 5% quema la cuenta. En Ultra, el balance de trabajo soporta rachas de balas. |
| **Max Floating Drawdown** | **$\le 80.00\%$** | **$\le 80.00\%$** | Absorbe el ruido intrabar sin cerrar antes de alcanzar el Break-Even (+1.5R). |
| **Apalancamiento** | **Contratos Fijos** (1-3 Minis / 10-30 Micros) | **Hasta $500\text{x}$** (Margen Aislado 1R) | Fondeo prohíbe sobreapalancamiento. Ultra usa apalancamiento aislado por bala. |
| **Deflated Sharpe Ratio (DSR)**| **$\ge 2.00$** | N/A (No penaliza *fat-tails*) | DSR ajusta el Sharpe por asimetría, curtosis y número de ensayos múltiples. |
| **Payoff Ratio ($\frac{\overline{W}}{\overline{L}}$)** | $\ge 1.30 - 1.50$ | **$\ge 3.00$** (Típico 3.0R - 8.0R) | En Ultra la ganancia media DEBE ser al menos 3 veces la pérdida media. |
| **Asimetría ($\text{Skewness}$)** | Indiferente ($\approx 0$) | **$\ge +0.50$** ($\text{Right-Skewed}$) | Obliga a que los retornos tengan cola derecha pesada (Taleb). |
| **Tail Gain Ratio** | N/A | **$\ge 40.0\%$** | Al menos el 40% del beneficio proviene de trades $\ge 3\text{R}$. |
| **Daily Loss Limit** | **$0$ violaciones** ($< \$1,000$ en 50k) | No aplica (Aislado por bala) | Un solo día con pérdida $> \$1,000$ cancela una cuenta fondeada. |
| **Riesgo de Ruina (Monte Carlo)**| **$0.00\%$** | Ráfaga 10 Balas: **$\le 1.0\%$** | Fondeo no tolera ruina; Ultra evalúa supervivencia de ráfagas. |
| **Bóveda Ratchet** | N/A (Retiros mensuales bancarios) | **$50\% - 85\%$ a Spot USDT** | Transferencia irrevocable que no se re-arriesga en la misma serie. |

---

## 🏛️ 5. EXPLICACIÓN MATEMÁTICA: META-ESTRATEGIAS EN FONDEO VS ULTRA

### ¿Por qué una Meta-Estrategia puede tener menor rentabilidad nominal que la mejor individual?
1. **En TRACK_FONDEO:**
   - La mejor estrategia individual puede marcar $+300\%$ de retorno, pero con un Drawdown de $35\%$. Para una Prop Firm institucional (Topstep/Apex), esa estrategia está **muerta y descalificada en el primer mes**.
   - Al ensamblar 3 o 4 activos ortogonales (ej. `NQ` + `GC` + `EURUSD`), el efecto de la matriz de covarianza descorrelacionada comprime el Drawdown a **$2.8\%\text{--}3.5\%$**, permitiendo que la cuenta pase la evaluación, reciba fondeo y sea escalable a $\$150\text{k}\text{--}\$300\text{k}$.
2. **En TRACK_ULTRA:**
   - La meta-estrategia no busca restringir el retorno nominal, sino operar como un **cargador multi-bala descorrelacionado**. Al distribuir balas 1R entre `BTC`, `ETH`, `SOL` y `SUI`, se neutralizan los periodos laterales de unos activos con las expansiones parabólicas de otros, disparando el Ratio de Sharpe conjunto a $> 2.50$ y manteniendo una tasa de cosecha a Bóveda Ratchet continua.
