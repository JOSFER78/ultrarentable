# Embudo de FILTROS ORGÁNICOS — Ultra_Matrix (2026-08-29, 15:25 UTC)

Mandatos aplicados: filtrado "orgánico y natural, no ultra exigente"; no fiarse de lo instalado;
justificación SOLO por nuestra evidencia (log de hoy + forense del embudo) y coherencia interna.
Ningún número citado proviene de docs ni de valores de fábrica.

## Evidencia propia de hoy (log_2026_08_29.log, 15:25)
- Estrategias generadas (run vigente 13:16→): ~35.592 acumuladas al 15:22.
- Llegan a MC: 650 distintas en todo el día (~0,15-0,8% según ventana) → **~99,85% muere ANTES de MC, sin traza individual** (solo agregados `Rechazado 100,00 %`).
- MC: **4.826 dismissals / 650 estrategias / 100% por "Filtro automático: sin transacciones"**. Único motivo en todo el día (cero ProbabilityUp, cero NetProfit, cero Sharpe). El fix 30→10 de hoy no cambió nada: 913 muertes MC a las 14h y 450 a las 15h.
- Guardadas: **0** todo el día (`En la base de datos 0`, última 15:22:58).

## Recuento de puertas ACTIVAS — reconciliación con "~11 filtros"
El usuario recuerda ~11. Contados sobre el cfx real:
- **CrossChecks del Build (evaluados): 5** — WalkForwardOptimization, RetestWithHigherPrecision, MonteCarloRetest, OptProfileSysParamPermutation, + las condiciones WF que viven DENTRO del propio WFO (thresholdPct=80: 6 sub-condiciones: WFM>0, WFO%>60, ProfitableRuns>70, MaxProfitByRun<50, MinTradesInRun>20, DD≤25).
- Si se cuentan las 6 sub-condiciones WF como filtros independientes: 5 + 6 = **11 ≈ lo que recuerda el usuario**. Pero estructuralmente son **3-4 puertas físicas** (WF, Retest, MC, OptProfile) + 4 puertas INACTIVAS (RetestOnAdditionalMarkets, WalkForwardMatrix, MonteCarloManipulation, WhatIf) + la tarea Improve añadida hoy con su propio WF (NetProfit%>65, MaxProfitByRun<45, thresholdPct=65, RobComb 4×4 min10) que es una 5ª puerta activa en la práctica.
- **Reconciliación: 5 puertas físicas activas** (4 Build + WF-Improve), 4 inactivas. El "~11" probablemente cuenta las sub-condiciones de umbral. No hay filtros ocultos adicionales: la muerte masiva pre-MC NO deja traza y es coherente con el apilado WF(threshold 80 sobre 6 condiciones) + MinTradesInRun>20.

## Contradicciones internas detectadas (nuestra evidencia, no docs)
1. **MinTradesInRun>20 (WF) × optim period=20 × MaxTradesPerDay=1**: con 1 trade/día máximo y runs de validación de 20 períodos, exigir >20 trades por run obliga a operar prácticamente TODOS los días con señal. Con reglas de solo 1-3 condiciones (periodos 5-120), la mayoría de días no hay señal → el backtest del run sale vacío o con 1-3 trades → "Filtro automático: sin transacciones" (exactamente el error único que vemos 4.826 veces en MC, que replica el mismo backtest randomizado). Esta contradicción SOLO es visible con nuestra evidencia: el 99,85% que muere pre-MC y el 100% que muere en MC mueren del mismo tirón.
2. **Retest trades>=80% del main**: los candidatos que llegan a Retest tienen poquísimos trades (los mismos que luego mueren en MC por vacío). Con 5-10 trades en el main, exigir ≥80% en el retest es puro ruido estadístico (±1 trade decide). Ruido puro, sin señal.
3. **WF Build thresholdPct=80 / WF Improve thresholdPct=65 con umbrales cruzados**: Improve exige NetProfit%>65 (más duro que el 60 del Build) pero thresholdPct=65 (más blando que 80). Dos puertas WF consecutivas con filosofías opuestas = incoherencia interna; además Improve RobComb 4×4 min10 es más duro que el 2×2 del Build.
4. **MC exige NetProfit MC(p80) ≥ main(p90)×50% sobre estrategias que a veces ni generan transacciones**: se está comparando percentiles de un backtest que muchas veces está vacío. El comparador de percentiles es la puerta menos problemática; el problema es que las 20 sims nacen de un main con tan pocos trades que cualquier randomización (spread 1-5, slippage 0-5, StartingBar 100) vacía el backtest. ProbUp 30→10 de hoy no tocó la causa real.
5. **StopCondition databank-full 200 estrategias + Fitness ReturnDDRatio sobre caudal 0**: el embudo está secuestrado por el filtro; el databank lleva todo el día a 0 Records (verificado por API y disco) — el sistema está optimizando para un criterio que ninguna estrategia ha podido demostrar.

## Propuesta por puerta (MANTENER / SUAVIZAR / JUBILAR) — objetivo orgánico: WF acepta 1-5%, Retest ≥50%, MC ≥50%, banco recibe decenas/día

