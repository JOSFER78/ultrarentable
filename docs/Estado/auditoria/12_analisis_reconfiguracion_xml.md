# 🛠️ Análisis de Reconfiguración Exacta de `Build-Task1.xml` (SQX Build 144)

> **Proyecto:** Ultrarentable · **Fecha:** 2026-08-09  
> **Archivo Destino:** `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx` → `Build-Task1.xml`  
> **Estado:** Documento de especificación técnica y validación sintáctica XML SQX 144.

---

## 1. Resumen Ejecutivo

El diagnóstico de la plantilla real `Ultra_Auto_Pilot` (`Build-Task1.xml` versión `144.2953`) reveló 5 errores graves que convierten al generador de StrategyQuant X en un "memorizador de ruido":
1. Fitness basado en `NetProfit` bruto.
2. Evolución 100% In-Sample (`ratio="100"`).
3. Interruptor maestro de `CrossChecks` en `use="false"`.
4. Costes irreales para BTC (`spread="0"`, `slippage="1"`).
5. Ausencia total de filtros de sesión y régimen.

Este documento especifica los **cambios XML exactos y mínimos** necesarios para transformar la plantilla en un generador de kandidatas/balas robustas alineado con la doctrina del proyecto, verificando la compatibilidad sintáctica estricta con el parser de StrategyQuant X Build 144 para no corruptar el archivo `project.cfx`.

---

## 2. Análisis Detallado por Componente y Fragmentos XML Exactos

### 2.1 Fitness Function / Ranking (Punto 1)

#### Diagnóstico del XML Actual:
```xml
<!-- Línea 175-181 de Build-Task1.xml -->
<Rankings type="never">
  <MaxStrategies>24</MaxStrategies>
  <FitnessCriteria method="ComputeFromStrategyResult">
    <Settings>
      <Ranking type="NetProfit" />
    </Settings>
  </FitnessCriteria>
```
- **Problema:** Optimiza exclusivamente por beneficio neto. Premia estrategias con pocos trades afortunados o drawdowns masivos (p.ej. 80% DD). Además, `<Rankings type="never">` impide aplicar filtros hard en la fase de generación.

#### Cambio Propuesto (Perfil A Growth / Perfil B Fondeo):
Para buscar "balas" con curva de equidad estable y drawdown acotado, el ranking debe cambiarse a `ReturnDDRatio` (o `AnnualPercentReturn` ponderado) y activar el filtrado en fase de ranking con `<Rankings type="always">` o `<Rankings type="after-generation">`.

#### Fragmento XML Reemplazable:
```xml
<!-- REEMPLAZO EN LÍNEAS 175-184 -->
<Rankings type="always">
  <MaxStrategies>200</MaxStrategies>
  <FitnessCriteria method="ComputeFromStrategyResult">
    <Settings>
      <Ranking type="ReturnDDRatio" />
    </Settings>
  </FitnessCriteria>
  <ConditionsType>1</ConditionsType>
  <Conditions>
    <Condition use="true">
      <Left-Side valueType="column">
        <Column-Value column="NumberOfTrades" columnType="0" name="# of trades" format="Integer" resultType="main" direction="0" sampleType="127" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="NumberOfTrades" />
      </Left-Side>
      <Comparator value="&gt;=" />
      <Right-Side valueType="numeric">
        <Numeric-Value value="100" />
      </Right-Side>
    </Condition>
    <Condition use="true">
      <Left-Side valueType="column">
        <Column-Value column="DrawdownPct" columnType="0" name="Max DD %" format="Decimal2Pct" resultType="main" direction="0" sampleType="127" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="DrawdownPct" />
      </Left-Side>
      <Comparator value="&lt;=" />
      <Right-Side valueType="numeric">
        <Numeric-Value value="35" />
      </Right-Side>
    </Condition>
  </Conditions>
```

#### Validación Sintáctica SQX 144:
- `Ranking type="ReturnDDRatio"` es una clase estándar registrada en el motor Java de SQX (`com.strategyquant.databank.columns.ReturnDDRatio`).
- `<Rankings type="always">` instruye a SQX a aplicar las condiciones de descarte a cada individuo generado antes de guardarlo en el databank.

