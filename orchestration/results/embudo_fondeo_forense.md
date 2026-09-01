# Embudo forense FONDEO — por qué 0 certificadas de 14.352 configuraciones

Fecha del análisis: 2026-09-01 · Solo lectura/análisis, cero minería lanzada por este informe.
Fuentes: `orchestration/results/cola_mineria.jsonl` (campaña gobernada `scripts/mine.py`),
`orchestration/results/meta_resultados.json`, `orchestration/results/campana_fondeo_1h.log`,
`orchestration/results/fase_05_discovery.log` (servicio continuo `ultrarentable-discovery.service`),
código fuente de `scripts/mine.py` y `services/discovery/discovery_validation_pipeline.py`,
y conteo directo de barras de `data/normalized/ds_trad_*_1h_*.json`.

`meta_resultados.json` contiene `{"FONDEO": null}` — no aporta nada, se descarta como fuente.

---

## 1. Resumen ejecutivo

| Pregunta | Respuesta con evidencia |
| :--- | :--- |
| ¿Cuántas celdas válidas hay hoy en disco? | **24** (12 símbolos × 2 perfiles), no 23 — el informe previo (`campana_fondeo_1h_2026-09-01.md`) es una foto tomada antes de que terminara la última celda (USDCHF amplio) |
| ¿Cuántas configuraciones se evaluaron en total? | **14.352** (4.176 del perfil `arquetipos` + 10.176 del perfil `amplio`), no 13.504 |
| ¿Cuántas de esas 24 celdas son evidencia VÁLIDA? | **18** — las 6 celdas de forex del perfil `arquetipos` corrieron con el motor ≤5.15.0 (comisión de forex rota, ver §5) y no cuentan como veredicto de edge |
| ¿Dónde muere cada configuración, en las celdas válidas? | Dos modos distintos y bien diferenciados — ver §3 |
| ¿Cuál es el techo real de operaciones por símbolo hoy? | Recalculado con el **mejor caso real observado** (no solo ES): **~61.000 barras** para 200 operaciones OOS en RTY/CL, no ~101.000 — ver §4 |
| ¿Hay algo más, fuera de esta campaña, que explique el 0? | Sí — **hallazgo nuevo**: el pipeline paralelo `ultrarentable-discovery.service` lleva **ciego a FONDEO desde 2026-08-30 ~10:30** por un bug de enrutamiento en el código actual (HEAD), no solo en el histórico — ver §5 |

---

## 2. Qué hay en disco y qué NO se puede reconstruir

`scripts/cola_mineria.py` (líneas 179-180) captura del subproceso `mine.py` solo:
```python
salida = (info["proc"].stdout.read() or "").strip().splitlines()
cola_salida = " | ".join(salida[-3:])[:500]   # ÚLTIMAS 3 LÍNEAS, truncado a 500 chars
```
`run_mining_pipeline()` (scripts/mine.py) sí calcula y devuelve una `telemetria` completa (una
entrada por configuración descartada, con `strategy_id`, `etapa`, `trades`, `pf`) y un `embudo`
agregado — pero **ese `dict` de retorno nunca se serializa a disco**: ni el CLI de `mine.py`
lo escribe (no existe `--telemetria-out`), ni la cola lo persiste (solo guarda las 3 últimas
líneas de stdout). El dato se calcula y se tira.

Consecuencia medible: la línea `Embudo: {...}` (con el desglose IS/VAL) solo sobrevive en el log
cuando **0 configuraciones alcanzan OOS** (esa línea + `Particionado` + `Minería completada` caben
en 3 líneas). En cuanto 1+ configuraciones llegan a OOS, se imprimen hasta 5 líneas `mejor: ...`
que empujan fuera la línea `Embudo`, y **solo se preservan las 2 últimas `mejor:` de esas 5** (las
peor rankeadas del top-5, no necesariamente las 2 mejores) más la línea final.

**Esto significa, explícitamente:**
- Para las **10 celdas** donde sí hay configuraciones que llegan a OOS, no se puede saber el
  número EXACTO de supervivientes de IS/VAL/OOS (solo que fue ≥2), ni si las 2 candidatas
  capturadas son las mejores o las peores del top-5 real.
- La atribución por arquetipo de §3.3 es **indicativa, no exhaustiva**: se reconstruye
  únicamente a partir de los `c<N>` índice de configuración visibles en esas 2 líneas por celda
  (20 puntos de datos en total sobre 14.352 configuraciones), mapeados de vuelta a su arquetipo
  llamando a `build_candidate_search_configs()` (lectura de código, sin backtests).
