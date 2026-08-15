# 🔬 Diagnóstico Real de Plantilla SQX — Ultra_Auto_Pilot

**Fecha:** 2026-08-09  
**Fuente:** `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx` → `Build-Task1.xml`  
**Regla:** REAL-ONLY — todos los valores citados provienen del XML descomprimido, sin estimaciones.

---

## 1. Configuración ACTUAL Real Extraída del XML

### 1.1 Fitness Function

| Parámetro | Valor Real (XML) | Evidencia |
|-----------|-------------------|----------|
| Método | `ComputeFromStrategyResult` | `<FitnessCriteria method="ComputeFromStrategyResult">` |
| Tipo de Ranking | **NetProfit** (beneficio neto bruto) | `<Ranking type="NetProfit" />` |
| Rankings type | `never` (sin filtro de ranking) | `<Rankings type="never">` |
| ConditionsType | `1` | `<ConditionsType>1</ConditionsType>` |
| Conditions | **Vacío** (ninguna condición de filtro) | `<Conditions />` |
| MaxStrategies | 24 | `<MaxStrategies>24</MaxStrategies>` |
| StopCondition | databank-full, 200 estrategias ó 30 min | `passedStrategies="200" minutes="30"` |

### 1.2 Opciones Genéticas

| Parámetro | Valor Real | Evidencia XML |
|-----------|-----------|---------------|
| Tipo de generación | `genetic-evolution` | `generationType="genetic-evolution"` |
| PopulationSize | **80** | `<PopulationSize>80</PopulationSize>` |
| MaxGenerations | **40** | `<MaxGenerations>40</MaxGenerations>` |
| CrossoverProbability | **95%** | `<CrossoverProbability>95</CrossoverProbability>` |
| MutationProbability | **45%** | `<MutationProbability>45</MutationProbability>` |
| Islands | **8** | `<Islands>8</Islands>` |
| MigrationModulo | 20 | `<MigrationModulo>20</MigrationModulo>` |
| MigrationRate | 15 | `<MigrationRate>15</MigrationRate>` |
| DecimationCoef | 4 | `<DecimationCoef>4</DecimationCoef>` |
| **EvoInSamplePeriod** | **ratio="100"** ⚠️ | `<EvoInSamplePeriod ratio="100" />` |
| EvoRestartOnFinish | true | `status="true"` |
| EvoRestartOnStagnation | **false** | `status="false"` |
| FreshBloodWeakestPct | 25% | `<FreshBloodWeakestPct>25</FreshBloodWeakestPct>` |
| FilterInitialPopulation | false | `<FilterInitialPopulation>false</FilterInitialPopulation>` |

### 1.3 Data (Datos de Mercado)

| Parámetro | Valor Real | Evidencia XML |
|-----------|-----------|---------------|
| Símbolo | **BTCUSDT_AUTO** | `symbol="BTCUSDT_AUTO"` |
| Timeframe | **H1** | `timeframe="H1"` |
| dateFrom | **2026.02.26** | `dateFrom="2026.02.26"` |
| dateTo | **2026.8.4** | `dateTo="2026.8.4"` |
| **Rango total** | **~5 meses y 8 días** ⚠️ | Calculado: Feb 26 → Ago 4 |
| testPrecision | **1** (mínima: "Selected ticks") | `testPrecision="1"` |
| **Spread** | **0** ⚠️ (CERO) | `spread="0"` |
| Slippage | **1** pip | `slippage="1"` |
| Session | **"No Session"** ⚠️ | `session="No Session"` |
| Engine | MetaTrader4 | `engine="MetaTrader4"` |
| Comisión | PercentageBased, **0.05%** | `value="0.05"` `type="PercentageBased"` |
| OutOfSample (rango visual) | 2026.06.18 → 2026.8.4 | `<Range dateFrom="2026.06.18" dateTo="2026.8.4" />` |
| OOS showGraph | **false** | `showGraph="false"` |

### 1.4 CrossChecks (Validaciones Cruzadas)

