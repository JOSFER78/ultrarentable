# PLAN COMPLETO DEL PIPELINE DE ESTRATEGIAS — Ultra_Matrix (2026-08-29)

Fuente: evidencia propia exclusiva (log_2026_08_29.log, project.cfx real, javap en /tmp/um_mcprobe/,
API 5050 read-only). Sin docs oficiales ni defaults de fábrica como autoridad. Motor SOLO lectura
desde el plano; toda modificación se ejecuta por ventanas de parada controladas.

## 0. Definiciones de estado (criterios de paso explícitos)

| Estado | Definición operativa | Criterio de paso (verificable) |
|---|---|---|
| **CRUDA** (semilla) | Estrategia generada por el Build, pre-filtro o que no cruzó puertas. Hoy: `Last generation` (legacy, 95–97 records volátiles). | Existe en databank o CSV exportado. Sin criterio de calidad: es materia prima. |
| **CANDIDATA** | CRUDA que cruza las 4 puertas del Build: WF (thresholdPct 70, MinTradesInRun>8), RetestPrecision (≥50%), MonteCarlo (≥50%, fusible MC corregido), OptProfilePermutation. | Aparece en `Results`/databank de salida del Build (`En la base de datos > 0`). Origen anotado en CSV (columna banco_origen). |
| **VALIDADA** | CANDIDATA que además cruza Improve: WF-Improve con umbrales ALINEADOS al Build (un solo criterio, ver D2), permanece ≥1 ciclo sin degradarse en refiltro. | Record en `Results_robust_20260809` + sobrevive al refiltro siguiente (no purgada por ReturnDDRatio) + CSV diario la contiene 2 veces seguidas. |
| **META-ESTRATEGIA** | VALIDADA que se convierte en insumo del lazo: su variante mejorada entra a `InitialPopulation` y el genético arranca evolucionando sobre ella. | `InitialPopulation Records > 0` Y el siguiente "Project started" del Build arranca con InitialPopulation poblado (verificado por API `-databank action=list`). |

## 1. Correcciones del embudo (precondición de todo el pipeline)

C1. **Fusible MC por trades=0** (causa raíz verificada por javap): el fusible es por-sim en
    BacktestEngine.computeResults cuando OrdersList.size()==0 (AutomaticDismissal bit 1). Acción:
    apagar `RandomizeStartingBar` (0–100 → off) en MonteCarloRetest; si persiste, probar apagando
    RandomizeMinDistance/Spread/Slippage en orden. NO tocar AutomaticDismissal del proyecto.
C2. **Filtros orgánicos** (filtros_organicos.md, ya justificados por mortalidad medida):
    WF Build: period 5→10, optim 20→10, thresholdPct 80→70, MinTradesInRun >20→>8, WFO%>60→>30,
    ProfitableRuns>70→>60, MaxProfitByRun<50→<60, DD≤25→≤30. Retest: NP y trades ≥80%→≥50%.
    MC: RandomizeHistoryData Prob 10→5/Change 10→5, StrategyParams 10/20→5/10, StartingBar→50,
    condición NP p80 ≥ main p90×50%→×30%.
C3. **Coherencia WF Build/Improve**: hoy Build thresholdPct=80 vs Improve=65 con NetProfit%>65>60 —
    filosofías opuestas en puertas consecutivas. Unificar: un solo juego de umbrales WF (los del C2)
    para Build e Improve; Improve aporta solo lo que el Build no hace (parametrización Recommended,
    stabilityRange), no una segunda WF contradictoria.
C4. **Gatillo del meta-ciclo**: parchear improve_cycle.sh para parsear count desde
    `-databank action=list` (nombres con espacios no direccionables por `count name=`); semillero =
    suma de `Last generation` + `LastGeneration`; crontab explícito `*/15 * * * *`.

## 2. El lazo banco→mejora→refiltro→InitialPopulation (ciclo cerrado)

```
[Build corre] → `Last generation` (semillero crudo, volátil)
   watchdog 15 min: semillero≥umbral y estable ≥2 ticks
   → CAPTURA (stop) → copy semillero→ToImprove + export CSV evidencia
   → MEJORA (startOnlyTask task=2) → Results_robust_20260809
   → REFILTRO (al terminar Improve): export CSV + purgar peores N por ReturnDDRatio
       → copy Results_robust→InitialPopulation
   → re-arrancar Build con InitialPopulation poblado  ← LAZO CERRADO
```
Reglas del lazo: solo con proyecto parado; guard ToImprove>0 antes de Improve; guard
InitialPopulation>0 antes de re-arrancar; snapshot CSV diario 04:00 cinturón anti-reciclado;
si semillero=0 real, el watchdog espera y registra — nunca se fabrican semillas.

## 3. FASE 1 — Primeras 24h (desbloquear y capturar)