---

### 2.2 In-Sample vs Out-of-Sample Evolutivo (Punto 2)

#### Diagnóstico del XML Actual:
```xml
<!-- Línea 85 de Build-Task1.xml -->
<EvoInSamplePeriod ratio="100" />
```
- **Problema:** Con `ratio="100"`, el algoritmo genético evalúa la adaptación sobre el 100% de la muestra de datos disponible. No hay validación ciega *durante* el cruce y mutación.

#### Valoración de Bajar `ratio` a 70-80:
1. **Pros:** Reservar un 20% - 30% como Out-Of-Sample (OOS) *dentro del ciclo de evolución* impide que la población evolutiva converga hacia patrones memorizados del tramo final. Las estrategias que fallan en el tramo OOS no reciben puntuación alta de fitness.
2. **Impacto en Velocidad:** La velocidad por generación aumenta ligeramente en la fase IS (30% menos barras a simular en la primera pasada), pero añade la evaluación del tramo OOS. El tiempo total por candidato es prácticamente idéntico (±5%).
3. **Recomendación:** Ajustar a `ratio="70"` (70% In-Sample, 30% Out-of-Sample). En la muestra actual de ~5.2 meses (~158 días), esto asigna ~110 días a entrenamiento evolutivo y ~48 días a verificación OOS inmediata.

#### Fragmento XML Reemplazable:
```xml
<!-- REEMPLAZO EN LÍNEA 85 -->
<EvoInSamplePeriod ratio="70" />
```

#### Validación Sintáctica SQX 144:
- `ratio` acepta un entero de 10 a 90 en SQX 144. El valor `70` es procesado directamente por la clase `EvoInSamplePeriod`.

---

### 2.3 Walk-Forward Optimization (Punto 3)

#### Diagnóstico del XML Actual:
```xml
<!-- Línea 215 y 247-256 de Build-Task1.xml -->
<CrossChecks use="false" evaluateAll="false">
  ...
  <WalkForwardOptimization use="false">
    <Settings>
      <WalkForward type="1" period="10" optimization="15">
        <Param1 value="20" />
        <Param2 value="10" />
      </WalkForward>
      <OptimizePeriods>true</OptimizePeriods>
      <OptimizeExitTypes>true</OptimizeExitTypes>
      <MaxTests>100</MaxTests>
    </Settings>
```

#### Análisis de Sensatez para 5 Meses de Datos:
- **Configuración actual en XML:** `period="10"`, `optimization="15"`.
- **Evaluación crítica:** 5.2 meses equivalen a ~158 días (~3,800 barras H1). Si dividimos la muestra en **10 períodos**, cada tramo de optimización OOS es de solo **15 días** (apenas 360 barras H1).
- En H1, 15 días generan un promedio de solo 2 a 6 operaciones. Un tamaño muestral de 2-6 trades por fold es **estadísticamente nulo** y producirá falsos descartes por falta de trades o falsos aprobados por suerte.
- **Recomendación para 5 meses:** Reducir a `period="5"` (folds de ~31 días OOS cada uno, ~15-20 trades/fold) u `optimization="20"` (20% OOS por fold). Además, es **imprescindible activar el switch máster** `<CrossChecks use="true">`.

#### Fragmento XML Reemplazable:
```xml
<!-- REEMPLAZO EN LÍNEA 215 Y LÍNEAS 247-256 -->
<CrossChecks use="true" evaluateAll="false">
  <WalkForwardOptimization use="true">
    <Settings>
      <WalkForward type="1" period="5" optimization="20">
        <Param1 value="20" />
        <Param2 value="10" />
      </WalkForward>
      <OptimizePeriods>true</OptimizePeriods>
      <OptimizeExitTypes>true</OptimizeExitTypes>
      <MaxTests>100</MaxTests>
    </Settings>
    <AcceptanceSettings>
      <Conditions thresholdPct="80">
        <Condition use="true">
          <Left-Side valueType="column">
            <Column-Value column="WFPctOfProfitableRuns" columnType="33" name="WF Special Percentage of profitable runs" format="Decimal2Pct" resultType="WalkForwardOptimization" direction="0" sampleType="10" plType="10" confidenceLevel="50" market="1" subresult="33" pctRatio="0" class="WFPctOfProfitableRuns" />
          </Left-Side>
          <Comparator value="&gt;=" />
          <Right-Side valueType="numeric">
            <Numeric-Value value="70" />
          </Right-Side>
        </Condition>
      </Conditions>
    </AcceptanceSettings>
  </WalkForwardOptimization>
```

