# Motor propio de mejora: primera entrega comprobada con un caso real

Fecha: 2026-09-06, 15:15 CEST. VPS: 88.99.210.167. Rama: `motor-mejora-entrega-1`.
Estrategia: `Strategy 1.1.27` sobre @EW H1 (E-mini S&P MidCap 400, datos de futuros continuos de SQX).
Destinos evaluados: Fondeo (escenarios provisionales de examen) y Ultra (exploratorio).

Resumen en una línea: **el mecanismo funciona de principio a fin con una estrategia real
(contrato → diagnóstico → hipótesis pre-registradas → dos variantes reales → recálculo nativo →
comparación emparejada → clasificación → entrega), ninguna variante alcanza progreso útil y ninguna
es candidata a validación.** Cero estrategias acreditadas para fondeo. Nada de esto predice
resultados futuros.

## 1. Qué funciona ahora y cómo se comprobó

| Capacidad | Comprobación |
| --- | --- |
| Contrato de entrada reproducible desde un `.sqx` (instrumento, temporalidad, datos, periodo IS/OOS, entradas, salidas, tamaño, costes, opciones, procedencia, carencias) | `contract.json` del ciclo; estado `CONTRACT_COMPLETE`; prueba con archivo roto → `CONTRACT_INCOMPLETE` con la carencia nombrada |
| Distinción entre cambio real y cambio de metadatos | La variante real del Improver nativo (`Strategy 1.1.27 - Improved 1.1.15`) se clasifica `METADATA_ONLY_NO_BEHAVIOUR_CHANGE` y queda `REJECTED_BEFORE_RETEST`: no gastó recálculo |
| Referencia reproducible | El control recalculado a las 15:13 CEST produce exactamente las mismas 230 órdenes (fecha, precio, P&L, tipo de cierre) que el control del experimento de las 12:02 CEST |
| Diagnóstico determinista de las órdenes (salidas, devolución de MFE, concentración, horarios, costes, frecuencia, múltiplos R, cribado de examen provisional, estudio de exposición) | `diagnosis_base_fresh.json`; valor del punto deducido de las órdenes (100) coincide con la ficha CME |
| Hipótesis solo cuando el hallazgo aparece en IS y en OOS; criterios registrados antes de recalcular | `plan.json`, `criteria.json` (hash fijado en la evaluación); una tercera hipótesis (`H_SL_TIGHT`) queda `NOT_SUPPORTED_IN_BOTH_SAMPLES` |
| Mutaciones verificadas (cambian exactamente los parámetros previstos y nada más) | `manifest.json` → `variants[].changes`; el motor rechaza un valor idéntico ("no altera nada") |
| Recálculo nativo con evidencia (SQX 144.2953, precisión M1, un contrato) | `verified_start.json`, `native_retest.log` ("Éxito: 3, Fallido: 0"), órdenes exportadas con el lector Java de SQX, hashes |
| Comparación emparejada por día y clasificación honesta | `evaluation.json`: sumas de deltas, IC bootstrap 80/90 %, prueba de signos, tolerancias de equivalencia, cribado por destino |
| Registro por estrategia para no repetir variantes | `improvement_registry/<reglas>.json` con cuatro variantes ya exploradas y dos experimentos |
| Pruebas | 170 pruebas de `tests/sqx_runtime` correctas (15 en `test_improvement_cycle.py`, 5 en `test_hypothesis_debate.py`, sobre la evidencia real y con respuestas de agentes grabadas) |
| Debate de agentes (fase 2, §8 bis y §8 ter) | Tres debates reales (dos por Claude Code, uno por el omnirouter del sistema) y dos ciclos recalculados en SQX con hipótesis nacidas del debate |
| Revisión adversarial del código nuevo | Doce hallazgos (subagente revisor); los confirmados se corrigieron antes de cerrar y se re-evaluó todo con el código corregido (sección 4 bis) |

## 2. Qué cambió y por qué

- `scripts/herramientas/sqx_strategy_contract.py` (nuevo): contrato de entrada, hash semántico de reglas (ignora metadatos de editor y renombrados de identificadores de orden, conserva fórmulas y valores) y comparador de reglas con rutas estructurales.
- `scripts/herramientas/sqx_trade_diagnosis.py` (nuevo): diagnóstico desde las órdenes nativas; tipos de cierre según `OrderCloseTypes` de la instalación (javap, 2026-09-06); escenarios de examen provisionales explícitos; ventanas rodantes de 1–5 días con recuento de ventanas disjuntas; estudio de exposición por contratos.
- `scripts/herramientas/sqx_variant_mutations.py` (nuevo): cambios de salida verificados (objetivo, stop, trailing y activación, ATR o fijo).
- `scripts/herramientas/sqx_improvement_cycle.py` (nuevo): ciclo completo por subcomandos (`prepare-local`, `run`, `evaluate`) con criterios pre-registrados, clasificación en siete clases y paquete `entrega.json`.
- `scripts/herramientas/sqx_native_improvement.py` (motor existente, conservado): `prepare` admite `custom_variants` (reglas revisadas) sin tocar las recetas anteriores; el recuento de bancos cae a exportación + conteo de filas cuando SQX omite la línea `Records:` (ver incidencia); la protección contra proyectos duplicados también mira el directorio del proyecto.
- Se conserva el motor anterior en la VPS como `sqx_native_improvement.py.before-cycle-20260906T130723Z`.