Actor: **yo** por API/script (sqcli 5050, ediciones de config por ventana de parada).
Subagente: solo el diagnóstico MC si C1 requiere más ingeniería inversa.
1. Ventana de parada: aplicar correcciones del embudo en project.cfx: C1 (RandomizeStartingBar
   off + fallbacks), C2 (umbrales orgánicos), C3 (unificar WF Build/Improve). Backup previo del cfx.
2. Capturar el semillero legacy: copy `Last generation`→ToImprove + export CSV
   `/home/ubuntu/ORDENAR/semillas_*.csv` (las 95+ crudas reales, inmunes al reciclado).
3. Ejecutar primer ciclo manual del lazo (§2) con ese semillero, aunque sean crudas no-MC-validadas
   (mandato del usuario lo autoriza; riesgo marcado con banco_origen en CSV).
4. Parchear improve_cycle.sh (C4) y añadir crontab */15.
**Verificación de éxito FASE 1**: (a) tras re-arranque, motivos de rechazo en log DIFERENTES de
"sin transacciones" (la contradicción MinTradesInRun×MaxTradesPerDay resuelta); (b) `En la base de
datos > 0` en alguna línea de status; (c) ToImprove>0 e InitialPopulation>0 por API; (d) al menos
un "Project started" con InitialPopulation poblado (lazo cerrado una vez). Caudal esperado: WF acepta
1–5% de generadas; MC ≥50% de las que llegan; banco decenas/día.

## 4. FASE 2 — Primera semana (régimen continuo y calibración)

Actor: **yo** (scripts cron + análisis diario de log/métricas) + **subagente** para análisis
forense nocturno del log (distribución de mortalidad por puerta, detección de nuevas contradicciones).
1. Lazo en producción: watchdog cada 15 min → ciclos captura/mejora/refiltro automáticos con guards.
2. Calibración por evidencia: cada día, medir caudal real por puerta (generadas → WF → Retest → MC
   → banco) y ajustar solo la puerta cuya mortalidad se desvíe del objetivo orgánico (WF 1–5%,
   Retest ≥50%, MC ≥50%), un parámetro por vez, con backup y re-medición.
3. Anti-estancamiento: purga de peores N de InitialPopulation por ReturnDDRatio en cada refiltro;
   snapshot CSV diario 04:00; monitoreo de diversidad (nº de firmas de reglas distintas en el banco).
4. Registro: bitácora por ciclo (timestamp, counts por banco, cambios aplicados) en /tmp/um_restruct/.
**Verificación de éxito FASE 2**: (a) ≥5 ciclos completos del lazo en la semana sin intervención
manual de emergencia; (b) banco de VALIDADAS crece monótonamente (≥ decenas/día sostenido);
(c) mortalidad MC <50% sostenida; (d) cero días con "En la base de datos 0" completo;
(e) snapshot CSV diario presente y no vacío.

## 5. FASE 3 — Estabilización (semana 2+)

Actor: **yo** (supervisión por excepción) + **subagente** (auditorías semanales del cfx vs lo
documentado; estudios sobre VALIDADAS: correlación entre pares, estabilidad out-of-sample real).
1. El lazo corre solo; intervención solo si un guard falla o el caudal cae bajo el objetivo 3 días.
2. Apretar progresivamente SOLO si hay excedente: si el banco recibe >decenas/día de forma estable
   durante ≥1 semana, subir un umbral WF por vez hacia versiones más exigentes, midiendo siempre
   el efecto en caudal antes del siguiente ajuste.
3. Meta-estrategias de 2º orden: usar las VALIDADAS más longevas (sobrevivieron ≥N refiltros) como
   semilla preferente del genético (peso en InitialPopulation), cerrando "estrategias que buscan
   estrategias" en su forma fuerte.
4. Estudios sobre el banco validado (mandato SOLO-línea-de-estrategias): cuales atributos de las
   VALIDADAS predicen supervivencia al refiltro siguiente; retroalimentar como filtro orgánico.
**Verificación de éxito FASE 3**: (a) 14 días sin pérdida de semillero (todo snapshot recuperable);
(b) pipeline completo ejecuta sin intervención ≥7 días; (c) definición de META-ESTRATEGIA cumplida
en producción: InitialPopulation poblado por descendientes de VALIDADAS, Build arrancando sobre ellas;
(d) métricas de caudal dentro de objetivo orgánico con umbrales estables (sin oscilaciones >2 ajustes).

## 6. Riesgos y decisiones de contingencia

- Si apagar RandomizeStartingBar no basta (C1): apagar métodos de randomización restantes uno a uno,
  medir motivo de muerte tras cada cambio; el fusible por trades=0 NUNCA se desactiva globalmente.
- Si el banco legacy se recicla antes de la captura: los CSV de evidencia son la única fuente
  irrecuperable — captura es la PRIMERA acción de FASE 1.
- Nunca fabricar datos: sin semillero real, el sistema espera (watchdog pasivo registrado).
