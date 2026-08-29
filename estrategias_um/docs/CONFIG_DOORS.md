# Puertas (checks/filtros) del proyecto SQX Ultra_Matrix — 2026-08-29

Fuente ACTUAL: `/tmp/um_doors/cfx_actual/` (extraído de `project.cfx` real, 12:13 hoy).
Fuente BACKUP: `/tmp/um_doors/cfx_backup/` (extraído de `backup_Ultra_Matrix_pre_window_20260829.cfx`, 09:05 hoy).
Nota: el backup indicado en la orden (`backup_Ultra_Matrix_pre_improve.cfx`) NO existe; se usó `backup_Ultra_Matrix_pre_window_20260829.cfx` (backup pre-ventana de hoy). El backup no contiene `Improve-Task1.xml` (la tarea Improve se añadió hoy).

## 1. Build-Task1.xml — Genético (no descarta, genera)
| Parámetro | Valor actual | Backup |
|---|---|---|
| BuildMode | genetic-evolution | igual |
| PopulationSize | 100 | igual |
| Islands | 8 | igual |
| MaxGenerations | 60 | igual |
| CrossoverProbability | 95 | igual |
| MutationProbability | 45 | igual |
| MigrationRate / MigrationModulo | 15 / 20 | igual |
| FreshBlood (similar/weakest, gens, pct) | true/true, 2, 25% | igual |
| DecimationCoef | 4 | igual |
| EvoInSamplePeriod ratio | 70% | igual |
| EvoRestartOnFinish / OnStagnation | true / false (30 gens) | igual |
| StopCondition | databank-full, 200 estrategias, 30 min | igual |
| FitnessCriteria | Ranking = ReturnDDRatio | igual |
| RulesComplexity (Main chart) | 1–3 condiciones entrada, 0–2 salida, periodo 5–120, shift 1–2 | igual |
| SL/PT ranges (pips/ATR) | SL 40–50 pips / ATR 0.5–2x (10–20); PT 51–60 pips / ATR 2.1–3x (21–30) | igual |
| MaxTradesPerDay | 1 | igual |
| MoneyManagement | RiskFixedBalancePct 2%, cap 5 lots | igual |
| RiskManagement maxDrawdown | 30% | igual |
| EOD/Friday exit, LimitTimeRange | false/false/false | igual |

## 2. Build — CrossChecks (`use=true`, evaluateAll=false = pasa con la PRIMERA condición que evalúe; el resto no corre)
| Puerta | use | Parámetros (valor actual = backup salvo indicado) |
|---|---|---|
| WalkForwardOptimization | TRUE | WF tipo 1, period=5, optimization=20 (params 20/10), MaxTests=100; **Conditions thresholdPct=80**: NetProfit WFM > 0; NetProfit% WFO > 60; WFPctOfProfitableRuns > 70%; WFMaxProfitByRunInPct < 50%; WFMinTradesInRun > 20; WFMaxPctDDbyRun <= 25%. (Inactivas: DD < 130%, Ret/DD > 60, Stagnation < 30) |
| RetestWithHigherPrecision | TRUE | Precision=2, Spread=3; NetProfit retest >= 80% del main; NumberOfTrades retest >= 80% del main; DD% retest < 130% del main |
| MonteCarloRetest | TRUE | 20 sims; métodos: RandomizeHistoryData **ProbabilityUp/Down=10, MaxChangeUp/Down=10** (BACKUP: 30/30/30/30 ← CAMBIÓ HOY); MinDistance 0–10; Slippage 0–5; Spread 1–5; StartingBar 100; StrategyParams prob 10%, change 20%. Condiciones: NetProfit MC(p80) >= main(p90)×50%; DD% MC(p80) <= main(p90)×200% |
| OptProfileSysParamPermutation | TRUE | MaxTests=100; ProfitOptPct=30, AvgProfit=0, UniformDistrChanges=5, StdevAvgProfit=1 (todas las Eval*Check=true) |
| RetestOnAdditionalMarkets | false | (inactiva) ProfitFactor > 1.1, MinConditions=2, MinMarkets=1 |
| WalkForwardMatrix | false | (inactiva) mismas condiciones WFO con thresholdPct=80, robComb 2×2 |
| MonteCarloManipulation | false | (inactiva) 30 sims |
| WhatIf | false | (inactiva) ExcludeTradesWithBiggestPl/LowestPl = 2 trades |