Decisión de arquitectura: SQX sigue siendo el único evaluador (recalcula 3 estrategias en 24 s ocioso, 66 s con el generador activo); lo propio es determinista (contrato, diagnóstico, mutaciones, estadística) y no hay IA en ninguna decisión del ciclo.

## 3. Estrategia, destinos e hipótesis probadas

Referencia (recálculo fresco, un contrato, comisión 5, deslizamiento 2, capital 50 000):

| Muestra | Operaciones | Neto | Factor de beneficio | Retorno/caída | Cierres por hora (15:00 Chicago) | Cierres por objetivo | Cierres por stop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| IS 2022–2024 | 173 | 40 503 | 1,57 | 2,19 | 102 | 13 | 58 |
| OOS 2025 (desarrollo) | 56 | 7 706 | 1,32 | 1,19 | 30 | 5 | 21 |

Hallazgos consistentes en ambas muestras (con el diagnóstico corregido tras la revisión): la mayoría de las salidas las decide el reloj; el objetivo (2,0–2,4 ATR) casi nunca se alcanza (7,5 % / 8,9 % de las operaciones); opera solo el 19 % de los días (1,1 operaciones por semana, entradas entre las 08 y las 15 h de Chicago); con un contrato, menos del 8 % de las ventanas de cinco días alcanza el objetivo provisional del 6 %. La "devolución alta del recorrido favorable" que el diagnóstico inicial señalaba era en parte un artefacto (mezclaba perdedoras): medida solo sobre ganadoras es del 25 % (IS) y 43 % (OOS) del beneficio medio, por debajo del umbral del 50 %.

Hipótesis registradas antes de recalcular (`criteria.json` fija cuándo una variante cuenta como progreso útil: en Fondeo, ≥ +5 puntos en la tasa de objetivo limpio a cinco días en IS y OOS sin subir la ruptura más de un punto; en Ultra, exploratorio, convexidad no peor y cola derecha o MFE ≥ 2R al alza; en ambos casos con evidencia OOS emparejada por encima del ruido):

- `VPT_NEAR` (H_PT_NEAR): objetivo × 0,6 (2,0→1,2 ATR largo; 2,4→1,44 ATR corto). Problema: objetivo lejano. Sigue justificada con el diagnóstico corregido.
- `VTS_TIGHT` (H_TS_TIGHT): activación del trailing × 0,5 y distancia × 0,5 en ambas direcciones. Problema declarado: devolución desde el máximo favorable. **Con el diagnóstico corregido esta hipótesis ya no está respaldada en ambas muestras** (el motor actual la deja en `NOT_SUPPORTED_IN_BOTH_SAMPLES`); el experimento se conserva como ejecutado y su resultado es válido, pero su justificación original era defectuosa.

## 4. Resultados, incluidos los rechazos

| Variante | IS neto / FB / R:DD | OOS neto / FB / R:DD | Días con cambio (IS/OOS) | Suma de deltas OOS, IC 90 % | Objetivo 5 d IS/OOS (base 7,5 % / 3,1 %) | Ruptura 5 d IS/OOS (base 8,6 % / 4,3 %) | Clase |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VPT_NEAR | 38 360 / 1,50 / 2,15 (peor) | 9 583 / 1,35 / 1,48 (mejor) | 35 / 11 | +1 877 [−4 965, +9 697] | 6,0 % / 1,9 % | 8,6 % / 4,3 % | **INCONCLUSIVE** |
| VTS_TIGHT | 36 139 / 1,50 / 1,73 (peor) | 12 228 / 1,56 / 1,89 (mejor) | 21 / 8 | +4 522 [−1 225, +11 382] | 6,6 % / 3,5 % | 8,7 % / 3,5 % | **INCONCLUSIVE** |

Lectura: los mecanismos previstos sí se activaron (VPT_NEAR triplica los cierres por objetivo, 13→40 en IS y 5→12 en OOS, y baja la devolución de las ganadoras; VTS_TIGHT convierte parte de los cierres por hora en cierres por stop, 58→76 y 21→27), pero ninguna variante mejora las dos muestras, ninguna alcanza relevancia para Fondeo y VPT_NEAR destruye la convexidad que Ultra necesita (beneficio procedente de operaciones ≥ 3R, medido con el riesgo del control: 35 % → 16 % en IS y 31 % → 0 % en OOS). La mejora OOS de ambas descansa en 8–11 días y su intervalo incluye el cero. No se ajusta nada sobre el OOS.

### 4 bis. Correcciones aplicadas tras la revisión adversarial (antes de cerrar)

