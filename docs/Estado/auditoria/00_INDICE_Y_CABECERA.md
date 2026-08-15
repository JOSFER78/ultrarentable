# Auditoría Técnica — Búsqueda de estrategias en StrategyQuant X (SQX)
> Proyecto: Ultrarentable · `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`
> Fecha: 2026-08-09 · Rol: Analista Cuantitativo / Especialista SQX
> Regla REAL-ONLY: toda métrica proviene de lectura real de API/BD/XML. No se inventan valores.

---

## Objetivo
Investigar por qué la generación automática en SQX **no produce los candidatos deseados** (miles de % verificables)
y proponer una solución técnica documentada, ejecutable por multiagentes bajo supervisión del orquestador.

## Estado verificado del sistema (2026-08-09, VPS)
| Componente | Estado | Evidencia |
|---|---|---|
| StrategyQuant X | `active` 24/7 | MCP `127.0.0.1:8080`, web UI `127.0.0.1:5050` (HTTP 200) |
| API FastAPI | `active` | `127.0.0.1:8000` — 56 endpoints |
| Frontend Next.js | `active` | `127.0.0.1:3000` |
| BD operacional | OK | `strategies=95`, `backtests=77`, `campaigns=2`, `datasets=5` |

## Documentos de esta auditoría (índice)
| # | Documento | Contenido | Estado |
|---|---|---|---|
| 00 | `00_INDICE_Y_CABECERA.md` | Este índice + diagnóstico de cabecera | ✅ |
| 01 | `01_matriz_causa_raiz.md` | Matriz de 5 errores principales (evidencia XML) | ✅ (elaboración propia) |
| 02 | `02_configuracion_actual_sqx.md` | Configuración ACTUAL real extraída del XML | ✅ (evidencia propia) |
| 03 | `03_diagnostico_plantilla_sqx_real.md` | Auditoría profunda del Build-Task1.xml | ⏳ (agente 1) |
| 04 | `04_pipeline_validacion_multimotor.md` | Pipeline SQX→Nautilus + gates de robustez | ⏳ (agente 2) |
| 05 | `05_plantilla_sqx_perfiles_ab.md` | Plantillas Builder Perfil A (Growth) y B (Fondeo) | ⏳ (agente 3) |
| 06 | `06_plan_accion_multiagente.md` | Roadmap 48-72h de implementación modular | ⏳ (agente 4) |

## Evidencia real extraída del `project.cfx` (Ultra_Auto_Pilot / Build-Task1.xml)
Extracción directa del zip `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx`:

| Parámetro | Valor real en XML | Impacto |
|---|---|---|
| Fitness / Ranking | `<FitnessCriteria method="ComputeFromStrategyResult">` + `<Ranking type="NetProfit">` | **Optimiza retorno bruto, NO penaliza DD/estabilidad** → curvas frágiles |
| Population | `<PopulationSize>80` | — |
| Crossover / Mutation | `<CrossoverProbability>95` / `<MutationProbability>45` | Alta mutación → diversidad pero riesgo de perder buenos padres |
| Islands | `<Islands>8` | Muchas islas → más diversidad, más lento |
| Stop (DD builder) | `maxDrawdown=30` | Freno solo al 30% en builder |
| Data symbol | `BTCUSDT_AUTO`, timeframe `H1`, Binance USDT-M | Solo BTC si HBO, 1 timeframe |
| Data range | `dateFrom=2026-02-26` → `dateTo=2026-08-04` (≈5.2 meses) | **Rango MUY corto** → muestra insuficiente para CAGR estable |
| Test precision | `<Setup testPrecision="1">` (Selected timeframe, 4 ticks/barra) | Bajo detalle, sin DD intrabar real |
| Spread / slippage | `spread=0` / `slippage=1` | **Spread 0 en el setup principal** → irreal, HFT fantasma |
| Commissions | `CommissionPct=0.05` (PercentageBased) | Comisión presente pero baja |
| Engine | `MetaTrader4` (simulation) | Simulación, sin datos tick reales |
| Cross checks | `RetestWithHigherPrecision use="true"`; `WalkForwardOptimization use="false"`; `MonteCarloRetest use="false"`; `WalkForwardMatrix use="false"`; `MonteCarloManipulation use="false"`; SPP/WhatIf `use="false"` | **Casi todas las validaciones OOS/MC desactivadas** |
| MaxStrategies | `24` | Databank capado a 24 estrategias |
| MoneyManagement | Base, sin Kelly | Sin sizing por edge |
| Filtros de sesión | NO presentes | Sin Londres/NY |
| Filtros de régimen | NO presentes | Sin ATR/volatilidad |
| OOS/setup real | Setup fóndeo EURUSD_M1_dukas: `dateFrom=2003.5.5`→`2019.12.13`, spread=2, precision=1 | Setup residual separado |

**Conclusión de cabecera (evidencia real):** la configuración actual optimiza por **retorno neto bruto** sobre un rango
corto y **sin validación OOS/WFA/Monte Carlo activa**, con **spread=0** en el setup principal. Esto es la firma clásica
de sobreajuste IS → curvas que lucen bien en M1 historical pero colapsan OOS/en real. Coincide con el resultado real
de la BD: 24 candidatos, 0 winners, mejor WFE ≈ 0.12 (way below 0.60).

## Documentos de referencia del proyecto
- `plan_implementacion/MEMO_BUSCADOR_PERFILES_A_B.md` — fitness dual (Growth+Kelly vs Fondeo+DD intrabar)
- `plan_implementacion/BLUEPRINT_CONTROLADOR_ESTRATEGIAS_MUNDIAL.md` — protocolo WFE/OOS/Monte Carlo
- `plan_implementacion/AUDITORIA_CANDIDATOS_KAMIKAZE.md` — scorecard 3 capas, 0 winners
- `docs/Estado/auditoria/04_pipeline_validacion_multimotor.md` — Pipeline completo SQX→NautilusTrader, WFA/MC/SPP gates, scorecard integrada, gaps BD
- `plan_implementacion/GUIA_EXPERTO_USAR_SQUANT.md` — integración SQX (GUI real, no scripts)

*Documento de cabecera generado por el orquestador con evidencia directa del XML. Los informes 03-06 los completan los subagentes.*
