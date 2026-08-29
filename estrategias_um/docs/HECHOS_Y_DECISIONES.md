# 04_HECHOS_Y_DECISIONES.md — Hechos verificados vs hipótesis (2026-08-29)

> Regla del proyecto: HECHO = verificado con herramienta y fuente citada. HIPÓTESIS = no confirmada, marcada como tal. Evidencia cruda en `evidencia/2026-08-29/`.

## 1. HECHOS verificados (con fuente)

| # | Hecho | Evidencia |
|---|---|---|
| H1 | El día 29 se generaron **62.942+ estrategias y 0 fueron guardadas** en todo el día | `docs/FUNNEL.md` (log 14:00:23 "Estrategias generadas 62942", 46 status "En la base de datos 0"); API 16:17: 107.914 generadas, Aceptado 0,00% |
| H2 | **~99,85% muere ANTES del Monte Carlo sin traza individual** (solo agregados "Rechazado 100,00%") | `docs/FUNNEL.md`: 94 de 62.942 llegan a MC |
| H3 | **El 100% de las que llegan al MC mueren con el motivo ÚNICO "Filtro automático: sin transacciones"** (4.826+ dismissals, 650 estrategias distintas, cero otros motivos) | `docs/FUNNEL.md` + log, verificado a las 16:20 |
| H4 | **El fusible está en código**: `BadStrategyException` en `BacktestEngine.computeResults` cuando `OrdersList.size()==0` (check por-sim, no por conjunto); el texto sale de la clave "Automatic filter" + "no trades" → Spanish.csv L1889 "sin transacciones" | javap en `evidencia/2026-08-29/mcprobe/` + `internal/langs/Spanish.csv` L1889 y English.csv L3367 |
| H5 | El `<AutomaticDismissal><Problem code="1" dismiss="true"/>` del project.cfx es lo que ACTIVA ese fusible | `evidencia/2026-08-29/mcprobe/fuse_evidence.txt` |
| H6 | **Apagar RandomizeHistoryData (±10 velas) y RandomizeStrategyParameters NO redujo las muertes** — la causa NO era la perturbación de datos/parámetros | log: 913 muertes 14h, 450 a 15h tras ambos parches; motivo idéntico |
| H7 | **El motor sirve la configuración de SU MEMORIA**: los parches escritos en project.cfx no surten efecto hasta recargar/reiniciar el proyecto | config.xml en disco dice Output=LastGeneration; el runtime escribe en "Last generation" legacy; parches en disco verificados pero mortalidad sin cambio |
| H8 | **Duplicidad de bancos**: "Last generation" (legacy, con espacio) acumuló **91-93 estrategias crudas REALES**; "LastGeneration" (renombrado hoy en config) = 0 | API `-databank action=list` 15:31 y 16:17 |
| H9 | **El gatillo del meta-ciclo está roto**: improve_cycle.sh cuenta `LastGeneration` (0 eterno) → umbral 30 nunca se cruza; 9 ticks hoy todos "espero" | `improve_cycle.log` + script línea 61 |
| H10 | **El nombre con espacio NO es direccionable por `count name=`** (devuelve "Databank 'Last' doesn't exist"); solo vía `action=list` | probado por API 16:32 |
| H11 | **improve_cycle.sh NO está en crontab** (y su origen de disparo es desconocido); sqx_autostart.sh nunca ejecutado | `crontab -l` + cartógrafo (01_ESTADO.md R4) |
| H12 | Coherencia rota entre puertas: WF Build (thresholdPct=80, MinTradesInRun>20, period optim=20) × MaxTradesPerDay=1 → exigir >20 trades por tramo a un bot limitado a 1/día obliga a operar casi todos los días → backtests vacíos = el motivo H3 | `docs/CONFIG_DOORS.md` + `docs/FILTROS_ORGANICOS.md` contradicción a |
| H13 | Todo vive en RAM del motor: disco `databanks/*` = 0 archivos; un reinicio pierde lo no exportado | cartógrafo 01_ESTADO.md §3, verificado 16:17 |
| H14 | De fábrica, el examen MonteCarloRetest viene APAGADO en toda la instalación y los métodos de aleatorización de velas apagados en las plantillas del builder | `docs/FACTORY_REFERENCE.md` (solo referencia, NO autoridad) |

## 2. HIPÓTESIS (NO confirmadas)

| # | Hipótesis | Estado |
|---|---|---|
| P1 | **RandomizeStartingBar (0-100) es el culpable residual H6**: retrasa el inicio hasta 100 barras y una estrategia poco frecuente queda a 0 trades en esa ventana | Razonable (veredicto del detective), **sin experimento confirmatorio** |
| P2 | RandomizeMinDistance/Spread/Slippage también pueden vaciar fills | Candidatos menores, sin confirmar |
| P3 | Con umbrales orgánicos (C2) el caudal sería WF 1-5%, MC ≥50%, decenas/día al banco | Objetivo de diseño, sin medir aún |
| P4 | `startOnlyTask task=2` lanza realmente Improve | Índice no confirmado en vivo (verificar al usar) |

## 3. DECISIONES PENDIENTES (requieren aprobación del usuario)

| # | Decisión | Opciones | Recomendación |
|---|---|---|---|
| DD1 | ¿Qué hacer con el fusible MC? | (a) apagar RandomizeStartingBar y probar; (b) apagar además MinDistance/Spread/Slippage; (c) desactivar MC del todo | **(a) primero, un cambio por vez** midiendo motivo de muerte tras cada uno; NUNCA tocar AutomaticDismissal global (H4-H5) |
| DD2 | ¿Recargar config del motor? | (a) reinicio del proyecto vía API (recarga config, vacía bancos RAM); (b) dejar como está | **(a) PERO solo DESPUÉS de capturar el semillero** (H8+H13: sin export previo se pierde) — orden estricto en FASE 1 |
| DD3 | ¿Bancos legacy vs renombrados? | (a) parchear improve_cycle.sh para leer via `list` (acepta espacios); (b) intentar forzar rename en caliente | **(a)** — el runtime usa el legacy (H7); parche de NUESTRO script, cero riesgo |
| DD4 | ¿Jubilar OptProfileSysParamPermutation? | (a) use=false; (b) dejarlo | **(a) aplazado**: 0 llegadas jamás (H2), pero si DD1+C2 abren caudal, re-evaluar con datos |
| DD5 | ¿Umbrales orgánicos C2 (WF 70/8, Retest ≥50%, MC suavizado)? | (a) aplicar todos; (b) solo los contradictorios (MinTradesInRun) | **(a)** en una sola ventana de parada (una sola cirugía = medición limpia) |
| DD6 | ¿Arrancar 1er ciclo con las ~91 semillas CRUDAS (no validadas)? | (a) sí, mandato bancar; (b) esperar a que el embudo valide | **(a)**, anotando banco_origen en el CSV (riesgo marcado) |

## 4. Experimentos abiertos (si se retoman)

| Experimento | Coste | Valor |
|---|---|---|
| E1: apagar RandomizeStartingBar → medir motivo de muertes 30 min | 1 ventana de parada (~2 min) + 30 min de log | Confirma/refuta P1 — decide DD1 |
| E2: primer ciclo del lazo con semillas crudas | ~30-40 min por API | Demuestra el meta-ciclo entero (FASE 1) |
| E3: confirmar índice task=2 = Improve | 1 API call + status | Cierra P4 antes de la primera mejora |