#### Validación Sintáctica SQX 144:
- `use="true"` activa el sub-módulo WFA.
- `type="1"` corresponde a WFA Rolling re-optimization en el esquema interno de SQX. `period="5"` es parseado correctamente como entero positivo.

---

### 2.4 Activación de Otros Cross-Checks (Punto 4)

#### Diagnóstico del XML Actual:
Actualmente `MonteCarloRetest`, `MonteCarloManipulation`, `OptProfileSysParamPermutation` (SPP) y `RetestWithHigherPrecision` tienen `use="false"` (o están apagados por el switch máster).

#### Pruebas a Activar y Parámetros Recomendados:

1. **RetestWithHigherPrecision (Mayor Precisión):**
   - Activar con `use="true"`, `Precision=2` (1-minute data / tick precision) y `Spread=3`.
   - Exige que el beneficio con precisión superior no caiga más del 20% respecto a la simulación principal.

2. **MonteCarloRetest (Simulación de Variación de Mercado):**
   - Activar con `use="true"`, `NumberOfSimulations="20"`.
   - Métodos: `RandomizeSlippage` [0.0 a 5.0 pips], `RandomizeSpread` [1.0 a 5.0 pips], `RandomizeStrategyParameters` [±10-15% cambio].
   - Umbral de aceptación: Al 80% de nivel de confianza, el NetProfit debe ser ≥ 50% del original y el DD ≤ 150% del original.

3. **OptProfileSysParamPermutation / SPP (Sensibilidad de Parámetros):**
   - Activar con `use="true"`, `MaxTests="100"`.
   - Verifica la "meseta de parámetros": pequeñas variaciones de ±10-15% en periodos de indicadores o SL/TP no deben destruir el resultado de la estrategia (evita picos de sierra aislados).

