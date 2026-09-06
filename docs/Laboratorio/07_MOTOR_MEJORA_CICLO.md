# Motor propio de mejora: ciclo por estrategia (guía comprobada)

Estado: primera entrega comprobada el 2026-09-06 con `Strategy 1.1.27` (@EW H1). Resultado,
límites y evidencia en `orchestration/results/codex/MOTOR_MEJORA_20260906/RESULTADO.md`. Esta guía
describe el recorrido que ya se ejecutó de verdad; no acredita rentabilidad ni aprobación de exámenes.

## Módulos independientes (todos en `scripts/herramientas/`, biblioteca estándar, desplegados en `/opt/SQX-headless/import/`)

Cada programa tiene una responsabilidad y un contrato de ficheros; se puede modificar y probar por separado sin tocar los demás. El orden de la tabla es el orden del flujo.

| Módulo | Responsabilidad | Entrada → salida | Cambiarlo cuando… |
| --- | --- | --- | --- |
| `sqx_strategy_contract.py` | Contrato de entrada; hash semántico; comparación de reglas | `.sqx` → `contract.json`; dos `.sqx` → `IDENTICAL_BYTES` / `METADATA_ONLY_NO_BEHAVIOUR_CHANGE` / `RULES_CHANGED` | cambie el formato de SQX o qué se considera metadato |
| `sqx_trade_diagnosis.py` | Diagnóstico determinista de órdenes; cribado provisional de examen; estudio de exposición | CSV de órdenes + contrato → perfil IS/OOS, hallazgos, ventanas 1–5 días | se añadan análisis o escenarios de examen |
| `sqx_variant_mutations.py` | Vocabulario de cambios (salidas, parámetros por ruta, filtros de hora/día/dirección como bloques nativos de SQX) y verificación de que la variante cambia exactamente lo declarado | reglas XML + cambios → reglas nuevas + registro; catálogo `mutable_parameters` | los agentes pidan una palanca nueva (salidas parciales, indicadores…) |
| `sqx_hypothesis_debate.py` | Debate de agentes: dosier, proponentes ciegos, validación, crítico, árbitro; proveedores (`omniroute` del sistema, `anthropic`, `claude-cli`, `replay`) | ciclo con contrato/diagnóstico/criterios/explorados → `debate/hypotheses.json` + registro | cambien los roles, los prompts o el endpoint de IA |
| `sqx_native_improvement.py` | Recálculo nativo en SQX (motor existente): proyecto Retest dedicado, evidencia, órdenes | experimento preparado → `retest.csv`, `retested/*.sqx`, órdenes, `assessment.json` | cambie SQX o su CLI |
| `sqx_variant_evaluation.py` | Política de evaluación: comparación emparejada por día, relevancia por destino, clases; criterios registrados antes | experimento recalculado + contrato + `criteria.json` → `evaluation.json` | cambien los criterios de aceptación o los destinos |
| `sqx_improvement_cycle.py` | Orquestación de UN experimento y entrega: `dossier`, `prepare-local`, `run`, `evaluate`; paquete `entrega.json`; registro por estrategia | ficheros del ciclo → `entrega.json`, `improvement_registry/<reglas>.json` | cambie el formato de entrega o el registro |
| `sqx_improvement_service.py` | Servicio autónomo (v2): admisión desde las fuentes de estrategias extraídas, cola persistente, reparto de cada ejecución entre varias estrategias, presupuesto por falta de progreso, linaje desde variantes aceptadas con evidencia creciente, reintentos limitados | fuentes (`fondeo/entrega_fase5/strategies`, `fondeo/preseleccion/*/selected`) → `mejora/inbox/*.sqx` + `.json` → `mejora/strategies/<slug>/ciclo_NN/`, `queue.json`, `status.json`, `outbox/` | cambie qué fuentes se admiten, la política de presupuesto, de prioridad o de linaje |
| `sqx_fixed_hypotheses_scaffold.py` | Andamio de hipótesis fijas SOLO para pruebas del mecanismo | — | nunca en producción (Emilio: los agentes piensan) |

## Servicio autónomo en la VPS (v2, 2026-09-06: todas las extraídas, todo lo posible)