| CrossCheck | Estado | Evidencia XML |
|-----------|--------|---------------|
| **Master switch** | **`use="false"`** ⚠️ | `<CrossChecks use="false" evaluateAll="false">` |
| RetestOnAdditionalMarkets | `use="false"` | Línea ~213 |
| WalkForwardOptimization | `use="false"` | Línea 247: `<WalkForwardOptimization use="false">` |
| WalkForwardMatrix | Presente pero deshabilitado | Dentro de CrossChecks deshabilitados |
| RetestWithHigherPrecision | Configurado (Precision=2, Spread=3) pero **inactivo** | Dentro de CrossChecks `use="false"` |
| MonteCarloManipulation | **`use="false"`** | `<MonteCarloManipulation use="false">` |
| SPP (SysParamPermutation) | **`use="false"`** | `<OptProfileSysParamPermutation use="false">` |
| WhatIf | **`use="false"`** | `<WhatIf use="false">` |

> **CRÍTICO:** El switch maestro `<CrossChecks use="false">` desactiva TODOS los crosschecks, incluso aquellos que tienen configuración interna.

### 1.5 Money Management

| Parámetro | Valor Real | Evidencia XML |
|-----------|-----------|---------------|
| Método activo | **RiskFixedBalancePct** | `type="RiskFixedBalancePct" use="true"` |
| Riesgo por trade | **2%** del balance | `<Param key="Risk">2</Param>` |
| Capital inicial | **$1,000** | `<InitialCapital>1000</InitialCapital>` |
| MaxLots | 5 | `<Param key="MaxLots">5</Param>` |
| LotsIfNoMM | 0.001 | `<Param key="LotsIfNoMM">0.001</Param>` |
| Decimals | 3 | `<Param key="Decimals">3</Param>` |
| MaxDrawdown | 30% | `maxDrawdown="30"` |
| RiskManagement | AllowAllTrades | `type="AllowAllTrades" use="true"` |
| FixedSize | Deshabilitado | `use="false"` |

### 1.6 Building Blocks

| Parámetro | Valor Real |
|-----------|----------|
| Tipo | `simple` |
| Bloques habilitados | **123** de 354 totales |
| Calibration maxSteps | 50 |
| Incluye ATR signals | Sí (ATRChangesDown/Up, ATRCrossDown/Up, ATRFalling, ATRHigher, etc.) |
| Incluye Ichimoku, MACD, BB, KC, MA, PSAR | Sí |
| Stop/Limit Price Levels | Múltiples (Ask, Bid, BB, EMA, Ichimoku, KC, etc.) |
| Stop/Limit Price Ranges | ATR, BBRange, BarRange, BiggestRange, MTATR, SmallestRange |

### 1.7 Filtros de Sesión y Régimen de Volatilidad

| Filtro | Estado | Evidencia |
|--------|--------|----------|
| Session filter | **"No Session"** — SIN filtro | `session="No Session"` en línea 160 |
| LimitTimeRange | **false** | `<Param key="LimitTimeRange">false</Param>` |
| ExitAtEndOfDay | **false** | `<Param key="ExitAtEndOfDay">false</Param>` |
| Régimen ATR/Volatilidad | **NO EXISTE** | No hay ningún bloque de régimen ATR como filtro de entorno |
| Filtro de volatilidad | **AUSENTE** | Los bloques ATR solo están como señales de entry/exit, no como filtro de régimen |

---

## 2. Los 5 Errores de Causa Raíz con Evidencia Concreta

### ❌ ERROR #1: Fitness = NetProfit Bruto → Máquina de Sobreajuste

**Evidencia XML:**
```xml
<FitnessCriteria method="ComputeFromStrategyResult">
  <Settings>
    <Ranking type="NetProfit" />
  </Settings>
</FitnessCriteria>
```

**Diagnóstico:** La evolución genética selecciona y cruza individuos exclusivamente por beneficio neto bruto. Esto es el driver #1 de curve-fitting:

- El algoritmo genético **premia estrategias que memorizan los movimientos del histórico** en lugar de descubrir patrones estadísticamente robustos.
- No hay penalización por drawdown, por número de trades, por estabilidad de la equity curve, ni por ratio de Sharpe/Sortino.
- Con `<Conditions />` vacío y `<Rankings type="never">`, no hay NINGÚN filtro secundario — toda estrategia que tenga alto profit pasa, sin importar si tiene 3 trades o 3000, si tiene 80% drawdown o 5%.
- **Resultado previsible:** IS altísimo (miles de %) → OOS negativo o plano. La estrategia memorizó el ruido.

