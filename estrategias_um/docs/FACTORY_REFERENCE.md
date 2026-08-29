# Referencia de FÁBRICA — MonteCarloRetest / RandomizeHistoryData (SQX build 144)

Fuente: instalación local `/home/ubuntu/StrategyQuantX144` (solo lectura, excluyendo `user/projects`).
Nuestro bloque: `/tmp/um_doors/cfx_actual/Build-Task1.xml` líneas 1330–1396 (`MonteCarloRetest use="true"`).

## Bloques de fábrica encontrados (verbatim, resumidos)

1) `internal/plugins/TaskBuild/task_forex.xml` (idéntico en task_futures.xml, task_stockpicker.xml) L403:
   `<MonteCarloRetest use="false">` → RandomizeHistoryData: ProbabilityUp=30, ProbabilityDown=30, MaxChangeUp=30, MaxChangeDown=30; RandomizeMinDistance 0–10; Slippage 0–5; Spread 1–5; StartingBar 100; StrategyParams Prob=10 MaxChange=20 Symmetric=true; NumberOfSimulations=10. Condiciones: MC NetProfit >= main NetProfit(pctRatio=50); MC DrawdownPct <= main DD (pctRatio=200).

2) `internal/plugins/TaskRetest/task.xml` L315: `<MonteCarloRetest use="false">` → mismos 30/30/30/30, sims=10, mismas condiciones que (1).

3) `internal/plugins/TaskAutomaticRetest/task.xml` L149: `<MonteCarloRetest use="false">` → RandomizeHistoryData estilo antiguo: Probability=20, MaxChange=10; sims=100; `<Conditions/>` vacías (sin condiciones de aceptación).

4) `internal/web/BUILDER/templates/tpl_build.xml` L122 (RobustnessTests, todos use="false") → RandomizeHistoryData: Probability=20, MaxChange=10; sims=10.

5) `internal/web/BUILDER/simpleTemplates/Default.xml` (y DefaultForex.xml, etc.) L403: `<MonteCarloRetest use="false">` → 30/30/30/30, sims=10, mismas condiciones que (1).

6) `internal/plugins/TaskBuild/task_futures.xml` L590 y `DefaultForex.xml` L580: segunda referencia (Retest MC posterior) con sims=30.

Nota: `tests/tmp/simpleBuilderConfig.xml` L1330 tiene EXACTAMENTE nuestros valores (10/10/10/10, sims=20, use=true) — es fichero de test, no de fábrica; confirma que nuestra config proviene de ese estilo, no del default de la instalación.

## Tabla comparativa

| Parámetro | Nuestro valor (Build-Task1.xml) | Valor de fábrica | Fichero fuente de fábrica | ¿Desviación? |
|---|---|---|---|---|
| MonteCarloRetest @use | **true** | **false** (en TODOS los bloques de fábrica) | TaskBuild/task_forex.xml L403, TaskRetest L315, TaskAutomaticRetest L149, simpleTemplates/Default.xml L403 | ⚠️ SÍ — activamos el check que de fábrica está apagado |
| RandomizeHistoryData ProbabilityUp | 10 | 30 | task_forex.xml L407, Default.xml L408, TaskRetest L319 | ⚠️ SÍ (10 vs 30) |
| RandomizeHistoryData ProbabilityDown | 10 | 30 | ídem | ⚠️ SÍ |
| RandomizeHistoryData MaxChangeUp | 10 | 30 | ídem | ⚠️ SÍ |
| RandomizeHistoryData MaxChangeDown | 10 | 30 | ídem | ⚠️ SÍ |
| (variante antigua) Probability / MaxChange | — | 20 / 10 | TaskAutomaticRetest L153-154, tpl_build.xml L123-124 | n/a (esquema distinto) |
| RandomizeMinDistance Min/Max | 0.0 / 10.0 | 0.0 / 10.0 | task_forex.xml L415-418 | ✅ igual |
| RandomizeSlippage Min/Max | 0.0 / 5.0 | 0.0 / 5.0 | task_forex.xml L421-424 | ✅ igual |
| RandomizeSpread Min/Max | 1.0 / 5.0 | 1.0 / 5.0 | task_forex.xml L427-430 | ✅ igual |
| RandomizeStartingBar MaxChange | 100 | 100 | task_forex.xml L433 | ✅ igual |
| RandomizeStrategyParameters Prob/MaxChange/Symmetric | 10 / 20 / true | 10 / 20 / true | task_forex.xml L437-440 | ✅ igual |
| NumberOfSimulations | 20 | 10 (TaskBuild/TaskRetest/simpleTemplates); 100 (TaskAutomaticRetest); 30 (2ª ref. futures/forex) | task_forex.xml L443, TaskAutomaticRetest L191 | ⚠️ SÍ (20 vs 10) |
| Condición NetProfit: MC >= main (pctRatio=50, conf 80/90) | presente, idéntica | presente, idéntica | task_forex.xml L448-459 | ✅ igual |
| Condición DrawdownPct: MC <= main (pctRatio=200) | presente, idéntica | presente, idéntica | task_forex.xml L460+ | ✅ igual |

## Conclusión / propuesta de corrección segura

Desviaciones detectadas: (a) `use="true"` cuando la fábrica lo trae `false`; (b) RandomizeHistoryData 10/10/10/10 en vez de 30/30/30/30; (c) 20 sims en vez de 10.

Importante para el diagnóstico: restaurar 30/30/30/30 RANDOMIZA MÁS los datos (no menos), y 20→10 sims no elimina el problema de backtests sin trades con MaxTradesPerDay=1. El único ajuste que reproduce el comportamiento de fábrica al 100% es `MonteCarloRetest use="false"` (estado de fábrica en todos los task/templates) o, si se quiere conservar el check, `Method use="false"` en RandomizeHistoryData (tpl_build.xml trae todos los métodos use="false" por defecto), dejando el resto de métodos y condiciones como están.

Propuesta priorizada:
1. Mínima y más segura: `MonteCarloRetest use="true"` → `use="false"` (restaura fábrica exacta; el filtro 'sin transacciones' desaparece porque no se ejecutan las sims).
2. Si se exige mantener MonteCarloRetest activo: poner `RandomizeHistoryData` en `use="false"` (patrón de fábrica de tpl_build.xml) y opcionalmente NumberOfSimulations 20→10.
3. No tocar: Slippage/Spread/MinDistance/StartingBar/StrategyParams ni las condiciones NetProfit/DD — ya son idénticos a fábrica.
