# Informe de Auditoría y Verificación XML: Plan Maestro `Build-Task1.xml`

**Proyecto:** StrategyQuant X `Ultra_Auto_Pilot`  
**Fichero Auditado:** `/tmp/cfx_check/Build-Task1.xml` (desempaquetado desde `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx`)  
**Fecha de Auditoría:** 9 de Agosto de 2026  
**Tipo de Verificación:** REAL-ONLY (inspección directa del contenido en disco)

---

## 1. Resumen Ejecutivo

Se ha completado la auditoría empírica del archivo de configuración `Build-Task1.xml` extraído del proyecto `project.cfx`. El análisis confirma que el estado actual del archivo XML presenta una **aplicación parcial** de las directrices establecidas en el Plan Maestro (`15_PLAN_MAESTRO_ESTABLE_GENERADOR.md`).

* **Total Cambios Planificados:** 10
* **APLICADOS:** 4 (Puntos 2, 3, 7, 8)
* **PARCIALES:** 3 (Puntos 5, 6, 9)
* **NO APLICADOS:** 3 (Puntos 1, 4, 10)

Un hallazgo crítico de esta auditoría REAL-ONLY es la corrección sobre la hipótesis del orquestador respecto al **Punto 6 (`OptProfileSysParamPermutation`)**: la etiqueta **SÍ EXISTE** en el XML (Línea 582) con `use="true"`, pero requiere ajustar `MaxTests` de 1000 a 100.

---

## 2. Tabla de Verificación de los 10 Cambios

| ID | Parámetro / Módulo | Estado en Plan Maestro | Estado Actual XML | Líneas XML | Clasificación |
|---|---|---|---|---|---|
| 1 | `Rankings` | `type="always"`, `Ranking type="ReturnDDRatio"`, trades>=100, MaxDD%<=35 | `type="never"`, `Ranking type="NetProfit"`, sin condiciones | L175-L183 | **NO APLICADO** |
| 2 | `EvoInSamplePeriod` | `ratio="70"` | `ratio="70"` | L85 | **APLICADO** |
| 3 | `CrossChecks` | `use="true"` | `use="true" evaluateAll="false"` | L215 | **APLICADO** |
| 4 | `WalkForwardOptimization` | `use="true"`, `period="5"`, `optimization="20"`, WFPctOfProfitableRuns>=70 | `use="false"`, `period="10"`, `optimization="15"` (WFPct prediseñado) | L247-L256 | **NO APLICADO** |
| 5 | `MonteCarloRetest` | `use="true"`, `NumberOfSimulations="20"` | `use="true"`, `NumberOfSimulations="10"` | L380, L422 | **PARCIAL** |
| 6 | `OptProfileSysParamPermutation` | `use="true"`, `MaxTests="100"` | Bloque EXISTE: `use="true"`, `MaxTests="1000"` | L582-L587 | **PARCIAL** |
| 7 | `Chart` Spread (BTC) | `spread="30"` | `spread="30"` | L161 | **APLICADO** |
| 8 | `Setup` Slippage (BTC) | `slippage="3"` | `slippage="3"` | L160 | **APLICADO** |
| 9 | Filtro de Sesión (Doble Capa) | Capa A (`Setup`): `LondonNY`<br>Capa B (`BuildTradingOptions`): `LimitTimeRange=true`, From=25200, To=75600, `Session=LondonNY` | Capa A: `session="LondonNY"` (**Aplicado**)<br>Capa B: `LimitTimeRange=false`, From=28800, To=57600, `Session="No Session"` (**No Aplicado**) | L160 (Capa A)<br>L9-L18 (Capa B) | **PARCIAL** |
| 10 | Parámetros Genéticos | `PopulationSize="100"`, `MaxGenerations="60"` | `PopulationSize="80"`, `MaxGenerations="40"` | L72-L73 | **NO APLICADO** |

---

## 3. Análisis Detallado por Punto y Fragmentos XML Exactos