## 3. Improve-Task1.xml (Optimize) — NUEVO hoy (no existe en el backup)
| Parámetro | Valor |
|---|---|
| Input / Output databank | LastGeneration → Results_robust_20260809 |
| Optimization type / maxOptimizations | 1 / 25 |
| SimpleOptimization | pctToPass=60, resultsCount=5, stabilityRange=20 |
| AutomaticSettings | distributionUp/Down=20, maxSteps=3 |
| WhatToParametrize | solo Recommended=true |
| MaxStrategies | 200 |
| Fitness | ReturnDDRatio |
| WF Conditions (Improve) | NetProfit WFM > 0; NetProfit% WFO > 65 (vs 60 en Build); WFPctProfitableRuns > 70; MaxProfitByRun% < 45 (vs 50 en Build); ThresholdPct=65; RobComb 4×4, RobMinComb=10 |

## 4. config.xml — cambió hoy
| Ítem | Actual | Backup |
|---|---|---|
| Tarea Improve (Optimize) | AÑADIDA hoy | no existía |
| Databanks registrados | 9 (añade LastGeneration, InitialPopulation, ToImprove, Strategies to optimize) | 5 |
| Nombres databanks en Build | LastGeneration / InitialPopulation / ToImprove | "Last generation" / "Initial population" / "Strategies to improve" (RENOMBRADOS hoy) |

## 5. HALLAZGO CRÍTICO — por qué los databanks están a 0
- El Build **sí guarda en LastGeneration y Results** (Databanks Output del Build-Task1.xml), pero **no ha guardado NADA todavía**.
- Disco: todos los dirs `user/projects/Ultra_Matrix/databanks/*` están VACÍOS (0 archivos) — confirma el "Records: 0" por API.
- Log de hoy (`log_2026_08_29.log`): **3.569 simulaciones MC descartadas entre 09:07 y 14:02**, TODAS con el mismo error:
  `MC retest job Strategy X MC n dismissed, error: Exception in backtest: Filtro automático: sin transacciones`.
- Es decir, la puerta que está comiendo todo es el **MonteCarloRetest** (obligatorio, `evaluateAll=false` no ayuda: si el MC falla, la estrategia se descarta): cada una de las 20 simulaciones produce un backtest **sin transacciones** ("Filtro automático: sin transacciones"), y el candidato entero se descarta antes de poder escribir en LastGeneration. El genético consume ~136k tests/h sin que uno solo cruce la puerta MC.
- El cambio de hoy en MC RandomizeHistoryData (30→10) NO fue la causa de bloqueo total (el error es "sin transacciones", no umbral); con el backup a 30/30/30/30 el MC fallaría igual o peor. La causa raíz es de trades: candidatos con tan pocas operaciones que cualquier randomización (params 10%, spread 1–5, slippage 0–5, starting bar) deja el backtest vacío — coherente con `MaxTradesPerDay=1` y rangos SL/PT estrechos.
- `data.db` (sqlite, leído en modo ro) no contiene databanks de estrategias (solo SESSIONS/ELEMENTS/INSTRUMENTS/DATA/STOCK/BROKER); los resultados viven en `user/projects/Ultra_Matrix/databanks/`, físicamente vacíos.

## Resumen de cambios de HOY (backup 09:05 → actual 12:13)
1. MC RandomizeHistoryData: ProbabilityUp/Down y MaxChangeUp/Down 30 → 10 (más suave).
2. Databanks renombrados: "Last generation"→LastGeneration, "Initial population"→InitialPopulation, "Strategies to improve"→ToImprove.
3. Añadida tarea Improve (Optimize) con sus propias puertas WF (NetProfit% > 65, MaxProfitByRun < 45%, thresholdPct 65, robustez 4×4 min 10).
4. config.xml: +4 databanks registrados.
5. Ningún umbral WF/Retest/Precision cambió: idénticos al backup.