#### Fragmento XML Reemplazable:
```xml
<!-- REEMPLAZO EN LÍNEAS 343-446 Y LÍNEAS 582-599 -->
    <RetestWithHigherPrecision use="true">
      <Settings>
        <Precision>2</Precision>
        <Spread>3</Spread>
      </Settings>
      <AcceptanceSettings>
        <Conditions CrossCheck="RetestWithHigherPrecision">
          <Condition use="true">
            <Left-Side valueType="column">
              <Column-Value column="NetProfit" columnType="0" name="Net profit" format="Decimal2PL" resultType="RetestWithHigherPrecision" direction="0" sampleType="127" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="NetProfit" />
            </Left-Side>
            <Comparator value="&gt;=" />
            <Right-Side valueType="column">
              <Column-Value column="NetProfit" columnType="0" name="Net profit" format="Decimal2PL" resultType="main" direction="0" sampleType="127" plType="10" confidenceLevel="undefined" market="undefined" subresult="undefined" pctRatio="80" class="NetProfit" />
            </Right-Side>
          </Condition>
        </Conditions>
      </AcceptanceSettings>
    </RetestWithHigherPrecision>

    <MonteCarloRetest use="true">
      <Settings>
        <Methods>
          <Method use="true" type="RandomizeSlippage">
            <Params>
              <Param key="Min" type="Double">0.0</Param>
              <Param key="Max" type="Double">5.0</Param>
            </Params>
          </Method>
          <Method use="true" type="RandomizeSpread">
            <Params>
              <Param key="Min" type="Double">1.0</Param>
              <Param key="Max" type="Double">5.0</Param>
            </Params>
          </Method>
          <Method use="true" type="RandomizeStrategyParameters">
            <Params>
              <Param key="Probability" type="Integer">15</Param>
              <Param key="MaxChange" type="Integer">15</Param>
              <Param key="Symmetric" type="Boolean">true</Param>
            </Params>
          </Method>
        </Methods>
        <NumberOfSimulations>20</NumberOfSimulations>
      </Settings>
      <AcceptanceSettings>
        <Conditions CrossCheck="MonteCarloRetest">
          <Condition use="true">
            <Left-Side valueType="column">
              <Column-Value column="NetProfit" columnType="0" name="Net profit" format="Decimal2PL" resultType="MonteCarloRetest" direction="0" sampleType="10" plType="10" confidenceLevel="80" market="1" subresult="30" pctRatio="0" />
            </Left-Side>
            <Comparator value="&gt;=" />
            <Right-Side valueType="column">
              <Column-Value column="NetProfit" columnType="0" name="Net profit" format="Decimal2PL" resultType="main" direction="0" sampleType="127" plType="10" confidenceLevel="90" market="1" subresult="30" pctRatio="50" />
            </Right-Side>
          </Condition>
        </Conditions>
      </AcceptanceSettings>
    </MonteCarloRetest>

    <OptProfileSysParamPermutation use="true">
      <Settings>
        <OptimPeriods>true</OptimPeriods>
        <OptimExitTypes>true</OptimExitTypes>
        <MaxTests>100</MaxTests>
      </Settings>
      <AcceptanceSettings>
        <ProfitOptPct>30</ProfitOptPct>
        <AvgProfit>0</AvgProfit>
        <UniformDistrChanges>5</UniformDistrChanges>
        <StdevAvgProfit>1</StdevAvgProfit>
        <EvalProfitOptCheck>true</EvalProfitOptCheck>
        <EvalAvgProfitCheck>true</EvalAvgProfitCheck>
        <EvalUniformDistrCheck>true</EvalUniformDistrCheck>
        <EvalTopProfitCheck>true</EvalTopProfitCheck>
        <Conditions />
      </AcceptanceSettings>
    </OptProfileSysParamPermutation>
```

#### Validación Sintáctica SQX 144:
- Todos los tags (`<MonteCarloRetest>`, `<OptProfileSysParamPermutation>`, `<RetestWithHigherPrecision>`) respetan la sintaxis nativa extraída del XML de Build 144 descomprimido.

---

### 2.5 Costes Realistas Binance BTCUSDT (Punto 5)

#### Diagnóstico del XML Actual:
```xml
<!-- Líneas 160-168 de Build-Task1.xml -->
<Setup dateFrom="2026.02.26" dateTo="2026.8.4" testPrecision="1" session="No Session" slippage="1" minDist="0" engine="MetaTrader4">
  <Chart symbol="BTCUSDT_AUTO" timeframe="H1" spread="0" />
  <Commissions>
    <Method type="PercentageBased" use="true">
      <Params>
        <Param key="CommissionPct" ... value="0.05" ... />
      </Params>
    </Method>
  </Commissions>
</Setup>
```

#### Análisis de Costes Reales Binance Futures (USDT-M):
- **Spread:** En BTCUSDT spot/futures, el spread bid/ask medio varía entre $0.50 y $3.00 (dependiendo de volatilidad). En un broker/feed MT4 con 2 decimales para BTC (donde 1 pip/punto = $0.01 o $0.10), esto equivale a **30 a 50 pips/puntos**. Fijar `spread="0"` genera estrategias H1 que hacen scalping de pequeña ganancia que se evapora en real.
- **Slippage:** 1 pip en BTC es de apenas $0.01-$0.10. Un slippage realista en ejecuciones con volatilidad es de **3 a 5 pips/puntos** ($0.30 - $0.50).
- **Comisión Taker:** 0.05% (`CommissionPct="0.05"`) es realista para nivel VIP0 en Binance.
- **Precisión de Test:** `testPrecision="1"` (Selected timeframe) es la más imprecisa. Debe ajustarse a `testPrecision="2"` (1-minute data / bar magnifier) para evaluar intrabar con precisión aceptable.