### Punto 1: Criterio de Ranking y Filtros de Entrada a Databank
* **Ubicación:** Líneas 175–183.
* **Estado:** **NO APLICADO**.
* **Fragmento Actual Exacto:**
```xml
  <Rankings type="never">
    <MaxStrategies>24</MaxStrategies>
    <FitnessCriteria method="ComputeFromStrategyResult">
      <Settings>
        <Ranking type="NetProfit" />
      </Settings>
    </FitnessCriteria>
    <ConditionsType>1</ConditionsType>
    <Conditions />
```
* **Fragmento Propuesto Exacto:**
```xml
  <Rankings type="always">
    <MaxStrategies>24</MaxStrategies>
    <FitnessCriteria method="ComputeFromStrategyResult">
      <Settings>
        <Ranking type="ReturnDDRatio" />
      </Settings>
    </FitnessCriteria>
    <ConditionsType>1</ConditionsType>
    <Conditions>
      <Condition use="true">
        <Left-Side valueType="column">
          <Column-Value column="NumberOfTrades" columnType="0" format="Integer" resultType="main" direction="0" sampleType="10" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="NumberOfTrades" />
        </Left-Side>
        <Comparator value="&gt;=" />
        <Right-Side valueType="numeric">
          <Numeric-Value value="100" />
        </Right-Side>
      </Condition>
      <Condition use="true">
        <Left-Side valueType="column">
          <Column-Value column="DrawdownPct" columnType="0" format="Decimal2Pct" resultType="main" direction="0" sampleType="10" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="DrawdownPct" />
        </Left-Side>
        <Comparator value="&lt;=" />
        <Right-Side valueType="numeric">
          <Numeric-Value value="35" />
        </Right-Side>
      </Condition>
    </Conditions>
```

---

### Punto 2: Evolución In-Sample / Out-of-Sample Ratio
* **Ubicación:** Línea 85.
* **Estado:** **APLICADO**.
* **Fragmento Actual Exacto:**
```xml
      <EvoInSamplePeriod ratio="70" />
```

---

### Punto 3: Validación Cruzada (CrossChecks Main Switch)
* **Ubicación:** Línea 215.
* **Estado:** **APLICADO**.
* **Fragmento Actual Exacto:**
```xml
  <CrossChecks use="true" evaluateAll="false">
```

---

### Punto 4: Optimización Walk-Forward (WFO)
* **Ubicación:** Líneas 247–256.
* **Estado:** **NO APLICADO**.
* **Fragmento Actual Exacto:**
```xml
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
* **Fragmento Propuesto Exacto:**
```xml
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
```
* **Nota sobre Condiciones:** La condición `<Condition use="true">` para `WFPctOfProfitableRuns > 70` ya existe dentro de `<AcceptanceSettings>` (Líneas 277–285), pero el módulo principal está desactivado (`use="false"`).

---

### Punto 5: Simulación Monte Carlo Retest
* **Ubicación:** Líneas 380 y 422.
* **Estado:** **PARCIAL**.
* **Fragmento Actual Exacto:**
```xml
    <MonteCarloRetest use="true">
      <Settings>
        <!-- ... métodos ... -->
        <NumberOfSimulations>10</NumberOfSimulations>
      </Settings>
```
* **Fragmento Propuesto Exacto:**
```xml
    <MonteCarloRetest use="true">
      <Settings>
        <!-- ... métodos ... -->
        <NumberOfSimulations>20</NumberOfSimulations>
      </Settings>
```

---

### Punto 6: Permutación de Parámetros del Sistema (SPP)
* **Ubicación:** Líneas 582–587.
* **Estado:** **PARCIAL** (Aclaración REAL-ONLY: El bloque **SÍ EXISTE** en el XML, contrariamente a lo supuesto inicialmente).
* **Fragmento Actual Exacto:**
```xml
    <OptProfileSysParamPermutation use="true">
      <Settings>
        <OptimPeriods>true</OptimPeriods>
        <OptimExitTypes>true</OptimExitTypes>
        <MaxTests>1000</MaxTests>
      </Settings>
```
* **Fragmento Propuesto Exacto:**
```xml
    <OptProfileSysParamPermutation use="true">
      <Settings>
        <OptimPeriods>true</OptimPeriods>
        <OptimExitTypes>true</OptimExitTypes>
        <MaxTests>100</MaxTests>
      </Settings>
```

---

### Puntos 7 y 8: Spread y Slippage en Setup Principal (BTCUSDT_AUTO H1)
* **Ubicación:** Líneas 160–161.
* **Estado:** **APLICADO**.
* **Fragmento Actual Exacto:**
```xml
      <Setup dateFrom="2026.02.26" dateTo="2026.8.4" testPrecision="1" session="LondonNY" slippage="3" minDist="0" engine="MetaTrader4">
        <Chart symbol="BTCUSDT_AUTO" timeframe="H1" spread="30" />