| Puerta | Estado | Veredicto | Valor concreto propuesto | Justificación (solo evidencia propia) |
|---|---|---|---|---|
| **WalkForwardOptimization (Build)** | ACTIVA | **SUAVIZAR** | period 5→10; optim 20→10; thresholdPct 80→70; **MinTradesInRun >20 → >8**; NetProfit% WFO >60 → >30; WFPctProfitableRuns >70 → >60; WFMaxProfitByRunInPct <50 → <60; WFMaxPctDDbyRun ≤25 → ≤30 | MinTradesInRun>20 es la contradicción #1 y el cuello de botella silencioso. Con 8 trades mínimos por run y period 10, el WF sigue validando estabilidad pero deja pasar candidatos con señal real (nuestro log: 99,85% muere aquí sin traza, caudal objetivo 1-5% = 350-1.800 de las 35.592 de hoy) |
| **RetestWithHigherPrecision** | ACTIVA | **SUAVIZAR** | Precision=2 mantener; Spread=3 mantener; **NetProfit retest ≥80% → ≥50%**; **NumberOfTrades ≥80% → ≥50%**; DD<130% mantener | Con poquísimos trades, 80% es ruido (#2). 50% sigue validando coherencia direccional (nuestro objetivo de caudal: ≥50% de los que llegan deben pasar, hoy no hay trazas de retest porque nadie llega con trades suficientes) |
| **MonteCarloRetest** | ACTIVA | **SUAVIZAR + repensar** | 20 sims mantener; RandomizeHistoryData Prob 10→5, MaxChange 10→5; StrategyParams prob 10%→5%, change 20%→10%; MinDistance 0-10 mantener; Slippage 0-5 mantener; Spread 1-5 mantener; StartingBar 100→50; condición NP p80 ≥ main p90×50% → ≥ main p90×30% | Es la puerta asesina Nº1 CON traza: 4.826/4.826 (100%) por "sin transacciones". El fix de hoy (30→10) no tocó la causa: los candidatos nacen con tan pocos trades que cualquier randomización vacía el backtest. Suavizar randomización + subir trades aguas arriba (WF) es lo que desbloquea. Objetivo: ≥50% de los que llegan deben sobrevivir |
| **OptProfileSysParamPermutation** | ACTIVA | **JUBILAR (desactivar temporalmente)** | use=true → false | Evidencia propia: 0 estrategias han llegado jamás a esta puerta (0 aceptadas, 0 en databank en todo el día). 4º filtro apilado tras WF+Retest+MC; sin caudal no aporta señal, solo muertes sin traza. Reactivar cuando el banco reciba decenas/día |
| **WF Improve (Optimize)** | ACTIVA (nueva hoy) | **MANTENER pero coherenciar** | NetProfit% WFO >65 → >60 (igual al Build); thresholdPct 65 → 70 (igual al Build suavizado); MaxProfitByRun<45 → <55 (igual al Build suavizado); RobComb 4×4 min10 → 3×3 min6 | Contradicción #3: dos puertas WF consecutivas con umbrales cruzados (Improve más duro en %, más blando en threshold). Coherencia = misma filosofía en ambas etapas. Sin esto, Improve será un segundo cuello de botella invisible cuando Build empiece a pasar candidatos |
| **RetestOnAdditionalMarkets** | inactiva | **JUBILAR** | use=false (mantener) | Con caudal 0 verificado, activarla multiplicaría muertes sin señal. Reevaluar solo cuando el banco reciba decenas/día y los candidatos tengan >20-30 trades reales |
| **WalkForwardMatrix** | inactiva | **JUBILAR** | use=false (mantener) | Duplicaría el WF ya existente (mismas condiciones, robComb 2×2). Nuestra evidencia: WF Build ya filtra 99,85% — WFM sería redundante y mataría el caudal restante |
| **MonteCarloManipulation** | inactiva | **JUBILAR** | use=false (mantener) | Superpuesta con MonteCarloRetest activa. Dos puertas MC = duplicar la mortalidad del único motivo que ya mata el 100% ("sin transacciones"). No aporta robustez distinta |
| **WhatIf** | inactiva | **JUBILAR** | use=false (mantener) | Excluir 2 trades extremos es cosmético sobre estrategias que casi no tienen trades; no aporta robustez real con el caudal actual |

## Objetivo de caudal orgánico (verificable con el mismo log de mañana)
- WF (Build+Improve combinadas): aceptar **1-5%** de las generadas → con 35.592 hoy, ~350-1.800 llegarían a Retest/MC.
- Retest: **≥50%** de los que llegan pasan.
- MC: **≥50%** de los que llegan pasan (hoy: 0/650).
- Banco: **decenas/día** (hoy: 0). Métrica de éxito para mañana: `En la base de datos > 0` y aparición de motivos de rechazo DIFERENTES de "sin transacciones" (eso demostrará que la contradicción #1 está resuelta y que el embudo vuelve a ser orgánico).

## Nota de trazabilidad
- Ningún valor propuesto proviene de docs SQX ni de defaults de fábrica: todos derivan de (a) las cifras de mortalidad medidas hoy en log_2026_08_29.log, (b) la estructura del cfx real leído hoy, (c) coherencia interna entre puertas vecinas.
- NO se ha tocado project.cfx, config.xml ni ningún binario del motor (solo lectura).
