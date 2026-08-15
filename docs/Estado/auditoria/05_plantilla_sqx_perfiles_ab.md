# 05 — Plantillas de Configuración SQX Builder: Perfil A (Growth/Ultra) y Perfil B (Fondeo)

> **Documento operativo** — listo para ejecución manual por un experto o por un agente `computer_use` en la GUI real de SQX (Xvfb :99, Electron, `http://127.0.0.1:5050`).
>
> Fecha: 2026-08-09 | Proyecto: Ultrarentable | Motor: StrategyQuant X

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Perfil A — Growth/Ultra (Miles de %)](#2-perfil-a--growthmiles-de-)
3. [Perfil B — Fondeo/Prop Firm (DD Diario Intrabar)](#3-perfil-b--fondeoprop-firm)
4. [Walk-Forward Anclado (Común a Ambos Perfiles)](#4-walk-forward-anclado)
5. [Pipeline de Búsqueda (Reemplaza Grid)](#5-pipeline-de-búsqueda)
6. [Mapa Completo: Pestaña GUI → Configuración](#6-mapa-completo-pestaña-gui--configuración)
7. [Checklist de Verificación Pre-Run](#7-checklist-de-verificación-pre-run)
8. [Instrucciones computer_use Paso a Paso](#8-instrucciones-computer_use-paso-a-paso)

---

## 1. Resumen Ejecutivo

| Dimensión | Perfil A — Growth/Ultra | Perfil B — Fondeo/Prop Firm |
|---|---|---|
| **Objetivo** | CAGR máximo OOS con DD acotado | Pasar challenge + sobrevivir 90 días |
| **Fitness** | `CAGR_OOS × estabilidad` | `P(pasar_challenge) × P(sobrevivir_90d)` |
| **Position Sizing** | Kelly fraccional acotado `f ∈ [0.005, 0.05]` | Fijo conservador: 0.5-1% riesgo/trade |
| **DD máximo** | Intradía ≤ 35% | Diario intrabar ≤ 0.6×límite diario; Total ≤ 0.5×límite total |
| **Building Blocks** | Momentum/Breakout/Volatilidad | Mean Reversion/Trend Multi-TF |
| **Filtros** | Sesión (Londres/NY) + Régimen (ATR/ADX) | Sesión + Régimen conservador |
| **Trades OOS mín** | ≥ 150 | ≥ 100 |
| **Walk-Forward** | 6 folds anclado, gap 1 semana | 6 folds anclado, gap 1 semana |

---

## 2. Perfil A — Growth/Ultra (Miles de %)

### 2.1 Fitness Function

```
fitness_A = CAGR_OOS × estabilidad

donde:
  estabilidad = (1 - CV_CAGR_entre_folds) × ratio_folds_positivos
  CV_CAGR = std(CAGR_fold_i) / mean(CAGR_fold_i)
  ratio_folds_positivos = folds_con_profit_positivo / total_folds
```

**Implementación en SQX:**
- **Pestaña**: `Rankings & Filtering` → `Fitness` / `Custom Fitness`
- **Campo principal**: Seleccionar `Annual % Return` como fitness primaria
- **Peso secundario**: `Stability` o `Ret/DD Ratio` como criterio secundario
- **Custom formula** (si disponible): `AnnualReturn * (1 - StdDevReturns/AvgReturn) * OOSPositiveFoldsRatio`

### 2.2 Restricciones Duras (DESCARTE, no penalización)

| Restricción | Valor | Pestaña SQX | Campo exacto |
|---|---|---|---|
| Trades OOS | ≥ 150 | `Rankings & Filtering` → `Conditions` | `Number of trades (OOS) >= 150` |
| Folds OOS positivos | ≥ 70% | `Rankings & Filtering` → `Conditions` | Custom: `OOS Positive Periods >= 70%` |
| Max DD intradía | ≤ 35% | `Rankings & Filtering` → `Conditions` | `Max drawdown % <= 35` |
| Peor mes | ≥ -20% | `Rankings & Filtering` → `Conditions` | `Worst month return >= -20%` |
| Tiempo recuperación máx | ≤ 12 meses | `Rankings & Filtering` → `Conditions` | `Max stagnation period (days) <= 365` |
| Profit Factor OOS | ≥ 1.0 | `Rankings & Filtering` → `Conditions` | `Profit factor (OOS) >= 1.0` |
| Ret/DD Ratio | ≥ 2.0 | `Rankings & Filtering` → `Conditions` | `Return / Drawdown >= 2.0` |

### 2.3 Position Sizing — Kelly Fraccional en el Espacio de Búsqueda

**Concepto clave**: Los "miles de %" vienen del SIZING, no de la señal. Meter la fracción de riesgo como variable optimizable.

- **Pestaña**: `Money Management`
- **Configuración**:
  - **Tipo**: `Fixed % Risk` (porcentaje fijo de equity por trade)
  - **Rango de búsqueda**: `f ∈ [0.5%, 5.0%]` (equivalente a Kelly fraccional acotado)
  - **Step**: 0.25% (para 19 niveles de búsqueda: 0.5, 0.75, 1.0, ..., 5.0)
  - **Método**: Marcar el checkbox `"Optimize"` o `"Include in search space"` para que el genético explore el sizing
  - **Stop Loss vinculado**: El risk % se calcula respecto al SL; asegurar que SL está definido en Building Blocks

**Pasos en la GUI:**
1. Ir a `Money Management`
2. Seleccionar `Fixed % risk per trade`
3. En el campo de porcentaje, NO poner un valor fijo
4. Activar `Optimize this parameter`
5. Rango mínimo: `0.5` | Rango máximo: `5.0` | Step: `0.25`
6. Esto crea 19 variantes que el genético explora

### 2.4 Building Blocks de Entrada

- **Pestaña**: `Building Blocks` → `Entry conditions` / `Signals`

#### Bloques de ENTRADA habilitados (Perfil A):

| Categoría | Bloques a Habilitar | Justificación |
|---|---|---|
| **Momentum** | `ROC (Rate of Change)`, `Momentum indicator`, `RSI > 50 cross`, `MACD signal cross` | Capturan tendencia naciente |
| **Breakout** | `Donchian Channel breakout`, `Bollinger Band breakout`, `N-bar high/low breakout`, `Range breakout` | Alta asimetría: SL pequeño vs movimiento grande |
| **Volatilidad** | `ATR expansion`, `Bollinger Width expansion`, `Keltner Channel breakout`, `Volatility ratio` | Filtran entradas a momentos de movimiento real |
| **Price Action** | `Higher highs/lows`, `Inside bar breakout`, `Pin bar / hammer` | Patrones directos de precio |

#### Bloques de SALIDA habilitados:

| Tipo | Bloques | Configuración |
|---|---|---|
| **Stop Loss** | `Fixed SL (ATR-based)`, `Trailing stop (ATR)`, `Time stop` | ATR multiplier ∈ [1.0, 4.0] |
| **Take Profit** | `Fixed TP (ATR-based)`, `Trailing TP` | Ratio TP/SL ∈ [1.5, 5.0] |
| **Exit signal** | `RSI overbought/oversold`, `MACD cross contra`, `Momentum reversal` | Salida dinámica |

**Pasos en la GUI:**
1. Ir a `Building Blocks`
2. Expandir `Entry Signals` → habilitar SOLO los bloques listados arriba
3. DESHABILITAR bloques irrelevantes: `Mean reversion`, `Oscillator oversold entries`, `Counter-trend`
4. Expandir `Exit Conditions` → configurar SL/TP con rangos ATR
5. En `Rules Complexity`: `maxConditions = 4-6`, `maxExitConditions = 3-4`, `maxPeriod = 50`

### 2.5 Filtros de Sesión y Régimen

- **Pestaña**: `Trading Options` → `Trading hours` / `Session filter`
- **Pestaña alternativa**: `Building Blocks` → `Conditions` (como condición adicional de entrada)

#### Filtro de Sesión:

| Sesión | Horario UTC | Configuración SQX |
|---|---|---|
| **Londres** | 07:00 – 16:00 UTC | `Trading Options` → `Allow trading` → From: 07:00, To: 16:00 |
| **New York** | 13:00 – 21:00 UTC | `Trading Options` → `Allow trading` → From: 13:00, To: 21:00 |
| **Solape LON/NY** | 13:00 – 16:00 UTC | Variante más restrictiva: From: 13:00, To: 16:00 |

**Implementación**: Incluir el filtro de hora en el espacio de búsqueda:
- Marcar `Optimize` en el campo From y To
- From range: [06:00, 14:00], To range: [15:00, 22:00]
- El genético encontrará la ventana óptima

#### Filtro de Régimen (como condición de entrada):

| Indicador | Condición | Pestaña | Rango búsqueda |
|---|---|---|---|
| **ADX** | ADX > umbral → tendencia activa | `Building Blocks` → `Entry conditions` | Umbral ∈ [15, 30] |
| **ATR percentil** | ATR(14) > percentil(ATR, 50) → volatilidad suficiente | `Building Blocks` → `Entry conditions` | Percentil ∈ [30, 70] |
| **Volatilidad realizada** | StdDev(close, 20) > umbral | `Building Blocks` → `Entry conditions` | Como bloque custom |

**Pasos en la GUI:**
1. En `Building Blocks` → `Entry Conditions`
2. Añadir condición: `ADX(14) > [optimize: 15-30]`
3. Añadir condición: `ATR(14) > SMA(ATR(14), 50)` (ATR por encima de su media → vol activa)
4. Marcar ambas como `required` (AND con la señal de entrada)

---

## 3. Perfil B — Fondeo/Prop Firm

### 3.1 Fitness Function

```
fitness_B = P(pasar_challenge) × P(sobrevivir_90d | pasado)

aproximación práctica en SQX:
  fitness_B ≈ (NetReturn_OOS / target_challenge) × (1 - P_violar_DD)
           ≈ Ret/DD_Ratio_OOS × Consistency_Score
```

**Implementación en SQX:**
- **Pestaña**: `Rankings & Filtering` → `Fitness`
- **Campo principal**: `Ret/DD Ratio` como fitness primaria
- **Peso secundario**: `Stability` / `Consistency`
- **Objetivo**: Maximizar ratio retorno/drawdown OOS (no retorno bruto)

### 3.2 Restricciones Duras — DD Diario Intrabar

> **CRÍTICO**: El DD diario debe medirse **intrabar** (no sobre cierres). Requiere datos M1 o tick para reconstruir el peor punto intradiario.

| Restricción | Valor (ej. FTMO 100K) | Pestaña SQX | Campo exacto |
|---|---|---|---|
| Max DD diario intrabar | ≤ 0.6 × $5,000 = **$3,000** (≤ 3%) | `Rankings & Filtering` → `Conditions` | `Max daily drawdown <= 3%` |
| Max DD total intrabar | ≤ 0.5 × $10,000 = **$5,000** (≤ 5%) | `Rankings & Filtering` → `Conditions` | `Max drawdown % <= 5%` |
| P(violar DD diario) | ≤ 2% | Post-procesado MC | No directamente en GUI |
| Días hasta target | ≤ límite programa (ej. 30 días) | `Rankings & Filtering` → `Conditions` | Custom: `Days to reach target <= 30` |
| Trades OOS | ≥ 100 | `Rankings & Filtering` → `Conditions` | `Number of trades (OOS) >= 100` |
| Profit Factor OOS | ≥ 1.1 | `Rankings & Filtering` → `Conditions` | `Profit factor (OOS) >= 1.1` |
| Consistencia diaria | ≥ 60% días positivos | `Rankings & Filtering` → `Conditions` | `% Winning days >= 60` |

**Tabla de referencia por fondeadora:**

| Fondeadora | DD Diario | DD Total | Target | Restricción SQX DD diario | Restricción SQX DD total |
|---|---|---|---|---|---|
| FTMO 100K | 5% ($5K) | 10% ($10K) | 10% ($10K) | ≤ 3.0% | ≤ 5.0% |
| FTMO 200K | 5% ($10K) | 10% ($20K) | 10% ($20K) | ≤ 3.0% | ≤ 5.0% |
| MFF 100K | 5% ($5K) | 12% ($12K) | 8% ($8K) | ≤ 3.0% | ≤ 6.0% |
| The5ers 100K | 4% ($4K) | 6% ($6K) | 6% ($6K) | ≤ 2.4% | ≤ 3.0% |

> **Regla 0.6×/0.5×**: Siempre configurar el límite SQX MÁS ESTRICTO que el de la fondeadora. Margen de seguridad obligatorio.

### 3.3 Position Sizing — Fijo Conservador

- **Pestaña**: `Money Management`
- **Configuración**:
  - **Tipo**: `Fixed % Risk per trade`
  - **Valor fijo**: `0.5%` (NO optimizable — valor fijo conservador)
  - **Alternativa**: `Fixed lots` con tamaño conservador (ej. 0.5 lotes por $100K)
  - **NO activar** `Optimize this parameter` — el sizing es fijo por diseño en fondeo

**Pasos en la GUI:**
1. Ir a `Money Management`
2. Seleccionar `Fixed % risk per trade`
3. Valor: `0.5`
4. Asegurar que `Optimize` está DESMARCADO
5. El SL define el tamaño del lote automáticamente

### 3.4 Building Blocks de Entrada — Conservadores

- **Pestaña**: `Building Blocks`

#### Bloques de ENTRADA habilitados (Perfil B):

| Categoría | Bloques a Habilitar | Justificación |
|---|---|---|
| **Mean Reversion** | `RSI oversold/overbought`, `Bollinger Band bounce`, `CCI extreme`, `Stochastic cross` | Operaciones de reversión con RR acotado |
| **Trend Multi-TF** | `EMA cross (confirmado por TF superior)`, `MACD histogram direction`, `Parabolic SAR` | Tendencia confirmada en múltiples marcos |
| **Filtro de rango** | `ADX < umbral` (para mean reversion), `ADX > umbral` (para trend) | Contexto del tipo de mercado |
| **Patrones conservadores** | `Inside bar`, `Engulfing candle`, `Morning/Evening star` | Patrones con expectativa definida |

#### Bloques de SALIDA habilitados (Perfil B):

| Tipo | Bloques | Configuración |
|---|---|---|
| **Stop Loss** | `Fixed SL (ATR-based)` OBLIGATORIO | ATR multiplier ∈ [1.0, 2.5] (MÁS AJUSTADO que Perfil A) |
| **Take Profit** | `Fixed TP`, `Partial close at target` | TP/SL ratio ∈ [1.0, 2.5] |
| **Time stop** | `Close after N bars` | N ∈ [5, 30] barras (no mantener trades muertos) |
| **DD guard** | `Close all if daily loss > X%` | X = 2% (colchón antes del límite 3%) |

**Diferencias clave vs Perfil A:**
- DESHABILITAR bloques agresivos: `Breakout extremo`, `Volatility explosion`, `N-bar high breakout`
- SL MÁS AJUSTADO (ATR×1-2.5 vs ATR×1-4)
- TP/SL ratio MENOR (1.0-2.5 vs 1.5-5.0)
- Complejidad de reglas MENOR: `maxConditions = 3-4`, `maxExitConditions = 2-3`

### 3.5 Filtros de Sesión y Régimen (Perfil B)

- Idéntica configuración de sesión que Perfil A (Londres/NY)
- Filtro de régimen MÁS ESTRICTO:
  - Para mean reversion: `ADX(14) < 25` (mercado en rango)
  - Para trend: `ADX(14) > 20 AND ADX creciente`
  - `ATR(14) < percentil_80(ATR)` → evitar volatilidad extrema (DD killer)

---

## 4. Walk-Forward Anclado (Común a Ambos Perfiles)

### Configuración

```
Método:    Walk-Forward ANCLADO (expanding window)
Folds:     6
Gap:       1 semana (5 días de trading) entre IS y OOS
IS mínimo: 2 años (punto de anclaje)
OOS:       3-6 meses por fold
```

### Esquema temporal (ejemplo con datos 2019-2025):

```
Fold 1: IS = 2019-01 a 2020-06 | gap 1 sem | OOS = 2020-07 a 2020-12
Fold 2: IS = 2019-01 a 2021-00 | gap 1 sem | OOS = 2021-01 a 2021-06
Fold 3: IS = 2019-01 a 2021-06 | gap 1 sem | OOS = 2021-07 a 2022-00
Fold 4: IS = 2019-01 a 2022-06 | gap 1 sem | OOS = 2022-07 a 2023-00
Fold 5: IS = 2019-01 a 2023-06 | gap 1 sem | OOS = 2023-07 a 2024-00
Fold 6: IS = 2019-01 a 2024-06 | gap 1 sem | OOS = 2024-07 a 2025-06
```

### Configuración en SQX:

- **Pestaña**: `Data` → `Setups` / `Walk-Forward`
- **Campos**:
  1. `Walk-Forward type`: Seleccionar `Anchored` (si disponible) o `Rolling` con IS expandido manualmente
  2. `Number of runs`: `6`
  3. `OOS percentage`: calcular según el esquema (≈15-20% del total por fold)
  4. `Gap between IS and OOS`: `5 bars` (en barras diarias = 1 semana)
  5. **IMPORTANTE**: Si SQX no soporta gap nativo, ajustar manualmente las fechas de cada fold recortando 5 días del inicio del OOS

**Alternativa si SQX no soporta WF anclado nativamente:**
- Configurar en `Data` → `Setups` con fechas manuales para cada fold
- Crear 6 setups de datos con los rangos IS/OOS exactos
- En `Cross Checks` → habilitar `Walk-Forward Optimization` con 6 períodos

**Pestaña exacta**: `Cross Checks` → `Walk-Forward Analysis`
- Marcar `Use Walk-Forward Analysis`: ✅
- `Number of periods`: 6
- `OOS percentage`: 20% (ajustar según datos disponibles)
- `Type`: Anchored/Expanding si disponible

---

## 5. Pipeline de Búsqueda (Reemplaza Grid)

### Sustitución del grid por pipeline inteligente:

```
PASO 1: Sampleo Latino Hipercubo  → 500 candidatos, solo train
PASO 2: Filtro Barato              → descarta por restricciones duras (rápido, sin OOS)
PASO 3: Optimización Bayesiana TPE → 2000 evaluaciones sobre supervivientes
PASO 4: Walk-Forward Anclado       → 6 folds con gap de 1 semana
PASO 5: Gate de Robustez            → 4 pruebas obligatorias
PASO 6: Monte Carlo de Trades       → 10K reordenamientos; reporta p5 CAGR y p95 DD
```

### Implementación en SQX:

#### PASO 1-3: Configuración Genética (sustituye grid)

- **Pestaña**: `Genetic Options`
- **Campos**:

| Parámetro | Valor Perfil A | Valor Perfil B | Campo SQX |
|---|---|---|---|
| `PopulationSize` | 120 | 100 | `Genetic Options` → `Population size` |
| `MaxGenerations` | 80 | 60 | `Genetic Options` → `Max generations` |
| `CrossoverProbability` | 95% | 94% | `Genetic Options` → `Crossover probability` |
| `MutationProbability` | 50% | 45% | `Genetic Options` → `Mutation probability` |
| `Islands` | 8 | 6 | `Genetic Options` → `Number of islands` |
| `MigrationModulo` | 15 | 12 | `Genetic Options` → `Migration every N gens` |
| `MigrationRate` | 15% | 12% | `Genetic Options` → `Migration rate` |
| `InitGenerationType` | 2 (random) | 2 (random) | `Genetic Options` → `Init generation type` |
| `DecimationCoef` | 5 | 4 | `Genetic Options` → `Decimation coefficient` |
| `FreshBloodReplaceWeakest` | true | true | `Genetic Options` → `Fresh blood` |
| `FreshBloodWeakestPct` | 30% | 25% | `Genetic Options` → `Replace weakest %` |
| `FilterInitialPopulation` | false | false | `Genetic Options` → `Filter initial population` |
| `ShowAdvancedGeneticSettings` | true | true | `Genetic Options` → toggle avanzado |
| `EvoRestartOnFinish` | true | true | `Genetic Options` → `Restart on finish` |
| `EvoStagnationRestartGenerations` | 12 | 10 | `Genetic Options` → `Stagnation restart gens` |
| `EvoInSamplePeriod` | 100% | 100% | `Genetic Options` → `In-sample period` |

#### PASO 4: Walk-Forward (ver Sección 4)

#### PASO 5: Gate de Robustez

- **Pestaña**: `Cross Checks`
- **Campos**:

| Prueba | Habilitada | Configuración | Campo SQX |
|---|---|---|---|
| **Parameter Sensitivity** | ✅ | Perturbar ±15%; fitness no cae >30% | `Cross Checks` → `Parameter sensitivity` → `Change %: 15`, `Min fitness retention: 70%` |
| **Monte Carlo (trades)** | ✅ | 10,000 reordenamientos | `Cross Checks` → `Monte Carlo` → `Randomize trades order`, `Runs: 10000`, `Confidence: 95%` |
| **Monte Carlo (params)** | ✅ | Slippage ×2, Spread ×2 | `Cross Checks` → `Monte Carlo` → `Randomize strategy parameters`, check `Increase costs` |
| **Retest Higher Precision** | ✅ (solo Fondeo) | Tick data si disponible | `Cross Checks` → `Retest with higher precision data` |
| **Walk-Forward Analysis** | ✅ | 6 folds anclado | `Cross Checks` → `Walk-Forward Analysis` → `Periods: 6` |

**Cross-instrumento** (manual post-SQX): validar el candidato en instrumento correlacionado sin reoptimizar. Si pierde >50% de fitness → descarte.

#### PASO 6: Monte Carlo Final

- **Post-procesado** (fuera de SQX, en Python):
  - 10,000 permutaciones del orden de trades
  - Reportar: percentil 5 de CAGR (p5_CAGR), percentil 95 de DD (p95_DD)
  - Perfil A: p5_CAGR > 50%, p95_DD < 40%
  - Perfil B: p5_CAGR > 15%, p95_DD < 5% (límite fondeadora)

---

## 6. Mapa Completo: Pestaña GUI → Configuración

### 6.1 What to Build (`WhatToBuild`)

| Campo | Perfil A | Perfil B |
|---|---|---|
| Strategy type | `Algo Wizard` / `Custom` | `Algo Wizard` / `Custom` |
| Direction | `Long + Short` | `Long + Short` |
| Instruments | Forex majors (EURUSD, GBPUSD, USDJPY) + Indices (NAS100, US30) | Forex majors solo (EURUSD, GBPUSD) |
| Timeframe primario | M15 / H1 | M15 / H1 |
| Timeframe secundario (multi-TF) | H4 / D1 como filtro | H4 como filtro de sesgo |

### 6.2 Genetic Options (`GeneticOptions`)

Ver tabla en Sección 5, PASO 1-3. Todos los valores se configuran aquí.

**Instrucciones GUI:**
1. Abrir pestaña `Genetic Options` en Full Settings
2. Activar `Show Advanced Settings` (checkbox superior)
3. Rellenar cada campo según la tabla
4. Verificar que `Filter Initial Population = false`
5. Verificar que `Init Generation Type = 2 (Random)`

### 6.3 Data (`Data` / `Setups`)

| Campo | Perfil A | Perfil B |
|---|---|---|
| Data source | Datos propios M1 (reconstrucción intrabar) | Datos propios M1 (DD intrabar CRÍTICO) |
| Main timeframe | M15 o H1 | M15 o H1 |
| Date range IS | 2019-01-01 a 2024-06-30 | 2019-01-01 a 2024-06-30 |
| Date range OOS | Definido por WF folds | Definido por WF folds |
| Spread | Variable por sesión (realista) | Variable por sesión (realista) |
| Commission | Según broker real | Según broker real |
| Slippage | 1-2 pips (configurar en Trading Options) | 1-2 pips |
| Precision | `Use M1 data for bar magnifier` ✅ | `Use M1 data for bar magnifier` ✅ OBLIGATORIO |

**Instrucciones GUI:**
1. Ir a `Data` → `Setups`
2. Seleccionar el data feed principal (ej. `Custom data` o `Dukascopy`)
3. Configurar fecha From y To
4. En `Bar Magnifier` / `Higher precision`: activar `Use M1 data` → OBLIGATORIO para medir DD intrabar
5. Configurar spread: `Variable spread from data` si disponible, o `Fixed` con valor realista

### 6.4 Trading Options (`TradingOptions`)

| Campo | Perfil A | Perfil B |
|---|---|---|
| Trading hours | Optimizable: From [06-14], To [15-22] | Optimizable: From [06-14], To [15-22] |
| Allow overnight | Sí (optimizable) | No preferido (cerrar antes del rollover) |
| Max open trades | 3-5 | 1-2 (conservador) |
| Slippage | 1 pip | 1 pip |
| Min bars between entries | 5 | 10 (evitar sobreoperar) |

**Instrucciones GUI:**
1. Ir a `Trading Options`
2. En `Trading hours`: marcar `Restrict trading hours`
3. Configurar From/To con optimización habilitada
4. En `Other settings`: `Max open trades = 3` (Perfil A) / `1` (Perfil B)
5. `Slippage = 1 pip` (o `10 points` según el instrumento)

### 6.5 Building Blocks (`BuildingBlocks`)

Ver Secciones 2.4 (Perfil A) y 3.4 (Perfil B) para la lista completa de bloques.

**Instrucciones GUI:**
1. Ir a `Building Blocks`
2. Expandir `Entry Signals`
3. Para cada bloque:
   - ✅ Habilitar los bloques listados en la sección del perfil
   - ❌ Deshabilitar TODOS los demás
4. Expandir `Exit Conditions`
5. Configurar SL/TP con rangos optimizables
6. En `Rules Complexity`:
   - Perfil A: `Max conditions = 6`, `Max exit conditions = 4`, `Max period = 50`
   - Perfil B: `Max conditions = 4`, `Max exit conditions = 3`, `Max period = 30`

### 6.6 ATM (Advanced Trade Management)

| Campo | Perfil A | Perfil B |
|---|---|---|
| Trailing Stop | ATR trailing, activar ∈ [1×ATR, 3×ATR] | ATR trailing ajustado, activar ∈ [0.5×ATR, 2×ATR] |
| Break-even | Mover SL a BE cuando profit > 1×ATR | Mover SL a BE cuando profit > 0.5×ATR |
| Partial close | Cerrar 50% en 1.5×ATR de profit | Cerrar 50% en 1×ATR de profit |

**Instrucciones GUI:**
1. Ir a `ATM` o `Advanced Trade Management`
2. Habilitar `Trailing Stop` → tipo ATR → rango optimizable
3. Habilitar `Break-even` → threshold optimizable
4. Habilitar `Partial close` → porcentaje y threshold

### 6.7 Money Management (`MoneyManagement`)

Ver Secciones 2.3 (Perfil A) y 3.3 (Perfil B).

**Instrucciones GUI:**
1. Ir a `Money Management`
2. Perfil A: `Fixed % Risk` → `Optimize ON` → rango [0.5, 5.0], step 0.25
3. Perfil B: `Fixed % Risk` → valor fijo `0.5%` → `Optimize OFF`

### 6.8 Cross Checks (`CrossChecks`)

Ver Sección 5, PASO 5.

**Instrucciones GUI:**
1. Ir a `Cross Checks`
2. Habilitar `Walk-Forward Analysis` → 6 períodos, OOS 20%
3. Habilitar `Monte Carlo` → 10,000 runs, 95% confianza
4. Habilitar `Parameter Sensitivity` → ±15%, retención mínima 70%
5. Perfil B: habilitar adicionalmente `Retest with higher precision`
6. Perfil A: `Cross Checks use`: TRUE para todas
7. **NO deshabilitar Cross Checks** — son la defensa contra overfit

### 6.9 Rankings & Filtering (`Rankings & Filtering`)

Ver Secciones 2.1/2.2 (Perfil A) y 3.1/3.2 (Perfil B).

**Instrucciones GUI:**
1. Ir a `Rankings & Filtering`
2. En `Fitness`:
   - Perfil A: `Annual % Return` ponderado con `Stability`
   - Perfil B: `Ret/DD Ratio` ponderado con `Stability`
3. En `Conditions` (restricciones duras):
   - Añadir CADA restricción de la tabla (Sección 2.2 o 3.2)
   - Verificar que están como `Hard filter` (descarte), no `Penalty`
4. En `Stop Condition`:
   - `Databank full` → `passedStrategies = 200` (alto para no limitar la búsqueda)
   - O mejor: DESACTIVAR stop condition por databank
5. **Verificar** que no quedan filtros residuales de ejecuciones anteriores

### 6.10 Setups

| Campo | Perfil A | Perfil B |
|---|---|---|
| Capital inicial | $10,000 | $100,000 (cuenta fondeadora) |
| Compounding | Sí (compound equity) | No (fixed position size) |
| Account type | Standard | Standard |

---

## 7. Checklist de Verificación Pre-Run

### Perfil A — Growth/Ultra

- [ ] `Genetic Options` → Advanced visible, Population 120, Islands 8, Init type 2
- [ ] `Data` → M1 bar magnifier activado
- [ ] `Data` → Rango IS 2019-2024, spread variable
- [ ] `Building Blocks` → Solo momentum/breakout/volatilidad habilitados
- [ ] `Building Blocks` → Mean reversion DESHABILITADO
- [ ] `Money Management` → Fixed % Risk con Optimize ON, rango [0.5, 5.0]
- [ ] `Trading Options` → Horas optimizables Londres/NY
- [ ] `Trading Options` → Max open trades = 3-5
- [ ] `Rankings & Filtering` → Fitness = Annual Return × Stability
- [ ] `Rankings & Filtering` → Trades OOS ≥ 150 (hard filter)
- [ ] `Rankings & Filtering` → DD ≤ 35% (hard filter)
- [ ] `Rankings & Filtering` → PF OOS ≥ 1.0 (hard filter)
- [ ] `Rankings & Filtering` → Peor mes ≥ -20% (hard filter)
- [ ] `Rankings & Filtering` → passedStrategies = 200 (o sin límite)
- [ ] `Cross Checks` → WF 6 folds activado
- [ ] `Cross Checks` → Monte Carlo 10K activado
- [ ] `Cross Checks` → Parameter Sensitivity ±15% activado
- [ ] Databank de resultados VACÍA o nueva (evitar cache)
- [ ] Servicio SQX reiniciado tras cambios de .cfx

### Perfil B — Fondeo/Prop Firm

- [ ] `Genetic Options` → Population 100, Islands 6, Init type 2
- [ ] `Data` → M1 bar magnifier OBLIGATORIO (DD intrabar)
- [ ] `Data` → Rango IS 2019-2024, spread variable
- [ ] `Building Blocks` → Solo mean reversion/trend multi-TF habilitados
- [ ] `Building Blocks` → Breakout agresivo DESHABILITADO
- [ ] `Money Management` → Fixed % Risk = 0.5% FIJO, Optimize OFF
- [ ] `Trading Options` → Max open trades = 1-2
- [ ] `Trading Options` → Horas restringidas a sesión activa
- [ ] `Rankings & Filtering` → Fitness = Ret/DD Ratio × Stability
- [ ] `Rankings & Filtering` → DD diario ≤ 3% (hard filter, con margen sobre 5% de FTMO)
- [ ] `Rankings & Filtering` → DD total ≤ 5% (hard filter, con margen sobre 10%)
- [ ] `Rankings & Filtering` → Trades OOS ≥ 100 (hard filter)
- [ ] `Rankings & Filtering` → PF OOS ≥ 1.1 (hard filter)
- [ ] `Rankings & Filtering` → Consistencia ≥ 60% días positivos
- [ ] `Cross Checks` → WF 6 folds activado
- [ ] `Cross Checks` → Monte Carlo 10K activado
- [ ] `Cross Checks` → Retest higher precision activado
- [ ] `Cross Checks` → Parameter Sensitivity ±15% activado
- [ ] Capital inicial = $100,000 (tamaño de cuenta fondeadora)
- [ ] Compounding DESACTIVADO

---

## 8. Instrucciones computer_use Paso a Paso

### Secuencia de navegación en la GUI de SQX

La GUI de SQX (Electron en `http://127.0.0.1:5050` / display `:99`) tiene el Builder como vista principal. La navegación sigue este orden:

```
1. Abrir SQX → Builder → Seleccionar proyecto (o crear nuevo)
2. Click en "Full Settings" (icono engranaje o pestaña superior)
3. Navegación por pestañas laterales izquierdas (de arriba a abajo):
   ├── What to Build
   ├── Genetic Options
   ├── Data
   ├── Trading Options
   ├── Building Blocks
   ├── ATM
   ├── Money Management
   ├── Cross Checks
   ├── Rankings & Filtering
   └── Setups
4. Configurar cada pestaña según el perfil
5. Guardar proyecto (Ctrl+S o File → Save)
6. Vaciar/renombrar databank Results
7. Iniciar búsqueda (botón "Start")
```

### Instrucciones para el agente computer_use:

#### Fase 1: Captura y navegación
```
computer_use(action='capture', mode='som', app='StrategyQuantX')
→ Identificar elementos numerados
→ Buscar elemento "Full Settings" o "Builder" tab
computer_use(action='click', element=N)  # donde N es el índice de Full Settings
```

#### Fase 2: Configurar cada pestaña (orden secuencial)
```
Para cada pestaña en [WhatToBuild, GeneticOptions, Data, ...]:
  1. computer_use(action='capture', mode='som')  # ver pestaña actual
  2. computer_use(action='click', element=N)  # click en la pestaña lateral
  3. computer_use(action='capture', mode='som')  # ver campos de la pestaña
  4. Para cada campo a configurar:
     a. computer_use(action='click', element=M)  # click en el campo
     b. computer_use(action='type', text='valor')  # escribir el valor
     c. O: computer_use(action='set_value', element=M, value='valor')  # para dropdowns
  5. Verificar con capture que los valores quedaron correctos
```

#### Fase 3: Verificación y lanzamiento
```
1. Navegar a cada pestaña y capturar para verificar valores
2. Guardar: computer_use(action='key', keys='ctrl+s')
3. Vaciar databank: navegar a databank Results → click derecho → Clear/Delete
4. Start: computer_use(action='click', element=N)  # botón Start/Run
5. Verificar que la búsqueda inició (Progress tab muestra generaciones)
```

#### Notas críticas para computer_use:
- SQX corre en Xvfb :99 → usar `DISPLAY=:99` para capturas
- Si `computer_use` devuelve 0×0, fallback a:
  ```bash
  import -window $(xdotool search --name 'StrategyQuant') -display :99 /tmp/sqx_capture.png
  ```
- Después de editar el .cfx manualmente, REINICIAR servicio SQX:
  ```bash
  systemctl --user restart strategyquantx
  ```
- Verificar que el servicio está activo antes de interactuar con la GUI

---

## Apéndice: Fórmulas de Referencia

### Kelly Fraccional Acotado (Perfil A)
```
f_kelly = (W × R - (1-W)) / R
donde:
  W = win rate
  R = avg_win / avg_loss
  f_acotado = max(0.005, min(0.05, f_kelly × 0.5))  # half-Kelly acotado
```

### Estabilidad (Perfil A)
```
estabilidad = (1 - CV) × ratio_positivos
CV = std(CAGR_por_fold) / mean(CAGR_por_fold)
ratio_positivos = count(fold_profit > 0) / total_folds
```

### P(pasar challenge) aproximada (Perfil B)
```
P(pasar) ≈ P(alcanzar_target_en_N_dias) × P(no_violar_DD_diario) × P(no_violar_DD_total)
```
Estimada por Monte Carlo: simular 10K secuencias de trades, contar las que pasan todas las condiciones simultáneamente.

---

> **Última actualización**: 2026-08-09
> **Autor**: Auditoría automatizada — Motor de búsqueda Ultrarentable
> **Siguiente paso**: Ejecutar estas configuraciones en la GUI real de SQX con computer_use