Objetivo fijado por Emilio: *"con las estrategias que tenemos extraídas de SQX, mejorarlas todo lo posible"*. Las
estrategias extraídas son las que el generador de fondeo (`m1_runner_sqx.py`) selecciona en cada ronda
(`/opt/SQX-headless/import/fondeo/preseleccion/<celda>_r<N>_<fecha>/selected/*.sqx`; 125 únicas el 2026-09-06 en
23 celdas de M6E, MCL, MES, MGC, MNQ y MYM; periodo 2023-01 → 2026-08-30 con OOS desde 2025-12-06) y las que la
fase 5 de triaje entrega al motor (`fondeo/entrega_fase5/strategies/*.sqx`, prioridad más alta). Los bancos
brutos de 20 000 estrategias, `export1` y el `ToImprove` de `Ultra_Matrix` (2 034 estrategias AUDUSD H1 con OOS
de tres días, no evaluable) no entran. Excepto M6E, los datos de esas celdas son alias CFD de futuros
(`known_proxy_alias` en el contrato): el cribado provisional de examen no es elegible y la relevancia la aporta
el criterio Ultra (expectativa R, cola); queda anotado en cada entrada (`data_is_known_cfd_proxy`).

`sqx-mejora-agentes.timer` ejecuta cada 15 minutos `sqx_improvement_service.py --once --max-experiments-per-run 6
--time-budget-minutes 12`. Cada ejecución: (1) **admisión**: copia al inbox los `.sqx` nuevos de las fuentes con su
procedencia (`origin`, celda, ronda, métricas de la selección); un archivo ya visto (mismo SHA-256) no vuelve a
entrar y los orígenes no se tocan; (2) **reparto**: la estrategia activa de mayor prioridad y menos atendida
primero, así todas avanzan en paralelo; un experimento por estrategia y ejecución, hasta agotar el tiempo; (3)
**presupuesto por falta de progreso**: `max_experiments_without_progress` (3 seguidos sin ninguna clase
`DEV_FAVORABLE_*`), `max_experiments` (6, tope duro), `max_empty_debates` (2), `max_failed_attempts` (2); (4)
**linaje**: una variante `DEV_FAVORABLE_RELEVANT` se entrega a `outbox/` y además pasa a ser una estrategia hija
(su `.sqx` recalculado como fuente, sus órdenes frescas como base, prioridad más alta, las variantes probadas por
sus antecesoras en el dosier); la madre queda `IMPROVED_CONTINUED`. La evidencia OOS emparejada exigida crece con
la profundidad (`required_oos_evidence`: MODERATE en las dos primeras generaciones, STRONG después; tope
`max_lineage_depth` 3, y entonces `CANDIDATE_FOR_VALIDATION`), porque iterar sobre el mismo OOS de desarrollo
aumenta el riesgo de descubrimiento falso. Estados: `QUEUED` → `IN_PROGRESS` → `IMPROVED_CONTINUED` |
`CANDIDATE_FOR_VALIDATION` | `EXHAUSTED` | `NEEDS_ATTENTION` | `REJECTED_INPUT`. `--inspect` muestra la cola con
resumen por estado y linajes; `status.json` la última ejecución (`runs`, `queue`). Comprobaciones previas por
experimento: sin reclamación activa de recálculo, memoria y disco. Ninguna clase acredita rentabilidad: toda
candidata exige validación con datos no consultados.

## Filtros de entrada (comprobados en SQX el 2026-09-06, 19:33–19:41 CEST)

Vocabulario nuevo, pedido por los agentes en todas las rondas anteriores. Cada filtro se añade como
condición `AND` al `If` de la regla de entrada de la dirección indicada, con los bloques nativos
`SQ.Blocks.BarAndTime` (`BarHourIsBigger`, `BarHourIsSmaller`, `BarDayOfWeekIsNot`) o `Boolean`
(`SQ.Blocks.Other`), en la forma XML de la plantilla propia de SQX
`user/settings/StrategyTemplates/highest_breakout_template_daily_filter.sqx`. No se usan las opciones
de trading de `lastSettings.xml` (`LimitTimeRange`, `ExitAtEndOfDay`…) porque el proyecto de recálculo
las copia al `Retest` con `customSettings="true"` y son comunes a control y variantes: solo lo que
está en las reglas varía por variante.