- Marcas de tiempo: SQX escribe las horas de bolsa como si fueran UTC cuando el recurso declara zona "Exchange" (todos los cierres por hora caen a las 15:00 exactas durante cuatro años). El diagnóstico las convertía otra vez y desplazaba el perfil horario 5–6 horas; corregido (`timestamp_interpretation`). Para esta estrategia de sesión regular el día de negociación, el emparejamiento diario y las ventanas de examen no cambian.
- Múltiplos R de una variante: ahora se miden con el riesgo inicial del control por entrada, de modo que ceñir el stop no infla la convexidad aparente.
- Devolución desde el MFE: se mide sobre ganadoras; las perdedoras que llegaron a +1R se cuentan aparte (`LOSERS_AFTER_FAVOURABLE_EXCURSION`).
- Cribado de examen: el objetivo solo cuenta si es limpio; una ventana con objetivo pero posible ruptura intradía cuenta como ruptura; el límite diario también mira la peor excursión estimada; el suelo arrastrado declara que se detiene en el saldo inicial.
- Clasificación: `DEV_FAVORABLE_RELEVANT` exige además evidencia OOS emparejada moderada o fuerte (IC 80 %/90 % por encima de cero y al menos 5/10 días con cambio); si no, `INCONCLUSIVE` con la razón.
- Calendarios IS/OOS: la muestra IS es todo el periodo fuera de la unión de los rangos OOS; una orden fuera del calendario de su muestra detiene el diagnóstico en vez de perderse.
- `prepare-local` es repetible sin reescribir criterios ni experimento; la evaluación rechaza criterios alterados después de preparar (hash en el manifiesto).
- Periodos de la entrega derivados del contrato; nombres de diagnóstico por etiqueta de variante; parámetro `atr_period` admitido; comprobación de nodo XML sin valor booleano implícito.

Ningún veredicto cambió con las correcciones; sí cambiaron la justificación de `VTS_TIGHT` (ver sección 3) y las tasas de objetivo/ruptura de esa variante en OOS (3,5 % / 3,5 % en lugar de las cifras previas a la corrección, porque cuatro de sus ventanas alcanzan el objetivo con posible ruptura intradía).

Casos de control del propio motor:

- Variante que solo cambia metadatos: rechazada antes de recalcular (0 recálculos gastados).
- Experimento previo de stops ±10 % (12:02 CEST) reclasificado con los mismos criterios: `EXIT90` → `HISTORICAL_FIT_ONLY` (mejora IS, empeora OOS), `EXIT110` → `INCONCLUSIVE` (IS peor, OOS mejor). Está en `ciclo_ew_prev_sl_20260906/`.
- Estudio de exposición (sin recálculo, P&L lineal en contratos): con 2, 3 y 4 contratos la tasa de objetivo a cinco días sube a 15–20 %, pero la de ruptura sube a 18–34 %. Es exposición, no mejora de la estrategia; se entrega junto, como pide el encargo.

Coste medido: recálculo nativo de 3 estrategias en 1 min 6 s con el generador ocupando los 8 núcleos (24 s a las 12:02 con SQX ocioso); ciclo completo (importación, recálculo, exportación de órdenes, evaluación) en 92 s de pared más unos segundos de evaluación. Cero mejoras aceptadas: el coste por mejora aceptada no es calculable todavía.

Niveles del encargo: mecanismo funciona = sí; progreso útil = no; candidata a validación = ninguna; resultado validado = ninguno.

## 5. Dónde está la evidencia

- VPS: `/opt/SQX-headless/import/ciclo_ew_20260906_01/` (ciclo completo, incluidos `experiment/retested/*.sqx`, órdenes, `reconciliation_1/`) y `/opt/SQX-headless/import/ciclo_ew_prev_sl_20260906/`; registro en `/opt/SQX-headless/import/improvement_registry/`.
- Repositorio: esta carpeta. `ciclo_ew_20260906_01.zip` (47 entradas, SHA-256 `966df3ca4fdc4a56db80a99ac80ab7913b77a6c1cb885145dc8b24c6d2275b22`), `entrega_ciclo_01.json`, `evaluacion_ciclo_01.json`, `criterios_ciclo_01.json`, `plan_ciclo_01.json`, `ciclo_ew_prev_sl_20260906/`, `improvement_registry/`, `MANIFIESTO.json` con los hashes. Los archivos nativos del experimento previo ya estaban en `../SQX_NATIVE_IMPROVEMENT_20260905/ew_improvement_final_20260906.zip`. El `diagnosis_base.json` de la preparación conserva el perfil horario anterior a la corrección; el corregido es `diagnosis_base_fresh.json`.
- Módulos desplegados en `/opt/SQX-headless/import/` (SHA-256 iguales a los del repositorio): motor `55aa3d18…`, contrato `e28fc02d…`, diagnóstico `766fdac8…`, mutaciones `24987647…`, ciclo `6c116564…` (con la entrada de hipótesis de agentes).
- Requisitos documentados de Ultra recuperados: `ULTRA_REQUISITOS_20260906.md`.
- Guía de uso del ciclo: `docs/Laboratorio/07_MOTOR_MEJORA_CICLO.md`.

## 6. Incidencia encontrada en la VPS (no causada por este trabajo)

Desde las 12:02:26 CEST del 6 de septiembre la CLI de SQX responde a `-databank action=count` y a `-project action=list` sin líneas de datos (ni `Records:` ni nombres), y `-project action=status` lanza `Not implemented`. Por eso `m1-runner.service` entró en bucle de fallo (35 reinicios entre las 14:2x y 14:43, `sqx_bank_retention.py: Native bank count is unknown`) hasta que a las 14:48 retomó `FONDEO_MGC_M1` por su cuenta. El primer intento de este ciclo (15:10) falló en ese mismo recuento; se reconcilió con evidencia (`reconciliation_1/`), se eliminó el proyecto a medio cargar y se repitió con el recuento por exportación. No se reinició SQX ni el generador. El mismo fallback serviría para la retención del runner; no se ha tocado porque está fuera de esta fase.

## 7. Qué sigue sin demostrarse

