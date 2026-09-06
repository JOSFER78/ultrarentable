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
| Pruebas | 164 pruebas de `tests/sqx_runtime` correctas en 86 s (14 nuevas en `test_improvement_cycle.py`, sobre la evidencia real) |
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

## 9. Siguiente paso más pequeño y útil

Fase 2: el debate de agentes como servicio en la VPS (sin conversación abierta con la IA, según la directriz de que la autonomía vive en el backend):

1. `sqx_hypothesis_debate.py`: tres roles con llamadas a la API del modelo, salida JSON estricta en el formato que el ciclo ya acepta, presupuesto por estrategia (máximo de hipótesis y de rondas), registro de cada propuesta y de cada rechazo del crítico.
2. Mutaciones más generales para lo que los agentes propongan (parámetros de indicador, filtros de horario y día, validez de la orden, tamaño), siempre con verificación de que el cambio es exactamente el declarado; y la política de comparación para variantes que cambian la muestra de operaciones.
3. Verificación de la fase: mismo caso EW, un ciclo completo con hipótesis nacidas del debate, mismo paquete `entrega.json`, misma clasificación; los agentes reciben el resultado y proponen la ronda siguiente sin repetir lo registrado.

Requisitos que debe decidir Emilio antes de la fase 2: qué proveedor y clave de API del modelo usa la VPS para el debate, y si la suscripción de datos de SQX permite traer @EW de 2026 (enero–agosto) para reservarlo como prueba final. Sin esa muestra el motor solo puede producir candidatas, nunca resultados validados.
