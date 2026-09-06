# Motor propio de mejora: ciclo por estrategia (guía comprobada)

Estado: primera entrega comprobada el 2026-09-06 con `Strategy 1.1.27` (@EW H1). Resultado,
límites y evidencia en `orchestration/results/codex/MOTOR_MEJORA_20260906/RESULTADO.md`. Esta guía
describe el recorrido que ya se ejecutó de verdad; no acredita rentabilidad ni aprobación de exámenes.

## Piezas (todas en `scripts/herramientas/`, biblioteca estándar, desplegadas en `/opt/SQX-headless/import/`)

| Módulo | Función | Entrada → salida |
| --- | --- | --- |
| `sqx_strategy_contract.py` | Contrato de entrada y comparación de reglas | `.sqx` → `contract.json`; dos `.sqx` → `IDENTICAL_BYTES` / `METADATA_ONLY_NO_BEHAVIOUR_CHANGE` / `RULES_CHANGED` con parámetros cambiados |
| `sqx_trade_diagnosis.py` | Diagnóstico de órdenes y cribado provisional de examen | CSV de órdenes + contrato → perfil IS/OOS, hallazgos, ventanas 1–5 días, estudio de exposición |
| `sqx_variant_mutations.py` | Cambios de salida verificados | reglas XML + lista de cambios → reglas nuevas + registro; falla si el cambio no altera nada o toca algo más |
| `sqx_improvement_cycle.py` | Ciclo completo | `prepare-local` (PC o VPS), `run` (solo VPS), `evaluate` (PC o VPS) |
| `sqx_native_improvement.py` | Motor de recálculo existente (proyecto Retest dedicado, evidencia, órdenes) | se conserva; `prepare(..., custom_variants=...)` |

## Reparto decidido por Emilio (2026-09-06)

Los agentes piensan: analizan cada estrategia (contrato, diagnóstico, reglas, registro de lo probado), debaten y proponen pocas hipótesis con cambio concreto y criterio de aceptación. Los programas de esta guía ejecutan y miden; no deciden qué probar. La biblioteca fija `HYPOTHESIS_LIBRARY` es solo un andamio de pruebas del mecanismo.

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