- No existe muestra final reservada: los datos de @EW en SQX terminan el 2025-12-31 y el OOS 2025 ya se ha consultado. Sin datos de 2026 no hay validación independiente posible para ninguna variante.
- La procedencia de @EW (suscripción de datos de SQX, "continuous contracts") no está verificada de forma independiente; la campaña continua sigue sobre alias CFD, excluidos.
- El cribado de examen usa dos escenarios provisionales y una estimación conservadora del peor punto intradía (MAE por operación); no es la regla fechada de ninguna empresa.
- Ultra: no hay criterio de mejora sellado; lo medido (E[R], payoff, cola ≥ 3R, MFE ≥ 2R, asimetría) es exploratorio, y la línea figura como aparcada desde el 2026-09-01 en `orchestration/README.md`.
- El ciclo se ejecuta bajo demanda; el temporizador horario sigue con las recetas MYM/MNQ anteriores y no invoca este ciclo.
- Hipótesis de horario, día de la semana o lado de entrada (las que atacan la baja frecuencia) no están implementadas: exigen añadir bloques de condición al XML o cambiar la muestra de operaciones.

## 8. Dirección corregida por Emilio al cierre (2026-09-06, 15:35 CEST)

"No quiero un sistema hardcodeado con ATR, stop +2, trailing −1; quiero que un debate de agentes trate cada estrategia y la analice, un sistema de ellos y programas de depuración especializados; el software solo no podrá pensar."

Consecuencia: la biblioteca fija de hipótesis (`HYPOTHESIS_LIBRARY`) queda como andamio para probar el mecanismo, no como diseño. El reparto pasa a ser:

- **Agentes (piensan):** reciben el contrato, el diagnóstico de órdenes, las reglas y el registro de lo ya probado; debaten por estrategia (proponente, crítico, árbitro) y devuelven pocas hipótesis con su cambio concreto, su justificación y el resultado que las aceptaría o rechazaría.
- **Programas especializados (ejecutan y miden):** contrato de entrada, diagnóstico, mutación verificada, recálculo nativo en SQX, comparación emparejada, clasificación y registro. No deciden qué probar.

El ciclo ya admite esa entrada: `prepare-local --hypotheses <json>` toma las hipótesis de los agentes (`{id, title, problem, change, expected, changes:[…]}`), las valida (el cambio nulo se rechaza, el cambio real se construye y se verifica) y marca el plan como `AGENT_DEBATE`. Probado localmente con dos hipótesis de ejemplo (una válida, una nula) sin recalcular.

## 8 bis. Fase 2 ejecutada el mismo día: debate de agentes real y ciclo 02 (16:15–16:35 CEST)

Emilio pidió investigar si el debate semántico tiene sentido y, en ese caso, implementarlo. La
investigación está en `INVESTIGACION_DEBATE_SEMANTICO.md` (respuesta: sí para proponer y criticar,
no para medir ni aceptar; el "debate" que ya existía en la API era un guion pregrabado sin modelo).
Implementado en `scripts/herramientas/sqx_hypothesis_debate.py` e integrado en el ciclo.

**Debate real sobre la misma estrategia** (dos rondas con Claude Opus 5 vía Claude Code desde el
PC; la primera se conserva porque destapó un defecto del validador, corregido antes de la segunda):

| Ronda | Propuestas | Aplicables | Refutadas por el crítico | Seleccionadas | Coste | Tiempo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 (validador v1) | 5 | 2 | 3 | 1 | 2,07 USD | 342 s |
| 2 (validador corregido, registro con cambios) | 5 | 4 | 2 | 2 | 1,89 USD | 316 s |

Las hipótesis nacieron del dosier, no de una biblioteca: el crítico refutó la repetición de ejes ya
explorados (trailing, objetivo) y el árbitro seleccionó `BarsValid` largo 4→8 (único eje nuevo,
ataca la baja frecuencia) y, con desacuerdo registrado, un objetivo intermedio 1,6/2,0 ATR.
El árbitro dejó escrito que 5 puntos de tasa de objetivo sobre 52 ventanas disjuntas OOS son ruido
y que, si el objetivo intermedio repetía el perfil de `VPT_NEAR`, había que cerrar la familia de
objetivos. Carencias de capacidad señaladas por los agentes: filtros de hora y día, filtro por
dirección, salidas parciales, hora de cierre forzado, relajar entradas.

**Ciclo 02** (recálculo nativo de 3 estrategias en 28 s con SQX ocioso; ciclo completo en 52 s):

| Variante (hipótesis de agente) | IS neto / FB / R:DD | OOS neto / FB / R:DD | Órdenes que cambian | Clase |
| --- | --- | --- | --- | --- |
| `VLONG_BARSVALID_EST2` (validez orden larga 4→8) | 40 503 / 1,57 / 2,19 (idéntico) | 7 706 / 1,32 / 1,19 (idéntico) | 0 de 229 | **NO_EFFECT_IN_SAMPLE** |
| `VPT_MID_ASIM_EST1` (objetivo 1,6 / 2,0 ATR) | 40 480 / 1,55 / 2,13 (equivalente) | 6 059 / 1,25 / 0,93 (peor) | 29 distintas, 15 nuevas, 5 perdidas | **HISTORICAL_FIT_ONLY** |