| Cambio | Efecto verificado (proyectos `UR_IMPROVE_MECANISMO_FILTROS_01/02`, sin registro) |
| --- | --- |
| `{"filter": "hour_range", "direction": "long\|short\|both", "from": H1, "to": H2}` | Señal solo si `H1 <= hora de apertura de la barra que acaba de cerrar < H2` (zona de los datos, `Shift 0`). La orden stop queda activa desde la barra siguiente: con `from=10, to=11` los rellenos cayeron a las 11 h (45 de 47 en IS) y 12 h; con `8–13`, rellenos entre las 10 y las 14 h. Para permitir primeros rellenos entre las A y las B: `from=A-1, to=B-1`. La orden sigue válida `BarsValid` barras (4 largos, 8 cortos en esta estrategia), así que puede rellenarse después de la ventana. |
| `{"filter": "exclude_weekdays", "direction": ..., "days": ["Monday", "Friday"]}` | Sin señal en esos días (máximo tres; nombres en inglés o español; 0 = domingo). Con lunes y viernes excluidos: cero rellenos en lunes; en viernes quedaron 16 de 60 rellenos, todos en la apertura de las 08:30, procedentes de órdenes de la víspera aún válidas. El filtro acota la señal, no la orden pendiente. |
| `{"filter": "disable_direction", "direction": "long\|short"}` | La regla de entrada recibe `AND Boolean(false)` y nunca se cumple: sin cortos, 140/48 operaciones (IS/OOS) frente a 173/56 del control; las largas no cambian. |

Verificación estructural (`build_variant`): todo cambio detectado dentro del `If` de la regla filtrada
debe ser una adición; nada existente puede cambiar; fuera de los filtros el número de parámetros que
cambian sigue siendo exactamente el previsto. Un filtro de hora ya presente no se apila: se reajusta
por `param_path` (`#Hour#` entra en el catálogo). El dosier del debate muestra las tablas por hora,
día y dirección **solo de la muestra de construcción** y oculta el segmento concreto de los hallazgos
OOS de concentración: elegir un filtro mirando el OOS convertiría la comprobación de desarrollo en
ajuste. Las cuatro variantes de mecanismo dieron `REJECTED_WORSE` o `INCONCLUSIVE`, como corresponde a
filtros elegidos sin hipótesis.

## Reparto decidido por Emilio (2026-09-06)

Los agentes piensan: analizan cada estrategia (contrato, diagnóstico, reglas, registro de lo probado), debaten y proponen pocas hipótesis con cambio concreto y criterio de aceptación. Los programas de esta guía ejecutan y miden; no deciden qué probar. La biblioteca fija `HYPOTHESIS_LIBRARY` es solo un andamio de pruebas del mecanismo.

## Recorrido con debate de agentes (flujo previsto)

0. `sqx_improvement_cycle.py dossier --source <original.sqx> --orders <órdenes_base.csv> --cycle <dir> [--registry <dir>]` → `contract.json`, `diagnosis_base.json`, `criteria.json`, `explored.json`.
0b. `sqx_hypothesis_debate.py --cycle <dir> --provider anthropic|claude-cli [--model …] [--max-variants 2]` → `debate/{dossier,proponente_*,critico,arbitro,summary,log,intervenciones}.json` y `debate/hypotheses.json`. Dos proponentes ciegos entre sí, validación determinista de cada cambio, crítico, árbitro sin consenso forzado; el desacuerdo y el presupuesto de búsqueda quedan registrados. Motivación y guardas en `orchestration/results/codex/MOTOR_MEJORA_20260906/INVESTIGACION_DEBATE_SEMANTICO.md`.
   Proveedor del sistema: `omniroute` (por defecto) = el omnirouter de la VPS de Oracle, `https://omniroute.143-47-35-167.sslip.io/pro/omniroute/api/v1` (OpenAI-compatible; la ruta `/v1` del proxy nginx no funciona). El módulo pide los alias de tarea `ultrarentable-mejora-proponente|critico|arbitro`, que Emilio define en el panel de superadmin del omnirouter; si no existen cae a `auto/best-reasoning` (`--model` o `OMNIROUTE_DEFAULT_MODEL`) y lo anota. Variables: `OMNIROUTE_URL`, `OMNIROUTE_API_KEY` (si se activan claves en el panel), `OMNIROUTE_INSECURE=1` (certificado sslip no reconocido; si no, se degrada solo y queda registrado). Respaldos de prueba: `anthropic` (SDK oficial), `claude-cli` (Claude Code `-p` desde el PC; sin `--bare`, que falla en 2.1.259), `replay` (pruebas).