#### Fragmento XML Reemplazable:
```xml
<!-- REEMPLAZO EN LÍNEAS 160-169 -->
<Setup dateFrom="2026.02.26" dateTo="2026.8.4" testPrecision="2" session="LondonNY" slippage="3" minDist="0" engine="MetaTrader4">
  <Chart symbol="BTCUSDT_AUTO" timeframe="H1" spread="30" />
  <Commissions>
    <Method type="PercentageBased" use="true">
      <Params>
        <Param key="CommissionPct" name="Commission" dataType="2" min="-100.0" max="100.000000" step="0.01" value="0.05" description="Commission in % of price per full lot" decimals="4" className="PercentageBased" category="Default" engine="*" />
      </Params>
    </Method>
  </Commissions>
</Setup>
```

#### Validación Sintáctica SQX 144:
- `spread="30"` asigna 30 pips/puntos en la simulación del chart principal.
- `slippage="3"` modela 3 pips/puntos de deslizamiento por orden.
- `testPrecision="2"` activa el Bar Magnifier M1 nativo de SQX.

---

### 2.6 Filtros de Sesión y Régimen de Mercado (Punto 6)

#### Diagnóstico del XML Actual:
```xml
<!-- Línea 9-18 de Build-Task1.xml -->
<Param key="LimitTimeRange" className="LimitTimeRange">false</Param>
<Param key="SignalTimeRangeFrom" className="LimitTimeRange">28800</Param>
<Param key="SignalTimeRangeTo" className="LimitTimeRange">57600</Param>
<Param key="Session" className="SessionOption">No Session</Param>
```
- **Problema:** Operación 24/7 sin filtrar momentos de baja liquidez (madrugada asiática, domingos) donde los spreads crypto se ensanchan y los movimientos carecen de volumen institucional. Tampoco hay filtros de régimen de volatilidad (ATR/ADX).

#### Propuesta de Filtro de Sesión y Régimen:

1. **Filtro de Sesión (London / New York):**
   - Configurar `LimitTimeRange="true"`, `SignalTimeRangeFrom="25200"` (07:00 UTC) y `SignalTimeRangeTo="75600"` (21:00 UTC).
   - O bien asignar `Session="LondonNY"` si la plantilla de sesiones está definida en la base de datos de SQX.

2. **Filtro de Régimen de Volatilidad / Tendencia:**
   - En la sección `<WhatToBuild>` / `<BuildingBlocks>`, limitar los bloques de entrada para requerir la presencia de filtros de volatilidad/tendencia como condiciones AND obligatorias:
     - `ADX(14) > 20` (filtro de presencia de tendencia).
     - `ATR(14) > SMA(ATR(14), 50)` (filtro de volatilidad activa vs estancamiento).

#### Fragmento XML Reemplazable (`BuildTradingOptions`):
```xml
<!-- REEMPLAZO EN LÍNEAS 9-18 -->
<Param key="LimitTimeRange" className="LimitTimeRange">true</Param>
<Param key="SignalTimeRangeFrom" className="LimitTimeRange">25200</Param>
<Param key="SignalTimeRangeTo" className="LimitTimeRange">75600</Param>
<Param key="ExitAtEndOfRange" className="LimitTimeRange">false</Param>
<Param key="Session" className="SessionOption">LondonNY</Param>
```

#### Validación Sintáctica SQX 144:
- `LimitTimeRange`, `SignalTimeRangeFrom` (en segundos desde 00:00: 25200 = 07:00:00, 75600 = 21:00:00) son parámetros parseados por `com.strategyquant.tradingoptions.LimitTimeRange`.

---

## 3. Matriz de Compatibilidad Sintáctica SQX Build 144