Lectura: el cambio que los agentes consideraron más prometedor es real en las reglas pero inerte
en estos datos (ninguna orden larga sobrevive más de 4 barras sin ejecutarse o cancelarse), y el
motor lo detecta sin declarar nada; el objetivo intermedio confirma la advertencia del árbitro
(familia de objetivos cerrada para esta estrategia: dos multiplicadores probados, ambos sin
progreso útil). El registro por estrategia acumula ya seis variantes y tres experimentos; los
próximos debates las reciben con sus cambios y su resultado.

Niveles: mecanismo funciona = sí (incluido el debate); progreso útil = no; candidatas = ninguna;
validadas = ninguna.

**Endpoint de IA del sistema.** Al cierre Emilio fijó que las llamadas de IA vayan por el
omnirouter de su VPS de Oracle, con la elección de modelo por tarea en el panel de superadmin.
Comprobado: la API compatible con OpenAI responde en
`https://omniroute.143-47-35-167.sslip.io/pro/omniroute/api/v1` (el proxy `/v1` de nginx apunta a
una ruta inexistente y devuelve 404), sin clave, con 1 727 modelos y combos; `auto` enruta a
OpenRouter, que hoy responde "sin créditos"; `auto/best-reasoning` responde vía Antigravity
(Gemini 3 Flash). El proveedor `omniroute` del debate pide los alias de tarea
`ultrarentable-mejora-proponente|critico|arbitro` (para definirlos en el panel) y cae a
`auto/best-reasoning` dejando constancia mientras no existan. Ver §8 ter para el resultado de
la ejecución por ese endpoint.

## 8 ter. Debate por el endpoint del sistema (omnirouter) y ciclo 03

Tercer debate, esta vez por el omnirouter de Oracle (proveedor `omniroute`), con el registro de
seis variantes ya exploradas: cuatro llamadas en 69 s, ~47 000 tokens de entrada, coste cero para
este proyecto (enrutado por Antigravity a Gemini 3 Flash porque los alias de tarea aún no existen
en el panel; el fallback y la conexión TLS degradada quedan anotados en cada llamada de
`debate_ciclo_03_omniroute/log.json`). Seis propuestas, cuatro aplicables, cuatro refutadas, dos
seleccionadas con mecanismos nuevos para esta estrategia: salida por tiempo (`ExitAfterBars` 5
barras en ambas direcciones, contra la dominancia del cierre por reloj) y stop corto 115→90
(simetría con el largo, con la reserva del árbitro por solo 8 operaciones cortas OOS). Las dos
propuestas de "mover el stop a break-even" quedaron no aplicables: la fórmula `RangeLevel.None`
no está en el vocabulario de mutaciones (carencia registrada). Resultado del ciclo 03 (recálculo nativo en 27 s; ciclo completo en 50 s; `entrega_ciclo_03.json`,
`ciclo_ew_20260906_03.zip`):

| Variante (hipótesis por omnirouter) | IS neto / FB / R:DD | OOS neto / FB / R:DD | Órdenes que cambian | Días con cambio IS/OOS | Clase |
| --- | --- | --- | --- | --- | --- |
| `EXIT_AFTER_BARS` (salida a las 5 barras, ambas direcciones) | 37 975 / 1,53 / 1,99 (peor; IC 90 % de la suma de deltas [−5 055, −189]) | 10 079 / 1,43 / 1,59 (mejor; IC incluye el cero) | 39 distintas, 6 nuevas | 30 / 11 | **INCONCLUSIVE** |
| `REDUCE_SHORT_SL` (stop corto 115→90) | 39 965 / 1,56 / 2,21 (equivalente) | 8 316 / 1,36 / 1,28 (mejor) | 14 distintas, 2 nuevas | 11 / 3 | **INCONCLUSIVE** (solo 3 días OOS cambian) |

La salida por tiempo convierte 30 cierres por reloj en cierres a las 5 barras en IS y 11 en OOS,
y repite el patrón de todas las variantes de salida probadas hoy: peor en 2022–2024, mejor en
2025. Con cinco variantes de salida en la misma dirección (`VPT_NEAR`, `VTS_TIGHT`, `VPT_MID`,
`EXIT_AFTER_BARS`, `EXIT110`) el árbitro de la ronda 2 ya lo había dicho: la superficie de salidas
de esta estrategia está saturada de ajuste y no se debe seguir gastando en ella. El registro por
estrategia cierra el día con ocho variantes y cinco experimentos; el próximo debate los recibe con
sus cambios y resultados.

Coste de la fase 2 completa: tres debates (2,07 + 1,89 USD de Claude Code y coste cero por el
omnirouter) y dos ciclos en SQX (28 + 27 s de recálculo). Cero mejoras aceptadas: el coste por
mejora aceptada sigue sin ser calculable, y ésa es la respuesta honesta para esta estrategia.

## 10. Fase 3 el mismo día: módulos independientes y servicio autónomo en la VPS

Emilio pidió meter los agentes "en el sistema" y dejar todo como programas independientes
modificables por partes. Tiene sentido por dos razones: el encargo exige continuidad en la VPS sin
conversación abierta, y la fase 2 demostró que las piezas cambian a ritmos distintos (criterios y
vocabulario mucho más que el recálculo). Hecho:

- **Nueve programas con contrato de ficheros** (tabla en `docs/Laboratorio/07_MOTOR_MEJORA_CICLO.md`):
  contrato, diagnóstico, mutaciones, debate, recálculo (motor existente), **evaluación separada en
  `sqx_variant_evaluation.py`** (la política de aceptación vive sola), orquestación de un experimento
  y entrega, **servicio autónomo `sqx_improvement_service.py`**, y un andamio de hipótesis fijas que
  solo usan las pruebas. Las pruebas existentes siguen verdes tras la separación.
- **Servicio autónomo** (`sqx-mejora-agentes.timer`, cada hora): cola persistente `queue.json` por
  hash semántico de reglas; `inbox/` como entrada (un `.sqx` y su procedencia); presupuesto por
  estrategia (3 experimentos, 2 debates vacíos, 2 fallos técnicos); estados `QUEUED` →
  `IN_PROGRESS` → `CANDIDATE_FOR_VALIDATION` (entrega a `outbox/`) | `EXHAUSTED` |
  `NEEDS_ATTENTION` (fallo repetido con diagnóstico, sin reintentos infinitos) | `REJECTED_INPUT`;
  comprobaciones previas de reclamación activa, memoria y disco; cerrojo contra ejecuciones
  solapadas; `status.json` con la última ejecución para que la web o la API lo lean. Seis pruebas
  de cola, presupuesto y reconciliación (`test_improvement_service.py`).

**Primera ejecución autónoma en la VPS (17:28–17:30 CEST, sin intervención):** el servicio tomó
`Strategy 1.1.27.sqx` del `inbox/`, lo contrató, exportó sus órdenes heredadas con el lector Java
de SQX, lo diagnosticó, convocó el debate por el omnirouter (seis propuestas en 83 s) y el crítico
refutó las seis: todas reescalaban ejes ya probados (el registro ya tenía ocho variantes de esta
estrategia). Resultado `NO_HYPOTHESES`, cero recálculos gastados, estrategia `IN_PROGRESS` con un
debate vacío contado; al segundo pasará a `EXHAUSTED` y el servicio quedará `IDLE` hasta que entre
otra estrategia. La única carencia señalada por los agentes vuelve a ser el filtro de hora y día de
la semana. Evidencia: `servicio_mejora_20260906/` (cola, estado, debate). El temporizador
`sqx-mejora-agentes.timer` queda activado (cada hora; siguiente ejecución dentro de una hora).

**Segunda ejecución, disparada por el propio temporizador (17:30–17:32 CEST):** esta vez el
árbitro seleccionó dos propuestas de ejes nuevos (activación del trailing largo 1,4→1,0 ATR y
periodo de la banda de Bollinger de la señal corta 188→100), el servicio preparó, recalculó en SQX
(3 s de tarea nativa con los datos ya cargados; 26 s de ciclo), evaluó, registró y empaquetó sin
intervención:

| Variante (agentes, por omnirouter) | IS neto / FB / R:DD | OOS neto / FB / R:DD | Órdenes que cambian | Clase registrada |
| --- | --- | --- | --- | --- |
| `TA_LONG_TIGHT` (activación 1,4→1,0 ATR) | 40 624 / 1,57 / 2,20 (equivalente) | 6 807 / 1,29 / 1,05 (peor) | 4 distintas, 2 nuevas; 1 día OOS | **INCONCLUSIVE** (muestra insuficiente) |
| `SHORT_BB_PERIOD_REDUCE` (periodo 188→100) | 30 067 / 1,39 / 1,46 (peor; IC 90 % de la suma de deltas [−19 965, −1 758]) | 5 427 / 1,23 / 0,74 (peor) | 12 entradas perdidas, 17 nuevas | **INCONCLUSIVE** (2 días OOS) |

La segunda clase es demasiado benévola: una variante que destruye la construcción con evidencia
(IC 90 % íntegramente más allá de la tolerancia registrada) no debe quedar "inconclusa" porque el
OOS cambie poco. Corregido en `sqx_variant_evaluation.py` (esa condición → `REJECTED_WORSE`,
antes de la regla de días mínimos; un empeoramiento IS pequeño cuyo intervalo roza el cero, como el
stop +10 % de la mañana, sigue inconcluso) con pruebas; la clase registrada en la VPS se conserva
tal cual se emitió y el registro de la estrategia ya impide repetir esa variante.

Lo que esto demuestra y lo que no: el sistema funciona de extremo a extremo sin el PC y sin una IA
conversando (dos ejecuciones, una manual y una por temporizador, sin errores ni reconciliaciones);
sabe parar cuando una estrategia se estanca; no ha producido todavía ninguna mejora útil, y con el
vocabulario actual esta estrategia no dará más de sí. Ocho experimentos en total sobre `Strategy
1.1.27`, doce variantes registradas, cero candidatas.

## 11. Fase 4 el mismo día: filtros de hora, día y dirección (19:30–20:30 CEST)

Encargo de Emilio: "dedícate solo a que el motor nuevo funcione; para pruebas usa tu IA, luego el
sistema usará otra de omniroute". La carencia que los agentes registraron en las tres rondas
anteriores (y otra vez en el ciclo 03 del servicio, 18:31 CEST: "filtros de horario para la hora 10",
"filtros por día para los lunes", citando cifras OOS) era el vocabulario: no había forma de expresar
un filtro de hora o de día.

### Qué se construyó y cómo se verificó