```

---

### Punto 9: Configuración de Sesión y Horario de Señales (Doble Capa)
* **Ubicación:** Línea 160 (Capa A) y Líneas 9–18 (Capa B).
* **Estado:** **PARCIAL**.
* **Capa A (`Setup` de Datos - L160):** `session="LondonNY"` está **APLICADO**.
* **Capa B (`BuildTradingOptions` Params - L9-L18):** **NO APLICADO**.
* **Fragmento Actual Exacto (Capa B):**
```xml
        <Param key="LimitTimeRange" className="LimitTimeRange">false</Param>
        <Param key="SignalTimeRangeFrom" className="LimitTimeRange">28800</Param>
        <Param key="SignalTimeRangeTo" className="LimitTimeRange">57600</Param>
        <Param key="ExitAtEndOfRange" className="LimitTimeRange">false</Param>
        <Param key="MaxTradesPerDay" className="MaxTradesPerDay">0</Param>
        <Param key="MinimumSL" className="MinMaxSLPT">0</Param>
        <Param key="MaximumSL" className="MinMaxSLPT">0</Param>
        <Param key="MinimumPT" className="MinMaxSLPT">0</Param>
        <Param key="MaximumPT" className="MinMaxSLPT">0</Param>
        <Param key="Session" className="SessionOption">No Session</Param>
```
* **Fragmento Propuesto Exacto (Capa B):**
```xml
        <Param key="LimitTimeRange" className="LimitTimeRange">true</Param>
        <Param key="SignalTimeRangeFrom" className="LimitTimeRange">25200</Param>
        <Param key="SignalTimeRangeTo" className="LimitTimeRange">75600</Param>
        <Param key="ExitAtEndOfRange" className="LimitTimeRange">false</Param>
        <Param key="MaxTradesPerDay" className="MaxTradesPerDay">0</Param>
        <Param key="MinimumSL" className="MinMaxSLPT">0</Param>
        <Param key="MaximumSL" className="MinMaxSLPT">0</Param>
        <Param key="MinimumPT" className="MinMaxSLPT">0</Param>
        <Param key="MaximumPT" className="MinMaxSLPT">0</Param>
        <Param key="Session" className="SessionOption">LondonNY</Param>
```
* **Conversión de Horarios a Segundos UTC:**
  * `25200` segundos = 07:00:00 UTC (Inicio de sesión Londres).
  * `75600` segundos = 21:00:00 UTC (Cierre de sesión New York).

---

### Punto 10: Tamaño de Población y Generaciones Máximas
* **Ubicación:** Líneas 71–74.
* **Estado:** **NO APLICADO**.
* **Fragmento Actual Exacto:**
```xml
    <BuildMode generationType="genetic-evolution">
      <PopulationSize>80</PopulationSize>
      <MaxGenerations>40</MaxGenerations>
```
* **Fragmento Propuesto Exacto:**
```xml
    <BuildMode generationType="genetic-evolution">
      <PopulationSize>100</PopulationSize>
      <MaxGenerations>60</MaxGenerations>
```

---

## 4. Análisis de Datos Adicionales y Configuraciones Existentes

### A. Rango Out-of-Sample (OOS) Prediseñado
En las líneas 171–173 se confirma la presencia del rango OOS:
```xml
    <OutOfSample showGraph="false">
      <Range dateFrom="2026.06.18" dateTo="2026.8.4" />
    </OutOfSample>
```
* **Rango In-Sample (IS):** 26-Feb-2026 a 17-Jun-2026 (~3.7 meses).
* **Rango Out-of-Sample (OOS):** 18-Jun-2026 a 04-Ago-2026 (~1.5 meses, 30% del total de 5.2 meses).

### B. Setup Residual Integrado (`EURUSD_M1_dukas`)
En las líneas 218–228 se identifica un segundo setup de prueba en la sección `<CrossChecks><RetestOnAdditionalMarkets>`:
```xml
        <Setups detailed="true">
          <Setup dateFrom="2003.5.5" dateTo="2019.12.13" testPrecision="1" session="No Session" slippage="1" minDist="0" engine="MetaTrader4">
            <Chart symbol="EURUSD_M1_dukas" timeframe="H1" spread="2" />
            <!-- ... -->
          </Setup>
        </Setups>