- No hay logs por-job en disco (`orchestration/logs/*.log` son de otra campaña, del 2026-08-31
  temprano; `fase_05_discovery.log` es un pipeline distinto, ver §5) que permitan recuperar la
  telemetría completa sin re-ejecutar la minería — cosa que esta tarea tiene prohibido hacer.

**Recomendación de instrumentación** (no aplicada, solo señalada): que `mine.py` escriba
`telemetria` + `embudo` completos a un JSON por job (p. ej.
`orchestration/results/telemetria/<job_id>.json`) y que `cola_mineria.py` deje de truncar a 3
líneas. Coste marginal, evita perder exactamente el dato que este informe tuvo que reconstruir
a medias.

---

## 3. Embudo por etapa — celda a celda (evidencia directa)

Filtros de `scripts/mine.py::run_mining_pipeline` (líneas 821-841): IS descarta si
`trades<5 or PF<1.05`; VAL descarta si `trades<3 or PF<1.0`; OOS descarta si
`trades<100 (MIN_OPERACIONES_OOS) or PF<1.10`. `embudo[etapa]` cuenta cuántas configuraciones
mueren en esa etapa (las que sobreviven las 3 etapas + gates se certifican; certificadas = 0 en
las 24 celdas).

### 3.1 Celdas con embudo IS/VAL completo en el log (8 celdas, todas válidas)

| Símbolo | Clase | Perfil | Total cfg | Muere IS | Muere VAL | Llega a OOS | % muere en IS |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| GC | futuro | arquetipos | 348 | 341 | 7 | 0 | 98,0% |
| ES | futuro | arquetipos | 348 | 345 | 3 | 0 | 99,1% |
| GC | futuro | amplio | 848 | 836 | 12 | 0 | 98,6% |
| EURUSD | forex | amplio | 848 | 840 | 8 | 0 | 99,1% |
| GBPUSD | forex | amplio | 848 | 832 | 16 | 0 | 98,1% |
| AUDUSD | forex | amplio | 848 | 848 | 0 | 0 | 100,0% |
| USDCAD | forex | amplio | 848 | 848 | 0 | 0 | 100,0% |
| USDCHF | forex | amplio | 848 | 828 | 20 | 0 | 97,6% |
| **Suma** | | | **5.784** | **5.718** | **66** | **0** | **98,86%** |

**De las 66 configuraciones que sí superan IS en estas 8 celdas, el 100% muere en VAL. Ninguna
llega siquiera a ser evaluada en OOS.** No es un problema de barras de OOS para estos símbolos:
mueren dos etapas antes, con muestras de apenas 5-20 trades en ventanas de miles de barras.

### 3.2 Celdas donde SÍ hay configuraciones que llegan a OOS (10 celdas; embudo IS/VAL exacto no
recuperable, ver §2)

| Símbolo | Clase | Perfil | Mejor caso visible en OOS (trades / PF) | Arquetipo (deducido) |
| :--- | :--- | :--- | :--- | :--- |
| RTY | futuro | arquetipos | 8 / 0,61 y 8 / 0,43 | SQUEEZE_BREAKOUT (ambos) |
| CL | futuro | arquetipos | 24 / 0,82 y 44 / 0,69 | SESSION_MOMENTUM, STREAK_EDGE |
| NQ | futuro | arquetipos | 0 / 0,00 y 0 / 0,00 | STREAK_EDGE (ambos) |
| YM | futuro | arquetipos | 4 / 3,68 y 4 / 3,68 | SQUEEZE_BREAKOUT (ambos, idénticos) |
| ES | futuro | amplio | 27 / 0,65 y 27 / 0,65 | TREND_FOLLOWING, MEAN_REVERSION |
| NQ | futuro | amplio | 1 / 99,00 y 1 / 99,00 | MEAN_REVERSION (ambos) |
| YM | futuro | amplio | 4 / 3,68 y 4 / 3,68 | SQUEEZE_BREAKOUT (ambos) |
| RTY | futuro | amplio | **45 / 0,62** y 45 / 0,62 | INSTITUTIONAL_SESSION_MOMENTUM (ambos) |
| CL | futuro | amplio | 9 / 1,00 y 9 / 1,00 | TREND_FOLLOWING, MEAN_REVERSION |
| USDJPY | forex | amplio | 40 / 0,89 y **48 / 0,83** | SQUEEZE_BREAKOUT (ambos) |