- **Dónde viven los filtros.** No en las opciones de trading de `lastSettings.xml`
  (`LimitTimeRange`, `ExitAtEndOfDay`…): el motor copia esas opciones al proyecto `Retest` con
  `customSettings="true"` y son comunes a control y variantes. Los filtros van como condiciones `AND`
  en el `If` de la regla de entrada de cada dirección, con los bloques nativos de SQX
  `BarHourIsBigger`, `BarHourIsSmaller`, `BarDayOfWeekIsNot` (`SQ.Blocks.BarAndTime`) y `Boolean`
  (`SQ.Blocks.Other`), copiando la forma XML de la plantilla propia de SQX
  `highest_breakout_template_daily_filter.sqx` (única estrategia de las 2 342 de la VPS que los usa).
- **Verificación estructural nueva** (`build_variant`): cada filtro declara el alcance
  `…/Rule#N/If`; todo cambio detectado ahí debe ser una adición y nada existente puede cambiar;
  fuera de los filtros, el número de parámetros que cambian sigue siendo exactamente el previsto.
  Un filtro de hora presente no se apila: `#Hour#` entra en el catálogo y se reajusta por `param_path`.
- **Semántica medida en SQX** con dos recálculos de mecanismo, sin registro de la estrategia
  (`UR_IMPROVE_MECANISMO_FILTROS_01`, 19:33 CEST, y `_02`, 19:40 CEST; 20 s cada uno, tarea nativa
  de 0,5 s con los datos cargados):

| Variante de mecanismo | Operaciones IS / OOS (control 173 / 56) | Qué se observó |
| --- | --- | --- |
| `hour_range` 8–13, ambas direcciones | 121 / 42 | Rellenos entre las 10 y las 14 h; desaparecen los de las 08 y 09 h. |
| `hour_range` 10–11 (solo la barra de las 10) | 47 / 20 | 45 de 47 rellenos IS a las 11 h y 2 a las 12 h: **el filtro lee la barra que acaba de cerrar y el primer relleno cae en la hora siguiente**. Para permitir primeros rellenos entre las A y las B: `from=A-1, to=B-1`. |
| `exclude_weekdays` lunes y viernes | 113 / 34 | Cero rellenos en lunes; en viernes quedan 16 de 60, todos en la apertura de las 08:30, de órdenes de la víspera aún válidas (`BarsValid` 4/8). El filtro acota la señal, no la orden pendiente. |
| `disable_direction` cortos | 140 / 48 | Sin cortos; las largas idénticas al control (188 órdenes compartidas, ninguna con distinto resultado). |

Las cuatro dieron `REJECTED_WORSE` o `INCONCLUSIVE`, como corresponde a filtros elegidos sin
hipótesis; su evidencia está en `mecanismo_filtros_20260906.zip` (manifiesto con SHA-256 al lado).

- **Dosier del debate contra la minería de datos:** las tablas por hora, día y dirección se muestran
  solo de la muestra de construcción; en OOS quedan los agregados y el código del hallazgo de
  concentración sin el segmento concreto. El crítico recibe la instrucción explícita de refutar
  filtros justificados solo por una celda perdedora. Los proponentes deben dar una razón estructural
  (apertura, cierre, liquidez) y declarar cuántas celdas miraron.
- **Módulos afectados:** `sqx_variant_mutations.py` (vocabulario y verificación), `sqx_strategy_contract.py`
  (filtros visibles en el contrato), `sqx_hypothesis_debate.py` (esquema, dosier, prompts),
  `sqx_improvement_cycle.py` (claves de cambio, registro, duración en ms). Nueve módulos con hashes
  iguales en el PC y en la VPS; 187 pruebas correctas (11 nuevas en `test_variant_filters.py`).
- **Cambio ajeno conservado:** `sqx_trade_diagnosis.py` apareció modificado en el árbol de trabajo a
  las 18:07 CEST (después del commit de la fase 3) y ya desplegado en la VPS: el calendario de cada
  muestra termina en la sesión que abre la tarde del último día, y `daily_results` tolera órdenes a
  ±3 días de los extremos. Coherente con `trading_day()`; dos pruebas mías se adaptan (258 días de
  negociación en el OOS 2025, y el 1-1-2024 pertenece al OOS que termina el domingo 31-12-2023).

### Revisión adversarial del vocabulario (subagente, 19:47–19:59 CEST) y correcciones

Nueve hallazgos, todos verificados con código sobre las reglas reales; corregidos con prueba los
siete que eran defectos: (1) un `If` sin AND raíz se envuelve en un AND nuevo y la variante se
rechazaba por "alterar condiciones"; ahora el traslado se verifica por forma canónica y se atribuye
al filtro; (2) la atribución por prefijo de regla se tragaba cambios `param_path` legítimos dentro
del mismo `If` (reajustar un `#Hour#` existente junto a un filtro de día); ahora solo cuentan como
filtro las adiciones bajo el bloque exacto añadido; (3) un bloque de hora dentro de un `Not` se
listaba como filtro activo; ahora solo se recorre la conjunción; (4) combinaciones sin sentido que
gastarían un recálculo (las dos direcciones desactivadas, cambios sobre una dirección desactivada);
(5) cambios con claves mezcladas (filtro + salida) que se aplicaban a medias; (6) un `Boolean true`
contaba como dirección desactivada; (7) fuga OOS por dirección en el dosier (`long_trades`/
`short_trades` del resumen y la `dimension` de los hallazgos ocultos); ahora los hallazgos de segmento
OOS se colapsan en uno sin dimensión y el resumen OOS no lleva recuentos por dirección. El octavo
(el filtro de día "no se había recalculado") era anterior al segundo recálculo de mecanismo; el
noveno, código muerto, se sustituyó por la regla "máximo dos días laborables excluidos".