**Fitness correcto para Ultrarentable:** SQX Score, Profit Factor, Return/DD ratio, o una fórmula compuesta multi-objetivo (profit × stability × trades).

### ❌ ERROR #2: EvoInSamplePeriod ratio="100" → Evolución Ciega sin OOS

**Evidencia XML:**
```xml
<EvoInSamplePeriod ratio="100" />
```

**Diagnóstico:** El parámetro `ratio="100"` significa que el **100% del rango de datos se usa como In-Sample** durante la evolución genética. No hay Out-of-Sample interno durante el proceso evolutivo.

- La evolución genética opera en un bucle cerrado: genera → evalúa en el mismo dato → selecciona → cruza → repite.
- Sin un período OOS interno, **no hay ningún mecanismo de detección de overfitting durante la construcción**.
- Aunque existe un rango OOS visual (`2026.06.18 → 2026.8.4`), con `showGraph="false"` y sin crosschecks activos, este rango **no se usa para filtrar ni descartar** estrategias sobreajustadas.
- Con solo ~5 meses de datos y 100% IS, cada generación se ajusta más y más al ruido de esos 5 meses.

**Correcto:** ratio=70 (70% IS / 30% OOS) como mínimo, idealmente con WFA rolling.

### ❌ ERROR #3: CrossChecks Completamente Desactivados → Sin Validación de Robustez

**Evidencia XML:**
```xml
<CrossChecks use="false" evaluateAll="false">
```

Y cada crosscheck individual:
```xml
<WalkForwardOptimization use="false">
<MonteCarloManipulation use="false">
<OptProfileSysParamPermutation use="false">
<WhatIf use="false">
```

**Diagnóstico:** El switch maestro `use="false"` desactiva **TODA** la batería de validación cruzada:

| CrossCheck | Propósito | Estado |
|-----------|-----------|--------|
| WFO/WFA | Detectar si la estrategia funciona en datos no vistos | ❌ OFF |
| Monte Carlo Manipulation | Verificar robustez ante variación de orden/skip de trades | ❌ OFF |
| SPP (Sys Param Permutation) | Detectar si pequeños cambios en parámetros destruyen el resultado | ❌ OFF |
| WhatIf | Verificar si el resultado depende de 2-3 trades outlier | ❌ OFF |
| Retest Higher Precision | Verificar con ticks más precisos | ❌ OFF |
| Retest Additional Markets | Verificar en otros instrumentos | ❌ OFF |

**Sin ninguno de estos filtros, las 200 estrategias del databank son candidatas sin validar** — el equivalente a publicar un paper sin peer review.

### ❌ ERROR #4: Spread=0 + Slippage=1 pip en BTCUSDT → Costes Irreales

**Evidencia XML:**
```xml
<Chart symbol="BTCUSDT_AUTO" timeframe="H1" spread="0" />
<!-- slippage="1" en el Setup -->
<Param key="CommissionPct" value="0.05" />
```

**Diagnóstico:**

- **Spread = 0** en BTCUSDT es ficticio. En la realidad, incluso los mejores exchanges crypto tienen spread de 0.01-0.05% del precio (~$6-$30 en BTC a $60k). En pips MT4, esto se traduce a 60-300 puntos dependiendo de la cotización.
- **Slippage = 1 pip** es insignificante para crypto. El slippage real en BTC/USDT puede ser 5-50 pips dependiendo del tamaño y la liquidez.
- **Comisión = 0.05%** es razonable para un exchange spot tier-1, pero con spread=0 el coste total está subestimado en un ~50-70%.
- **Impacto:** Estrategias que parecen rentables con costes ficticios **se vuelven perdedoras** cuando se aplican costes reales. Cada trade tiene ~$12-60 de costes ocultos no modelados.
- Con `testPrecision="1"` (mínima), la simulación de fills también es imprecisa.

### ❌ ERROR #5: Ausencia Total de Filtros de Sesión y Régimen de Volatilidad

**Evidencia XML:**
```xml
<Param key="Session" className="SessionOption">No Session</Param>
<Param key="LimitTimeRange" className="LimitTimeRange">false</Param>
setup: session="No Session"
```

