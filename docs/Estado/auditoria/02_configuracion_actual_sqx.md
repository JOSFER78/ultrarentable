# Configuración ACTUAL de la plantilla SQX (evidencia XML)
> Proyecto: Ultrarentable · Fecha: 2026-08-09 · Regla REAL-ONLY
> Fuente: `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx` → `Build-Task1.xml` (descomprimido).

---

## Proyecto y tarea activa
| Campo | Valor real |
|---|---|
| Proyecto | `Ultra_Auto_Pilot` (versión `144.2953`) |
| Tarea | `Build` — "Autonomous candidate search" (`Build-Task1.xml`, activa) |
| Tipo de estrategia | `simple` (SQ4 template) |
| Lados de mercado | `both` |
| Modo de build | `genetic-evolution` |
| Note | "Ultrarentable autonomous execution pilot. Candidate generation only; requires subsequent O..." |

## Data / símbolo
| Campo | Valor real |
|---|---|
| Símbolo | `BTCUSDT_AUTO` (source 7) → `uSymbol=BTCUSDT` `uSymbolName="Binance USDT-M"` |
| Timeframe | `H1` |
| Rango | `dateFrom=2026.02.26` → `dateTo=2026.8.4` (~5.2 meses) |
| removeWeekends | `false` |
| Precision de test | `testPrecision=1` (Selected timeframe, 4 ticks/barra) |
| Engine | `MetaTrader4` (simulación) |
| Session | `No Session` |

## Costes (setup principal)
| Campo | Valor real |
|---|---|
| Spread | `0` (chart principal) |
| Slippage | `1` |
| Min distance | `0` |
| Comisión | `PercentageBased`, `CommissionPct=0.05` (0.05% por lote completo) |

> Setup residual separado (fondeo): `EURUSD_M1_dukas`, H1, `spread=2`, `slippage=1`,
> `dateFrom=2003.5.5` → `dateTo=2019.12.13`, comisión `None`. **No es el setup del run activo.**

## Genética / evolución
| Campo | Valor real |
|---|---|
| PopulationSize | `80` |
| CrossoverProbability | `95` |
| MutationProbability | `45` |
| Islands | `8` |
| MaxStrategies (databank) | `24` |
| RiskManagement maxDrawdown | `30` |
| StopCondition | `databank-full` (passedStrategies=200, restartCount=0, minutes=30) |

## Fitness / Ranking
| Campo | Valor real |
|---|---|
| FitnessCriteria | `ComputeFromStrategyResult` |
| Ranking | `NetProfit` |

## Cross Checks / robustez
| Prueba | Estado real |
|---|---|
| RetestOnAdditionalMarkets | `use="false"` |
| WalkForwardOptimization | `use="false"` |
| RetestWithHigherPrecision | `use="true"` (NetProfit ≥ 80% del main; trades ≥ 80% del main; DD < 130% del main) |
| MonteCarloRetest | `use="false"` |
| WalkForwardMatrix | `use="false"` |
| MonteCarloManipulation | `use="false"` |
| OptProfileSysParamPermutation (SPP) | `use="false"` |
| WhatIf | `use="false"` |

> Solo la prueba de precisión alta está activa. **Todo el bloque WFA/MonteCarlo/SPP/WhatIf está OFF.**

## Money Management
- Base (sin Kelly). El MEMO A/B pide Kelly fraccional acotado en el espacio de búsqueda; hoy no existe.

## Filtros
- **Sesión:** NO hay filtros (Londres/NY ausentes).
- **Régimen de mercado:** NO hay filtros (ATR/ADX/volatilidad ausentes).

---

## Síntesis (qué está mal en la config real)
1. Ranking por **NetProfit** → premia curvas frágiles.
2. **Todos los gates OOS/WFA/MC/SPP OFF** → imposible distinguir edge de ruido.
3. Rango solo **5.2 meses, BTC 1h** → muestra corta y sesgada.
4. **Spread=0** + slippage bajo → fricción irreales.
5. **Sin filtros** de sesión ni régimen.

*Documento de evidencia propia del orquestador. Referencia cruzada con `03_diagnostico_plantilla_sqx_real.md` (agente 1).*