```
* **Directiva:** Este setup secundario se encuentra inactivo (`RetestOnAdditionalMarkets use="false"`) y **NO DEBE SER MODIFICADO**. Las sustituciones de Find/Replace deben acotarse estrictamente al setup principal de `BTCUSDT_AUTO` y al bloque `<BuildTradingOptions>`.

---

## 5. Análisis Sintáctico del XML

El análisis estructural de `Build-Task1.xml` (13,906 líneas, 1,225,608 bytes) confirma lo siguiente:
1. **Prolog y Estructura Raíz:** Correctamente encabalgado por `<Settings>` y cerrado en la línea 13,906 con `</Settings>`.
2. **Integridad de Bloques Principal/CrossChecks:** Todos los elementos (`<WhatToBuild>`, `<Data>`, `<Rankings>`, `<CrossChecks>`, `<BuildingBlocks>`) están anidados sin desbordamientos de etiquetas.
3. **Respeto a la Sintaxis XML de StrategyQuant X:** Los tipos de datos de atributos (`use="true/false"`, `type="..."`, etc.) cumplen con el esquema interno del motor.

---

## 6. Análisis de Riesgos Específicos

1. **Riesgo WFO en Serie H1 Corta (5.2 meses totales):**
   * **Insumo:** 5.2 meses en timeframe H1 representan aproximadamente 3,744 velas.
   * **Efecto de 5 Periodos:** Cada periodo de Walk-Forward abarca solo 1 mes de datos (~720 velas) para optimizar.
   * **Mitigación:** Es imprescindible mantener `WFPctOfProfitableRuns >= 70%` para rechazar estrategias con sobreajuste en ventanas tan reducidas.
2. **Riesgo por Cómputo Excesivo en SPP (`MaxTests`):**
   * El valor actual de `MaxTests="1000"` en SPP generaría 1,000 permutaciones por cada candidato que supere los filtros previos, multiplicando exponencialmente el tiempo de generación. Reducirlo a `MaxTests="100"` es crítico.
3. **Riesgo por Inconsistencia en la Doble Capa de Sesiones:**
   * Tener `session="LondonNY"` en el Setup de datos pero `LimitTimeRange="false"` con rango `28800-57600` (08:00–16:00 UTC) en `BuildTradingOptions` provoca que el generador de reglas no fuerce restricciones horarias en los bloques de entrada, permitiendo entradas fuera del horario previsto.

---

## 7. Orden de Aplicación Seguro (Secuencia de Edit/Replace)

Para reconfigurar el archivo `Build-Task1.xml` sin romper la validez sintáctica ni alterar partes no deseadas, se debe ejecutar la siguiente secuencia ordenada de reemplazos exactos:

### Paso 1: Reconfigurar Parámetros Genéticos (Punto 10)
* **Buscar:**
```xml
    <BuildMode generationType="genetic-evolution">
      <PopulationSize>80</PopulationSize>
      <MaxGenerations>40</MaxGenerations>
```
* **Reemplazar por:**
```xml
    <BuildMode generationType="genetic-evolution">
      <PopulationSize>100</PopulationSize>
      <MaxGenerations>60</MaxGenerations>
```

### Paso 2: Reconfigurar Filtro de Sesión en Layer B (Punto 9)
* **Buscar:**
```xml
        <Param key="LimitTimeRange" className="LimitTimeRange">false</Param>
        <Param key="SignalTimeRangeFrom" className="LimitTimeRange">28800</Param>
        <Param key="SignalTimeRangeTo" className="LimitTimeRange">57600</Param>
        <Param key="ExitAtEndOfRange" className="LimitTimeRange">false</Param>
        <Param key="MaxTradesPerDay" className="MaxTradesPerDay">0</Param>
        <Param key="MinimumSL" className="MinMaxSLPT">0</Param>
        <Param key="MaximumSL" className="MinMaxSLPT">0</Param>
        <Param key="MinimumPT" className="MinMaxSLPT">0</Param>
        <Param key="MaximumPT" className="MinMaxSLPT">0</Param>
        <Param key="Session" className="SessionOption">No Session</Param>