**Diagnóstico:**

- **No hay filtro de sesión (Londres/NY):** Las estrategias generadas operan las 24 horas, 7 días. En crypto esto incluye períodos de baja liquidez (madrugada asiática, fines de semana) donde el spread real se amplía, el slippage aumenta, y los movimientos son erráticos.
- **No hay filtro de régimen de volatilidad:** No existe ningún bloque que condicione las entradas al nivel de ATR actual, al percentil de volatilidad, o a la fase de mercado (trending/ranging). Los bloques ATR presentes (ATRChangesDown, etc.) son señales de entrada/salida, NO filtros de régimen ambiental.
- **No hay ExitAtEndOfDay:** Las posiciones pueden mantenerse durante períodos de baja liquidez nocturna.
- **Consecuencia:** Las estrategias generadas son "ciegas al contexto" — operan igual durante un crash de $5,000 que durante un rango lateral de $200, y operan igual a las 3am UTC que durante la apertura de NY.

---

## 3. Por Qué NetProfit Produce Curvas Frágiles y Sobreajuste

La optimización por NetProfit puro es el anti-patrón más documentado en trading algorítmico:

1. **Sesgo de supervivencia del outlier:** Una estrategia con 5 trades puede tener $50,000 de profit si captura un movimiento extremo. NetProfit la rankea por encima de una estrategia con 500 trades y $40,000 de profit consistente.

2. **Memorización vs. generalización:** El algoritmo genético con fitness=NetProfit converge hacia estrategias que "memorizan" los 3-5 movimientos más grandes del período IS. Estos movimientos son irrepetibles.

3. **IS alto / OOS negativo es el síntoma cardinal:**
   - IS: La estrategia captura todos los movimientos grandes → profit enorme
   - OOS: Los movimientos grandes son diferentes → la estrategia no los reconoce → pérdida

4. **Sin penalización por drawdown:** Una estrategia con 2000% de retorno y 85% de drawdown pasa. En la práctica, sufriría una margin call antes de alcanzar ese retorno.

5. **Sin penalización por número de trades:** Estrategias con 5-10 trades pasan con profit alto, pero no tienen significancia estadística (p-value > 0.3).

---

## 4. Resumen de Estado: Semáforo de Configuración

| Componente | Estado | Calificación |
|-----------|--------|-------------|
| Fitness Function | NetProfit bruto, sin condiciones | 🔴 CRÍTICO |
| Evolución IS/OOS | 100% IS, 0% OOS evolutivo | 🔴 CRÍTICO |
| CrossChecks | TODOS desactivados (master=false) | 🔴 CRÍTICO |
| Spread | 0 (ficticio para BTCUSDT) | 🔴 CRÍTICO |
| Slippage | 1 pip (insuficiente para crypto) | 🟠 GRAVE |
| Comisión | 0.05% (razonable pero spread=0 lo anula) | 🟡 PARCIAL |
| Rango de datos | ~5 meses (muy corto) | 🟠 GRAVE |
| Precisión de test | 1 (mínima) | 🟠 GRAVE |
| Sesión/horario | "No Session" — sin filtro | 🔴 CRÍTICO |
| Régimen volatilidad | Ausente | 🔴 CRÍTICO |
| Money Management | 2% risk, $1000 capital, MaxDD 30% | 🟢 ACEPTABLE |
| Genética | 80 pop, 8 islas, 95% cross, 45% mut | 🟡 PARCIAL |
| Building Blocks | 123/354 habilitados | 🟡 PARCIAL |

---

## 5. Conclusión

La plantilla actual de Ultra_Auto_Pilot está configurada como una **máquina de sobreajuste**: optimiza por profit bruto sin validación, con costes ficticios, sin filtros de contexto, y con solo 5 meses de datos al 100% In-Sample. **Cualquier estrategia generada por esta configuración es estadísticamente inválida** para trading real hasta que se corrijan los 5 errores de causa raíz identificados.

> **Próximo paso:** Aplicar las correcciones documentadas en el plan de reconfiguración para convertir esta plantilla de "generador de ilusiones" a "generador de candidatos robustos validados".