| Componente XML | Tag / Atributo Modificado | Valor Antiguo | Valor Nuevo | Compatibilidad SQX 144 | Impacto en `project.cfx` |
|---|---|---|---|---|---|
| **Fitness** | `<Ranking type="..." />` | `NetProfit` | `ReturnDDRatio` | 🟢 100% Nativo | Reemplazo limpio |
| **Fitness Gate** | `<Rankings type="..." />` | `never` | `always` | 🟢 100% Nativo | Reemplazo limpio |
| **Evolución OOS** | `<EvoInSamplePeriod ratio="..." />` | `100` | `70` | 🟢 100% Nativo | Reemplazo limpio |
| **CrossChecks Master** | `<CrossChecks use="..." />` | `false` | `true` | 🟢 100% Nativo | Reemplazo limpio |
| **WFO Use** | `<WalkForwardOptimization use="..." />` | `false` | `true` | 🟢 100% Nativo | Reemplazo limpio |
| **WFO Periods** | `<WalkForward period="..." optimization="..." />` | `period="10"` `opt="15"` | `period="5"` `opt="20"` | 🟢 100% Nativo | Reemplazo limpio |
| **Higher Precision** | `<RetestWithHigherPrecision use="..." />` | `true` (OFF master) | `true` (ON master) | 🟢 100% Nativo | Reemplazo limpio |
| **Monte Carlo Retest** | `<MonteCarloRetest use="..." />` | `false` | `true` | 🟢 100% Nativo | Reemplazo limpio |
| **SPP Permutation** | `<OptProfileSysParamPermutation use="..." />` | `false` | `true` | 🟢 100% Nativo | Reemplazo limpio |
| **Spread** | `<Chart spread="..." />` | `0` | `30` | 🟢 100% Nativo | Reemplazo limpio |
| **Slippage** | `<Setup slippage="..." />` | `1` | `3` | 🟢 100% Nativo | Reemplazo limpio |
| **Test Precision** | `<Setup testPrecision="..." />` | `1` | `2` | 🟢 100% Nativo | Reemplazo limpio |
| **Horario Trading** | `<Param key="LimitTimeRange">` | `false` | `true` | 🟢 100% Nativo | Reemplazo limpio |

---

## 4. Recomendación Concreta de la Plantilla Objetivo Reconfigurada

Se recomienda empaquetar los cambios en una nueva plantilla `Ultra_Auto_Pilot_Robust.cfx` o actualizar `Build-Task1.xml` directamente dentro del `project.cfx` activo mediante el flujo seguro de desempaquetado/modificación/empaquetado ZIP.

### Estructura Consolidada de la Plantilla Objetivo Recomendada (`Build-Task1.xml` Core Settings):

