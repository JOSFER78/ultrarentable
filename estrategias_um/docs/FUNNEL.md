# Forense del embudo — Ultra_Matrix (log_2026_08_29.log, snapshot 14:04 UTC)

## Regla de evidencia
Todas las cifras provienen de líneas reales del log de hoy (no existe log_2026_08_28.log en el directorio;
el día 29 acumula toda la actividad). Extracción: grep/rg sobre
`/home/ubuntu/StrategyQuantX144/user/log/StrategyQuant/log_2026_08_29.log` (15 MB). SOLO LECTURA.

## Tabla del embudo (run vigente, contador reseteado a 0 a las 11:53:19)

| Etapa | Estrategias | % que sobrevive | % muertes en esta puerta | Evidencia (línea de log) |
|---|---|---|---|---|
| Generadas | 62,942 | 100% | — | `14:00:23.585 ... Estrategias generadas  62942` |
| Pasan WF / CrossChecks previos | no registradas por línea | — | ~99.85% mueren AQUÍ de forma silenciosa | Solo contadores agregados: `Rechazado 100.00 %` (26 veces), `Aceptado 0.00 %` (46 veces), `Fallido 0 / Éxito 0` (44 veces). Cero líneas "passed"/"failed" por estrategia (`rg -c passed` = 0) |
| Llegan a MC retest (distintas) | 519 | 0.82% del total generado histórico | — | `rg -o "MC retest job Strategy [0-9.]+" \| sort -u \| wc -l` → 519 (run completo del día) |
| Pasan MonteCarlo | **0** | 0% | **100% de las que llegan** | 3,581 líneas `MC retest job ... dismissed`, 100% con el mismo motivo |
| Guardadas / En la base de datos | **0** | 0% | — | 46 status lines `En la base de datos 0` (última `14:00:23.586 ... En la base de datos 0`); `Records: 0` en todos los databanks |

## Puerta asesina Nº1: MonteCarlo — "Filtro automático: sin transacciones"
- 3,581/3,581 (100%) de las líneas MC retest terminan en: 
  `09:07:28.004 [Blocking computeThread common #0 - Builder_5-Generation 6.1.119] ERROR MonteCarloCrossCheckMethod - MC retest job Strategy 6.1.119 MC 5 dismissed, error: Exception in backtest: Filtro automático: sin transacciones`
- Único motivo presente en TODO el día: "sin transacciones" (3,579 líneas MC + 2 variante sin prefijo MC). 
  Cero menciones de ProbabilityUp, NetProfit, Sharpe u otros motivos de MC (`rg -c ProbabilityUp` = 0).
- 519 estrategias distintas murieron en MC; cada una pierde todos sus jobs MC (MC 0–19).
- Distribución horaria de muertes MC: 09h=733, 10h=1020, 11h=892, 12h=201, 13h=639, 14h=31.

## Puerta asesina Nº2 (invisible, por volumen): el filtro previo a MC
- De 62,942 generadas en el run vigente, solo 94 estrategias distintas llegaron siquiera a MC (0.15%).
  Las otras ~62,848 (99.85%) son rechazadas sin NINGUNA línea de examen individual:
  el log solo registra el agregado `Rechazado 100.00 %` / `Aceptado 0.00 %`.
- No hay líneas de Walk-Forward/Retest pass/fail en el log (0 matches de "walk", "passed", "failed").
  Muerte mayoritaria, pero sin evidencia de en qué sub-condición exacta.

## Re-arranque (~12:35 indicado; en el log el proyecto arrancó 12:14:45 y de nuevo 13:16:01)
- Arranques: `12:14:45.063 =========== Project started ===========` (task 2 a las 12:17:13) y 
  `13:16:01.429 =========== Project started ===========` (run vigente).
- Guardadas desde el re-arranque: **0**. Evidencia: `13:18:52 ... En la base de datos 0`, 
  `13:56:20 ... En la base de datos 0`, `14:00:23 ... En la base de datos 0`.
- Primera cola de MC retests tras el arranque de 12:14: **12:16:34.332** 
  (`... Builder_2-Generation 3.1.168 ... MC 10 dismissed ... sin transacciones`).
- Primera cola de MC retests tras el arranque de 13:16: **13:17:16.579** 
  (`... Builder_2-Generation 3.1.156 ... MC 1 dismissed`).
- Tras el fix (MC ProbabilityUp 30→10) NO se ve ninguna línea de ProbabilityUp: el cuello de botella 
  sigue siendo "sin transacciones" en el backtest del retest MC, no el umbral ProbabilityUp.

## Conclusión
- Embudo observado: 62,942 generadas → ~94 (0.15%) llegan a MC → 0 pasan MC (0/519 en el día) → 0 guardadas.
- Puerta Nº1 por volumen: rechazo silencioso pre-MC (99.85% de las generadas, sin trazas individuales).
- Puerta Nº1 con trazas explícitas: MonteCarlo retest, motivo único "Filtro automático: sin transacciones" 
  (3,581 dismissals, 519 estrategias, 100% de mortalidad entre las que llegan).
- El fix ProbabilityUp 30→10 no ha cambiado nada observable: sigue 0 guardadas y el motivo de muerte 
  dominante es otro (sin transacciones en retest MC).
