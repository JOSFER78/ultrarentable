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
| `sqx_variant_mutations.py` | Vocabulario de cambios y verificación de que la variante cambia exactamente lo declarado | reglas XML + cambios → reglas nuevas + registro; catálogo `mutable_parameters` | los agentes pidan una palanca nueva (filtros de hora/día, salidas parciales…) |
| `sqx_hypothesis_debate.py` | Debate de agentes: dosier, proponentes ciegos, validación, crítico, árbitro; proveedores (`omniroute` del sistema, `anthropic`, `claude-cli`, `replay`) | ciclo con contrato/diagnóstico/criterios/explorados → `debate/hypotheses.json` + registro | cambien los roles, los prompts o el endpoint de IA |
| `sqx_native_improvement.py` | Recálculo nativo en SQX (motor existente): proyecto Retest dedicado, evidencia, órdenes | experimento preparado → `retest.csv`, `retested/*.sqx`, órdenes, `assessment.json` | cambie SQX o su CLI |
| `sqx_variant_evaluation.py` | Política de evaluación: comparación emparejada por día, relevancia por destino, clases; criterios registrados antes | experimento recalculado + contrato + `criteria.json` → `evaluation.json` | cambien los criterios de aceptación o los destinos |
| `sqx_improvement_cycle.py` | Orquestación de UN experimento y entrega: `dossier`, `prepare-local`, `run`, `evaluate`; paquete `entrega.json`; registro por estrategia | ficheros del ciclo → `entrega.json`, `improvement_registry/<reglas>.json` | cambie el formato de entrega o el registro |
| `sqx_improvement_service.py` | Servicio autónomo: cola persistente, presupuesto por estrategia, reintentos limitados, reconciliación; una estrategia y un experimento por ejecución | `mejora/inbox/*.sqx` → `mejora/strategies/<slug>/ciclo_NN/`, `queue.json`, `status.json`, `outbox/` | cambie la política de presupuesto o de continuidad |
| `sqx_fixed_hypotheses_scaffold.py` | Andamio de hipótesis fijas SOLO para pruebas del mecanismo | — | nunca en producción (Emilio: los agentes piensan) |

## Servicio autónomo en la VPS

`sqx-mejora-agentes.timer` ejecuta cada hora `sqx_improvement_service.py --once` (unidad `sqx-mejora-agentes.service`). Para encolar una estrategia: dejar su `.sqx` (y un `.json` opcional con procedencia y destino) en `/opt/SQX-headless/import/mejora/inbox/`. El servicio la contrata, exporta sus órdenes heredadas (o usa las del último recálculo), diagnostica, convoca el debate por el omnirouter, construye y verifica las variantes, recalcula en SQX, evalúa, registra y empaqueta. Estados por estrategia: `QUEUED` → `IN_PROGRESS` → `CANDIDATE_FOR_VALIDATION` (entrega copiada a `outbox/`) | `EXHAUSTED` (presupuesto de experimentos o debates vacíos agotado) | `NEEDS_ATTENTION` (fallo técnico repetido, con diagnóstico) | `REJECTED_INPUT` (contrato incompleto o archivo corrupto). `--inspect` muestra la cola; `status.json` la última ejecución. Comprobaciones previas: sin reclamación activa de recálculo, memoria y disco. El temporizador antiguo `sqx-improvement.timer` (recetas MYM/MNQ) sigue existiendo; ambos se excluyen por la reclamación del motor.

## Reparto decidido por Emilio (2026-09-06)

Los agentes piensan: analizan cada estrategia (contrato, diagnóstico, reglas, registro de lo probado), debaten y proponen pocas hipótesis con cambio concreto y criterio de aceptación. Los programas de esta guía ejecutan y miden; no deciden qué probar. La biblioteca fija `HYPOTHESIS_LIBRARY` es solo un andamio de pruebas del mecanismo.

## Recorrido con debate de agentes (flujo previsto)

0. `sqx_improvement_cycle.py dossier --source <original.sqx> --orders <órdenes_base.csv> --cycle <dir> [--registry <dir>]` → `contract.json`, `diagnosis_base.json`, `criteria.json`, `explored.json`.
0b. `sqx_hypothesis_debate.py --cycle <dir> --provider anthropic|claude-cli [--model …] [--max-variants 2]` → `debate/{dossier,proponente_*,critico,arbitro,summary,log,intervenciones}.json` y `debate/hypotheses.json`. Dos proponentes ciegos entre sí, validación determinista de cada cambio, crítico, árbitro sin consenso forzado; el desacuerdo y el presupuesto de búsqueda quedan registrados. Motivación y guardas en `orchestration/results/codex/MOTOR_MEJORA_20260906/INVESTIGACION_DEBATE_SEMANTICO.md`.
   Proveedor del sistema: `omniroute` (por defecto) = el omnirouter de la VPS de Oracle, `https://omniroute.143-47-35-167.sslip.io/pro/omniroute/api/v1` (OpenAI-compatible; la ruta `/v1` del proxy nginx no funciona). El módulo pide los alias de tarea `ultrarentable-mejora-proponente|critico|arbitro`, que Emilio define en el panel de superadmin del omnirouter; si no existen cae a `auto/best-reasoning` (`--model` o `OMNIROUTE_DEFAULT_MODEL`) y lo anota. Variables: `OMNIROUTE_URL`, `OMNIROUTE_API_KEY` (si se activan claves en el panel), `OMNIROUTE_INSECURE=1` (certificado sslip no reconocido; si no, se degrada solo y queda registrado). Respaldos de prueba: `anthropic` (SDK oficial), `claude-cli` (Claude Code `-p` desde el PC; sin `--bare`, que falla en 2.1.259), `replay` (pruebas).
1. Después, el recorrido de abajo con `--hypotheses <dir>/debate/hypotheses.json`.

## Recorrido

1. `prepare-local --source <original.sqx> --orders <órdenes_base.csv> --template <project.cfx de un retest verificado> --cycle <dir> --remote-dir /opt/SQX-headless/import/<dir>/experiment --project UR_IMPROVE_<NOMBRE> --hypotheses <hipótesis_de_los_agentes.json> [--candidate ETIQUETA=<variante externa.sqx>] [--registry <dir>]`
   Produce `contract.json`, `diagnosis_base.json`, `plan.json`, `criteria.json` (criterios registrados antes de recalcular) y `experiment/` (control + hasta dos variantes, proyecto `.cfx`, `manifest.json`). Formato de `--hypotheses`: `{"hypotheses": [{"id", "title", "problem", "change", "expected", "changes": [{"direction": "long|short", "exit": "profit_target|stop_loss|trailing_stop|trailing_activation|move_sl_to_be|exit_after_bars", "value"|"atr_period"}]}]}`; una hipótesis cuyo cambio no altera las reglas queda `NOT_APPLICABLE` y no se recalcula. Los candidatos externos que solo cambian metadatos se rechazan aquí. Repetir el paso no reescribe criterios ni experimento. En Windows, ejecutar con `MSYS_NO_PATHCONV=1` para que Git Bash no reescriba `/opt/...`.
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