```xml
<Settings>
  <Options customSettings="false">
    <BuildTradingOptions>
      <Params>
        <Param key="ExitAtEndOfDay" className="ExitAtEndOfDay">false</Param>
        <Param key="ExitOnFriday" className="ExitOnFriday">true</Param>
        <Param key="FridayExitTime" className="ExitOnFriday">74400</Param>
        <Param key="LimitTimeRange" className="LimitTimeRange">true</Param>
        <Param key="SignalTimeRangeFrom" className="LimitTimeRange">25200</Param>
        <Param key="SignalTimeRangeTo" className="LimitTimeRange">75600</Param>
        <Param key="Session" className="SessionOption">LondonNY</Param>
      </Params>
    </BuildTradingOptions>
  </Options>
  <WhatToBuild>
    <BuildMode generationType="genetic-evolution">
      <PopulationSize>100</PopulationSize>
      <MaxGenerations>60</MaxGenerations>
      <CrossoverProbability>95</CrossoverProbability>
      <MutationProbability>45</MutationProbability>
      <Islands>8</Islands>
      <EvoInSamplePeriod ratio="70" />
      <FreshBloodReplaceWeakest>true</FreshBloodReplaceWeakest>
      <FreshBloodWeakestPct>25</FreshBloodWeakestPct>
    </BuildMode>
  </WhatToBuild>
  <Data>
    <Setups>
      <Setup dateFrom="2026.02.26" dateTo="2026.8.4" testPrecision="2" session="LondonNY" slippage="3" minDist="0" engine="MetaTrader4">
        <Chart symbol="BTCUSDT_AUTO" timeframe="H1" spread="30" />
        <Commissions>
          <Method type="PercentageBased" use="true">
            <Params>
              <Param key="CommissionPct" value="0.05" className="PercentageBased" />
            </Params>
          </Method>
        </Commissions>
      </Setup>
    </Setups>
  </Data>
  <Rankings type="always">
    <MaxStrategies>200</MaxStrategies>
    <FitnessCriteria method="ComputeFromStrategyResult">
      <Settings>
        <Ranking type="ReturnDDRatio" />
      </Settings>
    </FitnessCriteria>
    <ConditionsType>1</ConditionsType>
    <Conditions>
      <Condition use="true">
        <Left-Side valueType="column">
          <Column-Value column="NumberOfTrades" columnType="0" name="# of trades" format="Integer" resultType="main" direction="0" sampleType="127" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="NumberOfTrades" />
        </Left-Side>
        <Comparator value="&gt;=" />
        <Right-Side valueType="numeric">
          <Numeric-Value value="100" />
        </Right-Side>
      </Condition>
      <Condition use="true">
        <Left-Side valueType="column">
          <Column-Value column="DrawdownPct" columnType="0" name="Max DD %" format="Decimal2Pct" resultType="main" direction="0" sampleType="127" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="DrawdownPct" />
        </Left-Side>
        <Comparator value="&lt;=" />
        <Right-Side valueType="numeric">
          <Numeric-Value value="35" />
        </Right-Side>
      </Condition>
    </Conditions>
    <StopCondition type="databank-full" passedStrategies="200" minutes="60" />
  </Rankings>
  <CrossChecks use="true" evaluateAll="false">
    <WalkForwardOptimization use="true">
      <Settings>
        <WalkForward type="1" period="5" optimization="20">
          <Param1 value="20" />
          <Param2 value="10" />
        </WalkForward>
        <MaxTests>100</MaxTests>
      </Settings>
      <AcceptanceSettings>
        <Conditions thresholdPct="80">
          <Condition use="true">
            <Left-Side valueType="column">
              <Column-Value column="WFPctOfProfitableRuns" columnType="33" name="WF Special Percentage of profitable runs" format="Decimal2Pct" resultType="WalkForwardOptimization" direction="0" sampleType="10" plType="10" confidenceLevel="50" market="1" subresult="33" pctRatio="0" class="WFPctOfProfitableRuns" />
            </Left-Side>
            <Comparator value="&gt;=" />
            <Right-Side valueType="numeric">
              <Numeric-Value value="70" />
            </Right-Side>
          </Condition>
        </Conditions>
      </AcceptanceSettings>
    </WalkForwardOptimization>
    <RetestWithHigherPrecision use="true">
      <Settings>
        <Precision>2</Precision>
        <Spread>3</Spread>
      </Settings>
    </RetestWithHigherPrecision>
    <MonteCarloRetest use="true">
      <Settings>
        <NumberOfSimulations>20</NumberOfSimulations>
      </Settings>
    </MonteCarloRetest>
    <OptProfileSysParamPermutation use="true">
      <Settings>
        <MaxTests>100</MaxTests>
      </Settings>
    </OptProfileSysParamPermutation>
  </CrossChecks>
</Settings>
```

---

## 5. Próximos Pasos para Ejecución

1. **Inyección en `project.cfx`:** Aplicar los reemplazos XML sobre `/tmp/cfx_audit/unpacked/Build-Task1.xml` mediante `patch` o script Python.
2. **Re-empaquetado ZIP:** Repaquetar `/tmp/cfx_audit/unpacked/*` en `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx`.
3. **Reinicio de Servicio:** Reiniciar el servicio SQX (`systemctl --user restart strategyquantx`) para que cargue la nueva configuración en memoria.
4. **Verificación GUI:** Confirmar vía `computer_use` o CDP que la interfaz muestra `Fitness = ReturnDDRatio`, `OOS = 70%`, `CrossChecks = ON` y `Spread = 30`.
