# PERFIL DE FONDEO CANÓNICO (Reglas Cuantitativas y Gates de Evaluación)

> **Proyecto:** Ultrarentable · **Fecha:** 2026-08-15  
> **Doctrina:** REAL-ONLY · **Prioridad:** FONDEO-PRIMERO (Modo ULTRA Congelado)  
> **Propósito:** Definir los límites cuantitativos obligatorios para generación y filtrado de estrategias destinadas a superar exámenes de prop firms y cobrar retiros de $3.000–$4.000.

---

## 1. Parámetros Cuantitativos de Evaluación (Cuenta Base 50K)

Para una cuenta de evaluación estándar de **$50.000 USD** (ej. Topstep Combine 50K / Apex 50K / TradeDay 50K):

| Parámetro | Valor Objetivo / Buffer | Límite Típico de la Firma | Razón Matemática |
|---|---|---|---|
| **Profit Target** | **$3.000 USD (6.0%)** | $3.000 USD (6.0%) | Meta de paso de examen |
| **Límite de Pérdida Diaria (Daily Loss Limit)** | **≤ $1.250 USD (2.5%)** | $1.500 USD (3.0%) | Buffer de seguridad del 0.5% por debajo del cierre forzoso |
| **Drawdown Máximo / Trailing DD** | **≤ $2.000 USD (4.0%)** | $2.500 USD (5.0%) | Buffer de seguridad del 1.0% respecto al corte de quiebra |
| **Regla de Consistencia** | **≤ 40% del profit en 1 día** | 50% max en 1 día | Exige ≥ 3–5 días con ganancias distribuidas, evitando golpes de suerte |
| **Riesgo por Operación** | **≤ $250 USD (0.5% balance)** | Variable (máx. 1 micro MES/MNQ) | Permite tolerar rachas de 5 pérdidas consecutivas sin tocar el DLL |
| **Ratio Riesgo/Beneficio (R:R)** | **≥ 1.25 : 1** | — | Con Win Rate del 50%, garantiza expectativa matemática positiva |
| **Número Mínimo de Trades OOS** | **≥ 20 trades** | — | Significancia estadística mínima con el histórico de 5,2 meses H1 |
| **Número Mínimo de Trades Totales** | **≥ 50 trades** | — | Validación de ciclo completo (IS + OOS) |
| **Profit Factor OOS** | **≥ 1.30** | — | Supervivencia comprobada fuera de muestra |
| **Ratio PF OOS / PF IS** | **≥ 0.70** | — | Anti-overfitting: la estrategia no debe degradar más del 30% en OOS |

---

## 2. Configuración en StrategyQuant X (CFX)

1. **Función Fitness:** `ReturnDDRatio` (Ratio Retorno / Drawdown). Prohibido terminantemente `NetProfit` puro.
2. **Restricción en Generación (Ranking):**
   - Condición: `#trades >= 50`
   - Condición: `MaxDD% <= 20%` (en escala de backtest de laboratorio)
3. **Validación Cruzada (Cross-Checks):**
   - `WalkForwardOptimization`: `use="true"` con `period="5"`, `optimization="20"`, exigiendo `WFPctOfProfitableRuns >= 70%`.
   - `MonteCarloRetest`: `use="true"` (20 simulaciones con variación de slippage y spread).
   - `OptProfileSysParamPermutation`: `use="true"` (análisis de meseta paramétrica).
4. **Partición de Datos:** `EvoInSamplePeriod ratio="70"` (reserva 30% OOS para evaluación ciega).

---

## 3. Catálogo de Firmas Compatibles y Pregunta de Selección

El perfil genérico cubre de forma estricta las reglas de las principales firmas de futuros:

| Firma | Plataforma Recomendada | Regla Clave | Coste Estimado |
|---|---|---|---|
| **Topstep** | TopstepX / Tradovate | 50% consistencia, $2K Trailing EOD, 90/10 split | ~$49–$150/mes |
| **Apex Trader Funding** | NinjaTrader 8 / Tradovate | Trailing intraday, permite bots sin restricción de velocidad | ~$20–$150 one-time |
| **TradeDay** | Tradovate / NinjaTrader | 14-day trial disponible, 30% consistencia en eval | ~$62–$125/mes |
| **Take Profit Trader** | Tradovate | Sin límite de tiempo, regla de consistencia al retiro | ~$75–$170/mes |
| **FundedNext Futures** | MT5 / TradeLocker | Rapid Pro sin daily loss, 90/10 split | ~$70–$250 one-time |

> **Nota para Fase 3 / 4:** El usuario puede seleccionar cualquiera de estas firmas. Por defecto, los gates aplicarán el perfil más conservador (DLL ≤ 2.5%, Max DD ≤ 4.0%, Consistencia ≤ 40%).