1. Después, el recorrido de abajo con `--hypotheses <dir>/debate/hypotheses.json`.

## Recorrido

1. `prepare-local --source <original.sqx> --orders <órdenes_base.csv> --template <project.cfx de un retest verificado> --cycle <dir> --remote-dir /opt/SQX-headless/import/<dir>/experiment --project UR_IMPROVE_<NOMBRE> --hypotheses <hipótesis_de_los_agentes.json> [--candidate ETIQUETA=<variante externa.sqx>] [--registry <dir>]`
   Produce `contract.json`, `diagnosis_base.json`, `plan.json`, `criteria.json` (criterios registrados antes de recalcular) y `experiment/` (control + hasta dos variantes, proyecto `.cfx`, `manifest.json`). Formato de `--hypotheses`: `{"hypotheses": [{"id", "title", "problem", "change", "expected", "changes": [{"direction": "long|short", "exit": "profit_target|stop_loss|trailing_stop|trailing_activation|move_sl_to_be|exit_after_bars", "value"|"atr_period"} | {"param_path", "value"} | {"filter": "hour_range|exclude_weekdays|disable_direction", "direction": "long|short|both", "from", "to" | "days"}]}]}`; una hipótesis cuyo cambio no altera las reglas queda `NOT_APPLICABLE` y no se recalcula. Los candidatos externos que solo cambian metadatos se rechazan aquí. Repetir el paso no reescribe criterios ni experimento. En Windows, ejecutar con `MSYS_NO_PATHCONV=1` para que Git Bash no reescriba `/opt/...`.
2. Copiar el directorio del ciclo a la VPS exactamente en `<remote-dir>` (tar por ssh; comprobar SHA-256 de `project.cfx` y de `input/*.sqx`).
3. En la VPS: `python3 sqx_improvement_cycle.py run --cycle /opt/SQX-headless/import/<dir>`. Usa `run_reviewed` del motor: reclama el experimento (`reviewed_improvement_jobs/active.json`), carga el proyecto, importa, arranca, espera `TAREA TERMINADA`, exporta métricas, archivos y órdenes, y escribe `assessment.json` y `cost.json`. Comprobar antes: memoria disponible ≥ 8 GiB, sin `active.json`, sin directorio `user/projects/<proyecto>`.
4. `evaluate --cycle <dir> --registry /opt/SQX-headless/import/improvement_registry` → `evaluation.json`, `entrega.json` y registro por estrategia.
5. Traer la evidencia al repositorio (zip con manifiesto de hashes) y escribir el resultado con las siete preguntas del encargo.

## Clases de resultado

`NO_CHANGE_RULES`, `NO_EFFECT_IN_SAMPLE`, `REJECTED_WORSE`, `HISTORICAL_FIT_ONLY` (mejora IS, empeora OOS), `DEV_FAVORABLE_RELEVANT` (mejora ambas muestras y con relevancia para un destino según `criteria.json`), `DEV_FAVORABLE_NOT_RELEVANT`, `INCONCLUSIVE`. Ninguna clase equivale a validado: la validación exige datos no consultados.

## Reglas que se aprendieron ejecutándolo

- SQX 144.2953 puede responder a `count` y `list` sin líneas de datos (desde el 2026-09-06 12:02 CEST). El motor cuenta entonces exportando el banco a CSV; la protección contra proyectos duplicados mira `user/projects/<nombre>`.
- Un proyecto cargado a medias hay que eliminarlo (`-project action=remove`) antes de repetir; volver a cargar el mismo nombre crea `<nombre>(2)`.
- Un intento fallido deja `active.json` y un registro `NEEDS_RECONCILIATION`: se mueven a `reconciliation_N/` del ciclo con la causa escrita, nunca se borran.
- Con el generador activo el recálculo de tres estrategias tarda ~66 s (24 s ocioso). El motor espera hasta 120 s.
- El OOS que se consulta para clasificar es desarrollo. Sin datos posteriores reservados no hay validación independiente.
- Los calendarios de muestra (`sample_calendars`) terminan en la sesión que abre la tarde del último día del rango (las barras de domingo pertenecen al lunes siguiente): 258 días de negociación en el OOS 2025, no 257; las órdenes de esa sesión no quedan fuera del calendario.