En estas 10 celdas la causa de muerte es siempre **`trades < 100`**, nunca `PF < 1,10` como
condición limitante: el máximo absoluto observado es 48 (USDJPY) y 45 (RTY), ambos muy por
debajo del suelo de 100. Los PF altos con pocas operaciones (NQ 99,00 con 1 trade; YM 3,68 con
4 trades) son ruido estadístico, no señal — el filtro de 100 operaciones los descarta
correctamente y el propio motor documenta ese antipatrón en un comentario (línea 836-837 de
`mine.py`: "el 2026-08-31 se colaron 30 candidatas de 17-18 operaciones que certificaron por no
operar").

**Ninguna configuración de las 14.352 llegó nunca a la etapa GATES** (evaluación de los 11
gates): la barrera de 100 operaciones OOS es, en la práctica, la única que se puso a prueba de
verdad en este dataset — el resto de gates (DSR, Monte Carlo, persistencia, etc.) nunca tuvo
ocasión de rechazar ni aprobar nada.

### 3.3 Por arquetipo (evidencia parcial — 20 puntos de datos sobre 14.352, ver limitación §2)

| Arquetipo | Apariciones entre supervivientes a OOS capturados | Símbolos donde aparece |
| :--- | ---: | :--- |
| SQUEEZE_BREAKOUT | 8 | RTY(arq), YM(arq), YM(amplio), USDJPY(amplio) |
| MEAN_REVERSION | 4 | ES(amplio), NQ(amplio) ×2, CL(amplio) |
| STREAK_EDGE | 3 | CL(arq), NQ(arq) ×2 |
| TREND_FOLLOWING | 2 | ES(amplio), CL(amplio) |
| INSTITUTIONAL_SESSION_MOMENTUM | 2 | RTY(amplio) |
| SESSION_MOMENTUM | 1 | CL(arq) |
| REVERSION_ATR | **0** | — |

REVERSION_ATR no aparece nunca entre las 20 configuraciones capturadas como "mejor superviviente
en OOS" en ninguna de las 10 celdas donde algo llega a OOS. Con solo 20 puntos de datos no se
puede afirmar que REVERSION_ATR nunca genere trades suficientes, pero es la única de las 7
familias que no deja rastro positivo en la muestra disponible — candidato a revisar primero si
se re-instrumenta la telemetría completa (§2).

---

## 4. Techo real de operaciones por símbolo (barras de hoy, 1h, dataset Yahoo `ds_trad_*`)

Conteo directo de `data/normalized/ds_trad_<símbolo>_1h_*.json` (partición 60/20/20 idéntica a
`run_mining_pipeline`):

| Símbolo | Clase | Total barras | IS | VAL | OOS | Mejor trades OOS observado | Ratio trades/barra OOS | Barras totales necesarias para 200 OOS* |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ES | futuro | 13.701 | 8.220 | 2.740 | 2.741 | 27 | 1/101,5 | ~101.500 |
| NQ | futuro | 13.699 | 8.219 | 2.740 | 2.740 | 1 (no fiable) | — | — |
| YM | futuro | 13.694 | 8.216 | 2.739 | 2.739 | 4 | 1/684,8 | ~684.800 |
| **RTY** | futuro | 13.721 | 8.232 | 2.744 | 2.745 | **45** | **1/61,0** | **~61.000** |
| GC | futuro | 13.737 | 8.242 | 2.747 | 2.748 | 0 (nunca llega a OOS) | — | — |
| **CL** | futuro | 13.541 | 8.124 | 2.708 | 2.709 | 44 | **1/61,6** | **~61.600** |
| EURUSD | forex | 17.236 | 10.341 | 3.447 | 3.448 | 0 (nunca llega a OOS, válido) | — | — |
| GBPUSD | forex | 17.241 | 10.344 | 3.448 | 3.449 | 0 (nunca llega a OOS, válido) | — | — |
| **USDJPY** | forex | 17.139 | 10.283 | 3.428 | 3.428 | 48 | 1/71,4 | ~71.400 |
| AUDUSD | forex | 17.335 | 10.401 | 3.467 | 3.467 | 0 (nunca llega a OOS) | — | — |
| USDCAD | forex | 17.334 | 10.400 | 3.467 | 3.467 | 0 (nunca llega a OOS) | — | — |
| USDCHF | forex | 17.181 | 10.308 | 3.436 | 3.437 | 0 (nunca llega a OOS, válido) | — | — |

\* Extrapolación lineal ingenua (`200 / ratio_observado / 0,2`) sobre el ratio del MEJOR caso
observado, no una garantía de que la relación se mantenga a mayor escala ni de que ese ratio
venga de una configuración con PF≥1,10 — la mayoría de estos "mejores casos" tienen PF<1,0
(ver §3.2). Es una cota de barras necesarias, no una predicción de edge.

**Corrección respecto al documento previo (`current_phase.md`, `campana_fondeo_1h_2026-09-01.md`):**
esos documentos calculan "~101.000 barras necesarias" usando solo el ratio de ES. Con el mejor
ratio real observado en toda la campaña (RTY y CL, ambos ~1 trade cada 61 barras), el techo baja
a **~61.000 barras — 4,5x el disponible hoy (13.700), no 7,3x**. Dukascopy 5m acumulado desde 2023
(~250.000 barras mencionadas en `current_phase.md`) sigue siendo suficiente por un margen amplio
si el ratio de trades/barra se mantiene at 5m (más barras, pero también arquetipos con más
señales potenciales por unidad de tiempo — no verificado, requiere minería real).

---

## 5. Hallazgo adicional — el pipeline continuo de discovery lleva ciego a FONDEO desde hace >24h

Al buscar más evidencia de FONDEO en disco aparte de `cola_mineria.jsonl`, `fase_05_discovery.log`
(el log del servicio systemd `ultrarentable-discovery.service`, **un pipeline distinto y paralelo**
a `scripts/mine.py`: `services/discovery/discovery_validation_pipeline.py`) tiene 167 líneas
`UR_FONDEO_*` — pero **todas fechadas entre 2026-08-30 02:13 y 2026-08-30 10:27**. Ni una sola
línea `UR_FONDEO_*` aparece en las 22 horas siguientes del log (hasta 2026-09-01 08:31), pese a
que el servicio sigue corriendo ciclos continuamente y los datasets `ds_trad_*` (que antes se
enrutaban a FONDEO) siguen presentes en `data/normalized/`.

**Causa raíz identificada — bug de enrutamiento en el código actual (HEAD), no solo histórico:**

`services/discovery/discovery_validation_pipeline.py` (líneas ~204-220) decide la ruta así:
```python
elif "fondeo" in fname.lower():
    route = StrategyRoute.FONDEO
elif "ultra" in fname.lower():
    route = StrategyRoute.ULTRA
else:
    is_fondeo = any(f_sym == symbol.upper() or f_sym in symbol.upper() for f_sym in [...])
    route = StrategyRoute.FONDEO if (is_fondeo and "fondeo" in fname.lower()) else StrategyRoute.ULTRA
```
El `else` solo se alcanza cuando `"fondeo" in fname.lower()` **ya es False** (falló el primer
`elif`). La condición final `is_fondeo and "fondeo" in fname.lower()` es entonces **siempre
False** para cualquier dataset sin la palabra "fondeo" en el nombre de fichero — que es el caso
de TODOS los `ds_trad_*.json` (ES, NQ, YM, RTY, GC, CL, EURUSD...). Resultado: **todo dataset de
FONDEO sin "fondeo" literal en el nombre se enruta a ULTRA**, con `initial_cap=$1.000` (en vez de
$50.000) y `dd_ceiling=25%` (en vez de 4,5%) — parámetros de otro track.

**Confirmado con `git log -p`**: el commit `687aed29f` (2026-08-30 08:46:59,
`"feat(discovery): expand ULTRA and FONDEO to all universe assets..."`) introdujo este `and`. La
versión anterior era `route = StrategyRoute.FONDEO if is_fondeo else StrategyRoute.ULTRA` (sin la
comprobación redundante del nombre de fichero) y funcionaba. El log muestra el efecto exacto: el
ciclo que empieza a las 10:30:46 (justo después de que el commit ya estuviera en disco) es el
primero en imprimir `UR_ULTRA_ES_1H`, `UR_ULTRA_AUDUSD_1H`, etc. — los MISMOS instrumentos que
0,5h antes se etiquetaban `UR_FONDEO_*`. Ningún commit posterior (`245009fe`, `a5cf4cd7`, ambos
del 2026-08-31) toca esa lógica: **el bug sigue en HEAD hoy**.

Esto es una segunda causa, independiente de la campaña `cola_mineria.jsonl` analizada en §3-4:
el servicio de discovery continuo, que corre 24/7 y es una de las tres vías de trabajo del
proyecto, **no ha evaluado ni una sola estrategia FONDEO real desde hace más de 24 horas**, y
cuando lo hacía (antes del bug) usaba capital inicial y techo de drawdown de ULTRA, no de FONDEO.
No se ha corregido este código en esta tarea (fuera de alcance: la tarea es lectura/análisis, no
edición de motor) — se reporta como hallazgo para que el orquestador decida.

**No aplica Regla #26**: este hallazgo no implica ningún cambio de código en esta tarea; no se ha
tocado `services/discovery/discovery_validation_pipeline.py` ni ningún otro fichero de producción.

---

## 6. Hallazgo adicional — los datos de discovery del 2026-08-30 son inválidos como evidencia de edge

Las 167 líneas `UR_FONDEO_*` de §5 (52 combinaciones símbolo×TF: 15M/1H/4H/5M sobre ES, NQ, YM,
RTY, GC, CL, SI + 6 divisas) son anteriores a **toda** la cascada de fixes del motor documentada
en `services/engine_version.py`, todos fechados 2026-08-31 o después:

- 5.5.0: semántica de cruce corregida (antes, señal de "estado" en vez de "evento" → casi
  siempre en mercado)
- 5.6.0: `point_value` real CME por símbolo (antes, FONDEO probablemente usaba 1.0 como ULTRA)
- 5.9.0: latencia de entrada (antes, fill en el mismo close de la señal — look-ahead)
- 5.10.0: unidad de riesgo fracción vs. porcentaje (bug de sizing ~100x)
- 5.11.0: sizing consciente de `point_value` en futuros
- 5.16.0: comisión de forex (2026-09-01, posterior incluso a la campaña de §3-4)

Los resultados del 2026-08-30 (p. ej. `UR_FONDEO_SI_1H -> REJECTED_GATES_INCOMPLETE, OOS Trades:
115, OOS PF: 1,25, Gates: 9/11` — el caso más prometedor de todo el log) **no se pueden citar
como evidencia de edge o de ausencia de edge**: corren sobre un motor con look-ahead, sizing
~100x incorrecto y sin el multiplicador CME real. Se documentan aquí solo para que quede
constancia de por qué se descartan, no como insumo para la decisión de §7.

---

## 7. Recomendación priorizada

1. **No relanzar minería FONDEO en 1h con los perfiles `arquetipos`/`amplio` tal cual hasta
   resolver el cuello de datos.** El 98,9% de mortalidad en IS (§3.1) y el hecho de que ninguna
   configuración pase de 48 operaciones OOS (§3.2) son dos síntomas del mismo problema de fondo:
   con 13.5-17.3k barras 1h, el suelo de 100 operaciones OOS es prácticamente inalcanzable salvo
   en el mejor 1-2% de configuraciones, y aun esas no tienen PF≥1,10.
2. **Priorizar el backfill de Dukascopy para RTY y CL primero, no solo ES.** Son los símbolos con
   mejor ratio trades/barra observado (~1/61, §4) — el techo real (~61.000 barras) es más
   alcanzable que el de ES (~101.500) y muchísimo más que el de YM (~684.800, arquetipo actual
   mal ajustado a ese símbolo). RTY no tiene proxy Dukascopy (`FONDEO_DUKASCOPY_PROXY`, ver
   `current_phase.md`) — decisión pendiente de si se acepta Yahoo para RTY o se excluye.
3. **Corregir el bug de enrutamiento de §5 antes de asumir que el servicio de discovery continuo
   aporta cobertura FONDEO.** Hoy no aporta ninguna desde hace >24h, y aunque se corrija el
   enrutamiento, ese pipeline reutiliza el mismo motor y los mismos filtros — no resuelve el
   cuello de barras de §3-4 por sí solo.
4. **Instrumentar la telemetría completa (§2) antes de la próxima campaña grande.** Con 14.352
   configuraciones evaluadas y solo 20 puntos de datos recuperables sobre supervivientes a OOS,
   la próxima campaña de este tamaño será tan ciega como esta si no se persiste
   `embudo`+`telemetria` a disco. Coste bajo, ya calculado por `run_mining_pipeline` y tirado.
5. **REVERSION_ATR (§3.3) es el arquetipo con menos indicios de generar volumen de trades
   suficiente** en la muestra parcial disponible — candidato a revisar primero (¿el ancla EMA +
   banda ATR es demasiado restrictiva en 1h?) si se decide invertir en mejorar arquetipos en vez
   de solo esperar más barras. Esto no se puede confirmar sin la telemetría completa del punto 4.
6. **Antes de certificar cualquier cosa sobre Dukascopy**, sigue pendiente la validación
   doctrinal ya señalada en `current_phase.md`: son CFDs proxy, no futuros CME reales — requiere
   validar correlación/spread en el tramo que solapa con Yahoo antes de tratarlos como
   equivalentes.