### Ciclo 04: debate con la IA de Claude sobre el vocabulario nuevo (19:44–19:53 CEST)

Por indicación de Emilio las pruebas usan mi IA (`claude-cli`, Claude Opus 5; 2,32 $, 6,3 min); el
servicio de la VPS sigue con omniroute. Dosier con las once variantes ya registradas y el vocabulario
de filtros. Resultado del debate: cinco propuestas, tres aplicables, dos refutadas automáticamente
(`move_sl_to_be` está en `SQ.Formulas.RangeLevel.None` y el motor no sabe activarla: hueco de
vocabulario, registrado), dos seleccionadas con desacuerdo anotado. **Ninguna de las cinco usó
filtros**: con las tablas OOS por segmento ocultas y la exigencia de razón estructural, los agentes
prefirieron otras palancas. Recálculo en la VPS (`UR_IMPROVE_CICLO_EW_20260906_04`, 20 s de ciclo,
0,5 s de tarea nativa), evaluación con el registro de la estrategia:

| Variante (agentes, Claude) | IS neto / FB / R:DD | OOS neto / FB / R:DD | Órdenes que cambian | Clase registrada |
| --- | --- | --- | --- | --- |
| `P3_SENAL_MENOS_RETRASO` (Shift de "banda inferior cayendo" 4→2) | 21 670 / 1,27 / 1,02 (peor) | 5 172 / 1,20 / 0,64 (peor) | 112 entradas perdidas, 105 nuevas; 27 días OOS | **REJECTED_WORSE** |
| `PROP_SAL_02_TS_LONG_55` (arrastre largo 90→55) | 39 974 / 1,56 / 2,17 (equivalente) | idéntico al control | 3 órdenes IS; 0 días OOS | **INCONCLUSIVE** (sin efecto en desarrollo) |

Registro de la estrategia tras el ciclo: 13 variantes, 9 experimentos, cero candidatas. Evidencia:
`ciclo_ew_20260906_04.zip`, `debate_ciclo_04_claude/`, `entrega_ciclo_04.json`, `evaluacion_ciclo_04.json`,
`improvement_registry/` (instantánea del registro de la VPS).

### Qué sigue sin demostrarse y siguiente paso más pequeño

- El motor **funciona** de extremo a extremo con el vocabulario ampliado (cuatro recálculos de mecanismo
  y un ciclo con agentes hoy, sin errores ni reconciliaciones), pero **no ha producido progreso útil**:
  la estrategia `1.1.27` sigue sin candidatas tras nueve experimentos. Es un resultado, no un fallo del
  motor; la palanca que falta es otra estrategia de entrada o un vocabulario que cambie la estructura.
- Los agentes todavía no han propuesto un filtro real con el vocabulario nuevo: hace falta al menos una
  ronda en la que lo hagan para saber si el filtro de horas sobrevive a la evaluación (el servicio de la
  VPS lo intentará cada hora con omniroute).
- Huecos de vocabulario registrados por los agentes en esta ronda, por orden de valor: activar
  `move_sl_to_be` cuando está en `None` (cambio de fórmula, no solo de valor; cinco de las siete
  propuestas de break-even de hoy murieron ahí), desplazamiento del break-even para cubrir costes,
  salidas parciales (no expresable en el `Retest` compartido), salida por tiempo condicionada.
- Siguiente paso más pequeño: `move_sl_to_be` activable (`RangeLevel.None` → `FixedValue`/`ATRBasedValue`
  con verificación de que solo cambia esa salida), porque es la hipótesis que los agentes más repiten y
  hoy no se puede recalcular.

## 9 (antes). Siguiente paso más pequeño y útil

La fase 2 (debate de agentes integrado, con hipótesis que se recalculan de verdad) quedó ejecutada
el mismo día (§8 bis). Lo siguiente, en orden de valor:

1. **Emilio, en el panel de superadmin del omnirouter:** definir los combos
   `ultrarentable-mejora-proponente`, `ultrarentable-mejora-critico` y `ultrarentable-mejora-arbitro`
   con la IA que quiera para cada tarea (hoy caen a `auto/best-reasoning`); y reponer créditos o
   cambiar el destino del combo `auto`, que hoy falla por falta de créditos en OpenRouter.
2. **Vocabulario de cambios que los agentes ya han pedido** (carencias registradas en ambas rondas):
   filtros de hora y de día de la semana, filtro por dirección y salidas parciales, con la política
   de comparación para variantes que cambian la muestra de operaciones. Es la palanca que ataca la
   causa medida de la baja tasa de examen sin repetir multiplicadores.
3. **Servicio persistente en la VPS:** encadenar `dossier` → debate por omnirouter → `prepare-local`
   → `run` → `evaluate` como unidad `systemd` con presupuesto por estrategia (máximo de experimentos,
   parada cuando el registro muestra estancamiento) y las mismas reconciliaciones que ya existen.
4. **Muestra final reservada:** confirmar si la suscripción de datos de SQX permite traer @EW de 2026
   (enero–agosto). Sin ella el motor solo produce candidatas, nunca resultados validados.