```
* **Reemplazar por:**
```xml
        <Param key="LimitTimeRange" className="LimitTimeRange">true</Param>
        <Param key="SignalTimeRangeFrom" className="LimitTimeRange">25200</Param>
        <Param key="SignalTimeRangeTo" className="LimitTimeRange">75600</Param>
        <Param key="ExitAtEndOfRange" className="LimitTimeRange">false</Param>
        <Param key="MaxTradesPerDay" className="MaxTradesPerDay">0</Param>
        <Param key="MinimumSL" className="MinMaxSLPT">0</Param>
        <Param key="MaximumSL" className="MinMaxSLPT">0</Param>
        <Param key="MinimumPT" className="MinMaxSLPT">0</Param>
        <Param key="MaximumPT" className="MinMaxSLPT">0</Param>
        <Param key="Session" className="SessionOption">LondonNY</Param>
```

### Paso 3: Reconfigurar Rankings y Criterios de Databank (Punto 1)
* **Buscar:**
```xml
  <Rankings type="never">
    <MaxStrategies>24</MaxStrategies>
    <FitnessCriteria method="ComputeFromStrategyResult">
      <Settings>
        <Ranking type="NetProfit" />
      </Settings>
    </FitnessCriteria>
    <ConditionsType>1</ConditionsType>
    <Conditions />
```
* **Reemplazar por:**
```xml
  <Rankings type="always">
    <MaxStrategies>24</MaxStrategies>
    <FitnessCriteria method="ComputeFromStrategyResult">
      <Settings>
        <Ranking type="ReturnDDRatio" />
      </Settings>
    </FitnessCriteria>
    <ConditionsType>1</ConditionsType>
    <Conditions>
      <Condition use="true">
        <Left-Side valueType="column">
          <Column-Value column="NumberOfTrades" columnType="0" format="Integer" resultType="main" direction="0" sampleType="10" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="NumberOfTrades" />
        </Left-Side>
        <Comparator value="&gt;=" />
        <Right-Side valueType="numeric">
          <Numeric-Value value="100" />
        </Right-Side>
      </Condition>
      <Condition use="true">
        <Left-Side valueType="column">
          <Column-Value column="DrawdownPct" columnType="0" format="Decimal2Pct" resultType="main" direction="0" sampleType="10" plType="10" confidenceLevel="50" market="1" subresult="30" pctRatio="0" class="DrawdownPct" />
        </Left-Side>
        <Comparator value="&lt;=" />
        <Right-Side valueType="numeric">
          <Numeric-Value value="35" />
        </Right-Side>
      </Condition>
    </Conditions>
```

### Paso 4: Activar y Reconfigurar Walk-Forward Optimization (Punto 4)
* **Buscar:**
```xml
    <WalkForwardOptimization use="false">
      <Settings>
        <WalkForward type="1" period="10" optimization="15">
          <Param1 value="20" />
          <Param2 value="10" />
        </WalkForward>
```
* **Reemplazar por:**
```xml
    <WalkForwardOptimization use="true">
      <Settings>
        <WalkForward type="1" period="5" optimization="20">
          <Param1 value="20" />
          <Param2 value="10" />
        </WalkForward>
```

### Paso 5: Reconfigurar Número de Simulaciones Monte Carlo (Punto 5)
* **Buscar:**
```xml
        <NumberOfSimulations>10</NumberOfSimulations>
      </Settings>
      <AcceptanceSettings>
        <Conditions CrossCheck="MonteCarloRetest">
```
* **Reemplazar por:**
```xml
        <NumberOfSimulations>20</NumberOfSimulations>
      </Settings>
      <AcceptanceSettings>
        <Conditions CrossCheck="MonteCarloRetest">
```

### Paso 6: Ajustar MaxTests en SPP (Punto 6)
* **Buscar:**
```xml
    <OptProfileSysParamPermutation use="true">
      <Settings>
        <OptimPeriods>true</OptimPeriods>
        <OptimExitTypes>true</OptimExitTypes>
        <MaxTests>1000</MaxTests>
      </Settings>
```
* **Reemplazar por:**
```xml
    <OptProfileSysParamPermutation use="true">
      <Settings>
        <OptimPeriods>true</OptimPeriods>
        <OptimExitTypes>true</OptimExitTypes>
        <MaxTests>100</MaxTests>
      </Settings>
```
