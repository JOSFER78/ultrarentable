# REVIEW AG2-P02-003 — DECISIÓN EXTERNA

## Resultado
`REWORK`

## Lo que SÍ terminó Antigravity
La orden `AG2-P02-003` fue ejecutada, probada y entregada en `origin/main` con `READY_FOR_REVIEW`. El handoff declara 13/13 tests PASS y documenta la cadena `CanonicalStrategy -> compile_to_runtime -> CanonicalRuntimeAdapter -> RuntimeExecutionResult`.

## Lo que NO puedo aprobar todavía
La revisión del código real publicado en `origin/main` encuentra defectos que impiden considerar la Fase 02 cerrada:

### P02-004-01 — Defaults ocultos en runtime
`CanonicalRuntimeAdapter.__init__()` mantiene valores por defecto para `engine_version` y `policy_version`. Son identidad cuantitativa y deben proceder de una política/versión autoritativa o fallar cerrado.

### P02-004-02 — Fallback silencioso de indicadores
`_eval_indicator()` cae a `close` para indicadores no soportados y usa defaults de periodo/valores. Eso puede cambiar la semántica de una estrategia sin evidencia. Indicador desconocido, parámetro ausente o fuente inexistente debe fallar cerrado.

### P02-004-03 — Semántica de SL/TP no universal
El adaptador convierte `sl_value` y `tp_value` directamente en porcentajes independientemente de `sl_type`/`tp_type`. El contrato soporta ATR, puntos, porcentaje, RR y otras modalidades. No se puede declarar equivalencia si la implementación ejecuta una semántica distinta.

### P02-004-04 — Ejecución no suficientemente canónica
Aunque existe el adaptador, el código mostrado contiene un backtest propio simplificado que no demuestra que el motor universal canónico de ULTRARENTABLE sea el que consume las instrucciones en la ruta productiva definitiva. Debe demostrarse el call-site real hasta ledger/execution boundary, no sólo un ejecutor nuevo en paralelo.

### P02-004-05 — Direction/risk/session completeness
La ejecución actual no demuestra de forma completa SHORT/BOTH, sizing real, `max_open_positions`, session windows y trailing/time-stop. No basta con transportar los campos; deben llegar a la semántica del motor real o bloquearse si no están soportados.

### P02-004-06 — Dataset y execution identity deben ser reales
`execute_backtest()` acepta `dataset_id` y `dataset_sha256` como argumentos sin demostrar que proceden de la cadena de custodia canónica. No puede certificarse una ejecución sólo porque se le pase una identidad desde fuera.

## Decisión adaptativa
No avanzar a Phase 03.

Siguiente trabajo:
`AG2-P02-004` — Runtime Semantics, Real Engine Binding & Fail-Closed Execution.

## Alcance obligatorio
- SOLO Phase 02 / rework.
- Implementar únicamente las correcciones anteriores y sus dependencias directas.
- No tocar Discovery, ULTRA, FONDEO, Meta-Strategy ni Phase 03.
- Todo hallazgo fuera de alcance = `DEFERRED_TO_FUTURE_ORDER` salvo blocker directo.

## Criterio de salida
1. Cero defaults cuantitativos silenciosos en runtime.
2. Indicadores y parámetros no soportados fallan cerrado; ningún fallback a `close`.
3. SL/TP se ejecutan según su tipo canónico real, o se rechazan si el engine actual no lo soporta.
4. Existe un único call-path real hasta el execution/ledger boundary.
5. Direction, sizing, session y exits mantienen semántica real de extremo a extremo.
6. Dataset identity/hash provienen de la cadena de custodia canónica.
7. Tests independientes prueban equivalencia y fail-closed.
8. Todo queda publicado en `origin/main` con SHA verificable.
9. Handoff `READY_FOR_REVIEW` y STOP.
